"""Extract named interior meshes from a car's Collada file (e.g. the game's bx.dae) into an .npy
used by find_positions*.py and build_pod_mesh.py.

    python extract_cabin.py bx.dae bx_cabin.npy bx_intcarpet_hatch,bx_rollcage,bx_dash,...

Output: {node name: (positions Nx3 in car space, triangles Mx3)}. The game's meshes are BeamNG's
files; keep the extracted data out of this repository.
"""
import sys, numpy as np, xml.etree.ElementTree as ET
NS='{http://www.collada.org/2005/11/COLLADASchema}'
want=set(sys.argv[3].split(','))
root=ET.parse(sys.argv[1]).getroot()
geos={g.get('id'):g for g in root.iter(NS+'geometry')}
out={}
def walk(node,M):
    m=node.find(NS+'matrix')
    if m is not None: M=M@np.array(m.text.split(),float).reshape(4,4)
    nid=node.get('id') or node.get('name')
    if nid in want:
        for ig in node.findall(NS+'instance_geometry'):
            g=geos[ig.get('url')[1:]]; mesh=g.find(NS+'mesh')
            srcs={s.get('id'):np.array(s.find(NS+'float_array').text.split(),float) for s in mesh.findall(NS+'source')}
            vx=mesh.find(NS+'vertices'); possrc=[i.get('source')[1:] for i in vx.findall(NS+'input') if i.get('semantic')=='POSITION'][0]
            P=srcs[possrc].reshape(-1,3); P=(np.c_[P,np.ones(len(P))]@M.T)[:,:3]
            T=[]
            for prim in list(mesh.findall(NS+'triangles'))+list(mesh.findall(NS+'polylist')):
                ins=prim.findall(NS+'input'); st=max(int(i.get('offset')) for i in ins)+1
                vo=[int(i.get('offset')) for i in ins if i.get('semantic')=='VERTEX'][0]
                p=np.array(prim.find(NS+'p').text.split(),int).reshape(-1,st)[:,vo]
                if prim.tag.endswith('polylist'):
                    vc=np.array(prim.find(NS+'vcount').text.split(),int); k=0
                    for c in vc:
                        for j in range(1,c-1): T.append((p[k],p[k+j],p[k+j+1]))
                        k+=c
                else: T+=list(p.reshape(-1,3))
            if nid in out:
                op,ot=out[nid]; out[nid]=(np.vstack([op,P]),np.vstack([ot,np.array(T)+len(op)]))
            else: out[nid]=(P.astype(np.float32),np.array(T,np.int32))
    for c in node.findall(NS+'node'): walk(c,M)
for vs in root.iter(NS+'visual_scene'):
    for n in vs.findall(NS+'node'): walk(n,np.eye(4))
for k,(p,t) in out.items(): print(k,len(p),len(t),p.min(0).round(3),p.max(0).round(3))
print('missing',want-set(out))
np.save(sys.argv[2],out,allow_pickle=True)
