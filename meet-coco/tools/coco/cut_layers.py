"""Cut Coco (reference/coco_x4.png) into the cut-out layers of the Rive rig.

Every moving piece becomes its own transparent PNG, and what it hides is painted in: the body
behind the wing, the neck under the head, chin feathers behind the lower beak, the eye ring
behind the pupil, the tail's root under the wing. The spread flight wing does not exist in the
drawing; it is painted here in the colours and soft shading of Coco's folded wing.

Coordinates are pixels of the original drawing (reference/coco.jpg, 188 x 425); the textures
are 4x (reference/coco_x4.png, an upscale of it). Output: layers/<name>.png + layers/layers.json
(where each layer sits, in drawing px).

usage: python3 tools/coco/cut_layers.py [--debug dir]
"""
import json
import math
import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, 'reference', 'coco_x4.png')
OUT = os.path.join(HERE, 'layers')
K = 4  # texture px per drawing px


# --------------------------------------------------------------------------- helpers

def catmull(pts, closed=True, n=10):
    p = np.asarray(pts, float)
    m = len(p)
    out = []
    for i in range(m if closed else m - 1):
        p0 = p[(i - 1) % m] if (closed or i > 0) else p[i]
        p1, p2 = p[i], p[(i + 1) % m]
        p3 = p[(i + 2) % m] if (closed or i + 2 < m) else p2
        for t in np.linspace(0, 1, n, endpoint=False):
            out.append(0.5 * (2 * p1 + (p2 - p0) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t
                              + (3 * p1 - p0 - 3 * p2 + p3) * t ** 3))
    if not closed:
        out.append(p[-1])
    return [tuple(q) for q in out]


def ellipse_pts(cx, cy, rx, ry, rot=0.0, n=64):
    a = math.radians(rot)
    t = np.linspace(0, 2 * np.pi, n, endpoint=False)
    x, y = rx * np.cos(t), ry * np.sin(t)
    return list(zip(cx + x * math.cos(a) - y * math.sin(a), cy + x * math.sin(a) + y * math.cos(a)))


def poly_mask(pts, shape, ss=4):
    h, w = shape
    img = Image.new('L', (w * ss, h * ss), 0)
    ImageDraw.Draw(img).polygon([(x * K * ss, y * K * ss) for x, y in pts], fill=255)
    return np.asarray(img.resize((w, h), Image.BOX), np.float32) / 255.0


def shift(a, dy, dx):
    out = np.zeros_like(a)
    h, w = a.shape[:2]
    out[max(dy, 0):h + min(dy, 0), max(dx, 0):w + min(dx, 0)] = \
        a[max(-dy, 0):h + min(-dy, 0), max(-dx, 0):w + min(-dx, 0)]
    return out


NB8 = [(dy, dx) for dy in (-1, 0, 1) for dx in (-1, 0, 1) if dy or dx]


def dilate(m, r=1):
    for _ in range(r):
        o = m.copy()
        for dy, dx in NB8:
            o |= shift(m, dy, dx)
        m = o
    return m


def flood(dark, seeds):
    img = Image.fromarray(np.where(dark, 0, 255).astype(np.uint8)).copy()
    for x, y in seeds:
        if img.getpixel((x, y)) == 0:
            ImageDraw.floodfill(img, (x, y), 128, thresh=0)
    return np.asarray(img) == 128


def propagate(rgb, known, todo, iters):
    rgb = rgb.copy()
    known = known.copy()
    for _ in range(iters):
        kf = known.astype(np.float32)
        s = np.zeros_like(rgb)
        n = np.zeros(known.shape, np.float32)
        for dy, dx in NB8:
            s += shift(rgb * kf[..., None], dy, dx)
            n += shift(kf, dy, dx)
        new = todo & ~known & (n > 0)
        if not new.any():
            break
        rgb[new] = s[new] / n[new][:, None]
        known |= new
    return rgb, known


def fill(rgb, known, todo, iters=40):
    """Smooth multigrid (push-pull + Jacobi) fill of `todo` from the `known` colours."""
    ys, xs = np.nonzero(todo)
    if len(ys) == 0:
        return rgb
    m = 24
    y0, y1 = max(ys.min() - m, 0), min(ys.max() + m + 1, rgb.shape[0])
    x0, x1 = max(xs.min() - m, 0), min(xs.max() + m + 1, rgb.shape[1])
    win = (slice(y0, y1), slice(x0, x1))
    t = todo[win] & ~known[win]
    sub = _fill(rgb[win].astype(np.float64), known[win], t, iters)
    out = rgb.copy()
    out[win][t] = sub[t]
    return out


