"""The `scene` card: compose the picture the narration describes, instead of picking a ready-made recipe.

A recipe is a fixed composition with a few variants: perfect for common moments, repetitive over a long film. A `scene`
card is written like a director's note and compiled into a staged, acted, filmed scene:

    {"at": "In the winter of 1916", "recipe": "scene",
     "says": "In the hunger winter families lived on turnips.",
     "idea": "A mother drops the last turnip into the pot while her two children watch the empty table — supper is a turnip.",
     "where": "mueller_kitchen", "time": "night",
     "people": [
        {"who": "mother", "at": "center_right", "mood": "worried", "do": [{"act": "stir"}, {"act": "look_up", "on": "turnips"}]},
        {"who": "girl", "at": "center_left", "depth": "near", "size": 0.72, "seated": true, "mood": "hungry", "face": "mother"}],
     "things": [{"what": "stove", "at": "right", "depth": "mid"}, {"what": "pot", "on": "stove"},
                {"what": "table", "at": "center_left", "depth": "near"}, {"what": "turnips", "on": "table", "n": 2}],
     "camera": "wide_then_close", "focus": "mother", "close_on": "turnips"}

The compiler computes positions, depth and sizes, who faces whom, the gestures people make while they talk, listen or wait
(seeded per film: no two films move alike), the camera shots and dissolves, footsteps and business sounds, the ambience.
Vocabulary: tools/cardlib/stagecraft.py -> recipes/STAGECRAFT.md. Method and examples: playbook/scene-writing.md.
"""
from __future__ import annotations

import difflib
import random
import re
import shutil
from pathlib import Path

from shotlib import AID, FX, PROP, SHOT

from . import stagecraft as SC
from .core import TOOLS, CardError, Param, _where, recipe, stage

_VOCAB = {}


def _ts_keys(name):
    """keys of an exported object literal in src/sets/Kit.tsx (ROOM_STYLES, TOWN_STYLES, ...)"""
    if name not in _VOCAB:
        s = (TOOLS.parent / "src/sets/Kit.tsx").read_text(encoding="utf-8")
        i = s.index(f"export const {name}")
        j = s.index("\n};", i)
        _VOCAB[name] = re.findall(r"^\s{2}(\w+): \{", s[i:j], re.M)
    return _VOCAB[name]


def vocab():
    if "engine" not in _VOCAB:
        import validate_plan  # tools/validate_plan.py reads the engine's vocabulary from src/
        _VOCAB["engine"] = validate_plan.vocab()
    return _VOCAB["engine"]


def _near(word, options, n=3):
    return difflib.get_close_matches(str(word), list(options), n=n, cutoff=0.5)


from . import library as LIBMOD  # noqa: E402


def library():
    """the living library's drawable assets (library/<props|vehicles|buildings|plants>/<id>/asset.json)"""
    if "library" not in _VOCAB:
        _VOCAB["library"] = LIBMOD.drawables()
    return _VOCAB["library"]


def drawings(film):
    """everything this film can place or hold: the library + the project's own assets (projects/<slug>/assets/) +
    cards/_film.json "drawings" (the most local wins)"""
    key = "drawings:" + str(film.get("_proj"))
    if key not in _VOCAB:
        proj = Path(film["_proj"]) if film.get("_proj") else None
        _VOCAB[key] = LIBMOD.drawables(project=proj)
    return {**_VOCAB[key], **(film.get("drawings") or {})}


def _thing_ok(c, what):
    return what in vocab()["props"] or what in drawings(c.film)


def _hold_kv(c, item):
    """keys that make a person hold `item` (an engine prop or a declarative drawing)"""
    if not item:
        return {"holds": "", "holdsDrawing": None, "holdsGrip": None}
    dw = drawings(c.film).get(item)
    if dw:
        return {"holds": item, "holdsDrawing": dw["parts"], "holdsGrip": dw.get("grip") or (dw.get("anchors") or {}).get("grip")}
    if item not in vocab()["props"]:
        near = _near(item, list(vocab()["props"]) + list(drawings(c.film)))
        _warn(c, f"held thing \"{item}\" is neither an engine prop nor a drawing (shown as paper). Did you mean {near}? "
                 f"Define it in cards/_film.json \"drawings\" (playbook/scene-writing.md §5). Logged in work/missing_assets.json.")
        _missing(c, "thing", item, "paper")
        return {"holds": "paper", "holdsDrawing": None, "holdsGrip": None}
    return {"holds": item, "holdsDrawing": None, "holdsGrip": None}


HOLDING_POSES = {"hold", "holdUp", "show", "give", "carry", "sack", "basket", "cradle", "port", "shoulder", "aim", "charge", "ease", "binoculars", "drink",
                 "read", "phone", "smoke", "write", "eat", "stir", "ladle", "peel", "reach", "pull", "push", "hammer", "typing", "count"}


def _missing(c, kind, name, used):
    c.film.setdefault("_missing", []).append({"card": _where(c.raw), "kind": kind, "name": name, "used": used})


def _warn(c, msg):
    c.warns.append(msg)


# ------------------------------------------------------------------ WHERE
PASS_ROOM = ("items", "wall", "wallColor", "floor", "floorColor", "light", "poor", "view", "beams", "cold", "lightX", "nation", "seed")
PASS_TOWN = ("buildings", "items", "ground", "back", "nation", "seed")


def _place(c):
    """-> {"kind": room|town|set, "set": {...}, "world": {...}, "key": "..."}; story places are remembered by place_id."""
    sets = c.film.get("sets", {})
    remembered = c.film.setdefault("_scene_places", {})
    pid = c.raw.get("place_id")
    w = c.p("where")
    if w is None and pid in sets:
        w = pid
    if w is None and pid in remembered:
        return {**remembered[pid], "set": dict(remembered[pid]["set"])}
    if w is None:
        raise CardError(f"{_where(c.raw)}: a scene card needs \"where\": a story place from cards/_film.json \"sets\" "
                        f"({sorted(sets) or 'none yet'}), a room style ({_ts_keys('ROOM_STYLES')}), a town style ({_ts_keys('TOWN_STYLES')}) "
                        f"or an engine set (recipes/STAGECRAFT.md).")
    key = w if isinstance(w, str) else None
    if isinstance(w, str) and w in sets:
        spec = dict(sets[w])
        pid = pid or w
    elif isinstance(w, str):
        if w in _ts_keys("ROOM_STYLES"):
            spec = {"room": w}
        elif w in _ts_keys("TOWN_STYLES"):
            spec = {"town": w}
        elif w in vocab()["sets"]:
            spec = {"set": w}
        elif w in LIBMOD.places(Path(c.film["_proj"]) if c.film.get("_proj") else None):
            # a story place kept in the living library (library/places/<id>, or this project's assets/<id>)
            spec = dict(LIBMOD.places(Path(c.film["_proj"]) if c.film.get("_proj") else None)[w].get("spec") or {})
            pid = pid or w
        else:
            raise CardError(f"{_where(c.raw)}: \"where\" = \"{w}\" is not a story place, a room style, a town style or an engine set. "
                            f"Did you mean {_near(w, list(sets) + _ts_keys('ROOM_STYLES') + _ts_keys('TOWN_STYLES') + sorted(vocab()['sets']) + list(LIBMOD.places()))}? "
                            f"Define new story places in cards/_film.json \"sets\" (playbook/scene-writing.md §2).")
    elif isinstance(w, dict):
        spec = dict(w)
    else:
        raise CardError(f"{_where(c.raw)}: \"where\" must be a name or an object like {{\"room\": \"kitchen\", \"items\": [...]}}.")
    seed = (c.film.get("look") or {}).get("seed", 0)
    row_els = []
    if "compose" in spec:
        st, row_els = _compose(c, spec, seed)
        kind = "compose"
    elif "room" in spec or spec.get("kit") == "room":
        style = spec.get("room") or spec.get("style") or "kitchen"
        if style not in _ts_keys("ROOM_STYLES"):
            raise CardError(f"{_where(c.raw)}: room style \"{style}\" does not exist. Use one of {_ts_keys('ROOM_STYLES')} (then change items/wall/floor/light).")
        st = {"kind": "room", "style": style, "seed": seed, **{k: spec[k] for k in PASS_ROOM if k in spec}}
        st["items"] = _check_items(c, st.get("items"), _ts_keys("ROOM_ITEMS"), "room item")
        _check_flags(c, st, st.get("items") if st.get("items") is not None else _style_items(style), "flag")
        kind = "room"
    elif "town" in spec or spec.get("kit") == "town":
        style = spec.get("town") or spec.get("style") or "german"
        if style not in _ts_keys("TOWN_STYLES"):
            raise CardError(f"{_where(c.raw)}: town style \"{style}\" does not exist. Use one of {_ts_keys('TOWN_STYLES')}.")
        st = {"kind": "town", "style": style, "seed": seed, **{k: spec[k] for k in PASS_TOWN if k in spec}}
        st["buildings"] = _check_items(c, st.get("buildings"), _ts_keys("TOWN_BUILDINGS"), "building")
        st["items"] = _check_items(c, st.get("items"), _ts_keys("TOWN_ITEMS"), "street item")
        _check_flags(c, st, (st.get("items") or []) + [b for b in (st.get("buildings") or []) if "townhall" in str(b)], "banner")
        kind = "town"
    else:
        name = spec.get("set") or spec.get("kind")
        if name not in vocab()["sets"]:
            raise CardError(f"{_where(c.raw)}: set \"{name}\" does not exist. Did you mean {_near(name, vocab()['sets'])}?")
        st = {"kind": name, **{k: v for k, v in spec.items() if k not in ("set", "kind", "time", "weather", "tag")}}
        kind = "set"
    st = {k: v for k, v in st.items() if v is not None}
    for k in ("time", "weather"):
        if spec.get(k) and not c.raw.get(k):
            st[k] = spec[k]
    world = dict(SC.WORLDS[kind])
    if kind in ("set", "compose") and (spec.get("horizon") or st.get("horizon")):
        world["horizon"] = spec.get("horizon") or st.get("horizon")
    out = {"kind": kind, "set": st, "world": world, "key": key or f"{kind}:{st.get('style', st['kind'])}", "tag": spec.get("tag"), "row_els": row_els}
    if pid:
        remembered[pid] = {**out, "set": dict(st)}
    return out


