"""London's landmarks, each in its own layer: the London Eye (frame, wheel, capsule), Westminster,
St Paul's, the Gherkin, the Shard, the City towers and Tower Bridge."""
import numpy as np

from buildings import face, soft_shadow, window_row
from paint import Layer, Shape, blur, hexc, lambert, lerp, noise, ramp, smoothstep

STONE = '#eedfbd'      # Portland stone / Anston limestone
STONE_WARM = '#e8cf9c'
SLATE = '#3f5878'
GOLD = '#e2ae45'
GOLD_HI = '#ffe08e'
IRON_BLUE = '#4a80bd'
GLASS = '#5d9fd3'


def _bb(pts):
    xs, ys = [p[0] for p in pts], [p[1] for p in pts]
    return min(xs), min(ys), max(xs), max(ys)


def P(pts):
    return Shape(*_bb(pts)).poly(pts)


def R(x0, y0, x1, y1):
    return Shape(x0, y0, x1, y1).rect(x0, y0, x1, y1)


def vgrad(c0, c1, y0, y1):
    a, b = (hexc(c) if isinstance(c, str) else c for c in (c0, c1))

    def f(X, Y):
        t = np.clip((Y - y0) / max(y1 - y0, 1), 0, 1)[..., None]
        return lerp(a, b, t)
    return f


def hgrad(c0, c1, x0, x1):
    a, b = (hexc(c) if isinstance(c, str) else c for c in (c0, c1))

    def f(X, Y):
        t = np.clip((X - x0) / max(x1 - x0, 1), 0, 1)[..., None]
        return lerp(a, b, t)
    return f


def cylinder(c_lit, c_shade, x0, x1, power=1.0):
    """Colour across a vertical cylinder lit from the left."""
    a, b = hexc(c_lit), hexc(c_shade)

    def f(X, Y):
        u = np.clip((X - x0) / max(x1 - x0, 1), 0, 1)
        # Lambert across a cylinder with the sun from the left, softened
        n = np.cos((u - 0.5) * np.pi)
        sx = -np.sin((u - 0.5) * np.pi)
        lit = np.clip(0.55 * n + 0.6 * sx * 0.9 + 0.25, 0, 1) ** power
        return lerp(b, a, lit[..., None])
    return f


# ======================================================================== the London Eye

EYE_R = 350          # rim radius
EYE_CAPSULES = 32


def eye_wheel():
    """The wheel: twin rims tied by a truss, cables to the hub. It rotates, so it is lit evenly."""
    m = 40
    S = 2 * (EYE_R + m)
    L = Layer(S, S)
    c = S / 2
    rim_c = hexc('#f4f6f8')
    # spokes: fine cables from the hub to the inner rim
    sp = Shape(0, 0, S, S)
    n_sp = 64
    for i in range(n_sp):
        a = 2 * np.pi * i / n_sp
        x1, y1 = c + np.cos(a) * (EYE_R - 26), c + np.sin(a) * (EYE_R - 26)
        x0, y0 = c + np.cos(a + 0.05) * 20, c + np.sin(a + 0.05) * 20
        sp.stroke([(x0, y0), (x1, y1)], 1.1, cap='flat')
    L.paint(sp, hexc('#dfe6ee'), alpha=0.85)
    # the twin rims
    for r, wdt in ((EYE_R, 6.0), (EYE_R - 26, 4.2)):
        ring = Shape(0, 0, S, S).ellipse(c, c, r + wdt / 2, r + wdt / 2).ellipse(c, c, r - wdt / 2, r - wdt / 2, v=0)
        L.paint(ring, rim_c)
    # the truss between them
    tr = Shape(0, 0, S, S)
    n_tr = 96
    for i in range(n_tr):
        a0 = 2 * np.pi * i / n_tr
        a1 = 2 * np.pi * (i + 1) / n_tr
        p_out = (c + np.cos(a0) * EYE_R, c + np.sin(a0) * EYE_R)
        p_in = (c + np.cos(a1) * (EYE_R - 26), c + np.sin(a1) * (EYE_R - 26))
        p_out2 = (c + np.cos(a1) * EYE_R, c + np.sin(a1) * EYE_R)
        tr.stroke([p_out, p_in, p_out2] if i % 2 == 0 else [p_in, p_out2], 1.7, cap='flat')
    L.paint(tr, hexc('#e8edf2'))
    # a soft grey line inside each rim gives them roundness
    for r in (EYE_R - 1.8, EYE_R - 26 - 1.2):
        ring = Shape(0, 0, S, S).ellipse(c, c, r + 0.8, r + 0.8).ellipse(c, c, r - 0.8, r - 0.8, v=0)
        L.paint(ring, hexc('#a9b7c7'), alpha=0.55)
    # the hub
    L.paint(Shape(c - 30, c - 30, c + 30, c + 30).ellipse(c, c, 24, 24), hexc('#cfd8e2'))
    L.paint(Shape(c - 30, c - 30, c + 30, c + 30).ellipse(c, c, 17, 17), hexc('#8d9cae'))
    L.paint(Shape(c - 30, c - 30, c + 30, c + 30).ellipse(c, c, 9, 9), hexc('#eef2f6'))
    L.save('eye_wheel', anchor=(c, c), crop=False)
    return L


def eye_capsule():
    """One glass capsule, hung level from its bracket (the anchor is the bracket on the rim)."""
    w, h = 64, 46
    L = Layer(w, h + 16)
    cx, cy = w / 2, 10 + h / 2
    # the egg-shaped pod
    body = Shape(0, 0, w, h + 16).ellipse(cx, cy, w * 0.46, h * 0.42)
    L.paint(body, hexc('#f1f4f7'))
    glass = Shape(0, 0, w, h + 16).ellipse(cx, cy, w * 0.42, h * 0.35)

    def g(X, Y):
        t = np.clip((Y - (cy - h * 0.35)) / (h * 0.7), 0, 1)[..., None]
        u = np.clip((X - (cx - w * 0.42)) / (w * 0.84), 0, 1)[..., None]
        base = lerp(hexc('#bfe0f4'), hexc('#3e78ad'), t * 0.8 + u * 0.25)
        return base
    L.paint(glass, g)
    # glazing bars and the lower deck band
    bars = Shape(0, 0, w, h + 16)
    for k in range(-2, 3):
        x = cx + k * w * 0.15
        bars.rect(x - 0.7, cy - h * 0.34, x + 0.7, cy + h * 0.34)
    L.paint(bars, hexc('#f4f7fa'), alpha=0.8, clip=True)
    L.paint(Shape(0, 0, w, h + 16).ellipse(cx, cy + h * 0.24, w * 0.44, h * 0.12), hexc('#dce3ea'), clip=True)
    # a soft sheen upper left
    sheen = Shape(0, 0, w, h + 16).ellipse(cx - w * 0.16, cy - h * 0.14, w * 0.14, h * 0.08)
    L.paint((blur(sheen.a, 1.2), sheen.x0, sheen.y0), hexc('#ffffff'), alpha=0.7, clip=True)
    L.save('eye_capsule', anchor=(cx, cy), crop=False)
    return L


