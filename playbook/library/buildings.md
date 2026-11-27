# Buildings — houses, shops, huts, temples, bunkers

Examples in the library: `kampong_house` (Malay house on stilts), `shophouse` (Chinese shophouse). The engine's own town
kit (European streets, villages: `python tools/make.py … preview --kit`) covers most European towns.

## The frame
- **Straight front view** of the facade, like a stage set; the ground line flat at y 0; the whole roof visible.
- Sizes in man-units: a door ~250–300, one storey ~260–300, a one-storey house 450–600, a two-storey shophouse ~640.
- `"flip": "none"` in rows (a building with writing must not be mirrored).

## A complete building (path B): the kampong house, in order
1. the stilts: five `rect`s from y −190 to 0;
2. the floor beam: a wide `rect` at y −210;
3. the walls: a `rect` from −400 to −210, plus thin vertical plank lines (`path` with many `M… L…`);
4. windows and shutters: dark `rect`s with a lighter half (an open shutter);
5. the door;
6. the steps: two slanted `path` lines and four short treads;
7. the roof: a big `path` triangle in thatch colour with a darker underside, the gable triangle, a few thatch lines.
The whole record is `library/buildings/kampong_house/asset.json`: copy it with `lib new buildings <id> --from kampong_house`
and change the colours, the number of windows, the roof.

## Use it
- In a composed place, as a row or a single item:
  ```json
  "rows": [{"what": "shophouse", "depth": 800, "from": -120, "to": 2100, "gap": 560, "jitter": 0, "vary": false, "flip": "none"}]
  "items": [{"what": "kampong_house", "at": 1500, "depth": 790}]
  ```
- In any scene card: `"things": [{"what": "kampong_house", "at": "right", "depth": "far"}]`.

## Image path (A)
`library/prompts/buildings.md`: front view, flat ground line, whole building, white background. Import with
`--height 520` (one storey) or `--height 640` (two storeys).

## Check
- `lib preview --grid`: the man reaches about the top of the door.
- In a place preview: the row of buildings joins up (gap ≈ the building's width × its scale at that depth).