def _compose(c, spec, seed):
    """a composed place: {"compose": {"far": [...], "ground": "...", "road": {...}, "rows": [...], "items": [...], "plates": [...]}, "horizon": 560}
    -> the set (sky, plates, far layers, ground, road, far rows) and the drawing elements of the near rows (sorted in depth with people)"""
    cp = spec["compose"] if isinstance(spec["compose"], dict) else {}
    where = _where(c.raw)
    hz = float(spec.get("horizon", cp.get("horizon", 560)))
    far = cp.get("far", ["hills"])
    far = far if isinstance(far, list) else [far]
    for f in far:
        if f not in SC.COMPOSE_FAR:
            raise CardError(f"{where}: compose \"far\": \"{f}\" is not a far layer. Use some of {list(SC.COMPOSE_FAR)}.")
    ground = cp.get("ground", "grass")
    if ground not in SC.COMPOSE_GROUND:
        raise CardError(f"{where}: compose \"ground\": \"{ground}\" is not a ground. Use one of {list(SC.COMPOSE_GROUND)}.")
    st = {"kind": "compose", "horizon": hz, "far": [f for f in far if f != "none"], "ground": ground, "seed": seed,
          "_rows_spec": [{"what": r.get("what")} for r in (cp.get("rows") or []) + (cp.get("items") or [])]}
    if spec.get("ambience") or cp.get("ambience"):
        st["ambience"] = spec.get("ambience") or cp.get("ambience")
    road = cp.get("road")
    if road:
        road = {"kind": road} if isinstance(road, str) else dict(road)
        if road.get("kind", "laterite") not in SC.COMPOSE_ROADS:
            raise CardError(f"{where}: compose road kind \"{road.get('kind')}\" is unknown. Use one of {list(SC.COMPOSE_ROADS)}.")
        if isinstance(road.get("y"), str):
            road["y"] = _depth(road["y"])
        st["road"] = road
    if cp.get("haze") is not None:
        st["haze"] = float(cp["haze"])
    # painted plates (images made by an image model, imported with lib import --type plates): copied into public/plates/<id>/
    plates = []
    pool = LIBMOD.load(types=("plates",))
    if c.film.get("_proj"):
        pool.update(LIBMOD.load(Path(c.film["_proj"]) / "assets", types=("plates",)))
    for pl in cp.get("plates") or []:
        pl = {"id": pl} if isinstance(pl, str) else dict(pl)
        a = pool.get(pl["id"])
        if a is None:
            raise CardError(f"{where}: plate \"{pl['id']}\" is not a plates asset. Close: {_near(pl['id'], list(pool))}. "
                            f"Make one: library/prompts/plates.md, then python tools/lib.py import <picture> --type plates --layer far …")
        for layer, fname in (a.get("layers") or {}).items():
            if pl.get("layers") and layer not in pl["layers"]:
                continue
            src = Path(a["_dir"]) / fname
            dst = Path(__file__).resolve().parents[2] / "public" / "plates" / pl["id"] / fname
            if src.exists() and (not dst.exists() or dst.stat().st_mtime < src.stat().st_mtime):
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(src, dst)
            plates.append({"src": f"plates/{pl['id']}/{fname}", "layer": layer, **{k: pl[k] for k in ("x", "y", "w", "h", "opacity", "drift") if k in pl}})
    if plates:
        st["plates"] = plates
    world = {**SC.WORLDS["compose"], "horizon": hz}

    def ps(y):
        return max(0.03, world["scale"] * (y - hz) / max(1, world["y"] - hz))

    set_rows, els = [], []
    rows = list(cp.get("rows") or []) + [{**it, "n": 1, "gap": 1, "from": it.get("at", 960), "to": it.get("at", 960)} for it in (cp.get("items") or [])]
    for i, r in enumerate(rows):
        what = r.get("what")
        dw = drawings(c.film).get(what)
        if dw is None or not dw.get("parts"):
            raise CardError(f"{where}: compose row \"{what}\" is not a drawing (library or this film). Did you mean {_near(str(what), list(drawings(c.film)))}? "
                            f"Find or make it: python tools/lib.py search \"{what}\" · python tools/lib.py new plants {what} --project <project>")
        try:
            y0 = float(r["depth"]) if isinstance(r.get("depth"), (int, float)) else _depth(r.get("depth"), "back")
            x0, x1 = _slot(r.get("from"), -260), _slot(r.get("to"), 2180)
        except CardError as e:
            raise CardError(f"{where}: compose row {i + 1} ({what}): {e}")
        rng = random.Random(f"{seed}:{what}:{i}:{y0}")
        n = int(r.get("n", 0))
        gap = float(r.get("gap", (x1 - x0) / max(1, n - 1) if n > 1 else 220 * ps(y0) * float(dw.get("size", 1.0)) * 1.6))
        jit = float(r.get("jitter", gap * 0.18))
        spread = float(r.get("spread", 0))
        clear = r.get("clear") or []
        flip_mode = r.get("flip", "random")
        k, x = 0, x0
        while x <= x1 + 0.5 and k < 200:
            xx = x + (rng.uniform(-jit, jit) if x0 != x1 else 0)
            yy = y0 + (rng.uniform(-spread, spread) if spread else 0)
            x += gap if gap > 0 else 1e9
            k += 1
            if any(a <= xx <= b for a, b in clear):
                continue
            s = ps(yy) * float(dw.get("size", 1.0)) * float(r.get("scale", 1.0)) * (rng.uniform(0.9, 1.1) if r.get("vary", True) else 1.0)
            flip = (k % 2 == 0) if flip_mode == "alternate" else (rng.random() < 0.5) if flip_mode == "random" else bool(flip_mode is True)
            item = {"x": round(xx, 1), "y": round(yy, 1), "s": round(s, 4), "phase": round(rng.uniform(0, 3), 2)}
            if flip:
                item["flip"] = True
            if r.get("layer") == "set" or (r.get("layer") != "people" and yy < hz + 110):
                set_rows.append((dw["parts"], item))
            else:
                el = {"kind": "drawing", "id": f"row{i}_{k}", "x": round(xx), "y": round(yy), "scale": round(s, 4), "parts": dw["parts"],
                      "phase": item["phase"], "depthY": round(yy + k * 0.001, 3), "enter": "none"}
                if flip:
                    el["flip"] = True
                els.append(el)
    if set_rows:
        grouped = {}
        for parts, item in set_rows:
            grouped.setdefault(id(parts), {"parts": parts, "items": []})["items"].append(item)
        st["setRows"] = list(grouped.values())
    for k in ("time", "weather"):
        if spec.get(k):
            st[k] = spec[k]
    return st, els


def _style_items(style):
    """the default modules of a room style (read from src/sets/Kit.tsx)"""
    src = (TOOLS.parent / "src/sets/Kit.tsx").read_text(encoding="utf-8")
    m = re.search(r"^\s{2}" + re.escape(style) + r": \{[^\n]*items: \[([^\]]*)\]", src, re.M)
    return re.findall(r"'([^']+)'", m.group(1)) if m else []


def _check_flags(c, st, items, word):
    """a flag must say whose it is: the wrong flag on a wall is a factual error the viewer notices at once"""
    if st.get("nation"):
        return
    for it in items or []:
        name = it if isinstance(it, str) else (it or {}).get("item", "")
        has_arg = (isinstance(it, str) and ":" in it) or (isinstance(it, dict) and (it.get("arg") or it.get("nation") or ":" in it.get("item", "")))
        if name.split(":")[0] in ("flag", "banner", "townhall") and not has_arg:
            _warn(c, f"place \"{c.raw.get('place_id') or c.raw.get('where')}\" shows a {word} without saying whose: write \"{name.split(':')[0]}:<NATION>\" "
                     f"(e.g. {name.split(':')[0]}:AUS, {name.split(':')[0]}:UK) or give the place a \"nation\". Without it the engine draws the German flag.")
            return


def _check_items(c, items, known, what):
    if items is None:
        return None
    out = []
    for it in items:
        name = (it if isinstance(it, str) else (it or {}).get("item", "")).split(":")[0]
        if name in known:
            out.append(it)
        else:
            near = _near(name, known)
            _warn(c, f"{what} \"{name}\" does not exist in the kit (skipped). Did you mean {near}? It was logged in work/missing_assets.json.")
            _missing(c, what, name, "skipped")
    return out


# ------------------------------------------------------------------ WHO
class Actor:
    def __init__(self, aid, who, x, y, world, size=1.0):
        self.id, self.who, self.x, self.y = aid, who, x, y
        self.world, self.size = world, size
        self.keys = {}
        self.fixed = []        # times of explicit keys (auto acting keeps away from them)
        self.busy = []         # (t0, t1) business: no auto gestures
        self.moves = []        # (t0, t1)
        self.talks = []        # (t0, t1)
        self.extra = {}
        self.crowd = False

    def scale(self, y=None):
        w = self.world
        hz = w.get("horizon", 560)
        return max(0.05, w["scale"] * ((self.y if y is None else y) - hz) / max(1, w["y"] - hz)) * self.size

    def key(self, t, fixed=True, **kv):
        t = round(max(0.0, t), 2)
        self.keys.setdefault(t, {}).update(kv)
        if fixed:
            self.fixed.append(t)

    def free(self, t, gap=0.7):
        if any(abs(t - f) < gap for f in self.fixed):
            return False
        return not any(a - 0.3 <= t <= b + 0.3 for a, b in self.busy + self.moves)

    def pos_at(self, t):
        x, y = self.x, self.y
        for tk in sorted(self.keys):
            if tk <= t and "x" in self.keys[tk]:
                x = self.keys[tk]["x"]
            if tk <= t and "y" in self.keys[tk]:
                y = self.keys[tk]["y"]
        return x, y