def eye_frame():
    """The A-frame that holds the wheel from the bank, its back-stay cables and the boarding pier.
    The anchor is the hub."""
    R_ = EYE_R
    w, h = int(R_ * 2.0), int(R_ * 1.36)
    hub = (w * 0.68, 40)
    base_y = hub[1] + R_ + 34
    L = Layer(w, h)
    # back-stay cables to the ground
    cables = Shape(0, 0, w, h)
    for k, fx in enumerate((0.05, 0.12)):
        cables.stroke([(hub[0] - 6, hub[1] + 4), (w * fx, base_y)], 2.2)
    L.paint(cables, hexc('#d8dfe7'))
    # the two legs of the A-frame, seen from the side, lit from the left
    legs = [((w * 0.28, base_y), 17), ((w * 0.4, base_y), 15)]
    for (bx, by), lw in legs:
        pts = _tapered_line((bx, by), (hub[0] - 4, hub[1] + 6), lw, lw * 0.7)
        L.paint(P(pts), cylinder('#ffffff', '#aebccc', min(p[0] for p in pts), max(p[0] for p in pts)))
    # cross ties between the legs
    ties = Shape(0, 0, w, h)
    for t in (0.35, 0.62):
        a = (lerp(w * 0.28, hub[0], t), lerp(base_y, hub[1], t))
        b = (lerp(w * 0.4, hub[0], t), lerp(base_y, hub[1], t))
        ties.stroke([a, b], 4)
    L.paint(ties, hexc('#e9eef3'))
    # the boarding pier at the foot of the wheel
    px0, px1 = hub[0] - R_ * 0.55, hub[0] + R_ * 0.55
    L.paint(R(px0, base_y - 16, px1, base_y + 2), vgrad('#f2f4f6', '#b9c4cf', base_y - 16, base_y + 2))
    L.paint(R(px0, base_y - 18, px1, base_y - 14), hexc('#ffffff'))
    soft_shadow(L, px0, base_y - 14, px1, base_y - 8, 0.25)
    L.save('eye_frame', anchor=hub, crop=False)
    return L


def _tapered_line(p0, p1, w0, w1):
    p0, p1 = np.array(p0, np.float32), np.array(p1, np.float32)
    d = p1 - p0
    d /= np.linalg.norm(d)
    n = np.array([-d[1], d[0]])
    return [tuple(p0 + n * w0 / 2), tuple(p1 + n * w1 / 2), tuple(p1 - n * w1 / 2), tuple(p0 - n * w0 / 2)]


# ======================================================================== Westminster

def gothic_window(sh, x, y, w, h):
    """A tall lancet: straight sides, pointed head."""
    r = w * 0.62
    pts = [(x, y + h), (x, y + w * 0.55)]
    for a in np.linspace(0, 1, 8):
        pts.append((x + w / 2 * a, y + w * 0.55 - (w * 0.55) * np.sin(a * np.pi / 2)))
    for a in np.linspace(1, 0, 8):
        pts.append((x + w - w / 2 * a, y + w * 0.55 - (w * 0.55) * np.sin(a * np.pi / 2)))
    pts += [(x + w, y + w * 0.55), (x + w, y + h)]
    sh.poly(pts)


def pinnacle(L, x, y_base, w, h, stone=STONE, gold=False):
    """A slim Gothic pinnacle: a little shaft with a pointed cap."""
    L.paint(R(x - w / 2, y_base - h * 0.55, x + w / 2, y_base), cylinder('#fbf0d4', '#b79e70', x - w / 2, x + w / 2))
    cap = [(x - w * 0.62, y_base - h * 0.55), (x, y_base - h), (x + w * 0.62, y_base - h * 0.55)]
    L.paint(P(cap), hexc(GOLD) if gold else hgrad('#f6e7c4', '#a98f63', x - w * 0.62, x + w * 0.62))


