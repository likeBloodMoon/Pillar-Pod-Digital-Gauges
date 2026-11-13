"""Multi-function display: portrait screen housing with a page button, and a pod that grows from the
housing back onto the A-pillar (or roll-cage bar), every face a quad.

Model space: screen centred on the origin, facing +Y (towards the driver), Z up. Built full size and
scaled by DBG_SCALE at the end.

    DBG_C=x,y,z DBG_YAW=deg DBG_SCALE=0.8 DBG_OCC=mesh1,mesh2 DBG_CABIN=cabin.npy \
        python build_mfd_mesh.py parts_mfd_std.npy
"""
import math, os, sys
import numpy as np
import bpy, bmesh

C = np.array([float(x) for x in os.environ['DBG_C'].split(',')]); YAW = float(os.environ['DBG_YAW'])
SCALE = float(os.environ.get('DBG_SCALE', '1'))
SHARP_DEG = 38.0

# screen 52.5 x 70 mm (3:4 portrait), housing 60 x 83 mm with a 9 mm chin for the page button.
# The housing is a 12 mm deep rounded tray; behind it a narrower neck tapers into the pillar.
SX, SZ = 0.02625, 0.035                     # screen half sizes
OX0, OX1, OZ0, OZ1, OR = -0.0298, 0.0298, -0.0442, 0.0385, 0.009
# other units (e.g. the wide cluster screen) override the sizes: DBG_SCREEN_HALF=sx,sz DBG_OUTER=x0,x1,z0,z1,r
if os.environ.get('DBG_SCREEN_HALF'): SX, SZ = [float(v) for v in os.environ['DBG_SCREEN_HALF'].split(',')]
if os.environ.get('DBG_OUTER'): OX0, OX1, OZ0, OZ1, OR = [float(v) for v in os.environ['DBG_OUTER'].split(',')]
NO_BUTTON = os.environ.get('DBG_NOBUTTON') == '1'
PITCH = float(os.environ.get('DBG_PITCH', '0'))  # tilt back, degrees (the unit faces up the panel)
SCREEN_Y = -0.0015                          # screen sits 1.5 mm behind the front face
FRONT_Y, BACK_Y = 0.001, -0.012
NECK = float(os.environ.get('DBG_NECK', '-0.0085'))                              # the neck is the housing outline pulled in by this much
BUTTON = (0.0, (OZ0 + -SZ) / 2)             # page button centre (x, z) in the chin
BUTTON_R = 0.0032
K, M_LONG, M_SHORT = 8, 9, 6
if os.environ.get('DBG_SIDES'): M_LONG, M_SHORT = [int(v) for v in os.environ['DBG_SIDES'].split(',')]                # outline samples: arc steps per corner, points along sides

def rz(deg):
    a = math.radians(deg); c, s = math.cos(a), math.sin(a)
    return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]])

def outline(x0, x1, z0, z1, r, off=0.0):
    """Rounded rectangle offset outwards by off; same point count and order for every call, so rings
    line up. Order: bottom-right corner, up the right side, top, down the left, along the bottom."""
    x0 -= off; x1 += off; z0 -= off; z1 += off; r = max(1e-4, r + off)
    corners = [((x1 - r, z0 + r), -90), ((x1 - r, z1 - r), 0), ((x0 + r, z1 - r), 90), ((x0 + r, z0 + r), 180)]
    sides = [M_LONG, M_SHORT, M_LONG, M_SHORT]
    pts = []
    for ci, ((cx, cz), a0) in enumerate(corners):
        arc = [(cx + r * math.cos(math.radians(a0 + 90 * k / K)), cz + r * math.sin(math.radians(a0 + 90 * k / K))) for k in range(K + 1)]
        pts += arc
        (nx, nz), na = corners[(ci + 1) % 4]
        end = arc[-1]; nxt = (nx + r * math.cos(math.radians(na)), nz + r * math.sin(math.radians(na)))
        for m in range(1, sides[ci] + 1):
            f = m / (sides[ci] + 1); pts.append((end[0] + (nxt[0] - end[0]) * f, end[1] + (nxt[1] - end[1]) * f))
    return np.array(pts)

N = len(outline(OX0, OX1, OZ0, OZ1, OR))
def ring(xz, y): return [np.array([x, y, z]) for x, z in xz]

bpy.ops.wm.read_factory_settings(use_empty=True)
def new_obj(name, verts, faces):
    me = bpy.data.meshes.new(name); me.from_pydata([tuple(v) for v in verts], [], faces); me.update()
    ob = bpy.data.objects.new(name, me); bpy.context.scene.collection.objects.link(ob); return ob
def strip(rings, closed_cap=None):
    verts, quads = [], []
    for r in rings: verts += [tuple(p) for p in r]
    for k in range(len(rings) - 1):
        for i in range(N):
            j = (i + 1) % N
            quads.append((k * N + i, k * N + j, (k + 1) * N + j, (k + 1) * N + i))
    tris = []
    if closed_cap is not None:
        cv = len(verts); verts.append(tuple(closed_cap)); last = (len(rings) - 1) * N
        tris = [(last + i, last + (i + 1) % N, cv) for i in range(N)]
    return verts, quads + tris

