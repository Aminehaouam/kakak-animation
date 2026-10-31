"""A contact sheet of every generated image in public/art, on a checkerboard."""
import json
import os
import sys

from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.join(os.path.dirname(__file__), '..')
man = json.load(open(os.path.join(ROOT, 'public', 'art', 'manifest.json')))
extra = {'water_displace': {'file': 'art/water_displace.png'}, 'water_ripples': {'file': 'art/water_ripples.png'}}
items = sorted({**man, **extra}.items())
B = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
R = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
cw, ch, pad, cols = 360, 250, 22, 6
rows = (len(items) + cols - 1) // cols
head = 120
sheet = Image.new('RGB', (cols * cw + (cols + 1) * pad, head + rows * (ch + 60) + pad), (246, 244, 239))
d = ImageDraw.Draw(sheet)
d.text((pad, 26), f'Coco in London: the {len(items)} generated images', font=ImageFont.truetype(B, 36), fill=(30, 36, 48))
d.text((pad, 76), 'Painted by the Python scripts in art/ (Coco is cut from the original character image). Checkerboard = transparent.', font=ImageFont.truetype(R, 20), fill=(80, 88, 100))


def checker(w, h, s=12):
    im = Image.new('RGB', (w, h), (236, 236, 236))
    dd = ImageDraw.Draw(im)
    for y in range(0, h, s):
        for x in range(0, w, s):
            if (x // s + y // s) % 2:
                dd.rectangle([x, y, x + s - 1, y + s - 1], fill=(214, 214, 214))
    return im


for i, (name, a) in enumerate(items):
    x = pad + (i % cols) * (cw + pad)
    y = head + (i // cols) * (ch + 60)
    img = Image.open(os.path.join(ROOT, 'public', a['file'])).convert('RGBA')
    full = img.size
    img.thumbnail((cw, ch), Image.LANCZOS)
    cell = checker(cw, ch)
    cell.paste(img, ((cw - img.width) // 2, (ch - img.height) // 2), img)
    sheet.paste(cell, (x, y))
    d.text((x, y + ch + 6), name, font=ImageFont.truetype(B, 18), fill=(30, 36, 48))
    d.text((x, y + ch + 30), f'{full[0]} x {full[1]} px', font=ImageFont.truetype(R, 15), fill=(100, 106, 116))
out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, 'renders', 'assets-sheet.jpg')
sheet.save(out, quality=88)
print(out, sheet.size, len(items))
