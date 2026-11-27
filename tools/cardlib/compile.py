"""Compile cards/*.json -> plan.json (+ checks written as instructions)."""
from __future__ import annotations

import difflib
import json
from pathlib import Path

from . import sides as SIDES
from .core import (RECIPES, Card, CardError, _where, apply_common, auto_coverage, check_card, load_cards, load_words)

# story grammar targets (projects/ember-test/ANALYSIS.md, playbook/narration-to-picture.md): most of the film is ACTED
# (people doing what the sentence says, in a real place: action + talk recipes); maps and documents/charts are short bridges
TARGET = {"acted": 0.75, "map": 0.10, "device": 0.10, "host": 0.08}


def _voice_file(proj: Path):
    inp = proj / "work" / "inputs.json"
    if inp.exists():
        v = json.loads(inp.read_text(encoding="utf-8")).get("voice")
        if v and (proj / v).exists():
            return v
    for ext in ("wav", "mp3", "m4a", "aac", "flac", "ogg"):
        f = proj / "input" / f"voice.{ext}"
        if f.exists():
            return f"input/voice.{ext}"
    return None


def _pick_variant(rid, history, wanted):
    vs = RECIPES[rid].variants
    if wanted and wanted != "auto":
        if wanted not in vs:
            return vs[0], f"variant \"{wanted}\" does not exist for '{rid}' (has {list(vs)}); used {vs[0]}"
        return wanted, None
    used = history.setdefault(rid, [])
    counts = {v: used.count(v) for v in vs}
    last = used[-1] if used else None
    best = sorted(vs, key=lambda v: (counts[v], v == last, vs.index(v)))[0]
    return best, None


