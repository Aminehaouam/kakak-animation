"""A small painting toolkit for the London artwork.

Shapes are rasterised at 4x and averaged down, so every edge is clean. All artwork is lit by
one sun (upper left, a little in front of the scene), and soft shading comes from height
fields and blurred masks, the way a painter builds form, not from effects added on top.
Layers are kept premultiplied in float32 and saved as trimmed WebP with an anchor point.
"""
import json
import math
import os

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage
from shapely.geometry import LineString, MultiPolygon, Polygon

SS = 4
SUN = np.array([-0.55, -0.62, 0.56], np.float32)  # x right, y down, z toward the viewer
SUN /= np.linalg.norm(SUN)

OUT = os.path.join(os.path.dirname(__file__), '..', 'public', 'art')
MANIFEST = {}


# ---------------------------------------------------------------- colour helpers

def hexc(h):
    h = h.lstrip('#')
    return np.array([int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)], np.float32)


def lerp(a, b, t):
    return a + (b - a) * t


def smoothstep(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0), 0, 1)
    return t * t * (3 - 2 * t)


def ramp(stops, t):
    """Colour ramp: stops = [(t0, '#hex'), ...] ascending; t is an array -> (..., 3)."""
    t = np.asarray(t, np.float32)
    ts = np.array([s[0] for s in stops], np.float32)
    cs = np.stack([hexc(s[1]) if isinstance(s[1], str) else np.asarray(s[1], np.float32) for s in stops])
    out = np.empty(t.shape + (3,), np.float32)
    for c in range(3):
        out[..., c] = np.interp(t, ts, cs[:, c])
    return out


# ---------------------------------------------------------------- noise and blur

def noise(h, w, cell, octaves=4, seed=0, persistence=0.55):
    """Smooth value noise in about [-1, 1], with `cell` the size of the largest blobs in pixels."""
    rng = np.random.default_rng(seed)
    total = np.zeros((h, w), np.float32)
    amp, norm = 1.0, 0.0
    for _ in range(octaves):
        c = max(cell, 1.5)
        gh, gw = int(h / c) + 4, int(w / c) + 4
        g = rng.random((gh, gw), dtype=np.float32)
        img = Image.fromarray(g, 'F').resize((int(gw * c), int(gh * c)), Image.BICUBIC)
        a = np.asarray(img, np.float32)
        oy, ox = rng.integers(0, max(1, int(c))), rng.integers(0, max(1, int(c)))
        total += a[oy:oy + h, ox:ox + w] * amp
        norm += amp
        amp *= persistence
        cell /= 2
    return (total / norm) * 2 - 1


def blur(a, sigma):
    if sigma <= 0:
        return a
    if a.ndim == 3:
        return np.stack([ndimage.gaussian_filter(a[..., i], sigma, mode='nearest') for i in range(a.shape[2])], -1)
    return ndimage.gaussian_filter(a, sigma, mode='nearest')


def normals(hf, k=1.0):
    gy, gx = np.gradient(hf)
    nx, ny, nz = -gx * k, -gy * k, np.ones_like(hf)
    n = np.sqrt(nx * nx + ny * ny + nz * nz)
    return nx / n, ny / n, nz / n


def lambert(hf, k=1.0, sun=SUN):
    nx, ny, nz = normals(hf, k)
    return nx * sun[0] + ny * sun[1] + nz * sun[2]


# ---------------------------------------------------------------- shapes

