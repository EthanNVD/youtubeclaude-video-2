# The living library — find, make and keep everything a film shows

Every film needs people, clothes, places, buildings, plants, vehicles, things and weather.
- Some already exist: **use** them.
- Some are close: **adapt** them.
- The rest are missing: **create** them, with an image model or by drawing in code.
- At the end of the film, **promote** the new ones into `library/`, so the next film starts richer.

This page is the loop. Each kind of asset has its own page with a full worked example in [library/](library/):
[props](library/props.md) · [vehicles](library/vehicles.md) · [buildings](library/buildings.md) · [plants](library/plants.md) ·
[costumes](library/costumes.md) · [characters](library/characters.md) · [places](library/places.md) · [plates](library/plates.md) ·
[weather](library/weather.md). The reference for the asset file itself is [library/README.md](../library/README.md).

The worked example of the whole loop is `projects/malaya-test` (66 s, Malaya 1941–42): read its `understanding.md` §8b and
`cards/_film.json` side by side with this page.

---

## The loop in 7 steps

| # | step | command / file | done when |
|---|---|---|---|
| 1 | **Inventory**: list what the pictures need | `understanding.md` §8b | every person, costume, place, building, plant, vehicle, thing and weather of the beats is a row |
| 2 | **Match** the list against the library | `python tools/lib.py match --project projects/<slug>` | `work/match.md` has a decision for every row |
| 3 | **Use** what exists | ids in `cards/_film.json` and the cards | the compile finds them |
| 4 | **Adapt** what is close | `lib new <type> <id> --from <close id>` or `"recolor"` in the cast | the copy is changed |
| 5 | **Create** what is missing | `lib new <type> <id>` → image path (A) or code path (B) | `lib check` has 0 errors |
| 6 | **Preview** everything new | `lib preview --project … --grid` and `make.py … preview` | every sheet looks right next to a man |
| 7 | **Promote** at the end of the film | `lib promote --project projects/<slug>` | the assets are in `library/`, `INDEX.md` lists them |

Steps 1–6 happen in pre-production, **before the cards**. Step 7 happens after the video is approved.

---

## 1. Inventory (understanding.md §8b)

Read the whole narration first (`playbook/02-understand.md`). Then, for every beat, write down what the picture needs.
One row per need:

```
| kind | id | description | first used at |
|---|---|---|---|
| costume | songkok | Malay black velvet cap | 0:06 |
| plant | rubber_tree | tapped rubber tree with a latex cup, in rows | 0:10 |
| building | kampong_house | Malay house on stilts | 0:43 |
| vehicle | bicycle | a bicycle people ride | 0:04 |
| place | estate_road | red road through a rubber estate | 0:10 |
| weather | haze | humid tropical haze | 0:06 |
```

Rules:
- **kind** is one of: `person`, `costume`, `place`, `building`, `plant`, `vehicle`, `prop` (or `thing`), `plate`, `weather`.
- **id**: lowercase words joined by `_`, saying what it is: `rubber_tree`, `sikh_turban`. Not `tree2`.
- **description**: 4–12 words a stranger could draw. Region and era words help the search ("Malay", "1941", "WW1").
- People: a row per *kind of person* (a Malay villager, a Sikh soldier), not per name. Their clothes are `costume` rows.

## 2. Match

```
python tools/lib.py match --project projects/<slug>
```

It searches the library and the engine for every row and writes `work/match.md`:

| decision | meaning | what you do |
|---|---|---|
| `use <id>` | the same thing exists (score ≥ 0.7, or the same id) | write the id in the cast or the card (§3) |
| `use preset <id>` | (people) a cast preset fits | a cast entry with that preset + colours + costume pieces |
| `adapt from <id>` | something close exists (0.45–0.7) | look at its preview; copy and change it (§4), or use it as it is if it is right |
| `create new` | nothing close | make it (§5) |
| `made in this project` | you already made it in `projects/<slug>/assets/` | preview and check it |
| `defined in this film` | a story place in `cards/_film.json` "sets" | keep it for later films with `lib place` (§7) |

**Always open the preview picture of a match** (`library/<type>/<id>/preview.jpg`) before you trust it. The score only
compares words.

To search by hand: `python tools/lib.py search "malay village house" --n 8`.

## 3. Use

