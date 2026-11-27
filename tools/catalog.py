"""Build the recipe catalog (recipes/*.md) and, with --previews, a preview still of every recipe variant.

python tools/catalog.py            write recipes/CATALOG.md, recipes/<id>.md, recipes/PEOPLE.md (no rendering)
python tools/catalog.py --previews also render recipes/img/<id>_<variant>.jpg and recipes/img/stagecraft/ (≈ 7 min; one render at a time!)
python tools/catalog.py --stagecraft-previews   only the scene-card pictures (room/town styles, acts, library drawings)
Also writes recipes/STAGECRAFT.md: the whole vocabulary of the `scene` card.

The recipe code (tools/cardlib/recipes_*.py) is the single source of truth: parameters, defaults, allowed values, when to use,
example cards. Run this after changing a recipe.
"""
from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
from cardlib import RECIPES  # noqa: E402
from cardlib.core import COMMON  # noqa: E402
from cardlib import sides as SIDES  # noqa: E402

OUT = ROOT / "recipes"
CLASS_ORDER = [("action", "Action — people and machines DOING something (most of the film)"), ("talk", "Talk — people in a place, with business (keep short)"),
               ("map", "Maps — where (≤ 5 s in battle chapters)"), ("device", "Documents, numbers, devices, titles (≤ 4-7 s)"), ("host", "The host")]
ERA_OF = {"convoy": "ww2", "bombing": "ww2", "air_battle": "ww2", "airfield": "ww2", "para_drop": "ww2", "river_crossing": "ww2"}


def phrases_in(card):
    out = []
    for k, v in card.items():
        if k == "at":
            continue
        if isinstance(v, str) and (k.endswith("_on") or k == "on"):
            out.append(v)
        elif isinstance(v, dict) and isinstance(v.get("on"), str):
            out.append(v["on"])
        elif isinstance(v, list):
            for it in v:
                if isinstance(it, dict) and isinstance(it.get("on"), str):
                    out.append(it["on"])
    return out


def preview_project():
    proj = ROOT / "projects" / "_recipes"
    if proj.exists():
        shutil.rmtree(proj)
    (proj / "cards").mkdir(parents=True)
    (proj / "work").mkdir()
    cards, words, t = [], [], 0.0
    names = []
    for rid, r in sorted(RECIPES.items()):
        for v in r.variants:
            ex = json.loads(json.dumps(r.example))
            if not ex:
                continue
            ex["variant"] = v
            ex["era"] = ex.get("era") or ERA_OF.get(rid, "ww1")
            text = f"{ex['at']} " + " ".join(phrases_in(ex)) + " and so the story went on for a while longer here"
            toks = text.split()
            # unique start: prefix with a marker word so phrases never collide between cards
            marker = f"zz{len(cards)}"
            toks = [marker] + toks
            ex["at"] = marker + " " + ex["at"]
            step = max(0.2, 6.5 / len(toks))
            for w in toks:
                words.append({"w": w, "start": round(t, 3), "end": round(t + step * 0.9, 3)})
                t += step
            t += 0.3
            cards.append(ex)
            names.append((rid, v))
    film = {"title": "Recipe previews", "lang": "en", "era": "ww1", "sides": ["german", "british"], "host_set": "station", "cast": {}}
    (proj / "cards" / "_film.json").write_text(json.dumps(film, indent=1), encoding="utf-8")
    (proj / "cards" / "ch01.json").write_text(json.dumps({"cards": cards}, indent=1, ensure_ascii=False), encoding="utf-8")
    (proj / "work" / "words.json").write_text(json.dumps(words), encoding="utf-8")
    return proj, names


def render_previews():
    proj, names = preview_project()
    r = subprocess.run([sys.executable, str(ROOT / "tools/cards.py"), str(proj)], capture_output=True, text=True, encoding="utf-8")
    rep = json.loads(r.stdout[r.stdout.index("{"):])
    if rep.get("errors"):
        print(json.dumps(rep["errors"], indent=1, ensure_ascii=False))
        sys.exit("preview cards failed — fix the recipe examples above")
    subprocess.run([sys.executable, str(ROOT / "tools/make.py"), str(proj), "review", "--at", "mid"], check=True)
    plan = json.loads((proj / "plan.json").read_text(encoding="utf-8"))
    img = OUT / "img"
    img.mkdir(parents=True, exist_ok=True)
    stills = sorted((proj / "review").glob("s*_*.jpg"))
    by_id = {}
    for f in stills:
        by_id.setdefault(f.name.split("_")[0], f)
    for s, (rid, v) in zip(plan["scenes"], names):
        f = by_id.get(s["id"])
        if f:
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(f), "-vf", "scale=480:-1", str(img / f"{rid}_{v}.jpg")], check=True)
    print(f"{len(names)} previews -> {img}")


