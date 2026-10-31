"""Trees and bushes: London planes with lumpy, sunlit canopies and mottled bark."""
import numpy as np

from paint import Layer, Shape, blur, hexc, lambert, lerp, noise, ramp, smoothstep

# leaf colours from deep shade to sunlit edge
GREENS = [(0.0, '#123826'), (0.22, '#1f5530'), (0.45, '#2f7536'), (0.66, '#4f9a3b'), (0.84, '#86bf47'), (1.0, '#d3e586')]
GREENS_FAR = [(0.0, '#2c5a4a'), (0.35, '#3d7556'), (0.65, '#5f9a5e'), (0.88, '#93c071'), (1.0, '#c9e0a0')]
BARK = ['#7d7a5e', '#9a9478', '#b5b09a', '#d2c9a6', '#6e6b52']


def _clump_centres(rng, cx, cy, rx, ry, n):
    """Clump centres spread through the crown envelope, a little denser at the rim."""
    pts = []
    tries = 0
    min_d = np.sqrt(np.pi * rx * ry / n) * 0.62
    while len(pts) < n and tries < 4000:
        tries += 1
        a = rng.uniform(0, 2 * np.pi)
        d = np.sqrt(rng.uniform(0, 1)) ** 0.8
        x, y = cx + np.cos(a) * rx * d * 0.86, cy + np.sin(a) * ry * d * 0.84
        if all((x - p[0]) ** 2 + (y - p[1]) ** 2 > min_d ** 2 for p in pts):
            pts.append((x, y, d))
    return pts, min_d


