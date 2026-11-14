"""Render the README's demo animation: a boost and an oil temperature gauge going through a short
drive. Ignition on (start-up sweep), a pull to full boost with the shift light, lift off (peak
recall), then ignition off (shut-down sweep).

    python tools/render_demo_gif.py <repo root> <out.gif>

Needs Python with playwright and Pillow, and Google Chrome (CHROME=path if it is not google-chrome /
chromium on the PATH). The page clock is replaced by a fake one that moves exactly one frame per
picture, so the animation comes out the same every time and doesn't depend on how fast the machine
renders. Page timers are switched off, the way the game can stop them; everything runs through
updateData(), as in the game.
"""
import asyncio, io, os, shutil, sys
from PIL import Image, ImageChops, ImageDraw, ImageFilter

FPS = 20
SIZE = 220                      # one gauge in the GIF, in pixels
GAP = 20
BG = (19, 20, 22)

BOOST = {"source": "boost", "minValue": -10, "maxValue": 0, "zeroValue": 0, "zeroLed": 6, "warnValue": 0,
         "uiUnitPressure": "psi", "peakRecall": True, "recallTime": 2.0, "shiftLight": 1, "face": "black"}
OIL = {"source": "oiltemp", "decimals": 0, "minValue": 50, "maxValue": 150, "titleLabel": "OIL TEMP",
       "warnValue": 130, "uiUnitTemperature": "c", "face": "black"}
GAUGES = [("boost", BOOST), ("oil", OIL)]


def lerp(a, b, u):
    u = max(0.0, min(1.0, u))
    return a + (b - a) * u


def ease(u):
    u = max(0.0, min(1.0, u))
    return u * u * (3 - 2 * u)


def state(t):
    """Electrics at time t (seconds) of the scripted drive."""
    ign = 0 if t < 0.4 or t >= 7.6 else 2
    running = 0.9 <= t < 7.6
    rpm = 0.0
    boost = 0.0
    if running:
        rpm, boost = 900.0, -9.5                                 # idle
        if 2.4 <= t < 5.0:                                       # the pull
            u = ease((t - 2.4) / 2.4)
            rpm, boost = lerp(1500, 7150, u), lerp(-4, 17.2, ease((t - 2.4) / 1.4))
        elif 5.0 <= t < 5.6:                                     # lift off
            u = ease((t - 5.0) / 0.6)
            rpm, boost = lerp(7150, 2600, u), lerp(17.2, -12, u)
        elif t >= 5.6:
            rpm, boost = lerp(2600, 950, (t - 5.6) / 1.2), lerp(-12, -9.5, (t - 5.6) / 1.2)
    e = {"ignitionLevel": ign, "engineRunning": 1 if running else 0, "rpm": rpm, "maxrpm": 7200,
         "turboBoost": boost, "oiltemp": 96 + max(0.0, t - 2.4) * 1.5, "watertemp": 90, "lights": 0}
    mod = {"light": 1, "maxBoost": 17.5, "egt": 600, "resets": 0}
    return {"electrics": e, "customModules": {"dbgAmbient": mod}}


SCRIPT_END = 8.9                  # 1.3 s dark after the shut-down sweep, then the GIF loops


def chrome():
    return os.environ.get("CHROME") or shutil.which("google-chrome") or shutil.which("chromium") or shutil.which("chromium-browser")


def bezel(face):
    """Round the square render off into a gauge: crop to the face, add a dark bezel ring."""
    s = SIZE * 2                                             # draw at 2x, scale down for smooth edges
    g = face.resize((s, s), Image.LANCZOS)
    out = Image.new("RGB", (s, s), BG)
    mask = Image.new("L", (s, s), 0)
    ImageDraw.Draw(mask).ellipse((24, 24, s - 24, s - 24), fill=255)
    out.paste(g, (0, 0), mask)
    d = ImageDraw.Draw(out)
    d.ellipse((4, 4, s - 4, s - 4), outline=(52, 54, 58), width=22)
    d.ellipse((4, 4, s - 4, s - 4), outline=(78, 80, 86), width=3)
    return out.resize((SIZE, SIZE), Image.LANCZOS)


async def render(root, out_path):
    from playwright.async_api import async_playwright
    pages = os.path.join(os.path.abspath(root), "vehicles/common/pillar_pod_gauges")
    errors = []
    async with async_playwright() as p:
        browser = await p.chromium.launch(executable_path=chrome(), args=["--allow-file-access-from-files"])
        tabs = []
        for face, cfg in GAUGES:
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
            tabs.append((pg, printed))

        frames = []
        n = int(SCRIPT_END * FPS)
        sub = 2                                              # two updates per frame: 50 Hz, like the game's GFX steps
        for i in range(n):
            t = i / FPS
            for k in range(sub):
                tt = t + k / (FPS * sub)
                for pg, _ in tabs:
                    await pg.evaluate("([d, ms]) => { window.__t = ms; updateData(d); }", [state(tt), 1000 + tt * 1000])
            row = Image.new("RGB", (SIZE * len(tabs) + GAP * (len(tabs) + 1), SIZE + GAP * 2), BG)
            for j, (pg, printed) in enumerate(tabs):
                shot = await pg.screenshot(type="png")
                emissive = Image.open(io.BytesIO(shot)).convert("RGB")
                glow = emissive.filter(ImageFilter.GaussianBlur(6)).point(lambda v: int(v * 0.45))
                face = ImageChops.add(ImageChops.add(printed, emissive), glow)
                row.paste(bezel(face), (GAP + j * (SIZE + GAP), GAP))
            frames.append(row)
            if i % 40 == 0:
                print("frame %d/%d" % (i, n))
        await browser.close()

    pal = [f.quantize(colors=64, method=Image.MEDIANCUT, dither=Image.NONE) for f in frames]
    pal[0].save(out_path, save_all=True, append_images=pal[1:], duration=int(1000 / FPS), loop=0, optimize=True, disposal=1)
    print("wrote %s (%d frames, %.0f KB)" % (out_path, len(frames), os.path.getsize(out_path) / 1024))
    for e in errors:
        print("page error:", e)
    return errors


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    sys.exit(1 if asyncio.run(render(sys.argv[1], sys.argv[2])) else 0)