class Shape:
    """Shapes drawn at SS x into a local box; `a` is the float coverage at 1x, placed at (x0, y0)."""

    def __init__(self, x0, y0, x1, y1):
        self.x0, self.y0 = int(math.floor(x0)) - 2, int(math.floor(y0)) - 2
        self.x1, self.y1 = int(math.ceil(x1)) + 2, int(math.ceil(y1)) + 2
        self.w, self.h = self.x1 - self.x0, self.y1 - self.y0
        self.img = Image.new('L', (self.w * SS, self.h * SS), 0)
        self.d = ImageDraw.Draw(self.img)
        self._a = None

    def _p(self, pts):
        return [((x - self.x0) * SS, (y - self.y0) * SS) for x, y in pts]

    def poly(self, pts, v=255):
        if len(pts) >= 3:
            self.d.polygon(self._p(pts), fill=v)
        self._a = None
        return self

    def rect(self, x0, y0, x1, y1, v=255):
        return self.poly([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], v)

    def ellipse(self, cx, cy, rx, ry, v=255):
        self.d.ellipse([((cx - rx) - self.x0) * SS, ((cy - ry) - self.y0) * SS, ((cx + rx) - self.x0) * SS, ((cy + ry) - self.y0) * SS], fill=v)
        self._a = None
        return self

    def geom(self, g, v=255):
        """A shapely polygon or multipolygon, holes included."""
        polys = g.geoms if isinstance(g, MultiPolygon) else [g]
        for p in polys:
            if p.is_empty:
                continue
            self.poly(list(p.exterior.coords), v)
            for hole in p.interiors:
                self.poly(list(hole.coords), 0 if v else 255)
        return self

    def stroke(self, pts, w, v=255, cap='round', join='round'):
        caps = {'round': 1, 'flat': 2, 'square': 3}
        joins = {'round': 1, 'mitre': 2, 'bevel': 3}
        g = LineString(pts).buffer(w / 2, cap_style=caps[cap], join_style=joins[join], quad_segs=6)
        return self.geom(g, v)

    @property
    def a(self):
        if self._a is None:
            self._a = np.asarray(self.img.reduce(SS), np.float32) / 255
        return self._a


def bbox_of(pts, pad=0):
    xs, ys = [p[0] for p in pts], [p[1] for p in pts]
    return min(xs) - pad, min(ys) - pad, max(xs) + pad, max(ys) + pad


def poly(pts):
    return Shape(*bbox_of(pts)).poly(pts)


def rect(x0, y0, x1, y1):
    return Shape(x0, y0, x1, y1).rect(x0, y0, x1, y1)


def ellipse(cx, cy, rx, ry):
    return Shape(cx - rx, cy - ry, cx + rx, cy + ry).ellipse(cx, cy, rx, ry)


def stroke(pts, w, cap='round', join='round'):
    x0, y0, x1, y1 = bbox_of(pts, w)
    return Shape(x0, y0, x1, y1).stroke(pts, w, cap=cap, join=join)


def bezier(p0, p1, p2, p3, n=24):
    t = np.linspace(0, 1, n)[:, None]
    p0, p1, p2, p3 = (np.array(p, np.float32) for p in (p0, p1, p2, p3))
    pts = (1 - t) ** 3 * p0 + 3 * (1 - t) ** 2 * t * p1 + 3 * (1 - t) * t ** 2 * p2 + t ** 3 * p3
    return [tuple(p) for p in pts]


def quad(p0, p1, p2, n=20):
    t = np.linspace(0, 1, n)[:, None]
    p0, p1, p2 = (np.array(p, np.float32) for p in (p0, p1, p2))
    pts = (1 - t) ** 2 * p0 + 2 * (1 - t) * t * p1 + t ** 2 * p2
    return [tuple(p) for p in pts]


# ---------------------------------------------------------------- layers

