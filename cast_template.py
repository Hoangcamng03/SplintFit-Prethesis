"""Structured scan-fitted cast panels. Experimental; no anatomical inference.

Only single, closed, star-shaped cross-sections are supported. Missing data is
rejected, never bridged. All coordinates remain in the scan's millimetre frame.
The full perforated quad surface and the simple Form base are separate assets.
"""
import numpy as np
import pyvista as pv
from scipy.interpolate import RegularGridInterpolator


def validate_cast_parameters(p):
    for key in ('cast_template','ventilation'):
        if type(getattr(p,key)) is not bool:
            raise ValueError('Tùy chọn tạo nẹp phải là đúng/sai.')
    ranges={'hole_pitch_mm':(16,45),'hole_ratio':(.2,.65),
            'hand_notch_depth_mm':(0,60),'hand_notch_width_deg':(30,140),
            'hand_notch_angle_deg':(-180,180)}
    for key,(lo,hi) in ranges.items():
        v=getattr(p,key)
        if isinstance(v,(bool,np.bool_)) or not isinstance(v,(int,float,np.integer,np.floating)) or not np.isfinite(v) or not lo<=v<=hi:
            raise ValueError('Thông số mẫu nẹp không hợp lệ: '+key)


def _segments(mesh, origin, z, x, y):
    """Read observed section segments, verifying a single cycle."""
    section=mesh.slice(normal=z,origin=origin).clean(tolerance=1e-6,absolute=True)
    edges=[];lines=np.asarray(section.lines);i=0
    while i<len(lines):
        count=int(lines[i]);ids=lines[i+1:i+count+1]
        edges.extend(zip(ids[:-1],ids[1:]));i+=count+1
    if not edges:raise ValueError('Không có mặt cắt tại vùng đã chọn.')
    edges=np.unique(np.sort(np.asarray(edges),axis=1),axis=0)
    lengths=np.linalg.norm(section.points[edges[:,1]]-section.points[edges[:,0]],axis=1)
    edges=edges[lengths>1e-7]
    verts,counts=np.unique(edges,return_counts=True)
    if not len(edges) or np.any(counts!=2):
        raise ValueError('Mặt cắt hở: cần thu vùng hoặc quét bổ sung; không tự nối dữ liệu thiếu.')
    adj={int(v):[] for v in verts}
    for a,b in edges:adj[int(a)].append(int(b));adj[int(b)].append(int(a))
    visited=set();todo=[int(verts[0])]
    while todo:
        v=todo.pop()
        if v not in visited:visited.add(v);todo.extend(adj[v])
    if len(visited)!=len(verts):
        raise ValueError('Có nhiều vòng mặt cắt (ví dụ ngón tay rời). Thu vùng dưới các ngón hoặc dùng thiết kế chuyên biệt.')
    relative=section.points-origin
    xy=np.column_stack((relative@x,relative@y))
    return xy,edges


def _cross(a,b):return a[...,0]*b[...,1]-a[...,1]*b[...,0]