def canopy(w, h, seed, leaf=6.0, clumps=None, greens=GREENS, envelope=None, depth_shade=0.22):
    """A canopy painted into its own w x h layer; returns (layer, alpha).

    The crown is built from leaf masses painted back to front. Each mass is lit on its own
    (sunlit upper left, shaded underside) and casts a soft shadow on the masses behind it;
    the light falls in soft painterly bands whose edges break into leaf clumps."""
    rng = np.random.default_rng(seed)
    L = Layer(w, h)
    cx, cy, rx, ry = envelope or (w / 2, h * 0.53, w * 0.42, h * 0.40)
    n = clumps or int(9 + (rx * ry) / 7000)
    n = min(n, 26)
    pts, spacing = _clump_centres(rng, cx, cy, rx, ry, n)
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    n_fine = noise(h, w, leaf * 1.1, 2, seed + 21)
    n_mid = noise(h, w, leaf * 2.8, 3, seed + 22)
    total = np.zeros((h, w), np.float32)
    # the shaded core of the crown, so the masses read as one tree
    th0 = np.arctan2(yy - cy, xx - cx)
    wob0 = 1 + 0.06 * np.cos(3 * th0 + rng.uniform(0, 6.3)) + 0.04 * np.cos(5 * th0 + rng.uniform(0, 6.3))
    core_d = np.sqrt(((xx - cx) / (rx * 0.74)) ** 2 + ((yy - cy) / (ry * 0.72)) ** 2) / wob0
    core = smoothstep(1.0, 0.96, core_d + n_mid * 0.05 + n_fine * 0.03)
    core_t = np.clip(0.28 + lambert(np.sqrt(np.clip(1 - core_d ** 2, 0, None)) * min(rx, ry), 1.0) * 0.12, 0, 1)
    L.paint((core, 0, 0), ramp(greens, core_t))
    total = core.copy()
    order = sorted(range(len(pts)), key=lambda i: rng.uniform(0, 1) * 0.6 + (1 - pts[i][2]) * 0.4)
    sun_dx, sun_dy = 0.55, 0.62
    for rank, i in enumerate(order):
        x, y, d = pts[i]
        depth = rank / max(len(order) - 1, 1)  # 0 = at the back, 1 = in front
        r = spacing * rng.uniform(1.12, 1.42) * (0.88 if d > 0.8 else 1.0)
        th = np.arctan2(yy - y, xx - x)
        wob = 1 + 0.08 * np.cos(3 * th + rng.uniform(0, 6.3)) + 0.05 * np.cos(5 * th + rng.uniform(0, 6.3))
        dist = np.sqrt((xx - x) ** 2 + ((yy - y) * 1.08) ** 2) / wob
        edge = r - dist + n_mid * leaf * 1.3 + n_fine * leaf * 0.7
        a = smoothstep(-0.9, 0.9, edge)
        if a.max() < 0.01:
            continue
        # the mass in front shades the masses behind it
        sh = np.roll(np.roll(blur(a, leaf * 2.2), int(leaf * 2.4 * sun_dy), 0), int(leaf * 2.4 * sun_dx), 1)
        L.paint((np.clip(sh * 0.55 * (1 - a), 0, 1), 0, 0), hexc('#0e2a1c'), clip=True, mode='multiply')
        # light on this mass
        u = np.clip(dist / r, 0, 1)
        dome = np.sqrt(np.clip(1 - u * u, 0, None)) * r
        lit = lambert(dome + n_mid * leaf * 0.35 + n_fine * leaf * 0.12, k=1.0)
        t = np.clip(lit * 0.55 + 0.45, 0, 1)
        t = t - smoothstep(cy - ry * 0.3, cy + ry * 1.1, yy) * 0.2 - (1 - depth) * depth_shade
        t += n_fine * 0.05 + n_mid * 0.04
        # soft painterly bands
        bands = (smoothstep(0.30, 0.36, t) + smoothstep(0.52, 0.58, t) + smoothstep(0.72, 0.78, t)) / 3
        t = np.clip(lerp(t, bands, 0.55), 0, 1)
        col = ramp(greens, t)
        tint = rng.uniform(-1, 1, 3).astype(np.float32) * np.array([0.03, 0.022, 0.012], np.float32)
        col = np.clip(col + tint, 0, 1)
        L.paint((a, 0, 0), col)
        total = np.maximum(total, a)
    # bright leaf dabs on the sunlit side of the crown
    sunny = smoothstep(cx + rx * 0.2, cx - rx * 0.8, xx) * smoothstep(cy + ry * 0.2, cy - ry * 0.9, yy)
    dabs = smoothstep(0.42, 0.62, n_fine) * smoothstep(0.1, 0.5, n_mid) * sunny * 0.5
    L.paint((dabs, 0, 0), hexc('#c9e07c'), clip=True)
    # deeper shade in the heart of the crown, low down
    heart = np.exp(-(((xx - cx) / (rx * 0.65)) ** 2 + ((yy - (cy + ry * 0.35)) / (ry * 0.5)) ** 2))
    L.paint((np.clip(heart * 0.32, 0, 1), 0, 0), hexc('#173826'), clip=True, mode='multiply')
    return L, total


def trunk_paths(x, y_base, height, spread, seed, width):
    """A slightly bent trunk that splits into limbs: list of (polyline, width0, width1)."""
    rng = np.random.default_rng(seed)
    top = (x + rng.uniform(-0.05, 0.05) * spread, y_base - height)
    trunk = [(x, y_base), (x + rng.uniform(-0.04, 0.04) * spread, y_base - height * 0.5), top]
    limbs = [(trunk, width, width * 0.72)]
    for k in range(3):
        ang = -np.pi / 2 + (k - 1) * 0.62 + rng.uniform(-0.12, 0.12)
        ln = height * rng.uniform(0.32, 0.46)
        mid = (top[0] + np.cos(ang) * ln * 0.5, top[1] + np.sin(ang) * ln * 0.5 - ln * 0.05)
        end = (top[0] + np.cos(ang) * ln, top[1] + np.sin(ang) * ln)
        limbs.append(([top, mid, end], width * 0.62, width * 0.22))
    return limbs


