"""User journeys: required checks remain manual and model export stays distinct."""
import os
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch,MagicMock

if sys.platform.startswith('linux') and not os.environ.get('DISPLAY'):
    os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from app import QApplication,SplintFit,QFileDialog,QMessageBox,QDesktopServices
from geometry import build


class GuidedJourneyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.qt=QApplication.instance() or QApplication([])

    def setUp(self):
        self.w=SplintFit();self.w.render=lambda *args:None
        self.errors=[];self.w.error=self.errors.append

    def wait_worker(self):
        deadline=time.monotonic()+15
        while self.w.worker and time.monotonic()<deadline:
            self.qt.processEvents();time.sleep(.005)
        self.assertIsNone(self.w.worker)

    def tearDown(self):
        if self.w.worker:self.wait_worker()
        self.w.close();self.qt.processEvents()

    def build_demo(self):
        self.w.load_demo();self.w.build_revision=self.w.revision
        self.w.build_done(build(self.w.mesh,self.w.parameters()))

    def test_empty_case_guide_opens_file_picker(self):
        self.assertEqual(self.w.workflow_hint()[3],'load')
        with patch.object(QFileDialog,'getOpenFileName',return_value=('','')) as choose:
            self.w.guide_button.click();choose.assert_called_once()
        self.assertIsNone(self.w.mesh)

    def test_navigation_never_confirms_scale_or_region_for_user(self):
        self.w.load_demo();self.w.scale_confirm.setChecked(False)
        self.w.steps.setCurrentRow(4);self.w.guide_button.click()
        self.assertEqual(self.w.steps.currentRow(),0)
        self.assertFalse(self.w.scale_confirm.isChecked())
        self.w.go_forward(1);self.assertEqual(self.w.steps.currentRow(),0)
        self.w.scale_confirm.setChecked(True);self.w.clear_landmarks();self.w.go_forward(2)
        self.assertEqual(self.w.steps.currentRow(),1)
        self.assertFalse(self.w.region_confirm.isChecked())

    def test_guided_three_points_advance_and_still_require_confirmation(self):
        self.w.load_demo();self.w.start_guided_pick()
        for mode,point in [('proximal',[25,0,25]),('distal',[32,0,195]),('side',[29,0,115])]:
            self.assertEqual(self.w.pick_mode,mode)
            self.assertIn('CHUỘT PHẢI',self.w.guide_detail.text())
            self.w.on_pick(point);self.qt.processEvents()
        self.assertTrue(self.w.ready_landmarks())
        self.assertFalse(self.w.region_confirm.isChecked())
        self.assertIsNone(self.w.pick_mode)
        self.assertEqual(self.w.workflow_hint()[3],'region')

    def test_leaving_step_cancels_queued_next_point(self):
        self.w.load_demo();self.w.start_guided_pick();self.w.on_pick([25,0,25])
        self.w.steps.setCurrentRow(2);self.qt.processEvents()
        self.assertIsNone(self.w.pick_mode)
        self.assertEqual(self.w.guided_pick_queue,[])
        self.assertNotIn('distal',self.w.landmarks)

    def test_manual_pick_cannot_be_overridden_by_old_guided_callback(self):
        self.w.load_demo();self.w.start_guided_pick();self.w.on_pick([25,0,25])
        self.w.start_pick('measure_a');self.qt.processEvents()
        self.assertEqual(self.w.pick_mode,'measure_a')
        self.assertEqual(self.w.guided_pick_queue,[])

    def test_guided_pick_resumes_partial_landmarks(self):
        self.w.load_demo();self.w.clear_landmarks();self.w.landmarks={'proximal':[25.,0.,25.]}
        self.w.invalidate();self.w.start_guided_pick()
        self.assertEqual(self.w.pick_mode,'distal')
        self.assertEqual(self.w.landmarks['proximal'],[25.,0.,25.])

    def test_jump_to_export_without_model_routes_to_build(self):
        self.w.load_demo();self.w.steps.setCurrentRow(4)
        self.assertEqual(self.w.workflow_hint()[3],'build')
        self.w.guide_button.click();self.wait_worker()
        self.assertIsNotNone(self.w.result)
        self.assertTrue(self.w.result['export_ready'])
        self.assertTrue(self.w.show_shell.isChecked())
        self.assertEqual(self.w.steps.currentRow(),3)
        self.assertFalse(self.errors)

    def test_export_journey_requires_reviewer_and_review_then_opens_real_folder(self):
        self.build_demo();self.w.go_forward(4)
        self.assertEqual(self.w.workflow_hint()[3],'reviewer')
        self.w.guide_button.click();self.assertFalse(self.w.review.isChecked())
        self.w.reviewer.setText('Research tester')
        self.assertEqual(self.w.workflow_hint()[3],'review')
        self.w.guide_button.click();self.assertFalse(self.w.review.isChecked())
        self.w.review.setChecked(True)
        self.assertEqual(self.w.workflow_hint()[3],'export')
        with tempfile.TemporaryDirectory() as temp:
            with patch.object(QFileDialog,'getExistingDirectory',return_value=temp),patch.object(QMessageBox,'information'):
                self.w.guide_button.click()
            folder=self.w.last_export_folder
            self.assertTrue((folder/'splint_form_quad.obj').is_file())
            self.assertTrue((folder/'shell_prototype_NOT_CLINICALLY_VALIDATED.stl').is_file())
            self.assertEqual(self.w.workflow_hint()[3],'open_export')
            with patch.object(QDesktopServices,'openUrl',return_value=True) as opener:
                self.w.guide_button.click()
                self.assertEqual(opener.call_args.args[0].toLocalFile(),str(folder))
            self.w.controls['thickness_mm'].setValue(4)
            self.assertIsNone(self.w.last_export_folder)
            self.assertFalse(self.w.open_export_btn.isEnabled())

    def test_save_project_does_not_mark_model_as_exported(self):
        self.w.load_demo()
        with tempfile.TemporaryDirectory() as temp:
            file=Path(temp)/'project.splintfit.json'
            with patch.object(QFileDialog,'getSaveFileName',return_value=(str(file),'')):
                self.w.save_project()
            self.assertTrue(file.is_file())
            self.assertIsNone(self.w.last_export_folder)
            self.assertIsNone(self.w.result)
            self.assertIn('bước 5',self.w.work_label.text())

    def test_preview_only_result_cannot_advance_to_export(self):
        self.w.load_demo();self.w.build_revision=self.w.revision
        self.w.result={'status':'preview_only','export_ready':False,'report':{'messages':['Vùng quét thiếu dữ liệu.']}}
        self.w.go_forward(4)
        self.assertEqual(self.w.steps.currentRow(),3)
        self.assertEqual(self.w.workflow_hint()[3],'fix_region')
        self.assertIn('thiếu dữ liệu',self.w.workflow_hint()[1])

    def test_metadata_change_resets_export_confirmation_and_old_folder(self):
        self.build_demo();self.w.reviewer.setText('Tester');self.w.review.setChecked(True)
        self.w.last_export_folder=Path('/old/export');self.w.finishing_notes.setPlainText('Changed')
        self.assertFalse(self.w.review.isChecked())
        self.assertIsNone(self.w.last_export_folder)

    def test_blocked_circumference_guides_to_the_failing_input(self):
        self.w.load_demo();self.w.controls['circumference_distal_mm'].setValue(999)
        self.w.build_revision=self.w.revision
        self.w.build_done(build(self.w.mesh,self.w.parameters()))
        self.assertEqual(self.w.result['status'],'blocked')
        self.assertEqual(self.w.workflow_hint()[3],'measurements')
        self.w.guide_button.click()
        self.assertEqual(self.w.steps.currentRow(),3)
        self.assertTrue(self.w.circumference_toggle.isChecked())
        self.assertEqual(self.w.controls['circumference_distal_mm'].value(),999)
        self.assertFalse(self.w.result['export_ready'])

    def test_close_cancels_queued_guided_point(self):
        self.w.load_demo();self.w.start_guided_pick();self.w.on_pick([25,0,25])
        self.w.close();self.qt.processEvents()
        self.assertEqual(self.w.guided_pick_queue,[])
        self.assertIsNone(self.w.pick_mode)

    def test_scene_labels_points_without_making_them_pickable(self):
        self.w.load_demo()
        fake_plotter=MagicMock();fake_plotter.camera_position=self.w.plotter.camera_position
        with patch.object(self.w,'plotter',fake_plotter):
            SplintFit.render(self.w)
        args,kwargs=fake_plotter.add_point_labels.call_args
        self.assertEqual(len(args[0]),3)
        self.assertEqual(len(args[1]),3)
        self.assertFalse(kwargs['pickable'])
        self.assertTrue(kwargs['always_visible'])


if __name__=='__main__':unittest.main()
