"""The things that move or frame the view: the bus and its wheels, river boats, people on the
promenade, and the trees and bushes of the foreground."""
import numpy as np

from buildings import face, soft_shadow
from foliage import GREENS, bush, tree
from landmarks import P, R, cylinder, hgrad, vgrad
from paint import Layer, Shape, blur, hexc, lerp, noise, smoothstep

RED_TOP, RED, RED_LOW = '#ea4337', '#d42b2a', '#9f171c'


def _round_rect_pts(x0, y0, x1, y1, r_tl, r_tr, r_br, r_bl, n=10):
    pts = []
    for (cx, cy, r, a0) in ((x0 + r_tl, y0 + r_tl, r_tl, np.pi), (x1 - r_tr, y0 + r_tr, r_tr, 1.5 * np.pi), (x1 - r_br, y1 - r_br, r_br, 0), (x0 + r_bl, y1 - r_bl, r_bl, 0.5 * np.pi)):
        for a in np.linspace(a0, a0 + np.pi / 2, n):
            pts.append((cx + np.cos(a) * r, cy + np.sin(a) * r))
    return pts


def _glass(y0, y1, dark=False):
    top, low = ('#7fa6c6', '#26384f') if not dark else ('#5c7a96', '#1b2738')

    def f(X, Y):
        t = np.clip((Y - y0) / max(y1 - y0, 1), 0, 1)[..., None]
        c = lerp(hexc(top), hexc(low), t ** 0.8)
        streak = smoothstep(0.72, 1.0, np.sin((X * 0.55 - Y) * 0.045))[..., None] * 0.22
        return np.clip(c + streak, 0, 1)
    return f


# ======================================================================== the bus

