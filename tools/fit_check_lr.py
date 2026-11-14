"""Fit-check renders: every mounting seen from the driver's camera, left-hand drive next to right-hand
drive, using the game's real LHD and RHD interior meshes (not a mirror of one side).

    python fit_check_lr.py covet covet_cabin_lr.npy <parts dir> <out dir> [eye x,y,z]
    python fit_check_lr.py bx    bx_cabin_lr.npy    <parts dir> <out dir> [eye x,y,z]

<parts dir> holds the pod/display meshes written by build_pod_mesh.py / build_mfd_mesh.py
(parts_*.npy, mfd_*.npy). The cabin .npy comes from extract_cabin.py and is BeamNG's data: keep it
out of the repository. Each image: driver's view (camera field of view 55 deg, the game's default)
and a close-up of the mounting, LHD on top and RHD below (the RHD row is flipped left-right so the
two rows line up).
"""
import math, os, sys
import numpy as np
from PIL import Image, ImageDraw

car, cabin_file, parts_dir, out_dir = sys.argv[1:5]
os.makedirs(out_dir, exist_ok=True)
cab = np.load(cabin_file, allow_pickle=True).item()
EYES = {'covet': (0.340, 0.176, 1.079), 'bx': (0.349, 0.266, 1.049)}   # default driver cameras, measured in game
eye_l = np.array([float(v) for v in sys.argv[5].split(',')] if len(sys.argv) > 5 else EYES[car])

GREY = (0.62, 0.62, 0.64)
COL = {'body': (0.80, 0.80, 0.82), 'dash': (0.30, 0.30, 0.32), 'door': (0.42, 0.42, 0.46), 'sunvisor': (0.70, 0.66, 0.58),
       'rollcage': (0.92, 0.92, 0.94), 'stripped': (0.72, 0.72, 0.75), 'intcarpet': (0.45, 0.30, 0.28), 'mirror': (0.25, 0.25, 0.27),
       'intpanels': (0.50, 0.48, 0.46)}
def colour(name):
    for k, c in COL.items():
        if k in name: return c
    return GREY

RHD_NAME = {'covet_door_L': 'covet_door_R', 'covet_doorpanel_L': 'covet_doorpanel_R', 'covet_door_grp_doorpanel_L': 'covet_door_grp_doorpanel_R',
            'covet_sunvisor_L': 'covet_sunvisor_R', 'covet_dash': 'covet_dash_rhd', 'covet_dash_rally': 'covet_dash_rhd_rally',
            'covet_doorglass_L_int': 'covet_doorglass_R_int', 'covet_grp_dash_lhd': 'covet_grp_dash_rhd',
            'bx_door_L': 'bx_door_R', 'bx_doorpanel_L': 'bx_doorpanel_R', 'bx_sunvisor_L': 'bx_sunvisor_R', 'bx_dash': 'bx_dash_rhd',
            'bx_dash_rally': 'bx_dash_rhd_rally', 'bx_mirror_int_lhd': 'bx_mirror_int_rhd', 'bx_grp_dash': 'bx_grp_dash_rhd', 'bx_steer': 'bx_steer_rhd'}
CB = ['covet_body', 'covet_door_L', 'covet_doorpanel_L', 'covet_door_grp_doorpanel_L', 'covet_sunvisor_L', 'covet_grp_dash_lhd']
BB = ['bx_body_hatch', 'bx_door_L', 'bx_doorpanel_L', 'bx_sunvisor_L', 'bx_sunvisor_mounts', 'bx_mirror_int_lhd', 'bx_intpanels_hatch', 'bx_grp_dash']
# mounting -> interior meshes (LHD names), gauges [(centre, yaw, parts file, scale)], display (centre, yaw, mfd file) or None
MOUNTS = {
    'covet': {
        'std': (CB + ['covet_dash', 'covet_intcarpet'], [((0.5749, -0.3246, 1.0758), 24.8, 'std', 0.8), ((0.5397, -0.2291, 1.1372), 25.7, 'std_2', 0.8)], ((0.5474, -0.2651, 1.1024), 24.8, 'std')),
        'stripped': (CB + ['covet_dash_rally', 'covet_stripped_int_F'], [((0.5823, -0.3407, 1.0756), 24.8, 'stripped', 0.8), ((0.5473, -0.2448, 1.1393), 25.7, 'stripped_2', 0.8)], ((0.5523, -0.2756, 1.1029), 24.8, 'stripped')),
        'cage': (CB + ['covet_dash_rally', 'covet_stripped_int_F', 'covet_rollcage_F'], [((0.5175, -0.2189, 1.0961), 23.8, 'cage', 0.65), ((0.4972, -0.1483, 1.1426), 25.2, 'cage_2', 0.65)], ((0.5165, -0.1981, 1.0992), 24.8, 'cage')),
    },
    'bx': {
        'pillar': (BB + ['bx_dash', 'bx_intcarpet_hatch', 'bx_steer'], [((0.6081, -0.2417, 1.0150), 27.0, 'bx_std', 0.8), ((0.5753, -0.1308, 1.0769), 29.7, 'bx_std_2', 0.8)], None),
        'cage': (BB + ['bx_dash_rally', 'bx_rollcage', 'bx_steer'], [((0.5245, -0.1621, 1.0259), 22.3, 'bx_cage', 0.65), ((0.4943, -0.0712, 1.0781), 23.3, 'bx_cage_2', 0.65)], None),
    }}
