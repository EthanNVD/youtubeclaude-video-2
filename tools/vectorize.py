"""Image -> library asset (the "image path" of the living library). Called by tools/lib.py:

    python tools/lib.py import <image> --project projects/<slug> --id <id> [--type props|vehicles|buildings|plants|plates]
                                       [--height 170] [--colors 10] [--simplify 1.2] [--snap]
    python tools/lib.py import <wheel.png> --project projects/<slug> --id <id> --as-part wheel_front --at -70,-38 [--spin 360]
    python tools/lib.py style-sheet

What `import` does (vector types):
  1. removes the plain background (the colour of the border, flood-filled from the edges) and crops to the thing
  2. quantises the colours (k-means, --colors, default 10); the darkest colour becomes the house outline colour INK
  3. traces every colour region with its holes (OpenCV contours), simplifies it and smooths it into curves
  4. puts the ground point (bottom centre) at (0, 0) and scales it so the thing is --height units tall (a man is 260)
  5. writes asset.json (+ parts.json when big) and art.svg, copies the picture into source/
--snap moves every colour to the nearest colour of the house palette (more uniform, less faithful).
--as-part adds the picture as a moving group (a wheel, a turret, a crown) to an asset that already exists, centred at --at.
For `plates` (far backgrounds) the picture stays a picture (no tracing): background removed except for the sky layer.

Images must be: one thing, side view (or as asked), flat colours, thick dark outlines, PLAIN WHITE background, nothing
cropped. The prompt templates in library/prompts/ ask an image model for exactly that.
"""
from __future__ import annotations

import datetime as _dt
import json
import shutil
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
INK = "#2a2622"
HOUSE = ["#2a2622", "#f2ead8", "#e9dcc2", "#d9c49a", "#c98a42", "#b27a47", "#8a5a33", "#5a3e2a", "#3a2a1a", "#7a828c", "#4a4a50", "#9aa2a8",
         "#b8392e", "#8a3a2e", "#3a6a8a", "#4f86a8", "#bfe0ef", "#4f7a3a", "#76a458", "#8db86a", "#2f4f2a", "#e3c46a", "#d9b35a", "#f2c9a8",
         "#e8d2b8", "#a8624a", "#c9a27a", "#6b7059", "#55606a", "#fbf8f0"]
DEFAULT_H = {"props": 120, "vehicles": 200, "buildings": 520, "plants": 420}


def _opt(args, name, default=None):
    return args[args.index(name) + 1] if name in args and args.index(name) + 1 < len(args) else default


def _hex(c):
    return "#%02x%02x%02x" % tuple(int(max(0, min(255, v))) for v in c)


def _rgb(h):
    h = h.lstrip("#")
    return np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)], dtype=np.float32)


def load_cut(path: Path, keep_bg=False):
    """RGBA array of the thing alone: background (the border colour, connected to the edges) made transparent, cropped"""
    import cv2
    from PIL import Image
    im = np.array(Image.open(path).convert("RGBA"))
    rgb = im[:, :, :3].astype(np.int16)
    alpha = im[:, :, 3]
    if not keep_bg and alpha.min() == 255:
        border = np.concatenate([rgb[0], rgb[-1], rgb[:, 0], rgb[:, -1]])
        bg = np.median(border, axis=0)
        near = (np.abs(rgb - bg).sum(axis=2) < 60).astype(np.uint8)
        n, lab = cv2.connectedComponents(near, connectivity=4)
        edge = set(np.unique(np.concatenate([lab[0], lab[-1], lab[:, 0], lab[:, -1]]))) - {0}
        bgmask = np.isin(lab, list(edge))
        alpha = np.where(bgmask, 0, 255).astype(np.uint8)
        im[:, :, 3] = alpha
    ys, xs = np.nonzero(alpha > 128)
    if len(xs) == 0:
        raise SystemExit("ERROR: the picture is empty after removing the background — use a plain white background and a dark outline")
    y0, y1, x0, x1 = ys.min(), ys.max(), xs.min(), xs.max()
    return im[max(0, y0 - 2):y1 + 3, max(0, x0 - 2):x1 + 3]


