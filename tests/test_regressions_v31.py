"""Regression cases found while reviewing v3; no GPU/Fusion guarantee."""
import json
import os
import sys
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path
from unittest.mock import patch

if sys.platform.startswith('linux') and not os.environ.get('DISPLAY'):
    os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import numpy as np
import pyvista as pv
from app import QApplication, QFileDialog, SplintFit
from geometry import build, demo_mesh, export_bundle, read_mesh
from project_io import validated_project
from test_project_io_v3 import example
from test_geometry_v2 import clinical_params


class GeometryRegressionTests(unittest.TestCase):
    def test_stl_obj_ply_surface_import(self):
        mesh = demo_mesh()
        with tempfile.TemporaryDirectory() as temp:
            for suffix in ('stl', 'obj', 'ply'):
                with self.subTest(format=suffix):
                    file = Path(temp)/('arm.'+suffix)
                    mesh.save(file)
                    loaded = read_mesh(file)
                    self.assertEqual(loaded.n_cells, mesh.n_cells)
                    np.testing.assert_allclose(loaded.bounds, mesh.bounds, atol=1e-4)

    def test_point_cloud_rejected_with_actionable_message(self):
        with tempfile.TemporaryDirectory() as temp:
            file = Path(temp)/'cloud.ply'
            pv.PolyData(np.array([[0.,0,0], [1,0,0], [0,1,0]])).save(file)
            with self.assertRaisesRegex(ValueError, 'point cloud'):
                read_mesh(file)

    def test_bivalve_export_has_two_stls_and_interpiece_check(self):
        mesh = demo_mesh()
        params = replace(clinical_params(mesh), splint_mode='bivalve')
        result = build(mesh, params)
        self.assertEqual(result['report']['interpiece_check']['status'], 'NO_CONTACT_DETECTED')
        with tempfile.TemporaryDirectory() as temp:
            output = export_bundle(Path(temp)/'export', mesh, result, params, {})
            for index, piece in enumerate(result['pieces'], 1):
                saved = pv.read(output/f'shell_piece_{index}_prototype.stl')
                self.assertEqual(saved.n_cells, piece['shell'].n_cells)
            self.assertEqual(len(json.loads((output/'parameters_and_report.json').read_text())['pieces']), 2)

    def test_interpiece_contact_and_containment_are_detected(self):
        from geometry import check_piece_contact
        outer = pv.Cube(x_length=10, y_length=10, z_length=10).triangulate()
        intersecting = outer.translate([5,0,0], inplace=False)
        nested = pv.Cube(x_length=2, y_length=2, z_length=2).triangulate()
        separate = outer.translate([15,0,0], inplace=False)
        self.assertEqual(check_piece_contact(outer, separate)['status'], 'NO_CONTACT_DETECTED')
        self.assertEqual(check_piece_contact(outer, intersecting)['status'], 'CONTACT_DETECTED')
        self.assertEqual(check_piece_contact(outer, nested)['status'], 'CONTAINMENT_DETECTED')

    def test_bivalve_zero_gap_cannot_export_touching_pieces(self):
        mesh=demo_mesh()
        params=replace(clinical_params(mesh),splint_mode='bivalve',seam_gap_mm=0)
        result=build(mesh,params)
        self.assertFalse(result['export_ready'])
        self.assertIsNotNone(result['patch'])
        self.assertIn('Hai mảnh nẹp chạm',result['report']['messages'][0])
        with tempfile.TemporaryDirectory() as temp:
            with self.assertRaises(ValueError):
                export_bundle(Path(temp)/'blocked',mesh,result,params,{})
            self.assertFalse((Path(temp)/'blocked').exists())


