"""Riverside buildings: facades with real window detail, cornices, roofs and chimneys, all lit by
the same sun, with a gentle perspective so each building shows a side face toward the centre."""
import numpy as np

import world
from paint import Shape, blur, hexc, lerp, noise, smoothstep

WARM = hexc('#fff1d6')
COOL = hexc('#5d7698')
GLASS_TOP = hexc('#bcdcf0')
GLASS_MID = hexc('#6f9fc6')
GLASS_LOW = hexc('#2f4f72')
LIT_WINDOW = hexc('#ffd998')
SLATE = '#4b6282'

MATERIALS = {
    'brick': '#b65b3e', 'brick_warm': '#c66e45', 'brick_dark': '#94493a', 'terracotta': '#d4844f',
    'stone': '#efe0bd', 'cream': '#f3e7cc', 'sand': '#e6cf9f', 'render_pink': '#e9c3a8',
    'grey': '#cfc8b8', 'ochre': '#ddb070', 'white': '#f6f1e6',
}


def face(base, which):
    """The colour of a surface given which way it faces (the sun is upper left, in front)."""
    b = hexc(base) if isinstance(base, str) else np.asarray(base, np.float32)
    if which == 'front':
        return np.clip(lerp(b, b * WARM, 0.25), 0, 1)
    if which == 'left':  # faces the sun
        return np.clip(b * WARM * 1.08, 0, 1)
    if which == 'right':  # in shade, a little cooled by the sky
        return np.clip(lerp(b * 0.66, COOL * 0.75, 0.13), 0, 1)
    if which == 'top':
        return np.clip(b * 1.1, 0, 1)
    if which == 'under':
        return np.clip(lerp(b * 0.45, COOL * 0.45, 0.25), 0, 1)
    return b


def surface(base, which, y0, y1, seed, tex=0.035):
    """A colour function for a wall: lighter towards the sky, a touch darker at street level,
    with a faint, uneven material tone."""
    c = face(base, which)

    def f(X, Y):
        t = np.clip((Y - y0) / max(y1 - y0, 1), 0, 1)[..., None]
        n = noise(X.shape[0], X.shape[1], 26, 3, seed)[..., None]
        out = c * (1.04 - 0.1 * t) * (1 + n * tex)
        return np.clip(out, 0, 1)
    return f


def soft_shadow(L, x0, y0, x1, y1, strength=0.35, colour='#2a2830'):
    """A soft band of shade (under a cornice, a sill, an overhang), clipped to existing paint."""
    sh = Shape(x0, y0 - 2, x1, y1 + 2).rect(x0, y0, x1, y1)
    a = blur(sh.a, max((y1 - y0) * 0.35, 0.6))
    L.paint((a * strength, sh.x0, sh.y0), hexc(colour), clip=True, mode='multiply')


