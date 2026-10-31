"""The scenery around the landmarks: sky, clouds, the far skyline, the riverside row with its
trees and river wall, the water and its textures, the near balustrade, the promenade and road,
and the street lamps."""
import numpy as np

import world
from buildings import building, face, soft_shadow
from foliage import GREENS, GREENS_FAR, canopy, tree
from paint import Layer, Shape, blur, hexc, lambert, lerp, noise, ramp, smoothstep
from landmarks import P, R, cylinder, hgrad, vgrad

WIDE = world.WIDE
M = world.MARGIN


# ======================================================================== sky and clouds

def sky():
    """The sky: deep cerulean overhead, clearing to a pale, warm haze at the horizon."""
    h = 1320
    L = Layer(WIDE, h)
    yy, xx = np.mgrid[0:h, 0:WIDE].astype(np.float32)
    t = yy / h
    col = ramp([(0.0, '#2f7fcb'), (0.25, '#4b98da'), (0.5, '#7cb9e8'), (0.72, '#b2d8f1'), (0.86, '#d6ebf4'), (1.0, '#eaf2ef')], t)
    # a faint, warm brightening toward the sun (upper left) and slow painterly variation
    sun = np.exp(-(((xx - 500) / 1700) ** 2 + ((yy + 150) / 900) ** 2))
    col = lerp(col, hexc('#cfe6f5'), (sun * 0.32)[..., None])
    n = noise(h, WIDE, 420, 3, 5)
    col = np.clip(col * (1 + n[..., None] * 0.018), 0, 1)
    L.paint((np.ones((h, WIDE), np.float32), 0, 0), col)
    L.save('sky', anchor=(M, 0), crop=False, quality=94)


def cloud(name, w, h, seed, puffs=None, flat=0.3, soft=1.0, alpha_max=1.0):
    """A cumulus built from puffs, painted back to front: each puff is lit on its own (warm
    white on the upper left, soft blue-grey underneath) and shades the puffs behind it."""
    rng = np.random.default_rng(seed)
    L = Layer(w, h)
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    base_y = h - 6
    n = puffs or int(6 + w / 150)
    smooth_n = noise(h, w, h * 0.35, 2, seed + 3)
    fine_n = noise(h, w, h * 0.09, 2, seed + 4)
    items = []
    for i in range(n):
        f = (i + 0.5) / n
        mound = np.sin(np.pi * np.clip(f * 1.05 - 0.025, 0, 1)) ** 0.9
        r = h * (0.2 + 0.32 * mound) * rng.uniform(0.85, 1.12)
        px = w * (0.08 + 0.84 * f) + rng.uniform(-0.025, 0.025) * w
        py = base_y - r * rng.uniform(0.25, 0.55) - h * 0.32 * mound * rng.uniform(0.3, 0.7)
        items.append((px, py, r))
    for i in range(int(n * 0.5)):
        px = w * rng.uniform(0.3, 0.7)
        r = h * rng.uniform(0.16, 0.24)
        py = base_y - h * rng.uniform(0.5, 0.72)
        items.append((px, py, r))
    # back to front: higher puffs sit behind lower ones
    items.sort(key=lambda p: p[1])
    flat_cut = smoothstep(base_y + 1, base_y - h * 0.1, yy)
    for px, py, r in items:
        d = np.sqrt((xx - px) ** 2 + ((yy - py) * 1.06) ** 2)
        edge = r - d + smooth_n * r * 0.1 + fine_n * r * 0.03
        a = smoothstep(-r * 0.03 * soft, r * 0.05 * soft, edge) * flat_cut
        if a.max() < 0.01:
            continue
        sh = np.roll(np.roll(blur(a, r * 0.12), int(r * 0.1), 0), int(r * 0.08), 1)
        L.paint((np.clip(sh * 0.22 * (1 - a), 0, 1), 0, 0), hexc('#7d93b3'), clip=True, mode='multiply')
        u = np.clip(d / r, 0, 1)
        dome = np.sqrt(np.clip(1 - u * u, 0, None)) * r
        lit = lambert(dome + smooth_n * r * 0.08, k=1.0)
        t = np.clip(lit * 0.5 + 0.5, 0, 1)
        t = t - smoothstep(base_y - h * 0.5, base_y, yy) * 0.3
        bands = (smoothstep(0.4, 0.47, t) + smoothstep(0.62, 0.69, t) + smoothstep(0.8, 0.86, t)) / 3
        t = np.clip(lerp(t, bands, 0.3), 0, 1)
        col = ramp([(0.0, '#9bb2cf'), (0.3, '#bccce0'), (0.55, '#dde7f2'), (0.8, '#f7fafd'), (1.0, '#fffaf0')], t)
        L.paint((a * alpha_max, 0, 0), col)
    L.save(name, anchor=(w / 2, base_y))


