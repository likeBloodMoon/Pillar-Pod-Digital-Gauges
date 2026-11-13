"""Digital cluster screens for the Covet, in car coordinates (the parts place them without pos/rot).

- Standard dashboards: one flat screen with the exact outline of the stock gauge face
  (covet_gauges), 0.6 mm in front of where that face was, UV-mapped to the 1024 x 272 page.
- Race dashboards: the wide screen unit from build_mfd_mesh.py (race_unit.npy, model space plus its
  rotation) placed on the carbon instrument panel.
Right-hand drive is mirrored; screen UVs are recomputed so the picture is never mirrored.

    python build_cluster_mesh.py covet_cluster.npy race_unit.npy out.npy
Needs the Covet's covet_gauges mesh in covet_cluster.npy (extract_cabin.py).
"""
import sys
from collections import Counter
import numpy as np

cab = np.load(sys.argv[1], allow_pickle=True).item()
race = np.load(sys.argv[2], allow_pickle=True).item()
RACE_C = np.array([0.3360, -0.5465, 0.8377])          # screen centre of the race unit (on the carbon panel)
U0, U1, V0, V1 = -0.2375, 0.1225, -0.0362, 0.0595       # face extents in the page's coordinates (see cluster.html)

# ---- standard dashboard: outline of the stock gauge face ----
p, t = cab['covet_gauges']; p = p.astype(float)
cen = p.mean(0); _, _, vt = np.linalg.svd(p - cen); n = vt[2]
if n[1] > 0: n = -n                                     # n points away from the driver
U = np.array([-1.0, 0, 0]); U -= n * (U @ n); U /= np.linalg.norm(U)   # driver's right
V = np.cross(n, U); V = V if V[2] > 0 else -V                           # up
edges = Counter()
for tr in t:
    for a, b in ((tr[0], tr[1]), (tr[1], tr[2]), (tr[2], tr[0])): edges[tuple(sorted((a, b)))] += 1
adj = {}
for (a, b), k in edges.items():
    if k == 1: adj.setdefault(a, []).append(b); adj.setdefault(b, []).append(a)
# the outer loop is the boundary loop with the largest extent
loops, seen = [], set()
for s in adj:
    if s in seen: continue
    loop, prev, cur = [s], None, s
    seen.add(s)
    while True:
        nx = [x for x in adj[cur] if x != prev]
        if not nx: break
        prev, cur = cur, nx[0]
        if cur == s: break
        loop.append(cur); seen.add(cur)
    loops.append(loop)
outer = max(loops, key=lambda l: np.ptp((p[l] - cen) @ U))
q = np.c_[(p[outer] - cen) @ U, (p[outer] - cen) @ V]

def face(mirror):
    qq = q.copy()
    if mirror: qq[:, 0] = -qq[:, 0]; qq = qq[::-1]       # mirrored outline, still read left to right
    u0, u1 = (U0, U1) if not mirror else (-U1, -U0)
    centre2 = qq.mean(0)
    pts2 = np.vstack([qq, centre2])
    uv = np.c_[(pts2[:, 0] - u0) / (u1 - u0), (pts2[:, 1] - V0) / (V1 - V0)]
    c3 = cen.copy(); n3 = n.copy(); U3 = U.copy(); V3 = V.copy()
    if mirror: c3[0] = -c3[0]; n3[0] = -n3[0]; V3[0] = -V3[0]   # U stays the driver's right (-x)
    P = c3 + np.outer(pts2[:, 0], U3) + np.outer(pts2[:, 1], V3) - n3 * 0.0006
    k = len(qq)
    T = np.array([[i, (i + 1) % k, k] for i in range(k)])
    fn = np.cross(P[T[0, 1]] - P[T[0, 0]], P[T[0, 2]] - P[T[0, 0]])
    if fn @ (-n3) < 0: T = T[:, ::-1].copy()                    # face the driver
    N = np.tile(-n3, (len(P), 1))
    return P, N, T, uv

# ---- race dashboard: the screen unit, rotated and placed ----
def unit(mirror):
    R = race['rot']; out = {}
    for key in ('shell', 'frame', 'screen'):
        P, N, T, uv = race[key]
        P = P @ R.T + RACE_C; N = N @ R.T
        if mirror:
            P = P.copy(); N = N.copy(); P[:, 0] *= -1; N[:, 0] *= -1; T = T[:, ::-1].copy()
            if key == 'screen': uv = uv.copy(); uv[:, 0] = 1 - uv[:, 0]   # keep the picture the right way round
        out[key] = (P, N, T, uv)
    return out

res = {'std_lhd': face(False), 'std_rhd': face(True), 'race_lhd': unit(False), 'race_rhd': unit(True),
       'face': dict(cen=cen, n=n, U=U, V=V), 'race_c': RACE_C, 'race_rot': race['rot']}
np.save(sys.argv[3], res, allow_pickle=True)
print('standard face outline points', len(q), ' u', q[:, 0].min().round(4), q[:, 0].max().round(4), ' v', q[:, 1].min().round(4), q[:, 1].max().round(4))
