"""SplintFit v3.2: guided desktop workflow and scan-based geometry."""
import os
os.environ.setdefault('QT_API','pyqt6')
import sys,json,logging
from datetime import datetime
from pathlib import Path
from dataclasses import asdict
import numpy as np
import pyvista as pv
from PyQt6.QtCore import Qt,QThread,pyqtSignal,QTimer,QUrl
from PyQt6.QtGui import QDesktopServices
from PyQt6.QtWidgets import (QApplication,QMainWindow,QWidget,QVBoxLayout,QHBoxLayout,
    QLabel,QPushButton,QListWidget,QStackedWidget,QFileDialog,QDoubleSpinBox,QSpinBox,
    QComboBox,QCheckBox,QFormLayout,QGroupBox,QScrollArea,QMessageBox,QLineEdit,
    QSplitter,QProgressBar,QTextEdit,QTabWidget,QToolButton,QSizePolicy)
from pyvistaqt import QtInteractor
from geometry import (Parameters,read_mesh,stats,build,export_bundle,demo_mesh,
    prepare_scan,display_mesh,suggested_points,clinical_frame)
from project_io import source_sha256,validated_project,atomic_write_json,mesh_reference
from theme import STYLE

LOG=logging.getLogger('splintfit');LOG.setLevel(logging.INFO)
LOG_PATH=Path(os.environ.get('LOCALAPPDATA',str(Path.home()/'.local'/'state')))/'SplintFit'/'splintfit.log'
try:
    LOG_PATH.parent.mkdir(parents=True,exist_ok=True)
    handler=logging.FileHandler(LOG_PATH,encoding='utf-8')
    handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s %(message)s'));LOG.addHandler(handler)
except OSError:LOG.addHandler(logging.StreamHandler())


def label(text,name=None):
    w=QLabel(text);w.setWordWrap(True);w.setTextFormat(Qt.TextFormat.PlainText)
    if name:w.setObjectName(name)
    return w


def prepare_display(scan):
    for piece in scan['pieces']:
        m=piece['mesh'];piece['display']=display_mesh(m);piece['stats']=stats(m)
        piece['suggested']=suggested_points(m)
        piece['boundaries']=m.extract_feature_edges(boundary_edges=True,non_manifold_edges=True,
                                                    feature_edges=False,manifold_edges=False)
    return scan


class Worker(QThread):
    success=pyqtSignal(object);error=pyqtSignal(str);progress=pyqtSignal(int,str)
    def __init__(self,task,**kwargs):
        super().__init__();self.task=task;self.kwargs=kwargs
    def run(self):
        try:
            if self.task=='load':
                self.progress.emit(5,'Đang đọc dữ liệu quét…')
                digest=source_sha256(self.kwargs['path'])
                expected=self.kwargs.get('expected_sha256')
                if expected and digest!=expected:
                    raise ValueError('Mesh nguồn đã thay đổi so với dự án đã lưu. Nạp lại như ca mới và chọn lại mốc; không áp mốc cũ lên mesh khác.')
                mesh=read_mesh(self.kwargs['path'],self.kwargs['scale'])
                self.progress.emit(30,'Đang kiểm tra bề mặt và các mảnh rời…')
                scan=prepare_scan(mesh);scan['source_sha256']=digest;self.progress.emit(60,'Đang chuẩn bị hình hiển thị…')
                out=prepare_display(scan);self.progress.emit(100,'Đã nạp dữ liệu quét.')
            elif self.task=='build':out=build(self.kwargs['mesh'],self.kwargs['params'],self.progress.emit)
            else:
                out=prepare_display(prepare_scan(self.kwargs['mesh']));self.progress.emit(100,'Đã cập nhật tỷ lệ.')
            self.success.emit(out)
        except Exception as exc:
            LOG.exception('Task %s failed',self.task);self.error.emit(str(exc))


