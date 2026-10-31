"""Coco, taken from the original character image (source/parrot.jpg in the repository, the only
existing artwork this experiment uses): matted off its black background and cut into a body, a
near wing and a far wing, so PixiJS can flap the wings and land him."""
import json
import os

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage

import paint

SRC = os.path.join(os.path.dirname(__file__), '..', '..', 'source', 'parrot.jpg')
UP = 2  # work at twice the source size for clean edges

# the folded near wing, in source pixels
WING = [(100, 207), (112, 210), (122, 218), (124, 234), (121, 254), (111, 277), (97, 297), (78, 313), (55, 321), (34, 321),
        (27, 311), (35, 289), (50, 265), (66, 243), (79, 225), (90, 212)]
# the body's own outline where the wing hides it (its back edge down to the tail)
BODY_UNDER = [(96, 200), (126, 212), (126, 300), (100, 322), (74, 326), (58, 318), (57, 296), (61, 268), (68, 244), (78, 222), (88, 207)]
SHOULDER = (104, 214)
EYE = (115.5, 134.5)


def matte(rgb):
    """Alpha from a black background: flood the background in from the border, then take a soft
    edge from brightness, and un-mix the black from the edge colours."""
    lum = rgb.max(axis=2)
    dark = lum < 16 / 255
    lab, _ = ndimage.label(dark)
    border = set(np.unique(np.concatenate([lab[0], lab[-1], lab[:, 0], lab[:, -1]]))) - {0}
    bg = np.isin(lab, list(border))
    fg = ~bg
    near_bg = ndimage.binary_dilation(bg, iterations=2) & fg
    ref = ndimage.maximum_filter(np.where(fg & ~near_bg, lum, 0), size=7)
    ref = np.where(ref > 0.05, ref, ndimage.maximum_filter(lum, size=9))
    edge_a = np.clip(lum / np.maximum(ref, 1e-3), 0, 1)
    edge_a = np.clip((edge_a - 0.22) / 0.7, 0, 1)  # trim the dark JPEG halo at the outline
    alpha = np.where(near_bg, edge_a, fg.astype(np.float32))
    alpha = np.where(bg, np.clip((lum - 4 / 255) / 0.12, 0, 1) * ndimage.binary_dilation(fg, iterations=1), alpha)
    colour = np.clip(rgb / np.maximum(alpha[..., None], 1e-3), 0, 1)
    colour = np.where(alpha[..., None] > 0.02, colour, 0)
    return colour, alpha.astype(np.float32)


def poly_mask(pts, shape, feather=1.0):
    img = Image.new('L', (shape[1] * 4, shape[0] * 4), 0)
    ImageDraw.Draw(img).polygon([(x * UP * 4, y * UP * 4) for x, y in pts], fill=255)
    m = np.asarray(img.reduce(4), np.float32) / 255
    return ndimage.gaussian_filter(m, feather) if feather else m


def inpaint(colour, hole, keep, iters=220):
    """Fill `hole` by diffusing the colours around it (only from pixels in `keep`)."""
    c = colour.copy()
    known = keep & ~hole
    w = known.astype(np.float32)
    acc = c * w[..., None]
    for _ in range(iters):
        acc_b = np.stack([ndimage.uniform_filter(acc[..., i], 5) for i in range(3)], -1)
        w_b = ndimage.uniform_filter(w, 5)
        fill = acc_b / np.maximum(w_b[..., None], 1e-4)
        newly = (w_b > 0.02) & ~known
        c = np.where(newly[..., None], fill, c)
        known = known | newly
        w = known.astype(np.float32)
        acc = c * w[..., None]
    return c


def save(name, colour, alpha, anchor, meta=None):
    L = paint.Layer(colour.shape[1], colour.shape[0])
    L.px[..., :3] = colour * alpha[..., None]
    L.px[..., 3] = alpha
    return L.save(name, anchor=anchor, quality=95, meta=meta)