def _fill(c, known, todo, iters):
    h, w = known.shape
    if min(h, w) <= 6 or not known.any():
        r, _ = propagate(c.astype(np.float32), known, np.ones_like(known), 10000)
        return r.astype(np.float64)
    h2, w2 = (h + 1) // 2, (w + 1) // 2

    def down(a):
        p = np.zeros((h2 * 2, w2 * 2) + a.shape[2:], a.dtype)
        p[:h, :w] = a
        return p.reshape((h2, 2, w2, 2) + a.shape[2:]).sum((1, 3))

    kw = down(known.astype(np.float64))
    kc = down(c * known[..., None]) / np.maximum(kw, 1e-9)[..., None]
    known2 = kw > 0
    todo2 = (down(todo.astype(np.float64)) > 0) & ~known2
    coarse = _fill(kc, known2, todo2, iters)
    up = np.repeat(np.repeat(coarse, 2, 0), 2, 1)[:h, :w]
    c = c.copy()
    c[todo] = up[todo]
    act = (known | todo).astype(np.float64)
    for _ in range(iters):
        s = np.zeros_like(c)
        n = np.zeros((h, w))
        for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            s += shift(c * act[..., None], dy, dx)
            n += shift(act, dy, dx)
        upd = todo & (n > 0)
        c[upd] = s[upd] / n[upd][:, None]
    return c


def smoothstep(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0), 0, 1)
    return t * t * (3 - 2 * t)


def lum(rgb):
    return rgb[..., 0] * 0.299 + rgb[..., 1] * 0.587 + rgb[..., 2] * 0.114


def redness(rgb):
    return (rgb[..., 0] - np.maximum(rgb[..., 1], rgb[..., 2])) / 255.0


def matte(rgb):
    """Alpha of the bird over the black background and its un-premultiplied colour."""
    h, w = rgb.shape[:2]
    dark = rgb.max(2) <= 8
    bg = flood(dark, [(0, 0), (w - 1, 0), (0, h - 1), (w - 1, h - 1), (98 * K, 340 * K)])
    band = dilate(bg, 5) & ~bg
    core = ~bg & ~band
    fg, _ = propagate(rgb, core, band, 10)
    proj = (rgb * fg).sum(2) / np.maximum((fg * fg).sum(2), 1e-3)
    alpha = np.where(core, 1.0, np.where(band, np.clip(proj, 0, 1), 0.0)).astype(np.float32)
    return alpha, np.where(core[..., None], rgb, fg)


def below_line(line, shape, soft=(0.0, 0.0)):
    """1 below a polyline y(x) (drawing px), 0 above, with a soft ramp from soft[0] to soft[1]."""
    ys, xs = np.mgrid[0:shape[0], 0:shape[1]]
    lx, ly = zip(*line)
    d = (ys + 0.5) / K - np.interp((xs + 0.5) / K, lx, ly)
    if soft[1] == soft[0]:
        return (d > soft[0]).astype(np.float32)
    return smoothstep(soft[0], soft[1], d)


# --------------------------------------------------------------------------- landmarks (drawing px)

GAPE = [(128, 140), (136.5, 145), (140, 148.5), (145, 153), (150, 156), (155, 158), (160, 159),
        (164, 162.5), (168, 166.3), (176, 169), (190, 171)]
UPPER_BEAK_ROI = [(130, 92), (150, 90), (174, 98), (188, 115), (192, 140), (191, 162)] + GAPE[::-1]
MANDIBLE_ROI = GAPE + [(186, 182), (160, 188), (140, 188), (127, 178), (127, 150)]
NOSTRIL = ellipse_pts(153.5, 110.4, 5.0, 3.2)
CHIN = [(127, 140), (136, 143.5), (140, 146), (145, 149.3), (150, 151), (155, 151.5),
        (158.7, 152.4), (162.8, 160.4), (167, 168.4), (161, 171.5), (156, 175.5), (151, 181),
        (148, 190), (128, 190)]
PUPIL = ellipse_pts(115.3, 137.0, 12.5, 17.0, rot=-9)
WING_ROI = [(80, 207), (100, 203), (122, 209), (131, 232), (131, 252), (125, 272), (114, 290),
            (104, 294), (98, 298.5), (92, 303.5), (88, 306.5), (84, 309.5), (80, 312), (76, 314),
            (72, 318), (60, 328), (40, 336), (20, 330), (14, 312), (24, 282), (48, 236), (70, 214)]
