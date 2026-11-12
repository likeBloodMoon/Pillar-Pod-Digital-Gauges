"""Render the Covet cabin + the pod from the driver's eye, in car coordinates (perspective)."""
import numpy as np, sys, math
from PIL import Image
cab=np.load(sys.argv[1],allow_pickle=True).item()
out=sys.argv[2]; show=sys.argv[3].split(','); trip=sys.argv[4:]
meshes=[]
cols={'covet_intcarpet':(0.55,0.18,0.18),'covet_body':(0.8,0.8,0.8),'covet_door_L':(0.3,0.4,0.8),'covet_dash':(0.35,0.2,0.2),'covet_doorpanel_L':(0.4,0.25,0.25),
      'covet_stripped_int_F':(0.75,0.75,0.78),'covet_rollcage_F':(0.95,0.95,0.95),'covet_door_grp_doorpanel_L':(0.25,0.25,0.3),'covet_grp_dash_lhd':(0.2,0.2,0.22)}
for k in show:
    p,t=cab[k]; meshes.append((p.astype(float),t,cols.get(k,(0.5,0.5,0.5))))
Cs=[]
for i in range(0,len(trip),3):
    parts=np.load(trip[i],allow_pickle=True).item(); C=np.array([float(x) for x in trip[i+1].split(',')]); YAW=float(trip[i+2]); Cs.append(C)
    a=math.radians(YAW); R=np.array([[math.cos(a),-math.sin(a),0],[math.sin(a),math.cos(a),0],[0,0,1]])
    for name,c in (('pod',(0.12,0.12,0.13)),('gauge',(0.3,0.3,0.33))):
        p,n,t,_=parts[name]; meshes.append((p@R.T+C,t,c))
    Rs=float(np.abs(parts["gauge"][0][:,0]).max())*0.0235/0.0292; ang=np.linspace(0,2*np.pi,41)[:-1]
    sp=np.vstack([[0,0,0],np.c_[Rs*np.cos(ang),0*ang,Rs*np.sin(ang)]])@R.T+C; st=np.array([[0,1+i,1+(i+1)%40] for i in range(40)])
    meshes.append((sp,st,(1,0.1,0.1) if i==0 else (1,0.6,0.1)))
C=np.mean(Cs,axis=0)
def render(eye,target,fov=60,S=(640,480),two_sided=True):
    eye=np.array(eye,float);f=np.array(target,float)-eye;f/=np.linalg.norm(f)
    r=np.cross(f,[0,0,1]);r/=np.linalg.norm(r);u=np.cross(r,f)
    W,H=S;fl=(W/2)/math.tan(math.radians(fov)/2)
    img=np.full((H,W,3),(150,190,230),np.uint8);zb=np.full((H,W),1e9)
    L=np.array([0.2,0.5,0.8]);L/=np.linalg.norm(L)
    for P,T,c in meshes:
        Q=P-eye;z=Q@f;ok=z>0.03
        px=W/2+fl*(Q@r)/np.maximum(z,1e-6);py=H/2-fl*(Q@u)/np.maximum(z,1e-6)
        fn=np.cross(P[T[:,1]]-P[T[:,0]],P[T[:,2]]-P[T[:,0]]);ln=np.linalg.norm(fn,axis=1)+1e-12;fn/=ln[:,None]
        for ti,t in enumerate(T):
            if not ok[t].all(): continue
            X,Y,Z=px[t],py[t],z[t]
            x0,x1=int(max(0,np.floor(X.min()))),int(min(W-1,np.ceil(X.max())));y0,y1=int(max(0,np.floor(Y.min()))),int(min(H-1,np.ceil(Y.max())))
            if x1<x0 or y1<y0: continue
            den=(Y[1]-Y[2])*(X[0]-X[2])+(X[2]-X[1])*(Y[0]-Y[2])
            if abs(den)<1e-9: continue
            gx,gy=np.meshgrid(np.arange(x0,x1+1)+.5,np.arange(y0,y1+1)+.5)
            w0=((Y[1]-Y[2])*(gx-X[2])+(X[2]-X[1])*(gy-Y[2]))/den;w1=((Y[2]-Y[0])*(gx-X[2])+(X[0]-X[2])*(gy-Y[2]))/den;w2=1-w0-w1
            m=(w0>=0)&(w1>=0)&(w2>=0);zz=1/(w0/Z[0]+w1/Z[1]+w2/Z[2]+1e-12)
            sub=zb[y0:y1+1,x0:x1+1];m&=zz<sub
            sh=abs(fn[ti]@L)*0.6+0.4
            sub[m]=zz[m];img[y0:y1+1,x0:x1+1][m]=(np.array(c)*sh*255).astype(np.uint8)
    return img
eye=(0.333,0.20,1.08)
a1=render(eye,(0.45,-1.5,0.95),fov=75)
a2=render(eye,tuple(C),fov=40)
a3=render((0.15,-0.15,1.12),tuple(C),fov=50)   # from the passenger side, looking at the pillar
Image.fromarray(np.hstack([a1,a2,a3])).save(out)
