"""Research geometry pipeline. No hole filling and no clinical safety certification."""
from dataclasses import dataclass, asdict, replace
from pathlib import Path
import json
import os
import shutil
import tempfile
import csv
import numpy as np
import pyvista as pv
from measurements import compare_sections


@dataclass
class Parameters:
    axis: str = 'Z'
    start_percent: float = 10.0
    end_percent: float = 90.0
    opening_rotation_deg: float = 0.0
    clearance_mm: float = 1.5
    padding_mm: float = 0.0
    thickness_mm: float = 3.0
    target_triangles: int = 1800
    max_sampled_deviation_mm: float = 0.5
    flip_normals: bool = False
    # v2 UI uses world-space points rather than X/Y/Z and percentage cuts.
    proximal_point: list | None = None
    distal_point: list | None = None
    side_point: list | None = None
    coverage_deg: float = 180.0
    start_adjust_mm: float = 0.0
    end_adjust_mm: float = 0.0
    reliefs: list | None = None
    splint_mode: str = 'single'
    seam_gap_mm: float = 4.0
    allow_incomplete_preview: bool = False
    auto_orient_open_normals: bool = False
    circumference_proximal_mm: float = 0.0
    circumference_mid_mm: float = 0.0
    circumference_distal_mm: float = 0.0
    circumference_tolerance_mm: float = 3.0
    cast_template: bool = False
    ventilation: bool = True
    hole_pitch_mm: float = 24.0
    hole_ratio: float = 0.48
    hand_notch_depth_mm: float = 0.0
    hand_notch_width_deg: float = 75.0
    hand_notch_angle_deg: float = 0.0
    rim_flare_mm: float = 1.4


def triangles(mesh):
    return np.asarray(mesh.faces).reshape(-1, 4)[:, 1:]


def edge_data(faces):
    directed = np.concatenate([faces[:, [0, 1]], faces[:, [1, 2]], faces[:, [2, 0]]])
    unique, inverse, counts = np.unique(np.sort(directed, axis=1), axis=0,
                                         return_inverse=True, return_counts=True)
    return directed, unique, inverse, counts


def stats(mesh):
    if mesh.n_cells == 0:
        return {'vertices':int(mesh.n_points),'triangles':0,'boundary_edges':0,
                'nonmanifold_edges':0,'boundary_branch_vertices':0,
                'inconsistent_edges':0,'degenerate_triangles':0,'components':0,'edge_watertight':False}
    f = triangles(mesh)
    directed, unique, inverse, counts = edge_data(f)
    sign = np.where(directed[:, 0] < directed[:, 1], 1, -1)
    sums = np.bincount(inverse, weights=sign, minlength=len(unique))
    a, b, c = np.asarray(mesh.points)[f].transpose(1, 0, 2)
    area = np.linalg.norm(np.cross(b-a, c-a), axis=1) * 0.5
    boundary = unique[counts == 1]
    # Boundary branching catches bow-tie vertices along an open boundary.
    _, degree = np.unique(boundary, return_counts=True)
    components = mesh.connectivity()
    regions = components.cell_data.get('RegionId', np.zeros(mesh.n_cells))
    return {
        'vertices': int(mesh.n_points), 'triangles': int(len(f)),
        'boundary_edges': int(np.sum(counts == 1)),
        'nonmanifold_edges': int(np.sum(counts > 2)),
        'boundary_branch_vertices': int(np.sum(degree != 2)),
        'inconsistent_edges': int(np.sum((counts == 2) & (sums != 0))),
        'degenerate_triangles': int(np.sum(area < 1e-10)),
        'components': int(len(np.unique(regions))),
        'edge_watertight': bool(np.all(counts == 2)),
    }


def clean_surface(raw, scale=1.0):
    if not np.isfinite(scale) or scale <= 0:
        raise ValueError('Hệ số đổi sang mm phải lớn hơn 0.')
    if isinstance(raw, pv.MultiBlock):
        raw = raw.combine().extract_surface(algorithm='dataset_surface')
    elif not isinstance(raw, pv.PolyData):
        raw = raw.extract_surface(algorithm='dataset_surface')
    if raw.n_points == 0 or not np.isfinite(raw.points).all():
        raise ValueError('Mesh rỗng hoặc có tọa độ không hợp lệ.')
    # Remove non-surface cells; merge only coincident points, never fill gaps.
    m = pv.PolyData(np.asarray(raw.points, dtype=float) * scale, raw.faces)
    m = m.triangulate()
    if not len(m.faces):
        raise ValueError('File chỉ có điểm/đường, không có bề mặt. Hãy xuất mesh từ KIRI, không xuất point cloud.')
    m = m.clean(tolerance=0.0)
    m = pv.PolyData(m.points, m.faces).triangulate()
    f = triangles(m)
    pts = np.asarray(m.points, dtype=np.float64)
    area = np.linalg.norm(np.cross(pts[f[:,1]]-pts[f[:,0]],pts[f[:,2]]-pts[f[:,0]]),axis=1)*.5
    keep = area > 1e-10
    removed_degenerate = int(np.sum(~keep))
    f = f[keep]
    if not len(f):
        raise ValueError('Không còn tam giác có diện tích sau khi đọc file.')
    _, idx = np.unique(np.sort(f,axis=1), axis=0, return_index=True)
    removed_duplicate = int(len(f)-len(idx))
    f = f[np.sort(idx)]
    m = pv.PolyData(pts, np.column_stack((np.full(len(f),3),f)).ravel()).clean(tolerance=0.0)
    m.field_data['input_cleanup'] = [json.dumps({'degenerate_faces_removed':removed_degenerate,
                                               'duplicate_faces_removed':removed_duplicate})]
    return m


def read_mesh(path, scale=1.0):
    try:
        return clean_surface(pv.read(path), scale)
    except (FileNotFoundError, OSError) as exc:
        raise ValueError(f'Không đọc được file {Path(path).name}: {exc}') from exc


