import math
import re,sys
import argparse
# Per-car setup. POS: mounting -> (boost position, oil position) -> ((x,y,z) centre of the gauge face, yaw).
# Positions are for the left-hand-drive side; right-hand drive mirrors x and yaw.
# AUTO: automatic-mounting letter for each (mounting, side); the letters must match the meshes
# written by export_dae.py and the table in dbgAmbient.lua.
CARS={
 "covet":dict(
  label="Ibishu Covet", root="covet_digital_boost_gauge_pillar", mod_slot="covet_mod", group="covet_dash",
  out="vehicles/covet/covet_pillar_pod_gauges.jbeam",
  POS={"std":(((0.5749,-0.3246,1.0758),24.8),((0.5397,-0.2291,1.1372),25.7)),
       "stripped":(((0.5823,-0.3407,1.0756),24.8),((0.5473,-0.2448,1.1393),25.7)),
       "cage":(((0.5175,-0.2189,1.0961),23.8),((0.4972,-0.1483,1.1426),25.2))},
  SIZE={"std":"80","stripped":"80","cage":"65"},
  NAMES={"std":"A-Pillar, Standard Interior","stripped":"A-Pillar, Stripped / Race / Rally Interior","cage":"Roll Cage Bar"},
  MESH={"std":"std","stripped":"stripped","cage":"cage"},
  AUTO=(("A","std",1),("B","stripped",1),("C","cage",1),("D","std",-1),("E","stripped",-1),("F","cage",-1)),
  # multi-function display: screen centre, yaw and scale per mounting (tools/find_mfd_position.py),
  # and the body nodes the page button's click trigger hangs from, per side
  MFD={"std":((0.5474,-0.2651,1.1024),24.8,1.0),"stripped":((0.5523,-0.2756,1.1029),24.8,1.0),
       "cage":((0.5165,-0.1981,1.0992),24.8,0.85)},
  TRIGGER_NODES={1:("p1l","rf1l","p2l"),-1:("p1r","rf1r","p2r")},
  # digital cluster in the car's own Gauges slots: (slot type, kind, side, meshes, touch point on the
  # page panel for LHD). Meshes are in car coordinates (build_cluster_mesh.py).
  CLUSTER=(("covet_gauges","std",1,["dbg_cluster_covet"]),
           ("covet_gauges_rhd","std",-1,["dbg_cluster_covet_rhd"]),
           ("covet_gauges_race_lhd","race",1,["covet_grp_dash_instrumentpanel","dbg_cluster_race_shl","dbg_cluster_race_frm","dbg_cluster_race_scr"]),
           ("covet_gauges_race_rhd","race",-1,["covet_grp_dash_instrumentpanel_rhd","dbg_cluster_race_shl_rhd","dbg_cluster_race_frm_rhd","dbg_cluster_race_scr_rhd"])),
  CLUSTER_TOUCH={"std":(0.2334,-0.6415,0.8186),"race":(0.2676,-0.5404,0.8312)}),
 "bx":dict(
  label="Ibishu 200BX", root="bx_pillar_pod_gauges", mod_slot="bx_mod", group="bx_body",
  out="vehicles/bx/bx_pillar_pod_gauges.jbeam",
  # the 200BX's A-pillar is the same shape with every interior, coupe or liftback, so one pillar mounting covers them all
  POS={"pillar":(((0.5837,-0.1443,1.0671),24.7),((0.5502,-0.0285,1.1255),26.9)),
       "cage":(((0.4943,-0.0537,1.0857),19.6),((0.4630,0.0510,1.1297),20.4))},
  SIZE={"pillar":"80","cage":"65"},
  NAMES={"pillar":"A-Pillar, Any Interior","cage":"Roll Cage Bar"},
  MESH={"pillar":"bx_pillar","cage":"bx_cage"},
  AUTO=(("G","pillar",1),("H","cage",1),("I","pillar",-1),("J","cage",-1))),
}
ap=argparse.ArgumentParser(description="Generate a car's part file")
ap.add_argument("out"); ap.add_argument("--car",default="covet",choices=sorted(CARS))
args=ap.parse_args(); CAR=CARS[args.car]
POS,SIZE,NAMES,MESH=CAR["POS"],CAR["SIZE"],CAR["NAMES"],CAR["MESH"]
P=args.car; GROUP=CAR["group"]
HEAD_CFG='''            "materialName": "@{mat}",
            "htmlPath": "local://local/vehicles/common/pillar_pod_gauges/screen.html",
            "displayWidth":512,
            "displayHeight":512,'''
