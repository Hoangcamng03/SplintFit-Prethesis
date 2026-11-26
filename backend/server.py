"""SplintFit Studio Local Web Server (Flask).

Provides REST APIs for 3D scan loading, landmark suggestion, 2-piece perforated
splint generation, all-quad Fusion 360 Form mesh export, and STL export.
"""
from __future__ import annotations

import io
import os
import re
import subprocess
import sys
import tempfile
import uuid
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
from flask import Flask, Response, jsonify, request, send_from_directory

ROOT_DIR = Path(__file__).resolve().parent.parent
ENGINE_DIR = ROOT_DIR / "engine"
FRONTEND_DIR = ROOT_DIR / "frontend"
EXPORTS_DIR = ROOT_DIR / "exports"
EXPORTS_DIR.mkdir(parents=True, exist_ok=True)

if str(ENGINE_DIR) not in sys.path:
    sys.path.insert(0, str(ENGINE_DIR))

import pyvista as pv  # noqa: E402
from cast_template import hand_demo_mesh  # noqa: E402
from geometry import (  # noqa: E402
    DesignProblem,
    Parameters,
    build as engine_build,
    demo_mesh,
    display_mesh,
    export_bundle,
    prepare_scan,
    read_mesh,
    stats as mesh_stats,
    suggested_points,
    triangles,
    write_obj,
)

app = Flask(__name__, static_folder=str(FRONTEND_DIR), static_url_path="/static")
app.config["MAX_CONTENT_LENGTH"] = 250 * 1024 * 1024  # 250 MB scans

SESSIONS: dict[str, dict[str, Any]] = {}
EXPORT_RECORDS: dict[str, Path] = {}


def _polydata_to_three_json(mesh: pv.PolyData, max_tris: int = 60000, scalar_key: str | None = None) -> dict[str, Any]:
    """Serialize a PyVista PolyData triangle mesh for Three.js BufferGeometry."""
    m = display_mesh(mesh, target=max_tris) if mesh.n_cells > max_tris else mesh
    m = m.triangulate()
    pts = np.asarray(m.points, dtype=np.float32)
    tris = triangles(m).astype(np.int32)
    payload: dict[str, Any] = {
        "positions": np.round(pts, 3).ravel().tolist(),
        "indices": tris.ravel().tolist(),
        "vertex_count": int(len(pts)),
        "triangle_count": int(len(tris)),
        "bounds": [round(float(v), 3) for v in m.bounds],
        "center": [round(float(v), 3) for v in m.center],
    }
    if scalar_key and scalar_key in m.point_data:
        vals = np.asarray(m.point_data[scalar_key], dtype=np.float32)
        payload["scalars"] = np.round(vals, 3).tolist()
        payload["scalar_min"] = round(float(np.min(vals)), 3) if len(vals) else 0.0
        payload["scalar_max"] = round(float(np.max(vals)), 3) if len(vals) else 0.0
    return payload


def _boundary_segments(mesh: pv.PolyData) -> list[float]:
    """Extract open/non-manifold boundary edges as flat line-segment coordinates."""
    edges_mesh = mesh.extract_feature_edges(
        boundary_edges=True,
        non_manifold_edges=True,
        feature_edges=False,
        manifold_edges=False,
    )
    if edges_mesh.n_cells == 0:
        return []
    pts = np.asarray(edges_mesh.points, dtype=np.float32)
    lines = np.asarray(edges_mesh.lines)
    coords: list[float] = []
    i = 0
    while i < len(lines):
        count = int(lines[i])
        ids = lines[i + 1 : i + 1 + count]
        for a, b in zip(ids[:-1], ids[1:]):
            coords.extend(np.round(pts[a], 3).tolist())
            coords.extend(np.round(pts[b], 3).tolist())
        i += count + 1
    return coords


