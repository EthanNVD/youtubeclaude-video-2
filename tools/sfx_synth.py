"""Procedural, royalty-free SFX + ambience library (48 kHz mono WAV) -> assets/sfx/<id>.wav

python tools/sfx_synth.py            # build all
python tools/sfx_synth.py stamp pop  # build some

Real recordings (CC0 / licensed) dropped into assets/sfx/ with the same id override these:
the mixer simply loads assets/sfx/<id>.wav.  Ambience ids are loopable beds (>= 20 s).
"""
import sys, wave
from pathlib import Path
import numpy as np
from scipy import signal

SR = 48000
OUT = Path(__file__).resolve().parent.parent / "assets" / "sfx"
rng = np.random.default_rng(42)


def t_(d):
    return np.arange(int(d * SR)) / SR


def noise(d, color="white"):
    n = rng.standard_normal(int(d * SR))
    if color == "pink":
        b, a = [0.049922035, -0.095993537, 0.050612699, -0.004408786], [1, -2.494956002, 2.017265875, -0.522189400]
        n = signal.lfilter(b, a, n) * 6
    elif color == "brown":
        n = np.cumsum(n) / 60
        n = signal.lfilter([1, -1], [1, -0.995], n)
    return n


def bp(x, lo, hi, order=2):
    sos = signal.butter(order, [lo / (SR / 2), min(hi, SR / 2 - 100) / (SR / 2)], "band", output="sos")
    return signal.sosfilt(sos, x)


def lp(x, f, order=2):
    return signal.sosfilt(signal.butter(order, f / (SR / 2), "low", output="sos"), x)


def hp(x, f, order=2):
    return signal.sosfilt(signal.butter(order, f / (SR / 2), "high", output="sos"), x)


def env_exp(d, decay, attack=0.002):
    t = t_(d)
    e = np.exp(-t / decay)
    a = np.minimum(1, t / max(attack, 1e-4))
    return e * a


def adsr(n, a, r):
    e = np.ones(n)
    ai, ri = int(a * SR), int(r * SR)
    if ai:
        e[:ai] = np.linspace(0, 1, ai)
    if ri:
        e[-ri:] *= np.linspace(1, 0, ri)
    return e


def place(dst, src, at):
    i = int(at * SR)
    if i >= len(dst):
        return
    n = min(len(src), len(dst) - i)
    dst[i:i + n] += src[:n]


def reverb(x, size=0.6, wet=0.25):
    ir_len = int(size * SR)
    ir = rng.standard_normal(ir_len) * np.exp(-np.arange(ir_len) / (ir_len / 5))
    ir = lp(ir, 5000)
    ir /= np.abs(ir).sum() ** 0.5 * 4
    y = signal.fftconvolve(x, ir)[: len(x) + ir_len]
    out = np.zeros(len(y))
    out[: len(x)] += x * (1 - wet)
    return out + y * wet


def norm(x, peak=0.9):
    m = np.max(np.abs(x)) or 1
    return x / m * peak


def loopable(x, fade=1.0):
    """crossfade end into start so the bed loops seamlessly"""
    n = int(fade * SR)
    a, b = x[:n].copy(), x[-n:]
    w = np.linspace(0, 1, n)
    x = x[:-n].copy()
    x[:n] = a * w + b * (1 - w)
    return x


