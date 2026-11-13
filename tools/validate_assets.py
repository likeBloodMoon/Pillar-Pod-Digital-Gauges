#!/usr/bin/env python3
"""Static integrity checks for the Pillar Pod Digital Gauges mod.

Run from any directory:
    python tools/validate_assets.py
"""
from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
# one part file per supported car: (generator --car name, part file, root part)
CARS = (
    ("covet", ROOT / "vehicles/covet/covet_pillar_pod_gauges.jbeam", "covet_digital_boost_gauge_pillar"),
    ("bx", ROOT / "vehicles/bx/bx_pillar_pod_gauges.jbeam", "bx_pillar_pod_gauges"),
)
DAE = ROOT / "vehicles/common/pillar_pod_gauges/pillar_pod_gauges.dae"
MATERIALS = ROOT / "vehicles/common/pillar_pod_gauges/main.materials.json"
SCREEN = ROOT / "vehicles/common/pillar_pod_gauges/screen.html"
MFD_PAGE = ROOT / "vehicles/common/pillar_pod_gauges/mfd.html"
GENERATOR = ROOT / "tools/gen_jbeam.py"
BAKER = ROOT / "tools/bake_faceplates.html"
EXPECTED_HTML = "local://local/vehicles/common/pillar_pod_gauges/screen.html"
ERRORS: list[str] = []
WARNINGS: list[str] = []


def error(message: str) -> None:
    ERRORS.append(message)


def warning(message: str) -> None:
    WARNINGS.append(message)


def strip_jbeam_comments(source: str) -> str:
    """Remove // and /* */ comments without touching quoted strings."""
    out: list[str] = []
    i = 0
    quote = None
    escaped = False
    while i < len(source):
        ch = source[i]
        nxt = source[i + 1] if i + 1 < len(source) else ""
        if quote:
            out.append(ch)
            if escaped:
                escaped = False
            elif ch == "\\":
                escaped = True
            elif ch == quote:
                quote = None
            i += 1
        elif ch in ("'", '"'):
            quote = ch
            out.append(ch)
            i += 1
        elif ch == "/" and nxt == "/":
            while i < len(source) and source[i] not in "\r\n":
                i += 1
        elif ch == "/" and nxt == "*":
            i += 2
            while i + 1 < len(source) and source[i:i + 2] != "*/":
                i += 1
            i = min(len(source), i + 2)
        else:
            out.append(ch)
            i += 1
    return "".join(out)


def parse_jbeam(path: Path) -> dict:
    source = strip_jbeam_comments(path.read_text(encoding="utf-8"))
    # JBeam permits trailing commas; JSON does not.
    source = re.sub(r",\s*([}\]])", r"\1", source)
    try:
        value = json.loads(source)
    except json.JSONDecodeError as exc:
        error(f"{path.relative_to(ROOT)}: invalid JBeam/JSON syntax at line {exc.lineno}, column {exc.colno}: {exc.msg}")
        return {}
    if not isinstance(value, dict):
        error(f"{path.relative_to(ROOT)}: expected a top-level object")
        return {}
    return value


def check_required_files() -> bool:
    ok = True
    for path in (*(c[1] for c in CARS), DAE, MATERIALS, SCREEN, GENERATOR, BAKER):
        if not path.is_file():
            error(f"required file is missing: {path.relative_to(ROOT)}")
            ok = False
    return ok


def collect_flexbody_meshes(document: dict) -> set[str]:
    meshes: set[str] = set()
    for part_name, part in document.items():
        if not isinstance(part, dict):
            continue
        rows = part.get("flexbodies", [])
        if not isinstance(rows, list):
            error(f"{part_name}: flexbodies must be an array")
            continue
        for row in rows[1:]:  # first row is the flexbody column header
            if isinstance(row, list) and row and isinstance(row[0], str):
                meshes.add(row[0])
            else:
                error(f"{part_name}: malformed flexbody row: {row!r}")
    return meshes


def check_jbeam_structure(document: dict, root_part: str) -> None:
    if not document:
        return
    if root_part not in document:
        error(f"JBeam is missing the root part {root_part!r}")
    for name, part in document.items():
        if not isinstance(part, dict):
            error(f"{name}: part definition must be an object")
            continue
        info = part.get("information")
        if not isinstance(info, dict) or not info.get("name"):
            error(f"{name}: missing information.name")
        if not isinstance(part.get("slotType"), str):
            error(f"{name}: missing string slotType")
        for key in ("slots2", "controller", "variables", "flexbodies"):
            if key in part and not isinstance(part[key], list):
                error(f"{name}: {key} must be an array")
        if "flexbodies" in part:
            rows = part["flexbodies"]
            if len(rows) < 2 or not isinstance(rows[0], list) or rows[0][:1] != ["mesh"]:
                error(f"{name}: flexbodies is missing its mesh header row")
            for row in rows[1:]:
                if not isinstance(row, list) or len(row) < 4:
                    error(f"{name}: invalid flexbody entry: {row!r}")
        # Check the custom gauge config, including paths and material aliases.
        for ctrl_name in ("dbgGauge", "dbgOilGauge"):
            ctrl = part.get(ctrl_name)
            if not isinstance(ctrl, dict):
                continue
            cfg = ctrl.get("configuration", {})
            html_path = cfg.get("htmlPath")
            if html_path != EXPECTED_HTML:
                error(f"{name}.{ctrl_name}: htmlPath should be {EXPECTED_HTML!r}, got {html_path!r}")
            material = str(cfg.get("materialName", "")).removeprefix("@")
            if material and material not in material_names:
                error(f"{name}.{ctrl_name}: unknown materialName {material!r}")


material_names: set[str] = set()