def big_ben(L, cx, base_y, scale=1.0):
    """The Elizabeth Tower: panelled shaft, the clock stage, belfry and gilded spire.
    It stands left of the centre, so its right (shaded) side face shows."""
    s = scale
    fw, sw = 66 * s, 26 * s           # front face and side face widths
    x0, x1 = cx - fw / 2, cx + fw / 2
    shaft_top = base_y - 372 * s
    stone_f, stone_s = face(STONE_WARM, 'front'), face(STONE_WARM, 'right')
    drop = 0.06
    # shaft: front and side
    L.paint(R(x0, shaft_top, x1, base_y), vgrad(np.clip(stone_f * 1.06, 0, 1), stone_f * 0.92, shaft_top, base_y))
    L.paint(P([(x1, shaft_top), (x1 + sw, shaft_top + sw * drop), (x1 + sw, base_y), (x1, base_y)]), stone_s)
    # panelling: recessed vertical panels with fine mullions, banded every storey
    pan = Shape(x0, shaft_top, x1 + sw, base_y)
    mul = Shape(x0, shaft_top, x1 + sw, base_y)
    storeys = 9
    sh_ = (base_y - shaft_top) / storeys
    for k in range(storeys):
        y0 = shaft_top + k * sh_ + 4 * s
        y1 = y0 + sh_ - 9 * s
        for j in range(4):
            px = x0 + 5 * s + j * (fw - 10 * s) / 4
            pw = (fw - 10 * s) / 4 - 3 * s
            gothic_window(pan, px, y0, pw, y1 - y0)
            mul.rect(px + pw / 2 - 0.5 * s, y0 + pw * 0.4, px + pw / 2 + 0.5 * s, y1)
        for j in range(2):
            px = x1 + 3 * s + j * (sw - 5 * s) / 2
            gothic_window(pan, px, y0 + 1.5, (sw - 5 * s) / 2 - 2 * s, y1 - y0)
    L.paint(pan, hexc('#7d6b4e'), alpha=0.42, mode='multiply', clip=True)
    L.paint(mul, np.clip(stone_f * 1.08, 0, 1), alpha=0.75)
    bands = Shape(x0, shaft_top, x1 + sw, base_y)
    for k in range(storeys + 1):
        y = shaft_top + k * sh_
        bands.rect(x0 - 1, y - 1.4 * s, x1 + sw, y + 1.4 * s)
    L.paint(bands, np.clip(stone_f * 1.12, 0, 1))
    # the clock stage: wider, with a gilded frame and a white dial
    cs_top = shaft_top - 96 * s
    cw = 10 * s
    L.paint(R(x0 - cw, cs_top, x1 + cw, shaft_top), stone_f)
    L.paint(P([(x1 + cw, cs_top), (x1 + cw + sw, cs_top + sw * drop), (x1 + cw + sw, shaft_top), (x1 + cw, shaft_top)]), stone_s)
    L.paint(R(x0 - cw, cs_top + 8 * s, x1 + cw, cs_top + 88 * s), hexc(GOLD), alpha=0.22, clip=True)
    ccx, ccy, cr = cx, cs_top + 50 * s, 30 * s
    L.paint(Shape(ccx - cr - 6, ccy - cr - 6, ccx + cr + 6, ccy + cr + 6).ellipse(ccx, ccy, cr + 5 * s, cr + 5 * s), hexc(GOLD))
    L.paint(Shape(ccx - cr - 6, ccy - cr - 6, ccx + cr + 6, ccy + cr + 6).ellipse(ccx, ccy, cr, cr), vgrad('#fffaf0', '#efe6d3', ccy - cr, ccy + cr))
    ticks = Shape(ccx - cr, ccy - cr, ccx + cr, ccy + cr)
    for k in range(12):
        a = 2 * np.pi * k / 12
        p0 = (ccx + np.cos(a) * cr * 0.72, ccy + np.sin(a) * cr * 0.72)
        p1 = (ccx + np.cos(a) * cr * 0.9, ccy + np.sin(a) * cr * 0.9)
        ticks.stroke([p0, p1], 2.0 * s, cap='flat')
    L.paint(ticks, hexc('#2a2a32'))
    hands = Shape(ccx - cr, ccy - cr, ccx + cr, ccy + cr)
    hands.stroke([(ccx, ccy), (ccx + np.cos(-1.05) * cr * 0.5, ccy + np.sin(-1.05) * cr * 0.5)], 2.6 * s)  # hour hand
    hands.stroke([(ccx, ccy), (ccx + np.cos(-1.57) * cr * 0.78, ccy + np.sin(-1.57) * cr * 0.78)], 1.8 * s)  # minute hand
    L.paint(hands, hexc('#1f2026'))
    L.paint(Shape(ccx - 4, ccy - 4, ccx + 4, ccy + 4).ellipse(ccx, ccy, 2.6 * s, 2.6 * s), hexc(GOLD))
    # the side dial, foreshortened
    sx = x1 + cw + sw * 0.5
    L.paint(Shape(sx - 14, ccy - cr - 6, sx + 14, ccy + cr + 6).ellipse(sx, ccy + sw * drop * 0.5, sw * 0.44, cr + 4 * s), face(GOLD, 'right'))
    L.paint(Shape(sx - 14, ccy - cr - 4, sx + 14, ccy + cr + 4).ellipse(sx, ccy + sw * drop * 0.5, sw * 0.34, cr * 0.9), face('#f6eedc', 'right'))
    for xx in (x0 - cw, x1 + cw):
        pinnacle(L, xx, cs_top + 2, 9 * s, 46 * s, gold=True)
    soft_shadow(L, x0 - cw, shaft_top, x1 + cw + sw, shaft_top + 10 * s, 0.4)
    # belfry with pointed openings
    bt = cs_top - 62 * s
    L.paint(R(x0 - 2 * s, bt, x1 + 2 * s, cs_top), stone_f)
    L.paint(P([(x1 + 2 * s, bt), (x1 + 2 * s + sw * 0.9, bt + sw * drop), (x1 + 2 * s + sw * 0.9, cs_top), (x1 + 2 * s, cs_top)]), stone_s)
    op = Shape(x0, bt, x1 + sw, cs_top)
    for j in range(3):
        gothic_window(op, x0 + 6 * s + j * 19 * s, bt + 12 * s, 14 * s, 42 * s)
    L.paint(op, hexc('#3b3a44'))
    L.paint(R(x0 - 3 * s, bt - 3 * s, x1 + 3 * s + sw, bt + 3 * s), hexc(GOLD))
    # the spire: dark slate with gilded ribs and lucarnes
    sp_top = bt - 168 * s
    spire_l = [(x0 - 2 * s, bt), (cx, sp_top), (cx, bt)]
    spire_r = [(cx, bt), (cx, sp_top), (x1 + sw * 0.8, bt + sw * drop)]
    L.paint(P(spire_l), vgrad('#5d7290', '#3c4f6c', sp_top, bt))
    L.paint(P(spire_r), vgrad('#3e5170', '#26344a', sp_top, bt))
    ribs = Shape(x0, sp_top, x1 + sw, bt)
    for f in (0.0, 0.5, 1.0):
        ribs.stroke([(lerp(x0 - 2 * s, x1 + sw * 0.8, f), bt), (cx, sp_top)], 2.2 * s)
    for k in range(1, 5):
        yy = lerp(bt, sp_top, k / 6)
        half = lerp(fw / 2 + sw * 0.4, 0, k / 6)
        ribs.rect(cx - half, yy - 1.2 * s, cx + half, yy + 1.2 * s)
    L.paint(ribs, hexc(GOLD), alpha=0.9)
    for k, yy in enumerate((bt - 40 * s, bt - 86 * s)):
        lw = 12 * s * (1 - k * 0.3)
        L.paint(P([(cx - lw, yy + lw * 1.4), (cx - lw, yy + lw * 0.5), (cx, yy - lw * 0.2), (cx + lw, yy + lw * 0.5), (cx + lw, yy + lw * 1.4)]), hexc(GOLD))
    # cross and orb
    L.paint(R(cx - 1.6 * s, sp_top - 26 * s, cx + 1.6 * s, sp_top + 2), hexc(GOLD))
    L.paint(R(cx - 7 * s, sp_top - 19 * s, cx + 7 * s, sp_top - 16 * s), hexc(GOLD))
    L.paint(Shape(cx - 6, sp_top - 10, cx + 6, sp_top + 2).ellipse(cx, sp_top - 4 * s, 4 * s, 4 * s), hexc(GOLD_HI))
    for xx in (x0 - 2 * s, x1 + sw * 0.8):
        pinnacle(L, xx, bt + 1, 8 * s, 40 * s, gold=True)