def prepare_scan(mesh):
    """Analyze pieces in a worker. Keep every piece in the source reference."""
    connected = mesh.connectivity()
    ids = np.asarray(connected.cell_data['RegionId'])
    areas = np.asarray(connected.compute_cell_sizes(length=False, area=True, volume=False).cell_data['Area'])
    counts = np.bincount(ids)
    sums = np.bincount(ids, weights=areas)
    ordered = np.argsort(sums)[::-1]
    pieces = []
    # Expose the twenty largest regions plus an all-pieces option in UI.
    for region in ordered[:20]:
        part = connected.extract_cells(np.flatnonzero(ids == region)).extract_surface(algorithm='dataset_surface')
        part = pv.PolyData(part.points,part.faces).triangulate().clean(tolerance=0.0)
        pieces.append({'id':int(region), 'triangles':int(counts[region]),
                       'area_mm2':float(sums[region]), 'mesh':part})
    return {'source':mesh, 'stats':stats(mesh), 'pieces':pieces,
            'total_pieces':int(len(ordered))}


def display_mesh(mesh, target=60000):
    if mesh.n_cells <= target:
        return mesh
    # Display only. Full-resolution source remains the calculation input.
    return mesh.decimate_pro(1-target/mesh.n_cells, preserve_topology=False,
                             splitting=False, boundary_vertex_deletion=True)


def suggested_points(mesh):
    pts = np.asarray(mesh.points,dtype=float)
    origin = pts.mean(axis=0)
    _, vectors = np.linalg.eigh(np.cov((pts-origin).T))
    z = vectors[:,-1]
    # Fix PCA's arbitrary sign for deterministic suggestions, not anatomical naming.
    if z[np.argmax(abs(z))] < 0:
        z = -z
    values = (pts-origin) @ z
    span = float(np.ptp(values))
    lo, hi = float(values.min()), float(values.max())
    x = vectors[:,-2]
    y = np.cross(z, x)

    # Detect contiguous single-loop, star-shaped sleeve region (avoids fingertips/thumb/open rims).
    f_lo, f_hi = 0.12, 0.88
    safe_lo, safe_hi = lo + f_lo * (hi - lo), lo + f_hi * (hi - lo)
    radius_est = 32.0
    try:
        from cast_template import _segments, _cross
        probe_fracs = np.linspace(0.05, 0.95, 32)
        valid = []
        slice_centers = []
        slice_radii = []
        test_theta = np.linspace(-np.pi, np.pi, 36, endpoint=False)
        for f in probe_fracs:
            zv = lo + f * (hi - lo)
            try:
                xy, edges = _segments(mesh, origin + z * zv, z, x, y)
                c = (xy.min(axis=0) + xy.max(axis=0)) / 2
                a_e, b_e = xy[edges[:, 0]] - c, xy[edges[:, 1]] - c
                delta = b_e - a_e
                ok = True
                rs = []
                for th in test_theta:
                    d_vec = np.array([np.cos(th), np.sin(th)])
                    den = _cross(d_vec, delta)
                    good = abs(den) > 1e-10
                    rr = np.divide(_cross(a_e, delta), den, out=np.zeros(len(a_e)), where=good)
                    tt = np.divide(_cross(a_e, d_vec), den, out=np.zeros(len(a_e)), where=good)
                    hits = np.sort(rr[good & (rr > 1e-6) & (tt >= -1e-8) & (tt <= 1 + 1e-8)])
                    hits = hits[np.r_[True, np.diff(hits) > 1e-4]] if len(hits) else hits
                    if len(hits) != 1:
                        ok = False
                        break
                    rs.append(hits[0])
                valid.append(ok)
                slice_centers.append(c if ok else None)
                slice_radii.append(float(np.median(rs)) if ok and rs else None)
            except Exception:
                valid.append(False)
                slice_centers.append(None)
                slice_radii.append(None)
        # Find longest contiguous True run
        best_start, best_len, cur_start, cur_len = 0, 0, 0, 0
        for idx, ok in enumerate(valid):
            if ok:
                if cur_len == 0:
                    cur_start = idx
                cur_len += 1
                if cur_len > best_len:
                    best_start, best_len = cur_start, cur_len
            else:
                cur_len = 0
        if best_len >= 4:
            # Inset by 1 probe step from ends for guaranteed safety against open boundary / thumb split
            i0 = min(best_start + 1, best_start + best_len - 2)
            i1 = max(best_start + best_len - 2, i0 + 1)
            f_lo = float(probe_fracs[i0])
            f_hi = float(probe_fracs[i1])
            safe_lo = lo + f_lo * (hi - lo)
            safe_hi = lo + f_hi * (hi - lo)
            good_radii = [r for r in slice_radii[i0 : i1 + 1] if r is not None]
            if good_radii:
                radius_est = float(np.median(good_radii))
    except Exception:
        pass

    # Center origin laterally on the valid forearm-wrist segment so 3D rings sit dead-center
    seg_pts = pts[(values >= safe_lo) & (values <= safe_hi)]
    if len(seg_pts) >= 10:
        seg_center = seg_pts.mean(axis=0)
        shift = seg_center - origin
        shift -= z * (shift @ z)
        origin = origin + shift

    z_mid = 0.5 * (safe_lo + safe_hi)
    prox_pt = (origin + z * safe_lo).tolist()
    dist_pt = (origin + z * safe_hi).tolist()
    side_pt = (origin + z * z_mid + x * (radius_est + 6.0)).tolist()

    return {
        'proximal': prox_pt,
        'distal': dist_pt,
        'side': side_pt,
        'span_mm': span,
        'safe_frame': {
            'origin': [round(float(v), 3) for v in origin],
            'axis_z': [round(float(v), 6) for v in z],
            'axis_x': [round(float(v), 6) for v in x],
            'axis_y': [round(float(v), 6) for v in y],
            'safe_min_mm': round(float(safe_lo), 2),
            'safe_max_mm': round(float(safe_hi), 2),
            'default_start_mm': round(float(safe_lo), 2),
            'default_end_mm': round(float(safe_hi), 2),
            'safe_span_mm': round(float(safe_hi - safe_lo), 1),
            'radius_est_mm': round(float(radius_est), 2),
        },
    }