# ---------------- one-shots ----------------
def whoosh(d=0.9, lo=300, hi=3000, peak=0.55):
    n = noise(d, "pink")
    t = t_(d)
    f = lo + (hi - lo) * np.sin(np.pi * t / d) ** 2
    out = np.zeros_like(n)
    # time-varying bandpass via short blocks
    blk = 1024
    for i in range(0, len(n), blk):
        c = f[min(i + blk // 2, len(f) - 1)]
        seg = n[max(0, i - 2048): i + blk]
        y = bp(seg, max(80, c * 0.5), c * 1.6)
        out[i:i + blk] = y[-len(n[i:i + blk]):]
    e = np.sin(np.pi * np.clip(t / d, 0, 1)) ** 1.6
    return norm(out * e, peak)


def pop():
    t = t_(0.12)
    f = 900 * np.exp(-t * 30) + 380
    x = np.sin(2 * np.pi * np.cumsum(f) / SR) * env_exp(0.12, 0.03)
    return norm(x, 0.5)


def stamp():
    d = 0.6
    t = t_(d)
    thump = np.sin(2 * np.pi * (70 + 60 * np.exp(-t * 30)) * t) * env_exp(d, 0.08)
    slap = hp(noise(d), 800) * env_exp(d, 0.012)
    wood = bp(noise(d), 180, 900) * env_exp(d, 0.05)
    return norm(reverb(thump * 1.0 + slap * 0.5 + wood * 0.6, 0.35, 0.15), 0.95)


def thud():
    d = 0.5
    t = t_(d)
    return norm(np.sin(2 * np.pi * (55 + 40 * np.exp(-t * 25)) * t) * env_exp(d, 0.09) + lp(noise(d), 400) * env_exp(d, 0.03) * 0.5, 0.9)


def paper():
    d = 0.8
    x = np.zeros(int(d * SR))
    for k in range(14):
        at = rng.uniform(0, d - 0.08)
        burst = hp(noise(0.06), 1500) * env_exp(0.06, 0.012) * rng.uniform(0.3, 1)
        place(x, burst, at)
    x += bp(noise(d), 2000, 8000) * adsr(len(x), 0.1, 0.4) * 0.15
    return norm(x, 0.5)


def scribble(d=1.5, chalk=False):
    n = noise(d)
    x = bp(n, 1800, 7000) if not chalk else bp(n, 900, 5000)
    t = t_(d)
    am = np.abs(np.sin(2 * np.pi * (5 + 2 * np.sin(t * 3)) * t)) ** 0.6
    am *= (rng.random(len(t)) > 0.002).astype(float)
    x = x * am * adsr(len(x), 0.03, 0.08)
    if chalk:
        x += np.sin(2 * np.pi * 2400 * t) * am * 0.04
    return norm(x, 0.45)


def click(f=3000, d=0.03):
    return bp(noise(d), f * 0.6, f * 1.6) * env_exp(d, 0.004)


def typewriter(d=3.0):
    x = np.zeros(int(d * SR))
    at = 0.0
    while at < d - 0.1:
        k = click(rng.uniform(1800, 3500), 0.05) * rng.uniform(0.5, 1)
        k += lp(noise(0.05), 600) * env_exp(0.05, 0.01) * 0.6
        place(x, k, at)
        at += rng.uniform(0.07, 0.16)
    return norm(reverb(x, 0.2, 0.1), 0.6)


def bell(f=2200, d=1.2):
    t = t_(d)
    x = sum(np.sin(2 * np.pi * f * m * t) * np.exp(-t * (2 + m)) / m for m in (1, 2.76, 5.4))
    return norm(x * env_exp(d, 0.4), 0.5)


def clock_tick(d=3.0):
    x = np.zeros(int(d * SR))
    for i in range(int(d)):
        place(x, click(4200, 0.02) * 0.9, i)
        place(x, click(3000, 0.02) * 0.6, i + 0.5)
    return norm(reverb(x, 0.25, 0.2), 0.45)


def explosion(d=3.0, big=False, distant=False):
    t = t_(d)
    n = noise(d, "brown") * 8 + noise(d, "pink") * 0.6
    body = lp(n, 900 if not distant else 300) * env_exp(d, 0.5 if big else 0.32, 0.004)
    crack = hp(noise(d), 1500) * env_exp(d, 0.03) * (0 if distant else 0.8)
    sub = np.sin(2 * np.pi * (45 + 30 * np.exp(-t * 6)) * t) * env_exp(d, 0.45 if big else 0.3)
    debris = np.zeros(len(t))
    if not distant:
        for k in range(25):
            place(debris, click(rng.uniform(800, 3000), 0.04) * rng.uniform(0.05, 0.25), rng.uniform(0.2, d * 0.7))
    x = body + crack + sub * 1.2 + debris
    return norm(reverb(x, 0.9, 0.3), 0.98 if not distant else 0.5)


def gunshot(d=0.6, heavy=False):
    t = t_(d)
    x = hp(noise(d), 300) * env_exp(d, 0.03 if not heavy else 0.08) + lp(noise(d, "brown") * 6, 500) * env_exp(d, 0.12)
    x += np.sin(2 * np.pi * 90 * t) * env_exp(d, 0.06) * 0.6
    return norm(reverb(x, 0.6, 0.25), 0.9)


def machinegun(d=1.6, rate=12):
    x = np.zeros(int(d * SR))
    for i in range(int(d * rate)):
        place(x, gunshot(0.25) * rng.uniform(0.6, 1), i / rate + rng.uniform(0, 0.01))
    return norm(x, 0.85)


def artillery(d=3.5):
    x = explosion(d, big=True) * 0.7
    place(x, gunshot(0.8, True) * 0.9, 0)
    return norm(x, 0.95)


def engine(d, f0=38, harm=6, rough=0.3, prop=False):
    t = t_(d)
    wob = 1 + 0.02 * np.sin(2 * np.pi * 0.7 * t) + 0.01 * np.sin(2 * np.pi * 3.1 * t)
    ph = 2 * np.pi * np.cumsum(f0 * wob) / SR
    x = sum(np.sin(ph * k + k) / k ** 0.9 for k in range(1, harm + 1))
    x += lp(noise(d), 400) * rough
    if prop:
        x *= 1 + 0.35 * np.sin(ph * 3)
    return x


def plane_flyby(d=4.0):
    t = t_(d)
    k = (t - d / 2) / (d / 2)
    f0 = 95 * (1 - 0.18 * np.tanh(k * 2))
    ph = 2 * np.pi * np.cumsum(f0) / SR
    x = sum(np.sin(ph * m) / m for m in range(1, 8)) * (1 + 0.3 * np.sin(ph * 3))
    x += bp(noise(d, "pink"), 300, 3000) * 0.5
    e = 1 / (1 + (k * 2.2) ** 2)
    return norm(x * e, 0.8)


def plane_dive(d=4.0):
    t = t_(d)
    f = 400 + 900 * (t / d) ** 1.5
    whine = np.sin(2 * np.pi * np.cumsum(f) / SR) * 0.35
    eng = engine(d, 70 + 50 * 0, 7, 0.4, True) * 0.5
    air = bp(noise(d), 800, 5000) * (t / d) * 0.6
    return norm((whine + eng + air) * np.minimum(1, t / 0.5) * adsr(len(t), 0.2, 0.3), 0.8)


def splash(d=1.5):
    x = bp(noise(d, "pink"), 200, 6000) * env_exp(d, 0.35, 0.01)
    x += lp(noise(d, "brown") * 5, 300) * env_exp(d, 0.2)
    return norm(reverb(x, 0.4, 0.2), 0.8)


def phone_ring(d=2.4):
    t = t_(d)
    x = np.zeros(len(t))
    for start in (0, 1.2):
        seg = t_(0.9)
        r = np.sign(np.sin(2 * np.pi * 20 * seg)) * 0.5 + 0.5
        tone = (np.sin(2 * np.pi * 1100 * seg) + 0.6 * np.sin(2 * np.pi * 1400 * seg)) * r * np.exp(-((seg * 3) % 1) * 2)
        place(x, tone * adsr(len(seg), 0.01, 0.05), start)
    return norm(reverb(x, 0.4, 0.2), 0.5)


def morse(d=2.5):
    t = t_(d)
    gate = np.zeros(len(t))
    at = 0.0
    while at < d - 0.2:
        ln = rng.choice([0.06, 0.18])
        gate[int(at * SR):int((at + ln) * SR)] = 1
        at += ln + 0.06 + (0.18 if rng.random() < 0.25 else 0)
    gate = lp(gate, 200)
    return norm(np.sin(2 * np.pi * 700 * t) * gate, 0.4)


def radio_static(d=2.0):
    x = bp(noise(d), 800, 6000) * (0.6 + 0.4 * np.sin(2 * np.pi * 7 * t_(d)))
    return norm(x * adsr(len(x), 0.05, 0.2), 0.3)


def metal_clank():
    d = 0.9
    t = t_(d)
    x = sum(np.sin(2 * np.pi * f * t) * np.exp(-t * dcy) for f, dcy in ((420, 6), (1130, 9), (2310, 14), (3570, 20)))
    x += hp(noise(d), 2000) * env_exp(d, 0.01)
    return norm(x, 0.6)


def footsteps(d=2.0, rate=2.0, surface="hard"):
    x = np.zeros(int(d * SR))
    for i in range(int(d * rate)):
        s = lp(noise(0.12), 1200 if surface == "hard" else 600) * env_exp(0.12, 0.025)
        if surface == "snow":
            s = bp(noise(0.2), 400, 3000) * env_exp(0.2, 0.06)
        place(x, s * rng.uniform(0.6, 1), i / rate)
    return norm(x, 0.5)


def bicycle(d=4.0, bell_at=0.6):
    """bicycles going by: tyres on a road (soft hiss), the chain, freewheels ticking, one ring of a bell"""
    n = int(d * SR)
    x = bp(noise(d, "pink"), 600, 2400) * 0.18
    x += bp(noise(d), 2500, 6000) * 0.05 * (1 + np.sin(t_(d) * 2 * np.pi * 1.1)) / 2
    for i in range(int(d * 9)):
        place(x, click(4200, 0.012) * rng.uniform(0.15, 0.3), i / 9 + rng.uniform(0, 0.02))
    if bell_at is not None and bell_at < d - 0.6:
        place(x, bell(2600, 0.9) * 0.5, bell_at)
        place(x, bell(2600, 0.9) * 0.4, bell_at + 0.22)
    return norm(x * adsr(n, 0.4, 0.6), 0.5)


def heartbeat(d=2.0):
    x = np.zeros(int(d * SR))
    for i in range(int(d / 0.9)):
        for off, a in ((0, 1), (0.22, 0.7)):
            s = np.sin(2 * np.pi * 50 * t_(0.15)) * env_exp(0.15, 0.04)
            place(x, s * a, i * 0.9 + off)
    return norm(x, 0.7)


def riser(d=2.5):
    t = t_(d)
    x = whoosh(d, 200, 6000, 1.0) * (t / d) ** 2
    return norm(x, 0.5)


def impact_hit():
    x = thud() * 0.8
    place(x, whoosh(0.4, 500, 4000, 0.4) * 0.3, 0)
    return norm(reverb(x, 0.8, 0.3), 0.9)


def cash():
    x = np.zeros(int(1.0 * SR))
    for k in range(8):
        place(x, bell(rng.uniform(3000, 5000), 0.3) * 0.4, rng.uniform(0, 0.4))
    return norm(x, 0.5)


def ship_horn(d=2.5):
    t = t_(d)
    x = sum(np.sin(2 * np.pi * f * t) for f in (110, 165, 220, 330)) * adsr(len(t), 0.15, 0.5)
    return norm(reverb(x, 1.0, 0.35), 0.6)


def crowd_cheer(d=3.0):
    x = sum(bp(noise(d, "pink"), f, f * 1.8) * (0.7 + 0.3 * np.sin(2 * np.pi * rng.uniform(1, 4) * t_(d))) for f in (300, 500, 900, 1500))
    return norm(x * adsr(len(x), 0.4, 1.2), 0.6)


# ---------------- ambience beds (loopable) ----------------
def amb_sea(d=24):
    t = t_(d + 1)
    swell = 0.55 + 0.45 * np.sin(2 * np.pi * t / 6.0) ** 2
    x = lp(noise(d + 1, "pink"), 1800) * swell + bp(noise(d + 1), 2000, 7000) * swell ** 3 * 0.15
    return loopable(norm(x, 0.5))


def amb_wind(d=24, cold=False):
    t = t_(d + 1)
    g = 0.5 + 0.5 * np.sin(2 * np.pi * t / 7.3) * np.sin(2 * np.pi * t / 3.1 + 1)
    x = bp(noise(d + 1, "pink"), 200 if not cold else 500, 1200 if not cold else 3000) * (0.4 + 0.6 * g)
    if cold:
        x += np.sin(2 * np.pi * np.cumsum(700 + 200 * g) / SR) * 0.02 * g
    return loopable(norm(x, 0.45))


def amb_rain(d=24):
    x = bp(noise(d + 1), 1000, 9000) * 0.5 + lp(noise(d + 1, "pink"), 600) * 0.3
    drops = np.zeros(len(x))
    for k in range(int(d * 40)):
        place(drops, click(rng.uniform(2000, 6000), 0.02) * rng.uniform(0.05, 0.3), rng.uniform(0, d))
    return loopable(norm(x + drops, 0.45))


def amb_room(d=24, hum=False):
    x = lp(noise(d + 1, "brown"), 300) * 2 + lp(noise(d + 1, "pink"), 2000) * 0.05
    if hum:
        t = t_(d + 1)
        x += (np.sin(2 * np.pi * 60 * t) + 0.5 * np.sin(2 * np.pi * 120 * t)) * 0.02
    return loopable(norm(x, 0.22))


def amb_office(d=24):
    x = amb_room(d) * 1.0
    clk = clock_tick(d)
    n = min(len(x), len(clk))
    x[:n] += clk[:n] * 0.12
    return norm(x, 0.25)


def amb_factory(d=24):
    t = t_(d + 1)
    x = engine(d + 1, 50, 8, 0.6) * 0.3 + lp(noise(d + 1, "brown") * 4, 500) * 0.4
    hits = np.zeros(len(t))
    for i in range(int(d / 1.5)):
        place(hits, metal_clank() * 0.25, i * 1.5 + 0.3)
    return loopable(norm(x + hits, 0.4))


def amb_battle(d=24, distant=True):
    x = amb_wind(d) * 0.6
    x = np.concatenate([x, np.zeros(int(SR))])[: int((d + 1) * SR)]
    for k in range(int(d / 1.6)):
        place(x, explosion(3.0, distant=True) * rng.uniform(0.2, 0.5), rng.uniform(0, d - 2))
    for k in range(int(d / 4)):
        place(x, machinegun(1.0, 10) * 0.08, rng.uniform(0, d - 2))
    return loopable(norm(x, 0.45))


def amb_crowd(d=24):
    t = t_(d + 1)
    x = sum(bp(noise(d + 1, "pink"), f, f * 1.5) * (0.6 + 0.4 * np.sin(2 * np.pi * rng.uniform(0.2, 1.5) * t + rng.uniform(0, 6))) for f in (250, 420, 700, 1100, 1800))
    return loopable(norm(x, 0.35))


def amb_fire(d=24):
    x = lp(noise(d + 1, "brown") * 3, 400) * 0.5
    for k in range(int(d * 25)):
        place(x, click(rng.uniform(1500, 5000), 0.02) * rng.uniform(0.05, 0.5), rng.uniform(0, d))
    return loopable(norm(x, 0.4))


def amb_engine(d=24):
    return loopable(norm(engine(d + 1, 42, 8, 0.4, True), 0.4))


def amb_jungle(d=24):
    t = t_(d + 1)
    x = lp(noise(d + 1, "pink"), 3000) * 0.2
    for k in range(int(d * 2)):
        at = rng.uniform(0, d - 1)
        f = rng.uniform(2500, 5000)
        seg = t_(0.25)
        chirp = np.sin(2 * np.pi * (f + 800 * np.sin(2 * np.pi * 12 * seg)) * seg) * np.sin(np.pi * seg / 0.25)
        place(x, chirp * 0.15, at)
    x += np.sin(2 * np.pi * 4800 * t) * (0.5 + 0.5 * np.sign(np.sin(2 * np.pi * 30 * t))) * 0.015
    return loopable(norm(x, 0.35))


def amb_city_night(d=24):
    x = amb_room(d) * 0.5 + amb_wind(d) * 0.5
    for k in range(int(d / 3)):
        place(x, explosion(3.0, distant=True) * rng.uniform(0.15, 0.35), rng.uniform(0, d - 3))
    return norm(x, 0.4)


LIB = {
    # one-shots
    "whoosh": lambda: whoosh(0.9), "whoosh_soft": lambda: whoosh(0.7, 250, 1800, 0.3), "whoosh_fast": lambda: whoosh(0.4, 600, 5000, 0.5),
    "pop": pop, "stamp": stamp, "thud": thud, "paper": paper, "pen": lambda: scribble(1.5), "chalk": lambda: scribble(1.5, True),
    "typewriter": typewriter, "bell": bell, "clock_tick": clock_tick, "explosion": lambda: explosion(3.0),
    "explosion_big": lambda: explosion(4.0, big=True), "boom_distant": lambda: explosion(3.0, distant=True),
    "gunshot": gunshot, "rifle": gunshot, "machinegun": machinegun, "artillery": artillery, "cannon": lambda: gunshot(1.2, True),
    "plane_flyby": plane_flyby, "plane_dive": plane_dive, "plane_engine": lambda: norm(engine(4, 80, 7, 0.3, True) * adsr(int(4 * SR), 0.5, 0.8), 0.6),
    "tank_engine": lambda: norm(engine(4, 30, 6, 0.6) * adsr(int(4 * SR), 0.5, 0.8), 0.7), "truck": lambda: norm(engine(4, 45, 6, 0.4) * adsr(int(4 * SR), 0.4, 0.8), 0.6),
    "train": lambda: norm(footsteps(4, 3.2) * 0.6 + engine(4, 35, 5, 0.5) * 0.3, 0.6), "splash": splash, "phone_ring": phone_ring, "morse": morse,
    "radio_static": radio_static, "metal_clank": metal_clank, "footsteps": footsteps, "footsteps_snow": lambda: footsteps(2, 2, "snow"),
    "heartbeat": heartbeat, "riser": riser, "impact": impact_hit, "map_draw": lambda: scribble(1.5), "cash": cash, "ship_horn": ship_horn,
    "cheer": crowd_cheer, "bicycle": bicycle, "bicycle_bell": lambda: norm(bell(2600, 0.9) + np.pad(bell(2600, 0.9), (int(0.22 * SR), 0))[: int(0.9 * SR)] * 0.8, 0.6), "tick": lambda: norm(click(4000, 0.03), 0.4), "church_bell": lambda: bell(420, 3.0),
    # ambience beds
    "amb_sea": amb_sea, "amb_wind": amb_wind, "amb_wind_cold": lambda: amb_wind(cold=True), "amb_rain": amb_rain,
    "amb_room": amb_room, "amb_office": amb_office, "amb_basement": lambda: amb_room(hum=True), "amb_factory": amb_factory,
    "amb_battle": amb_battle, "amb_crowd": amb_crowd, "amb_fire": amb_fire, "amb_engine": amb_engine, "amb_jungle": amb_jungle,
    "amb_city_night": amb_city_night,
}


def save(name, x):
    OUT.mkdir(parents=True, exist_ok=True)
    x = np.clip(x, -1, 1)
    with wave.open(str(OUT / f"{name}.wav"), "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((x * 32767).astype(np.int16).tobytes())


if __name__ == "__main__":
    names = sys.argv[1:] or list(LIB)
    for n in names:
        save(n, LIB[n]())
        print(n)