def parliament(L, x0, x1, base_y, scale=1.0, flag_pole=True):
    """The Palace of Westminster's river front: buttresses with pinnacles, rows of Gothic
    windows, a steep roof, the central lantern and Victoria Tower at the far end."""
    s = scale
    h = 168 * s
    yt = base_y - h
    stone_f = face(STONE_WARM, 'front')
    # the steep roof behind the parapet
    L.paint(R(x0 + 10, yt - 34 * s, x1 - 160 * s, yt + 4), vgrad('#647894', '#3b4d68', yt - 34 * s, yt))
    L.paint(R(x0, yt, x1, base_y), vgrad(np.clip(stone_f * 1.05, 0, 1), stone_f * 0.9, yt, base_y))
    bays = int((x1 - x0) / (24 * s))
    bw = (x1 - x0) / bays
    win = Shape(x0, yt, x1, base_y)
    for i in range(bays):
        bx = x0 + i * bw
        for k, (wy, wh) in enumerate(((yt + 26 * s, 44 * s), (yt + 84 * s, 40 * s), (yt + 134 * s, 26 * s))):
            gothic_window(win, bx + bw * 0.3, wy, bw * 0.4, wh)
    L.paint(win, hexc('#4a5b72'))
    gl = Shape(x0, yt, x1, base_y)
    for i in range(bays):
        bx = x0 + i * bw
        for wy, wh in ((yt + 26 * s, 44 * s), (yt + 84 * s, 40 * s)):
            gl.rect(bx + bw * 0.34, wy + bw * 0.3, bx + bw * 0.66, wy + wh * 0.5)
    L.paint(gl, hexc('#9cc3e0'), alpha=0.45)
    # buttresses and their pinnacles
    for i in range(bays + 1):
        bx = x0 + i * bw
        L.paint(R(bx - 2.6 * s, yt - 2, bx + 2.6 * s, base_y), cylinder('#fbefd2', '#c2a87a', bx - 2.6 * s, bx + 2.6 * s))
        if i % 2 == 0:
            pinnacle(L, bx, yt + 2, 6 * s, 30 * s)
    # string courses and the pierced parapet
    sc = Shape(x0, yt - 6, x1, base_y)
    for yy in (yt + 4 * s, yt + 76 * s, yt + 128 * s):
        sc.rect(x0, yy - 1.4 * s, x1, yy + 1.4 * s)
    L.paint(sc, np.clip(stone_f * 1.14, 0, 1))
    for yy in (yt + 4 * s, yt + 76 * s, yt + 128 * s):
        soft_shadow(L, x0, yy + 1.4 * s, x1, yy + 5 * s, 0.25)
    # the central lantern
    lx = (x0 + x1) / 2 - 40 * s
    L.paint(R(lx - 14 * s, yt - 70 * s, lx + 14 * s, yt + 2), cylinder('#f9ebc9', '#bca275', lx - 14 * s, lx + 14 * s))
    L.paint(P([(lx - 15 * s, yt - 70 * s), (lx, yt - 170 * s), (lx + 15 * s, yt - 70 * s)]), hgrad('#6e819d', '#34465f', lx - 15 * s, lx + 15 * s))
    L.paint(R(lx - 1.2 * s, yt - 190 * s, lx + 1.2 * s, yt - 168 * s), hexc(GOLD))
    # Victoria Tower at the far end
    vx = x1 - 70 * s
    vw = 116 * s
    vt = base_y - 420 * s
    L.paint(R(vx - vw / 2, vt, vx + vw / 2, base_y), vgrad(np.clip(stone_f * 1.05, 0, 1), stone_f * 0.9, vt, base_y))
    L.paint(R(vx + vw / 2 - 18 * s, vt, vx + vw / 2, base_y), face(STONE_WARM, 'right'), alpha=0.85)
    vwin = Shape(vx - vw / 2, vt, vx + vw / 2, base_y)
    for k in range(6):
        wy = vt + 36 * s + k * 62 * s
        for j in range(3):
            gothic_window(vwin, vx - vw / 2 + 16 * s + j * 30 * s, wy, 16 * s, 44 * s)
    L.paint(vwin, hexc('#4a5b72'))
    vb = Shape(vx - vw / 2, vt, vx + vw / 2, base_y)
    for k in range(7):
        yy = vt + 22 * s + k * 62 * s
        vb.rect(vx - vw / 2, yy - 1.5 * s, vx + vw / 2, yy + 1.5 * s)
    L.paint(vb, np.clip(stone_f * 1.14, 0, 1))
    for xx in (vx - vw / 2, vx + vw / 2):
        L.paint(R(xx - 7 * s, vt - 40 * s, xx + 7 * s, vt + 30 * s), cylinder('#fbefd2', '#b89c6c', xx - 7 * s, xx + 7 * s))
        pinnacle(L, xx, vt - 38 * s, 13 * s, 44 * s, gold=True)
    for xx in (vx - vw / 4, vx + vw / 4):
        pinnacle(L, xx, vt + 2, 8 * s, 28 * s)
    if flag_pole:
        L.paint(R(vx - 1.3 * s, vt - 120 * s, vx + 1.3 * s, vt), hexc('#d9d4c8'))
    return (vx, vt - 120 * s)


def westminster(scale=1.0):
    """Big Ben and the Palace of Westminster in one layer; anchor is Big Ben's base."""
    s = scale
    w, h = int(700 * s), int(720 * s)
    L = Layer(w, h)
    base_y = h - 6
    bb_x = 70 * s
    flag = parliament(L, bb_x + 34 * s, w - 14, base_y, s)
    big_ben(L, bb_x, base_y, s)
    L.save('westminster', anchor=(bb_x, base_y), meta={'flag': [round(flag[0] - bb_x, 1), round(flag[1] - base_y, 1)]})
    return L


# ======================================================================== St Paul's

