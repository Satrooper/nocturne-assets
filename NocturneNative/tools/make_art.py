"""Original procedural artwork for in-game paintings and scrolls (no third-party images)."""
import os, numpy as np
from PIL import Image, ImageDraw, ImageFilter
OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets", "textures", "art")
rng = np.random.default_rng(11)
W, H = 384, 480

def canvas_finish(img, warm=1.0, crack=True):
    a = np.asarray(img).astype(float) / 255
    h, w = a.shape[:2]
    weave = (np.sin(np.arange(w)[None, :] * 2.1) * np.sin(np.arange(h)[:, None] * 2.1)) * .02
    a += weave[..., None] + rng.normal(0, .015, a.shape)
    if crack:
        c = Image.new("L", (w, h), 0); d = ImageDraw.Draw(c)
        for _ in range(140):
            x, y = rng.integers(0, w), rng.integers(0, h)
            for _ in range(6):
                nx, ny = x + rng.integers(-14, 15), y + rng.integers(-14, 15)
                d.line([(x, y), (nx, ny)], fill=int(rng.integers(30, 70)), width=1); x, y = nx, ny
        a -= np.asarray(c)[..., None] / 255 * .25
    yy, xx = np.mgrid[0:h, 0:w]; v = ((xx - w / 2) / (w / 2)) ** 2 + ((yy - h / 2) / (h / 2)) ** 2
    a *= (1 - .45 * np.clip(v, 0, 1))[..., None]
    a[..., 0] *= 1.0 + .06 * warm; a[..., 2] *= 1.0 - .08 * warm   # aged varnish
    return Image.fromarray((np.clip(a, 0, 1) * 255).astype(np.uint8))

def brush(d, x, y, r, col, n=30, spread=1.0):
    for _ in range(n):
        dx, dy = rng.normal(0, r * spread, 2); rr = abs(rng.normal(r * .5, r * .2)) + 1
        c = tuple(int(np.clip(v + rng.normal(0, 10), 0, 255)) for v in col)
        d.ellipse([x + dx - rr, y + dy - rr * .6, x + dx + rr, y + dy + rr * .6], fill=c)

def gradient(top, bottom):
    t = np.linspace(0, 1, H)[:, None, None]
    return Image.fromarray((np.array(top)[None, None, :] * (1 - t) + np.array(bottom)[None, None, :] * t).repeat(W, 1).astype(np.uint8))

