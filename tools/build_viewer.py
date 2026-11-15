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


def build() -> dict:
    viewer = VIEWER.read_text(encoding="utf-8").rstrip() + "\n"
    out = {}
    for template, target in OUTPUTS:
        text = template.read_text(encoding="utf-8")
        if text.count(MARK) != 1:
            raise SystemExit(f"{template.relative_to(ROOT)}: needs exactly one {MARK}")
        text = text.replace(MARK, viewer.rstrip("\n"))
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
