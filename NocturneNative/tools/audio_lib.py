"""Shared synth library for Nocturne audio generators."""
import os, subprocess, numpy as np
from scipy.signal import butter, sosfilt, fftconvolve

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MUSIC = os.path.join(ROOT, "assets", "music")
SFX = os.path.join(ROOT, "assets", "sfx")
os.makedirs(MUSIC, exist_ok=True); os.makedirs(SFX, exist_ok=True)
rng = np.random.default_rng(7)

# ---------------------------------------------------------------- helpers
def lp(x, f, sr, order=2):
    return sosfilt(butter(order, min(f, sr * .45), "low", fs=sr, output="sos"), x)
def hp(x, f, sr, order=2):
    return sosfilt(butter(order, f, "high", fs=sr, output="sos"), x)
def bp(x, lo, hi, sr, order=2):
    return sosfilt(butter(order, [lo, min(hi, sr * .45)], "band", fs=sr, output="sos"), x)
def env(n, sr, a=.002, d=.2, curve=1.0):
    t = np.arange(n) / sr
    e = np.minimum(1, t / max(a, 1e-4)) * np.exp(-np.maximum(0, t - a) / max(d, 1e-4) * curve)
    return e
def saw(f, n, sr, detune=0.0, voices=1, phase_rand=True):
    t = np.arange(n) / sr; out = np.zeros(n)
    for v in range(voices):
        fv = f * (1 + detune * (v - (voices - 1) / 2) / max(1, voices - 1)) if voices > 1 else f
        ph = rng.random() if phase_rand else 0
        out += 2 * ((t * fv + ph) % 1) - 1
    return out / voices
def square(f, n, sr, pw=.5):
    t = np.arange(n) / sr
    return np.where((t * f) % 1 < pw, 1.0, -1.0)
def sine(f, n, sr):
    return np.sin(2 * np.pi * f * np.arange(n) / sr)
def mtof(m): return 440.0 * 2 ** ((m - 69) / 12)
def norm(x, peak=.89):
    m = np.max(np.abs(x)) or 1
    return x / m * peak
def write_wav(path, x, sr):
    import wave
    x = np.clip(x, -1, 1)
    with wave.open(path, "wb") as w:
        w.setnchannels(1 if x.ndim == 1 else 2); w.setsampwidth(2); w.setframerate(sr)
        data = (x * 32767).astype("<i2")
        w.writeframes(np.ascontiguousarray(data).tobytes())


SR = 22050
def sfx(name, x, peak=.9):
    write_wav(os.path.join(SFX, name + ".wav"), norm(x, peak), SR)

# ---------------------------------------------------------------- MUSIC
MSR = 32000
CHORDS = {"m": [0, 3, 7], "M": [0, 4, 7], "m7": [0, 3, 7, 10], "M7": [0, 4, 7, 11], "sus": [0, 5, 7], "dim": [0, 3, 6]}