def window_row(L, xs, y, w, h, frame='#f4efe4', wall='#b65b3e', arch=False, rng=None, lit=0.07, bars=True, sill=True, which='front'):
    """A row of windows with the same top and height: openings, glass, frames, sills, shade."""
    rng = rng or np.random.default_rng(0)
    if not xs:
        return
    x_min, x_max = min(xs) - 3, max(xs) + w + 3
    wall_c = face(wall, which)
    reveal_dark = np.clip(wall_c * 0.48, 0, 1)
    # the opening (seen as the dark reveal around the glass)
    op = Shape(x_min, y - h * 0.3 - 2, x_max, y + h + 2)
    gl = Shape(x_min, y - h * 0.3 - 2, x_max, y + h + 2)
    fr = Shape(x_min, y - h * 0.3 - 2, x_max, y + h + 2)
    m = max(0.9, w * 0.11)
    for x in xs:
        if arch:
            r = w / 2
            pts = [(x, y + h), (x, y + r)] + [(x + r - np.cos(a) * r, y + r - np.sin(a) * r) for a in np.linspace(0, np.pi, 14)] + [(x + w, y + h)]
            op.poly(pts)
            gpts = [(x + m, y + h - m * 0.6), (x + m, y + r)] + [(x + r - np.cos(a) * (r - m), y + r - np.sin(a) * (r - m)) for a in np.linspace(0, np.pi, 14)] + [(x + w - m, y + h - m * 0.6)]
            gl.poly(gpts)
        else:
            op.rect(x, y, x + w, y + h)
            gl.rect(x + m, y + m, x + w - m, y + h - m * 0.6)
        if bars:
            bw = max(0.6, w * 0.055)
            fr.rect(x + w / 2 - bw / 2, y + m, x + w / 2 + bw / 2, y + h - m)  # the mullion
            fr.rect(x + m, y + h * 0.52 - bw / 2, x + w - m, y + h * 0.52 + bw / 2)  # the meeting rail
    L.paint(op, reveal_dark)
    y_top = y

    bright = {}
    for x in xs:
        bright[int(x)] = rng.uniform(-0.12, 0.12)

    def glass(X, Y):
        t = np.clip((Y - y_top) / h, 0, 1)[..., None]
        c = np.where(t < 0.4, lerp(GLASS_TOP, GLASS_MID, t / 0.4), lerp(GLASS_MID, GLASS_LOW, (t - 0.4) / 0.6))
        # each pane reflects a slightly different patch of sky
        k = np.zeros(X.shape, np.float32)
        for bx, v in bright.items():
            k = np.where((X >= bx) & (X < bx + w), v, k)
        sheen = (0.5 + 0.5 * np.sin(X * 0.011 + 1.3))[..., None] * 0.08
        return np.clip(c * (1 + k[..., None]) + sheen, 0, 1)
    L.paint(gl, glass)
    # some windows are lit from inside or have warm curtains
    for x in xs:
        if rng.random() < lit:
            sh = Shape(x, y, x + w, y + h).rect(x + m, y + m, x + w - m, y + h - m)
            L.paint(sh, LIT_WINDOW, alpha=0.75, clip=True)
        elif rng.random() < 0.12:
            sh = Shape(x, y, x + w, y + h).rect(x + m, y + m, x + w - m, y + h * 0.4)
            L.paint(sh, hexc(['#e8d6b0', '#d7b98d', '#c9d6dc'][rng.integers(0, 3)]), alpha=0.8, clip=True)
    if bars:
        L.paint(fr, hexc(frame))
    # the lintel shades the top of the opening; the left reveal is in shade
    sh = Shape(x_min, y - 2, x_max, y + h + 2)
    for x in xs:
        sh.rect(x, y, x + w, y + h * 0.16)
        sh.rect(x, y, x + max(1.0, w * 0.14), y + h)
    L.paint((blur(sh.a, 0.8) * 0.45, sh.x0, sh.y0), hexc('#1d2433'), clip=True, mode='multiply')
    if sill:
        s = Shape(x_min, y + h - 1, x_max, y + h + 4)
        for x in xs:
            s.rect(x - w * 0.08, y + h, x + w * 1.08, y + h + max(1.2, h * 0.07))
        L.paint(s, np.clip(face(wall, which) * 1.18 + 0.05, 0, 1))
        soft_shadow_strip = Shape(x_min, y + h, x_max, y + h + 6)
        for x in xs:
            soft_shadow_strip.rect(x - w * 0.05, y + h + max(1.2, h * 0.07), x + w * 1.05, y + h + max(2.4, h * 0.14))
        L.paint((blur(soft_shadow_strip.a, 0.7) * 0.3, soft_shadow_strip.x0, soft_shadow_strip.y0), hexc('#2a2830'), clip=True, mode='multiply')


def lintels(L, xs, y, w, h, base, keystone=True, which='front'):
    """Stone lintels over a row of windows, with keystones."""
    stone = np.clip(face('#efe3c6', which), 0, 1)
    sh = Shape(min(xs) - w, y - h * 0.3, max(xs) + 2 * w, y + 2)
    for x in xs:
        sh.rect(x - w * 0.12, y - h * 0.16, x + w * 1.12, y - 0.4)
    L.paint(sh, stone)
    if keystone:
        k = Shape(min(xs) - w, y - h * 0.3, max(xs) + 2 * w, y + 3)
        for x in xs:
            cx = x + w / 2
            k.poly([(cx - w * 0.11, y - h * 0.2), (cx + w * 0.11, y - h * 0.2), (cx + w * 0.07, y + 1), (cx - w * 0.07, y + 1)])
        L.paint(k, np.clip(stone * 1.04, 0, 1))
    soft_shadow(L, min(xs) - w * 0.12, y - 0.5, max(xs) + w * 1.12, y + h * 0.06, 0.18)