BOOST_CFG='''            "source":"boost",
            //"auto" follows the game's pressure unit setting; or force "psi", "bar" or "kpa"
            "unit":"auto",
            //LED arc range in PSI; LEDs below zeroValue show vacuum
            "minValue":-10,
            //0 = automatic: 1.25 x the turbo wastegate limit, so the red LEDs start just above it. A number here fixes the scale
            "maxValue":0,
            "zeroValue":0,
            //the zero mark stays on the 7th LED so it matches the printed face; the scale stretches around it
            "zeroLed":6,
            "titleLabel":"BOOST",
            //after a pull, flash the peak value for recallTime seconds
            //1 = the whole LED ring flashes red near the rev limit (shiftAt = fraction of maximum RPM)
            "shiftLight":"$dbg_boost_shift",
            "shiftAt":0.96,
            "peakRecall":true,
            "recallTime":"$dbg_boost_recall",
            //digits flash at or above this boost
            "warnValue":"$dbg_boost_warn_at",
            //seconds the peak LED stays lit
            "peakHold":1.5,
            //display brightness at night or with headlights on (1 = no dimming)
            "nightBrightness":"$dbg_boost_night",'''
OIL_CFG='''            "source":"oiltemp",
            "decimals":0,
            //LED arc range in deg C (the digits follow the game's temperature unit setting)
            "minValue":50,
            "maxValue":150,
            "titleLabel":"OIL TEMP",
            //digits flash at or above this temperature (deg C)
            "warnValue":"$dbg_oil_warn",
            //a blue COLD mark shows below this oil temperature (deg C); 0 = off
            "coldBelow":"$dbg_oil_cold",
            "peakHold":0,
            "nightBrightness":"$dbg_oil_night",'''
WATER_CFG='''            "source":"watertemp",
            "decimals":0,
            //LED arc range in deg C (the digits follow the game's temperature unit setting)
            "minValue":40,
            "maxValue":130,
            "titleLabel":"COOLANT",
            //digits flash at or above this temperature (deg C)
            "warnValue":"$dbg_water_warn",
            //a blue COLD mark shows below this coolant temperature (deg C); 0 = off
            "coldBelow":"$dbg_water_cold",
            "peakHold":0,
            "nightBrightness":"$dbg_water_night",'''
EGT_CFG='''            "source":"egt",
            "decimals":0,
            //LED arc range in deg C (the digits follow the game's temperature unit setting; in deg F they read in hundreds)
            "minValue":200,
            "maxValue":1000,
            "titleLabel":"EGT",
            //digits flash at or above this temperature (deg C)
            "warnValue":"$dbg_egt_warn",
            "peakHold":0,
            "nightBrightness":"$dbg_egt_night",'''
FUEL_CFG='''            "source":"fuel",
            //tank level in percent
            "minValue":0,
            "maxValue":100,
            "titleLabel":"FUEL",
            //the warning is at the low end: red LEDs first, digits flash at or below warnValue (percent)
            "warnLow":1,
            "warnValue":"$dbg_fuel_low",
            "peakHold":0,
            "nightBrightness":"$dbg_fuel_night",'''
AUTO_DEFAULT=P+"_dbg_boost_auto"
_rows=[['"name"','"allowTypes"','"denyTypes"','"default"','"description"'],
       ['"%s_dbg_boost"'%P,'["%s_dbg_boost"]'%P,'[]','"%s"'%AUTO_DEFAULT,'"Lower Gauge"'],
       ['"%s_dbg_oil"'%P,'["%s_dbg_oil"]'%P,'[]','""','"Upper Gauge"']]
