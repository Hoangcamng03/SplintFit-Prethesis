import os,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
import numpy as np
if sys.platform.startswith('linux') and not os.environ.get('DISPLAY'):
    os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
from app import QApplication,SplintFit,QFileDialog


class CastUITests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.qt=QApplication.instance() or QApplication([])
    def setUp(self):
        self.w=SplintFit();self.w.render=lambda *args:None
        self.w.error=lambda m:self.fail(m)
    def tearDown(self):self.w.close()
    def test_cast_demo_save_open_keeps_correct_demo_geometry_and_settings(self):
        w=self.w;w.load_cast_demo();before=np.asarray(w.mesh.points).copy()
        w.ventilation.setChecked(False);w.controls['hole_pitch_mm'].setValue(30)
        with tempfile.TemporaryDirectory() as t:
            p=str(Path(t)/'case.json')
            with patch.object(QFileDialog,'getSaveFileName',return_value=(p,'')):w.save_project()
            w.load_demo()
            with patch.object(QFileDialog,'getOpenFileName',return_value=(p,'')):w.open_project()
        self.assertEqual(w.demo_kind,'hand_envelope_v1')
        np.testing.assert_allclose(w.mesh.points,before)
        self.assertTrue(w.parameters().cast_template);self.assertFalse(w.parameters().ventilation)
        self.assertEqual(w.parameters().hole_pitch_mm,30)
        self.assertEqual(w.parameters().splint_mode,'bivalve')
    def test_hole_controls_invalidate_prior_geometry(self):
        w=self.w;w.load_cast_demo();w.result={'dummy':True}
        w.controls['hole_ratio'].setValue(.6)
        self.assertIsNone(w.result)
        w.undo();self.assertAlmostEqual(w.parameters().hole_ratio,.48)


if __name__=='__main__':unittest.main()