def quoins(L, x, y0, y1, bw, base, side='left'):
    """Alternating stone blocks up a corner."""
    stone = face('#f0e5ca', 'front')
    n = int((y1 - y0) / (bw * 0.55))
    sh = Shape(x - bw * 1.2, y0, x + bw * 1.2, y1)
    for i in range(n):
        yy0 = y0 + i * (y1 - y0) / n
        yy1 = yy0 + (y1 - y0) / n - 1.0
        ww = bw if i % 2 == 0 else bw * 0.62
        if side == 'left':
            sh.rect(x, yy0, x + ww, yy1)
        else:
            sh.rect(x - ww, yy0, x, yy1)
    L.paint(sh, stone)


def rustication(L, x0, x1, y0, y1, step):
    """Horizontal grooves cut into a stone ground floor."""
    g = Shape(x0, y0, x1, y1)
    hi = Shape(x0, y0, x1, y1)
    y = y0 + step
    while y < y1 - 1:
        g.rect(x0, y - 0.7, x1, y + 0.5)
        hi.rect(x0, y + 0.5, x1, y + 1.4)
        y += step
    L.paint(g, hexc('#3a3226'), alpha=0.35, clip=True, mode='multiply')
    L.paint(hi, hexc('#fff6e2'), alpha=0.35, clip=True)


def pilasters(L, xs, y0, y1, pw, base):
    """Flat pilasters: a lit face with a shaded right edge."""
    sh = Shape(min(xs) - pw, y0, max(xs) + pw, y1)
    dk = Shape(min(xs) - pw, y0, max(xs) + pw, y1)
    for x in xs:
        sh.rect(x - pw / 2, y0, x + pw / 2, y1)
        dk.rect(x + pw / 2, y0, x + pw / 2 + max(1.2, pw * 0.22), y1)
    L.paint(sh, np.clip(face(base, 'front') * 1.06 + 0.02, 0, 1))
    L.paint((blur(dk.a, 0.6) * 0.35, dk.x0, dk.y0), hexc('#2a2830'), clip=True, mode='multiply')


def pediments(L, xs, y, w, h, base, kind='triangle'):
    """Hoods over the windows of the main floor."""
    stone = np.clip(face(base, 'front') * 1.1 + 0.03, 0, 1)
    sh = Shape(min(xs) - w, y - h * 0.5, max(xs) + 2 * w, y + 3)
    for x in xs:
        if kind == 'triangle':
            sh.poly([(x - w * 0.16, y), (x + w / 2, y - h * 0.24), (x + w * 1.16, y)])
        else:
            sh.poly([(x - w * 0.16, y)] + [(x + w / 2 - np.cos(a) * w * 0.66, y - np.sin(a) * h * 0.16) for a in np.linspace(0, np.pi, 12)] + [(x + w * 1.16, y)])
        sh.rect(x - w * 0.16, y - 0.5, x + w * 1.16, y + max(1.4, h * 0.05))
    L.paint(sh, stone)
    soft_shadow(L, min(xs) - w * 0.16, y + max(1.4, h * 0.05), max(xs) + w * 1.16, y + h * 0.14, 0.25)


def balcony(L, x0, x1, y, h):
    """A black wrought-iron balcony rail."""
    iron = hexc('#24272d')
    sh = Shape(x0 - 2, y - h - 2, x1 + 2, y + 3)
    sh.rect(x0, y - h, x1, y - h + max(1.0, h * 0.12))
    sh.rect(x0, y - max(1.0, h * 0.1), x1, y)
    step = max(2.2, h * 0.28)
    x = x0
    while x <= x1:
        sh.rect(x, y - h, x + max(0.6, h * 0.06), y)
        x += step
    L.paint(sh, iron, alpha=0.92)
    soft_shadow(L, x0, y, x1, y + h * 0.5, 0.2)