_w=[max(len(r[i]) for r in _rows)+1 for i in range(5)]
SLOTS2="\n".join("        ["+" ".join((c+",").ljust(_w[i]+1) if i<4 else c for i,c in enumerate(r))+"]," for r in _rows)
out=f'''{{
//Pillar Pod Digital Gauges - parts for the {CAR["label"]}.
//  Additional Modification -> Digital Pillar Gauges
//      Lower Gauge: boost (default), oil temp, coolant temp, exhaust temp or fuel level
//      Upper Gauge: empty (default), oil temp, coolant temp, exhaust temp, fuel level or boost
//Every gauge type comes with automatic mounting in black or silver: it picks the position that
//matches the car's interior. Boost (lower) and oil temp (upper) are also offered in fixed mountings,
//which always use the position they name.
"{CAR["root"]}": {{
    "information":{{
        "authors":"Kristof",
        "name":"Digital Pillar Gauges",
        "value":0,
    }},
    "slotType" : "{CAR["mod_slot"]}",
    "slots2": [
{SLOTS2}
    ],
    //ambient light for automatic display dimming (shared by both gauges)
    "controller": [
        ["fileName"],
        ["gauges/customModules/dbgAmbient"],
    ],
}},
'''
BOOST_VARS='''        ["$dbg_boost_shift", "range", "", "Gauges", 1, 0, 1, "Boost Gauge: Shift Light", "1 = the LED ring flashes red near the rev limit, 0 = off", {"stepDis":1}],
        ["$dbg_boost_warn_at", "range", "psi", "Gauges", 0, 0, 45, "Boost Gauge: Overboost Warning", "The digits flash at or above this boost pressure. 0 = automatic, just above the turbo wastegate limit", {"stepDis":0.5}],
        ["$dbg_boost_recall", "range", "s", "Gauges", 2.5, 0, 6, "Boost Gauge: Peak Recall Time", "How long the peak is shown after a pull; 0 turns peak recall off", {"stepDis":0.5}],
        ["$dbg_boost_night", "range", "%", "Gauges", 12, 3, 100, "Boost Gauge: Night Brightness", "Display brightness at night or with the headlights on", {"stepDis":1}],'''
WATER_VARS='''        ["$dbg_water_cold", "range", "C", "Gauges", 60, 0, 100, "Coolant Temp Gauge: Cold Mark Below", "A blue COLD mark shows below this coolant temperature (deg C). 0 = off", {"stepDis":1}],
        ["$dbg_water_warn", "range", "C", "Gauges", 110, 90, 130, "Coolant Temp Gauge: Warning Temperature", "The digits flash at or above this coolant temperature (deg C)", {"stepDis":1}],
        ["$dbg_water_night", "range", "%", "Gauges", 12, 3, 100, "Coolant Temp Gauge: Night Brightness", "Display brightness at night or with the headlights on", {"stepDis":1}],'''
EGT_VARS='''        ["$dbg_egt_warn", "range", "C", "Gauges", 900, 500, 1100, "Exhaust Temp Gauge: Warning Temperature", "The digits flash at or above this exhaust gas temperature (deg C)", {"stepDis":10}],
        ["$dbg_egt_night", "range", "%", "Gauges", 12, 3, 100, "Exhaust Temp Gauge: Night Brightness", "Display brightness at night or with the headlights on", {"stepDis":1}],'''
FUEL_VARS='''        ["$dbg_fuel_low", "range", "%", "Gauges", 10, 0, 40, "Fuel Gauge: Low Fuel Warning", "The digits flash at or below this tank level (percent). 0 = off", {"stepDis":1}],
        ["$dbg_fuel_night", "range", "%", "Gauges", 12, 3, 100, "Fuel Gauge: Night Brightness", "Display brightness at night or with the headlights on", {"stepDis":1}],'''
OIL_VARS='''        ["$dbg_oil_cold", "range", "C", "Gauges", 70, 0, 100, "Oil Temp Gauge: Cold Mark Below", "A blue COLD mark shows below this oil temperature (deg C). 0 = off", {"stepDis":1}],
        ["$dbg_oil_warn", "range", "C", "Gauges", 130, 90, 160, "Oil Temp Gauge: Warning Temperature", "The digits flash at or above this oil temperature (deg C)", {"stepDis":1}],
        ["$dbg_oil_night", "range", "%", "Gauges", 12, 3, 100, "Oil Temp Gauge: Night Brightness", "Display brightness at night or with the headlights on", {"stepDis":1}],'''