def clinical_frame(mesh, p):
    origin=np.asarray(mesh.center,dtype=float)
    if p.proximal_point is not None or p.distal_point is not None:
        if p.proximal_point is None or p.distal_point is None:
            raise ValueError('Chọn đủ đầu nẹp gần khuỷu và đầu nẹp gần bàn tay.')
        a,b=np.asarray(p.proximal_point,dtype=float),np.asarray(p.distal_point,dtype=float)
        if a.shape != (3,) or b.shape != (3,) or not np.isfinite(np.r_[a,b]).all():
            raise ValueError('Mốc vùng nẹp không hợp lệ.')
        if np.linalg.norm(b-a)<5:
            raise ValueError('Hai đầu nẹp quá gần nhau. Chọn lại trên mesh.')
        z=(b-a)/np.linalg.norm(b-a)
        start=float((a-origin) @ z)-p.start_adjust_mm
        end=float((b-origin) @ z)+p.end_adjust_mm
    elif p.axis == 'AUTO':
        s=suggested_points(mesh)
        return clinical_frame(mesh,replace(p,proximal_point=s['proximal'],distal_point=s['distal']))
    else:
        axis,z,_,start_abs,end_abs=frame(mesh,p)
        start,end=start_abs-origin[axis],end_abs-origin[axis]
    # Estimate the local center from the chosen segment, avoiding hand/finger bias.
    projections=(mesh.points-origin) @ z
    region=np.asarray(mesh.points)[(projections>=start)&(projections<=end)]
    if len(region):
        center=region.mean(axis=0)
        shift=center-origin
        shift-=z*(shift @ z)
        origin+=shift
    if p.side_point is not None:
        side=np.asarray(p.side_point,dtype=float)
        if side.shape != (3,) or not np.isfinite(side).all():
            raise ValueError('Điểm mặt đặt nẹp không hợp lệ.')
        x=side-origin; x-=z*(x @ z)
        if np.linalg.norm(x)<1:
            raise ValueError('Điểm mặt đặt nẹp quá gần trục. Chọn điểm ở bề mặt da.')
        x/=np.linalg.norm(x)
    else:
        helper=np.eye(3)[np.argmin(abs(z))]
        x=helper-z*(helper @ z);x/=np.linalg.norm(x)
    y=np.cross(z,x)
    angle=np.deg2rad(p.opening_rotation_deg)
    x=np.cos(angle)*x+np.sin(angle)*y
    y=np.cross(z,x)
    return origin,z,x,y,start,end


def cut_region(mesh, p, opposite=False):
    origin,z,x,y,start,end=clinical_frame(mesh,p)
    if end-start < 5:
        raise ValueError('Vùng nẹp ngắn dưới 5 mm. Kiểm tra lại hai đầu.')
    if opposite:
        x,y=-x,-y
    patch=mesh.clip(normal=z,origin=origin+z*start,invert=False)
    patch=patch.clip(normal=-z,origin=origin+z*end,invert=False)
    planes=[(z,origin+z*start),(-z,origin+z*end)]
    if p.splint_mode == 'bivalve':
        plane_origin=origin+x*p.seam_gap_mm/2
        patch=patch.clip(normal=x,origin=plane_origin,invert=False)
        planes.append((x,plane_origin))
    else:
        half=np.deg2rad(p.coverage_deg/2)
        n1=np.sin(half)*x-np.cos(half)*y
        n2=np.sin(half)*x+np.cos(half)*y
        if p.coverage_deg<=180:
            patch=patch.clip(normal=n1,origin=origin,invert=False)
            patch=patch.clip(normal=n2,origin=origin,invert=False)
        else:
            a=patch.clip(normal=n1,origin=origin,invert=False)
            b=patch.clip(normal=n1,origin=origin,invert=True)
            b=b.clip(normal=n2,origin=origin,invert=False)
            patch=a.merge(b,merge_points=True)
        planes.extend([(n1,origin),(n2,origin)])
    patch=patch.triangulate().clean(tolerance=1e-8,absolute=True)
    patch=pv.PolyData(patch.points,patch.faces).triangulate().clean(tolerance=0.0)
    return patch,planes,(origin,z,x,y,start,end)


def frame(mesh, p):
    axis = 'XYZ'.index(p.axis)
    z = np.eye(3)[axis]
    x = np.eye(3)[(axis+1) % 3]
    y = np.cross(z, x)
    angle = np.deg2rad(p.opening_rotation_deg)
    normal = np.cos(angle)*x + np.sin(angle)*y
    vals = np.asarray(mesh.points)[:, axis]
    lo, hi = float(vals.min()), float(vals.max())
    start = lo + (hi-lo)*p.start_percent/100
    end = lo + (hi-lo)*p.end_percent/100
    return axis, z, normal, start, end


def sample_points(mesh, maximum=15000):
    pts = np.vstack((mesh.points, mesh.cell_centers().points))
    if len(pts) > maximum:
        pts = pts[np.linspace(0, len(pts)-1, maximum, dtype=int)]
    return pts


def distances(points, target):
    # Unsigned nearest-surface distance. No inside/outside claim on an open mesh.
    result = pv.PolyData(points).compute_implicit_distance(target)
    return np.abs(np.asarray(result['implicit_distance']))