def quantise(rgba, k=10, snap=False):
    import cv2
    a = rgba[:, :, 3] > 128
    px = rgba[:, :, :3][a].astype(np.float32)
    k = max(2, min(k, len(px)))
    crit = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.5)
    _, labels, centers = cv2.kmeans(px, k, None, crit, 3, cv2.KMEANS_PP_CENTERS)
    lab = np.full(a.shape, -1, dtype=np.int32)
    lab[a] = labels.ravel()
    lum = centers @ np.array([0.299, 0.587, 0.114], dtype=np.float32)
    colors = [_hex(c) for c in centers]
    dark = int(np.argmin(lum))
    if lum[dark] < 90:
        colors[dark] = INK  # the outline colour of the house style
    if snap:
        pal = np.stack([_rgb(h) for h in HOUSE])
        colors = [h if h == INK else HOUSE[int(np.argmin(((pal - _rgb(h)) ** 2).sum(axis=1)))] for h in colors]
    return lab, colors, dark


def _smooth_path(pts, corner_deg=38.0):
    """closed polygon -> path that keeps real corners sharp (roofs, walls, wheels' spokes) and rounds only the gentle bends
    (a curve traced from pixels is a chain of short straight steps: those become smooth curves through the midpoints)"""
    import math
    n = len(pts)
    if n < 3:
        return ""

    def turn(i):
        ax, ay = pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1]
        bx, by = pts[(i + 1) % n][0] - pts[i][0], pts[(i + 1) % n][1] - pts[i][1]
        la, lb = math.hypot(ax, ay), math.hypot(bx, by)
        if la == 0 or lb == 0:
            return 180.0
        c = max(-1.0, min(1.0, (ax * bx + ay * by) / (la * lb)))
        return math.degrees(math.acos(c))

    corner = [turn(i) > corner_deg for i in range(n)]
    mid = lambda a, b: ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)  # noqa: E731
    f = lambda q: f"{q[0]:.1f} {q[1]:.1f}"  # noqa: E731
    if not any(corner):  # an organic shape (a crown, a cloud): one smooth closed curve
        ms = [mid(pts[i], pts[(i + 1) % n]) for i in range(n)]
        return f"M{f(ms[-1])} " + " ".join(f"Q{f(pts[i])} {f(ms[i])}" for i in range(n)) + " Z"
    s0 = corner.index(True)
    order = [(s0 + k) % n for k in range(n)]
    d = [f"M{f(pts[s0])}"]
    prev_corner = True
    for k in range(1, n + 1):
        i = order[k % n]
        p, prev = pts[i], pts[order[k - 1]]
        if corner[i]:
            d.append(f"L{f(p)}")
            prev_corner = True
        else:
            if prev_corner:
                d.append(f"L{f(mid(prev, p))}")
            nxt = pts[(i + 1) % n]
            d.append(f"Q{f(p)} {f(mid(p, nxt))}")
            prev_corner = False
    return " ".join(d) + " Z"


def trace(lab, colors, dark, k_units, origin, simplify=1.2, min_area=6.0):
    """colour regions -> parts (paths in asset units), big regions first, the outline colour last"""
    import cv2
    ox, oy = origin
    order = sorted(range(len(colors)), key=lambda i: (i == dark, -int((lab == i).sum())))
    parts, points = [], 0
    for i in order:
        mask = (lab == i).astype(np.uint8) * 255
        if mask.sum() == 0:
            continue
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, np.ones((2, 2), np.uint8))
        cnts, hier = cv2.findContours(mask, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_NONE)
        if hier is None:
            continue
        subpaths = []
        for j, c in enumerate(cnts):
            if cv2.contourArea(c) < min_area:
                continue
            ap = cv2.approxPolyDP(c, simplify, True).reshape(-1, 2)
            if len(ap) < 3:
                continue
            pts = [((x - ox) * k_units, (y - oy) * k_units) for x, y in ap]
            points += len(pts)
            subpaths.append(_smooth_path(pts))
        if subpaths:
            parts.append({"path": " ".join(subpaths), "fill": colors[i], "stroke": False, "rule": "evenodd"})
    return parts, points


def to_svg(parts, bb):
    x0, y0, x1, y1 = bb
    body = "\n".join(f'  <path d="{p["path"]}" fill="{p["fill"]}" fill-rule="evenodd"/>' for p in parts if p.get("path"))
    return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{x0 - 10:.0f} {y0 - 10:.0f} {x1 - x0 + 20:.0f} {y1 - y0 + 20:.0f}">\n{body}\n</svg>\n'


