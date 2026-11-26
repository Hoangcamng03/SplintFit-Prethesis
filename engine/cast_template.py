"""Structured scan-fitted cast panels with staggered honeycomb-like ventilation & flared rims.

Only single, closed, star-shaped cross-sections are supported. Missing data is
rejected, never bridged. All coordinates remain in the scan's millimetre frame.
The full perforated quad surface and the simple Fusion 360 Form base are separate assets.
"""
import numpy as np
import pyvista as pv
from scipy.interpolate import RegularGridInterpolator


def validate_cast_parameters(p):
    for key in ('cast_template', 'ventilation'):
        if type(getattr(p, key)) is not bool:
            raise ValueError('Tùy chọn tạo nẹp phải là đúng/sai.')
    ranges = {
        'hole_pitch_mm': (15, 45),
        'hole_ratio': (0.2, 0.68),
        'hand_notch_depth_mm': (0, 60),
        'hand_notch_width_deg': (30, 140),
        'hand_notch_angle_deg': (-180, 180),
        'rim_flare_mm': (0, 5.0),
    }
    for key, (lo, hi) in ranges.items():
        if not hasattr(p, key):
            continue
        v = getattr(p, key)
        if isinstance(v, (bool, np.bool_)) or not isinstance(v, (int, float, np.integer, np.floating)) or not np.isfinite(v) or not lo <= v <= hi:
            raise ValueError('Thông số mẫu nẹp không hợp lệ: ' + key)


def _segments(mesh, origin, z, x, y):
    """Read observed section segments, verifying a single cycle."""
    section = mesh.slice(normal=z, origin=origin).clean(tolerance=1e-6, absolute=True)
    edges = []
    lines = np.asarray(section.lines)
    i = 0
    while i < len(lines):
        count = int(lines[i])
        ids = lines[i + 1 : i + count + 1]
        edges.extend(zip(ids[:-1], ids[1:]))
        i += count + 1
    if not edges:
        raise ValueError('Không có mặt cắt tại vùng đã chọn.')
    edges = np.unique(np.sort(np.asarray(edges), axis=1), axis=0)
    lengths = np.linalg.norm(section.points[edges[:, 1]] - section.points[edges[:, 0]], axis=1)
    edges = edges[lengths > 1e-7]
    verts, counts = np.unique(edges, return_counts=True)
    if not len(edges) or np.any(counts != 2):
        raise ValueError('Mặt cắt hở: cần thu vùng hoặc quét bổ sung; không tự nối dữ liệu thiếu.')
    adj = {int(v): [] for v in verts}
    for a, b in edges:
        adj[int(a)].append(int(b))
        adj[int(b)].append(int(a))
    visited = set()
    todo = [int(verts[0])]
    while todo:
        v = todo.pop()
        if v not in visited:
            visited.add(v)
            todo.extend(adj[v])
    if len(visited) != len(verts):
        raise ValueError('Có nhiều vòng mặt cắt (ví dụ ngón tay rời). Thu vùng dưới các ngón hoặc dùng thiết kế chuyên biệt.')
    relative = section.points - origin
    xy = np.column_stack((relative @ x, relative @ y))
    return xy, edges


def _cross(a, b):
    return a[..., 0] * b[..., 1] - a[..., 1] * b[..., 0]


