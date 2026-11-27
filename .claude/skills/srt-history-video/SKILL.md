---
name: srt-history-video
description: Turn a narration (an .srt, a voice recording, or both) into a finished military-history animated documentary told like a film — every clause one concrete acted picture, chibi characters acting in detailed story places, dissolves and slow camera moves, place/time tags, big-question captions, battles, maps as short bridges, ambience and SFX (no music) — rendered with this repo's engine, plus the YouTube package (3 titles, thumbnail prompts + drafts, description with chapters, tags, hashtags). Planned as scene cards compiled by tools/make.py. Use whenever the user drops an .srt and/or a voice file into projects/ or asks to make, re-make or fix a history video, its thumbnails or its metadata.
---

# Narration → military-history animated video (studio edition)

You are the director. The engine draws. You decide what the viewer sees for every clause, by writing **scene cards**.
The film is told like an animated movie: one clause → one concrete picture of exactly what it says, acted by people in a real place; text and maps are rare bridges ([references/storytelling-film.md](references/storytelling-film.md), measured on the reference channel).

**Follow `AGENTS.md`, then `playbook/00-START-HERE.md`, step by step.** This skill file only adds what a Claude session needs on top of them.

## The path (details in playbook/)
1. `python tools/make.py projects/<slug> prepare`. It accepts an SRT only, a voice only, or both.
2. Read **all** of `work/reading.md`. Then fill `understanding.md`:
   - question and answer;
   - people → presets;
   - **story arcs** (anecdotes);
   - **story places** (`place_id`, tag text, how they change);
   - symbols and **big questions**;
   - numbers (spoken / stat / chart);
   - chapters;
   - for every clause: WHO · DOES WHAT · WHERE · WHEN · **IDEA** (what we see, why) · scene card or recipe (`playbook/narration-to-picture.md` §1, `playbook/visual-ideas.md`).
   - **Pre-production lists**: every person, costume, story place, building, plant, vehicle, thing and weather the pictures need (template §8b).
2a. **The living library** (`playbook/library.md`): `python tools/lib.py match --project projects/<slug>` → `work/match.md`.
   Use what exists, adapt what is close (`lib new … --from`, `"recolor"`), create what is missing:
   - with an image model (Muse): `prompt.txt` + `library/STYLE_REFERENCE.jpg` → `lib import` (vector) — far backgrounds stay pictures (`plates`);
   - without one: draw the parts in code (the type pages in `playbook/library/` have complete examples);
   - then `lib preview --grid` and `lib check`.
2b. Pre-production, in `cards/_film.json`:
   - `cast`: everyone; children with `"size": 0.7–0.8`; costume pieces with `"wear"`;
   - `sets`: story places — rooms, towns, or composed landscapes (`compose`: far layers, ground, road, rows of library plants and buildings), with tags; library places by id;
   - `drawings`: only one-off things;
   - `look`: seed and grade, so each film looks and moves differently.

   Then run `python tools/make.py projects/<slug> preview` and fix until every sheet is right (`playbook/scene-writing.md` §8).
3. Write the cards:
   - `cards/_film.json`: era, sides, cast with name and role, extra places, `look`, `sets`, `drawings`.
   - **Most cards are `scene` cards**: `idea` → `where` → `people` with `do` acts on the words → `things` → `camera` (`playbook/scene-writing.md`; vocabulary in `recipes/STAGECRAFT.md`). Recipes for battles, maps, charts and documents.
   - `cards/chNN.json`: one card per idea, 3–10 s. Each card has:
     - `at`: the first words, copied exactly;
     - `recipe`;
     - `says`: the meaning in your own words;
     - the recipe's fields.

   Choose recipes with `playbook/narration-to-picture.md`; the fields are in `recipes/<id>.md`.
   Use the story fields on every film:
   - `place_id` (a returning place keeps its setting and tag);
   - `tag` + `tag_on` (place/time tag on each new place);
   - `name_card`;
   - `caption` (big questions only, over acted cards).
   Use `stat` and `paper_note` rarely.