def confirmed_wall_samples(points, shell):
    """Confirm signed-distance candidates by solid-angle winding on a closed shell.

    Pseudonormal distance alone can have the wrong sign near concave shell corners.
    This is a bounded, sampled screen, not a full surface intersection proof.
    """
    if not len(points):return 0
    oriented=shell.compute_normals(point_normals=False,cell_normals=True,
                    consistent_normals=True,auto_orient_normals=True,split_vertices=False)
    signed=np.asarray(pv.PolyData(points).compute_implicit_distance(oriented)['implicit_distance'])
    candidates=points[signed < -.05]
    faces=triangles(oriented)
    if len(candidates)*len(faces)>20_000_000:
        raise ValueError('Kiểm tra va chạm lấy mẫu vượt giới hạn tính toán. Giảm vùng/mật độ hoặc kiểm tra hình học chuyên dụng trước khi xuất.')
    surface=np.asarray(oriented.points,dtype=float)[faces]
    count=0
    for point in candidates:
        v=surface-point
        a,b,c=v[:,0],v[:,1],v[:,2]
        la,lb,lc=(np.linalg.norm(x,axis=1) for x in (a,b,c))
        numerator=np.einsum('ij,ij->i',a,np.cross(b,c))
        denominator=(la*lb*lc+np.einsum('ij,ij->i',a,b)*lc+
                     np.einsum('ij,ij->i',b,c)*la+np.einsum('ij,ij->i',c,a)*lb)
        winding=np.sum(2*np.arctan2(numerator,denominator))/(4*np.pi)
        count+=int(abs(winding)>.5)
    return count


def check_piece_contact(first, second):
    """Triangle contact plus bounded containment samples for two closed pieces.

    No-contact from VTK is not a numerical proof of separation or a minimum gap.
    The winding screen also catches nested shells without surface crossings.
    """
    bounds_a=np.asarray(first.bounds).reshape(3,2)
    bounds_b=np.asarray(second.bounds).reshape(3,2)
    if np.any(bounds_a[:,1]<bounds_b[:,0]) or np.any(bounds_b[:,1]<bounds_a[:,0]):
        return {'status':'NO_CONTACT_DETECTED','method':'disjoint bounding boxes',
                'minimum_gap_mm':None,'containment_sample_count':0}
    _,contacts=first.collision(second,contact_mode=1,box_tolerance=1e-6,cell_tolerance=0.)
    if contacts:
        return {'status':'CONTACT_DETECTED','method':'VTK triangle first-contact',
                'minimum_gap_mm':None,'containment_sample_count':0}
    sample_count=0
    for source,target,bounds in ((first,second,bounds_b),(second,first,bounds_a)):
        points=sample_points(source,maximum=10000)
        points=points[np.all((points>=bounds[:,0]) & (points<=bounds[:,1]),axis=1)]
        sample_count+=len(points)
        if confirmed_wall_samples(points,target):
            return {'status':'CONTAINMENT_DETECTED','method':'VTK triangle contact + sampled solid-angle containment',
                    'minimum_gap_mm':None,'containment_sample_count':sample_count}
    return {'status':'NO_CONTACT_DETECTED','method':'VTK triangle contact + sampled solid-angle containment',
            'minimum_gap_mm':None,'containment_sample_count':sample_count}


def tri_to_quads(mesh):
    """Split each triangle into three planar quads with shared edge midpoints.

    This is a basic all-quad control cage, NOT curvature-aligned retopology.
    The polygon surface is preserved here; Fusion T-Spline smoothing is not.
    """
    f = triangles(mesh)
    edges = np.sort(np.concatenate((f[:, [0, 1]], f[:, [1, 2]], f[:, [2, 0]])), axis=1)
    unique, inv = np.unique(edges, axis=0, return_inverse=True)
    n, nf = mesh.n_points, len(f)
    pts = np.vstack((mesh.points, mesh.points[unique].mean(axis=1), mesh.points[f].mean(axis=1)))
    ab, bc, ca = (inv.reshape(3, nf) + n)
    center = np.arange(nf) + n + len(unique)
    q = np.vstack((np.column_stack((f[:, 0], ab, center, ca)),
                   np.column_stack((f[:, 1], bc, center, ab)),
                   np.column_stack((f[:, 2], ca, center, bc))))
    return pts, q


def thicken_patch(inner, normals, thickness):
    f = triangles(inner)
    n = inner.n_points
    pts = np.vstack((inner.points, inner.points + normals*thickness))
    directed, _, inv, counts = edge_data(f)
    boundary = directed[counts[inv] == 1]
    # Inner has reversed normals; outer has the oriented source normals.
    out = [f[:, ::-1], f+n]
    if len(boundary):
        a, b = boundary.T
        out.extend((np.column_stack((a, b, b+n)), np.column_stack((a, b+n, a+n))))
    faces = np.vstack(out)
    return pv.PolyData(pts, np.column_stack((np.full(len(faces), 3), faces)).ravel())


class DesignProblem(ValueError):
    def __init__(self, message, patch=None):
        super().__init__(message)
        self.patch = patch