def compile_project(proj: Path, write=True):
    proj = Path(proj)
    film, cards, chapters = load_cards(proj)
    W = load_words(proj)
    errors, warns = [], []
    from . import core as CORE
    from . import library as LIBMOD
    presets = LIBMOD.weather_presets(proj)
    CORE.EXTRA_WEATHER = set(presets)
    for raw in cards:
        errors += check_card(raw)
    if errors:
        return {"ok": False, "errors": errors, "warnings": warns}

    # 1. resolve every card's start on the voice (in order)
    starts = []
    cursor = 0
    for k, raw in enumerate(cards):
        try:
            i, j, score = W.find(raw["at"], cursor)
        except KeyError:
            ahead = W.text(cursor, cursor + 40)
            errors.append(f"{_where(raw)}: \"at\" = \"{raw['at']}\" was not found in the narration after the previous card. "
                          f"The narration continues: \"{ahead} …\". Copy the first 3-6 words of this scene from it exactly.")
            starts.append((cursor, cursor))
            continue
        if score < 1.0:
            warns.append(f"{_where(raw)}: \"at\" matched approximately (\"{W.text(i, j + 1)}\"). Copy the words exactly to be safe.")
        if k > 0 and i <= starts[-1][0]:
            errors.append(f"{_where(raw)}: starts at or before the previous card. Cards must follow the narration in order.")
        starts.append((i, j))
        cursor = i + 1
    if errors:
        return {"ok": False, "errors": errors, "warnings": warns}
    end_time = round(W.words[-1]["end"] + 1.5, 2)
    stats = proj / "work" / "stats.json"
    if stats.exists():
        vd = json.loads(stats.read_text(encoding="utf-8")).get("voice_duration")
        if vd:
            end_time = max(end_time, round(vd + 0.6, 2))
    t_start = []
    for k, (i, _) in enumerate(starts):
        t = 0.0 if k == 0 else max(0.0, W.words[i]["start"] - 0.12)
        if k and t < t_start[-1] + 0.8:
            t = t_start[-1] + 0.8
        t_start.append(round(t, 2))

    # 2. build scenes
    history, scenes = {}, []
    places = {}          # place_id -> {"setting": ..., "tag": ..., "first": card}: a story place keeps its look and tag
    cast = json.loads(json.dumps(film.get("cast", {})))
    film["_proj"] = str(proj)  # recipes find this project's own assets (projects/<slug>/assets/<id>/asset.json)
    for k, raw in enumerate(cards):
        i0 = starts[k][0]
        i1 = starts[k + 1][0] if k + 1 < len(cards) else len(W.words)
        end = t_start[k + 1] if k + 1 < len(cards) else end_time
        variant, note = _pick_variant(raw["recipe"], history, raw.get("variant"))
        if note:
            warns.append(f"{_where(raw)}: {note}")
        history.setdefault(raw["recipe"], []).append(variant)
        pid = raw.get("place_id")
        if pid:
            known = places.get(pid)
            rp = RECIPES[raw["recipe"]].params
            if known:
                if "setting" in rp and "setting" not in raw and known.get("setting"):
                    raw["setting"] = known["setting"]
                elif "setting" in rp and raw.get("setting") and known.get("setting") and raw["setting"] != known["setting"]:
                    warns.append(f"{_where(raw)}: place_id \"{pid}\" was \"{known['setting']}\" in {_where(known['first'])}; here it is \"{raw['setting']}\". "
                                 f"A story place keeps its setting (change time/weather to show time passing) — or give this place another place_id.")
                if not raw.get("tag") and known.get("tag"):
                    raw["tag"] = known["tag"]
            else:
                places[pid] = {"setting": raw.get("setting"), "tag": raw.get("tag"), "first": raw}
        c = Card(raw, film, W, i0, i1, t_start[k], end, variant, k)
        try:
            s = RECIPES[raw["recipe"]].fn(c)
            s = apply_common(c, s)
            warns += [f"{_where(raw)}: {m}" for m in c.warns]
        except CardError as e:
            errors.append(str(e))
            continue
        except Exception as e:  # a bug in a recipe: report it plainly
            errors.append(f"{_where(raw)}: recipe '{raw['recipe']}' failed with {type(e).__name__}: {e}. "
                          f"Check the parameter values against recipes/{raw['recipe']}.md; if they are right, report this card.")
            continue
        if raw.get("_chapter"):
            s["chapter"] = raw["_chapter"]
        s["_cls"] = raw.get("class", "action") if raw["recipe"] == "raw" else RECIPES[raw["recipe"]].cls
        s["_raw"] = raw
        scenes.append(s)
    if errors:
        return {"ok": False, "errors": errors, "warnings": warns}

    # 3. people: derived looks ("preset@variant") become cast entries; presets used directly are fine
    for s in scenes:
        for e in s.get("elements", []):
            if e.get("kind") in ("actor", "crowd") and isinstance(e.get("who"), str):
                e["who"] = SIDES.resolve_who(e["who"], cast)
    from . import library as LIBMOD
    try:
        clean_cast = LIBMOD.resolve_cast(cast, proj, film)
    except KeyError as e:
        return {"ok": False, "errors": [f"cards/_film.json {e.args[0]}"], "warnings": warns}
    for cid, spec in clean_cast.items():
        if not spec.get("preset") and not spec.get("outfit"):
            errors.append(f"cards/_film.json cast \"{cid}\": add \"preset\" (a look from recipes/PEOPLE.md), e.g. \"preset\": \"german_officer\".")
        elif spec.get("preset") and spec["preset"] not in SIDES.PRESETS:
            near = difflib.get_close_matches(spec["preset"], SIDES.PRESETS, n=3)
            errors.append(f"cards/_film.json cast \"{cid}\": preset \"{spec['preset']}\" does not exist. Did you mean {near}? (recipes/PEOPLE.md)")
    if errors:
        return {"ok": False, "errors": errors, "warnings": warns}

    # 4. tile, ids, coverage safety net; a tag that does not change stays put (no slide-in) across scenes
    for k, s in enumerate(scenes):
        if k == 0:
            s["transition"] = "cut"
        if k and s.get("tag") and s.get("tag") == scenes[k - 1].get("tag"):
            s["tagIn"] = -1
    for k, s in enumerate(scenes):
        s["id"] = f"s{k + 1:03d}"
        s["end"] = scenes[k + 1]["start"] if k + 1 < len(scenes) else end_time
    auto_coverage(scenes, end_time)

    # 5. checks that need the whole film
    warns += film_checks(scenes)
    warns += scene_checks(scenes)
    # things the writers wanted but the engine lacks: the to-do list for the next engine upgrade (playbook/scene-writing.md §9)
    missing = film.pop("_missing", [])
    film.pop("_proj", None)
    if write:
        (proj / "work").mkdir(exist_ok=True)
        (proj / "work" / "missing_assets.json").write_text(json.dumps(missing, indent=1, ensure_ascii=False), encoding="utf-8")
    if missing:
        names = sorted({f"{m['kind']} '{m['name']}'" for m in missing})
        warns.append(f"{len(missing)} missing asset(s) logged in work/missing_assets.json: {', '.join(names[:12])}{' …' if len(names) > 12 else ''}")

    meta = {"title": film.get("title", proj.name), "lang": film.get("lang", "en"), "fps": 24, "duration": end_time, "grain": 0.5}
    if (film.get("look") or {}).get("grade"):
        meta["grade"] = film["look"]["grade"]
    v = _voice_file(proj)
    if v:
        meta["voice"] = v
    else:
        warns.append("No input/voice.*: the video will have ambience and SFX only (add the narration later in editing, or drop the voice in input/ and re-run).")
    mix = mix_of(scenes)
    for s in scenes:
        s.pop("_cls", None)
        s.pop("_raw", None)
    # a weather preset of the library ("weather": "monsoon_downpour") becomes its parameters
    for s_ in scenes:
        wv = (s_.get("set") or {}).get("weather")
        if isinstance(wv, str) and wv in presets:
            s_["set"]["weather"] = presets[wv].get("spec") or {"kind": "rain"}
    plan = {"meta": meta, "cast": clean_cast, "scenes": scenes}
    import layout_check  # noqa: E402
    layout_check.fix_speeds(plan)
    pack_drawings(plan)
    if write:
        (proj / "plan.json").write_text(json.dumps(plan, indent=1, ensure_ascii=False), encoding="utf-8")
    return {"ok": True, "errors": [], "warnings": warns, "scenes": len(scenes), "duration": end_time, "mix": mix}