def st_pauls(scale=1.0):
    """St Paul's Cathedral: the colonnaded drum, the lead dome with its ribs, the lantern and
    golden cross, and the two baroque west towers. Anchor: the centre of the base."""
    s = scale
    w, h = int(560 * s), int(640 * s)
    L = Layer(w, h)
    cx, base_y = w / 2, h - 6
    stone = STONE
    sf = face(stone, 'front')
    # the body of the church (mostly hidden behind the riverside buildings)
    body_top = base_y - 150 * s
    L.paint(R(cx - 250 * s, body_top, cx + 250 * s, base_y), vgrad(np.clip(sf * 1.04, 0, 1), sf * 0.9, body_top, base_y))
    bwin = Shape(cx - 250 * s, body_top, cx + 250 * s, base_y)
    for i in range(-7, 8):
        x = cx + i * 32 * s
        if abs(i) > 1:
            bwin.rect(x - 6 * s, body_top + 34 * s, x + 6 * s, body_top + 70 * s)
            bwin.rect(x - 6 * s, body_top + 96 * s, x + 6 * s, body_top + 130 * s)
    L.paint(bwin, hexc('#5b6476'), alpha=0.85)
    pil = Shape(cx - 250 * s, body_top, cx + 250 * s, base_y)
    for i in range(-7, 9):
        x = cx + (i - 0.5) * 32 * s
        pil.rect(x - 2.2 * s, body_top + 10 * s, x + 2.2 * s, base_y)
    L.paint(pil, np.clip(sf * 1.1, 0, 1))
    _balustrade(L, cx - 250 * s, cx + 250 * s, body_top, 12 * s, stone)
    soft_shadow(L, cx - 250 * s, body_top + 2, cx + 250 * s, body_top + 10 * s, 0.3)
    # the west towers, left and right of the dome
    for side in (-1, 1):
        tx = cx + side * 205 * s
        tw = 52 * s
        tt = body_top - 120 * s
        L.paint(R(tx - tw / 2, tt, tx + tw / 2, body_top + 4), cylinder('#fbf3df', '#b6a585', tx - tw / 2, tx + tw / 2))
        op = Shape(tx - tw, tt, tx + tw, body_top)
        op.rect(tx - 9 * s, tt + 26 * s, tx + 9 * s, tt + 66 * s)
        L.paint(op, hexc('#4b5466'))
        L.paint(Shape(tx - 12, tt + 78 * s - 12, tx + 12, tt + 78 * s + 12).ellipse(tx, tt + 88 * s, 9 * s, 9 * s), hexc(GOLD))
        # the little cupola and golden pineapple
        L.paint(P([(tx - tw * 0.42, tt), (tx, tt - 48 * s), (tx + tw * 0.42, tt)]), hgrad('#7e93ad', '#3d4f68', tx - tw * 0.42, tx + tw * 0.42))
        L.paint(R(tx - tw * 0.3, tt - 8 * s, tx + tw * 0.3, tt + 2), np.clip(sf * 1.08, 0, 1))
        L.paint(Shape(tx - 6, tt - 66 * s, tx + 6, tt - 44 * s).ellipse(tx, tt - 52 * s, 4 * s, 7 * s), hexc(GOLD))
    # the drum: a ring of columns, a balustrade, then the attic with windows
    dr = 112 * s
    drum_bot, drum_top = body_top + 2, body_top - 96 * s
    L.paint(R(cx - dr, drum_top, cx + dr, drum_bot), cylinder('#fff8ea', '#b9a98a', cx - dr, cx + dr))
    cols = Shape(cx - dr, drum_top, cx + dr, drum_bot)
    gaps = Shape(cx - dr, drum_top, cx + dr, drum_bot)
    for k in range(16):
        a = np.pi * (k + 0.5) / 16
        x = cx - np.cos(a) * dr * 0.97
        cw_ = max(2.2 * s, 7.5 * s * np.sin(a))
        gaps.rect(x + cw_ * 0.6, drum_top + 14 * s, x + cw_ * 0.6 + max(1.5 * s, 6 * s * np.sin(a)), drum_bot - 8 * s)
        cols.rect(x - cw_ / 2, drum_top + 12 * s, x + cw_ / 2, drum_bot - 6 * s)
    L.paint(gaps, hexc('#4a4e5c'), alpha=0.8)
    L.paint(cols, cylinder('#ffffff', '#c9bba0', cx - dr, cx + dr))
    _balustrade(L, cx - dr - 4 * s, cx + dr + 4 * s, drum_top, 12 * s, stone)
    at = drum_top - 46 * s
    ar = dr * 0.86
    L.paint(R(cx - ar, at, cx + ar, drum_top), cylinder('#fff6e4', '#b5a483', cx - ar, cx + ar))
    aw = Shape(cx - ar, at, cx + ar, drum_top)
    for k in range(9):
        a = np.pi * (k + 0.5) / 9
        x = cx - np.cos(a) * ar * 0.9
        ww = 7 * s * np.sin(a) + 1.2
        aw.rect(x - ww / 2, at + 12 * s, x + ww / 2, drum_top - 10 * s)
    L.paint(aw, hexc('#59627a'), alpha=0.8)
    soft_shadow(L, cx - ar, at, cx + ar, at + 8 * s, 0.35)
    # the dome: grey-blue lead, ribs, lit upper left
    dw, dh = ar * 1.02, 150 * s
    dome_base = at + 1
    pts = [(cx - dw, dome_base)] + [(cx - np.cos(a) * dw, dome_base - np.sin(a) * dh) for a in np.linspace(0, np.pi, 60)] + [(cx + dw, dome_base)]
    dome = P(pts)

    def lead(X, Y):
        u = np.clip((X - cx) / dw, -1, 1)
        v = np.clip((dome_base - Y) / dh, 0, 1)
        nz = np.sqrt(np.clip(1 - u * u - (v * 0.9) ** 2, 0.05, 1))
        lit = np.clip(-u * 0.55 + v * 0.45 + nz * 0.45, 0, 1)
        return ramp([(0.0, '#2f3d55'), (0.4, '#4c6081'), (0.75, '#7c93b3'), (1.0, '#c9d6e6')], lit)
    L.paint(dome, lead)
    ribs = Shape(cx - dw, dome_base - dh, cx + dw, dome_base)
    for k in range(1, 16):
        a = np.pi * k / 16
        x_b = cx - np.cos(a) * dw
        pts_r = [(cx + (x_b - cx) * np.cos(t * np.pi / 2), dome_base - np.sin(t * np.pi / 2) * dh * (1 - 0.0)) for t in np.linspace(0, 1, 20)]
        ribs.stroke(pts_r, 1.3 * s)
    L.paint(ribs, hexc('#2c3a50'), alpha=0.35, clip=True)
    # the lantern, golden ball and cross
    lt = dome_base - dh - 66 * s
    L.paint(R(cx - 17 * s, lt, cx + 17 * s, dome_base - dh + 8 * s), cylinder('#fff7e6', '#b3a284', cx - 17 * s, cx + 17 * s))
    lop = Shape(cx - 17 * s, lt, cx + 17 * s, dome_base - dh)
    for k in (-1, 0, 1):
        lop.rect(cx + k * 9 * s - 2.5 * s, lt + 14 * s, cx + k * 9 * s + 2.5 * s, lt + 46 * s)
    L.paint(lop, hexc('#4b5466'))
    L.paint(P([(cx - 14 * s, lt), (cx, lt - 22 * s), (cx + 14 * s, lt)]), hgrad('#7a8fab', '#3a4b63', cx - 14 * s, cx + 14 * s))
    L.paint(Shape(cx - 8, lt - 36 * s, cx + 8, lt - 20 * s).ellipse(cx, lt - 28 * s, 6.5 * s, 6.5 * s), hgrad(GOLD_HI, '#b98428', cx - 6 * s, cx + 6 * s))
    L.paint(R(cx - 1.8 * s, lt - 62 * s, cx + 1.8 * s, lt - 32 * s), hexc(GOLD))
    L.paint(R(cx - 8 * s, lt - 54 * s, cx + 8 * s, lt - 50.5 * s), hexc(GOLD))
    L.save('st_pauls', anchor=(cx, base_y))
    return L


def _balustrade(L, x0, x1, y, h, stone):
    sf = face(stone, 'front')
    L.paint(R(x0, y - h, x1, y - h + 3), np.clip(sf * 1.12, 0, 1))
    L.paint(R(x0, y - 3, x1, y), sf)
    b = Shape(x0, y - h, x1, y)
    x = x0 + 3
    while x < x1 - 2:
        b.rect(x, y - h + 3, x + 1.6, y - 3)
        x += 4.2
    L.paint(b, np.clip(sf * 1.05, 0, 1))


# ======================================================================== the Gherkin

