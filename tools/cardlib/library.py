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


SLOTS = ("head", "headback", "body", "hips", "back")


def recolor(parts, cmap):
    """a copy of parts with fill/stroke colours swapped by cmap {"#3e5d8c": "#8c3e3e"} (case-insensitive) — the adapt path"""
    cm = {k.lower(): v for k, v in (cmap or {}).items()}
    out = []
    for p in parts:
        q = dict(p)
        for k in ("fill", "stroke"):
            if isinstance(q.get(k), str) and q[k].lower() in cm:
                q[k] = cm[q[k].lower()]
        if q.get("group"):
            q["group"] = recolor(q["group"], cmap)
        out.append(q)
    return out


def costume_slots(asset):
    """[{slot, parts, above?}] of a costume asset: one piece ("slot" + "parts") or several ("pieces")"""
    if asset.get("pieces"):
        return [{"slot": p.get("slot", "head"), "parts": p["parts"], **({"above": True} if p.get("above") else {})} for p in asset["pieces"]]
    return [{"slot": asset.get("slot", "head"), "parts": asset.get("parts") or [], **({"above": True} if asset.get("above") else {})}]


def resolve_cast(cast: dict, project: Path | None = None, film: dict | None = None):
    """cast entries -> engine specs:
    - "look": "<characters asset>" merges a saved cast look (the entry's own fields win);
    - "wear": ["songkok", {"piece": "sarong", "recolor": {"#3e5d8c": "#7a3030"}}, {"slot": "head", "parts": [...]}]
      turns costume ids into pieces {slot, parts, above} (library + project assets + film "drawings");
    - name / role / note are dropped (they are for name cards and people).
    Unknown ids raise KeyError with the closest names (the compiler turns it into an instruction)."""
    import difflib
    looks = load(types=("characters",))
    pieces = costume_pieces(project)
    if project is not None:
        looks.update(load(project / "assets", types=("characters",)))
    out = {}
    for cid, spec in cast.items():
        spec = dict(spec)
        if spec.get("look"):
            lk = looks.get(spec["look"])
            if lk is None:
                raise KeyError(f'cast "{cid}": look "{spec["look"]}" is not a characters asset. Close: {difflib.get_close_matches(spec["look"], list(looks), 3)}')
            base = {k: v for k, v in (lk.get("spec") or {}).items()}
            base.update({k: v for k, v in spec.items() if k != "look"})
            spec = base
        wear = []
        for w in spec.get("wear") or []:
            if isinstance(w, dict) and "parts" in w:
                wear.append({"slot": w.get("slot", "head"), "parts": w["parts"], **({"above": True} if w.get("above") else {})})
                continue
            wid = w if isinstance(w, str) else w.get("piece")
            pc = pieces.get(wid) or ((film or {}).get("drawings") or {}).get(wid)
            if pc is None:
                raise KeyError(f'cast "{cid}": costume piece "{wid}" does not exist. Close: {difflib.get_close_matches(str(wid), list(pieces), 3)}. '
                               f'Make it: python tools/lib.py new costumes {wid} --project <project>')
            for sl in costume_slots(pc):
                if isinstance(w, dict) and w.get("recolor"):
                    sl = {**sl, "parts": recolor(sl["parts"], w["recolor"])}
                wear.append(sl)
        if wear:
            spec["wear"] = wear
        else:
            spec.pop("wear", None)
        out[cid] = {k: v for k, v in spec.items() if k not in ("name", "role", "note")}
    return out
