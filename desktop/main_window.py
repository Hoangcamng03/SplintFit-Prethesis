"""SplintFit Studio Desktop v3.0 — Native Windows Application (PyQt6 + PyVistaQt).

Features:
- 5-step clinical Wizard with 1 consistent primary CTA per step
- Auto Safe-Zone detection + 3 live 3D sliders (zero placement errors)
- 4 clinical preset card groups for doctors + collapsible advanced panel for technicians
- 2-piece staggered honeycomb splint with flared rims + live Explode & Quad wireframe view
- Clean 5-file Fusion 360 Form (All-Quad OBJ + mm scan reference) export with native Windows folder picker
"""
from __future__ import annotations

import math
import os
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

os.environ.setdefault("QT_API", "pyqt6")

ROOT_DIR = Path(__file__).resolve().parent.parent
ENGINE_DIR = ROOT_DIR / "engine"
EXPORTS_DIR = ROOT_DIR / "exports"
EXPORTS_DIR.mkdir(parents=True, exist_ok=True)

if str(ENGINE_DIR) not in sys.path:
    sys.path.insert(0, str(ENGINE_DIR))
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import numpy as np  # noqa: E402
import pyvista as pv  # noqa: E402
from PyQt6.QtCore import QSettings, Qt  # noqa: E402
from PyQt6.QtWidgets import (  # noqa: E402
    QApplication,
    QButtonGroup,
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QFileDialog,
    QFormLayout,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSlider,
    QSplitter,
    QStackedWidget,
    QToolButton,
    QVBoxLayout,
    QWidget,
)
from pyvistaqt import QtInteractor  # noqa: E402

from cast_template import hand_demo_mesh  # noqa: E402
from desktop.theme import STUDIO_QSS  # noqa: E402
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
    write_obj,
)

CLINICAL_PRESETS = {
    "fit": {
        "swollen": {"clearance": 2.5, "padding": 1.0},
        "standard": {"clearance": 1.5, "padding": 0.5},
        "snug": {"clearance": 1.3, "padding": 0.0},
    },
    "rigidity": {
        "light": {"thickness": 2.8},
        "medium": {"thickness": 3.2},
        "rigid": {"thickness": 4.0},
    },
    "vent": {
        "honeycomb": {"ventilation": True, "hole_pitch": 20.0, "hole_ratio": 0.58},
        "moderate": {"ventilation": True, "hole_pitch": 25.0, "hole_ratio": 0.48},
        "solid": {"ventilation": False, "hole_pitch": 24.0, "hole_ratio": 0.48},
    },
    "notch": {
        "wide": {"depth": 22.0},
        "mild": {"depth": 14.0},
        "straight": {"depth": 0.0},
    },
}

PRIMARY_BTN_LABELS = {
    0: "Tiếp tục chọn vùng →",
    1: "Tiếp tục thiết kế →",
    2: "Tạo mô hình nẹp 3D",
    3: "Sang bước xuất Fusion 360 →",
    4: "Xuất lưới cho Fusion 360 Form",
}


def _sanitize_name(value: str, default: str = "CASE-001") -> str:
    cleaned = re.sub(r"[^A-Za-z0-9_-]+", "_", (value or "").strip()).strip("_")
    return cleaned[:48] or default


def _quad_polydata(points: np.ndarray, quads: np.ndarray) -> pv.PolyData:
    faces = np.column_stack((np.full(len(quads), 4, dtype=np.int64), quads)).ravel()
    return pv.PolyData(np.asarray(points, dtype=float), faces)


def _ring_polydata(center: np.ndarray, axis_z: np.ndarray, radius: float, n: int = 48) -> pv.PolyData:
    z = axis_z / np.linalg.norm(axis_z)
    helper = np.array([1.0, 0.0, 0.0]) if abs(z[0]) < 0.8 else np.array([0.0, 1.0, 0.0])
    u = np.cross(z, helper)
    u /= np.linalg.norm(u)
    v = np.cross(z, u)
    angles = np.linspace(0.0, 2.0 * np.pi, n, endpoint=False)
    pts = center[None, :] + radius * (np.cos(angles)[:, None] * u[None, :] + np.sin(angles)[:, None] * v[None, :])
    lines = np.hstack(([n + 1], np.arange(n), [0]))
    return pv.PolyData(pts, lines=lines)


def _make_card(title: str | None = None) -> tuple[QFrame, QVBoxLayout]:
    frame = QFrame()
    frame.setProperty("class", "card")
    lay = QVBoxLayout(frame)
    lay.setContentsMargins(13, 12, 13, 12)
    lay.setSpacing(8)
    if title:
        lbl = QLabel(title)
        lbl.setProperty("class", "cardTitle")
        lbl.setWordWrap(True)
        lay.addWidget(lbl)
    return frame, lay


def _make_stat_box(label_text: str, value_text: str = "—") -> tuple[QFrame, QLabel]:
    box = QFrame()
    box.setProperty("class", "statBox")
    lay = QVBoxLayout(box)
    lay.setContentsMargins(9, 7, 9, 7)
    lay.setSpacing(2)
    k = QLabel(label_text)
    k.setProperty("class", "muted")
    v = QLabel(value_text)
    v.setStyleSheet("font-size: 14px; font-weight: 700; background: transparent;")
    lay.addWidget(k)
    lay.addWidget(v)
    return box, v


