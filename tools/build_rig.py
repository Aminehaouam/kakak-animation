"""Build the Rev2D rig of the parrot: parrot/parrot.r2d.json.

The layer images come from make_layers.py (parrot/textures/layers.json says where each one sits).
This script writes the rest of the model: parameters, the body lattice and its deformation fields,
the nested wing / tail / mandible lattices, the image parts, the mouth interior and the eye opening
(vector), bindings, physics and animations (animations.py).

Landmarks are written in SOURCE px of source/parrot.jpg and shifted into model px with S().
Angles are degrees, clockwise-positive on screen (+y is down), as everywhere in Rev2D.

usage: python3 tools/build_rig.py
"""
import json
import math
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from animations import animations  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL = os.path.join(ROOT, 'parrot', 'parrot.r2d.json')
LAYERS = json.load(open(os.path.join(ROOT, 'parrot', 'textures', 'layers.json')))
OX, OY = LAYERS['offset']
W, H = LAYERS['canvas']


def S(x, y):
    """Source px -> model px."""
    return (x + OX, y + OY)


# --------------------------------------------------------------------------- landmarks (source px)

NECK = [(0, 197), (60, 197), (80, 199), (100, 197), (120, 195), (140, 189), (160, 186), (300, 186)]
NECK_BAND = 16          # px below the neck line over which head motion fades out
HEAD_REACH = (105, 145)  # head motion fades out this far from HEAD_CENTER (only the background)
HEAD_CENTER = (104, 136)
NECK_PIVOT = (104, 192)  # head tilt and nod
YAW = dict(cx=108.0, rx=76.0, cy=138.0, ry=62.0, beak_u=0.38)  # head-turn cylinder; the beak
#                                                                rides on the face at u = 0.38
KNEE_Y, FEET_Y = 322, 347  # the body moves as a whole above KNEE_Y; the toes stay planted
BODY_CX = 110
CHEST = dict(cx=112, cy=262, rx=58, ry=72)
SHOULDER = (104, 217)    # wing pivot
TAIL_PIVOT = (78, 311)
HINGE = (137, 149)       # lower mandible pivot, at the corner of the beak
PUPIL_C = (115.3, 137.0)

# the dark gape between the beaks, measured on the 4x picture: top edge = underside of the upper
# beak, bottom edge = top of the mandible, open on the right where the mandible tip ends
GAPE_TOP = [(136.4, 144.3), (138, 145.25), (140, 146.75), (142, 148.25), (144, 149.5),
            (146, 150.25), (148, 151.0), (150, 151.75), (152, 152.0), (154, 152.25),
            (156, 152.0), (158, 151.75), (160, 152.5)]
GAPE_BOTTOM = [(137, 145.75), (138, 147.25), (140, 150.25), (142, 152.5), (144, 154.75),
               (146, 156.75), (148, 158.5), (150, 160.25), (152, 162.0), (154, 163.5),
               (156, 164.5), (158, 165.25), (160, 166.0), (162, 166.25), (164, 166.5),
               (166, 166.5), (168.3, 166.9)]
# underside of the hook, from the end of the gape to the hook tip: as drawn, the dark inside ends on a
# line from the start of the hook to the mandible tip (you see through under the hook); a beak opened
# wider shows the dark inside up to the hook tip
HOOK = [(162.5, 151.0), (165.5, 151.3), (168.5, 153.0), (171.5, 155.5), (174.5, 159.0), (177.5, 162.1)]
MANDIBLE_ANGLE = {0.0: -15.0, 0.15: -7.5, 0.3: 0.0, 0.65: 12.0, 1.0: 24.0}  # MouthOpen -> degrees
HOOK_SPREAD = {0.0: 0.0, 0.15: 0.0, 0.3: 0.0, 0.65: 0.7, 1.0: 1.0}

# --------------------------------------------------------------------------- helpers


def smoothstep(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0), 0.0, 1.0)
    return t * t * (3 - 2 * t)