def clouds():
    cloud('cloud_big', 1150, 400, 3)
    cloud('cloud_mid', 860, 300, 11)
    cloud('cloud_mid2', 720, 250, 17)
    cloud('cloud_small', 460, 170, 23)
    cloud('cloud_small2', 380, 140, 29)
    cloud('cloud_far', 900, 150, 37, puffs=13, soft=1.6, alpha_max=0.8)


# ======================================================================== far skyline

def far_skyline():
    """Pale towers and cranes far behind the river, softened by distance."""
    h = 700
    L = Layer(WIDE, h)
    rng = np.random.default_rng(12)
    base = h - 2
    x = 0
    while x < WIDE:
        bw = rng.uniform(46, 150)
        bh = rng.uniform(150, 420) * (1.35 if 2500 < x < 3300 else 1.0)
        c = ['#b9cee0', '#adc4d9', '#c3d5e5', '#a6bed5'][rng.integers(0, 4)]
        top = base - bh
        kind = rng.random()
        if kind < 0.12:  # a stepped tower
            L.paint(R(x, top, x + bw, base), face(c, 'front'))
            L.paint(R(x + bw * 0.2, top - bh * 0.18, x + bw * 0.8, top + 2), face(c, 'front'))
        elif kind < 0.2:  # a slim tower with a mast
            L.paint(R(x + bw * 0.25, top, x + bw * 0.75, base), face(c, 'front'))
            L.paint(R(x + bw * 0.49, top - 60, x + bw * 0.51, top), face(c, 'front'))
        else:
            L.paint(R(x, top, x + bw, base), face(c, 'front'))
        # the shaded side and a hint of floors
        L.paint(R(x + bw * 0.68, top - bh, x + bw, base), hexc('#7f97b3'), alpha=0.22, clip=True, mode='multiply')
        fl = Shape(x, top, x + bw, base)
        y = top + 8
        while y < base:
            fl.rect(x + 3, y, x + bw - 3, y + 1.2)
            y += 11
        L.paint(fl, hexc('#e8f0f6'), alpha=0.22, clip=True)
        x += bw + rng.uniform(-20, 30)
    # cranes, as London always has
    for cx, ch in ((900, 380), (1900, 420), (3350, 360)):
        cr = Shape(cx - 260, base - ch - 40, cx + 260, base)
        cr.rect(cx - 4, base - ch, cx + 4, base)
        cr.rect(cx - 230, base - ch - 4, cx + 200, base - ch + 4)
        cr.stroke([(cx, base - ch - 36), (cx - 220, base - ch)], 1.6)
        cr.stroke([(cx, base - ch - 36), (cx + 190, base - ch)], 1.6)
        cr.rect(cx - 6, base - ch - 40, cx + 6, base - ch)
        L.paint(cr, hexc('#a2bad1'))
    L.save('skyline_far', anchor=(M, base), crop=False, quality=90)


# ======================================================================== the riverside row

