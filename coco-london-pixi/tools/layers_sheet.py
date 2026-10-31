"""A labelled sheet of the scene's layers, back to front, from renders/layers/*.png."""
import os
import sys

from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.join(os.path.dirname(__file__), '..')
LAYERS = [
    ('sky', 'Sky', 'art'), ('sunlight', 'Sun glow', 'pixi'), ('clouds-far', 'Far clouds, drifting', 'art'),
    ('clouds', 'Clouds, drifting', 'art'), ('gulls', 'Gulls, gliding', 'pixi'), ('skyline-far', 'Far skyline', 'art'),
    ('haze-far', 'Haze between depths', 'pixi'), ('landmarks-back', "St Paul's, the City, the Gherkin, the Shard", 'art'),
    ('haze-mid', 'Haze between depths', 'pixi'), ('riverside', 'Riverside buildings', 'art'),
    ('landmarks-front', 'London Eye (turning), Westminster, waving flag', 'both'), ('haze-near', 'Haze between depths', 'pixi'),
    ('farbank', 'Plane trees and river wall', 'art'), ('tower-bridge', 'Tower Bridge', 'art'),
    ('river', 'Thames: reflections, ripples, glints, boats', 'both'), ('balustrade', 'Balustrade', 'art'),
    ('promenade', 'Promenade and road', 'art'), ('cloud-shade', 'Cloud shadows on the ground', 'pixi'),
    ('street', 'Lamps, trees, people, contact shadows', 'both'), ('coco', 'Coco: rigged and animated', 'both'),
    ('traffic', 'Bus with turning wheels', 'both'), ('foreground', 'Foreground bushes', 'art'),
    ('light', 'Warm light, cool shade, vignette', 'pixi'),
]
KIND = {'art': ('PAINTED ARTWORK', (186, 120, 40)), 'pixi': ('PIXIJS RENDERING', (40, 104, 186)), 'both': ('ARTWORK + PIXIJS', (112, 82, 160))}
B = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
R = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
tw, th = 600, 338
cols = 4
pad = 26
head = 150
rows = (len(LAYERS) + 1 + cols - 1) // cols
sheet = Image.new('RGB', (cols * tw + (cols + 1) * pad, head + rows * (th + 74) + pad), (246, 244, 239))
d = ImageDraw.Draw(sheet)
d.text((pad, 30), 'Coco in London: the scene, layer by layer (back to front)', font=ImageFont.truetype(B, 40), fill=(30, 36, 48))
d.text((pad, 88), 'Every layer is shown alone at the same moment (t = 12 s). Painted layers are images made by the art scripts; PixiJS layers are drawn and animated in code.', font=ImageFont.truetype(R, 22), fill=(80, 88, 100))
cells = [('__final__', 'The finished frame', 'both')] + LAYERS
for i, (name, label, kind) in enumerate(cells):
    x = pad + (i % cols) * (tw + pad)
    y = head + (i // cols) * (th + 74)
    src = os.path.join(ROOT, 'renders', 'layers', f'{name}.png') if name != '__final__' else os.path.join(ROOT, 'renders', 'london-4k.png')
    im = Image.open(src).convert('RGB').resize((tw, th), Image.LANCZOS)
    sheet.paste(im, (x, y))
    tag, col = KIND[kind]
    num = 'all' if name == '__final__' else str(i)
    d.text((x, y + th + 8), f'{num}. {label}', font=ImageFont.truetype(B, 20), fill=(30, 36, 48))
    d.text((x, y + th + 36), tag, font=ImageFont.truetype(B, 15), fill=col)
out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, 'renders', 'layers-breakdown.jpg')
sheet.save(out, quality=88)
print(out, sheet.size)
