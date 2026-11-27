"""The living library — find what exists, make what is missing, check it, add it for the next film.

    python tools/lib.py index                                 rebuild library/index.json + library/INDEX.md
    python tools/lib.py search "rubber tree"  [--type plants] [--n 8]
    python tools/lib.py match   --project projects/<slug>     the project's inventory -> use / adapt / create (work/match.md)
    python tools/lib.py new <type> <id> --project projects/<slug> [--name ".."] [--tags a,b] [--doc ".."] [--from <asset id>]
    python tools/lib.py import <image.png> --project projects/<slug> --id <id> [--type <type>] [--colors 10] [--snap]
    python tools/lib.py check   [--project projects/<slug>] [ids…]
    python tools/lib.py preview [--project projects/<slug>] [ids…] [--grid]
    python tools/lib.py place <set id> --project projects/<slug> [--tags a,b] [--name ".."] [--doc ".."]
                                                              save a story place of cards/_film.json "sets" as a places asset
    python tools/lib.py promote --project projects/<slug> [ids…] [--replace] [--keep]
                                                              move the film's new assets into library/ (--keep: leave a copy)
    python tools/lib.py style-sheet                           library/STYLE_REFERENCE.jpg (attach it when an image model draws)

Types: props, vehicles, buildings, plants, costumes, characters, places, plates, weather (library/README.md).
Every error says what to change. Read playbook/library.md for the whole loop.
"""
from __future__ import annotations

import datetime as _dt
import difflib
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

from cardlib import library as L  # noqa: E402

TODAY = _dt.date.today().isoformat()


def die(msg):
    sys.exit(f"ERROR: {msg}")


def opt(args, name, default=None):
    return args[args.index(name) + 1] if name in args and args.index(name) + 1 < len(args) else default


def rel(p: Path) -> str:
    try:
        return str(Path(p).resolve().relative_to(ROOT)).replace("\\", "/")
    except ValueError:
        return str(p)


# ================================================================== builtin engine assets (code-drawn, always available)
def _kit_docs(name):
    src = (ROOT / "src/sets/Kit.tsx").read_text(encoding="utf-8")
    i = src.index(f"export const {name}")
    j = src.index("\n};", i)
    out = {}
    for m in re.finditer(r"^\s{2}(\w+): \{(.*)$", src[i:j], re.M):
        d = re.search(r"doc: '((?:[^'\\]|\\.)*)'", m.group(2))
        out[m.group(1)] = d.group(1).replace("\\'", "'") if d else ""
    return out


def _spec_options():
    """the look options of the character rig, read from the CharSpec comments in src/char/Character.tsx"""
    src = (ROOT / "src/char/Character.tsx").read_text(encoding="utf-8")
    out = {}
    for field in ("outfit", "hair", "facial", "hat", "glasses", "extra"):
        m = re.search(rf"^\s+{field}\?: [^;]+;\s*//\s*(.+)$", src, re.M)
        if m:
            out[field] = [w.strip() for w in re.split(r"[|,]| ", m.group(1)) if re.match(r"^[a-z_0-9]+$", w.strip())]
    return out


def builtins():
    import validate_plan
    from cardlib import stagecraft as SC
    v = validate_plan.vocab()
    out = []

    def add(type_, id_, doc, tags=(), preview=None, how=""):
        out.append({"id": id_, "type": type_, "source": "builtin", "name": id_.replace("_", " "), "tags": list(tags) + id_.split("_"),
                    "doc": doc, "preview": preview, "how": how})
    for p in sorted(v["props"]):
        add("props", p, SC.THING_DOC.get(p, "engine prop"), how=f'{{"what": "{p}"}} in things, or "holds": "{p}"')
    for p in sorted(v["vehicles"]):
        add("vehicles", p, "engine vehicle", how=f'{{"type": "{p}"}} in vehicles')
    for p in sorted(v["presets"]):
        add("characters", p, "cast preset (recipes/PEOPLE.md)", how=f'cast: {{"x": {{"preset": "{p}"}}}}')
    for s in sorted(v["sets"] - {"room", "town"}):
        add("places", s, "engine set", how=f'"where": "{s}"')
    img = ROOT / "recipes" / "img" / "stagecraft"
    for k, d in _kit_docs("ROOM_STYLES").items():
        add("places", f"room_{k}", d, ("room", "interior", k), rel(img / f"room_{k}.jpg") if (img / f"room_{k}.jpg").exists() else None, f'"where": {{"room": "{k}"}}')
    for k, d in _kit_docs("TOWN_STYLES").items():
        add("places", f"town_{k}", d, ("town", "street", k), rel(img / f"town_{k}.jpg") if (img / f"town_{k}.jpg").exists() else None, f'"where": {{"town": "{k}"}}')
    for k, d in _kit_docs("TOWN_BUILDINGS").items():
        add("buildings", f"kit_{k}", d, ("town", "kit"), how=f'"buildings": ["{k}"] in a town place')
    for k, d in _kit_docs("ROOM_ITEMS").items():
        add("props", f"room_item_{k}", d, ("room", "kit"), how=f'"items": ["{k}"] in a room place')
    for field, vals in _spec_options().items():
        for val in vals:
            add("costumes", f"{field}_{val}", f"character look option: {field} = {val}", (field,), how=f'cast: {{"{field}": "{val}"}}')
    for w in ("rain", "snow"):
        add("weather", w, f"engine weather: {w}", how=f'"weather": "{w}"')
    return out


