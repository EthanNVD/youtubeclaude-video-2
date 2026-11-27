"""Stagecraft vocabulary for the `scene` card (tools/cardlib/recipes_scene.py).

Everything a writer may name in a `scene` card is defined here, with a one-line doc that tools/catalog.py turns into
recipes/STAGECRAFT.md. Keep entries concrete: what the viewer SEES.

  WHERE   ROOM_STYLES / TOWN_STYLES (src/sets/Kit.tsx) or any set of the engine; story places live in _film.json "sets"
  WHO     people: a cast id or a preset, at a SLOT and a DEPTH, facing someone, in a MOOD
  DOES    ACTS (gestures, business, moves, reactions), each on a phrase of the narration
  WITH    THINGS (props on the floor, on a table, in a hand) and EFFECTS
  CAMERA  CAMERAS presets (or a list of shots)
"""
from __future__ import annotations

# ------------------------------------------------------------------ where people stand
SLOTS = {"far_left": 230, "left": 470, "center_left": 720, "center": 960, "center_right": 1200, "right": 1450, "far_right": 1690,
         "off_left": -260, "off_right": 2180}
SLOT_DOC = "far_left · left · center_left · center · center_right · right · far_right (or a number of px, 0-1920); off_left / off_right = outside the frame (for enter/exit)"
DEPTHS = {"front": 1015, "near": 965, "mid": 915, "back": 860, "far": 815}
DEPTH_DOC = "front (big, close to the lens) · near · mid (default) · back · far (small, against the back wall / the facades)"

# world (depth model) per kind of place: a person whose feet are at y is scaled scale*(y-horizon)/(915-horizon)
WORLDS = {"room": {"scale": 1.7, "y": 915, "horizon": 520}, "town": {"scale": 1.0, "y": 915, "horizon": 560},
          "set": {"scale": 1.15, "y": 915}, "compose": {"scale": 1.0, "y": 915, "horizon": 560}}

# ------------------------------------------------------------------ composed places (any region): layers, far to near
COMPOSE_FAR = {"hills": "soft rolling hills", "mountains": "blue mountain peaks", "jungle": "a dark wall of jungle canopy on the horizon",
               "treeline": "a light line of trees", "palms": "palm silhouettes", "sea": "the sea on the horizon", "town": "far roofs", "none": "nothing"}
COMPOSE_GROUND = {"grass": "green grass", "laterite": "red tropical earth", "sand": "sand (beach, desert)", "paddy": "rice fields with water",
                  "mud": "brown mud", "dry": "dry yellow grass (savanna, steppe)", "jungle_floor": "dark green undergrowth", "snow": "snow"}
COMPOSE_ROADS = {"laterite": "red earth road", "dirt": "dirt road", "tarmac": "tarred road", "cobbles": "cobbled road", "sand": "sand track"}

# ------------------------------------------------------------------ moods: base face + the gestures people make
MOODS = {
    # mood: (expression, gestures while TALKING, while LISTENING, while just being there)
    "neutral": ("neutral", ["talk", "explain", "present", "palms", "count"], ["idle", "cross", "behind", "chin"], ["idle", "behind", "hips", "pockets"]),
    "worried": ("worried", ["wring", "palms", "talk", "heart", "explain"], ["wring", "idle", "chin", "cross"], ["wring", "wait", "idle", "cross"]),
    "sad": ("sad", ["heart", "palms", "talk"], ["wait", "idle", "heart"], ["wait", "idle", "heart"]),
    "grief": ("sad", ["heart", "palms"], ["pray", "wait"], ["pray", "wait", "idle"]),
    "angry": ("angry", ["fist", "point", "explain", "slam", "talk"], ["cross", "hips", "fist"], ["hips", "cross", "fist"]),
    "determined": ("determined", ["point", "fist", "present", "explain", "talk"], ["cross", "behind", "hips"], ["behind", "hips", "idle"]),
    "proud": ("smug", ["present", "point", "explain", "talk"], ["behind", "hips", "cross"], ["behind", "hips"]),
    "happy": ("happy", ["talk", "present", "palms", "explain", "clap"], ["idle", "clap", "hips"], ["idle", "hips", "pockets"]),
    "tired": ("tired", ["palms", "talk", "heart"], ["idle", "wait"], ["idle", "wait", "wipe"]),
    "hungry": ("tired", ["palms", "talk"], ["wait", "idle"], ["wait", "idle", "wring"]),
    "cold": ("worried", ["talk", "palms"], ["shiver", "idle"], ["shiver", "rub", "idle"]),
    "shocked": ("shocked", ["palms", "gasp", "talk"], ["gasp", "idle"], ["idle", "gasp"]),
    "fear": ("panic", ["palms", "gasp"], ["cower", "gasp"], ["wring", "gasp", "idle"]),
    "smug": ("smug", ["present", "explain", "talk", "point"], ["cross", "hips", "behind"], ["hips", "behind", "cross"]),
    "nervous": ("nervous", ["wring", "talk", "palms"], ["wring", "idle"], ["wring", "rub", "idle"]),
}
MOOD_DOC = "the person's inner state: sets the face AND which gestures they make while talking, listening or waiting"

