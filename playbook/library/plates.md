# Plates — painted far backgrounds (image path only)

A plate is a picture, not a drawing: the sky, far hills, a skyline, a far tree line. It is only for things **far away**,
behind everything that moves. People, vehicles, near trees and buildings stay vector drawings.

## Make one (needs an image model, e.g. Muse)
1. `python tools/lib.py new plates malaya_hills --project projects/<slug> --tags malaya,hills,far,tropical`
2. Use `library/prompts/plates.md` (also in the asset's `prompt.txt`): a wide 2400 × 1400 picture, soft flat colours, low
   contrast, no people, no text, in separate layers:
   - `sky.png` — the sky only, filling the picture;
   - `far.png` — the farthest hills / skyline / tree line on plain white;
   - `mid.png` — (optional) the middle distance on plain white.
   Attach `library/STYLE_REFERENCE.jpg`. Same light and season as the scenes.
3. Import each layer:
   ```
   python tools/lib.py import projects/<slug>/assets/malaya_hills/source/far.png --project projects/<slug> --id malaya_hills --type plates --layer far
   python tools/lib.py import …/source/sky.png --project projects/<slug> --id malaya_hills --type plates --layer sky
   ```
   The white background is cut out (except for the sky). The record lists `"layers": {"far": "far.png", "sky": "sky.png"}`.

## Use it
In a composed place: `"compose": {"plates": ["malaya_hills"], "far": ["none"], …}` or with options
`{"id": "malaya_hills", "layers": ["far"], "opacity": 0.9, "y": 300, "h": 380, "drift": 4}`. The compiler copies the
pictures into `public/plates/<id>/` (not committed) when the cards compile.

## Check
Place preview: the plate sits on the horizon (no gap under it, no hard edge), it is softer than the near drawings, and the
haze covers its bottom.

## Without an image model
Use the procedural far layers instead (`"far": ["hills", "jungle"]`). They are always available.