BODY_BACK = (catmull([(84, 205), (77, 214), (69, 227), (61, 242), (55, 258), (51, 275), (50, 290),
                      (51, 302), (55, 311)], closed=False, n=8)
             + [(60, 316), (64, 314.8), (68, 312.8), (72, 311.6), (76, 310.5), (79, 316),
                (90, 322), (112, 315), (132, 290), (142, 255), (136, 215), (110, 203)])
TAIL_ROI = [(0, 296), (96, 296), (96, 380), (0, 380)]
TAIL_ROOT = catmull([(34, 321), (40, 313), (48, 307), (58, 305), (72, 304), (82, 305), (87, 312),
                     (87, 328), (84, 342), (79, 348), (74, 336), (66, 328), (50, 328), (38, 326)],
                    closed=True, n=8)

# head / body boundary; the head fades out over HEAD_FADE px below it and the body keeps the
# drawing from BODY_KEEP px above it, so they overlap. Above that the body gets a feathered neck
# dome (hidden under the head at rest) so a tilting head never uncovers a gap.
NECK = [(0, 197), (60, 197), (80, 199), (100, 197), (120, 195), (140, 189), (160, 186), (300, 186)]
HEAD_FADE = 7.0
BODY_KEEP = 9.0
NECK_DOME = catmull([(52, 204), (53, 184), (60, 168), (76, 157), (100, 153), (124, 156),
                     (139, 164), (147, 176), (150, 192), (150, 204)], closed=True, n=8)
# body / legs boundary: the thighs leave the belly here; the legs layer reaches LEGS_OVERLAP px
# above it (hidden behind the belly) so the joint never opens
BELLY = [(0, 312), (72, 312), (80, 316), (90, 320.5), (98, 322.5), (106, 321.5), (116, 318.5),
         (128, 314), (200, 310)]
LEGS_OVERLAP = 9.0


# --------------------------------------------------------------------------- the cut

