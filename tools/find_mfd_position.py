"""Find where the multi-function display sits on a car's A-pillar: aim along the pillar from the
driver's eye, then move the housing out along the view line until every sample point on it is
visible from the driver's and the centre eye (so it neither sinks into the trim nor hides behind it).

    python find_mfd_position.py covet_cabin.npy <scale> [std|stripped|cage]
Prints the screen centre and yaw for each searched aim height.
"""
import numpy as np, sys, math
cab = np.load(sys.argv[1], allow_pickle=True).item()
S = float(sys.argv[2]); ONLY = sys.argv[3] if len(sys.argv) > 3 else None
class Occ:
    def __init__(s, names):
        T = []; own = []
        for k in names:
            p, t = cab[k]; T.append(p.astype(float)[t]); own += [k] * len(t)
        T = np.vstack(T); s.A = T[:, 0]; s.E1 = T[:, 1] - s.A; s.E2 = T[:, 2] - s.A; s.own = np.array(own)
    def hit(s, o, d, tmax=1e9):
        h = np.cross(d, s.E2); a = np.einsum('ij,ij->i', s.E1, h); ok = np.abs(a) > 1e-12
        f = 1 / np.where(ok, a, 1); q0 = o - s.A; u = f * np.einsum('ij,ij->i', q0, h)
        q = np.cross(q0, s.E1); v = f * (q @ d); t = f * np.einsum('ij,ij->i', s.E2, q)
        m = ok & (u >= 0) & (v >= 0) & (u + v <= 1) & (t > 1e-5) & (t < tmax)
        if not m.any(): return np.inf, None
        i = np.where(m)[0][np.argmin(t[m])]; return t[i], s.own[i]
# Covet driver's eye and pillar aim point (same as find_positions.py)
eye = np.array([0.333, 0.20, 1.08]); eye2 = np.array([0.0, 0.15, 1.10])
CA = np.array([0.579, -0.3336, 1.0757])
f = CA - eye; f /= np.linalg.norm(f); left = -np.cross(f, [0, 0, 1]); left /= np.linalg.norm(left); up = np.cross(left, -f)
# housing outline in model space (x across, z up, y towards the driver), screen centre at the origin
X0, X1, Z0, Z1, YF, YB = -0.028, 0.028, -0.042, 0.036, 0.001, -0.014
def samples(C, yaw):
    a = math.radians(yaw); ex = np.array([math.cos(a), math.sin(a), 0]); ey = np.array([-math.sin(a), math.cos(a), 0]); ez = np.array([0, 0, 1.0])
    pts = []
    for y in (YF, YB):
        for u in np.linspace(0, 1, 9):
            for x, z in ((X0 + (X1 - X0) * u, Z0), (X0 + (X1 - X0) * u, Z1), (X0, Z0 + (Z1 - Z0) * u), (X1, Z0 + (Z1 - Z0) * u)):
                pts.append(C + (ex * x + ey * y + ez * z) * S)
    return pts
def clear(occ, C, yaw):
    for p in samples(C, yaw):
        for e in (eye, eye2):
            d = p - e; L = np.linalg.norm(d)
            if occ.hit(e, d / L, L - 1e-4)[0] < np.inf: return False
    return True
V = {'std': ['covet_intcarpet', 'covet_body', 'covet_door_L', 'covet_doorpanel_L', 'covet_dash'],
     'stripped': ['covet_stripped_int_F', 'covet_body', 'covet_door_L', 'covet_door_grp_doorpanel_L', 'covet_doorpanel_L', 'covet_grp_dash_lhd', 'covet_dash'],
     'cage': ['covet_stripped_int_F', 'covet_intcarpet', 'covet_rollcage_F', 'covet_body', 'covet_door_L', 'covet_door_grp_doorpanel_L', 'covet_doorpanel_L', 'covet_grp_dash_lhd', 'covet_dash']}
TARGET = {'std': 'covet_intcarpet', 'stripped': 'covet_stripped_int_F', 'cage': 'covet_rollcage_F'}
for name, names in V.items():
    if ONLY and name != ONLY: continue
    occ = Occ(names); best = None
    for du in np.arange(0.0, 0.10, 0.01):
        aim = CA + up * du; d = aim - eye; d /= np.linalg.norm(d); t, o = occ.hit(eye, d)
        if o != TARGET[name]: continue
        Sp = eye + d * t
        for off in np.arange(0.01, 0.20, 0.004):
            C = Sp - d * off; e = eye - C; yaw = math.degrees(math.atan2(-e[0], e[1]))
            if clear(occ, C, yaw):
                print('%s du %.2f  C %.4f,%.4f,%.4f yaw %.1f  off %.3f  dist %.2f' % (name, du, *C, yaw, off, np.linalg.norm(C - eye)))
                if best is None or off < best[2]: best = (C, yaw, off, du)
                break
    if best: print('BEST', name, '%.4f,%.4f,%.4f' % tuple(best[0]), round(best[1], 1), 'off', round(best[2], 3), 'du', round(best[3], 2))
