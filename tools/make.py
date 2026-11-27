"""One entry point for the whole pipeline.

python tools/make.py <project> prepare     inputs (SRT and/or voice) -> work/words.json, reading.md, understanding.md (step 1)
python tools/make.py <project> preview     cast, story places and drawings of cards/_film.json -> review/preview/sheet_*.jpg (before the cards)
                                           --kit every room/town style, --acts every act, --library every shared drawing
python tools/make.py <project> check       check the cards only (fast)
python tools/make.py <project> cards       cards/*.json -> plan.json + validate (step 4)
python tools/make.py <project> analyze     SRT + voice -> work/reading.md, stats.json (old name, part of prepare)
python tools/make.py <project> validate    merge plan -> work/plan.merged.json, check vocabulary/timing
python tools/make.py <project> review      stills of every scene -> review/sheet_*.jpg (look at them!)
python tools/make.py <project> audio       voice + ambience + SFX -> out/audio/mix.wav (+ stems)
python tools/make.py <project> video       render picture (muted) -> out/picture.mp4
python tools/make.py <project> mux         picture + mix -> out/<slug>.mp4
python tools/make.py <project> patch       after fixing some cards: re-render ONLY the changed scenes, splice, re-mux (--dry = list them)
python tools/make.py <project> prompts     youtube/thumb_prompts.json -> out/youtube/thumb_prompts.md (+ character reference sheet)
python tools/make.py <project> thumbs      thumbs.json -> out/thumbs/thumb_1..3 (engine draft, or headline composited on input/thumb_N.png)
python tools/make.py <project> package     youtube/package.json -> out/youtube/ (checks + publish.txt)
python tools/make.py <project> all         validate, audio, video, mux, thumbs, package
options: --from S --to S (partial video), --scenes s1,s2 (review subset)
"""
import json, subprocess, sys, shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PY = sys.executable


def run(cmd, **kw):
    print("$", " ".join(str(c) for c in cmd))
    r = subprocess.run([str(c) for c in cmd], cwd=ROOT, **kw)
    if r.returncode:
        sys.exit(r.returncode)


def node(*a):
    run(["node", ROOT / "tools" / "render.mjs", *a])


