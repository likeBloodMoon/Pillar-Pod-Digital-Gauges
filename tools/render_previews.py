"""Render every screen of the mod with fixed sample data, so changes to the screen pages can be
reviewed as pictures: the round gauges (composited over their printed face, like the material
does), the multi-function display's pages and the digital cluster's pages.

    python tools/render_previews.py <repo root> <out dir>            render one version
    python tools/render_previews.py --compare <before> <after> <out>  side-by-side sheets + changes.md

Needs Python with playwright and Pillow, and Google Chrome (pass CHROME=path if it is not
google-chrome / chromium on the PATH). Page timers are switched off while rendering, the way the
game can stop them, and every screen is driven through updateData() until it settles.
"""
import asyncio, json, os, shutil, sys
from PIL import Image, ImageChops, ImageDraw

SETTLE = 1.2                     # seconds of updateData() calls after the start-up sweep, before each picture

E = {"turboBoost": 12.4, "rpm": 5200, "maxrpm": 7000, "engineRunning": 1, "ignitionLevel": 2, "oiltemp": 104,
     "watertemp": 92, "fuel": 0.42, "fuelVolume": 21.3, "wheelspeed": 31.5, "gear": 4, "lights": 0,
     "checkengine": 0, "parkingbrake": 0, "lowfuel": 0}
MFD = {"ws": {"FL": 31.2, "FR": 31.0, "RL": 31.4, "RR": 30.9}, "tp": {"FL": 221, "FR": 219, "RL": 205, "RR": 214},
       "tt": {"FL": 72, "FR": 88, "RL": 61, "RR": 64}, "bt": {"FL": 512, "FR": 498, "RL": 260, "RR": 301},
       "glat": 0.84, "glon": -0.32, "range": 243, "envT": 18}
MOD = {"light": 1, "maxBoost": 17.5, "egt": 712, "resets": 0, "mfd": MFD}
DATA = {"electrics": E, "customModules": {"dbgAmbient": MOD, "dbgCluster": MOD}}

BOOST = {"source": "boost", "minValue": -10, "maxValue": 0, "zeroValue": 0, "zeroLed": 6, "warnValue": 0, "recallTime": 0}
# (name, printed face, finish, configuration)
GAUGES = [
    ("gauge_boost_psi", "boost", "black", dict(BOOST, uiUnitPressure="psi")),
    ("gauge_boost_bar", "boost", "black", dict(BOOST, uiUnitPressure="bar")),
    ("gauge_oil_c", "oil", "black", {"source": "oiltemp", "decimals": 0, "minValue": 50, "maxValue": 150, "titleLabel": "OIL TEMP", "warnValue": 130}),
    ("gauge_oil_f_silver", "oil", "white", {"source": "oiltemp", "decimals": 0, "minValue": 50, "maxValue": 150, "titleLabel": "OIL TEMP", "warnValue": 130, "uiUnitTemperature": "f"}),
    ("gauge_coolant", "oil", "black", {"source": "watertemp", "decimals": 0, "minValue": 40, "maxValue": 130, "titleLabel": "COOLANT", "warnValue": 110}),
    ("gauge_egt_f", "egt", "black", {"source": "egt", "decimals": 0, "minValue": 200, "maxValue": 1000, "titleLabel": "EGT", "warnValue": 900, "printedDigits": 0, "uiUnitTemperature": "f"}),
    ("gauge_fuel", "fuel", "black", {"source": "fuel", "minValue": 0, "maxValue": 100, "warnLow": 1, "titleLabel": "FUEL", "warnValue": 10}),
]
MFD_PAGES = ["boost", "tyres", "engine", "brakes", "gforce"]
CLUSTER_PAGES = ["boost", "tyres", "engine", "brakes", "gforce", "trip"]


def chrome():
    return os.environ.get("CHROME") or shutil.which("google-chrome") or shutil.which("chromium") or shutil.which("chromium-browser")