# ------------------------------------------------------------------ acts: what a person DOES (on a phrase)
# kind: pose = a held gesture/business (cyc = it keeps moving: stirring, writing…), move = changes place,
#       special = handled by the compiler (talk, head moves, facing, sitting, falling, giving)
A = lambda pose, doc, **kw: {"kind": "pose", "pose": pose, "doc": doc, **kw}  # noqa: E731
ACTS = {
    # --- everyday business (keeps going until the next act)
    "stir": A("stir", "stirs a pot (put a pot thing in front, on a stove or table)", holds="spoon", cyc=True, sfx=("metal_clank", 0.25)),
    "ladle": A("ladle", "ladles soup out of a pot", holds="spoon", cyc=True, sfx=("metal_clank", 0.25)),
    "eat": A("eat", "eats with a spoon, slowly (hungry: mood hungry)", holds="spoon", cyc=True),
    "drink": A("drink", "drinks from a cup", holds="cup"),
    "peel": A("peel", "peels / cuts something small (a turnip, a potato)", holds="knife", cyc=True),
    "knock": A("knock", "knocks on a door", cyc=True, sfx=("thud", 0.5)),
    "hammer": A("hammer", "hammers (worker, builder)", cyc=True, sfx=("metal_clank", 0.45)),
    "write": A("write", "writes at a desk", holds="pen", cyc=True, sfx=("pen", 0.5)),
    "type": A("typing", "types on a typewriter", cyc=True, sfx=("typewriter", 0.5)),
    "read": A("read", "reads a letter/paper held in both hands (with: letter | paper | telegram | newspaper | card)", holds="paper", cyc=True, sfx=("paper", 0.4)),
    "count": A("count", "counts (coins, cards, men) with a pointing finger", cyc=True),
    "phone": A("phone", "talks on a telephone", holds="phone"),
    "smoke": A("smoke", "smokes a cigar / pipe", holds="cigar"),
    "pray": A("pray", "prays, hands together, head bowed", expr="sad"),
    "cry": A("cry", "cries into the hands", expr="cry"),
    "wring_hands": A("wring", "wrings the hands (worry, waiting for news)", expr="worried"),
    "warm_hands": A("warm", "holds the hands out to a stove or fire", cyc=True),
    "shiver": A("shiver", "hugs himself and shivers with cold", expr="worried"),
    "rub_hands": A("rub", "rubs the hands (cold, or greed)"),
    "wait": A("wait", "waits, hands clasped in front (a queue)"),
    "hold": A("hold", "holds a thing in front of the chest (with: thing)"),
    "hold_up": A("holdUp", "holds a thing up for all to see (with: thing)"),
    "show": A("show", "shows a thing to someone (with: thing)"),
    "carry": A("carry", "carries a box / crate in both arms (with: crate)", holds="crate"),
    "carry_sack": A("sack", "carries a sack on the shoulder", holds="sack"),
    "carry_basket": A("basket", "carries a basket on the arm (with: basket)", holds="basket"),
    "cradle": A("cradle", "holds a baby in the arms", holds="baby"),
    "reach_up": A("reachup", "reaches up to a high shelf"),
    "lean": A("lean", "leans on a table with both hands"),
    "push": A("push", "pushes something heavy (a cart, a door)"),
    "pull": A("pull", "pulls a rope / a cart"),
    "listen": A("listen", "cups a hand to the ear, listening"),
    "tip_hat": A("tiphat", "touches the hat brim (greeting)"),
    "binoculars": A("binoculars", "looks through binoculars", holds="binoculars"),
    "dig": A("dig", "digs with a shovel (a trench, a gun pit, a grave)", holds="shovel", cyc=True, sfx=("thud", 0.3)),
    # --- gestures (usually with talking, or a reaction)
    "point": A("point", "points at someone/something (to: id)"),
    "point_down": A("pointdown", "points down at a table / map"),
    "beckon": A("beckon", "waves someone to come closer"),
    "explain": A("explain", "explains with an open hand"),
    "present": A("present", "presents with an open hand (\"here it is\")"),
    "palms": A("palms", "both palms up: \"what can we do?\""),
    "shrug": A("shrug", "shrugs"),
    "think": A("chin", "hand to chin, thinking"),
    "ponder": A("think", "finger to the temple, pondering"),
    "despair": A("head", "hands on the head in despair", expr="sad"),
    "facepalm": A("facepalm", "hand over the face", expr="tired"),
    "gasp": A("gasp", "hand over the mouth, shocked", expr="shocked"),
    "hand_on_heart": A("heart", "hand on the heart (sincere, moved, grieving)"),
    "comfort": A("comfort", "lays a hand on someone's shoulder (to: id; stand next to them)", expr="sad"),
    "fist": A("fist", "raises both fists (anger, triumph)", expr="angry"),
    "slam": A("slam", "slams the fist down on the table", expr="angry", sfx=("thud", 0.8)),
    "arms_crossed": A("cross", "folds the arms"),
    "hands_behind": A("behind", "hands behind the back (officers, waiting)"),
    "hands_on_hips": A("hips", "hands on the hips"),
    "pockets": A("pockets", "hands in the pockets"),
    "scratch_head": A("scratch", "scratches the head (puzzled)"),
    "wipe_brow": A("wipe", "wipes the brow (heat, relief, effort)", expr="tired"),
    "clap": A("clap", "claps", expr="happy"),
    "cheer": A("cheer", "cheers with raised fists", expr="happy", sfx=("cheer", 0.35)),
    "wave": A("wave", "waves", expr="smile"),
    "salute": A("salute", "salutes", expr="determined"),
    "stop": A("stop", "raises a hand: halt!"),
    "beg": A("beg", "begs with clasped hands", expr="sad"),
    "surrender": A("surrender", "hands up, surrenders", expr="panic"),
    "cower": A("cower", "cowers, arms over the head", expr="panic"),
    "thumbs_up": A("thumbsup", "thumbs up", expr="smile"),
    "give": {"kind": "special", "doc": "hands a thing to someone (to: id, with: thing): the thing changes hands"},
    "take": A("reach", "reaches out to take something"),
    # --- soldiers
    "aim": A("aim", "aims a rifle", holds="rifle"),
    "fire": {"kind": "special", "doc": "aims and fires a rifle (shots on the phrase)", "pose": "aim", "holds": "rifle"},
    "port_arms": A("port", "holds the rifle across the body", holds="rifle"),
    "shoulder_arms": A("shoulder", "rifle on the shoulder", holds="rifle"),
    # --- talking, faces, heads
    "say": {"kind": "special", "doc": "talks (mouth moves) from `on` to `till` with gestures from the mood (depicted speech, not the narrator)"},
    "react": {"kind": "special", "doc": "the face changes (expr: shocked | sad | angry | happy | worried | panic | …) — the take is automatic"},
    "nod": {"kind": "special", "doc": "nods"},
    "shake_head": {"kind": "special", "doc": "shakes the head (no)"},
    "laugh": {"kind": "special", "doc": "laughs", "expr": "laugh"},
    "shout": {"kind": "special", "doc": "shouts (mouth open, points)", "expr": "shout", "pose": "point"},
    "sigh": {"kind": "special", "doc": "sighs, the shoulders drop", "expr": "tired", "pose": "idle"},
    "freeze": {"kind": "special", "doc": "stops dead, stunned", "expr": "shocked", "pose": "idle"},
    "look_up": {"kind": "special", "doc": "stops what he is doing and looks up (at the camera / at the news)", "expr": "worried", "pose": "idle"},
    "look_at": {"kind": "special", "doc": "turns the head and eyes to someone (to: id)"},
    "look_away": {"kind": "special", "doc": "looks away from someone (shame, refusal)"},
    "look_around": {"kind": "special", "doc": "looks left and right (searching, unsure)"},
    "look_down": {"kind": "special", "doc": "lowers the head (shame, grief)", "expr": "sad"},
    # --- facing and body
    "turn_away": {"kind": "special", "doc": "turns the back to us (to the window, to the wall)"},
    "turn_back": {"kind": "special", "doc": "turns round to face us again"},
    "turn_to": {"kind": "special", "doc": "turns toward someone (to: id) or a side (to: left | right)"},
    "sit": {"kind": "special", "doc": "sits down on a chair (a chair is added)"},
    "stand_up": {"kind": "special", "doc": "stands up from the chair"},
    "kneel": {"kind": "special", "doc": "kneels"},
    "rise": {"kind": "special", "doc": "gets up from kneeling"},
    "fall": {"kind": "special", "doc": "falls (hit, fainting); stays down"},
    # --- moves
    "walk_to": {"kind": "move", "doc": "walks to a slot or a person (to: slot | id | px)"},
    "run_to": {"kind": "move", "doc": "runs to a slot or a person", "speed": 520},
    "shuffle_to": {"kind": "move", "doc": "shuffles slowly (hungry, exhausted)", "speed": 90, "style": "shuffle"},
    "march_to": {"kind": "move", "doc": "marches (parade step)", "speed": 210, "style": "march"},
    "limp_to": {"kind": "move", "doc": "limps (wounded)", "speed": 110, "style": "limp"},
    "enter": {"kind": "move", "doc": "walks in from outside the frame on the phrase (from: left | right; to: slot or person; default: their own `at`)"},
    "exit": {"kind": "move", "doc": "walks out of the frame (to: left | right)"},
}
BUSY = {k for k, v in ACTS.items() if v.get("cyc")} | {"wait", "hold", "carry", "carry_sack", "carry_basket", "cradle", "binoculars", "aim", "phone", "smoke", "pray", "cry", "shiver", "lean"}

