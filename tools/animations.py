"""Animations of the parrot rig.

Parameter tracks only (never the physics outputs TailSway / WingSway), so physics adds the
follow-through. Looping tracks end on their first value at t = duration, and "smooth" keys flow
through the loop seam (Rev2D closes Catmull-Rom tangents over the loop).
"""

REST_BEAK = 0.3  # MouthOpen as drawn


def track(param, keys, ease='smooth'):
    """keys: [(t, v), ...] or [(t, v, ease), ...]; a key's ease shapes the segment after it."""
    return {'target': f'param:{param}',
            'keys': [{'t': round(k[0], 4), 'v': k[1], 'ease': k[2] if len(k) > 2 else ease}
                     for k in keys]}


def blink_keys(t0, closed=0.11, hold=0.04, opening=0.13):
    """One blink starting at t0: close fast, hold, open a little slower."""
    return [(t0, 1, 'inQuad'), (t0 + closed, 0, 'linear'), (t0 + closed + hold, 0, 'outQuad'),
            (t0 + closed + hold + opening, 1, 'linear')]


def beats(times, on, off, half):
    """A value that snaps to `on` at every beat and eases back to `off` half a beat later."""
    keys = []
    for t in times:
        keys += [(t, on, 'outQuad'), (t + half, off, 'inQuad')]
    return keys


def idle():
    d = 6.0
    return {
        'id': 'idle', 'duration': d, 'loop': True,
        'description': 'Breathing, a slow lean, small head turns and tilts, a glance, a beak click '
                       'and two blinks. Seamless loop; layer talk or blink on top.',
        'tracks': [
            track('Breath', [(0, 0), (1.5, 1), (3, 0), (4.5, 1), (d, 0)]),
            track('BodyAngleX', [(0, 0), (1.5, 2.5), (3, 0), (4.5, -2), (d, 0)]),
            track('AngleZ', [(0, 0), (1.2, 5), (2.6, 4), (3.8, -4), (5, -2), (d, 0)]),
            track('AngleX', [(0, 0), (1.4, 6), (3, 2), (4.4, -6), (d, 0)]),
            track('AngleY', [(0, 0), (1.5, 4), (3, -2), (4.5, 3), (d, 0)]),
            track('EyeBallX', [(0, 0, 'linear'), (2.2, 0, 'outQuad'), (2.4, 0.6, 'linear'),
                               (3.2, 0.6, 'outQuad'), (3.4, 0, 'linear'), (d, 0)]),
            track('EyeBallY', [(0, 0, 'linear'), (2.2, 0, 'outQuad'), (2.4, 0.3, 'linear'),
                               (3.2, 0.3, 'outQuad'), (3.4, 0, 'linear'), (d, 0)]),
            track('MouthOpen', [(0, REST_BEAK, 'linear'), (3.55, REST_BEAK, 'inQuad'),
                                (3.65, 0.05, 'outQuad'), (3.8, 0.4, 'inOutSine'),
                                (3.95, REST_BEAK, 'linear'), (d, REST_BEAK)]),
            track('EyeOpen', [(0, 1, 'linear')] + blink_keys(1.9) + blink_keys(4.9)
                  + [(d, 1, 'linear')]),
        ],
    }


def blink():
    return {'id': 'blink', 'duration': 0.3, 'loop': False,
            'description': 'One blink; play it with "once" over another animation.',
            'tracks': [track('EyeOpen', blink_keys(0.0))]}


def talk():
    d = 2.0
    mouth = [(0, REST_BEAK), (0.12, 0.85), (0.26, 0.15), (0.42, 0.7), (0.55, 0.2), (0.72, 0.95),
             (0.9, 0.1), (1.05, 0.6), (1.2, 0.25), (1.38, 0.9), (1.55, 0.15), (1.72, 0.55),
             (1.86, REST_BEAK), (d, REST_BEAK)]
    return {
        'id': 'talk', 'duration': d, 'loop': True,
        'description': 'Chatter: the beak opens and closes with small nods. Keys sit around the '
                       'defaults, so it also plays as an "add" layer over idle.',
        'tracks': [
            track('MouthOpen', [(t, v, 'inOutSine') for t, v in mouth]),
            track('AngleY', [(0, 0), (0.36, 3), (0.72, -2), (1.1, 3), (1.5, -2), (d, 0)]),
            track('AngleZ', [(0, 0), (0.5, -3), (1.0, 2), (1.5, -2), (d, 0)]),
            track('HeadX', [(0, 0), (0.72, 0.25), (1.05, 0), (1.38, 0.2), (d, 0)]),
        ],
    }


def dance():
    d, half = 2.0, 0.25          # 120 bpm: a beat every 0.5 s
    on = [0.0, 0.5, 1.0, 1.5]

    def beat_track(param, down, up):
        return track(param, beats(on, down, up, half) + [(d, down, 'linear')])

    return {
        'id': 'dance', 'duration': d, 'loop': True,
        'description': 'Head-bobbing dance at 120 bpm: the head snaps forward and down on every '
                       'beat while the knees bounce, the body sways over two beats each way, the '
                       'tail wags, the wing pops on beats 2 and 4 and the beak chirps on 1 and 3.',
        'tracks': [
            beat_track('HeadX', 1.0, -0.5),
            beat_track('HeadY', -0.7, 0.5),
            beat_track('AngleY', -6, 4),
            beat_track('Bounce', 0.8, -0.3),
            track('BodyAngleX', [(0, -4), (1.0, 4), (d, -4)]),
            track('AngleZ', [(0, -7), (1.0, 7), (d, -7)]),
            track('TailWag', [(0, 0.5), (0.5, -0.2), (1.0, -0.5), (1.5, 0.2), (d, 0.5)]),
            track('WingFlap', [(0, 0, 'linear'), (0.5, 0, 'outQuad'), (0.6, 0.4, 'inOutSine'),
                               (0.85, 0, 'linear'), (1.5, 0, 'outQuad'), (1.6, 0.4, 'inOutSine'),
                               (1.85, 0, 'linear'), (d, 0)]),
            track('MouthOpen', [(0, REST_BEAK, 'outQuad'), (0.07, 0.85, 'inOutSine'),
                                (0.3, REST_BEAK, 'linear'), (1.0, REST_BEAK, 'outQuad'),
                                (1.07, 0.85, 'inOutSine'), (1.3, REST_BEAK, 'linear'),
                                (d, REST_BEAK)]),
            track('EyeOpen', [(0, 1, 'linear')] + blink_keys(1.25) + [(d, 1, 'linear')]),
        ],
    }


