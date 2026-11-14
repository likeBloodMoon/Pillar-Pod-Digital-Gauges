"""LHD vs RHD check of every mounting against the game's real left/right interior meshes: nearest
interior part to the pod/display (clearance, leaving out the surface it mounts on) and how much of the
gauge face/screen the driver can see. RHD uses the RHD meshes and a mirrored eye.

    python check_rhd.py <200BX eye x,y,z> <parts dir> covet_cabin_lr.npy bx_cabin_lr.npy

The cabin files come from extract_cabin.py (BeamNG's data: keep them out of the repository)."""
import numpy as np, math, sys
from scipy.spatial import cKDTree
V4=(sys.argv[2] if len(sys.argv)>2 else '.')+'/'
cov=np.load(sys.argv[3] if len(sys.argv)>3 else 'covet_cabin_lr.npy',allow_pickle=True).item(); bxc=np.load(sys.argv[4] if len(sys.argv)>4 else 'bx_cabin_lr.npy',allow_pickle=True).item()
EYE={'covet':np.array([0.340,0.176,1.079]),'bx':np.array([float(v) for v in (sys.argv[1] if len(sys.argv)>1 else '0.349,0.266,1.049').split(',')])}
class Occ:
    def __init__(s,d,names):
        T=[];own=[]
        for k in names:
            p,t=d[k]; T.append(p.astype(float)[t]); own+=[k]*len(t)
        T=np.vstack(T); s.A=T[:,0]; s.E1=T[:,1]-s.A; s.E2=T[:,2]-s.A; s.own=np.array(own)
        s.pts=cKDTree(np.vstack([T[:,0],T[:,1],T[:,2],T.mean(1)])); s.ownp=np.concatenate([s.own]*4)
    def hit(s,o,d,tmax):
        h=np.cross(d,s.E2); a=np.einsum('ij,ij->i',s.E1,h); ok=np.abs(a)>1e-12
        f=1/np.where(ok,a,1); q0=o-s.A; u=f*np.einsum('ij,ij->i',q0,h)
        q=np.cross(q0,s.E1); v=f*(q@d); t=f*np.einsum('ij,ij->i',s.E2,q)
        m=ok&(u>=0)&(v>=0)&(u+v<=1)&(t>1e-5)&(t<tmax)
        return s.own[m][np.argmin(t[m])] if m.any() else None
def rot(yaw):
    a=math.radians(yaw); return np.array([[math.cos(a),-math.sin(a),0],[math.sin(a),math.cos(a),0],[0,0,1]])
def mirror_names(names,car):
    out=[]
    for n in names:
        m={'covet_door_L':'covet_door_R','covet_doorpanel_L':'covet_doorpanel_R','covet_door_grp_doorpanel_L':'covet_door_grp_doorpanel_R','covet_sunvisor_L':'covet_sunvisor_R','covet_dash':'covet_dash_rhd','covet_dash_rally':'covet_dash_rhd_rally','covet_doorglass_L_int':'covet_doorglass_R_int',
           'bx_door_L':'bx_door_R','bx_doorpanel_L':'bx_doorpanel_R','bx_sunvisor_L':'bx_sunvisor_R','bx_dash':'bx_dash_rhd','bx_dash_rally':'bx_dash_rhd_rally','bx_mirror_int_lhd':'bx_mirror_int_rhd','bx_grp_dash':'bx_grp_dash_rhd','bx_steer':'bx_steer_rhd'}.get(n,n)
        out.append(m)
    return out
