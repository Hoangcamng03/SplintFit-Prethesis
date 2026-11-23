import sys
import tempfile
import unittest
from pathlib import Path
import numpy as np
import pyvista as pv
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from geometry import (Parameters, demo_mesh, build, triangles, tri_to_quads,
                      stats, write_obj, read_mesh, export_bundle)


class GeometryTests(unittest.TestCase):
    def test_quad_subdivision_preserves_triangle_surface_and_shared_edges(self):
        source = pv.Plane(i_resolution=1, j_resolution=1).triangulate()
        pts, q = tri_to_quads(source)
        self.assertEqual(q.shape, (6, 4))
        self.assertEqual(len(pts), 11)  # 4 vertices, 5 shared midpoints, 2 centers
        quad = pv.PolyData(pts, np.column_stack((np.full(6, 4), q)).ravel())
        self.assertAlmostEqual(quad.area, source.area)
        self.assertTrue(np.allclose(pts[:, 2], 0))

    def test_open_scan_produces_closed_shell_without_filling_scan(self):
        mesh = demo_mesh()
        original = mesh.points.copy()
        result = build(mesh, Parameters())
        np.testing.assert_array_equal(mesh.points, original)
        self.assertGreater(stats(mesh)['boundary_edges'], 0)
        self.assertTrue(result['report']['shell']['edge_watertight'])
        self.assertEqual(result['report']['shell']['inconsistent_edges'], 0)
        self.assertGreater(result['shell'].volume, 0)
        n = result['inner'].n_points
        np.testing.assert_allclose(np.linalg.norm(result['shell'].points[n:] - result['shell'].points[:n], axis=1), 3)

    def test_existing_hole_in_selected_region_is_rejected(self):
        m = demo_mesh()
        centers = m.cell_centers().points
        idx = np.argmin(np.linalg.norm(centers-np.array([29, 0, 115]), axis=1))
        f = np.delete(triangles(m), idx, axis=0)
        m = pv.PolyData(m.points, np.column_stack((np.full(len(f), 3), f)).ravel())
        with self.assertRaisesRegex(ValueError, 'cạnh hở'):
            build(m, Parameters())

    def test_invalid_crop_is_rejected(self):
        with self.assertRaises(ValueError):
            build(demo_mesh(), Parameters(start_percent=90, end_percent=10))

    def test_rotation_and_decimation(self):
        r = build(demo_mesh(), Parameters(opening_rotation_deg=33, target_triangles=900))
        self.assertLessEqual(r['report']['decimation_sampled_max_mm'], 0.5)
        self.assertLess(r['report']['quad_faces'], 9000)
        self.assertTrue(r['report']['shell']['edge_watertight'])

    def test_outside_selected_region_hole_does_not_block(self):
        m = demo_mesh()
        centers = m.cell_centers().points
        idx = np.argmin(np.linalg.norm(centers-np.array([-29, 0, 115]), axis=1))
        f = np.delete(triangles(m), idx, axis=0)
        m = pv.PolyData(m.points, np.column_stack((np.full(len(f), 3), f)).ravel())
        self.assertTrue(build(m, Parameters())['report']['shell']['edge_watertight'])

    def test_export_obj_has_four_indices_and_mm_scale_roundtrip(self):
        m = demo_mesh()
        r = build(m, Parameters())
        with tempfile.TemporaryDirectory() as temp:
            p = export_bundle(Path(temp)/'output', m, r, Parameters(), {})
            lines = (p/'splint_form_quad.obj').read_text().splitlines()
            faces = [line.split()[1:] for line in lines if line.startswith('f ')]
            self.assertEqual(len(faces), r['report']['quad_faces'])
            self.assertTrue(all(len(face) == 4 for face in faces))
            read = pv.read(p/'splint_form_quad.obj')
            np.testing.assert_allclose(read.bounds, r['inner'].bounds, atol=1e-5)
            source = read_mesh(p/'scan_reference_mm.stl', scale=2)
            np.testing.assert_allclose(np.ptp(source.points, axis=0), np.ptp(m.points, axis=0)*2, atol=1e-4)

    def test_deviation_limit_stops_overaggressive_simplification(self):
        with self.assertRaisesRegex(ValueError, 'Sai lệch'):
            build(demo_mesh(), Parameters(target_triangles=100, max_sampled_deviation_mm=0.00001))


if __name__ == '__main__':
    unittest.main()