# ---------------------------------------------------------------- front frame (bezel material)
scr = lambda off: outline(-SX, SX, -SZ, SZ, 0.002, off)
out = lambda off: outline(OX0, OX1, OZ0, OZ1, OR, off)
# the lip starts 0.6 mm inside the screen edge and in front of it, so there is never a gap to see through
frame_rings = [ring(scr(-0.0006), SCREEN_Y + 0.0003), ring(scr(-0.0006), FRONT_Y), ring(scr(0.0016), FRONT_Y + 0.0004),
               ring(out(-0.0045), FRONT_Y + 0.0002), ring(out(-0.0018), FRONT_Y - 0.0004), ring(out(-0.0005), FRONT_Y - 0.0016),
               ring(out(0.0), FRONT_Y - 0.0032)]
fv, ff = strip(frame_rings)
frame = new_obj("frame", fv, ff)
# backing plate just behind the screen: closes the housing so nothing behind it can show through
pv = [tuple(p) for p in ring(out(-0.0005), SCREEN_Y - 0.0006)] + [((OX0 + OX1) / 2, SCREEN_Y - 0.0006, (OZ0 + OZ1) / 2)]
plate = new_obj("plate", pv, [(i, (i + 1) % N, N) for i in range(N)])
# ---------------------------------------------------------------- shell (pod material): sides + pod onto the pillar
def rx(deg):
    a = math.radians(deg); c, s_ = math.cos(a), math.sin(a)
    return np.array([[1, 0, 0], [0, c, -s_], [0, s_, c]])
ROT = rz(YAW) @ rx(PITCH)                  # model -> car
Rinv = ROT.T
_cab = np.load(os.environ['DBG_CABIN'], allow_pickle=True).item()
_T = np.vstack([(_cab[k][0].astype(float)[_cab[k][1]] - C) @ Rinv.T for k in os.environ['DBG_OCC'].split(',')]) / SCALE
_A = _T[:, 0]; _E1 = _T[:, 1] - _A; _E2 = _T[:, 2] - _A
def ray(o, d):
    h = np.cross(d, _E2); a = np.einsum('ij,ij->i', _E1, h); ok = np.abs(a) > 1e-12
    f = 1 / np.where(ok, a, 1); q0 = o - _A; u = f * np.einsum('ij,ij->i', q0, h)
    q = np.cross(q0, _E1); v = f * (q @ d); t = f * np.einsum('ij,ij->i', _E2, q)
    m = ok & (u >= 0) & (v >= 0) & (u + v <= 1) & (t > 1e-5)
    return float(t[m].min()) if m.any() else float('inf')
# the neck is a rounded superellipse (not a box) inside the housing outline, so the pod reads as one
# smooth moulding growing out of the pillar
def neck(pull, y, n=2.4):
    o = out(0.0); cx_, cz_ = (OX0 + OX1) / 2, (OZ0 + OZ1) / 2
    a = (OX1 - OX0) / 2 + pull; b = (OZ1 - OZ0) / 2 + pull
    pts = []
    for x, z in o:
        th = math.atan2(z - cz_, x - cx_)
        r = (abs(math.cos(th) / a) ** n + abs(math.sin(th) / b) ** n) ** (-1 / n)
        pts.append(np.array([cx_ + r * math.cos(th), y, cz_ + r * math.sin(th)]))
    return pts
back = None                                # set below from the neck
d0 = np.array([0.0, -1.0, 0.0])
TAPER = float(os.environ.get('DBG_TAPER', '0.25')); SINK = float(os.environ.get('DBG_SINK', '0.006'))
centre = np.array([(OX0 + OX1) / 2, 0.0, (OZ0 + OZ1) / 2])
back = neck(NECK, BACK_Y - 0.002)
inward = [(np.array([centre[0], p[1], centre[2]]) - p) for p in back]
TAPER = float(os.environ.get('DBG_TAPER', '0.35'))
raw = np.array([ray(p + w * TAPER, d0) for p, w in zip(back, inward)])
fin = raw[np.isfinite(raw)]
cap_len = float(np.median(fin)) * 1.5 + 0.01 if len(fin) else 0.05
length = [max(0.003, min(float(t), cap_len) + SINK) if np.isfinite(t) else cap_len for t in raw]
print("columns hitting surface", int(np.isfinite(raw).sum()), "/", N)
#   rounded back edge of the tray, then the neck
tray = [ring(out(0.0), FRONT_Y - 0.0032), ring(out(0.0), BACK_Y + 0.004), ring(out(-0.0012), BACK_Y + 0.0012),
        ring(out(-0.0035), BACK_Y), neck(NECK + 0.0015, BACK_Y - 0.0006), neck(NECK, BACK_Y - 0.002)]
