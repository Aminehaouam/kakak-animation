"""Cut the parrot illustration into Rev2D layer textures.

Input:  source/parrot_x4.png  the illustration upscaled 4x (tools/upscale_esrgan.py)
Output: parrot/textures/<layer>.png  RGBA, 4 texture px per model px, cropped to the layer
        parrot/textures/layers.json  where every layer sits in model px

All landmark coordinates below are in SOURCE pixels of source/parrot.jpg (188 x 425, +y down);
the model is the same space shifted by (OX, OY) so the bird has room to move.

usage: python3 tools/make_layers.py [--debug out_dir]
"""
import json
import os
import sys

import numpy as np
from PIL import Image, ImageDraw

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, 'source', 'parrot_x4.png')
OUT = os.path.join(ROOT, 'parrot', 'textures')

K = 4                   # texture px per source px
OX, OY = 56, -36        # model px = source px + (OX, OY)
CANVAS = (300, 360)     # model canvas, px


# --------------------------------------------------------------------------- geometry

def catmull(pts, closed=True, n=10):
    """Smooth curve through pts (Catmull-Rom), as a dense point list."""
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
    a = np.radians(rot)
    t = np.linspace(0, 2 * np.pi, n, endpoint=False)
    x, y = rx * np.cos(t), ry * np.sin(t)
    return list(zip(cx + x * np.cos(a) - y * np.sin(a), cy + x * np.sin(a) + y * np.cos(a)))


def poly_mask(pts, shape, ss=4):
    """Antialiased coverage of a polygon given in source px, on the 4x texture grid."""
    h, w = shape
    img = Image.new('L', (w * ss, h * ss), 0)
    ImageDraw.Draw(img).polygon([(x * K * ss, y * K * ss) for x, y in pts], fill=255)
    return np.asarray(img.resize((w, h), Image.BOX), np.float32) / 255.0


# --------------------------------------------------------------------------- raster helpers

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
    """Give `todo` pixels the mean colour of known neighbours, ring by ring."""
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
    """Smooth fill of the `todo` pixels from the `known` colours around them.

    Multigrid: restrict known colours down a pyramid, fill the coarsest level by propagation,
    then on the way up start every todo pixel from the coarser solution and relax it with
    Jacobi (Laplace) steps. Pixels that are neither known nor todo take no part."""
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


# --------------------------------------------------------------------------- matte

def matte(rgb):
    """Alpha of the bird over the black background, and its un-premultiplied colour.

    The background is the near-black region connected to the border (plus the pocket between
    the legs); the pupil and the mouth are dark too but enclosed. Edge pixels are
    pixel = alpha * fg over black, with fg the colour of the nearest solid pixel."""
    h, w = rgb.shape[:2]
    dark = rgb.max(2) <= 8
    bg = flood(dark, [(0, 0), (w - 1, 0), (0, h - 1), (w - 1, h - 1), (98 * K, 340 * K)])
    band = dilate(bg, 5) & ~bg
    core = ~bg & ~band
    fg, _ = propagate(rgb, core, band, 10)
    proj = (rgb * fg).sum(2) / np.maximum((fg * fg).sum(2), 1e-3)
    alpha = np.where(core, 1.0, np.where(band, np.clip(proj, 0, 1), 0.0)).astype(np.float32)
    color = np.where(core[..., None], rgb, fg)
    return alpha, color, bg


# --------------------------------------------------------------------------- landmarks (source px)

# the line through the dark gape between the upper beak and the lower mandible (measured: it
# stays inside the dark crescent at every column), extended into the face and past the hook
GAPE = [(128, 140), (136.5, 145), (140, 148.5), (145, 153), (150, 156), (155, 158),
        (160, 159), (164, 162.5), (168, 166.3), (176, 169), (190, 171)]