def _single(mesh, p, opposite=False, progress=None, fit=None):
    if p.cast_template:
        from cast_template import build_piece
        return build_piece(mesh,p,opposite,progress,fit=fit)
    emit = progress or (lambda percent,text:None)
    emit(15, 'Đang lấy vùng nẹp từ các điểm đã chọn…')
    patch,planes,axes = cut_region(mesh,p,opposite)
    origin,z,x,y,start,end = axes
    if patch.n_cells<4:
        raise DesignProblem('Vùng nẹp rỗng. Chọn lại hai đầu và mặt đặt nẹp.',patch)
    ps=stats(patch)
    if ps['components']!=1:
        raise DesignProblem('Vùng chọn gồm nhiều mảnh. Chọn đúng bề mặt chi ở bước Nạp quét hoặc thu vùng nẹp.',patch)
    if ps['nonmanifold_edges'] or ps['boundary_branch_vertices'] or ps['degenerate_triangles']:
        raise DesignProblem('Vùng nẹp có cạnh hoặc mặt lỗi. Đã hiện vùng này để kiểm tra; chưa thể xuất vỏ.',patch)
    _,edges,_,counts=edge_data(triangles(patch))
    ep=np.asarray(patch.points)[edges[counts==1]]
    tol=max(float(patch.length)*1e-6,1e-5)
    expected=np.zeros(len(ep),dtype=bool)
    for normal,point in planes:
        expected |= np.all(abs((ep-point) @ normal)<tol,axis=1)
    unexpected=int(np.sum(~expected))
    if unexpected:
        raise DesignProblem(f'Có {unexpected} cạnh hở trong vùng nẹp không thuộc đường cắt. '
                            'Vùng xem trước vẫn hiển thị; chuyển mặt nẹp, thu giới hạn hoặc quét bổ sung. Không tự lấp lỗ.',patch)
    emit(30,'Đang dựng bề mặt và chuẩn bị lưới chỉnh Form…')
    low=patch
    messages=[]
    # Work on the selected region, not the whole scan. Defects elsewhere do not block it.
    if patch.n_cells>p.target_triangles:
        candidate=patch.decimate_pro(1-p.target_triangles/patch.n_cells,
            preserve_topology=True,splitting=False,boundary_vertex_deletion=False).clean(tolerance=0.0)
        errs=np.concatenate((distances(sample_points(candidate),patch),distances(sample_points(patch),candidate)))
        if errs.max()<=p.max_sampled_deviation_mm:
            low=candidate
        else:
            messages.append(f'Giữ lưới vùng nẹp đầy đủ vì giảm lưới lệch {errs.max():.3f} mm.')
            if not p.allow_incomplete_preview:
                raise DesignProblem('Sai lệch giảm lưới vượt ngưỡng kỹ thuật.',patch)
    errors=np.concatenate((distances(sample_points(low),patch),distances(sample_points(patch),low)))
    form_available=low.n_cells*3<=9000
    if not form_available:
        messages.append('Đã tạo hình học; lưới còn quá lớn cho gói Form của app. Xuất tham chiếu hoặc retopology trong Fusion/công cụ khác.')
        if not p.allow_incomplete_preview:
            raise DesignProblem('Lưới quá lớn để xuất Form.',patch)
    low=low.compute_normals(point_normals=True,cell_normals=True,split_vertices=False,
                            consistent_normals=True,auto_orient_normals=False,non_manifold_traversal=False)
    normals=np.asarray(low.point_normals,dtype=float)
    radial=low.points-origin
    radial-=np.outer(radial @ z,z)
    orientation_vote=float(np.median(np.sum(normals*radial,axis=1)))
    automatic_flip=p.auto_orient_open_normals and orientation_vote<0
    if automatic_flip != p.flip_normals:
        f=triangles(low)[:,::-1]
        low=pv.PolyData(low.points,np.column_stack((np.full(len(f),3),f)).ravel())
        low=low.compute_normals(point_normals=True,cell_normals=True,split_vertices=False,
                               consistent_normals=True,auto_orient_normals=False)
    normals=np.asarray(low.point_normals,dtype=float).copy()
    lengths=np.linalg.norm(normals,axis=1)
    if np.any(lengths<1e-12):
        raise DesignProblem('Một số đỉnh không có hướng bề mặt rõ. Kiểm tra dữ liệu quét.',patch)
    normals/=lengths[:,None]
    radial = np.asarray(low.points, dtype=float)-origin
    radial -= np.outer(radial @ z, z)
    outward_vote = float(np.median(np.sum(normals*radial, axis=1)))
    if outward_vote <= 0:
        raise DesignProblem('Hướng bề mặt đang quay vào trục chi theo kiểm tra hình học. '
                            'Kiểm tra mũi tên và tùy chọn Đảo hướng; chưa xuất vỏ.', patch)
    emit(60,'Đang thêm lớp đệm, khoảng chừa và vùng tránh tì đè…')
    offset=np.full(low.n_points,p.clearance_mm+p.padding_mm,dtype=float)
    for relief in p.reliefs or []:
        center=np.asarray(relief['point'],dtype=float)
        radius=float(relief['radius_mm']); extra=float(relief['extra_mm'])
        if center.shape!=(3,) or not np.isfinite(np.r_[center,radius,extra]).all() or radius<=0 or extra<0:
            raise DesignProblem('Thông số vùng tránh tì đè không hợp lệ.',patch)
        idx=low.find_closest_point(center)
        d=np.linalg.norm(low.points-center,axis=1)
        # Compact smooth bump, restricted to similarly-facing surfaces.
        weight=np.maximum(0,1-(d/radius)**2)**2
        weight*=np.maximum(0,normals @ normals[idx])**2
        offset+=extra*weight
    inner=low.copy();inner.points=low.points+normals*offset[:,None]
    inner.point_data['nominal_clearance_mm']=offset
    inner.point_data['offset_normal']=normals.copy()
    shell=thicken_patch(inner,normals,p.thickness_mm)
    sh=stats(shell)
    if not sh['edge_watertight'] or sh['nonmanifold_edges'] or sh['degenerate_triangles'] or sh['inconsistent_edges']:
        raise DesignProblem('Vỏ có lỗi sau offset. Bản chọn vùng vẫn được giữ để kiểm tra.',patch)
    emit(85,'Đang kiểm tra cạnh, khoảng cách và độ vừa hình học…')
    measured=distances(sample_points(inner),mesh)
    inner.point_data['measured_scan_distance_mm'] = distances(inner.points, mesh)
    # The generated shell is closed; no inside/outside classification is made on the open scan.
    collision_points = sample_points(mesh, maximum=30000)
    bounds = np.asarray(shell.bounds).reshape(3,2)
    collision_points = collision_points[np.all((collision_points >= bounds[:,0]) &
                                              (collision_points <= bounds[:,1]), axis=1)]
    try:collision_count = confirmed_wall_samples(collision_points,shell)
    except ValueError as exc:raise DesignProblem(str(exc),patch) from exc
    if collision_count:
        raise DesignProblem(f'Có {collision_count} điểm lấy mẫu của chi nằm trong thành nẹp '
                            '(dung sai số học 0,05 mm). Kiểm tra offset, hướng và dữ liệu quét.', patch)
    report={'source':stats(mesh),'patch':stats(low),'shell':sh,
            'quad_faces':int(low.n_cells*3),'length_mm':float(end-start),
            'decimation_sampled_max_mm':float(errors.max()),
            'decimation_sampled_rms_mm':float(np.sqrt(np.mean(errors**2))),
            'decimation_sample_count':int(len(errors)),
            'sampled_unsigned_surface_distance_min_mm':float(measured.min()),
            'sampled_unsigned_surface_distance_max_mm':float(measured.max()),
            'deviation_method':'bidirectional vertex/centroid samples; not a Hausdorff bound',
            'unexpected_boundary_edges':unexpected,'form_available':form_available,
            'normal_direction_heuristic_flip':automatic_flip,
            'normal_radial_vote_mm':outward_vote,
            'sampled_scan_in_wall_count':collision_count,
            'collision_sample_count':int(len(collision_points)),
            'collision_check':'SAMPLED_ONLY; signed-distance candidates confirmed by solid-angle winding; no full triangle intersection guarantee',
            'self_intersection_check':'NOT_IMPLEMENTED','clinical_validation':'NOT_VALIDATED',
            'fusion_conversion':'NOT_TESTED_IN_FUSION',
            'thickness_method':'normal vertex displacement; not a minimum wall thickness guarantee',
            'hole_filling':False,'messages':messages,
            'nominal_clearance_min_mm':float(offset.min()),'nominal_clearance_max_mm':float(offset.max())}
    return {'inner':inner,'shell':shell,'patch':low,'normals':normals,
            'quad':tri_to_quads(inner) if form_available else None,
            'report':report,'status':'ready','export_ready':True,'form_available':form_available}