def _quad_wireframe(points: np.ndarray, quads: np.ndarray) -> list[float]:
    """Convert quad faces (N, 4) into unique wireframe line segments for Three.js."""
    if points is None or quads is None or len(quads) == 0:
        return []
    e0 = quads[:, [0, 1]]
    e1 = quads[:, [1, 2]]
    e2 = quads[:, [2, 3]]
    e3 = quads[:, [3, 0]]
    all_edges = np.vstack((e0, e1, e2, e3))
    unique_edges = np.unique(np.sort(all_edges, axis=1), axis=0)
    pts = np.round(np.asarray(points, dtype=np.float32), 3)
    return pts[unique_edges].reshape(-1).tolist()


def _sanitize_name(value: str, default: str = "CASE-001") -> str:
    cleaned = re.sub(r"[^A-Za-z0-9_-]+", "_", (value or "").strip()).strip("_")
    return cleaned[:48] or default


def _session_scan_response(session_id: str, session: dict[str, Any]) -> dict[str, Any]:
    active_mesh = session["active_mesh"]
    scan = session["scan"]
    sugg = suggested_points(active_mesh)
    pieces_info = [
        {"id": p["id"], "triangles": p["triangles"], "area_mm2": round(p["area_mm2"], 1)}
        for p in scan["pieces"]
    ]
    return {
        "session_id": session_id,
        "source_name": session["source_name"],
        "is_demo": session["is_demo"],
        "scale_mm": session["scale_mm"],
        "active_piece_id": session["active_piece_id"],
        "pieces": pieces_info,
        "total_pieces": scan["total_pieces"],
        "stats": mesh_stats(active_mesh),
        "suggested_landmarks": {
            "proximal": [round(float(v), 3) for v in sugg["proximal"]],
            "distal": [round(float(v), 3) for v in sugg["distal"]],
            "side": [round(float(v), 3) for v in sugg["side"]],
            "span_mm": round(float(sugg["span_mm"]), 2),
        },
        "safe_frame": sugg.get("safe_frame"),
        "mesh": _polydata_to_three_json(active_mesh, max_tris=55000),
        "boundary_segments": _boundary_segments(active_mesh),
    }


@app.get("/")
def index_page():
    return send_from_directory(FRONTEND_DIR, "index.html")


@app.get("/api/health")
def api_health():
    return jsonify({"status": "ok", "app": "SplintFit Studio", "version": "1.0.0", "pyvista": pv.__version__})


@app.post("/api/scan/demo")
def api_load_demo():
    body = request.get_json(silent=True) or {}
    kind = body.get("kind", "hand_forearm")
    if kind == "simple_forearm":
        mesh = demo_mesh()
        name = "Mau_thu_cang_tay_co_ban.stl"
    else:
        mesh = hand_demo_mesh()
        name = "Mau_thu_cang_tay_co_tay_ban_tay.stl"

    scan = prepare_scan(mesh)
    active = scan["pieces"][0]["mesh"] if scan["pieces"] else mesh
    sid = uuid.uuid4().hex[:12]
    SESSIONS[sid] = {
        "source_name": name,
        "is_demo": True,
        "demo_kind": kind,
        "scale_mm": 1.0,
        "scan": scan,
        "active_piece_id": scan["pieces"][0]["id"] if scan["pieces"] else -1,
        "active_mesh": active,
        "last_result": None,
        "last_params": None,
    }
    return jsonify(_session_scan_response(sid, SESSIONS[sid]))


