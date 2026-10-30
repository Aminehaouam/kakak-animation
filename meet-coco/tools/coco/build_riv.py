"""Build coco.riv: Coco as a Rive cut-out character with a state machine.

The layers come from cut_layers.py. The file holds one artboard, "Coco" (360 x 400, the feet at
(180, 372)), pivot nodes for every moving part, the layer images, eight animations and the
state machine "Coco":

  inputs   flying (bool)   takes off when set, lands when cleared
           perched (bool)  the calmer perched idle instead of standing
           look (trigger)  looks around once
           excite (trigger) a happy hop, wing flutter and squawk
  layer 1  Idle <-> Perch, Look, Excited, TakeOff -> Fly -> Land
  layer 2  Blink (runs on its own, only keys the eyelid)

Every body animation keys every animated property (rest values where it does not move), so
any transition lands on a complete pose: Rive leaves unkeyed properties where they were.

usage: python3 tools/coco/build_riv.py [out.riv]
"""
import io
import json
import math
import os
import sys

from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from riv import (DURATION_IS_PERCENT, ENABLE_EXIT_TIME, EXIT_TIME_IS_PERCENT, LOOP, ONE_SHOT,  # noqa: E402
                 OP_EQ, OP_NE, PROP, RivWriter)

HERE = os.path.dirname(os.path.abspath(__file__))
LAYERS = json.load(open(os.path.join(HERE, 'layers', 'layers.json')))
# The layers are cut at 4 texels per drawing px; the file embeds them at 2, which is plenty for
# Coco at any size the story shows him (at most ~650 device px tall) and a quarter of the bytes.
TEXELS = 2
TEX = 1.0 / TEXELS
DEFAULT_OUT = os.path.join(HERE, '..', '..', 'public', 'coco.riv')
MANIFEST = os.path.join(HERE, '..', '..', 'src', 'components', 'coco', 'rig.json')

ARTBOARD = (360, 400)
FEET = (108, 360)                    # drawing px of the feet, placed at ARTBOARD_FEET
ARTBOARD_FEET = (180, 372)
FPS = 60

# pivots in drawing px, parent first. The torso turns about the hips and the legs hang from the
# root, so the feet stay planted while the body sways.
PIVOTS = {
    'root': (None, FEET),
    'legsPivot': ('root', (102, 318)),
    'torso': ('root', (106, 314)),
    'tailPivot': ('torso', (78, 311)),
    'wingFarPivot': ('torso', (116, 209)),
    'wingNearPivot': ('torso', (104, 217)),
    'wingOpenPivot': ('wingNearPivot', (104, 217)),
    'neck': ('torso', (104, 192)),
    'mandiblePivot': ('neck', (137, 149)),
    'pupilPivot': ('neck', (115.3, 137.0)),
    'lid': ('pupilPivot', (115.3, 146.0)),
}
# images front to back (Rive draws the first one on top), with the node that carries them.
# Wing art is in the wing's own frame (shoulder at 0, 0); other layers are placed in the drawing.
IMAGES = [
    ('wingOpen', 'wingOpenPivot', 'local'),
    ('pupil', 'lid', 'drawing'),
    ('upperBeak', 'neck', 'drawing'),
    ('mandible', 'mandiblePivot', 'drawing'),
    ('mouthInner', 'mandiblePivot', 'drawing'),
    ('head', 'neck', 'drawing'),
    ('wingFolded', 'wingNearPivot', 'drawing'),
    ('body', 'torso', 'drawing'),
    ('legs', 'legsPivot', 'drawing'),
    ('wingFar', 'wingFarPivot', 'local'),
    ('tail', 'tailPivot', 'drawing'),
]

# Wing poses (rotation in degrees, then scaleX, scaleY). The open wing is painted pointing up;
# a negative scaleY mirrors it below the shoulder, so a wingbeat is a flip of scaleY. FOLD lays it
# over the drawn folded wing, where the two swap without a visible jump.
FOLD = (4, 0.72, -1.0)
UP = (-30, 1.25, 1.25)
DOWN = (-38, 1.2, -1.05)
FAR_FOLD = (0, 0.7, -0.9)
FAR_UP = (-16, 1.1, 1.15)
FAR_DOWN = (-30, 1.05, -0.9)
FLY_Y, FLY_X, FLY_PITCH, FLY_NECK = -30, -26, 26, -20     # lift, pitch compensation, pose