def rotation(px, py, cx, cy, deg):
    """Offsets that rotate the points (px, py) about (cx, cy) by deg."""
    a = math.radians(deg)
    c, s = math.cos(a), math.sin(a)
    dx, dy = px - cx, py - cy
    return cx + c * dx - s * dy - px, cy + s * dx + c * dy - py


def r3(v):
    return float(round(float(v), 3))


class Lattice:
    """A warp's rest lattice (model px) with the same points in source px."""

    def __init__(self, wid, rect, cols, rows, parent=None, description=None):
        self.id, self.rect, self.cols, self.rows = wid, rect, cols, rows
        self.parent, self.description = parent, description
        x, y, w, h = rect
        self.mx, self.my = np.meshgrid(np.linspace(x, x + w, cols + 1), np.linspace(y, y + h, rows + 1))
        self.sx, self.sy = self.mx - OX, self.my - OY

    def warp(self):
        out = {'id': self.id, 'rect': self.rect, 'cols': self.cols, 'rows': self.rows}
        if self.parent:
            out['parent'] = self.parent
        if self.description:
            out['description'] = self.description
        return out

    @staticmethod
    def offsets(dx, dy, sparse=True):
        """Offsets as a sparse map {"i": [dx, dy]} (unlisted = 0) or a full flat list."""
        dx, dy = np.ravel(dx), np.ravel(dy)
        if not sparse:
            return [r3(v) for pair in zip(dx, dy) for v in pair]
        return {str(i): [r3(a), r3(b)] for i, (a, b) in enumerate(zip(dx, dy))
                if abs(a) >= 5e-4 or abs(b) >= 5e-4}


def format_model_json(value, indent=2, width=100, precision=4):
    """Python port of Rev2D's formatModelJson (src/core/format.ts): the layout Rev2D itself writes
    (ops, the editor), so saving the model there gives a minimal diff. Objects break across lines,
    arrays of primitives stay on one line (wrapped at `width`, point pairs kept together)."""

    def num(n):
        r = round(float(n), precision)
        if r == 0:
            return '0'
        return str(int(r)) if r == int(r) else repr(r)

    def prim(v):
        if v is None:
            return 'null'
        if isinstance(v, bool):
            return 'true' if v else 'false'
        if isinstance(v, (int, float)):
            return num(v)
        if isinstance(v, str):
            return json.dumps(v, ensure_ascii=False)
        return None

    def compact(entries):
        parts = []
        for k, x in entries:
            s = prim(x)
            if s is None and isinstance(x, list) and len(x) <= 8:
                ps = [prim(q) for q in x]
                if all(q is not None for q in ps):
                    s = '[' + ', '.join(ps) + ']'
            if s is None:
                return None
            parts.append(f'{json.dumps(k, ensure_ascii=False)}: {s}')
        return '{ ' + ', '.join(parts) + ' }'

    def write(v, depth):
        p = prim(v)
        if p is not None:
            return p
        pad, end = ' ' * ((depth + 1) * indent), ' ' * (depth * indent)
        if isinstance(v, list):
            if not v:
                return '[]'
            prims = [prim(x) for x in v]
            if all(s is not None for s in prims):
                one = '[' + ', '.join(prims) + ']'
                if len(one) + depth * indent <= width:
                    return one
                numeric = all(isinstance(x, (int, float)) and not isinstance(x, bool) for x in v)
                step = 2 if len(v) % 2 == 0 and numeric else 1
                lines, line = [], ''
                for i in range(0, len(prims), step):
                    chunk = ', '.join(prims[i:i + step])
                    if line and len(pad) + len(line) + len(chunk) + 2 > width:
                        lines.append(line + ',')
                        line = chunk
                    else:
                        line = f'{line}, {chunk}' if line else chunk
                lines.append(line)
                return '[\n' + '\n'.join(pad + ln for ln in lines) + '\n' + end + ']'
            return '[\n' + ',\n'.join(pad + write(x, depth + 1) for x in v) + '\n' + end + ']'
        entries = list(v.items())
        if not entries:
            return '{}'
        c = compact(entries)
        if c is not None and len(c) + depth * indent <= width:
            return c
        body = [f'{pad}{json.dumps(k, ensure_ascii=False)}: {write(x, depth + 1)}' for k, x in entries]
        return '{\n' + ',\n'.join(body) + '\n' + end + '}'

    return write(value, 0) + '\n'


