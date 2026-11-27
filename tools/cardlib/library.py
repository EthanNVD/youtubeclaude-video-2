"""The living library: every reusable thing a film can show, one folder per asset.

    library/<type>/<id>/asset.json      the record (see library/README.md)
    library/<type>/<id>/art.svg         optional picture (image path)
    library/<type>/<id>/source/         optional original image(s) + prompt.txt
    library/<type>/<id>/preview.png     made by `python tools/lib.py preview`

A project makes new assets in projects/<slug>/assets/<id>/ (same layout, status "draft"); they work in that project's cards
at once and move into the library with `python tools/lib.py promote`.

This module is the single loader: the scene compiler and tools/lib.py both use it.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LIB = ROOT / "library"

TYPES = {
    "props": "things people hold or that stand on floors and tables (a broom, a lectern, a notice board, a shovel)",
    "vehicles": "things that move with wheels, tracks, hulls or wings (a bicycle, a cart, a field kitchen, an airship)",
    "buildings": "houses, shops, huts, temples, bunkers: whole buildings placed in a street or a landscape",
    "plants": "trees, palms, bushes, grass clumps, crops (they sway in the wind)",
    "costumes": "pieces people wear: hats, turbans, headscarves, sarongs, tunics, vests (drawn on the character rig)",
    "characters": "ready cast looks: a preset + costume pieces + colours (a Malay villager, a Sikh soldier)",
    "places": "story places: a room or town from the kit, or a composed landscape (sky + plates + ground + rows of assets)",
    "plates": "painted FAR background layers (sky, far hills, mid distance); never for things near people",
    "weather": "weather and atmosphere presets (rain, fog, haze, dust, snow…) with their parameters",
}
DRAWABLE = ("props", "vehicles", "buildings", "plants")
ID_RE = re.compile(r"^[a-z][a-z0-9_]{1,40}$")


def _read(f: Path):
    d = json.loads(f.read_text(encoding="utf-8"))
    d["_dir"] = str(f.parent)
    if d.get("parts_file"):
        d["parts"] = json.loads((f.parent / d["parts_file"]).read_text(encoding="utf-8"))
    return d


def load(where: Path | None = None, types=None):
    """{id: asset} of library/ (default) or of a project's assets/ folder."""
    out = {}
    base = where if where is not None else LIB
    if not base.exists():
        return out
    pattern = "*/asset.json" if where is not None else "*/*/asset.json"
    for f in sorted(base.glob(pattern)):
        try:
            d = _read(f)
        except Exception:  # a broken record is reported by `lib check`, never crashes a compile
            continue
        if types and d.get("type") not in types:
            continue
        out[d.get("id") or f.parent.name] = d
    return out


def drawables(project: Path | None = None, film: dict | None = None):
    """everything a scene card can place or hold: library + this project's assets + the film's own "drawings" (last wins)"""
    out = {k: v for k, v in load(types=DRAWABLE).items() if v.get("parts")}
    if project is not None:
        out.update({k: v for k, v in load(project / "assets").items() if v.get("parts")})
    if film:
        out.update(film.get("drawings") or {})
    return out


def places(project: Path | None = None):
    out = load(types=("places",))
    if project is not None:
        out.update(load(project / "assets", types=("places",)))
    return out


def weather_presets(project: Path | None = None):
    out = load(types=("weather",))
    if project is not None:
        out.update(load(project / "assets", types=("weather",)))
    return out


def costume_pieces(project: Path | None = None):
    out = load(types=("costumes",))
    if project is not None:
        out.update(load(project / "assets", types=("costumes",)))
    return out