# every property the body animations move, with its rest value (degrees for rotation; x/y are
# offsets in drawing px from the setup position)
REST = {
    ('root', 'x'): 0, ('root', 'y'): 0, ('root', 'scaleX'): 1, ('root', 'scaleY'): 1,
    ('torso', 'rotation'): 0, ('torso', 'scaleX'): 1, ('torso', 'scaleY'): 1,
    ('tailPivot', 'rotation'): 0,
    ('wingFarPivot', 'rotation'): FAR_FOLD[0], ('wingFarPivot', 'scaleX'): FAR_FOLD[1],
    ('wingFarPivot', 'scaleY'): FAR_FOLD[2], ('wingFarPivot', 'opacity'): 0,
    ('legsPivot', 'rotation'): 0, ('legsPivot', 'scaleY'): 1, ('legsPivot', 'opacity'): 1,
    ('wingNearPivot', 'rotation'): 0,
    ('wingOpenPivot', 'rotation'): FOLD[0], ('wingOpenPivot', 'scaleX'): FOLD[1],
    ('wingOpenPivot', 'scaleY'): FOLD[2],
    ('wingOpen', 'opacity'): 0, ('wingFolded', 'opacity'): 1,
    ('neck', 'rotation'): 0, ('neck', 'x'): 0, ('neck', 'y'): 0,
    ('mandiblePivot', 'rotation'): 0,
    ('pupilPivot', 'x'): 0, ('pupilPivot', 'y'): 0,
}

EASES = {  # cubic-bezier control points
    'inOut': (0.42, 0.0, 0.58, 1.0),
    'out': (0.0, 0.0, 0.4, 1.0),
    'in': (0.5, 0.0, 1.0, 1.0),
    'soft': (0.37, 0.0, 0.63, 1.0),
}


# --------------------------------------------------------------------------- poses


def k(*pairs, ease='inOut'):
    """Keyframes: k((frame, value), ..., ease=...) or k((frame, value, ease), ...)."""
    return [(p[0], p[1], p[2] if len(p) > 2 else ease) for p in pairs]


def wing(node, keys):
    """Tracks for a wing pivot from [(frame, (rotation, scaleX, scaleY), ease), ...]."""
    return {(node, prop): [(f, pose[i], e) for f, pose, e in keys]
            for i, prop in enumerate(('rotation', 'scaleX', 'scaleY'))}


BEAT = 27      # frames per wingbeat: a quick downstroke (11), a slower upstroke (16)


def fly_tracks(frames):
    """The loop starts at the bottom of a downstroke (where the takeoff ends)."""
    near, far, body_y, pitch, tail, neck = [], [], [], [], [], []
    for f in range(0, frames + 1, BEAT):
        near += [(f, DOWN, 'inOut'), (f + 16, UP, 'soft')]
        far += [(f, FAR_DOWN, 'inOut'), (f + 16, FAR_UP, 'soft')]
        body_y += [(f + 1, FLY_Y - 5, 'inOut'), (f + 16, FLY_Y, 'soft')]
        pitch += [(f + 2, FLY_PITCH - 3, 'inOut'), (f + 16, FLY_PITCH, 'soft')]
        tail += [(f + 2, -2, 'inOut'), (f + 16, -6, 'soft')]
        neck += [(f + 2, FLY_NECK + 2.5, 'inOut'), (f + 16, FLY_NECK, 'soft')]
    for tr, start in ((body_y, FLY_Y - 5), (pitch, FLY_PITCH - 3), (tail, -2),
                      (neck, FLY_NECK + 2.5)):
        tr.insert(0, (0, interp_loop(tr, frames), 'inOut'))
    cut = lambda tr: [p for p in tr if p[0] <= frames]  # noqa: E731
    return {
        **wing('wingOpenPivot', cut(near)), **wing('wingFarPivot', cut(far)),
        ('wingFarPivot', 'opacity'): k((0, 1)), ('wingOpen', 'opacity'): k((0, 1)),
        ('wingFolded', 'opacity'): k((0, 0)),
        ('root', 'y'): cut(body_y), ('root', 'x'): k((0, FLY_X)),
        ('torso', 'rotation'): cut(pitch), ('tailPivot', 'rotation'): cut(tail),
        ('neck', 'rotation'): cut(neck),
        ('legsPivot', 'rotation'): k((0, 35)), ('legsPivot', 'scaleY'): k((0, 0.6)),
        ('legsPivot', 'opacity'): k((0, 0)),
    }


