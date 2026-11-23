import copy,json,sys,tempfile,unittest
from unittest.mock import patch
from pathlib import Path
from dataclasses import asdict
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from geometry import Parameters
from project_io import validated_project,atomic_write_json,source_sha256,mesh_reference


def example():
    return {'schema':'splintfit.desktop.v3','params':asdict(Parameters()),
        'metadata':{'scale_used':1.,'synthetic_demo':True},
        'state':{'type':0,'coverage':1},'component_index':0}


class ProjectIOTests(unittest.TestCase):
    def test_legacy_and_current_schemas(self):
        for schema in ('splintfit.desktop.v1','splintfit.desktop.v2','splintfit.desktop.v3'):
            data=example();data['schema']=schema
            self.assertEqual(validated_project(data)['params']['thickness_mm'],3)

    def test_invalid_landmarks_flags_scale_and_type_are_rejected(self):
        changes=[('params','proximal_point',[1,2]),('params','distal_point',[0,0,float('nan')]),
            ('params','flip_normals','false'),('params','target_triangles',150.5),
            ('metadata','scale_used',-1),('state','type',9),('state','type',2)]
        for part,key,value in changes:
            with self.subTest(key=key,value=value):
                data=example();data[part][key]=value
                with self.assertRaises(ValueError):validated_project(data)

    def test_invalid_atomic_write_keeps_original_and_source_hash_detects_change(self):
        with tempfile.TemporaryDirectory() as temp:
            p=Path(temp)/'case.json';atomic_write_json(p,example())
            before=p.read_bytes();digest=source_sha256(p)
            with self.assertRaises(ValueError):atomic_write_json(p,{'bad':float('nan')})
            self.assertEqual(p.read_bytes(),before)
            atomic_write_json(p,{'new':123})
            self.assertNotEqual(source_sha256(p),digest)
            self.assertEqual(len(list(Path(temp).iterdir())),1)

    def test_desktop_out_of_range_and_malformed_finishing_rejected_before_apply(self):
        data=example();data['params']['thickness_mm']=100
        with self.assertRaisesRegex(ValueError,'phạm vi'):validated_project(data)
        data=example();data['metadata']['finishing_requested_not_generated']={'notes':[]}
        with self.assertRaisesRegex(ValueError,'hoàn thiện'):validated_project(data)

    def test_project_mesh_reference_falls_back_when_drives_differ(self):
        with patch('project_io.os.path.relpath',side_effect=ValueError('different drives')),patch('project_io.os.path.abspath',return_value='C:\\scans\\arm.stl'):
            self.assertEqual(mesh_reference('C:\\scans\\arm.stl','D:\\cases'),'C:\\scans\\arm.stl')