UPPER_BEAK_ROI = [(130, 92), (150, 90), (174, 98), (188, 115), (192, 140), (191, 162)] + GAPE[::-1]
MANDIBLE_ROI = GAPE + [(186, 182), (160, 188), (140, 188), (127, 178), (127, 150)]
NOSTRIL = ellipse_pts(153.5, 110.4, 5.0, 3.2)
# chin feathers behind the mandible and the gape. The throat line on the right runs from the front
# of the neck to just under the lower edge of the CLOSED mandible (rotated -15 deg about the
# hinge), so a closing beak uncovers feathers, not a notch; right of it the base is transparent
CHIN = [(127, 140), (136, 143.5), (140, 146), (145, 149.3), (150, 151), (155, 151.5),
        (158.7, 152.4), (162.8, 160.4), (167, 168.4), (161, 171.5), (156, 175.5), (151, 181),
        (148, 190), (128, 190)]  # 1.5 px inside the open side of the gape (160,152)-(168,168)

PUPIL = ellipse_pts(115.3, 137.0, 12.5, 17.0, rot=-9)

# around the wing; below it hugs the wing's lower edge where the leg starts (x >= 76), so the
# dark outline of the leg and the shadow in the neck notch stay out
WING_ROI = [(80, 207), (100, 203), (122, 209), (131, 232), (131, 252), (125, 272), (114, 290),
            (104, 294), (98, 298.5), (92, 303.5), (88, 306.5), (84, 309.5), (80, 312),
            (76, 314), (72, 318), (60, 328), (40, 336), (20, 330), (14, 312), (24, 282),
            (48, 236), (70, 214)]
# the body's back where the folded wing hides it (the wing hangs past it over the tail). Its rump
# reaches down to 1.5 px inside the wing's lower edge (measured per column), so a raised wing
# shows the rump with the tail coming out from under it; right of x = 76 the wing lies on the leg
BODY_BACK = (catmull([(84, 205), (77, 214), (69, 227), (61, 242), (55, 258), (51, 275), (50, 290),
                      (51, 302), (55, 311)], closed=False, n=8)
             + [(60, 316), (64, 314.8), (68, 312.8), (72, 311.6), (76, 310.5), (79, 316),
                (90, 322), (112, 315), (132, 290), (142, 255), (136, 215), (110, 203)])

# the neck line: the head layer (a copy of the base above it) draws over the wing, so a lowered
# head covers the top of the wing instead of slipping under it; the rig's head weight is 1 above
# this line too
NECK = [(0, 197), (60, 197), (80, 199), (100, 197), (120, 195), (140, 189), (160, 186), (300, 186)]

TAIL_ROI = [(0, 296), (96, 296), (96, 380), (0, 380)]
# the tail's root, hidden under the wing tip, the rump and the left leg
TAIL_ROOT = catmull([(34, 321), (40, 313), (48, 307), (58, 305), (72, 304), (82, 305),
                     (87, 312), (87, 328), (84, 342), (79, 348), (74, 336), (66, 328),
                     (50, 328), (38, 326)], closed=True, n=8)  # x <= 87: stays behind the leg