def interp_loop(track, frames):
    """Value at frame 0 of a looping track whose first key is a little after 0: the linear
    blend between its last key before the loop end and its first key, so the loop closes."""
    keys = [(f, v) for f, v, _ in track if f <= frames]
    (f0, v0), (f1, v1) = keys[0], keys[-1]
    span = f0 + (frames - f1)
    return v1 + (v0 - v1) * (frames - f1) / span if span else v0


ANIMATIONS = [
    # name, frames, loop, tracks
    ('idle', 240, LOOP, {
        ('torso', 'scaleY'): k((0, 1), (60, 1.012), (120, 1), (180, 1.012), (240, 1)),
        ('torso', 'scaleX'): k((0, 1), (60, 1.005), (120, 1), (180, 1.005), (240, 1)),
        ('torso', 'rotation'): k((0, 0), (90, 0.6), (200, -0.4), (240, 0), ease='soft'),
        ('neck', 'rotation'): k((0, 0), (60, -3), (100, -3.2), (165, 2.4), (240, 0), ease='soft'),
        ('neck', 'y'): k((0, 0), (60, -0.7), (120, 0), (180, -0.7), (240, 0)),
        ('tailPivot', 'rotation'): k((0, 0), (80, 1.6), (170, -1.1), (240, 0), ease='soft'),
        ('wingNearPivot', 'rotation'): k((0, 0), (60, 0.9), (120, 0), (180, 0.9), (240, 0)),
        ('pupilPivot', 'x'): k((0, 0), (136, 0), (146, 2.2), (182, 2.2), (194, 0), (240, 0)),
    }),
    ('perch', 240, LOOP, {
        ('root', 'y'): k((0, 1.5)), ('root', 'scaleY'): k((0, 0.975), (120, 0.985), (240, 0.975)),
        ('root', 'scaleX'): k((0, 1.025), (120, 1.018), (240, 1.025)),
        ('torso', 'rotation'): k((0, -0.8), (120, 0.9), (240, -0.8), ease='soft'),
        ('torso', 'scaleY'): k((0, 1), (120, 1.014), (240, 1)),
        ('neck', 'rotation'): k((0, 1.5), (90, -2), (180, 2.2), (240, 1.5), ease='soft'),
        ('neck', 'y'): k((0, 1.2)),
        ('tailPivot', 'rotation'): k((0, -1), (120, 1.5), (240, -1), ease='soft'),
        ('pupilPivot', 'x'): k((0, 0.6), (100, 0.6), (112, -1.2), (160, -1.2), (172, 0.6), (240, 0.6)),
    }),
    ('look', 168, ONE_SHOT, {
        ('neck', 'rotation'): k((0, 0, 'out'), (22, -13, 'soft'), (62, -11.5, 'inOut'),
                                (84, 9, 'soft'), (122, 8, 'inOut'), (150, 0), (168, 0)),
        ('neck', 'x'): k((0, 0), (22, 1.5), (62, 1.5), (84, -1), (122, -1), (150, 0), (168, 0)),
        ('pupilPivot', 'x'): k((0, 0, 'out'), (18, 2.6, 'soft'), (60, 2.6, 'out'), (78, -1.8, 'soft'),
                               (120, -1.8), (146, 0), (168, 0)),
        ('pupilPivot', 'y'): k((0, 0, 'out'), (18, -1.8, 'soft'), (60, -1.8, 'out'), (78, 2, 'soft'),
                               (120, 2), (146, 0), (168, 0)),
        ('torso', 'rotation'): k((0, 0), (30, -1.4), (90, 1.4), (150, 0), (168, 0), ease='soft'),
        ('tailPivot', 'rotation'): k((0, 0), (34, -2.5), (94, 2.5), (152, 0), (168, 0), ease='soft'),
    }),
    ('excited', 84, ONE_SHOT, {
        ('root', 'y'): k((0, 0, 'out'), (10, -9, 'in'), (20, 0, 'out'), (32, -7, 'in'), (42, 0), (84, 0)),
        ('root', 'scaleY'): k((0, 1), (18, 1.03), (21, 0.93, 'out'), (27, 1), (40, 1.03),
                              (43, 0.94, 'out'), (50, 1), (84, 1)),
        ('root', 'scaleX'): k((0, 1), (18, 0.98), (21, 1.05, 'out'), (27, 1), (40, 0.98),
                              (43, 1.04, 'out'), (50, 1), (84, 1)),
        ('wingNearPivot', 'rotation'): k((0, 0), (6, 24), (12, 5), (18, 24), (24, 5), (30, 24),
                                         (36, 5), (42, 18), (58, 0), (84, 0)),
        ('mandiblePivot', 'rotation'): k((0, 0, 'out'), (8, 17), (30, 12), (40, 17), (62, 0), (84, 0)),
        ('neck', 'rotation'): k((0, 0, 'out'), (10, -9), (30, -5), (40, -9), (62, 0), (84, 0)),
        ('tailPivot', 'rotation'): k((0, 0), (8, 9), (18, -7), (28, 9), (38, -7), (54, 0), (84, 0)),
        ('torso', 'rotation'): k((0, 0), (10, -2), (60, 0), (84, 0)),
    }),
    ('takeoff', 48, ONE_SHOT, {
        # crouch, swap to the open wing laid over the folded one, spread it down and back,
        # jump on a big upstroke, lift off on the first downstroke (where the fly loop starts)
        ('root', 'y'): k((0, 0), (14, 1.5, 'out'), (34, FLY_Y), (46, FLY_Y - 5), (48, FLY_Y - 5)),
        ('root', 'x'): k((0, 0), (14, 0), (34, FLY_X), (48, FLY_X)),
        ('root', 'scaleY'): k((0, 1), (10, 0.9), (17, 1.08, 'soft'), (28, 1), (48, 1)),
        ('root', 'scaleX'): k((0, 1), (10, 1.05), (17, 0.95, 'soft'), (28, 1), (48, 1)),
        ('torso', 'rotation'): k((0, 0), (10, 6), (34, FLY_PITCH), (48, FLY_PITCH - 3)),
        ('neck', 'rotation'): k((0, 0), (10, 3), (34, FLY_NECK), (48, FLY_NECK + 2.5)),
        ('neck', 'y'): k((0, 0), (10, 1.5), (20, 0), (48, 0)),
        ('wingOpen', 'opacity'): k((0, 0), (9, 0), (12, 1), (48, 1), ease='linear'),
        ('wingFolded', 'opacity'): k((0, 1), (11, 1), (14, 0), (48, 0), ease='linear'),
        ('wingFarPivot', 'opacity'): k((0, 0), (12, 0), (16, 1), (48, 1), ease='linear'),
        **wing('wingOpenPivot', [(0, FOLD, 'inOut'), (12, FOLD, 'out'), (21, DOWN, 'inOut'),
                                 (35, UP, 'inOut'), (46, DOWN, 'soft'), (48, DOWN, 'soft')]),
        **wing('wingFarPivot', [(0, FAR_FOLD, 'inOut'), (12, FAR_FOLD, 'out'),
                                (21, FAR_DOWN, 'inOut'), (35, FAR_UP, 'inOut'),
                                (46, FAR_DOWN, 'soft'), (48, FAR_DOWN, 'soft')]),
        ('legsPivot', 'rotation'): k((0, 0), (14, 0), (30, 35), (48, 35)),
        ('legsPivot', 'scaleY'): k((0, 1), (14, 1), (30, 0.6), (48, 0.6)),
        ('legsPivot', 'opacity'): k((0, 1), (18, 1), (26, 0), (48, 0), ease='linear'),
        ('tailPivot', 'rotation'): k((0, 0), (10, 4), (34, -6), (48, -2)),
    }),
    ('fly', 2 * BEAT, LOOP, fly_tracks(2 * BEAT)),
    ('land', 48, ONE_SHOT, {
        # flare upright with a braking downstroke, fold the wing back along the body (no flip),
        # reach with the feet, touch down with a squash
        ('root', 'y'): k((0, FLY_Y), (14, -8, 'in'), (20, 0, 'out'), (48, 0)),
        ('root', 'x'): k((0, FLY_X), (12, 0), (48, 0)),
        ('root', 'scaleY'): k((0, 1), (19, 1), (23, 0.9, 'out'), (30, 1.03), (38, 1), (48, 1)),
        ('root', 'scaleX'): k((0, 1), (19, 1), (23, 1.06, 'out'), (30, 0.99), (38, 1), (48, 1)),
        ('torso', 'rotation'): k((0, FLY_PITCH), (10, -6), (20, -3), (26, 3), (36, 0), (48, 0)),
        ('neck', 'rotation'): k((0, FLY_NECK), (10, 4), (24, -2), (36, 0), (48, 0)),
        **wing('wingOpenPivot', [(0, UP, 'inOut'), (10, (-50, 1.2, -1.0), 'soft'),
                                 (16, (-14, 0.95, -1.02), 'inOut'), (22, FOLD, 'inOut'),
                                 (48, FOLD, 'inOut')]),
        **wing('wingFarPivot', [(0, FAR_UP, 'inOut'), (10, FAR_DOWN, 'soft'),
                                (20, FAR_FOLD, 'inOut'), (48, FAR_FOLD, 'inOut')]),
        ('wingOpen', 'opacity'): k((0, 1), (21, 1), (24, 0), (48, 0), ease='linear'),
        ('wingFolded', 'opacity'): k((0, 0), (19, 0), (22, 1), (48, 1), ease='linear'),
        ('wingFarPivot', 'opacity'): k((0, 1), (16, 1), (21, 0), (48, 0), ease='linear'),
        ('legsPivot', 'rotation'): k((0, 35), (12, -12), (22, 0), (48, 0)),
        ('legsPivot', 'scaleY'): k((0, 0.6), (12, 1), (48, 1)),
        ('legsPivot', 'opacity'): k((0, 0), (3, 0), (8, 1), (48, 1), ease='linear'),
        ('tailPivot', 'rotation'): k((0, -6), (10, 8), (22, 3), (32, -2), (40, 0), (48, 0)),
    }),
]