async def render(root, out):
    from playwright.async_api import async_playwright
    pages = os.path.join(os.path.abspath(root), "vehicles/common/pillar_pod_gauges")
    os.makedirs(out, exist_ok=True)
    errors = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(executable_path=chrome(), args=["--allow-file-access-from-files"])

        async def run(html, size, cfg, data):
            pg = await browser.new_page(viewport={"width": size[0], "height": size[1]})
            pg.on("pageerror", lambda e: errors.append("%s: %s" % (html, e)))
            await pg.add_init_script("window.setInterval = function () { return 0; };")
            await pg.goto("file://" + os.path.join(pages, html))
            await pg.evaluate("c => setup(c)", cfg)
            # run until the start-up splash / sweep is over, then let the readings settle
            t0 = await pg.evaluate("performance.now()"); t_ready = None
            while True:
                await pg.evaluate("d => updateData(d)", data)
                await pg.wait_for_timeout(16)
                now = await pg.evaluate("performance.now()")
                if t_ready is None and await pg.evaluate("typeof bootT === 'undefined' || bootT < 0") and now - t0 > 200:
                    t_ready = now
                if t_ready is not None and now - t_ready > SETTLE * 1000:
                    break
                if now - t0 > 15000:
                    errors.append("%s: did not finish starting up within 15 s" % html); break
            path = os.path.join(out, "_shot.png")
            await pg.screenshot(path=path)
            await pg.close()
            return Image.open(path).convert("RGB")

        for name, face, fin, cfg in GAUGES:
            if not os.path.exists(os.path.join(pages, "dbg_face_%s_%s_b.color.png" % (fin, face))):
                continue                         # an older version without this face
            cfg = dict(cfg, face="white" if fin == "white" else "black")
            emissive = await run("screen.html", (512, 512), cfg, DATA)
            printed = Image.open(os.path.join(pages, "dbg_face_%s_%s_b.color.png" % (fin, face))).convert("RGB")
            ImageChops.add(printed, emissive).save(os.path.join(out, name + ".png"))
        for i, page in enumerate(MFD_PAGES):
            (await run("mfd.html", (384, 512), {"startPage": i}, DATA)).save(os.path.join(out, "display_%d_%s.png" % (i, page)))
        if os.path.exists(os.path.join(pages, "cluster.html")):
            for i, page in enumerate(CLUSTER_PAGES):
                (await run("cluster.html", (1024, 272), {"startPage": i}, DATA)).save(os.path.join(out, "cluster_%d_%s.png" % (i, page)))
        await browser.close()
    os.remove(os.path.join(out, "_shot.png"))
    with open(os.path.join(out, "errors.json"), "w") as f:
        json.dump(errors, f, indent=1)
    for e in errors:
        print("page error:", e)
    return errors


def changed(a, b):
    """True when two renders differ by more than easing noise."""
    if a.size != b.size:
        return True
    # two renders of the same version are pixel-identical, so a handful of clearly different pixels
    # is already a real change (a recoloured unit label is a few hundred)
    d = ImageChops.difference(a, b).convert("L").point(lambda v: 255 if v > 48 else 0)
    return sum(d.histogram()[255:]) > 20


def compare(before, after, out):
    os.makedirs(out, exist_ok=True)
    names = sorted(n for n in os.listdir(after) if n.endswith(".png"))
    rows = []
    for n in names:
        b = os.path.join(before, n)
        A = Image.open(os.path.join(after, n)).convert("RGB")
        if not os.path.exists(b):
            rows.append((n, "new"))
            B = None
        else:
            B = Image.open(b).convert("RGB")
            rows.append((n, "changed" if changed(B, A) else "same"))
        w, h = A.size
        sheet = Image.new("RGB", (w * 2 + 30, h + 34), (30, 30, 30))
        dr = ImageDraw.Draw(sheet)
        dr.text((8, 10), "before", fill=(200, 200, 200)); dr.text((w + 38, 10), "after", fill=(200, 200, 200))
        if B is not None:
            sheet.paste(B, (0, 34))
        sheet.paste(A, (w + 30, 34))
        sheet.save(os.path.join(out, n))
    errors = []
    if os.path.exists(os.path.join(after, "errors.json")):
        errors = json.load(open(os.path.join(after, "errors.json")))
    lines = ["| Screen | |", "|---|---|"] + ["| `%s` | %s |" % (n[:-4], {"changed": "**changed**", "new": "**new**", "same": "no visible change"}[s]) for n, s in rows]
    if errors:
        lines += ["", "**JavaScript errors while rendering:**", ""] + ["- `%s`" % e for e in errors]
    with open(os.path.join(out, "changes.md"), "w") as f:
        f.write("\n".join(lines) + "\n")
    n_changed = sum(1 for _, s in rows if s != "same")
    print("%d of %d screens changed" % (n_changed, len(rows)))
    return errors


if __name__ == "__main__":
    if sys.argv[1] == "--compare":
        sys.exit(1 if compare(*sys.argv[2:5]) else 0)
    sys.exit(1 if asyncio.run(render(sys.argv[1], sys.argv[2])) else 0)