CB=['covet_body','covet_door_L','covet_doorpanel_L','covet_door_grp_doorpanel_L','covet_sunvisor_L','covet_doorglass_L_int']
BB=['bx_steer','bx_body_hatch','bx_door_L','bx_doorpanel_L','bx_sunvisor_L','bx_sunvisor_mounts','bx_mirror_int_lhd','bx_intpanels_hatch']
ROWS=[ # car, mounting, interior meshes (LHD), [(C, yaw, parts file or mfd, kind, scale)]
 ('covet','std',CB+['covet_dash','covet_intcarpet'],[((0.5749,-0.3246,1.0758),24.8,'std','g',0.8),((0.5397,-0.2291,1.1372),25.7,'std_2','g',0.8),((0.5474,-0.2651,1.1024),24.8,'std','m',1)]),
 ('covet','stripped',CB+['covet_dash_rally','covet_stripped_int_F'],[((0.5823,-0.3407,1.0756),24.8,'stripped','g',0.8),((0.5473,-0.2448,1.1393),25.7,'stripped_2','g',0.8),((0.5523,-0.2756,1.1029),24.8,'stripped','m',1)]),
 ('covet','cage',CB+['covet_dash_rally','covet_stripped_int_F','covet_rollcage_F'],[((0.5175,-0.2189,1.0961),23.8,'cage','g',0.65),((0.4972,-0.1483,1.1426),25.2,'cage_2','g',0.65),((0.5165,-0.1981,1.0992),24.8,'cage','m',1)]),
 ('bx','pillar',BB+['bx_dash','bx_intcarpet_hatch'],[((0.6081,-0.2417,1.0150),27.0,'bx_std','g',0.8),((0.5753,-0.1308,1.0769),29.7,'bx_std_2','g',0.8)]),
 ('bx','cage',BB+['bx_dash_rally','bx_rollcage'],[((0.5245,-0.1621,1.0259),22.3,'bx_cage','g',0.65),((0.4943,-0.0712,1.0781),23.3,'bx_cage_2','g',0.65)]),
]
def samples(P,T,n=3):
    A,B,C=P[T[:,0]],P[T[:,1]],P[T[:,2]]; out=[P]
    for a in np.linspace(0,1,n+1):
        for b in np.linspace(0,1-a,n+1): out.append(A*(1-a-b)+B*a+C*b)
    return np.vstack(out)
results=[]
for car,mount,names,items in ROWS:
    d=cov if car=='covet' else bxc
    for C,yaw,pf,kind,sc in items:
        row=[car,mount,('gauge %s'%('1' if not pf.endswith('_2') else '2')) if kind=='g' else 'display']
        for sx in (1,-1):
            nm=names if sx>0 else mirror_names(names,car)
            R=rot(yaw); C3=np.array(C)
            if kind=='g':
                parts=np.load(V4+'parts_%s.npy'%pf,allow_pickle=True).item(); keys=['pod','gauge']
                ang=np.linspace(0,2*np.pi,24,endpoint=False); r=0.0235*sc
                face=np.vstack([[0,0.004,0],*[[rr*math.cos(t),0.004,rr*math.sin(t)] for rr in (r*0.5,r*0.95) for t in ang]])
            else:
                parts=np.load(V4+'mfd_%s.npy'%pf,allow_pickle=True).item(); keys=['shell','frame','button','screen']
                sp=parts['screen'][0].astype(float); face=sp+np.array([0,0.004,0])
            mesh=np.vstack([samples(parts[k][0].astype(float),parts[k][2].astype(int)) for k in keys])
            Pm=mesh@R.T+C3; F=face@R.T+C3
            if sx<0: Pm=Pm*[-1,1,1]; F=F*[-1,1,1]
            # clearance to everything except the mounting surface (body / stripped trim / cage tube)
            others=[k for k in nm if not any(s in k for s in ('body','stripped_int','rollcage','intcarpet','intpanels'))]
            Q=np.vstack([d[k][0].astype(float) for k in others]); own=np.concatenate([[k]*len(d[k][0]) for k in others])
            dd,ii=cKDTree(Q).query(Pm); j=np.argmin(dd); jn=ii[j]
            eye=EYE[car]*[sx,1,1]; occ=Occ(d,nm); vis=0; blockers={}
            for p in F:
                v=p-eye; L=np.linalg.norm(v); h=occ.hit(eye,v/L,L-0.006)
                if h is None: vis+=1
                else: blockers[h]=blockers.get(h,0)+1
            row+=[own[jn],dd[j]*1000,100*vis/len(F),blockers]
        results.append(row)
        print('%-5s %-8s %-8s | LHD: nearest %-26s %5.1f mm, face visible %5.1f %% %s | RHD: nearest %-26s %5.1f mm, face visible %5.1f %% %s'%tuple(row))