class ScanFit:
    def __init__(self, mesh, p):
        from geometry import clinical_frame, edge_data, triangles, DesignProblem

        self.origin, self.z, self.x, self.y, self.start, self.end = clinical_frame(mesh, p)
        if self.end - self.start < 20 or p.hand_notch_depth_mm > (self.end - self.start) * 0.45:
            raise DesignProblem('Vùng nẹp quá ngắn hoặc đường mở bàn tay quá sâu.', mesh)
        # Detect holes anywhere in the entire ROI, not only at sampled slices.
        roi = mesh.clip(normal=self.z, origin=self.origin + self.z * self.start, invert=False)
        roi = roi.clip(normal=self.z, origin=self.origin + self.z * self.end, invert=True).triangulate().clean()
        if roi.n_cells < 4:
            raise DesignProblem('Vùng chọn không có bề mặt.', roi)
        _, edges, _, counts = edge_data(triangles(roi))
        ends = np.asarray(roi.points)[edges[counts == 1]]
        tol = max(float(roi.length) * 1e-6, 1e-4)
        near_start = np.all(abs((ends - self.origin) @ self.z - self.start) < tol, axis=1)
        near_end = np.all(abs((ends - self.origin) @ self.z - self.end) < tol, axis=1)
        if np.any(counts > 2) or np.any(~(near_start | near_end)):
            raise DesignProblem('Vùng scan thiếu dữ liệu hoặc có cạnh lỗi; không tự vá lỗ trên vùng tiếp xúc da.', roi)
        self.roi = roi
        # <= 3.5 mm spacing; 128 angular samples.
        zs = np.linspace(self.start, self.end, max(44, int((self.end - self.start) / 3.5) + 1))
        self.theta = np.linspace(-np.pi, np.pi, 129)
        cs, rs = [], []
        for zvalue in zs:
            try:
                xy, edges = _segments(mesh, self.origin + self.z * zvalue, self.z, self.x, self.y)
                c = (xy.min(axis=0) + xy.max(axis=0)) / 2
                a, b = xy[edges[:, 0]] - c, xy[edges[:, 1]] - c
                delta = b - a
                radii = []
                for theta in self.theta:
                    direction = np.array([np.cos(theta), np.sin(theta)])
                    den = _cross(direction, delta)
                    good = abs(den) > 1e-10
                    rr = np.divide(_cross(a, delta), den, out=np.zeros(len(a)), where=good)
                    tt = np.divide(_cross(a, direction), den, out=np.zeros(len(a)), where=good)
                    hits = np.sort(rr[good & (rr > 1e-6) & (tt >= -1e-8) & (tt <= 1 + 1e-8)])
                    hits = hits[np.r_[True, np.diff(hits) > 1e-4]] if len(hits) else hits
                    if len(hits) != 1:
                        raise ValueError('Mặt cắt không phù hợp mẫu một vòng hướng tâm; không tự suy đoán vùng lõm/ngón cái.')
                    radii.append(hits[0])
                cs.append(c)
                rs.append(radii)
            except ValueError as exc:
                raise DesignProblem(f'Mặt cắt cách đầu vùng {zvalue - self.start:.1f} mm: {exc}', roi) from exc
        self.zs = zs
        self.centers = np.asarray(cs)
        self.radii = np.asarray(rs)
        self.interp = RegularGridInterpolator((zs, self.theta), self.radii, bounds_error=True)
        self.radius_min = float(self.radii.min())
        self.radius_median = float(np.median(self.radii))

    def surface(self, theta, zvalue):
        theta, zvalue = np.broadcast_arrays(theta, zvalue)
        shape = theta.shape
        t = (theta.ravel() + np.pi) % (2 * np.pi) - np.pi
        z = np.clip(zvalue.ravel(), self.zs[0], self.zs[-1])
        r = self.interp(np.column_stack((z, t)))
        cx = np.interp(z, self.zs, self.centers[:, 0])
        cy = np.interp(z, self.zs, self.centers[:, 1])
        points = self.origin + z[:, None] * self.z + (cx + r * np.cos(t))[:, None] * self.x + (cy + r * np.sin(t))[:, None] * self.y
        return points.reshape(shape + (3,))

    def points_normals(self, theta, zvalue):
        theta = np.asarray(theta)
        zvalue = np.asarray(zvalue)
        raw = self.surface(theta, zvalue)
        dt = self.surface(theta + 1e-4, zvalue) - self.surface(theta - 1e-4, zvalue)
        lo = np.maximum(self.start, zvalue - 0.02)
        hi = np.minimum(self.end, zvalue + 0.02)
        dz = self.surface(theta, hi) - self.surface(theta, lo)
        n = np.cross(dt, dz)
        length = np.linalg.norm(n, axis=-1, keepdims=True)
        if np.any(length < 1e-12):
            raise ValueError('Không xác định được hướng của mặt nền.')
        return raw, n / length