if len(sys.argv) > 6:          # positions to try instead of the ones above: mounting=x,y,z,yaw;x,y,z,yaw
    for spec in sys.argv[6:]:
        k, v = spec.split('=')
        g = MOUNTS[car][k][1]
        MOUNTS[car][k] = (MOUNTS[car][k][0], [(tuple(map(float, p.split(',')[:3])), float(p.split(',')[3]), g[i][2], g[i][3]) for i, p in enumerate(v.split(';'))], MOUNTS[car][k][2])

def rz(deg):
    a = math.radians(deg); return np.array([[math.cos(a), -math.sin(a), 0], [math.sin(a), math.cos(a), 0], [0, 0, 1]])

def render(meshes, eye, target, fov, size=(640, 400)):
    eye = np.asarray(eye, float); f = np.asarray(target, float) - eye; f /= np.linalg.norm(f)
    r = np.cross(f, [0, 0, 1]); r /= np.linalg.norm(r); u = np.cross(r, f)
    W, H = size; fl = (H / 2) / math.tan(math.radians(fov) / 2)   # vertical field of view, like the game's camera
    img = np.zeros((H, W, 3)); img[:] = (0.62, 0.74, 0.88)
    zb = np.full((H, W), 1e9)
    L = np.array([0.3, 0.4, 0.85]); L /= np.linalg.norm(L)
    for P, T, c in meshes:
        Q = P - eye; z = Q @ f
        px = W / 2 + fl * (Q @ r) / np.maximum(z, 1e-6); py = H / 2 - fl * (Q @ u) / np.maximum(z, 1e-6)
        fn = np.cross(P[T[:, 1]] - P[T[:, 0]], P[T[:, 2]] - P[T[:, 0]]); fn /= np.linalg.norm(fn, axis=1)[:, None] + 1e-12
        shade = np.abs(fn @ L) * 0.55 + 0.45
        for ti, t in enumerate(T):
            if not (z[t] > 0.03).all(): continue
            X, Y, Z = px[t], py[t], z[t]
            x0, x1 = int(max(0, np.floor(X.min()))), int(min(W - 1, np.ceil(X.max())))
            y0, y1 = int(max(0, np.floor(Y.min()))), int(min(H - 1, np.ceil(Y.max())))
            if x1 < x0 or y1 < y0: continue
            den = (Y[1] - Y[2]) * (X[0] - X[2]) + (X[2] - X[1]) * (Y[0] - Y[2])
            if abs(den) < 1e-9: continue
            gx, gy = np.meshgrid(np.arange(x0, x1 + 1) + .5, np.arange(y0, y1 + 1) + .5)
            w0 = ((Y[1] - Y[2]) * (gx - X[2]) + (X[2] - X[1]) * (gy - Y[2])) / den
            w1 = ((Y[2] - Y[0]) * (gx - X[2]) + (X[0] - X[2]) * (gy - Y[2])) / den
            w2 = 1 - w0 - w1
            m = (w0 >= 0) & (w1 >= 0) & (w2 >= 0)
            zz = 1 / (w0 / Z[0] + w1 / Z[1] + w2 / Z[2] + 1e-12)
            sub = zb[y0:y1 + 1, x0:x1 + 1]; m &= zz < sub
            sub[m] = zz[m]; img[y0:y1 + 1, x0:x1 + 1][m] = np.array(c) * shade[ti]
    return Image.fromarray((np.clip(img, 0, 1) * 255).astype(np.uint8))

