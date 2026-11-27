# AGENTS.md — how to make a video in this repo (read this first, every session)

This repo turns a narration (an `.srt` subtitle file and/or a voice recording) into an animated military-history video, in
the "Two Sides of War" style, plus its YouTube package. You are the **director**:
- you decide what the viewer sees for every sentence;
- the code draws it.

**You do not write animation code or coordinates.**
- You write **scene cards**: small JSON objects.
  - **Most cards are `scene` cards** ([playbook/scene-writing.md](playbook/scene-writing.md)): you write the director's `idea` for the clause, then the place, the people and what they do on which words, the things, and the camera.
  - The compiler stages it: positions, depth, who faces whom, gestures, camera, dissolves, sound.
  - Every script gets its own places, people and pictures. Nothing is a fixed template.
- **Recipes** (tested compositions: battles, maps, charts, documents) are the fast way to show those moments.
- A compiler turns the cards into the film.
- **The living library** (`library/`, [playbook/library.md](playbook/library.md)) holds everything films have needed so far:
  costume pieces, props, vehicles, buildings, plants, places, painted far backgrounds, weather presets.
  - For every film you list what the pictures need, **use** what exists, **adapt** what is close, **create** what is missing
    (with an image model, or by drawing shapes in code), check it on preview sheets,
  - and at the end you **promote** the new things into the library, so the next film starts richer.
  - Any region and any story works this way: Malaya 1942 needed songkoks, sarongs, rubber estates and bicycles; they are
    now in the library (`projects/malaya-test`).

## The 9 steps (do them in order; each has its own page in `playbook/`)