def validate_parameters(p):
    from cast_template import validate_cast_parameters
    validate_cast_parameters(p)
    values=[p.start_percent,p.end_percent,p.opening_rotation_deg,p.clearance_mm,p.padding_mm,
            p.thickness_mm,p.max_sampled_deviation_mm,p.coverage_deg,p.start_adjust_mm,
            p.end_adjust_mm,p.seam_gap_mm,p.circumference_proximal_mm,p.circumference_mid_mm,
            p.circumference_distal_mm,p.circumference_tolerance_mm]
    if any(isinstance(v,bool) or not isinstance(v,(int,float,np.integer,np.floating)) for v in values) or not np.isfinite(values).all():
        raise ValueError('Thông số phải là số hữu hạn.')
    if p.axis not in ('X','Y','Z','AUTO'):
        raise ValueError('Trục thiết kế không hợp lệ.')
    for flag in (p.flip_normals,p.allow_incomplete_preview,p.auto_orient_open_normals):
        if type(flag) is not bool:raise ValueError('Tùy chọn hướng/xem trước phải là đúng hoặc sai.')
    if isinstance(p.target_triangles,bool) or not isinstance(p.target_triangles,(int,np.integer)):
        raise ValueError('Số mặt phải là số nguyên.')
    if not 0<=p.start_percent<p.end_percent<=100:
        raise ValueError('Giới hạn vùng không hợp lệ.')
    if min(p.clearance_mm,p.padding_mm)<0 or p.thickness_mm<=0:
        raise ValueError('Khoảng chừa và đệm không âm; độ dày phải dương.')
    if not 100<=p.target_triangles<=100000 or p.max_sampled_deviation_mm<=0:
        raise ValueError('Thông số lưới nâng cao không hợp lệ.')
    if not 90<=p.coverage_deg<=270 or p.splint_mode not in ('single','bivalve') or p.seam_gap_mm<0:
        raise ValueError('Kiểu nẹp hoặc mức ôm quanh tay không hợp lệ.')
    if min(p.circumference_proximal_mm,p.circumference_mid_mm,p.circumference_distal_mm)<0 or p.circumference_tolerance_mm<=0:
        raise ValueError('Chu vi không âm và ngưỡng đối chiếu phải dương.')
    for point in (p.proximal_point,p.distal_point,p.side_point):
        if point is not None:
            try:
                valid=(isinstance(point,(list,tuple,np.ndarray)) and len(point)==3
                       and all(not isinstance(v,(bool,np.bool_)) and isinstance(v,(int,float,np.integer,np.floating)) for v in point)
                       and np.isfinite(point).all())
            except (TypeError,ValueError):valid=False
            if not valid:raise ValueError('Tọa độ mốc phải có ba số hữu hạn.')
    if p.reliefs is not None:
        if not isinstance(p.reliefs,list):raise ValueError('Danh sách vùng tránh tì đè không hợp lệ.')
        for relief in p.reliefs:
            try:
                point=relief['point'];radius=relief['radius_mm'];extra=relief['extra_mm']
                valid=(isinstance(point,(list,tuple,np.ndarray)) and len(point)==3
                       and all(not isinstance(v,(bool,np.bool_)) and isinstance(v,(int,float,np.integer,np.floating)) for v in [*point,radius,extra])
                       and np.isfinite([*point,radius,extra]).all() and radius>0 and extra>=0
                       and isinstance(relief.get('name','Vùng tránh tì đè'),str))
            except (TypeError,KeyError,ValueError):valid=False
            if not valid:raise ValueError('Thông số vùng tránh tì đè không hợp lệ.')


