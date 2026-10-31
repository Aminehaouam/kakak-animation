"""Paint every asset into public/art and write public/art/manifest.json.

    python3 art/build.py            # everything
    python3 art/build.py sky eye    # only some groups
"""
import sys
import time

import paint

GROUPS = {}


def group(name):
    def wrap(f):
        GROUPS[name] = f
        return f
    return wrap


@group('sky')
def _sky():
    import scenery
    scenery.sky()
    scenery.clouds()
    scenery.far_skyline()


@group('landmarks')
def _landmarks():
    import landmarks as LM
    LM.eye_wheel()
    LM.eye_capsule()
    LM.eye_frame()
    LM.westminster(0.92)
    LM.st_pauls()
    LM.gherkin()
    LM.shard()
    LM.city_towers()
    LM.tower_bridge()


@group('river')
def _river():
    import scenery
    scenery.riverside()
    scenery.farbank()
    scenery.water()
    scenery.water_textures()


@group('street')
def _street():
    import scenery
    scenery.balustrade()
    scenery.promenade()
    scenery.lamp()


@group('props')
def _props():
    import props
    props.all_props()


@group('coco')
def _coco():
    import coco
    coco.build()


if __name__ == '__main__':
    names = sys.argv[1:] or list(GROUPS)
    for n in names:
        t = time.time()
        GROUPS[n]()
        paint.write_manifest()
        print(f'{n}: {time.time() - t:.1f}s')