def scene(key, rhd):
    names, gauges, mfd = MOUNTS[car][key]
    sx = -1 if rhd else 1
    meshes = []
    for n in names:
        nn = RHD_NAME.get(n, n) if rhd else n
        p, t = cab[nn]; meshes.append((p.astype(float), t.astype(int), colour(nn)))
    centres = []
    for C, yaw, pf, sc in gauges:
        parts = np.load(os.path.join(parts_dir, 'parts_%s.npy' % pf), allow_pickle=True).item()
        R = rz(yaw); C = np.asarray(C)
        for k, c in (('pod', (0.10, 0.10, 0.11)), ('gauge', (0.22, 0.22, 0.24))):
            p, n, t, _ = parts[k]; q = p.astype(float) @ R.T + C
            if rhd: q = q * [-1, 1, 1]; t = t[:, ::-1]
            meshes.append((q, t.astype(int), c))
        a = np.linspace(0, 2 * np.pi, 41)[:-1]; rr = 0.0235 * sc       # the lit face: red ring so it stands out
        face = np.vstack([[0, 0.002, 0], np.c_[rr * np.cos(a), 0 * a + 0.002, rr * np.sin(a)]]) @ R.T + C
        if rhd: face = face * [-1, 1, 1]
        meshes.append((face, np.array([[0, 1 + i, 1 + (i + 1) % 40] for i in range(40)]), (0.95, 0.20, 0.12)))
        centres.append(C * [sx, 1, 1])
    if mfd and key != 'none':
        pass
    return meshes, np.mean(centres, axis=0)

def scene_mfd(key, rhd):
    names, _, (C, yaw, pf) = MOUNTS[car][key]
    meshes = []
    for n in names:
        nn = RHD_NAME.get(n, n) if rhd else n
        p, t = cab[nn]; meshes.append((p.astype(float), t.astype(int), colour(nn)))
    M = np.load(os.path.join(parts_dir, 'mfd_%s.npy' % pf), allow_pickle=True).item()
    R = rz(yaw); C = np.asarray(C)
    for k, c in (('shell', (0.10, 0.10, 0.11)), ('frame', (0.12, 0.12, 0.13)), ('button', (0.7, 0.7, 0.7)), ('screen', (0.15, 0.45, 0.95))):
        p, n, t, _ = M[k]; q = p.astype(float) @ R.T + C
        if rhd: q = q * [-1, 1, 1]; t = t[:, ::-1]
        meshes.append((q, t.astype(int), c))
    return meshes, C * [-1 if rhd else 1, 1, 1]

def row(meshes, centre, rhd):
    eye = eye_l * [-1 if rhd else 1, 1, 1]
    ahead = eye + np.array([0.0, -1.0, -0.08])          # the default driver camera looks straight ahead
    a = render(meshes, eye, ahead, 55)
    b = render(meshes, eye, centre, 22)
    if rhd: a, b = a.transpose(Image.FLIP_LEFT_RIGHT), b.transpose(Image.FLIP_LEFT_RIGHT)
    out = Image.new('RGB', (1280, 400)); out.paste(a, (0, 0)); out.paste(b, (640, 0)); return out

def save(name, build):
    img = Image.new('RGB', (1280, 830), (255, 255, 255)); d = ImageDraw.Draw(img)
    for i, rhd in enumerate((False, True)):
        m, c = build(rhd)
        img.paste(row(m, c, rhd), (0, 30 + i * 400))
    d.text((8, 8), '%s - %s    top: left-hand drive (LHD meshes)   bottom: right-hand drive (RHD meshes, flipped to line up)' % (car, name), fill=(0, 0, 0))
    tag = os.environ.get('FIT_TAG', '')
    if tag: d.text((1100, 8), tag.upper(), fill=(200, 0, 0))
    path = os.path.join(out_dir, '%s_%s%s.png' % (car, name, ('_' + tag) if tag else '')); img.save(path); print(path)

for key in MOUNTS[car]:
    save(key, lambda rhd, k=key: scene(k, rhd))
    if MOUNTS[car][key][2]:
        save(key + '_display', lambda rhd, k=key: scene_mfd(k, rhd))
