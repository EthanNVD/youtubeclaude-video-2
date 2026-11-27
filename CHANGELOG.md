# CHANGELOG

Newest first. One entry per change that matters to the look, the pipeline or the docs.

## 2026-11-27 — Video-2: the living library
Why: every person, costume, place, plant, vehicle and weather was fixed in the engine's library; a new region or story
(Malaya 1942) had nothing to show. Now each film finds what exists, adapts what is close, creates what is missing (with
an image model, or by drawing shapes in code) and promotes it, so the library grows with every film.

What changed:
- `library/<type>/<id>/asset.json` for props, vehicles, buildings, plants, costumes, characters, places, plates, weather;
  `tools/lib.py`: index, search, match, new, import (image → vector), check, preview, place, promote, style-sheet;
  `library/README.md`, `library/prompts/`, `library/STYLE_REFERENCE.jpg`.
- People: costume pieces drawn on the rig in five slots (`wear`, `recolor`, `armColor`); riding (`"rides": "bicycle"`,
  seat and crank anchors, pedals and rolling wheels); `cyclists` crowds; `dig` pose; bicycle sounds.
- World: composed places (`compose`: sky, plates, far layers, ground, road, rows of library assets in depth); library
  places by id; parametric weather (rain → downpour, snow, blizzard, haze, fog, dust, sandstorm, ash, leaves, petals,
  lightning; amount, wind) and weather presets.
- Plans store each drawing once (`plan.drawings`, `"@d<n>"`).
- Docs for every model: `playbook/library.md` (the loop) and one page per type with a worked example (`playbook/library/`).
- Proof: `projects/malaya-test` (66 s): 20 scene cards, 24 new assets drawn in code and promoted.

## 2026-11-22 — Rain and snow cover the whole frame
Why: the user saw rain (and snow) only in the bottom-right quarter of the picture, in this film and in earlier ones.

Cause:
- `src/scene/SceneView.tsx` drew the weather as an fx element. An fx element is already centred on the frame (x 960, y 540 by default).
- It was also wrapped in a second `translate(960 540)`. The rain field, centred on its origin, ended up centred on (1920, 1080): a quarter of the frame.

Fix:
- the extra translate is gone; the weather layer is placed once, at the frame centre;
- the fx element now passes its `w`/`h` to the drawing; the weather layer uses 2200×1300, so camera moves never show an edge.

Every film with `weather: rain|snow` outdoors is affected. Re-render the whole film with `video`: `patch` cannot see engine changes.

## 2026-11-22 — Natural arms and hands: no "chicken-wing" loops, things held in the hand
Why: the user flagged arms that curl inward in loops:
- hands in the pockets, holding cards or a crate;
- hands clasped, holding binoculars, carrying a sack in front of the face.

Cause: chibi arms are short. A full-length two-bone arm can reach a hand held in front of the chest or the face only by throwing the elbow out sideways and folding the forearm back.

What changed:
- `src/char/Character.tsx` `softIk`: an arm whose hand is in front of the body is drawn foreshortened, as if it pointed toward the camera.
  - It is a short tube from the shoulder to the hand, with a gentle bend (at most 0.45·d/2 + 5 px).
  - The elbow bows down and outward, never up or inward.
  - Poses whose look is the elbow out keep the bent arm: hands on hips, salute, telephone, a hand to the ear, the head, the face or the chin. So do rifle handling and running.
  - The switch between the two kinds of arm follows the pose blend: no elbow pops.
- **Held things sit in the hand.** The user flagged a sack floating beside a hand.
  - Every prop now has a grip point (`HOLD_ANCHOR` in `src/scene/Elements.tsx`): the neck of a sack, the handle of a basket, a bucket, a lantern or a suitcase, the middle of a crate or a pot, the handle of a spoon or a knife. That point is put in the palm.
  - Two-handed things have a half-width (`HOLD_WIDTH`), and the hands move to their sides.
  - A drawing can declare `"grip": [x, y]`.
- Sacks:
  - A sack on the shoulder (`sack` pose) is drawn big, tilted onto the shoulder and behind the head, with the hand over it.
  - A person who just holds a sack carries it in front with both arms (`HOLD_POSE` sack → carry); walkers carry a basket or a sack in front.
  - The face stays clear.
