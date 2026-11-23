import json
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path
import numpy as np
import pyvista as pv
from geometry import Parameters,build,triangles,edge_data,export_bundle,validate_parameters
from cast_template import hand_demo_mesh


def sample_params(**kwargs):
    return replace(Parameters(proximal_point=[34.,0.,15.],distal_point=[40.,0.,288.],
        side_point=[25.,0.,175.],splint_mode='bivalve',cast_template=True,
        hand_notch_depth_mm=35.,auto_orient_open_normals=True),**kwargs)


class CastGeometryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.mesh=hand_demo_mesh();cls.p=sample_params();cls.result=build(cls.mesh,cls.p)

    def test_two_material_solids_have_closed_oriented_edges(self):
        r=self.result
        self.assertTrue(r['export_ready']);self.assertEqual(len(r['pieces']),2)
        self.assertEqual(r['report']['shell']['components'],2)
        for piece in r['pieces']:
            s=piece['report']['shell']
            for field in ('boundary_edges','nonmanifold_edges','inconsistent_edges','degenerate_triangles'):
                self.assertEqual(s[field],0)

    def test_ventilation_and_strap_slots_are_topological_through_holes(self):
        # A single connected closed shell with h tunnels has Euler number 2-2h.
        # This checks material geometry, rather than trusting labels or colors.
        for piece in self.result['pieces']:
            shell=piece['shell'];f=triangles(shell)
            _,edges,_,_=edge_data(f)
            euler=shell.n_points-len(edges)+len(f)
            h=piece['report']['ventilation_holes']+piece['report']['strap_slots']
            self.assertGreater(piece['report']['ventilation_holes'],0)
            self.assertEqual(euler,2-2*h)

    def test_simple_form_is_a_connected_quad_sheet(self):
        for piece in self.result['pieces']:
            pts,q=piece['quad']
            self.assertEqual(q.shape[1],4)
            self.assertLess(len(q),2000)
            self.assertTrue(np.isfinite(pts).all())
            self.assertEqual(len(np.unique(q)),len(pts))

    def test_export_has_real_separate_mesh_and_form_files(self):
        with tempfile.TemporaryDirectory() as t:
            out=export_bundle(Path(t)/'case',self.mesh,self.result,self.p,{'synthetic_demo':True})
            for n in (1,2):
                for name in (f'splint_form_piece_{n}_quad.obj',f'splint_form_perforated_piece_{n}_quad.obj'):
                    text=(out/name).read_text()
                    faces=[line for line in text.splitlines() if line.startswith('f ')]
                    self.assertGreater(len(faces),0)
                    self.assertTrue(all(len(line.split())==5 for line in faces))
                reread=pv.read(out/f'shell_piece_{n}_prototype.stl').clean()
                self.assertEqual(reread.n_open_edges,0)
            report=json.loads((out/'parameters_and_report.json').read_text())
            self.assertEqual(report['report']['fusion_conversion'],'NOT_TESTED_IN_FUSION')

    def test_tiny_missing_scan_triangle_blocks_export(self):
        f=triangles(self.mesh);centers=self.mesh.cell_centers().points
        idx=int(np.argmin(np.linalg.norm(centers-[29,0,130],axis=1)))
        broken=pv.PolyData(self.mesh.points,np.column_stack((np.full(len(f)-1,3),np.delete(f,idx,axis=0))).ravel())
        r=build(broken,replace(self.p,allow_incomplete_preview=True))
        self.assertFalse(r['export_ready']);self.assertEqual(r['status'],'preview_only')
        with tempfile.TemporaryDirectory() as t:
            with self.assertRaises(ValueError):export_bundle(Path(t)/'bad',broken,r,self.p,{})

    def test_disable_vents_keeps_explicit_strap_slots(self):
        r=build(self.mesh,replace(self.p,ventilation=False))
        self.assertEqual(r['report']['ventilation_holes'],0)
        self.assertGreater(r['report']['strap_slots'],0)

    def test_translation_preserves_shape_and_reference_coordinates(self):
        shift=np.array([125.,-80.,30.])
        p=replace(self.p,proximal_point=(np.asarray(self.p.proximal_point)+shift).tolist(),
          distal_point=(np.asarray(self.p.distal_point)+shift).tolist(),
          side_point=(np.asarray(self.p.side_point)+shift).tolist())
        r=build(self.mesh.translate(shift,inplace=False),p)
        np.testing.assert_allclose(r['pieces'][0]['quad'][0],self.result['pieces'][0]['quad'][0]+shift,atol=1e-7)

    def test_invalid_template_values_are_rejected(self):
        for kw in ({'hole_ratio':float('nan')},{'hole_pitch_mm':0},{'ventilation':1},{'hand_notch_depth_mm':-1}):
            with self.assertRaises(ValueError):validate_parameters(replace(self.p,**kw))

    def test_same_scan_and_settings_reproduce_geometry(self):
        repeated=build(self.mesh,self.p)
        for original,new in zip(self.result['pieces'],repeated['pieces']):
            np.testing.assert_allclose(new['shell'].points,original['shell'].points,atol=1e-9,rtol=0)
            np.testing.assert_array_equal(new['shell'].faces,original['shell'].faces)


if __name__=='__main__':unittest.main()
