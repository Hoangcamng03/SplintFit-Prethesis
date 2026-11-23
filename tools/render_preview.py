"""CPU z-buffer render of exported triangles; no generative image or OpenGL."""
from pathlib import Path
import numpy as np
import pyvista as pv
from PIL import Image,ImageDraw,ImageFont

ROOT=Path(__file__).resolve().parents[1]
W,H=1400,1120
pixels=np.full((H,W,3),[244,247,249],dtype=np.uint8)
depth=np.full((H,W),-np.inf)


def render(mesh,color,cx,yaw):
    m=mesh.clean().compute_normals(point_normals=True,cell_normals=False,
         split_vertices=True,feature_angle=40,consistent_normals=True,auto_orient_normals=True)
    points=np.asarray(m.points)-[0,0,151]
    cy,sy=np.cos(yaw),np.sin(yaw);ct,st=np.cos(.17),np.sin(.17)
    a=points[:,0]*cy-points[:,1]*sy;b=points[:,0]*sy+points[:,1]*cy
    screen=np.column_stack((cx+a*2.55,540-(points[:,2]*ct-b*st)*2.55,points[:,2]*st+b*ct))
    light=np.array([sy*.65,cy*.65,.76]);light/=np.linalg.norm(light)
    brightness=.27+.73*np.maximum(0,np.asarray(m.point_normals)@light)
    faces=np.asarray(m.faces).reshape(-1,4)[:,1:]
    for f in faces:
        p=screen[f];minx=max(0,int(np.floor(p[:,0].min())));maxx=min(W-1,int(np.ceil(p[:,0].max())))
        miny=max(0,int(np.floor(p[:,1].min())));maxy=min(H-1,int(np.ceil(p[:,1].max())))
        if minx>maxx or miny>maxy:continue
        x,y=np.meshgrid(np.arange(minx,maxx+1)+.5,np.arange(miny,maxy+1)+.5)
        den=(p[1,1]-p[2,1])*(p[0,0]-p[2,0])+(p[2,0]-p[1,0])*(p[0,1]-p[2,1])
        if abs(den)<1e-10:continue
        aa=((p[1,1]-p[2,1])*(x-p[2,0])+(p[2,0]-p[1,0])*(y-p[2,1]))/den
        bb=((p[2,1]-p[0,1])*(x-p[2,0])+(p[0,0]-p[2,0])*(y-p[2,1]))/den;cc=1-aa-bb
        d=aa*p[0,2]+bb*p[1,2]+cc*p[2,2]
        target=depth[miny:maxy+1,minx:maxx+1]
        visible=(aa>=0)&(bb>=0)&(cc>=0)&(d>target)
        shades=aa*brightness[f[0]]+bb*brightness[f[1]]+cc*brightness[f[2]]
        rgb=np.clip(shades[...,None]*color,0,255).astype(np.uint8)
        pixels[miny:maxy+1,minx:maxx+1][visible]=rgb[visible];target[visible]=d[visible]


for index in (1,2):render(pv.read(ROOT/f'demo_export/shell_piece_{index}_prototype.stl'),np.array([113,190,60]),390,1.0)
render(pv.read(ROOT/'demo_export/shell_piece_1_prototype.stl'),np.array([113,190,60]),1030,1.1)
img=Image.fromarray(pixels);draw=ImageDraw.Draw(img)
font='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
def text(y,s,size=24,color='#254c61'):
    f=ImageFont.truetype(font,size);draw.text((W/2,y),s,font=f,fill=color,anchor='mt')
text(35,'SplintFit | Perforated cast prototype',33)
text(90,'Actual exported geometry / Synthetic arm envelope',18,'#587383')
f=ImageFont.truetype(font,20)
draw.text((390,145),'TWO-PIECE ASSEMBLY',font=f,fill='#254c61',anchor='mt')
draw.text((1030,145),'ONE PIECE / OPEN HOLES',font=f,fill='#254c61',anchor='mt')
text(990,'24 ventilation holes + 12 strap slots across both pieces',21)
text(1035,'Rim finishing, physical tests and Fusion conversion still require verification',16,'#587383')
img.save(ROOT/'PREVIEW_DEMO.png')
print(ROOT/'PREVIEW_DEMO.png')
