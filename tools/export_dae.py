import numpy as np, sys, math
names=['std','stripped','cage','std_2','stripped_2','cage_2',      # Ibishu Covet
       'bx_std','bx_cage','bx_std_2','bx_cage_2']                     # Ibishu 200BX
D={n:np.load('parts_%s.npy'%n,allow_pickle=True).item() for n in names}
R=0.0235; SEG=40
a=np.linspace(0,2*np.pi,SEG+1)[:-1]
sp=np.vstack([[0,0,0],np.c_[R*np.cos(a),0*a,R*np.sin(a)]]); sn=np.tile([0,1,0],(SEG+1,1)).astype(float)
suv=np.vstack([[0.5,0.5],np.c_[0.5-0.5*np.cos(a),0.5+0.5*np.sin(a)]])
st=np.array([[0,1+i,1+(i+1)%SEG] for i in range(SEG)])
# make sure the screen faces +Y
fn=np.cross(sp[st[0,1]]-sp[st[0,0]],sp[st[0,2]]-sp[st[0,0]])
if fn[1]<0: st=st[:,::-1]
def geom(name,groups):
    P=[];N=[];UV=[];tris=[];off=0
    for mat,(p,n,t,uv) in groups:
        P.append(p);N.append(n);UV.append(uv if uv is not None else np.zeros((len(p),2)));tris.append((mat,t+off));off+=len(p)
    P=np.vstack(P);N=np.vstack(N);UV=np.vstack(UV);nv=len(P)
    f=lambda A,fmt:" ".join(fmt%x for x in A.ravel())
    s=f'''    <geometry id="{name}-mesh" name="{name}">
      <mesh>
        <source id="{name}-mesh-positions"><float_array id="{name}-mesh-positions-array" count="{nv*3}">{f(P,"%.6f")}</float_array>
          <technique_common><accessor source="#{name}-mesh-positions-array" count="{nv}" stride="3"><param name="X" type="float"/><param name="Y" type="float"/><param name="Z" type="float"/></accessor></technique_common></source>
        <source id="{name}-mesh-normals"><float_array id="{name}-mesh-normals-array" count="{nv*3}">{f(N,"%.5f")}</float_array>
          <technique_common><accessor source="#{name}-mesh-normals-array" count="{nv}" stride="3"><param name="X" type="float"/><param name="Y" type="float"/><param name="Z" type="float"/></accessor></technique_common></source>
        <source id="{name}-mesh-map-0"><float_array id="{name}-mesh-map-0-array" count="{nv*2}">{f(UV,"%.5f")}</float_array>
          <technique_common><accessor source="#{name}-mesh-map-0-array" count="{nv}" stride="2"><param name="S" type="float"/><param name="T" type="float"/></accessor></technique_common></source>
        <vertices id="{name}-mesh-vertices"><input semantic="POSITION" source="#{name}-mesh-positions"/></vertices>
'''
    for mat,t in tris:
        idx=" ".join("%d %d %d"%(i,i,i) for i in t.ravel())
        s+=f'''        <triangles material="{mat}-material" count="{len(t)}">
          <input semantic="VERTEX" source="#{name}-mesh-vertices" offset="0"/>
          <input semantic="NORMAL" source="#{name}-mesh-normals" offset="1"/>
          <input semantic="TEXCOORD" source="#{name}-mesh-map-0" offset="2" set="0"/>
          <p>{idx}</p>
        </triangles>
'''
    return s+"      </mesh>\n    </geometry>\n"