def _poly(points, quads):
    return pv.PolyData(points, np.column_stack((np.full(len(quads), 4), quads)).ravel())


def _tiles(cols, rows, ventilation, ratio, staggered=True):
    """Conforming 16-edge quad tiles with brick-staggered honeycomb-like through-holes.

    Uses uniformly spaced boundary nodes [-1, -0.5, 0, +0.5, +1] along every tile edge
    so half-column shifted (staggered) rows share 100% identical seam vertices with
    adjacent rows — guaranteeing watertight, manifold all-quad topology.
    """
    points = []
    faces = []
    lookup = {}
    holes = []
    slots = []

    # 16 boundary points on unit square [-1, 1]^2 with uniform 0.5 spacing (CCW starting at (1, 0))
    square = np.array([
        [1.0, 0.0], [1.0, 0.5], [1.0, 1.0],
        [0.5, 1.0], [0.0, 1.0], [-0.5, 1.0], [-1.0, 1.0],
        [-1.0, 0.5], [-1.0, 0.0], [-1.0, -0.5], [-1.0, -1.0],
        [-0.5, -1.0], [0.0, -1.0], [0.5, -1.0], [1.0, -1.0],
        [1.0, -0.5],
    ])
    # Matching 16-point smooth rounded-hex/oval inner loop for organic medical-cast look
    angles = np.arctan2(square[:, 1], square[:, 0])
    # Slight superellipse/hex shaping gives sleeker struts than tiny circles
    r_shape = 1.0 + 0.06 * np.cos(6.0 * angles)
    hole_loop = np.column_stack((r_shape * np.cos(angles), r_shape * np.sin(angles)))

    def vertex(uv):
        key = (round(float(uv[0]), 10), round(float(uv[1]), 10))
        if key not in lookup:
            lookup[key] = len(points)
            points.append([float(uv[0]), float(uv[1])])
        return lookup[key]

    def add_solid_rect(u0, u1, v0, v1, nu=4, nv=4):
        us = np.linspace(u0, u1, nu + 1)
        vs = np.linspace(v0, v1, nv + 1)
        ids = [[vertex((u, v)) for u in us] for v in vs]
        for b in range(nv):
            for a in range(nu):
                faces.append([ids[b][a], ids[b][a + 1], ids[b + 1][a + 1], ids[b + 1][a]])

    def add_hole_tile(u0, u1, v0, v1, scale_xy, is_slot=False):
        cu, cv = 0.5 * (u0 + u1), 0.5 * (v0 + v1)
        hu, hv = 0.5 * (u1 - u0), 0.5 * (v1 - v0)
        outside = [vertex((cu + p[0] * hu, cv + p[1] * hv)) for p in square]
        mid_ring = [
            vertex((
                cu + 0.5 * (p[0] + q[0] * scale_xy[0]) * hu,
                cv + 0.5 * (p[1] + q[1] * scale_xy[1]) * hv,
            ))
            for p, q in zip(square, hole_loop)
        ]
        inside = [vertex((cu + q[0] * hu * scale_xy[0], cv + q[1] * hv * scale_xy[1])) for q in hole_loop]
        for i in range(16):
            j = (i + 1) % 16
            faces.append([outside[i], outside[j], mid_ring[j], mid_ring[i]])
            faces.append([mid_ring[i], mid_ring[j], inside[j], inside[i]])
        (slots if is_slot else holes).append([cu, cv])

    bands = {int(round((rows - 1) * f)) for f in (0.20, 0.50, 0.80)}

    for row in range(rows):
        v0 = row / rows
        v1 = (row + 1) / rows
        is_rim = row == 0 or row == rows - 1
        is_band = row in bands
        shift_row = staggered and (not is_rim) and (not is_band) and (row % 2 == 1) and cols >= 4

        if shift_row:
            # Left solid half-tile [0, 0.5/cols] (2 segments along u to match 0.25 step)
            add_solid_rect(0.0, 0.5 / cols, v0, v1, nu=2, nv=4)
            # Staggered interior full tiles [0.5 + c, 1.5 + c] / cols
            for col in range(cols - 1):
                u0 = (col + 0.5) / cols
                u1 = (col + 1.5) / cols
                if ventilation:
                    add_hole_tile(u0, u1, v0, v1, (ratio, min(0.70, ratio * 1.08)), is_slot=False)
                else:
                    add_solid_rect(u0, u1, v0, v1, nu=4, nv=4)
            # Right solid half-tile [(cols - 0.5)/cols, 1.0]
            add_solid_rect((cols - 0.5) / cols, 1.0, v0, v1, nu=2, nv=4)
        else:
            for col in range(cols):
                u0 = col / cols
                u1 = (col + 1) / cols
                is_slot = is_band and col in (0, cols - 1) and (not is_rim)
                is_vent = ventilation and (not is_band) and (not is_rim) and 0 < col < cols - 1
                if is_slot:
                    add_hole_tile(u0, u1, v0, v1, (0.30, 0.62), is_slot=True)
                elif is_vent:
                    add_hole_tile(u0, u1, v0, v1, (ratio, min(0.70, ratio * 1.08)), is_slot=False)
                else:
                    add_solid_rect(u0, u1, v0, v1, nu=4, nv=4)

    return np.asarray(points), np.asarray(faces), holes, slots


