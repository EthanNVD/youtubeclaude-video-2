# Places — story places, kept for the next film

A place is what a scene card names in `"where"`. Three kinds:
- **room** and **town** from the engine kit (`"room": "office"`, `"town": "village"`; `make.py … preview --kit` shows them);
- **compose**: a landscape built in layers from library assets — any region, any season;
- an engine **set** (`"set": "beach"`).

Library places (type `places`) keep the spec of a story place: `"where": "kampong"` in any film.
In the library now: `rubber_estate`, `estate_road`, `estate_road_open`, `roadblock`, `kampong`, `rainforest_edge`,
`jungle_myth`, `malay_town`, `singora_beach`.

## A composed place, layer by layer
```json
"estate_road": {
 "compose": {
  "far": ["treeline"],
  "ground": "grass",
  "road": {"kind": "laterite", "y": 885, "w": 210},
  "rows": [{"what": "rubber_tree", "depth": 650, "gap": 120},
           {"what": "rubber_tree", "depth": 720, "gap": 150},
           {"what": "rubber_tree", "depth": 800, "gap": 190},
           {"what": "lalang_grass", "depth": 1075, "gap": 120}],
  "plates": ["malaya_hills"]
 },
 "horizon": 600, "weather": "haze", "time": "day", "tag": "Behind the Japanese lines · January 1942"}
```
| field | values | what it does |
|---|---|---|
| `far` | `hills` `mountains` `jungle` `treeline` `palms` `sea` `town` `none` (a list: several layers) | flat shapes on the horizon |
| `ground` | `grass` `laterite` `sand` `paddy` `mud` `dry` `jungle_floor` `snow` | the ground colour and texture |
| `road` | `{"kind": laterite\|dirt\|tarmac\|cobbles\|sand, "y": depth, "w": width}`; `{"away": true, "x": 960, "vx": 1100, "bw": 900}` = a road going away from us | a road across the frame (people and cyclists use it) |
| `rows` | `{"what", "depth", "gap", "from", "to", "jitter", "scale", "flip": "random\|alternate\|none", "vary", "clear": [[x0, x1]], "spread"}` | a row of library assets at a depth |
| `items` | `{"what", "at", "depth"}` | one asset at a place |
| `plates` | plate ids (painted far backgrounds) | pictures behind the far layers ([plates](plates.md)) |
| `horizon` | 520–640 (default 560) | where the sky meets the ground; people's sizes follow it |
| `weather`, `time` | see [weather](weather.md); `day` `dawn` `dusk` `night` | haze and fog fade the distance too |
| `ambience` | `jungle` `sea` `wind` … | the sound bed (default: from what is in the place) |

Depth = the screen y of the feet: 600 (horizon) … 1080 (bottom). People stand at `far` 815, `back` 860, `mid` 915,
`near` 965, `front` 1015. Rows near the horizon are drawn in the haze; rows below the people stand in front of them.

## Make one
1. Write it in `cards/_film.json` `"sets"`; `make.py … preview` shows it with a man for scale; change gaps and depths.
2. Use it in the cards (`"where": "estate_road", "place_id": "estate_road"`).
3. Keep it: `python tools/lib.py place estate_road --project projects/<slug> --tags malaya,plantation,road,ww2 --doc "…"`,
   then `lib promote`. The tag (place/time text) is not kept: every film writes its own.

## Use a library place
```json
{"at": "…", "recipe": "scene", "where": "kampong", "place_id": "kampong", "tag": "A kampong near Kuantan · 1942", …}
```

## Check
Place sheets in `make.py … preview`: the man for scale stands on the road or the grass; nothing big hides the middle of
the frame; far rows look far (small, hazy); the rows join up (no holes, no pile-ups).
