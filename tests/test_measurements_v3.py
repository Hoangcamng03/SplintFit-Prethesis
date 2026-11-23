import sys,tempfile,unittest
from pathlib import Path
from dataclasses import replace
from unittest.mock import patch
import numpy as np
import pyvista as pv
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from measurements import closed_section
from geometry import (Parameters,demo_mesh,build,triangles,export_bundle,
                      clinical_frame,confirmed_wall_samples)


class MeasurementTests(unittest.TestCase):
    def test_known_cylinder_circumference_and_incomplete_contour(self):
        tube=pv.Cylinder(radius=35,height=250,direction=(0,0,1),resolution=180,capping=False).triangulate()
        result=closed_section(tube,[0,0,0],[0,0,1])
        self.assertEqual(result['status'],'CLOSED')
        self.assertLess(abs(result['circumference_mm']-2*np.pi*35),.02)
        faces=triangles(tube);centers=tube.cell_centers().points
        faces=faces[centers[:,0]<34]
        broken=pv.PolyData(tube.points,np.column_stack((np.full(len(faces),3),faces)).ravel())
        result=closed_section(broken,[0,0,0],[0,0,1])
        self.assertIsNone(result['circumference_mm'])
        self.assertEqual(result['status'],'OPEN_OR_MULTIPLE_CONTOURS')

    def test_two_loops_are_not_combined_into_one_circumference(self):
        a=pv.Cylinder(radius=20,height=100,direction=(0,0,1),capping=False)
        b=a.translate([80,0,0],inplace=False)
        result=closed_section(a.merge(b),[0,0,0],[0,0,1])
        self.assertEqual(result['components'],2)
        self.assertIsNone(result['circumference_mm'])

    def test_actual_measurement_mismatch_blocks_export_but_keeps_shell(self):
        mesh=demo_mesh();p=Parameters(circumference_mid_mm=999,allow_incomplete_preview=True)
        result=build(mesh,p)
        self.assertEqual(result['status'],'blocked');self.assertFalse(result['export_ready'])
        self.assertIsNotNone(result['shell'])
        self.assertEqual(result['report']['circumference_checks'][1]['comparison'],'MISMATCH')
        with tempfile.TemporaryDirectory() as temp:
            with self.assertRaises(ValueError):export_bundle(Path(temp)/'bad',mesh,result,p,{})

    def test_matching_circumference_and_actual_distance_array(self):
        mesh=demo_mesh();p=Parameters();origin,z,_,_,start,end=clinical_frame(mesh,p)
        real=closed_section(mesh,origin+z*(start+end)/2,z)['circumference_mm']
        result=build(mesh,replace(p,circumference_mid_mm=real))
        self.assertTrue(result['export_ready'])
        self.assertEqual(result['report']['circumference_checks'][1]['comparison'],'WITHIN_TOLERANCE')
        actual=result['inner'].point_data['measured_scan_distance_mm']
        self.assertTrue(np.isfinite(actual).all());self.assertGreater(float(actual.min()),1)

    def test_inward_offset_is_rejected(self):
        with self.assertRaisesRegex(ValueError,'quay vào'):
            build(demo_mesh(),Parameters(flip_normals=True))

    def test_wall_sample_confirmation_has_known_inside_and_outside(self):
        shell=pv.Sphere(radius=10,theta_resolution=30,phi_resolution=30).triangulate()
        points=np.array([[0,0,0],[1,1,1],[30,0,0],[-40,0,0]],dtype=float)
        self.assertEqual(confirmed_wall_samples(points,shell),2)

    def test_bivalve_normal_vectors_follow_merged_point_order(self):
        mesh=demo_mesh();p=Parameters(splint_mode='bivalve',allow_incomplete_preview=True)
        result=build(mesh,p)
        self.assertEqual(result['status'],'ready')
        radial=np.asarray(result['inner'].points).copy();radial[:,2]=0
        self.assertTrue(np.all(np.sum(result['normals']*radial,axis=1)>0))
        self.assertEqual(result['report']['collision_sample_count'],sum(piece['report']['collision_sample_count'] for piece in result['pieces']))

    def test_export_failure_leaves_no_partial_bundle(self):
        mesh=demo_mesh();p=Parameters();result=build(mesh,p)
        with tempfile.TemporaryDirectory() as temp:
            folder=Path(temp)/'output'
            with patch('geometry.write_obj',side_effect=OSError('disk failure')):
                with self.assertRaises(OSError):export_bundle(folder,mesh,result,p,{})
            self.assertEqual(list(Path(temp).iterdir()),[])
