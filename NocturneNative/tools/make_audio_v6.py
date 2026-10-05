"""v6 audio: layered realistic gunshots (3 variants each), footsteps per surface,
jump/land, and five extra radio tracks. All synthesised; no third-party audio.

    python3 tools/make_audio_v6.py [--sfx] [--radio]
"""
import sys
from audio_lib import *

GSR = 44100

def gsfx(name, x, peak=.92):
    write_wav(os.path.join(SFX, name + ".wav"), norm(x, peak), GSR)

def env_s(n, a, d):
    return env(n, GSR, a, d)

def addat(buf, start, x):
    x = x[:max(0, len(buf) - start)]
    buf[start:start + len(x)] += x

def gunshot(rng_, length=.9, blast_decay=.03, blast_lp=5500, thump_f=70, thump_decay=.09,
            body_lo=350, body_hi=1100, crack=True, cycle_at=None, tail_decay=.35, tail_lp=700,
            reflections=((.021, .35), (.047, .22), (.083, .14)), drive=4.0, click=.25):
    n = int(GSR * length)
    t = np.arange(n) / GSR
    j = lambda v, k=.12: v * (1 + rng_.uniform(-k, k))
    out = np.zeros(n)
    noise = rng_.uniform(-1, 1, n)
    # Firing pin / hammer click, a hair before the blast.
    m = int(GSR * .004)
    addat(out, 0, bp(noise[:m], 2500, 7000, GSR) * env(m, GSR, .0002, .0009) * click)
    o = int(GSR * .0012)
    # Supersonic crack: an N-wave spike with bright fizz.
    if crack:
        w = int(GSR * .0005)
        nwave = np.concatenate([np.linspace(0, 1, w // 2), np.linspace(1, -1, w), np.linspace(-1, 0, w // 2)])
        addat(out, o, nwave * 1.4)
        k = int(GSR * .012)
        addat(out, o, hp(noise[:k], 4500, GSR) * env(k, GSR, .0001, j(.0025)) * .9)
    # Muzzle blast: saturated broadband burst.
    k = n - o
    # Saturate first, then shape: keeps the blast punchy but lets it decay fast.
    blast = np.tanh(lp(noise[:k], j(blast_lp), GSR, 2) * drive) * env(k, GSR, .0003, j(blast_decay))
    addat(out, o, blast * 1.1)
    # Low-end thump with a falling pitch.
    k = int(GSR * .5); tt = np.arange(k) / GSR
    f = j(thump_f) * (1 + 1.8 * np.exp(-tt * 55))
    addat(out, o, np.sin(2 * np.pi * np.cumsum(f) / GSR) * env(k, GSR, .0005, j(thump_decay)) * .42)
    # Receiver/body resonance.
    k = int(GSR * .15)
    addat(out, o, bp(noise[:k], body_lo, body_hi, GSR, 2) * env(k, GSR, .0005, .022) * .7)
    # Bolt carrier cycling: metallic clack + slide.
    if cycle_at is not None:
        c = int(GSR * j(cycle_at, .05)); k = int(GSR * .06)
        clack = sum(sine(fq, k, GSR) * g for fq, g in ((j(2350, .05), .5), (j(3720, .05), .35), (j(5110, .05), .2)))
        clack = clack * env(k, GSR, .0002, .006) + bp(noise[:k], 1500, 6000, GSR) * env(k, GSR, .0005, .012) * .6
        addat(out, c, clack * .28)
    # Early reflections off nearby surfaces (stage reverb is added in-game).
    dry = out.copy()
    for delay, gain in reflections:
        d = int(GSR * j(delay, .15))
        out[d:] += lp(dry, 2500, GSR)[:n - d] * gain
    # Rolling tail.
    tail = lp(noise, j(tail_lp), GSR, 2) * env(n, GSR, .004, j(tail_decay)) * .22
    sweep = np.exp(-t * 2.2)
    out += tail * (.4 + .6 * sweep)
    fade = int(GSR * .02); out[-fade:] *= np.linspace(1, 0, fade)
    return np.tanh(out * 1.3)

def make_sfx():
    for v in range(1, 4):
        r = np.random.default_rng(100 + v)
        suffix = "" if v == 1 else "_%d" % v
        gsfx("pistol" + suffix, gunshot(r, .7, .012, 7000, 110, .028, 500, 1500, True, .045, .25, 900, drive=3.5))
        gsfx("rifle" + suffix, gunshot(r, .8, .015, 6000, 80, .035, 380, 1200, True, .038, .32, 750, drive=3.8))
        gsfx("shotgun" + suffix, gunshot(r, 1.2, .03, 4200, 60, .06, 250, 800, False, None, .5, 520,
                                         reflections=((.025, .4), (.058, .26), (.11, .16)), drive=4.5, click=.35))
        gsfx("mg" + suffix, gunshot(r, .45, .011, 6000, 85, .025, 400, 1300, True, .03, .16, 800,
                                    reflections=((.019, .25), (.041, .15)), drive=3.4), .85)
    # Footsteps: 4 variants per surface.
    for v in range(1, 5):
        r = np.random.default_rng(300 + v)
        n = int(SR * .3); noise = r.uniform(-1, 1, n)
        heel = bp(noise, 900, 4500, SR) * env(n, SR, .0005, .007) + lp(noise, 180, SR) * env(n, SR, .001, .025) * 2.2
        toe = np.zeros(n); d = int(SR * r.uniform(.04, .055)); m = n - d
        toe[d:] = bp(noise[:m], 1500, 6000, SR) * env(m, SR, .002, .02) * .35
        sfx("step_hard_%d" % v, heel + toe, .8)
        n = int(SR * .35); noise = r.uniform(-1, 1, n)
        crackles = (r.random(n) > .985) * r.uniform(-1, 1, n)
        rustle = bp(noise, 1500, 7000, SR) * env(n, SR, .01, .08) * .5 + hp(crackles, 2000, SR) * env(n, SR, .005, .1) * 2
        thud = lp(noise, 160, SR) * env(n, SR, .002, .03) * 1.6
        sfx("step_soft_%d" % v, rustle + thud, .65)
        n = int(SR * .45)
        ring = sum(sine(f * r.uniform(.97, 1.03), n, SR) * env(n, SR, .001, dd) * g for f, dd, g in ((640, .12, .5), (1310, .08, .35), (2420, .05, .25)))
        thud = lp(r.uniform(-1, 1, n), 220, SR) * env(n, SR, .001, .03) * 2
        sfx("step_metal_%d" % v, ring * .6 + thud, .8)
    r = np.random.default_rng(400)
    n = int(SR * .4); noise = r.uniform(-1, 1, n); t = np.arange(n) / SR
    push = lp(noise, 200, SR) * env(n, SR, .001, .03) * 1.5
    cloth = bp(noise, 600, 3500, SR) * np.sin(np.pi * np.clip(t / .3, 0, 1)) ** 2 * .5
    sfx("jump", push + cloth, .7)
    n = int(SR * .6); noise = r.uniform(-1, 1, n); t = np.arange(n) / SR
    boom = np.sin(2 * np.pi * (75 * np.exp(-t * 8) + 40) * t) * env(n, SR, .001, .08)
    gear = sum(bp(noise, 2000, 6000, SR) * env(n, SR, .001, .01) * np.roll(np.ones(n), int(SR * k)) * (np.arange(n) > SR * k) for k in (.0, .03, .06)) * .3
    sfx("land", boom * 1.4 + lp(noise, 600, SR) * env(n, SR, .002, .05) + gear, .85)
    print("sfx done")

def make_radio():
    # Rain Chase — outrun synthwave, F# minor.
    t = Track(116, 32)
    prog = [(0, "m"), (-4, "M"), (-2, "M"), (-7, "M")]
    for bar in range(t.bars):
        deg, kind = prog[(bar // 2) % 4]; r = 54 + deg; b = bar * 4; full = 8 <= bar < 28
        t.kick(b, .85); t.kick(b + 2, .85)
        if bar >= 4: t.snare(b + 1, .7); t.snare(b + 3, .7)
        for s in range(8): t.hat(b + s * .5, .07)
        for s in range(8): t.bass(b + s * .5, r - 12 + (12 if s % 2 else 0), .45, .34, 650, 1.4, .5)
        if bar % 2 == 0: t.pad(b, [r + 12 + i for i in CHORDS[kind]], 8, .15, 1700)
        if full:
            mel = [7, 10, 12, 10, 7, 5, 3, 5] if bar % 4 < 2 else [12, 15, 14, 12, 10, 7, 10, 12]
            for s in range(8): t.pluck(b + s * .5, r + 12 + mel[s], .12, .35, 3200, "sq")
        if bar % 8 == 7: t.riser(b, 4, .07)
    t.render("radio1")
    # Chrome Heist — funk house, A minor, octave bass + chord stabs.
    t = Track(122, 32)
    prog = [(0, "m7"), (5, "m7"), (3, "M7"), (-2, "M7")]
    for bar in range(t.bars):
        deg, kind = prog[(bar // 2) % 4]; r = 57 + deg; b = bar * 4; full = 4 <= bar < 30
        for beat in range(4):
            t.kick(b + beat, .85)
            t.hat(b + beat + .5, .16, True)
        if full: t.snare(b + 1, .5, True); t.snare(b + 3, .5, True)
        for s, (o, oct_) in enumerate([(0, 0), (.5, 12), (.75, 0), (1.5, 12), (2, 0), (2.5, 12), (3.25, 0), (3.5, 12)]):
            t.bass(b + o, r - 24 + oct_, .22, .5, 900, 1.8, .4)
        if full:
            for o in (.5, 1.75, 2.5, 3.75): 
                for note in CHORDS[kind]: t.pluck(b + o, r + 12 + note, .06, .1, 3800, "saw")
    t.render("radio2")
    # Lotus Drift — lo-fi, 78 BPM, swung, warm M7 chords + vinyl crackle.
    t = Track(78, 24)
    prog = [(0, "M7"), (-3, "m7"), (5, "m7"), (-5, "M7")]
    for bar in range(t.bars):
        deg, kind = prog[bar % 4]; r = 60 + deg; b = bar * 4
        t.kick(b, .6); t.kick(b + 2.5, .5); t.snare(b + 1, .32); t.snare(b + 3, .32)
        for s in range(4): t.hat(b + s + .0, .06); t.hat(b + s + .62, .04)
        notes = [r - 12 + i for i in CHORDS[kind]] + [r + 2]
        for k, note in enumerate(notes): t.pluck(b + k * .04, note, .1, .9, 1400, "sine")
        t.bass(b, r - 24, 1.5, .4, 260, 1.0, -.7); t.bass(b + 2.5, r - 24 + 7, 1.0, .35, 260, 1.0, -.7)
        if bar >= 4 and bar % 2 == 1:
            for s, m in enumerate([7, 9, 11, 14]): t.pluck(b + 2 + s * .5, r + 12 + m, .06, .5, 2000, "sine")
    n = len(t.buses["fx"]); crackle = (rng.random(n) > .9992) * rng.uniform(-1, 1, n)
    t.buses["fx"] += hp(crackle, 1500, t.sr) * .25 + lp(rng.uniform(-1, 1, n), 4000, t.sr) * .004
    t.render("radio3")
    # Iron Liturgy — heavy industrial, 135 BPM, D minor.
    t = Track(135, 32)
    for bar in range(t.bars):
        r = 50 + [0, 0, 1, -2][(bar // 2) % 4]; b = bar * 4; full = 4 <= bar < 30
        for beat in range(4): t.kick(b + beat, 1.0, 1.5)
        if full:
            t.snare(b + 1, .7); t.snare(b + 3, .7)
            for s in range(8): t.hat(b + s * .5, .1, s % 2 == 1)
            t.tom(b + 3.5, 90, .5); t.tom(b + 3.75, 70, .5)
        for s in range(16):
            if s % 4 != 3: t.bass(b + s * .25, r - 12 + (1 if s == 6 else 0), .22, .4, 1200, 6.0, .4)
        if bar % 2: t.metal(b + 1.5, .4); t.metal(b + 3.5, .3)
        if bar % 4 == 0: t.pad(b, [r, r + 1, r + 7], 16, .08, 1000)
    t.render("radio4")
    # Neon Pulse — festival EDM, 128 BPM, C minor, build + drop.
    t = Track(128, 32)
    prog = [(0, "m"), (-4, "M"), (-7, "M"), (-2, "M")]
    for bar in range(t.bars):
        deg, kind = prog[bar % 4]; r = 60 + deg; b = bar * 4
        drop = (8 <= bar < 16) or (24 <= bar < 32); build = 4 <= bar < 8 or 20 <= bar < 24
        if drop:
            for beat in range(4): t.kick(b + beat, 1.0, 1.2); t.hat(b + beat + .5, .14, True)
            t.snare(b + 1, .6, True); t.snare(b + 3, .6, True)
            for s in range(8): t.bass(b + s * .5 + .5 * 0, r - 24, .4, .45, 900, 2.5, .5)
            for s, note in enumerate([0, 7, 12, 7, 15, 12, 7, 3]):
                for d in (-0.08, 0, .08): t.pluck(b + s * .5, r + 12 + note + d, .07, .28, 6500, "saw")
        elif build:
            reps = 4 if bar % 4 < 2 else 8
            for s in range(reps): t.snare(b + s * 4 / reps, .25 + .1 * s / reps)
            t.pad(b, [r + i for i in CHORDS[kind]], 4, .14, 2600)
            if bar % 4 == 3: t.riser(b, 4, .12)
        else:
            t.pad(b, [r + i for i in CHORDS[kind]] + [r + 12], 4, .16, 1500)
            for s in range(8): t.pluck(b + s * .5, r + 12 + [0, 3, 7, 12][s % 4], .07, .3, 2500, "sq")
            t.kick(b, .5)
    t.render("radio5")

if __name__ == "__main__":
    args = set(sys.argv[1:]) or {"--sfx", "--radio"}
    if "--sfx" in args: make_sfx()
    if "--radio" in args: make_radio()