4. `python tools/make.py projects/<slug> cards`. Fix every error, which says what to change. Fix the warnings too:
   - the same recipe twice in a row;
   - chapter mix;
   - card length;
   - `says` copied from the narration.

   Targets: acted cards (action + talk recipes) ≥ 75 % of every chapter; maps ≤ 10 % (≤ 5 s each); documents/charts ≤ 10 %; host ≤ 8 %.
5. `review --at all`. Open every `review/sheet_*.jpg` and answer the yes/no checklist in `playbook/05-review.md` (24 questions; 17–24 are the scene-card problems: hidden focus, things over faces, writing, flags, children, seats, timing, natural arms). Fix **only the wrong cards**; re-check them with `review --scenes … --at all`.
6. `audio` → `video` → `mux`. Run one render at a time. Then check frames of the final MP4. Later fixes: `cards` → `review --scenes` → `patch` (re-renders only the changed scenes).
7. The YouTube package (`playbook/07-youtube.md`).

## Hands and held things (what the engine does, what you choose)
- **Arms:** hands in front of the body (holding, carrying, clasped, in the pockets, binoculars, praying, eating) are drawn foreshortened. The arm comes straight from the shoulder with the elbow down, never in an inward loop. Elbow-out poses keep the bent arm: hands on hips, salute, telephone, hand to the ear, head or chin.
- **Held things sit in the hand:**
  - every prop has a grip point (the neck of a sack, the handle of a basket, the middle of a crate);
  - two-handed things are held by their sides;
  - a drawing you make can say where it is held: `"grip": [x, y]`.
- **Choose the act that keeps the face clear:**
  - `show` presents a paper or an object at chest height (use it in close shots); `hold_up` lifts it above the head (a newsboy, a protester, in a wide shot);
  - `carry` holds a sack or a crate in front; `carry_sack` puts a sack on the shoulder, behind the head;
  - covering the face only when the story says so: `cry`, `gasp`, `binoculars`, `drink`.
- After a change in `src/` (how arms, props or sets are drawn), `patch` cannot see it: render the whole film with `video`.

## Fixed choices (never ask)
- Military history.
- The narration comes from the user.
- **No music**: ambience and SFX only.
- All visuals are drawn by the engine.
- 1920×1080, 24 fps.

Talk to the user in their language (Vietnamese by default). On-screen text and metadata follow the narration's language. Never upload or publish anything.

## When recipes are not enough (strong models)
- **A recurring kind of sentence**: add a recipe in `tools/cardlib/recipes_*.py`. Then run `python tools/catalog.py --previews`, check its preview tiles, and add a row to `narration-to-picture.md` (`playbook/08-advanced.md` §B).
- **A moment no recipe shows**: write a `scene` card. It composes any place, people, acts, things, crowd, vehicles and camera (`playbook/scene-writing.md`).
- **A thing the engine lacks** (a costume, a building, a plant, a vehicle, a prop, a place, a weather): make it a library asset of the film (`playbook/library.md`), then `lib promote` it when the film is done.
- **A one-off moment beyond that**: use the `raw` recipe, which takes an engine scene. Schema: [references/plan-schema.md](references/plan-schema.md).
- **A missing visual** (set, prop, vehicle, pose, fx): extend the engine in `src/`, then run `npx tsc --noEmit` and render a still. Follow the neighbouring code's style. Never fake a missing visual with a label.

## Reference material (for recipe and engine work)
- [references/storytelling-film.md](references/storytelling-film.md): the film grammar measured on the reference channel (dissolves, push-ins, tags, captions, anecdotes, places revisited, absence).
- [references/action.md](references/action.md): battle recipes, depth rules, how to animate fighting.
- [references/acting-camera.md](references/acting-camera.md): reads, coverage, acting and motion rules behind the recipes' camera work.
- [references/plan-schema.md](references/plan-schema.md): the engine's scene and element schema (`raw` scenes, engine work).
- [references/storytelling.md](references/storytelling.md): macro structure, the scored device, the host.
- [references/sound.md](references/sound.md), [references/thumbnails.md](references/thumbnails.md), [references/metadata.md](references/metadata.md), [references/cast.md](references/cast.md).
- `docs/STYLE_GUIDE.md` (what a good frame looks like) and `docs/QUALITY.md` (definition of done).