BLINK = ('blink', 420, LOOP, {
    ('lid', 'scaleY'): k((0, 1), (150, 1, 'in'), (155, 0.06, 'linear'), (158, 0.06, 'out'),
                         (166, 1), (270, 1, 'in'), (274, 0.08, 'linear'), (276, 0.08, 'out'),
                         (281, 1), (287, 1, 'in'), (291, 0.08, 'linear'), (293, 0.08, 'out'),
                         (299, 1), (420, 1)),
})
# lengths in seconds, for the app (canvas-lite does not expose an animation's duration)
DURATIONS = {name: frames / FPS for name, frames, _, _ in ANIMATIONS + [BLINK]}


# --------------------------------------------------------------------------- build


def texture(path, scale):
    """The layer PNG resampled by `scale` (in premultiplied alpha, so edges don't darken)."""
    im = Image.open(path).convert('RGBA')
    if scale != 1:
        size = (max(1, round(im.width * scale)), max(1, round(im.height * scale)))
        im = im.convert('RGBa').resize(size, Image.LANCZOS).convert('RGBA')
    buf = io.BytesIO()
    im.save(buf, 'PNG', optimize=True)
    return buf.getvalue(), im.size


def build(out_path):
    w = RivWriter()
    w.add('Backboard')
    assets = {}
    for name, _, _ in IMAGES:
        p = LAYERS['layers'][name]
        data, size = texture(os.path.join(HERE, 'layers', p['file']), TEXELS / LAYERS['texelsPerPx'])
        assets[name] = w.asset('ImageAsset', data, name=name, width=size[0], height=size[1])

    w.artboard(name='Coco', width=ARTBOARD[0], height=ARTBOARD[1], originX=0, originY=0, clip=False)
    ids, setup = {}, {}
    for node, (parent, pos) in PIVOTS.items():
        if parent is None:
            local = (ARTBOARD_FEET[0] + pos[0] - FEET[0], ARTBOARD_FEET[1] + pos[1] - FEET[1])
            pid = 0
        else:
            ppos = PIVOTS[parent][1]
            local = (pos[0] - ppos[0], pos[1] - ppos[1])
            pid = ids[parent]
        opacity = REST.get((node, 'opacity'), 1)      # the far wing hides until Coco flies
        ids[node] = w.component('Node', name=node, parentId=pid, x=local[0], y=local[1],
                                opacity=opacity)
        setup[node] = {'x': local[0], 'y': local[1], 'rotation': 0, 'scaleX': 1, 'scaleY': 1,
                       'opacity': opacity}
    for name, carrier, frame in IMAGES:
        p = LAYERS['layers'][name]
        cx, cy = p['cx'], p['cy']
        if frame == 'drawing':
            cpos = PIVOTS[carrier][1]
            cx, cy = cx - cpos[0], cy - cpos[1]
        ids[name] = w.component('Image', name=name, parentId=ids[carrier], assetId=assets[name],
                                x=cx, y=cy, scaleX=TEX, scaleY=TEX,
                                opacity=REST.get((name, 'opacity'), 1))
        setup[name] = {'x': cx, 'y': cy, 'rotation': 0, 'scaleX': TEX, 'scaleY': TEX,
                       'opacity': REST.get((name, 'opacity'), 1)}
    ease_ids = {name: w.component('CubicEaseInterpolator', x1=a, y1=b, x2=c, y2=d)
                for name, (a, b, c, d) in EASES.items()}

    def value(node, prop, v):
        if prop == 'rotation':
            return math.radians(v)
        if prop in ('x', 'y'):
            return setup[node][prop] + v
        return v

    def write_animation(name, frames, loop, tracks, complete):
        w.add('LinearAnimation', name=name, fps=FPS, duration=frames, loopValue=loop)
        keys = dict(tracks)
        if complete:
            for key, rest in REST.items():
                keys.setdefault(key, [(0, rest, 'linear')])
        by_node = {}
        for (node, prop), kf in keys.items():
            by_node.setdefault(node, []).append((prop, kf))
        for node, props in by_node.items():
            w.add('KeyedObject', objectId=ids[node])
            for prop, kf in props:
                w.add('KeyedProperty', propertyKey=PROP[prop])
                for frame, v, ease in sorted(kf, key=lambda q: q[0]):
                    if frame > frames:
                        continue
                    kw = {'frame': frame, 'value': value(node, prop, v)}
                    if ease == 'hold':
                        kw['interpolationType'] = 0
                    elif ease == 'linear':
                        kw['interpolationType'] = 1
                    else:
                        kw['interpolationType'] = 2
                        kw['interpolatorId'] = ease_ids[ease]
                    w.add('KeyFrameDouble', **kw)

    for name, frames, loop, tracks in ANIMATIONS:
        write_animation(name, frames, loop, tracks, complete=True)
    write_animation(*BLINK, complete=False)
    anim_index = {a[0]: i for i, a in enumerate(ANIMATIONS + [BLINK])}

    # ---- state machine
    w.add('StateMachine', name='Coco')
    inputs = ['flying', 'perched', 'look', 'excite']
    w.add('StateMachineBool', name='flying', value=False)
    w.add('StateMachineBool', name='perched', value=False)
    w.add('StateMachineTrigger', name='look')
    w.add('StateMachineTrigger', name='excite')
    inp = {n: i for i, n in enumerate(inputs)}

    def layer(name, states, transitions):
        """states: list of animation names (after Entry, Any, Exit); transitions:
        {from: [(to, duration ms, [conditions], exit_percent or None)]} with 'entry'/'any'."""
        w.add('StateMachineLayer', name=name)
        index = {'entry': 0, 'any': 1, 'exit': 2}
        for i, s in enumerate(states):
            index[s] = 3 + i

        def emit(src):
            for to, ms, conds, exit_pct in transitions.get(src, []):
                flags = 0
                kw = {'stateToId': index[to], 'duration': ms}
                if exit_pct is not None:
                    flags |= ENABLE_EXIT_TIME | EXIT_TIME_IS_PERCENT
                    kw['exitTime'] = exit_pct
                kw['flags'] = flags
                w.add('StateTransition', **kw)
                for c in conds:
                    if c[0] == 'trigger':
                        w.add('TransitionTriggerCondition', inputId=inp[c[1]])
                    else:
                        w.add('TransitionBoolCondition', inputId=inp[c[1]],
                              opValue=OP_EQ if c[2] else OP_NE)

        w.add('EntryState')
        emit('entry')
        w.add('AnyState')
        emit('any')
        w.add('ExitState')
        for s in states:
            w.add('AnimationState', animationId=anim_index[s])
            emit(s)

    grounded = ['idle', 'perch', 'look', 'excited']
    t = {
        'entry': [('idle', 0, [], None)],
        'idle': [('takeoff', 120, [('bool', 'flying', True)], None),
                 ('perch', 450, [('bool', 'perched', True)], None),
                 ('look', 260, [('trigger', 'look')], None),
                 ('excited', 140, [('trigger', 'excite')], None)],
        'perch': [('takeoff', 120, [('bool', 'flying', True)], None),
                  ('idle', 450, [('bool', 'perched', False)], None),
                  ('look', 260, [('trigger', 'look')], None),
                  ('excited', 140, [('trigger', 'excite')], None)],
        'look': [('takeoff', 120, [('bool', 'flying', True)], None),
                 ('perch', 320, [('bool', 'perched', True)], 100),
                 ('idle', 320, [('bool', 'perched', False)], 100)],
        'excited': [('takeoff', 120, [('bool', 'flying', True)], None),
                    ('perch', 260, [('bool', 'perched', True)], 100),
                    ('idle', 260, [('bool', 'perched', False)], 100)],
        'takeoff': [('fly', 80, [], 100)],
        'fly': [('land', 140, [('bool', 'flying', False)], None)],
        'land': [('takeoff', 120, [('bool', 'flying', True)], 60),
                 ('perch', 220, [('bool', 'perched', True)], 100),
                 ('idle', 220, [('bool', 'perched', False)], 100)],
    }
    assert set(grounded) <= set(t)
    layer('Body', ['idle', 'perch', 'look', 'excited', 'takeoff', 'fly', 'land'], t)
    layer('Blink', ['blink'], {'entry': [('blink', 0, [], None)]})

    data = w.tobytes()
    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
    with open(out_path, 'wb') as f:
        f.write(data)
    # what the React component needs to know about the file
    manifest = {'artboard': 'Coco', 'stateMachine': 'Coco', 'size': ARTBOARD, 'feet': ARTBOARD_FEET,
                'inputs': inputs, 'durations': {n: round(d, 4) for n, d in DURATIONS.items()}}
    os.makedirs(os.path.dirname(MANIFEST), exist_ok=True)
    with open(MANIFEST, 'w') as f:
        json.dump(manifest, f, indent=1)
        f.write('\n')
    print(f'wrote {os.path.relpath(out_path)}: {len(data) // 1024} KB, {len(ANIMATIONS) + 1} '
          f'animations, state machine "Coco" ({", ".join(inputs)}); {os.path.relpath(MANIFEST)}')


if __name__ == '__main__':
    build(sys.argv[1] if len(sys.argv) > 1 else DEFAULT_OUT)
