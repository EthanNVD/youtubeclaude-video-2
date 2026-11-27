# 02 — Understand the script (before ANY card)

Films go wrong when scenes are chosen from keywords. Every "attack" becomes the same picture, every number becomes a card, and the film turns into a slideshow. You avoid that by understanding the story first: who it happens to, where, and what each clause would look like on camera.

## 1. Read the whole narration

Open `work/reading.md` and read it from the first line to the last line. If it is long, read it in parts of about 300 lines, and keep going until the end. Do not start writing cards after reading only the beginning.

While reading, keep a scratch list of:
- **people**: every name, and who is "on screen" in each part;
- **places**: rooms, buildings, battlefields, towns;
- **anecdotes**: a story about one person on one day (these are the backbone of the film);
- **dates** and **time jumps**;
- **numbers**;
- **questions** the narrator asks out loud;
- **turns**: "but", "then", "by the end of…".

## 2. Fill in `understanding.md`

The file is already in your project (`prepare` copied it). Fill in every section.

**§1 The film in three lines.** These decide `era` and `sides` in `cards/_film.json`. The era is one of `ww1 ww2 napoleonic ancient vietnam modern`, and the side names come from `recipes/PEOPLE.md`.

**§2 People.**
- Give each person a short cast id and a `preset` from `recipes/PEOPLE.md`.
- If the exact person has no preset, use the closest one, e.g. `german_officer`, and change the look in the cast entry: `glasses`, `facial`, `age`…
- The name and role written here go on their name card.

**§3 Story arcs.** List the anecdotes. For each one: who it follows, where it happens, and whether the film comes back to it. Example: the Kaiser at Spa opens the film and the verdict returns to him. These arcs give the film its thread; most cards belong to one of them.

**§4 Story places.** Give every place that appears more than once:
- a `place_id`;
- one setting;
- one tag text, e.g. `"Spa, Belgium · 29 September 1918"`;
- the way it changes over time (dusk, then night; rain later; empty at the end).

The compiler keeps a place's setting and tag the same wherever its `place_id` is used.

**§5 Symbols and big questions.**
- **Symbols**: pick the objects that stand for the film's ideas (a watch for "two hours", a helmet on a rifle for the dead, a ridge facing Paris for the high-water mark). They can come back.
- **Big questions**: copy the exact words of the film's 2–4 questions. They become `caption`s over acted scenes.

**§6 Numbers.** Most numbers are **spoken only**: show the thing, and the voice gives the number. Mark at most one number every ~2 minutes as **stat** (read on screen), and mark numbers that are **compared** as **chart**.

**§7 Chapters.** Make 8–14 chapters of 1.5–4.5 minutes each. Start each at a sentence boundary, and note which arcs and places each chapter uses.

**§8 Beats.** Do this one chapter at a time, just before writing that chapter's cards.
- Write one line per clause, using the five questions of [narration-to-picture.md §1](narration-to-picture.md#1-the-picture-writing-method-do-this-for-every-clause): `time | first words | WHO | DOES WHAT | WHERE | WHEN | recipe`.
- Then check the lines:
  - Every line has a **visible action**. "Map of…", "text saying…" and "shows the number" are not actions.
  - No recipe appears on two lines in a row, unless it is the same place revisited.
  - At least 3 lines in 4 are acted recipes.
  - Each new place has a tag, and each first appearance of a person has a name card.

**§9 Fact flags.** List names the subtitles may have misspelled and claims the narration itself calls uncertain. Spell names correctly on screen.

## 3. Examples

- `projects/example-ww1-cold-open/understanding.md`: 60 s of WW1 told as a film (story places, acted beats).
- `projects/example-ww1-verdun/understanding.md`: 2 minutes of battle narration.

## Done when

Every section has content, and §8 is filled in for the chapter you are about to build. Tick "understand" in `STATUS.md`.

## The idea column (storyboard)

For every beat, after WHO / DOES WHAT / WHERE / WHEN, write the **idea**: one sentence of what the viewer sees and why that picture tells this clause. It becomes the card's `idea` field ([scene-writing.md](scene-writing.md) §1).

- Read the ideas of a whole chapter together before writing its cards. Two ideas that would look alike → change one: another person, another act, a detail, the consequence, the same place at another time.
- Stuck? Find the clause's situation in [visual-ideas.md](visual-ideas.md) (a number, a list, a decision, hunger, loss, news, a journey, memory) and take a device.

## Pre-production lists (§8b of the template)

While you understand the script, list everything the pictures need, one row each (kind · id · description · first used at):
- **people** (`person`): every kind of person who appears, named or not: the mother, the clerk, the admiral, a Malay villager;
- **costumes** (`costume`): what they wear that a preset does not have: a songkok, a turban, a sarong, a slouch hat;
- **story places** (`place`) with their tags; **buildings** (`building`) and **plants** (`plant`) of the region;
- **things** (`prop`) and **vehicles** (`vehicle`): a field kitchen, a parang, a bicycle people ride;
- **weather** (`weather`) and painted far backgrounds (`plate`) if the image path is used.

Then match the list against the living library: `python tools/lib.py match --project projects/<slug>` writes
`work/match.md` (use / adapt / create for every row). Make what is missing ([library.md](library.md)), then build the
`cast`, `sets` (and one-off `drawings`) of `cards/_film.json` and check them with
`python tools/make.py projects/<slug> preview` before writing cards.