def binding(bid, target, param, keys, description):
    return {'id': bid, 'target': target, 'params': [param],
            'keys': [{'at': [at], 'value': value} for at, value in keys], 'description': description}


# --------------------------------------------------------------------------- body lattice fields

body = Lattice('bodyWarp', [0, 0, W, H], 30, 36,
               description='Root lattice over the whole canvas: one continuous mesh for head, neck, '
                           'body and legs. Head turn / tilt / nod / bob, lean, bounce, breath and hop '
                           'are additive offset fields on it; the toes stay planted.')
bx, by = body.sx, body.sy

_nx, _ny = zip(*NECK)
_neck_y = np.interp(bx, _nx, _ny)
W_HEAD = ((1 - smoothstep(_neck_y, _neck_y + NECK_BAND, by))
          * (1 - smoothstep(HEAD_REACH[0], HEAD_REACH[1],
                            np.hypot(bx - HEAD_CENTER[0], by - HEAD_CENTER[1]))))
W_BODY = 1 - smoothstep(KNEE_Y, FEET_Y, by)


def head_tilt(deg):
    dx, dy = rotation(bx, by, *NECK_PIVOT, deg)
    return dx * W_HEAD, dy * W_HEAD


def head_yaw(deg):
    """Pseudo-3D turn on a sphere: the face (eye, beak base) slides most, the silhouette least."""
    u = np.clip((bx - YAW['cx']) / YAW['rx'], -1, YAW['beak_u'])
    v = np.clip((by - YAW['cy']) / YAW['ry'], -1, 1)
    phi = np.arcsin(np.clip(0.98 * u, -1, 1))
    u2 = np.sin(np.clip(phi + math.radians(deg), -math.pi / 2, math.pi / 2)) / 0.98
    dx = (u2 - u) * YAW['rx'] * np.sqrt(np.clip(1 - 0.8 * v * v, 0, 1)) * W_HEAD
    return dx, np.zeros_like(dx)


def head_nod(deg, pitch_px):
    """Look up (deg < 0: the beak rises) with the face sliding up by pitch_px (< 0 = up)."""
    dx, dy = rotation(bx, by, *NECK_PIVOT, deg)
    u = np.clip((bx - YAW['cx']) / YAW['rx'], -1, 1)
    v = np.clip((by - YAW['cy']) / YAW['ry'], -1, 1)
    slide = pitch_px * np.clip(1 - v * v, 0, 1) * np.sqrt(np.clip(1 - 0.6 * u * u, 0, 1))
    return dx * W_HEAD, (dy + slide) * W_HEAD


def head_shift(px, py):
    return px * W_HEAD, py * W_HEAD


def lean(deg):
    dx, dy = rotation(bx, by, BODY_CX, FEET_Y, deg)
    return dx * W_BODY, dy * W_BODY


def bounce(b):
    """b > 0: crouch (body drops and squashes, legs bend), b < 0: stretch up."""
    drop, squash, widen = (7 * b, 0.035 * b, 0.02 * b) if b > 0 else (4 * b, 0.03 * b, 0.012 * b)
    dy_body = drop + squash * np.clip(KNEE_Y - by, 0, None)
    dy_neck = drop + squash * (KNEE_Y - NECK_PIVOT[1])
    dy = (dy_body * (1 - W_HEAD) + dy_neck * W_HEAD) * W_BODY
    dx = (bx - BODY_CX) * widen * (1 - W_HEAD) * W_BODY
    return dx, dy


