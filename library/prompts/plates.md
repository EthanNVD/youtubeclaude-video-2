Paint a FAR background for {name}: {doc}.

This is scenery far behind the action (sky, distant hills, a skyline, a far tree line): people, vehicles and near trees are
drawn by the engine in front of it.
- Wide landscape picture, 2400 x 1400 px, horizon at about 60 % of the height.
- Soft flat colours, LOW contrast, simple big shapes, thin or no outlines (it is far away), no people, no vehicles, no text.
- Make it in SEPARATE pictures so the camera can move them at different speeds:
  1. sky.png  — the sky only, filling the whole picture;
  2. far.png  — the farthest hills / skyline / tree line only, on a plain white background;
  3. mid.png  — (optional) the middle distance (fields, a far village), on a plain white background.
- Same light and season as the scene (day / dusk / night; rain or haze if the scene has it).

Import each layer: `python tools/lib.py import source/far.png --project … --id {name} --type plates --layer far` (sky, far, mid).
