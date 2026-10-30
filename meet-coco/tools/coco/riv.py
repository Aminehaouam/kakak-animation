"""A small writer for Rive runtime files (.riv, format 7).

A .riv file is the "RIVE" fingerprint, the major / minor version, a file id and a property
table of contents, followed by a flat stream of core objects. Each object is its type key and
(property key, value) pairs ended by a 0 key. Hierarchy and references are indices:

- Component.parentId, KeyedObject.objectId and KeyFrame.interpolatorId index the artboard's
  object list (the artboard is 0; every component and keyframe interpolator after it takes the
  next index).
- Image.assetId indexes the file's assets in stream order.
- AnimationState.animationId indexes the artboard's animations; StateTransition.stateToId
  indexes the states of its layer; condition inputId indexes the state machine's inputs.

Type and property keys come from the generated headers of the open-source runtime
(github.com/rive-app/rive-runtime, include/rive/generated/*_base.hpp). Only what this project
uses is listed. Values: double = float32 LE, uint / id = LEB128, bool = 1 byte, string and
bytes = LEB128 length + data, color = uint32 LE (0xAARRGGBB).
"""
import struct

MAJOR, MINOR = 7, 0

# name -> (type key, {property: (key, wire type)})
_COMPONENT = {'name': (4, 'string'), 'parentId': (5, 'uint')}
_TRANSFORM = {**_COMPONENT, 'rotation': (15, 'double'), 'scaleX': (16, 'double'),
              'scaleY': (17, 'double'), 'opacity': (18, 'double'), 'x': (13, 'double'),
              'y': (14, 'double')}
_DRAWABLE = {**_TRANSFORM, 'blendModeValue': (23, 'uint'), 'drawableFlags': (129, 'uint')}
_PATH = {**_TRANSFORM, 'pathFlags': (128, 'uint')}

TYPES = {
    'Backboard': (23, {}),
    'ImageAsset': (105, {'name': (203, 'string'), 'assetId': (204, 'uint'),
                         'height': (207, 'double'), 'width': (208, 'double')}),
    'FileAssetContents': (106, {'bytes': (212, 'bytes')}),
    'Artboard': (1, {**_DRAWABLE, 'width': (7, 'double'), 'height': (8, 'double'),
                     'originX': (11, 'double'), 'originY': (12, 'double'), 'clip': (196, 'bool'),
                     'defaultStateMachineId': (236, 'uint')}),
    'Node': (2, _TRANSFORM),
    'Image': (100, {**_DRAWABLE, 'assetId': (206, 'uint'), 'originX': (380, 'double'),
                    'originY': (381, 'double')}),
    'Shape': (3, _DRAWABLE),
    'Ellipse': (4, {**_PATH, 'width': (20, 'double'), 'height': (21, 'double'),
                    'originX': (123, 'double'), 'originY': (124, 'double')}),
    'Rectangle': (7, {**_PATH, 'width': (20, 'double'), 'height': (21, 'double'),
                      'originX': (123, 'double'), 'originY': (124, 'double'),
                      'cornerRadiusTL': (31, 'double')}),
    'PointsPath': (16, {**_PATH, 'isClosed': (32, 'bool')}),
    'StraightVertex': (5, {**_COMPONENT, 'x': (24, 'double'), 'y': (25, 'double'),
                           'radius': (26, 'double')}),
    'CubicDetachedVertex': (6, {**_COMPONENT, 'x': (24, 'double'), 'y': (25, 'double'),
                                'inRotation': (84, 'double'), 'inDistance': (85, 'double'),
                                'outRotation': (86, 'double'), 'outDistance': (87, 'double')}),
    'Fill': (20, {**_COMPONENT, 'isVisible': (41, 'bool'), 'fillRule': (40, 'uint')}),
    'SolidColor': (18, {**_COMPONENT, 'colorValue': (37, 'color')}),
    'RadialGradient': (17, {**_COMPONENT, 'startX': (42, 'double'), 'startY': (33, 'double'),
                            'endX': (34, 'double'), 'endY': (35, 'double'),
                            'opacity': (46, 'double')}),
    'GradientStop': (19, {**_COMPONENT, 'colorValue': (38, 'color'), 'position': (39, 'double')}),
    'CubicEaseInterpolator': (28, {'x1': (63, 'double'), 'y1': (64, 'double'),
                                   'x2': (65, 'double'), 'y2': (66, 'double')}),
    'LinearAnimation': (31, {'name': (55, 'string'), 'fps': (56, 'uint'), 'duration': (57, 'uint'),
                             'speed': (58, 'double'), 'loopValue': (59, 'uint')}),
    'KeyedObject': (25, {'objectId': (51, 'uint')}),
    'KeyedProperty': (26, {'propertyKey': (53, 'uint')}),
    'KeyFrameDouble': (30, {'frame': (67, 'uint'), 'interpolationType': (68, 'uint'),
                            'interpolatorId': (69, 'uint'), 'value': (70, 'double')}),
    'StateMachine': (53, {'name': (55, 'string')}),
    'StateMachineNumber': (56, {'name': (138, 'string'), 'value': (140, 'double')}),
    'StateMachineTrigger': (58, {'name': (138, 'string')}),
    'StateMachineBool': (59, {'name': (138, 'string'), 'value': (141, 'bool')}),
    'StateMachineLayer': (57, {'name': (138, 'string')}),
    'AnyState': (62, {}),
    'EntryState': (63, {}),
    'ExitState': (64, {}),
    'AnimationState': (61, {'animationId': (149, 'uint'), 'speed': (292, 'double')}),
    'StateTransition': (65, {'stateToId': (151, 'uint'), 'flags': (152, 'uint'),
                             'duration': (158, 'uint'), 'exitTime': (160, 'uint')}),
    'TransitionTriggerCondition': (68, {'inputId': (155, 'uint')}),
    'TransitionBoolCondition': (71, {'inputId': (155, 'uint'), 'opValue': (156, 'uint')}),
    'TransitionNumberCondition': (70, {'inputId': (155, 'uint'), 'opValue': (156, 'uint'),
                                       'value': (157, 'double')}),
}