def cut(rgb):
    alpha, color = matte(rgb)
    shape = alpha.shape
    L = lum(color)
    red = redness(color)
    layers = {}

    # beak, pupil, wing, tail memberships (colour edges inside the drawing)
    beak_grey = 1 - smoothstep(100, 135, L)
    not_gape = smoothstep(32, 52, L)
    nostril = poly_mask(NOSTRIL, shape)
    layers['upperBeak'] = (color, alpha * poly_mask(UPPER_BEAK_ROI, shape) * beak_grey
                           * np.maximum(not_gape, nostril))
    mand_roi = poly_mask(MANDIBLE_ROI, shape)
    layers['mandible'] = (color, alpha * mand_roi * beak_grey * not_gape)

    pupil_roi = poly_mask(PUPIL, shape)
    ring_white, ink = 254.0, 22.0
    pa = np.clip((ring_white - L) / (ring_white - ink), 0, 1) * pupil_roi
    unmixed = (color - (1 - pa[..., None]) * ring_white) / np.maximum(pa, 1e-3)[..., None]
    layers['pupil'] = (np.where((pa > 0.3)[..., None], np.clip(unmixed, 0, 255),
                                np.array([24, 24, 30], np.float32)), pa)

    wing_m = (poly_mask(WING_ROI, shape) * (1 - smoothstep(118, 138, L))
              * (1 - smoothstep(0.10, 0.25, red)))
    layers['wingFolded'] = (color, alpha * wing_m)

    tail_m = poly_mask(TAIL_ROI, shape) * smoothstep(0.12, 0.30, red)
    tail_vis = alpha * tail_m

    # ---- the whole bird minus the tail and wing, painted in behind them
    base_col = color.copy()
    base_a = alpha * (1 - smoothstep(0.6, 0.95, tail_m))
    leg = (alpha > 0.5) & (red < 0.1) & (L > 120) & (poly_mask(TAIL_ROOT, shape) > 0)
    leg_line = dilate(leg, 6) & (tail_m > 0) & (L < 84)
    base_a = np.where(leg_line, alpha, base_a)
    back = poly_mask(BODY_BACK, shape)
    w_area = dilate(wing_m > 0.02, 3)
    body_known = (base_a > 0.98) & ~w_area & (L > 135) & (red < 0.1)
    base_col = np.where((w_area & (back > 0))[..., None],
                        fill(color, body_known, w_area & (back > 0)), base_col)
    base_a = base_a * (1 - wing_m * (1 - back))
    chin = poly_mask(CHIN, shape)
    mouth_stuff = mand_roi * (1 - smoothstep(100, 135, L))
    m_area = dilate(mouth_stuff > 0.02, 3) & (chin > 0)
    chin_known = (alpha > 0.98) & (L > 135) & ~dilate(mouth_stuff > 0.02, 3)
    chin_known &= poly_mask([(118, 140), (150, 140), (150, 196), (118, 196)], shape) > 0
    base_col = np.where(m_area[..., None], fill(color, chin_known, m_area), base_col)
    base_a = base_a * (1 - mouth_stuff * (1 - chin))
    ring_known = (L > 236) & (pupil_roi < 0.02) & dilate(pupil_roi > 0, 24)
    base_col = base_col + (fill(color, ring_known, pupil_roi > 0) - base_col) * pupil_roi[..., None]

    # ---- head: above the neck line, fading out below it
    head_a = base_a * (1 - below_line(NECK, shape, (0.0, HEAD_FADE)))
    layers['head'] = (base_col, head_a)

    # ---- body: below the neck line (overlapping the head), above the belly, plus the neck dome
    keep = below_line(NECK, shape, (-BODY_KEEP - 1.5, -BODY_KEEP))
    dome = poly_mask(NECK_DOME, shape)
    dome_todo = (dome > 0) & (keep < 0.999)
    neck_known = (keep > 0.999) & (base_a > 0.98) & (L > 135) & dilate(dome > 0, 40)
    body_col = np.where(dome_todo[..., None], fill(base_col, neck_known, dome_todo), base_col)
    body_a = np.maximum(base_a * keep, dome * (base_a > 0.5))
    not_legs = 1 - below_line(BELLY, shape, (0.0, 2.0))
    layers['body'] = (body_col, body_a * not_legs)

    # ---- legs: below the belly line, reaching up behind it
    legs_a = base_a * below_line(BELLY, shape, (-LEGS_OVERLAP, -LEGS_OVERLAP + 1.5))
    legs_a *= poly_mask([(76, 300), (134, 300), (160, 380), (55, 380)], shape)
    legs_a *= 1 - smoothstep(0.06, 0.15, red)          # the tail's red edge stays with the tail
    layers['legs'] = (base_col, legs_a)

    # ---- tail with its root painted under the wing, rump and leg
    root = poly_mask(TAIL_ROOT, shape) * smoothstep(0.9, 1.0, alpha)
    tail_known = ((tail_vis > 0.9) & (alpha > 0.95) & (red > 0.42) & ~dilate(wing_m > 0.02, 6)
                  & ~leg_line)
    tail_col = fill(color, tail_known, (root > 0) & ((tail_vis < 0.9) | leg_line))
    tail_col = np.where(((tail_vis >= 0.9) & ~leg_line)[..., None], color, tail_col)
    layers['tail'] = (tail_col, np.maximum(tail_vis, root))

    return layers, color, alpha


# --------------------------------------------------------------------------- mouth interior

# the dark gape between the beaks (measured): top = underside of the upper beak, bottom = top of
# the mandible. The interior hangs from the mandible and reaches up behind the upper beak, so an
# opening beak shows the inside of the mouth and a closing one tucks it away.
GAPE_TOP = [(136.4, 144.3), (138, 145.25), (140, 146.75), (142, 148.25), (144, 149.5),
            (146, 150.25), (148, 151.0), (150, 151.75), (152, 152.0), (154, 152.25), (156, 152.0),
            (158, 151.75), (160, 152.5)]
GAPE_BOTTOM = [(137, 145.75), (138, 147.25), (140, 150.25), (142, 152.5), (144, 154.75),
               (146, 156.75), (148, 158.5), (150, 160.25), (152, 162.0), (154, 163.5),
               (156, 164.5), (158, 165.25), (160, 166.0), (162, 166.25), (164, 166.5),
               (166, 166.5), (168.3, 166.9)]


def mouth_interior(shape):
    # the top reaches up behind the upper beak, except at the corner of the gape, where nothing
    # covers it: there the outline closes on the drawn corner
    top = [(x, y - 7.0 * float(smoothstep(139.0, 146.0, x))) for x, y in GAPE_TOP]
    bottom = [(x, y + 1.0) for x, y in GAPE_BOTTOM]     # tucked under the mandible's edge
    side = [(160.8, 150.0), (163, 155), (165.5, 160.5), (168.6, 166.4)]  # the open side
    a = poly_mask(top[:-1] + side + bottom[::-1], shape)
    # the drawn gape is near black, like an African grey's mouth; the part hidden behind the upper
    # beak at rest is a little warmer, so a wide-open beak shows some depth
    col = np.zeros(shape + (3,), np.float32) + np.array([28, 28, 33], np.float32)
    deep = 1 - below_line(GAPE_TOP, shape, (-6.0, -2.0))
    col += deep[..., None] * np.array([22, 10, 12], np.float32)
    return col, a


