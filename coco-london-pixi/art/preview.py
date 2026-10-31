"""Flatten the scene from scene.json with plain compositing, for judging the composition."""
import json
import os
import sys

from PIL import Image

ROOT = os.path.join(os.path.dirname(__file__), '..')
scene = json.load(open(os.path.join(ROOT, 'src', 'scene', 'scene.json')))
man = json.load(open(os.path.join(ROOT, 'public', 'art', 'manifest.json')))
W, H = scene['frame']
canvas = Image.new('RGBA', (W, H), '#7fb8e6')
cache = {}
for layer in scene['layers']:
    for it in layer['items']:
        m = man[it['art']]
        if it['art'] not in cache:
            cache[it['art']] = Image.open(os.path.join(ROOT, 'public', m['file'])).convert('RGBA')
        im = cache[it['art']]
        haze = layer.get('haze', 0)
        if haze:
            fog = Image.new('RGBA', im.size, (214, 232, 244, 0))
            r, g, b, a = im.split()
            mixed = Image.blend(Image.merge('RGB', (r, g, b)), Image.new('RGB', im.size, (214, 232, 244)), haze)
            im = Image.merge('RGBA', (*mixed.split(), a))
        canvas.alpha_composite(im, (int(round(it['x'] - m['ax'])), int(round(it['y'] - m['ay']))))
        if it['art'] == 'eye_wheel':
            import math
            cap = Image.open(os.path.join(ROOT, 'public', man['eye_capsule']['file'])).convert('RGBA')
            for i in range(32):
                a = 2 * math.pi * i / 32
                x = it['x'] + math.cos(a) * 374
                y = it['y'] + math.sin(a) * 374
                canvas.alpha_composite(cap, (int(x - man['eye_capsule']['ax']), int(y - man['eye_capsule']['ay'])))
out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(__file__), '.cache', 'preview.jpg')
canvas.convert('RGB').resize((W // 2, H // 2), Image.LANCZOS).save(out, quality=90)
print(out)
