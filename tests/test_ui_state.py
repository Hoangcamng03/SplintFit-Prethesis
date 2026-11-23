"""State tests use a headless Qt platform on Linux; no Windows/Fusion claim."""
import os
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch
if sys.platform.startswith('linux') and not os.environ.get('DISPLAY'):
    os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app import QApplication, SplintFit, QFileDialog, QMessageBox
from geometry import build


class UIStateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.qt = QApplication.instance() or QApplication([])

    def setUp(self):
        self.w = SplintFit()
        # Rendering is checked separately; here exercise project/revision logic.
        self.w.render = lambda *args: None
        self.w.error = lambda message: self.fail(message)

    def tearDown(self):
        if self.w.worker:
            self.w.worker.wait(15000)
            self.qt.processEvents()
        self.w.close()

    def test_background_build_then_parameter_change_invalidates_export(self):
        self.w.load_demo()
        self.w.start_build()
        deadline = time.monotonic()+15
        while self.w.worker and time.monotonic() < deadline:
            self.qt.processEvents()
            time.sleep(0.005)
        self.assertIsNone(self.w.worker)
        self.assertIsNotNone(self.w.result)
        self.assertTrue(self.w.export_btn.isEnabled())
        self.w.controls['thickness_mm'].setValue(4)
        self.assertIsNone(self.w.result)
        self.assertFalse(self.w.export_btn.isEnabled())

    def test_stale_worker_result_is_discarded(self):
        self.w.load_demo()
        result = build(self.w.mesh, self.w.parameters())
        self.w.build_revision = self.w.revision
        self.w.controls['thickness_mm'].setValue(4)
        self.w.build_done(result)
        self.assertIsNone(self.w.result)

    def test_project_roundtrip_and_export(self):
        self.w.load_demo()
        self.w.controls['thickness_mm'].setValue(4.2)
        with tempfile.TemporaryDirectory() as temp:
            project = str(Path(temp)/'project.json')
            with patch.object(QFileDialog, 'getSaveFileName', return_value=(project,'')):
                self.w.save_project()
            self.w.controls['thickness_mm'].setValue(3)
            with patch.object(QFileDialog, 'getOpenFileName', return_value=(project,'')):
                self.w.open_project()
            self.assertEqual(self.w.parameters().thickness_mm, 4.2)
            self.w.build_revision = self.w.revision
            self.w.build_done(build(self.w.mesh, self.w.parameters()))
            self.w.reviewer.setText('Research tester');self.w.review.setChecked(True)
            with patch.object(QFileDialog, 'getExistingDirectory', return_value=temp), patch.object(QMessageBox, 'information'):
                self.w.export_files()
            exports = list(Path(temp).glob('SplintFit_export_*'))
            self.assertEqual(len(exports),1)
            self.assertTrue((exports[0]/'splint_form_quad.obj').exists())
            self.assertTrue((exports[0]/'FUSION_FORM.md').exists())

    def test_landmark_selection_undo_and_advanced_mode(self):
        self.w.load_demo()
        before=self.w.landmarks['distal']
        self.w.pick_mode='distal'
        self.w.on_pick([29,0,150])
        self.assertNotEqual(self.w.landmarks['distal'],before)
        self.assertFalse(self.w.region_confirm.isChecked())
        self.w.undo()
        self.assertEqual(self.w.landmarks['distal'],before)
        self.w.mode.setCurrentIndex(1)
        self.assertFalse(self.w.expert_widgets[0].isHidden())

    def test_actual_file_import_runs_in_background(self):
        self.w.load_demo()
        with tempfile.TemporaryDirectory() as t:
            source=Path(t)/'arm.stl';self.w.mesh.save(source)
            self.w.load_path(str(source))
            deadline=time.monotonic()+15
            while self.w.worker and time.monotonic()<deadline:
                self.qt.processEvents();time.sleep(.005)
            self.assertIsNone(self.w.worker)
            self.assertEqual(self.w.mesh_path,str(source))
            self.assertGreater(self.w.mesh.n_cells,0)
            self.assertFalse(self.w.is_demo)
            self.assertFalse(self.w.scale_confirm.isChecked())

    def test_entered_measurements_and_landmarks_still_need_scale_confirmation(self):
        self.w.load_demo()
        self.w.scale_confirm.setChecked(False)
        self.w.real_distance.setValue(125)
        self.assertTrue(self.w.ready_landmarks())
        self.w.steps.setCurrentRow(2)
        errors=[]
        self.w.error=errors.append
        with patch.object(self.w,'new_worker') as launch:
            self.w.start_build()
            launch.assert_not_called()
            self.assertEqual(self.w.steps.currentRow(),0)
            self.assertEqual(len(errors),1)
            self.assertIn('Đã đối chiếu đúng kích thước thực',errors[0])
            self.w.scale_confirm.setChecked(True)
            self.w.start_build()
            launch.assert_called_once()
            self.assertEqual(launch.call_args.args[0],'build')


if __name__ == '__main__':
    unittest.main()