def md_param(name, p):
    t = p.type
    vals = f"one of `{'`, `'.join(str(v) for v in p.values)}`" if p.values else {"phrase": "words copied from this card's narration", "who": "cast id",
                                                                                  "side": "side name", "list": "list", "dict": "object", "bool": "true / false",
                                                                                  "int": "whole number"}.get(t, "text")
    d = "" if p.default is None else f"`{json.dumps(p.default)}`"
    return f"| `{name}` | {'**yes**' if p.required else 'no'} | {vals} | {d} | {p.doc} |"


def write_docs():
    OUT.mkdir(exist_ok=True)
    lines = ["# Recipe catalog", "",
             "Every card uses exactly one recipe. Choose the recipe from what the narration SAYS: look the sentence up in "
             "`playbook/narration-to-picture.md` first, then open the recipe's page here for its fields.", "",
             "This file is generated by `python tools/catalog.py` from the code. Do not edit it by hand.", ""]
    for cls, title in CLASS_ORDER:
        rs = [r for r in sorted(RECIPES.values(), key=lambda r: r.id) if r.cls == cls]
        if not rs:
            continue
        lines += [f"## {title}", "", "| recipe | use it when | do NOT use it when | preview |", "|---|---|---|---|"]
        for r in rs:
            pv = f"![]({'img/' + r.id + '_' + r.variants[0] + '.jpg'})" if (OUT / "img" / f"{r.id}_{r.variants[0]}.jpg").exists() else ""
            lines.append(f"| [`{r.id}`]({r.id}.md) | {r.when} | {r.not_when or '—'} | {pv} |")
        lines.append("")
    lines += ["## Fields every card can have", "", "| field | required | value | default | meaning |", "|---|---|---|---|---|"]
    lines += [md_param(k, p) for k, p in COMMON.items()]
    (OUT / "CATALOG.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    for r in RECIPES.values():
        L = [f"# `{r.id}` ({r.cls})", "", f"**Use it when:** {r.when}", "", f"**Do NOT use it when:** {r.not_when or '—'}", "",
             f"**Camera (what the compiler does, per variant):** {r.shots_doc}", "", "## Fields", "",
             "| field | required | value | default | meaning |", "|---|---|---|---|---|"]
        L += [md_param(k, p) for k, p in r.params.items()]
        L += ["", "Plus the common fields (`at`, `recipe`, `says`, `variant`, `date`, `place`, `name_card`, `label`, `counter`, `stamp`, `time`, "
              "`weather`, `tint`, …) — see [CATALOG.md](CATALOG.md#fields-every-card-can-have).", "",
              f"Variants: {', '.join(r.variants)} (leave `variant` out: the compiler rotates them so the film never repeats a composition).", "",
              "## Example card", "", "```json", json.dumps(r.example, ensure_ascii=False, indent=1), "```", ""]
        pv = [v for v in r.variants if (OUT / "img" / f"{r.id}_{v}.jpg").exists()]
        if pv:
            L += ["## Previews (middle frame of the example, each variant)", ""] + [f"Variant {v}: ![]({'img/' + r.id + '_' + v + '.jpg'})" for v in pv] + [""]
        (OUT / f"{r.id}.md").write_text("\n".join(L), encoding="utf-8")
    write_people()
    print(f"{len(RECIPES)} recipes -> {OUT}")


def write_people():
    L = ["# People: sides, uniforms, presets", "", "Generated by `python tools/catalog.py`.", "",
         "## Soldiers come from `side` + the film's `era`", "", "You never pick a uniform. A card says `\"side\": \"german\"`, and the film's era decides the rest.", ""]
    for era, t in SIDES.TABLE.items():
        if era == "modern":
            continue
        L += [f"### era `{era}`", "", "| side | soldier | officer | flag | tank | ship |", "|---|---|---|---|---|---|"]
        for s, row in t.items():
            L.append(f"| `{s}` | {row.get('soldier')} | {row.get('officer')} | {row.get('nation')} | {row.get('tank') or '—'} | {row.get('ship') or '—'} |")
        L.append("")
    L += ["## Named people (`cast` in cards/_film.json)", "",
          "Give every named person a cast id with a `preset` from this list. If someone is missing, pick the closest preset and change it, e.g. "
          "`{\"preset\": \"german_officer\", \"facial\": \"walrus\", \"glasses\": \"round\", \"age\": 0.7}`. See references/cast.md for all the look fields.", ""]
    groups = {}
    for p in sorted(SIDES.PRESETS):
        key = "WW1" if p.startswith("ww1_") or p in ("kaiser_wilhelm", "hindenburg", "ludendorff", "moltke", "schlieffen", "kluck", "falkenhayn", "scheer", "holtzendorff",
                                                      "zimmermann", "bauer", "joffre", "lanrezac", "gallieni", "foch", "jellicoe", "brusilov", "wilson", "lenin", "monash", "currie", "kaiser") else \
            "Host" if p.startswith("host") or p in ("aide", "narrator_archivist", "narrator_accountant") else \
            "Civilians" if p in ("civilian_man", "civilian_woman", "worker", "diplomat", "reporter", "dutch_civilian", "dutch_woman", "vn_peasant") else \
            "Older eras" if p in ("napoleon", "wellington", "kutuzov", "hannibal", "roman_legionary", "caesar") else "WW2 and later"
        groups.setdefault(key, []).append(p)
    for k in ("WW1", "WW2 and later", "Older eras", "Civilians", "Host"):
        L += [f"### {k}", "", ", ".join(f"`{p}`" for p in groups.get(k, [])), ""]
    (OUT / "PEOPLE.md").write_text("\n".join(L), encoding="utf-8")


# ------------------------------------------------------------------ the scene card's vocabulary (recipes/STAGECRAFT.md)
SC_IMG = OUT / "img" / "stagecraft"


def _kit_docs(name):
    """{key: doc} of an exported table in src/sets/Kit.tsx"""
    src = (ROOT / "src/sets/Kit.tsx").read_text(encoding="utf-8")
    i = src.index(f"export const {name}")
    j = src.index("\n};", i)
    out = {}
    for m in re.finditer(r"^\s{2}(\w+): \{(.*)$", src[i:j], re.M):
        d = re.search(r"doc: '((?:[^'\\]|\\.)*)'", m.group(2))
        out[m.group(1)] = d.group(1).replace("\\'", "'") if d else ""
    return out


def render_stagecraft_previews():
    """one still per room style and town style, every act acted, every library drawing (about 1-2 min)"""
    import preview as PV
    scenes = []
    PV.kit_sheets(scenes)
    PV.act_sheets(scenes)
    PV.drawing_sheets(PV.RS.library(), scenes, "library drawings")
    for k, sc in enumerate(scenes):
        b = sc["beat"]
        if b.startswith("room style"):
            sc["id"] = "room_" + b.split()[-1]
        elif b.startswith("town style"):
            sc["id"] = "town_" + b.split()[-1]
        elif b.startswith("acts"):
            sc["id"] = f"acts_{k:02d}"
        else:
            sc["id"] = f"library_{k:02d}"
    plan = {"meta": {"title": "stagecraft", "fps": 24, "width": 1920, "height": 1080, "duration": len(scenes) * PV.DUR}, "cast": {}, "scenes": scenes}
    tmp = ROOT / "recipes" / "_stagecraft_plan.json"
    tmp.write_text(json.dumps(plan), encoding="utf-8")
    if SC_IMG.exists():
        shutil.rmtree(SC_IMG)
    SC_IMG.mkdir(parents=True)
    subprocess.run(["node", str(ROOT / "tools" / "render.mjs"), "stills", str(tmp), str(SC_IMG), "--scale", "0.4", "--at", "mid"], cwd=ROOT, check=True)
    tmp.unlink()
    for f in list(SC_IMG.glob("*.jpg")):
        f.rename(SC_IMG / (re.sub(r"_\d+$", "", f.stem) + ".jpg"))
    for f in SC_IMG.glob("*.json"):
        f.unlink()


def write_stagecraft():
    from cardlib import stagecraft as SC
    from cardlib import recipes_scene as RS
    import validate_plan
    v = validate_plan.vocab()

    def img(n, w=360):
        return f'<img src="img/stagecraft/{n}.jpg" width="{w}">' if (SC_IMG / f"{n}.jpg").exists() else ""

    L = ["# Stagecraft — everything a `scene` card can name", "",
         "Generated by `python tools/catalog.py` (pictures: `--stagecraft-previews`) from `tools/cardlib/stagecraft.py`, `src/sets/Kit.tsx` "
         "and the engine. Do not edit by hand.", "",
         "How to write a scene card: [playbook/scene-writing.md](../playbook/scene-writing.md). When you need an idea: "
         "[playbook/visual-ideas.md](../playbook/visual-ideas.md). See your own cast, places and drawings: `python tools/make.py projects/<slug> preview`.", ""]
    L += ["## Where people stand", "", f"- `at`: {SC.SLOT_DOC}", f"- `depth`: {SC.DEPTH_DOC}", ""]
    L += ["## Places", "", '### Room styles (`{"room": "<style>"}`)', "", "| style | what it is | picture |", "|---|---|---|"]
    L += [f"| `{k}` | {d} | {img('room_' + k)} |" for k, d in _kit_docs("ROOM_STYLES").items()]
    L += ["", "### Room modules (`items`, left to right along the back wall)", "", "| module | what it is |", "|---|---|"]
    L += [f"| `{k}` | {d} |" for k, d in _kit_docs("ROOM_ITEMS").items()]
    L += ["", "Room fields: `wall` (plaster paper panel plank timber brick stone tile concrete) + `wallColor`, `floor` (boards tile stone carpet earth "
          "duckboard parquet) + `floorColor`, `light` (window lamp candle lantern fire dim), `poor`, `beams`, `view`, `cold`, `lightX`, `nation`.", ""]
    L += ['### Town styles (`{"town": "<style>"}`)', "", "| style | what it is | picture |", "|---|---|---|"]
    L += [f"| `{k}` | {d} | {img('town_' + k)} |" for k, d in _kit_docs("TOWN_STYLES").items()]
    L += ["", "### Buildings (`buildings`, left to right)", "", "| building | what it is |", "|---|---|"]
    L += [f"| `{k}` | {d} |" for k, d in _kit_docs("TOWN_BUILDINGS").items()]
    L += ["", "### Street items (`items`)", "", "| item | what it is |", "|---|---|"]
    L += [f"| `{k}` | {d} |" for k, d in _kit_docs("TOWN_ITEMS").items()]
    L += ["", "Town fields: `ground` (cobbles mud snow dirt), `back` (spire chimneys hills city none), `nation`.", "",
          '### Engine sets (`{"set": "<name>"}`)', "", ", ".join(f"`{k}`" for k in sorted(v["sets"] - {"room", "town"})), ""]
    L += ["## People", "", "Cast presets and look fields: [PEOPLE.md](PEOPLE.md). Moods (the face, and the gestures people choose by themselves):", "",
          "| mood | face | while talking | while listening | while waiting |", "|---|---|---|---|---|"]
    L += [f"| `{k}` | {e} | {', '.join(t)} | {', '.join(li)} | {', '.join(w)} |" for k, (e, t, li, w) in SC.MOODS.items()]
    L += ["", '## Acts (`do`: `{"act": …, "on": "words"}`)', "", "| act | what the viewer sees | pose | holds |", "|---|---|---|---|"]
    for k, a in SC.ACTS.items():
        L.append(f"| `{k}` | {a['doc']} | {a.get('pose', '—')} | {a.get('holds', '—')} |")
    acts_imgs = sorted(f.stem for f in SC_IMG.glob("acts_*.jpg")) if SC_IMG.exists() else []
    if acts_imgs:
        L += ["", "The pose acts, acted (five per picture, in the order of the table above):", ""] + [img(n, 300) for n in acts_imgs]
    L += ["", '## Crowds (`crowd`: `{"kind": …}`)', "", "| kind | what it is |", "|---|---|"] + [f"| `{k}` | {d} |" for k, d in SC.CROWDS.items()]
    L += ["", "## Things (`things`)", "", "| thing | size next to a person | what it is |", "|---|---|---|"]
    for k in sorted(v["props"]):
        L.append(f"| `{k}` | {SC.THINGS.get(k, {}).get('size', '—')} | {SC.THING_DOC.get(k, '')} |")
    lib = RS.library()
    L += ["", "## Library drawings (`library/`)", "",
          "Use them like things (`{\"what\": \"rubber_tree\"}`), hold them, ride them (`\"rides\": \"bicycle\"`) or put them in rows of a "
          "composed place. Find more with `python tools/lib.py search \"words\"`; make new ones as assets of the film and promote them "
          "([playbook/library.md](../playbook/library.md)).", "", "| drawing | what it is |", "|---|---|"]
    L += [f"| `{k}` | {d.get('doc', '')} |" for k, d in lib.items()]
    lib_imgs = sorted(f.stem for f in SC_IMG.glob("library_*.jpg")) if SC_IMG.exists() else []
    L += [""] + [img(n, 480) for n in lib_imgs] + [""]
    L += ["## Vehicles (`vehicles`)", "", ", ".join(f"`{k}`" for k in sorted(v["vehicles"])), "",
          "## Effects (`effects`)", "", "| effect | what it is |", "|---|---|"] + [f"| `{k}` | {d} |" for k, d in SC.EFFECTS.items()]
    L += ["", "## Cameras (`camera`)", "", "| camera | what it does |", "|---|---|"] + [f"| `{k}` | {d} |" for k, d in SC.CAMERAS.items()]
    L += ["", "## Poses (`pose`: a person's starting pose)", "", ", ".join(f"`{k}`" for k in sorted(v["poses"])), ""]
    (OUT / "STAGECRAFT.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    print(f"stagecraft -> {OUT / 'STAGECRAFT.md'}")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    if "--previews" in sys.argv:
        render_previews()
        render_stagecraft_previews()
    elif "--stagecraft-previews" in sys.argv:
        render_stagecraft_previews()
    write_docs()
    write_stagecraft()