def riverside():
    """The far bank, district by district, from Lambeth to Shad Thames. Screen x = layer x - M."""
    h = 520
    L = Layer(WIDE, h)
    base = h - 6  # = BANK_TOP + 10 on screen
    rng = np.random.default_rng(31)
    specs = []

    def add(x, w, hgt, **kw):
        specs.append(dict(x=x + M, w=w, h=hgt, base_y=base, **kw))

    # Lambeth: brick terraces with mansards and chimneys
    x = -200
    for w_, h_, mat, roof in ((190, 250, 'brick', 'mansard'), (150, 210, 'cream', 'parapet'), (170, 270, 'brick_warm', 'gable'), (160, 230, 'stone', 'mansard')):
        add(x, w_, h_, material=mat, roof=roof, floors=int(h_ / 50), bays=max(3, int(w_ / 38)), chimneys=2, lintels=mat.startswith('brick'), quoins=mat.startswith('brick'), roof_h=44)
        x += w_
    # County Hall: a long stone block with a colonnade, beside the Eye
    add(470, 560, 210, material='stone', roof='mansard', roof_h=46, floors=4, bays=16, ground=46, pilasters=True, pediments='segment', pediment_floor=1, dormers=7)
    add(1030, 170, 190, material='brick', roof='parapet', floors=4, bays=4, lintels=True, quoins=True)
    add(1200, 160, 170, material='render_pink', roof='parapet', floors=4, bays=4, balcony=1)
    # Whitehall, low behind the palace
    x = 1360
    for w_, h_, mat in ((210, 150, 'stone'), (200, 165, 'sand'), (230, 150, 'stone'), (190, 160, 'cream')):
        add(x, w_, h_, material=mat, roof='parapet', floors=3, bays=max(4, int(w_ / 36)), string=True)
        x += w_
    # Victoria Embankment and the approach to St Paul's: stone offices
    x = 2000
    for w_, h_, mat, roof in ((180, 230, 'stone', 'mansard'), (150, 250, 'sand', 'parapet'), (170, 215, 'cream', 'mansard'), (160, 240, 'stone', 'parapet')):
        add(x, w_, h_, material=mat, roof=roof, roof_h=40, floors=int(h_ / 48), bays=max(4, int(w_ / 34)), string=True, pilasters=(mat == 'stone'), ground=40, pediments='triangle' if roof == 'parapet' else None, pediment_floor=1)
        x += w_
    # the City's edge: taller modern blocks
    x = 2660
    for w_, h_, mat in ((150, 280, 'grey'), (130, 300, 'white'), (160, 260, 'ochre')):
        add(x, w_, h_, material=mat, roof='parapet', floors=int(h_ / 40), bays=max(4, int(w_ / 26)), window_scale=1.15, cornice=False)
        x += w_
    # Shad Thames warehouses behind Tower Bridge: brick, arched windows, loading bays
    x = 3100
    for w_, h_, mat in ((200, 230, 'brick_dark'), (180, 250, 'brick'), (190, 220, 'brick_warm'), (200, 240, 'brick_dark'), (180, 210, 'brick')):
        add(x, w_, h_, material=mat, roof='pitched', roof_h=34, floors=int(h_ / 44), bays=max(3, int(w_ / 40)), arch=True, lintels=True, chimneys=1)
        x += w_
    # draw from the outside in, toward the vanishing point, so side faces sit behind neighbours
    vp = world.VP_X + M
    left = sorted([b for b in specs if b['x'] + b['w'] / 2 < vp], key=lambda b: b['x'])
    right = sorted([b for b in specs if b['x'] + b['w'] / 2 >= vp], key=lambda b: -b['x'])
    for b in left:
        b['side'] = 14 if b['h'] > 200 else 0
        building(L, b, rng)
    for b in right:
        b['side'] = -14 if b['h'] > 200 else 0
        building(L, b, rng)
    L.save('riverside', anchor=(M, base), crop=False, quality=92)