def node(name,mats):
    im="".join(f'''              <instance_material symbol="{m}-material" target="#{m}-material"><bind_vertex_input semantic="UVMap" input_semantic="TEXCOORD" input_set="0"/></instance_material>\n''' for m in mats)
    return f'''      <node id="{name}" name="{name}" type="NODE">
        <matrix sid="transform">1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1</matrix>
        <instance_geometry url="#{name}-mesh" name="{name}">
          <bind_material><technique_common>
{im}          </technique_common></bind_material>
        </instance_geometry>
      </node>
'''
mats=[("dbg_body","0.03 0.03 0.03"),("dbg_bezel","0.01 0.01 0.01"),("dbg_screen","0.05 0.05 0.05"),("dbg_oil_screen","0.05 0.05 0.05"),("dbg_bezel_silver","0.7 0.7 0.7"),("dbg_screen_w","0.8 0.8 0.8"),("dbg_oil_screen_w","0.8 0.8 0.8")]
# screens with the other printed faces, for any gauge type in either position (automatic mounting only)
mats+=[("dbg_mfd_screen","0.02 0.02 0.025"),("dbg_mfd_frame","0.025 0.025 0.028")]   # multi-function display
mats+=[(m,"0.05 0.05 0.05" if not m.endswith("_w") else "0.8 0.8 0.8") for m in
       ("dbg_screen_t","dbg_screen_t_w","dbg_screen_f","dbg_screen_f_w","dbg_oil_screen_b","dbg_oil_screen_b_w","dbg_oil_screen_f","dbg_oil_screen_f_w")]
eff="".join(f'''    <effect id="{m}-effect"><profile_COMMON><technique sid="common"><lambert>
      <emission><color sid="emission">0 0 0 1</color></emission><diffuse><color sid="diffuse">{c} 1</color></diffuse>
      <index_of_refraction><float sid="ior">1.45</float></index_of_refraction></lambert></technique></profile_COMMON></effect>\n''' for m,c in mats)
def mirror(part):
    p,n,t,uv=part
    p=p.copy(); n=n.copy(); p[:,0]*=-1; n[:,0]*=-1
    return p,n,t[:,::-1].copy(),uv
geoms="";nodes=""
for tag,src,sc in (("80","std",0.8),("65","cage",0.65)):     # two gauge sizes: A-pillar mountings and roll-cage mounting
    g=D[src]['gauge']
    geoms+=geom("dbg_gauge_"+tag,[("dbg_bezel",g)])+geom("dbg_screen_"+tag,[("dbg_screen",(sp*sc,sn,st,suv))])+geom("dbg_oil_screen_"+tag,[("dbg_oil_screen",(sp*sc,sn,st,suv))])
    nodes+=node("dbg_gauge_"+tag,["dbg_bezel"])+node("dbg_screen_"+tag,["dbg_screen"])+node("dbg_oil_screen_"+tag,["dbg_oil_screen"])
    # silver bezel + white faceplate versions
    geoms+=geom("dbg_gauge_silver_"+tag,[("dbg_bezel_silver",g)])+geom("dbg_screen_w_"+tag,[("dbg_screen_w",(sp*sc,sn,st,suv))])+geom("dbg_oil_screen_w_"+tag,[("dbg_oil_screen_w",(sp*sc,sn,st,suv))])
    nodes+=node("dbg_gauge_silver_"+tag,["dbg_bezel_silver"])+node("dbg_screen_w_"+tag,["dbg_screen_w"])+node("dbg_oil_screen_w_"+tag,["dbg_oil_screen_w"])
POD_NAME={'bx_std':'bx_pillar'}   # mesh name differs from the parts file name
for n in names:
    base_n=n[:-2] if n.endswith("_2") else n
    base_n=POD_NAME.get(base_n,base_n)
    nm=("dbg_pod2_" if n.endswith("_2") else "dbg_pod_")+base_n
    geoms+=geom(nm,[("dbg_body",D[n]['pod'])]); nodes+=node(nm,["dbg_body"])
    geoms+=geom(nm+"_rhd",[("dbg_body",mirror(D[n]['pod']))]); nodes+=node(nm+"_rhd",["dbg_body"])