def part(key,name,slot,gvars,ctrl,cfgf,el,fb):
    return f'''"{key}": {{
    "information":{{
        "authors":"Kristof",
        "name":"{name}",
        "value":180,
    }},
    "slotType" : "{slot}",
    //sliders in the Tuning menu
    "variables": [
        ["name", "type", "unit", "category", "default", "min", "max", "title", "description"],
{gvars}
    ],
    "controller": [
        ["fileName"],
        ["gauges/genericGauges", {{"name":"{ctrl}"}}],
    ],
    "{ctrl}": {{
        "configuration": {{
{cfgf}
        }},
        "displayData": {{
            "electrics": [
{el}
            ],
            "customModules": [
                ["moduleName", "property"],
                ["dbgAmbient", "light"],
                ["dbgAmbient", "maxBoost"],
                ["dbgAmbient", "egt"],
            ],
        }},
    }},
    "flexbodies": [
        ["mesh", "[group]:", "nonFlexMaterials"],
{fb}
    ],
}},
'''
LIGHT=["ignitionLevel","lights","lowhighbeam"]
# gauge types: (key, name, config, sliders, electrics, printed face b/t/f)
TYPES={"boost":("Boost",BOOST_CFG,BOOST_VARS,["turboBoost","superchargerBoost","engineRunning","rpm","maxrpm"]+LIGHT,"b"),
       "oil":("Oil Temp",OIL_CFG,OIL_VARS,["oiltemp"]+LIGHT,"t"),
       "water":("Coolant Temp",WATER_CFG,WATER_VARS,["watertemp"]+LIGHT,"t"),
       "fuel":("Fuel Level",FUEL_CFG,FUEL_VARS,["fuel"]+LIGHT,"f"),
       "egt":("Exhaust Temp",EGT_CFG,EGT_VARS,LIGHT,"t")}
# positions: (slot, controller, screen material, fixed pod mesh, fixed screen mesh, its own gauge type, other types in list order)
POSITIONS=((P+"_dbg_boost","dbgGauge","dbg_screen","dbg_pod","dbg_screen","boost",("oil","water","egt","fuel")),
           (P+"_dbg_oil","dbgOilGauge","dbg_oil_screen","dbg_pod2","dbg_oil_screen","oil",("water","egt","fuel","boost")))
FINS=(("black","","","dbg_gauge","","black"),("silver","_silver",", Silver","dbg_gauge_silver","_w","white"))
SIDES=(("lhd",1,"","LHD"),("rhd",-1,"_rhd","RHD"))
def auto_part(gi,slot,ctrl,mat,tkey,keyname):
    gname,tcfg,gvars,electrics,facecode=TYPES[tkey]
    el="\n".join('                "%s",'%e for e in electrics)
    global out
    # automatic mounting: every mounting's meshes are fitted; the mod's script shows the matching one
    for fin,fkey,fname,bezel,scr_suffix,face in FINS:
        fb="        //meshes for every mounting (%s); dbgAmbient.lua"%"".join(c for c,_,_ in CAR["AUTO"])+" hides all but the one matching the car's interior\n"
        lines=[]
        for code,key,sx in CAR["AUTO"]:
            (x,y,z),yaw=POS[key][gi]
            pr='{"pos":{"x":%g,"y":%g,"z":%g},"rot":{"x":0,"y":0,"z":%g}}'%(sx*x,y,z,sx*yaw)
            base="dbgv%s%d"%(code,gi+1)
            k="k" if fin=="black" else "s"
            lines+=['        ["%spod", ["%s"],[],%s],'%(base,GROUP,pr),'        ["%sbz%s", ["%s"],[],%s],'%(base,k,GROUP,pr),'        ["%ss%s%s", ["%s"],[],%s],'%(base,facecode,k,GROUP,pr)]
        cfgf=HEAD_CFG.format(mat=mat)+"\n"+tcfg+'\n            "face":"%s",'%face
        out+=part(f"{keyname}_auto{fkey}", f"{gname} - Automatic Mounting{fname}", slot, gvars, ctrl, cfgf, el, fb+"\n".join(lines))
for gi,(slot,ctrl,mat,pod,screen,own,others) in enumerate(POSITIONS):
    auto_part(gi,slot,ctrl,mat,own,slot)
    for tkey in others:
        auto_part(gi,slot,ctrl,mat,tkey,f"{slot}_{tkey}")
    gname,tcfg,gvars,electrics,facecode=TYPES[own]
    el="\n".join('                "%s",'%e for e in electrics)
    for (fin,fkey,fname,bezel,scr_suffix,face),(side,sx,suffix,label) in [(f,s) for f in FINS for s in SIDES]:
        for key in POS:
            (x,y,z),yaw=POS[key][gi]
            cfgf=HEAD_CFG.format(mat=mat)+"\n"+tcfg+'\n            "face":"%s",'%face
            pr='{"pos":{"x":%g,"y":%g,"z":%g},"rot":{"x":0,"y":0,"z":%g}}'%(sx*x,y,z,sx*yaw)
            fb=f'''        //pos = centre of the gauge face. The pod mesh is shaped for exactly this spot.
        ["{pod}_{MESH[key]}{suffix}", ["{GROUP}"],[],{pr}],
        ["{bezel}_{SIZE[key]}", ["{GROUP}"],[],{pr}],
        ["{screen}{scr_suffix}_{SIZE[key]}", ["{GROUP}"],[],{pr}],'''
            out+=part(f"{slot}_{key}_{side}{fkey}", f"{gname} - {NAMES[key]} ({label}){fname}", slot, gvars, ctrl, cfgf, el, fb)

