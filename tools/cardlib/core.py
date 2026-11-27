"""Scene cards -> plan.json.

A *card* is one scene (one place, usually 3-10 s of narration) written as a small JSON object:

    {"at": "Attacks on the Western Front", "recipe": "assault", "says": "Frontal attacks gained almost nothing and killed many men.",
     "side": "british", "falls": 3, "hit_on": "cost enormous", "counter": {"to": 57470, "suffix": " CASUALTIES", "on": "fifty-seven"}}

- `at`      the first words of the narration this scene starts on (copied exactly from work/reading.md)
- `recipe`  which picture to build (see recipes/CATALOG.md)
- `says`    what the narration means, in your own plain words (proves the card was understood; never shown)
- the rest  recipe parameters + common modifiers (date, place, name_card, label, counter, stamp, tint, time, weather...)

The compiler resolves every phrase to a time on the voice, builds each scene with its recipe (positions, depth, camera
cuts, motion, sound are computed here, not by the writer), rotates composition variants so scenes do not repeat, and
writes plan.json. Errors are written as instructions: what is wrong and exactly what to change.
"""
from __future__ import annotations

import difflib
import json
import random
import re
import sys
from pathlib import Path

TOOLS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOLS))
import shotlib  # noqa: E402
from shotlib import SHOT  # noqa: E402,F401

from . import sides as SIDES  # noqa: E402

RECIPES: dict[str, "Recipe"] = {}

# ------------------------------------------------------------------ errors written as instructions


class CardError(Exception):
    """An error in one card. The message says what to change."""


def _where(card):
    return f"{card.get('_file', '?')} card #{card.get('_n', '?')} (recipe '{card.get('recipe', '?')}', at \"{card.get('at', '')}\")"


# ------------------------------------------------------------------ narration words and phrase timing
def norm(w: str) -> str:
    return re.sub(r"[^a-z0-9']", "", w.lower().replace("’", "'"))


def tokens(phrase: str) -> list[str]:
    return [t for t in (norm(x) for x in re.split(r"[\s\-–—/]+", phrase)) if t]


class Words:
    """Every narration word with start/end seconds (work/words.json)."""

    def __init__(self, words):
        self.words = words
        # hyphenated words ("seventy-seven") count as several tokens, so phrases match however they are written
        self.tok, self.owner = [], []
        for i, w in enumerate(words):
            for t in tokens(w["w"]):
                self.tok.append(t)
                self.owner.append(i)

    def text(self, i0, i1):
        return " ".join(w["w"] for w in self.words[i0:i1])

    def find(self, phrase, lo=0, hi=None, fuzzy=True):
        """Word indexes (first, last) of `phrase` at/after word lo and before word hi. Exact first, then fuzzy."""
        toks = tokens(phrase)
        if not toks:
            raise KeyError("empty phrase")
        hi = len(self.words) if hi is None else hi
        t_lo = next((k for k, o in enumerate(self.owner) if o >= lo), len(self.tok))
        t_hi = next((k for k, o in enumerate(self.owner) if o >= hi), len(self.tok))
        n = len(toks)
        for k in range(t_lo, max(t_lo, t_hi - n + 1)):
            if self.tok[k:k + n] == toks:
                return self.owner[k], self.owner[k + n - 1], 1.0
        if not fuzzy:
            raise KeyError(phrase)
        best, bk = 0.0, None
        target = " ".join(toks)
        for k in range(t_lo, max(t_lo, min(t_hi, t_lo + 4000) - n + 1)):
            r = difflib.SequenceMatcher(None, " ".join(self.tok[k:k + n]), target).ratio()
            if r > best:
                best, bk = r, k
        if bk is not None and best >= 0.8:
            return self.owner[bk], self.owner[bk + n - 1], best
        raise KeyError(phrase)


def load_words(proj: Path) -> Words:
    f = proj / "work" / "words.json"
    if not f.exists():
        raise CardError("work/words.json is missing. Run first:  python tools/make.py projects/<slug> prepare")
    return Words(json.loads(f.read_text(encoding="utf-8")))


# ------------------------------------------------------------------ recipe registry
WEATHER_KINDS = ["rain", "drizzle", "downpour", "snow", "blizzard", "haze", "fog", "dust", "sandstorm", "ash", "leaves", "petals", "lightning"]


