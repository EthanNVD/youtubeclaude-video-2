# `scene` (action)

**Use it when:** ANY moment the narration describes that no ready-made recipe shows exactly — and most moments of everyday life, politics, the home front, economics, consequences: a family at supper, a queue at a bakery, an admiral at a chart, dockers unloading cotton, a farmer in a rotten field. Write the director's `idea` first, then stage it: where, who, what they do on which words, the camera.

**Do NOT use it when:** A battle, a map move, a chart: use those recipes (assault, wave, map_*, chart). A scene must show people/things doing what the clause says.

**Camera (what the compiler does, per variant):** Chosen by `camera` (auto picks from the content and never repeats the previous card's camera). Shots dissolve (0.6 s).

## Fields

| field | required | value | default | meaning |
|---|---|---|---|---|
| `idea` | **yes** | text |  | the director's note: what the viewer SEES and why it tells this clause (one sentence, 10+ words). Write it before anything else |
| `where` | no | text |  | a story place from cards/_film.json "sets", a library place (kampong, rubber_estate…), a room style, a town style, an engine set, or an object {"room": "kitchen", "items": [...]} / {"compose": {"far": [...], "ground": "grass", "rows": [...]}} |
| `people` | no | list |  | persons: {who, id, at, depth, face, mood, pose, holds, seated, kneel, walk, rides (a vehicle drawing, e.g. bicycle: he sits on it and enter/exit/walk_to ride it), size, name_card, do: [{act, on, till, to, with, expr}]} |
| `crowd` | no | object |  | {kind: queue|watchers|walkers|marchers|cyclists|mourners|cheering|workers|protest|listeners, n, who: [presets], at, depth, toward, mood, react_on; cyclists: abreast, vehicle} |
| `things` | no | list |  | props: {what, id, at, depth, on (another thing's id), held_by, n, text, color, appear (phrase), scale, steam/lit} |
| `effects` | no | list |  | {fx: smoke|fire|explosion|shellburst|dust|steam|sparks|exclaim|question…, at, depth, on, over (person), size} |
| `vehicles` | no | list |  | {type: battleship|cruiser|cargo|truck|cart|wagon|horse|train…, nation, at, depth (or screen y, e.g. 660 on the sea), to (moves there), on, till, scale, flip} |
| `camera` | no | text |  | wide | push_in | pan | wide_then_close | close_then_wide | detail_then_wide | medium | close | two_shot | group | follow | over_shoulder | auto (default) — or a list of shots [{on, frame, size}] |
| `focus` | no | text |  | the person (or thing) the camera favours; default the first person |
| `partner` | no | text |  | second person for two_shot / over_shoulder |
| `close_on` | no | words copied from this card's narration |  | words where wide_then_close moves in |
| `wide_on` | no | words copied from this card's narration |  | words where close_then_wide / detail_then_wide pulls out |
| `detail` | no | text |  | the thing id detail_then_wide starts on |
| `revisit` | no | true / false | `false` | true = this deliberately repeats an earlier composition (a callback); silences the repetition check |
| `wish` | no | list |  | things you wanted but the engine lacks ("a horse-drawn cart") — logged in work/missing_assets.json for the next engine upgrade |
| `life` | no | true / false | `true` | false = no automatic gestures (a frozen tableau) |

Plus the common fields (`at`, `recipe`, `says`, `variant`, `date`, `place`, `name_card`, `label`, `counter`, `stamp`, `time`, `weather`, `tint`, …) — see [CATALOG.md](CATALOG.md#fields-every-card-can-have).

Variants: A (leave `variant` out: the compiler rotates them so the film never repeats a composition).

## Example card

```json
{
 "at": "Then came a bad harvest.",
 "recipe": "scene",
 "says": "A bad harvest made the hunger much worse.",
 "idea": "A farmer kneels in a grey field and lifts a rotten potato; his wife stands behind him with an empty basket.",
 "where": "field",
 "time": "dusk",
 "weather": "rain",
 "people": [
  {
   "who": "worker",
   "id": "farmer",
   "at": "center_left",
   "depth": "near",
   "mood": "sad",
   "kneel": true,
   "do": [
    {
     "act": "hold_up",
     "with": "turnip",
     "on": "bad harvest"
    }
   ]
  },
  {
   "who": "civilian_woman",
   "at": "center_right",
   "depth": "back",
   "mood": "worried",
   "holds": "basket",
   "pose": "basket"
  }
 ],
 "things": [
  {
   "what": "potatoes",
   "at": "center",
   "depth": "front",
   "color": "#5a4a32",
   "n": 7
  }
 ],
 "camera": "wide_then_close",
 "focus": "farmer",
 "close_on": "harvest"
}
```