| kind | how a film uses it |
|---|---|
| prop, building, plant, vehicle | `"things": [{"what": "<id>", "at": "left", "depth": "back"}]`, or rows in a composed place |
| held prop | `"holds": "<id>"` on a person (it needs a `grip` anchor) |
| vehicle somebody rides | `"rides": "<id>"` on a person; `"crowd": {"kind": "cyclists", "vehicle": "<id>"}` |
| costume | in the cast entry: `"wear": ["<id>", …]` |
| character | in the cast entry: `"look": "<id>"` |
| place | `"where": "<id>"` in a card (the place is copied from the library) |
| plate | in a composed place: `"plates": ["<id>"]` |
| weather | `"weather": "<kind>"` or `{"kind": …, "amount": …, "wind": …}` on a place or a card |

## 4. Adapt

Two ways, both keep the original untouched:
- **A copy**: `python tools/lib.py new <type> <new_id> --project projects/<slug> --from <close id>`. The copy lands in
  `projects/<slug>/assets/<new_id>/asset.json`. Change what is different (a colour, a part, the size), then preview.
- **Recolour in the cast** (costumes only): `"wear": [{"piece": "sarong", "recolor": {"#3e5d8c": "#8a3a30"}}]`.
  The keys are colours of the piece (read them in its `asset.json`); the values are the new colours.

Name variants by what changes: `sarong_white`, `kampong_house_large`. Never `sarong2`.

## 5. Create

```
python tools/lib.py new <type> <id> --project projects/<slug> --name "Rubber tree (tapped)" --tags malaya,ww2,tree,plantation --doc "a tapped rubber tree with a latex cup"
```

This makes `projects/<slug>/assets/<id>/` with `asset.json` (blank), `request.md` (fill it in) and `prompt.txt` (the image
prompt for this type). Then choose a path:

### Path A — you can make images (an image model such as Muse)
1. Fill `request.md`: what it is, the view, the 3 details that make it right, the colours.
2. Make the picture with `prompt.txt` and attach `library/STYLE_REFERENCE.jpg`. One thing, white background, thick dark
   outlines, flat colours (the prompt says it all).
3. Save it as `projects/<slug>/assets/<id>/source/<id>.png`.
4. `python tools/lib.py import projects/<slug>/assets/<id>/source/<id>.png --project projects/<slug> --id <id> --type <type> --height <man-units>`
   - `--height`: how tall the thing is when a man is 260 (a bicycle 110, a palm 700, a house 520).
   - Moving parts (wheels, a tree crown): import each part picture with `--as-part <name> --at x,y --spin 240` or `--sway 3`.
   - Far backgrounds stay pictures: `--type plates --layer sky|far|mid` ([plates](library/plates.md)).

### Path B — you cannot make images (draw in code)
Write the `parts` of `asset.json` yourself: rectangles, circles, polygons and paths in man-units
([library/README.md §4](../library/README.md)). The type pages show complete examples you can copy and change.
Simple and recognisable beats detailed: 5–25 shapes, 3 details that say "this is a rubber tree".

### Both paths, then
```
python tools/lib.py preview --project projects/<slug> <id> --grid     # the thing next to a man, on a grid
python tools/lib.py check   --project projects/<slug> <id>            # fix every ERROR, read every warning
```
Read positions off the grid to fix anchors and the size. Repeat until it looks right. It already works in this film's cards.

## 6. Preview the film's pre-production

```
python tools/make.py projects/<slug> preview
```
Sheets of the cast (standing and acting, with their costume pieces), every story place (with the rows of plants and
buildings, a man for scale) and every new asset of the film. Look at every sheet before writing cards.

## 7. Promote (after the video is approved)

```
python tools/lib.py place <set id> --project projects/<slug> --tags malaya,plantation,ww2   # keep a story place too
python tools/lib.py promote --project projects/<slug>
```
- `lib place` copies a story place from `cards/_film.json` "sets" into the project's assets (type `places`).
- `promote` checks every asset, **moves** it to `library/<type>/<id>/` (status `approved`), shrinks the source pictures,
  makes `preview.jpg` and rebuilds `library/INDEX.md`. The film keeps working: it now finds them in the library.
- An id that already exists is refused: add `--replace` only if yours is the better version of the same thing, otherwise
  rename it (`rubber_tree_young`).
- Ids are unique across all types: a place cannot be called like a plant.

---

## Rules that keep the library good
1. **Search before you make.** A close asset is adapted, never duplicated.
2. **One thing per asset.** A street is a *place* made of shophouses and palms, not one picture.
3. **Near things are vectors.** Painted pictures are only for far backgrounds (`plates`).
4. **3+ tags**: region, era, kind (`malaya`, `ww2`, `plantation`).
5. **Correct and respectful**: real uniforms and flags right; no hate symbols; no traced photos, no logos.
6. **Small**: ≤ 12 colours, ≤ 6000 points (`lib check` warns).
7. **Commit the library with the film** (asset.json, preview.jpg, small sources). Never commit renders.