# multi-function display: a lower-gauge option with automatic mounting; the page button on its chin
# is an in-cabin click trigger (one per mounting, since the mounting is only known in game) that runs
# the dbgMfdNextPage action from pillar_pod_gauges.interaction.json
MFD_VARS='''        ["$dbg_mfd_page", "range", "", "Gauges", 0, 0, 4, "Display: First Page", "Page shown at start: 0 boost, 1 tyres, 2 engine, 3 brakes, 4 g-force", {"stepDis":1}],
        ["$dbg_mfd_night", "range", "%", "Gauges", 12, 3, 100, "Display: Night Brightness", "Display brightness at night or with the headlights on", {"stepDis":1}],'''
BUTTON=(0.0,0.0028,-0.0396)            # page button centre in the display's own space, before scaling
if "MFD" in CAR:
    fb=["        //meshes for every mounting; dbgAmbient.lua hides all but the one matching the car's interior"]
    trig=[]; links=[]
    for code,key,sx in CAR["AUTO"]:
        (x,y,z),yaw,sc=CAR["MFD"][key]
        pr='{"pos":{"x":%g,"y":%g,"z":%g},"rot":{"x":0,"y":0,"z":%g}}'%(sx*x,y,z,sx*yaw)
        for suf in ("shl","frm","btn","scr"):
            fb.append('        ["dbgv%s3%s", ["%s"],[],%s],'%(code,suf,GROUP,pr))
        a=math.radians(yaw); bx,by,bz=[c*sc for c in BUTTON]
        wx=x+bx*math.cos(a)-by*math.sin(a); wy=y+bx*math.sin(a)+by*math.cos(a); wz=z+bz
        n1,n2,n3=CAR["TRIGGER_NODES"][sx]
        trig.append('        ["dbg_mfd_%s", "%s","%s","%s", "sphere", %g, {"x":0,"y":0,"z":0},{"x":0,"y":0,"z":0},{"x":0,"y":0,"z":0},{"x":0,"y":0,"z":0}, {"baseTranslationGlobal":{"x":%.4f,"y":%.4f,"z":%.4f},"mesh":"dbgv%s3btn"}],'%(code,n1,n2,n3,round(0.011*sc/0.8,4),sx*wx,wy,wz,code))
        links.append('        ["dbg_mfd_%s", "action0", "dbgMfdNextPage"],'%code)
    slot=P+"_dbg_boost"
    out+=f'''"{slot}_mfd_auto": {{
    "information":{{
        "authors":"Kristof",
        "name":"Multi-Function Display - Automatic Mounting",
        "value":420,
    }},
    "slotType" : "{slot}",
    //takes the whole pillar: leave the Upper Gauge empty with this one
    "variables": [
        ["name", "type", "unit", "category", "default", "min", "max", "title", "description"],
{MFD_VARS}
    ],
    "controller": [
        ["fileName"],
        ["gauges/genericGauges", {{"name":"dbgMfd"}}],
    ],
    "dbgMfd": {{
        "configuration": {{
            "materialName": "@dbg_mfd_screen",
            "htmlPath": "local://local/vehicles/common/pillar_pod_gauges/mfd.html",
            "displayWidth":384,
            "displayHeight":512,
            "startPage":"$dbg_mfd_page",
            "nightBrightness":"$dbg_mfd_night",
        }},
        "displayData": {{
            "electrics": [
                "dbg_mfd_page", "turboBoost", "superchargerBoost", "rpm", "maxrpm", "oiltemp", "watertemp",
                "fuel", "fuelVolume", "lowfuel", "wheelspeed", "gear", "checkengine", "parkingbrake",
                "ignitionLevel", "lights", "lowhighbeam",
            ],
            "customModules": [
                ["moduleName", "property"],
                ["dbgAmbient", "light"],
                ["dbgAmbient", "maxBoost"],
                ["dbgAmbient", "egt"],
                ["dbgAmbient", "mfd"],
            ],
        }},
    }},
    "flexbodies": [
        ["mesh", "[group]:", "nonFlexMaterials"],
{chr(10).join(fb)}
    ],
    //page button: click it in the cabin, or bind "Display: next page" in the controls
    "triggers2":[
        ["id", "idRef:", "idX:", "idY:", "type", "size", "baseRotation", "rotation", "translation", "baseTranslation"],
{chr(10).join(trig)}
    ],
    "actionsEnabled": [
        ["id"],
        ["dbgMfdNextPage"],
    ],
    "triggerEventLinks2":[
        ["triggerId:triggers2", "triggerInput", "inputAction"],
{chr(10).join(links)}
    ],
}},
'''
# digital cluster: a part for each of the car's own Gauges slots (no Additional Modification needed).
# Touching the page panel on the right of the screen, or the "Display: next page" binding, flips pages.
CLUSTER_VARS='''        ["$dbg_cluster_page", "range", "", "Gauges", 0, 0, 5, "Digital Cluster: First Page", "Page shown at start on the right of the cluster: 0 boost, 1 tyres, 2 engine, 3 brakes, 4 g-force, 5 trip", {"stepDis":1}],
        ["$dbg_cluster_night", "range", "%", "Gauges", 25, 3, 100, "Digital Cluster: Night Brightness", "Cluster brightness at night or with the headlights on", {"stepDis":1}],'''