def cornice(L, x0, x1, y, depth, base, which='front'):
    """A moulded cornice: lit top, light face, soft shadow beneath."""
    top = Shape(x0 - depth * 0.4, y - depth, x1 + depth * 0.4, y + depth)
    top.rect(x0 - depth * 0.35, y - depth * 0.55, x1 + depth * 0.35, y)
    L.paint(top, np.clip(face(base, which) * 1.15 + 0.04, 0, 1))
    hi = Shape(x0 - depth, y - depth, x1 + depth, y).rect(x0 - depth * 0.35, y - depth * 0.55, x1 + depth * 0.35, y - depth * 0.38)
    L.paint(hi, np.clip(face(base, 'top') * 1.12 + 0.06, 0, 1))
    soft_shadow(L, x0, y, x1, y + depth * 1.1, 0.42)


def chimney(L, x, y_base, w, h, base, pots=2, rng=None):
    rng = rng or np.random.default_rng(0)
    L.paint(Shape(x, y_base - h, x + w, y_base).rect(x, y_base - h, x + w, y_base), face(base, 'front'))
    L.paint(Shape(x, y_base - h, x + w, y_base).rect(x + w * 0.62, y_base - h, x + w, y_base), face(base, 'right'))
    L.paint(Shape(x - 2, y_base - h - 3, x + w + 2, y_base - h + 3).rect(x - w * 0.08, y_base - h - 2, x + w * 1.08, y_base - h + 1.5), np.clip(face(base, 'top') * 1.15, 0, 1))
    for k in range(pots):
        px = x + w * (0.22 + 0.5 * k / max(pots - 1, 1)) - w * 0.08
        pw, ph = w * 0.16, h * 0.28
        L.paint(Shape(px, y_base - h - ph, px + pw, y_base - h).rect(px, y_base - h - ph, px + pw, y_base - h - 1), face('#c0663f', 'front'))
        L.paint(Shape(px, y_base - h - ph, px + pw, y_base - h).rect(px + pw * 0.6, y_base - h - ph, px + pw, y_base - h - 1), face('#c0663f', 'right'))


def mansard(L, x0, x1, y_base, h, rng, dormers=3, colour=SLATE, dormer_w=None):
    """A slate mansard roof with dormer windows."""
    inset = h * 0.45
    pts = [(x0 - 2, y_base), (x0 + inset, y_base - h), (x1 - inset, y_base - h), (x1 + 2, y_base)]
    sh = Shape(*_bb(pts)).poly(pts)

    def slate(X, Y):
        t = np.clip((Y - (y_base - h)) / h, 0, 1)[..., None]
        c = lerp(hexc('#7f97b6'), hexc(colour), 0.35 + 0.65 * t)
        lines = (np.sin(Y * 1.7) > 0.86)[..., None] * 0.05
        return np.clip(c * (1 - lines), 0, 1)
    L.paint(sh, slate)
    # the ridge catches the light
    L.paint(Shape(x0 + inset - 2, y_base - h - 3, x1 - inset + 2, y_base - h + 3).rect(x0 + inset, y_base - h - 1.5, x1 - inset, y_base - h + 1.2), hexc('#c6d3e2'))
    # dormers
    span = (x1 - x0) - 2 * inset
    dw = dormer_w or min(h * 0.75, span / (dormers * 1.8))
    for k in range(dormers):
        cx = x0 + inset + span * (k + 0.5) / dormers
        dx0, dx1 = cx - dw / 2, cx + dw / 2
        dy0 = y_base - h * 0.88
        body = Shape(dx0 - 2, dy0 - dw * 0.5, dx1 + 2, y_base).rect(dx0, dy0, dx1, y_base - h * 0.12)
        L.paint(body, face('#f0e8d8', 'front'))
        roof = [(dx0 - dw * 0.12, dy0 + 1), (cx, dy0 - dw * 0.42), (dx1 + dw * 0.12, dy0 + 1)]
        L.paint(Shape(*_bb(roof)).poly(roof), hexc(colour))
        L.paint(Shape(*_bb(roof)).poly([(cx, dy0 - dw * 0.42), (dx1 + dw * 0.12, dy0 + 1), (cx, dy0 + 1)]), face(colour, 'right'))
        window_row(L, [dx0 + dw * 0.2], dy0 + dw * 0.18, dw * 0.6, (y_base - h * 0.12 - dy0) * 0.7, wall='#f0e8d8', rng=rng, sill=False)
        soft_shadow(L, dx1, dy0, dx1 + dw * 0.35, y_base - h * 0.12, 0.25)