def bus():
    """A red London double-decker, side on, facing right. Wheels are separate (they turn)."""
    w, h = 660, 320
    L = Layer(w, h)
    x0, x1, y0, y1 = 12, 646, 18, 274
    body = _round_rect_pts(x0, y0, x1, y1, 30, 40, 12, 8)
    L.paint(P(body), vgrad(RED_TOP, RED_LOW, y0, y1))
    # the roof catches the sky
    L.paint(P(_round_rect_pts(x0 + 3, y0 + 2, x1 - 3, y0 + 26, 26, 34, 2, 2)), hexc('#f06b5c'), alpha=0.45, clip=True)
    # lower skirt, a little darker
    L.paint(R(x0, 238, x1, y1), hexc('#7d1216'), alpha=0.45, clip=True, mode='multiply')
    # upper deck windows
    win = Shape(x0, y0, x1, y1)
    xs = np.linspace(44, 548, 7)
    for a, b in zip(xs[:-1], xs[1:]):
        win.poly(_round_rect_pts(a + 5, 48, b - 5, 112, 7, 7, 7, 7, 6))
    win.poly(_round_rect_pts(560, 46, 630, 114, 8, 30, 8, 8, 8))  # front upper windscreen
    L.paint(win, _glass(46, 114))
    # lower deck windows, doors and windscreen
    lw = Shape(x0, y0, x1, y1)
    for a, b in ((44, 136), (146, 238), (322, 414), (424, 516)):
        lw.poly(_round_rect_pts(a, 152, b, 208, 6, 6, 6, 6, 6))
    lw.poly(_round_rect_pts(588, 146, 636, 236, 6, 14, 6, 6, 6))  # windscreen
    L.paint(lw, _glass(146, 236))
    doors = Shape(x0, y0, x1, y1)
    for a in (250, 528):
        doors.rect(a, 148, a + 54, 252)
    L.paint(doors, hexc('#2b2f38'))
    dg = Shape(x0, y0, x1, y1)
    for a in (250, 528):
        dg.rect(a + 4, 152, a + 25, 246)
        dg.rect(a + 29, 152, a + 50, 246)
    L.paint(dg, _glass(150, 246, dark=True))
    # passengers: a few heads in the windows
    heads = Shape(x0, y0, x1, y1)
    rng = np.random.default_rng(3)
    for cx in (92, 176, 262, 350, 430, 512):
        if rng.random() < 0.7:
            heads.ellipse(cx + rng.uniform(-14, 14), 96, 11, 13)
            heads.rect(cx - 17, 104, cx + 17, 114)
    for cx in (90, 190, 368, 470):
        if rng.random() < 0.6:
            heads.ellipse(cx + rng.uniform(-12, 12), 192, 10, 12)
    L.paint(heads, hexc('#1c2433'), alpha=0.55, clip=True)
    # destination display on the front, route number on the side
    L.paint(R(566, 24, 632, 42), hexc('#121317'))
    L.paint(R(572, 30, 600, 36), hexc('#ffb22e'), alpha=0.9)
    L.paint(R(604, 30, 626, 36), hexc('#ffb22e'), alpha=0.6)
    # body panel lines and a cream band between the decks
    pl = Shape(x0, y0, x1, y1)
    pl.rect(x0, 126, x1, 128)
    pl.rect(x0, 236, x1, 237.5)
    L.paint(pl, hexc('#7a1013'), alpha=0.6)
    L.paint(R(x0 + 2, 120, x1 - 2, 124), hexc('#f3e6cf'), alpha=0.9)
    soft_shadow(L, x0, 114, x1, 122, 0.35)
    soft_shadow(L, x0, 208, x1, 216, 0.25)
    # lights, grille, mirror
    L.paint(Shape(624, 240, 646, 262).ellipse(634, 250, 8, 7), hexc('#fff6d6'))
    L.paint(R(x0 + 2, 230, x0 + 10, 250), hexc('#ff5a3c'))
    L.paint(R(600, 252, 640, 258), hexc('#3a3d45'))
    L.paint(R(640, 112, 650, 116), hexc('#2b2f38'))
    L.paint(R(646, 112, 652, 140), hexc('#2b2f38'))
    # wheel arches (the wheels themselves are their own sprites)
    arches = Shape(x0, y0, x1, h)
    for cx in (148, 520):
        arches.ellipse(cx, 262, 44, 44)
    L.paint(arches, hexc('#1a1316'), clip=True)
    soft_shadow(L, x0, 252, x1, 270, 0.3)
    L.save('bus', anchor=(w / 2, 300), meta={'wheels': [[148 - w / 2, 262 - 300], [520 - w / 2, 262 - 300]]})


def wheel():
    S = 80
    L = Layer(S, S)
    c = S / 2
    L.paint(Shape(0, 0, S, S).ellipse(c, c, 34, 34), hgrad('#3a3c42', '#121316', c - 34, c + 34))
    L.paint(Shape(0, 0, S, S).ellipse(c, c, 30, 30), hexc('#1d1e22'))
    L.paint(Shape(0, 0, S, S).ellipse(c, c, 19, 19), hgrad('#e9ecef', '#8c939c', c - 19, c + 19))
    L.paint(Shape(0, 0, S, S).ellipse(c, c, 13, 13), hgrad('#c0262a', '#7e1418', c - 13, c + 13))
    nuts = Shape(0, 0, S, S)
    for k in range(5):
        a = 2 * np.pi * k / 5
        nuts.ellipse(c + np.cos(a) * 9, c + np.sin(a) * 9, 2.2, 2.2)
    L.paint(nuts, hexc('#f1f3f5'))
    L.paint(Shape(0, 0, S, S).ellipse(c, c, 3.4, 3.4), hexc('#2b2f38'))
    L.save('bus_wheel', anchor=(c, c), crop=False)


# ======================================================================== boats

