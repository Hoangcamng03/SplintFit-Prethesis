import os,sys,json,tempfile,time,unittest
from pathlib import Path
from unittest.mock import patch
import numpy as np
if sys.platform.startswith('linux') and not os.environ.get('DISPLAY'):
    os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from app import QApplication,SplintFit,QFileDialog
from geometry import demo_mesh,build
import pyvista as pv


class WorkflowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.qt=QApplication.instance() or QApplication([])
    def setUp(self):
        self.w=SplintFit();self.w.render=lambda *a:None
        self.errors=[];self.w.error=self.errors.append
    def wait_worker(self):
        deadline=time.monotonic()+15
        while self.w.worker and time.monotonic()<deadline:
            self.qt.processEvents();time.sleep(.005)
        self.assertIsNone(self.w.worker)
    def tearDown(self):
        if self.w.worker:self.wait_worker()
        self.w.close()

    def test_changing_component_clears_old_scale_confirmation_and_measurement_text(self):
        mesh=demo_mesh().merge(pv.Sphere(radius=3,center=(200,0,100)))
        self.w.install_mesh(mesh)
        self.w.scale_confirm.setChecked(True)
        self.w.calibration={'measure_a':[0,0,0],'measure_b':[0,0,100]}
        self.w.update_calibration_label()
        self.w.component.setCurrentIndex(1)
        self.assertFalse(self.w.scale_confirm.isChecked())
        self.assertEqual(self.w.calibration,{})
        self.assertIn('Chưa chọn',self.w.measured_label.text())

    def test_scale_reference_change_invalidates_result_and_confirmation(self):
        self.w.load_demo();self.w.build_revision=self.w.revision
        self.w.build_done(build(self.w.mesh,self.w.parameters()))
        self.w.real_distance.setValue(123)
        self.assertFalse(self.w.scale_confirm.isChecked())
        self.assertIsNone(self.w.result)
        self.assertIn('xác nhận kích thước',self.w.build_hint.text())

    def test_relabeling_splint_does_not_discard_landmark_confirmation(self):
        self.w.load_demo();before=self.w.landmarks.copy()
        self.w.splint_type.setCurrentIndex(1)
        self.assertTrue(self.w.region_confirm.isChecked())
        self.assertEqual(self.w.landmarks,before)

    def test_changing_measurement_plane_clears_tape_measurements(self):
        self.w.load_demo();self.w.controls['circumference_mid_mm'].setValue(200)
        self.w.controls['start_adjust_mm'].setValue(5)
        self.assertEqual(self.w.controls['circumference_mid_mm'].value(),0)

    def test_invalid_project_is_rejected_before_changing_current_case(self):
        self.w.load_demo();self.w.case_id.setText('KEEP-THIS-CASE')
        before=self.w.state_snapshot()
        with tempfile.TemporaryDirectory() as temp:
            file=Path(temp)/'case.json'
            with patch.object(QFileDialog,'getSaveFileName',return_value=(str(file),'')):self.w.save_project()
            data=json.loads(file.read_text());data['state']['type']=99;data['metadata']['case_id']='BAD'
            file.write_text(json.dumps(data))
            with patch.object(QFileDialog,'getOpenFileName',return_value=(str(file),'')):self.w.open_project()
        self.assertEqual(self.w.case_id.text(),'KEEP-THIS-CASE')
        self.assertEqual(self.w.state_snapshot(),before)
        self.assertTrue(self.errors)

    def test_changed_source_file_is_rejected_on_project_open(self):
        with tempfile.TemporaryDirectory() as temp:
            meshfile=Path(temp)/'arm.stl';project=Path(temp)/'case.json'
            demo_mesh().save(meshfile);self.w.load_path(str(meshfile));self.wait_worker()
            self.assertIsNotNone(self.w.source_digest)
            with patch.object(QFileDialog,'getSaveFileName',return_value=(str(project),'')):self.w.save_project()
            before=self.w.mesh.points.copy()
            demo_mesh().translate([100,0,0],inplace=False).save(meshfile)
            with patch.object(QFileDialog,'getOpenFileName',return_value=(str(project),'')):self.w.open_project()
            self.wait_worker()
            self.assertTrue(any('Mesh nguồn đã thay đổi' in e for e in self.errors))
            np.testing.assert_allclose(self.w.mesh.points,before)

    def test_reviewer_name_required_and_metadata_edits_reset_review(self):
        self.w.load_demo();self.w.build_revision=self.w.revision
        self.w.build_done(build(self.w.mesh,self.w.parameters()))
        self.w.review.setChecked(True)
        with patch.object(QFileDialog,'getExistingDirectory') as choose:
            self.w.export_files();choose.assert_not_called()
        self.assertTrue(any('Nhập tên' in e for e in self.errors))
        self.w.reviewer.setText('Tester');self.w.review.setChecked(True)
        self.w.case_id.setText('OTHER-CASE')
        self.assertFalse(self.w.review.isChecked())

    def test_rescale_preserves_selected_component_and_resets_landmarks(self):
        mesh=demo_mesh().merge(pv.Sphere(radius=3,center=(200,0,100)))
        self.w.install_mesh(mesh);self.w.component.setCurrentIndex(1)
        before=np.ptp(self.w.mesh.points,axis=0)
        self.w.calibration={'measure_a':[197,0,100],'measure_b':[203,0,100]}
        self.w.real_distance.setValue(12);self.w.calibrate_scale();self.wait_worker()
        self.assertEqual(self.w.component.currentIndex(),1)
        np.testing.assert_allclose(np.ptp(self.w.mesh.points,axis=0),before*2,atol=1e-4)
        self.assertEqual(self.w.landmarks,{})
        self.assertFalse(self.w.scale_confirm.isChecked())
