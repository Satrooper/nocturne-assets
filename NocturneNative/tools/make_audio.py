"""Generates Nocturne's original v5 music and sound effects (no third-party audio).

    python3 tools/make_audio.py      -> assets/music/*.ogg, assets/sfx/*.wav
    python3 tools/make_audio_v6.py   -> realistic gun variants, footsteps, radio tracks
"""
from audio_lib import *

# ---------------------------------------------------------------- SFX (22.05 kHz mono)

def gunshot(n_s=.35, body=150, crack=3500, noise_decay=.06, body_decay=.09, tail=.18):
    n = int(SR * n_s)
    noise = rng.uniform(-1, 1, n)
    crackle = hp(noise, crack, SR) * env(n, SR, .0005, noise_decay * .4)
    blast = lp(noise, 2500, SR) * env(n, SR, .001, noise_decay)
    t = np.arange(n) / SR
    thump = np.sin(2 * np.pi * (body * np.exp(-t * 18) + 40) * t) * env(n, SR, .001, body_decay)
    rumble = lp(noise, 300, SR) * env(n, SR, .005, tail) * .6
    return np.tanh(2.4 * (crackle * .9 + blast + thump * 1.2 + rumble))

sfx("pistol", gunshot(.32, 170, 4200, .05, .07, .14))
sfx("rifle", gunshot(.30, 140, 3400, .045, .06, .12))
sfx("shotgun", gunshot(.7, 95, 2500, .12, .16, .35))
sfx("mg", gunshot(.22, 120, 3000, .035, .05, .08), .8)
# Laser beam: a seamless hum loop (buzz + shimmering harmonics).
n = int(SR * 1.0); t = np.arange(n) / SR
hum = (saw(110, n, SR, .01, 3) * .4 + square(220, n, SR, .3) * .2 + sine(880 + 30 * np.sin(2 * np.pi * 6 * t), n, SR) * .35)
hum = lp(hum, 3500, SR) + hp(rng.uniform(-1, 1, n), 5000, SR) * .08
sfx("laser_loop", hum * (0.85 + .15 * np.sin(2 * np.pi * 12 * t)), .55)
# Blaster "pew": fast downward chirp with a bright attack.
n = int(SR * .28); t = np.arange(n) / SR
f = 1900 * np.exp(-t * 14) + 180
pew = np.sin(2 * np.pi * np.cumsum(f) / SR) * env(n, SR, .001, .09)
pew += hp(rng.uniform(-1, 1, n), 4000, SR) * env(n, SR, .0005, .015) * .5
sfx("blaster", np.tanh(1.8 * pew), .8)
# Rocket launch: whoosh + thump.
n = int(SR * .9); t = np.arange(n) / SR
noise = rng.uniform(-1, 1, n)
whoosh = bp(noise, 300, 2500, SR) * env(n, SR, .02, .35)
thump = np.sin(2 * np.pi * (90 * np.exp(-t * 10) + 35) * t) * env(n, SR, .001, .12)
sfx("rocket", np.tanh(1.6 * (whoosh + thump * 1.3)))
# Explosion: deep boom with long crackling tail.
n = int(SR * 1.8); t = np.arange(n) / SR
noise = rng.uniform(-1, 1, n)
boom = np.sin(2 * np.pi * (70 * np.exp(-t * 5) + 28) * t) * env(n, SR, .002, .35)
roar = lp(noise, 900, SR) * env(n, SR, .004, .5)
crack = hp(noise * (rng.random(n) > .985), 1500, SR) * env(n, SR, .01, .6) * 3
sfx("explosion", np.tanh(2.0 * (boom * 1.4 + roar + crack)))
# Sword swings: filtered noise sweeps (light, light, heavy).
def swing(dur, lo, hi, heavy=False):
    n = int(SR * dur); t = np.arange(n) / SR
    noise = rng.uniform(-1, 1, n); out = np.zeros(n)
    centre = lo + (hi - lo) * np.sin(np.pi * t / dur)
    block = 256
    for i in range(0, n, block):
        c = centre[min(i, n - 1)]
        out[i:i + block] = bp(noise[i:i + block + 0], c * .6, c * 1.6, SR)[:len(out[i:i + block])]
    shape = np.sin(np.pi * np.clip(t / dur, 0, 1)) ** 2
    ring = sine(2400 if not heavy else 1300, n, SR) * env(n, SR, .002, .25) * .12
    return out * shape + ring
