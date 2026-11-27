# The living library

Everything a film can show and that the engine did not always have lives here, one folder per thing:
people's costume pieces, props, vehicles, buildings, plants, places, painted far backgrounds, weather.

**The rule of every film:**
1. **Find** what the story needs (`lib match`).
2. **Use** what exists. **Adapt** what is close. **Create** only what is missing.
3. **Preview** and **check** it.
4. **Promote** it here, so the next film starts richer.

The whole loop for a film is in [playbook/library.md](../playbook/library.md). This page is the reference: what is in an asset and how to make one.

---

## 1. Layout

```
library/
  README.md              this page
  INDEX.md, index.json   the catalogue (generated: python tools/lib.py index) — search it: python tools/lib.py search "words"
  STYLE_REFERENCE.jpg    what the house style looks like (attach it when an image model draws)
  prompts/<type>.md      the image prompt for each kind of asset
  <type>/<id>/
    asset.json           the record (§3)
    parts.json           the drawing when it is big (asset.json then has "parts_file": "parts.json")
    art.svg              the picture as SVG (made by import; for people to look at)
    source/              the original picture(s) and prompt (image path)
    preview.jpg          made by lib preview / lib promote
```

A film makes its new assets in `projects/<slug>/assets/<id>/` (same layout, `"status": "draft"`).
- **Before promotion:** they already work in that film's cards.
- **After promotion:** they work in every film.

## 2. Types

| type | what | used in a scene card as |
|---|---|---|
| `props` | things held or standing (a shovel, a lectern, a notice board) | `"things": [{"what": "<id>"}]`, `"holds": "<id>"`, `"with": "<id>"` |
| `vehicles` | things that move (a bicycle, a cart, an airship) | `"things": [{"what": "<id>", "to": "right", "when": "words"}]` |
| `buildings` | whole buildings (a kampong house, a shophouse) | `"things"` at the back, or in a composed place |
| `plants` | trees, palms, bushes, crops (sway) | `"things"`, or rows in a composed place |
| `costumes` | pieces people wear (hats, turbans, sarongs) | in the cast entry (playbook/library.md §Costumes) |
| `characters` | ready cast looks | copy into `cards/_film.json` "cast" |
| `places` | story places (a room / town spec, or a composed landscape) | `"where": "<id>"` |
| `plates` | painted FAR background layers (sky, far, mid) | in a composed place |
| `weather` | weather presets | `"weather": "<id>"` |

The engine's own code-drawn things are in the index too, as `builtin`:
- props, vehicles, cast presets, sets;
- room and town styles and their modules;
- look options.

`lib search` finds both kinds.

## 3. The record: asset.json

```json
{
 "id": "rubber_tree",                      // lowercase, digits, _ ; unique in the library
 "type": "plants",
 "name": "Rubber tree (tapped)",
 "tags": ["malaya", "ww2", "plantation", "tree", "tropical", "rubber"],   // region, era, kind: 3 or more
 "doc": "a tapped rubber tree with a latex cup, planted in rows in Malayan estates",
 "size": 1.0,                              // scale next to a man when the drawing is in man-units (a man = 260 units tall)
 "h": 420,                                 // height of the drawing in its own units
 "top": 0,                                 // props/furniture: height of the top surface things stand on
 "anchors": {"ground": [0, 0], "grip": [0, -30]},   // grip = where a hand holds it (held things)
 "floats": false,                          // true = in the sky / on water: no ground check
 "parts": [ … ],                           // the drawing (§4)
 "source": {"kind": "image", "files": ["rubber_tree.png"], "colors": 8},   // or {"kind": "code"}
 "project": "malaya-test", "status": "approved", "created": "2026-11-27"
}
```

## 4. The drawing: parts

Coordinates:
- `(0, 0)` is where the thing **stands**: the bottom centre.
- **y up is negative**.
- A man is **260 units** tall, a door ~250, a table ~120, a one-storey house ~500.
- A thing that is held is drawn around the **hand** instead, and gives `"anchors": {"grip": [x, y]}`.

