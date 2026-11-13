"""Bake the printed face textures (dbg_face_<black|white>_<boost|oil|fuel>_b.color.png) with headless
Chrome, using bake_faceplates.html and the display page's own drawing code.

    pip install playwright
    python tools/bake_faces.py [path to chrome]
"""
import asyncio, os, shutil, sys
from playwright.async_api import async_playwright
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
OUT = os.path.join(ROOT, 'vehicles/common/pillar_pod_gauges')
CHROME = sys.argv[1] if len(sys.argv) > 1 else shutil.which('google-chrome') or shutil.which('chromium')

async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path=CHROME, args=['--allow-file-access-from-files'])
        pg = await b.new_page(viewport={'width': 512, 'height': 512})
        for face in ('boost', 'oil', 'fuel'):
            for fin in ('black', 'white'):
                await pg.goto('about:blank')                 # a hash-only change would not reload the page
                await pg.goto('file://' + ROOT + '/tools/bake_faceplates.html#' + face + ',' + fin)
                await pg.wait_for_timeout(700)
                path = os.path.join(OUT, 'dbg_face_%s_%s_b.color.png' % (fin, face))
                await pg.screenshot(path=path, clip={'x': 0, 'y': 0, 'width': 512, 'height': 512})
                print(path)
        await b.close()

asyncio.run(main())