def build_piece(mesh, p, opposite=False, progress=None, fit=None):
    from geometry import (
        DesignProblem,
        stats,
        thicken_patch,
        distances,
        sample_points,
        confirmed_wall_samples,
    )

    emit = progress or (lambda *args: None)
    if fit is None:
        emit(15, 'Đang kiểm vùng scan và lấy mặt cắt cho mẫu nẹp…')
        fit = ScanFit(mesh, p)
    if p.splint_mode == 'bivalve':
        if p.seam_gap_mm <= 0:
            raise DesignProblem('Mẫu hai mảnh cần khe mở dương.', fit.roi)
        gap = p.seam_gap_mm / 2
        if gap >= fit.radius_min * 0.5:
            raise DesignProblem('Khe mở quá rộng so với kích thước chi.', fit.roi)
        half = np.pi / 2 - np.arcsin(gap / fit.radius_min)
    else:
        half = np.deg2rad(p.coverage_deg) / 2

    center = np.pi if opposite else 0.0
    low = center - half
    high = center + half
    length = fit.end - fit.start
    cols = max(4, int(2 * half * fit.radius_median / p.hole_pitch_mm))
    rows = max(7, int(length / p.hole_pitch_mm))
    rim_flare_mm = float(getattr(p, 'rim_flare_mm', 1.4))

    def map_uv(uv):
        theta = low + (high - low) * uv[:, 0]
        relative = (theta - np.deg2rad(p.hand_notch_angle_deg) + np.pi) % (2 * np.pi) - np.pi
        width = np.deg2rad(p.hand_notch_width_deg) / 2
        # Smooth anatomical U-shaped distal cutout for wrist/thumb-base mobility
        dip = p.hand_notch_depth_mm * np.maximum(0, 1 - (relative / width) ** 2) ** 2
        z = fit.start + uv[:, 1] * (length - dip)
        raw, normals = fit.points_normals(theta, z)
        offsets = np.full(len(raw), p.clearance_mm + p.padding_mm)

        # Gentle proximal & distal rim flare (~14 mm band) so rims don't dig into skin
        if rim_flare_mm > 0:
            v = uv[:, 1]
            band = min(0.14, 15.0 / max(length, 40.0))
            prox_flare = np.maximum(0.0, 1.0 - v / band) ** 2
            dist_flare = np.maximum(0.0, 1.0 - (1.0 - v) / band) ** 2
            offsets += rim_flare_mm * (prox_flare + dist_flare)

        for relief in p.reliefs or []:
            point = np.asarray(relief['point'])
            radius = relief['radius_mm']
            extra = relief['extra_mm']
            idx = np.argmin(np.linalg.norm(raw - point, axis=1))
            weight = np.maximum(0, 1 - (np.linalg.norm(raw - point, axis=1) / radius) ** 2) ** 2
            weight *= np.maximum(0, normals @ normals[idx]) ** 2
            offsets += extra * weight
        return raw, raw + normals * offsets[:, None], normals, offsets

    emit(45, 'Đang tạo lưới thoáng tổ ong so le, khe đai và mặt nền Fusion Form…')
    uv, q, holes, slots = _tiles(cols, rows, p.ventilation, p.hole_ratio, staggered=True)
    raw, points, normals, offsets = map_uv(uv)
    inner = _poly(points, q).triangulate()
    inner.point_data['offset_normal'] = normals
    inner.point_data['nominal_clearance_mm'] = offsets
    shell = thicken_patch(inner, normals, p.thickness_mm)
    sh = stats(shell)
    if not sh['edge_watertight'] or sh['nonmanifold_edges'] or sh['degenerate_triangles'] or sh['inconsistent_edges'] or sh['components'] != 1:
        raise DesignProblem('Vỏ mẫu có lỗi topology; cần thay thông số hoặc vùng scan.', fit.roi)

    # Separate regular, low-density All-Quad control cage for Fusion 360 Form (T-Spline)
    nc = max(14, cols * 3)
    nr = max(24, rows * 3)
    simple_uv = np.array([[j / nc, i / nr] for i in range(nr + 1) for j in range(nc + 1)])
    simple_q = np.array([[i * (nc + 1) + j, i * (nc + 1) + j + 1, (i + 1) * (nc + 1) + j + 1, (i + 1) * (nc + 1) + j] for i in range(nr) for j in range(nc)])
    _, simple_points, _, _ = map_uv(simple_uv)

    errors = distances(raw, mesh)
    if errors.max() > p.max_sampled_deviation_mm:
        raise DesignProblem(f'Xấp xỉ scan lệch {errors.max():.3f} mm tại mẫu kiểm, vượt ngưỡng đã chọn.', fit.roi)

    emit(80, 'Đang kiểm vỏ kín và va chạm với bề mặt chi…')
    measured = distances(sample_points(inner), mesh)
    inner.point_data['measured_scan_distance_mm'] = distances(inner.points, mesh)
    collision_points = sample_points(mesh, maximum=15000)
    bounds = np.asarray(shell.bounds).reshape(3, 2)
    collision_points = collision_points[np.all((collision_points >= bounds[:, 0]) & (collision_points <= bounds[:, 1]), axis=1)]
    count = confirmed_wall_samples(collision_points, shell)
    if count:
        raise DesignProblem(f'Có {count} điểm scan nằm trong thành nẹp. Hãy tăng khoảng chừa thoáng hoặc kiểm tra vùng chọn.', fit.roi)

    report = {
        'source': stats(mesh),
        'patch': stats(inner),
        'shell': sh,
        'length_mm': float(length),
        'quad_faces': int(len(simple_q)),
        'form_available': True,
        'quad_method': 'regular anatomical-coordinate all-quad grid with flared rims for Fusion T-Spline',
        'perforated_quad_faces': int(len(q)),
        'ventilation_holes': len(holes),
        'strap_slots': len(slots),
        'grid_tiles': [cols, rows],
        'rim_flare_mm': rim_flare_mm,
        'template_engine': 'cross-section radial fit, staggered honeycomb-like all-quad panels',
        'hand_notch_depth_mm': p.hand_notch_depth_mm,
        'decimation_sampled_max_mm': float(errors.max()),
        'decimation_sampled_rms_mm': float(np.sqrt(np.mean(errors ** 2))),
        'decimation_sample_count': len(errors),
        'deviation_method': 'unoffset constructed-vertex distance to scan; not a Hausdorff bound',
        'sampled_unsigned_surface_distance_min_mm': float(measured.min()),
        'sampled_unsigned_surface_distance_max_mm': float(measured.max()),
        'nominal_clearance_min_mm': float(offsets.min()),
        'nominal_clearance_max_mm': float(offsets.max()),
        'sampled_scan_in_wall_count': count,
        'collision_sample_count': len(collision_points),
        'collision_check': 'SAMPLED_ONLY',
        'self_intersection_check': 'NOT_IMPLEMENTED',
        'clinical_validation': 'NOT_VALIDATED',
        'fusion_conversion': 'NOT_TESTED_IN_FUSION',
        'hole_filling': False,
        'messages': [
            f'Mảnh nẹp có {len(holes)} lỗ thoáng tổ ong so le, {len(slots)} khe luồn dây đai và loe mép {rim_flare_mm:.1f} mm; chưa kiểm tiếp xúc/áp lực.',
            'Gói Fusion Form gồm bản nền trơn All-Quad (khuyên dùng để kéo nắn T-Spline) và bản đã đục lỗ.',
            'Cần bo tròn mép (Fillet) và kiểm tra lại độ vừa với scan_reference_mm.stl trong Fusion 360 trước khi in 3D.',
        ],
    }
    return {
        'inner': inner,
        'shell': shell,
        'patch': fit.roi,
        'normals': normals,
        'quad': (simple_points, simple_q),
        'perforated_quad': (points, q),
        'report': report,
        'status': 'ready',
        'export_ready': True,
        'form_available': True,
    }