# ------------------------------------------------------------------ crowds
CROWDS = {
    "queue": "a line of people waiting at a door/counter, facing it; the line shuffles forward now and then (toward: left | right)",
    "watchers": "people standing, watching the focus person or a point (they react on `react_on`)",
    "walkers": "passers-by crossing the frame at different depths and speeds",
    "marchers": "a column marching across (soldiers): `who` a soldier preset",
    "mourners": "people with heads bowed, praying, crying",
    "cheering": "people cheering, clapping, waving",
    "workers": "people working (hammer, carry crates, push carts)",
    "protest": "angry people shouting, fists up",
    "listeners": "people facing a speaker (a meeting, a sermon, a lecture); add \"view\": \"back\" when they stand between us and the speaker",
    "cyclists": "people riding bicycles across the frame, 3-4 abreast in rows (\"abreast\": 3, \"vehicle\": \"bicycle\", \"toward\": \"left|right\"; \"start\": \"in\" = already in the frame at \"at\", for short shots), chatting",
}

# ------------------------------------------------------------------ things (engine props) and their sizes
# size = scale relative to a person at the same depth; top = height (prop units) of the surface other things stand on
THINGS = {
    "table": {"size": 1.0, "top": 120}, "counter": {"size": 1.0, "top": 126}, "stove": {"size": 1.0, "top": 160}, "chair": {"size": 1.0},
    "stool": {"size": 1.0}, "bench": {"size": 1.0, "top": 62}, "crate": {"size": 1.0, "top": 100}, "barrel": {"size": 1.0, "top": 140},
    "cart": {"size": 1.0}, "sack": {"size": 0.9}, "bale": {"size": 0.9, "top": 120}, "ingots": {"size": 0.8}, "bucket": {"size": 0.8},
    "pot": {"size": 0.55}, "bowl": {"size": 0.38}, "plate": {"size": 0.4}, "bread": {"size": 0.45}, "cup": {"size": 0.38}, "bottle": {"size": 0.4},
    "jug": {"size": 0.45}, "basket": {"size": 0.6}, "turnip": {"size": 0.35}, "turnips": {"size": 0.55}, "potatoes": {"size": 0.55},
    "card": {"size": 0.35}, "letter": {"size": 0.35}, "paper": {"size": 0.4}, "telegram": {"size": 0.35}, "coins": {"size": 0.35},
    "candle": {"size": 0.4}, "lantern": {"size": 0.45}, "scale": {"size": 0.6}, "knife": {"size": 0.4}, "spoon": {"size": 0.4},
    "radio": {"size": 0.6}, "typewriter": {"size": 0.6}, "phone": {"size": 0.45}, "helmet": {"size": 0.45}, "book": {"size": 0.4},
    "ledger": {"size": 0.45}, "suitcase": {"size": 0.6}, "clock": {"size": 0.5}, "globe": {"size": 0.6}, "photo": {"size": 0.4},
    "medal": {"size": 0.3}, "baby": {"size": 0.5}, "flag": {"size": 1.0}, "oil": {"size": 0.9}, "shell": {"size": 0.6},
}
THING_DOC = {
    "table": "kitchen / office table (people stand or sit behind it)", "counter": "shop counter (shopkeeper behind, customers in front)",
    "stove": "iron stove with a flue (glows; on: false = cold)", "turnips": "a heap of turnips (n = how many)", "potatoes": "a heap of potatoes (color dark = rotten)",
    "card": "ration card (text: BROTKARTE…)", "bale": "bound bale (text: COTTON, WOOL…)", "ingots": "copper / metal bars", "sack": "grain sack (text: MEHL…)",
    "cart": "hand cart (n: 1 = loaded with sacks)", "bowl": "bowl (on: true = steaming, n: 0 = empty)", "pot": "cooking pot (steams)",
}