def gherkin(scale=1.0):
    """30 St Mary Axe: a glass bullet wrapped in a diamond grid, with dark spirals."""
    s = scale
    H_ = 560 * s
    W_ = 150 * s
    w, h = int(W_ + 20), int(H_ + 12)
    L = Layer(w, h)
    cx, base_y = w / 2, h - 4

    def half_width(t):  # t = 0 at the base, 1 at the tip
        return W_ / 2 * (0.66 + 0.55 * np.sin(np.clip(t, 0, 1) * np.pi * 0.86) - 0.21 * t) * np.sqrt(np.clip(1 - t ** 6, 0, 1))
    ts = np.linspace(0, 1, 90)
    left = [(cx - half_width(t), base_y - t * H_) for t in ts]
    right = [(cx + half_width(t), base_y - t * H_) for t in ts[::-1]]
    body = P(left + right)
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    t = np.clip((base_y - yy) / H_, 0, 1)
    hw = np.maximum(half_width(t), 1)
    u = np.clip((xx - cx) / hw, -1, 1)
    # around the cylinder: angle theta, lit from the left
    theta = np.arcsin(u)
    lit = np.clip(-np.sin(theta) * 0.5 + np.cos(theta) * 0.55 + 0.05, 0, 1)
    sky = smoothstep(0.2, 1.0, t) * 0.18
    col = ramp([(0, '#1f3f66'), (0.35, '#2f5f92'), (0.65, '#4f8dc4'), (0.88, '#8fc0e4'), (1, '#d2e8f6')], np.clip(lit + sky, 0, 1))
    # the diagrid: two families of helices
    phase = theta * 7.0
    hgt = (base_y - yy) / (22 * s)
    g1 = np.abs(np.sin((phase + hgt) * np.pi / 2))
    g2 = np.abs(np.sin((phase - hgt) * np.pi / 2))
    grid = np.maximum(smoothstep(0.965, 1.0, g1), smoothstep(0.965, 1.0, g2))
    # dark spirals
    spiral = smoothstep(0.62, 0.9, np.sin(theta * 3.0 + hgt * 0.42 * np.pi))
    col = col * (1 - spiral[..., None] * 0.35)
    col = lerp(col, hexc('#e8f1f8'), (grid * 0.55)[..., None])
    a = body.a
    full = np.zeros((h, w), np.float32)
    full[body.y0:body.y0 + a.shape[0], body.x0:body.x0 + a.shape[1]] = a[:h - body.y0, :w - body.x0] if body.y0 >= 0 else 0
    L.paint((full, 0, 0), col)
    # the dark glass cap
    cap_t = 0.93
    cap = [(cx - half_width(t2), base_y - t2 * H_) for t2 in np.linspace(cap_t, 1, 12)] + [(cx + half_width(t2), base_y - t2 * H_) for t2 in np.linspace(1, cap_t, 12)]
    L.paint(P(cap), hexc('#1d3150'))
    L.save('gherkin', anchor=(cx, base_y))
    return L


# ======================================================================== the Shard

def shard(scale=1.0):
    """The Shard: a splintered glass pyramid. The sunlit facets reflect the sky; the shaded
    ones are deep blue; fine floor lines and fins catch the light."""
    s = scale
    H_ = 960 * s
    w, h = int(290 * s), int(H_ + 40 * s)
    L = Layer(w, h)
    cx, base_y = w / 2, h - 4
    top = base_y - H_
    bl, br = cx - 128 * s, cx + 128 * s
    # four facets, each a narrow splinter
    facets = [
        ([(bl, base_y), (cx - 10 * s, top + 30 * s), (cx - 4 * s, top + 4 * s), (cx - 40 * s, base_y)], ('#d6ecf9', '#8dc3e6', '#5d9fd1')),
        ([(cx - 40 * s, base_y), (cx - 4 * s, top + 4 * s), (cx + 4 * s, top - 18 * s), (cx + 18 * s, base_y)], ('#b4daf2', '#6aa9d8', '#3f7fbd')),
        ([(cx + 18 * s, base_y), (cx + 6 * s, top - 6 * s), (cx + 12 * s, top + 26 * s), (br - 22 * s, base_y)], ('#5d93c4', '#3c6fa6', '#294f80')),
        ([(br - 22 * s, base_y), (cx + 12 * s, top + 26 * s), (cx + 14 * s, top + 60 * s), (br, base_y)], ('#3d6797', '#2b4d78', '#1d3657')),
    ]
    for k, (pts, (c0, c1, c2)) in enumerate(facets):
        sh = P(pts)

        def glass(X, Y, c0=c0, c1=c1, c2=c2, k=k):
            t = np.clip((base_y - Y) / H_, 0, 1)[..., None]
            c = np.where(t > 0.5, lerp(hexc(c1), hexc(c0), (t - 0.5) * 2), lerp(hexc(c2), hexc(c1), t * 2))
            # broad reflections of clouds drifting across the glass
            n = noise(X.shape[0], X.shape[1], 60 * s, 2, 40 + k)[..., None]
            return np.clip(c * (1 + n * 0.08), 0, 1)
        L.paint(sh, glass)
    # floor lines and vertical fins
    lines = Shape(bl, top, br, base_y)
    y = base_y - 6 * s
    while y > top + 60 * s:
        lines.rect(bl, y - 0.45, br, y + 0.45)
        y -= 7.2 * s
    L.paint(lines, hexc('#e9f4fb'), alpha=0.28, clip=True)
    fins = Shape(bl, top, br, base_y)
    for f in np.linspace(-0.85, 0.85, 9):
        fins.stroke([(cx + f * 128 * s, base_y), (cx + f * 4 * s, top + 40 * s)], 0.9 * s)
    L.paint(fins, hexc('#f1f8fc'), alpha=0.25, clip=True)
    # the facet edges catch the sun
    edges = Shape(bl, top, br, base_y)
    edges.stroke([(cx - 40 * s, base_y), (cx - 4 * s, top + 4 * s)], 1.6 * s)
    edges.stroke([(cx + 18 * s, base_y), (cx + 6 * s, top - 6 * s)], 1.4 * s)
    L.paint(edges, hexc('#ffffff'), alpha=0.55)
    # the open, splintered top
    for dx, dy in ((-6, -10), (4, -24), (12, 6)):
        sp = [(cx + dx * s - 3 * s, top + 40 * s), (cx + dx * s, top + dy * s - 10 * s), (cx + dx * s + 3 * s, top + 40 * s)]
        L.paint(P(sp), hexc('#cfe5f5'))
    L.save('shard', anchor=(cx, base_y))
    return L


# ======================================================================== the City towers