class SplintFit(QMainWindow):
    def __init__(self):
        super().__init__();self.setWindowTitle('SplintFit • Nẹp có lỗ + Fusion Form • v4.0.1 prototype')
        available=QApplication.primaryScreen().availableGeometry()
        self.resize(min(1440,available.width()-40),min(900,available.height()-60))
        self.setMinimumSize(980,620);self.setAcceptDrops(True)
        self.mesh=self.source=self.scan=self.result=self.worker=None
        self.mesh_path='';self.scale_used=1.;self.is_demo=False;self.revision=0;self.build_revision=-1
        self.demo_kind='forearm_v1'
        self.loading=True;self.controls={};self.landmarks={};self.reliefs=[];self.calibration={}
        self.pick_mode=None;self.history=[];self.redo_history=[];self.last_state=None
        self.restore_pending=None;self.expert_widgets=[];self.rebuild_requested=False
        self.source_digest=None;self.audit_events=[];self.last_failure=None
        self.guided_pick_queue=[];self.pick_session=0;self.last_export_folder=None
        self.timer=QTimer(self);self.timer.setSingleShot(True);self.timer.timeout.connect(self.start_build)
        root=QWidget();self.setCentralWidget(root)
        layout=QVBoxLayout(root);layout.setContentsMargins(0,0,0,0);layout.setSpacing(0)
        header=QWidget();header.setObjectName('header');h=QHBoxLayout(header);h.setContentsMargins(15,10,15,10)
        h.addWidget(label('SplintFit','brand'));version=label('v4.0.1 prototype','muted');version.setWordWrap(False);h.addWidget(version)
        h.addSpacing(15);h.addWidget(label('Mã ca'));self.case_id=QLineEdit('CASE-001');self.case_id.setMaximumWidth(130);h.addWidget(self.case_id)
        self.side=QComboBox();self.side.addItems(['Tay trái','Tay phải']);h.addWidget(self.side)
        self.stage=QComboBox();self.stage.addItems(['Chưa ghi giai đoạn','Đang sưng / giai đoạn cấp','Theo dõi / giai đoạn sau'])
        self.stage.setToolTip('Ghi nhận lâm sàng, không tự đổi khoảng chừa theo mức sưng.')
        h.addStretch();self.mode=QComboBox();self.mode.addItems(['Cơ bản','Nâng cao']);h.addWidget(self.mode)
        self.undo_btn=self.button('↶',self.undo);h.addWidget(self.undo_btn)
        self.redo_btn=self.button('↷',self.redo);h.addWidget(self.redo_btn)
        self.open_project_btn=self.button('Mở dự án',self.open_project);h.addWidget(self.open_project_btn)
        self.save_project_btn=self.button('Lưu dự án JSON',self.save_project)
        self.save_project_btn.setToolTip('Lưu để làm tiếp trong SplintFit. Muốn có OBJ/STL: dùng Xuất mô hình 3D ở bước 5.')
        h.addWidget(self.save_project_btn);h.addWidget(self.button('Cách dùng',self.show_help));layout.addWidget(header)
        guide=QWidget();guide.setObjectName('guide');g=QHBoxLayout(guide);g.setContentsMargins(16,10,16,10)
        guide_text=QVBoxLayout();self.guide_title=label('Bắt đầu với file quét','guideTitle')
        self.guide_detail=label('','muted');guide_text.addWidget(self.guide_title);guide_text.addWidget(self.guide_detail)
        g.addLayout(guide_text,1)
        self.guide_button=self.button('Chọn file quét',self.run_guide_action,True);self.guide_button.setMinimumWidth(210)
        g.addWidget(self.guide_button);layout.addWidget(guide)
        split=QSplitter(Qt.Orientation.Horizontal)
        self.steps=QListWidget();self.steps.setMinimumWidth(190);self.steps.setMaximumWidth(215)
        self.steps.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.step_names=['Nạp file & kích thước','Chọn vùng làm nẹp','Tạo mô hình nẹp','Xem kết quả','Xuất mô hình 3D']
        self.steps.addItems(self.step_names);split.addWidget(self.steps)
        center=QWidget();c=QVBoxLayout(center);c.setContentsMargins(10,10,10,10)
        tools=QHBoxLayout();self.scene_title=label('CHƯA NẠP QUÉT','muted');tools.addWidget(self.scene_title,1)
        tools.addWidget(self.button('Vừa khung',lambda:self.plotter.reset_camera()))
        tools.addWidget(self.button('Dọc chi',self.view_long));tools.addWidget(self.button('Mặt nẹp',self.view_side));c.addLayout(tools)
        self.pick_hint=label('Xoay hình: chuột trái • Phóng to: cuộn chuột','muted');c.addWidget(self.pick_hint)
        self.cancel_pick_btn=self.button('Dừng chọn điểm',self.cancel_pick);self.cancel_pick_btn.hide();c.addWidget(self.cancel_pick_btn)
        self.plotter=QtInteractor(center);self.plotter.set_background('#EDF2F6');self.plotter.add_axes();c.addWidget(self.plotter,1)
        opts=QHBoxLayout();self.show_scan=QCheckBox('Chi quét');self.show_scan.setChecked(True)
        self.show_cage=QCheckBox('Mặt trong');self.show_cage.setChecked(True);self.show_shell=QCheckBox('Vỏ nẹp')
        self.show_holes=QCheckBox('Biên hở');self.show_normals=QCheckBox('Hướng ra ngoài');self.show_heatmap=QCheckBox('Khoảng chừa')
        for w in [self.show_scan,self.show_cage,self.show_shell,self.show_holes,self.show_normals,self.show_heatmap]:
            opts.addWidget(w);w.toggled.connect(self.render)
        c.addLayout(opts);c.addWidget(label('Tư thế chi lấy từ lần quét; app không tự nắn chỉnh xương hoặc xoay khớp.','muted'));split.addWidget(center)
        self.panels=QStackedWidget();self.panels.setMinimumWidth(340);self.panels.setMaximumWidth(440)
        split.addWidget(self.panels);split.setSizes([200,700,410]);layout.addWidget(split,1)
        bottom=QWidget();b=QHBoxLayout(bottom);b.setContentsMargins(12,6,12,6)
        self.work_label=label('Sẵn sàng','muted');b.addWidget(self.work_label,1)
        self.progress=QProgressBar();self.progress.setMaximumWidth(200);self.progress.setValue(0);b.addWidget(self.progress);layout.addWidget(bottom)
        self.make_panels();self.steps.currentRowChanged.connect(self.change_step);self.mode.currentIndexChanged.connect(self.change_mode)
        self.steps.setCurrentRow(0);self.controls['seam_gap_mm'].setEnabled(False)
        self.seam_form.setRowVisible(self.controls['seam_gap_mm'],False)
        self.splint_type.setCurrentIndex(2)
        self.loading=False;self.change_mode();self.last_state=self.state_snapshot();self.update_actions();self.setStyleSheet(STYLE)

    def button(self,text,action,primary=False):
        w=QPushButton(text);w.clicked.connect(action)
        if primary:w.setObjectName('primary')
        return w
    def panel(self,title,subtitle):
        page=QWidget();lay=QVBoxLayout(page);lay.setContentsMargins(16,16,16,16);lay.setSpacing(11)
        lay.addWidget(label(title,'title'));lay.addWidget(label(subtitle,'muted'))
        scroll=QScrollArea();scroll.setWidgetResizable(True);scroll.setWidget(page);self.panels.addWidget(scroll);return lay
    def group(self,layout,title,expert=False):
        box=QGroupBox(title);form=QFormLayout(box);form.setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapAllRows);form.setVerticalSpacing(8);layout.addWidget(box)
        if expert:self.expert_widgets.append(box)
        return form
    def fold_group(self,layout,title):
        box=QWidget();outer=QVBoxLayout(box);outer.setContentsMargins(0,0,0,0)
        toggle=QToolButton();toggle.setText(title);toggle.setCheckable(True)
        toggle.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon);toggle.setArrowType(Qt.ArrowType.RightArrow)
        toggle.setSizePolicy(QSizePolicy.Policy.Expanding,QSizePolicy.Policy.Fixed)
        body=QWidget();form=QFormLayout(body);form.setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapAllRows)
        outer.addWidget(toggle);outer.addWidget(body);body.hide()
        def expand(checked):
            body.setVisible(checked);toggle.setArrowType(Qt.ArrowType.DownArrow if checked else Qt.ArrowType.RightArrow)
        toggle.toggled.connect(expand);layout.addWidget(box)
        return form,toggle
    def spin(self,key,low,high,value,suffix=' mm',integer=False):
        w=QSpinBox() if integer else QDoubleSpinBox()
        if not integer:w.setDecimals(2);w.setSingleStep(.5)
        w.setRange(low,high);w.setValue(value);w.setSuffix(suffix);self.controls[key]=w;w.valueChanged.connect(self.invalidate);return w

    def make_panels(self):
        l=self.panel('01  Nạp quét & số đo','Nạp file từ KIRI Engine. Có thể kéo STL, OBJ hoặc PLY vào cửa sổ.')
        self.file_label=label('Chưa chọn file','muted');l.addWidget(self.file_label)
        f=self.group(l,'File và đơn vị');self.unit=QComboBox();self.unit.addItems(['Milimét (mm)','Centimét (cm)','Mét (m)']);f.addRow('Đơn vị khi xuất file',self.unit)
        self.load_btn=self.button('Chọn file quét',self.load_file,True);l.addWidget(self.load_btn);l.addWidget(self.button('Thử mẫu nẹp cổ tay có lỗ',self.load_cast_demo))
        l.addWidget(self.button('Xuất báo cáo lỗi nạp file',self.export_diagnostic))
        self.component=QComboBox();self.component.currentIndexChanged.connect(self.change_component);f.addRow('Bề mặt để thiết kế',self.component)
        self.scan_stats=label('Mesh chưa được đọc.');l.addWidget(self.scan_stats)
        self.scale_confirm=QCheckBox('Đã đối chiếu đúng kích thước thực');self.scale_confirm.toggled.connect(self.invalidate)
        l.addWidget(label('Kiểm tra đơn vị và đối chiếu với số đo độc lập, rồi xác nhận bên dưới. Nếu sai tỷ lệ, mở phần hiệu chỉnh.','muted'))
        l.addWidget(self.scale_confirm)
        f,self.calibration_toggle=self.fold_group(l,'Hiệu chỉnh kích thước khi cần')
        f.addRow(self.button('Chọn mốc đo A',lambda:self.start_pick('measure_a')));f.addRow(self.button('Chọn mốc đo B',lambda:self.start_pick('measure_b')))
        self.measured_label=label('Chưa chọn đủ hai mốc.');f.addRow(self.measured_label)
        self.real_distance=QDoubleSpinBox();self.real_distance.setRange(.1,1000);self.real_distance.setValue(100);self.real_distance.setSuffix(' mm')
        self.real_distance.valueChanged.connect(self.scale_reference_changed)
        f.addRow('Khoảng cách thẳng đo thực tế A–B',self.real_distance);f.addRow(self.button('Hiệu chỉnh theo số đo',self.calibrate_scale))
        f.addRow(label('A–B là khoảng cách thẳng, không phải chu vi. Sau hiệu chỉnh, kiểm lại và xác nhận kích thước; các mốc vùng cũ sẽ bị xóa.','muted'))
        l.addStretch();l.addWidget(self.button('Tiếp: Chọn vùng nẹp',lambda:self.go_forward(1)))
        l=self.panel('02  Chọn vùng cần giữ','Bấm nút rồi nhấp chuột phải lên da. Hai đầu xác định chiều dài; điểm thứ ba xác định mặt đặt nẹp.')
        self.guided_pick_btn=self.button('Bắt đầu chọn 3 mốc',self.start_guided_pick,True);l.addWidget(self.guided_pick_btn)
        l.addWidget(label('Lần lượt: 1. đầu phía khuỷu → 2. đầu phía bàn tay → 3. giữa mặt đặt nẹp. App sẽ nhắc từng lần nhấp chuột phải.','muted'))
        f=self.group(l,'Vị trí nẹp');self.marker_labels={}
        for key,title in [('proximal','1. Đầu nẹp phía khuỷu'),('distal','2. Đầu nẹp phía bàn tay'),('side','3. Giữa mặt đặt nẹp')]:
            f.addRow(self.button('Chọn '+title.lower(),lambda _=False,k=key:self.start_pick(k)))
            self.marker_labels[key]=label('Chưa chọn','muted');f.addRow(self.marker_labels[key])
        suggestion=self.button('Gợi ý hình học (cần kiểm tra lại)',self.suggest_landmarks);self.expert_widgets.append(suggestion)
        f.addRow(suggestion);f.addRow(self.button('Xóa các mốc vùng nẹp',self.clear_landmarks))
        self.region_confirm=QCheckBox('Đã xác nhận các mốc và vùng cần cố định');self.region_confirm.toggled.connect(self.invalidate);l.addWidget(self.region_confirm)
        f,self.region_details_toggle=self.fold_group(l,'Chỉnh thêm giới hạn và hồ sơ')
        f.addRow('Kéo dài thêm về phía khuỷu',self.spin('start_adjust_mm',-100,100,0));f.addRow('Kéo dài thêm về phía bàn tay',self.spin('end_adjust_mm',-100,100,0))
        l.addWidget(label('Số âm để thu ngắn. Chọn biên thực tế theo chỉ định; app không suy ra khớp cần cố định từ mesh.','muted'))
        self.indication=QLineEdit();self.indication.setPlaceholderText('Tổn thương / mục tiêu cố định…');f.addRow('Mục tiêu nẹp',self.indication)
        f.addRow('Giai đoạn ghi nhận',self.stage)
        self.posture=QLineEdit();self.posture.setPlaceholderText('Ví dụ: cổ tay tư thế trung tính…');f.addRow('Tư thế tại thời điểm quét',self.posture)
        l.addStretch();l.addWidget(self.button('Tiếp: Điều chỉnh nẹp',lambda:self.go_forward(2)))
        design_layout=self.panel('03  Điều chỉnh độ vừa','Chọn nhóm cần chỉnh. Các thông số ban đầu dùng thử, không phải chỉ định điều trị.')
        self.design_tabs=QTabWidget();core=QWidget();l=QVBoxLayout(core)
        self.design_tabs.addTab(core,'Độ vừa')
        f=self.group(l,'Kiểu và mức ôm');self.splint_type=QComboBox();self.splint_type.addItems(['Máng mặt lòng','Máng mặt lưng','Nẹp hai mảnh'])
        self.splint_type.currentIndexChanged.connect(self.type_changed);f.addRow('Kiểu nẹp theo chỉ định',self.splint_type)
        self.coverage=QComboBox();self.coverage.addItems(['Máng hẹp','Khoảng nửa vòng tay','Máng ôm rộng','Tùy chỉnh nâng cao']);self.coverage.setCurrentIndex(1)
        self.coverage.currentIndexChanged.connect(self.coverage_changed);f.addRow('Nẹp ôm quanh tay',self.coverage);f.addRow('Khe giữa hai mảnh',self.spin('seam_gap_mm',0,25,4));self.seam_form=f
        l.addWidget(label('Mặt lòng/lưng lấy từ điểm đã chọn ở bước 2. Đổi phía đặt nẹp: chọn lại điểm trên da.','muted'))
        f=self.group(l,'Đệm, độ ôm và độ dày');f.addRow('Độ dày lớp đệm khi sử dụng',self.spin('padding_mm',0,20,0))
        f.addRow('Chừa thêm ngoài lớp đệm',self.spin('clearance_mm',0,30,1.5));f.addRow('Độ dày thành nẹp',self.spin('thickness_mm',.2,15,3))
        self.controls['padding_mm'].setToolTip('Phần không gian dự kiến dành cho lớp đệm, tính bằng mm. App không mô phỏng độ nén của đệm.')
        self.controls['clearance_mm'].setToolTip('Khoảng chừa hình học thêm ngoài lớp đệm. Giá trị cần được người phụ trách lựa chọn và kiểm chứng.')
        self.controls['thickness_mm'].setToolTip('Độ dịch giữa hai mặt vỏ. Chưa phải bảo đảm độ dày nhỏ nhất hoặc độ bền.')
        self.fit_summary=label('','fitSummary');l.addWidget(self.fit_summary)
        l.addWidget(label('Khoảng chừa = đệm + phần chừa thêm + nâng cục bộ. Phù nề và độ vững phải được đánh giá riêng.','muted'))
        l.addStretch();relief_page=QWidget();l=QVBoxLayout(relief_page);self.design_tabs.addTab(relief_page,'Tránh tì đè')
        f=self.group(l,'Vùng tránh tì đè');self.relief_name=QLineEdit('Vùng xương nhô / da nhạy cảm');f.addRow('Tên vùng',self.relief_name)
        self.relief_radius=QDoubleSpinBox();self.relief_radius.setRange(2,60);self.relief_radius.setValue(12);self.relief_radius.setSuffix(' mm');f.addRow('Bán kính vùng nâng',self.relief_radius)
        self.relief_extra=QDoubleSpinBox();self.relief_extra.setRange(0,10);self.relief_extra.setValue(1.5);self.relief_extra.setSuffix(' mm');f.addRow('Chừa thêm ở tâm vùng',self.relief_extra)
        f.addRow(self.button('Chọn vùng trên da và thêm',lambda:self.start_pick('relief')))
        self.relief_list=QListWidget();self.relief_list.setMaximumHeight(95);f.addRow(self.relief_list);f.addRow(self.button('Xóa vùng đang chọn',self.remove_relief))
        l.addWidget(label('Chọn vùng theo đánh giá của người phụ trách; vùng nâng hình học không chứng minh áp lực đã giảm đủ.','muted'));l.addStretch()
        technical_page=QWidget();l=QVBoxLayout(technical_page);self.design_tabs.addTab(technical_page,'Kỹ thuật')
        f=self.group(l,'Tùy chọn kỹ thuật',True);f.addRow('Mức bao phủ chính xác',self.spin('coverage_deg',90,270,180,' °'))
        self.controls['coverage_deg'].valueChanged.connect(self.sync_coverage_label)
        f.addRow('Xoay quanh trục đã chọn',self.spin('opening_rotation_deg',-180,180,0,' °'))
        f.addRow('Mục tiêu số mặt trước tạo quads',self.spin('target_triangles',100,100000,1800,' mặt',True));f.addRow('Sai lệch giảm lưới cho phép',self.spin('max_sampled_deviation_mm',.01,5,.5))
        self.flip=QCheckBox('Đảo hướng bề mặt được gợi ý');self.flip.toggled.connect(self.invalidate);f.addRow(self.flip)
        template_page=QWidget();tl=QVBoxLayout(template_page);self.design_tabs.addTab(template_page,'Dáng & lỗ')
        self.cast_template=QCheckBox('Tạo mẫu nẹp có cấu trúc cho Fusion Form');self.cast_template.setChecked(True);self.cast_template.toggled.connect(self.invalidate);tl.addWidget(self.cast_template)
        self.ventilation=QCheckBox('Tạo lỗ thoáng xuyên thành nẹp');self.ventilation.setChecked(True);self.ventilation.toggled.connect(self.invalidate);tl.addWidget(self.ventilation)
        tf=self.group(tl,'Lỗ thoáng & khe đai')
        tf.addRow('Khoảng bố trí danh nghĩa',self.spin('hole_pitch_mm',16,45,24))
        tf.addRow('Tỷ lệ kích thước lỗ/ô (0,20–0,65)',self.spin('hole_ratio',.2,.65,.48,''))
        self.controls['hole_ratio'].setSingleStep(.05)
        self.controls['hole_ratio'].setToolTip('Tỷ lệ kích thước theo hai chiều của ô tham số. 0,48 không phải 48% diện tích toàn nẹp. Chưa đo bề rộng vách nhỏ nhất theo mm sau ánh xạ.')
        tl.addWidget(label('Khe luồn đai được tạo trên ba dải ngang. Chưa có đai vật lý, bo mép hoặc đánh giá độ bền.','muted'))
        tf=self.group(tl,'Đường khuyết vùng ngón cái — đặt thủ công')
        tf.addRow('Độ sâu tính từ đầu bàn tay',self.spin('hand_notch_depth_mm',0,60,0))
        tf.addRow('Bề rộng quanh tay',self.spin('hand_notch_width_deg',30,140,75,' °'))
        tf.addRow('Vị trí so với mốc mặt đặt nẹp',self.spin('hand_notch_angle_deg',-180,180,0,' °'))
        tl.addWidget(label('Để độ sâu = 0 khi chỉ làm vùng cẳng tay. Chỉ đặt cửa bàn tay khi scan có vùng đó; app không tự nhận diện ngón cái. Dùng góc để xoay đường khuyết, rồi kiểm trên hình.','muted'))
        tl.addStretch()
        l.addStretch();l=design_layout;l.addWidget(self.design_tabs,1)
        self.live=QCheckBox('Tự cập nhật sau khi đổi thông số');l.addWidget(self.live)
        self.expert_widgets.append(self.live)
        self.build_hint=label('Nạp file quét để bắt đầu.','muted');l.addWidget(self.build_hint)
        self.build_btn=self.button('Tạo / Cập nhật nẹp',self.start_build,True);l.addWidget(self.build_btn);l.addStretch()
        l=self.panel('04  Kiểm tra thiết kế','Bản đồ màu đo khoảng cách không dấu từ mặt trong đến bản quét; không phải áp lực hoặc chứng minh không xuyên nhau.')
        self.result_status=label('Chưa tạo mô hình nẹp. Dùng nút hướng dẫn phía trên.','notice');l.addWidget(self.result_status)
        self.report_label=label('Chưa tạo thiết kế.');self.report_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse);l.addWidget(self.report_label)
        f,self.circumference_toggle=self.fold_group(l,'Đối chiếu chu vi thước dây (nếu có)')
        f.addRow('Gần đầu nẹp phía khuỷu',self.spin('circumference_proximal_mm',0,1000,0))
        f.addRow('Giữa hai đầu nẹp',self.spin('circumference_mid_mm',0,1000,0))
        f.addRow('Gần đầu nẹp phía bàn tay',self.spin('circumference_distal_mm',0,1000,0))
        f.addRow('Ngưỡng sai lệch nghiên cứu',self.spin('circumference_tolerance_mm',.1,30,3))
        f.addRow(label('Để 0 nếu chưa đo, app sẽ ghi chưa đối chiếu. Đo đúng mặt phẳng tím; đổi vùng cần đo lại. 3 mm là ngưỡng nghiên cứu có thể sửa, chưa là tiêu chuẩn lâm sàng.','muted'))
        l.addWidget(label('Vùng thiếu vẫn hiển thị để sửa giới hạn/chọn mặt hoặc quét bổ sung. Không tự lấp dữ liệu giải phẫu.','muted'))
        l.addStretch();l.addWidget(self.button('Tiếp: Xuất mô hình 3D',lambda:self.go_forward(4)))
        l=self.panel('05  Xuất mô hình 3D','Chọn thư mục để nhận OBJ, STL và hồ sơ. Nút Lưu dự án JSON chỉ để mở lại trong SplintFit.')
        self.export_summary=label('Chưa có thiết kế đủ điều kiện xuất.');l.addWidget(self.export_summary)
        l.addWidget(label('OBJ: thử chuyển sang Form trong Fusion. STL: vỏ và tham chiếu. JSON: thông số, không chứa mô hình Form.','muted'))
        self.reviewer=QLineEdit();self.reviewer.setPlaceholderText('Nhập tên người kiểm tra');l.addWidget(label('Người kiểm tra bản nghiên cứu'));l.addWidget(self.reviewer)
        self.review=QCheckBox('Đã xem vùng phủ, số đo và hướng mặt trong');l.addWidget(self.review)
        self.review.toggled.connect(self.update_actions)
        self.export_btn=self.button('Xuất mô hình 3D (OBJ / STL)',self.export_files,True);l.addWidget(self.export_btn)
        self.export_location=label('Sau khi xuất, đường dẫn kết quả sẽ hiện tại đây.','muted');l.addWidget(self.export_location)
        self.open_export_btn=self.button('Mở thư mục kết quả',self.open_export_folder);self.open_export_btn.setEnabled(False);l.addWidget(self.open_export_btn)
        f,self.finishing_toggle=self.fold_group(l,'Ghi chú hoàn thiện thêm trong Fusion');self.strap_count=QSpinBox();self.strap_count.setRange(0,8);self.strap_count.setValue(3);f.addRow('Số đai dự kiến',self.strap_count)
        self.edge_radius=QDoubleSpinBox();self.edge_radius.setRange(0,8);self.edge_radius.setValue(2);self.edge_radius.setSuffix(' mm');f.addRow('Bán kính bo mép dự kiến',self.edge_radius)
        self.finishing_notes=QTextEdit();self.finishing_notes.setMaximumHeight(90);self.finishing_notes.setPlaceholderText('Vị trí đai, lỗ thoáng, cửa sổ vết thương, vật liệu…');f.addRow('Ghi chú',self.finishing_notes)
        f.addRow(label('Mẫu mới tạo lỗ thoáng và khe luồn đai. Đai vật lý, bo mép và các yêu cầu bổ sung vẫn cần hoàn thiện trong Fusion.','muted'))
        l.addWidget(self.button('Xuất báo cáo để kiểm tra lỗi',self.export_diagnostic))
        l.addWidget(label('Gói hình học chưa kiểm định dùng trên người. Chuyển Form vẫn cần kiểm lại độ khít.','notice'));l.addStretch()
        for w in [self.case_id,self.reviewer,self.indication,self.posture]:w.textChanged.connect(self.metadata_changed)
        self.side.currentIndexChanged.connect(self.metadata_changed);self.stage.currentIndexChanged.connect(self.metadata_changed)
        self.strap_count.valueChanged.connect(self.metadata_changed);self.edge_radius.valueChanged.connect(self.metadata_changed)
        self.finishing_notes.textChanged.connect(self.metadata_changed)

    def metadata_changed(self,*_):
        if not self.loading:
            if self.last_export_folder:self.export_location.setText('Hồ sơ đã thay đổi. Xuất lại để cập nhật gói kết quả.')
            self.last_export_folder=None;self.review.setChecked(False);self.update_actions()

    def show_help(self):
        QMessageBox.information(self,'Cách dùng SplintFit',
            '1. Nạp file → kiểm tra đơn vị, đối chiếu kích thước → tích xác nhận.\n\n'
            '2. Chọn vùng → Bắt đầu chọn 3 mốc → nhấp chuột phải lần lượt theo hướng dẫn → kiểm tra và xác nhận vùng.\n\n'
            '3. Chọn kiểu nẹp, đệm, khoảng chừa, độ dày → Tạo mô hình nẹp.\n\n'
            '4. Xoay xem vỏ và đọc kết quả. Có lỗi thì sửa vùng hoặc dữ liệu; có số đo thước thì mở phần đối chiếu chu vi.\n\n'
            '5. Nhập người kiểm tra, tích ô đã xem → Xuất mô hình 3D → Mở thư mục kết quả.\n\n'
            'Nút xanh trên cùng luôn chỉ việc cần làm tiếp. Lưu dự án JSON để làm tiếp trong SplintFit; OBJ/STL nằm trong gói xuất ở bước 5.\n\n'
            'Đây là công cụ nghiên cứu, chưa xác nhận an toàn lâm sàng.')

    def current_result(self):
        return self.result is not None and self.build_revision==self.revision

    def workflow_hint(self):
        """Return an instruction and a reversible navigation/action; never tick consent."""
        if self.worker:
            return ('Đang xử lý dữ liệu','Chờ hoàn tất. Bạn có thể đọc hướng dẫn; chưa chọn điểm hoặc xuất trong lúc này.','Đang xử lý…','busy')
        if self.pick_mode:
            names={'proximal':'Mốc 1: đầu nẹp phía khuỷu','distal':'Mốc 2: đầu nẹp phía bàn tay',
                'side':'Mốc 3: giữa mặt đặt nẹp','measure_a':'Mốc đo A','measure_b':'Mốc đo B','relief':'Tâm vùng tránh tì đè'}
            return (names[self.pick_mode],'Nhấp CHUỘT PHẢI lên da. Xoay bằng chuột trái, cuộn để phóng to.','Dừng chọn điểm','cancel_pick')
        if self.mesh is None:
            detail='Chọn STL, OBJ hoặc PLY dạng bề mặt. Có thể dùng mẫu tổng hợp ở bước 1 để tập thao tác.'
            if self.last_failure:detail='Lần nạp trước chưa thành công: '+self.last_failure['message'].splitlines()[0]
            return ('Bước 1 / 5 — Nạp dữ liệu quét',detail,'Chọn file quét','load')
        if not self.scale_confirm.isChecked():
            return ('Bước 1 / 5 — Kiểm tra kích thước','Đối chiếu với số đo độc lập. Nếu cần, mở hiệu chỉnh A–B. Sau khi kiểm tra, tự tích ô xác nhận kích thước.','Đến ô xác nhận kích thước','scale')
        index=self.steps.currentRow()
        if index==0:
            return ('Đã xác nhận kích thước','Tiếp theo chọn hai đầu vùng làm nẹp và một điểm trên mặt đặt nẹp.','Tiếp: Chọn vùng','step_1')
        if not self.ready_landmarks():
            return ('Bước 2 / 5 — Chọn vùng làm nẹp','App sẽ nhắc từng mốc. Với ca thử cẳng tay, kiểm tra không lấy nhầm cả các ngón vào vùng.','Bắt đầu chọn các mốc','pick_region')
        if not self.region_confirm.isChecked():
            return ('Bước 2 / 5 — Kiểm tra ba mốc','Nhìn các nhãn 1, 2, 3 trên hình; chọn lại nếu sai, rồi tự tích xác nhận vùng cần cố định.','Đến ô xác nhận vùng','region')
        if index==1:
            return ('Đã xác nhận vùng làm nẹp','Tiếp theo chọn kiểu nẹp, độ dày lớp đệm, phần chừa thêm và độ dày vỏ.','Tiếp: Điều chỉnh nẹp','step_2')
        if not self.current_result():
            return ('Bước 3 / 5 — Cần tạo mô hình nẹp','Lưu JSON chưa tạo mô hình. Bấm nút bên cạnh để dựng từ vùng và thông số hiện tại.','Tạo mô hình nẹp','build')
        if not self.result.get('export_ready',False):
            detail=self.result['report'].get('messages',['Cần kiểm tra lại vùng chọn.'])[0]
            if self.result['status']=='blocked':
                return ('Chưa xuất được — kiểm tra số đo',detail,'Đến số đo cần kiểm tra','measurements')
            return ('Chưa tạo được vỏ hoàn chỉnh',detail,'Sửa vùng ở bước 2','fix_region')
        if index==2:
            return ('Đã tạo mô hình nẹp','Xem vỏ, vùng phủ và các thông báo trước khi xuất.','Tiếp: Xem kết quả','step_3')
        if index==3:
            return ('Bước 4 / 5 — Xem kết quả','Xoay xem vỏ và đọc báo cáo. Các kiểm tra hình học không phải xác nhận an toàn lâm sàng.','Tiếp: Xuất mô hình 3D','step_4')
        if not self.reviewer.text().strip():
            return ('Bước 5 / 5 — Ghi người kiểm tra','Nhập tên người đã kiểm tra bản nghiên cứu. Gói xuất sẽ có OBJ/STL nếu đủ điều kiện, cùng hồ sơ.','Nhập tên người kiểm tra','reviewer')
        if not self.review.isChecked():
            return ('Bước 5 / 5 — Xác nhận đã xem thiết kế','Sau khi xem vùng phủ, số đo và hướng mặt trong, tự tích ô xác nhận.','Đến ô xác nhận đã xem','review')
        if self.last_export_folder:
            return ('Đã xuất mô hình 3D','Kết quả nằm trong thư mục bên cạnh. OBJ phục vụ thử Form, STL là vỏ và tham chiếu.','Mở thư mục kết quả','open_export')
        detail='Chọn thư mục đích. App sẽ ghi mô hình OBJ/STL và hồ sơ vào một thư mục con.'
        if not self.result.get('form_available'):detail='Lưới chưa đủ điều kiện xuất OBJ Form. Có thể xuất STL/thông số; xem báo cáo trước khi tiếp tục.'
        return ('Sẵn sàng xuất bản nghiên cứu',detail,'Xuất mô hình 3D','export')

    def focus_control(self,index,control):
        self.steps.setCurrentRow(index);self.panels.widget(index).ensureWidgetVisible(control)
        control.setFocus()

    def run_guide_action(self):
        action=self.workflow_hint()[3]
        if action=='load':self.steps.setCurrentRow(0);self.load_file()
        elif action=='scale':self.focus_control(0,self.scale_confirm)
        elif action=='region':self.focus_control(1,self.region_confirm)
        elif action=='pick_region':self.steps.setCurrentRow(1);self.start_guided_pick()
        elif action=='build':self.steps.setCurrentRow(2);self.start_build()
        elif action=='fix_region':self.steps.setCurrentRow(1);self.work_label.setText('Kiểm tra mốc, thu vùng hoặc quét bổ sung theo thông báo ở bước 4.')
        elif action=='reviewer':self.focus_control(4,self.reviewer)
        elif action=='measurements':
            self.circumference_toggle.setChecked(True)
            rows=self.result['report'].get('circumference_checks',[])
            failed=next((r['name'] for r in rows if r['comparison'] in ('MISMATCH','UNMEASURABLE')),'middle')
            key={'proximal':'circumference_proximal_mm','middle':'circumference_mid_mm','distal':'circumference_distal_mm'}[failed]
            self.focus_control(3,self.controls[key])
        elif action=='review':self.focus_control(4,self.review)
        elif action=='export':self.export_files()
        elif action=='open_export':self.open_export_folder()
        elif action=='cancel_pick':self.cancel_pick()
        elif action.startswith('step_'):self.go_forward(int(action[-1]))

    def go_forward(self,target):
        if self.worker:return
        if self.mesh is None:self.steps.setCurrentRow(0);return
        if target>0 and not self.scale_confirm.isChecked():self.focus_control(0,self.scale_confirm);return
        if target>1 and (not self.ready_landmarks() or not self.region_confirm.isChecked()):
            self.focus_control(1,self.region_confirm);return
        if target>=3 and not self.current_result():self.steps.setCurrentRow(2);return
        if target>=4 and not self.result.get('export_ready',False):self.steps.setCurrentRow(3);return
        self.steps.setCurrentRow(target)

    def update_guidance(self):
        if not hasattr(self,'guide_button') or not hasattr(self,'review'):return
        title,detail,button,action=self.workflow_hint()
        self.guide_title.setText(title);self.guide_detail.setText(detail);self.guide_button.setText(button)
        self.guide_button.setEnabled(action!='busy')
        ready=self.current_result() and self.result.get('export_ready',False)
        done=[self.mesh is not None and self.scale_confirm.isChecked(),self.ready_landmarks() and self.region_confirm.isChecked(),
              ready,ready and self.review.isChecked(),bool(self.last_export_folder)]
        for index,name in enumerate(self.step_names):
            self.steps.item(index).setText(f'{index+1:02d}  {name}\n      '+('Đã thực hiện' if done[index] else 'Chưa hoàn thành'))
        self.guided_pick_btn.setEnabled(self.mesh is not None and not self.worker)
        self.cancel_pick_btn.setVisible(self.pick_mode is not None or bool(self.guided_pick_queue))
        self.open_export_btn.setEnabled(bool(self.last_export_folder) and not self.worker)
        self.save_project_btn.setEnabled(self.mesh is not None and not self.worker);self.open_project_btn.setEnabled(not self.worker)
        self.fit_summary.setText(f"Khoảng chừa cơ bản = {self.controls['padding_mm'].value():g} mm đệm + {self.controls['clearance_mm'].value():g} mm thêm = {self.controls['padding_mm'].value()+self.controls['clearance_mm'].value():g} mm.\nChưa tính các vùng nâng cục bộ.")

    def open_export_folder(self):
        if self.last_export_folder and Path(self.last_export_folder).is_dir():
            if not QDesktopServices.openUrl(QUrl.fromLocalFile(str(self.last_export_folder))):
                self.error('Chưa mở được thư mục tự động. Mở bằng đường dẫn:\n'+str(self.last_export_folder))
    def record_event(self,event,**details):
        self.audit_events.append({'event':event,'at':datetime.now().astimezone().isoformat(),
            'revision':self.revision,**details})
    def scale_reference_changed(self,*_):
        if self.loading:return
        self.scale_confirm.setChecked(False);self.invalidate()
        self.work_label.setText('Số đo tham chiếu đã đổi: kiểm tra/hiệu chỉnh rồi xác nhận lại kích thước.')

    def parameters(self):
        vals={k:w.value() for k,w in self.controls.items()}
        vals.update(axis='AUTO',flip_normals=self.flip.isChecked(),proximal_point=self.landmarks.get('proximal'),
            distal_point=self.landmarks.get('distal'),side_point=self.landmarks.get('side'),reliefs=json.loads(json.dumps(self.reliefs)),
            splint_mode='bivalve' if self.splint_type.currentIndex()==2 else 'single',allow_incomplete_preview=True,auto_orient_open_normals=True)
        vals.update(cast_template=self.cast_template.isChecked(),ventilation=self.ventilation.isChecked())
        return Parameters(**vals)
    def state_snapshot(self):
        if not self.controls:return {}
        return {'controls':{k:w.value() for k,w in self.controls.items()},'landmarks':json.loads(json.dumps(self.landmarks)),
            'reliefs':json.loads(json.dumps(self.reliefs)),'type':self.splint_type.currentIndex(),'coverage':self.coverage.currentIndex(),'flip':self.flip.isChecked(),
            'cast_template':self.cast_template.isChecked(),'ventilation':self.ventilation.isChecked()}
    def invalidate(self,*_):
        if self.loading:return
        self.last_export_folder=None
        # A queued live rebuild must never outlive its scale/region confirmation.
        self.timer.stop();self.rebuild_requested=False
        now=self.state_snapshot()
        if self.last_state:
            plane_changed=now['landmarks']!=self.last_state['landmarks'] or any(now['controls'][k]!=self.last_state['controls'][k] for k in ('start_adjust_mm','end_adjust_mm'))
            if plane_changed:
                self.loading=True
                for key in ('circumference_proximal_mm','circumference_mid_mm','circumference_distal_mm'):self.controls[key].setValue(0)
                self.loading=False;now=self.state_snapshot()
        if self.last_state and now!=self.last_state:
            self.history.append(self.last_state);self.history=self.history[-40:];self.redo_history.clear()
        self.last_state=now;self.revision+=1;self.result=None;self.review.setChecked(False)
        self.report_label.setText('Thiết kế cần cập nhật. Chọn Tạo / Cập nhật nẹp.');self.export_summary.setText('Thông số hoặc vùng nẹp đã đổi. Tạo lại trước khi xuất.')
        self.result_status.setText('Chưa có mô hình cập nhật. Dùng nút Tạo mô hình nẹp trên cùng.')
        self.export_location.setText('Chưa xuất mô hình cho thông số hiện tại.')
        self.update_actions();self.update_marker_labels()
        if self.mesh is not None:self.render()
        if self.live.isChecked() and self.ready_landmarks() and self.scale_confirm.isChecked() and self.region_confirm.isChecked():
            if self.worker:self.rebuild_requested=True
            else:self.timer.start(700)
    def restore_state(self,state):
        self.cancel_pick()
        if state['landmarks']!=self.landmarks:self.region_confirm.setChecked(False)
        self.loading=True;self.landmarks=json.loads(json.dumps(state['landmarks']));self.reliefs=json.loads(json.dumps(state['reliefs']))
        self.splint_type.setCurrentIndex(state['type']);self.coverage.setCurrentIndex(state['coverage']);self.flip.setChecked(state['flip'])
        self.cast_template.setChecked(state.get('cast_template',False));self.ventilation.setChecked(state.get('ventilation',True))
        for k,w in self.controls.items():
            value=state['controls'].get(k,w.value());w.setValue(int(value) if isinstance(w,QSpinBox) else value)
        self.loading=False;self.last_state=self.state_snapshot();self.invalidate();self.refresh_reliefs()
    def undo(self):
        if self.history:self.redo_history.append(self.state_snapshot());self.restore_state(self.history.pop())
    def redo(self):
        if self.redo_history:self.history.append(self.state_snapshot());self.restore_state(self.redo_history.pop())
    def change_mode(self,*_):
        for w in self.expert_widgets:w.setVisible(self.mode.currentIndex()==1)
        self.design_tabs.setTabVisible(2,self.mode.currentIndex()==1)
    def type_changed(self,*_):
        two=self.splint_type.currentIndex()==2;self.coverage.setEnabled(not two);self.controls['seam_gap_mm'].setEnabled(two)
        self.seam_form.setRowVisible(self.controls['seam_gap_mm'],two)
        self.invalidate()
    def coverage_changed(self,*_):
        if not self.loading and self.coverage.currentIndex()<3:
            self.controls['coverage_deg'].setValue([120,180,240][self.coverage.currentIndex()])
    def sync_coverage_label(self,value):
        values=[120,180,240];index=values.index(value) if value in values else 3
        self.coverage.blockSignals(True);self.coverage.setCurrentIndex(index);self.coverage.blockSignals(False)
    def change_step(self,index):
        if index<0:return
        if index>0 and self.mesh is None:self.steps.setCurrentRow(0);self.work_label.setText('Nạp file quét trước.');return
        if index!=self.panels.currentIndex() and (self.pick_mode or self.guided_pick_queue):self.cancel_pick()
        self.panels.setCurrentIndex(index)
        if not self.loading:self.update_guidance()
        if self.mesh is not None:self.render()
    def update_actions(self):
        if not hasattr(self,'export_btn'):return
        busy=self.worker is not None;self.build_btn.setEnabled(self.mesh is not None and not busy)
        self.load_btn.setEnabled(not busy);self.component.setEnabled(not busy)
        self.export_btn.setEnabled(self.result is not None and self.result.get('export_ready',False) and not busy)
        self.undo_btn.setEnabled(bool(self.history));self.redo_btn.setEnabled(bool(self.redo_history))
        if hasattr(self,'build_hint'):
            missing=[]
            if self.mesh is None:missing.append('nạp file quét')
            if not self.scale_confirm.isChecked():missing.append('xác nhận kích thước ở bước 1')
            if not self.ready_landmarks():missing.append('đặt đủ 3 mốc ở bước 2')
            if not self.region_confirm.isChecked():missing.append('xác nhận vùng ở bước 2')
            self.build_hint.setText('Còn thiếu: '+ '; '.join(missing) if missing else 'Đủ thông tin để tạo bản xem trước nghiên cứu.')
        self.update_guidance()
    def ready_landmarks(self):return all(k in self.landmarks for k in ['proximal','distal','side'])
    def update_marker_labels(self):
        if not hasattr(self,'marker_labels'):return
        for k,w in self.marker_labels.items():w.setText('Đã đặt trên hình' if k in self.landmarks else 'Chưa chọn')
        if self.ready_landmarks():
            length=np.linalg.norm(np.asarray(self.landmarks['distal'])-self.landmarks['proximal'])
            self.marker_labels['distal'].setText(f'Đã đặt • hai mốc cách nhau {length:.1f} mm')
    def cancel_pick(self):
        self.pick_session+=1;self.guided_pick_queue=[];self.pick_mode=None
        self.plotter.disable_picking();self.pick_hint.setText('Xoay hình: chuột trái • Phóng to: cuộn chuột')
        self.update_actions()

    def start_guided_pick(self):
        if self.worker or self.mesh is None:return
        self.cancel_pick();self.steps.setCurrentRow(1)
        if self.ready_landmarks():self.clear_landmarks()
        self.guided_pick_queue=[k for k in ('proximal','distal','side') if k not in self.landmarks]
        self.continue_guided_pick(self.pick_session)

    def continue_guided_pick(self,token):
        if token!=self.pick_session or self.worker or self.steps.currentRow()!=1:return
        if self.guided_pick_queue:self.start_pick(self.guided_pick_queue.pop(0),guided=True)

    def start_pick(self,mode,guided=False):
        if self.worker:self.work_label.setText('Chờ xử lý xong rồi chọn mốc.');return
        if self.mesh is None:self.error('Nạp mesh trước khi chọn điểm.');return
        if not guided:self.pick_session+=1;self.guided_pick_queue=[]
        self.pick_mode=mode;self.show_scan.setChecked(True);self.render();self.plotter.disable_picking()
        self.plotter.enable_surface_point_picking(callback=self.on_pick,show_message=False,show_point=False,left_clicking=False,picker='cell',pickable_window=False)
        names={'proximal':'đầu nẹp phía khuỷu','distal':'đầu nẹp phía bàn tay','side':'giữa mặt đặt nẹp',
            'relief':'tâm vùng cần tránh tì đè','measure_a':'mốc đo A','measure_b':'mốc đo B'}
        self.pick_hint.setText('Nhấp CHUỘT PHẢI lên da để chọn '+names[mode]+'.')
        self.update_actions()
    def on_pick(self,point):
        if not self.pick_mode or self.mesh is None or self.worker:return
        point=np.asarray(point,dtype=float)
        if point.shape!=(3,) or not np.isfinite(point).all():return
        _,nearest=self.mesh.find_closest_cell(point,return_closest_point=True)
        point=np.asarray(nearest).tolist();mode=self.pick_mode;self.pick_mode=None
        if mode.startswith('measure_'):
            self.calibration[mode]=point
            self.update_calibration_label();self.scale_reference_changed()
        elif mode=='relief':
            self.reliefs.append({'name':self.relief_name.text(),'point':point,'radius_mm':self.relief_radius.value(),'extra_mm':self.relief_extra.value()})
            self.refresh_reliefs();self.invalidate()
        else:self.landmarks[mode]=point;self.region_confirm.setChecked(False);self.invalidate()
        self.pick_hint.setText('Đã chọn. Xoay hình bằng chuột trái; chọn nút khác để đặt mốc tiếp.');self.plotter.disable_picking();self.render()
        if self.guided_pick_queue:
            token=self.pick_session;QTimer.singleShot(0,lambda:self.continue_guided_pick(token))
        elif mode in ('proximal','distal','side') and self.ready_landmarks():
            self.pick_hint.setText('Đã đủ 3 mốc. Kiểm tra vị trí 1, 2, 3 rồi tích xác nhận vùng ở bên phải.')
        self.update_actions()
    def suggest_landmarks(self):
        if self.mesh is None:return
        self.cancel_pick()
        s=suggested_points(self.mesh);self.landmarks={k:s[k] for k in ['proximal','distal','side']}
        self.region_confirm.setChecked(False);self.invalidate()
        self.pick_hint.setText('Mốc gợi ý hình học cần chọn lại và xác nhận; app chưa biết đầu nào là khuỷu.')
    def clear_landmarks(self):
        self.cancel_pick();self.landmarks={};self.region_confirm.setChecked(False);self.invalidate()
    def update_calibration_label(self):
        if all(k in self.calibration for k in ('measure_a','measure_b')):
            d=np.linalg.norm(np.asarray(self.calibration['measure_a'])-self.calibration['measure_b'])
            self.measured_label.setText(f'Trên mesh: {d:.2f} mm (đường thẳng A–B)')
        else:self.measured_label.setText('Chưa chọn đủ hai mốc đo A–B trên bề mặt.')
    def refresh_reliefs(self):
        self.relief_list.clear()
        for r in self.reliefs:self.relief_list.addItem(f"{r['name']} • thêm {r['extra_mm']:g} mm • bán kính {r['radius_mm']:g} mm")
    def remove_relief(self):
        idx=self.relief_list.currentRow()
        if idx>=0:self.reliefs.pop(idx);self.refresh_reliefs();self.invalidate()
    def new_worker(self,task,**kwargs):
        if self.worker is not None:return False
        self.last_failure=None
        self.timer.stop();self.cancel_pick()
        self.worker=Worker(task,**kwargs);self.worker.progress.connect(self.progress_update)
        self.worker.success.connect(self.build_done if task=='build' else self.scan_done)
        self.worker.error.connect(self.worker_error);self.worker.finished.connect(self.worker_finished);self.update_actions();self.worker.start();return True
    def progress_update(self,pct,text):self.progress.setValue(pct);self.work_label.setText(text)
    def worker_finished(self):
        worker=self.worker;self.worker=None
        if worker:worker.deleteLater()
        self.update_actions()
        if self.rebuild_requested and self.live.isChecked() and self.ready_landmarks() and self.scale_confirm.isChecked() and self.region_confirm.isChecked():self.timer.start(700)
        self.rebuild_requested=False
    def worker_error(self,message):
        self.last_failure={'task':self.worker.task if self.worker else 'unknown','message':message,
            'at':datetime.now().astimezone().isoformat(),
            'attempted_path':getattr(self,'pending_path','') if self.worker and self.worker.task=='load' else self.mesh_path}
        self.restore_pending=None;self.rebuild_requested=False
        self.work_label.setText('Không xử lý được. Xuất báo cáo ở bước 1 hoặc bước 5 để kiểm tra lỗi.')
        self.record_event('worker_failed',**self.last_failure)
        self.error(message+'\n\nChi tiết được ghi tại: '+str(LOG_PATH))
    def load_file(self):
        path,_=QFileDialog.getOpenFileName(self,'Chọn dữ liệu quét','','Mesh (*.stl *.obj *.ply)')
        if path:self.load_path(path)
    def load_path(self,path):
        if self.worker:return
        self.pending_path=str(path);self.pending_scale=[1.,10.,1000.][self.unit.currentIndex()]
        self.new_worker('load',path=path,scale=self.pending_scale)
    def scan_done(self,scan):
        self.last_failure=None
        self.scan=scan;self.source=scan['source'];self.loading=True
        rescaling=self.worker is not None and self.worker.task=='rescale'
        if not rescaling:self.source_digest=scan.get('source_sha256');self.audit_events=[]
        self.mesh_path=getattr(self,'pending_path',self.mesh_path);self.scale_used=getattr(self,'pending_scale',self.scale_used);self.is_demo=not self.mesh_path
        self.component.clear()
        for i,piece in enumerate(scan['pieces']):self.component.addItem(f"Mảnh {i+1} • {piece['triangles']:,} mặt"+(' (lớn nhất)' if i==0 else ''),i)
        index=getattr(self,'pending_component',0) if rescaling else 0
        index=min(index,len(scan['pieces'])-1)
        self.component.setCurrentIndex(index);self.loading=False;self.install_piece(index)
        self.file_label.setText(Path(self.mesh_path).name if self.mesh_path else 'Mẫu tổng hợp — không phải người bệnh');self.scale_confirm.setChecked(self.is_demo and not rescaling)
        if self.restore_pending:
            data=self.restore_pending;self.restore_pending=None;idx=int(data.get('component_index',0))
            try:
                if not 0<=idx<len(scan['pieces']):raise ValueError('Mảnh quét đã lưu không còn tồn tại trong file nguồn.')
                self.component.setCurrentIndex(idx);self.apply_project(data)
            except Exception as exc:LOG.exception('Restore failed');self.error('Đã nạp mesh, nhưng chưa phục hồi được thông số: '+str(exc))
        self.history.clear();self.redo_history.clear();self.last_state=self.state_snapshot();self.update_actions();self.plotter.reset_camera()
        self.record_event('rescale' if rescaling else 'load_scan',scale_used=self.scale_used,source_sha256=self.source_digest)
        if scan['total_pieces']>1:self.work_label.setText('File có nhiều mảnh. Đang gợi ý mảnh lớn nhất; kiểm tra đúng chi trước khi tiếp tục.')
    def install_piece(self,index):
        self.cancel_pick()
        piece=self.scan['pieces'][index];self.mesh=piece['mesh'];self.visible_mesh=piece['display'];self.boundaries=piece['boundaries']
        self.landmarks={};self.reliefs=[];self.calibration={};self.refresh_reliefs();self.region_confirm.setChecked(False)
        self.scale_confirm.setChecked(False);self.update_calibration_label();self.pick_mode=None;self.plotter.disable_picking()
        self.reviewer.clear()
        # A new component or coordinate scale invalidates correspondence to tape measurements.
        self.loading=True
        for key in ('circumference_proximal_mm','circumference_mid_mm','circumference_distal_mm'):self.controls[key].setValue(0)
        self.loading=False
        s=piece['stats'];span=piece['suggested']['span_mm']
        dimensions=np.ptp(np.asarray(self.mesh.points),axis=0)
        self.scan_stats.setText(f"Bề mặt chọn: {s['triangles']:,} tam giác\nChiều dài hình học gợi ý: {span:.1f} mm\n"
            f"Kích thước hộp bao: {dimensions[0]:.1f} × {dimensions[1]:.1f} × {dimensions[2]:.1f} mm\n"
            f"Biên hở: {s['boundary_edges']:,} cạnh • Mảnh trong file: {self.scan['total_pieces']}\nBiên hở không tự động có nghĩa là mesh không dùng được.")
        self.scene_title.setText('DỮ LIỆU QUÉT • mm');self.invalidate();self.render();self.plotter.reset_camera()
    def change_component(self,index):
        if self.loading or index<0 or self.scan is None:return
        self.install_piece(index);self.history.clear();self.redo_history.clear();self.last_state=self.state_snapshot();self.update_actions()
    def install_mesh(self,mesh,path='',demo=False,scale=1.):
        self.pending_path=str(path);self.pending_scale=scale;self.scan_done(prepare_display(prepare_scan(mesh)))
    def load_demo(self):
        if self.worker:return
        self.demo_kind='forearm_v1';self.install_mesh(demo_mesh(),demo=True)
        self.loading=True;self.cast_template.setChecked(False);self.splint_type.setCurrentIndex(0);self.controls['hand_notch_depth_mm'].setValue(0);self.loading=False
        self.suggest_landmarks();self.region_confirm.setChecked(True)
    def load_cast_demo(self):
        if self.worker:return
        from cast_template import hand_demo_mesh
        self.demo_kind='hand_envelope_v1'
        self.install_mesh(hand_demo_mesh(),demo=True)
        self.loading=True
        self.landmarks={'proximal':[34.,0.,15.],'distal':[40.,0.,288.],'side':[25.,0.,175.]}
        self.controls['hand_notch_depth_mm'].setValue(35)
        self.cast_template.setChecked(True);self.ventilation.setChecked(True);self.splint_type.setCurrentIndex(2)
        self.loading=False;self.scale_confirm.setChecked(True);self.region_confirm.setChecked(True)
        self.invalidate();self.update_marker_labels();self.plotter.reset_camera();self.steps.setCurrentRow(2)
    def calibrate_scale(self):
        if self.worker or self.source is None:return
        if not all(k in self.calibration for k in ['measure_a','measure_b']):self.error('Chọn đủ hai mốc đo A và B.');return
        measured=np.linalg.norm(np.asarray(self.calibration['measure_a'])-self.calibration['measure_b'])
        if measured<.001:self.error('Hai mốc đo quá gần nhau.');return
        ratio=self.real_distance.value()/measured;updated=self.source.copy();updated.points=np.asarray(updated.points,dtype=float)*ratio
        self.pending_component=self.component.currentIndex()
        self.pending_path=self.mesh_path;self.pending_scale=self.scale_used*ratio;self.scale_confirm.setChecked(False);self.restore_pending=None
        self.new_worker('rescale',mesh=updated)
    def start_build(self):
        if self.worker or self.mesh is None:return
        if not self.scale_confirm.isChecked():
            self.steps.setCurrentRow(0)
            self.scale_confirm.setFocus()
            self.error('Chưa xác nhận kích thước thực.\n\n'
                'Ở bước 1, kiểm tra kích thước rồi tích ô “Đã đối chiếu đúng kích thước thực”.\n'
                'Nếu cần sửa tỷ lệ: chọn mốc đo A–B, nhập khoảng cách thực và bấm “Hiệu chỉnh theo số đo” trước.\n\n'
                'Nhập số đo hoặc chọn mốc vùng nẹp chưa tự xác nhận kích thước; sau hiệu chỉnh cần xác nhận lại.')
            return
        if not self.ready_landmarks() or not self.region_confirm.isChecked():
            names={'proximal':'đầu nẹp phía khuỷu','distal':'đầu nẹp phía bàn tay','side':'giữa mặt đặt nẹp'}
            missing=[title for key,title in names.items() if key not in self.landmarks]
            reason='Còn thiếu mốc: '+', '.join(missing)+'.' if missing else 'Đã đủ mốc nhưng chưa tích “Đã xác nhận các mốc và vùng cần cố định”.'
            self.steps.setCurrentRow(1);self.error(reason+'\nKiểm tra ở bước 2 rồi tạo lại.');return
        self.timer.stop();self.result=None;self.review.setChecked(False);self.build_revision=self.revision
        self.new_worker('build',mesh=self.mesh.copy(),params=self.parameters())
    def build_done(self,result):
        if self.build_revision!=self.revision:self.work_label.setText('Thông số đã đổi; bỏ kết quả cũ. Tạo lại thiết kế.');return
        self.result=result;r=result['report']
        self.record_event('build',status=result['status'],parameters=asdict(self.parameters()))
        if result['status']=='preview_only':
            self.result_status.setText('Chưa tạo được vỏ hoàn chỉnh. Vùng màu cam cần xử lý trước khi xuất.')
            self.report_label.setText('ĐÃ GIỮ VÙNG XEM TRƯỚC\n\n'+'\n'.join(r['messages'])+'\n\nBật Biên hở để xem vị trí cần xử lý.')
            self.export_summary.setText('Vùng chọn cần xử lý thêm. Có thể xuất báo cáo lỗi.');self.show_holes.setChecked(True)
        else:
            self.result_status.setText('Đã tạo vỏ nghiên cứu. Xoay xem hình và đọc kiểm tra bên dưới.' if result['export_ready'] else 'Đã có vỏ xem trước, nhưng số đo đối chiếu đang chặn xuất.')
            if not self.live.isChecked():
                self.show_shell.blockSignals(True);self.show_shell.setChecked(True);self.show_shell.blockSignals(False)
                self.show_cage.blockSignals(True);self.show_cage.setChecked(False);self.show_cage.blockSignals(False)
            self.report_label.setText(f"Chiều dài nẹp: {r['length_mm']:.1f} mm\nKhoảng chừa danh nghĩa: {r['nominal_clearance_min_mm']:.2f}–{r['nominal_clearance_max_mm']:.2f} mm\n"
                f"Vỏ: {r['shell']['boundary_edges']} cạnh hở • {r['shell']['nonmanifold_edges']} cạnh lỗi\nSai lệch xấp xỉ scan lấy mẫu: {r['decimation_sampled_max_mm']:.3f} mm\n\n"
                f"Khoảng cách tới quét (lấy mẫu): {r['sampled_unsigned_surface_distance_min_mm']:.2f}–{r['sampled_unsigned_surface_distance_max_mm']:.2f} mm\n\n"
                +'\n'.join(r['messages'])+'\n\nChưa kiểm tự giao, áp lực, độ bền hoặc sai lệch sau T-Spline.')
            self.export_summary.setText('Chưa xuất: đối chiếu chu vi chưa đạt. Xem bước 4.' if not result['export_ready'] else 'Có OBJ để sửa Form + STL tham chiếu + vỏ thử nghiệm + JSON.' if result['form_available'] else
                'Có vỏ và STL tham chiếu + JSON. Chưa có OBJ Form vì lưới quá lớn; cần retopology.')
            sections=[]
            for row in r.get('circumference_checks',[]):
                name={'proximal':'Phía khuỷu','middle':'Giữa','distal':'Phía bàn tay'}[row['name']]
                measured='không có một vòng kín' if row['circumference_mm'] is None else f"{row['circumference_mm']:.1f} mm"
                actual='chưa nhập số đo' if row['real_mm'] is None else f"thước {row['real_mm']:.1f} mm; lệch {row['difference_mm']:+.1f} mm" if row['difference_mm'] is not None else 'chưa đo được để đối chiếu'
                sections.append(f'{name}: mesh {measured}; {actual}')
            checklist=['• '+c['name']+': '+{'PASSED':'Đạt kiểm tra hình học','PASSED_SAMPLED':'Chưa phát hiện lỗi ở mẫu kiểm','FAILED':'Chưa đạt','NOT_ENTERED':'Chưa nhập','NOT_VALIDATED':'Chưa kiểm định'}[c['status']] for c in r.get('technical_checks',[])]
            self.report_label.setText(self.report_label.text()+'\n\nĐỐI CHIẾU CHU VI\n'+'\n'.join(sections)+'\n\n'+'\n'.join(checklist))
        self.render();self.update_actions()
        if not self.live.isChecked():self.steps.setCurrentRow(3)
    def render(self,*_):
        if self.loading or self.mesh is None:return
        camera=self.plotter.camera_position;self.plotter.clear();self.plotter.add_axes()
        if self.show_scan.isChecked():self.plotter.add_mesh(self.visible_mesh,color='#D7B59C',opacity=.5 if self.result and not self.pick_mode else 1,smooth_shading=True,name='scan',pickable=True)
        if self.show_holes.isChecked() and self.boundaries.n_points:self.plotter.add_mesh(self.boundaries,color='#C62828',line_width=4,pickable=False)
        if self.result and not self.pick_mode:
            if self.result['status']=='preview_only' and self.result['patch'] is not None and self.result['patch'].n_cells:
                self.plotter.add_mesh(self.result['patch'],color='#E8AA46',opacity=.9,pickable=False)
            elif self.result['inner'] is not None:
                inner=self.result['inner']
                if self.show_cage.isChecked():
                    if self.show_heatmap.isChecked():self.plotter.add_mesh(inner,scalars='measured_scan_distance_mm',cmap='viridis',scalar_bar_args={'title':'Khoang cach toi quet (mm)'},pickable=False)
                    else:self.plotter.add_mesh(inner,color='#89BFE3',opacity=.9,pickable=False)
                if self.show_shell.isChecked():self.plotter.add_mesh(self.result['shell'],color='#4C95C9',opacity=.8,pickable=False)
                if self.show_normals.isChecked():
                    pts=inner.points;ids=np.linspace(0,len(pts)-1,min(60,len(pts)),dtype=int)
                    self.plotter.add_arrows(pts[ids],self.result['normals'][ids],mag=6,color='#D8702D',pickable=False)
        colors={'proximal':'#0F6CBD','distal':'#0F6CBD','side':'#2E7D32'}
        for k,point in self.landmarks.items():self.plotter.add_mesh(pv.Sphere(radius=max(self.mesh.length*.008,1),center=point),color=colors[k],pickable=False)
        if self.landmarks:
            names={'proximal':'1 - Phia khuyu','distal':'2 - Phia ban tay','side':'3 - Mat dat nep'}
            keys=list(self.landmarks)
            self.plotter.add_point_labels(np.asarray([self.landmarks[k] for k in keys]),[names[k] for k in keys],
                show_points=False,font_size=12,text_color='#183B56',shape_color='white',shape_opacity=.85,
                pickable=False,always_visible=True,reset_camera=False,render=False)
        if 'proximal' in self.landmarks and 'distal' in self.landmarks:self.plotter.add_mesh(pv.Line(self.landmarks['proximal'],self.landmarks['distal']),color='#0F6CBD',line_width=3,pickable=False)
        for r in self.reliefs:self.plotter.add_mesh(pv.Sphere(radius=2,center=r['point']),color='#ED8B00',pickable=False)
        for point in self.calibration.values():self.plotter.add_mesh(pv.Sphere(radius=1.5,center=point),color='#8E44AD',pickable=False)
        if self.steps.currentRow()==3 and self.ready_landmarks():
            try:
                origin,z,x,y,start,end=clinical_frame(self.mesh,self.parameters())
                for fraction in (0.,.5,1.):
                    contour=self.mesh.slice(normal=z,origin=origin+z*(start+(end-start)*fraction))
                    if contour.n_points:self.plotter.add_mesh(contour,color='#8E44AD',line_width=4,pickable=False)
            except ValueError:pass
        self.plotter.camera_position=camera;self.plotter.render()
    def view_direction(self,longitudinal=False):
        if self.mesh is None:return
        try:
            origin,z,x,y,*_=clinical_frame(self.mesh,self.parameters())
        except ValueError as exc:
            self.work_label.setText('Chọn đủ hai đầu nẹp trước khi đổi góc nhìn theo vùng.')
            self.error(str(exc));return
        direction,up=(z,y) if longitudinal else (x,z)
        self.plotter.camera_position=[origin+direction*self.mesh.length*1.5,origin,up]
    def view_long(self):self.view_direction(longitudinal=True)
    def view_side(self):self.view_direction()
    def metadata(self):
        return {'case_id':self.case_id.text(),'side':self.side.currentText(),'stage':self.stage.currentText(),'indication':self.indication.text(),'scan_posture':self.posture.text(),
            'source_filename':Path(self.mesh_path).name if self.mesh_path else 'SYNTHETIC_DEMO','synthetic_demo':self.is_demo,'scale_used':self.scale_used,
            'scale_user_confirmed':self.scale_confirm.isChecked(),'clinical_region_user_confirmed':self.region_confirm.isChecked(),
            'splint_type_label':self.splint_type.currentText(),'reviewer':self.reviewer.text().strip(),'source_sha256':self.source_digest,
            'software_version':'4.0.1-prototype','geometry_revision':self.revision,'synthetic_demo_kind':self.demo_kind,
            'finishing_requested_not_generated':{'strap_count':self.strap_count.value(),'edge_radius_mm':self.edge_radius.value(),'notes':self.finishing_notes.toPlainText()},
            'metadata_at':datetime.now().astimezone().isoformat()}
    def export_files(self):
        if self.result is None or not self.result.get('export_ready') or self.build_revision!=self.revision:self.error('Cần cập nhật thiết kế và xử lý vùng quét lỗi trước khi xuất.');return
        if not self.review.isChecked():self.error('Xem lại vùng phủ, số đo và hướng mặt trong trước khi xuất.');return
        if not self.reviewer.text().strip():self.error('Nhập tên người kiểm tra bản nghiên cứu ở bước 5. Đây là dấu vết kiểm tra, không phải xác nhận an toàn lâm sàng.');return
        parent=QFileDialog.getExistingDirectory(self,'Chọn thư mục chứa gói thiết kế')
        if not parent:return
        try:
            self.record_event('export_requested',reviewer=self.reviewer.text().strip(),parameters=asdict(self.parameters()))
            metadata=self.metadata();metadata['audit_events']=self.audit_events;metadata['reviewed_at']=datetime.now().astimezone().isoformat()
            metadata['exported_at']=metadata['reviewed_at']
            folder=export_bundle(Path(parent)/('SplintFit_export_'+datetime.now().strftime('%Y%m%d_%H%M%S_%f')),self.source,self.result,self.parameters(),metadata)
            self.last_export_folder=folder;self.export_location.setText('Đã xuất mô hình tại:\n'+str(folder));self.update_actions()
            QMessageBox.information(self,'Đã xuất mô hình 3D',f'Gói mô hình và hồ sơ:\n{folder}\n\nBấm Mở thư mục kết quả ở bước 5. Đọc FUSION_FORM.md để tiếp tục trong Fusion.')
        except Exception as exc:LOG.exception('Export failed');self.error(str(exc))
    def diagnostic_data(self):
        return {'application':'SplintFit v4.0.1 prototype','mesh_path':self.mesh_path,'metadata':self.metadata(),'parameters':asdict(self.parameters()),'audit_events':self.audit_events,
            'last_failure':self.last_failure,
            'runtime':{'python':sys.version,'platform':sys.platform,'pyvista':pv.__version__,'vtk':str(pv.vtk_version_info)},
            'source_stats':self.scan['stats'] if self.scan else None,'selected_component_index':self.component.currentIndex(),
            'selected_stats':stats(self.mesh) if self.mesh is not None else None,'result_report':self.result['report'] if self.result else None,
            'note':'No mesh bytes included. Report can include case identifier and local path.'}
    def export_diagnostic(self):
        path,_=QFileDialog.getSaveFileName(self,'Xuất báo cáo kiểm tra','SplintFit_diagnostic.json','JSON (*.json)')
        if not path:return
        try:Path(path).write_text(json.dumps(self.diagnostic_data(),ensure_ascii=False,indent=2),encoding='utf-8')
        except Exception as exc:self.error(str(exc))
    def save_project(self):
        if self.worker:self.error('Chờ thao tác đang chạy kết thúc rồi lưu dự án.');return
        if self.mesh is None:self.error('Nạp dữ liệu quét trước khi lưu dự án.');return
        path,_=QFileDialog.getSaveFileName(self,'Lưu dự án','project.splintfit.json','JSON (*.json)')
        if not path:return
        try:
            self.record_event('save_project')
            target=Path(path);data={'schema':'splintfit.desktop.v3','mesh_path':mesh_reference(self.mesh_path,target.parent),
                'metadata':self.metadata(),'params':asdict(self.parameters()),'state':self.state_snapshot(),'component_index':self.component.currentIndex()}
            data['audit_events']=self.audit_events
            atomic_write_json(target,data);self.work_label.setText('Đã lưu dự án JSON để làm tiếp. Muốn có mô hình OBJ/STL: dùng bước 5 — Xuất mô hình 3D.')
        except Exception as exc:self.error(str(exc))
    def open_project(self):
        path,_=QFileDialog.getOpenFileName(self,'Mở dự án','','JSON (*.json)')
        if not path or self.worker:return
        try:
            data=validated_project(json.loads(Path(path).read_text(encoding='utf-8')))
            meta=data['metadata']
            if meta.get('synthetic_demo'):
                scale=float(meta['scale_used'])
                from cast_template import hand_demo_mesh
                self.demo_kind=meta.get('synthetic_demo_kind','forearm_v1')
                mesh=hand_demo_mesh() if self.demo_kind=='hand_envelope_v1' else demo_mesh()
                mesh.points=np.asarray(mesh.points,dtype=float)*scale
                self.install_mesh(mesh,demo=True,scale=scale);self.suggest_landmarks();self.apply_project(data)
            else:
                target=(Path(path).parent/data['mesh_path']).resolve()
                if not target.is_file():raise ValueError('Không tìm thấy mesh được tham chiếu trong dự án.')
                self.restore_pending=data;self.pending_path=str(target);self.pending_scale=float(meta['scale_used']);self.new_worker('load',path=str(target),scale=self.pending_scale,expected_sha256=meta.get('source_sha256'))
        except Exception as exc:LOG.exception('Project load failed');self.error(str(exc))
    def apply_project(self,data):
        p=Parameters(**data['params']);meta=data['metadata']
        for k,w in self.controls.items():
            value=getattr(p,k)
            if not isinstance(value,(int,float)) or not np.isfinite(value) or not w.minimum()<=value<=w.maximum():raise ValueError('Thông số ngoài phạm vi: '+k)
        self.loading=True
        try:
            self.case_id.setText(str(meta.get('case_id','CASE-001')));self.side.setCurrentText(meta.get('side','Tay trái'));self.stage.setCurrentText(meta.get('stage','Chưa ghi giai đoạn'))
            self.indication.setText(meta.get('indication',''));self.posture.setText(meta.get('scan_posture',''));self.flip.setChecked(p.flip_normals)
            self.cast_template.setChecked(p.cast_template);self.ventilation.setChecked(p.ventilation)
            for k,w in self.controls.items():
                value=getattr(p,k);w.setValue(int(value) if isinstance(w,QSpinBox) else value)
            if data['schema'] in ('splintfit.desktop.v2','splintfit.desktop.v3'):
                self.landmarks={k:v for k,v in [('proximal',p.proximal_point),('distal',p.distal_point),('side',p.side_point)] if v is not None}
                self.reliefs=p.reliefs or [];self.splint_type.setCurrentIndex(data['state']['type']);self.coverage.setCurrentIndex(data['state']['coverage'])
                finish=meta.get('finishing_requested_not_generated',{});self.strap_count.setValue(finish.get('strap_count',3));self.edge_radius.setValue(finish.get('edge_radius_mm',2));self.finishing_notes.setPlainText(finish.get('notes',''))
            two=self.splint_type.currentIndex()==2;self.coverage.setEnabled(not two);self.controls['seam_gap_mm'].setEnabled(two)
            self.seam_form.setRowVisible(self.controls['seam_gap_mm'],two)
            self.region_confirm.setChecked(self.is_demo);self.scale_confirm.setChecked(self.is_demo)
            self.audit_events=data.get('audit_events',[]).copy();self.record_event('open_project')
        finally:self.loading=False
        self.last_state=self.state_snapshot();self.invalidate();self.refresh_reliefs();self.steps.setCurrentRow(0)
    def dragEnterEvent(self,event):
        if event.mimeData().hasUrls() and not self.worker:event.acceptProposedAction()
    def dropEvent(self,event):
        for url in event.mimeData().urls():
            path=url.toLocalFile()
            if Path(path).suffix.lower() in ['.stl','.obj','.ply']:self.load_path(path);event.acceptProposedAction();break
    def error(self,message):QMessageBox.warning(self,'Cần kiểm tra',message)
    def closeEvent(self,event):
        if self.worker:self.work_label.setText('Chờ thao tác hiện tại kết thúc trước khi đóng.');event.ignore();return
        self.timer.stop();self.cancel_pick();self.plotter.close();event.accept()


if __name__=='__main__':
    app=QApplication(sys.argv);window=SplintFit();window.show();sys.exit(app.exec())