# ------------------------------------------------------------------ effects
EFFECTS = {
    "smoke": "a column of smoke", "fire": "flames", "explosion": "a big explosion", "shellburst": "a shell bursting in the ground",
    "impact": "a hit / spark", "dust": "dust kicked up", "splash": "water splash", "sparks": "sparks (workshop, fire)", "flash": "a flash of light",
    "searchlight": "a searchlight beam", "steam": "steam / breath (small smoke)", "exclaim": "a ! over someone's head (over: id) — a realisation",
    "question": "a ? over someone's head (over: id) — puzzlement",
}

# ------------------------------------------------------------------ camera
CAMERAS = {
    "wide": "the whole place with a slow push — for an establishing shot or a group",
    "push_in": "starts wide and pushes in slowly all through the scene (tension, realisation)",
    "pan": "drifts sideways across the place (a street, a queue, a row of beds)",
    "wide_then_close": "wide, then dissolves to the focus person (on `close_on`) — the default for a moment that lands on one face",
    "close_then_wide": "starts on the focus (a face, a thing) and dissolves out to the whole place on `wide_on` — a reveal",
    "detail_then_wide": "starts on a thing (detail: id), then reveals the people around it",
    "medium": "waist-up on the focus person all through (a confession, a decision)",
    "close": "a close-up of the focus face (a reaction, grief)",
    "two_shot": "two people together (focus + partner)",
    "group": "everybody in the scene, framed tight",
    "follow": "follows the focus person as they walk",
    "over_shoulder": "over the shoulder of `partner` onto the focus person (a dialogue, an interrogation)",
}
