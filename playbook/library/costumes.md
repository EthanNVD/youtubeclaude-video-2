# Costumes — pieces people wear on the engine's rig

People are never drawn from pictures: the engine's rig walks, gestures, talks and rides. A **costume piece** is drawn on
top of the rig in one of five slots. Examples in the library: `songkok`, `sarong`, `sikh_turban`, `slouch_hat`,
`jp_field_cap` (two pieces), `singlet`.

## The slots and their frames
| slot | drawn | frame (where (0, 0) is) | for |
|---|---|---|---|
| `head` | over the head | **head centre**; top of the head y −74, chin +50, ears at x ±66, eyes ~ +5 | caps, hats, turbans, headscarves |
| `headback` | behind the head | same head frame | neck flaps, long hair, a hood's back, a veil's back |
| `body` | over the torso, under the arms | **body frame**: feet y 0, hips −98, shoulders −172; torso half-width ~29 at the shoulders, ~37 at the hem | vests, sashes, necklines, bandoliers |
| `hips` | over the legs, under the torso (add `"above": true` to draw it over the torso) | body frame | sarongs, kilts, skirts, aprons |
| `back` | behind everything | body frame | packs, capes, quivers |

The piece follows the head (tilts, nods) or the body (walks, bobs, rides). Draw it **front view**, as if the person faces
us; it is mirrored with the person.

## A complete one-piece costume: the songkok
```json
{"id": "songkok", "type": "costumes", "name": "Songkok (Malay velvet cap)",
 "tags": ["malaya", "malay", "indonesia", "hat", "cap", "muslim", "civilian", "ww2"],
 "doc": "the black velvet songkok, flat-topped and oval, worn by Malay men",
 "slot": "head",
 "parts": [
  {"path": "M-58 -38 L-55 -92 Q0 -101 55 -92 L58 -38 Q0 -28 -58 -38 Z", "fill": "#26252c", "width": 4},
  {"path": "M-51 -85 Q0 -93 51 -85", "stroke": "#45444f", "width": 5},
  {"path": "M-55 -46 Q0 -37 55 -46", "stroke": "#3a3942", "width": 3}]}
```
The bottom edge sits at y −38 (on the forehead, above the eyebrows); the top at −92 (above the head top −74).

## Several pieces in one costume: the Japanese field cap
```json
{"id": "jp_field_cap", "type": "costumes",
 "pieces": [
  {"slot": "headback", "parts": [ …two cloth flaps from (−60, −46) down to the shoulders (y ~ +60)… ]},
  {"slot": "head", "parts": [ …the cap dome, the band, the visor, the yellow star… ]}]}
```

## Wear it (cards/_film.json "cast")
```json
"villager":  {"preset": "civilian_man", "skin": "#c8986c", "wear": ["songkok", "sarong"]},
"villager2": {"preset": "civilian_man", "wear": ["songkok", {"piece": "sarong", "recolor": {"#3e5d8c": "#8a3a30", "#2b4471": "#6a2a24"}}]},
"jp_soldier": {"preset": "japanese_soldier", "hat": "none", "wear": ["jp_field_cap"]},
"shopkeeper": {"preset": "civilian_man", "outfit": "robe", "color": "#efece2", "skin": "#f1c9a5", "armColor": "#f1c9a5", "wear": ["singlet"]}
```
- Set `"hat": "none"` when the piece replaces the preset's hat; `"hair": "none"` under a turban.
- `armColor` = the sleeve colour; the skin colour gives bare arms (a singlet, a sleeveless vest).
- `recolor` maps the piece's colours (read them in its asset.json) to new ones: one sarong, many patterns.

## Image path (A)
`library/prompts/costumes.md`: the piece alone, front view, sized for the reference heads of `STYLE_REFERENCE.jpg`.
Import it as a `props` drawing first to get the parts, then move them into the head frame (head centre at 0, 0) and set
`"type": "costumes"`, `"slot": "head"`. Garments are usually easier in code (a sarong is one trapezoid and three stripes).

## Check
`python tools/lib.py preview --project … <id>` shows it on three people (a civilian, a soldier, a woman; one turned and
talking, one pointing). Then `make.py … preview` shows the whole cast wearing their pieces. Look for: the hat sits on the
head (not floating, not over the eyes), flaps behind the head, the sarong covers the legs to the ankles.