# --------------------------------------------------------------------------- the flight wing

def paint_open_wing(scale=K, ss=2):
    """Coco's spread wing pointing up from the shoulder, painted like the drawing's folded wing:
    one soft rounded shape with a scalloped trailing edge, a lighter leading edge and covert
    area, darker feather tips and a few blurred feather strokes. No outlines.

    Local frame: drawing px, shoulder at (0, 0), +x toward the beak, -y up. Returns
    (rgba uint8, (x, y) of the shoulder inside the image, in drawing px)."""
    x0, y0, x1, y1 = -100, -122, 22, 22
    S = scale * ss
    W, H = int((x1 - x0) * S), int((y1 - y0) * S)
    yy, xx = np.mgrid[0:H, 0:W]
    X, Y = xx / S + x0, yy / S + y0                      # drawing px, wing-local

    # silhouette: leading edge up from the shoulder to the tip, then a scalloped trailing edge
    lead = [(5, 6), (9, -14), (8, -36), (2, -58), (-9, -82), (-22, -103), (-30, -112)]
    tips = [(-30, -112), (-49, -104), (-64, -91), (-77, -73), (-85, -53), (-86, -33),
            (-80, -15), (-67, -1), (-49, 9), (-29, 14), (-10, 13)]
    centre = np.array([-34.0, -42.0])
    trail = []
    for i in range(len(tips) - 1):
        p0, p1 = np.array(tips[i], float), np.array(tips[i + 1], float)
        mid = (p0 + p1) / 2
        out = mid - centre
        out /= np.linalg.norm(out)
        trail += [tuple(p0), tuple(mid + out * 3.2)]     # a rounded feather tip between notches
        notch = p1 + (centre - p1) / np.linalg.norm(centre - p1) * 4.0
        trail.append(tuple(notch))
    trail.append(tips[-1])
    outline = catmull(lead + trail + [(0, 14)], closed=True, n=8)
    m = Image.new('L', (W, H), 0)
    ImageDraw.Draw(m).polygon([((x - x0) * S, (y - y0) * S) for x, y in outline], fill=255)
    mask = np.asarray(m.filter(ImageFilter.GaussianBlur(0.35 * S)), np.float32) / 255.0

    # shading: distance from the leading edge (0 = front, 1 = trailing feather tips)
    lead_arr = np.array(catmull(lead, closed=False, n=12))
    d_lead = np.full(X.shape, 1e9)
    for (ax, ay), (bx, by) in zip(lead_arr[:-1], lead_arr[1:]):
        vx, vy = bx - ax, by - ay
        t = np.clip(((X - ax) * vx + (Y - ay) * vy) / (vx * vx + vy * vy), 0, 1)
        d_lead = np.minimum(d_lead, np.hypot(X - ax - t * vx, Y - ay - t * vy))
    reach = np.hypot(X - 0, Y - 0)
    depth = np.clip(d_lead / 62.0, 0, 1)
    light = np.array([126, 125, 142], np.float32)
    mid = np.array([106, 106, 123], np.float32)
    dark = np.array([84, 84, 101], np.float32)
    col = light + (mid - light) * smoothstep(0.0, 0.45, depth)[..., None]
    col = col + (dark - col) * (smoothstep(0.55, 1.0, depth) * 0.85)[..., None]
    col *= (1 - 0.06 * smoothstep(60, 110, reach))[..., None]          # far tips a touch darker

    # coverts: a softly scalloped lighter area along the front, near the shoulder
    cov = Image.new('L', (W, H), 0)
    cpts = catmull([(7, 4), (9, -18), (5, -40), (-4, -55), (-18, -60), (-30, -50), (-38, -36),
                    (-40, -18), (-32, -4), (-18, 6)], closed=True, n=10)
    ImageDraw.Draw(cov).polygon([((x - x0) * S, (y - y0) * S) for x, y in cpts], fill=255)
    cov = np.asarray(cov.filter(ImageFilter.GaussianBlur(1.6 * S)), np.float32) / 255.0
    col = col + (np.array([132, 131, 147], np.float32) - col) * (cov * 0.55)[..., None]

    # feather strokes: soft dark lines running in from each notch, like the folded wing's
    strokes = Image.new('L', (W, H), 0)
    sd = ImageDraw.Draw(strokes)
    for i in range(1, len(tips) - 1):
        n = np.array(tips[i], float)
        inward = centre - n
        inward /= np.linalg.norm(inward)
        length = 26 if i < 5 else 18
        pts = [tuple(n + inward * t + np.array([inward[1], -inward[0]]) * 2.5 * math.sin(t / length * math.pi))
               for t in np.linspace(4, length, 8)]
        sd.line([((x - x0) * S, (y - y0) * S) for x, y in pts], fill=255, width=int(1.3 * S))
    strokes = np.asarray(strokes.filter(ImageFilter.GaussianBlur(0.8 * S)), np.float32) / 255.0
    strokes *= (1 - cov)
    col = col * (1 - 0.22 * strokes)[..., None]

    rgba = np.dstack([np.clip(col, 0, 255), mask * 255]).astype(np.uint8)
    img = Image.fromarray(rgba, 'RGBA').resize((int((x1 - x0) * scale), int((y1 - y0) * scale)),
                                                Image.LANCZOS)
    return np.asarray(img), (-x0, -y0)


