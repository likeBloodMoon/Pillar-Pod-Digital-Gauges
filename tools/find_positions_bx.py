"""200BX version of find_positions.py: driver eye, pillar aim point and occluder meshes for the Ibishu 200BX.
    python find_positions_bx.py bx_cabin.npy <scale 0.8|0.65> [std|cage] [lower deg] [upper deg]

The eye is the game's default driver camera, measured in game (1.2.1). The two gauges are placed
as high up the pillar as they can go while their bezels look no bigger from the driver's seat than
the Covet's (lower about 2.85 deg, upper about 3.45 deg radius), so a 52 mm gauge looks the same
size in both cars. The steering wheel counts as an occluder.
"""
import numpy as np, sys, math
cab=np.load(sys.argv[1],allow_pickle=True).item()
ONLY=sys.argv[3] if len(sys.argv)>3 else None
class Occ:
    def __init__(s,names):
        T=[];own=[]
        for k in names:
            p,t=cab[k]; T.append(p.astype(float)[t]); own+=[k]*len(t)
        T=np.vstack(T); s.A=T[:,0]; s.E1=T[:,1]-s.A; s.E2=T[:,2]-s.A; s.own=np.array(own)
    def hit(s,o,d,tmax=1e9):
        h=np.cross(d,s.E2); a=np.einsum('ij,ij->i',s.E1,h); ok=np.abs(a)>1e-12
        f=1/np.where(ok,a,1); q0=o-s.A; u=f*np.einsum('ij,ij->i',q0,h)
        q=np.cross(q0,s.E1); v=f*(q@d); t=f*np.einsum('ij,ij->i',s.E2,q)
        m=ok&(u>=0)&(v>=0)&(u+v<=1)&(t>1e-5)&(t<tmax)
        if not m.any(): return np.inf,None
        i=np.where(m)[0][np.argmin(t[m])]; return t[i],s.own[i]
eye=np.array([0.349,0.266,1.049]); eye2=np.array([0.0,0.216,1.069])   # driver camera (measured), and a head leaned to the centre
CA=np.array([0.6152,-0.2008,1.0668])
f=CA-eye; f/=np.linalg.norm(f); left=-np.cross(f,[0,0,1]); left/=np.linalg.norm(left); up=np.cross(left,-f)
S=float(sys.argv[2])
def clear(occ,C,yaw,R=0.036*S):
    a=math.radians(yaw); ax=np.array([-math.sin(a),math.cos(a),0]); ex=np.array([math.cos(a),math.sin(a),0]); ez=np.array([0,0,1.])
    for depth in (0.006*S,-0.016*S):
        for rr in (R,R*0.6):
            for k in range(32):
                th=2*math.pi*k/32; p=C+ax*depth+ex*rr*math.cos(th)+ez*rr*math.sin(th)
                for e in (eye,eye2):
                    d=p-e; L=np.linalg.norm(d)
                    if occ.hit(e,d/L,L-1e-4)[0]<np.inf: return False
    return True
COMMON=['bx_intcarpet_hatch','bx_body_hatch','bx_door_L','bx_doorpanel_L','bx_sunvisor_L','bx_sunvisor_mounts','bx_dash','bx_grp_dash','bx_dash_rally','bx_rollcage_derby','bx_windshield_bar','bx_mirror_int_lhd','bx_steer','bx_grp_column']
V={'std':COMMON,'cage':COMMON+['bx_rollcage']}
TARGET={'std':'bx_intcarpet_hatch','cage':'bx_rollcage'}
SL=np.array([0.40,-0.45,0.95])
def ang(a,b): return math.degrees(math.acos(np.dot(a,b)/np.linalg.norm(a)/np.linalg.norm(b)))
def place(occ,name,du):
    span=[]
    for dl in np.arange(0.09,-0.09,-0.005):
        aim=CA+left*dl+up*du; d=aim-eye; d/=np.linalg.norm(d); t,o=occ.hit(eye,d)
        if o==TARGET[name]: span.append((dl,d,t))
    if not span: return None
    mid=span[len(span)//2]
    for dl,d,t in sorted(span,key=lambda x:abs(x[0]-mid[0])):
        Sp=eye+d*t
        for off in np.arange(0.015,0.16,0.005):
            C=Sp-d*off; e=eye-C; yaw=math.degrees(math.atan2(-e[0],e[1]))
            if clear(occ,C,yaw): return C,yaw,off
    return None
T1=float(sys.argv[4]) if len(sys.argv)>4 else 2.85    # bezel angular radius limits, deg
T2=float(sys.argv[5]) if len(sys.argv)>5 else 3.45
def rad(C): return math.degrees(0.034*S/np.linalg.norm(C-eye))
for name,names in V.items():
    if ONLY and name!=ONLY: continue
    occ=Occ(names); done=False
    # walk the lower gauge down the pillar until both gauges are no bigger than the limits
    for du1 in np.arange(0.06,-0.30,-0.005):
        r=place(occ,name,du1)
        if not r: continue
        C1,y1,o1=r; r1=rad(C1)
        if r1>T1: continue
        for du in np.arange(0.05,0.16,0.005):
            r=place(occ,name,du1+du)
            if not r: continue
            C2,y2,o2=r; r2=rad(C2); gap=ang(C2-eye,C1-eye)-r1-r2
            if gap>=1.2 and np.linalg.norm(C2-C1)>=0.068*S+0.01: break
        else: continue
        if r2>T2: continue
        print('%s_1 %.4f,%.4f,%.4f %.1f   # du %.3f off %.3f, %.2f m from eye, radius %.2f deg'%(name,*C1,y1,du1,o1,np.linalg.norm(C1-eye),r1))
        print('%s_2 %.4f,%.4f,%.4f %.1f   # du %.3f off %.3f, %.2f m from eye, radius %.2f deg, gap %.1f deg, z %.3f'%(name,*C2,y2,du1+du,o2,np.linalg.norm(C2-eye),r2,gap,C2[2]))
        done=True; break
    if not done: print(name,'no position within the size limits at this scale')
