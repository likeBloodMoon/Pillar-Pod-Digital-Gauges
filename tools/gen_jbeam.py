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
  AUTO=(("A","std",1),("B","stripped",1),("C","cage",1),("D","std",-1),("E","stripped",-1),("F","cage",-1))),
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
BOOST_CFG='''            "materialName": "@dbg_screen",
            "htmlPath": "local://local/vehicles/common/pillar_pod_gauges/screen.html",
            "displayWidth":512,
            "displayHeight":512,
            "source":"boost",
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
OIL_CFG='''            "materialName": "@dbg_oil_screen",
            "htmlPath": "local://local/vehicles/common/pillar_pod_gauges/screen.html",
            "displayWidth":512,
            "displayHeight":512,
            "source":"oiltemp",
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
AUTO_DEFAULT=P+"_dbg_boost_auto"
_rows=[['"name"','"allowTypes"','"denyTypes"','"default"','"description"'],
       ['"%s_dbg_boost"'%P,'["%s_dbg_boost"]'%P,'[]','"%s"'%AUTO_DEFAULT,'"Boost Gauge"'],
       ['"%s_dbg_oil"'%P,'["%s_dbg_oil"]'%P,'[]','""','"Oil Temp Gauge"']]
_w=[max(len(r[i]) for r in _rows)+1 for i in range(5)]
SLOTS2="\n".join("        ["+" ".join((c+",").ljust(_w[i]+1) if i<4 else c for i,c in enumerate(r))+"]," for r in _rows)
out=f'''{{
//Pillar Pod Digital Gauges - parts for the {CAR["label"]}.
//  Additional Modification -> Digital Pillar Gauges
//      Boost Gauge:    automatic mounting (black or silver), or a fixed mounting
//      Oil Temp Gauge: empty, automatic mounting, or a fixed mounting
//Fit one or both. Boost sits in the lower position, oil temp above it. The automatic parts pick
//the position that matches the car's interior; the fixed ones always use the position they name.
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
            ],
        }},
    }},
    "flexbodies": [
        ["mesh", "[group]:", "nonFlexMaterials"],
{fb}
    ],
}},
'''
GAUGES=((P+"_dbg_boost","Boost","dbgGauge",BOOST_CFG,BOOST_VARS,["turboBoost","superchargerBoost","engineRunning","rpm","maxrpm","ignitionLevel","lights","lowhighbeam"],"dbg_pod","dbg_screen"),
        (P+"_dbg_oil","Oil Temp","dbgOilGauge",OIL_CFG,OIL_VARS,["oiltemp","ignitionLevel","lights","lowhighbeam"],"dbg_pod2","dbg_oil_screen"))
for gi,(slot,gname,ctrl,cfg,gvars,electrics,pod,screen) in enumerate(GAUGES):
    el="\n".join('                "%s",'%e for e in electrics)
    FINS=(("black","","","dbg_gauge","","black"),("silver","_silver",", Silver","dbg_gauge_silver","_w","white"))
    SIDES=(("lhd",1,"","LHD"),("rhd",-1,"_rhd","RHD"))
    # automatic mounting: all six mountings' meshes are fitted; the mod's script shows the matching one
    for fin,fkey,fname,bezel,scr_suffix,face in FINS:
        fb="        //meshes for every mounting (%s); dbgAmbient.lua"%"".join(c for c,_,_ in CAR["AUTO"])+" hides all but the one matching the car's interior\n"
        lines=[]
        for code,key,sx in CAR["AUTO"]:
            (x,y,z),yaw=POS[key][gi]
            pr='{"pos":{"x":%g,"y":%g,"z":%g},"rot":{"x":0,"y":0,"z":%g}}'%(sx*x,y,z,sx*yaw)
            base="dbgv%s%d"%(code,gi+1)
            k="k" if fin=="black" else "s"
            lines+=['        ["%spod", ["%s"],[],%s],'%(base,GROUP,pr),'        ["%sbz%s", ["%s"],[],%s],'%(base,k,GROUP,pr),'        ["%ssc%s", ["%s"],[],%s],'%(base,k,GROUP,pr)]
        out+=part(f"{slot}_auto{fkey}", f"{gname} - Automatic Mounting{fname}", slot, gvars, ctrl, cfg+'\n            "face":"%s",'%face, el, fb+"\n".join(lines))
    for (fin,fkey,fname,bezel,scr_suffix,face),(side,sx,suffix,label) in [(f,s) for f in FINS for s in SIDES]:
        for key in POS:
            (x,y,z),yaw=POS[key][gi]
            cfgf=cfg+'\n            "face":"%s",'%face
            pr='{"pos":{"x":%g,"y":%g,"z":%g},"rot":{"x":0,"y":0,"z":%g}}'%(sx*x,y,z,sx*yaw)
            fb=f'''        //pos = centre of the gauge face. The pod mesh is shaped for exactly this spot.
        ["{pod}_{MESH[key]}{suffix}", ["{GROUP}"],[],{pr}],
        ["{bezel}_{SIZE[key]}", ["{GROUP}"],[],{pr}],
        ["{screen}{scr_suffix}_{SIZE[key]}", ["{GROUP}"],[],{pr}],'''
            out+=part(f"{slot}_{key}_{side}{fkey}", f"{gname} - {NAMES[key]} ({label}){fname}", slot, gvars, ctrl, cfgf, el, fb)

out+='}\n'
open(args.out,'w').write(out)
print(len(re.findall(r'^"%s_'%P,out,re.M)),'parts; braces',out.count('{'),out.count('}'),'brackets',out.count('['),out.count(']'))
meshes=set(re.findall(r'\["(dbg[\w]+)", \["%s"\]'%GROUP,out)); print(len(meshes),'meshes')