def cut_layers(rgb, debug=None):
    alpha, color, _ = matte(rgb)
    shape = alpha.shape
    L = lum(color)
    red = redness(color)
    layers = {}

    # ---- upper beak and mandible: beak grey between the light face and the dark gape
    beak_grey = 1 - smoothstep(100, 135, L)
    not_gape = smoothstep(32, 52, L)
    nostril = poly_mask(NOSTRIL, shape)
    upper = alpha * poly_mask(UPPER_BEAK_ROI, shape) * beak_grey * np.maximum(not_gape, nostril)
    mand_roi = poly_mask(MANDIBLE_ROI, shape)
    mandible = alpha * mand_roi * beak_grey * not_gape
    layers['upperBeak'] = (color, upper)
    layers['mandible'] = (color, mandible)

    # ---- pupil: dark ink un-mixed against the white eye ring (the highlight stays a hole)
    pupil_roi = poly_mask(PUPIL, shape)
    ring_white, ink = 254.0, 22.0
    pa = np.clip((ring_white - L) / (ring_white - ink), 0, 1) * pupil_roi
    unmixed = (color - (1 - pa[..., None]) * ring_white) / np.maximum(pa, 1e-3)[..., None]
    pupil_col = np.where((pa > 0.3)[..., None], np.clip(unmixed, 0, 255),
                         np.array([24, 24, 30], np.float32))
    layers['pupil'] = (pupil_col, pa)

    # ---- wing: the darker grey over the body, not the red tail
    wing_m = (poly_mask(WING_ROI, shape) * (1 - smoothstep(118, 138, L))
              * (1 - smoothstep(0.10, 0.25, red)))
    layers['wing'] = (color, alpha * wing_m)

    # ---- tail: red feathers plus their root under the wing and the leg
    tail_m = poly_mask(TAIL_ROI, shape) * smoothstep(0.12, 0.30, red)
    tail_vis = alpha * tail_m

    # ---- base: everything else, with what the moving layers hide filled in. The cut-outs use the
    # colour memberships (not times alpha), so the soft silhouette of a moving layer leaves no
    # faint outline behind in the base
    base_col = color.copy()
    # only clearly red pixels leave the base: the dark outline of the leg against the tail stays
    # solid with the leg instead of turning into a faint seam when the tail swings
    base_a = alpha * (1 - smoothstep(0.6, 0.95, tail_m))
    # the dark line between the red feathers and the left leg is the leg's edge: it stays in the
    # base, and the tail is painted plain red under it
    leg = (alpha > 0.5) & (red < 0.1) & (L > 120) & (poly_mask(TAIL_ROOT, shape) > 0)
    leg_line = dilate(leg, 6) & (tail_m > 0) & (L < 84)
    base_a = np.where(leg_line, alpha, base_a)
    # body behind the wing. The repainted area reaches 3 texels past the wing, so its antialiased
    # edge is replaced too and no dark outline stays on the body when the wing lifts
    back = poly_mask(BODY_BACK, shape)
    w_area = dilate(wing_m > 0.02, 3)
    body_known = (base_a > 0.98) & ~w_area & (L > 135) & (red < 0.1)
    body_fill = fill(color, body_known, w_area & (back > 0))
    base_col = np.where((w_area & (back > 0))[..., None], body_fill, base_col)
    base_a = base_a * (1 - wing_m * (1 - back))
    # chin feathers behind the mandible and the gape (same 3 texel margin)
    chin = poly_mask(CHIN, shape)
    mouth_stuff = mand_roi * (1 - smoothstep(100, 135, L))
    m_area = dilate(mouth_stuff > 0.02, 3) & (chin > 0)
    chin_known = (alpha > 0.98) & (L > 135) & ~dilate(mouth_stuff > 0.02, 3)
    chin_known &= poly_mask([(118, 140), (150, 140), (150, 196), (118, 196)], shape) > 0
    chin_fill = fill(color, chin_known, m_area)
    base_col = np.where(m_area[..., None], chin_fill, base_col)
    base_a = base_a * (1 - mouth_stuff * (1 - chin))
    # eye ring behind the pupil
    ring_known = (L > 236) & (pupil_roi < 0.02) & dilate(pupil_roi > 0, 24)
    ring_fill = fill(color, ring_known, pupil_roi > 0)
    base_col = base_col + (ring_fill - base_col) * pupil_roi[..., None]
    layers['base'] = (base_col, base_a)

    # head: the base above the neck line, only where the base is solid (soft silhouette edges
    # stay in the base alone, so nothing is drawn twice at rest)
    ys, xs = np.mgrid[0:shape[0], 0:shape[1]]
    nx, ny = zip(*NECK)
    above = np.interp((xs + 0.5) / K, nx, ny) - (ys + 0.5) / K
    head_a = smoothstep(-1.0, 2.0, above) * smoothstep(0.98, 1.0, base_a)
    layers['head'] = (base_col, head_a)

    # tail root: only under solid pixels of the picture (the wing, the leg), so it never shows
    # at rest, also not through their soft edges against the tail
    root = poly_mask(TAIL_ROOT, shape) * smoothstep(0.9, 1.0, alpha)
    tail_a = np.maximum(tail_vis, root)
    # painted from saturated red away from the wing (not the edge pixels that mix in the wing's
    # grey or the shadow it casts), so an uncovered root looks like more feather
    tail_known = ((tail_vis > 0.9) & (alpha > 0.95) & (red > 0.42) & ~dilate(wing_m > 0.02, 6)
                  & ~leg_line)
    tail_col = fill(color, tail_known, (root > 0) & ((tail_vis < 0.9) | leg_line))
    tail_col = np.where(((tail_vis >= 0.9) & ~leg_line)[..., None], color, tail_col)
    layers['tail'] = (tail_col, tail_a)

    if debug:
        os.makedirs(debug, exist_ok=True)
        tint = {'upperBeak': (255, 200, 0), 'mandible': (0, 220, 255), 'pupil': (255, 0, 255),
                'wing': (60, 255, 60), 'tail': (255, 120, 0)}
        over = color * alpha[..., None] * 0.55
        for name, rgbv in tint.items():
            a = layers[name][1][..., None]
            over = over * (1 - 0.6 * a) + np.array(rgbv, np.float32) * 0.6 * a
        Image.fromarray(over.clip(0, 255).astype(np.uint8)).save(os.path.join(debug, 'cuts.png'))
        for name, (c, a) in layers.items():
            bgc = np.array([40, 90, 160], np.float32)
            comp = c * a[..., None] + bgc * (1 - a[..., None])
            Image.fromarray(comp.clip(0, 255).astype(np.uint8)).save(
                os.path.join(debug, f'layer_{name}.png'))
    return layers