sfx("sword_1", swing(.32, 600, 3200))
sfx("sword_2", swing(.30, 700, 3600))
sfx("sword_heavy", swing(.5, 300, 2200, True))
# Sword impact: metallic ring + flesh thud.
n = int(SR * .6); t = np.arange(n) / SR
ring = sum(sine(f, n, SR) * env(n, SR, .001, d) * a for f, d, a in [(1530, .25, .5), (2470, .18, .35), (3910, .1, .25), (720, .3, .3)])
thud = lp(rng.uniform(-1, 1, n), 600, SR) * env(n, SR, .001, .06) * 1.4
sfx("sword_hit", np.tanh(1.5 * (ring + thud)))
# Ground slam shockwave.
n = int(SR * 1.1); t = np.arange(n) / SR
slam = np.sin(2 * np.pi * (55 * np.exp(-t * 4) + 30) * t) * env(n, SR, .002, .3) + lp(rng.uniform(-1, 1, n), 1200, SR) * env(n, SR, .002, .2)
sfx("slam", np.tanh(2.2 * slam))
# Iron-style boost: jet ignition roar + rising whine.
n = int(SR * .7); t = np.arange(n) / SR
jet = bp(rng.uniform(-1, 1, n), 500, 6000, SR) * env(n, SR, .01, .22)
whine = np.sin(2 * np.pi * np.cumsum(np.interp(t, [0, .7], [500, 1300])) / SR) * env(n, SR, .02, .25) * .3
ign = np.sin(2 * np.pi * (120 * np.exp(-t * 12) + 50) * t) * env(n, SR, .001, .08)
sfx("boost", np.tanh(1.7 * (jet + whine + ign)))
# Reload / UI / misc.
n = int(SR * .5)
def click(at, f=2500, d=.012, a=1.0):
    x = np.zeros(n); i = int(at * SR); m = int(SR * .08)
    x[i:i + m] = bp(rng.uniform(-1, 1, m), f * .5, f * 1.6, SR) * env(m, SR, .0005, d) * a
    return x
sfx("reload", click(.02, 1800) + click(.2, 3200, .01, .8) + click(.33, 2200, .02, 1.1))
sfx("empty", click(.0, 3000, .008)[:int(SR * .1)], .5)
n = int(SR * .12)
sfx("ui", sine(1320, n, SR) * env(n, SR, .001, .03) + sine(1980, n, SR) * env(n, SR, .001, .02) * .5, .45)
n = int(SR * .9); t = np.arange(n) / SR
sfx("overheat", np.tanh(hp(rng.uniform(-1, 1, n), 2500, SR) * env(n, SR, .01, .35) * 1.5 + sine(300, n, SR) * env(n, SR, .002, .15)), .7)
n = int(SR * .5); t = np.arange(n) / SR
sfx("hurt", np.tanh(lp(rng.uniform(-1, 1, n), 500, SR) * env(n, SR, .002, .09) * 2 + sine(90, n, SR) * env(n, SR, .002, .12)), .8)

