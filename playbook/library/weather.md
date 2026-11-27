# Weather — parametric, never a picture

Weather is drawn by the engine over the whole frame (`src/fx/Weather.tsx`); in a composed place it also fades the
distance. Write it on a place (`"sets"`) or on one card (it wins for that card).

```json
"weather": "rain"
"weather": {"kind": "rain", "amount": 0.9, "wind": 0.4}
"weather": {"kind": "lightning", "flash": [2.1, 5.8]}
```
| kind | default amount | what you see |
|---|---|---|
| `drizzle` / `rain` / `downpour` | 0.3 / 0.6 / 1 | falling streaks, a grey veil, splashes on the ground when heavy |
| `lightning` | 0.9 | a downpour with white flashes and a bolt (`flash`: exact seconds, else every few seconds) |
| `snow` / `blizzard` | 0.5 / 1 | flakes drifting; a white-out veil and fast sideways flakes in a blizzard |
| `haze` | 0.6 | humid tropical haze: the distance fades into a warm white |
| `fog` | 0.6 | a grey-white veil, heavier near the ground, slow fog banks |
| `dust` / `sandstorm` | 0.5 / 1 | an ochre veil with drifting dust; streaks across the frame in a sandstorm |
| `ash` | 0.5 | grey flakes falling slowly (burning cities) |
| `leaves` / `petals` | 0.5 | leaves (or blossom) tumbling across the frame |

- `amount`: 0 (barely) … 1 (the strongest); `wind`: −1 … 1 (slant and drift, negative = to the left).
- Indoors (rooms) nothing falls.
- Rain and storms change the sky of a composed place to a storm sky and the ambience to rain.

## A weather preset in the library (type `weather`)
A named setting a film can reuse, e.g. `monsoon_downpour`:
```json
{"id": "monsoon_downpour", "type": "weather", "name": "Monsoon downpour",
 "tags": ["tropical", "monsoon", "rain", "malaya", "burma", "india"],
 "doc": "a heavy tropical downpour with wind", "spec": {"kind": "downpour", "amount": 1, "wind": 0.5}}
```
Use it by id: `"weather": "monsoon_downpour"` (the compiler puts in its `spec`).

## Check
Review the scene at start, middle and end: the weather covers the **whole** frame, never a corner; faces stay readable.
