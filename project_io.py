"""Validated project input, source identity and atomic project writes."""
import copy
import hashlib
import json
import os
import tempfile
from dataclasses import asdict
from pathlib import Path
import numpy as np
from geometry import Parameters, validate_parameters


def source_sha256(path):
    digest=hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda:stream.read(1024*1024),b''):
            digest.update(chunk)
    return digest.hexdigest()


def validated_project(data):
    if not isinstance(data,dict) or data.get('schema') not in ('splintfit.desktop.v1','splintfit.desktop.v2','splintfit.desktop.v3'):
        raise ValueError('Không phải dự án desktop SplintFit được hỗ trợ.')
    data=copy.deepcopy(data)
    try:
        p=Parameters(**data['params']);validate_parameters(p)
        # Early prototypes did not persist a display name for relief regions.
        # Normalize before touching the current case or any Qt widgets.
        if p.reliefs:
            for relief in p.reliefs:
                relief.setdefault('name','Vùng tránh tì đè')
                if not 2<=relief['radius_mm']<=60 or not 0<=relief['extra_mm']<=10:
                    raise ValueError('Vùng tránh tì đè ngoài phạm vi giao diện.')
        bounds={'clearance_mm':(0,30),'padding_mm':(0,20),'thickness_mm':(.2,15),
            'max_sampled_deviation_mm':(.01,5),'opening_rotation_deg':(-180,180),
            'start_adjust_mm':(-100,100),'end_adjust_mm':(-100,100),'seam_gap_mm':(0,25),
            'circumference_proximal_mm':(0,1000),'circumference_mid_mm':(0,1000),
            'circumference_distal_mm':(0,1000),'circumference_tolerance_mm':(.1,30)}
        for key,(lo,hi) in bounds.items():
            if not lo<=getattr(p,key)<=hi:raise ValueError('Thông số ngoài phạm vi giao diện: '+key)
        meta=data['metadata'];scale=meta['scale_used']
        if meta.get('synthetic_demo_kind','forearm_v1') not in ('forearm_v1','hand_envelope_v1'):
            raise ValueError('Không nhận diện được mẫu mô phỏng của dự án.')
        if isinstance(scale,bool) or not isinstance(scale,(int,float)) or not np.isfinite(scale) or scale<=0:
            raise ValueError('Tỷ lệ dự án không hợp lệ.')
        if not isinstance(meta.get('synthetic_demo',False),bool):
            raise ValueError('Cờ dữ liệu mẫu không hợp lệ.')
        if not meta.get('synthetic_demo') and not isinstance(data.get('mesh_path'),str):
            raise ValueError('Dự án thiếu đường dẫn mesh.')
        digest=meta.get('source_sha256')
        if digest is not None and (not isinstance(digest,str) or len(digest)!=64 or any(c not in '0123456789abcdef' for c in digest)):
            raise ValueError('Mã kiểm tra mesh không hợp lệ.')
        if data['schema']!='splintfit.desktop.v1':
            state=data['state']
            if type(state['type']) is not int or state['type'] not in (0,1,2):
                raise ValueError('Kiểu nẹp trong dự án không hợp lệ.')
            if type(state['coverage']) is not int or state['coverage'] not in (0,1,2,3):
                raise ValueError('Mức bao phủ trong dự án không hợp lệ.')
            if (state['type']==2)!=(p.splint_mode=='bivalve'):
                raise ValueError('Kiểu nẹp và hình học lưu trong dự án không khớp.')
            if state['coverage']<3 and p.coverage_deg!=[120,180,240][state['coverage']]:
                raise ValueError('Nhãn bao phủ và góc bao phủ trong dự án không khớp.')
        component=data.get('component_index',0)
        if type(component) is not int or component<0:
            raise ValueError('Chỉ số mảnh quét không hợp lệ.')
        for key in ('case_id','side','stage','indication','scan_posture','reviewer'):
            if key in meta and not isinstance(meta[key],str):
                raise ValueError('Trường hồ sơ không hợp lệ: '+key)
        finish=meta.get('finishing_requested_not_generated',{})
        if not isinstance(finish,dict):raise ValueError('Yêu cầu hoàn thiện không hợp lệ.')
        count=finish.get('strap_count',3);radius=finish.get('edge_radius_mm',2)
        if type(count) is not int or not 0<=count<=8 or isinstance(radius,bool) or not isinstance(radius,(int,float)) or not np.isfinite(radius) or not 0<=radius<=8 or not isinstance(finish.get('notes',''),str):
            raise ValueError('Số đai, bán kính bo hoặc ghi chú hoàn thiện không hợp lệ.')
        if not isinstance(data.get('audit_events',[]),list):
            raise ValueError('Nhật ký dự án không hợp lệ.')
        # Materialize only JSON-safe finite values, without executing file contents.
        json.dumps(data,allow_nan=False)
        data['params']=asdict(p)
        return data
    except (KeyError,TypeError,OverflowError) as exc:
        raise ValueError('Dự án thiếu trường hoặc sai kiểu dữ liệu: '+str(exc)) from exc


def atomic_write_json(path,data):
    target=Path(path)
    content=json.dumps(data,ensure_ascii=False,indent=2,allow_nan=False)
    fd,temp=tempfile.mkstemp(prefix='.'+target.name+'.',suffix='.tmp',dir=target.parent)
    try:
        with os.fdopen(fd,'w',encoding='utf-8',newline='\n') as stream:
            stream.write(content);stream.flush();os.fsync(stream.fileno())
        os.replace(temp,target)
    finally:
        Path(temp).unlink(missing_ok=True)


def mesh_reference(path,parent):
    if not path:return ''
    try:return os.path.relpath(path,parent)
    except ValueError:
        # Windows cannot express a relative path between two different drives.
        return os.path.abspath(path)
