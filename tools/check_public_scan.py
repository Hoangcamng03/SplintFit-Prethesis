"""Reproduce upload → region → build → export/readback using a public arm scan.

UW GRAIL data is research-only. Downloaded scans and derived meshes stay outside
Git. This does not test Autodesk Fusion, a printer, physical fit or clinical use.
"""
import argparse
import hashlib
import io
import json
from pathlib import Path
import sys
import time
import urllib.request
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from backend.server import app, SESSIONS, EXPORT_RECORDS
from geometry import stats, read_mesh

SOURCE = 'https://grail.cs.washington.edu/data/scans/'
ARCHIVE = SOURCE + 'arms-obj.zip'
ATTRIBUTION = 'University of Washington Graphics and Imaging Laboratory; Brett Allen, Brian Curless, Zoran Popović (SIGGRAPH 2002)'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data-dir', type=Path, required=True,
                        help='Local directory for research-only scan and derived exports; do not commit it.')
    args = parser.parse_args()
    data_dir = args.data_dir.resolve()
    data_dir.mkdir(parents=True, exist_ok=True)
    archive = data_dir / 'arms-obj.zip'
    if not archive.exists():
        urllib.request.urlretrieve(ARCHIVE, archive)
    source_file = data_dir / '001.obj'
    with zipfile.ZipFile(archive) as zf:
        source_file.write_bytes(zf.read('001.obj'))
    report = {
        'source_page': SOURCE, 'archive_url': ARCHIVE, 'attribution': ATTRIBUTION,
        'usage': 'Research only, noncommercial; retain author acknowledgement. Not redistributed.',
        'archive_sha256': digest(archive), 'mesh_sha256': digest(source_file),
        'pose': '001: source describes straight elbow; wrist digit 1 = approximately neutral; gripping a tube.',
        'scale_assumption': 'Coordinate values treated as mm (scale=1); no independent anthropometry. Software test only.',
        'scope': 'Manually shortened forearm sleeve; does not demonstrate wrist immobilization.',
        'cases': [], 'fusion': 'NOT_TESTED', 'printing': 'NOT_TESTED', 'clinical': 'NOT_VALIDATED',
    }
    client = app.test_client()
    with source_file.open('rb') as f:
        started = time.perf_counter()
        response = client.post('/api/scan/upload', data={
            'file': (f, 'UW_GRAIL_001.obj'), 'scale_mm': '1'})
    assert response.status_code == 200, response.get_json()
    scan = response.get_json()
    report['upload_seconds'] = round(time.perf_counter() - started, 3)
    report['scan_stats'] = scan['stats']
    sf = scan['safe_frame']
    report['automatic_suggestion'] = sf
    report['automatic_suggestion_limit'] = 'Longest eligible section run is not anatomical recognition; includes upper-arm region in this scan. Manual shortening required.'
    import numpy as np
    origin, axis = np.array(sf['origin']), np.array(sf['axis_z'])
    x = np.array(sf['axis_x'])
    # Reproduce UI selection: move first slider 330 mm inward, keep distal slider
    # at floor(span). Selected by inspecting the source, not as treatment limits.
    start = sf['safe_min_mm'] + 330
    end = sf['safe_min_mm'] + int(sf['safe_max_mm'] - sf['safe_min_mm'])
    p = {
        'proximal_point': (origin + axis * start).tolist(),
        'distal_point': (origin + axis * end).tolist(),
        'side_point': (origin + axis * ((start + end) / 2) + x * (sf['radius_est_mm'] + 6)).tolist(),
        'hand_notch_depth_mm': 0, 'clearance_mm': 1.5, 'padding_mm': .5,
        'thickness_mm': 3.2, 'hole_pitch_mm': 20, 'hole_ratio': .58,
    }
    report['selected_params'] = p
    for name, overrides in [('perforated_B', {}),
                            ('perforated_A', {'clearance_mm': 2.5, 'padding_mm': 1.}),
                            ('no_ventilation_C', {'clearance_mm': 1.3, 'padding_mm': 0., 'ventilation': False})]:
        params = {**p, **overrides}
        started = time.perf_counter()
        response = client.post('/api/build', json={
            'session_id': scan['session_id'], 'params': params,
            'confirmations': {'scale': True, 'region': True}})
        built = response.get_json()
        case = {'name': name, 'build_http': response.status_code,
                'build_seconds': round(time.perf_counter() - started, 3)}
        if response.status_code != 200 or not built.get('export_ready'):
            case['error'] = built.get('error', built.get('report'))
            report['cases'].append(case)
            continue
        case['report'] = built['report']
        for mode in ['fusion_only', 'full']:
            exp_response = client.post('/api/export', json={
                'session_id': scan['session_id'], 'build_id': built['build_id'],
                'params': params, 'case_id': name, 'export_mode': mode,
                'output_dir': str(data_dir / 'derived')})
            assert exp_response.status_code == 200, exp_response.get_json()
            exp = exp_response.get_json()
            folder = Path(exp['folder_path'])
            files = {f['path'] for f in exp['files']}
            if mode == 'fusion_only':
                assert len(files) == 5, files
            checked = []
            for obj in sorted(folder.glob('*_quad.obj')):
                faces = [line.split()[1:] for line in obj.read_text().splitlines() if line.startswith('f ')]
                assert faces and all(len(face) == 4 for face in faces)
                checked.append({'file': obj.name, 'quad_faces': len(faces), 'sha256': digest(obj)})
                streamed = client.get(f"/api/export/{exp['export_id']}/file/{obj.name}")
                assert hashlib.sha256(streamed.data).hexdigest() == digest(obj)
            readback = []
            if mode == 'full':
                for stl in sorted(folder.glob('shell_piece_*_prototype.stl')):
                    st = stats(read_mesh(stl, scale=1.))
                    assert st['edge_watertight'] and st['nonmanifold_edges'] == 0 and st['degenerate_triangles'] == 0, st
                    readback.append({'file': stl.name, 'stats': st, 'sha256': digest(stl)})
                exported_scan = read_mesh(folder / 'scan_reference_mm.stl', scale=1.)
                assert np.allclose(exported_scan.bounds, SESSIONS[scan['session_id']]['active_mesh'].bounds, atol=.001)
            zipped = client.get(exp['download_url'])
            assert zipped.status_code == 200
            with zipfile.ZipFile(io.BytesIO(zipped.data)) as zf:
                assert len(zf.namelist()) == len(files)
            case[mode] = {'file_count': len(files), 'quads': checked, 'stl_readback': readback, 'zip_readback': 'PASS'}
        report['cases'].append(case)
    # Negative test: remove an observed triangle inside selected region. No filling.
    session = SESSIONS[scan['session_id']]
    mesh = session['active_mesh']
    mid = (np.array(p['proximal_point']) + np.array(p['distal_point'])) / 2
    index = int(np.argmin(np.linalg.norm(mesh.cell_centers().points - mid, axis=1)))
    session['active_mesh'] = mesh.remove_cells([index])
    bad = client.post('/api/build', json={'session_id': scan['session_id'], 'params': p,
                                        'confirmations': {'scale': True, 'region': True}})
    report['missing_triangle_test'] = {'http': bad.status_code, 'error': bad.get_json().get('error')}
    assert bad.status_code == 422 and session['last_result'] is None
    passed = all(c['build_http'] == 200 and 'full' in c for c in report['cases'])
    report['software_pipeline_passed'] = passed
    out = data_dir / 'public_scan_report.json'
    out.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding='utf-8')
    print(json.dumps({'report': str(out), 'cases': [
        {k: v for k, v in c.items() if k not in ('report', 'full', 'fusion_only')} for c in report['cases']],
        'software_pipeline_passed': passed}, ensure_ascii=False), flush=True)
    return 0 if passed else 1


if __name__ == '__main__':
    raise SystemExit(main())