def build(mesh,p,progress=None):
    emit=progress or (lambda percent,text:None)
    validate_parameters(p)
    try:
        shared_fit = None
        if p.cast_template:
            from cast_template import ScanFit
            emit(15, 'Đang kiểm vùng scan và lấy mặt cắt cho mẫu nẹp…')
            shared_fit = ScanFit(mesh, p)
        first=_single(mesh,p,progress=emit,fit=shared_fit)
        if p.splint_mode=='single':
            first['pieces']=[first.copy()]
            emit(100,'Hoàn tất xem trước và kiểm tra hình học.')
            return attach_measurements(first,mesh,p)
        second=_single(mesh,p,opposite=True,progress=emit,fit=shared_fit)
        emit(92,'Đang kiểm tra giao nhau giữa hai mảnh…')
        try:piece_check=check_piece_contact(first['shell'],second['shell'])
        except Exception as exc:
            raise DesignProblem('Chưa hoàn thành kiểm tra hai mảnh: '+str(exc),first['patch']) from exc
        if piece_check['status']!='NO_CONTACT_DETECTED':
            raise DesignProblem('Hai mảnh nẹp chạm, giao nhau hoặc có điểm nằm trong thành mảnh còn lại. '
                                'Tăng khe mở và kiểm lại khoảng chừa, vùng nâng, hướng bề mặt.',
                                first['patch'].merge(second['patch'],merge_points=False))
        inner=first['inner'].merge(second['inner'],merge_points=False)
        shell=first['shell'].merge(second['shell'],merge_points=False)
        patch=first['patch'].merge(second['patch'],merge_points=False)
        report=dict(first['report']);report['shell']=stats(shell)
        report['interpiece_check']=piece_check
        report['patch']=stats(patch)
        report['quad_faces']+=second['report']['quad_faces']
        for key in ('ventilation_holes','strap_slots','perforated_quad_faces'):
            if key in report:report[key]+=second['report'].get(key,0)
        report['messages']+=second['report']['messages']
        report['nominal_clearance_min_mm']=min(first['report']['nominal_clearance_min_mm'],second['report']['nominal_clearance_min_mm'])
        report['nominal_clearance_max_mm']=max(first['report']['nominal_clearance_max_mm'],second['report']['nominal_clearance_max_mm'])
        report['form_available']=first['form_available'] and second['form_available']
        report['decimation_sampled_max_mm']=max(first['report']['decimation_sampled_max_mm'],second['report']['decimation_sampled_max_mm'])
        n1,n2=(piece['report']['decimation_sample_count'] for piece in (first,second))
        report['decimation_sampled_rms_mm']=float(np.sqrt((n1*first['report']['decimation_sampled_rms_mm']**2+n2*second['report']['decimation_sampled_rms_mm']**2)/(n1+n2)))
        report['decimation_sample_count']=n1+n2
        report['sampled_unsigned_surface_distance_min_mm']=min(piece['report']['sampled_unsigned_surface_distance_min_mm'] for piece in (first,second))
        report['sampled_unsigned_surface_distance_max_mm']=max(piece['report']['sampled_unsigned_surface_distance_max_mm'] for piece in (first,second))
        report['sampled_scan_in_wall_count']+=second['report']['sampled_scan_in_wall_count']
        report['collision_sample_count']+=second['report']['collision_sample_count']
        result={'inner':inner,'shell':shell,'patch':patch,
                'normals':np.asarray(inner.point_data['offset_normal']).copy(),'quad':None,
                'report':report,'status':'ready','export_ready':True,
                'form_available':report['form_available'],'pieces':[first,second]}
        emit(100,'Hoàn tất hai mảnh nẹp.')
        return attach_measurements(result,mesh,p)
    except DesignProblem as exc:
        if not p.allow_incomplete_preview:
            raise
        emit(100,'Đã giữ vùng xem trước; cần xử lý vùng quét trước khi xuất.')
        return {'status':'preview_only','export_ready':False,'form_available':False,
                'patch':exc.patch,'inner':None,'shell':None,'quad':None,'normals':None,'pieces':[],
                'report':{'messages':[str(exc)],'source':stats(mesh),
                          'patch':stats(exc.patch) if exc.patch is not None else None,
                          'hole_filling':False,'clinical_validation':'NOT_VALIDATED'}}


def attach_measurements(result, mesh, p):
    origin,z,_,_,start,end = clinical_frame(mesh,p)
    rows = compare_sections(mesh,origin,z,start,end,p)
    result['report']['circumference_checks'] = rows
    result['report']['circumference_threshold_note'] = 'User-configurable research threshold, not a clinical acceptance standard.'
    failures = [r for r in rows if r['comparison'] in ('MISMATCH','UNMEASURABLE')]
    result['report']['technical_checks'] = [
        {'name':'Vùng quét đủ bề mặt tại vùng nẹp','status':'PASSED'},
        {'name':'Cạnh vỏ kín và không có mặt suy biến','status':'PASSED'},
        {'name':'Không thấy điểm quét trong thành nẹp khi lấy mẫu','status':'PASSED_SAMPLED'},
        {'name':'Đối chiếu chu vi đã nhập','status':'FAILED' if failures else ('PASSED' if any(r['real_mm'] for r in rows) else 'NOT_ENTERED')},
        {'name':'Tự giao toàn bề mặt / áp lực / độ bền / lâm sàng','status':'NOT_VALIDATED'}]
    if p.splint_mode=='bivalve':
        result['report']['technical_checks'].insert(3,{
            'name':'Hai mảnh: kiểm giao tam giác và bao chứa lấy mẫu',
            'status':'PASSED_SAMPLED'})
    if failures:
        result['status']='blocked';result['export_ready']=False
        result['report']['messages'].append('Chưa xuất: chu vi đã nhập lệch ngưỡng hoặc mặt cắt thiếu/không có một vòng kín. Kiểm tra cùng mặt phẳng đo, tỷ lệ và quét bổ sung.')
    return result