class ScanFit:
    def __init__(self,mesh,p):
        from geometry import clinical_frame,edge_data,triangles,DesignProblem
        self.origin,self.z,self.x,self.y,self.start,self.end=clinical_frame(mesh,p)
        if self.end-self.start<20 or p.hand_notch_depth_mm>(self.end-self.start)*.45:
            raise DesignProblem('Vùng nẹp quá ngắn hoặc cửa ngón cái quá sâu.',mesh)
        # Detect holes anywhere in the entire ROI, not only at sampled slices.
        roi=mesh.clip(normal=self.z,origin=self.origin+self.z*self.start,invert=False)
        roi=roi.clip(normal=self.z,origin=self.origin+self.z*self.end,invert=True).triangulate().clean()
        if roi.n_cells<4:raise DesignProblem('Vùng chọn không có bề mặt.',roi)
        _,edges,_,counts=edge_data(triangles(roi))
        ends=np.asarray(roi.points)[edges[counts==1]]
        tol=max(float(roi.length)*1e-6,1e-4)
        near_start=np.all(abs((ends-self.origin)@self.z-self.start)<tol,axis=1)
        near_end=np.all(abs((ends-self.origin)@self.z-self.end)<tol,axis=1)
        if np.any(counts>2) or np.any(~(near_start|near_end)):
            raise DesignProblem('Vùng scan thiếu dữ liệu hoặc có cạnh lỗi; mẫu có lỗ thoáng không được dùng để che lỗi scan.',roi)
        self.roi=roi
        # <= 4 mm spacing; 128 angular samples. Interpolation is disclosed.
        zs=np.linspace(self.start,self.end,max(40,int((self.end-self.start)/4)+1))
        self.theta=np.linspace(-np.pi,np.pi,129)
        cs=[];rs=[]
        for zvalue in zs:
            try:
                xy,edges=_segments(mesh,self.origin+self.z*zvalue,self.z,self.x,self.y)
                c=(xy.min(axis=0)+xy.max(axis=0))/2
                a,b=xy[edges[:,0]]-c,xy[edges[:,1]]-c
                delta=b-a;radii=[]
                for theta in self.theta:
                    direction=np.array([np.cos(theta),np.sin(theta)])
                    den=_cross(direction,delta)
                    good=abs(den)>1e-10
                    rr=np.divide(_cross(a,delta),den,out=np.zeros(len(a)),where=good)
                    tt=np.divide(_cross(a,direction),den,out=np.zeros(len(a)),where=good)
                    hits=np.sort(rr[good&(rr>1e-6)&(tt>=-1e-8)&(tt<=1+1e-8)])
                    hits=hits[np.r_[True,np.diff(hits)>1e-4]] if len(hits) else hits
                    if len(hits)!=1:
                        raise ValueError('Mặt cắt không phù hợp mẫu một vòng hướng tâm; không tự suy đoán vùng lõm/ngón cái.')
                    radii.append(hits[0])
                cs.append(c);rs.append(radii)
            except ValueError as exc:
                raise DesignProblem(f'Mặt cắt cách đầu vùng {zvalue-self.start:.1f} mm: {exc}',roi) from exc
        self.zs=zs;self.centers=np.asarray(cs);self.radii=np.asarray(rs)
        self.interp=RegularGridInterpolator((zs,self.theta),self.radii,bounds_error=True)
        self.radius_min=float(self.radii.min())
        self.radius_median=float(np.median(self.radii))

    def surface(self,theta,zvalue):
        theta,zvalue=np.broadcast_arrays(theta,zvalue)
        shape=theta.shape;t=(theta.ravel()+np.pi)%(2*np.pi)-np.pi;z=zvalue.ravel()
        r=self.interp(np.column_stack((z,t)))
        cx=np.interp(z,self.zs,self.centers[:,0]);cy=np.interp(z,self.zs,self.centers[:,1])
        points=self.origin+z[:,None]*self.z+(cx+r*np.cos(t))[:,None]*self.x+(cy+r*np.sin(t))[:,None]*self.y
        return points.reshape(shape+(3,))

    def points_normals(self,theta,zvalue):
        theta=np.asarray(theta);zvalue=np.asarray(zvalue)
        raw=self.surface(theta,zvalue)
        dt=self.surface(theta+1e-4,zvalue)-self.surface(theta-1e-4,zvalue)
        lo=np.maximum(self.start,zvalue-.02);hi=np.minimum(self.end,zvalue+.02)
        dz=self.surface(theta,hi)-self.surface(theta,lo)
        n=np.cross(dt,dz);length=np.linalg.norm(n,axis=-1,keepdims=True)
        if np.any(length<1e-12):raise ValueError('Không xác định được hướng của mặt nền.')
        return raw,n/length


def _poly(points,quads):
    return pv.PolyData(points,np.column_stack((np.full(len(quads),4),quads)).ravel())


def _compact(points,faces):
    ids,inv=np.unique(faces,return_inverse=True)
    return points[ids],inv.reshape(faces.shape)


def _tiles(cols,rows,ventilation,ratio):
    """Conforming 16-edge rectangular tiles with actual oval through-holes.

    Adjacent tiles share identical boundary samples. Hole rings are quads;
    solid tiles use a matching 4x4 grid, not a triangle->quad split.
    """
    points=[];faces=[];lookup={};holes=[];slots=[]
    angles=np.arange(16)*np.pi/8
    circle=np.column_stack((np.cos(angles),np.sin(angles)))
    square=circle/np.max(abs(circle),axis=1)[:,None]
    def vertex(uv):
        key=tuple(np.round(uv,12))
        if key not in lookup:lookup[key]=len(points);points.append(uv)
        return lookup[key]
    bands=set(int(round((rows-1)*f)) for f in (.22,.5,.78))
    for row in range(rows):
        for col in range(cols):
            center=np.array([(col+.5)/cols,(row+.5)/rows]);half=np.array([.5/cols,.5/rows])
            outside=[vertex(center+v*half) for v in square]
            slot=row in bands and col in (0,cols-1) and 0<row<rows-1
            vent=ventilation and row not in bands and 0<row<rows-1 and 0<col<cols-1
            if vent or slot:
                scale=np.array([.30,.62]) if slot else np.array([ratio,ratio])
                inside=[vertex(center+v*half*scale) for v in circle]
                for i in range(16):faces.append([outside[i],outside[(i+1)%16],inside[(i+1)%16],inside[i]])
                (slots if slot else holes).append(center.tolist())
            else:
                ts=np.array([-1,-np.tan(np.pi/8),0,np.tan(np.pi/8),1])
                ids=np.array([[vertex(center+np.array([a,b])*half) for a in ts] for b in ts])
                for b in range(4):
                    for a in range(4):faces.append([ids[b,a],ids[b,a+1],ids[b+1,a+1],ids[b+1,a]])
    return np.asarray(points),np.asarray(faces),holes,slots