def boat():
    """A Thames sightseeing cruiser, facing right: a white hull with a navy band and red boot
    stripe, a long glazed cabin, an open upper deck with passengers, a small flag at the stern."""
    w, h = 620, 210
    L = Layer(w, h)
    wl = 176  # waterline
    hull = [(14, 118), (560, 118), (612, 124), (586, wl), (40, wl), (18, 150)]
    L.paint(P(hull), vgrad('#ffffff', '#d7dde4', 118, wl))
    L.paint(P([(16, 146), (598, 146), (590, 160), (30, 160)]), hexc('#1f3b63'))
    L.paint(P([(34, wl - 9), (588, wl - 9), (584, wl), (40, wl)]), hexc('#c8312f'))
    soft_shadow(L, 14, 118, 612, 126, 0.25)
    # the cabin
    cab = _round_rect_pts(60, 62, 540, 120, 18, 30, 2, 2)
    L.paint(P(cab), vgrad('#ffffff', '#e1e6ec', 62, 120))
    win = Shape(60, 62, 540, 120)
    xs = np.linspace(80, 520, 12)
    for a, b in zip(xs[:-1], xs[1:]):
        win.poly(_round_rect_pts(a + 3, 74, b - 3, 106, 5, 5, 5, 5, 5))
    L.paint(win, _glass(74, 106))
    L.paint(R(60, 58, 540, 64), hexc('#1f3b63'))
    # upper deck railing and passengers
    rail = Shape(60, 20, 540, 62)
    rail.rect(70, 30, 520, 33)
    x = 72
    while x < 520:
        rail.rect(x, 30, x + 2, 58)
        x += 14
    L.paint(rail, hexc('#f4f6f8'))
    rng = np.random.default_rng(8)
    ppl = Shape(60, 0, 540, 62)
    cols = ['#d94f3d', '#2f6db0', '#f2b33d', '#3d8a5b', '#7a4fa0', '#e9e3d6']
    for k in range(9):
        px = rng.uniform(90, 500)
        c = cols[k % len(cols)]
        L.paint(Shape(px - 8, 26, px + 8, 58).rect(px - 6, 38, px + 6, 58), hexc(c))
        L.paint(Shape(px - 8, 18, px + 8, 40).ellipse(px, 32, 5.5, 6), hexc(['#f1c7a5', '#c98f68', '#8a5a3c'][k % 3]))
    # wheelhouse and flag
    L.paint(P(_round_rect_pts(470, 34, 540, 64, 8, 14, 0, 0, 6)), hexc('#f6f8fa'))
    L.paint(R(486, 42, 530, 56), _glass(42, 56))
    L.paint(R(36, 6, 39, 62), hexc('#d9dde2'))
    flag = Shape(10, 4, 40, 24)
    L.paint(flag.rect(8, 6, 36, 22), hexc('#1d3a73'))
    L.paint(Shape(8, 6, 36, 22).stroke([(8, 6), (36, 22)], 3).stroke([(8, 22), (36, 6)], 3), hexc('#ffffff'))
    L.paint(Shape(8, 6, 36, 22).rect(8, 12, 36, 16).rect(20, 6, 24, 22), hexc('#ffffff'))
    L.paint(Shape(8, 6, 36, 22).rect(8, 13, 36, 15).rect(21, 6, 23, 22), hexc('#c8102e'))
    L.save('boat', anchor=(w / 2, wl), meta={'waterline': 0})


def boat_small():
    """A small river launch for the distance."""
    w, h = 300, 110
    L = Layer(w, h)
    wl = 96
    L.paint(P([(8, 60), (270, 60), (292, 66), (276, wl), (26, wl)]), vgrad('#2c4f7c', '#1b3456', 60, wl))
    L.paint(P([(10, 60), (272, 60), (276, 68), (14, 68)]), hexc('#f2f4f6'))
    L.paint(P(_round_rect_pts(60, 26, 210, 62, 10, 14, 0, 0, 6)), hexc('#f5f6f8'))
    L.paint(R(76, 34, 196, 50), _glass(34, 50))
    L.paint(R(150, 6, 153, 28), hexc('#d9dde2'))
    L.save('boat_small', anchor=(w / 2, wl))


# ======================================================================== people

