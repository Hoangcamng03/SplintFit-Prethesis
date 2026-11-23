"""Measurements from observed surface only. Never bridge a missing contour."""
import numpy as np


def closed_section(mesh, origin, normal):
    section = mesh.slice(normal=normal, origin=origin).clean(tolerance=1e-7, absolute=True)
    lines = np.asarray(section.lines)
    edges = []
    cursor = 0
    while cursor < len(lines):
        count = int(lines[cursor]); ids = lines[cursor+1:cursor+1+count]
        edges.extend(zip(ids[:-1], ids[1:])); cursor += count+1
    if not edges:
        return {'status': 'NO_CONTOUR', 'circumference_mm': None}
    edges = np.unique(np.sort(np.asarray(edges, dtype=int), axis=1), axis=0)
    lengths = np.linalg.norm(section.points[edges[:, 1]]-section.points[edges[:, 0]], axis=1)
    edges, lengths = edges[lengths > 1e-8], lengths[lengths > 1e-8]
    if not len(edges):
        return {'status': 'NO_CONTOUR', 'circumference_mm': None}
    vertices, degree = np.unique(edges, return_counts=True)
    adjacency = {int(v): set() for v in vertices}
    for a, b in edges:
        adjacency[int(a)].add(int(b)); adjacency[int(b)].add(int(a))
    unseen = set(adjacency); components = 0
    while unseen:
        components += 1; todo = [unseen.pop()]
        while todo:
            for other in adjacency[todo.pop()]:
                if other in unseen:
                    unseen.remove(other); todo.append(other)
    closed = bool(np.all(degree == 2) and components == 1)
    return {'status': 'CLOSED' if closed else 'OPEN_OR_MULTIPLE_CONTOURS',
            'circumference_mm': float(lengths.sum()) if closed else None,
            'components': components, 'segment_count': int(len(edges)),
            'interpolation': False}


def compare_sections(mesh, origin, axis, start, end, p):
    rows = []
    definitions = [('proximal', 0., p.circumference_proximal_mm),
                   ('middle', .5, p.circumference_mid_mm),
                   ('distal', 1., p.circumference_distal_mm)]
    for name, fraction, actual in definitions:
        position = start+(end-start)*fraction
        center = origin+axis*position
        row = closed_section(mesh, center, axis)
        row.update(name=name, fraction=fraction, plane_origin_mm=center.tolist(),
                   plane_normal=axis.tolist(), real_mm=actual if actual > 0 else None,
                   tolerance_mm=p.circumference_tolerance_mm, difference_mm=None)
        if actual <= 0:
            row['comparison'] = 'NOT_ENTERED'
        elif row['circumference_mm'] is None:
            row['comparison'] = 'UNMEASURABLE'
        else:
            row['difference_mm'] = row['circumference_mm']-actual
            row['comparison'] = 'WITHIN_TOLERANCE' if abs(row['difference_mm']) <= p.circumference_tolerance_mm else 'MISMATCH'
        rows.append(row)
    return rows