@app.post("/api/scan/upload")
def api_upload_scan():
    upload = request.files.get("file")
    if upload is None or not upload.filename:
        return jsonify({"error": "Chưa chọn file quét 3D (.stl, .obj, .ply)."}), 400
    filename = upload.filename
    ext = Path(filename).suffix.lower()
    if ext not in {".stl", ".obj", ".ply"}:
        return jsonify({"error": f"Định dạng '{ext}' chưa hỗ trợ. Hãy dùng file .stl, .obj hoặc .ply xuất từ KIRI Engine."}), 400
    try:
        scale_mm = float(request.form.get("scale_mm", 1.0))
    except ValueError:
        return jsonify({"error": "Hệ số đơn vị không hợp lệ."}), 400

    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
            upload.save(tmp)
            tmp_path = Path(tmp.name)
        mesh = read_mesh(str(tmp_path), scale=scale_mm)
        scan = prepare_scan(mesh)
        active = scan["pieces"][0]["mesh"] if scan["pieces"] else mesh
        sid = uuid.uuid4().hex[:12]
        SESSIONS[sid] = {
            "source_name": filename,
            "is_demo": False,
            "scale_mm": scale_mm,
            "scan": scan,
            "active_piece_id": scan["pieces"][0]["id"] if scan["pieces"] else -1,
            "active_mesh": active,
            "last_result": None,
            "last_params": None,
        }
        return jsonify(_session_scan_response(sid, SESSIONS[sid]))
    except Exception as exc:
        return jsonify({"error": str(exc)}), 400
    finally:
        if tmp_path and tmp_path.exists():
            try:
                tmp_path.unlink()
            except OSError:
                pass


@app.post("/api/scan/select-piece")
def api_select_piece():
    body = request.get_json(silent=True) or {}
    sid = body.get("session_id")
    session = SESSIONS.get(sid)
    if not session:
        return jsonify({"error": "Phiên làm việc không tồn tại. Hãy nạp lại file quét."}), 404
    piece_id = body.get("piece_id")
    scan = session["scan"]
    if piece_id == "all":
        session["active_mesh"] = scan["source"]
        session["active_piece_id"] = "all"
    else:
        found = next((p for p in scan["pieces"] if p["id"] == int(piece_id)), None)
        if not found:
            return jsonify({"error": "Không tìm thấy mảnh lưới đã chọn."}), 400
        session["active_mesh"] = found["mesh"]
        session["active_piece_id"] = found["id"]
    session["last_result"] = None
    return jsonify(_session_scan_response(sid, session))


def _parse_parameters(data: dict[str, Any]) -> Parameters:
    return Parameters(
        axis="AUTO",
        proximal_point=data.get("proximal_point"),
        distal_point=data.get("distal_point"),
        side_point=data.get("side_point"),
        opening_rotation_deg=float(data.get("opening_rotation_deg", 0.0)),
        clearance_mm=float(data.get("clearance_mm", 1.5)),
        padding_mm=float(data.get("padding_mm", 0.5)),
        thickness_mm=float(data.get("thickness_mm", 3.2)),
        coverage_deg=float(data.get("coverage_deg", 180.0)),
        start_adjust_mm=float(data.get("start_adjust_mm", 0.0)),
        end_adjust_mm=float(data.get("end_adjust_mm", 0.0)),
        reliefs=data.get("reliefs") or [],
        splint_mode=str(data.get("splint_mode", "bivalve")),
        seam_gap_mm=float(data.get("seam_gap_mm", 4.0)),
        cast_template=bool(data.get("cast_template", True)),
        ventilation=bool(data.get("ventilation", True)),
        hole_pitch_mm=float(data.get("hole_pitch_mm", 20.0)),
        hole_ratio=float(data.get("hole_ratio", 0.58)),
        hand_notch_depth_mm=float(data.get("hand_notch_depth_mm", 22.0)),
        hand_notch_width_deg=float(data.get("hand_notch_width_deg", 75.0)),
        hand_notch_angle_deg=float(data.get("hand_notch_angle_deg", 0.0)),
        rim_flare_mm=float(data.get("rim_flare_mm", 1.4)),
        circumference_proximal_mm=float(data.get("circumference_proximal_mm", 0.0)),
        circumference_mid_mm=float(data.get("circumference_mid_mm", 0.0)),
        circumference_distal_mm=float(data.get("circumference_distal_mm", 0.0)),
        circumference_tolerance_mm=float(data.get("circumference_tolerance_mm", 3.0)),
        max_sampled_deviation_mm=float(data.get("max_sampled_deviation_mm", 1.5)),
        allow_incomplete_preview=bool(data.get("allow_incomplete_preview", False)),
        auto_orient_open_normals=True,
    )