Shapes:
- `{"rect": [x, y, w, h], "r": 6}`
- `{"circle": [cx, cy, r]}`
- `{"ellipse": [cx, cy, rx, ry]}`
- `{"poly": [[x, y], …]}`
- `{"line": [[x, y], …], "width": 8}`
- `{"path": "M… Z", "rule": "evenodd"}`
- `{"text": "SIGN", "at": [x, y], "size": 24}`

Style on any part:
- `fill`;
- `stroke` (`false` = no outline; the default outline is the house ink);
- `width` (outline, default 4);
- `opacity`.

Motion on any part:
- `spin` (deg/s around `center`);
- `sway` (degrees around `pivot`, with `period` seconds);
- `bob` (px up and down);
- `flicker` (flames);
- `blink` (lamps);
- `drift`;
- `phase` (seconds of offset).

**Moving parts:** put them in a group, which moves as one around its own origin.

```json
{"group": [ …wheel parts drawn around (0, 0)… ], "id": "wheel_front", "at": [-70, -38], "spin": 240}
{"group": [ …crown parts… ], "id": "crown", "at": [0, -300], "sway": 3, "pivot": [0, 40], "period": 4}
```

Write parts in this order: big shapes first, details after, outlines included (each shape has its own outline unless `"stroke": false`).

## 5. Making an asset — two ways, same result

Start with `python tools/lib.py new <type> <id> --project projects/<slug> --name "…" --tags a,b,c --doc "…"`.
- It makes the folder, a blank record, `request.md` (fill it in) and `prompt.txt` (the image prompt for this type).
- `--from <existing id>` starts from a copy of a close asset: the **adapt** path, e.g. recolour, extend, change a part.

### A. You can make images (Muse)
1. Fill `request.md`.
2. Make the picture with `prompt.txt` and attach `library/STYLE_REFERENCE.jpg`. Keep to the rules:
   - one thing;
   - the view the prompt asks;
   - plain white background;
   - thick dark outlines;
   - flat colours.
3. Save it in the asset's `source/` folder.
4. `python tools/lib.py import <folder>/source/<file>.png --project projects/<slug> --id <id> --type <type> --height <units>`.
   - `--height` is its height in man-units (a bicycle ~110, a house ~520).
   - `--colors 6..12`: fewer is simpler.
   - `--snap` moves the colours to the house palette.
5. Moving parts: import each part picture with `--as-part <name> --at x,y [--spin 240 | --sway 3]`.
6. Plates (far backgrounds) stay pictures: `--type plates --layer sky|far|mid`.

### B. You cannot make images
Draw the parts in `asset.json` by hand (§4):
- Look at reference photos only to describe the thing: proportions, colours, the 3 details that make it recognisable. Never trace a photo.
- Start from the simplest silhouette (2–4 shapes), then add the details.
- Use a `--from` copy when something close exists.

### Then, both ways
1. `python tools/lib.py preview --project projects/<slug> <id> --grid`: the thing next to a man, on a coordinate grid. Read positions off the grid to fix anchors and moving parts.
2. `python tools/lib.py check --project projects/<slug> <id>`: fix every ERROR; read every warning.
3. Use it in the cards. It already works in this film.
4. At the end of the film: `python tools/lib.py promote --project projects/<slug>`. It refuses ids that exist (use `--replace` or a variant id like `rubber_tree_2`), shrinks source pictures, makes `preview.jpg` and updates INDEX.md.

## 6. Rules that keep the library good
- **Search before you make.** `lib search` with 2–4 words. Read the top 5. A close one is adapted, not duplicated.
- **Names say what it is:** `kampong_house`, `rubber_tree`, `sikh_turban`. Not `house2` or `tree_new`.
- **Tags:** at least 3 (region, era, kind), so the next film finds it.
- **One thing per asset.** A street is a place made of many assets, not one picture.
- **Near things are vectors; painted pictures are only for far backgrounds** (plates).
- **No photos traced, no logos, no real flags painted wrong, no hate symbols.**
- **Small and simple wins:** ≤ 12 colours, no tiny specks (`lib check` warns).
