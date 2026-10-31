# Coco in London · a PixiJS visual experiment

A standalone prototype of one premium, illustrated London scene: the Thames from the South Bank
promenade, with the London Eye, Westminster and Big Ben, St Paul's, the City (the Gherkin, the
Walkie-Talkie, the Cheesegrater), the Shard and Tower Bridge. Coco flies in over the river and
lands on the balustrade.

It is fully independent: its own folder, package, dependencies and code, made from scratch for
this experiment. It does not use the Meet Coco project. The only existing artwork it uses is
Coco's original character image (`source/parrot.jpg` at the root of this repository).

## Run it

```bash
npm install
npm run dev          # http://127.0.0.1:5180
```

`?t=12` shows a fixed moment, paused; `?speed=0.5` slows time down. Moving the pointer adds a
little parallax. With *reduce motion* turned on in the system, the settled scene is shown still.

Rebuild the artwork (Python 3 with Pillow, NumPy, SciPy and Shapely):

```bash
python3 art/build.py                 # everything, about 2 minutes
python3 art/build.py landmarks coco  # only some groups
python3 art/preview.py               # a flat composite of scene.json, without PixiJS
```

Renders (needs Playwright with Chromium, and ffmpeg for the video):

```bash
npm run build && npm run preview     # serves on 127.0.0.1:4180
node tools/capture.cjs still  --t 12 --size 3840x2160 --out renders/london-4k.png
node tools/capture.cjs layers --t 12 --size 1920x1080 --out renders/layers
node tools/capture.cjs video  --from 0 --to 22 --fps 30 --size 1920x1080 --out renders/frames
ffmpeg -framerate 30 -i renders/frames/f%05d.png -c:v libx264 -pix_fmt yuv420p -crf 20 -movflags +faststart renders/coco-london.mp4
python3 tools/layers_sheet.py && python3 tools/assets_sheet.py
```

## How it is made

The artwork is **painted in code** with Python: the same kind of tooling as before (Pillow and
NumPy), with no AI image generation and no stock art. Shapes are rasterised at 4x for clean
edges. One sun (upper left, slightly in front) lights everything. Form comes from height fields
and soft shading: the leaf masses of the trees, the puffs of the clouds, the drum and dome of
St Paul's, the Gherkin's glass. Every asset is saved as a trimmed WebP with an anchor point in
`public/art/manifest.json`.

**PixiJS** composes that artwork into depth layers and does everything that should live and move:

| Element | Painted artwork (art/*.py) | Rendered by PixiJS (src/scene/*.ts) |
|---|---|---|
| Sky and clouds | sky gradient, 6 cumulus clouds | cloud drift, sun glow, gulls |
| Far city | far skyline, St Paul's, City towers, Gherkin, Shard | atmospheric haze between depths, parallax |
| Riverside | buildings district by district, plane trees, river wall | parallax, haze |
| Landmarks | London Eye (frame, wheel, capsule), Westminster, Tower Bridge, Union flag | Eye rotation with 32 level capsules, flag waving (mesh) |
| The Thames | base water colour, ripple and displacement textures | live reflection of the far bank (render texture), rippled by a drifting displacement map; depth wash; ripple highlights; sun glints; boat reflections and wakes; cloud shadows |
| Embankment | balustrade, promenade and road, lamps, trees, people, bushes | contact shadows, cloud shadows on the ground, two walkers |
| Bus | body and wheel | driving, wheels turning with distance, suspension bob, shadow |
| Boats | cruiser and launch | sailing, bobbing, wakes, reflections |
| Coco | body, near wing and far wing, cut from the original image | rig, wingbeats, flight path, flare and landing, breathing, blinking, shadow |
| Light | (consistent sun baked into every asset) | warm wash, cool shade, vignette, colour grade |

The whole scene is a pure function of time (`LondonScene.update(t)`), so any moment can be shown
exactly, which is how the stills, the layer sheet and the video frames are made.

## Scene layers, back to front

`src/scene/scene.json` places every painted asset (in 3840 x 2160 frame units) and gives each
layer a parallax depth. Layers added in code are marked *(PixiJS)*.

1. sky · 2. sun glow *(PixiJS)* · 3. far clouds · 4. clouds · 5. gulls *(PixiJS)* · 6. far skyline ·
7. haze *(PixiJS)* · 8. St Paul's, the City, the Gherkin, the Shard · 9. haze *(PixiJS)* ·
10. riverside buildings · 11. London Eye, Westminster, flag · 12. haze *(PixiJS)* ·
13. plane trees and river wall · 14. Tower Bridge · 15. the Thames *(painted water + PixiJS)* ·
16. balustrade · 17. promenade and road · 18. cloud shadows *(PixiJS)* · 19. lamps, trees,
people · 20. Coco · 21. bus · 22. foreground bushes · 23. light and vignette *(PixiJS)*

## The generated images (46)

| Group | Images |
|---|---|
| Sky | `sky`, `cloud_big`, `cloud_mid`, `cloud_mid2`, `cloud_small`, `cloud_small2`, `cloud_far`, `skyline_far` |
| Landmarks | `eye_frame`, `eye_wheel`, `eye_capsule`, `westminster`, `st_pauls`, `gherkin`, `shard`, `city_towers`, `tower_bridge`, `flag_union` |
| River | `riverside`, `farbank`, `water`, `water_displace`, `water_ripples` |
| Embankment | `balustrade`, `promenade`, `lamp`, `tree_prom_1`, `tree_prom_2`, `bush_1`, `bush_2`, `bush_3` |
| Life | `bus`, `bus_wheel`, `boat`, `boat_small`, `person_1` to `person_8` |
| Coco | `coco_body`, `coco_wing`, `coco_wing_far` |

## Files

- `art/`: the painting scripts. `paint.py` (toolkit), `foliage.py` (trees and bushes),
  `buildings.py` (facades, windows, roofs), `landmarks.py`, `scenery.py`, `props.py`, `coco.py`,
  `build.py` (runs them all), `preview.py` (flat composite).
- `public/art/`: the generated images and `manifest.json`.
- `src/main.ts`: the PixiJS app, fitting, time, capture hooks.
- `src/scene/`: `build.ts` (layers, light, motion), `river.ts`, `coco.ts`, `fx.ts` (code-made
  light and shadow textures), `assets.ts`, `scene.json` (layout).
- `tools/`: `capture.cjs` (stills, layers, video frames), `layers_sheet.py`, `assets_sheet.py`.
- `renders/`: the 4K still (`london-4k.png`), the video (`coco-london.mp4`), the layer and asset sheets.