def breath(b):
    e = np.hypot((bx - CHEST['cx']) / CHEST['rx'], (by - CHEST['cy']) / CHEST['ry'])
    w_torso = (1 - smoothstep(0.75, 1.25, e)) * (1 - W_HEAD)
    return (bx - CHEST['cx']) * 0.022 * b * w_torso, -1.6 * b * smoothstep(335, 235, by)


def hop(h):
    return np.zeros_like(bx), np.full_like(by, -24.0 * h)


def body_binding(bid, param, fn, ats, description):
    keys = []
    for at, args in ats:
        dx, dy = fn(*args) if args is not None else (np.zeros_like(bx), np.zeros_like(by))
        keys.append((at, Lattice.offsets(dx, dy)))
    return binding(bid, 'warp:bodyWarp.offsets', param, keys, description)


# --------------------------------------------------------------------------- nested lattices

wing = Lattice('wingWarp', [78, 165, 108, 132], 6, 8, parent='bodyWarp',
               description='The wing, raised about the shoulder by WingFlap and WingSway.')
tail = Lattice('tailWarp', [58, 256, 96, 86], 4, 3, parent='bodyWarp',
               description='The red tail, swung about its root by TailWag and TailSway.')
mandible = Lattice('mandibleWarp', [187, 105, 42, 44], 3, 3, parent='bodyWarp',
                   description='The lower mandible, opened about the corner of the beak by MouthOpen.')


def lattice_rotation(lat, pivot, deg):
    return Lattice.offsets(*rotation(lat.sx, lat.sy, *pivot, deg), sparse=False)


# --------------------------------------------------------------------------- vector parts


def fmt(pts):
    return ' '.join(f'{r3(x)} {r3(y)}' for x, y in pts)


def mouth_path(m):
    """The dark inside of the beak between the underside of the upper beak (tucked 0.8 px under it)
    and the top of the mandible, rotated with the mandible (tucked 0.8 px under it).

    On the right it ends on a line to the mandible tip. Up to the drawn opening that line starts at
    the end of the gape, as in the picture; a wider beak spreads the HOOK points along the underside
    of the hook, so the dark inside reaches the hook tip (every keyform has the same points)."""
    deg, spread = MANDIBLE_ANGLE[m], HOOK_SPREAD[m]
    top = [(x, y - 0.8) for x, y in GAPE_TOP]
    tx, ty = zip(*top)
    a = math.radians(deg)
    c, s = math.cos(a), math.sin(a)
    low = []
    for x, y in GAPE_BOTTOM:
        y += 0.8
        dx, dy = x - HINGE[0], y - HINGE[1]
        rx, ry = HINGE[0] + c * dx - s * dy, HINGE[1] + s * dx + c * dy
        ry = max(ry, float(np.interp(rx, tx, ty)) + 0.6)  # closed: a sliver under the upper beak
        low.append((rx, ry))
    start, tip = np.array(top[-1]), np.array(low[-1])
    n = len(HOOK)
    hook = [(1 - spread) * (start + (tip - start) * (i + 1) / (n + 4))
            + spread * (np.array(h) - (0, 0.8)) for i, h in enumerate(HOOK)]
    side = [hook[-1] + (tip - hook[-1]) * t for t in (0.25, 0.5, 0.75)]
    pts = [S(*p) for p in top + [tuple(p) for p in hook + side] + low[::-1]]
    return 'M ' + fmt(pts[:1]) + ' L ' + fmt(pts[1:]) + ' Z'


def eye_path(openness):
    """Mask of the pupil: an ellipse around the pupil (room for the gaze) when open, a thin curved
    sliver through the middle of the pupil when closed (the dark closed-eye line)."""
    cx, cy = PUPIL_C
    a = math.radians(-9)
    c, s = math.cos(a), math.sin(a)

    def e(x, y):
        return (cx + c * x - s * y, cy + s * x + c * y)

    rx, ry, k = 15.5, 20.5, 4 / 3
    opened = [e(-rx, 0), e(-rx, -k * ry), e(rx, -k * ry), e(rx, 0), e(rx, k * ry), e(-rx, k * ry)]
    closed = [(102.5, 139.2), (109.0, 143.4), (121.5, 142.8), (128.0, 137.6), (121.5, 145.6),
              (109.0, 146.2)]
    p = [S(o[0] * openness + q[0] * (1 - openness), o[1] * openness + q[1] * (1 - openness))
         for o, q in zip(opened, closed)]
    return (f'M {fmt(p[0:1])} C {fmt(p[1:3])} {fmt(p[3:4])} '
            f'C {fmt(p[4:6])} {fmt(p[0:1])} Z')