class ProjectRegressionTests(unittest.TestCase):
    def test_bad_reliefs_are_rejected_before_project_apply(self):
        bad = [
            {'name': [], 'point':[0,0,0], 'radius_mm':12, 'extra_mm':1},
            {'point':[True,0,0], 'radius_mm':12, 'extra_mm':1},
            {'point':[0,0,0], 'radius_mm':True, 'extra_mm':1},
            {'point':[0,0,0], 'radius_mm':12, 'extra_mm':'2'},
        ]
        for relief in bad:
            with self.subTest(relief=relief):
                data = example(); data['params']['reliefs'] = [relief]
                with self.assertRaises(ValueError):
                    validated_project(data)

    def test_old_relief_without_name_gets_default(self):
        data = example()
        data['params']['reliefs'] = [{'point':[0,0,0], 'radius_mm':12, 'extra_mm':1}]
        self.assertIsInstance(validated_project(data)['params']['reliefs'][0]['name'], str)

    def test_reject_inconsistent_coverage_label(self):
        data = example();data['state']['coverage'] = 0
        with self.assertRaises(ValueError):validated_project(data)


class UIRegressionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.qt=QApplication.instance() or QApplication([])

    def setUp(self):
        self.w = SplintFit();self.w.render=lambda *args:None
        self.errors=[];self.w.error=self.errors.append

    def tearDown(self):self.w.close()

    def test_view_controls_do_not_raise_with_partial_landmarks(self):
        self.w.load_demo()
        self.w.landmarks={'proximal':[30.,0.,30.]}
        for method in (self.w.view_long,self.w.view_side):
            with self.subTest(method=method.__name__):method()
        self.assertEqual(len(self.errors), 2)
        self.assertTrue(all('Chọn đủ' in error for error in self.errors))

    def test_losing_confirmation_cancels_pending_live_update(self):
        self.w.load_demo();self.w.live.setChecked(True)
        self.w.controls['thickness_mm'].setValue(4)
        self.assertTrue(self.w.timer.isActive())
        self.w.scale_confirm.setChecked(False)
        self.assertFalse(self.w.timer.isActive())
        self.assertFalse(self.w.rebuild_requested)

    def test_legacy_relief_can_be_opened_without_name(self):
        self.w.load_demo();before=self.w.mesh.points.copy()
        with tempfile.TemporaryDirectory() as temp:
            file=Path(temp)/'case.json'
            with patch.object(QFileDialog,'getSaveFileName',return_value=(str(file),'')):self.w.save_project()
            data=json.loads(file.read_text());data['params']['reliefs']=[{'point':[1,2,3],'radius_mm':12,'extra_mm':1}]
            file.write_text(json.dumps(data))
            with patch.object(QFileDialog,'getOpenFileName',return_value=(str(file),'')):self.w.open_project()
            self.assertFalse(self.errors)
            self.assertEqual(len(self.w.reliefs),1)
            self.assertIn('name',self.w.reliefs[0])
            np.testing.assert_allclose(self.w.mesh.points,before)

    def test_import_failure_report_available_without_loaded_mesh(self):
        from types import SimpleNamespace
        self.w.worker=SimpleNamespace(task='load');self.w.pending_path='broken_scan.ply'
        self.w.worker_error('File chỉ có điểm, không có bề mặt.')
        self.w.worker=None
        report=self.w.diagnostic_data()
        self.assertIsNone(report['source_stats'])
        self.assertEqual(report['last_failure']['task'],'load')
        self.assertEqual(report['last_failure']['attempted_path'],'broken_scan.ply')
        self.assertIn('không có bề mặt',report['last_failure']['message'])
        self.assertIn('python',report['runtime'])
        self.assertEqual(report['audit_events'][-1]['event'],'worker_failed')

    def test_invalid_relief_is_rejected_without_changing_current_case(self):
        self.w.load_demo();self.w.case_id.setText('KEEP-ME')
        before=self.w.state_snapshot()
        with tempfile.TemporaryDirectory() as temp:
            file=Path(temp)/'case.json'
            with patch.object(QFileDialog,'getSaveFileName',return_value=(str(file),'')):self.w.save_project()
            data=json.loads(file.read_text());data['metadata']['case_id']='CORRUPT'
            data['params']['reliefs']=[{'name':[],'point':[1,2,3],'radius_mm':12,'extra_mm':1}]
            file.write_text(json.dumps(data))
            with patch.object(QFileDialog,'getOpenFileName',return_value=(str(file),'')):self.w.open_project()
        self.assertTrue(self.errors)
        self.assertEqual(self.w.case_id.text(),'KEEP-ME')
        self.assertEqual(self.w.state_snapshot(),before)


if __name__ == '__main__':unittest.main()