def hand_demo_mesh():
    """Anatomical synthetic forearm-wrist-palm envelope (single closed star-shaped slices).

    Includes realistic forearm muscle taper, wrist narrowing, subtle ulnar/radial
    styloid prominences, dorsopalmar palm flattening, and thenar eminence bulge.
    """
    levels = np.array([0, 45, 95, 145, 185, 205, 235, 270, 300.0])
    # Mediolateral (a) and dorsopalmar (b) half-axes in mm
    a_base = np.array([38.0, 37.5, 33.5, 28.0, 25.5, 27.0, 36.5, 42.5, 41.0])
    b_base = np.array([32.0, 31.0, 27.5, 22.5, 19.5, 19.0, 17.5, 15.5, 14.5])
    # Subtle natural anatomical centerline curvature (gentle wrist extension/ulnar offset)
    cx_curve = np.array([0.0, 0.5, 1.0, 0.5, 0.0, -1.0, -2.5, -3.5, -4.0])
    cy_curve = np.array([0.0, 0.0, -0.5, -1.0, -0.5, 1.5, 3.5, 5.0, 5.5])

    ns = 96
    nz = 91
    theta = np.linspace(0, 2 * np.pi, ns, endpoint=False)
    zs = np.linspace(0, 300.0, nz)
    points = []

    for z in zs:
        aa = np.interp(z, levels, a_base)
        bb = np.interp(z, levels, b_base)
        cx = np.interp(z, levels, cx_curve)
        cy = np.interp(z, levels, cy_curve)

        # Base elliptical radius with slight anatomical squaring at palm
        palm_w = np.clip((z - 195.0) / 70.0, 0.0, 1.0)
        x = aa * np.cos(theta)
        y = bb * np.sin(theta)

        # Gentle dorsal flattening & palmar arch in palm region
        y = y - 2.2 * palm_w * np.exp(-((theta - np.pi / 2) / 0.75) ** 2)

        # Thenar eminence (thumb-base muscle pad) on radial-volar side (around theta = -0.65 rad, z ~ 220..265)
        thenar_z = np.exp(-((z - 238.0) / 26.0) ** 2)
        thenar_t = np.exp(-(((theta + 0.65 + np.pi) % (2 * np.pi) - np.pi) / 0.55) ** 2)
        thenar = 6.5 * thenar_z * thenar_t

        # Subtle ulnar styloid prominence at wrist (theta ~ pi, z ~ 188)
        styloid_z = np.exp(-((z - 188.0) / 11.0) ** 2)
        styloid_t = np.exp(-(((theta - np.pi + np.pi) % (2 * np.pi) - np.pi) / 0.35) ** 2)
        styloid = 2.4 * styloid_z * styloid_t

        r_add = thenar + styloid
        x = cx + x + r_add * np.cos(theta)
        y = cy + y + r_add * np.sin(theta)
        points.extend(np.column_stack((x, y, np.full(ns, z))))

    q = []
    for i in range(nz - 1):
        for j in range(ns):
            n = i * ns + j
            m = i * ns + (j + 1) % ns
            q.append([n, m, m + ns, n + ns])
    return _poly(np.asarray(points), np.asarray(q)).triangulate()