class Param:
    def __init__(self, type_="str", default=None, values=None, doc="", required=False):
        self.type, self.default, self.values, self.doc, self.required = type_, default, values, doc, required


class Recipe:
    def __init__(self, id_, fn, cls, when, not_when, params, variants, example, shots_doc):
        self.id, self.fn, self.cls, self.when, self.not_when = id_, fn, cls, when, not_when
        self.params, self.variants, self.example, self.shots_doc = params, variants, example, shots_doc


def recipe(id_, cls, when, not_when="", params=None, variants=("A",), example=None, shots=""):
    """Register a recipe. cls: action | talk | map | device | host (drives the screen-time mix)."""
    def deco(fn):
        RECIPES[id_] = Recipe(id_, fn, cls, when, not_when, params or {}, tuple(variants), example or {}, shots)
        return fn
    return deco


# common modifiers every card may carry (applied after the recipe)
COMMON = {
    "at": Param("phrase", required=True, doc="first words of the narration where this scene starts (copy them exactly from work/reading.md)"),
    "recipe": Param("str", required=True, doc="recipe id (recipes/CATALOG.md)"),
    "says": Param("str", required=True, doc="what this part of the narration MEANS, in your own words (one sentence, 6+ words)"),
    "variant": Param("enum", "auto", doc="composition variant (A, B, C, D) or auto: the compiler rotates them so scenes never look the same"),
    "date": Param("str", doc="date badge top-left, e.g. \"21 FEBRUARY 1916\" — on every jump in time"),
    "place": Param("str", doc="place badge under the date, e.g. \"VERDUN\""),
    "name_card": Param("who", doc="cast id whose name card shows (first appearance of a person); name/role come from cards/_film.json cast"),
    "label": Param("dict", doc="{\"text\": \"1-5 WORDS\", \"on\": \"phrase\"} a short tag at the top centre"),
    "counter": Param("dict", doc="{\"to\": 57470, \"from\": 0, \"suffix\": \" KILLED\", \"prefix\": \"\", \"on\": \"phrase\", \"color\": \"#f08070\"} a number counting up at the top (over the action)"),
    "stamp": Param("dict", doc="{\"text\": \"FAILED\", \"on\": \"phrase\"} a rubber stamp slammed on screen"),
    "time": Param("enum", values=["day", "dusk", "dawn", "night"], doc="time of day of the place"),
    "weather": Param("weather", doc="weather: rain · drizzle · downpour · snow · blizzard · haze · fog · dust · sandstorm · ash · leaves · petals · lightning, "
                                     "or {\"kind\": \"rain\", \"amount\": 0.9, \"wind\": 0.4} (amount 0..1, wind -1..1; lightning: \"flash\": [seconds])"),
    "tint": Param("enum", values=["sepia", "grey", "cold", "warm", "night", "red"], doc="colour mood: grey = grief, sepia = myth/memory"),
    "letterbox": Param("str", doc="cinema bars for a dramatised moment (about one per chapter): true or a caption"),
    "transition": Param("enum", values=["cut", "fade", "dip", "flash"], doc="how this scene comes in (dip = big jump in time/place)"),
    "ambience": Param("str", doc="override the ambience bed (sea, wind, rain, room, office, battle, crowd, fire, engine, city_night) or \"none\""),
    "sfx": Param("list", doc="extra sounds [{\"on\": \"phrase\", \"id\": \"explosion\"}]"),
    "note": Param("str", doc="free note for humans; ignored"),
    "era": Param("enum", values=["ww1", "ww2", "napoleonic", "ancient", "vietnam", "modern"], doc="rarely needed: this card is in another era than the film (a flashback)"),
    # ---- story continuity and documentary text (playbook/narration-to-picture.md §Storytelling)
    "place_id": Param("str", doc="a short name for a story place that comes back, e.g. \"kaiser_study\". Every card with the same place_id reuses the same setting and place/time tag; change only time/weather to show time passing"),
    "tag": Param("str", doc="place/time tag top-left, e.g. \"Spa, Belgium · 29 September 1918\". Set it on the first card of a place; cards with the same place_id inherit it; it stays put (no re-animation) while the tag does not change"),
    "tag_on": Param("phrase", doc="word(s) where the tag slides in (the date or the place name); default: at the start"),
    "caption": Param("dict", doc="the film's BIG QUESTIONS only (opening, verdict): {\"from\": \"first words\", \"to\": \"last words\", \"accent\": [\"Paris\", \"collapse\"]} -> the words appear as they are spoken at the bottom, accent words in amber. Always on an acted scene"),
    "stat": Param("dict", doc="rarely: one number that must be read, as engraved capitals over the scene: {\"text\": \"About 56 km from Paris\", \"sub\": \"the closest since 1914\", \"top\": \"June 1918\", \"on\": \"fifty-six\"} (at most one every ~2 minutes)"),
    "paper_note": Param("dict", doc="rarely: the exact words of a quote/order typed on a paper note: {\"lines\": [\"Fight on.\", \"Never surrender.\"], \"kicker\": \"Orders, 1944\", \"on\": \"phrase\", \"accent_last\": true}"),
}


