# Scene writing — compose every picture from the narration

This is the page you use most while writing cards. It teaches the **`scene` card**:
- you describe the picture the way a director would;
- the compiler stages it, acts it and films it.

Recipes (`recipes/CATALOG.md`) remain the fast way to show a battle, a map move or a chart. For everything else, the scene card is the default, because it is not limited to a fixed composition:
- people at home, in offices, shops, streets, ports, ministries and schools;
- decisions, consequences, money, hunger, politics.

Every new script gets **new places, new people and new pictures**, built from what the sentence says.

Two complete examples compile and render in this repo; read them before your first film:
- `projects/creative-blockade/` (WW1 blockade → Turnip Winter, 20 cards, 94 s): docks, an admiralty, a pub, a customs quay, a Rotterdam street, a Berlin kitchen.
- `projects/creative-austria/` (how Austria taught Hitler, 13 cards, 65 s): classrooms, a ministry, a press conference, parliament, custom props (a broom, school desks, a lectern, a declaration).

---

## 1. The method: from a clause to a card (do it for every clause)

**Step 1 — Read the clause and say what it MEANS** (`says`):
- one sentence in your own words;
- it proves you understood the clause before you draw anything.

**Step 2 — Write the director's IDEA** (`idea`):
- one sentence, 10+ words: **who we see, doing what, where, and why that picture tells this clause**;
- write it before any field, because the card is built from it;
- a good idea is concrete enough that two artists would draw almost the same picture.

| the clause | a weak idea (do not write) | a strong idea (write this) |
|---|---|---|
| "Germany fed its people and its factories with imports." | "Show imports." | "Dawn on the Hamburg quay: dockers carry sacks ashore from a freighter while a foreman waves them on toward the town — the country is fed through this gate." |
| "Then came a bad harvest." | "A bad harvest." | "In a grey field in the rain a farmer kneels by a heap of rotten black potatoes, hands to his head; his wife stands behind him with an empty basket." |
| "Austria's official memory rested on paragraph one." | "Austria's memory." | "In a Vienna ministry an official reads the first paragraph of the declaration aloud to two colleagues, who nod with relief." |

To find the idea, answer the five questions of [narration-to-picture.md](narration-to-picture.md) §1:
- **WHO**: a person, a group, nobody.
- **DOES WHAT**: a visible action, on a key word.
- **WHERE**: a real place.
- **WHEN**: time of day and weather.
- **WHY this picture**: what the viewer understands from it.

When you are stuck, take a device from [visual-ideas.md](visual-ideas.md):
- the clause names a list → things appear as they are named;
- the clause names a loss → absence;
- the clause names a decision → the man at the desk, then the field.

**Step 3 — Stage it** (the card fields):
- `where`: the place;
- `people`: who stands where, faces whom, in what mood, doing which act on which words;
- `things`: what is on the table, the counter, the floor;
- `crowd`, `vehicles`, `effects`: when the idea needs them;
- `camera`: how we look at it.

**Step 4 — Compile, look, fix only what is wrong** (§9).

---

## 2. The card, field by field

```json
{"at": "Then came a bad harvest.", "recipe": "scene",
 "says": "A failed potato harvest in 1916 made the hunger much worse.",
 "idea": "In a grey field in the rain a farmer kneels by a heap of rotten potatoes, hands to his head; his wife stands behind with an empty basket.",
 "where": "rotten_field", "place_id": "rotten_field", "time": "dusk", "weather": "rain",
 "people": [
   {"who": "farmer", "at": "center_left", "depth": "near", "kneel": true, "mood": "sad",
    "do": [{"act": "look_down"}, {"act": "despair", "on": "rotted"}]},
   {"who": "farmer_wife", "at": "center_right", "depth": "back", "mood": "grief", "holds": "basket",
    "do": [{"act": "shake_head", "on": "winter"}]}],
 "things": [{"what": "potatoes", "at": "center", "depth": "front", "color": "#4a3e2e", "n": 8}],
 "camera": "wide_then_close", "focus": "farmer", "close_on": "rotted"}
```

| field | what to write | notes |
|---|---|---|
| `at` | the first words of this card's narration, copied exactly from `work/reading.md` | the card lasts until the next card's `at` |
| `recipe` | `"scene"` | |
| `says` | the meaning, in your words (6+ words) | never copy the narration |
| `idea` | the director's note (10+ words) | checked against the other cards for repetition |
| `where` | a story place from `_film.json` `"sets"`, a library place (`kampong`, `rubber_estate`…), a room style, a town style, an engine set, or an object | §3 |
| `place_id` | the story place's name | same `place_id` = same place: the tag and the look carry over |
| `time`, `weather` | `day dawn dusk night`; `rain drizzle downpour snow blizzard haze fog dust sandstorm ash leaves petals lightning`, or `{"kind": "rain", "amount": 0.9, "wind": 0.4}`, or a library preset (`monsoon_downpour`) | indoors, nothing falls ([library/weather.md](library/weather.md)) |
| `people` | a list of persons | §4 |
| `crowd` | one group (or a list of groups) | §4.5 |
| `things` | props on the floor, on other things, in hands; drawings you defined | §5 |
| `vehicles` | ships, trucks, carts, trains, planes | §5.3 |
| `effects` | smoke, fire, explosion, flash, steam, `!` over a head… | §5.4 |
| `camera`, `focus`, `partner`, `close_on`, `wide_on`, `detail` | how we look | §6 |
| `revisit` | `true` = a deliberate callback to an earlier composition | silences the repetition check |
| `wish` | things you wanted but the engine lacks, e.g. `["a horse-drawn hearse"]` | logged in `work/missing_assets.json` |
| any common field | `tag`, `tag_on`, `name_card`, `caption`, `stat`, `paper_note`, `sfx`, `ambience`, `tint`, `letterbox`, `transition` | as in [03-cards.md](03-cards.md) |