def check_materials() -> None:
    global material_names
    try:
        data = json.loads(MATERIALS.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        error(f"material file cannot be parsed: {exc}")
        return
    if not isinstance(data, dict):
        error("material file must contain an object")
        return
    material_names = set(data)
    for key, material in data.items():
        if not isinstance(material, dict):
            error(f"material {key!r} must be an object")
            continue
        if material.get("name") != key:
            error(f"material {key!r}: name does not match its key")
        for stage in material.get("Stages", []):
            if not isinstance(stage, dict):
                continue
            for texture_key in ("baseColorMap", "normalMap", "emissiveMap"):
                texture = stage.get(texture_key)
                if not isinstance(texture, str) or not texture.startswith("/"):
                    continue
                asset = ROOT / texture.lstrip("/")
                if not asset.is_file():
                    error(f"material {key!r}: {texture_key} points to missing asset {texture}")


def check_dae(meshes: set[str]) -> None:
    try:
        tree = ET.parse(DAE)
    except (OSError, ET.ParseError) as exc:
        error(f"DAE cannot be parsed: {exc}")
        return
    root = tree.getroot()
    ns = {"c": "http://www.collada.org/2005/11/COLLADASchema"}
    dae_meshes = {
        node.attrib.get("name") or node.attrib.get("id", "").removesuffix("-mesh")
        for node in root.findall(".//c:library_geometries/c:geometry", ns)
    }
    missing = sorted(meshes - dae_meshes)
    for mesh in missing:
        error(f"JBeam flexbody mesh {mesh!r} is absent from the Collada file")
    dae_materials = {
        node.attrib.get("name")
        for node in root.findall(".//c:library_materials/c:material", ns)
    }
    for material in sorted(dae_materials - material_names):
        error(f"DAE material {material!r} has no matching main.materials.json entry")
    for material in sorted(material_names - dae_materials):
        warning(f"material {material!r} is defined but not declared in the DAE")


def check_html_and_generator() -> None:
    generator_source = GENERATOR.read_text(encoding="utf-8")
    baker_source = BAKER.read_text(encoding="utf-8")
    sources = [("JBeam generator", generator_source)]
    sources += [(path.relative_to(ROOT).as_posix(), path.read_text(encoding="utf-8")) for _, path, _ in CARS]
    for label, source in sources:
        if EXPECTED_HTML not in source:
            error(f"{label} does not reference the current gauge screen.html path")
        if "digital_boost_gauge/screen.html" in source:
            error(f"{label} contains the obsolete digital_boost_gauge screen path")
    if "digital_boost_gauge/screen.html" in baker_source:
        error("faceplate baker iframe still points to the obsolete digital_boost_gauge path")
    if "pillar_pod_gauges/screen.html" not in baker_source:
        error("faceplate baker does not load the current pillar_pod_gauges screen")

    # The generator should produce the same structured JBeam as each checked-in part file.
    with tempfile.TemporaryDirectory() as tmp:
        for car, path, _ in CARS:
            generated = Path(tmp) / f"{car}.jbeam"
            result = subprocess.run(
                [sys.executable, str(GENERATOR), "--car", car, str(generated)],
                cwd=ROOT, text=True, capture_output=True
            )
            if result.returncode:
                error(f"JBeam generator failed for {car}: " + (result.stderr.strip() or result.stdout.strip()))
                continue
            if parse_jbeam(generated) != parse_jbeam(path):
                error(f"generated JBeam is out of sync with {path.relative_to(ROOT).as_posix()}")


def check_javascript() -> None:
    node = shutil.which("node")
    if not node:
        warning("Node.js is not installed; skipped embedded JavaScript syntax check")
        return
    for page in (SCREEN, MFD_PAGE):
        html = page.read_text(encoding="utf-8")
        scripts = re.findall(r"<script\b[^>]*>(.*?)</script\s*>", html, flags=re.I | re.S)
        inline = [script for script in scripts if script.strip()]
        if not inline:
            error(f"{page.name} contains no inline JavaScript to validate")
            continue
        with tempfile.TemporaryDirectory() as tmp:
            for index, script in enumerate(inline, 1):
                path = Path(tmp) / f"page-{index}.js"
                path.write_text(script, encoding="utf-8")
                result = subprocess.run([node, "--check", str(path)], text=True, capture_output=True)
                if result.returncode:
                    error(f"{page.name} JavaScript syntax error:\n" + (result.stderr.strip() or result.stdout.strip()))


def check_python_syntax() -> None:
    for path in sorted((ROOT / "tools").glob("*.py")):
        result = subprocess.run(
            [sys.executable, "-m", "py_compile", str(path)],
            cwd=ROOT, text=True, capture_output=True
        )
        if result.returncode:
            error(f"{path.relative_to(ROOT)} Python syntax error: " +
                  (result.stderr.strip() or result.stdout.strip()))


def main() -> int:
    if not check_required_files():
        return 1
    check_materials()
    meshes: set[str] = set()
    part_count = 0
    for _, path, root_part in CARS:
        document = parse_jbeam(path)
        part_count += len(document)
        check_jbeam_structure(document, root_part)
        meshes |= collect_flexbody_meshes(document)
    check_dae(meshes)
    check_html_and_generator()
    check_javascript()
    check_python_syntax()

    for message in WARNINGS:
        print(f"WARNING: {message}")
    if ERRORS:
        for message in ERRORS:
            print(f"ERROR: {message}")
        print(f"\nValidation failed: {len(ERRORS)} error(s), {len(WARNINGS)} warning(s).")
        return 1
    print(f"Validation passed: {part_count} JBeam parts in {len(CARS)} cars, {len(meshes)} referenced meshes, "
          f"{len(material_names)} materials checked; embedded JavaScript syntax is valid.")
    if WARNINGS:
        print(f"{len(WARNINGS)} warning(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
