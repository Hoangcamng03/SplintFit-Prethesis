import sys,tempfile,unittest
from pathlib import Path
from dataclasses import replace
from unittest.mock import patch
import numpy as np
import pyvista as pv
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from geometry import (Parameters,demo_mesh,suggested_points,build,triangles,clean_surface,
                      prepare_scan,read_mesh,export_bundle)


def clinical_params(mesh):
    s=suggested_points(mesh)
    return Parameters(axis='AUTO',proximal_point=s['proximal'],distal_point=s['distal'],
        side_point=s['side'],allow_incomplete_preview=True,auto_orient_open_normals=True)


class ClinicalGeometryTests(unittest.TestCase):
    def test_landmarks_work_for_oblique_translated_scan(self):
        m=demo_mesh().rotate_x(35,inplace=False).rotate_y(25,inplace=False).translate([1000,-1500,400],inplace=False)
        r=build(m,clinical_params(m))
        self.assertEqual(r['status'],'ready')
        self.assertEqual(r['report']['shell']['boundary_edges'],0)
        self.assertGreater(r['report']['length_mm'],170)

    def test_local_relief_really_changes_inner_surface_locally(self):
        m=demo_mesh();p=clinical_params(m);base=build(m,p)
        r=build(m,replace(p,reliefs=[{'point':[29,0,115],'radius_mm':15,'extra_mm':2}]))
        delta=np.linalg.norm(r['inner'].points-base['inner'].points,axis=1)
        self.assertAlmostEqual(float(delta.max()),2)
        self.assertEqual(np.sum(delta>.01)<len(delta)/3,True)

    def test_multiple_regions_are_retained_and_selectable(self):
        m=demo_mesh().merge(pv.Sphere(radius=3,center=(200,0,100)),merge_points=False)
        scan=prepare_scan(m)
        self.assertEqual(scan['total_pieces'],2)
        self.assertEqual(scan['source'].n_cells,m.n_cells)
        self.assertGreater(scan['pieces'][0]['area_mm2'],scan['pieces'][1]['area_mm2'])
        selected=scan['pieces'][0]['mesh']
        self.assertEqual(build(selected,clinical_params(selected))['status'],'ready')

    def test_multiblock_import_and_duplicate_face_cleanup(self):
        m=demo_mesh();f=triangles(m)
        duplicate=pv.PolyData(m.points,np.column_stack((np.full(len(f)+1,3),np.vstack((f,f[0])))).ravel())
        clean=clean_surface(duplicate)
        self.assertEqual(clean.n_cells,m.n_cells)
        raw=pv.MultiBlock([m,pv.Sphere(radius=3,center=(200,0,100))])
        with patch('geometry.pv.read',return_value=raw):
            self.assertEqual(prepare_scan(read_mesh('scene.obj'))['total_pieces'],2)

    def test_point_cloud_error_explains_need_for_surface_mesh(self):
        with self.assertRaisesRegex(ValueError,'point cloud'):
            clean_surface(pv.PolyData(np.random.default_rng(0).random((100,3))))

    def test_missing_region_is_previewed_but_export_is_blocked(self):
        m=demo_mesh();f=triangles(m);centers=m.cell_centers().points
        idx=np.argmin(np.linalg.norm(centers-[29,0,115],axis=1));f=np.delete(f,idx,axis=0)
        broken=pv.PolyData(m.points,np.column_stack((np.full(len(f),3),f)).ravel())
        r=build(broken,clinical_params(m))
        self.assertEqual(r['status'],'preview_only');self.assertGreater(r['patch'].n_cells,0)
        with tempfile.TemporaryDirectory() as t:
            with self.assertRaises(ValueError):export_bundle(Path(t)/'out',broken,r,clinical_params(m),{})

    def test_high_density_blocks_only_form_not_geometry(self):
        m=demo_mesh().subdivide(2)
        r=build(m,Parameters(target_triangles=100000,allow_incomplete_preview=True))
        self.assertEqual(r['status'],'ready');self.assertTrue(r['export_ready']);self.assertFalse(r['form_available'])
        with tempfile.TemporaryDirectory() as t:
            out=export_bundle(Path(t)/'out',m,r,Parameters(),{})
            self.assertTrue((out/'shell_prototype_NOT_CLINICALLY_VALIDATED.stl').exists())
            self.assertFalse((out/'splint_form_quad.obj').exists())

    def test_two_piece_splint_and_coverage_choices(self):
        m=demo_mesh();p=clinical_params(m)
        sizes=[]
        for coverage in [120,180,240]:
            r=build(m,replace(p,coverage_deg=coverage));self.assertEqual(r['status'],'ready');sizes.append(r['inner'].area)
        self.assertTrue(sizes[0]<sizes[1]<sizes[2])
        p=replace(p,splint_mode='bivalve');r=build(m,p)
        self.assertEqual(len(r['pieces']),2);self.assertEqual(r['report']['shell']['components'],2)
        with tempfile.TemporaryDirectory() as t:
            out=export_bundle(Path(t)/'out',m,r,p,{})
            self.assertTrue((out/'splint_form_piece_1_quad.obj').exists())
            self.assertTrue((out/'splint_form_piece_2_quad.obj').exists())


if __name__=='__main__':unittest.main()