# --------------------------------------------------------------------------- output

def save(name, rgba, placements, origin=None):
    """Crop to the layer, bleed colour into its transparent border, write PNG and placement."""
    a = rgba[..., 3]
    ys, xs = np.nonzero(a > 1)
    y0, y1 = max(ys.min() - 3, 0), min(ys.max() + 4, a.shape[0])
    x0, x1 = max(xs.min() - 3, 0), min(xs.max() + 4, a.shape[1])
    crop = rgba[y0:y1, x0:x1].astype(np.float32)
    col, al = crop[..., :3], crop[..., 3] / 255.0
    solid = al > 0.97
    col, _ = propagate(col, solid, ~solid, 12)
    out = np.dstack([np.clip(col, 0, 255), al * 255]).round().astype(np.uint8)
    Image.fromarray(out, 'RGBA').save(os.path.join(OUT, name + '.png'), optimize=True)
    ox, oy = origin or (0.0, 0.0)
    placements[name] = {'file': f'{name}.png', 'w': (x1 - x0) / K, 'h': (y1 - y0) / K,
                        'cx': (x0 + x1) / 2 / K - ox, 'cy': (y0 + y1) / 2 / K - oy,
                        'px': [int(x1 - x0), int(y1 - y0)]}


def rgba(col, a):
    return np.dstack([np.clip(col, 0, 255), np.clip(a, 0, 1) * 255]).astype(np.uint8)


def main(argv):
    os.makedirs(OUT, exist_ok=True)
    rgb = np.asarray(Image.open(SRC).convert('RGB'), np.float32)
    layers, _, _ = cut(rgb)
    placements = {}
    for name, (col, a) in layers.items():
        save(name, rgba(col, a), placements)
    col, a = mouth_interior(rgb.shape[:2])
    save('mouthInner', rgba(col, a), placements)
    wing, origin = paint_open_wing()
    save('wingOpen', wing.astype(np.float32), placements, origin=origin)
    far = wing.astype(np.float32).copy()
    far[..., :3] = far[..., :3] * 0.78 + np.array([10, 10, 22]) * 0.22   # in shadow, cooler
    save('wingFar', far, placements, origin=origin)
    with open(os.path.join(OUT, 'layers.json'), 'w') as f:
        json.dump({'texelsPerPx': K, 'layers': placements}, f, indent=1)
    total = sum(os.path.getsize(os.path.join(OUT, p['file'])) for p in placements.values())
    for n, p in placements.items():
        print(f"{n:11s} {p['px'][0]:4d}x{p['px'][1]:<4d} centre ({p['cx']:.1f}, {p['cy']:.1f})")
    print(f'{len(placements)} layers, {total // 1024} KB')
    if '--debug' in argv:
        d = argv[argv.index('--debug') + 1]
        os.makedirs(d, exist_ok=True)
        for name, (col, a) in layers.items():
            comp = col * a[..., None] + np.array([40, 90, 160]) * (1 - a[..., None])
            Image.fromarray(comp.clip(0, 255).astype(np.uint8)).save(os.path.join(d, f'{name}.png'))
        Image.fromarray(wing).save(os.path.join(d, 'wingOpen_rgba.png'))


if __name__ == '__main__':
    main(sys.argv[1:])
