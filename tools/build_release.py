"""Builds the release tree and zip from the working files (renames the working folder to the release name)."""
import json, os, shutil, subprocess, zipfile
S='mod/'; R='release/pillar_pod_gauges/'
shutil.rmtree(R, ignore_errors=True)
C=R+'vehicles/common/pillar_pod_gauges/'
os.makedirs(C); os.makedirs(R+'vehicles/covet'); os.makedirs(R+'lua/vehicle/controller/gauges/customModules')
src=S+'vehicles/common/digital_boost_gauge/'
for f in os.listdir(src):
    if f.endswith('.png'): shutil.copy(src+f, C+f)
d=open(src+'digital_boost_gauge.dae').read().replace('<author>digital_boost_gauge</author>','<author>Pillar Pod Digital Gauges</author>')
open(C+'pillar_pod_gauges.dae','w').write(d)
m=open(src+'main.materials.json').read().replace('/vehicles/common/digital_boost_gauge/','/vehicles/common/pillar_pod_gauges/'); json.loads(m)
open(C+'main.materials.json','w').write(m)
h=open(src+'screen.html').read()
a=h.index("  // one log line whenever the dimming inputs change"); b=h.index("  var ign = e.ignitionLevel;"); h=h[:a]+h[b:]
a=h.index("    if (typeof beamng !== \"undefined\" && beamng.sendEngineLua) {\n      beamng.sendEngineLua(\"log('I','digital_boost_gauge','auto scale"); b=h.index("    }\n",a)+6; h=h[:a]+h[b:]
h=h.replace('var lastDimState = "";\n','').replace("htmlTexture.digital_boost_gauge","htmlTexture.pillar_pod_gauges").replace("<title>digital_boost_gauge</title>","<title>pillar_pod_gauges</title>")
assert 'digital_boost_gauge' not in h and 'lastDimState' not in h
open(C+'screen.html','w').write(h)
j=open(S+'vehicles/covet/covet_digital_boost_gauge.jbeam').read()
j=j.replace('local://local/vehicles/common/digital_boost_gauge/screen.html','local://local/vehicles/common/pillar_pod_gauges/screen.html')
j=j.replace('//Digital pillar gauges for the Covet.','//Pillar Pod Digital Gauges - parts for the Ibishu Covet.')
assert 'digital_boost_gauge' not in j.replace('covet_digital_boost_gauge_pillar','')
open(R+'vehicles/covet/covet_pillar_pod_gauges.jbeam','w').write(j)
shutil.copy(S+'lua/vehicle/controller/gauges/customModules/dbgAmbient.lua', R+'lua/vehicle/controller/gauges/customModules/')
z='release/pillar_pod_gauges.zip'
if os.path.exists(z): os.remove(z)
subprocess.check_call(['zip','-r','-q','../pillar_pod_gauges.zip','vehicles','lua'],cwd=R)
zz=zipfile.ZipFile(z); print(len([n for n in zz.namelist() if not n.endswith('/')]),'files, test:',zz.testzip(), os.path.getsize(z),'bytes')