# --------------------------------------------------------------------------- output

def save_layer(name, color, alpha, placements, pad=3, bleed=4):
    """Crop to the layer, bleed colours into the transparent border, write RGBA PNG."""
    on = alpha > 1.5 / 255
    ys, xs = np.nonzero(on)
    y0, y1 = max(ys.min() - pad, 0), min(ys.max() + 1 + pad, alpha.shape[0])
    x0, x1 = max(xs.min() - pad, 0), min(xs.max() + 1 + pad, alpha.shape[1])
    # keep crops on whole source px so texture px map exactly onto model px
    y0, x0 = y0 - y0 % K, x0 - x0 % K
    y1, x1 = y1 + (-y1) % K, x1 + (-x1) % K
    col = color[y0:y1, x0:x1].copy()
    a = alpha[y0:y1, x0:x1]
    # decontaminate soft edges: they take the colour of the solid pixels next to them, so an
    # edge that moves away from its neighbour does not carry the neighbour's colour along
    solid = a > 0.97
    col, _ = propagate(col, solid, ~solid, bleed + 8)
    rgba = np.dstack([np.clip(col, 0, 255), np.clip(a * 255, 0, 255)]).round().astype(np.uint8)
    Image.fromarray(rgba, 'RGBA').save(os.path.join(OUT, name + '.png'), optimize=True)
    placements[name] = {
        'file': f'textures/{name}.png',
        'x': x0 / K + OX, 'y': y0 / K + OY, 'w': (x1 - x0) / K, 'h': (y1 - y0) / K,
        'px': [int(x1 - x0), int(y1 - y0)],
    }


def main(argv):
    debug = argv[argv.index('--debug') + 1] if '--debug' in argv else None
    rgb = np.asarray(Image.open(SRC).convert('RGB'), np.float32)
    layers = cut_layers(rgb, debug)
    os.makedirs(OUT, exist_ok=True)
    placements = {}
    for name, (col, a) in layers.items():
        save_layer(name, col, a, placements)
    meta = {'canvas': CANVAS, 'offset': [OX, OY], 'texelsPerPx': K, 'layers': placements}
    with open(os.path.join(OUT, 'layers.json'), 'w') as f:
        json.dump(meta, f, indent=2)
    for name, p in placements.items():
        print(f"{name:10s} {p['px'][0]:4d}x{p['px'][1]:<4d} at model ({p['x']:.2f}, {p['y']:.2f})")


if __name__ == '__main__':
    main(sys.argv[1:])
