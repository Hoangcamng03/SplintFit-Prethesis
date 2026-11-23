"""Offline, dependency-free review of exported geometry. Display only."""
import json
from pathlib import Path
import numpy as np


def write_viewer(folder,mesh,result):
    from geometry import triangles,display_mesh
    objects=[]
    for i,piece in enumerate(result.get('pieces') or [result]):
        m=piece['shell']
        objects.append({'name':f'piece{i+1}','label':f'Mảnh {i+1}',
          'color':[92,173,53] if i==0 else [132,194,77],
          'vertices':np.round(m.points,5).tolist(),'faces':triangles(m).tolist()})
    m=display_mesh(mesh,target=10000)
    objects.append({'name':'scan','label':'Scan tham chiếu','color':[200,169,145],
      'vertices':np.round(m.points,5).tolist(),'faces':triangles(m).tolist()})
    html=(Path(__file__).parent/'viewer_template.html').read_text(encoding='utf-8')
    html=html.replace('__GEOMETRY_JSON__',json.dumps(objects,separators=(',',':'),allow_nan=False))
    (Path(folder)/'XEM_MAU_3D.html').write_text(html,encoding='utf-8')