def pack_drawings(plan):
    """store every drawing once: lists under "parts" / "holdsDrawing" go to plan["drawings"] and are replaced by "@d<n>"
    (a row of twelve rubber trees, every rider's bicycle, every costume piece: one copy each). src/lib/plan.ts undoes it."""
    table, seen = {}, {}

    def walk(v):
        if isinstance(v, list):
            return [walk(x) for x in v]
        if isinstance(v, dict):
            out = {}
            for k, x in v.items():
                if k in ("parts", "holdsDrawing") and isinstance(x, list) and x:
                    key = json.dumps(x, sort_keys=True, separators=(",", ":"))
                    if key not in seen:
                        seen[key] = f"d{len(seen)}"
                        table[seen[key]] = x
                    out[k] = "@" + seen[key]
                else:
                    out[k] = walk(x)
            return out
        return v

    plan["cast"] = walk(plan["cast"])
    plan["scenes"] = walk(plan["scenes"])
    if table:
        plan["drawings"] = table
    return plan


def mix_of(scenes):
    tot = {}
    T = 0.0
    for s in scenes:
        d = s["end"] - s["start"]
        tot[s["_cls"]] = tot.get(s["_cls"], 0) + d
        T += d
    return {k: round(v / max(1e-6, T), 2) for k, v in sorted(tot.items())}


def film_checks(scenes):
    w = []
    chap = []
    cur = None
    for s in scenes:
        if cur is None or s.get("chapter"):
            cur = {"title": s.get("chapter") or "(opening)", "scenes": []}
            chap.append(cur)
        cur["scenes"].append(s)
    for k in range(1, len(scenes)):
        a, b = scenes[k - 1]["_raw"], scenes[k]["_raw"]
        if a["recipe"] == b["recipe"] and RECIPES[a["recipe"]].cls != "map" and b["recipe"] != "scene":
            w.append(f"{_where(b)}: same recipe '{b['recipe']}' as the card before. Two scenes in a row that look alike feel like a loop: "
                     f"show the NEXT thing (the consequence, the other side, a close detail). See playbook/narration-to-picture.md.")
    for c in chap:
        n = len(c["scenes"])
        dur = sum(s["end"] - s["start"] for s in c["scenes"])
        counts = {}
        for s in c["scenes"]:
            counts[s["_raw"]["recipe"]] = counts.get(s["_raw"]["recipe"], 0) + 1
        for rid, m in counts.items():
            if n >= 6 and m / n > 0.3 and RECIPES[rid].cls != "map" and rid != "scene":
                w.append(f"chapter '{c['title']}': recipe '{rid}' is used {m} times in {n} cards. Use at most ~30 % per recipe; pick other recipes for some of them.")
        shares = mix_of(c["scenes"])
        acted = shares.get("action", 0) + shares.get("talk", 0)
        if dur >= 45 and acted < TARGET["acted"] - 0.05:
            w.append(f"chapter '{c['title']}': only {acted:.0%} of the time shows people acting in a place (target ≥ {TARGET['acted']:.0%}). "
                     f"Replace map/document/chart cards by the scene the sentence describes (playbook/narration-to-picture.md §3).")
        for cls in ("map", "device", "host"):
            if dur >= 45 and shares.get(cls, 0) > TARGET[cls] + 0.04:
                w.append(f"chapter '{c['title']}': {cls} is {shares[cls]:.0%} of the time (keep ≤ {TARGET[cls]:.0%}); show the moment itself instead.")
        stats = sum(1 for s in c["scenes"] if s["_raw"].get("stat"))
        if stats > max(1, dur / 120):
            w.append(f"chapter '{c['title']}': {stats} stat cards. Use at most one every ~2 minutes; let the scene and the voice carry numbers.")
    for s in scenes:
        raw = s["_raw"]
        d = s["end"] - s["start"]
        if d < 1.8:
            w.append(f"{_where(raw)}: only {d:.1f} s long. Merge it with the card before or after (scenes under 2 s flash by).")
        if RECIPES[raw["recipe"]].cls == "map" and d > 6.5:
            w.append(f"{_where(raw)}: a {d:.1f} s map. Keep maps ≤ 5 s: start the next card (the people in that place) earlier.")
        if raw.get("caption") and RECIPES[raw["recipe"]].cls in ("map", "device"):
            w.append(f"{_where(raw)}: a caption on a {RECIPES[raw['recipe']].cls} card. Big-question captions run over an ACTED scene.")
        if d > 12 and RECIPES[raw["recipe"]].cls != "host":
            w.append(f"{_where(raw)}: {d:.1f} s long. Split it into 2-3 cards at sentence starts (one idea per card, 3-10 s).")
        says = raw.get("says", "")
        if says and difflib.SequenceMatcher(None, says.lower(), s["beat"].lower()[:len(says) + 20]).ratio() > 0.8:
            w.append(f"{_where(raw)}: \"says\" copies the narration. Write what it MEANS (who does what, why it matters) in your own words.")
    return w