def build():
    src = Image.open(SRC).convert('RGB')
    big = src.resize((src.width * UP, src.height * UP), Image.LANCZOS)
    rgb = np.asarray(big, np.float32) / 255
    rgb = np.clip(rgb, 0, 1)
    colour, alpha = matte(rgb)
    H, W = alpha.shape
    wing = poly_mask(WING, (H, W), feather=0.8)
    under = poly_mask(BODY_UNDER, (H, W), feather=0.8)
    # the near wing on its own
    wing_a = alpha * wing
    # the body without it: the hidden flank is filled from the plumage around it, and wing
    # parts that stick out past the body become transparent
    hole = ndimage.binary_dilation(wing > 0.35, iterations=2)
    # the hidden flank: the body's own grey, rounded (lighter toward the breast, darker toward
    # the back), filled where the wing covered it
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    breast = (alpha > 0.95) & ~ndimage.binary_dilation(hole, iterations=6) & (yy > 200 * UP) & (yy < 300 * UP) & (xx > 110 * UP)
    base = np.median(colour[breast], axis=0) if breast.any() else np.array([0.66, 0.66, 0.7], np.float32)
    xs_h = xx[hole]
    x_l, x_r = (xs_h.min(), xs_h.max()) if xs_h.size else (0, 1)
    u = np.clip((xx - x_l) / max(x_r - x_l, 1), 0, 1)
    shade = 0.74 + 0.2 * u ** 0.8
    flank_c = np.clip(base[None, None, :] * shade[..., None], 0, 1)
    soft_hole = ndimage.gaussian_filter(hole.astype(np.float32), 1.5)
    body_c = colour * (1 - soft_hole[..., None]) + flank_c * soft_hole[..., None]
    # outside the body's own outline, the wing area becomes transparent
    body_a = alpha * (1 - soft_hole) + np.minimum(under, 1) * soft_hole * (alpha > 0.01)
    ys, xs = np.nonzero(alpha > 0.5)
    feet_y = ys.max() / UP
    feet_x = float(np.median(xs[ys > ys.max() - 6])) / UP
    anchor = (feet_x * UP, feet_y * UP)
    rel = lambda p: [round((p[0] - feet_x) * UP, 1), round((p[1] - feet_y) * UP, 1)]
    meta = {'scale': UP, 'shoulder': rel(SHOULDER), 'eye': rel(EYE), 'eyeR': 21 * UP, 'pupilR': 10 * UP, 'height': round(feet_y - ys.min() / UP, 1) * UP}
    save('coco_body', body_c, body_a, anchor, meta)
    save('coco_wing', colour, wing_a, (SHOULDER[0] * UP, SHOULDER[1] * UP))
    far = np.clip(colour * np.array([0.74, 0.74, 0.8], np.float32), 0, 1)
    save('coco_wing_far', far, wing_a, (SHOULDER[0] * UP, SHOULDER[1] * UP))
    # a quick check sheet: the cut, and a raised wing
    sheet = Image.new('RGBA', (W * 3 + 40, H), '#7fb8e6')
    for k, (c_, a_) in enumerate(((body_c, body_a), (colour, wing_a))):
        sheet.alpha_composite(Image.fromarray((np.dstack([c_, a_]) * 255).astype(np.uint8), 'RGBA'), (k * (W + 20), 0))
    body_img = Image.fromarray((np.dstack([body_c, body_a]) * 255).astype(np.uint8), 'RGBA')
    wing_img = Image.fromarray((np.dstack([colour, wing_a]) * 255).astype(np.uint8), 'RGBA')
    comp = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    comp.alpha_composite(body_img)
    raised = wing_img.rotate(70, center=(SHOULDER[0] * UP, SHOULDER[1] * UP), resample=Image.BICUBIC)
    comp.alpha_composite(raised)
    sheet.alpha_composite(comp, (2 * (W + 20), 0))
    sheet.convert('RGB').save(os.path.join(os.path.dirname(__file__), '.cache', 'coco_cut.jpg'), quality=92)