# ------------------------------------------------------------------ the card object recipes work with
class Card:
    def __init__(self, raw, film, words, i0, i1, start, end, variant, index):
        self.raw, self.film, self.W = raw, film, words
        self.i0, self.i1 = i0, i1
        self.start, self.end = start, end
        self.dur = round(end - start, 2)
        self.variant = variant
        self.index = index
        self.rng = random.Random(index * 7919 + 13)
        self.text = words.text(i0, i1)
        self.cast = film.get("cast", {})
        self.era = raw.get("era") or film.get("era", "ww2")
        self.recipe = RECIPES[raw["recipe"]]
        self.warns = []  # recipe warnings (unknown acts, things...): reported by the compiler

    # -- parameters
    def p(self, name, default=None):
        if name in self.raw:
            return self.raw[name]
        spec = self.recipe.params.get(name)
        if spec is not None and spec.default is not None:
            return spec.default
        return default

    # -- time of a phrase inside this card, relative to the scene start
    def t(self, phrase, default_frac=0.45, floor=0.3):
        """Seconds from the scene start to the first word of `phrase` (searched inside this card's narration).
        phrase None -> default_frac of the scene. Always clamped inside the scene."""
        if phrase is None or phrase == "":
            return round(max(floor, min(self.dur - 0.4, self.dur * default_frac)), 2)
        if isinstance(phrase, (int, float)):
            return round(max(0.0, min(self.dur - 0.2, float(phrase))), 2)
        try:
            i, _, _ = self.W.find(phrase, self.i0, self.i1 + 2)
        except KeyError:
            raise CardError(f"{_where(self.raw)}: the phrase \"{phrase}\" is not in this card's narration. "
                            f"This card's narration is: \"{self.text}\". Copy 2-5 words from it exactly, or remove the field.")
        return round(max(0.0, min(self.dur - 0.2, self.W.words[i]["start"] - self.start)), 2)

    def t_end(self, phrase):
        i, j, _ = self.W.find(phrase, self.i0, self.i1 + 2)
        return round(min(self.dur, self.W.words[j]["end"] - self.start), 2)

    # -- sides and people
    def side(self, key="side", default=None):
        name = self.p(key, default)
        if name is None:
            name = self.film.get("sides", ["german", "british"])[0 if key == "side" else 1]
        return SIDES.side(name, self.era, self.film)

    def person(self, key, default=None):
        """A cast id or preset name from a parameter (validated)."""
        who = self.p(key, default)
        if who is None:
            return None
        if who not in self.cast and who not in SIDES.PRESETS:
            raise CardError(f"{_where(self.raw)}: '{key}' = \"{who}\" is neither in cards/_film.json \"cast\" nor a preset. "
                            f"Add it to the cast (with a preset) or use a preset from recipes/PEOPLE.md.")
        return who

    def pick(self, *options):
        """The option for this card's variant (A -> first, B -> second, ... wraps)."""
        return options[(ord(self.variant) - 65) % len(options)]