# ================================================================== index and search
def index(write=True):
    lib = L.load()
    entries = []
    for aid, a in sorted(lib.items()):
        d = Path(a["_dir"])
        pv = next((p for p in (d / "preview.jpg", d / "preview.png") if p.exists()), None)
        entries.append({"id": aid, "type": a.get("type"), "source": "library", "name": a.get("name", aid), "tags": a.get("tags", []),
                        "doc": a.get("doc", ""), "preview": rel(pv) if pv else None, "path": rel(d), "status": a.get("status", "draft"),
                        "project": a.get("project")})
    entries += builtins()
    if write:
        L.LIB.mkdir(exist_ok=True)
        (L.LIB / "index.json").write_text(json.dumps(entries, indent=1, ensure_ascii=False), encoding="utf-8")
        md = ["# Library index", "", "Generated by `python tools/lib.py index`. Do not edit by hand. Search it: `python tools/lib.py search \"words\"`.", "",
              "**library** = made for a film and kept (vector drawings, costume pieces, places, plates, weather presets).",
              "**builtin** = drawn by the engine code (props, vehicles, presets, sets, kit styles and modules, look options).", ""]
        for t, doc in L.TYPES.items():
            mine = [e for e in entries if e["type"] == t and e["source"] == "library"]
            bi = [e for e in entries if e["type"] == t and e["source"] == "builtin"]
            md += [f"## {t}", "", f"_{doc}_", ""]
            if mine:
                md += ["| id | what | tags | made in | preview |", "|---|---|---|---|---|"]
                for e in mine:
                    pv = f'<img src="../{e["preview"]}" width="220">' if e["preview"] else ""
                    md.append(f"| `{e['id']}` | {e['doc']} | {', '.join(e['tags'][:8])} | {e.get('project') or ''} | {pv} |")
                md.append("")
            if bi:
                md += [f"Builtin ({len(bi)}): " + ", ".join(f"`{e['id']}`" for e in bi), ""]
        (L.LIB / "INDEX.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    return entries


_STOP = {"a", "an", "the", "of", "and", "with", "for", "in", "on", "to", "or", "at", "by"}


def _toks(s):
    out = []
    for w in re.split(r"[^a-z0-9]+", str(s).lower()):
        if w and w not in _STOP:
            out.append(w[:-1] if len(w) > 4 and w.endswith("s") else w)
    return out


def _strong(e):
    return set(_toks(e["id"]) + _toks(e.get("name", "")) + [t for tag in e.get("tags", []) for t in _toks(tag)])


def _idf(entries):
    """rare words weigh more: "conical hat" must not match every hat; "japanese soldier" must find the Japanese soldier"""
    import math
    df = {}
    for e in entries:
        for w in _strong(e) | set(_toks(e.get("doc", ""))):
            df[w] = df.get(w, 0) + 1
    n = len(entries)
    return lambda w: math.log((n + 1) / (1 + df.get(w, 0))) + 0.5


def score(query, e, idf=None):
    q = _toks(query)
    if not q:
        return 0.0
    idf = idf or (lambda w: 1.0)
    strong, weak = _strong(e), set(_toks(e.get("doc", "")))
    total = sum(idf(w) for w in q)
    s = sum(idf(w) * (1.0 if w in strong else 0.5 if w in weak else 0.0) for w in q) / total
    s += 0.15 * difflib.SequenceMatcher(None, "_".join(q), e["id"]).ratio()
    if e["source"] == "library":
        s += 0.05  # prefer what a film already made
    return round(s, 3)


def search(query, type_=None, n=8, entries=None):
    entries = entries if entries is not None else (json.loads((L.LIB / "index.json").read_text(encoding="utf-8")) if (L.LIB / "index.json").exists() else index())
    idf = _idf(entries)
    pool = [e for e in entries if not type_ or e["type"] in (type_ if isinstance(type_, (list, tuple, set)) else [type_])]
    return sorted(((score(query, e, idf), e) for e in pool), key=lambda z: -z[0])[:n]


# ================================================================== geometry of drawing parts (for check and preview)
_NUM = re.compile(r"[-+]?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?")


def _path_points(d):
    pts, x, y, sx, sy = [], 0.0, 0.0, 0.0, 0.0
    for cmd, args in re.findall(r"([MmLlHhVvCcSsQqTtZz])([^MmLlHhVvCcSsQqTtZzAa]*)", d):
        a = [float(v) for v in _NUM.findall(args)]
        rel_ = cmd.islower()
        c = cmd.upper()
        if c == "Z":
            x, y = sx, sy
            continue
        step = {"M": 2, "L": 2, "T": 2, "H": 1, "V": 1, "C": 6, "S": 4, "Q": 4}[c]
        for i in range(0, len(a) - step + 1, step):
            chunk = a[i:i + step]
            if c == "H":
                x = x + chunk[0] if rel_ else chunk[0]
            elif c == "V":
                y = y + chunk[0] if rel_ else chunk[0]
            else:
                for k in range(0, step, 2):
                    px, py = (x + chunk[k], y + chunk[k + 1]) if rel_ else (chunk[k], chunk[k + 1])
                    pts.append((px, py))
                x, y = (x + chunk[-2], y + chunk[-1]) if rel_ else (chunk[-2], chunk[-1])
            pts.append((x, y))
            if c == "M" and i == 0:
                sx, sy = x, y
    return pts


def part_points(p, ox=0.0, oy=0.0, k=1.0):
    pts = []
    if p.get("group") is not None:
        at = p.get("at") or [0, 0]
        for q in p["group"]:
            pts += part_points(q, ox + at[0] * k, oy + at[1] * k, k * float(p.get("scale", 1.0)))
        return pts
    if p.get("rect"):
        x, y, w, h = p["rect"][:4]
        pts = [(x, y), (x + w, y + h)]
    elif p.get("circle"):
        cx, cy, r = p["circle"][:3]
        pts = [(cx - r, cy - r), (cx + r, cy + r)]
    elif p.get("ellipse"):
        cx, cy, rx, ry = p["ellipse"][:4]
        pts = [(cx - rx, cy - ry), (cx + rx, cy + ry)]
    elif p.get("poly"):
        pts = [tuple(q[:2]) for q in p["poly"]]
    elif p.get("line"):
        pts = [tuple(q[:2]) for q in p["line"]]
    elif p.get("path"):
        pts = _path_points(p["path"])
    elif p.get("text") is not None and p.get("at"):
        sz = float(p.get("size", 24))
        n = len(str(p["text"]))
        pts = [(p["at"][0] - n * sz * 0.3, p["at"][1] - sz), (p["at"][0] + n * sz * 0.3, p["at"][1])]
    return [(ox + x * k, oy + y * k) for x, y in pts]


def bbox(parts):
    pts = [q for p in parts for q in part_points(p)]
    if not pts:
        return None
    xs, ys = [q[0] for q in pts], [q[1] for q in pts]
    return min(xs), min(ys), max(xs), max(ys)


def _fills(parts, acc=None):
    acc = set() if acc is None else acc
    for p in parts:
        if p.get("group") is not None:
            _fills(p["group"], acc)
        elif p.get("fill") and p.get("fill") != "none":
            acc.add(str(p["fill"]).lower())
    return acc


def _count(parts):
    n = 0
    for p in parts:
        if p.get("group") is not None:
            n += _count(p["group"])
        elif p.get("path"):
            n += len(_NUM.findall(p["path"])) // 2
        else:
            n += 4
    return n


KINDS = ("rect", "circle", "ellipse", "poly", "line", "path", "text", "group")


# ================================================================== check
def check_asset(a, known_ids=()):
    errs, warns = [], []
    aid = a.get("id", "?")
    if not L.ID_RE.match(str(aid)):
        errs.append(f"{aid}: \"id\" must be lowercase letters, digits and _ (2-41 chars), e.g. rubber_tree")
    if a.get("type") not in L.TYPES:
        errs.append(f"{aid}: \"type\" = {a.get('type')!r} — use one of {list(L.TYPES)}")
    for f in ("name", "doc"):
        if not a.get(f):
            warns.append(f"{aid}: add \"{f}\" (one line: what it is, where and when it belongs)")
    if len(a.get("tags", [])) < 3:
        warns.append(f"{aid}: add 3+ \"tags\" (region, era, kind: e.g. [\"malaya\", \"ww2\", \"tree\", \"plantation\"]) so the next film finds it")
    if a.get("type") in L.DRAWABLE:
        parts = a.get("parts") or []
        if not parts:
            errs.append(f"{aid}: no \"parts\". Draw it (library/README.md §Drawing) or import an image (`lib import`).")
        for i, p in enumerate(parts):
            if not any(k in p for k in KINDS):
                errs.append(f"{aid}: part {i + 1} has none of {KINDS}")
        bb = bbox(parts)
        if bb:
            x0, y0, x1, y1 = bb
            grip = (a.get("anchors") or {}).get("grip") or a.get("grip")
            if not grip and not a.get("floats") and abs(y1) > 14:
                warns.append(f"{aid}: its lowest point is at y {y1:.0f}; a thing that stands must touch y 0 (move the parts by {-y1:.0f}) — "
                             f"or give \"anchors\": {{\"grip\": [x, y]}} if it is held")
            h = y1 - y0
            if a.get("h") and abs(h - a["h"]) > 0.3 * max(h, a["h"]):
                warns.append(f"{aid}: \"h\" is {a['h']} but the drawing is {h:.0f} units tall — set \"h\": {h:.0f}")
            if grip and not (x0 - 20 <= grip[0] <= x1 + 20 and y0 - 20 <= grip[1] <= y1 + 20):
                errs.append(f"{aid}: the grip {grip} is outside the drawing ({x0:.0f},{y0:.0f})–({x1:.0f},{y1:.0f})")
        size = float(a.get("size", 1.0))
        if not 0.03 <= size <= 6:
            errs.append(f"{aid}: \"size\" {size} is odd (1.0 = drawn in man-units, a man is ~260 units tall)")
        if len(_fills(parts)) > 16:
            warns.append(f"{aid}: {len(_fills(parts))} fill colours — keep ≤ 12 (flat style); re-import with --colors 10 or merge colours")
        if _count(parts) > 6000:
            warns.append(f"{aid}: very detailed ({_count(parts)} points) — re-import with a simpler image or --simplify 2")
        inks = sum(1 for p in parts if p.get("stroke") is not False) + sum(1 for c in _fills(parts) if c in ("#2a2320", "#1f1a17", "#2b2522", "#262019"))
        if not inks:
            warns.append(f"{aid}: no dark outline — the house style outlines every shape (keep the default stroke, or import keeps the dark lines)")
    if a.get("type") == "costumes":
        sl = L.costume_slots(a)
        for s in sl:
            if s["slot"] not in L.SLOTS:
                errs.append(f"{aid}: slot \"{s['slot']}\" — use one of {list(L.SLOTS)} (head pieces in the head frame, body pieces in the body frame: library/README.md §Costumes)")
            if not s["parts"]:
                errs.append(f"{aid}: a piece in slot {s['slot']} has no \"parts\"")
            for i, p in enumerate(s["parts"]):
                if not any(k in p for k in KINDS):
                    errs.append(f"{aid}: {s['slot']} part {i + 1} has none of {KINDS}")
            bb = bbox(s["parts"])
            if bb and s["slot"] in ("head", "headback") and (bb[1] < -220 or bb[3] > 160 or bb[0] < -200 or bb[2] > 200):
                warns.append(f"{aid}: the {s['slot']} piece reaches ({bb[0]:.0f},{bb[1]:.0f})–({bb[2]:.0f},{bb[3]:.0f}); the head frame is about -75..+50 high, ±66 wide — is it drawn in the head frame?")
            if bb and s["slot"] in ("body", "hips", "back") and (bb[1] < -320 or bb[3] > 20):
                warns.append(f"{aid}: the {s['slot']} piece reaches y {bb[1]:.0f}..{bb[3]:.0f}; the body frame has the feet at 0 and the shoulders at -172")
    if a.get("type") == "places":
        sp = a.get("spec") or {}
        if not any(k in sp for k in ("compose", "room", "town", "set", "kit")):
            errs.append(f"{aid}: a places asset needs \"spec\": the story place as written in cards/_film.json \"sets\" "
                        f"({{\"compose\": {{…}}}}, {{\"room\": \"office\", …}} or {{\"town\": \"village\", …}}) — make it with `lib place <set id>`")
    if a.get("type") == "characters":
        sp = a.get("spec") or {}
        if not sp.get("preset"):
            errs.append(f"{aid}: a characters asset needs \"spec\": {{\"preset\": \"civilian_man\", …look fields, \"wear\": [costume ids]}}")
    if aid in known_ids:
        warns.append(f"{aid}: an asset with this id already exists in the library (promote with --replace to overwrite, or pick another id)")
    return errs, warns


def cmd_check(args):
    proj = Path(opt(args, "--project")) if opt(args, "--project") else None
    ids = [a for a in args if not a.startswith("--") and a != opt(args, "--project")]
    pool = L.load(proj / "assets") if proj else L.load()
    known = set(L.load()) if proj else set()
    if ids:
        pool = {k: v for k, v in pool.items() if k in ids}
    n_err = 0
    for aid, a in sorted(pool.items()):
        errs, warns = check_asset(a, known)
        n_err += len(errs)
        for m in errs:
            print("ERROR  ", m)
        for m in warns:
            print("warning", m)
        if not errs and not warns:
            print("ok     ", aid)
    print(json.dumps({"assets": len(pool), "errors": n_err}))
    return n_err


# ================================================================== new
REQUEST = """# Request: {id} ({type})

Fill every line, then make the asset in ONE of the two ways (library/README.md):
- you can make images (Muse): use prompt.txt, save the picture(s) here as source/<id>.png, then
  `python tools/lib.py import {proj}/assets/{id}/source/{id}.png --project {proj} --id {id} --type {type}`
- you cannot make images: draw the parts in asset.json (library/README.md §Drawing), check them with
  `python tools/lib.py preview --project {proj} {id} --grid`

- What it is (one line):
- Region and period (e.g. Malaya 1941):
- Where the film uses it (card / scene):
- View (side / front / three-quarter):
- Size next to a man (a man is 260 units; e.g. a bicycle ~170 long, a house ~600 tall):
- Main colours (3-6):
- Parts that move (wheels spin, crown sways, flag flutters…) and where their centres are:
- Where a hand holds it / where someone sits / its top surface (if any):
- Reference notes (what makes it look right; describe, do not trace photos):
"""


def cmd_new(args):
    if len(args) < 2:
        die("usage: lib new <type> <id> --project projects/<slug> [--name ..] [--tags a,b] [--doc ..] [--from <asset id>]")
    type_, aid = args[0], args[1]
    proj = Path(opt(args, "--project") or die("add --project projects/<slug>"))
    if type_ not in L.TYPES:
        die(f"type {type_!r} — use one of {list(L.TYPES)}")
    if not L.ID_RE.match(aid):
        die("id: lowercase letters, digits and _ (e.g. rubber_tree)")
    d = proj / "assets" / aid
    if d.exists():
        die(f"{d} already exists — edit it, or pick another id")
    taken = L.load().get(aid)
    if taken and taken.get("type") != type_:
        die(f"the id \"{aid}\" is already a {taken['type']} asset of the library — ids are unique across all types: pick another (e.g. {aid}_{type_.rstrip('s')})")
    rec = {"id": aid, "type": type_, "name": opt(args, "--name", aid.replace("_", " ")), "tags": [t for t in (opt(args, "--tags", "") or "").split(",") if t],
           "doc": opt(args, "--doc", ""), "size": 1.0, "anchors": {"ground": [0, 0]}, "parts": [], "source": {"kind": "code"},
           "project": proj.name, "status": "draft", "created": TODAY}
    src = opt(args, "--from")
    if src:
        base = {**L.load(), **L.load(proj / "assets")}.get(src)
        if not base:
            die(f"--from {src}: no such asset (python tools/lib.py search \"{src}\")")
        for k in ("size", "h", "top", "anchors", "parts", "tags"):
            if base.get(k) is not None:
                rec[k] = json.loads(json.dumps(base[k]))
        rec["source"] = {"kind": "code", "adapted_from": src}
    (d / "source").mkdir(parents=True)
    (d / "asset.json").write_text(json.dumps(rec, indent=1, ensure_ascii=False), encoding="utf-8")
    (d / "request.md").write_text(REQUEST.format(id=aid, type=type_, proj=rel(proj)), encoding="utf-8")
    tmpl = L.LIB / "prompts" / f"{type_}.md"
    prompt = tmpl.read_text(encoding="utf-8") if tmpl.exists() else "(no prompt template yet for this type: describe the thing in the house style)"
    (d / "prompt.txt").write_text(prompt.replace("{name}", rec["name"]).replace("{doc}", rec["doc"] or rec["name"]), encoding="utf-8")
    print(json.dumps({"created": rel(d), "next": "fill request.md, then import an image or draw the parts; then lib preview --grid and lib check"}, indent=1))


# ================================================================== preview (renders: one render at a time!)
def _grid_parts(bb, step=50):
    x0, y0, x1, y1 = bb
    gx0, gx1 = int((x0 // step) * step), int(((x1 // step) + 1) * step)
    gy0, gy1 = int((y0 // step) * step), max(0, int(((y1 // step) + 1) * step))
    parts = []
    for x in range(gx0, gx1 + 1, step):
        parts.append({"line": [[x, gy0], [x, gy1]], "width": 3 if x == 0 else 1, "stroke": "#3a6ea5" if x == 0 else "#7a9cc0", "opacity": 0.55})
        if x % 100 == 0:
            parts.append({"text": str(x), "at": [x, gy1 + 22], "size": 16, "fill": "#3a6ea5"})
    for y in range(gy0, gy1 + 1, step):
        parts.append({"line": [[gx0, y], [gx1, y]], "width": 3 if y == 0 else 1, "stroke": "#c05a3a" if y == 0 else "#7a9cc0", "opacity": 0.55})
        if y % 100 == 0:
            parts.append({"text": str(y), "at": [gx0 - 26, y + 5], "size": 16, "fill": "#c05a3a"})
    return parts


def _render(plan, out_dir: Path):
    out_dir.mkdir(parents=True, exist_ok=True)
    pf = out_dir / "_plan.json"
    pf.write_text(json.dumps(plan), encoding="utf-8")
    r = subprocess.run(["node", str(ROOT / "tools" / "render.mjs"), "stills", str(pf), str(out_dir), "--scale", "0.5", "--at", "mid"], cwd=ROOT)
    pf.unlink(missing_ok=True)
    if r.returncode:
        die("render failed (is another render running? only one at a time)")


def preview_plan(assets, grid=False):
    scenes = []
    for k, (aid, a) in enumerate(assets.items()):
        parts = a.get("parts") or []
        bb = bbox(parts) or (-100, -200, 100, 0)
        size = float(a.get("size", 1.0))
        h = max((bb[3] - bb[1]) * size, 260.0)
        w = max((bb[2] - bb[0]) * size, 120.0)
        sc = round(min(2.2, 620 / h, 900 / w), 3)
        gy = round(880 - max(0.0, bb[3]) * sc * size)  # things drawn around the hand (a broom, a shovel) stand on the floor too
        els = [{"kind": "actor", "id": "man", "who": "civilian_man", "x": 330, "y": 880, "scale": sc, "pose": "idle", "expr": "neutral"},
               {"kind": "drawing", "id": aid, "x": 1060, "y": gy, "scale": round(sc * size, 3), "parts": parts},
               {"kind": "label", "text": f"{aid} · {a.get('type')} · a man for scale", "x": 960, "y": 1010, "style": "tag", "size": 28, "in": 0, "enter": "none"}]
        if grid:
            els.insert(1, {"kind": "drawing", "id": "grid", "x": 1060, "y": gy, "scale": round(sc * size, 3), "parts": _grid_parts(bb)})
        scenes.append({"id": f"a{k:03d}_{aid}", "start": k * 2.0, "end": (k + 1) * 2.0, "type": "stage", "set": {"kind": "studio"}, "elements": els,
                       "beat": f"{aid} ({a.get('type')}) {a.get('doc', '')[:90]}", "transition": "cut"})
    return {"meta": {"title": "assets", "fps": 24, "width": 1920, "height": 1080, "duration": len(scenes) * 2.0}, "cast": {}, "scenes": scenes}


def people_plan(assets, plan, proj=None):
    """costumes: worn by three different people (standing, turned and talking, walking); characters: the look standing and acting"""
    base = len(plan["scenes"])
    for k, (aid, a) in enumerate(assets.items()):
        t0 = (base + k) * 2.0
        if a.get("type") == "costumes":
            who = [("civilian_man", {}), ("british_soldier", {"hat": "none"}), ("civilian_woman", {"hair": "short"})]
            els = []
            for j, (preset, extra) in enumerate(who):
                cid = f"w{k}_{j}"
                plan["cast"][cid] = {"preset": preset, "hat": "none", **extra, "wear": L.costume_slots(a)}
                el = {"kind": "actor", "id": cid, "who": cid, "x": [430, 960, 1490][j], "y": 900, "scale": 1.45,
                      "pose": ["idle", "talk", "point"][j], "expr": ["neutral", "smile", "happy"][j]}
                if j == 1:
                    el.update({"turn": 0.4, "talk": True})
                if j == 2:
                    el.update({"flip": True, "turn": 0.4})
                els.append(el)
        else:
            sp = dict(a.get("spec") or {"preset": "civilian_man"})
            if sp.get("wear"):
                sp = L.resolve_cast({"x": sp}, proj)["x"]
            plan["cast"][f"c{k}"] = sp
            els = [{"kind": "actor", "id": "a", "who": f"c{k}", "x": 700, "y": 900, "scale": 1.45, "pose": "idle", "expr": "neutral"},
                   {"kind": "actor", "id": "b", "who": f"c{k}", "x": 1220, "y": 900, "scale": 1.45, "pose": "explain", "expr": "smile", "talk": True, "turn": 0.4}]
        els.append({"kind": "label", "text": f"{aid} · {a.get('type')}", "x": 960, "y": 1010, "style": "tag", "size": 28, "in": 0, "enter": "none"})
        plan["scenes"].append({"id": f"a{base + k:03d}_{aid}", "start": t0, "end": t0 + 2.0, "type": "stage", "set": {"kind": "studio"}, "elements": els,
                               "beat": f"{aid} ({a.get('type')}) {a.get('doc', '')[:90]}", "transition": "cut"})
    plan["meta"]["duration"] = len(plan["scenes"]) * 2.0
    return plan


def places_plan(assets, plan, proj=None):
    """places: the place itself with a man for scale (rows of things included)"""
    import types as _types
    from cardlib import recipes_scene as RS
    from cardlib import stagecraft as SC
    base = len(plan["scenes"])
    for k, (aid, a) in enumerate(assets.items()):
        film = {"sets": {aid: a["spec"]}, "cast": {}}
        if proj:
            film["_proj"] = str(proj)
        raw = {"where": aid, "place_id": aid, "recipe": "scene", "_file": "asset.json", "_n": aid, "at": "(preview)"}
        c = _types.SimpleNamespace(film=film, raw=raw, warns=[], cast={})
        c.p = lambda key, d=None, raw=raw: raw.get(key, d)
        pl = RS._place(c)
        t0 = (base + k) * 2.0
        els = [{"kind": "actor", "id": "man", "who": "civilian_man", "x": 1500, "y": SC.DEPTHS["mid"], "pose": "idle", "expr": "neutral"}]
        els += pl.get("row_els") or []
        st = {kk: v for kk, v in pl["set"].items() if not kk.startswith("_")}
        plan["scenes"].append({"id": f"a{base + k:03d}_{aid}", "start": t0, "end": t0 + 2.0, "type": "stage", "set": st, "world": pl["world"],
                               "elements": els, "beat": f"{aid} (places) {a.get('doc', '')[:90]}", "transition": "cut",
                               "tag": f"{aid} · places", "tagIn": -1})
    plan["meta"]["duration"] = len(plan["scenes"]) * 2.0
    return plan


def cmd_place(args):
    """save a story place of the film (cards/_film.json "sets") as a places asset of the project"""
    proj = Path(opt(args, "--project") or die("add --project projects/<slug>"))
    ids = [a for a in args if not a.startswith("--") and a not in (opt(args, "--project"), opt(args, "--tags"), opt(args, "--name"), opt(args, "--doc"))]
    if not ids:
        die("say which story place: python tools/lib.py place <set id> --project projects/<slug>")
    film = json.loads((proj / "cards" / "_film.json").read_text(encoding="utf-8"))
    sets = film.get("sets") or {}
    for sid in ids:
        if sid not in sets:
            die(f"\"{sid}\" is not in cards/_film.json \"sets\" ({sorted(sets)})")
        spec = {k: v for k, v in sets[sid].items() if k not in ("tag",)}
        d = proj / "assets" / sid
        # ids are unique across ALL types (the project's assets/ folder is flat): never overwrite a plant called like the place
        for f in (d / "asset.json", *L.LIB.glob(f"*/{sid}/asset.json")):
            if f.exists() and json.loads(f.read_text(encoding="utf-8")).get("type") != "places":
                die(f"\"{sid}\" is already the id of a {json.loads(f.read_text(encoding='utf-8')).get('type')} asset ({rel(f)}). "
                    f"Rename the story place in cards/_film.json \"sets\" (and in the cards), e.g. {sid}_place, then run this again.")
        d.mkdir(parents=True, exist_ok=True)
        kind = "composed landscape" if "compose" in spec else "room" if "room" in spec else "town" if "town" in spec else "set"
        rec = {"id": sid, "type": "places", "name": opt(args, "--name", sid.replace("_", " ")),
               "tags": [t for t in (opt(args, "--tags", "") or "").split(",") if t] or ["place", kind.split()[0]],
               "doc": opt(args, "--doc", f"a {kind}: {sets[sid].get('tag') or sid}"), "spec": spec, "source": {"kind": "code"},
               "project": proj.name, "status": "draft", "created": TODAY}
        (d / "asset.json").write_text(json.dumps(rec, indent=1, ensure_ascii=False), encoding="utf-8")
        print(json.dumps({"place": sid, "asset": rel(d / "asset.json"), "next": "add 3+ tags (region, era, kind), then lib preview / lib promote"}))


def cmd_preview(args, ids=None, into_library=False):
    proj = Path(opt(args, "--project")) if opt(args, "--project") else None
    ids = ids if ids is not None else [a for a in args if not a.startswith("--") and a != opt(args, "--project")]
    pool0 = L.load(proj / "assets") if proj and not into_library else L.load()
    pool = {k: v for k, v in pool0.items() if v.get("type") in L.DRAWABLE and (not ids or k in ids)}
    people = {k: v for k, v in pool0.items() if v.get("type") in ("costumes", "characters") and (not ids or k in ids)}
    places = {k: v for k, v in pool0.items() if v.get("type") == "places" and v.get("spec") and (not ids or k in ids)}
    if not pool and not people and not places:
        die("nothing to preview (props, vehicles, buildings, plants, costumes, characters, places)")
    out = (proj / "review" / "assets") if proj and not into_library else (ROOT / "library" / "_previews")
    if out.exists():
        shutil.rmtree(out)
    _render(places_plan(places, people_plan(people, preview_plan(pool, grid="--grid" in args), proj), proj), out)
    every = {**pool, **people, **places}
    if into_library or not proj:
        for f in out.glob("a*_*.jpg"):
            aid = re.sub(r"^a\d{3}_", "", re.sub(r"_\d+$", "", f.stem))
            if aid in every:
                shutil.copyfile(f, Path(every[aid]["_dir"]) / "preview.jpg")
        shutil.rmtree(out)
        print(json.dumps({"previews": len(every)}))
    else:
        subprocess.run([sys.executable, str(ROOT / "tools" / "contact_sheet.py"), str(out), "--per", "6"], cwd=ROOT)
        print(json.dumps({"sheets": sorted(rel(p) for p in out.glob("sheet_*.jpg")), "next": "look at every sheet; fix asset.json; lib check"}, indent=1))


# ================================================================== promote
def cmd_promote(args):
    proj = Path(opt(args, "--project") or die("add --project projects/<slug>"))
    ids = [a for a in args if not a.startswith("--") and a != opt(args, "--project")]
    pool = L.load(proj / "assets")
    pool = {k: v for k, v in pool.items() if not ids or k in ids}
    known = L.load()
    done, blocked = [], []
    for aid, a in sorted(pool.items()):
        errs, warns = check_asset(a)
        if errs:
            blocked.append(f"{aid}: {errs[0]}")
            continue
        if aid in known and "--replace" not in args:
            blocked.append(f"{aid}: already in the library ({known[aid]['_dir']}). Use --replace, or rename it (a variant: {aid}_2)")
            continue
        dst = L.LIB / a["type"] / aid
        if dst.exists():
            shutil.rmtree(dst)
        shutil.copytree(a["_dir"], dst, ignore=shutil.ignore_patterns("*.psd", "*.tmp"))
        rec = json.loads((dst / "asset.json").read_text(encoding="utf-8"))
        rec.update({"status": "approved", "project": rec.get("project") or proj.name, "promoted": TODAY})
        (dst / "asset.json").write_text(json.dumps(rec, indent=1, ensure_ascii=False), encoding="utf-8")
        _shrink_sources(dst / "source")
        done.append(aid)
    if done:
        # promotion MOVES the asset: one copy only (the film now uses the library one; improvements reach every film)
        if "--keep" not in args:
            for aid in done:
                shutil.rmtree(pool[aid]["_dir"], ignore_errors=True)
            pool = {k: {**v, "_dir": str(L.LIB / v["type"] / k)} for k, v in pool.items()}
        drawable = [k for k in done if pool[k].get("type") in L.DRAWABLE + ("costumes", "characters", "places")]
        if drawable:
            cmd_preview([], ids=drawable, into_library=True)
        index()
    print(json.dumps({"promoted": done, "blocked": blocked, "index": "library/INDEX.md"}, indent=1, ensure_ascii=False))


def _shrink_sources(d: Path, max_side=1280):
    """keep source pictures small (the disk is precious): longest side ≤ max_side"""
    if not d.exists():
        return
    try:
        from PIL import Image
    except ImportError:
        return
    for f in d.glob("*"):
        if f.suffix.lower() in (".png", ".jpg", ".jpeg", ".webp"):
            im = Image.open(f)
            if max(im.size) > max_side:
                im.thumbnail((max_side, max_side))
                im.save(f)


# ================================================================== match (the project's inventory against the library)
KIND_TYPES = {"person": ("characters", "costumes"), "people": ("characters", "costumes"), "character": ("characters", "costumes"),
              "costume": ("costumes",), "place": ("places",), "set": ("places",), "building": ("buildings", "places"),
              "thing": ("props",), "prop": ("props",), "vehicle": ("vehicles",), "plant": ("plants",), "tree": ("plants",),
              "weather": ("weather",), "plate": ("plates",), "background": ("plates", "places")}


def read_needs(proj: Path):
    f = proj / "cards" / "_needs.json"
    if f.exists():
        return json.loads(f.read_text(encoding="utf-8"))
    u = proj / "understanding.md"
    if not u.exists():
        die("no inventory: fill understanding.md §8b (or cards/_needs.json)")
    text = u.read_text(encoding="utf-8")
    m = re.search(r"##\s*8b\..*?\n(.*?)(?:\n##\s|\Z)", text, re.S)
    rows = []
    for line in (m.group(1) if m else "").splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) >= 3 and cells[0] and not set(cells[0]) <= {"-", ":"} and cells[0].lower() != "kind":
            rows.append({"kind": cells[0].lower(), "id": cells[1], "description": cells[2]})
    return rows


def cmd_match(args):
    proj = Path(opt(args, "--project") or die("add --project projects/<slug>"))
    needs = read_needs(proj)
    entries = index(write=False)
    fj = proj / "cards" / "_film.json"
    film_sets = (json.loads(fj.read_text(encoding="utf-8")).get("sets") or {}) if fj.exists() else {}
    entries += [{"id": k, "type": v.get("type"), "source": "project", "name": v.get("name", k), "tags": v.get("tags", []), "doc": v.get("doc", "")}
                for k, v in L.load(proj / "assets").items()]
    lines = ["# Inventory against the library", "", f"Project `{proj.name}` · {TODAY} · made by `python tools/lib.py match`.", "",
             "| need | kind | best match | score | decision | next |", "|---|---|---|---|---|---|"]
    out = []
    for n in needs:
        types = KIND_TYPES.get(n["kind"].rstrip("s"), None) or KIND_TYPES.get(n["kind"], None)
        hits = search(f"{n.get('id', '')} {n.get('description', '')}", types, 3, entries)
        best_s, best = hits[0] if hits else (0, None)
        # the same id already in the library (or the engine): use it as it is
        same = [e for e in entries if e["id"] == n.get("id") and (not types or e["type"] in types) and e["source"] != "project"]
        if same and not (best and best["source"] == "project" and best["id"] == n.get("id")):
            best_s, best = 1.0, same[0]
        if types and "places" in types and n.get("id") in film_sets:
            out.append({"need": n, "best": n["id"], "score": 1.0, "decision": "defined in this film"})
            lines.append(f"| {n.get('id')}: {n.get('description', '')[:60]} | {n['kind']} | {n['id']} (cards/_film.json sets) | 1.00 | defined in this film | "
                         f"keep it for the next film: `lib place {n['id']} --project {rel(proj)}` |")
            continue
        person = bool(types) and "characters" in types
        if best and best["source"] == "project":
            dec, nxt = "made in this project", f"`lib preview --project {rel(proj)} {best['id']}`"
        elif person and best and best["type"] == "characters" and best_s >= 0.3:
            # people are never drawn from scratch: a preset + look fields + costume pieces makes anyone
            dec, nxt = f"use preset `{best['id']}`", f'cast: {{"{n.get("id") or "who"}": {{"preset": "{best["id"]}"}}}} (+ colours, costume pieces; preview)'
        elif best_s >= 0.7:
            dec, nxt = f"use `{best['id']}`", best.get("how") or "use it"
        elif best_s >= 0.45:
            dec, nxt = f"adapt from `{best['id']}`", f"`lib new {(types or ['props'])[0]} {n.get('id') or 'new_id'} --project {rel(proj)} --from {best['id']}`" if best["source"] == "library" else (best.get("how") or "")
        else:
            dec, nxt = "create new", f"`lib new {(types or ['props'])[0]} {n.get('id') or 'new_id'} --project {rel(proj)}`"
        out.append({"need": n, "best": best and best["id"], "score": best_s, "decision": dec})
        lines.append(f"| {n.get('id')}: {n.get('description', '')[:60]} | {n['kind']} | {best['id'] if best else '—'} ({best['source'] if best else ''}) | {best_s:.2f} | {dec} | {nxt} |")
    (proj / "work").mkdir(exist_ok=True)
    (proj / "work" / "match.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    summary = {d: sum(1 for o in out if o["decision"].startswith(d)) for d in ("use", "adapt", "create", "made", "defined")}
    print(json.dumps({"needs": len(out), **summary, "report": rel(proj / "work" / "match.md")}, indent=1))


# ================================================================== main
def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    cmd, args = sys.argv[1], sys.argv[2:]
    if cmd == "index":
        e = index()
        print(json.dumps({"entries": len(e), "library": sum(1 for x in e if x["source"] == "library"), "index": "library/INDEX.md"}))
    elif cmd == "search":
        q = " ".join(a for a in args if not a.startswith("--") and a not in (opt(args, "--type"), opt(args, "--n")))
        for s, e in search(q, opt(args, "--type"), int(opt(args, "--n", 8))):
            print(f"{s:5.2f}  {e['type']:<10} {e['source']:<8} {e['id']:<28} {e.get('doc', '')[:70]}" + (f"   [{e['preview']}]" if e.get("preview") else ""))
    elif cmd == "new":
        cmd_new(args)
    elif cmd == "check":
        sys.exit(1 if cmd_check(args) else 0)
    elif cmd == "preview":
        cmd_preview(args)
    elif cmd == "promote":
        cmd_promote(args)
    elif cmd == "match":
        cmd_match(args)
    elif cmd == "place":
        cmd_place(args)
    elif cmd in ("import", "style-sheet"):
        import vectorize
        vectorize.main(cmd, args)
    else:
        sys.exit(__doc__)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