def _words(s):
    return {w for w in "".join(ch.lower() if ch.isalnum() else " " for ch in s).split() if len(w) > 3}


def scene_checks(scenes):
    """Anti-repetition for scene cards: the same place + camera + action twice in a short span, or an idea that repeats
    an earlier one, reads as a loop to the viewer. Deliberate callbacks carry "revisit": true."""
    w = []
    seen = []  # (index, sig, raw)
    for k, s in enumerate(scenes):
        raw = s["_raw"]
        sig = raw.get("_sig")
        if not sig or raw.get("revisit"):
            if sig:
                seen.append((k, sig, raw))
            continue
        for k2, sig2, raw2 in reversed(seen):
            if k - k2 > 8:
                break
            same_look = sig["where"] == sig2["where"] and sig["camera"] == sig2["camera"] and sig["acts"] == sig2["acts"]
            if same_look:
                w.append(f"{_where(raw)}: looks like {_where(raw2)} (same place, camera \"{sig['camera']}\" and the same acts {sig['acts']}). "
                         f"Show the NEXT thing: another person, another act, a detail, the consequence, or the same place at another time "
                         f"(playbook/scene-writing.md §6). If it is a deliberate callback, add \"revisit\": true.")
                break
        a = _words(sig.get("idea") or "")
        for k2, sig2, raw2 in seen:
            b = _words(sig2.get("idea") or "")
            if a and b and len(a & b) / max(1, min(len(a), len(b))) > 0.7:
                w.append(f"{_where(raw)}: its idea repeats {_where(raw2)} (\"{(sig2.get('idea') or '')[:70]}…\"). "
                         f"Every card needs its own picture: pick another device from playbook/visual-ideas.md.")
                break
        seen.append((k, sig, raw))
    # one place for too long without a change of time, people or camera
    run = 1
    for k in range(1, len(scenes)):
        a, b = scenes[k - 1]["_raw"].get("_sig"), scenes[k]["_raw"].get("_sig")
        run = run + 1 if a and b and a["where"] == b["where"] else 1
        if run == 5:
            w.append(f"{_where(scenes[k]['_raw'])}: 5 scene cards in a row in \"{b['where']}\". Cut away (the other side, the street outside, a detail, a map bridge) and come back.")
    cams = [s["_raw"]["_sig"]["camera"] for s in scenes if s["_raw"].get("_sig")]
    for k in range(2, len(cams)):
        if cams[k] == cams[k - 1] == cams[k - 2] and cams[k] != "custom":
            w.append(f"three scene cards in a row use camera \"{cams[k]}\" (around card {k + 1} of the scene cards). Vary the camera (or leave it \"auto\").")
            break
    return w


BATTLE = {"assault", "wave", "under_fire", "gun_crew", "mg_nest", "hit", "stretcher", "aftermath", "tank_attack", "retreat", "surrender",
          "naval_battle", "sinking", "air_battle", "bombing", "submarine_attack", "river_crossing", "para_drop"}