# ------------------------------------------------------------------ scene helpers for recipes
def stage(c: Card, set_, els, shots=None, world=None, **kw):
    s = {"start": round(c.start, 2), "type": "stage", "elements": [e for e in els if e]}
    if set_ is not None:
        s["set"] = dict(set_) if isinstance(set_, dict) else {"kind": set_}
    if shots:
        s["shots"] = sorted(shots, key=lambda q: q["t"])
    if world:
        s["world"] = world
    s.update({k: v for k, v in kw.items() if v is not None})
    return s


def mapscene(c: Card, m, els, camera=None, **kw):
    s = {"start": round(c.start, 2), "type": "map", "map": m, "elements": [e for e in els if e]}
    if camera:
        s["camera"] = camera
    s.update({k: v for k, v in kw.items() if v is not None})
    return s


# ------------------------------------------------------------------ modifiers shared by every recipe
def apply_common(c: Card, s: dict):
    # a recipe that defines a field with a common name (e.g. map_move's arrow "label") handles it itself
    own = set(c.recipe.params) - {"time", "weather"}
    raw = {k: v for k, v in c.raw.items() if k not in own}
    for k in ("date", "place", "tint", "letterbox", "transition"):
        if raw.get(k):
            s[k] = raw[k]
    # documentary film grammar (measured on the reference films): every scene comes in with a 0.6 s cross-dissolve and
    # every change of set-up inside a place dissolves too; hard cuts only when a card asks for "transition": "cut"
    s.setdefault("transition", "fade")
    if s.get("type") == "stage":
        s.setdefault("shotDissolve", True)
    if raw.get("tag"):
        s["tag"] = raw["tag"]
        s["tagIn"] = c.t(raw.get("tag_on"), 0.05, 0.3) + (0.25 if raw.get("tag_on") else 0)
    cap = raw.get("caption")
    if cap:
        try:
            i, _, _ = c.W.find(cap["from"], c.i0, c.i1 + 2)
            _, j, _ = c.W.find(cap["to"], i, c.i1 + 40)
        except (KeyError, TypeError):
            raise CardError(f"{_where(c.raw)}: \"caption\" needs \"from\" and \"to\" = words copied from this card's narration: \"{c.text}\".")
        acc = [a.lower() for a in cap.get("accent", [])]
        words = [{"w": w["w"].strip(), "t": round(w["start"] + 0.05 - c.start, 2),
                  "accent": any(a in w["w"].lower() for a in acc)} for w in c.W.words[i:j + 1]]
        s.setdefault("elements", []).append({"kind": "caption", "words": words})
    st = raw.get("stat")
    if st:
        s.setdefault("elements", []).append({"kind": "stat", "text": st["text"], "sub": st.get("sub"), "top": st.get("top"),
                                             "in": c.t(st.get("on"), 0.3) + 0.25, "y": st.get("y", 330)})
    pn = raw.get("paper_note")
    if pn:
        s.setdefault("elements", []).append({"kind": "note", "lines": pn["lines"], "kicker": pn.get("kicker"), "accentLast": bool(pn.get("accent_last")),
                                             "in": c.t(pn.get("on"), 0.3) + 0.25, "x": pn.get("x", 1380), "y": pn.get("y", 120), "speed": pn.get("speed", 26)})
    if s.get("type") == "stage" and s.get("set"):
        if raw.get("time"):
            s["set"]["time"] = raw["time"]
        if raw.get("weather"):
            s["set"]["weather"] = raw["weather"]
    if raw.get("ambience"):
        s["ambience"] = None if raw["ambience"] == "none" else raw["ambience"]
    els = s.setdefault("elements", [])
    nc = raw.get("name_card")
    if nc:
        who = nc if isinstance(nc, str) else nc.get("who")
        info = c.cast.get(who, {})
        name = (nc.get("name") if isinstance(nc, dict) else None) or info.get("name") or who.replace("_", " ").title()
        role = (nc.get("role") if isinstance(nc, dict) else None) or info.get("role", "")
        els.append({"kind": "namecard", "name": name, "role": role, "in": 0.4 if s.get("type") == "stage" else 0.6})
    lab = raw.get("label")
    if lab:
        lab = {"text": lab} if isinstance(lab, str) else lab
        els.append({"kind": "label", "text": lab["text"], "x": 960, "y": 170, "style": lab.get("style", "tag"), "size": lab.get("size", 44),
                    "in": c.t(lab.get("on"), 0.15), "hud": True})
    cnt = raw.get("counter")
    if cnt:
        els.append({"kind": "counter", "from": cnt.get("from", 0), "to": cnt["to"], "x": 960, "y": 150, "in": c.t(cnt.get("on"), 0.2),
                    "suffix": cnt.get("suffix", ""), "prefix": cnt.get("prefix", ""), "size": cnt.get("size", 70), "dur": cnt.get("dur", 1.8),
                    "hud": True, **({"color": cnt["color"]} if cnt.get("color") else {})})
    st = raw.get("stamp")
    if st:
        st = {"text": st} if isinstance(st, str) else st
        els.append({"kind": "stamp", "text": st["text"], "x": st.get("x", 1380), "y": st.get("y", 520), "in": c.t(st.get("on"), 0.7),
                    "size": st.get("size", 90), "tilt": -8, "hud": True, **({"color": st["color"]} if st.get("color") else {})})
    for q in raw.get("sfx") or []:
        s.setdefault("sfx", []).append({"t": c.t(q.get("on"), 0.3), "id": q["id"], **({"dur": q["dur"]} if q.get("dur") else {})})
    s["beat"] = c.text[:160]
    s["card"] = f"{raw.get('_file')}#{raw.get('_n')}:{raw['recipe']}/{c.variant}"
    return s