class Layer:
    def __init__(self, w, h):
        self.w, self.h = int(w), int(h)
        self.px = np.zeros((self.h, self.w, 4), np.float32)  # premultiplied

    def _clip(self, x0, y0, w, h):
        lx0, ly0 = max(x0, 0), max(y0, 0)
        lx1, ly1 = min(x0 + w, self.w), min(y0 + h, self.h)
        if lx1 <= lx0 or ly1 <= ly0:
            return None
        return (slice(ly0, ly1), slice(lx0, lx1)), (slice(ly0 - y0, ly1 - y0), slice(lx0 - x0, lx1 - x0)), (lx0, ly0, lx1, ly1)

    @staticmethod
    def _colour(color, X, Y):
        if callable(color):
            c = color(X, Y)
        else:
            c = np.asarray(color if not isinstance(color, str) else hexc(color), np.float32)
        c = np.asarray(c, np.float32)
        if c.ndim == 1:
            c = np.broadcast_to(c, X.shape + (3,))
        return c

    def grid(self, box):
        lx0, ly0, lx1, ly1 = box
        return np.meshgrid(np.arange(lx0, lx1, dtype=np.float32) + 0.5, np.arange(ly0, ly1, dtype=np.float32) + 0.5)

    def paint(self, shape, color, alpha=1.0, clip=False, mode='over'):
        """Paint `color` through `shape` (a Shape, or (array, x0, y0)).

        clip: only where the layer already has paint (like a clipping mask).
        mode: 'over', 'multiply' (darken existing paint), 'screen' (lighten existing paint),
        'erase' (cut away existing paint)."""
        a, x0, y0 = (shape.a, shape.x0, shape.y0) if isinstance(shape, Shape) else shape
        r = self._clip(x0, y0, a.shape[1], a.shape[0])
        if r is None:
            return self
        dst_s, src_s, box = r
        cov = a[src_s]
        if np.ndim(alpha) == 0:
            cov = cov * float(alpha)
        else:
            cov = cov * np.asarray(alpha, np.float32)[src_s] if np.shape(alpha) == a.shape else cov * alpha
        dst = self.px[dst_s]
        if clip:
            cov = cov * dst[..., 3]
        if mode == 'erase':
            dst *= (1 - cov)[..., None]
            return self
        X, Y = self.grid(box)
        c = self._colour(color, X, Y)
        k = cov[..., None]
        if mode == 'over':
            dst[..., :3] = c * k + dst[..., :3] * (1 - k)
            dst[..., 3] = cov + dst[..., 3] * (1 - cov)
        elif mode == 'multiply':
            dst[..., :3] *= 1 - k * (1 - c)
        elif mode == 'screen':
            al = dst[..., 3:4]
            dst[..., :3] = al - (al - dst[..., :3]) * (1 - c * k)
        return self

    def fill_all(self, color, alpha=1.0):
        a = np.ones((self.h, self.w), np.float32)
        return self.paint((a, 0, 0), color, alpha)

    def alpha(self):
        return self.px[..., 3]

    def under(self, other, dx=0, dy=0):
        """Composite `other` (a Layer) beneath this one."""
        r = self._clip(dx, dy, other.w, other.h)
        if r is None:
            return self
        dst_s, src_s, _ = r
        top = self.px[dst_s].copy()
        bot = other.px[src_s]
        self.px[dst_s] = top + bot * (1 - top[..., 3:4])
        return self

    def over(self, other, dx=0, dy=0, alpha=1.0):
        """Composite `other` (a Layer) on top of this one."""
        r = self._clip(dx, dy, other.w, other.h)
        if r is None:
            return self
        dst_s, src_s, _ = r
        top = other.px[src_s] * alpha
        self.px[dst_s] = top + self.px[dst_s] * (1 - top[..., 3:4])
        return self

    def straight(self):
        a = self.px[..., 3:4]
        rgb = np.where(a > 1e-5, self.px[..., :3] / np.maximum(a, 1e-5), 0)
        return np.concatenate([np.clip(rgb, 0, 1), np.clip(a, 0, 1)], -1)

    def image(self):
        return Image.fromarray((self.straight() * 255 + 0.5).astype(np.uint8), 'RGBA')

    def save(self, name, anchor=(0, 0), crop=True, pad=3, quality=92, lossless=False, meta=None):
        """Save as public/art/<name>.webp, trimmed; the manifest records where `anchor` (layer
        pixel coordinates) lands in the saved image."""
        img = self.image()
        x0, y0 = 0, 0
        if crop:
            bb = img.getchannel('A').point(lambda v: 255 if v > 1 else 0).getbbox()
            if bb:
                x0, y0 = max(bb[0] - pad, 0), max(bb[1] - pad, 0)
                x1, y1 = min(bb[2] + pad, self.w), min(bb[3] + pad, self.h)
                img = img.crop((x0, y0, x1, y1))
        os.makedirs(OUT, exist_ok=True)
        path = os.path.join(OUT, f'{name}.webp')
        img.save(path, 'WEBP', quality=quality, lossless=lossless, method=6, alpha_quality=100, exact=True)
        MANIFEST[name] = {'file': f'art/{name}.webp', 'w': img.width, 'h': img.height,
                          'ax': round(anchor[0] - x0, 2), 'ay': round(anchor[1] - y0, 2), **(meta or {})}
        return img


def write_manifest(extra=None):
    path = os.path.join(OUT, 'manifest.json')
    data = {}
    if os.path.exists(path):
        data = json.load(open(path))
    data.update(MANIFEST)
    if extra:
        data.update(extra)
    json.dump(dict(sorted(data.items())), open(path, 'w'), indent=1)


def preview(layer, path, bg='#8fb8d8', scale=1.0):
    """Flatten a layer over a plain colour for a quick look."""
    img = layer.image()
    if scale != 1:
        img = img.resize((int(img.width * scale), int(img.height * scale)), Image.LANCZOS)
    base = Image.new('RGBA', img.size, bg)
    base.alpha_composite(img)
    base.convert('RGB').save(path, quality=90)