def main():
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    proj = Path(sys.argv[1]).resolve()
    step = sys.argv[2]
    rest = sys.argv[3:]
    opt = lambda k: rest[rest.index("--" + k) + 1] if "--" + k in rest else None
    merged = proj / "work" / "plan.merged.json"
    slug = proj.name

    def prepare():
        run([PY, ROOT / "tools/prepare.py", proj, *[r for r in rest if r in ("--align",)]])

    def cards():
        run([PY, ROOT / "tools/cards.py", proj])

    def check():
        run([PY, ROOT / "tools/cards.py", proj, "--check"])

    def analyze():
        run([PY, ROOT / "tools/srt_tool.py", proj])

    def validate():
        run([PY, ROOT / "tools/validate_plan.py", proj])

    def review():
        validate()
        d = proj / "review"
        if d.exists() and not opt("scenes"):
            # a full review replaces the scene stills and sheets; the pre-production sheets in review/preview and
            # review/assets (make.py preview, lib preview) stay
            for f in d.iterdir():
                if f.is_file():
                    f.unlink()
        for old in d.glob("sheet_*.jpg") if d.exists() else []:
            old.unlink()  # a partial review makes new sheets of the re-rendered scenes only: never leave stale sheets behind
        args = ["stills", merged, d, "--scale", "0.5", "--at", opt("at") or "mid"]
        if opt("scenes"):
            args += ["--scenes", opt("scenes")]
        node(*args)
        run([PY, ROOT / "tools/contact_sheet.py", d, "--per", "12"])

    def audio():
        validate()
        run([PY, ROOT / "tools/mix_audio.py", proj, "--plan", merged])

    def video():
        validate()
        (proj / "out").mkdir(exist_ok=True)
        args = ["video", merged, proj / "out" / "picture.mp4"]
        if opt("from"):
            args += ["--from", opt("from"), "--to", opt("to") or str(float(opt("from")) + 20)]
        if opt("concurrency"):
            args += ["--concurrency", opt("concurrency")]
        node(*args)
        if not opt("from"):
            # remember what was rendered: `patch` re-renders only the scenes that change after this
            shutil.copyfile(merged, proj / "out" / "plan.rendered.json")

    def preview():
        run([PY, ROOT / "tools/preview.py", proj, *[r for r in rest if r.startswith("--")]])

    def patch():
        validate()
        run([PY, ROOT / "tools/patch_video.py", proj, *[r for r in rest if r == "--dry"]])

    def mux():
        pic, mix = proj / "out" / "picture.mp4", proj / "out" / "audio" / "mix.wav"
        out = proj / "out" / f"{slug}.mp4"
        cmd = ["ffmpeg", "-v", "error", "-y", "-i", pic, "-i", mix, "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart"]
        if opt("from"):
            cmd += ["-ss", "0"]
        cmd += ["-shortest", out]
        run(cmd)
        print(json.dumps({"video": str(out)}))

    def thumbs():
        src = proj / "thumbs.json"
        if not src.exists():
            print("no thumbs.json — skipped")
            return
        data = json.loads(src.read_text(encoding="utf-8"))
        if "cast" not in data and merged.exists():
            data["cast"] = json.loads(merged.read_text(encoding="utf-8")).get("cast", {})
            tmp = proj / "work" / "thumbs.merged.json"
            tmp.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
            src = tmp
        # AI art dropped by the user (input/thumb_N.png|jpg|webp) becomes the background, the headline is composited on top
        data = json.loads(src.read_text(encoding="utf-8"))
        changed = False
        for i, th in enumerate(data.get("thumbs", []), 1):
            if not th.get("image"):
                for ext in ("png", "jpg", "jpeg", "webp"):
                    f = proj / "input" / f"thumb_{i}.{ext}"
                    if f.exists():
                        th["image"] = str(f)
                        th["grade"] = "none"
                        changed = True
                        break
        if changed:
            tmp = proj / "work" / "thumbs.image.json"
            tmp.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
            src = tmp
        node("thumb", src, proj / "out" / "thumbs", "--base", proj)
        # YouTube limit: < 2 MB -> also write high-quality JPGs
        for p in sorted((proj / "out" / "thumbs").glob("thumb_*.png")):
            run(["ffmpeg", "-v", "error", "-y", "-i", p, "-q:v", "2", p.with_suffix(".jpg")])

    def prompts():
        run([PY, ROOT / "tools/thumb_prompts.py", proj])
        refs = proj / "work" / "thumb_refs.json"
        if refs.exists() and json.loads(refs.read_text(encoding="utf-8")):
            cast = json.loads(merged.read_text(encoding="utf-8")).get("cast", {}) if merged.exists() else {}
            spec = proj / "work" / "thumb_refs.props.json"
            spec.write_text(json.dumps({"names": json.loads(refs.read_text(encoding="utf-8"))[:4], "cast": cast}), encoding="utf-8")
            (proj / "out" / "thumbs").mkdir(parents=True, exist_ok=True)
            node("refs", spec, proj / "out" / "thumbs" / "ref_characters.png")

    def package():
        run([PY, ROOT / "tools/seo_check.py", proj])

    steps = {"prepare": [prepare], "cards": [cards], "check": [check], "analyze": [analyze], "validate": [validate], "review": [review], "audio": [audio], "video": [video], "mux": [mux], "preview": [preview], "patch": [patch],
             "thumbs": [thumbs], "prompts": [prompts], "package": [package], "all": [audio, video, mux, prompts, thumbs, package]}
    if step not in steps:
        sys.exit(__doc__)
    for f in steps[step]:
        f()


if __name__ == "__main__":
    main()