The full vocabulary, with pictures, is in [recipes/STAGECRAFT.md](../recipes/STAGECRAFT.md):
- every slot and depth;
- every act, mood, crowd kind, thing, effect, camera, room style, room module, town style, building and street item.

---

## 3. WHERE — places

### 3.1 Define each story place ONCE, in `cards/_film.json` `"sets"`

Every place the film visits more than once is a story place. Write its full description once, give it a name, and use the name in the cards (`"where": "mueller_kitchen"`). The compiler then:
- remembers it, so the same kitchen looks the same every time;
- carries its `tag`;
- lets you change only `time`/`weather` to show time passing.

```json
"sets": {
  "mueller_kitchen": {"room": "kitchen", "items": ["shelf:empty", "window:snow_street", "clock", "hooks"],
                      "light": "candle", "poor": true, "lightX": 760, "tag": "Berlin · Winter 1916–17"},
  "rotterdam_street": {"town": "dutch", "buildings": ["house", {"item": "shop:grocer", "text": "IMPORT · EXPORT", "goods": "tins"}, "house", "tenement"],
                       "items": ["crates", "lamppost", "barrels"], "tag": "Rotterdam · 1915"},
  "parliament": {"set": "parliament", "tag": "Parliament, Vienna · July 1991"}
}
```

### 3.2 Three kinds of place

**A room (the kit):** `{"room": "<style>", ...}`.

Styles:
- `kitchen`, `tenement`, `parlour`, `farmhouse`;
- `shop`, `bakery`, `tavern`, `warehouse`;
- `office`, `ministry`, `admiralty`, `food_office`;
- `ward`, `barracks`, `dugout`, `cellar`, `classroom`, `church`.

The style alone gives a finished room. Change it with:
- `items`: the back-wall modules, left to right. Modules: `window` (`window:snow_street`, `window:small`, `window:tall:sea`), `door` (`door:open`), `shelf:<jars|tins|bottles|books|bread|plates|empty|sacks>`, `cupboard`, `cabinet`, `drawers`, `stove` (`stove:cold`), `fireplace`, `oven`, `bed`, `beds`, `bunk`, `clock` (`clock:4:15`), `portrait` (`portrait:UK` shows a flag), `map` (`map:sea`), `poster` (`{"item": "poster", "text": "BROTKARTE"}`), `flag:<NATION>`, `calendar`, `photos`, `crucifix`, `mirror`, `hooks`, `lamp`, `barrels`, `crates:<TEXT>`, `sacks`, `rifles`, `blackboard` (`{"item": "blackboard", "text": "1943"}`), `sink`, `cradle`, `arch`, `stained`, `sign` (`{"item": "sign", "text": "KOLONIALWAREN"}`), `radio`, `pipes`.
- `wall`: `plaster paper panel plank timber brick stone tile concrete`, with `wallColor`.
- `floor`: `boards tile stone carpet earth duckboard parquet`, with `floorColor`.
- `light`: `window lamp candle lantern fire dim`.
- `poor: true`: cracked plaster, patches.
- `beams: true`, `view` (what every window shows), `cold: true` (frost on the glass).

**A street (the kit):** `{"town": "<style>", ...}`.

Styles:
- `german`, `austrian`, `french`, `english`, `russian`, `dutch`;
- `industrial`, `village`.

The style sets the walls, roofs and the **language of the shop signs**. Change it with:
- `buildings`, left to right: `house`, `tenement`, `shop:<bakery|butcher|grocer|cafe|post|bank|office>` (`{"item": "shop:bakery", "goods": "empty"}`; goods `bread meat veg turnips tins empty`), `church`, `townhall`, `factory`, `office`, `post`, `ruin`, `station`;
- `items`: `lamppost`, `poster` (with `text`), `cart`, `bench`, `pump`, `barrels`, `crates`, `sandbags`, `tree`, `pole`, `snowbank`, `banner:<NATION>`, `rope`; give `"x"` to place one exactly;
- `ground`: `cobbles mud snow dirt`;
- `back`: `spire chimneys hills city none`.

