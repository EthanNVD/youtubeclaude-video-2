# Vehicles — things that move: bicycles, carts, rickshaws, boats, airships

Examples in the library: `bicycle`, `field_kitchen`, `zeppelin`. The engine draws many military vehicles itself (tanks,
trucks, ships, planes): search first (`lib search "truck"` shows the `builtin` ones).

## The frame
- **Exact side view, facing right**, all wheels on one level, standing on y 0. y up is negative; a man is 260 units.
- Wheels are **groups** that roll: `{"group": [...wheel drawn around (0, 0)...], "id": "wheel_front", "at": [76, -50], "roll": 48}`.
  `roll` = the wheel's radius: it turns with the distance the vehicle travels (and stops when it stops).
  `spin` (degrees per second) is for things that turn all the time (a propeller, a mill).
- Things that fly or float give `"floats": true` and are placed with a screen `"y"`.

## Something people ride: the bicycle
A rider sits on it, holds the bars and pedals. Give the anchors in the bicycle's own units:
```json
"anchors": {"ground": [0, 0], "seat": [-40, -130], "crank": [-10, -50], "bars": [40, -143]}
```
- `seat`: where the rider's hips sit (the engine lifts the rider so the hips are there, and puts the bicycle under him);
- `crank`: the centre the feet go round (radius 17 units);
- `bars`: where the hands are (for your own check; the `ride` pose already reaches there for a bicycle).
A motorbike, a rickshaw or a horse cart that someone rides needs the same three anchors.

The library bicycle (wheels with spokes that roll):
```json
{"group": [{"circle": [0, 0, 48], "fill": "none", "stroke": "#2a2a2a", "width": 8},
           {"line": [[-44, 0], [44, 0]], "stroke": "#5a5a5a", "width": 3},
           {"line": [[-22, -38], [22, 38]], "stroke": "#5a5a5a", "width": 3},
           {"line": [[22, -38], [-22, 38]], "stroke": "#5a5a5a", "width": 3},
           {"circle": [0, 0, 6], "fill": "#2a2a2a", "stroke": false}],
 "id": "wheel_back", "at": [-70, -50], "roll": 48}
```
then the same at `[76, -50]`, then the frame lines, the saddle rect, the bars.

## Use it
```json
"people": [{"who": "jp_soldier", "at": "right", "rides": "bicycle", "do": [{"act": "walk_to", "to": "center"}]}]
"crowd": {"kind": "cyclists", "who": ["jp_soldier", "jp_soldier2"], "n": 9, "abreast": 3, "toward": "left", "depth": "mid", "start": "in", "at": 1300}
"things": [{"what": "bicycle", "at": "far_left", "depth": "back"}]                     // a parked bicycle
"things": [{"what": "field_kitchen", "at": "off_left", "to": "center", "when": "rolled in"}]  // a moving vehicle
```
- A rider moves with `walk_to`, `enter`, `exit` (at riding speed, with a bicycle sound); he does not walk.
- `cyclists`: rows of riders side by side (`abreast`), chatting; `start: "in"` puts the first row in the frame at `at`
  (short shots), otherwise they ride in from the edge.

## Image path (A)
`prompt.txt` asks for the body and each moving part as separate pictures (`source/body.png`, `source/wheel_front.png`…).
Import the body, then each wheel with `--as-part wheel_front --at 76,-50`, then edit the group: replace `spin` with
`"roll": <radius>` for wheels that roll on the ground.

## Check
- `lib preview --grid`: wheels touch the floor line; size next to the man (a bicycle ~150 high, a cart ~200, a truck ~330).
- For something ridden: preview it in a card (`make.py … review --scenes …`): hips on the seat, feet on the pedals.