def pitched(L, x0, x1, y_base, h, colour=SLATE):
    """A pitched roof seen along its length, rising behind the parapet."""
    pts = [(x0 + 4, y_base), (x0 + h * 0.6, y_base - h), (x1 - h * 0.6, y_base - h), (x1 - 4, y_base)]
    sh = Shape(*_bb(pts)).poly(pts)

    def slate(X, Y):
        t = np.clip((Y - (y_base - h)) / h, 0, 1)[..., None]
        return lerp(hexc('#8aa1bd'), hexc(colour), 0.25 + 0.75 * t)
    L.paint(sh, slate)
    L.paint(Shape(x0, y_base - h - 3, x1, y_base - h + 3).rect(x0 + h * 0.6, y_base - h - 1.2, x1 - h * 0.6, y_base - h + 1.2), hexc('#c9d5e3'))


def _bb(pts):
    xs, ys = [p[0] for p in pts], [p[1] for p in pts]
    return min(xs), min(ys), max(xs), max(ys)


def building(L, b, rng):
    """Paint one building described by the dict `b`.

    keys: x, w, h (front face), base_y, material, floors, bays, roof ('parapet' | 'mansard' |
    'pitched' | 'gable' | 'flat'), roof_h, side (side face width; + right, - left), arch,
    window_scale, chimneys, cornice, ground (ground-floor height), lit."""
    x, w, h, yb = b['x'], b['w'], b['h'], b['base_y']
    mat = MATERIALS.get(b.get('material', 'brick'), b.get('material', 'brick'))
    yt = yb - h
    seed = int(rng.integers(0, 1 << 30))
    side = b.get('side', 0)
    # the side face, seen toward the vanishing point: its top edge slopes toward eye level
    if side:
        if side > 0:
            sx0, sx1 = x + w, x + w + side
            drop = (world.HORIZON - yt) * side / max(abs(world.VP_X - (x + w)), 300)
            pts = [(sx0, yt), (sx1, yt + drop), (sx1, yb), (sx0, yb)]
            which = 'left' if (x + w) < world.VP_X else 'left'
            which = 'right'
        else:
            sx0, sx1 = x + side, x
            drop = (world.HORIZON - yt) * (-side) / max(abs(world.VP_X - x), 300)
            pts = [(sx0, yt + drop), (sx1, yt), (sx1, yb), (sx0, yb)]
            which = 'left'
        sh = Shape(*_bb(pts)).poly(pts)
        L.paint(sh, surface(mat, which, yt, yb, seed + 1))
        # a few foreshortened windows on the side
        floors = b.get('floors', 4)
        fh = (h - b.get('ground', 0)) / floors
        sw = abs(side)
        if sw > 10:
            for f in range(floors):
                wy = yt + fh * f + fh * 0.28 + (drop if side > 0 else drop) * 0.15
                wx = (sx0 + sw * 0.3) if side > 0 else (sx0 + sw * 0.25)
                window_row(L, [wx], wy, sw * 0.38, fh * 0.48, wall=mat, which=which, rng=rng, bars=False)
    # the front face
    front = Shape(x, yt, x + w, yb).rect(x, yt, x + w, yb)
    L.paint(front, surface(mat, 'front', yt, yb, seed))
    ground = b.get('ground', 0)
    if b.get('pilasters'):
        nb = b.get('bays', max(2, int(w / 34)))
        pilasters(L, [x + w * i / nb for i in range(1, nb)], yt + 2, yb - ground, max(3.0, w / nb * 0.12), mat)
    if b.get('quoins'):
        qw = max(5.0, w * 0.045)
        quoins(L, x, yt, yb - ground, qw, mat, 'left')
        quoins(L, x + w, yt, yb - ground, qw, mat, 'right')
    if ground:
        gcol = b.get('ground_material', 'stone')
        L.paint(Shape(x, yb - ground, x + w, yb).rect(x, yb - ground, x + w, yb), surface(MATERIALS.get(gcol, gcol), 'front', yb - ground, yb, seed + 2))
        if b.get('rusticated', True):
            rustication(L, x, x + w, yb - ground, yb, max(5.0, ground / 7))
        soft_shadow(L, x, yb - ground, x + w, yb - ground + 5, 0.3)
    # windows, floor by floor
    floors = b.get('floors', 4)
    bays = b.get('bays', max(2, int(w / 34)))
    fh = (h - ground - b.get('attic', 0)) / floors
    ws = b.get('window_scale', 1.0)
    bw = w / bays
    win_w = bw * 0.46 * ws
    for f in range(floors):
        top = yt + b.get('attic', 0) + fh * f
        win_h = fh * (0.56 if f > 0 else 0.62) * ws
        wy = top + (fh - win_h) * 0.45
        xs = [x + bw * (i + 0.5) - win_w / 2 for i in range(bays)]
        window_row(L, xs, wy, win_w, win_h, frame=b.get('frame', '#f4efe4'), wall=mat, arch=b.get('arch', False) and f == floors - 1, rng=rng, lit=b.get('lit', 0.05))
        if b.get('lintels', False) and not (b.get('arch', False) and f == floors - 1):
            lintels(L, xs, wy, win_w, win_h, mat)
        if b.get('pediments') and f == b.get('pediment_floor', 1):
            pediments(L, xs, wy - 1, win_w, win_h, mat, b['pediments'])
        if b.get('balcony') == f:
            balcony(L, x + bw * 0.25, x + w - bw * 0.25, wy + win_h + 1, win_h * 0.32)
        if b.get('string', False) and f < floors - 1:
            soft_shadow(L, x, top + fh - 1, x + w, top + fh + 2.5, 0.18)
            L.paint(Shape(x, top + fh - 3, x + w, top + fh).rect(x, top + fh - 2.2, x + w, top + fh - 0.6), np.clip(face(mat, 'front') * 1.12, 0, 1))
    if ground:
        gx = [x + bw * (i + 0.5) - bw * 0.35 for i in range(bays)]
        window_row(L, gx, yb - ground * 0.82, bw * 0.7, ground * 0.7, frame='#2b3440', wall=MATERIALS.get(b.get('ground_material', 'stone'), '#e6cf9f'), arch=b.get('ground_arch', False), rng=rng, lit=0.1, bars=False, sill=False)
    # roofline
    roof = b.get('roof', 'parapet')
    if b.get('cornice', True):
        cornice(L, x, x + w, yt, max(3.0, h * 0.022), mat)
    if roof == 'parapet':
        ph = max(5, h * 0.035)
        L.paint(Shape(x, yt - ph, x + w, yt).rect(x - 1, yt - ph, x + w + 1, yt), face(mat, 'front'))
        L.paint(Shape(x, yt - ph - 2, x + w, yt - ph + 2).rect(x - 2, yt - ph - 1.5, x + w + 2, yt - ph + 0.6), np.clip(face(mat, 'top') * 1.12, 0, 1))
    elif roof == 'mansard':
        mansard(L, x, x + w, yt - 1, b.get('roof_h', h * 0.2), rng, dormers=b.get('dormers', max(2, int(w / 60))))
    elif roof == 'pitched':
        pitched(L, x, x + w, yt - 1, b.get('roof_h', h * 0.16))
    elif roof == 'gable':
        gh = b.get('roof_h', w * 0.4)
        pts = [(x - 2, yt), (x + w / 2, yt - gh), (x + w + 2, yt)]
        L.paint(Shape(*_bb(pts)).poly(pts), surface(mat, 'front', yt - gh, yt, seed + 3))
        coping = [(x - 4, yt + 1), (x + w / 2, yt - gh - 3), (x + w + 4, yt + 1)]
        L.paint(Shape(*_bb(coping)).stroke(coping, max(2.5, w * 0.02)), np.clip(face(mat, 'top') * 1.1, 0, 1))
        window_row(L, [x + w / 2 - w * 0.07], yt - gh * 0.55, w * 0.14, gh * 0.4, wall=mat, arch=True, rng=rng)
    for k in range(b.get('chimneys', 0)):
        cw = max(10, w * 0.09)
        cx = x + w * (0.12 + 0.76 * k / max(b.get('chimneys', 1) - 1, 1)) - cw / 2
        chimney(L, cx, yt - (b.get('roof_h', 0) * 0.5 if roof in ('mansard', 'pitched') else 0), cw, max(18, h * 0.12), b.get('chimney_material', MATERIALS['brick']), rng=rng)
    # a little shade at the foot of the wall
    soft_shadow(L, x, yb - h * 0.05, x + w, yb, 0.22)
