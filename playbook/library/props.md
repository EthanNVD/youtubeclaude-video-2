# Props — things people hold, or that stand on the ground

Examples in the library: `shovel`, `parang`, `notice_board`, `sandbag_wall`. The engine's own props (table, crate, rifle,
letter, lantern…) are listed by `python tools/lib.py search "<words>"` as `builtin`.

## The frame
- `(0, 0)` = where it **stands**: the bottom centre. **y up is negative.** A man is **260 units** tall.
- A thing that is **held** is drawn around the hand instead and gives `"anchors": {"grip": [x, y]}`: the point the fist
  closes on. The engine puts that point in the hand and turns the thing with the pose.
- A thing other things stand on gives `"top"`: the height of its top surface (a table 120, a crate 100).

## A complete held prop (path B, code): the parang
```json
{
 "id": "parang", "type": "props", "name": "Parang (machete)",
 "tags": ["malaya", "southeast_asia", "machete", "parang", "jungle", "blade", "tool", "ww2"],
 "doc": "a parang: the heavy Malay machete used to cut through undergrowth (held in the hand)",
 "size": 1.0, "h": 122,
 "anchors": {"grip": [0, 4]},
 "parts": [
  {"path": "M-6 0 L8 0 L8 -10 L-6 -10 Z", "fill": "#3a2a1e", "width": 2.5},
  {"path": "M-8 10 L10 10 L9 -2 L-7 -2 Z", "fill": "#5a3e28", "width": 3},
  {"path": "M-6 -10 L-10 -96 Q2 -112 16 -96 L8 -10 Z", "fill": "#b9bec2", "width": 3.5},
  {"path": "M-8 -30 L-10 -92", "stroke": "#e8ecee", "width": 2.5}
 ],
 "source": {"kind": "code"}
}
```
Read it like this: the handle is around `(0, 0)` (where the fist is), the blade goes **up** to y −112. Order: big shapes
first, the shine line last.

## A complete standing prop: the sandbag wall (made with a few lines of Python)
Three courses of rounded sacks, the lowest touching y 0, `"top": 108` so a rifle can rest on it. When a shape repeats,
write a tiny script that prints the parts (see `projects/malaya-test` history: one loop over rows and sacks).

## Use it
```json
"people": [{"who": "jp_soldier", "holds": "parang", "do": [{"act": "hold_up", "with": "parang", "on": "hack"}]}]
"things": [{"what": "sandbag_wall", "at": 780, "depth": "front"}]
"things": [{"what": "notice_board", "at": "right", "depth": "back"}, {"what": "letter", "on": "notice_board"}]
```

## Check
- `lib preview --project … <id> --grid`: a held prop must sit on the floor next to the man in the preview (the tool
  stands it on its lowest point); a standing prop must touch the floor line.
- `lib check`: "its lowest point is at y …" = move the parts down, or add a `grip` if it is held.
- In the film's review: the held thing is **in** the fist, not floating beside it, and does not cover the face.

## Common mistakes
- Drawing a held thing standing on y 0 without a `grip`: it floats at the feet.
- Drawing it 10× too big or small: compare with the man on the grid (a rifle ~150, a cup ~20, a table ~120 high).
- Text on props: keep it short, in the narration's language, and only if it must be read.