# property keys an animation can key (KeyedProperty.propertyKey)
PROP = {'x': 13, 'y': 14, 'rotation': 15, 'scaleX': 16, 'scaleY': 17, 'opacity': 18}

# StateTransition.flags
DURATION_IS_PERCENT, ENABLE_EXIT_TIME, EXIT_TIME_IS_PERCENT = 1 << 1, 1 << 2, 1 << 3
# TransitionValueCondition.opValue
OP_EQ, OP_NE, OP_LE, OP_GE, OP_LT, OP_GT = 0, 1, 2, 3, 4, 5
# LinearAnimation.loopValue
ONE_SHOT, LOOP, PING_PONG = 0, 1, 2


def _varuint(n):
    out = bytearray()
    while True:
        b = n & 0x7F
        n >>= 7
        if n:
            out.append(b | 0x80)
        else:
            out.append(b)
            return bytes(out)


def _value(kind, v):
    if kind == 'double':
        return struct.pack('<f', float(v))
    if kind == 'uint':
        return _varuint(int(v))
    if kind == 'bool':
        return b'\x01' if v else b'\x00'
    if kind == 'string':
        data = v.encode('utf-8')
        return _varuint(len(data)) + data
    if kind == 'bytes':
        return _varuint(len(v)) + bytes(v)
    if kind == 'color':
        return struct.pack('<I', int(v) & 0xFFFFFFFF)
    raise ValueError(kind)


class RivWriter:
    """Collects objects in stream order and serialises them."""

    def __init__(self):
        self.objects = []        # (type name, props)
        self.artboard_index = -1  # index in the current artboard's object list
        self.assets = 0
        self.animations = 0

    def add(self, type_name, **props):
        if type_name not in TYPES:
            raise KeyError(type_name)
        known = TYPES[type_name][1]
        for k in props:
            if k not in known:
                raise KeyError(f'{type_name}.{k}')
        self.objects.append((type_name, props))
        return type_name

    # -- helpers that return the index a later object uses to refer to this one ----------------

    def artboard(self, **props):
        self.add('Artboard', **props)
        self.artboard_index = 0
        self.animations = 0
        return 0

    def component(self, type_name, **props):
        """A component or keyframe interpolator of the current artboard: returns its index."""
        self.add(type_name, **props)
        self.artboard_index += 1
        return self.artboard_index

    def asset(self, type_name, data, **props):
        self.add(type_name, assetId=self.assets, **props)
        self.add('FileAssetContents', bytes=data)
        self.assets += 1
        return self.assets - 1

    def tobytes(self):
        out = bytearray(b'RIVE')
        out += _varuint(MAJOR) + _varuint(MINOR) + _varuint(0)
        out += _varuint(0)  # empty property table of contents: every key used here is known
        for type_name, props in self.objects:
            type_key, known = TYPES[type_name]
            out += _varuint(type_key)
            for k, v in props.items():
                key, kind = known[k]
                out += _varuint(key) + _value(kind, v)
            out += _varuint(0)
        return bytes(out)