def farbank():
    """The far embankment: plane trees along the river wall, and the wall itself."""
    h = 330
    L = Layer(WIDE, h)
    wall_top = h - 30  # = BANK_TOP on screen
    rng = np.random.default_rng(44)
    zones = [(-200, 1290), (1990, 2860)]
    for z0, z1 in zones:
        x = z0 + rng.uniform(10, 60)
        while x < z1:
            tw = rng.uniform(150, 270)
            th = tw * rng.uniform(0.95, 1.4)
            T, base = tree(int(tw), int(th), int(rng.integers(0, 10000)), greens=GREENS_FAR, leaf=max(2.6, tw / 95), clumps=int(rng.integers(15, 22)), crown=rng.uniform(0.68, 0.78))
            L.over(T, int(x + M - base[0]), int(wall_top + 6 - base[1]))
            x += tw * rng.uniform(0.5, 0.9)
    # the river wall: granite, a lit coping, darker where the tide reaches
    L.paint(R(0, wall_top, WIDE, h), vgrad('#ddd5c4', '#a9a08f', wall_top, h))
    L.paint(R(0, wall_top - 3, WIDE, wall_top + 3), hexc('#f2ece0'))
    soft_shadow(L, 0, wall_top + 3, WIDE, wall_top + 9, 0.35)
    tide = Shape(0, h - 12, WIDE, h).rect(0, h - 11, WIDE, h)
    L.paint(tide, hexc('#6f6a5d'), alpha=0.45, clip=True, mode='multiply')
    joints = Shape(0, wall_top, WIDE, h)
    x = 0
    while x < WIDE:
        joints.rect(x, wall_top + 4, x + 1.2, h)
        x += 64
    joints.rect(0, wall_top + 14, WIDE, wall_top + 15)
    L.paint(joints, hexc('#5f584c'), alpha=0.25, clip=True, mode='multiply')
    L.save('farbank', anchor=(M, wall_top), crop=False, quality=92)


# ======================================================================== water