def _slot(v, default=960):
    if v is None:
        return default
    if isinstance(v, (int, float)):
        return float(v)
    if v in SC.SLOTS:
        return SC.SLOTS[v]
    raise CardError(f"position \"{v}\" is not a slot. Use one of {list(SC.SLOTS)} or a number of px.")


def _depth(v, default="mid"):
    v = default if v is None else v
    if isinstance(v, (int, float)):
        return float(v)
    if v in SC.DEPTHS:
        return SC.DEPTHS[v]
    raise CardError(f"depth \"{v}\" is not allowed. Use one of {list(SC.DEPTHS)} or a number (screen y of the feet, 800-1040).")


def _facing(actor, target_x=None, side=None):
    """(flip, turn) so the actor faces screen-left or screen-right (the right hand, which gestures, leads)."""
    if side is None:
        side = "right" if (target_x or 960) >= actor.x else "left"
    if side == "right":
        return False, 0.38
    if side == "left":
        return True, 0.38
    return False, 0.0


HOLD_POSE = {"basket": "basket", "sack": "carry", "baby": "cradle", "crate": "carry", "rifle": "port", "binoculars": "binoculars",
             "paper": "hold", "letter": "hold", "telegram": "hold", "card": "hold", "folder": "hold", "bowl": "hold", "pot": "hold",
             "bread": "hold", "turnip": "show", "cup": "drink", "lantern": "basket", "bucket": "basket", "suitcase": "basket", "coins": "hold"}
BIG_HOLDS = {"basket", "sack", "baby", "crate", "rifle", "pot", "bucket", "suitcase", "binoculars"}
DEFAULT_SLOTS = {1: ["center"], 2: ["center_left", "center_right"], 3: ["left", "center", "right"], 4: ["left", "center_left", "center_right", "right"],
                 5: ["far_left", "left", "center", "right", "far_right"]}
SPEED = {"walk": 165, "shuffle": 70, "limp": 85, "march": 165, "sneak": 90, "run": 430, "ride": 280}


def _people(c, place, rng):
    specs = c.p("people") or []
    if not isinstance(specs, list):
        raise CardError(f"{_where(c.raw)}: \"people\" must be a list of persons, e.g. [{{\"who\": \"mother\", \"at\": \"center\"}}].")
    actors, used = {}, set()
    slots = DEFAULT_SLOTS.get(len(specs), list(SC.SLOTS)[:7])
    for i, p in enumerate(specs):
        if not isinstance(p, dict) or not p.get("who"):
            raise CardError(f"{_where(c.raw)}: person {i + 1} needs \"who\" (a cast id from cards/_film.json or a preset from recipes/PEOPLE.md).")
        who = p["who"]
        if who not in c.cast and who not in vocab()["presets"]:
            raise CardError(f"{_where(c.raw)}: person \"{who}\" is neither in cards/_film.json \"cast\" nor a preset. Did you mean {_near(who, list(c.cast) + sorted(vocab()['presets']))}? "
                            f"Add new people (a mother, a baker, an admiral) to the cast with a preset and a look (playbook/scene-writing.md §3).")
        aid = p.get("id") or (who if who not in used else f"{who}_{i + 1}")
        used.add(aid)
        try:
            x = _slot(p.get("at"), SC.SLOTS[slots[i % len(slots)]] if i < len(slots) else 960)
            y = _depth(p.get("depth"))
        except CardError as e:
            raise CardError(f"{_where(c.raw)}: person \"{aid}\": {e}")
        a = Actor(aid, who, x, y, place["world"], float(p.get("size", c.cast.get(who, {}).get("size", 1.0))))
        mood = p.get("mood", "neutral")
        if mood not in SC.MOODS:
            near = _near(mood, SC.MOODS) or ["neutral"]
            _warn(c, f"person \"{aid}\": mood \"{mood}\" is unknown, used \"{near[0]}\". Moods: {list(SC.MOODS)}.")
            mood = near[0]
        a.mood = mood
        a.expr = p.get("expr") or SC.MOODS[mood][0]
        a.rest = p.get("pose") or ("idle" if mood in ("neutral", "happy") else SC.MOODS[mood][3][0])
        if a.rest not in vocab()["poses"]:
            _warn(c, f"person \"{aid}\": pose \"{a.rest}\" does not exist (used idle). Poses are listed in recipes/STAGECRAFT.md.")
            a.rest = "idle"
        a.holds = p.get("holds")
        if a.holds and not p.get("pose"):
            a.rest = HOLD_POSE.get(a.holds, "hold")
        a.pose0 = a.rest
        a.seated, a.kneel = bool(p.get("seated")), bool(p.get("kneel"))
        a.walk = p.get("walk")
        a.face = p.get("face")
        a.spec = p
        if p.get("rides"):
            a.extra["ride"] = _ride_kv(c, p["rides"])
            a.holds = None
            if not p.get("pose"):
                a.rest = a.pose0 = "ride"
        if p.get("name_card") and not c.raw.get("name_card"):
            c.raw["name_card"] = who
        actors[aid] = a
    # nobody stands inside anybody: people on (almost) the same depth keep about a body apart
    lst = sorted(actors.values(), key=lambda a: a.x)
    for _ in range(3):
        for a, b in zip(lst, lst[1:]):
            if abs(a.y - b.y) < 45:
                need = 120 * max(a.scale(), b.scale())
                if b.x - a.x < need:
                    d = (need - (b.x - a.x)) / 2
                    a.x -= d
                    b.x += d
    return actors


# ------------------------------------------------------------------ crowds
CIVILIANS = ["civilian_woman", "civilian_man", "worker", "civilian_woman", "civilian_man"]


