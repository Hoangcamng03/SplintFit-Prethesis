"""End-to-end automated tests for SplintFit Studio backend, geometry & Fusion 360 Form export."""
import io
import shutil
import sys
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.server import app, SESSIONS, EXPORT_RECORDS  # noqa: E402


class TestSplintFitStudioAPI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = app.test_client()
        cls.created_folders = []

    @classmethod
    def tearDownClass(cls):
        for folder in cls.created_folders:
            if folder.exists():
                shutil.rmtree(folder, ignore_errors=True)

    def test_health_and_frontend_served(self):
        r = self.client.get("/api/health")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.get_json()["status"], "ok")

        idx = self.client.get("/")
        self.assertEqual(idx.status_code, 200)
        self.assertIn("SplintFit Studio", idx.get_data(as_text=True))

        css = self.client.get("/static/styles.css")
        self.assertEqual(css.status_code, 200)
        self.assertIn("--primary", css.get_data(as_text=True))
        idx.close()
        css.close()

    def test_full_demo_build_and_fusion_form_export(self):
        # 1. Load synthetic forearm-hand scan
        r_scan = self.client.post("/api/scan/demo", json={"kind": "hand_forearm"})
        self.assertEqual(r_scan.status_code, 200)
        scan = r_scan.get_json()
        sid = scan["session_id"]
        lm = scan["suggested_landmarks"]
        self.assertGreater(scan["mesh"]["triangle_count"], 1000)

        # 2. Build 2-piece perforated splint + Fusion 360 Form Quad cage
        params = {
            'proximal_point': lm['proximal'], 'distal_point': lm['distal'], 'side_point': lm['side'],
            'splint_mode': 'bivalve', 'cast_template': True, 'clearance_mm': 1.5,
            'padding_mm': .5, 'thickness_mm': 3.2, 'seam_gap_mm': 4.,
            'ventilation': True, 'hole_pitch_mm': 24., 'hole_ratio': .48,
            'hand_notch_depth_mm': 18.,
        }
        r_build = self.client.post(
            "/api/build",
            json={
                "session_id": sid,
                "params": {
                    "proximal_point": lm["proximal"],
                    "distal_point": lm["distal"],
                    "side_point": lm["side"],
                    "splint_mode": "bivalve",
                    "cast_template": True,
                    "clearance_mm": 1.5,
                    "padding_mm": 0.5,
                    "thickness_mm": 3.2,
                    "seam_gap_mm": 4.0,
                    "ventilation": True,
                    "hole_pitch_mm": 24.0,
                    "hole_ratio": 0.48,
                    "hand_notch_depth_mm": 18.0,
                },
            },
        )
        self.assertEqual(r_build.status_code, 200, r_build.get_data(as_text=True))
        built = r_build.get_json()
        self.assertTrue(built["export_ready"])
        self.assertTrue(built["form_available"])
        self.assertEqual(len(built["pieces"]), 2)
        self.assertGreater(built["report"]["ventilation_holes"], 0)
        self.assertGreater(built["report"]["strap_slots"], 0)
        self.assertGreater(len(built["pieces"][0]["quad_wireframe"]), 0)

        # 3. Export clean Fusion 360 Form only bundle (default)
        r_exp = self.client.post(
            "/api/export",
            json={
                "session_id": sid,
                "build_id": built['build_id'], "params": params,
                "case_id": "TEST-FUSION",
                "side": "Tay trái",
            },
        )
        self.assertEqual(r_exp.status_code, 200, r_exp.get_data(as_text=True))
        exp = r_exp.get_json()
        out_dir = Path(exp["folder_path"])
        self.created_folders.append(out_dir)
        self.assertTrue(out_dir.exists())

        # Verify ONLY the 5 clean Fusion 360 Form mesh files are exported by default
        expected_fusion_files = {
            "splint_form_piece_1_quad.obj",
            "splint_form_piece_2_quad.obj",
            "splint_form_perforated_piece_1_quad.obj",
            "splint_form_perforated_piece_2_quad.obj",
            "scan_reference_mm.stl",
        }
        actual_files = {f["path"] for f in exp["files"]}
        self.assertEqual(actual_files, expected_fusion_files)

        # Verify pure All-Quad OBJ topology (strictly 4 vertices per face) for Fusion Form T-Spline
        for fname in (
            "splint_form_piece_1_quad.obj",
            "splint_form_piece_2_quad.obj",
            "splint_form_perforated_piece_1_quad.obj",
        ):
            obj_lines = (out_dir / fname).read_text(encoding="utf-8").splitlines()
            faces = [line.split()[1:] for line in obj_lines if line.startswith("f ")]
            self.assertGreater(len(faces), 100)
            self.assertTrue(all(len(f) == 4 for f in faces), f"{fname} must be strictly all-quad for Fusion 360 Form!")

        # 4. Verify individual file streaming (for Browser File System Access API) & ZIP download
        r_file = self.client.get(f"/api/export/{exp['export_id']}/file/splint_form_piece_1_quad.obj")
        self.assertEqual(r_file.status_code, 200)
        self.assertIn(b"SplintFit_Inner_Control_Cage", r_file.data)

        r_folders = self.client.get("/api/user-folders")
        self.assertEqual(r_folders.status_code, 200)
        self.assertIn("desktop", r_folders.get_json())

        r_zip = self.client.get(exp["download_url"])
        self.assertEqual(r_zip.status_code, 200)
        with zipfile.ZipFile(io.BytesIO(r_zip.data)) as zf:
            names = zf.namelist()
            self.assertEqual(len(names), 5)
            self.assertTrue(any(n.endswith("splint_form_piece_1_quad.obj") for n in names))

        # 5. Verify custom output_dir + optional full export still work
        custom_base = Path(exp["folder_path"]).parent / "_custom_test_dir"
        r_full = self.client.post(
            "/api/export",
            json={
                "session_id": sid,
                "build_id": built['build_id'], "params": params,
                "case_id": "TEST-FULL",
                "side": "Tay trái",
                "export_mode": "full",
                "output_dir": str(custom_base),
            },
        )
        self.assertEqual(r_full.status_code, 200, r_full.get_data(as_text=True))
        full_dir = Path(r_full.get_json()["folder_path"])
        self.created_folders.append(custom_base)
        self.assertEqual(full_dir.parent.resolve(), custom_base.resolve())
        self.assertTrue((full_dir / "shell_piece_1_prototype.stl").is_file())
        self.assertTrue((full_dir / "fusion_user_parameters.json").is_file())


if __name__ == "__main__":
    unittest.main()
