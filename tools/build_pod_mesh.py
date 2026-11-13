"""v4: hand-built quad topology. The pod is one swept shell: 40 columns x N rings, every face a quad,
its 40 columns line up with the gauge's 40 segments.

Model space: gauge face centred on the origin, facing +Y (towards the driver), Z up.
"""
import math, sys
import numpy as np
import bpy, bmesh
from mathutils import Matrix

import os
C = np.array([float(x) for x in os.environ.get('DBG_C', '0.5906,-0.3945,1.0753').split(',')]); YAW = float(os.environ.get('DBG_YAW', '23'))
EDGE = np.array([float(x) for x in os.environ.get("DBG_EDGE","0.601,-0.477,1.066").split(",")]); FACE_T = np.array([0.042, 0.024, 0.002]); U = np.array([float(x) for x in os.environ.get("DBG_U","-0.079,0.242,0.17").split(",")])
SEG = 40
R_SCREEN = 0.0235
SHARP_DEG = 38.0

def rz(deg):
    a = math.radians(deg); c, s = math.cos(a), math.sin(a)
    return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]])
def unit(v):
    v = np.asarray(v, float); return v / np.linalg.norm(v)
def arc(cx, cy, r, a0, a1, steps):
    return [(cx + r * math.cos(math.radians(a0 + (a1 - a0) * k / steps)),
             cy + r * math.sin(math.radians(a0 + (a1 - a0) * k / steps))) for k in range(steps + 1)]

bpy.ops.wm.read_factory_settings(use_empty=True)

# ---------------------------------------------------------------- pillar frame (model space)
Rinv = rz(-YAW)
um = unit(Rinv @ U)
tm = Rinv @ FACE_T; tm = unit(tm - np.dot(tm, um) * um)
nf = np.cross(um, tm)
Un = unit(U)
foot_car = EDGE + unit(FACE_T) * 0.018
foot_car = foot_car + Un * np.dot(C - foot_car, Un)      # slide along the pillar to sit level with the gauge
foot_c = Rinv @ (foot_car - C)
if np.dot(nf, -foot_c) < 0: nf = -nf
pad_c = foot_c

# sweep frames: a = "long" axis, b = d x a, d = direction of travel (cup -> pillar)
d0 = np.array([0.0, -1.0, 0.0]); a0 = unit(um - np.dot(um, d0) * d0); b0 = np.cross(d0, a0)
d1 = -nf;                        a1 = um;                              b1 = np.cross(d1, a1)
q0 = Matrix(np.column_stack([a0, b0, d0]).tolist()).to_quaternion()
q1 = Matrix(np.column_stack([a1, b1, d1]).tolist()).to_quaternion()

def frame(t):
    m = np.array(q0.slerp(q1, t).to_matrix())
    return m[:, 0], m[:, 1], m[:, 2]

# 2D outlines, both start on the +a axis and run towards +b
def circle2d(r):
    return np.array([[r * math.cos(2 * math.pi * i / SEG), r * math.sin(2 * math.pi * i / SEG)] for i in range(SEG)])