def build_piece(mesh,p,opposite=False,progress=None):
    from geometry import (DesignProblem,stats,triangles,thicken_patch,distances,
                          sample_points,confirmed_wall_samples)
    emit=progress or (lambda *args:None)
    emit(15,'Đang kiểm vùng scan và lấy mặt cắt cho mẫu nẹp…')
    fit=ScanFit(mesh,p)
    if p.splint_mode=='bivalve':
        if p.seam_gap_mm<=0:raise DesignProblem('Mẫu hai mảnh cần khe mở dương.',fit.roi)
        gap=p.seam_gap_mm/2
        if gap>=fit.radius_min*.5:raise DesignProblem('Khe mở quá rộng so với kích thước chi.',fit.roi)
        half=np.pi/2-np.arcsin(gap/fit.radius_min)
    else:half=np.deg2rad(p.coverage_deg)/2
    center=np.pi if opposite else 0.;low=center-half;high=center+half
    length=fit.end-fit.start
    cols=max(4,int(2*half*fit.radius_median/p.hole_pitch_mm))
    rows=max(6,int(length/p.hole_pitch_mm))
    def map_uv(uv):
        theta=low+(high-low)*uv[:,0]
        relative=(theta-np.deg2rad(p.hand_notch_angle_deg)+np.pi)%(2*np.pi)-np.pi
        width=np.deg2rad(p.hand_notch_width_deg)/2
        # Smooth compact U-shaped distal boundary. User-positioned, not inferred anatomy.
        dip=p.hand_notch_depth_mm*np.maximum(0,1-(relative/width)**2)**2
        z=fit.start+uv[:,1]*(length-dip)
        raw,normals=fit.points_normals(theta,z)
        offsets=np.full(len(raw),p.clearance_mm+p.padding_mm)
        for relief in p.reliefs or []:
            point=np.asarray(relief['point']);radius=relief['radius_mm'];extra=relief['extra_mm']
            idx=np.argmin(np.linalg.norm(raw-point,axis=1))
            weight=np.maximum(0,1-(np.linalg.norm(raw-point,axis=1)/radius)**2)**2
            weight*=np.maximum(0,normals@normals[idx])**2
            offsets+=extra*weight
        return raw,raw+normals*offsets[:,None],normals,offsets
    emit(45,'Đang tạo lỗ thoáng, khe đai và mặt nền Form…')
    uv,q,holes,slots=_tiles(cols,rows,p.ventilation,p.hole_ratio)
    raw,points,normals,offsets=map_uv(uv)
    inner=_poly(points,q).triangulate()
    inner.point_data['offset_normal']=normals
    inner.point_data['nominal_clearance_mm']=offsets
    shell=thicken_patch(inner,normals,p.thickness_mm)
    sh=stats(shell)
    if not sh['edge_watertight'] or sh['nonmanifold_edges'] or sh['degenerate_triangles'] or sh['inconsistent_edges'] or sh['components']!=1:
        raise DesignProblem('Vỏ mẫu có lỗi topology; cần thay thông số hoặc vùng scan.',fit.roi)
    # Separate regular, low-density control cage without ventilation or strap holes.
    nc=max(14,cols*3);nr=max(24,rows*3)
    simple_uv=np.array([[j/nc,i/nr] for i in range(nr+1) for j in range(nc+1)])
    simple_q=np.array([[i*(nc+1)+j,i*(nc+1)+j+1,(i+1)*(nc+1)+j+1,(i+1)*(nc+1)+j] for i in range(nr) for j in range(nc)])
    _,simple_points,_,_=map_uv(simple_uv)
    # Sample model interpolation against actual scan; not a global Hausdorff bound.
    errors=distances(raw,mesh)
    if errors.max()>p.max_sampled_deviation_mm:
        raise DesignProblem(f'Xấp xỉ scan lệch {errors.max():.3f} mm tại mẫu kiểm, vượt ngưỡng đã chọn. Thu vùng hoặc tăng ngưỡng kỹ thuật có căn cứ.',fit.roi)
    emit(80,'Đang kiểm vỏ kín và điểm quét nằm trong vật liệu…')
    measured=distances(sample_points(inner),mesh)
    inner.point_data['measured_scan_distance_mm']=distances(inner.points,mesh)
    collision_points=sample_points(mesh,maximum=15000)
    bounds=np.asarray(shell.bounds).reshape(3,2)
    collision_points=collision_points[np.all((collision_points>=bounds[:,0])&(collision_points<=bounds[:,1]),axis=1)]
    count=confirmed_wall_samples(collision_points,shell)
    if count:raise DesignProblem(f'Có {count} điểm scan nằm trong thành nẹp tại phép kiểm lấy mẫu. Kiểm độ cong, độ chừa và vùng chọn.',fit.roi)
    report={'source':stats(mesh),'patch':stats(inner),'shell':sh,'length_mm':float(length),
      'quad_faces':int(len(simple_q)),'form_available':True,'quad_method':'regular anatomical-coordinate grid; not triangle splitting',
      'perforated_quad_faces':int(len(q)),'ventilation_holes':len(holes),'strap_slots':len(slots),
      'grid_tiles':[cols,rows],'template_engine':'cross-section radial fit, conforming perforated quad panels',
      'hole_design_status':'RULE_BASED_GEOMETRY_NOT_MECHANICALLY_VALIDATED',
      'hole_size_ratio_definition':'diameter fraction in each parametric tile; not whole-device open-area fraction',
      'measured_minimum_ligament_mm':None,'measured_open_area_fraction':None,
      'anatomical_hole_exclusion_masks':'NOT_IMPLEMENTED',
      'hand_notch_depth_mm':p.hand_notch_depth_mm,'decimation_sampled_max_mm':float(errors.max()),
      'decimation_sampled_rms_mm':float(np.sqrt(np.mean(errors**2))),'decimation_sample_count':len(errors),
      'deviation_method':'unoffset constructed-vertex distance to scan; not a Hausdorff bound; no Fusion smoothing included',
      'sampled_unsigned_surface_distance_min_mm':float(measured.min()),'sampled_unsigned_surface_distance_max_mm':float(measured.max()),
      'nominal_clearance_min_mm':float(offsets.min()),'nominal_clearance_max_mm':float(offsets.max()),
      'sampled_scan_in_wall_count':count,'collision_sample_count':len(collision_points),
      'collision_check':'SAMPLED_ONLY; no complete triangle intersection guarantee',
      'self_intersection_check':'NOT_IMPLEMENTED','clinical_validation':'NOT_VALIDATED',
      'fusion_conversion':'NOT_TESTED_IN_FUSION','hole_filling':False,
      'thickness_method':'sampled surface-normal displacement; no minimum thickness guarantee',
      'edge_rounding':'NOT_GENERATED; finish rim edges in Fusion before physical fit tests',
      'messages':[f'Mẫu có {len(holes)} lỗ thoáng và {len(slots)} khe luồn đai trên mảnh này.',
        'Form nền không có lỗ để kéo dáng; OBJ perforated có lỗ để thử chỉnh trực tiếp. Cả hai chưa thử chuyển trong Fusion.',
        'Cửa ngón cái là đường khuyết do người dùng đặt. Chưa tạo nhánh ôm riêng ngón cái/spica.',
        'Chỉ hỗ trợ mặt cắt một vòng hướng tâm. Mép cần bo và kiểm lại trong Fusion.']}
    return {'inner':inner,'shell':shell,'patch':fit.roi,'normals':normals,
      'quad':(simple_points,simple_q),'perforated_quad':(points,q),
      'report':report,'status':'ready','export_ready':True,'form_available':True}


def hand_demo_mesh():
    """Synthetic forearm-wrist-palm envelope, no fingers; not patient anatomy."""
    levels=np.array([0,70,135,175,205,240,275,300.])
    a=np.array([35,33,29,24,23,32,41,40.])
    b=np.array([28,27,24,21,19,18,17,16.])
    theta=np.linspace(0,2*np.pi,96,endpoint=False);points=[]
    for z in np.linspace(0,300,81):
        aa=np.interp(z,levels,a);bb=np.interp(z,levels,b)
        points.extend(np.column_stack((aa*np.cos(theta),bb*np.sin(theta),np.full(96,z))))
    q=[]
    for i in range(80):
        for j in range(96):
            n=i*96+j;m=i*96+(j+1)%96;q.append([n,m,m+96,n+96])
    return _poly(np.asarray(points),np.asarray(q)).triangulate()
