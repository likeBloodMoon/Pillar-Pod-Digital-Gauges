"""Render the colour-themes animation: five round gauges, each a different type in a different colour,
going through the same short drive as the README demo. Ignition on (start-up sweep), a pull to full
boost (the tachometer's shift light, boost peak recall, the oil gauge passing its warning limit in
red), lift off, then ignition off (shut-down sweep).

    python tools/render_themes_gif.py <repo root> <out.gif>

Needs Python with playwright and Pillow, and Google Chrome (CHROME=path if it is not google-chrome /
chromium on the PATH). Uses the same fake clock and compositing as render_demo_gif.py, so it comes
out the same every time.
"""
import asyncio, io, os, sys
from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from render_demo_gif import BG, FPS, GAP, SCRIPT_END, SIZE, bezel, chrome, ease, lerp, state as base_state

CAPTION = 46                    # caption strip under each gauge, in pixels

BOOST = {"source": "boost", "minValue": -10, "maxValue": 0, "zeroValue": 0, "zeroLed": 6, "warnValue": 0,
         "uiUnitPressure": "psi", "peakRecall": True, "recallTime": 2.0, "shiftLight": 0}
TACH = {"source": "rpm", "minValue": 0, "maxValue": 0, "titleLabel": "RPM", "shiftLight": 1, "shiftAt": 96, "peakHold": 1.5}
OIL = {"source": "oiltemp", "decimals": 0, "minValue": 50, "maxValue": 150, "titleLabel": "OIL TEMP",
       "warnValue": 105, "uiUnitTemperature": "c"}          # a low warning limit, so the red warning digits show
WATER = {"source": "watertemp", "decimals": 0, "minValue": 40, "maxValue": 130, "titleLabel": "COOLANT",
         "warnValue": 110, "uiUnitTemperature": "c"}
EGT = {"source": "egt", "decimals": 0, "minValue": 200, "maxValue": 1000, "titleLabel": "EGT", "warnValue": 900,
       "printedDigits": 0, "uiUnitTemperature": "c"}
# (caption, printed face, configuration with its colour theme)
GAUGES = [
    ("White · Tachometer", "oil", dict(TACH, theme=1)),
    ("Amber · Oil temp", "oil", dict(OIL, theme=2)),
    ("Purple · Boost", "boost", dict(BOOST, theme=4)),
    ("Blue · Coolant", "oil", dict(WATER, theme=3)),
    ("Super green · EGT", "egt", dict(EGT, theme=5)),
]


def state(t):
    """The README demo's drive, plus oil, coolant and exhaust temperatures that move with the pull."""
    d = base_state(t)
    e, mod = d["electrics"], d["customModules"]["dbgAmbient"]
    pull = ease((t - 2.4) / 2.6) if t >= 2.4 else 0.0
    cool = ease((t - 5.0) / 2.6) if t >= 5.0 else 0.0
    e["oiltemp"] = 97 + 11 * pull - 4 * cool                 # passes the 105 deg C warning during the pull
    e["watertemp"] = 88 + 5 * pull - 2 * cool
    mod["egt"] = 430 + 390 * pull - 250 * cool if e["engineRunning"] else 0
    return d


def caption_font():
    """Barlow Semi Condensed from the mod (stored as woff2, which Pillow can't read: unpacked with
    fontTools), or Pillow's default font if fontTools/brotli aren't installed."""
    src = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..",
                       "vehicles/common/pillar_pod_gauges/fonts/barlow-semi-condensed-latin-600-normal.woff2")
    try:
        from fontTools.ttLib import TTFont
        f = TTFont(src)
        f.flavor = None
        buf = io.BytesIO()
        f.save(buf)
        buf.seek(0)
        return ImageFont.truetype(buf, 19)
    except Exception as e:
        print("caption font: %s, using the default font" % e)
        return ImageFont.load_default()


async def render(root, out_path):
    from playwright.async_api import async_playwright
    pages = os.path.join(os.path.abspath(root), "vehicles/common/pillar_pod_gauges")
    errors = []
    font = caption_font()
    async with async_playwright() as p:
        browser = await p.chromium.launch(executable_path=chrome(), args=["--allow-file-access-from-files"])
        tabs = []
        for label, face, cfg in GAUGES:
            pg = await browser.new_page(viewport={"width": 512, "height": 512})
            pg.on("pageerror", lambda e: errors.append(str(e)))
            await pg.add_init_script("""
                window.setInterval = function () { return 0; };
                window.__t = 1000;
                performance.now = function () { return window.__t; };
                Date.now = function () { return window.__t; };
            """)
            await pg.goto("file://" + os.path.join(pages, "screen.html"))
            await pg.evaluate("() => document.fonts.ready")
            await pg.evaluate("c => setup(c)", cfg)
            printed = Image.open(os.path.join(pages, "dbg_face_black_%s_b.color.png" % face)).convert("RGB")
            tabs.append((pg, printed, label))

        width = SIZE * len(tabs) + GAP * (len(tabs) + 1)
        strip = Image.new("RGB", (width, CAPTION), BG)          # the captions never change: draw them once
        d = ImageDraw.Draw(strip)
        for j, (_, _, label) in enumerate(tabs):
            cx = GAP + j * (SIZE + GAP) + SIZE / 2
            d.text((cx, 14), label, font=font, fill=(205, 207, 212), anchor="mt")

        frames = []
        n = int(SCRIPT_END * FPS)
        sub = 2
        for i in range(n):
            t = i / FPS
            for k in range(sub):
                tt = t + k / (FPS * sub)
                for pg, _, _ in tabs:
                    await pg.evaluate("([d, ms]) => { window.__t = ms; updateData(d); }", [state(tt), 1000 + tt * 1000])
            row = Image.new("RGB", (width, SIZE + GAP + CAPTION), BG)
            for j, (pg, printed, _) in enumerate(tabs):
                shot = await pg.screenshot(type="png")
                emissive = Image.open(io.BytesIO(shot)).convert("RGB")
                glow = emissive.filter(ImageFilter.GaussianBlur(6)).point(lambda v: int(v * 0.45))
                face = ImageChops.add(ImageChops.add(printed, emissive), glow)
                row.paste(bezel(face), (GAP + j * (SIZE + GAP), GAP))
            row.paste(strip, (0, SIZE + GAP))
            frames.append(row)
            if i % 40 == 0:
                print("frame %d/%d" % (i, n))
        await browser.close()

    # one shared palette for every frame keeps the colours steady and the file small
    sample = frames[::8]
    sheet = Image.new("RGB", (frames[0].width, frames[0].height * len(sample)))
    for k, f in enumerate(sample):
        sheet.paste(f, (0, k * f.height))
    pal0 = sheet.quantize(colors=160, method=Image.MEDIANCUT, dither=Image.NONE)
    pal = [f.quantize(palette=pal0, dither=Image.NONE) for f in frames]
    pal[0].save(out_path, save_all=True, append_images=pal[1:], duration=int(1000 / FPS), loop=0, optimize=True, disposal=1)
    print("wrote %s (%d frames, %.0f KB)" % (out_path, len(frames), os.path.getsize(out_path) / 1024))
    for e in errors:
        print("page error:", e)
    return errors


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    sys.exit(1 if asyncio.run(render(sys.argv[1], sys.argv[2])) else 0)