def _crowd(c, place, actors, rng, focus_x):
    specs = c.p("crowd")
    if not specs:
        return
    specs = specs if isinstance(specs, list) else [specs]
    T = c.dur
    for ci, cr in enumerate(specs):
        kind = cr.get("kind", "watchers")
        if kind not in SC.CROWDS:
            raise CardError(f"{_where(c.raw)}: crowd kind \"{kind}\" does not exist. Use one of {list(SC.CROWDS)}.")
        n = int(cr.get("n", 6))
        who = cr.get("who") or CIVILIANS
        who = who if isinstance(who, list) else [who]
        for w in who:
            if w not in c.cast and w not in vocab()["presets"]:
                raise CardError(f"{_where(c.raw)}: crowd person \"{w}\" is neither a cast id nor a preset. Did you mean {_near(w, sorted(vocab()['presets']))}?")
        mood = cr.get("mood", "neutral" if kind not in ("mourners",) else "grief")
        mood = mood if mood in SC.MOODS else "neutral"
        x0 = _slot(cr.get("at"), 960)
        y0 = _depth(cr.get("depth"), "back")
        toward = cr.get("toward")
        tdir = 1 if toward == "right" else -1 if toward == "left" else (1 if focus_x > x0 else -1)
        for j in range(n):
            aid = f"c{ci}_{j}"
            jitter = rng.uniform(-14, 14)
            if kind == "queue":
                x, y = x0 - tdir * j * 112, y0 + ((j % 2) * 22 - 8) + jitter * 0.3
            elif kind in ("walkers",):
                x, y = 0, y0 + rng.choice([-40, 0, 40, 80])
            elif kind == "marchers":
                # "start": "in" = the column is already in the frame, its head at "at" (short shots)
                x, y = (x0 if cr.get("start") == "in" else -260) - j * 130, y0 + (j % 2) * 28
            elif kind == "cyclists":
                ab = int(cr.get("abreast", 3))
                lane, row = j % ab, j // ab
                # "start": "in" = the first row is already in the frame at "at" (short shots); default: they ride in from the edge
                xs = x0 if cr.get("start") == "in" else (-260 if tdir > 0 else 2180)
                # lanes side by side: the nearer lane rides a little behind, so the riders of a row do not cover each other
                x, y = xs - tdir * (row * 190 + lane * 48) + rng.uniform(-20, 20), y0 + lane * 40
            else:
                cols = max(1, (n + 1) // 2)
                x = x0 + ((j // 2) - (cols - 1) / 2) * 150 + rng.uniform(-30, 30)
                y = y0 + (j % 2) * 46 + jitter
            a = Actor(aid, who[j % len(who)], x, y, place["world"])
            a.crowd, a.mood, a.spec = True, mood, cr
            a.expr = SC.MOODS[mood][0]
            pal = SC.MOODS[mood][3]
            a.rest = {"queue": pal[j % len(pal)] if mood != "neutral" else ["wait", "idle", "behind", "pockets"][j % 4],
                      "mourners": ["pray", "wait", "cry", "heart"][j % 4], "cheering": ["cheer", "clap", "wave", "cheer"][j % 4],
                      "workers": ["hammer", "carry", "push", "hammer"][j % 4], "protest": ["fist", "point", "fist", "cheer"][j % 4],
                      "marchers": "shoulder"}.get(kind, SC.MOODS[mood][2][j % len(SC.MOODS[mood][2])])
            a.pose0, a.holds, a.seated, a.kneel, a.face = a.rest, None, False, False, None
            a.walk = "march" if kind == "marchers" else ("shuffle" if mood in ("hungry", "tired", "cold", "grief") else None)
            if kind == "workers" and a.rest == "carry":
                a.holds = "crate"
            if kind == "cyclists":
                a.rest, a.pose0 = "ride", "ride"
                a.extra["ride"] = _ride_kv(c, cr.get("vehicle", "bicycle"))
                sp = SPEED["ride"] * a.scale() * rng.uniform(0.95, 1.05)
                a.key(0, fixed=False, x=round(x), y=round(y), flip=tdir < 0)
                a.key(T, fixed=False, x=round(x + tdir * sp * T), y=round(y), ease="linear")
                a.moves.append((0, T))
                a.expr = rng.choice(["happy", "smile", "laugh", "neutral"])
                if rng.random() < 0.5:
                    t0 = rng.uniform(0, max(0.1, T - 1.5))
                    a.key(t0, fixed=False, talk=True)
                    a.key(t0 + rng.uniform(0.8, 1.6), fixed=False, talk=False)
            elif kind == "marchers":
                a.holds = "rifle"
                sp = SPEED["march"] * a.scale()
                a.key(0, fixed=False, x=x, y=y)
                a.key(T, fixed=False, x=round(x + sp * T), y=y, ease="linear")
                a.moves.append((0, T))
            elif kind == "walkers":
                d = rng.choice([1, -1])
                sp = SPEED["walk"] * a.scale() * rng.uniform(0.8, 1.2)
                t0 = rng.uniform(-T * 0.5, T * 0.5)
                xs = -200 if d > 0 else 2120
                a.x = xs + d * sp * max(0, -t0)
                a.key(0, fixed=False, x=round(a.x), y=y)
                a.key(T, fixed=False, x=round(a.x + d * sp * T), y=y, ease="linear")
                a.flip = d < 0
                a.moves.append((0, T))
                if rng.random() < 0.35:
                    a.rest, a.holds = rng.choice([("basket", "basket"), ("carry", "sack")])
                    a.pose0 = a.rest
            elif kind == "queue":
                a.face = "right" if tdir > 0 else "left"
                xq = x
                for tt in (T * 0.38, T * 0.74):
                    if tt > 1.2 and T - tt > 0.8:
                        ts = tt + j * 0.18
                        a.key(ts, fixed=False, x=round(xq), y=round(y))
                        xq += tdir * 36 * a.scale()
                        a.key(ts + 0.9, fixed=False, x=round(xq), y=round(y), ease="smooth")
            elif kind in ("watchers", "listeners", "mourners", "cheering", "protest"):
                a.face = "right" if focus_x > x else "left"
            if kind != "walkers":
                a.x = x
            a.y = y
            if cr.get("view") == "back":
                # an audience between us and the speaker: heads and shoulders along the bottom edge of the frame, never in
                # front of the focus person (a big back in the middle of the frame hides the one we came to see)
                a.view0, a.face = "back", "away"
                lanes = [x for x in (170, 470, 770, 1150, 1450, 1750) if abs(x - focus_x) > 260] or [170, 1750]
                a.x = lanes[j % len(lanes)] + rng.uniform(-40, 40)
                a.y = 1215 + (j % 2) * 30
                a.fixed_scale = round(1.75 + (j % 2) * 0.15, 2)
            actors[aid] = a
        if kind == "cyclists":
            c.raw.setdefault("_crowd_sfx", []).append({"t": 0.0, "id": "bicycle", "vol": 0.45, "dur": round(min(8.0, T), 2)})
        if cr.get("react_on"):
            tr = c.t(cr["react_on"])
            for j in range(n):
                a = actors[f"c{ci}_{j}"]
                a.key(tr + 0.12 * (j % 4), expr=cr.get("expr", "shocked"))


# ------------------------------------------------------------------ DOES
def _act_time(c, act, k, n_acts, prev_t):
    if act.get("on") is not None:
        return c.t(act["on"])
    if k == 0:
        return 0.0
    return round(prev_t + (c.dur - prev_t) / (n_acts - k + 1), 2)


def _target_x(c, actors, to, me):
    if to is None:
        return None
    if isinstance(to, (int, float)):
        return float(to)
    if to in actors:
        return actors[to].pos_at(99)[0]
    if to in SC.SLOTS:
        return SC.SLOTS[to]
    if to in ("left", "right"):
        return me.x + (-400 if to == "left" else 400)
    raise CardError(f"{_where(c.raw)}: \"to\": \"{to}\" is neither a person in this card ({list(actors)}) nor a slot ({list(SC.SLOTS)}).")


def _acts(c, actors, sfx, drops):
    snow = (c.raw.get("weather") == "snow")
    for a in [x for x in actors.values() if not x.crowd]:
        a.cur_hold = a.holds
        acts = a.spec.get("do") or []
        if isinstance(acts, dict) or isinstance(acts, str):
            acts = [acts]
        acts = [{"act": q} if isinstance(q, str) else dict(q) for q in acts]
        prev = 0.0
        timed = []
        for k, q in enumerate(acts):
            name = q.get("act")
            if name not in SC.ACTS:
                near = _near(name, SC.ACTS) or (["say"] if "talk" in str(name) else ["react"])
                _warn(c, f"person \"{a.id}\": act \"{name}\" is unknown — used \"{near[0]}\". Acts are listed in recipes/STAGECRAFT.md (logged in work/missing_assets.json).")
                _missing(c, "act", name, near[0])
                name = q["act"] = near[0]
            t = _act_time(c, q, k, len(acts), prev)
            prev = t
            timed.append((t, q))
        timed.sort(key=lambda z: z[0])
        for idx, (t, q) in enumerate(timed):
            name = q["act"]
            spec = SC.ACTS[name]
            t_next = timed[idx + 1][0] if idx + 1 < len(timed) else c.dur
            t_till = c.t(q["till"]) if q.get("till") else None
            end = min(t_next, t_till) if t_till is not None else t_next
            to = q.get("to")
            if spec["kind"] == "pose" or name == "fire":
                kv = {"pose": spec["pose"]}
                h = q.get("with", spec.get("holds"))
                if h is not None:
                    kv.update(_hold_kv(c, h))
                elif a.cur_hold in BIG_HOLDS and spec["pose"] not in HOLDING_POSES:
                    # arms full and the act needs a free hand: the thing is put down first (it stays on the floor)
                    kv.update(_hold_kv(c, ""))
                    drops.append({"what": a.cur_hold, "x": a.pos_at(t)[0] + (-70 if a.keys.get(0, {}).get("flip") or getattr(a, "flip0", False) else 70) * a.scale(),
                                  "y": a.pos_at(t)[1] + 4, "s": a.scale(), "t": t})
                    a.cur_hold = None
                if h is not None:
                    a.cur_hold = h or None
                if q.get("expr") or spec.get("expr"):
                    kv["expr"] = q.get("expr") or spec["expr"]
                if t <= 0.01:
                    a.pose0 = spec["pose"]
                    if h is not None:
                        a.holds = h or None
                    if kv.get("expr"):
                        a.expr = kv["expr"]
                a.key(t, **kv)
                if to is not None:
                    fl, tu = _facing(a, _target_x(c, actors, to, a))
                    a.key(t, flip=fl, turn=tu)
                if name in SC.BUSY:
                    a.busy.append((t, end))
                if spec.get("sfx"):
                    sid, vol = spec["sfx"]
                    reps = 3 if name == "knock" else 1
                    for r in range(reps):
                        sfx.append({"t": round(t + 0.35 + r * 0.24, 2), "id": sid, "vol": vol})
                if name == "fire":
                    a.extra.setdefault("fireAt", []).extend([round(t + 0.5, 2), round(t + 1.4, 2)])
                    sfx += [{"t": round(t + 0.5, 2), "id": "rifle"}, {"t": round(t + 1.4, 2), "id": "rifle"}]
                if t_till is not None:
                    a.key(t_till, pose=a.rest)
            elif name == "say":
                t1 = t_till if t_till is not None else (t_next if idx + 1 < len(timed) and timed[idx + 1][1]["act"] == "say" else c.dur - 0.15)
                a.key(t, talk=True)
                a.key(t1, talk=False)
                a.talks.append((t, t1))
            elif name in ("react", "laugh", "shout", "sigh", "freeze", "look_up", "look_down"):
                kv = {"expr": q.get("expr") or spec.get("expr") or SC.MOODS[a.mood][0]}
                if spec.get("pose"):
                    kv["pose"] = spec["pose"]
                if name in ("look_up", "freeze"):
                    kv["turn"] = 0.0
                    kv["look"] = 0
                if name == "look_down":
                    kv["pose"] = "wait"
                a.key(t, **kv)
                if name == "laugh":
                    a.key(t, headMove="nod")
                    a.key(t + 1.2, headMove="")
                if name == "shout":
                    a.key(t, talk=True)
                    a.key(t + 1.3, talk=False)
            elif name in ("nod", "shake_head"):
                a.key(t, headMove="nod" if name == "nod" else "shake")
                a.key(t + 1.1, headMove="")
            elif name in ("look_at", "turn_to", "look_away"):
                tx = _target_x(c, actors, to, a)
                if tx is None:
                    raise CardError(f"{_where(c.raw)}: person \"{a.id}\": act \"{name}\" needs \"to\" (a person id, a slot, left or right).")
                fl, tu = _facing(a, tx)
                if name == "look_away":
                    fl = not fl
                a.key(t, flip=fl, turn=tu, look=0.6, view="front")
            elif name == "look_around":
                a.key(t, look=-0.9)
                a.key(t + 0.8, look=0.9)
                a.key(t + 1.6, look=0)
            elif name == "turn_away":
                a.key(t, view="back")
            elif name == "turn_back":
                a.key(t, view="front")
            elif name in ("sit", "stand_up"):
                a.key(t, seated=(name == "sit"))
                a.needs_chair = True
            elif name in ("kneel", "rise"):
                a.key(t, kneel=(name == "kneel"))
            elif name == "fall":
                a.extra["fallAt"] = round(t, 2)
                a.extra["fallDir"] = 1 if a.keys.get(0, {}).get("flip") else -1
                a.key(t, expr="shocked")
                sfx.append({"t": round(t + 0.5, 2), "id": "thud", "vol": 0.6})
            elif name == "give":
                rcv = actors.get(to) if isinstance(to, str) else None
                if rcv is None:
                    raise CardError(f"{_where(c.raw)}: person \"{a.id}\": \"give\" needs \"to\": the id of a person in this card ({list(actors)}).")
                thing = q.get("with") or a.holds or "paper"
                if not a.holds:
                    a.holds = thing
                gap = abs(rcv.pos_at(t)[0] - a.pos_at(t)[0])
                if gap > 380:  # too far for a hand-over: the giver steps up to the receiver first
                    dur_w = (gap - 155 * a.scale()) / (SPEED["walk"] * a.scale())
                    _move(c, a, "walk_to", {"to": rcv.id, "pose": HOLD_POSE.get(thing, "hold")}, max(0.0, t - dur_w - 0.15), actors, sfx, snow)
                    t = round(max(t, a.moves[-1][1] + 0.1), 2)
                fl, tu = _facing(a, rcv.x)
                a.key(max(0, t - 0.5), flip=fl, turn=tu)
                a.key(t, pose="give", **_hold_kv(c, thing))
                a.key(t + 0.8, pose=a.rest if a.rest not in HOLDING_POSES else "idle", **_hold_kv(c, ""))
                a.cur_hold = None
                fl2, tu2 = _facing(rcv, a.x)
                rcv.key(max(0, t - 0.3), flip=fl2, turn=tu2)
                rcv.key(t + 0.5, pose="reach")
                rcv.key(t + 0.8, pose=HOLD_POSE.get(thing, "hold"), **_hold_kv(c, thing))
                rcv.busy.append((t, t + 2.0))
                sfx.append({"t": round(t + 0.7, 2), "id": "paper" if thing in ("paper", "letter", "card", "telegram") else "pop", "vol": 0.4})
            elif spec["kind"] == "move":
                _move(c, a, name, q, t, actors, sfx, snow)


def _move(c, a, name, q, t, actors, sfx, snow):
    spec = SC.ACTS[name]
    riding = bool(a.extra.get("ride"))
    style = None if riding else (spec.get("style") or q.get("walk") or a.walk)
    speed = SPEED["ride"] if riding else (spec.get("speed") or SPEED.get(style or "walk", 140))
    x0, y0 = a.pos_at(t)
    to = q.get("to")
    if name == "enter":
        side = q.get("from") or ("left" if a.x < 960 else "right")
        xs = -230 if side == "left" else 2150
        tx = _target_x(c, actors, to, a) if to is not None else a.x
        dur = abs(tx - xs) / (speed * a.scale())
        a.x = xs  # waits outside the frame until the phrase
        a.key(t, x=round(xs), y=y0, flip=(tx < xs), turn=0.3)
        if t + dur > c.dur:
            k = (c.dur - t) / dur
            a.key(c.dur, x=round(xs + (tx - xs) * k), y=y0, ease="linear")
            dur = c.dur - t
        else:
            a.key(t + dur, x=round(tx), y=y0, ease="arrive")
        fl, tu = _facing(a, actors[to].x if isinstance(to, str) and to in actors else 960)
        if abs(tx - 960) > 120 or (isinstance(to, str) and to in actors):
            a.key(t + dur + 0.15, flip=fl, turn=tu)
        else:
            a.key(t + dur + 0.15, flip=False, turn=0.1)
        t_start, t_end = t, t + dur
    elif name == "exit":
        side = to if to in ("left", "right") else ("right" if a.x > 960 else "left")
        tx = -260 if side == "left" else 2180
        dur = abs(tx - x0) / (speed * a.scale())
        a.key(t, x=round(x0), y=y0, flip=(tx < x0), turn=0.3, view="front")
        if t + dur > c.dur:
            k = (c.dur - t) / dur
            a.key(c.dur, x=round(x0 + (tx - x0) * k), y=y0, ease="linear")
            dur = c.dur - t
        else:
            a.key(t + dur, x=round(tx), y=y0, ease="leave")
        t_start, t_end = t, t + dur
    else:
        tx = _target_x(c, actors, to, a)
        if tx is None:
            raise CardError(f"{_where(c.raw)}: person \"{a.id}\": \"{name}\" needs \"to\" (a slot, a person id or px).")
        if isinstance(to, str) and to in actors:
            tx = tx + (-155 if tx > x0 else 155) * a.scale()
        ty = _depth(q.get("depth"), "mid") if q.get("depth") else y0
        dist = ((tx - x0) ** 2 + ((ty - y0) * 1.6) ** 2) ** 0.5
        dur = max(0.6, dist / (speed * a.scale()))
        a.key(t, x=round(x0), y=round(y0), flip=(tx < x0), turn=0.3, view="front")
        if t + dur > c.dur:  # still walking when the scene ends: keep the pace through the cut
            k = (c.dur - t) / dur
            a.key(c.dur, x=round(x0 + (tx - x0) * k), y=round(y0 + (ty - y0) * k), ease="linear")
            dur = c.dur - t
        else:
            a.key(t + dur, x=round(tx), y=round(ty), ease="smooth")
        if isinstance(to, str) and to in actors:
            fl, tu = _facing(a, actors[to].x)
            a.key(t + dur + 0.1, flip=fl, turn=tu)
        t_start, t_end = t, t + dur
    if style:
        a.extra["walkStyle"] = style
    a.key(t_start, pose=q.get("pose") or ("ride" if riding else "idle" if a.rest not in ("carry", "sack", "basket", "cradle", "shoulder", "port") else a.rest))
    a.moves.append((t_start, t_end))
    if riding and t_end - t_start > 0.5:
        sfx.append({"t": round(max(0.0, t_start), 2), "id": "bicycle", "vol": 0.4, "dur": round(min(6.0, t_end - t_start), 2)})
    elif t_end - t_start > 0.5:
        sfx.append({"t": round(max(0.0, t_start), 2), "id": "footsteps_snow" if snow else "footsteps", "vol": 0.35, "dur": round(min(6.0, t_end - t_start), 2)})


# ------------------------------------------------------------------ auto acting: people are never frozen
def _anchor_words(c, t0, t1, min_gap=1.4):
    """stressed words (long words, numbers, names) between t0 and t1 (scene seconds) -> gesture times"""
    out = []
    for w in c.W.words[c.i0:c.i1 + 1]:
        ts = w["start"] - c.start
        if ts < t0 + 0.25 or ts > t1 - 0.45:
            continue
        word = re.sub(r"[^\w]", "", w["w"])
        stressed = len(word) >= 6 or word[:1].isupper() or any(ch.isdigit() for ch in word)
        if stressed and (not out or ts - out[-1] >= min_gap):
            out.append(round(ts, 2))
    return out


def _auto_life(c, actors, rng):
    T = c.dur
    talks = [(a.id, t0, t1) for a in actors.values() for t0, t1 in a.talks]
    for a in actors.values():
        if a.spec.get("still"):
            continue
        talk_pal, listen_pal, idle_pal = SC.MOODS[a.mood][1:]
        if a.seated:
            idle_pal = listen_pal = [p for p in ("idle", "chin", "wait", "cross", "think") if p != "think" or a.mood == "neutral"]
        if a.holds in BIG_HOLDS:  # arms full: no gestures, only glances
            talk_pal = listen_pal = idle_pal = [a.rest]
        last = a.pose0
        # 1. talking: a new gesture on stressed words
        for t0, t1 in a.talks:
            if any(b0 - 0.2 <= t0 <= b1 for b0, b1 in a.busy):
                continue
            for ts in _anchor_words(c, t0, t1, 1.5 if a.crowd else 1.3):
                if not a.free(ts - 0.15, 0.6):
                    continue
                g = rng.choice([p for p in talk_pal if p != last] or talk_pal)
                a.key(ts - 0.15, fixed=False, pose=g)
                last = g
            if a.free(t1 + 0.1, 0.4):
                a.key(t1 + 0.1, fixed=False, pose=a.rest)
                last = a.rest
        # 2. listening: someone else talks
        for sid, t0, t1 in talks:
            if sid == a.id or a.crowd and rng.random() < 0.5:
                continue
            ts = t0 + rng.uniform(0.5, 1.0)
            spk = actors[sid]
            if a.face is None and a.free(ts - 0.2, 0.5) and abs(spk.x - a.x) > 40:
                fl, tu = _facing(a, spk.x)
                a.key(ts - 0.2, fixed=False, flip=fl, turn=tu * 0.9)
            while ts < t1 - 0.6:
                if a.free(ts):
                    r = rng.random()
                    if r < 0.28 and a.mood in ("neutral", "sad", "determined", "worried", "grief", "tired", "hungry"):
                        a.key(ts, fixed=False, headMove="nod")
                        a.key(ts + 0.9, fixed=False, headMove="")
                    elif r < 0.75:
                        g = rng.choice([p for p in listen_pal if p != last] or listen_pal)
                        a.key(ts, fixed=False, pose=g)
                        last = g
                ts += rng.uniform(2.4, 3.8)
        # 3. just being there: glances and small changes of stance
        ts = rng.uniform(1.2, 2.6)
        while ts < T - 0.8:
            if a.free(ts, 1.2) and not any(t0 - 0.5 <= ts <= t1 + 0.5 for _, t0, t1 in talks):
                if rng.random() < 0.55:
                    a.key(ts, fixed=False, look=round(rng.uniform(-0.7, 0.7), 2))
                elif not a.crowd or rng.random() < 0.5:
                    g = rng.choice([p for p in idle_pal if p != last] or idle_pal)
                    if g in vocab()["poses"] and not any(b0 <= ts <= b1 for b0, b1 in a.busy):
                        a.key(ts, fixed=False, pose=g)
                        last = g
            ts += rng.uniform(2.8, 4.6) if not a.crowd else rng.uniform(3.5, 6.0)


# ------------------------------------------------------------------ WITH
INDOOR_SETS = {"office", "study", "cabinet", "conference", "warroom", "bunker", "codebreak", "classroom", "kitchen", "home", "factory", "bridge",
               "hangar", "radio", "tent", "corridor", "parliament", "cell", "train_interior", "cockpit", "workshop", "cabin", "hotel", "studio"}


def _things(c, actors, world, drops=(), indoor=False):
    out, placed = [], {}
    hz = world.get("horizon", 560)

    def ps(y):
        return max(0.05, world["scale"] * (y - hz) / max(1, world["y"] - hz))

    for j, th in enumerate(c.p("things") or []):
        th = {"what": th} if isinstance(th, str) else dict(th)
        what = th.get("what")
        dw = drawings(c.film).get(what)
        if not _thing_ok(c, what):
            near = _near(what, list(vocab()["props"]) + list(drawings(c.film)))
            _warn(c, f"thing \"{what}\" is neither an engine prop nor a drawing (skipped). Did you mean {near}? "
                     f"Draw it in cards/_film.json \"drawings\" (playbook/scene-writing.md §5). Logged in work/missing_assets.json.")
            _missing(c, "thing", what, "skipped")
            continue
        tid = th.get("id") or (what if what not in placed else f"{what}_{j + 1}")
        size = (dw.get("size", 1.0) if dw else SC.THINGS.get(what, {}).get("size", 0.6)) * float(th.get("scale", 1.0))
        if th.get("held_by"):
            a = actors.get(th["held_by"])
            if a is None:
                raise CardError(f"{_where(c.raw)}: thing \"{what}\": held_by \"{th['held_by']}\" is not a person in this card ({list(actors)}).")
            a.holds = what
            if dw:
                a.extra["holdsDrawing"] = dw["parts"]
                g = dw.get("grip") or (dw.get("anchors") or {}).get("grip")
                if g:
                    a.extra["holdsGrip"] = g
            if th.get("text"):
                a.extra["holdsText"] = th["text"]
            continue
        on = th.get("on")
        if on and on in placed:
            base = placed[on]
            x = base["x"] + float(th.get("dx", 0)) * base["s"]
            s = ps(base["y"]) * size
            y = base["y"] - base["top"] * base["s"]
            depth_y = base["y"] + 0.5 + j * 0.01
        else:
            if on and on not in placed:
                _warn(c, f"thing \"{tid}\": on \"{on}\" — put \"{on}\" earlier in \"things\" (it was placed on the floor).")
            try:
                x = _slot(th.get("at"), 960)
                y = float(th["y"]) if th.get("y") is not None else _depth(th.get("depth"), "mid")
            except CardError as e:
                raise CardError(f"{_where(c.raw)}: thing \"{tid}\": {e}")
            # "y" = free placement (in the sky, on a wall): screen y and an absolute scale; otherwise sized by its depth
            s = size if th.get("y") is not None else ps(y) * size
            depth_y = None
            if th.get("lift"):
                depth_y = y
                y = y - float(th["lift"]) * s
        el = PROP(what, round(x), round(y), round(s, 3), at=c.t(th["appear"]) if th.get("appear") else 0.0, id=tid)
        if dw:
            el = {"kind": "drawing", "id": tid, "x": round(x), "y": round(y), "scale": round(s, 3), "in": el["in"], "parts": dw["parts"]}
        if th.get("to") is not None:  # a thing that moves (a custom cart, a zeppelin, a boat): from `when` to `till`
            t0 = c.t(th["when"]) if th.get("when") else 0.0
            t1 = c.t(th["till"]) if th.get("till") else c.dur
            el["keys"] = [{"t": round(t0, 2), "x": round(x)}, {"t": round(t1, 2), "x": round(_slot(th["to"], x)), "ease": th.get("ease", "linear")}]
        if depth_y is not None:
            el["depthY"] = round(depth_y, 2)
        for k_src, k_dst in (("text", "text"), ("n", "value"), ("color", "color"), ("on_", "on")):
            if th.get(k_src) is not None:
                el[k_dst] = th[k_src]
        if "lit" in th or "steam" in th:
            el["on"] = bool(th.get("lit", th.get("steam")))
        if th.get("appear"):
            el["enter"] = "pop"
        if th.get("flip"):
            el["flip"] = True
        top = (dw.get("top", 100) if dw else SC.THINGS.get(what, {}).get("top", 100))
        h = (dw.get("h") if dw else None) or SC.THINGS.get(what, {}).get("h", 120)
        placed[tid] = {"x": x, "y": y if depth_y is None else depth_y, "s": s, "what": what, "top": top, "h": h, "draw_y": y}
        if depth_y is not None:
            placed[tid]["y"] = depth_y
        out.append(el)
    # things people put down (a crate before wiping the brow): they stay where they were dropped
    for k, d in enumerate(drops):
        el = PROP(d["what"], round(d["x"]), round(d["y"]), round(d["s"] * SC.THINGS.get(d["what"], {}).get("size", 0.8), 3), at=round(d["t"] + 0.3, 2), id=f"dropped_{k}")
        dw = drawings(c.film).get(d["what"])
        if dw:
            el = {"kind": "drawing", "id": f"dropped_{k}", "x": el["x"], "y": el["y"], "scale": round(d["s"] * dw.get("size", 1.0), 3), "in": el["in"], "parts": dw["parts"]}
        el["enter"] = "none"
        out.append(el)
    # a seat under people who sit: a chair indoors, a crate outside (both are seat-high for the rig)
    for a in actors.values():
        if a.seated or getattr(a, "needs_chair", False):
            seat = a.spec.get("seat") or ("chair" if indoor else "crate")
            if seat != "none":
                out.append(PROP(seat, round(a.x), round(a.y - 2), round(a.scale(), 3), id=f"seat_{a.id}"))
    return out, placed


def _ride_kv(c, rid):
    """the actor element's "ride": the ridden thing's drawing + where the rider sits on it (anchors seat and crank,
    library/README.md §3). The engine draws it under the rider, flips it with him and rolls its wheels."""
    dw = drawings(c.film).get(rid)
    if dw is None or not dw.get("parts"):
        raise CardError(f"{_where(c.raw)}: \"rides\": \"{rid}\" is not a drawing of the library or of this film. Use \"bicycle\", "
                        f"or make it: python tools/lib.py new vehicles {rid} --from bicycle --project <project> (give it anchors seat and crank).")
    an = dw.get("anchors") or {}
    kv = {"parts": dw["parts"], "size": float(dw.get("size", 1.0))}
    for k in ("seat", "crank"):
        if an.get(k):
            kv[k] = an[k]
    return kv


SHIPS = {"battleship", "cruiser", "destroyer", "cargo", "freighter", "carrier", "transport", "uboat", "submarine"}
PLANES = {"bomber", "dakota", "divebomber", "fighter", "glider", "plane"}


def _vehicles(c, world, sfx):
    out = []
    hz = world.get("horizon", 560)
    for j, v in enumerate(c.p("vehicles") or []):
        v = {"type": v} if isinstance(v, str) else dict(v)
        typ = v.get("type")
        if typ not in vocab()["vehicles"]:
            _warn(c, f"vehicle \"{typ}\" does not exist (skipped). Did you mean {_near(typ, vocab()['vehicles'])}?")
            _missing(c, "vehicle", typ, "skipped")
            continue
        x = _slot(v.get("at"), 960)
        y = _depth(v.get("depth"), "back")
        ps = max(0.05, world["scale"] * (y - hz) / max(1, world["y"] - hz))
        base = 0.3 if typ in SHIPS else 0.4 if typ in PLANES else 0.5 if typ in ("boat", "assaultboat") else 0.55
        el = {"kind": "vehicle", "id": v.get("id") or f"{typ}{j + 1}", "type": typ, "x": round(x), "y": round(y),
              "nation": v.get("nation") or (c.film.get("nation") or None)}
        if v.get("scale") is not None or typ in SHIPS or typ in PLANES:
            el["scale"] = round(float(v.get("scale", base * ps)), 3)
        if v.get("flip"):
            el["flip"] = True
        if v.get("to") is not None:
            t0 = c.t(v["on"]) if v.get("on") else 0.0
            t1 = c.t(v["till"]) if v.get("till") else c.dur
            tx = _slot(v["to"], x)
            el["keys"] = [{"t": round(t0, 2), "x": round(x)}, {"t": round(t1, 2), "x": round(tx), "ease": v.get("ease", "linear")}]
            if typ not in SHIPS and typ not in PLANES and typ not in ("cart", "wagon", "horse"):
                sfx.append({"t": round(t0, 2), "id": "truck" if typ in ("truck", "car", "jeep") else "tank_engine", "vol": 0.4, "dur": round(min(6, t1 - t0), 2)})
        if v.get("smoke"):
            el["smoke"] = True
        out.append(el)
    return out


def _effects(c, actors):
    out = []
    for ef in c.p("effects") or []:
        ef = {"fx": ef} if isinstance(ef, str) else dict(ef)
        kind = ef.get("fx")
        if kind not in SC.EFFECTS:
            _warn(c, f"effect \"{kind}\" does not exist (skipped). Use one of {list(SC.EFFECTS)}.")
            _missing(c, "effect", kind, "skipped")
            continue
        t = c.t(ef["on"]) if ef.get("on") else 0.0
        if ef.get("over"):
            a = actors.get(ef["over"])
            if a is None:
                raise CardError(f"{_where(c.raw)}: effect \"{kind}\": over \"{ef['over']}\" is not a person in this card.")
            x, y = a.x + 40 * a.scale(), a.y - 300 * a.scale()
            out.append({"kind": "fx", "type": kind, "x": round(x), "y": round(y), "in": t, "size": round(0.8 * a.scale(), 2), "fixedLayer": True})
            continue
        x = _slot(ef.get("at"), 960)
        y = _depth(ef.get("depth"), "back")
        fx = "smoke" if kind == "steam" else kind
        size = float(ef.get("size", 0.45 if kind == "steam" else 1.0))
        out.append(FX(fx, round(x), round(y), size=size, **{"in": t}))
    return out


# ------------------------------------------------------------------ CAMERA
CAM_ALT = {"wide": "push_in", "push_in": "pan", "pan": "wide", "wide_then_close": "close_then_wide", "close_then_wide": "wide_then_close",
           "medium": "push_in", "close": "medium", "two_shot": "over_shoulder", "group": "wide", "follow": "wide", "over_shoulder": "two_shot",
           "detail_then_wide": "wide_then_close"}


def _camera(c, actors, things, place, rng):
    T = c.dur
    people = [a for a in actors.values() if not a.crowd]
    focus = c.p("focus") or (people[0].id if people else None)
    if focus is not None and focus not in actors and focus not in things:
        raise CardError(f"{_where(c.raw)}: \"focus\": \"{focus}\" is not a person or thing in this card ({list(actors) + list(things)}).")
    partner = c.p("partner") or next((a.id for a in people if a.id != focus), None)
    cam = c.p("camera") or "auto"
    last = c.film.get("_last_cam")
    if cam == "auto":
        moving = focus in actors and actors[focus].moves
        if moving and T > 3.5:
            cam = "follow"
        elif c.p("close_on"):
            cam = "wide_then_close"
        elif len(people) >= 3 or any(a.crowd for a in actors.values()):
            cam = rng.choice(["wide", "pan", "push_in"])
        elif len(people) == 2:
            cam = rng.choice(["two_shot", "wide_then_close", "push_in"])
        elif people:
            cam = rng.choice(["push_in", "medium", "wide_then_close"]) if T > 4 else "medium"
        else:
            cam = rng.choice(["wide", "pan", "push_in"])
        if cam == last:
            cam = CAM_ALT.get(cam, "wide")
    if isinstance(cam, list):
        shots = []
        for q in cam:
            t = c.t(q["on"]) if q.get("on") else 0.0
            on = q.get("frame")
            if on in (None, "wide"):
                shots.append(SHOT(t, None, None, zoom=q.get("zoom", 1.0), push=q.get("push", 0.05)))
            else:
                shots.append(SHOT(t, on, q.get("size", "medium"), push=q.get("push", 0.04), track=q.get("track")))
        return shots, "custom"
    if cam not in SC.CAMERAS:
        raise CardError(f"{_where(c.raw)}: camera \"{cam}\" does not exist. Use one of {list(SC.CAMERAS)} or a list of shots.")
    c.film["_last_cam"] = cam
    tc = c.t(c.p("close_on"), 0.5) if c.p("close_on") else round(T * 0.5, 2)
    fa = actors.get(focus)
    raised = bool(fa) and any((q.get("act") if isinstance(q, dict) else q) in ("hold_up", "cheer", "surrender", "reach_up", "wave")
                              for q in (fa.spec.get("do") or []))
    moving = bool(fa) and bool(fa.moves)
    near_size = "full" if raised else "medium"
    trk = True if moving else None
    tw = c.t(c.p("wide_on"), 0.45) if c.p("wide_on") else round(T * 0.45, 2)
    short = T < 2.6
    wide = lambda t, push=0.05, **kw: SHOT(t, None, None, zoom=kw.pop("zoom", 1.0), push=push, **kw)  # noqa: E731
    fx_side = lambda who: 0.12 if (actors[who].x if who in actors else 960) < 960 else -0.12  # noqa: E731
    if cam == "wide":
        return [wide(0, 0.06)], cam
    if cam == "push_in":
        return [wide(0, 0.22 if T > 5 else 0.14)], cam
    if cam == "pan":
        d = rng.choice([-1, 1])
        return [wide(0, 0.03, zoom=1.16, panX=d * min(260, 50 * T))], cam
    if cam == "wide_then_close":
        return ([wide(0, 0.05)] + ([] if short else [SHOT(tc, focus, near_size, push=0.05, frameX=fx_side(focus), frameY=0.05, track=trk)])), cam
    if cam == "close_then_wide":
        return ([SHOT(0, focus, near_size, push=0.03, frameY=0.05, track=trk)] + ([] if short else [wide(tw, 0.04)])), cam
    if cam == "detail_then_wide":
        d = c.p("detail") or focus
        if d in things:
            th = things[d]
            hh = max(30.0, th["h"] * th["s"])
            first = SHOT(0, None, None, x=round(th["x"]), y=round(th["draw_y"] - hh * 0.6), zoom=round(max(1.6, min(3.0, 1080 / (hh * 4.2))), 2), push=0.05)
        else:
            first = SHOT(0, d, "close", push=0.05, frameY=0.04)
        return ([first] + ([] if short else [wide(tw, 0.04)])), cam
    if cam == "medium":
        return [SHOT(0, focus, near_size, push=0.05, frameX=fx_side(focus), frameY=0.05, track=trk)], cam
    if cam == "close":
        return [SHOT(0, focus, "close", push=0.05, frameY=0.04)], cam
    if cam == "two_shot":
        return [SHOT(0, [focus, partner] if partner else focus, "full", push=0.05)], cam
    if cam == "group":
        return [SHOT(0, [a.id for a in people] or None, "full", push=0.05)], cam
    if cam == "follow":
        return [SHOT(0, focus, "full", track=True, push=0.02)], cam
    if cam == "over_shoulder":
        if not partner:
            raise CardError(f"{_where(c.raw)}: camera over_shoulder needs two people (focus + partner).")
        f, p = actors[focus], actors[partner]
        side = -1 if f.x >= 960 else 1
        p.x, p.y = f.x + side * 400, SC.DEPTHS["front"] + 40
        p.keys = {t: {k: v for k, v in kv.items() if k not in ("x", "y")} for t, kv in p.keys.items()}
        p.face = "away"
        p.view0 = "back"
        fl, tu = _facing(f, p.x)
        f.key(0, flip=fl, turn=tu)
        return [SHOT(0, focus, "medium", push=0.04, frameX=-0.1 * side, frameY=0.05)], cam
    return [wide(0)], cam


def _qa(c, actors):
    """staging checks a viewer would notice: people cut by the frame edge, nobody to look at"""
    for a in actors.values():
        if a.crowd or a.moves or a.spec.get("at") in ("off_left", "off_right"):
            continue
        if a.x < 90 or a.x > 1830:
            _warn(c, f"\"{a.id}\" stands at x {a.x:.0f}, half outside the frame. Use a slot between far_left and far_right, or make them enter/exit.")
    people = [a for a in actors.values() if not a.crowd]
    for a in people:
        for q in a.spec.get("do") or []:
            if isinstance(q, dict) and q.get("act") == "comfort" and q.get("to") in actors:
                b = actors[q["to"]]
                if abs(b.x - a.x) > 260 * a.scale():
                    _warn(c, f"\"{a.id}\" comforts \"{b.id}\" from too far away: put them side by side (one slot apart).")


def _long_shot_cover(c, actors, shots, cam):
    """a set-up held for more than ~6.5 s feels frozen: add one in the middle of every long stretch
    (the focus person if they stand still then, else the people who stand still, framed together)"""
    T = c.dur
    if cam in ("follow", "pan", "custom") or T < 6.5:
        return shots
    people = [a for a in actors.values() if not a.crowd and a.spec.get("at") not in ("off_left", "off_right")]
    if not people:
        return shots
    focus = c.p("focus") if c.p("focus") in actors else people[0].id
    out = sorted(shots, key=lambda q: q["t"])
    for _ in range(3):
        bounds = [q["t"] for q in out] + [T]
        gaps = [(a, b) for a, b in zip(bounds, bounds[1:]) if b - a > 6.5]
        if not gaps:
            break
        a, b = gaps[0]
        t = round((a + b) / 2, 2)
        still = [x for x in people if not any(m0 - 0.3 <= t <= m1 + 0.3 for m0, m1 in x.moves)]
        prev = max((q for q in out if q["t"] <= a), key=lambda q: q["t"])
        if focus in [x.id for x in still] and prev.get("on") != focus:
            add = SHOT(t, focus, "medium", push=0.04, frameY=0.05)
        elif len(still) >= 2:
            add = SHOT(t, [x.id for x in still[:3]], "full", push=0.04)
        elif still:
            add = SHOT(t, still[0].id, "full" if prev.get("size") == "medium" else "medium", push=0.04, frameY=0.05)
        else:
            break
        out = sorted(out + [add], key=lambda q: q["t"])
    return out


# ------------------------------------------------------------------ the recipe
@recipe("scene", "action",
        when="ANY moment the narration describes that no ready-made recipe shows exactly — and most moments of everyday life, politics, the home "
             "front, economics, consequences: a family at supper, a queue at a bakery, an admiral at a chart, dockers unloading cotton, a "
             "farmer in a rotten field. Write the director's `idea` first, then stage it: where, who, what they do on which words, the camera.",
        not_when="A battle, a map move, a chart: use those recipes (assault, wave, map_*, chart). A scene must show people/things doing what the clause says.",
        params={
            "idea": Param("str", required=True, doc="the director's note: what the viewer SEES and why it tells this clause (one sentence, 10+ words). Write it before anything else"),
            "where": Param("str", doc="a story place from cards/_film.json \"sets\", a library place (kampong, rubber_estate…), a room style, a town style, an engine set, or an object {\"room\": \"kitchen\", \"items\": [...]} / {\"compose\": {\"far\": [...], \"ground\": \"grass\", \"rows\": [...]}}"),
            "people": Param("list", doc="persons: {who, id, at, depth, face, mood, pose, holds, seated, kneel, walk, rides (a vehicle drawing, e.g. bicycle: he sits on it and enter/exit/walk_to ride it), size, name_card, do: [{act, on, till, to, with, expr}]}"),
            "crowd": Param("dict", doc="{kind: queue|watchers|walkers|marchers|cyclists|mourners|cheering|workers|protest|listeners, n, who: [presets], at, depth, toward, mood, react_on; cyclists: abreast, vehicle}"),
            "things": Param("list", doc="props: {what, id, at, depth, on (another thing's id), held_by, n, text, color, appear (phrase), scale, steam/lit}"),
            "effects": Param("list", doc="{fx: smoke|fire|explosion|shellburst|dust|steam|sparks|exclaim|question…, at, depth, on, over (person), size}"),
            "vehicles": Param("list", doc="{type: battleship|cruiser|cargo|truck|cart|wagon|horse|train…, nation, at, depth (or screen y, e.g. 660 on the sea), to (moves there), on, till, scale, flip}"),
            "camera": Param("str", doc="wide | push_in | pan | wide_then_close | close_then_wide | detail_then_wide | medium | close | two_shot | group | follow | over_shoulder | auto (default) — or a list of shots [{on, frame, size}]"),
            "focus": Param("str", doc="the person (or thing) the camera favours; default the first person"),
            "partner": Param("str", doc="second person for two_shot / over_shoulder"),
            "close_on": Param("phrase", doc="words where wide_then_close moves in"),
            "wide_on": Param("phrase", doc="words where close_then_wide / detail_then_wide pulls out"),
            "detail": Param("str", doc="the thing id detail_then_wide starts on"),
            "revisit": Param("bool", False, doc="true = this deliberately repeats an earlier composition (a callback); silences the repetition check"),
            "wish": Param("list", doc="things you wanted but the engine lacks (\"a horse-drawn cart\") — logged in work/missing_assets.json for the next engine upgrade"),
            "life": Param("bool", True, doc="false = no automatic gestures (a frozen tableau)"),
        },
        variants=("A",),
        shots="Chosen by `camera` (auto picks from the content and never repeats the previous card's camera). Shots dissolve (0.6 s).",
        example={"at": "Then came a bad harvest.", "recipe": "scene",
                 "says": "A bad harvest made the hunger much worse.",
                 "idea": "A farmer kneels in a grey field and lifts a rotten potato; his wife stands behind him with an empty basket.",
                 "where": "field", "time": "dusk", "weather": "rain",
                 "people": [{"who": "worker", "id": "farmer", "at": "center_left", "depth": "near", "mood": "sad", "kneel": True,
                             "do": [{"act": "hold_up", "with": "turnip", "on": "bad harvest"}]},
                            {"who": "civilian_woman", "at": "center_right", "depth": "back", "mood": "worried", "holds": "basket", "pose": "basket"}],
                 "things": [{"what": "potatoes", "at": "center", "depth": "front", "color": "#5a4a32", "n": 7}],
                 "camera": "wide_then_close", "focus": "farmer", "close_on": "harvest"})
def scene(c):
    if len((c.p("idea") or "").split()) < 10:
        raise CardError(f"{_where(c.raw)}: \"idea\" is too short. Write the director's note first (10+ words): who we see, doing what, where, "
                        f"and why that picture tells \"{c.text[:90]}\". See playbook/scene-writing.md §1.")
    seed = (c.film.get("look") or {}).get("seed", 0)
    rng = random.Random(f"{seed}:{c.raw.get('at', '')}")
    place = _place(c)
    actors = _people(c, place, rng)
    people = [a for a in actors.values()]
    focus_x = actors[c.p("focus")].x if c.p("focus") in actors else (people[0].x if people else 960)
    _crowd(c, place, actors, rng, focus_x)
    sfx = list(c.raw.pop("_crowd_sfx", []))
    drops = []
    _acts(c, actors, sfx, drops)
    things_els, placed = _things(c, actors, place["world"], drops, indoor=place["kind"] == "room" or place["set"].get("kind") in INDOOR_SETS)
    _qa(c, actors)
    # facing: explicit face, else toward the others (or the focus); alone = toward the centre
    for a in actors.values():
        if a.crowd and a.face in (None, "away"):
            continue
        if a.face in ("away", "back"):
            a.view0 = "back"
            fl, tu = False, 0.0
        elif a.face in ("viewer", "front"):
            fl, tu = False, 0.0
        elif a.face in ("left", "right"):
            fl, tu = _facing(a, side=a.face)
        elif a.face in actors:
            fl, tu = _facing(a, actors[a.face].x)
        elif a.face in placed:
            fl, tu = _facing(a, placed[a.face]["x"])
        else:
            others = [b.x for b in actors.values() if b is not a and not b.crowd]
            if others:
                fl, tu = _facing(a, sum(others) / len(others))
            elif abs(a.x - 960) < 140:
                fl, tu = False, 0.12 * (1 if rng.random() < 0.5 else -1)
            else:
                fl, tu = _facing(a, 960)
                tu *= 0.6
        a.flip0, a.turn0 = fl, tu
    if c.p("life", True):
        _auto_life(c, actors, rng)
    shots, cam = _camera(c, actors, placed, place, rng)
    shots = _long_shot_cover(c, actors, shots, cam)
    els = []
    for a in actors.values():
        keys = [{"t": t, **kv} for t, kv in sorted(a.keys.items())]
        if keys and keys[0]["t"] == 0:
            first = keys.pop(0)
            a.flip0 = first.pop("flip", getattr(a, "flip0", False))
            a.turn0 = first.pop("turn", getattr(a, "turn0", 0.0))
            a.x = first.pop("x", a.x)
            a.y = first.pop("y", a.y)
            a.pose0 = first.pop("pose", a.pose0)
            a.expr = first.pop("expr", a.expr)
            if "holds" in first:
                a.holds = first.pop("holds")
            if "seated" in first:
                a.seated = first.pop("seated")
            first.pop("ease", None)
            if first:
                keys.insert(0, {"t": 0.0, **first})
        el = AID(a.id, a.who, round(a.x), round(a.y), getattr(a, "fixed_scale", None), a.pose0, a.expr, keys=keys or None)
        if getattr(a, "flip0", False) or getattr(a, "flip", False):
            el["flip"] = True
        if getattr(a, "turn0", 0):
            el["turn"] = round(a.turn0, 2)
        if getattr(a, "view0", None):
            el["view"] = a.view0
        if a.holds:
            el.update({k: v for k, v in _hold_kv(c, a.holds).items() if v is not None})
        if a.seated:
            el["seated"] = True
        if a.kneel:
            el["kneel"] = True
        if a.size != 1.0:
            el["depthScale"] = a.size
        if a.walk and "walkStyle" not in a.extra:
            el["walkStyle"] = a.walk
        el.update(a.extra)
        els.append(el)
    els += place.get("row_els") or []
    els += things_els
    els += _vehicles(c, place["world"], sfx)
    els += _effects(c, actors)
    st = place["set"]
    amb = None
    if place["kind"] == "room":
        style = st.get("style")
        amb = "basement" if style in ("cellar", "dugout") else "fire" if style in ("farmhouse", "bakery") else "office" if style in ("office", "ministry", "admiralty", "food_office") else "room"
    elif place["kind"] == "town":
        amb = "wind_cold" if (c.raw.get("weather") or st.get("weather")) == "snow" else "crowd" if c.p("crowd") else "wind"
    elif place["kind"] == "compose":
        # the sound of a composed place follows what is in it: the sea, tropical plants (insects and birds), snow, else wind
        tropical = any("tropical" in (drawings(c.film).get(r.get("what"), {}).get("tags") or []) for r in (st.get("_rows_spec") or []))
        wk = c.raw.get("weather") or st.get("weather")
        wk = wk.get("kind") if isinstance(wk, dict) else wk
        amb = (st.get("ambience") or ("rain" if wk in ("rain", "downpour", "drizzle", "lightning") else "sea" if "sea" in (st.get("far") or [])
               else "wind_cold" if st.get("ground") == "snow" or wk in ("snow", "blizzard") else "jungle" if tropical or "jungle" in (st.get("far") or []) else "wind"))
    st.pop("_rows_spec", None)
    if place.get("tag") and not c.raw.get("tag") and not c.raw.get("_tag_done"):
        c.raw["tag"] = place["tag"]
    c.raw["_sig"] = {"where": place["key"], "camera": cam, "people": len([a for a in actors.values() if not a.crowd]),
                     "crowd": (c.p("crowd") or {}).get("kind") if isinstance(c.p("crowd"), dict) else None,
                     "acts": sorted({q.get("act") if isinstance(q, dict) else q for a in actors.values() if not a.crowd for q in (a.spec.get("do") or [])} - {"say", "react", "nod"}),
                     "idea": c.p("idea")}
    for w in c.p("wish") or []:
        _missing(c, "wish", w, "")
    return stage(c, st, els, shots, world=place["world"], ambience=amb, sfx=sorted(sfx, key=lambda q: q["t"]) or None)