# ------------------------------------------------------------------ coverage safety net (from the WW1 film)
def auto_coverage(scenes, end, max_gap=6.0):
    """In a people scene, a set-up held longer than max_gap gets an extra cut at its middle: alternately a close-up on the
    most active on-screen person and a medium of the group."""
    added = 0
    for i, s in enumerate(scenes):
        if s.get("type") != "stage" or s.get("camera"):
            continue
        if ":scene/" in s.get("card", ""):
            continue  # a scene card plans its own camera (recipes_scene._camera adds a second set-up to long shots itself)
        e_end = scenes[i + 1]["start"] if i + 1 < len(scenes) else end
        dur = e_end - s["start"]
        actors = [e for e in s.get("elements", []) if e.get("kind") == "actor" and e.get("view") != "back" and not e.get("lying") and not e.get("silhouette")]
        if not actors:
            continue
        for k, e in enumerate(actors):
            e.setdefault("id", f"a{k}")

        def x_at(e, t):
            ks = sorted([k for k in (e.get("keys") or []) if "x" in k], key=lambda k: k["t"])
            x, t0 = e.get("x", 960), 0.0
            for k in ks:
                if t <= k["t"]:
                    return x + (k["x"] - x) * max(0.0, min(1.0, (t - t0) / max(1e-6, k["t"] - t0)))
                x, t0 = k["x"], k["t"]
            return x
        active = sorted(actors, key=lambda e: (-int(bool(e.get("talk"))), -(e.get("scale") or e.get("y", 900) / 700), -len(e.get("keys") or [])))
        shots = s.get("shots") or [SHOT(0, None, None, zoom=1.0, push=0.03)]
        changed = True
        while changed:
            changed = False
            ts = sorted(q["t"] for q in shots)
            bounds = ts + [dur]
            for a0, b0 in zip(bounds, bounds[1:]):
                if b0 - a0 > max_gap:
                    t = round(a0 + (b0 - a0) / 2, 2)
                    prev = max((q for q in shots if q["t"] <= a0), key=lambda q: q["t"])
                    if prev.get("size") in ("close", "mediumclose", "ecu"):
                        new = SHOT(t, [e["id"] for e in actors[:3]], "medium" if len(actors) > 1 else "full", push=0.03)
                    else:
                        vis = [e for e in active if -60 < x_at(e, t) < 1980] or active
                        movers = [e for e in vis if any("x" in k for k in (e.get("keys") or []))]
                        if len(movers) >= 2:
                            # people on the move (a charge, a column): frame the group, never one giant running face
                            new = SHOT(t, [e["id"] for e in movers[:3]], "full", track=True, push=0.03)
                        else:
                            tgt = vis[len(shots) % len(vis)]
                            new = SHOT(t, tgt["id"], "close" if prev.get("size") != "medium" else "mediumclose",
                                       frameX=0.14 if tgt.get("x", 960) < 960 else -0.14, push=0.04)
                    shots.append(new)
                    added += 1
                    changed = True
                    break
        s["shots"] = sorted(shots, key=lambda q: q["t"])
    return added