| # | step | you run / write | page |
|---|---|---|---|
| 0 | Start the session | read this file, `ROADMAP.md`, the project's `STATUS.md` | [00-START-HERE](playbook/00-START-HERE.md) |
| 1 | Prepare the inputs | `python tools/make.py projects/<slug> prepare` | [01-setup](playbook/01-setup.md) |
| 2 | Understand the script | read **all** of `work/reading.md`, fill in `understanding.md` (with one `idea` per clause) | [02-understand](playbook/02-understand.md) + [visual-ideas](playbook/visual-ideas.md) |
| 2a | Inventory and match | `understanding.md` §8b (everything the pictures need), then `python tools/lib.py match --project projects/<slug>` → `work/match.md`: use / adapt / create | [library](playbook/library.md) |
| 2b | Pre-production | create what is missing (`lib new`, `lib import` or shapes in code, `lib preview`, `lib check`); `cards/_film.json`: `cast` (presets + `wear` costume pieces), `sets` (story places: rooms, towns, composed landscapes), `look`; then `python tools/make.py projects/<slug> preview` and look at every sheet | [library](playbook/library.md) + [scene-writing §8](playbook/scene-writing.md#8-pre-production-build-and-check-the-cast-places-and-drawings-first) |
| 3 | Write the cards | `cards/ch01.json`, `ch02.json`, …: `scene` cards for the story, recipes for battles/maps/charts | [scene-writing](playbook/scene-writing.md) + [03-cards](playbook/03-cards.md) + [narration-to-picture](playbook/narration-to-picture.md) + [recipes/STAGECRAFT](recipes/STAGECRAFT.md) + [recipes/CATALOG](recipes/CATALOG.md) |
| 4 | Compile and fix | `python tools/make.py projects/<slug> cards` (repeat until `"ok": true`, warnings fixed) | [04-compile](playbook/04-compile.md) |
| 5 | Look at it | `python tools/make.py projects/<slug> review --at all`, open every `review/sheet_*.jpg`; fix **only the wrong cards**, re-check them with `--scenes` | [05-review](playbook/05-review.md) |
| 6 | Sound | `python tools/make.py projects/<slug> audio` | [06-sound-render](playbook/06-sound-render.md) |
| 7 | Render | `python tools/make.py projects/<slug> video`, then `mux`; later fixes: `patch` re-renders only the changed scenes | [06-sound-render](playbook/06-sound-render.md) |
| 8 | YouTube package | titles, thumbnail prompts, description, tags | [07-youtube](playbook/07-youtube.md) |
| 9 | Hand over | `lib place` (story places worth keeping) + `lib promote` (the film's new assets → `library/`); report to the user, update `STATUS.md` | [library §7](playbook/library.md) + [00-START-HERE](playbook/00-START-HERE.md#9-hand-over) |

## Rules that are never broken

1. **Understand before you build.**
   - Read the whole of `work/reading.md`, not just the first part.
   - Fill in `understanding.md` before writing any card.
   - Every card has a `says` field: what the narration MEANS, in your own words.
2. **One card = one scene = one idea**, usually 3–10 seconds.
   - The card starts where that idea starts in the narration (`at` = the first words, copied exactly).
3. **Tell it like an animated film: one clause, one concrete picture.**
   - For every clause answer WHO, DOES WHAT (a visible action), WHERE, WHEN, then pick the recipe (`playbook/narration-to-picture.md` §1–2).
   - The picture shows exactly what the clause says, acted by people in a real place. Never pick by keyword or habit.
4. **People in places, not text.**
   - At least 75 % of every chapter is acted (people doing the thing); maps ≤ 10 % (≤ 5 s each); documents/charts ≤ 10 %.
   - Follow the anecdotes: the same people in the same places (`place_id`), revisited as time passes.
   - Text is rare: a place/time `tag`, name cards, the 2–4 big questions as `caption`, one `stat` per ~2 minutes at most.
5. **Never the same recipe twice in a row** (unless it is the same place revisited).
   - After a decision, show its consequence.
   - After an attack, show the other side or the cost.
5b. **Every card is its own picture.**
   - Write the `idea` first.
   - No two cards in a short span with the same place + camera + acts, unless it is a deliberate callback (`"revisit": true`). The compiler compares them.
   - Take devices from `playbook/visual-ideas.md`, each at most twice per film.
5c. **Build what is missing; never fake it with a label.** A person, a costume, a place, a building, a plant, a vehicle, a thing:
   - search the library first (`lib match`, `lib search`);
   - create what is missing as an asset of the film (`playbook/library.md` §5), or in `cards/_film.json` (`cast`, `sets`);
   - check it with `lib preview` and `make.py … preview`;
   - promote it at the end so it is never made twice.
5d. **Fix only what is wrong.** After `review`:
   - change only the wrong cards;
   - re-check them with `review --scenes …`;
   - after a render, `patch` re-renders only those scenes.
5e. **Read only what you need.**
   - Read your own project and the example projects a page names.
   - Do not open or search other films in `projects/`: their generated plans are large and only cost tokens.
   - Search in `tools/`, `src/`, `playbook/`, `recipes/` and your own project folder.
6. **Fix every error the tools print.**
   - Every message says exactly what to change.
   - Do not move to the next step while `"ok"` is `false`.
7. **Look at the pictures.** Open every review sheet and answer the checklist in `playbook/05-review.md`.
8. **Never run two renders at the same time.** Renders are `review`, `video`, `thumbs` and `prompts`; each one starts a browser, and two at once time out.
9. **Never upload or publish anything to YouTube.**
   - Do not commit media: `projects/*/out|review|work`, voice files, `assets/sfx/*.wav`.
10. **Language.**
    - Talk to the user in their language (Vietnamese by default).
    - Text on screen and YouTube metadata follow the narration's language.

## Fixed choices (do not ask the user about these)
- Military history.
- The user supplies the narration (`.srt`, voice, or both).
- **No music**: ambience and sound effects only.
- 1920×1080, 24 fps.
- Every picture is drawn by the engine in `src/`.

## Where things are

| path | what |
|---|---|
| `playbook/` | step-by-step instructions (start at `00-START-HERE.md`) |
| `playbook/scene-writing.md` | **the `scene` card**: method, every field, templates, examples, pre-production, fixing single scenes |
| `playbook/visual-ideas.md` | a bank of picture devices for numbers, lists, decisions, hunger, loss, news, journeys, memory |
| `recipes/STAGECRAFT.md` | everything a `scene` card can name (places, modules, acts, moods, crowds, things, drawings, cameras), with pictures |
| `library/` | **the living library**: one folder per asset (`library/<type>/<id>/asset.json` + `preview.jpg`); `library/INDEX.md` lists everything; `library/README.md` is the reference |
| `playbook/library.md`, `playbook/library/` | the library loop, and one page per asset type with a worked example |
| `tools/lib.py` | the library tool: `match`, `search`, `new`, `import`, `check`, `preview`, `place`, `promote`, `style-sheet` |
| `projects/malaya-test/` | the worked example of the library loop (66 s, Malaya 1941–42: costumes, plantations, bicycles) |
| `projects/creative-blockade/`, `projects/creative-austria/` | two complete scene-card films (WW1 blockade; how Austria taught Hitler) |
| `recipes/CATALOG.md` | every recipe: when to use it, its fields, preview images |
| `recipes/PEOPLE.md` | sides, uniforms, character presets |
| `data/places.json` | map places by name |
| `templates/` | `understanding.md`, `cards/_film.json`, `STATUS.md` |
| `projects/example-ww1-verdun/` | a complete worked example (understanding + cards → 70 % action) |
| `tools/cardlib/` | the compiler and the recipes (Python). Change recipes here, then `python tools/catalog.py --previews` |
| `src/` | the drawing engine (Remotion/React/SVG). Engine work: `.claude/skills/srt-history-video/references/` + `npx tsc --noEmit` |
| `docs/STYLE_GUIDE.md`, `docs/QUALITY.md` | what a good frame looks like; the definition of done |