def _glass_tower(L, pts, base_y, top_y, c_lit, c_mid, c_dark, seed, fins=9, floors=7.5):
    """A glass tower face: a vertical gradient, drifting reflections, floor lines and fins."""
    sh = P(pts)
    x0, _, x1, _ = _bb(pts)

    def glass(X, Y):
        t = np.clip((base_y - Y) / max(base_y - top_y, 1), 0, 1)[..., None]
        c = np.where(t > 0.5, lerp(hexc(c_mid), hexc(c_lit), (t - 0.5) * 2), lerp(hexc(c_dark), hexc(c_mid), t * 2))
        n = noise(X.shape[0], X.shape[1], 50, 2, seed)[..., None]
        return np.clip(c * (1 + n * 0.07), 0, 1)
    L.paint(sh, glass)
    ln = Shape(*_bb(pts))
    y = base_y - 4
    while y > top_y:
        ln.rect(x0, y - 0.4, x1, y + 0.4)
        y -= floors
    L.paint(ln, hexc('#e8f2f9'), alpha=0.22, clip=True)
    fn = Shape(*_bb(pts))
    for k in range(1, fins):
        x = x0 + (x1 - x0) * k / fins
        fn.rect(x - 0.5, top_y, x + 0.5, base_y)
    L.paint(fn, hexc('#eef5fa'), alpha=0.18, clip=True)


def city_towers(scale=1.0):
    """The City cluster behind the river: the Walkie-Talkie, the Cheesegrater and quieter towers.
    Anchor: the left end of the base line."""
    s = scale
    w, h = int(760 * s), int(640 * s)
    L = Layer(w, h)
    base_y = h - 4
    # quieter background towers first
    for (x, tw, th, cols) in ((40, 90, 360, ('#c9dce9', '#9fbcd2', '#7896b1')), (560, 110, 420, ('#d3dde6', '#a9b9c8', '#8195aa')), (680, 70, 300, ('#d9e4ec', '#b3c6d6', '#8ea6bb'))):
        x, tw, th = x * s, tw * s, th * s
        pts = [(x, base_y), (x, base_y - th), (x + tw, base_y - th), (x + tw, base_y)]
        _glass_tower(L, pts, base_y, base_y - th, *cols, seed=int(x), fins=6, floors=8 * s)
        L.paint(R(x + tw * 0.7, base_y - th, x + tw, base_y), face('#8ea6bb', 'right'), alpha=0.35, clip=True)
    # the Cheesegrater: a tall wedge sloping back toward the Thames
    cx0, cx1 = 420 * s, 560 * s
    ct = base_y - 560 * s
    wedge = [(cx0, base_y), (cx0, base_y - 330 * s), (cx1 - 20 * s, ct), (cx1, ct + 6 * s), (cx1, base_y)]
    _glass_tower(L, wedge, base_y, ct, '#d5e9f6', '#8ab9dc', '#4f83b3', seed=7, fins=8, floors=8 * s)
    lat = Shape(cx0, ct, cx1, base_y)
    for k in range(1, 12):
        y = base_y - k * 44 * s
        lat.stroke([(cx0, y), (cx1, y - 44 * s)], 1.2 * s)
        lat.stroke([(cx0, y - 44 * s), (cx1, y)], 1.2 * s)
    L.paint(lat, hexc('#f1ece0'), alpha=0.55, clip=True)
    L.paint(R(cx1 - 8 * s, ct, cx1, base_y), hexc('#ffb347'), alpha=0.7)  # the yellow-painted core edge
    # the Walkie-Talkie: wider at the top, curved sides
    wx, ww, wh = 210 * s, 150 * s, 470 * s
    ts = np.linspace(0, 1, 40)
    left = [(wx - (np.sin(t * np.pi * 0.5) ** 2) * 26 * s, base_y - t * wh) for t in ts]
    right = [(wx + ww + (np.sin(t * np.pi * 0.5) ** 1.5) * 36 * s, base_y - t * wh) for t in ts[::-1]]
    top_curve = [(wx - 26 * s + (ww + 62 * s) * f, base_y - wh - np.sin(f * np.pi) * 14 * s) for f in np.linspace(0, 1, 20)]
    shape = left + top_curve + right
    _glass_tower(L, shape, base_y, base_y - wh - 14 * s, '#cfe6f5', '#7fb2da', '#3f74a8', seed=11, fins=11, floors=7 * s)
    L.paint(P([(wx + ww * 0.62, base_y), (wx + ww + 36 * s, base_y - wh), (wx + ww + 40 * s, base_y)]), hexc('#203a5c'), alpha=0.25, clip=True)
    # the sky garden glass roof
    L.paint(P(top_curve + [(wx + ww + 36 * s, base_y - wh + 18 * s), (wx - 26 * s, base_y - wh + 18 * s)]), hexc('#e3f2fb'), alpha=0.55, clip=True)
    L.save('city_towers', anchor=(0, base_y))
    return L


# ======================================================================== Tower Bridge