# --------------------------------------------------------------------------- model


def image_part(pid, parent, z, cols, rows, description, **extra):
    p = LAYERS['layers'][pid]
    part = {'id': pid, 'parent': parent,
            'shape': {'type': 'image', 'texture': pid, 'x': p['x'], 'y': p['y'], 'w': p['w'],
                      'h': p['h'], 'cols': cols, 'rows': rows},
            'z': z, 'description': description}
    part.update(extra)
    return part


def build():
    params = [
        ('AngleX', -30, 30, 0, 'Head', 'Head turn: > 0 toward the screen right (more profile)'),
        ('AngleY', -30, 30, 0, 'Head', 'Head nod: > 0 looks up (the beak rises)'),
        ('AngleZ', -30, 30, 0, 'Head', 'Head tilt about the neck, clockwise for > 0 (the curious tilt)'),
        ('HeadX', -1, 1, 0, 'Head', 'Head bob forward (> 0) and back, 8 px'),
        ('HeadY', -1, 1, 0, 'Head', 'Head bob up (> 0) and down, 6 px'),
        ('EyeOpen', 0, 1, 1, 'Eye', 'Blink: 0 = closed (the visible eye is the left one)'),
        ('EyeBallX', -1, 1, 0, 'Eye', 'Gaze toward the screen right (> 0)'),
        ('EyeBallY', -1, 1, 0, 'Eye', 'Gaze up (> 0)'),
        ('MouthOpen', 0, 1, 0.3, 'Beak', 'Lower mandible: 0 closed, 0.3 as drawn (the smile), 1 wide open'),
        ('BodyAngleX', -10, 10, 0, 'Body', 'Lean toward the screen right (> 0), about the feet'),
        ('Breath', 0, 1, 0, 'Body', 'Inhale: the chest widens, the upper body rises'),
        ('Bounce', -1, 1, 0, 'Body', 'Knee bounce: > 0 crouch and squash, < 0 stretch up'),
        ('Hop', 0, 1, 0, 'Body', 'Jump: the whole bird rises 24 px'),
        ('WingFlap', 0, 1, 0, 'Wing', 'Raise the wing about the shoulder (34 deg at 1)'),
        ('WingSway', -1, 1, 0, 'Wing', 'Physics output: the wing lags behind body motion'),
        ('TailWag', -1, 1, 0, 'Tail', 'Tail swing (> 0: the tip rises)'),
        ('TailSway', -1, 1, 0, 'Tail', 'Physics output: the tail lags behind body motion'),
    ]
    parameters = [{'id': i, 'min': lo, 'max': hi, 'default': d, 'group': g, 'description': desc}
                  for i, lo, hi, d, g, desc in params]

    textures = [{'id': name, 'path': p['file'], 'width': p['px'][0], 'height': p['px'][1]}
                for name, p in LAYERS['layers'].items()]

    warps = [body.warp(), wing.warp(), tail.warp(), mandible.warp()]

    pupil = LAYERS['layers']['pupil']
    parts = [
        image_part('tail', 'tailWarp', 10, 8, 6, 'Red tail feathers; the root under the wing and the '
                   'leg is painted in, so a swing shows no gap.'),
        image_part('base', 'bodyWarp', 20, 40, 64, 'The whole bird except the tail, wing, mandible '
                   'and pupil; the body behind the wing, the chin behind the mandible and the eye '
                   'ring behind the pupil are painted in.'),
        image_part('wing', 'wingWarp', 25, 12, 16, 'The folded wing.'),
        image_part('head', 'bodyWarp', 28, 28, 24, 'The head above the neck line again, over the '
                   'wing: a lowered head covers the top of the wing. Same lattice as base, so it '
                   'never separates from it.'),
        {'id': 'mouthInner', 'parent': 'bodyWarp',
         'shape': {'type': 'path', 'd': mouth_path(0.3), 'detail': 3}, 'fill': '#1d1c22', 'z': 30,
         'description': 'Inside of the beak; its lower edge rides on the mandible (MouthOpen).'},
        image_part('mandible', 'mandibleWarp', 32, 4, 4, 'Lower mandible.'),
        image_part('upperBeak', 'bodyWarp', 34, 8, 10, 'Upper beak with the nostril, over the '
                   'mandible so a closing beak tucks under the hook.'),
        {'id': 'eyeOpening', 'parent': 'bodyWarp', 'visible': False,
         'shape': {'type': 'path', 'd': eye_path(1.0), 'detail': 3}, 'fill': '#ffffff', 'z': 39,
         'description': 'Mask of the pupil (never drawn): the lids. Closes to a curved sliver, '
                        'which leaves the dark closed-eye line.'},
        image_part('pupil', 'bodyWarp', 40, 4, 6, 'Pupil with its highlight (a hole that shows the '
                   'eye ring); clipped by eyeOpening.', mask=['eyeOpening']),
    ]

    bindings = [
        body_binding('headTilt', 'AngleZ', head_tilt,
                     [(-30, (-18,)), (-15, (-9,)), (0, None), (15, (9,)), (30, (18,))],
                     'Head tilt about the neck pivot, 18 deg at +-30; fades out over the neck.'),
        body_binding('headTurn', 'AngleX', head_yaw, [(-30, (-7,)), (0, None), (30, (7,))],
                     'Pseudo-3D head turn: yaw 7 deg on a sphere; the beak rides on the face.'),
        body_binding('headNod', 'AngleY', head_nod, [(-30, (6, 4)), (0, None), (30, (-6, -4))],
                     'Look up / down: 6 deg about the neck plus a 4 px slide of the face.'),
        body_binding('headBobX', 'HeadX', head_shift, [(-1, (-8, 0)), (0, None), (1, (8, 0))],
                     'Head bob forward / back.'),
        body_binding('headBobY', 'HeadY', head_shift, [(-1, (0, 6)), (0, None), (1, (0, -6))],
                     'Head bob up / down.'),
        body_binding('bodyLean', 'BodyAngleX', lean, [(-10, (-3,)), (0, None), (10, (3,))],
                     'Lean of everything above the knees about the feet, 3 deg at +-10.'),
        body_binding('bodyBounce', 'Bounce', bounce, [(-1, (-1,)), (0, None), (1, (1,))],
                     'Knee bounce: crouch 7 px and squash 3.5 %, or stretch; the head rides rigidly.'),
        body_binding('bodyBreath', 'Breath', breath, [(0, None), (1, (1,))],
                     'Breathing: the chest widens 2 %, the upper body rises 1.6 px.'),
        body_binding('bodyHop', 'Hop', hop, [(0, None), (1, (1,))], 'Jump: everything rises 24 px.'),
        binding('wingFlap', 'warp:wingWarp.offsets', 'WingFlap',
                [(0, lattice_rotation(wing, SHOULDER, 0)), (0.5, lattice_rotation(wing, SHOULDER, 17)),
                 (1, lattice_rotation(wing, SHOULDER, 34))],
                'Wing raised about the shoulder (clockwise lifts the tip up and back).'),
        binding('wingSway', 'warp:wingWarp.offsets', 'WingSway',
                [(-1, lattice_rotation(wing, SHOULDER, -5)), (0, lattice_rotation(wing, SHOULDER, 0)),
                 (1, lattice_rotation(wing, SHOULDER, 5))], 'Physics lag of the wing, 5 deg.'),
        binding('tailWag', 'warp:tailWarp.offsets', 'TailWag',
                [(-1, lattice_rotation(tail, TAIL_PIVOT, -14)), (0, lattice_rotation(tail, TAIL_PIVOT, 0)),
                 (1, lattice_rotation(tail, TAIL_PIVOT, 14))], 'Tail swing about its root, 14 deg.'),
        binding('tailSway', 'warp:tailWarp.offsets', 'TailSway',
                [(-1, lattice_rotation(tail, TAIL_PIVOT, -10)), (0, lattice_rotation(tail, TAIL_PIVOT, 0)),
                 (1, lattice_rotation(tail, TAIL_PIVOT, 10))], 'Physics lag of the tail, 10 deg.'),
        binding('beakOpen', 'warp:mandibleWarp.offsets', 'MouthOpen',
                [(m, lattice_rotation(mandible, HINGE, deg)) for m, deg in MANDIBLE_ANGLE.items()],
                'Lower mandible about the corner of the beak: -15 deg closed, 24 deg wide open.'),
        binding('mouthInside', 'part:mouthInner.shape.d', 'MouthOpen',
                [(m, mouth_path(m)) for m in MANDIBLE_ANGLE],
                'Inside of the beak follows the mandible (same keyforms, so it stays glued to it).'),
        binding('eyeLids', 'part:eyeOpening.shape.d', 'EyeOpen',
                [(0, eye_path(0.0)), (1, eye_path(1.0))], 'Lids close to a curved sliver.'),
        binding('gazeX', 'part:pupil.shape.x', 'EyeBallX',
                [(-1, pupil['x'] - 3), (0, pupil['x']), (1, pupil['x'] + 3)], 'Gaze left / right, 3 px.'),
        binding('gazeY', 'part:pupil.shape.y', 'EyeBallY',
                [(-1, pupil['y'] + 3), (0, pupil['y']), (1, pupil['y'] - 2.5)], 'Gaze down / up.'),
    ]

    physics = [
        {'id': 'tail', 'inputs': [{'param': 'BodyAngleX', 'type': 'x', 'weight': 2.5},
                                  {'param': 'HeadX', 'type': 'x', 'weight': 4},
                                  {'param': 'AngleZ', 'type': 'angle', 'weight': 0.15}],
         'outputs': [{'param': 'TailSway', 'type': 'angle', 'scale': 0.07}],
         'segments': [{'length': 40, 'mass': 1}], 'damping': 0.1, 'stiffness': 30,
         'description': 'The tail lags behind leaning and head bobbing.'},
        {'id': 'wing', 'inputs': [{'param': 'BodyAngleX', 'type': 'x', 'weight': 2},
                                  {'param': 'Bounce', 'type': 'angle', 'weight': 6}],
         'outputs': [{'param': 'WingSway', 'type': 'angle', 'scale': 0.08}],
         'segments': [{'length': 50, 'mass': 1}], 'damping': 0.12, 'stiffness': 40,
         'description': 'The folded wing lags a little behind leaning and bouncing.'},
    ]

    model = {
        'format': 'rev2d', 'version': 1,
        'meta': {'name': 'parrot', 'width': W, 'height': H, 'background': '#000000', 'fps': 30,
                 'author': 'kakak-animation',
                 'description': 'An African grey parrot rigged from one illustration: head turn, '
                                'tilt, nod and bob, blink and gaze, a beak that opens, a wing that '
                                'lifts, a red tail with physics, breathing, lean, bounce and hops.'},
        'parameters': parameters,
        'textures': textures,
        'warps': warps,
        'parts': parts,
        'bindings': bindings,
        'physics': physics,
        'animations': animations(),
    }
    with open(MODEL, 'w') as f:
        f.write(format_model_json(model))
    print(f'wrote {os.path.relpath(MODEL, ROOT)}: {len(parameters)} parameters, {len(parts)} parts, '
          f'{len(bindings)} bindings, {len(model["animations"])} animations, '
          f'{os.path.getsize(MODEL) // 1024} KB')


if __name__ == '__main__':
    build()