# ------------------------------------------------------------------ loading cards
def load_cards(proj: Path):
    d = proj / "cards"
    film_f = d / "_film.json"
    if not film_f.exists():
        raise CardError("cards/_film.json is missing. Copy templates/cards/_film.json into projects/<slug>/cards/ and fill it (playbook/03-cards.md).")
    try:
        film = json.loads(film_f.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise CardError(f"cards/_film.json is not valid JSON: {e}. Fix the comma/quote at that line.")
    cards, chapters = [], []
    files = sorted(f for f in d.glob("ch*.json"))
    if not files:
        raise CardError("No chapter files. Write cards/ch01.json, cards/ch02.json ... (playbook/03-cards.md).")
    for f in files:
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            raise CardError(f"{f.name} is not valid JSON: {e}. Fix the comma/quote at that line (no trailing commas, double quotes only).")
        if isinstance(data, list):
            data = {"cards": data}
        lst = data.get("cards") or []
        for n, raw in enumerate(lst, 1):
            if not isinstance(raw, dict):
                raise CardError(f"{f.name} card #{n} is not an object {{...}}.")
            raw["_file"], raw["_n"] = f.name, n
            if n == 1 and data.get("chapter"):
                raw["_chapter"] = data["chapter"]
            cards.append(raw)
        chapters.append((f.name, data.get("chapter"), len(lst)))
    return film, cards, chapters


# ------------------------------------------------------------------ static checks on one card
def check_card(raw) -> list[str]:
    errs = []
    w = _where(raw)
    rid = raw.get("recipe")
    if not rid:
        return [f"{w}: no \"recipe\". Pick one from recipes/CATALOG.md."]
    if rid not in RECIPES:
        near = difflib.get_close_matches(rid, RECIPES.keys(), n=3)
        return [f"{w}: unknown recipe \"{rid}\". Did you mean {near}? All recipes are listed in recipes/CATALOG.md."]
    r = RECIPES[rid]
    for k in ("at", "says"):
        if not raw.get(k):
            errs.append(f"{w}: missing \"{k}\" — {COMMON[k].doc}.")
    says = raw.get("says", "")
    if says and len(says.split()) < 6:
        errs.append(f"{w}: \"says\" is too short. Write one full sentence (6+ words) with what this narration means.")
    for k, v in raw.items():
        if k.startswith("_"):
            continue
        spec = r.params.get(k) or COMMON.get(k)
        if spec is None:
            near = difflib.get_close_matches(k, list(r.params) + list(COMMON), n=3)
            errs.append(f"{w}: unknown field \"{k}\" for recipe '{rid}'. Allowed: {sorted(r.params)} + common fields. Did you mean {near}?")
            continue
        if spec.type == "enum" and spec.values and v not in spec.values and not (k == "variant" and v in ("auto", "A", "B", "C", "D")):
            errs.append(f"{w}: \"{k}\" = {json.dumps(v)} is not allowed. Use one of {spec.values}.")
        if spec.type == "weather":
            kind = v if isinstance(v, str) else (v.get("kind") if isinstance(v, dict) else None)
            if kind not in WEATHER_KINDS:
                errs.append(f"{w}: \"{k}\" = {json.dumps(v)} is not a weather. Use one of {WEATHER_KINDS} or {{\"kind\": \"rain\", \"amount\": 0.8}}.")
        if spec.type == "int" and not isinstance(v, int):
            errs.append(f"{w}: \"{k}\" must be a whole number, e.g. 3 (no quotes).")
        if spec.type == "bool" and not isinstance(v, bool):
            errs.append(f"{w}: \"{k}\" must be true or false (no quotes).")
        if spec.type == "side" and v not in SIDES.ALL_SIDES:
            errs.append(f"{w}: \"{k}\" = \"{v}\" is not a side. Use one of {sorted(SIDES.ALL_SIDES)}.")
    for k, spec in r.params.items():
        if spec.required and k not in raw:
            errs.append(f"{w}: recipe '{rid}' needs \"{k}\" — {spec.doc}")
    return errs