**An engine set:** `{"set": "<name>"}`, for example:
- military: `trench`, `nomansland`, `airfield`, `hangar`, `tent`, `radio`, `bunker`, `warroom`;
- outdoors: `field`, `mud`, `snow`, `desert`, `jungle`, `harbor`, `sea`, `beach`, `railway`, `station`;
- buildings: `bridge` (a ship's bridge), `parliament`, `corridor`, `hotel`, `factory`, `office`, `cell`, `train_interior`, `cockpit`.

The full list is in `recipes/STAGECRAFT.md`.

**A composed landscape** (any region, any season): `{"compose": {"far": [...], "ground": "...", "road": {...}, "rows": [...]}, "horizon": 600}`.
Layers far to near: sky by time, painted plates, far shapes (`hills mountains jungle treeline palms sea town`), the ground
(`grass laterite sand paddy mud dry jungle_floor snow`), a road, and rows of library plants and buildings in depth
(rows below the people stand in front of them). The fields, with a worked example, are in [library/places.md](library/places.md).
```json
"estate_road": {"compose": {"far": ["treeline"], "ground": "grass", "road": {"kind": "laterite", "y": 885, "w": 210},
                            "rows": [{"what": "rubber_tree", "depth": 650, "gap": 120}, {"what": "rubber_tree", "depth": 800, "gap": 190},
                                     {"what": "lalang_grass", "depth": 1075, "gap": 120}]},
                "horizon": 600, "weather": "haze", "tag": "Behind the Japanese lines · January 1942"}
```
**A library place**: `"where": "kampong"` — places kept from earlier films (`python tools/lib.py search "village"`).

### 3.3 Flags and signs must be right

- A flag says whose it is: `flag:AUS`, `portrait:UK`, `banner:FRA`. A room style that hangs a flag (e.g. `ministry`) needs `flag:<NATION>` in its items or `"nation"` on the place, otherwise the compiler warns. A wrong flag is a factual error the viewer sees at once.
- Shop signs follow the town style's language. Write your own with `"text"` when the place needs it, e.g. `CUSTOMS` or `IMPORT · EXPORT`.

### 3.4 Same place, time passing

Re-use a `place_id` and change only `time`/`weather`, or the room's `items` (a full warehouse in 1913, half empty in 1915 with `"revisit": true`). The viewer recognises the place, and the change tells the story.

---

## 4. WHO — people

### 4.1 Make the cast first (`cards/_film.json` `"cast"`)

Every person who appears gets a cast entry: a preset from `recipes/PEOPLE.md`, plus whatever makes them this person.

```json
"cast": {
  "mother":    {"preset": "civilian_woman", "color": "#5a4a6a", "age": 0.3},
  "girl":      {"preset": "civilian_woman", "age": 0, "build": 0.85, "hair": "bun", "color": "#8a4a4a", "size": 0.74},
  "clerk":     {"preset": "civilian_man", "glasses": "round", "age": 0.6},
  "captain":   {"preset": "dutch_civilian", "hat": "navy", "facial": "beard", "color": "#2f3a4a"},
  "vranitzky": {"preset": "civilian_man", "outfit": "suit", "color": "#2f3440", "age": 0.45, "name": "Franz Vranitzky", "role": "Chancellor of Austria"}
}
```

Fields you can change:
- `outfit`: `tunic suit navy navywhite coat sailor civil dress party armor robe pilot tweed trench`;
- `color` (the jacket), `pants`, `skin`;
- `hair`: `side back bald baldtop short part curly bun long messy tousled none`, with `hairColor`;
- `facial`: `toothbrush walrus pencil handlebar beard goatee stubble none`;
- `hat`: `peaked garrison helmet_de helmet_uk … navy beret kepi ushanka fedora tophat flatcap crown none`, with `hatColor`;
- `glasses`: `round pince sun`;
- `extra`: `cigar pipe medals armband epaulettes tie bowtie scarf monocle wrinkles vest`;
- `build` (0.85 thin … 1.3 stout), `age` (0 young … 1 old: wrinkles, grey hair), `female`.

Two more fields:
- **Children:** `"size": 0.7–0.8`, with `age: 0` and `build: 0.85`.
- **Name cards:** `name` and `role`. Show them with `"name_card": true` on the person the first time they appear.

Run `python tools/make.py projects/<slug> preview` and look at the cast sheets before you write cards (§8).

### 4.2 A person in a card

```json
{"who": "mother", "id": "mum", "at": "center_right", "depth": "mid", "face": "girl", "mood": "worried",
 "holds": "spoon", "pose": "stir", "seated": false, "kneel": false, "walk": "shuffle", "size": 0.74, "name_card": true,
 "do": [{"act": "stir"}, {"act": "look_up", "on": "turnips"}, {"act": "walk_to", "to": "girl", "on": "winter"}]}
```

| field | values | default |
|---|---|---|
| `who` | a cast id or a preset | required |
| `id` | a short name to refer to this person (`to`, `focus`) | the cast id |
| `at` | `far_left left center_left center center_right right far_right` or px; `off_left`/`off_right` = outside the frame | spread evenly |
| `depth` | `front near mid back far`, or a screen y | `mid` |
| `face` | `left right viewer away`, or a person's or thing's id | toward the others |
| `mood` | `neutral worried sad grief angry determined proud happy tired hungry cold shocked fear smug nervous` | `neutral` |
| `pose` | the starting pose (`recipes/STAGECRAFT.md`) | from the mood or what they hold |
| `holds` | a thing in the hand (a prop, a library drawing with a grip, or one of your drawings) | — |
| `rides` | a vehicle drawing the person sits on (`bicycle`): he pedals; `walk_to`, `enter`, `exit` ride it at riding speed | — |
| `seated` / `kneel` | `true` (a chair indoors, a crate outdoors is added) | — |
| `walk` | `shuffle` (hungry, exhausted), `march`, `limp`, `sneak` | normal |
| `size` | 0.7–0.8 for children | the cast's `size` or 1 |
| `do` | the acts (§4.3) | — |

The **mood** does more than the face. It chooses the gestures the person makes by themselves:
- while talking: a worried mother wrings her hands, an angry officer points and makes fists;
- while listening: crossed arms, a hand on the chin, a nod;
- while waiting.

Pick it from the narration's feeling, not from habit.

### 4.3 Acts — what they DO, on which words

Each act is `{"act": "<name>", "on": "<2-5 words of this card's narration>"}`.

Optional fields:
- `till` (a phrase): when the act ends;
- `to`: a person, a slot, or `left`/`right`;
- `with`: what is in the hand;
- `expr`: the face.

An act without `on`:
- the first one starts the scene;
- the others are spread evenly.

| you want them to… | acts |
|---|---|
| work at something (it keeps moving) | `stir ladle eat drink peel knock hammer write type read count phone smoke warm_hands rub_hands wait` |
| carry or hold | `hold hold_up show carry carry_sack carry_basket cradle binoculars give take reach_up` |
| gesture while explaining | `point point_down beckon explain present palms shrug think ponder count` |
| feel something | `despair facepalm gasp hand_on_heart pray cry wring_hands shiver cower beg fist slam clap cheer wave` |
| stand a certain way | `arms_crossed hands_behind hands_on_hips pockets lean listen salute tip_hat stop surrender` |
| talk (mouth moves, gestures follow the mood) | `say` (with `on` and `till`) |
| change the face or head | `react` (with `expr`), `laugh`, `shout`, `sigh`, `freeze`, `nod`, `shake_head`, `look_up`, `look_down`, `look_at` (`to`), `look_away`, `look_around` |
| turn | `turn_away` (back to us), `turn_back`, `turn_to` (`to`) |
| change height | `sit`, `stand_up`, `kneel`, `rise`, `fall` |
| move | `walk_to`, `run_to`, `shuffle_to`, `march_to`, `limp_to` (`to`: a slot, a person or px; optional `depth`, `pose`); `enter` (`from`: left/right, starts on the phrase); `exit` (`to`: left/right) |
| soldiers | `aim`, `fire`, `port_arms`, `shoulder_arms` |

What the compiler does for you:
- **Turns** people toward whom they act on (`to`), toward a speaker who starts talking, and toward each other by default.
- **Walks** a giver up to the receiver when they stand too far apart for a hand-over.
- **Puts down** a crate or a sack before a gesture that needs a free hand.
- **Adds gestures** between your acts: on stressed words while talking, small shifts while listening, glances while waiting. Nobody is frozen. `"life": false` turns this off for a tableau.
- **Adds sounds** on contact: footsteps (in snow: snow steps), knocks, a slam, pen and paper, a typewriter, a rifle shot.

### 4.4 Put the act on the word

The picture must change **on the word that names it**:
- the head shakes on "more than half";
- the hands go to the head on "rotted";
- the thing appears on its name.

Copy 2–5 words of the narration exactly. If the compiler says a phrase is not in the card, it prints the card's narration: copy from there.

### 4.5 Crowds

```json
"crowd": {"kind": "queue", "n": 7, "who": ["civilian_woman", "worker", "civilian_man"], "at": "right", "depth": "back",
          "toward": "right", "mood": "cold", "react_on": "sold out", "expr": "sad"}
```

Kinds:
- `queue`: a line waiting at a door, facing it, shuffling forward now and then;
- `watchers`, `listeners` (with `"view": "back"` they become heads along the bottom of the frame, never in front of the speaker);
- `walkers`: passers-by at different depths and speeds;
- `marchers`: a column with rifles (`"start": "in"` = the column is already in the frame, its head at `at`);
- `cyclists`: rows of riders on bicycles, `"abreast": 3` side by side, chatting and laughing (`"toward"`, `"vehicle"`, `"start": "in"`);
- `mourners`, `cheering`, `workers`, `protest`.

`react_on` changes their faces together, slightly staggered.

---

## 5. WITH — things, your own drawings, vehicles, effects

### 5.1 Things

```json
"things": [
  {"what": "stove", "at": 1360, "depth": "mid"},
  {"what": "pot", "on": "stove", "dx": -40},
  {"what": "table", "at": 560, "depth": "front"},
  {"what": "plate", "on": "table", "dx": -110},
  {"what": "turnip", "on": "table", "dx": -110, "scale": 0.8, "appear": "Turnip Winter"},
  {"what": "bale", "text": "COTTON", "at": 330, "depth": "mid", "appear": "cotton"},
  {"what": "zeppelin", "at": "left", "y": 260, "scale": 0.7, "to": "right", "when": "night", "till": "Zeppelin"}
]
```

- `on`: stands on another thing (put the base first in the list); `dx` shifts it along the top.
- `appear`: it pops in on that word. This is the best way to show a list the narration names.
- `text`, `n` (how many / the value), `color`, `steam`/`lit`, `flip` change the look.
- `y` places it freely in the sky or on a wall, with an absolute `scale`. `lift` raises a drawing whose origin is not its foot, e.g. a broom drawn around the hand stands with `"lift": 264`.
- `to` makes it move (`when` and `till` are phrases): a cart crossing, an airship drifting, a boat leaving.
- `held_by`: a person holds it from the start.

Engine things:
- furniture: `table counter stove chair stool bench`;
- containers: `crate barrel sack bale ingots bucket basket cart`;
- food and tableware: `pot bowl plate cup bottle jug bread turnip turnips potatoes`;
- paper: `card letter paper telegram ledger book photo`;
- small things: `coins candle lantern scale knife spoon cards radio typewriter phone helmet suitcase clock globe medal baby`.

Plus every other engine prop (`recipes/STAGECRAFT.md`).

### 5.2 Your own drawings — new equipment, props, set pieces, simple vehicles

The engine cannot have everything (a field kitchen, a 1943 declaration, a school desk, a lectern, a zeppelin). **Draw it yourself in `_film.json` `"drawings"`.** It is drawn in the same style as everything else: flat colours, dark outlines. You can use it as a thing, hold it, or move it.

```json
"drawings": {
  "lectern": {
    "doc": "a speaker's lectern; put papers on it",
    "size": 1.0, "h": 150, "top": 140,
    "parts": [
      {"poly": [[-72, 0], [72, 0], [58, -126], [-58, -126]], "fill": "#6a4428"},
      {"poly": [[-86, -126], [86, -126], [78, -150], [-78, -142]], "fill": "#8a5a32"}
    ]}
}
```

Coordinates:
- `(0, 0)` is where it stands, its bottom centre;
- `y` goes **up** with negative numbers;
- a man is about **260 units** tall: a table is ~120 high, a door ~230.

Things you mostly hold (a broom, a newspaper, a document) are drawn **around the hand**, `(0, 0)` = the grip. A drawing that stands on the ground but is also carried says where the hand goes: `"grip": [x, y]`, e.g. the top of a handle. The engine puts that point in the palm, so the thing never floats beside the hand.

Parts:
- shapes: `rect [x, y, w, h]` (+ `r` for round corners), `circle [cx, cy, r]`, `ellipse [cx, cy, rx, ry]`, `poly [[x, y], …]`;
- `line [[x, y], …]` (+ `width`, `stroke`);
- `path` (an SVG path);
- `text` (+ `at`, `size`, `font`: `cond title hand mono`).

Style:
- every part: `fill`, `stroke` (`false` = none), `width` (outline, default 4), `opacity`;
- the outline is the dark ink of the style: keep it.

Motion:
- `spin` (deg/s around `center`: wheels, propellers);
- `flicker` (flames);
- `sway` (smoke, flags; around `pivot`);
- `blink` (lamps);
- `drift`.

Drawing-level fields:
- `size`: scale next to a person;
- `h`: height, for camera framing;
- `top`: height of its top surface, for things placed `on` it;
- `doc`: one line for the catalogue.

**The living library** (`library/`) holds the drawings any film can use: props (`shovel`, `parang`, `sandbag_wall`, `notice_board`),
vehicles (`bicycle`, `field_kitchen`, `zeppelin`), buildings (`kampong_house`, `shophouse`), plants (`rubber_tree`,
`coconut_palm`, `banana_plant`, `lalang_grass`, `jungle_edge`), and growing. Search it first: `python tools/lib.py search "words"`.
A drawing that would help other films is made as an asset of the film (`python tools/lib.py new …`) instead of in
`"drawings"`, then promoted at the end ([library.md](library.md)).

Check every drawing on the preview sheet, next to the man drawn for scale (§8).

### 5.3 Vehicles

```json
"vehicles": [{"type": "cruiser", "nation": "UK", "at": "far_left", "depth": 690, "to": "center_left", "scale": 0.4}]
```

Types:
- ships: `battleship cruiser destroyer cargo freighter transport uboat submarine boat`;
- land: `truck car jeep cart wagon horse train locomotive traincar` and the tanks;
- air: `plane fighter bomber`…

At sea, use `depth` as a screen y: 600–700 is the horizon of the `sea` and `beach` sets.

Fields:
- `to`, with `on`/`till`: the vehicle moves;
- `scale` for ships and planes; land vehicles are sized by depth when you leave `scale` out;
- `flip`: it faces the other way.

### 5.4 Effects

`{"fx": "<kind>", "at": "<slot>", "depth": "…", "on": "<phrase>", "size": 1.0}`.

Kinds:
- `smoke fire explosion shellburst impact dust splash sparks flash searchlight steam`;
- `exclaim` / `question` with `"over": "<person>"`: a `!` or `?` over a head.

Flashbulbs at a press conference: `flash` at the front, on the scandal's words.

---

## 6. CAMERA — how we look at it

| `camera` | what the viewer gets | use it for |
|---|---|---|
| `wide` | the whole place, a slow push | arriving somewhere, a group, a montage card |
| `push_in` | a long slow push through the whole scene | tension, a realisation, a quiet room |
| `pan` | a drift sideways | a street, a queue, a row of beds, a fleet |
| `wide_then_close` (+ `close_on`) | wide, then a dissolve to the focus person on the key words | **the default for a moment that lands on one face** |
| `close_then_wide` (+ `wide_on`) | starts on the focus, then reveals the place | a reveal: the clerk, then the empty warehouse |
| `detail_then_wide` (+ `detail`, `wide_on`) | starts on a thing, then the people around it | the turnip on the plate, then the family |
| `medium` | waist-up on the focus all through | a confession, a reaction, a speech |
| `close` | the face | grief, shock (short) |
| `two_shot` (+ `partner`) | two people together | a hand-over, a pair reacting |
| `group` | everybody, tight | a council, a family |
| `follow` | follows a walking focus | arrivals, departures, a messenger |
| `over_shoulder` (+ `partner`) | over the partner's back onto the focus | dialogue, an argument, an interrogation |
| a list of shots | `[{"on": "phrase", "frame": "wide" or an id or [ids], "size": "full", "zoom": 1.2}]` | when you need exact control |

You can also leave `camera` out (`auto`). The compiler then:
- picks a camera from the content;
- never repeats the camera of the card before;
- varies with the film's `look.seed`.

Things it does for every camera:
- a set-up held for more than ~6.5 s gets a second one by itself;
- close shots follow a person who walks;
- close shots open up when arms go up.

Vary the cameras along a sequence:
- three cards in a row with the same camera trigger a warning;
- as in [narration-to-picture.md](narration-to-picture.md) §5, go wide → closer as a moment builds;
- go back to wide on a new place.

---

## 7. Templates — copy one and fill it in

**A. Somebody busy is interrupted by the news** (the clause: "…was told", "the news reached…")
```json
{"at": "…", "recipe": "scene", "says": "…", "idea": "<who> is <busy with X> in <place> when <messenger> brings the news; on '<word>' <who> looks up, <reaction>.",
 "where": "<story place>", "place_id": "<story place>",
 "people": [{"who": "<A>", "at": "center_right", "do": [{"act": "write"}, {"act": "look_up", "expr": "shocked", "on": "<word>"}]},
            {"who": "<B>", "at": "center_left", "holds": "telegram", "do": [{"act": "enter", "from": "left"}, {"act": "give", "to": "<A>", "on": "<word>"}]}],
 "camera": "wide_then_close", "focus": "<A>", "close_on": "<word>"}
```

**B. A list the narration names**: the things appear as they are named.
```json
{"…": "…", "things": [{"what": "bale", "text": "COTTON", "at": 330, "appear": "cotton"}, {"what": "ingots", "at": 860, "appear": "copper"}, …],
 "people": [{"who": "<clerk>", "at": "right", "do": [{"act": "write", "with": "ledger"}]}],
 "camera": [{"frame": "wide", "zoom": 1.25, "push": 0}, {"on": "<last item>", "frame": "wide", "zoom": 1.05}]}
```

**C. Scarcity**: the same place, emptier.
```json
{"…": "…", "where": {"room": "warehouse", "items": ["door:open", "barrels"], "light": "dim"}, "place_id": "<the full place>", "revisit": true,
 "people": [{"who": "<clerk>", "mood": "worried", "do": [{"act": "read", "with": "ledger"}, {"act": "shake_head", "on": "<number words>"}]}],
 "camera": "close_then_wide", "focus": "<clerk>", "wide_on": "<number words>"}
```

**D. A queue for something that has run out**
```json
{"…": "…", "where": {"town": "german", "buildings": ["tenement", {"item": "shop:bakery", "goods": "empty"}, "house"], "ground": "snow"},
 "time": "dawn", "weather": "snow",
 "crowd": {"kind": "queue", "n": 8, "who": ["civilian_woman", "worker"], "at": "center_left", "toward": "right", "mood": "cold", "react_on": "<word>", "expr": "sad"},
 "people": [{"who": "<baker>", "at": "right", "do": [{"act": "shake_head", "on": "<word>"}, {"act": "palms"}]}],
 "camera": "pan"}
```

**E. A speech, with the hall listening**
```json
{"…": "…", "where": "parliament",
 "people": [{"who": "<speaker>", "at": "center", "depth": "back", "name_card": true, "do": [{"act": "say"}, {"act": "hand_on_heart", "on": "<word>"}]}],
 "crowd": {"kind": "listeners", "n": 5, "who": ["civilian_man", "civilian_woman"], "view": "back"},
 "things": [{"what": "lectern", "at": "center", "depth": "mid"}],
 "camera": "wide_then_close", "focus": "<speaker>", "close_on": "<word>"}
```

**F. A dialogue that carries the argument** (two people, one gives the reason)
```json
{"…": "…", "people": [{"who": "<A>", "at": "center_right", "mood": "smug", "do": [{"act": "say", "on": "<first word>"}, {"act": "palms", "on": "<word>"}, {"act": "point", "to": "far_right", "on": "<word>"}]},
                     {"who": "<B>", "at": "center_left", "pose": "cross"}],
 "camera": "over_shoulder", "focus": "<A>", "partner": "<B>"}
```

**G. A loss, by what is left**: an empty place, one object, light.
```json
{"…": "…", "where": "<the family's room>", "time": "dusk", "revisit": true,
 "people": [{"who": "<mother>", "at": "right", "seated": true, "mood": "grief", "do": [{"act": "cry", "on": "<word>"}]}],
 "things": [{"what": "chair", "at": "center_left", "depth": "mid"}, {"what": "helmet", "on": "chair"}],
 "camera": "detail_then_wide", "detail": "helmet", "wide_on": "<word>"}
```

**H. Two sides of one moment**: the same beat in each camp, two cards in a row.

The first card is in Berlin, the second in London, with the same act and a different mood. Mirror the composition: the German stands left facing right, the Briton right facing left.

**I. A callback**: the place or object from earlier returns, changed.
- `"revisit": true`, the same `place_id`, a changed `items` or `time`;
- the person shows the changed object (`declaration_half` → `declaration_full`).

---

## 8. Pre-production: build and check the cast, places and drawings first

Before the cards:
0. List what the pictures need (`understanding.md` §8b) and run `python tools/lib.py match --project projects/<slug>`:
   use, adapt or create every row ([library.md](library.md)).
1. Write `cards/_film.json`:
   - `cast`: every person, children with `size`; costume pieces with `"wear"` ([library/costumes.md](library/costumes.md));
   - `sets`: every story place, with `tag`: a room, a town, or a composed landscape ([library/places.md](library/places.md));
   - `drawings`: one-off things only this film needs (anything reusable is a library asset instead);
   - `look`: `{"seed": <any number>, "grade": "film|warm|cold|bleak|sepia|vivid"}`. The seed gives this film its own gestures and camera choices; the grade gives it its own colour. Pick the grade from the story: cold for a hunger winter, warm for a Vienna classroom.
2. Run `python tools/make.py projects/<slug> preview`. It renders `review/preview/sheet_*.jpg`:
   - every cast member standing and acting;
   - every story place with a man for scale;
   - every drawing and every new asset of the film (`projects/<slug>/assets/`) next to a man.
   - Add `--kit`, `--acts` or `--library` to see the whole room/town catalogue, every act, or the library's drawings.
3. Look at every sheet:
   - Are the faces, ages and outfits right? Are the children small?
   - Does each place say the right thing (flags, signs, the season)?
   - Is each drawing the right size next to the man?

   Fix `_film.json`, run `preview` again.

---

## 9. Check, then fix ONLY the scenes that are wrong

1. `python tools/make.py projects/<slug> cards`. Fix every error, and every warning you can. The warnings are written as instructions:
   - repeated looks or ideas;
   - three identical cameras;
   - a person at the frame edge;
   - a flag without a nation;
   - an unknown act or thing: the closest one was used and it was logged.
2. `python tools/make.py projects/<slug> review --at all`. Open every `review/sheet_*.jpg`: start, middle and end of every scene. Check each picture against [05-review.md](05-review.md); the problems seen most often are listed there:
   - someone hidden behind someone else;
   - a held thing over a face;
   - a flipped sign;
   - a seat that does not belong;
   - a crowd covering the speaker.
3. **Fix only the cards that are wrong.** Change those cards, run `cards`, then re-check only them: `review --scenes s009,s010 --at all`.

   Other cards do not change. Every card's randomness is tied to its own words, so inserting or editing a card does not reshuffle the others.
4. After the full render: when you fix a few scenes, run `python tools/make.py projects/<slug> patch`. It re-renders only the scenes that changed, splices them into the video and rebuilds the sound. `--dry` lists them first.

---

## 10. Mistakes that make a film feel cheap (the compiler catches some; you catch the rest)

| mistake | instead |
|---|---|
| the same composition again and again (two men in an office, wide) | another person, another act, a detail, the consequence, the same place at another time |
| a card that only illustrates a keyword ("blockade" → ships) when the clause says a person did something | stage the person doing it |
| everybody facing the camera, standing in a row | `face` each other, vary `depth`, give one of them business |
| a gesture that is not on the word | put `on` on the word that names it |
| text standing in for an event | act it; text only for an exact quote (`paper_note`), one number (`stat`) or the big question (`caption`) |
| a thing too big or floating | check it on the preview sheet; put small things `on` a table |
| a flag or a sign in the wrong language | `flag:<NATION>`, shop `text` |
| a crowd in front of the speaker | `"view": "back"` puts them along the bottom edge |
| a missing object faked with a label | draw it (§5.2) or put it in `wish` and pick the closest thing |

---

## 11. Example cards from other kinds of stories (all vocabulary is real)

**A decision in a cold room** (WW2, a general alone with a telegram):
```json
{"at": "That night Paulus", "recipe": "scene", "says": "Paulus was alone with an impossible order.",
 "idea": "In a bunker lit by one lantern, Paulus reads the order again, puts it down on the table and stares at the map — he cannot obey and cannot refuse.",
 "where": {"room": "dugout", "items": ["map", "bunk", "shelf:tins"], "light": "lantern", "cold": true}, "time": "night",
 "people": [{"who": "paulus", "at": "center", "depth": "mid", "mood": "tired", "do": [{"act": "read", "with": "telegram"}, {"act": "point_down", "on": "obey"}, {"act": "despair", "on": "refuse"}]}],
 "things": [{"what": "table", "at": "center", "depth": "near"}, {"what": "lantern", "on": "table", "dx": 120}],
 "camera": "push_in"}
```

**A homecoming** (a soldier back in his village):
```json
{"at": "When he finally came home", "recipe": "scene", "says": "The soldier returned to a village that had changed.",
 "idea": "A thin soldier limps down a snowy village street toward his house while an old neighbour stops sweeping and stares.",
 "where": {"town": "village", "buildings": ["house", "house", "church", "house"], "ground": "snow"}, "time": "dusk", "weather": "snow",
 "people": [{"who": "ww1_german", "id": "soldier", "at": "far_left", "do": [{"act": "limp_to", "to": "center"}]},
            {"who": "civilian_woman", "at": "right", "mood": "shocked", "do": [{"act": "freeze", "on": "home"}]}],
 "camera": "follow", "focus": "soldier"}
```

**Money and war** (war bonds):
```json
{"at": "Families bought war bonds", "recipe": "scene", "says": "Ordinary families lent their savings to the state.",
 "idea": "At a bank counter a mother counts out coins while a clerk slides a war-bond certificate back to her.",
 "where": {"room": "office", "items": ["poster", "drawers", "window"]},
 "people": [{"who": "civilian_woman", "at": "center_left", "depth": "near", "do": [{"act": "count", "on": "bought"}]},
            {"who": "civilian_man", "id": "clerk", "at": "center_right", "depth": "back", "do": [{"act": "give", "to": "civilian_woman", "with": "paper", "on": "bonds"}]}],
 "things": [{"what": "counter", "at": "center", "depth": "mid"}, {"what": "coins", "on": "counter", "dx": -120}],
 "camera": "two_shot", "focus": "civilian_woman", "partner": "clerk"}
```

**A field hospital** (the cost):
```json
{"at": "The hospitals were full", "recipe": "scene", "says": "The wounded filled every hospital.",
 "idea": "A nurse moves slowly along a row of beds in a ward at night with a lantern, stopping at one bed.",
 "where": {"room": "ward", "items": ["window", "beds", "window"], "light": "lantern"}, "time": "night",
 "people": [{"who": "civilian_woman", "id": "nurse", "at": "left", "holds": "lantern", "do": [{"act": "walk_to", "to": "center"}, {"act": "hand_on_heart", "on": "full"}]}],
 "camera": "pan"}
```

**Spies and secrets** (a message passed in a café):
```json
{"at": "The message reached Lisbon", "recipe": "scene", "says": "A secret message changed hands in neutral Lisbon.",
 "idea": "In a café two men at a table never look at each other; one slides a newspaper across, the other folds it away.",
 "where": {"room": "tavern", "items": ["shelf:bottles", "window:street", "mirror"]},
 "people": [{"who": "civilian_man", "id": "agent", "at": "center_left", "seated": true, "do": [{"act": "give", "to": "contact", "with": "paper", "on": "reached"}]},
            {"who": "diplomat", "id": "contact", "at": "center_right", "seated": true, "do": [{"act": "look_around", "on": "Lisbon"}]}],
 "things": [{"what": "table", "at": "center", "depth": "near"}, {"what": "cup", "on": "table", "dx": -60}, {"what": "cup", "on": "table", "dx": 60}],
 "camera": "wide_then_close", "focus": "contact", "close_on": "Lisbon"}
```

**A factory at full speed** (production):
```json
{"at": "Production doubled", "recipe": "scene", "says": "Factories doubled their output.",
 "idea": "In a works yard women push carts of shells past a foreman who checks each one off — the line never stops.",
 "where": {"town": "industrial", "buildings": ["factory", "tenement", "factory"]},
 "people": [{"who": "worker", "id": "foreman", "at": "right", "do": [{"act": "write", "with": "ledger"}, {"act": "point", "to": "left", "on": "doubled"}]}],
 "crowd": {"kind": "workers", "n": 5, "who": ["civilian_woman", "worker"], "at": "center_left"},
 "things": [{"what": "shell", "at": "center", "depth": "near"}, {"what": "shell", "at": 1100, "depth": "near"}],
 "camera": "pan"}
```

**Propaganda** (a poster changes minds):
```json
{"at": "The posters promised", "recipe": "scene", "says": "Posters promised a quick and glorious war.",
 "idea": "Young men crowd round a recruiting poster on a town wall and one of them tips his cap and walks toward the office.",
 "where": {"town": "english", "buildings": ["tenement", {"item": "office", "text": "RECRUITING OFFICE"}, "house"], "items": [{"item": "poster", "text": "YOUR COUNTRY NEEDS YOU", "x": 700}]},
 "crowd": {"kind": "watchers", "n": 4, "who": ["worker", "civilian_man"], "at": "center_left", "mood": "happy"},
 "people": [{"who": "worker", "id": "volunteer", "at": "center", "do": [{"act": "tip_hat", "on": "promised"}, {"act": "walk_to", "to": "center_right"}]}],
 "camera": "wide_then_close", "focus": "volunteer", "close_on": "promised"}
```

The two test projects hold 33 more cards: ports, warehouses, shops, admiralties, pubs, quays, streets by day and by night, fields, kitchens, classrooms, ministries, press rooms and parliaments.
