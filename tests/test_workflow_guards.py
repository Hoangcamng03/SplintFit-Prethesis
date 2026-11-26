"""Regression tests for stale exports, malformed input and missing scan data."""
import io
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from backend.server import app, SESSIONS, EXPORT_RECORDS


class WorkflowGuards(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()
        self.scan = self.client.post('/api/scan/demo', json={}).get_json()
        self.sid = self.scan['session_id']
        self.params = {k + '_point': self.scan['suggested_landmarks'][k]
                       for k in ('proximal', 'distal', 'side')}
        self.params['hand_notch_depth_mm'] = 0

    def tearDown(self):
        SESSIONS.pop(self.sid, None)

    def build(self, **kwargs):
        return self.client.post('/api/build', json={
            'session_id': self.sid, 'params': self.params, **kwargs})

    def test_failed_rebuild_cannot_export_previous_success(self):
        good = self.build()
        self.assertEqual(good.status_code, 200)
        token = good.get_json()['build_id']
        self.params['thickness_mm'] = -1
        self.assertEqual(self.build().status_code, 400)
        response = self.client.post('/api/export', json={
            'session_id': self.sid, 'build_id': token, 'params': self.params})
        self.assertEqual(response.status_code, 400)
        self.assertIsNone(SESSIONS[self.sid]['last_result'])

    def test_export_requires_current_token_and_identical_parameters(self):
        good = self.build().get_json()
        request = {'session_id': self.sid, 'params': self.params}
        self.assertEqual(self.client.post('/api/export', json=request).status_code, 409)
        request['build_id'] = good['build_id']
        request['params'] = {**self.params, 'clearance_mm': 2.5}
        self.assertEqual(self.client.post('/api/export', json=request).status_code, 409)

    def test_uploaded_scan_requires_scale_and_region_confirmation(self):
        # External uploads are not auto-confirmed, even if geometry is synthetic.
        SESSIONS[self.sid]['is_demo'] = False
        self.assertEqual(self.build().status_code, 400)
        self.assertEqual(self.build(confirmations={'scale': True}).status_code, 400)
        self.assertEqual(self.build(confirmations={'scale': True, 'region': True}).status_code, 200)

    def test_bad_scales_are_rejected_before_mesh_reader(self):
        for scale in ('nan', 'inf', '-1', '0'):
            with self.subTest(scale=scale):
                response = self.client.post('/api/scan/upload', data={
                    'file': (io.BytesIO(b'not a mesh'), 'scan.obj'), 'scale_mm': scale})
                self.assertEqual(response.status_code, 400)
                self.assertIn('đơn vị', response.get_json()['error'])

    def test_boolean_and_nonfinite_numbers_are_not_silently_coerced(self):
        for key, value in [('ventilation', 'false'), ('thickness_mm', True),
                           ('clearance_mm', float('nan')), ('padding_mm', '1.5')]:
            with self.subTest(key=key):
                self.params[key] = value
                self.assertEqual(self.build().status_code, 400)
                del self.params[key]

    def test_invalid_piece_selection_clears_result(self):
        self.assertEqual(self.build().status_code, 200)
        response = self.client.post('/api/scan/select-piece', json={
            'session_id': self.sid, 'piece_id': 'not-a-number'})
        self.assertEqual(response.status_code, 400)
        self.assertIsNone(SESSIONS[self.sid]['last_result'])

    def test_missing_triangle_inside_roi_is_blocked(self):
        import numpy as np
        mesh = SESSIONS[self.sid]['active_mesh']
        a = np.asarray(self.params['proximal_point'])
        b = np.asarray(self.params['distal_point'])
        mid = (a + b) / 2
        centers = mesh.cell_centers().points
        cell = int(np.argmin(np.linalg.norm(centers - mid, axis=1)))
        SESSIONS[self.sid]['active_mesh'] = mesh.remove_cells([cell])
        response = self.build()
        self.assertEqual(response.status_code, 422, response.get_data(as_text=True))
        self.assertIsNone(SESSIONS[self.sid]['last_result'])

    def test_export_download_cannot_escape_into_prefix_sibling(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            folder = base / 'out'
            folder.mkdir()
            sibling = base / 'outside'
            sibling.mkdir()
            (sibling / 'private.txt').write_text('not an export')
            EXPORT_RECORDS['path-guard'] = folder
            try:
                response = self.client.get('/api/export/path-guard/file/../outside/private.txt')
                self.assertEqual(response.status_code, 404)
            finally:
                EXPORT_RECORDS.pop('path-guard', None)


if __name__ == '__main__':
    unittest.main()