def water():
    """The river's own colour: lighter near the far bank where it mirrors the sky, deep blue
    toward us, with long, calm bands."""
    h = 430
    L = Layer(WIDE, h)
    yy, xx = np.mgrid[0:h, 0:WIDE].astype(np.float32)
    t = yy / h
    col = ramp([(0.0, '#6eaed8'), (0.12, '#4a92c8'), (0.45, '#2c79b8'), (0.8, '#1d63a1'), (1.0, '#185690')], t)
    bands = noise(h, WIDE // 8, 6, 3, 9)
    bands = np.asarray(__import__('PIL').Image.fromarray(bands, 'F').resize((WIDE, h)), np.float32)
    col = np.clip(col * (1 + bands[..., None] * 0.045), 0, 1)
    L.paint((np.ones((h, WIDE), np.float32), 0, 0), col)
    L.save('water', anchor=(M, 0), crop=False, quality=92)


def periodic_noise(size, seed, kx=1.0, ky=1.0, falloff=1.6):
    """Tileable noise from a random spectrum. kx, ky stretch it (kx < ky: long horizontal waves)."""
    rng = np.random.default_rng(seed)
    fy = np.fft.fftfreq(size)[:, None] * size
    fx = np.fft.fftfreq(size)[None, :] * size
    f = np.sqrt((fx / kx) ** 2 + (fy / ky) ** 2) + 1e-6
    amp = 1 / f ** falloff
    amp[0, 0] = 0
    spec = amp * np.exp(2j * np.pi * rng.random((size, size)))
    n = np.real(np.fft.ifft2(spec))
    n = (n - n.mean()) / (n.std() * 3)
    return np.clip(n, -1, 1).astype(np.float32)


def water_textures():
    from PIL import Image
    import os
    # displacement map: long horizontal swells in red (x) and green (y)
    S = 512
    r = periodic_noise(S, 1, kx=0.35, ky=1.4)
    g = periodic_noise(S, 2, kx=0.35, ky=1.4)
    img = np.stack([(r * 0.5 + 0.5), (g * 0.5 + 0.5), np.full_like(r, 0.5)], -1)
    Image.fromarray((img * 255).astype(np.uint8), 'RGB').save(os.path.join(os.path.dirname(__file__), '..', 'public', 'art', 'water_displace.png'))
    # ripple highlights: soft, short horizontal strokes on a tile, wrapping at the edges
    W_, H_ = 1024, 512
    rng = np.random.default_rng(5)
    a = np.zeros((H_, W_), np.float32)
    for _ in range(420):
        x, y = rng.uniform(0, W_), rng.uniform(0, H_)
        ln, th = rng.uniform(18, 110), rng.uniform(1.2, 3.2)
        sh = Shape(x - ln, y - th, x + ln, y + th).ellipse(x, y, ln / 2, th / 2)
        arr = sh.a * rng.uniform(0.35, 1.0)
        for ox in (-W_, 0, W_):
            for oy in (-H_, 0, H_):
                x0, y0 = sh.x0 + ox, sh.y0 + oy
                xs0, ys0 = max(x0, 0), max(y0, 0)
                xs1, ys1 = min(x0 + arr.shape[1], W_), min(y0 + arr.shape[0], H_)
                if xs1 > xs0 and ys1 > ys0:
                    a[ys0:ys1, xs0:xs1] = np.maximum(a[ys0:ys1, xs0:xs1], arr[ys0 - y0:ys1 - y0, xs0 - x0:xs1 - x0])
    rgba = np.dstack([np.ones_like(a), np.ones_like(a), np.ones_like(a), a])
    Image.fromarray((rgba * 255).astype(np.uint8), 'RGBA').save(os.path.join(os.path.dirname(__file__), '..', 'public', 'art', 'water_ripples.png'))


# ======================================================================== near embankment

def balustrade():
    """A Portland-stone balustrade: coping, turned balusters, plinth and pedestals."""
    h = world.PAVE_TOP - world.COPING + 4
    L = Layer(WIDE, h + 8)
    top, bot = 0, h
    stone = '#efe4c9'
    cop_h, plinth_h = 20, 15
    sf = face(stone, 'front')
    # balusters: a turned vase profile, lit from the left
    pitch, bw = 27, 17
    prof = lambda t: 0.36 + 0.22 * np.sin(np.clip(t, 0, 1) * np.pi * 1.1 + 0.25) ** 2  # half-width / bw
    x = 6
    bal = Shape(0, 0, WIDE, h)
    while x < WIDE:
        ys = np.linspace(cop_h, bot - plinth_h, 18)
        ts = (ys - cop_h) / (bot - plinth_h - cop_h)
        left = [(x + bw / 2 - prof(t) * bw, y) for t, y in zip(ts, ys)]
        right = [(x + bw / 2 + prof(t) * bw, y) for t, y in zip(ts[::-1], ys[::-1])]
        bal.poly(left + right)
        x += pitch
    L.paint(bal, cylinder('#fffaee', '#b4a27e', 0, pitch * 0.62) if False else hexc('#efe3c7'))
    # roundness: per-baluster shading through a repeating lit-to-shade ramp
    def shade(X, Y):
        u = ((X - 6) % pitch) / bw
        lit = np.clip(1.15 - u * 1.1, 0.35, 1.05)
        return np.stack([lit, lit * 0.98, lit * 0.94], -1)
    L.paint(bal, shade, clip=True, mode='multiply')
    # coping on top and plinth below
    L.paint(R(0, 0, WIDE, cop_h), vgrad(np.clip(sf * 1.12, 0, 1), sf * 0.92, 0, cop_h))
    L.paint(R(0, 0, WIDE, 4), hexc('#fffaf0'))
    soft_shadow(L, 0, cop_h, WIDE, cop_h + 7, 0.45)
    L.paint(R(0, bot - plinth_h, WIDE, bot + 6), vgrad(sf, sf * 0.82, bot - plinth_h, bot + 6))
    L.paint(R(0, bot - plinth_h, WIDE, bot - plinth_h + 2.5), np.clip(sf * 1.1, 0, 1))
    # pedestals every so often
    for px in range(120, WIDE, 520):
        L.paint(R(px - 22, -6, px + 22, bot + 6), vgrad(np.clip(sf * 1.08, 0, 1), sf * 0.84, -6, bot))
        L.paint(R(px + 12, -6, px + 22, bot + 6), face(stone, 'right'), alpha=0.75)
        L.paint(R(px - 25, -8, px + 25, -2), hexc('#fffaf0'))
    L.save('balustrade', anchor=(M, 0), crop=False, quality=92)


def promenade():
    """Paving, kerb, road and the near pavement, from the balustrade down to the frame's edge."""
    y0 = world.PAVE_TOP
    h = world.H - y0
    L = Layer(WIDE, h)
    yy, xx = np.mgrid[0:h, 0:WIDE].astype(np.float32)
    Y = yy + y0
    n = noise(h, WIDE, 40, 3, 21)
    fine = noise(h, WIDE, 4, 2, 22)
    kerb, road0, road1 = world.KERB, world.ROAD_TOP, world.ROAD_BOTTOM
    pave = ramp([(0, '#cbbd9f'), (1, '#e1d5bb')], np.clip((Y - y0) / (kerb - y0), 0, 1))
    road = ramp([(0, '#5b626d'), (1, '#4a505b')], np.clip((Y - road0) / (road1 - road0), 0, 1))
    near = ramp([(0, '#d5c8ac'), (1, '#e3d8bf')], np.clip((Y - road1) / (world.H - road1), 0, 1))
    col = np.where((Y < kerb)[..., None], pave, np.where((Y < road0)[..., None], hexc('#c8c2b6'), np.where((Y < road1 + 16)[..., None], road, near)))
    col = np.clip(col * (1 + n[..., None] * 0.025 + fine[..., None] * 0.012), 0, 1)
    L.paint((np.ones((h, WIDE), np.float32), 0, 0), col)
    # paving joints, rows getting deeper toward us
    jn = Shape(0, 0, WIDE, h)
    rows = [y0 + 2, 1680, 1712, 1746, kerb]
    for k in range(len(rows) - 1):
        ya, yb = rows[k] - y0, rows[k + 1] - y0
        jn.rect(0, ya, WIDE, ya + 1.1)
        step = 150 + k * 22
        x = (k * 61) % step
        while x < WIDE:
            jn.rect(x, ya, x + 1.1, yb)
            x += step
    for ya in (2040, 2100):
        jn.rect(0, ya - y0, WIDE, ya - y0 + 1.3)
    x = 40
    while x < WIDE:
        jn.rect(x, road1 + 16 - y0, x + 1.3, h)
        x += 260
    L.paint(jn, hexc('#7d7360'), alpha=0.35, mode='multiply')
    # the kerbs: a lit top edge and a shaded face
    L.paint(R(0, kerb - y0, WIDE, kerb - y0 + 5), hexc('#e6e2da'))
    L.paint(R(0, kerb - y0 + 5, WIDE, road0 - y0), hexc('#9e998f'))
    L.paint(R(0, road1 - y0, WIDE, road1 - y0 + 5), hexc('#e2ddd3'))
    L.paint(R(0, road1 - y0 + 5, WIDE, road1 - y0 + 16), hexc('#a9a398'))
    # road markings: double yellow lines and the dashed centre line
    for yl in (road0 + 10, road0 + 17):
        L.paint(R(0, yl - y0, WIDE, yl - y0 + 3.2), hexc('#efc548'), alpha=0.9)
    mid = (road0 + road1) / 2
    dash = Shape(0, mid - y0 - 4, WIDE, mid - y0 + 4)
    x = 30
    while x < WIDE:
        dash.rect(x, mid - y0 - 2.6, x + 110, mid - y0 + 2.6)
        x += 190
    L.paint(dash, hexc('#f1ede4'), alpha=0.92)
    # worn lanes: slightly darker where the tyres run
    for yl in (road0 + 52, mid + 48):
        band = Shape(0, yl - y0 - 18, WIDE, yl - y0 + 18).rect(0, yl - y0 - 14, WIDE, yl - y0 + 14)
        L.paint((blur(band.a, 6) * 0.18, band.x0, band.y0), hexc('#2f343c'), mode='multiply')
    # the balustrade's shade on the paving
    sh = Shape(0, 0, WIDE, 40).rect(0, 0, WIDE, 18)
    L.paint((blur(sh.a, 7) * 0.4, sh.x0, sh.y0), hexc('#5a5040'), mode='multiply')
    L.save('promenade', anchor=(M, 0), crop=False, quality=92)


def lamp():
    """A Victorian embankment lamp in cast iron: plinth, fluted column, ladder bar, lantern."""
    w, h = 110, 360
    L = Layer(w, h)
    cx, base = w / 2, h - 4
    iron_lit, iron = '#59657a', '#1f242b'
    col = cylinder(iron_lit, iron, cx - 12, cx + 12)
    # plinth
    L.paint(P([(cx - 26, base), (cx - 22, base - 34), (cx + 22, base - 34), (cx + 26, base)]), cylinder('#5f6b80', '#1a1e24', cx - 26, cx + 26))
    L.paint(R(cx - 28, base - 6, cx + 28, base), cylinder('#56627a', '#191c22', cx - 28, cx + 28))
    L.paint(R(cx - 18, base - 44, cx + 18, base - 33), cylinder('#5f6b80', '#1a1e24', cx - 18, cx + 18))
    # fluted column, tapering
    shaft = P([(cx - 11, base - 44), (cx - 7.5, base - 230), (cx + 7.5, base - 230), (cx + 11, base - 44)])
    L.paint(shaft, cylinder('#66738a', '#1b1f26', cx - 11, cx + 11))
    flutes = Shape(cx - 12, base - 232, cx + 12, base - 44)
    for k in (-6, -2, 2, 6):
        flutes.stroke([(cx + k, base - 50), (cx + k * 0.7, base - 226)], 0.9)
    L.paint(flutes, hexc('#0f1216'), alpha=0.45, clip=True)
    # collars and the ladder bar
    for yy, ww in ((base - 120, 13), (base - 232, 12)):
        L.paint(R(cx - ww, yy - 4, cx + ww, yy + 4), cylinder('#6c7891', '#1a1e24', cx - ww, cx + ww))
    bar_y = base - 248
    L.paint(R(cx - 30, bar_y - 3, cx + 30, bar_y + 3), hgrad('#4f5b70', '#1c2027', cx - 30, cx + 30))
    for bx in (cx - 30, cx + 30):
        L.paint(Shape(bx - 6, bar_y - 6, bx + 6, bar_y + 6).ellipse(bx, bar_y, 4.6, 4.6), hgrad('#7a879e', '#22272f', bx - 5, bx + 5))
    L.paint(R(cx - 6, base - 262, cx + 6, base - 232), col)
    # the lantern: glass panes in a black frame, a crown and finial
    lt, lb = base - 330, base - 262
    L.paint(P([(cx - 20, lb), (cx - 26, lt + 12), (cx + 26, lt + 12), (cx + 20, lb)]), hexc(iron))
    glass = P([(cx - 17, lb - 3), (cx - 22, lt + 15), (cx + 22, lt + 15), (cx + 17, lb - 3)])
    L.paint(glass, vgrad('#fbfbf2', '#d9e6ec', lt, lb))
    L.paint(P([(cx - 2, lb - 3), (cx - 3, lt + 15), (cx + 3, lt + 15), (cx + 2, lb - 3)]), hexc(iron))
    L.paint(P([(cx + 6, lb - 3), (cx + 9, lt + 15), (cx + 22, lt + 15), (cx + 17, lb - 3)]), hexc('#9fb2c2'), alpha=0.35, clip=True, mode='multiply')
    L.paint(P([(cx - 31, lt + 14), (cx, lt - 8), (cx + 31, lt + 14)]), hgrad('#5c687d', '#1a1e24', cx - 31, cx + 31))
    L.paint(R(cx - 31, lt + 12, cx + 31, lt + 17), hexc('#2a3038'))
    L.paint(Shape(cx - 6, lt - 24, cx + 6, lt - 6).ellipse(cx, lt - 13, 4.4, 6), hgrad('#7d8aa0', '#20252c', cx - 5, cx + 5))
    L.paint(R(cx - 1.3, lt - 26, cx + 1.3, lt - 16), hexc(iron))
    L.save('lamp', anchor=(cx, base))