def tb_tower(L, cx, base_y, s, deck_y):
    """One Gothic tower: stone body, corner turrets with slate spires and gilded finials."""
    tw = 118 * s
    top = base_y - 372 * s
    sf, ss = face('#efe5cf', 'front'), face('#efe5cf', 'right')
    # the pier in the river
    L.paint(R(cx - tw * 0.72, deck_y + 30 * s, cx + tw * 0.72, base_y), vgrad('#d9cfba', '#9f9684', deck_y, base_y))
    L.paint(P([(cx - tw * 0.72, base_y), (cx - tw * 0.95, base_y), (cx - tw * 0.72, deck_y + 30 * s)]), hexc('#b9af9a'))
    # the tower body
    L.paint(R(cx - tw / 2, top, cx + tw / 2, deck_y + 34 * s), vgrad(np.clip(sf * 1.05, 0, 1), sf * 0.9, top, deck_y))
    L.paint(R(cx + tw / 2 - 16 * s, top, cx + tw / 2, deck_y + 34 * s), ss, alpha=0.9)
    win = Shape(cx - tw / 2, top, cx + tw / 2, deck_y)
    for k, (wy, wh) in enumerate(((top + 44 * s, 54 * s), (top + 122 * s, 54 * s), (top + 200 * s, 40 * s))):
        for j in (-1, 1):
            gothic_window(win, cx + j * 22 * s - 9 * s, wy, 18 * s, wh)
    big = Shape(cx - tw / 2, top, cx + tw / 2, deck_y + 34 * s)
    gothic_window(big, cx - 30 * s, deck_y - 70 * s, 60 * s, 104 * s)
    L.paint(win, hexc('#46566e'))
    L.paint(big, vgrad('#2f3b4f', '#4a5b74', deck_y - 70 * s, deck_y + 34 * s))
    small = Shape(cx - tw / 2, top, cx + tw / 2, deck_y)
    for wy in (top + 52 * s, top + 130 * s):
        for j in (-1, 1):
            gothic_window(small, cx + j * 44 * s - 4 * s, wy + 10 * s, 8 * s, 30 * s)
    L.paint(small, hexc('#46566e'))
    bands = Shape(cx - tw / 2, top, cx + tw / 2, deck_y)
    for yy in (top + 30 * s, top + 108 * s, top + 186 * s, top + 256 * s):
        bands.rect(cx - tw / 2, yy - 1.6 * s, cx + tw / 2, yy + 1.6 * s)
    L.paint(bands, np.clip(sf * 1.12, 0, 1))
    # corner turrets with spires
    for j in (-1, 1):
        tx = cx + j * (tw / 2 - 9 * s)
        L.paint(R(tx - 13 * s, top - 44 * s, tx + 13 * s, top + 60 * s), cylinder('#fbf3e0', '#b8a989', tx - 13 * s, tx + 13 * s))
        tw_win = Shape(tx - 13 * s, top - 44 * s, tx + 13 * s, top)
        gothic_window(tw_win, tx - 3 * s, top - 34 * s, 6 * s, 22 * s)
        L.paint(tw_win, hexc('#46566e'))
        L.paint(R(tx - 15 * s, top - 47 * s, tx + 15 * s, top - 42 * s), np.clip(sf * 1.15, 0, 1))
        L.paint(P([(tx - 15 * s, top - 46 * s), (tx, top - 118 * s), (tx + 15 * s, top - 46 * s)]), hgrad('#6c84a6', '#2f4361', tx - 15 * s, tx + 15 * s))
        L.paint(R(tx - 1.4 * s, top - 128 * s, tx + 1.4 * s, top - 108 * s), hexc(GOLD))
        L.paint(Shape(tx - 5, top - 134 * s, tx + 5, top - 124 * s).ellipse(tx, top - 129 * s, 2.6 * s, 2.6 * s), hexc(GOLD_HI))
    # the central roof
    L.paint(P([(cx - tw * 0.34, top + 2), (cx - tw * 0.12, top - 70 * s), (cx + tw * 0.12, top - 70 * s), (cx + tw * 0.34, top + 2)]), hgrad('#7790b1', '#2c3f5c', cx - tw * 0.34, cx + tw * 0.34))
    L.paint(P([(cx - tw * 0.12, top - 70 * s), (cx, top - 104 * s), (cx + tw * 0.12, top - 70 * s)]), hgrad('#8aa2c2', '#34496a', cx - tw * 0.12, cx + tw * 0.12))
    L.paint(R(cx - 1.6 * s, top - 128 * s, cx + 1.6 * s, top - 100 * s), hexc(GOLD))
    L.paint(Shape(cx - 6, top - 134 * s, cx + 6, top - 124 * s).ellipse(cx, top - 129 * s, 3 * s, 3 * s), hexc(GOLD_HI))
    L.paint(R(cx - tw / 2 - 3 * s, top - 4 * s, cx + tw / 2 + 3 * s, top + 3 * s), np.clip(sf * 1.15, 0, 1))
    soft_shadow(L, cx - tw / 2, top + 3 * s, cx + tw / 2, top + 10 * s, 0.35)


def _lattice(L, x0, x1, y0, y1, s, colour=IRON_BLUE):
    """A high-level walkway: a blue box girder with white lattice."""
    L.paint(R(x0, y0, x1, y1), vgrad('#5f95cf', '#2f5f97', y0, y1))
    lat = Shape(x0, y0, x1, y1)
    step = (y1 - y0) * 1.1
    x = x0
    while x < x1:
        lat.stroke([(x, y0 + 2), (x + step, y1 - 2)], 1.6 * s)
        lat.stroke([(x + step, y0 + 2), (x, y1 - 2)], 1.6 * s)
        x += step
    L.paint(lat, hexc('#f2f6fa'), alpha=0.85, clip=True)
    L.paint(R(x0, y0, x1, y0 + 2.2 * s), hexc('#f5f8fb'))
    L.paint(R(x0, y1 - 2.2 * s, x1, y1), hexc('#e3ebf3'))
    soft_shadow(L, x0, y1, x1, y1 + 6 * s, 0.25)


def tower_bridge(scale=1.0):
    """Tower Bridge side-on: two towers on river piers, the twin high walkways, the bascule
    deck and the suspension chains to the banks. Anchor: the left end at the waterline."""
    s = scale
    span = 360 * s
    side = 230 * s
    w, h = int(span + 2 * side + 140 * s), int(560 * s)
    L = Layer(w, h)
    base_y = h - 4
    deck_y = base_y - 74 * s
    t1, t2 = side + 70 * s, side + 70 * s + span
    # suspension chains from the towers to the banks, with hangers
    chains = Shape(0, 0, w, h)
    hang = Shape(0, 0, w, h)
    chain_hi = Shape(0, 0, w, h)

    def chain_y(f):
        y0, y1 = deck_y - 236 * s, deck_y - 26 * s
        return lerp(y0, y1, f) + 34 * s * np.sin(np.pi * f) * (1 - f * 0.35)
    for tx, sgn in ((t1, -1), (t2, 1)):
        pts = [(tx + sgn * (52 * s + f * (side + 14 * s)), chain_y(f)) for f in np.linspace(0, 1, 36)]
        chains.stroke(pts, 7 * s)
        chain_hi.stroke([(x, y - 2.4 * s) for x, y in pts], 1.4 * s)
        for f in np.linspace(0.12, 0.9, 8):
            x = tx + sgn * (52 * s + f * (side + 14 * s))
            hang.rect(x - 0.8 * s, chain_y(f), x + 0.8 * s, deck_y - 8 * s)
    L.paint(hang, hexc('#e9eef4'))
    L.paint(chains, vgrad('#6aa0d8', '#2f6099', deck_y - 240 * s, deck_y))
    L.paint(chain_hi, hexc('#f4f8fb'), alpha=0.8)
    # the road deck: side spans and the bascules between the towers
    L.paint(R(0, deck_y - 6 * s, w, deck_y + 22 * s), vgrad('#5d7fa9', '#2a4566', deck_y - 6 * s, deck_y + 22 * s))
    L.paint(R(0, deck_y - 9 * s, w, deck_y - 5 * s), hexc('#eef3f8'))
    rail = Shape(0, deck_y - 22 * s, w, deck_y)
    x = 4
    while x < w:
        rail.rect(x, deck_y - 18 * s, x + 1.4 * s, deck_y - 6 * s)
        x += 8 * s
    rail.rect(0, deck_y - 19 * s, w, deck_y - 17 * s)
    L.paint(rail, hexc('#e6edf4'), alpha=0.9)
    soft_shadow(L, 0, deck_y + 22 * s, w, deck_y + 34 * s, 0.3)
    # the shore abutments at each end
    for ax in (0, w - 70 * s):
        L.paint(R(ax, deck_y - 30 * s, ax + 70 * s, base_y), vgrad('#e7dcc4', '#a69c88', deck_y - 30 * s, base_y))
    # the towers
    for tx in (t1, t2):
        tb_tower(L, tx, base_y, s, deck_y)
    # the high-level walkways between the towers
    for y0 in (deck_y - 268 * s, deck_y - 236 * s):
        _lattice(L, t1 + 59 * s, t2 - 59 * s, y0, y0 + 22 * s, s)
    L.save('tower_bridge', anchor=(0, base_y), meta={'towers': [round(t1, 1), round(t2, 1)]})
    return L