def write_obj(path, points, quads):
    with Path(path).open('w', encoding='utf-8', newline='\n') as f:
        f.write('# SplintFit research control cage. Units: mm. Not a finished splint.\n')
        f.write('o SplintFit_Inner_Control_Cage\n')
        for p in points:
            f.write('v ' + ' '.join(f'{float(v):.9f}' for v in p) + '\n')
        for q in quads:
            f.write('f ' + ' '.join(str(int(v)+1) for v in q) + '\n')


def export_bundle(folder, mesh, result, params, metadata):
    if not result.get('export_ready',False):
        raise ValueError('Vùng xem trước còn lỗi; không xuất vỏ hoặc Form.')
    folder = Path(folder)
    if folder.exists():raise ValueError('Thư mục xuất đã tồn tại. Chọn tên mới để giữ bản cũ.')
    folder.parent.mkdir(parents=True,exist_ok=True)
    # A failed export does not leave a directory looking like a finished bundle.
    with tempfile.TemporaryDirectory(prefix='.splintfit-export-',dir=folder.parent) as temp:
        staging=Path(temp)/'bundle'
        _write_bundle(staging,mesh,result,params,metadata)
        os.rename(staging,folder)
    return folder


def _write_bundle(folder, mesh, result, params, metadata):
    folder.mkdir(parents=True, exist_ok=False)
    pieces=result.get('pieces') or [result]
    for index,piece in enumerate(pieces):
        if len(pieces)>1:
            piece['shell'].save(folder/f'shell_piece_{index+1}_prototype.stl')
            piece['inner'].save(folder/f'inner_piece_{index+1}_reference_mm.stl')
        if piece['quad'] is not None:
            name='splint_form_quad.obj' if len(pieces)==1 else f'splint_form_piece_{index+1}_quad.obj'
            write_obj(folder/name,*piece['quad'])
        if piece.get('perforated_quad') is not None:
            name=f'splint_form_perforated_piece_{index+1}_quad.obj'
            write_obj(folder/name,*piece['perforated_quad'])
    mesh.save(folder/'scan_reference_mm.stl')
    result['inner'].save(folder/'inner_reference_mm.stl')
    result['shell'].save(folder/'shell_prototype_NOT_CLINICALLY_VALIDATED.stl')
    data = {'schema': 'splintfit.form-research.v3', 'units': 'mm',
            'metadata': metadata, 'parameters': asdict(params),
            'report': result['report'],
            'pieces':[{'index':i+1,'report':piece['report'],
                       'shell_file':f'shell_piece_{i+1}_prototype.stl' if len(pieces)>1 else 'shell_prototype_NOT_CLINICALLY_VALIDATED.stl',
                       'form_file':('splint_form_quad.obj' if len(pieces)==1 else f'splint_form_piece_{i+1}_quad.obj') if piece['quad'] is not None else None}
                      for i,piece in enumerate(pieces)],
            'quad_method': result['report'].get('quad_method','three planar quads per triangle; not optimized retopology'),
            'fusion': {'import_units': 'mm', 'convert': 'Quad Mesh to T-Splines',
                       'surface': 'inner', 'thicken': 'outward only',
                       'warning': 'T-Spline smoothing can change fit; compare with scan and inner reference.'}}
    (folder/'parameters_and_report.json').write_text(json.dumps(data, ensure_ascii=False, indent=2,allow_nan=False), encoding='utf-8')
    values={'sf_thickness':params.thickness_mm,'sf_padding':params.padding_mm,
            'sf_clearance':params.clearance_mm,'sf_length':result['report']['length_mm'],
            'sf_coverage':params.coverage_deg,'sf_seam_gap':params.seam_gap_mm,
            'sf_start_extension':params.start_adjust_mm,'sf_end_extension':params.end_adjust_mm}
    fusion={'schema':'splintfit.fusion-parameters.v1','units':'mm',
            'parameters':[{'name':name,'value':value,'unit':'deg' if name=='sf_coverage' else 'mm'} for name,value in values.items()],
            'note':'Parameters require explicit links to Fusion features. Imported Form does not regenerate from these values.'}
    (folder/'fusion_user_parameters.json').write_text(json.dumps(fusion,ensure_ascii=False,indent=2,allow_nan=False),encoding='utf-8')
    with (folder/'circumference_checks.csv').open('w',encoding='utf-8-sig',newline='') as stream:
        keys=['name','fraction','circumference_mm','real_mm','difference_mm','tolerance_mm','status','comparison']
        writer=csv.DictWriter(stream,fieldnames=keys,extrasaction='ignore');writer.writeheader()
        writer.writerows(result['report'].get('circumference_checks',[]))
    base=Path(__file__).parent
    shutil.copyfile(base/'FUSION_FORM.md',folder/'FUSION_FORM.md')
    shutil.copytree(base/'fusion',folder/'fusion',ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
    from viewer import write_viewer
    write_viewer(folder,mesh,result)
    return folder


def demo_mesh():
    # Synthetic tapered elliptical forearm-like tube, not patient anatomy.
    ns, nz = 48, 31
    theta = np.linspace(0, 2*np.pi, ns, endpoint=False)
    pts = []
    for z in np.linspace(0, 230, nz):
        a, b = 24+10*z/230, 19+7*z/230
        pts.extend(np.column_stack((a*np.cos(theta), b*np.sin(theta), np.full(ns, z))))
    faces = []
    for i in range(nz-1):
        for j in range(ns):
            a, b = i*ns+j, i*ns+(j+1)%ns
            faces.append([4, a, b, b+ns, a+ns])
    return pv.PolyData(np.asarray(pts), np.asarray(faces).ravel()).triangulate()
