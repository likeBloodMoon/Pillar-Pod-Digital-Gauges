import re,sys
POS={ # variant: (boost position, oil position) -> ((x,y,z),yaw)
 "std":(((0.5749,-0.3246,1.0758),24.8),((0.5397,-0.2291,1.1372),25.7)),
 "stripped":(((0.5823,-0.3407,1.0756),24.8),((0.5473,-0.2448,1.1393),25.7)),
 "cage":(((0.5175,-0.2189,1.0961),23.8),((0.4972,-0.1483,1.1426),25.2))}
SIZE={"std":"80","stripped":"80","cage":"65"}   # gauge size per mounting, percent of full size (the cage bar is much closer to the driver)
NAMES={"std":"A-Pillar, Standard Interior","stripped":"A-Pillar, Stripped / Race / Rally Interior","cage":"Roll Cage Bar"}
BOOST_CFG='''            "materialName": "@dbg_screen",
            "htmlPath": "local://local/vehicles/common/digital_boost_gauge/screen.html",
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
            "htmlPath": "local://local/vehicles/common/digital_boost_gauge/screen.html",
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
out='''{
//Digital pillar gauges for the Covet.
//  Additional Modification -> Digital Pillar Gauges
//      Boost Gauge:    empty, or one entry per interior type (standard / stripped / roll cage, LHD or RHD)
//      Oil Temp Gauge: empty, or one entry per interior type
//Fit one or both. Boost sits in the lower position, oil temp above it. Every entry has its own
//position and its own pod shape, so pick the one that matches the car's interior.
"covet_digital_boost_gauge_pillar": {
    "information":{
        "authors":"Kristof",
        "name":"Digital Pillar Gauges",
        "value":0,
    },
    "slotType" : "covet_mod",
    "slots2": [
        ["name",            "allowTypes",        "denyTypes", "default",              "description"],
        ["covet_dbg_boost", ["covet_dbg_boost"], [],          "covet_dbg_boost_auto", "Boost Gauge"],
        ["covet_dbg_oil",   ["covet_dbg_oil"],   [],          "",                     "Oil Temp Gauge"],
    ],
    //ambient light for automatic display dimming (shared by both gauges)
    "controller": [
        ["fileName"],
        ["gauges/customModules/dbgAmbient"],
    ],
},
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
GAUGES=(("covet_dbg_boost","Boost","dbgGauge",BOOST_CFG,BOOST_VARS,["turboBoost","superchargerBoost","engineRunning","rpm","maxrpm","ignitionLevel","lights","lowhighbeam"],"dbg_pod","dbg_screen"),
        ("covet_dbg_oil","Oil Temp","dbgOilGauge",OIL_CFG,OIL_VARS,["oiltemp","ignitionLevel","lights","lowhighbeam"],"dbg_pod2","dbg_oil_screen"))
for gi,(slot,gname,ctrl,cfg,gvars,electrics,pod,screen) in enumerate(GAUGES):
    el="\n".join('                "%s",'%e for e in electrics)
    FINS=(("black","","","dbg_gauge","","black"),("silver","_silver",", Silver","dbg_gauge_silver","_w","white"))
    SIDES=(("lhd",1,"","LHD"),("rhd",-1,"_rhd","RHD"))
    # automatic mounting: all six mountings' meshes are fitted; the mod's script shows the matching one
    for fin,fkey,fname,bezel,scr_suffix,face in FINS:
        fb="        //meshes for every mounting (A-F); dbgAmbient.lua hides all but the one matching the car's interior\n"
        lines=[]
        for code,key,sx in (("A","std",1),("B","stripped",1),("C","cage",1),("D","std",-1),("E","stripped",-1),("F","cage",-1)):
            (x,y,z),yaw=POS[key][gi]
            pr='{"pos":{"x":%g,"y":%g,"z":%g},"rot":{"x":0,"y":0,"z":%g}}'%(sx*x,y,z,sx*yaw)
            base="dbgv%s%d"%(code,gi+1)
            k="k" if fin=="black" else "s"
            lines+=['        ["%spod", ["covet_dash"],[],%s],'%(base,pr),'        ["%sbz%s", ["covet_dash"],[],%s],'%(base,k,pr),'        ["%ssc%s", ["covet_dash"],[],%s],'%(base,k,pr)]
        out+=part(f"{slot}_auto{fkey}", f"{gname} - Automatic Mounting{fname}", slot, gvars, ctrl, cfg+'\n            "face":"%s",'%face, el, fb+"\n".join(lines))
    for (fin,fkey,fname,bezel,scr_suffix,face),(side,sx,suffix,label) in [(f,s) for f in FINS for s in SIDES]:
        for key in ("std","stripped","cage"):
            (x,y,z),yaw=POS[key][gi]
            cfgf=cfg+'\n            "face":"%s",'%face
            pr='{"pos":{"x":%g,"y":%g,"z":%g},"rot":{"x":0,"y":0,"z":%g}}'%(sx*x,y,z,sx*yaw)
            fb=f'''        //pos = centre of the gauge face. The pod mesh is shaped for exactly this spot.
        ["{pod}_{key}{suffix}", ["covet_dash"],[],{pr}],
        ["{bezel}_{SIZE[key]}", ["covet_dash"],[],{pr}],
        ["{screen}{scr_suffix}_{SIZE[key]}", ["covet_dash"],[],{pr}],'''
            out+=part(f"{slot}_{key}_{side}{fkey}", f"{gname} - {NAMES[key]} ({label}){fname}", slot, gvars, ctrl, cfgf, el, fb)

out+='}\n'
open(sys.argv[1],'w').write(out)
print(len(re.findall(r'^"covet_',out,re.M)),'parts; braces',out.count('{'),out.count('}'),'brackets',out.count('['),out.count(']'))
meshes=set(re.findall(r'\["(dbg[\w]+)", \["covet_dash"\]',out)); print(sorted(meshes))