def portrait(name, bg, skin, cloth, halo=False):
    img = gradient(bg, tuple(int(c * .4) for c in bg)); d = ImageDraw.Draw(img)
    if halo:
        for r in range(70, 40, -2): d.ellipse([W/2 - r, 150 - r, W/2 + r, 150 + r], outline=(200 + r // 2, 160 + r // 3, 60), width=2)
    for i in range(500): brush(d, W / 2 + rng.normal(0, 70), 380 + rng.normal(0, 50), 10, cloth, 1)
    d.polygon([(W/2 - 150, H), (W/2 - 80, 300), (W/2 + 80, 300), (W/2 + 150, H)], fill=cloth)
    for i in range(160): brush(d, W/2 + rng.normal(0, 30), 165 + rng.normal(0, 40), 6, skin, 1)
    d.ellipse([W/2 - 48, 100, W/2 + 48, 230], fill=skin)
    d.ellipse([W/2 - 48, 100, W/2 + 6, 230], fill=tuple(int(c * .8) for c in skin))
    d.pieslice([W/2 - 58, 80, W/2 + 58, 190], 180, 360, fill=(40, 28, 22))
    for ex in (-18, 18): d.ellipse([W/2 + ex - 7, 156, W/2 + ex + 7, 164], fill=(35, 25, 20))
    d.line([(W/2, 165), (W/2 - 4, 190), (W/2 + 3, 192)], fill=tuple(int(c * .7) for c in skin), width=3)
    d.line([(W/2 - 14, 207), (W/2 + 14, 207)], fill=(110, 50, 45), width=3)
    img = img.filter(ImageFilter.GaussianBlur(1.1))
    canvas_finish(img).save(os.path.join(OUT, name + ".jpg"), quality=86)

def landscape(name, sky1, sky2, hill, water=True, storm=False):
    img = gradient(sky1, sky2); d = ImageDraw.Draw(img)
    for i in range(40): brush(d, rng.uniform(0, W), rng.uniform(20, 200), 18, tuple(int(c * 1.1) for c in sky1), 6, 2)
    for layer in range(3):
        pts = [(0, H)]; base = 230 + layer * 50
        for x in range(0, W + 20, 20): pts.append((x, base - 60 * np.sin(x / 70 + layer * 2) * (1 - layer * .3) - rng.uniform(0, 20)))
        pts.append((W, H)); d.polygon(pts, fill=tuple(int(c * (1 - layer * .25)) for c in hill))
    if water:
        d.rectangle([0, 380, W, H], fill=tuple(int(c * .6) for c in sky2))
        for i in range(200):
            y = rng.uniform(380, H); x = rng.uniform(0, W)
            d.line([(x, y), (x + rng.uniform(10, 40), y)], fill=tuple(int(c * .9) for c in sky1), width=1)
    if storm:
        for i in range(60):
            x, y = rng.uniform(0, W), rng.uniform(300, H)
            d.arc([x - 40, y - 20, x + 40, y + 20], 180, 360, fill=(220, 230, 235), width=3)
    img = img.filter(ImageFilter.GaussianBlur(1.3))
    canvas_finish(img).save(os.path.join(OUT, name + ".jpg"), quality=86)

def still_life(name):
    img = gradient((48, 34, 24), (18, 12, 8)); d = ImageDraw.Draw(img)
    d.rectangle([0, 330, W, H], fill=(70, 44, 26))
    d.ellipse([90, 290, 300, 350], fill=(150, 140, 120))
    for i, (x, y, c) in enumerate([(150, 280, (170, 40, 30)), (200, 270, (190, 150, 40)), (245, 285, (90, 120, 40)), (180, 250, (120, 30, 60))]):
        d.ellipse([x - 32, y - 32, x + 32, y + 32], fill=c); d.ellipse([x - 20, y - 24, x - 4, y - 8], fill=tuple(min(255, v + 70) for v in c))
    d.rectangle([300, 150, 330, 330], fill=(180, 170, 140)); d.ellipse([306, 120, 324, 152], fill=(255, 210, 120))
    canvas_finish(img.filter(ImageFilter.GaussianBlur(1.0))).save(os.path.join(OUT, name + ".jpg"), quality=86)

def ink_scroll(name, subject):
    w, h = 256, 640
    img = Image.new("RGB", (w, h), (226, 214, 186)); d = ImageDraw.Draw(img)
    if subject == "bamboo":
        for x in (80, 140, 190):
            for y in range(40, 600, 70): d.rectangle([x - 6, y, x + 6, y + 62], fill=(40, 45, 38)); d.line([(x - 8, y), (x + 8, y)], fill=(20, 20, 18), width=3)
            for _ in range(5):
                y = rng.uniform(60, 500); s = rng.choice([-1, 1])
                d.polygon([(x, y), (x + s * 70, y + 18), (x + s * 66, y + 26)], fill=(30, 34, 28))
    else:
        d.ellipse([120, 90, 200, 170], fill=(170, 40, 30))
        for _ in range(3):
            x = rng.uniform(40, 200); y = rng.uniform(260, 520)
            d.line([(x, y), (x + 40, y - 60), (x + 70, y - 50)], fill=(25, 25, 22), width=5)
            d.polygon([(x + 40, y - 60), (x - 30, y - 90), (x + 10, y - 50)], fill=(30, 30, 26))
            d.polygon([(x + 40, y - 60), (x + 110, y - 95), (x + 60, y - 48)], fill=(30, 30, 26))
    for i, ch in enumerate(range(6)): d.rectangle([20, 60 + i * 26, 34, 78 + i * 26], fill=(30, 28, 25))
    d.rectangle([200, 560, 226, 590], fill=(180, 40, 30))
    a = np.asarray(img.filter(ImageFilter.GaussianBlur(.8))).astype(float) + rng.normal(0, 4, (h, w, 3))
    Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)).save(os.path.join(OUT, name + ".jpg"), quality=86)

portrait("portrait_noble", (52, 40, 30), (196, 150, 118), (60, 20, 26))
portrait("portrait_saint", (30, 34, 52), (205, 168, 135), (40, 50, 90), halo=True)
portrait("portrait_widow", (22, 26, 24), (180, 140, 112), (18, 18, 20))
landscape("landscape_dusk", (230, 150, 90), (90, 70, 90), (50, 60, 45))
landscape("landscape_valley", (150, 180, 200), (210, 200, 170), (70, 90, 55), water=False)
landscape("storm_sea", (70, 80, 90), (40, 50, 60), (30, 40, 50), storm=True)
still_life("still_life")
ink_scroll("scroll_bamboo", "bamboo")
ink_scroll("scroll_cranes", "cranes")
print(sorted(os.listdir(OUT)))