def progression(t, bars_per, chords, root, fn):
    for bar in range(t.bars):
        deg, kind = chords[(bar // bars_per) % len(chords)]
        fn(bar, root + deg, CHORDS[kind])

# MENU — slow dark synthwave, A minor.
t = Track(92, 24)
prog = [(0, "m7"), (-4, "M7"), (3, "M"), (-2, "M")]
for bar in range(t.bars):
    deg, kind = prog[(bar // 2) % 4]; r = 57 + deg; b = bar * 4
    if bar % 2 == 0: t.pad(b, [r + i for i in CHORDS[kind]] + [r + 12], 8, .2, 1400)
    t.bass(b, r - 24, 3.5, .35, 300, 1.0)
    if bar >= 4:
        for s in range(8):
            notes = [r + i for i in CHORDS[kind]] + [r + 12]
            t.pluck(b + s * .5, notes[(s * 3) % len(notes)] + 12, .09, .3, 2200, "sq")
    if bar >= 8:
        t.kick(b, .6); t.kick(b + 2, .6); t.snare(b + 1, .3, True); t.snare(b + 3, .3, True)
        for s in range(4): t.hat(b + s + .5, .08)
    if bar % 8 == 7: t.riser(b, 4, .05)
t.render("menu")

# STAGE 1 — Neon Underworld: driving cyberpunk darksynth, D minor.
t = Track(122, 32)
prog = [(0, "m"), (-2, "M"), (-4, "M"), (-5, "M")]
for bar in range(t.bars):
    deg, kind = prog[(bar // 2) % 4]; r = 50 + deg; b = bar * 4; full = 8 <= bar < 28
    for s in range(16):
        if bar >= 2: t.bass(b + s * .25, r - 12 + (12 if s % 4 == 3 else 0), .24, .32, 700 if full else 450, 2.0, .4)
    if bar % 2 == 0: t.pad(b, [r + 12 + i for i in CHORDS[kind]], 8, .13, 1600)
    t.kick(b, .9); t.kick(b + 1, .9); t.kick(b + 2, .9); t.kick(b + 3, .9)
    if bar >= 4: t.snare(b + 1, .55); t.snare(b + 3, .55)
    for s in range(8): t.hat(b + s * .5, .12 if s % 2 else .06)
    if full:
        mel = [0, 3, 7, 10, 12, 10, 7, 3]
        for s in range(8): t.pluck(b + s * .5, r + 24 + mel[(s + bar) % 8] - (12 if kind == "M" else 0) * 0, .13, .2, 3800)
        if bar % 4 == 0: t.metal(b + 3.5, .2)
    if bar % 8 == 7: t.riser(b, 4, .09)
t.render("stage1")

# STAGE 2 — Glass Palace: sleek spy-house, G minor, offbeat hats, jazzy 7ths.
t = Track(118, 32)
prog = [(0, "m7"), (5, "m7"), (-2, "M7"), (3, "M7")]
for bar in range(t.bars):
    deg, kind = prog[bar % 4]; r = 55 + deg; b = bar * 4; full = 4 <= bar < 28
    for beat in range(4):
        t.kick(b + beat, .8); t.hat(b + beat + .5, .14, beat == 3)
        if full: t.snare(b + beat + .75, .08)
    if full: t.snare(b + 1, .45, True); t.snare(b + 3, .45, True)
    t.pad(b, [r + i for i in CHORDS[kind]], 4, .13, 2200, 3)
    for s, (o, d) in enumerate([(0, .5), (1.5, .5), (2.5, .25), (3, .75)]):
        t.bass(b + o, r - 24 + (7 if s == 2 else 0), d, .45, 500, 1.5)
    if bar >= 8 and bar < 24:
        mel = [7, 10, 12, 15, 14, 10, 7, 5]
        for s in range(0, 8, 1 if bar % 2 else 2): t.pluck(b + s * .5, r + 12 + mel[s], .1, .18, 4500, "sine")
t.render("stage2")

# STAGE 3 — Hollow Bamboo: pentatonic koto plucks, taiko toms, E minor.
t = Track(100, 32)
pent = [0, 3, 5, 7, 10, 12, 15]
for bar in range(t.bars):
    r = 52 + [0, 0, -4, -2][(bar // 2) % 4]; b = bar * 4
    if bar % 2 == 0: t.pad(b, [r, r + 7, r + 12], 8, .11, 1100, 3)
    t.bass(b, r - 12, 2, .3, 300, 1.0, -.8)
    t.tom(b, 80, .7); t.tom(b + 1.5, 95, .45); t.tom(b + 2.5, 80, .55)
    if bar >= 4: t.tom(b + 3.25, 130, .3); t.tom(b + 3.5, 130, .35)
    if bar >= 8:
        t.kick(b, .5); t.snare(b + 2, .3); [t.hat(b + s * .5, .05) for s in range(8)]
    pattern = [0, 2, 4, 5, 3, 4, 2, 1] if bar % 2 else [4, 3, 2, 0, 1, 2, 3, 6]
    if bar >= 2:
        for s in range(8):
            if (s + bar) % 5 != 4: t.pluck(b + s * .5, r + 12 + pent[pattern[s]], .2, .28, 5000, "sine")
    if bar % 8 == 0: t.bell(b, r + 24, .1)
t.render("stage3")

# STAGE 4 — Ashworks: industrial, distorted bass, metallic hits, C minor.
t = Track(128, 32)
for bar in range(t.bars):
    r = 48 + [0, 0, 3, -2][(bar // 2) % 4]; b = bar * 4; full = 4 <= bar < 30
    for beat in range(4):
        t.kick(b + beat, 1.0, 1.4)
        if full: t.hat(b + beat + .5, .16, True)
    if full: t.snare(b + 1, .6); t.snare(b + 3, .6); t.snare(b + 3.75, .25)
    for s in range(8):
        t.bass(b + s * .5, r - 12 + (0 if s % 3 else 1), .45, .38, 900, 4.0, .5)
    if bar % 2 == 1: t.metal(b + 2.5, .35); t.metal(b + 3.5, .25)
    if bar >= 8 and bar % 4 < 2:
        for s in range(4): t.pluck(b + s, r + 12 + [0, 3, 6, 3][s], .1, .4, 1800, "saw")
    if bar % 2 == 0: t.pad(b, [r, r + 3, r + 6], 8, .07, 900)
t.render("stage4")

# STAGE 5 — Black Cathedral: gothic organ/choir pads, bells, F minor.
t = Track(108, 32)
prog = [(0, "m"), (-4, "M"), (1, "M"), (-1, "dim")]
for bar in range(t.bars):
    deg, kind = prog[(bar // 2) % 4]; r = 53 + deg; b = bar * 4; full = 8 <= bar < 28
    if bar % 2 == 0:
        t.pad(b, [r - 12, r] + [r + 12 + i for i in CHORDS[kind]], 8, .19, 2400, 6)
    t.bass(b, r - 24, 4, .3, 250, 1.0, -.9)
    if bar % 4 == 0: t.bell(b, r + 24, .16)
    if bar >= 4:
        t.kick(b, .8); t.kick(b + 2.5, .6); t.snare(b + 2, .5)
        for s in range(8): t.hat(b + s * .5, .07)
    if full:
        for s in range(8): t.pluck(b + s * .5, r + 12 + [0, 7, 12, 7, 3, 7, 12, 15][s], .08, .22, 2600, "sq")
        t.tom(b + 3.5, 70, .4)
    if bar % 8 == 7: t.riser(b, 4, .07)
t.render("stage5")

# BOSS — aggressive, 148 BPM, E harmonic minor, distorted reese-ish bass.
t = Track(148, 32)
hm = [0, 2, 3, 5, 7, 8, 11, 12]
prog = [0, 0, -4, -1]
for bar in range(t.bars):
    r = 52 + prog[(bar // 2) % 4]; b = bar * 4; full = 4 <= bar < 30
    t.kick(b, 1.0, 1.3); t.kick(b + 2.5, .9, 1.3)
    if bar % 2: t.kick(b + 1.75, .7, 1.3)
    t.snare(b + 1, .7); t.snare(b + 3, .7)
    for s in range(16): t.hat(b + s * .25, .09 if s % 2 else .14)
    for s in range(4):
        t.bass(b + s, r - 12, .9, .4, 1100 if full else 600, 4.5, .5)
    if full:
        for s in range(16):
            t.pluck(b + s * .25, r + 12 + hm[[0, 4, 7, 4, 2, 5, 6, 5][s % 8]], .09, .12, 4200)
        if bar % 2 == 0: t.pad(b, [r, r + 3, r + 7, r + 11], 8, .1, 2000)
        if bar % 4 == 3: t.metal(b + 3, .3)
    if bar % 8 == 7: t.riser(b, 4, .1)
t.render("boss")
print("done")