@app.post("/api/build")
def api_build():
    try:
        body = request.get_json(silent=True) or {}
        sid = body.get("session_id")
        session = SESSIONS.get(sid)
        if not session:
            return jsonify({"error": "Phiên làm việc không tồn tại. Hãy nạp lại file quét."}), 404
        params = _parse_parameters(body.get("params", {}))
        result = engine_build(session["active_mesh"], params)
        session["last_result"] = result
        session["last_params"] = params

        pieces_payload = []
        raw_pieces = result.get("pieces") or [result]
        for idx, piece in enumerate(raw_pieces):
            shell_json = _polydata_to_three_json(piece["shell"], max_tris=80000) if piece.get("shell") is not None else None
            inner_json = (
                _polydata_to_three_json(piece["inner"], max_tris=60000, scalar_key="nominal_clearance_mm")
                if piece.get("inner") is not None
                else None
            )
            quad_wire = _quad_wireframe(*piece["quad"]) if piece.get("quad") is not None else []
            perf_wire = _quad_wireframe(*piece["perforated_quad"]) if piece.get("perforated_quad") is not None else []
            pieces_payload.append(
                {
                    "index": idx + 1,
                    "shell": shell_json,
                    "inner": inner_json,
                    "quad_wireframe": quad_wire,
                    "perforated_wireframe": perf_wire,
                    "quad_faces": int(piece["report"].get("quad_faces", 0)),
                    "perforated_quad_faces": int(piece["report"].get("perforated_quad_faces", 0)),
                }
            )

        return jsonify(
            {
                "status": result.get("status", "ready"),
                "export_ready": bool(result.get("export_ready", False)),
                "form_available": bool(result.get("form_available", False)),
                "report": result.get("report", {}),
                "pieces": pieces_payload,
            }
        )
    except DesignProblem as exc:
        return jsonify({"error": str(exc), "error_type": "design_problem"}), 422
    except ValueError as exc:
        return jsonify({"error": str(exc), "error_type": "validation"}), 400
    except Exception as exc:
        return jsonify({"error": f"Lỗi xử lý hình học: {exc}", "error_type": "internal"}), 500


