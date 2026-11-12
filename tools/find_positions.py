import numpy as np, sys, math
cab=np.load(sys.argv[1],allow_pickle=True).item()
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
eye=np.array([0.333,0.20,1.08]); eye2=np.array([0.0,0.15,1.10])
CA=np.array([0.579,-0.3336,1.0757])
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
V={'std':['covet_intcarpet','covet_body','covet_door_L','covet_doorpanel_L','covet_dash'],
   'stripped':['covet_stripped_int_F','covet_body','covet_door_L','covet_door_grp_doorpanel_L','covet_doorpanel_L','covet_grp_dash_lhd','covet_dash'],
   'cage':['covet_stripped_int_F','covet_intcarpet','covet_rollcage_F','covet_body','covet_door_L','covet_door_grp_doorpanel_L','covet_doorpanel_L','covet_grp_dash_lhd','covet_dash']}
TARGET={'std':'covet_intcarpet','stripped':'covet_stripped_int_F','cage':'covet_rollcage_F'}
SL=np.array([0.5897,-0.48,1.04])   # shift light on the dash (race interiors)
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
for name,names in V.items():
    occ=Occ(names); du0=0.025 if name=='cage' else 0.0
    C1,y1,o1=place(occ,name,du0); r1=math.degrees(0.034*S/np.linalg.norm(C1-eye))
    print('%s_1 %.4f,%.4f,%.4f %.1f   # off %.3f, %.2f m from eye, radius %.1f deg, shiftlight %.1f deg'%(name,*C1,y1,o1,np.linalg.norm(C1-eye),r1,ang(C1-eye,SL-eye)))
    for du in np.arange(0.05,0.16,0.005):
        r=place(occ,name,du0+du)
        if not r: continue
        C2,y2,o2=r; r2=math.degrees(0.034*S/np.linalg.norm(C2-eye)); gap=ang(C2-eye,C1-eye)-r1-r2
        if gap>=1.2 and np.linalg.norm(C2-C1)>=0.068*S+0.01:
            print('%s_2 %.4f,%.4f,%.4f %.1f   # du %.3f off %.3f, %.2f m from eye, radius %.1f deg, gap %.1f deg, z %.3f'%(name,*C2,y2,du,o2,np.linalg.norm(C2-eye),r2,gap,C2[2])); break
    else: print(name,'no pos2')