def curious():
    d = 4.0
    return {
        'id': 'curious', 'duration': d, 'loop': True,
        'description': 'The curious parrot: tilts its head back to look up, blinks, then tilts the '
                       'other way and leans in to peer down, double-blinks and comes back.',
        'tracks': [
            track('AngleZ', [(0, 0, 'inOutSine'), (0.45, -20, 'linear'), (1.4, -18, 'inOutSine'),
                             (1.9, 14, 'linear'), (2.9, 12, 'inOutSine'), (3.5, 0, 'linear'),
                             (d, 0)]),
            track('AngleY', [(0, 0, 'inOutSine'), (0.45, 8, 'linear'), (1.4, 8, 'inOutSine'),
                             (1.9, -6, 'linear'), (2.9, -6, 'inOutSine'), (3.5, 0, 'linear'),
                             (d, 0)]),
            track('HeadX', [(0, 0, 'linear'), (1.4, 0, 'inOutSine'), (1.9, 0.6, 'linear'),
                            (2.9, 0.6, 'inOutSine'), (3.5, 0, 'linear'), (d, 0)]),
            track('EyeBallX', [(0, 0, 'inOutSine'), (0.45, 0.5, 'linear'), (1.4, 0.5, 'inOutSine'),
                               (1.9, 0.7, 'linear'), (2.9, 0.7, 'inOutSine'), (3.5, 0, 'linear'),
                               (d, 0)]),
            track('EyeBallY', [(0, 0, 'inOutSine'), (0.45, 0.8, 'linear'), (1.4, 0.8, 'inOutSine'),
                               (1.9, -0.7, 'linear'), (2.9, -0.7, 'inOutSine'), (3.5, 0, 'linear'),
                               (d, 0)]),
            track('MouthOpen', [(0, REST_BEAK, 'inOutSine'), (0.5, 0.15, 'linear'),
                                (3.3, 0.15, 'inOutSine'), (3.8, REST_BEAK, 'linear'),
                                (d, REST_BEAK)]),
            track('Breath', [(0, 0), (1.3, 0.8), (2.6, 0.1), (d, 0)]),
            track('EyeOpen', [(0, 1, 'linear')] + blink_keys(0.95) + blink_keys(2.25, 0.08, 0.02, 0.1)
                  + blink_keys(2.55, 0.08, 0.02, 0.1) + [(d, 1, 'linear')]),
        ],
    }


def flap():
    d = 2.4
    return {
        'id': 'flap', 'duration': d, 'loop': True,
        'description': 'Excited squawk: a crouch, a hop with the wing fluttering, the beak wide '
                       'open and the head thrown back, a landing squash, then calm breathing.',
        'tracks': [
            track('Bounce', [(0, 0, 'inOutSine'), (0.2, 0.8, 'outQuad'), (0.3, -0.8, 'linear'),
                             (0.6, -0.4, 'outQuad'), (0.7, 0.8, 'inOutSine'), (0.95, 0, 'linear'),
                             (d, 0)]),
            track('Hop', [(0, 0, 'linear'), (0.25, 0, 'outQuad'), (0.45, 0.6, 'inQuad'),
                          (0.65, 0, 'linear'), (d, 0)]),
            track('WingFlap', [(0, 0, 'linear'), (0.25, 0, 'inOutSine'), (0.35, 1, 'inOutSine'),
                               (0.47, 0.25, 'inOutSine'), (0.59, 1, 'inOutSine'),
                               (0.71, 0.25, 'inOutSine'), (0.83, 1, 'inOutSine'),
                               (0.95, 0.25, 'inOutSine'), (1.07, 0.9, 'inOutSine'),
                               (1.35, 0, 'linear'), (d, 0)]),
            track('MouthOpen', [(0, REST_BEAK, 'linear'), (0.3, REST_BEAK, 'outQuad'),
                                (0.4, 1.0, 'linear'), (1.1, 0.95, 'inOutSine'),
                                (1.3, REST_BEAK, 'linear'), (d, REST_BEAK)]),
            track('AngleY', [(0, 0), (0.3, 0), (0.45, 14), (1.1, 12), (1.4, 0), (d, 0)]),
            track('BodyAngleX', [(0, 0), (0.45, -4), (1.2, -3), (1.6, 0), (d, 0)]),
            track('TailWag', [(0, 0), (0.3, 0), (0.45, 0.8), (0.7, -0.6), (0.95, 0.5),
                              (1.2, -0.3), (1.5, 0), (d, 0)]),
            track('Breath', [(0, 0), (1.5, 0), (1.95, 1), (d, 0)]),
            track('EyeOpen', [(0, 1, 'linear')] + blink_keys(1.8) + [(d, 1, 'linear')]),
        ],
    }


def animations():
    return [idle(), blink(), talk(), dance(), curious(), flap()]