class Track:
    def __init__(self, bpm, bars, sr=MSR):
        self.bpm, self.bars, self.sr = bpm, bars, sr
        self.beat = 60 / bpm; self.n = int(bars * 4 * self.beat * sr)
        tail = int(sr * 3)
        self.buses = {k: np.zeros(self.n + tail) for k in ["drums", "bass", "pad", "lead", "fx"]}
        self.kicks = []
    def at(self, beat): return int(beat * self.beat * self.sr)
    def add(self, bus, start, x):
        b = self.buses[bus]; i = self.at(start); x = x[:max(0, len(b) - i)]; b[i:i + len(x)] += x
    # drums
    def kick(self, beat, a=1.0, punch=1.0):
        n = int(self.sr * .45); t = np.arange(n) / self.sr
        x = np.sin(2 * np.pi * np.cumsum(48 + 140 * np.exp(-t * 32 * punch)) / self.sr) * env(n, self.sr, .001, .2)
        x += lp(rng.uniform(-1, 1, n), 4000, self.sr) * env(n, self.sr, .0005, .004) * .4
        self.add("drums", beat, np.tanh(1.5 * x) * a); self.kicks.append(beat)
    def snare(self, beat, a=.6, clap=False):
        n = int(self.sr * .35); noise = rng.uniform(-1, 1, n)
        x = bp(noise, 1200, 8000, self.sr) * env(n, self.sr, .001, .09 if not clap else .06)
        if clap:
            for k in (0.0, .011, .022):
                i = int(k * self.sr); x[i:] += bp(noise, 900, 3000, self.sr)[: n - i] * env(n - i, self.sr, .001, .012) * .7
        x += sine(190, n, self.sr) * env(n, self.sr, .001, .05) * .6
        self.add("drums", beat, x * a)
    def hat(self, beat, a=.18, open_=False):
        n = int(self.sr * (.25 if open_ else .06))
        x = hp(rng.uniform(-1, 1, n), 7000, self.sr) * env(n, self.sr, .0005, .12 if open_ else .018)
        self.add("drums", beat, x * a)
    def tom(self, beat, f=110, a=.5):
        n = int(self.sr * .5); t = np.arange(n) / self.sr
        x = np.sin(2 * np.pi * np.cumsum(f * (1 + .6 * np.exp(-t * 20))) / self.sr) * env(n, self.sr, .001, .18)
        x += lp(rng.uniform(-1, 1, n), 900, self.sr) * env(n, self.sr, .001, .03) * .3
        self.add("drums", beat, x * a)
    def metal(self, beat, a=.25):
        n = int(self.sr * .5)
        x = sum(sine(f, n, self.sr) for f in (523, 1187, 1853, 2741)) * env(n, self.sr, .001, .12)
        x = x * (1 + .5 * rng.uniform(-1, 1, n) * env(n, self.sr, .001, .01))
        self.add("fx", beat, x * a / 4)
    # tonal
    def bass(self, beat, note, dur, a=.5, cutoff=600, dist=1.0, sub=.6):
        n = int(dur * self.beat * self.sr); f = mtof(note)
        x = saw(f, n, self.sr, .004, 2) * .8 + sine(f / 2 if sub < 0 else f, n, self.sr) * abs(sub)
        x = lp(x, cutoff, self.sr) * env(n, self.sr, .004, dur * self.beat * .9, .6)
        rel = min(n, int(self.sr * .01)); x[-rel:] *= np.linspace(1, 0, rel)
        self.add("bass", beat, np.tanh(dist * x) * a)
    def pad(self, beat, notes, dur, a=.16, bright=1800, voices=5):
        n = int(dur * self.beat * self.sr)
        x = sum(saw(mtof(m), n, self.sr, .012, voices) for m in notes) / len(notes)
        x = lp(x, bright, self.sr)
        t = np.arange(n) / self.sr; L = n / self.sr
        e = np.minimum(1, t / (L * .25)) * np.minimum(1, (L - t) / (L * .2) + .0)
        self.add("pad", beat, x * np.clip(e, 0, 1) * a)
    def pluck(self, beat, note, a=.2, decay=.25, cutoff=3000, wave="saw", bus="lead"):
        n = int(self.sr * (decay * 4 + .05)); f = mtof(note)
        x = saw(f, n, self.sr, .006, 2) if wave == "saw" else (square(f, n, self.sr, .3) if wave == "sq" else
            sine(f, n, self.sr) + .3 * sine(f * 2.01, n, self.sr) * env(n, self.sr, .001, decay * .3) + .25 * sine(f * 3, n, self.sr) * env(n, self.sr, .001, .03))
        x = lp(x, cutoff, self.sr) * env(n, self.sr, .002, decay)
        self.add(bus, beat, x * a)
    def bell(self, beat, note, a=.18):
        n = int(self.sr * 3); f = mtof(note)
        x = sum(sine(f * r, n, self.sr) * env(n, self.sr, .001, d) * g for r, d, g in [(1, 1.6, 1), (2.76, .9, .5), (5.4, .4, .3), (8.93, .2, .2)])
        self.add("fx", beat, x * a)
    def riser(self, beat, beats, a=.12):
        n = int(beats * self.beat * self.sr); t = np.arange(n) / self.sr
        x = hp(rng.uniform(-1, 1, n), 800, self.sr) * (t / t[-1]) ** 2
        self.add("fx", beat, x * a)
    def render(self, name, master=.9):
        sr = self.sr; total = len(self.buses["drums"])
        # Sidechain pump from kicks onto bass + pad.
        duck = np.ones(total)
        for k in self.kicks:
            i = self.at(k); m = int(sr * self.beat * .9)
            curve = 1 - .65 * np.exp(-np.arange(m) / (sr * .09))
            duck[i:i + m] = np.minimum(duck[i:i + m], curve[: len(duck[i:i + m])])
        pad = self.buses["pad"] * duck; bass = self.buses["bass"] * (.55 + .45 * duck)
        lead = self.buses["lead"].copy()
        d = int(self.beat * .75 * sr)  # dotted-eighth delay
        for g in (.38, .22, .12):
            lead[d:] += self.buses["lead"][:-d] * g; d += int(self.beat * .75 * sr)
        ir_n = int(sr * 2.2); ir = rng.uniform(-1, 1, ir_n) * np.exp(-np.arange(ir_n) / (sr * .5)); ir = lp(ir, 5000, sr)
        wet = fftconvolve(pad * .6 + lead * .7 + self.buses["fx"], ir)[:total] * .035
        mix_l = self.buses["drums"] + bass + pad + lead + self.buses["fx"] + wet
        # Mild stereo: delayed pad/lead copy on the right side.
        s = int(sr * .012); side = np.zeros(total); side[s:] = (pad + lead * .6)[:-s]
        L = mix_l - side * .25; R = mix_l + side * .25 - (pad + lead * .6) * .25
        # Seamless loop: fold the reverb/delay tail onto the start.
        n = self.n
        L[: total - n] += L[n:]; R[: total - n] += R[n:]
        L, R = L[:n], R[:n]
        fade = int(sr * .006)
        for ch in (L, R):
            ch[:fade] *= np.linspace(0, 1, fade); ch[-fade:] *= np.linspace(1, 0, fade)
        stereo = np.stack([L, R])
        stereo = np.tanh(stereo / (np.max(np.abs(stereo)) or 1) * 1.6) * master
        stereo = stereo / np.max(np.abs(stereo)) * .9
        wav = os.path.join("/tmp", name + ".wav")
        write_wav(wav, stereo.T, sr)
        out = os.path.join(MUSIC, name + ".ogg")
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", wav, "-c:a", "libvorbis", "-q:a", "3", out], check=True)
        os.remove(wav)
        print("music", name, f"{n / sr:.0f}s", os.path.getsize(out) // 1024, "KB")