SKINS = ['#f1c7a5', '#e0a985', '#c58b62', '#8d5a3b', '#f5d2b8']
HAIR = ['#2a1d15', '#5a3519', '#c79a55', '#7d7d7d', '#1b1b1f']
COATS = ['#2f6db0', '#d94f3d', '#f2b33d', '#3d8a5b', '#7a4fa0', '#e9e3d6', '#2b2f36', '#e07b4c', '#5aa7c9']
TROUSERS = ['#2b2f36', '#3e4f6a', '#6b5a48', '#1f3b63', '#8a8f99']


def person(name, seed, pose='stand', bag=None, skirt=False, child=False):
    """A small figure on the promenade (about 110 px tall), lit from the left."""
    rng = np.random.default_rng(seed)
    s = 0.62 if child else 1.0
    w, h = 70, 124
    L = Layer(w, h)
    cx, feet = w / 2, h - 4
    skin = SKINS[rng.integers(0, len(SKINS))]
    hair = HAIR[rng.integers(0, len(HAIR))]
    coat = COATS[rng.integers(0, len(COATS))]
    legs = TROUSERS[rng.integers(0, len(TROUSERS))]
    H_ = 112 * s
    hip = feet - H_ * 0.47
    sh_ = feet - H_ * 0.8
    stride = 7 * s if pose == 'walk' else 2.2 * s
    # legs
    for dx, lean in ((-1, -stride), (1, stride)):
        x_hip = cx + dx * 4.5 * s
        L.paint(P([(x_hip - 4.2 * s, hip), (x_hip + 4.2 * s, hip), (x_hip + lean + 3.4 * s, feet - 3), (x_hip + lean - 3.4 * s, feet - 3)]), face(legs, 'front' if dx < 0 else 'right'))
        L.paint(Shape(0, 0, w, h).ellipse(x_hip + lean + 1.5 * s, feet - 2.5, 5.5 * s, 3), hexc('#1d1f24'))
    # body: coat or skirt
    torso = [(cx - 11 * s, sh_), (cx + 11 * s, sh_), (cx + 12.5 * s, hip + (12 * s if skirt else 4 * s)), (cx - 12.5 * s, hip + (12 * s if skirt else 4 * s))]
    L.paint(P(torso), hgrad(np.clip(hexc(coat) * 1.08, 0, 1), hexc(coat) * 0.7, cx - 12 * s, cx + 12 * s))
    # arms
    for dx in (-1, 1):
        ax = cx + dx * 12 * s
        swing = (-dx * stride * 0.8) if pose == 'walk' else 0
        L.paint(Shape(0, 0, w, h).stroke([(ax, sh_ + 3 * s), (ax + dx * 2 * s + swing, hip + 6 * s)], 6.4 * s), face(coat, 'front' if dx < 0 else 'right'))
        L.paint(Shape(0, 0, w, h).ellipse(ax + dx * 2 * s + swing, hip + 8 * s, 3 * s, 3.4 * s), hexc(skin))
    if bag == 'shoulder':
        L.paint(Shape(0, 0, w, h).rect(cx + 10 * s, hip - 6 * s, cx + 20 * s, hip + 8 * s), hexc('#7a4a2a'))
        L.paint(Shape(0, 0, w, h).stroke([(cx - 8 * s, sh_ + 2), (cx + 15 * s, hip - 6 * s)], 1.6), hexc('#5a3519'))
    elif bag == 'backpack':
        L.paint(Shape(0, 0, w, h).poly(_round_rect_pts(cx - 16 * s, sh_ + 4 * s, cx - 6 * s, hip, 3, 3, 3, 3, 4)), hexc('#3d8a5b'))
    elif bag == 'shopping':
        L.paint(Shape(0, 0, w, h).rect(cx - 22 * s, hip + 4 * s, cx - 11 * s, hip + 18 * s), hexc('#e9e3d6'))
    # neck, head and hair
    L.paint(R(cx - 2.6 * s, sh_ - 6 * s, cx + 2.6 * s, sh_ + 1), hexc(skin))
    hy = sh_ - 14 * s
    L.paint(Shape(0, 0, w, h).ellipse(cx, hy, 8 * s, 9.4 * s), hgrad(np.clip(hexc(skin) * 1.05, 0, 1), hexc(skin) * 0.78, cx - 8 * s, cx + 8 * s))
    hair_pts = [(cx - 8.6 * s, hy + 1)] + [(cx - np.cos(a) * 8.8 * s, hy - np.sin(a) * 10 * s) for a in np.linspace(0, np.pi, 14)] + [(cx + 8.6 * s, hy + 1), (cx + 3 * s, hy - 4 * s), (cx - 4 * s, hy - 3 * s)]
    L.paint(P(hair_pts), hexc(hair))
    if rng.random() < 0.35:  # a cap or a hat
        L.paint(Shape(0, 0, w, h).ellipse(cx, hy - 6 * s, 9.5 * s, 4.5 * s), hexc(COATS[rng.integers(0, len(COATS))]))
    L.save(name, anchor=(cx, feet))