# ---- automatic mounting: every mounting of every gauge gets its own uniquely named meshes, so the
# mod's script can show one set and hide the rest. Names are all 9 characters and none is a
# substring of another: dbgv + mounting (A-J) + position (1 lower, 2 upper) + one of
#   pod, bzk / bzs (black / silver bezel),
#   s + printed face (b boost, t temperature, f fuel) + k / s (black face / white face of the silver version)
AUTO=(("A","std",False,0.8,"std"),("B","stripped",False,0.8,"std"),("C","cage",False,0.65,"cage"),          # Covet
      ("D","std",True,0.8,"std"),("E","stripped",True,0.8,"std"),("F","cage",True,0.65,"cage"),
      ("G","bx_std",False,0.8,"std"),("H","bx_cage",False,0.65,"cage"),                                   # 200BX
      ("I","bx_std",True,0.8,"std"),("J","bx_cage",True,0.65,"cage"))
for code,var,rhd,sc,gsrc in AUTO:
    g=D[gsrc]['gauge']
    # screen material per position and printed face: (black, silver-version white)
    SCREENS=({"b":("dbg_screen","dbg_screen_w"),"t":("dbg_screen_t","dbg_screen_t_w"),"f":("dbg_screen_f","dbg_screen_f_w")},
             {"b":("dbg_oil_screen_b","dbg_oil_screen_b_w"),"t":("dbg_oil_screen","dbg_oil_screen_w"),"f":("dbg_oil_screen_f","dbg_oil_screen_f_w")})
    for gi,suffix in enumerate(("","_2"),1):
        pod=D[var+suffix]['pod']
        if rhd: pod=mirror(pod)
        base="dbgv%s%d"%(code,gi)
        items=[(base+"pod","dbg_body",pod),(base+"bzk","dbg_bezel",g),(base+"bzs","dbg_bezel_silver",g)]
        for face,(mk,ms) in SCREENS[gi-1].items():
            items+=[(base+"s"+face+"k",mk,(sp*sc,sn,st,suv)),(base+"s"+face+"s",ms,(sp*sc,sn,st,suv))]
        for nm,mat,part in items:
            geoms+=geom(nm,[(mat,part)]); nodes+=node(nm,[mat])
# multi-function display (automatic mounting only): dbgv + mounting + "3" + shl (housing and pod),
# frm (front frame), btn (page button), scr (screen). Built per mounting by build_mfd_mesh.py.
MFD_AUTO=(("A","std",False),("B","stripped",False),("C","cage",False),("D","std",True),("E","stripped",True),("F","cage",True))
for code,var,rhd in MFD_AUTO:
    M=np.load("mfd_%s.npy"%var,allow_pickle=True).item()
    base="dbgv%s3"%code
    for suf,key,mat in (("shl","shell","dbg_body"),("frm","frame","dbg_mfd_frame"),("btn","button","dbg_bezel_silver"),("scr","screen","dbg_mfd_screen")):
        part=M[key]
        if rhd and key=="shell": part=mirror(part)     # only the pod is shaped to one side; the housing is symmetric
        geoms+=geom(base+suf,[(mat,part)]); nodes+=node(base+suf,[mat])
xml=f'''<?xml version="1.0" encoding="utf-8"?>
<COLLADA xmlns="http://www.collada.org/2005/11/COLLADASchema" version="1.4.1" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
  <asset>
    <contributor><author>Pillar Pod Digital Gauges</author><authoring_tool>Blender (bpy) + tools/export_dae.py</authoring_tool></contributor>
    <created>2026-11-11T21:00:00</created><modified>2026-11-11T21:00:00</modified>
    <unit name="meter" meter="1"/><up_axis>Z_UP</up_axis>
  </asset>
  <library_effects>
{eff}  </library_effects>
  <library_materials>
'''+"".join(f'    <material id="{m}-material" name="{m}"><instance_effect url="#{m}-effect"/></material>\n' for m,_ in mats)+'''  </library_materials>
  <library_geometries>
'''+geoms+'''  </library_geometries>
  <library_visual_scenes>
    <visual_scene id="Scene" name="Scene">
'''+nodes+'''    </visual_scene>
  </library_visual_scenes>
  <scene><instance_visual_scene url="#Scene"/></scene>
</COLLADA>
'''
open(sys.argv[1],"w").write(xml)
import xml.dom.minidom as m; m.parse(sys.argv[1]); print("ok",len(xml))