def stadium2d(half_len, r):
    """Rounded-end outline sampled at SEG equal arc-length steps, starting at the +a tip."""
    dense = []
    n = 400
    for k in range(n):                                   # +a cap, from -b side round to +b side
        a = -math.pi / 2 + math.pi * k / n; dense.append((half_len + r * math.cos(a), r * math.sin(a)))
    for k in range(n):
        dense.append((half_len - 2 * half_len * k / n, r))
    for k in range(n):
        a = math.pi / 2 + math.pi * k / n; dense.append((-half_len + r * math.cos(a), r * math.sin(a)))
    for k in range(n):
        dense.append((-half_len + 2 * half_len * k / n, -r))
    dense = np.array(dense)
    seg = np.linalg.norm(np.roll(dense, -1, axis=0) - dense, axis=1)
    cum = np.r_[0, np.cumsum(seg)]; total = cum[-1]
    tip = cum[n // 2]                                    # arc length at the +a tip
    out = []
    closed = np.vstack([dense, dense[0]])
    for i in range(SEG):
        s = (tip + total * i / SEG) % total
        j = np.searchsorted(cum, s, side='right') - 1; j = min(j, len(dense) - 1)
        f = (s - cum[j]) / max(seg[j], 1e-12)
        out.append(closed[j] * (1 - f) + closed[j + 1] * f)
    return np.array(out)

# ---------------------------------------------------------------- pod shell
CUP_R_IN, CUP_R = 0.0280, 0.0336   # inner edge sits inside the gauge wall: no gap to see through
FRONT, SLEEVE_END = -0.0066, -0.0200
def spine(t):
    return (1 - t) ** 3 * B0 + 3 * (1 - t) ** 2 * t * P1 + 3 * (1 - t) * t ** 2 * P2 + t ** 3 * pad_c
def ease(t): return t * t * (3 - 2 * t)

rings = []
def cup_ring(r, y):
    return [np.array([0, y, 0]) + a0 * x + b0 * z for x, z in circle2d(r)]
rings.append(cup_ring(CUP_R_IN, FRONT))                  # inner edge against the gauge
rings.append(cup_ring(CUP_R - 0.0012, FRONT))            # flat front face
rings.append(cup_ring(CUP_R, FRONT - 0.0012))            # rolled rim
# Body: 40 straight columns run back from the rim until they meet the pillar face, so the pod is a
# tube growing out of the pillar at the gauge's angle. It tapers towards the pillar so its footprint
# stays on the pillar face.
# Each column is ray-cast straight back onto the car's real interior surface (trim, bare pillar or
# roll-cage bar, depending on the variant) and sunk a few millimetres into it.
rim = cup_ring(CUP_R, FRONT - 0.0012)
rim_out = [unit(p - np.array([0, p[1], 0])) for p in rim]
TAPER = float(os.environ.get('DBG_TAPER', '0.30'))       # footprint is this much narrower than the cup
SINK = float(os.environ.get('DBG_SINK', '0.006'))
_cab = np.load(os.environ['DBG_CABIN'], allow_pickle=True).item()
SCALE = float(os.environ.get('DBG_SCALE', '1'))            # whole gauge + pod is built full size, then scaled
_T = np.vstack([(_cab[k][0].astype(float)[_cab[k][1]] - C) @ Rinv.T for k in os.environ['DBG_OCC'].split(',')]) / SCALE
_A = _T[:, 0]; _E1 = _T[:, 1] - _A; _E2 = _T[:, 2] - _A
def ray(o, d):
    h = np.cross(d, _E2); a = np.einsum('ij,ij->i', _E1, h); ok = np.abs(a) > 1e-12
    f = 1 / np.where(ok, a, 1); q0 = o - _A; u = f * np.einsum('ij,ij->i', q0, h)
    q = np.cross(q0, _E1); v = f * (q @ d); t = f * np.einsum('ij,ij->i', _E2, q)
    m = ok & (u >= 0) & (v >= 0) & (u + v <= 1) & (t > 1e-5)
    return float(t[m].min()) if m.any() else float('inf')
raw = np.array([ray(p - o * (CUP_R * TAPER), d0) for p, o in zip(rim, rim_out)])
fin = raw[np.isfinite(raw)]
cap_len = float(np.median(fin)) * 1.5 + 0.01             # columns that miss the surface stop here
length = [max(0.004, min(float(t), cap_len) + SINK) if np.isfinite(t) else cap_len for t in raw]
print("columns hitting surface", int(np.isfinite(raw).sum()), "/", SEG, " capped", int((raw > cap_len).sum()))
FRACS = [0.18, 0.36, 0.54, 0.70, 0.84, 0.94, 1.0]
for f in FRACS:
    ring = []
    for p, o, L in zip(rim, rim_out, length):
        w = f * f * (3 - 2 * f)
        q = p + d0 * (L * f) - o * (CUP_R * TAPER * w)
        ring.append(q)
    rings.append(ring)
verts, quads = [], []
for r in rings: verts += [tuple(p) for p in r]
for k in range(len(rings) - 1):
    for i in range(SEG):
        j = (i + 1) % SEG
        quads.append((k * SEG + i, k * SEG + j, (k + 1) * SEG + j, (k + 1) * SEG + i))
# back cap (hidden against the pillar): one centre vertex
cv = len(verts); verts.append(tuple(np.mean(np.array(rings[-1]), axis=0))); last = (len(rings) - 1) * SEG
cap = [(last + i, last + (i + 1) % SEG, cv) for i in range(SEG)]

def new_obj(name, verts, faces):
    me = bpy.data.meshes.new(name); me.from_pydata([tuple(v) for v in verts], [], faces); me.update()
    ob = bpy.data.objects.new(name, me); bpy.context.scene.collection.objects.link(ob); return ob
pod = new_obj("pod", verts, quads + cap)
ring_len = [0.0]
for k in range(1, len(rings)):
    ring_len.append(ring_len[-1] + float(np.mean(np.linalg.norm(np.array(rings[k]) - np.array(rings[k - 1]), axis=1))))
UV_SCALE = 1 / 0.026                                     # one texture tile = 26 mm
uvl = pod.data.uv_layers.new(name="UVMap")
for f, poly in enumerate(pod.data.polygons):
    li = list(poly.loop_indices)
    if f < len(quads):
        k, i = divmod(f, SEG)
        per = 2 * math.pi * CUP_R * UV_SCALE / SEG * 1.0
        uv = [(i * per, ring_len[k] * UV_SCALE), ((i + 1) * per, ring_len[k] * UV_SCALE),
              ((i + 1) * per, ring_len[k + 1] * UV_SCALE), (i * per, ring_len[k + 1] * UV_SCALE)]
    else:
        uv = [(0, 0), (0.1, 0), (0.05, 0.1)]
    for l, c in zip(li, uv): uvl.data[l].uv = c

# ---------------------------------------------------------------- gauge unit (lathe, same 40 columns)
prof = [(R_SCREEN, 0.0), (0.0238, 0.0046)]
prof += arc(0.0261, 0.0046, 0.0023, 180, 0, 4)[1:]
prof += [(0.0284, -0.0022), (0.0276, -0.0030), (0.0276, -0.0046), (0.0292, -0.0056), (0.0292, -0.0130)]
gv, gq = [], []
for (r_, y_) in prof:
    gv += [tuple(p) for p in cup_ring(r_, y_)]
for k in range(len(prof) - 1):
    for i in range(SEG):
        j = (i + 1) % SEG
        gq.append((k * SEG + i, k * SEG + j, (k + 1) * SEG + j, (k + 1) * SEG + i))
gauge = new_obj("gauge", gv, gq)
_gl = gauge.data.uv_layers.new(name="UVMap")
for _d in _gl.data: _d.uv = (0.0, 0.0)

# ---------------------------------------------------------------- normals, triangulate, export arrays
def finish(ob):
    quads_out = [tuple(p.vertices) for p in ob.data.polygons]
    Vq = np.array([v.co[:] for v in ob.data.vertices])
    bm = bmesh.new(); bm.from_mesh(ob.data)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    bmesh.ops.triangulate(bm, faces=bm.faces[:], quad_method='SHORT_EDGE')
    thr = math.radians(SHARP_DEG)
    for f in bm.faces: f.smooth = True
    for e in bm.edges:
        e.smooth = not (len(e.link_faces) == 2 and e.calc_face_angle() > thr)
    bm.to_mesh(ob.data); bm.free(); ob.data.update()
    me = ob.data
    cn = np.array([c.vector[:] for c in me.corner_normals])
    V = np.array([v.co[:] for v in me.vertices])
    uvd = me.uv_layers[0].data
    key, pos, nor, tri, uvs = {}, [], [], [], []
    for p in me.polygons:                                 # weld corners that share position + normal
        idx = []
        for li in p.loop_indices:
            vi = me.loops[li].vertex_index
            uv = tuple(uvd[li].uv)
            k = (vi,) + tuple(np.round(cn[li], 4)) + tuple(np.round(uv, 5))
            if k not in key:
                key[k] = len(pos); pos.append(V[vi]); nor.append(cn[li]); uvs.append(uv)
            idx.append(key[k])
        tri.append(idx)
    return np.array(pos), np.array(nor), np.array(tri), Vq, quads_out, np.array(uvs)

parts = {}
for name, ob, ref in (("pod", pod, None), ("gauge", gauge, np.array([0, -0.004, 0]))):
    p, n, t, Vq, q, uv = finish(ob)
    fn = np.cross(p[t[:, 1]] - p[t[:, 0]], p[t[:, 2]] - p[t[:, 0]]); fc = p[t].mean(1)
    cen = p.mean(0) if ref is None else ref
    if name == "gauge":                                   # open lathe: outward = away from the axis ring
        radial = fc.copy(); radial[:, 1] = 0
        ok = np.einsum('ij,ij->', fn, radial + np.array([0, 1, 0]) * 0.0) 
        side = t[np.abs(fc[:, 1] + 0.008) < 0.003]        # the plain cylinder wall decides
        fs = np.cross(p[side[:, 1]] - p[side[:, 0]], p[side[:, 2]] - p[side[:, 0]]); cs = p[side].mean(1); cs[:, 1] = 0
        vol = np.einsum('ij,ij->', fs, cs)
    else:
        vol = np.einsum('ij,ij->', fn, fc - cen)
    if vol < 0:
        t = t[:, ::-1].copy(); n = -n
    parts[name] = (p * SCALE, n, t, uv)
    parts[name + "_wire"] = (Vq * SCALE, q)
    print(name, "verts", len(p), "tris", len(t), "quads", sum(1 for f in q if len(f) == 4), "bbox", p.min(0).round(4), p.max(0).round(4))

print("pad_c", pad_c.round(4), "nf", nf.round(3), "um", um.round(3), "column length min/max", round(min(length), 4), round(max(length), 4))
np.save(sys.argv[1], dict(parts, pad_c=pad_c, nf=nf, um=um, tm=tm), allow_pickle=True)
