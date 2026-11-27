# Plants — trees, palms, bushes, grass, crops

Examples in the library: `rubber_tree`, `coconut_palm`, `banana_plant`, `lalang_grass`, `jungle_edge` (a whole stretch of
rainforest). They sway in the wind.

## The frame
- Side view, the whole plant from the ground (y 0) to the top. A man is 260 units: a palm ~700, a rubber tree ~690, a
  banana ~360, tall grass ~160.
- The part that sways is a **group** with a pivot at its foot:
  ```json
  {"group": [ …leaf shapes drawn around (0, 0)… ], "id": "crown", "at": [-8, -520], "sway": 1.6, "pivot": [0, 60], "period": 4.2}
  ```
  `sway` = degrees, `period` = seconds per swing. Rows give every plant its own `phase`, so a row never sways in step.

## A complete plant (path B): the lalang grass clump
17 blades, each a thin filled curve from the ground up, in four greens, all in one swaying group:
```json
{"group": [
  {"path": "M-30 0 Q-24 -70 -10 -140 Q-20 -70 -18 0 Z", "fill": "#9db45a", "width": 2},
  {"path": "M-5 0 Q2 -80 20 -155 Q6 -78 7 0 Z", "fill": "#8aa64c", "width": 2},
  …
 ], "id": "blades", "sway": 2.5, "pivot": [0, 0], "period": 2.7}
```
Leafy crowns: draw 6–10 bumpy blobs (`path` with `Q` curves) in 2–3 greens, the darkest at the back, plus 2–3 light
patches without outline on top (`"stroke": false`). Palm fronds: a feather polygon along a curved spine (see
`library/plants/coconut_palm/asset.json`).

## Use it
- In a composed place, as rows in depth (the usual way):
  ```json
  "rows": [{"what": "rubber_tree", "depth": 650, "gap": 120},
           {"what": "rubber_tree", "depth": 800, "gap": 190, "clear": [[700, 1250]]},
           {"what": "lalang_grass", "depth": 1075, "gap": 120}]
  ```
  `depth` = the screen y of their feet (600 horizon … 1080 bottom): far rows small and hazy, near rows big. Rows below the
  people's depth (> 915) stand **in front of** people: a row of grass at 1075 hides a man kneeling at 1015 up to the chest.
  `clear` keeps an x range empty (room for the action).
- As single things: `"things": [{"what": "banana_plant", "at": "right", "depth": "near"}]`.

## Check
- `lib preview --grid`: stands on y 0; the crown group is at the top of the trunk (read it off the grid).
- In a place preview: rows at 3 depths read as a plantation / forest; nothing covers the focus person.
