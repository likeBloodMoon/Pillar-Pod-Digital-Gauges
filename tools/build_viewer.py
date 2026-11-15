"""Build the event history viewer into its two homes:

    ui/modules/apps/PillarPodEvents/app.js   the in-game Event History app
    viewer/index.html                         the PC page (works offline, from a file)

Both inline viewer/viewer.js, so there is one copy of the viewer to edit.

    python tools/build_viewer.py           write the outputs
    python tools/build_viewer.py --check   exit 1 if an output is out of date (validate_assets runs this)
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VIEWER = ROOT / "viewer" / "viewer.js"
OUTPUTS = [
    (ROOT / "viewer" / "app.template.js", ROOT / "ui" / "modules" / "apps" / "PillarPodEvents" / "app.js"),
    (ROOT / "viewer" / "index.template.html", ROOT / "viewer" / "index.html"),
]
MARK = "/*@VIEWER@*/"
FONTS = "/*@FONTS@*/"                     # the PC page embeds the mod's font so it works offline
FONT_DIR = ROOT / "vehicles" / "common" / "pillar_pod_gauges" / "fonts"


def font_css() -> str:
    import base64
    rules = []
    for w in (500, 600, 700):
        data = base64.b64encode((FONT_DIR / f"barlow-semi-condensed-latin-{w}-normal.woff2").read_bytes()).decode("ascii")
        rules.append('@font-face{font-family:"Barlow SC";font-weight:%d;src:url(data:font/woff2;base64,%s) format("woff2");}' % (w, data))
    return "\n".join(rules)


def build() -> dict:
    viewer = VIEWER.read_text(encoding="utf-8").rstrip() + "\n"
    out = {}
    for template, target in OUTPUTS:
        text = template.read_text(encoding="utf-8")
        if text.count(MARK) != 1:
            raise SystemExit(f"{template.relative_to(ROOT)}: needs exactly one {MARK}")
        text = text.replace(MARK, viewer.rstrip("\n"))
        if FONTS in text:
            text = text.replace(FONTS, font_css())
        out[target] = text
    return out


def main() -> int:
    check = "--check" in sys.argv
    stale = []
    for target, text in build().items():
        current = target.read_text(encoding="utf-8") if target.exists() else None
        if current == text:
            continue
        if check:
            stale.append(str(target.relative_to(ROOT)))
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(text, encoding="utf-8", newline="\n")
            print("wrote", target.relative_to(ROOT))
    if stale:
        print("out of date (run python tools/build_viewer.py):", ", ".join(stale))
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