- Docs:
  - `playbook/05-review.md` question 24 (natural arms);
  - `patch` cannot see engine changes: after a change in `src/`, render the whole film (06-sound-render §5, `tools/patch_video.py`).
- Both example films re-rendered; `recipes/img/stagecraft/` act pictures re-rendered.

## 2026-11-21 — Creative scenes: every clause composed from the narration, not picked from a template
Why:
- The recipes are fixed compositions with 2–3 variants, so long films repeated scenes.
- The user wanted every film told from its own content, creative and never repeating.
- They also wanted better character and hand movement, and the ability to create characters, equipment, places and vehicles first.
- After the build: check everything, and fix only the scenes that are wrong.

What changed:
- **The `scene` card** (`tools/cardlib/recipes_scene.py`, vocabulary in `tools/cardlib/stagecraft.py`). A director's `idea`, then:
  - `where`: a story place, room/town kit or engine set;
  - `people`: slot, depth, facing, mood, holds, seated/kneel, walking style, size, `do` acts on phrases;
  - `crowd`: queue, watchers, walkers, marchers, mourners, cheering, workers, protest, listeners; `"view": "back"` puts heads along the bottom edge;
  - `things` (on other things, appear on a word, moving, in the sky), `vehicles`, `effects`, `camera` (12 presets or a shot list).

  The compiler computes:
  - positions, depth, sizes;
  - who faces whom;
  - hand-overs: the giver walks up to the receiver;
  - putting big things down before a free-hand gesture;
  - seats: a chair indoors, a crate outside;
  - automatic acting: gestures on stressed words while talking, by mood; small shifts while listening; glances while waiting;
  - camera shots, dissolves, a second set-up for long shots, tracking of walking subjects;
  - footsteps and business sounds, ambience.

  Randomness is seeded by the film's `look.seed` and the card's own words: each film moves differently, and editing one card does not reshuffle the others.
- **Set kit** (`src/sets/Kit.tsx`):
  - `room`: 18 styles; 35 modules (windows with an outside view, shelves with contents or empty, stoves, ovens, beds, drawers, posters, flags, signs…); walls, floors, light (window shafts, lamp/candle/fire pools); poor/cold variants.
  - `town`: 8 styles with shop signs in the place's language; 10 building types (shops with awnings and window goods incl. "sold out"); 13 street items.
- **Characters**:
  - 30 new gestures and business poses with motion cycles (stir, ladle, eat, peel, knock, hammer, pray, cry, hand on heart, palms, lean, comfort, give, beckon, point down, warm hands, shiver, clap, wring, listen, reach up, cradle, sack, tip hat, push, pull, gasp, read, wait, basket);
  - walking styles `shuffle`, `march`, `limp`, `sneak`;
  - held props never mirror their writing; per-item hold sizes; children by `size`.
- **Props**: bowl, pot, bread, spoon, plate, cup, bottle, jug, sack, bale, ingots, basket, ration card, letter, bucket, lantern, baby, potatoes, turnips, counter, bench, stool, stove, cart, scale, knife, playing cards.
- **Declarative drawings** (`src/props/Drawing.tsx`): things the engine lacks, drawn in JSON from shapes, in the same style.
  - Placed, held, moved, stacked; motion: spin, flicker, sway, blink, drift.
  - Films define them in `cards/_film.json` `"drawings"`; the shared library is `assets/library/drawings/` (field_kitchen, notice_board, zeppelin, bicycle).
