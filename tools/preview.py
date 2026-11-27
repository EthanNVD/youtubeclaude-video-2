"""Pre-production sheets: look at the cast, the story places and the things BEFORE writing the cards (and after changing them).

    python tools/make.py projects/<slug> preview             cast (standing + acting), every story place in cards/_film.json
                                                              "sets" (with a person for scale), every drawing the film defines
    python tools/make.py projects/<slug> preview --kit       + every room style and town style of the kit
    python tools/make.py projects/<slug> preview --acts      + every act of the scene card, acted by one person
    python tools/make.py projects/<slug> preview --library   + every drawing of the shared library (library/, see library/README.md)

Writes review/preview/sheet_*.jpg (12 pictures per sheet). Look at every sheet: faces, outfits and costume pieces ("wear"),
ages, sizes of children, the rooms and streets, the drawings and this film's new assets (projects/<slug>/assets) next to a person. Fix cards/_film.json and run it again until it looks right.
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

from cardlib import recipes_scene as RS  # noqa: E402
from cardlib import stagecraft as SC  # noqa: E402

XS = [250, 600, 960, 1320, 1670]
DUR = 2.0


def _label(text, x, y, size=30):
    return {"kind": "label", "text": text, "x": x, "y": y, "style": "tag", "size": size, "in": 0, "enter": "none"}


def _scene(scenes, set_, els, beat, world=None, tag=None):
    i = len(scenes)
    s = {"id": f"p{i + 1:03d}", "start": i * DUR, "end": (i + 1) * DUR, "type": "stage", "set": set_, "elements": els, "beat": beat, "transition": "cut"}
    if world:
        s["world"] = world
    if tag:
        s["tag"], s["tagIn"] = tag, -1
    scenes.append(s)


def _fake_card(film, name):
    raw = {"where": name, "place_id": name, "recipe": "scene", "_file": "_film.json", "_n": name, "at": "(preview)"}
    c = types.SimpleNamespace(film=film, raw=raw, warns=[], cast=film.get("cast", {}))
    c.p = lambda k, d=None: raw.get(k, d)
    return c


def cast_sheets(film, scenes):
    cast = film.get("cast", {})
    ids = list(cast)
    acting = [("talk", "smile"), ("point", "angry"), ("palms", "worried"), ("wave", "happy"), ("cross", "sad")]
    for g in range(0, len(ids), 5):
        grp = ids[g:g + 5]
        for row, mode in enumerate(("standing", "acting")):
            els = []
            for k, cid in enumerate(grp):
                size = float(cast[cid].get("size", 1.0))
                pose, expr = ("idle", "neutral") if mode == "standing" else acting[k % len(acting)]
                els.append({"kind": "actor", "id": cid, "who": cid, "x": XS[k], "y": 900, "scale": round(1.35 * size, 3), "pose": pose, "expr": expr, "talk": mode == "acting" and k == 0})
                name = cast[cid].get("name")
                els.append(_label(cid if not name else f"{cid} · {name}", XS[k], 975, 24))
            _scene(scenes, {"kind": "studio"}, els, f"cast {mode}: {', '.join(grp)}")


def place_sheets(film, scenes):
    for name in film.get("sets", {}):
        c = _fake_card(film, name)
        try:
            pl = RS._place(c)
        except Exception as e:  # a broken place: show it as text so the writer sees the error on the sheet too
            print(f"place \"{name}\": {e}")
            continue
        for w in c.warns:
            print(f"place \"{name}\": {w}")
        ref = {"kind": "actor", "id": "scale_ref", "who": "civilian_man", "x": 1500, "y": SC.DEPTHS["mid"], "pose": "idle", "expr": "neutral"}
        st = dict(pl["set"])
        desc = {k: v for k, v in st.items() if k not in ("seed", "setRows", "plates")}
        _scene(scenes, st, [ref] + (pl.get("row_els") or []), f"place {name}: {json.dumps(desc, ensure_ascii=False)[:150]}",
               world=pl["world"], tag=f"{name} · {pl.get('tag') or ''}".strip(" ·"))


def drawing_sheets(defs, scenes, title):
    names = list(defs)
    for g in range(0, len(names), 4):
        grp = names[g:g + 4]
        els = [{"kind": "actor", "id": "scale_ref", "who": "civilian_man", "x": XS[0], "y": 900, "scale": 1.0, "pose": "idle", "expr": "neutral"},
               _label("a man (scale)", XS[0], 975, 22)]
        for k, n in enumerate(grp):
            d = defs[n]
            els.append({"kind": "drawing", "id": n, "x": XS[k + 1], "y": 900, "scale": float(d.get("size", 1.0)), "parts": d["parts"]})
            els.append(_label(n, XS[k + 1], 975, 22))
        _scene(scenes, {"kind": "studio"}, els, f"{title}: {', '.join(grp)}")


def kit_sheets(scenes):
    for style in RS._ts_keys("ROOM_STYLES"):
        _scene(scenes, {"kind": "room", "style": style}, [{"kind": "actor", "who": "civilian_man", "x": 1500, "y": SC.DEPTHS["mid"], "pose": "idle", "expr": "neutral"}],
               f"room style {style}", world=SC.WORLDS["room"], tag=f"room: {style}")
    for style in RS._ts_keys("TOWN_STYLES"):
        _scene(scenes, {"kind": "town", "style": style}, [{"kind": "actor", "who": "civilian_man", "x": 1500, "y": SC.DEPTHS["mid"], "pose": "idle", "expr": "neutral"}],
               f"town style {style}", world=SC.WORLDS["town"], tag=f"town: {style}")


def act_sheets(scenes, who="civilian_man"):
    acts = [(n, a) for n, a in SC.ACTS.items() if a.get("kind") == "pose"]
    for g in range(0, len(acts), 5):
        grp = acts[g:g + 5]
        els = []
        for k, (n, a) in enumerate(grp):
            el = {"kind": "actor", "id": n, "who": who, "x": XS[k], "y": 900, "scale": 1.35, "pose": a["pose"], "expr": a.get("expr", "neutral")}
            if a.get("holds"):
                el["holds"] = a["holds"]
            els += [el, _label(n, XS[k], 975, 24)]
        _scene(scenes, {"kind": "studio"}, els, f"acts: {', '.join(n for n, _ in grp)}")


def build(proj: Path, kit=False, acts=False, lib=False):
    film = json.loads((proj / "cards" / "_film.json").read_text(encoding="utf-8")) if (proj / "cards" / "_film.json").exists() else {}
    film["_proj"] = str(proj)  # this film's own assets (projects/<slug>/assets) are drawable in its places
    scenes = []
    cast_sheets(film, scenes)
    place_sheets(film, scenes)
    if film.get("drawings"):
        drawing_sheets(film["drawings"], scenes, "film drawings")
    from cardlib import library as LIBMOD
    mine = {k: v for k, v in LIBMOD.load(proj / "assets", types=LIBMOD.DRAWABLE).items() if v.get("parts")}
    if mine:
        drawing_sheets(mine, scenes, "this film's new assets")
    if lib:
        drawing_sheets(RS.library(), scenes, "library drawings")
    if kit:
        kit_sheets(scenes)
    if acts:
        act_sheets(scenes)
    if not scenes:
        sys.exit("nothing to preview: add \"cast\", \"sets\" or \"drawings\" to cards/_film.json")
    cast = LIBMOD.resolve_cast(film.get("cast", {}), proj, film)
    meta = {"title": "preview", "fps": 24, "width": 1920, "height": 1080, "duration": len(scenes) * DUR}
    if (film.get("look") or {}).get("grade"):
        meta["grade"] = film["look"]["grade"]
    return {"meta": meta, "cast": cast, "scenes": scenes}


def main():
    proj = Path(sys.argv[1]).resolve()
    flags = set(sys.argv[2:])
    plan = build(proj, kit="--kit" in flags, acts="--acts" in flags, lib="--library" in flags)
    work = proj / "work"
    work.mkdir(exist_ok=True)
    pf = work / "preview_plan.json"
    pf.write_text(json.dumps(plan, ensure_ascii=False), encoding="utf-8")
    out = Path(next((a.split("=", 1)[1] for a in sys.argv[2:] if a.startswith("--out=")), str(proj / "review" / "preview")))
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)
    cmd = ["node", str(ROOT / "tools" / "render.mjs"), "stills", str(pf), str(out), "--scale", "0.5", "--at", "mid"]
    print("$", " ".join(cmd))
    if subprocess.run(cmd, cwd=ROOT).returncode:
        sys.exit(1)
    subprocess.run([sys.executable, str(ROOT / "tools" / "contact_sheet.py"), str(out), "--per", "12"], cwd=ROOT, check=True)
    sheets = sorted(str(p) for p in out.glob("sheet_*.jpg"))
    print(json.dumps({"scenes": len(plan["scenes"]), "sheets": sheets,
                      "next": "look at every sheet; fix cards/_film.json (cast / sets / drawings) and run preview again"}, indent=1))


if __name__ == "__main__":
    main()
