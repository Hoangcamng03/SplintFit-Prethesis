"""Automated end-to-end tests for SplintFit Studio Native Desktop App (PyQt6 + PyVista)."""
import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from PyQt6.QtWidgets import QApplication  # noqa: E402
from desktop.main_window import SplintFitStudioWindow  # noqa: E402


class TestSplintFitDesktopApp(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])
        cls.tmp_root = Path(tempfile.mkdtemp(prefix="splintfit_desktop_test_"))

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp_root, ignore_errors=True)

    def test_full_5_step_desktop_workflow_and_fusion_export(self):
        win = SplintFitStudioWindow(offscreen=True)
        try:
            # Step 1: Load anatomical forearm-hand demo
            win.load_demo("hand_forearm")
            self.assertIsNotNone(win.active_mesh)
            self.assertIsNotNone(win.safe_frame)
            self.assertGreater(win.safe_frame["safe_span_mm"], 150.0)

            # Step 2: Safe-Zone sliders (shorten slightly + rotate seam 30 deg)
            win._go_to_step(1)
            win.sl_prox.setValue(10)
            win.sl_ang.setValue(30)
            self.assertEqual(win.lbl_ang_val.text(), "30°")

            # Step 3: Apply Clinical Presets & Build 2-piece honeycomb splint
            win._go_to_step(2)
            win._apply_preset("fit", "standard")
            win._apply_preset("rigidity", "medium")
            win._apply_preset("vent", "honeycomb")
            win._apply_preset("notch", "wide")
            ok = win.run_build()
            self.assertTrue(ok)
            self.assertEqual(win.current_step, 3)
            self.assertTrue(win.build_result["export_ready"])
            self.assertEqual(len(win.build_result["pieces"]), 2)
            self.assertGreater(win.build_result["report"]["ventilation_holes"], 0)
            self.assertGreater(win.build_result["report"]["quad_faces"], 200)

            # Step 5: Export clean 5-file Fusion 360 Form bundle named by Case ID (e.g. A -> A-1.obj)
            win._go_to_step(4)
            win.case_id_input.setText("A")
            win.chk_export_full.setChecked(False)
            out_dir = win.run_export(override_dir=str(self.tmp_root))
            self.assertIsNotNone(out_dir)
            self.assertTrue(out_dir.exists())

            expected = {
                "A-1.obj",
                "A-2.obj",
                "A-1_holes.obj",
                "A-2_holes.obj",
                "A_scan.stl",
            }
            actual = {p.name for p in out_dir.iterdir() if p.is_file()}
            self.assertEqual(actual, expected)

            # Verify strictly All-Quad OBJ faces (4 vertices per face) for Fusion 360 T-Spline
            for fname in ("A-1.obj", "A-2.obj", "A-1_holes.obj"):
                lines = (out_dir / fname).read_text(encoding="utf-8").splitlines()
                faces = [ln.split()[1:] for ln in lines if ln.startswith("f ")]
                self.assertGreater(len(faces), 100)
                self.assertTrue(all(len(f) == 4 for f in faces), f"{fname} must be strictly all-quad!")

            # Optional full export regression check
            win.chk_export_full.setChecked(True)
            full_dir = win.run_export(override_dir=str(self.tmp_root / "full_out"))
            self.assertIsNotNone(full_dir)
            self.assertTrue((full_dir / "shell_piece_1_prototype.stl").is_file())
            self.assertTrue((full_dir / "fusion_user_parameters.json").is_file())
        finally:
            win.close()


if __name__ == "__main__":
    unittest.main()
