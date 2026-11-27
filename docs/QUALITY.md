# Quality — definition of done and review checklist

A video is **done** only when every box below is ticked. Copy this list into `projects/<slug>/STATUS.md` and tick it there.

## A. Before rendering (plan + stills)
- [ ] `validate`: 0 errors. Every warning was read; overlap and speed warnings are fixed, not ignored.
- [ ] `review` sheets inspected for **every** scene (not a sample) at start/mid/end where motion matters:
  - [ ] nothing overlaps: text on text, text on faces, signs on signs, badges on labels;
  - [ ] nothing floats: characters stand on the ground, seated people have a seat, vehicles touch the ground or water;
  - [ ] nothing is half off-frame unless it is meant to be (busts at the edges are fine; a cut-off label is not);
  - [ ] every named place on a map is inside the frame and labelled;
  - [ ] backgrounds and foregrounds scroll consistently (no static trees beside a moving road);
  - [ ] vehicles move at believable speeds and ease in and out;
  - [ ] a shot is never fully static: there is camera drift or an actor gesture;
  - [ ] ≥ 60 % acting shots, ≤ 20 % charts and documents, maps 15–25 %;
  - [ ] `cards` / validate `mix`: acted (action + talk) ≥ 75 % per chapter, maps ≤ 10 % (each ≤ 5 s), documents/charts ≤ 10 %; no chapter-mix warnings;
  - [ ] every clause has one concrete picture of what it says (sound-off test on the review sheets); story places keep their setting and tag; big questions are captions over acted scenes; no music;
  - [ ] battle scenes: bursts drawn behind the near men, nobody lying and walking, stretchers read, muzzle flashes at rifle tips, `impacts` on bursts (`.claude/skills/srt-history-video/references/action.md` §5);
  - [ ] validate `coverage`: average set-up ≤ 4 s, close-ups in every chapter, no `one set-up for …` or `crosses … px` (sprint) warnings;
  - [ ] every acting scene has a reaction close-up or an over-the-shoulder shot; evidence is shown as an insert, not a label;
  - [ ] each idea on screen appears on the word that names it.
- [ ] No hate symbols: armbands plain, no swastika banners; rally/podium banners show national flags.
- [ ] Fact flags from the outline are fixed on screen (spelling of names and places; numbers as narrated).
- [ ] Pre-production checked: `preview` sheets of the cast (children small, costume pieces on the head and body, not floating), every story place (flags, signs, season; rows join up; nothing big hides the middle) and every drawing (size next to a man).
- [ ] Library: `work/match.md` done (nothing that exists was made again); every new asset passed `lib check` (0 errors) and `lib preview`; riders sit on their bicycles with feet on the pedals.
- [ ] Scene cards: `cards` prints no repetition warning (look, idea, camera) and no staging warning (edge of frame, flag without a nation); `work/missing_assets.json` read.
- [ ] Review questions 17–23 of `playbook/05-review.md` pass for every scene: focus visible, held things clear of faces, writing readable and the right way round, flags right, children small, seats right, gestures on the word.

## B. Sound
- [ ] `audio` reports `sound_warnings: []`.
- [ ] Integrated loudness −14 LUFS ±0.5; true peak ≤ −1 dBTP.
- [ ] Listen to one busy minute and one quiet minute: SFX land on the contact frame; ambience ducks under the voice.

## C. Render
- [ ] Only one render process at a time.
- [ ] The final MP4 lasts as long as the voice (±0.5 s): 1920×1080, H.264 + AAC.
- [ ] Spot-check 12 frames spread over the film plus motion strips (8 fps) of:
  - a walk-in;
  - a vehicle arriving and braking;
  - a pose change;
  - a prop put down;
  - a map move.
  Check for no jumps, no stops without slowing, no sliding feet, nothing popping in from nothing.

## D. Package
- [ ] 3 titles on three different angles; recommended one marked; 40–65 characters.
- [ ] Description: chapters valid (start 0:00, ≥ 10 s each), no `<` or `>`, sources only if real.
- [ ] Tags ≤ 500 characters; 3–4 hashtags.
- [ ] Thumbnail prompts: 3 layouts; exact headline of ≤ 5 words; reference sheet attached; drafts checked at 25 % size.

## E. Hand-off
- [ ] `projects/<slug>/STATUS.md` updated: what was delivered, known weaknesses, what to verify.
- [ ] Engine problems found during this video logged in `ROADMAP.md` → Known issues.
- [ ] Story places worth keeping saved (`lib place`), new assets promoted (`lib promote`): `library/INDEX.md` lists them with previews.
- [ ] Repo committed and pushed. No media committed.