@app.post("/api/export")
def api_export():
    try:
        body = request.get_json(silent=True) or {}
        sid = body.get("session_id")
        session = SESSIONS.get(sid)
        if not session or not session.get("last_result"):
            return jsonify({"error": "Chưa có mô hình nẹp nào được tạo. Hãy tạo mô hình ở bước 3 trước."}), 400
        result = session["last_result"]
        params = session["last_params"]
        if not result.get("export_ready"):
            return jsonify({"error": "Mô hình hiện tại chưa đạt điều kiện xuất file."}), 400

        case_id = _sanitize_name(body.get("case_id", "CASE-001"))
        side = str(body.get("side", "Tay trái"))
        notes = str(body.get("notes", ""))
        export_mode = str(body.get("export_mode", "fusion_only"))
        custom_dir = str(body.get("output_dir") or "").strip()
        if custom_dir:
            base_dir = Path(custom_dir).expanduser()
            base_dir.mkdir(parents=True, exist_ok=True)
        else:
            base_dir = EXPORTS_DIR
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        folder_name = f"{case_id}_{stamp}"
        target_dir = base_dir / folder_name

        if export_mode == "full":
            metadata = {
                "case_id": case_id,
                "side": side,
                "notes": notes,
                "source_name": session["source_name"],
                "exported_at": datetime.now().isoformat(timespec="seconds"),
                "app": "SplintFit Studio v2.0",
            }
            exported_path = export_bundle(target_dir, session["active_mesh"], result, params, metadata)
        else:
            # Clean Fusion 360 Form export: only All-Quad OBJ meshes + mm scan reference
            target_dir.mkdir(parents=True, exist_ok=False)
            pieces = result.get("pieces") or [result]
            for idx, piece in enumerate(pieces):
                if piece.get("quad") is not None:
                    name = "splint_form_quad.obj" if len(pieces) == 1 else f"splint_form_piece_{idx + 1}_quad.obj"
                    write_obj(target_dir / name, *piece["quad"])
                if piece.get("perforated_quad") is not None:
                    name = f"splint_form_perforated_piece_{idx + 1}_quad.obj"
                    write_obj(target_dir / name, *piece["perforated_quad"])
            session["active_mesh"].save(target_dir / "scan_reference_mm.stl")
            exported_path = target_dir

        export_id = uuid.uuid4().hex[:10]
        EXPORT_RECORDS[export_id] = exported_path

        files_list = sorted(
            [
                {"path": str(p.relative_to(exported_path)).replace("\\", "/"), "size_kb": round(p.stat().st_size / 1024.0, 1)}
                for p in exported_path.rglob("*")
                if p.is_file()
            ],
            key=lambda x: x["path"],
        )
        return jsonify(
            {
                "export_id": export_id,
                "folder_name": folder_name,
                "folder_path": str(exported_path),
                "download_url": f"/api/export/{export_id}/download",
                "files": files_list,
            }
        )
    except Exception as exc:
        return jsonify({"error": f"Không thể xuất gói file: {exc}"}), 500


@app.get("/api/export/<export_id>/download")
def api_export_download(export_id: str):
    folder = EXPORT_RECORDS.get(export_id)
    if not folder or not folder.exists():
        return jsonify({"error": "Gói xuất không tồn tại."}), 404
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for file_path in folder.rglob("*"):
            if file_path.is_file():
                zf.write(file_path, arcname=f"{folder.name}/{file_path.relative_to(folder)}")
    buf.seek(0)
    return Response(
        buf.getvalue(),
        mimetype="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{folder.name}.zip"'},
    )


@app.post("/api/browse-folder")
def api_browse_folder():
    body = request.get_json(silent=True) or {}
    initial = str(body.get("initial_dir") or "").strip()
    if not initial or not Path(initial).exists():
        initial = str(Path.home() / "Desktop")
    try:
        import tkinter as tk
        from tkinter import filedialog

        root = tk.Tk()
        root.withdraw()
        root.attributes("-topmost", True)
        chosen = filedialog.askdirectory(title="Chọn thư mục lưu file xuất Fusion 360", initialdir=initial)
        root.destroy()
        return jsonify({"folder": chosen or ""})
    except Exception as exc:
        return jsonify({"error": f"Không mở được hộp thoại chọn thư mục: {exc}"}), 500


@app.post("/api/export/<export_id>/open-folder")
def api_export_open_folder(export_id: str):
    folder = EXPORT_RECORDS.get(export_id)
    if not folder or not folder.exists():
        return jsonify({"error": "Thư mục xuất không tồn tại."}), 404
    if sys.platform == "win32":
        try:
            subprocess.Popen(["explorer.exe", str(folder.resolve())])
            return jsonify({"opened": True, "path": str(folder.resolve())})
        except OSError as exc:
            return jsonify({"opened": False, "error": str(exc)}), 500
    return jsonify({"opened": False, "path": str(folder)})


if __name__ == "__main__":
    port = int(os.environ.get("SPLINTFIT_PORT", "8765"))
    print(f"SplintFit Studio đang chạy tại: http://127.0.0.1:{port}")
    # VTK/PyVista is not thread-safe on Windows; run single-threaded on main thread to prevent C++ crashes.
    app.run(host="127.0.0.1", port=port, debug=False, threaded=False)