def cmd_import(args):
    sys.path.insert(0, str(ROOT / "tools"))
    from cardlib import library as L
    import lib as LIBTOOL
    src = Path(args[0])
    if not src.exists():
        raise SystemExit(f"ERROR: {src} does not exist")
    proj = Path(_opt(args, "--project") or sys.exit("ERROR: add --project projects/<slug>"))
    aid = _opt(args, "--id") or sys.exit("ERROR: add --id <asset id>")
    type_ = _opt(args, "--type", "props")
    d = proj / "assets" / aid
    rec_f = d / "asset.json"
    rec = json.loads(rec_f.read_text(encoding="utf-8")) if rec_f.exists() else {
        "id": aid, "type": type_, "name": aid.replace("_", " "), "tags": [], "doc": "", "size": 1.0, "anchors": {"ground": [0, 0]},
        "parts": [], "project": proj.name, "status": "draft", "created": _dt.date.today().isoformat()}
    (d / "source").mkdir(parents=True, exist_ok=True)
    if src.resolve() != (d / "source" / src.name).resolve():
        shutil.copyfile(src, d / "source" / src.name)

    if rec.get("type") == "plates" or type_ == "plates":
        # far backgrounds stay pictures: keep the sky whole, cut the background of the other layers
        from PIL import Image
        layer = _opt(args, "--layer", "far")
        keep = layer == "sky"
        rgba = load_cut(src, keep_bg=keep) if not keep else np.array(Image.open(src).convert("RGBA"))
        Image.fromarray(rgba).save(d / f"{layer}.png")
        rec.setdefault("layers", {})[layer] = f"{layer}.png"
        rec["type"] = "plates"
        rec["source"] = {"kind": "image", "files": sorted({*rec.get("source", {}).get("files", []), src.name})}
        rec_f.write_text(json.dumps(rec, indent=1, ensure_ascii=False), encoding="utf-8")
        print(json.dumps({"asset": str(d), "layer": layer, "size": rgba.shape[1::-1]}))
        return

    rgba = load_cut(src)
    from PIL import Image
    h_px, w_px = rgba.shape[:2]
    if max(h_px, w_px) > 900:  # tracing speed and point count
        f = 900 / max(h_px, w_px)
        rgba = np.array(Image.fromarray(rgba).resize((max(1, int(w_px * f)), max(1, int(h_px * f))), Image.LANCZOS))
        h_px, w_px = rgba.shape[:2]
    lab, colors, dark = quantise(rgba, int(_opt(args, "--colors", 10)), "--snap" in args)
    part_name = _opt(args, "--as-part")
    if part_name:
        if not rec.get("parts"):
            raise SystemExit("ERROR: --as-part adds a moving part to an asset that already has its body: import the body first")
        # the part is centred on its own middle and sized against the body (--height = its height in asset units)
        k = float(_opt(args, "--height", 80)) / h_px
        parts, pts = trace(lab, colors, dark, k, (w_px / 2, h_px / 2), float(_opt(args, "--simplify", 1.2)))
        at = [float(v) for v in (_opt(args, "--at", "0,0")).split(",")]
        group = {"group": parts, "at": at, "id": part_name, "center": [0, 0], "pivot": [0, 0]}
        if _opt(args, "--spin"):
            group["spin"] = float(_opt(args, "--spin"))
        if _opt(args, "--sway"):
            group["sway"] = float(_opt(args, "--sway"))
        rec["parts"] = [p for p in rec["parts"] if p.get("id") != part_name] + [group]
    else:
        height = float(_opt(args, "--height", rec.get("h") or DEFAULT_H.get(rec.get("type", type_), 150)))
        k = height / h_px
        parts, pts = trace(lab, colors, dark, k, (w_px / 2, h_px), float(_opt(args, "--simplify", 1.2)))
        keep_groups = [p for p in rec.get("parts", []) if p.get("group") is not None]
        rec["parts"] = parts + keep_groups
        rec["h"] = round(height)
    rec["source"] = {"kind": "image", "files": sorted({*rec.get("source", {}).get("files", []), src.name}), "colors": int(_opt(args, "--colors", 10)),
                     "simplify": float(_opt(args, "--simplify", 1.2)), "snap": "--snap" in args}
    big = sum(len(p.get("path", "")) for p in rec["parts"]) > 60000
    if big:
        (d / "parts.json").write_text(json.dumps(rec["parts"]), encoding="utf-8")
        rec["parts_file"] = "parts.json"
        out = {k2: v for k2, v in rec.items() if k2 != "parts"}
    else:
        out = {k2: v for k2, v in rec.items() if k2 != "parts_file"}
        (d / "parts.json").unlink(missing_ok=True)
    rec_f.write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")
    bb = LIBTOOL.bbox(rec["parts"]) or (-50, -100, 50, 0)
    (d / "art.svg").write_text(to_svg([p for p in rec["parts"] if p.get("path")], bb), encoding="utf-8")
    print(json.dumps({"asset": str(d), "parts": len(rec["parts"]), "points": pts, "colors": sorted(set(colors)),
                      "next": f"python tools/lib.py preview --project {proj.as_posix()} {aid} --grid   then fill tags/doc/anchors and lib check"}, indent=1))