shell_rings = tray[:]
for f in (0.12, 0.28, 0.46, 0.64, 0.8, 0.92, 1.0):
    w = f * f * (3 - 2 * f)
    shell_rings.append([p + d0 * (L * f) + iw * (TAPER * w) for p, iw, L in zip(back, inward, length)])
sv, sf = strip(shell_rings, closed_cap=np.mean(np.array(shell_rings[-1]), axis=0))
shell = new_obj("shell", sv, sf)
# ---------------------------------------------------------------- page button: short round cap in the chin
bx, bz = BUTTON; seg = 16
brings = []
for r_, y_ in ((BUTTON_R + 0.0006, FRONT_Y), (BUTTON_R, FRONT_Y + 0.0012), (BUTTON_R - 0.0006, FRONT_Y + 0.0018)):
    brings.append([np.array([bx + r_ * math.cos(2 * math.pi * i / seg), y_, bz + r_ * math.sin(2 * math.pi * i / seg)]) for i in range(seg)])
bverts, bfaces = [], []
for r in brings: bverts += [tuple(p) for p in r]
for k in range(len(brings) - 1):
    for i in range(seg):
        j = (i + 1) % seg; bfaces.append((k * seg + i, k * seg + j, (k + 1) * seg + j, (k + 1) * seg + i))
cv = len(bverts); bverts.append((bx, FRONT_Y + 0.0018, bz)); last = (len(brings) - 1) * seg
bfaces += [(last + i, last + (i + 1) % seg, cv) for i in range(seg)]
button = new_obj("button", bverts, bfaces)

def finish(ob):
    bm = bmesh.new(); bm.from_mesh(ob.data)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    bmesh.ops.triangulate(bm, faces=bm.faces[:], quad_method='SHORT_EDGE')
    thr = math.radians(SHARP_DEG)
    for f in bm.faces: f.smooth = True
    for e in bm.edges: e.smooth = not (len(e.link_faces) == 2 and e.calc_face_angle() > thr)
    bm.to_mesh(ob.data); bm.free(); ob.data.update()
    me = ob.data
    cn = np.array([c.vector[:] for c in me.corner_normals]); V = np.array([v.co[:] for v in me.vertices])
    key, pos, nor, tri = {}, [], [], []
    for p in me.polygons:
        idx = []
        for li in p.loop_indices:
            vi = me.loops[li].vertex_index
            k = (vi,) + tuple(np.round(cn[li], 4))
            if k not in key: key[k] = len(pos); pos.append(V[vi]); nor.append(cn[li])
            idx.append(key[k])
        tri.append(idx)
    p, n, t = np.array(pos), np.array(nor), np.array(tri)
    # outward faces: the frame and button face the driver (+Y), the shell faces away from its axis
    fn = np.cross(p[t[:, 1]] - p[t[:, 0]], p[t[:, 2]] - p[t[:, 0]]); fc = p[t].mean(1)
    if ob.name == "shell":
        ref = fc - np.array([centre[0], fc[:, 1].mean(), centre[2]]); ref[:, 1] = 0
        vol = np.einsum('ij,ij->', fn, ref)
    else:
        vol = fn[:, 1].sum()
    if vol < 0: t = t[:, ::-1].copy(); n = -n
    uv = np.c_[p[:, 0] / 0.026, (p[:, 1] + p[:, 2]) / 0.026]          # plastic texture tiles at 26 mm
    return p * SCALE, n, t, uv

parts = {name: finish(ob) for name, ob in (("frame", frame), ("plate", plate), ("shell", shell), ("button", button))}
fp, fn_, ft, fu = parts["frame"]; pp, pn, pt_, pu = parts.pop("plate")      # the plate shares the frame's material
parts["frame"] = (np.vstack([fp, pp]), np.vstack([fn_, pn]), np.vstack([ft, pt_ + len(fp)]), np.vstack([fu, pu]))
# screen: one quad, u runs from the driver's left (+x) to right, v = 1 at the top (like the gauges)
sp = np.array([[SX, SCREEN_Y, -SZ], [-SX, SCREEN_Y, -SZ], [-SX, SCREEN_Y, SZ], [SX, SCREEN_Y, SZ]])
suv = np.array([[0, 0], [1, 0], [1, 1], [0, 1]], float)
st = np.array([[0, 1, 2], [0, 2, 3]])
fn = np.cross(sp[st[0, 1]] - sp[st[0, 0]], sp[st[0, 2]] - sp[st[0, 0]])
if fn[1] < 0: st = st[:, ::-1].copy()
parts["screen"] = (sp * SCALE, np.tile([0, 1.0, 0], (4, 1)), st, suv)
parts["button_pos"] = np.array([bx, FRONT_Y + 0.0018, bz]) * SCALE
if NO_BUTTON: parts.pop("button")
parts["rot"] = ROT
for k, v in parts.items():
    if k != "button_pos": print(k, "verts", len(v[0]), "tris", len(v[2]))
print("pod length min/max", round(min(length) * SCALE, 4), round(max(length) * SCALE, 4))
np.save(sys.argv[1], parts, allow_pickle=True)