- **Pre-production preview** (`make.py <proj> preview`, `tools/preview.py`): sheets of the cast (standing and acting), every story place with a man for scale, every drawing; `--kit`, `--acts`, `--library`.
- **Patch render** (`make.py <proj> patch`, `tools/patch_video.py`): after fixing some cards, re-renders only the changed scenes (+ the dissolve after), splices them frame-exact, rebuilds the sound, re-muxes. Tested: a 2.7 s change re-rendered in about 1 min.
- **Checks**:
  - repetition of look (place + camera + acts) and of ideas;
  - three equal cameras in a row; five cards in one place;
  - people at the frame edge; a flag without a nation;
  - unknown acts/things replaced by the closest and logged in `work/missing_assets.json` (with the card's `wish`).
- **Look per film**: `look.grade` = film | warm | cold | bleak | sepia | vivid.
- **Partial review** no longer leaves stale sheets. Scene cards plan their own coverage (the old auto-coverage skips them).
- **Docs**:
  - `playbook/scene-writing.md`: method, fields, places, cast, acts, crowds, things, drawings, vehicles, effects, cameras, 9 templates, pre-production, fixing single scenes, mistakes, examples from many kinds of stories;
  - `playbook/visual-ideas.md`: a bank of ~50 picture devices;
  - `recipes/STAGECRAFT.md`, generated with pictures;
  - AGENTS, 00-START-HERE, 02, 03, 05 (questions 17–23), 06 (§5 patch), narration-to-picture, understanding template (IDEA column, pre-production lists), SKILL, QUALITY, CLAUDE.
- **Examples**:
  - `projects/creative-blockade/`: WW1 blockade → Turnip Winter, 20 cards, 94 s;
  - `projects/creative-austria/`: how Austria taught Hitler, 13 cards, 65 s, a different script with its own drawings.

  Both compiled without warnings, were reviewed frame by frame (start, middle, end), and rendered.

## 2026-11-21 — Story grammar: tell it like an animated film (every clause one acted picture)
Why: the user wanted films that tell the story with pictures the way Ember History does — characters acting in places that follow
the narration, not numbers and paper on screen. Two Ember films were measured frame by frame (projects/ember-test/ANALYSIS.md):
- ~88 % of transitions are 0.6 s dissolves;
- ~80 % of shots push in slowly (~1.5 %/s);
- shots last 4.6 s (median);
- text lands ~0.25 s after its word;
- stories enter through one person in one place, places return changed by time, and loss is shown by absence.

A 60 s WW1 test was approved, then rebuilt from cards only (`projects/example-ww1-cold-open`): 95 % acted, 3 s of map, no stat/paper cards.
- **Engine:**
  - `scene.shotDissolve`: set-up changes dissolve over 0.6 s;
  - scene dissolves 0.6 s (`transitionDur`);
  - place/time tag `scene.tag`/`tagIn` (carried over without re-animating);
  - HUD elements `caption` (word-by-word big questions, amber accents), `stat` (engraved statistic), `note` (typed paper note), `binoculars` (POV lenses);
  - label style `chalk`;
  - fonts Cinzel (`FONT.title`) and Cormorant Garamond (`FONT.book`).
- **Cards:**
  - Every scene dissolves by default; inside a place every reframing dissolves.
  - New common fields:
    - `place_id`: a story place keeps its setting and tag; a different setting under the same id warns;
    - `tag` / `tag_on`: an unchanged tag stays put;
    - `caption` / `stat` / `paper_note`.
  - Auto-coverage frames moving groups (never one giant running face).
- **10 story recipes** (`tools/cardlib/recipes_story.py`): `establish`, `approach`, `interrupt`, `confront`, `contemplate`, `watch_front`,
  `binocular_view`, `vista`, `lecture`, `absence`. `wave`/`retreat` reframed for groups; `lecture` keeps the board in frame.
- **Targets (replace "action ≥ 55 %"):**
  - acted cards (action + talk) ≥ 75 % per chapter;
  - maps ≤ 10 % and ≤ 5 s each;
  - documents/charts ≤ 10 %;
  - host ≤ 8 %;
  - ≤ 1 stat card per ~2 min;
  - captions only on acted cards.

  Applied in the compiler and the validator.
- **Docs:**
  - `playbook/narration-to-picture.md` rewritten: the five-question picture-writing method (WHO / DOES WHAT / WHERE / WHEN / recipe), the lookup table, ten film patterns, targets;
  - understanding template with story arcs, story places, symbols and big questions, and beats written as WHO · ACTION · WHERE · WHEN;
  - 02-understand, 03-cards (story and text fields), 04-compile (new warnings), 05-review (sound-off test);
  - AGENTS rules; SKILL.md;
  - new `references/storytelling-film.md`;
  - plan-schema (new fields), STYLE_GUIDE §2a, QUALITY;
  - worked example `projects/example-ww1-cold-open`; the study `projects/ember-test`.
- No music, as before: ambience and SFX only.

## 2026-11-21 — Fix: `bombing` without civilians framed a missing element
Why: `bombing` with `"civilians": false` cut to a close shot of `c0`, a civilian that is only drawn when civilians are on, so the
engine validator failed ("frames 'c0' — no element has that id"). Found while building `projects/fall-of-singapore`.
- `tools/cardlib/recipes_other.py` `bombing`: with no civilians, the second shot now follows the lead bomber `b0` (medium).

## 2026-11-17 — Studio edition: scene cards, recipe catalog, step-by-step playbook
Why: weaker models (Sonnet, Muse) building from the old skill repeated the same scenes and missed the meaning, because they had
to write raw engine JSON (coordinates, depth, camera, timing) and nothing forced them to understand the script first.
New repo `youtubeclaude-studio` (history kept); the engine is unchanged.
- **Scene cards** (`projects/<slug>/cards/_film.json` + `chNN.json`): one card = one scene = one idea; fields `at` (first words), `recipe`,
  `says` (meaning in own words), recipe fields from menus. `tools/cardlib/` compiles them to plan.json: phrase timing on the words,
  positions/depth/camera/motion/sound from tested recipes, rotating composition variants, sides → uniforms/vehicles by era,
  map places by name (`data/places.json`), cast looks (`preset@officer`), auto-coverage.
- **49 recipes** (people, ground action, sea, air, home front, mood, maps, documents, host, device, raw escape hatch), each with
  when/not-when, typed fields, 1-3 variants, an example card and preview stills (`recipes/`, generated by `tools/catalog.py --previews`).
- **Checks written as instructions**: unknown fields/values with suggestions, phrases not found (shows the narration to copy from),
  same recipe twice in a row, recipe overuse, per-chapter action/talk/map/device mix, card length, `says` copied from the narration.
- **Flexible input**: `tools/prepare.py` accepts SRT only, voice only (transcribed) or both (`--align` re-times words on the voice);
  writes words.json, reading.md, understanding.md, cards/_film.json.
- **Playbook** (`AGENTS.md`, `playbook/00-09`, `narration-to-picture.md`): every step with commands, done-criteria, error/warning fixes,
  yes/no review checklist; templates for understanding.md and STATUS.md; worked example `projects/example-ww1-verdun` (70 % action).

## 2026-11-17 — Action: screen-time mix, battle recipes, depth for effects
Why: the WW1 film was 22 % action (talk 25 %, maps 18 %): generals talking and charts where the reference animates battles.
The user asked for more action and natural combat animation. A 2-minute sample chapter (`projects/ww1-action-test`, WW1 599–723 s)
reached 74 % action. Review of that sample found explosions drawn over men in front of them, fallen and carried men still walking,
and an unreadable stretcher. All are fixed in the engine.
- Engine (`src/`):
  - actor `fallAt`/`fallDir` (tip over, small bounce, lie still), `lying`, `silhouette` (any element);
  - rifle `fireAt` (single shots) and `fire: [from, to, period]` (machine gun): muzzle flash at the rifle tip;
  - vehicle `fireAt` (flash, smoke puff, recoil; per-type barrel tip, `muzzle` override);
  - scene `impacts` (decaying camera jolt);
  - set `nomansland`, fx `shellburst`, prop `stretcher`.
- Depth: in `world` scenes ground effects (`shellburst explosion impact dust smoke fire splash`) and props are sorted far→near with
  people and vehicles, and ground effects are sized by depth; battle scenes without a world still sort people/vehicles/bursts by y.
  `depthY` overrides an element's sort depth.
- Gait: men who are down (`fallAt` passed, `lying`) never walk; `run: true` runs only while the path moves.
  A rifle appears only at 80 % of the pose blend when the previous pose had no rifle.
- Audio: guns that fire (`fireAt`) get artillery/cannon cues; `shellburst` gets explosion cues; `markiv`/`renault` get tank engine.
- `tools/shotlib.py` ACTION RECIPES: `assault`, `shells`, `gun_crew`, `mg_nest`, `hit_and_help`, `stretcher_team`, `fallen`,
  `man_path`, `person_scale`, `WORLD`.
- `tools/validate_plan.py`: `classify()` (action/talk/map/device/host), `mix` in the output and `work/mix.json` per chapter;
  warnings for chapters under target, maps > 12 s, people standing > 6 s with no business, bursts next to unscaled people
  without a world.
- Docs: new `references/action.md` (mix targets, recipes, depth rules, how to animate action, battle checklist); SKILL.md,
  plan-schema.md, storytelling.md, STYLE_GUIDE §4c, QUALITY, ROADMAP K1–K10.

## 2026-11-17 — WW1 Turning Point film + voice-only input
Why: the user supplied only a narration WAV for "What Was The REAL Turning Point of WW1".
- `tools/transcribe.py`: voice → SRT with faster-whisper (CPU, int8, word timestamps). With `--script`, the recognised words are aligned to the written script, so names and numbers are spelled as written (95.5 % matched on this film).
- WW1 vocabulary:
  - `pickelhaube` hat;
  - presets for the Kaiser, Hindenburg, Ludendorff, Moltke, Schlieffen, Kluck, Falkenhayn, Scheer, Holtzendorff, Zimmermann, Bauer, Joffre, Lanrezac, Gallieni, Foch, Jellicoe, Brusilov, Wilson, Lenin, Monash, Currie, plus 1914/1918 soldiers of each army and sailors;
  - `markiv` and `renault` tanks;
  - `turnip` prop;
  - a brass-framed hourglass with a falling sand stream.
- The validator accepts every machine vehicle type.
- `projects/ww1-turning-point/plan_src/timing.py` resolves scene starts from phrases of the aligned words; `lib.py` adds a cut to any people-shot held longer than 6 s (skipping people who have walked out of frame). This is a candidate for shotlib.
- Film: 259 scenes, 487 set-ups (avg 4.0 s), 12 chapters.

## 2026-11-17 — Acting, coverage and natural motion
Why: the user found Market Garden v2 static and its motion jerky.
- Static: one frozen set-up per 8 s scene, no close-ups, actions told by labels.
- Jerky: things popping in on every cut, moves that lunge then stop dead, sliding feet.

Approved on a 1-minute test (`projects/acting-test`).

Changes:
- **Coverage** (`scene.shots` in `src/scene/SceneView.tsx`):
  - set-ups framed by subject id and size (`wide … ecu`), `frameX`, push/pan;
  - `track` with a lagging camera;
  - hard cuts inside a place.
- **Acting:**
  - `turn` (3/4 face);
  - expression take;
  - `front` layer for desk props and over-the-shoulder actors;
  - keyed `holds`;
  - walking toward/away from the camera;
  - props `photo`, `magnifier`, `suitcase`; element `viewfinder`.
- **Motion** (`src/lib/anim.ts`, `Elements.tsx`, `Character.tsx`):
  - default ease is smoothstep (the old cubic peaked at 3× speed);
  - people travel with `walk`/`arrive`/`leave` profiles and vehicles with `drive`;
  - the gait is driven by the distance covered and its amplitude follows speed;
  - pose blends take 0.45–0.95 s with overlapping hands, anticipation and a 4 % settle;
  - no pop on cuts (`place`/`drop` enters for props, soft pop for text);
  - vehicles pitch with acceleration and aircraft bank;
  - camera shake is smooth noise.
- **Validator:**
  - errors for unknown shot ids/sizes;
  - warnings for single set-ups over 6.5 s and for sprinting actors;
  - a `coverage` summary (set-ups, average length, close-ups, acting share).
- **shotlib:** `SHOT`, `AID`, coverage templates `desk_read`, `ots_dialogue`, `desk_insert`, `walk_to_camera`, `walk_away`, `vehicle_arrives`.
- **Skill:** new `references/acting-camera.md` (reads, coverage, acting, motion, strip checks); SKILL, plan-schema, shots, storytelling, STYLE_GUIDE, QUALITY and ROADMAP updated.
- **Learned from** the ethanNVD frame studies (cut grammar, phases of an action) and opus-video-skills *painted-animation* (reads, timing, animation principles).

## 2026-11-17 — Script-writer skill and first drafts
Why: the user wanted the Codex `two-sides-war-script-writer` skill ported to Claude, upgraded from an editor's study of the channel's top 10 videos, able to research new topics and rewrite old scripts in the channel's voice.
- `.claude/skills/two-sides-war-script-writer/`: modes `topic_research` / `new_from_title` / `rewrite_channel_voice` / `rewrite_same_structure`; new references (top-10 analysis, channel formula, topic research, channel-voice rewrite); dialogue policy (QUOTE / REPORTED / DRAMATIZED / HOST, ≤15 %); clean + speaker-tagged outputs.
- Scripts: `channel_snapshot.py` (yt-dlp channel list + subtitles), `script_metrics.py --tagged` (tagged file matches clean text, dialogue share).
- `scripts_out/`: topic shortlist (18 scored candidates) and four research-limited drafts — Market Garden, WW1 turning point, Singapore, Battle of the Bulge — each with clean text, tagged text and sources.

## 2026-11-16 — Proportion and depth
Why: the user saw people as big as (or bigger than) the tank they stand next to.
Reference study:
- people next to vehicles are small (a man by a plane is fuselage-plus-gear high);
- people close to the camera can outsize a truck behind them.
Changes:
- `src/lib/depth.ts` + `scene.world`: ground-plane perspective; vehicles sized relative to people at the same depth (measured drawing sizes); far→near draw order; keyed `y` grows toward the camera.
- `layout_check.proportions` in validate: flags vehicles >40 % off.
- `parked: true`: landing gear for aircraft on the ground.
- Five depth-staged shot templates.
- Test clip: `projects/_test/out/depth-test.mp4` (32 s, silent).

## 2026-11-16 — Film-quality look, part 2
Why: the user found the maps cluttered and unlike the reference, spotted an extra blob on hands, and asked for roadmap items a–e in order, a stronger grade and occasional letterbox.
- Maps: clean coloured paper look (stipple, slate sea, thin borders), opt-in named rivers drawn as smooth water bands, `hatch`, small-caps town labels with `tag` for key places.
- Hands: thumb behind the palm (no ball on top), clean open hand; flat props gripped by their edges.
- Grade: stronger warm grade + vignette; `letterbox` scenes with a "DRAMATISED — …" caption.
- (a) Machines.tsx: trucks, jeep/Kübelwagen, half-tracks, field gun, fighters per nation, Stuka, heavy bombers, Dakota, Horsa, warships, Liberty ship, U-boat, boat — all with volume.
- (b) Rifle drill poses: port, aim, shoulder, charge, ease (rifle placed between the hands).
- (c) Physical devices in the new `workshop` set: glass tubes (bars), corkboard + yarn (timeline), brass scale with hanging tags.
- (d) Map movers (side-view icons with trails), `map.follow` camera, morphing fronts, shrinking pockets.
- (e) `tools/shotlib.py`: 13 shot templates + `Plan` assembler; documented in references/shots.md.

## 2026-11-16 — Film-quality look, part 1
Why: the user found the look crude (road scene: trees not scrolling, overlapping exits, vehicles zooming then stopping, sparse maps, text on text).
Studied two reference videos frame by frame → rules in `docs/STYLE_GUIDE.md`.
- Look: depth-of-field blur on backgrounds (`set.dof`), warm desaturated film grade + stronger vignette (`meta.grade`), slow camera drift on every shot without camera keys (`set.drift`).
- Vehicles: `drive` easing (accelerate–cruise–brake) is the default on vehicle `x`/`at` keys; wheels/tracks turn by distance travelled; new volume tanks `sherman panzer4 tiger t34 panther stug` (`src/props/Tanks.tsx`, `crew` = commander in the hatch).
- Road device v2: parallax world (forests, poplars, fence posts) scrolling with the road, exits only above the road with gantry signs, culled when far, town boards, `time`, `vehicles` (convoy).
- Maps: Natural Earth rivers + lakes (`public/maps/physical.json`, `tools/fetch_physical.py`), italic river names, inked coasts, ripple hatching, graticule, paper folds; `legend` and `blocks` elements.
- Validator: `tools/layout_check.py` — text/text, text/badge, text/face overlaps; vehicle speed limits; `fix_speeds()` for plan builders.
- Control docs: `ROADMAP.md`, `docs/STYLE_GUIDE.md`, `docs/QUALITY.md`, `projects/_template/STATUS.md`.
- Market Garden plan: 0 overlap/speed warnings. Needs a re-render to get the new look.

## 2026-11-16 — Market Garden delivered
- Full film (254 scenes, 34:04), package, thumbnail prompts. Rally banners now carry national flags. Mixer processes long voices in 30 s chunks.

## 2026-11-15 — Pipeline v1
- SRT + voice → plan → review → audio → render → mux → YouTube package. Characters with attached heads, hose limbs, pose blending, host + aide.