def cmd_style_sheet(args):
    """library/STYLE_REFERENCE.jpg: what the house style looks like, to attach when an image model draws an asset"""
    sys.path.insert(0, str(ROOT / "tools"))
    from cardlib import library as L
    import subprocess
    lib = L.drawables()
    els = []
    for k, (who, pose) in enumerate((("japanese_soldier", "idle"), ("british_soldier", "idle"), ("civilian_woman", "basket"), ("worker", "carry"))):
        el = {"kind": "actor", "who": who, "x": 230 + k * 210, "y": 560, "scale": 1.5, "pose": pose, "expr": "neutral"}
        if pose == "basket":
            el["holds"] = "basket"
        if pose == "carry":
            el["holds"] = "crate"
        els.append(el)
    for k, aid in enumerate(a for a in ("bicycle", "field_kitchen", "notice_board", "shovel") if a in lib):
        a = lib[aid]
        import lib as LIBTOOL
        bb = LIBTOOL.bbox(a["parts"]) or (0, 0, 0, 0)
        sc = 0.9 * float(a.get("size", 1.0))
        els.append({"kind": "drawing", "x": 260 + k * 420, "y": round(1000 - max(0.0, bb[3]) * sc), "scale": sc, "parts": a["parts"]})
    els += [{"kind": "prop", "item": it, "x": 1150 + k * 150, "y": 560, "scale": 0.9} for k, it in enumerate(("crate", "barrel", "sack", "pot", "bread"))]
    els.append({"kind": "label", "text": "HOUSE STYLE: flat colours · thick dark outline #2a2622 · no gradients · no texture · simple chunky shapes",
                "x": 960, "y": 80, "style": "tag", "size": 30, "in": 0, "enter": "none"})
    for k, h in enumerate(HOUSE[:20]):
        els.append({"kind": "drawing", "x": 1180 + (k % 10) * 70, "y": 260 + (k // 10) * 80, "scale": 1, "parts": [{"rect": [-30, -60, 60, 60], "r": 6, "fill": h}]})
    plan = {"meta": {"title": "style", "fps": 24, "width": 1920, "height": 1080, "duration": 2.0, "grade": "none"}, "cast": {},
            "scenes": [{"id": "style", "start": 0, "end": 2.0, "type": "stage", "set": {"kind": "paper"}, "elements": els, "transition": "cut"}]}
    out = ROOT / "library" / "_style"
    out.mkdir(parents=True, exist_ok=True)
    (out / "plan.json").write_text(json.dumps(plan), encoding="utf-8")
    subprocess.run(["node", str(ROOT / "tools" / "render.mjs"), "stills", str(out / "plan.json"), str(out), "--scale", "1", "--at", "mid"], cwd=ROOT, check=True)
    got = sorted(out.glob("style_*.jpg"))
    if got:
        shutil.copyfile(got[0], ROOT / "library" / "STYLE_REFERENCE.jpg")
    shutil.rmtree(out)
    print(json.dumps({"style_sheet": "library/STYLE_REFERENCE.jpg"}))


def main(cmd, args):
    if cmd == "import":
        if not args:
            sys.exit(__doc__)
        cmd_import(args)
    elif cmd == "style-sheet":
        cmd_style_sheet(args)