class SplintFitStudioWindow(QMainWindow):
    def __init__(self, offscreen: bool = False):
        super().__init__()
        self.offscreen = offscreen
        self.settings = QSettings("SplintFit", "SplintFitStudioDesktop")
        self.setWindowTitle("SplintFit Studio — Thiết kế nẹp 3D & Fusion 360 Form (Desktop v3.0)")
        self.resize(1380, 860)
        self.setMinimumSize(1060, 680)

        # Core state
        self.scan_data: dict | None = None
        self.active_mesh: pv.PolyData | None = None
        self.active_display: pv.PolyData | None = None
        self.active_boundaries: pv.PolyData | None = None
        self.source_name: str = ""
        self.safe_frame: dict | None = None
        self.landmarks: dict[str, list[float] | None] = {"proximal": None, "distal": None, "side": None}
        self.build_result: dict | None = None
        self.last_params: Parameters | None = None
        self.last_export_dir: Path | None = None
        self.current_step: int = 0
        self._syncing_sliders = False

        # Build UI
        self._build_ui()
        self.setStyleSheet(STUDIO_QSS)
        self._go_to_step(0)

    # ==================== UI Construction ====================
    def _build_ui(self):
        root = QWidget()
        self.setCentralWidget(root)
        main_lay = QVBoxLayout(root)
        main_lay.setContentsMargins(0, 0, 0, 0)
        main_lay.setSpacing(0)

        main_lay.addWidget(self._build_topbar())

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(self._build_viewport_panel())
        splitter.addWidget(self._build_wizard_panel())
        splitter.setSizes([880, 460])
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 1)
        main_lay.addWidget(splitter, 1)

    def _build_topbar(self) -> QWidget:
        bar = QWidget()
        bar.setObjectName("topbar")
        bar.setFixedHeight(60)
        h = QHBoxLayout(bar)
        h.setContentsMargins(16, 8, 16, 8)
        h.setSpacing(10)

        logo = QLabel("SF")
        logo.setObjectName("brandLogo")
        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        h.addWidget(logo)

        title_col = QVBoxLayout()
        title_col.setSpacing(0)
        row1 = QHBoxLayout()
        row1.setSpacing(6)
        t = QLabel("SplintFit Studio")
        t.setObjectName("brandTitle")
        b = QLabel("Desktop v3.0 • Fusion Form")
        b.setObjectName("badgePill")
        row1.addWidget(t)
        row1.addWidget(b)
        row1.addStretch()
        sub = QLabel("Thiết kế nẹp cổ tay–cẳng tay 3D cho Bác sĩ & Kỹ thuật viên")
        sub.setObjectName("brandSub")
        title_col.addLayout(row1)
        title_col.addWidget(sub)
        h.addLayout(title_col)

        h.addStretch(1)

        self.step_buttons: list[QPushButton] = []
        step_titles = ["1. Nạp Scan", "2. Chọn Vùng", "3. Thiết Kế", "4. Kiểm Tra", "5. Xuất Fusion 360"]
        for idx, text in enumerate(step_titles):
            btn = QPushButton(text)
            btn.setProperty("class", "stepPill")
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(lambda _checked=False, i=idx: self._go_to_step(i))
            self.step_buttons.append(btn)
            h.addWidget(btn)

        h.addStretch(1)

        self.case_id_input = QLineEdit("CASE-001")
        self.case_id_input.setFixedWidth(100)
        self.case_id_input.setToolTip("Mã ca thiết kế")
        self.hand_side_combo = QComboBox()
        self.hand_side_combo.addItems(["Tay trái", "Tay phải"])
        self.hand_side_combo.setFixedWidth(96)
        h.addWidget(self.case_id_input)
        h.addWidget(self.hand_side_combo)
        return bar

    def _build_viewport_panel(self) -> QWidget:
        wrap = QWidget()
        lay = QVBoxLayout(wrap)
        lay.setContentsMargins(12, 10, 8, 10)
        lay.setSpacing(8)

        # Top viewport toolbar
        top_bar = QFrame()
        top_bar.setObjectName("viewportToolbar")
        th = QHBoxLayout(top_bar)
        th.setContentsMargins(10, 6, 10, 6)
        self.scene_badge = QLabel("Chưa nạp dữ liệu quét — Mở mẫu thử hoặc chọn file STL/OBJ/PLY ở Bước 1")
        self.scene_badge.setStyleSheet("font-weight: 600; font-size: 12px; background: transparent;")
        th.addWidget(self.scene_badge, 1)
        for text, view in [("Vừa khung", "fit"), ("Mặt trước", "front"), ("Mặt bên", "side"), ("Dọc trục", "top")]:
            b = QPushButton(text)
            b.setStyleSheet("padding: 4px 10px; font-size: 12px;")
            b.clicked.connect(lambda _c=False, v=view: self._set_camera(v))
            th.addWidget(b)
        lay.addWidget(top_bar)

        # 3D Plotter
        if self.offscreen:
            self.plotter = pv.Plotter(off_screen=True)
            placeholder = QLabel("3D Viewport (Offscreen Test Mode)")
            placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
            placeholder.setStyleSheet("background-color: #EEF2F6; border: 1px solid #CBD5E1; border-radius: 10px; color: #64748B;")
            lay.addWidget(placeholder, 1)
        else:
            self.plotter = QtInteractor(wrap)
            self.plotter.set_background("#E8EEF5", top="#F8FAFC")
            try:
                self.plotter.enable_depth_peeling(4)
            except Exception:
                pass
            self.plotter.add_axes()
            lay.addWidget(self.plotter.interactor, 1)

        # Bottom layer & explode toolbar
        layer_bar = QFrame()
        layer_bar.setObjectName("layerBar")
        lh = QHBoxLayout(layer_bar)
        lh.setContentsMargins(12, 7, 12, 7)
        lh.setSpacing(12)

        self.chk_scan = QCheckBox("Chi quét")
        self.chk_scan.setChecked(True)
        self.chk_boundaries = QCheckBox("Biên hở")
        self.chk_boundaries.setChecked(True)
        self.chk_shell = QCheckBox("Vỏ nẹp 3D")
        self.chk_shell.setChecked(True)
        self.chk_quad = QCheckBox("Lưới Quad (Fusion Form)")
        self.chk_heatmap = QCheckBox("Độ thoáng mặt trong")

        for chk in (self.chk_scan, self.chk_boundaries, self.chk_shell, self.chk_quad, self.chk_heatmap):
            chk.toggled.connect(self._render_scene)
            lh.addWidget(chk)

        lh.addWidget(QLabel("Mờ chi:"))
        self.sl_opacity = QSlider(Qt.Orientation.Horizontal)
        self.sl_opacity.setRange(15, 100)
        self.sl_opacity.setValue(55)
        self.sl_opacity.setFixedWidth(78)
        self.sl_opacity.valueChanged.connect(self._render_scene)
        lh.addWidget(self.sl_opacity)

        lh.addWidget(QLabel("Tách 2 mảnh:"))
        self.sl_explode = QSlider(Qt.Orientation.Horizontal)
        self.sl_explode.setRange(0, 45)
        self.sl_explode.setValue(0)
        self.sl_explode.setFixedWidth(92)
        self.sl_explode.valueChanged.connect(self._render_scene)
        lh.addWidget(self.sl_explode)
        lh.addStretch()

        lay.addWidget(layer_bar)
        return wrap

    def _build_wizard_panel(self) -> QWidget:
        panel = QWidget()
        panel.setObjectName("wizardPanel")
        panel.setMinimumWidth(400)
        panel.setMaximumWidth(480)
        lay = QVBoxLayout(panel)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        # Inline status banner (never overlaps headings)
        self.status_banner = QLabel("")
        self.status_banner.setProperty("class", "statusBanner")
        self.status_banner.setWordWrap(True)
        self.status_banner.hide()
        banner_wrap = QWidget()
        banner_wrap.setStyleSheet("background: #FFFFFF;")
        bw = QVBoxLayout(banner_wrap)
        bw.setContentsMargins(16, 10, 16, 0)
        bw.addWidget(self.status_banner)
        lay.addWidget(banner_wrap)

        self.progress = QProgressBar()
        self.progress.setFixedHeight(4)
        self.progress.setTextVisible(False)
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        self.progress.hide()
        lay.addWidget(self.progress)

        self.stack = QStackedWidget()
        self.stack.addWidget(self._scroll_wrap(self._build_step1()))
        self.stack.addWidget(self._scroll_wrap(self._build_step2()))
        self.stack.addWidget(self._scroll_wrap(self._build_step3()))
        self.stack.addWidget(self._scroll_wrap(self._build_step4()))
        self.stack.addWidget(self._scroll_wrap(self._build_step5()))
        lay.addWidget(self.stack, 1)

        # Consistent single-primary-action footer
        footer = QWidget()
        footer.setObjectName("drawerFooter")
        fh = QHBoxLayout(footer)
        fh.setContentsMargins(16, 10, 16, 10)
        self.btn_prev = QPushButton("← Quay lại")
        self.btn_prev.clicked.connect(lambda: self._go_to_step(self.current_step - 1))
        self.btn_primary = QPushButton(PRIMARY_BTN_LABELS[0])
        self.btn_primary.setObjectName("primaryBtn")
        self.btn_primary.clicked.connect(self._on_primary_action)
        fh.addWidget(self.btn_prev)
        fh.addStretch()
        fh.addWidget(self.btn_primary)
        lay.addWidget(footer)
        return panel

    def _scroll_wrap(self, widget: QWidget) -> QScrollArea:
        sc = QScrollArea()
        sc.setWidgetResizable(True)
        sc.setWidget(widget)
        return sc

    def _step_header(self, lay: QVBoxLayout, tag: str, title: str, desc: str):
        t1 = QLabel(tag)
        t1.setProperty("class", "stepTag")
        t2 = QLabel(title)
        t2.setProperty("class", "stepTitle")
        t2.setWordWrap(True)
        t3 = QLabel(desc)
        t3.setProperty("class", "muted")
        t3.setWordWrap(True)
        lay.addWidget(t1)
        lay.addWidget(t2)
        lay.addWidget(t3)

    # ---------- Step 1: Load Scan ----------
    def _build_step1(self) -> QWidget:
        page = QWidget()
        page.setStyleSheet("background: #FFFFFF;")
        lay = QVBoxLayout(page)
        lay.setContentsMargins(16, 14, 16, 20)
        lay.setSpacing(10)
        self._step_header(
            lay,
            "BƯỚC 1 / 5",
            "Nạp file quét 3D cánh tay",
            "Hệ thống giữ nguyên bề mặt da thực tế, không tự vá lỗ (No Hole Filling) để đảm bảo an toàn giải phẫu.",
        )

        c1, l1 = _make_card("Mở file quét từ máy tính (KIRI Engine)")
        u_row = QHBoxLayout()
        u_row.addWidget(QLabel("Đơn vị file:"))
        self.unit_combo = QComboBox()
        self.unit_combo.addItem("Milimét (mm) — Mặc định", 1.0)
        self.unit_combo.addItem("Xentimét (cm) — Tự đổi ×10", 10.0)
        self.unit_combo.addItem("Mét (m) — Tự đổi ×1000", 1000.0)
        u_row.addWidget(self.unit_combo, 1)
        l1.addLayout(u_row)

        btn_open = QPushButton("📂 Chọn file .STL / .OBJ / .PLY trên máy…")
        btn_open.setProperty("class", "secondaryBtn")
        btn_open.clicked.connect(self._browse_scan_file)
        l1.addWidget(btn_open)

        self.chk_auto_build = QCheckBox("Tự động xác định 3 mốc & dựng sẵn nẹp 2 mảnh ngay khi nạp file")
        self.chk_auto_build.setChecked(True)
        l1.addWidget(self.chk_auto_build)
        lay.addWidget(c1)

        c2, l2 = _make_card("Hoặc dùng mẫu giải phẫu có sẵn (Thử nhanh)")
        hint = QLabel("Mô hình cẳng tay–cổ tay–bàn tay chuẩn (có thắt cổ tay, gò cái và mỏm trâm trụ).")
        hint.setProperty("class", "muted")
        hint.setWordWrap(True)
        l2.addWidget(hint)
        b_row = QHBoxLayout()
        b_hand = QPushButton("Mẫu cẳng tay – bàn tay")
        b_hand.setProperty("class", "secondaryBtn")
        b_hand.clicked.connect(lambda: self.load_demo("hand_forearm"))
        b_arm = QPushButton("Mẫu cẳng tay cơ bản")
        b_arm.clicked.connect(lambda: self.load_demo("simple_forearm"))
        b_row.addWidget(b_hand)
        b_row.addWidget(b_arm)
        l2.addLayout(b_row)
        lay.addWidget(c2)

        self.scan_summary_card, l3 = _make_card("Trạng thái bề mặt quét")
        grid = QGridLayout()
        grid.setSpacing(8)
        b1, self.st_tris = _make_stat_box("Độ chi tiết lưới")
        b2, self.st_span = _make_stat_box("Chiều dài mẫu")
        b3, self.st_bounds = _make_stat_box("Cạnh biên hở")
        b4, self.st_pieces = _make_stat_box("Số khối bề mặt")
        grid.addWidget(b1, 0, 0)
        grid.addWidget(b2, 0, 1)
        grid.addWidget(b3, 1, 0)
        grid.addWidget(b4, 1, 1)
        l3.addLayout(grid)

        self.piece_combo_label = QLabel("Chọn phần cánh tay chính (bỏ mảnh rác):")
        self.piece_combo_label.setProperty("class", "muted")
        self.piece_combo = QComboBox()
        self.piece_combo.currentIndexChanged.connect(self._on_piece_selected)
        self.piece_combo_label.hide()
        self.piece_combo.hide()
        l3.addWidget(self.piece_combo_label)
        l3.addWidget(self.piece_combo)

        self.scan_summary_card.hide()
        lay.addWidget(self.scan_summary_card)
        lay.addStretch()
        return page

    # ---------- Step 2: Safe-Zone Auto-Detection + 3 Live Sliders ----------
    def _build_step2(self) -> QWidget:
        page = QWidget()
        page.setStyleSheet("background: #FFFFFF;")
        lay = QVBoxLayout(page)
        lay.setContentsMargins(16, 14, 16, 20)
        lay.setSpacing(10)
        self._step_header(
            lay,
            "BƯỚC 2 / 5",
            "Chỉnh vùng đặt nẹp (Tự khóa vùng an toàn)",
            "Hệ thống tự nhận diện đoạn cẳng tay–cổ tay hợp lệ. Kéo 3 thanh trượt để chỉnh trực tiếp trên 3D — không lo đặt sai gây lỗi.",
        )

        c1, l1 = _make_card("Chỉnh trực tiếp trên mô hình 3D")
        self.safe_zone_pill = QLabel("✓ Vùng an toàn tự động: —")
        self.safe_zone_pill.setProperty("class", "metricPill")
        l1.addWidget(self.safe_zone_pill)

        # Slider 1: Proximal
        h1 = QHBoxLayout()
        h1.addWidget(QLabel("1. Đầu phía khuỷu tay (Vòng xanh)"))
        self.lbl_prox_val = QLabel("+0 mm")
        self.lbl_prox_val.setStyleSheet("color: #0F766E; font-weight: 700; background: transparent;")
        h1.addStretch()
        h1.addWidget(self.lbl_prox_val)
        l1.addLayout(h1)
        self.sl_prox = QSlider(Qt.Orientation.Horizontal)
        self.sl_prox.setRange(0, 100)
        self.sl_prox.valueChanged.connect(lambda: self._sync_landmarks_from_sliders("prox"))
        l1.addWidget(self.sl_prox)

        # Slider 2: Distal
        h2 = QHBoxLayout()
        h2.addWidget(QLabel("2. Đầu phía bàn tay (Vòng cam)"))
        self.lbl_dist_val = QLabel("100 mm")
        self.lbl_dist_val.setStyleSheet("color: #0F766E; font-weight: 700; background: transparent;")
        h2.addStretch()
        h2.addWidget(self.lbl_dist_val)
        l1.addLayout(h2)
        self.sl_dist = QSlider(Qt.Orientation.Horizontal)
        self.sl_dist.setRange(30, 200)
        self.sl_dist.valueChanged.connect(lambda: self._sync_landmarks_from_sliders("dist"))
        l1.addWidget(self.sl_dist)

        # Slider 3: Seam angle
        h3 = QHBoxLayout()
        h3.addWidget(QLabel("3. Xoay hướng tách 2 mảnh (Chấm tím)"))
        self.lbl_ang_val = QLabel("0°")
        self.lbl_ang_val.setStyleSheet("color: #0F766E; font-weight: 700; background: transparent;")
        h3.addStretch()
        h3.addWidget(self.lbl_ang_val)
        l1.addLayout(h3)
        self.sl_ang = QSlider(Qt.Orientation.Horizontal)
        self.sl_ang.setRange(0, 180)
        self.sl_ang.setSingleStep(5)
        self.sl_ang.valueChanged.connect(lambda: self._sync_landmarks_from_sliders("ang"))
        l1.addWidget(self.sl_ang)

        self.span_live_pill = QLabel("Chiều dài nẹp đang chọn: —")
        self.span_live_pill.setProperty("class", "metricPill")
        l1.addWidget(self.span_live_pill)

        btn_reset = QPushButton("Đặt lại vùng an toàn mặc định")
        btn_reset.clicked.connect(self._reset_safe_sliders)
        btn_rebuild_here = QPushButton("Cập nhật lại nẹp 3D theo vị trí vừa chỉnh")
        btn_rebuild_here.setProperty("class", "secondaryBtn")
        btn_rebuild_here.clicked.connect(lambda: self.run_build(stay_on_step=True))
        l1.addWidget(btn_rebuild_here)
        l1.addWidget(btn_reset)
        lay.addWidget(c1)
        lay.addStretch()
        return page

    # ---------- Step 3: Clinical Presets + Advanced Accordion ----------
    def _build_step3(self) -> QWidget:
        page = QWidget()
        page.setStyleSheet("background: #FFFFFF;")
        lay = QVBoxLayout(page)
        lay.setContentsMargins(16, 14, 16, 20)
        lay.setSpacing(10)
        self._step_header(
            lay,
            "BƯỚC 3 / 5",
            "Chọn cấu hình nẹp lâm sàng",
            "Chỉ cần chọn 4 nhóm trực quan theo tình trạng bệnh nhân — không cần nhớ thông số CAD.",
        )

        self.preset_groups: dict[str, QButtonGroup] = {}
        self._add_preset_card(
            lay,
            "0. Cấu trúc nẹp (1 mảnh / 2 mảnh)",
            "mode",
            [("bivalve", "Nẹp 2 mảnh tháo lắp\nCó 3 dải dây đai (Khuyên dùng)"), ("single", "Nẹp 1 mảnh máng hở\nĐeo kiểu máng")],
            "bivalve",
        )
        self._add_preset_card(
            lay,
            "1. Tình trạng tay (Độ ôm & lót đệm)",
            "fit",
            [("swollen", "Đang sưng\nThoáng + lót dày"), ("standard", "Ổn định\nVừa tiêu chuẩn"), ("snug", "Ôm sát\nKhông lót mút")],
            "standard",
        )
        self._add_preset_card(
            lay,
            "2. Độ cứng vỏ nẹp",
            "rigidity",
            [("light", "Nhẹ\nDày 2,8 mm"), ("medium", "Tiêu chuẩn\nDày 3,2 mm"), ("rigid", "Cứng chắc\nDày 4,0 mm")],
            "medium",
        )
        self._add_preset_card(
            lay,
            "3. Kiểu lưới thoáng khí",
            "vent",
            [("honeycomb", "Tổ ong thoáng\nSo le thoáng cao"), ("moderate", "Thoáng vừa\nThành dày hơn"), ("solid", "Vỏ kín\nKhông đục lỗ")],
            "honeycomb",
        )
        self._add_preset_card(
            lay,
            "4. Đường mở đầu bàn tay",
            "notch",
            [("wide", "Mở rộng\nGập cổ tay"), ("mild", "Vừa phải\nKhoét nhẹ"), ("straight", "Cắt thẳng\nKhuyên cho Form")],
            "wide",
        )

        self.clinical_summary = QLabel("")
        self.clinical_summary.setProperty("class", "metricPill")
        self.clinical_summary.setWordWrap(True)
        lay.addWidget(self.clinical_summary)

        # Collapsible Advanced Technician Section
        adv_toggle = QToolButton()
        adv_toggle.setText("▶  ⚙️ Tinh chỉnh nâng cao (Dành cho Kỹ thuật viên)")
        adv_toggle.setProperty("class", "accordionBtn")
        adv_toggle.setCheckable(True)
        adv_toggle.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        lay.addWidget(adv_toggle)

        adv_frame, adv_v = _make_card()
        form = QFormLayout()
        form.setSpacing(7)

        self.sp_mode = QComboBox()
        self.sp_mode.addItem("Nẹp 2 mảnh tháo lắp", "bivalve")
        self.sp_mode.addItem("Nẹp 1 mảnh máng hở", "single")
        self.sp_mode.currentIndexChanged.connect(self._update_clinical_summary)
        form.addRow("Cấu trúc nẹp:", self.sp_mode)

        self.sp_clearance = self._dspin(0.5, 6.0, 1.5, 0.25, " mm")
        self.sp_padding = self._dspin(0.0, 5.0, 0.5, 0.25, " mm")
        self.sp_thickness = self._dspin(2.0, 6.0, 3.2, 0.2, " mm")
        self.sp_flare = self._dspin(0.0, 3.5, 1.4, 0.2, " mm")
        self.sp_seam = self._dspin(2.0, 12.0, 4.0, 0.5, " mm")
        self.sp_vent = QCheckBox("Bật lỗ thoáng khí lưới tổ ong so le")
        self.sp_vent.setChecked(True)
        self.sp_pitch = self._dspin(16.0, 38.0, 20.0, 1.0, " mm")
        self.sp_ratio = self._dspin(0.25, 0.65, 0.58, 0.02, "")
        self.sp_notch_depth = self._dspin(0.0, 45.0, 22.0, 1.0, " mm")
        self.sp_notch_angle = self._dspin(-180.0, 180.0, 0.0, 15.0, "°")

        form.addRow("Khoảng hở thoáng da:", self.sp_clearance)
        form.addRow("Độ dày lớp lót mút:", self.sp_padding)
        form.addRow("Độ dày thành nhựa:", self.sp_thickness)
        form.addRow("Độ loe nhẹ mép 2 đầu:", self.sp_flare)
        form.addRow("Khe hở tách 2 mảnh:", self.sp_seam)
        form.addRow(self.sp_vent)
        form.addRow("Khoảng cách tâm lỗ:", self.sp_pitch)
        form.addRow("Độ mở lỗ trên ô:", self.sp_ratio)
        form.addRow("Độ sâu đường mở bàn tay:", self.sp_notch_depth)
        form.addRow("Hướng xoay góc mở (°):", self.sp_notch_angle)

        adv_v.addLayout(form)
        adv_frame.hide()
        lay.addWidget(adv_frame)

        def _toggle_adv(checked: bool):
            adv_frame.setVisible(checked)
            adv_toggle.setText(("▼  " if checked else "▶  ") + "⚙️ Tinh chỉnh nâng cao (Dành cho Kỹ thuật viên)")

        adv_toggle.toggled.connect(_toggle_adv)
        self._update_clinical_summary()
        lay.addStretch()
        return page

    def _dspin(self, lo: float, hi: float, val: float, step: float, suffix: str) -> QDoubleSpinBox:
        w = QDoubleSpinBox()
        w.setRange(lo, hi)
        w.setSingleStep(step)
        w.setDecimals(2 if step < 0.5 else 1)
        w.setValue(val)
        if suffix:
            w.setSuffix(suffix)
        w.valueChanged.connect(self._update_clinical_summary)
        return w

    def _add_preset_card(self, parent_lay: QVBoxLayout, title: str, group_key: str, items: list[tuple[str, str]], default_val: str):
        card, cl = _make_card(title)
        row = QHBoxLayout()
        row.setSpacing(6)
        grp = QButtonGroup(self)
        grp.setExclusive(True)
        for val, label in items:
            btn = QPushButton(label)
            btn.setCheckable(True)
            btn.setProperty("class", "presetCard")
            if val == default_val:
                btn.setChecked(True)
            btn.clicked.connect(lambda _c=False, gk=group_key, v=val: self._apply_preset(gk, v))
            grp.addButton(btn)
            row.addWidget(btn)
        self.preset_groups[group_key] = grp
        cl.addLayout(row)
        parent_lay.addWidget(card)

    # ---------- Step 4: Inspect ----------
    def _build_step4(self) -> QWidget:
        page = QWidget()
        page.setStyleSheet("background: #FFFFFF;")
        lay = QVBoxLayout(page)
        lay.setContentsMargins(16, 14, 16, 20)
        lay.setSpacing(10)
        self._step_header(
            lay,
            "BƯỚC 4 / 5",
            "Kiểm tra mô hình 3D & Lưới Form",
            "Dùng thanh phía dưới khung 3D để kéo Tách 2 mảnh xem mặt trong và bật Lưới Quad (Fusion Form).",
        )

        grid = QGridLayout()
        grid.setSpacing(8)
        b1, self.res_len = _make_stat_box("Chiều dài nẹp")
        b2, self.res_quads = _make_stat_box("Lưới Quad (Fusion)")
        b3, self.res_holes = _make_stat_box("Lỗ tổ ong / Khe đai")
        b4, self.res_clear = _make_stat_box("Độ hở mặt trong")
        grid.addWidget(b1, 0, 0)
        grid.addWidget(b2, 0, 1)
        grid.addWidget(b3, 1, 0)
        grid.addWidget(b4, 1, 1)
        lay.addLayout(grid)

        c_chk, self.checks_layout = _make_card("Kiểm tra an toàn hình học")
        lay.addWidget(c_chk)

        c_msg, l_msg = _make_card("Ghi chú cho Autodesk Fusion 360 Form")
        self.lbl_notes = QLabel("Chưa tạo mô hình nẹp.")
        self.lbl_notes.setProperty("class", "muted")
        self.lbl_notes.setWordWrap(True)
        l_msg.addWidget(self.lbl_notes)
        lay.addWidget(c_msg)
        lay.addStretch()
        return page

    # ---------- Step 5: Export to Fusion 360 Form ----------
    def _build_step5(self) -> QWidget:
        page = QWidget()
        page.setStyleSheet("background: #FFFFFF;")
        lay = QVBoxLayout(page)
        lay.setContentsMargins(16, 14, 16, 20)
        lay.setSpacing(10)
        self._step_header(
            lay,
            "BƯỚC 5 / 5",
            "Xuất lưới sang Autodesk Fusion 360 Form",
            "Chọn thư mục lưu trực tiếp trên Windows rồi nhấn nút xuất ở góc dưới để tạo đúng 5 file mesh chuẩn cho Fusion 360.",
        )

        c_dir, l_dir = _make_card("Chọn nơi lưu file xuất")
        saved_dir = str(self.settings.value("output_dir", str(Path.home() / "Desktop")))
        row_dir = QHBoxLayout()
        self.export_dir_input = QLineEdit(saved_dir)
        btn_browse = QPushButton("📁 Chọn thư mục…")
        btn_browse.setProperty("class", "secondaryBtn")
        btn_browse.clicked.connect(self._browse_export_dir)
        row_dir.addWidget(self.export_dir_input, 1)
        row_dir.addWidget(btn_browse)
        l_dir.addLayout(row_dir)

        q_row = QHBoxLayout()
        for label, path in [
            ("Desktop", Path.home() / "Desktop"),
            ("Downloads", Path.home() / "Downloads"),
            ("Documents", Path.home() / "Documents"),
        ]:
            b = QPushButton(label)
            b.setStyleSheet("padding: 4px 10px; font-size: 12px;")
            b.clicked.connect(lambda _c=False, p=str(path): self._set_export_dir(p))
            q_row.addWidget(b)
        q_row.addStretch()
        l_dir.addLayout(q_row)
        lay.addWidget(c_dir)

        c_files, l_files = _make_card("5 file mesh mặc định cho Fusion 360 Form")
        info = QLabel(
            "Đặt tên tự động theo Mã ca (ví dụ Mã ca = A):\n"
            "• A-1.obj & A-2.obj — Nền All-Quad trơn (kéo Edit Form mượt nhất)\n"
            "• A-1_holes.obj & A-2_holes.obj — Bản All-Quad đã có lỗ tổ ong\n"
            "• A_scan.stl — Cánh tay gốc cùng hệ tọa độ mm để đối chiếu khe hở"
        )
        info.setProperty("class", "muted")
        info.setWordWrap(True)
        l_files.addWidget(info)

        self.chk_export_full = QCheckBox("Kèm thêm STL in 3D, báo cáo JSON & trang xem 3D (tùy chọn)")
        l_files.addWidget(self.chk_export_full)

        self.export_result_lbl = QLabel("")
        self.export_result_lbl.setProperty("class", "metricPill")
        self.export_result_lbl.setWordWrap(True)
        self.export_result_lbl.hide()
        l_files.addWidget(self.export_result_lbl)

        self.btn_open_exported = QPushButton("📂 Mở thư mục vừa xuất trong Windows Explorer")
        self.btn_open_exported.setProperty("class", "secondaryBtn")
        self.btn_open_exported.clicked.connect(self._open_exported_folder)
        self.btn_open_exported.hide()
        l_files.addWidget(self.btn_open_exported)
        lay.addWidget(c_files)

        c_guide, l_guide = _make_card("Hướng dẫn nhanh 6 bước trong Fusion 360 Form")
        steps_txt = (
            "1. Preferences → Mesh: tắt Triangulate mesh polygons. Đặt đơn vị mm.\n"
            "2. Create Form → Insert Mesh → chọn <MãCa>-1.obj (Millimeter, giữ tọa độ gốc).\n"
            "3. Utilities/Modify → Convert → Quad Mesh to T-Splines.\n"
            "4. Chèn <MãCa>_scan.stl để soi khe hở, dùng Edit Form kéo chỉnh → Finish Form.\n"
            "5. Tab Surface → Thicken đẩy RA NGOÀI bằng độ dày đã chọn.\n"
            "6. Tab Solid → Fillet bo tròn mép → Lưu .f3d và xuất .stl in 3D."
        )
        guide_lbl = QLabel(steps_txt)
        guide_lbl.setProperty("class", "muted")
        guide_lbl.setWordWrap(True)
        l_guide.addWidget(guide_lbl)
        lay.addWidget(c_guide)
        lay.addStretch()
        return page

    # ==================== Actions & State Logic ====================
    def _set_status(self, msg: str, kind: str = "info"):
        if not msg:
            self.status_banner.hide()
            return
        self.status_banner.setText(msg)
        self.status_banner.setProperty("kind", kind)
        self.status_banner.style().unpolish(self.status_banner)
        self.status_banner.style().polish(self.status_banner)
        self.status_banner.show()

    def _go_to_step(self, step_idx: int):
        if step_idx > 0 and self.active_mesh is None:
            self._set_status("Hãy nạp file quét 3D hoặc mở mẫu thử ở Bước 1 trước.", "info")
            return
        self.current_step = max(0, min(4, step_idx))
        self.stack.setCurrentIndex(self.current_step)
        self.btn_prev.setVisible(self.current_step > 0)
        self.btn_primary.setText(PRIMARY_BTN_LABELS[self.current_step])
        for i, btn in enumerate(self.step_buttons):
            btn.setProperty("active", i == self.current_step)
            btn.setProperty("done", i < self.current_step)
            btn.style().unpolish(btn)
            btn.style().polish(btn)

    def _on_primary_action(self):
        if self.current_step == 0:
            self._go_to_step(1)
        elif self.current_step == 1:
            self._go_to_step(2)
        elif self.current_step == 2:
            self.run_build()
        elif self.current_step == 3:
            self._go_to_step(4)
        elif self.current_step == 4:
            self.run_export()

    def _apply_preset(self, group_key: str, val: str):
        if group_key == "mode":
            idx = self.sp_mode.findData(val)
            if idx >= 0:
                self.sp_mode.setCurrentIndex(idx)
            self._update_clinical_summary()
            return
        cfg = CLINICAL_PRESETS.get(group_key, {}).get(val)
        if not cfg:
            return
        if group_key == "fit":
            self.sp_clearance.setValue(cfg["clearance"])
            self.sp_padding.setValue(cfg["padding"])
        elif group_key == "rigidity":
            self.sp_thickness.setValue(cfg["thickness"])
        elif group_key == "vent":
            self.sp_vent.setChecked(cfg["ventilation"])
            self.sp_pitch.setValue(cfg["hole_pitch"])
            self.sp_ratio.setValue(cfg["hole_ratio"])
        elif group_key == "notch":
            self.sp_notch_depth.setValue(cfg["depth"])
        self._update_clinical_summary()

    def _update_clinical_summary(self):
        mode = "Nẹp 2 mảnh" if self.sp_mode.currentData() == "bivalve" else "Nẹp 1 mảnh"
        self.clinical_summary.setText(
            f"{mode} • Hở da {self.sp_clearance.value():.1f} mm • Lót {self.sp_padding.value():.1f} mm • "
            f"Dày {self.sp_thickness.value():.1f} mm • Loe mép {self.sp_flare.value():.1f} mm"
        )

    def _browse_scan_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Chọn file quét 3D từ KIRI Engine",
            str(Path.home() / "Downloads"),
            "3D Mesh (*.stl *.obj *.ply);;All Files (*)",
        )
        if path:
            self.load_scan_file(path, float(self.unit_combo.currentData()))

    def load_demo(self, kind: str = "hand_forearm"):
        mesh = demo_mesh() if kind == "simple_forearm" else hand_demo_mesh()
        name = "Mau_thu_cang_tay_co_ban.stl" if kind == "simple_forearm" else "Mau_thu_cang_tay_co_tay_ban_tay.stl"
        self._activate_scan(mesh, name)
        self._set_status("Đã nạp mẫu thử & tự khóa vùng an toàn cổ tay. Nhấn 'Tiếp tục chọn vùng →'.", "success")

    def load_scan_file(self, path: str, scale_mm: float = 1.0):
        try:
            self.progress.show()
            self.progress.setValue(25)
            QApplication.processEvents()
            mesh = read_mesh(path, scale=scale_mm)
            self._activate_scan(mesh, Path(path).name)
            self._set_status(f"Đã nạp {Path(path).name} & tự động khóa vùng an toàn cổ tay.", "success")
        except Exception as exc:
            self._set_status(str(exc), "error")
        finally:
            self.progress.hide()

    def _activate_scan(self, mesh: pv.PolyData, name: str):
        self.source_name = name
        self.scan_data = prepare_scan(mesh)
        self.piece_combo.blockSignals(True)
        self.piece_combo.clear()
        pieces = self.scan_data["pieces"]
        for i, p in enumerate(pieces):
            self.piece_combo.addItem(f"Khối #{i + 1} ({p['triangles']:,} mặt)", p["id"])
        if len(pieces) > 1:
            self.piece_combo.addItem("Giữ tất cả các khối", "all")
            self.piece_combo_label.show()
            self.piece_combo.show()
        else:
            self.piece_combo_label.hide()
            self.piece_combo.hide()
        self.piece_combo.blockSignals(False)

        active = pieces[0]["mesh"] if pieces else mesh
        self._set_active_mesh(active)

    def _on_piece_selected(self):
        if not self.scan_data:
            return
        pid = self.piece_combo.currentData()
        if pid == "all":
            self._set_active_mesh(self.scan_data["source"])
        else:
            found = next((p for p in self.scan_data["pieces"] if p["id"] == pid), None)
            if found:
                self._set_active_mesh(found["mesh"])

    def _set_active_mesh(self, mesh: pv.PolyData):
        self.active_mesh = mesh
        self.active_display = display_mesh(mesh, target=45000)
        self.active_boundaries = mesh.extract_feature_edges(
            boundary_edges=True, non_manifold_edges=True, feature_edges=False, manifold_edges=False
        )
        self.build_result = None
        self.sl_explode.setValue(0)

        st = mesh_stats(mesh)
        sugg = suggested_points(mesh)
        self.safe_frame = sugg.get("safe_frame")
        self.landmarks = {"proximal": sugg["proximal"], "distal": sugg["distal"], "side": sugg["side"]}

        self.st_tris.setText(f"{st['triangles']:,} mặt")
        self.st_span.setText(f"{sugg['span_mm']:.1f} mm")
        self.st_bounds.setText(str(st["boundary_edges"]))
        self.st_pieces.setText(str(self.scan_data["total_pieces"] if self.scan_data else 1))
        self.scan_summary_card.show()
        self.scene_badge.setText(f"{self.source_name} • {st['triangles']:,} mặt")

        self._reset_safe_sliders()
        self._render_scene(reset_cam=True)
        if self.chk_auto_build.isChecked():
            ok = self.run_build(stay_on_step=True)
            if ok:
                self._go_to_step(1)
                self._set_status(
                    "Đã tự động xác định 3 mốc (1. Đầu khuỷu, 2. Cổ tay, 3. Mặt nẹp) và dựng sẵn nẹp 2 mảnh! Bạn có thể kéo 3 thanh trượt để chỉnh lại vị trí.",
                    "success",
                )

    def _reset_safe_sliders(self):
        sf = self.safe_frame
        if not sf:
            return
        span = max(30, int(round(sf["safe_max_mm"] - sf["safe_min_mm"])))
        self._syncing_sliders = True
        self.sl_prox.setRange(0, max(0, span - 30))
        self.sl_prox.setValue(0)
        self.sl_dist.setRange(30, span)
        self.sl_dist.setValue(span)
        self.sl_ang.setValue(0)
        self._syncing_sliders = False
        self.safe_zone_pill.setText(f"✓ Vùng an toàn tự động: dài tối đa {span} mm")
        self._sync_landmarks_from_sliders()

    def _sync_landmarks_from_sliders(self, changed: str | None = None):
        if self._syncing_sliders or not self.safe_frame:
            return
        sf = self.safe_frame
        p_rel = self.sl_prox.value()
        d_rel = self.sl_dist.value()
        if d_rel - p_rel < 30:
            self._syncing_sliders = True
            if changed == "prox":
                p_rel = max(0, d_rel - 30)
                self.sl_prox.setValue(p_rel)
            else:
                d_rel = min(self.sl_dist.maximum(), p_rel + 30)
                self.sl_dist.setValue(d_rel)
            self._syncing_sliders = False

        z_start = sf["safe_min_mm"] + p_rel
        z_end = sf["safe_min_mm"] + d_rel
        z_mid = 0.5 * (z_start + z_end)
        ang = math.radians(self.sl_ang.value())
        r_side = (sf.get("radius_est_mm") or 30.0) + 12.0

        o = np.asarray(sf["origin"], dtype=float)
        z = np.asarray(sf["axis_z"], dtype=float)
        x = np.asarray(sf["axis_x"], dtype=float)
        y = np.asarray(sf["axis_y"], dtype=float)

        self.landmarks["proximal"] = (o + z * z_start).tolist()
        self.landmarks["distal"] = (o + z * z_end).tolist()
        self.landmarks["side"] = (o + z * z_mid + (math.cos(ang) * x + math.sin(ang) * y) * r_side).tolist()

        self.lbl_prox_val.setText(f"+{p_rel} mm")
        self.lbl_dist_val.setText(f"{d_rel} mm")
        self.lbl_ang_val.setText(f"{self.sl_ang.value()}°")
        self.span_live_pill.setText(f"Chiều dài nẹp đang chọn: {d_rel - p_rel:.0f} mm")
        self._render_scene()

    def current_parameters(self) -> Parameters:
        return Parameters(
            axis="AUTO",
            proximal_point=self.landmarks["proximal"],
            distal_point=self.landmarks["distal"],
            side_point=self.landmarks["side"],
            splint_mode=str(self.sp_mode.currentData()),
            cast_template=True,
            clearance_mm=float(self.sp_clearance.value()),
            padding_mm=float(self.sp_padding.value()),
            thickness_mm=float(self.sp_thickness.value()),
            rim_flare_mm=float(self.sp_flare.value()),
            seam_gap_mm=float(self.sp_seam.value()),
            ventilation=bool(self.sp_vent.isChecked()),
            hole_pitch_mm=float(self.sp_pitch.value()),
            hole_ratio=float(self.sp_ratio.value()),
            hand_notch_depth_mm=float(self.sp_notch_depth.value()),
            hand_notch_angle_deg=float(self.sp_notch_angle.value()),
            max_sampled_deviation_mm=1.5,
            auto_orient_open_normals=True,
        )

    def run_build(self, stay_on_step: bool = False) -> bool:
        if self.active_mesh is None:
            self._set_status("Chưa nạp dữ liệu quét.", "error")
            return False
        self.progress.show()
        self.progress.setValue(10)
        self._set_status("Đang dựng nẹp 2 mảnh lưới tổ ong, loe mép & lưới Quad cho Fusion Form…", "info")
        QApplication.processEvents()
        try:
            params = self.current_parameters()

            def _prog(pct: int, _msg: str):
                self.progress.setValue(int(pct))
                QApplication.processEvents()

            res = engine_build(self.active_mesh, params, progress=_prog)
            self.build_result = res
            self.last_params = params
            self._populate_inspect(res["report"])
            self._render_scene()
            if not stay_on_step:
                self._go_to_step(3)
            self._set_status("Đã tạo xong nẹp 2 mảnh và lưới Quad sẵn sàng cho Fusion 360 Form!", "success")
            return True
        except (DesignProblem, ValueError) as exc:
            self._set_status(str(exc), "error")
            return False
        except Exception as exc:
            self._set_status(f"Lỗi xử lý hình học: {exc}", "error")
            return False
        finally:
            self.progress.hide()

    def _populate_inspect(self, r: dict):
        self.res_len.setText(f"{r.get('length_mm', 0):.1f} mm")
        self.res_quads.setText(f"{r.get('quad_faces', 0):,} ô")
        self.res_holes.setText(f"{r.get('ventilation_holes', 0)} lỗ • {r.get('strap_slots', 0)} khe")
        self.res_clear.setText(f"{r.get('nominal_clearance_min_mm', 0):.1f}–{r.get('nominal_clearance_max_mm', 0):.1f} mm")

        # Clear old check rows (keep cardTitle at index 0)
        while self.checks_layout.count() > 1:
            item = self.checks_layout.takeAt(1)
            if item.widget():
                item.widget().deleteLater()

        badge_map = {
            "PASSED": ("Đạt", "#DCFCE7", "#166534"),
            "PASSED_SAMPLED": ("Đạt", "#DCFCE7", "#166534"),
            "FAILED": ("Cần chỉnh", "#FEE2E2", "#991B1B"),
            "NOT_ENTERED": ("Chưa đo", "#E2E8F0", "#475569"),
            "NOT_VALIDATED": ("Chưa thử lâm sàng", "#FEF3C7", "#92400E"),
        }
        for chk in r.get("technical_checks", []):
            row_w = QWidget()
            row_w.setStyleSheet("background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 7px;")
            rh = QHBoxLayout(row_w)
            rh.setContentsMargins(8, 5, 8, 5)
            lbl = QLabel(chk["name"])
            lbl.setStyleSheet("border: none; font-size: 11.5px;")
            lbl.setWordWrap(True)
            txt, bg, fg = badge_map.get(chk["status"], (chk["status"], "#E2E8F0", "#334155"))
            pill = QLabel(txt)
            pill.setStyleSheet(f"border: none; background: {bg}; color: {fg}; border-radius: 8px; padding: 2px 7px; font-size: 10.5px; font-weight: 700;")
            rh.addWidget(lbl, 1)
            rh.addWidget(pill)
            self.checks_layout.addWidget(row_w)

        msgs = list(dict.fromkeys(r.get("messages", [])))
        self.lbl_notes.setText("\n• ".join([""] + msgs).strip())

    def _browse_export_dir(self):
        current = self.export_dir_input.text().strip() or str(Path.home() / "Desktop")
        chosen = QFileDialog.getExistingDirectory(self, "Chọn thư mục lưu file xuất Fusion 360", current)
        if chosen:
            self._set_export_dir(chosen)

    def _set_export_dir(self, path_str: str):
        self.export_dir_input.setText(path_str)
        self.settings.setValue("output_dir", path_str)

    def run_export(self, override_dir: str | None = None) -> Path | None:
        if not self.build_result or not self.last_params or self.active_mesh is None:
            self._set_status("Hãy tạo mô hình nẹp 3D ở Bước 3 trước khi xuất.", "error")
            self._go_to_step(2)
            return None

        base_str = (override_dir if override_dir is not None else self.export_dir_input.text()).strip()
        base_dir = Path(base_str).expanduser() if base_str else EXPORTS_DIR
        base_dir.mkdir(parents=True, exist_ok=True)
        self.settings.setValue("output_dir", str(base_dir))

        case_id = _sanitize_name(self.case_id_input.text())
        folder_name = f"{case_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        target_dir = base_dir / folder_name

        try:
            if self.chk_export_full.isChecked():
                metadata = {
                    "case_id": case_id,
                    "side": self.hand_side_combo.currentText(),
                    "source_name": self.source_name,
                    "exported_at": datetime.now().isoformat(timespec="seconds"),
                    "app": "SplintFit Studio Desktop v3.0",
                }
                exported = export_bundle(target_dir, self.active_mesh, self.build_result, self.last_params, metadata)
            else:
                target_dir.mkdir(parents=True, exist_ok=False)
                pieces = self.build_result.get("pieces") or [self.build_result]
                for idx, piece in enumerate(pieces):
                    suffix = "" if len(pieces) == 1 else f"-{idx + 1}"
                    if piece.get("quad") is not None:
                        write_obj(target_dir / f"{case_id}{suffix}.obj", *piece["quad"])
                    if piece.get("perforated_quad") is not None:
                        write_obj(target_dir / f"{case_id}{suffix}_holes.obj", *piece["perforated_quad"])
                self.active_mesh.save(target_dir / f"{case_id}_scan.stl")
                exported = target_dir

            self.last_export_dir = exported
            files = sorted([p.name for p in exported.iterdir() if p.is_file()])
            self.export_result_lbl.setText(f"✓ Đã xuất {len(files)} file tại:\n{exported}")
            self.export_result_lbl.show()
            self.btn_open_exported.show()
            self._set_status("Đã xuất lưới Fusion 360 Form thành công!", "success")
            return exported
        except Exception as exc:
            self._set_status(f"Lỗi xuất file: {exc}", "error")
            return None

    def _open_exported_folder(self):
        if self.last_export_dir and self.last_export_dir.exists() and sys.platform == "win32":
            subprocess.Popen(["explorer.exe", str(self.last_export_dir.resolve())])

    # ==================== 3D Rendering ====================
    def _render_scene(self, reset_cam: bool = False):
        if self.offscreen:
            return
        self.plotter.clear()
        self.plotter.set_background("#E8EEF5", top="#F8FAFC")

        # Render solid 2-piece splint FIRST, translucent skin LAST so alpha sorting never hides the splint!
        if self.build_result:
            pieces = self.build_result.get("pieces") or [self.build_result]
            explode = float(self.sl_explode.value())
            sep_dir = np.array([1.0, 0.0, 0.0])
            if self.landmarks["proximal"] and self.landmarks["distal"] and self.landmarks["side"]:
                a = np.asarray(self.landmarks["proximal"], dtype=float)
                b = np.asarray(self.landmarks["distal"], dtype=float)
                s = np.asarray(self.landmarks["side"], dtype=float)
                z = (b - a) / max(np.linalg.norm(b - a), 1e-6)
                x = s - 0.5 * (a + b)
                x -= z * (x @ z)
                if np.linalg.norm(x) > 1e-4:
                    sep_dir = x / np.linalg.norm(x)

            colors = ["#0D9488", "#0284C7"]
            quad_colors = ["#F59E0B", "#7C3AED"]
            for idx, piece in enumerate(pieces):
                shift = sep_dir * (explode if idx == 0 else -explode) if len(pieces) > 1 else np.zeros(3)
                if self.chk_shell.isChecked() and piece.get("shell") is not None:
                    sh = piece["shell"].copy()
                    if explode > 0:
                        sh.translate(shift, inplace=True)
                    self.plotter.add_mesh(
                        sh,
                        color=colors[idx % 2],
                        smooth_shading=True,
                        ambient=0.22,
                        diffuse=0.78,
                        specular=0.35,
                        specular_power=24,
                    )
                if self.chk_quad.isChecked() and piece.get("quad") is not None:
                    qm = _quad_polydata(*piece["quad"])
                    if explode > 0:
                        qm.translate(shift, inplace=True)
                    self.plotter.add_mesh(qm, style="wireframe", color=quad_colors[idx % 2], line_width=1.5)
                if self.chk_heatmap.isChecked() and piece.get("inner") is not None:
                    inn = piece["inner"].copy()
                    if explode > 0:
                        inn.translate(shift, inplace=True)
                    self.plotter.add_mesh(inn, scalars="nominal_clearance_mm", cmap="turbo", show_scalar_bar=False)

        if self.active_display is not None and self.chk_scan.isChecked():
            self.plotter.add_mesh(
                self.active_display,
                color="#E6D6C7",
                opacity=self.sl_opacity.value() / 100.0,
                smooth_shading=True,
                ambient=0.25,
                diffuse=0.75,
            )

        if self.active_boundaries is not None and self.active_boundaries.n_cells > 0 and self.chk_boundaries.isChecked():
            self.plotter.add_mesh(self.active_boundaries, color="#DC2626", line_width=2)

        # Render Safe-Zone markers, rings & floating 3D labels
        label_pts = []
        label_txts = []
        if self.landmarks["proximal"] and self.landmarks["distal"]:
            a = np.asarray(self.landmarks["proximal"], dtype=float)
            b = np.asarray(self.landmarks["distal"], dtype=float)
            axis_v = b - a
            if np.linalg.norm(axis_v) > 5:
                r_ring = (self.safe_frame.get("radius_est_mm", 32.0) * 1.32) if self.safe_frame else 38.0
                self.plotter.add_mesh(pv.Line(a, b), color="#0F766E", line_width=2.5)
                self.plotter.add_mesh(_ring_polydata(a, axis_v, r_ring), color="#2563EB", line_width=3.5)
                self.plotter.add_mesh(_ring_polydata(b, axis_v, r_ring), color="#EA580C", line_width=3.5)
                self.plotter.add_mesh(pv.Sphere(radius=5.2, center=a), color="#2563EB")
                self.plotter.add_mesh(pv.Sphere(radius=5.2, center=b), color="#EA580C")
                label_pts.extend([a.tolist(), b.tolist()])
                label_txts.extend(["1. Elbow", "2. Wrist"])
        if self.landmarks["side"]:
            s_pt = np.asarray(self.landmarks["side"], dtype=float)
            self.plotter.add_mesh(pv.Sphere(radius=5.5, center=s_pt), color="#9333EA")
            label_pts.append(s_pt.tolist())
            label_txts.append("3. Splint Side")
        if label_pts:
            self.plotter.add_point_labels(
                np.asarray(label_pts, dtype=float),
                label_txts,
                font_size=11,
                bold=True,
                text_color="#0F172A",
                shape_color="#FFFFFF",
                shape_opacity=0.88,
                point_size=0,
                always_visible=True,
            )

        if reset_cam:
            self.plotter.reset_camera()
        self.plotter.render()

    def _set_camera(self, view: str):
        if self.offscreen:
            return
        if view == "fit":
            self.plotter.reset_camera()
        elif view == "front":
            self.plotter.view_xz()
        elif view == "side":
            self.plotter.view_yz()
        elif view == "top":
            self.plotter.view_xy()
        self.plotter.render()


def main():
    app = QApplication(sys.argv)
    win = SplintFitStudioWindow(offscreen=False)
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