def tapered(pts, w0, w1):
    """A polygon along a polyline whose width goes from w0 to w1."""
    pts = np.array(pts, np.float32)
    # resample for smoothness
    seg = np.linalg.norm(np.diff(pts, axis=0), axis=1)
    s = np.concatenate([[0], np.cumsum(seg)])
    u = np.linspace(0, s[-1], 24)
    P = np.stack([np.interp(u, s, pts[:, 0]), np.interp(u, s, pts[:, 1])], -1)
    d = np.gradient(P, axis=0)
    d /= np.linalg.norm(d, axis=1, keepdims=True) + 1e-6
    nrm = np.stack([-d[:, 1], d[:, 0]], -1)
    wid = np.linspace(w0, w1, len(P))[:, None] / 2
    left, right = P + nrm * wid, P - nrm * wid
    return [tuple(p) for p in left] + [tuple(p) for p in right[::-1]]


def paint_bark(L, outline, seed, light_side=-1):
    """Mottled plane-tree bark, lit from the left."""
    sh = Shape(*_bbox(outline)).poly(outline)
    rng_seed = seed

    def col(X, Y):
        n = noise(X.shape[0], X.shape[1], 16, 2, rng_seed)
        patches = np.digitize(n, [-0.3, 0.0, 0.25, 0.48])
        cs = np.stack([hexc(c) for c in BARK])
        c = cs[np.clip(patches, 0, len(BARK) - 1)]
        return c

    L.paint(sh, hexc('#9a9478'))
    L.paint(sh, col, alpha=0.45, clip=True)
    # roundness: lit left edge, shaded right edge
    x0, y0, x1, y1 = _bbox(outline)

    def shade(X, Y):
        t = (X - x0) / max(x1 - x0, 1)
        return np.stack([1 - 0.42 * t] * 3, -1) if light_side < 0 else np.stack([0.58 + 0.42 * t] * 3, -1)

    L.paint(sh, shade, clip=True, mode='multiply')


def _bbox(pts):
    xs, ys = [p[0] for p in pts], [p[1] for p in pts]
    return min(xs), min(ys), max(xs), max(ys)


def tree(w, h, seed, trunk_h=0.58, crown=0.74, leaf=None, greens=GREENS, trunk_w=None, clumps=None):
    """A whole tree in its own layer, base centre at (w/2, h - 4). Returns (layer, anchor)."""
    L = Layer(w, h)
    base = (w / 2, h - 4)
    leaf = leaf or max(3.0, w / 120)
    trunk_w = trunk_w or w * 0.075
    ch = int(h * crown)
    crown_layer, alpha = canopy(w, ch, seed, leaf=leaf, greens=greens, clumps=clumps)
    crown_top = 0
    # limbs reach up into the crown
    for k, (pts, w0, w1) in enumerate(trunk_paths(base[0], base[1], h * trunk_h, w * 0.5, seed, trunk_w)):
        outline = tapered(pts, w0, w1)
        if k == 0:  # a little root flare where the trunk meets the ground
            bx, by = base
            flare = [(bx - trunk_w * 1.05, by), (bx - trunk_w * 0.55, by - trunk_w * 0.5), (bx + trunk_w * 0.55, by - trunk_w * 0.5), (bx + trunk_w * 1.05, by)]
            paint_bark(L, flare, seed + 4)
        paint_bark(L, outline, seed + 5)
    # the crown casts soft shade on the upper trunk
    cast = np.zeros((h, w), np.float32)
    cast[crown_top:crown_top + ch] = blur(alpha, leaf * 4)
    cast = np.roll(cast, int(leaf * 5), axis=0)
    L.paint((np.clip(cast * 0.75, 0, 1), 0, 0), hexc('#1d2a22'), clip=True, mode='multiply')
    L.over(crown_layer, 0, crown_top)
    return L, base


def bush(w, h, seed, leaf=None, greens=GREENS):
    leaf = leaf or max(3.0, w / 100)
    L, alpha = canopy(w, h, seed, leaf=leaf, greens=greens, envelope=(w / 2, h * 0.6, w * 0.44, h * 0.46))
    # sit on the ground: flatten the bottom edge
    yy = np.arange(h, dtype=np.float32)[:, None]
    cut = 1 - smoothstep(h - 6, h - 1, yy) * 0
    L.px *= cut[..., None]
    return L, (w / 2, h - 2)