def people():
    specs = [('person_1', 3, 'walk', 'shoulder', False, False), ('person_2', 7, 'stand', None, True, False),
             ('person_3', 11, 'walk', 'backpack', False, False), ('person_4', 19, 'stand', 'shopping', False, False),
             ('person_5', 23, 'walk', None, True, False), ('person_6', 29, 'stand', None, False, True),
             ('person_7', 31, 'walk', None, False, False), ('person_8', 37, 'stand', 'backpack', False, False)]
    for name, seed, pose, bag, skirt, child in specs:
        person(name, seed, pose, bag, skirt, child)


# ======================================================================== trees and bushes

def greenery():
    for name, (w, h, seed) in {'tree_prom_1': (440, 560, 5), 'tree_prom_2': (400, 520, 13)}.items():
        T, base = tree(w, h, seed, leaf=6.5)
        T.save(name, anchor=base)
    for name, (w, h, seed) in {'bush_1': (760, 340, 4), 'bush_2': (560, 260, 9), 'bush_3': (420, 200, 15)}.items():
        B, base = bush(w, h, seed, leaf=7.5)
        B.save(name, anchor=base)


def union_flag():
    """The Union flag, flat; PixiJS makes it wave. Anchor: top of the hoist."""
    w, h = 160, 80
    L = Layer(w, h)
    L.paint(R(0, 0, w, h), hexc('#14317a'))
    diag = Shape(0, 0, w, h).stroke([(0, 0), (w, h)], h * 0.2, cap='flat').stroke([(0, h), (w, 0)], h * 0.2, cap='flat')
    L.paint(diag, hexc('#ffffff'))
    red = Shape(0, 0, w, h)
    red.stroke([(0, 0 + h * 0.04), (w / 2, h / 2 + h * 0.04)], h * 0.066, cap='flat').stroke([(w / 2, h / 2 - h * 0.04), (w, h - h * 0.04)], h * 0.066, cap='flat')
    red.stroke([(0, h - h * 0.04), (w / 2, h / 2 - h * 0.04)], h * 0.066, cap='flat').stroke([(w / 2, h / 2 + h * 0.04), (w, 0 + h * 0.04)], h * 0.066, cap='flat')
    L.paint(red, hexc('#c8102e'))
    L.paint(R(0, h * 0.333, w, h * 0.667), hexc('#ffffff'))
    L.paint(R(w / 2 - h * 0.167, 0, w / 2 + h * 0.167, h), hexc('#ffffff'))
    L.paint(R(0, h * 0.4, w, h * 0.6), hexc('#c8102e'))
    L.paint(R(w / 2 - h * 0.1, 0, w / 2 + h * 0.1, h), hexc('#c8102e'))
    L.save('flag_union', anchor=(0, 0), crop=False)


def all_props():
    bus()
    wheel()
    boat()
    boat_small()
    people()
    greenery()
    union_flag()