for slot,kind,sx,meshes in CAR.get("CLUSTER",()):
    tx,ty,tz=CAR["CLUSTER_TOUCH"][kind]; n1,n2,n3=CAR["TRIGGER_NODES"][1]
    fb="\n".join('        ["%s", ["%s"]],'%(m,GROUP) for m in meshes)
    name="Pillar Pod Digital Cluster" + (" (Race Dash)" if kind=="race" else "")
    out+=f'''"{slot}_dbg_cluster": {{
    "information":{{
        "authors":"Kristof",
        "name":"{name}",
        "value":650,
    }},
    "slotType" : "{slot}",
    "variables": [
        ["name", "type", "unit", "category", "default", "min", "max", "title", "description"],
{CLUSTER_VARS}
    ],
    "controller": [
        ["fileName"],
        ["gauges/customModules/dbgCluster"],
        ["gauges/genericGauges", {{"name":"dbgClusterScreen"}}],
    ],
    "dbgClusterScreen": {{
        "configuration": {{
            "materialName": "@dbg_cluster_screen",
            "htmlPath": "local://local/vehicles/common/pillar_pod_gauges/cluster.html",
            "displayWidth":1024,
            "displayHeight":272,
            "startPage":"$dbg_cluster_page",
            "nightBrightness":"$dbg_cluster_night",
            "shiftAt":0.92,
        }},
        "displayData": {{
            "electrics": [
                "dbg_mfd_page", "turboBoost", "superchargerBoost", "rpm", "maxrpm", "oiltemp", "watertemp",
                "fuel", "fuelVolume", "lowfuel", "wheelspeed", "gear", "checkengine", "parkingbrake",
                "ignitionLevel", "lights", "lowhighbeam",
            ],
            "customModules": [
                ["moduleName", "property"],
                ["dbgCluster", "light"],
                ["dbgCluster", "maxBoost"],
                ["dbgCluster", "egt"],
                ["dbgCluster", "mfd"],
            ],
        }},
    }},
    "flexbodies": [
        ["mesh", "[group]:", "nonFlexMaterials"],
{fb}
    ],
    //touch the page panel on the right of the screen to flip pages
    "triggers2":[
        ["id", "idRef:", "idX:", "idY:", "type", "size", "baseRotation", "rotation", "translation", "baseTranslation"],
        ["dbg_cluster_page", "{n1}","{n2}","{n3}", "sphere", 0.04, {{"x":0,"y":0,"z":0}},{{"x":0,"y":0,"z":0}},{{"x":0,"y":0,"z":0}},{{"x":0,"y":0,"z":0}}, {{"baseTranslationGlobal":{{"x":{sx*tx:.4f},"y":{ty:.4f},"z":{tz:.4f}}}}}],
    ],
    "actionsEnabled": [
        ["id"],
        ["dbgMfdNextPage"],
    ],
    "triggerEventLinks2":[
        ["triggerId:triggers2", "triggerInput", "inputAction"],
        ["dbg_cluster_page", "action0", "dbgMfdNextPage"],
    ],
}},
'''
out+='}\n'
open(args.out,'w').write(out)
print(len(re.findall(r'^"%s_'%P,out,re.M)),'parts; braces',out.count('{'),out.count('}'),'brackets',out.count('['),out.count(']'))
meshes=set(re.findall(r'\["(dbg[\w]+)", \["%s"\]'%GROUP,out)); print(len(meshes),'meshes')
