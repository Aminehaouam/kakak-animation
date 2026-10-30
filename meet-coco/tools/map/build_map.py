"""Build the UK map's data from real geography.

Inputs (downloaded into the cache folder on the first run, about 165 MB):
  Natural Earth 1:10m vectors (public domain, naturalearthdata.com): admin-0 map units (England,
  Scotland, Wales, Northern Ireland, Ireland, the Isle of Man and the neighbours), lakes,
  rivers, roads and ferry routes, railways.
  Terrain: AWS Terrain Tiles (registry.opendata.aws/terrain-tiles), terrarium encoding, zoom 8.
  Heights come from SRTM, GMTED, ETOPO1 and other public sources; depths from ETOPO1 and GEBCO.

Outputs:
  src/components/map/ukmap.json   projected vector paths (1 unit = 1 km) and the projection
  public/map/terrain.webp         shaded relief with hypsometric tints; alpha is the land
  public/map/sea.webp             depth-tinted sea with a soft seabed relief

Projection: spherical transverse Mercator, central meridian 4 deg W, origin 54.5 deg N, so the
scale error stays under 0.3 % across the British Isles. src/components/map/projection.ts
implements the same formulas for markers and labels.

usage: python3 tools/map/build_map.py [--cache DIR]      (Python 3 with numpy, Pillow, shapely)
"""
import argparse
import json
import math
import os
import sys
import urllib.request

import numpy as np
from PIL import Image, ImageDraw
from shapely import ops
from shapely.geometry import LineString, MultiLineString, MultiPolygon, Polygon, box, shape
from shapely.ops import unary_union

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT_JSON = os.path.join(ROOT, 'src', 'components', 'map', 'ukmap.json')
OUT_IMG = os.path.join(ROOT, 'public', 'map')
NE_URL = 'https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/{}.geojson'
DEM_URL = 'https://s3.amazonaws.com/elevation-tiles-prod/terrarium/{z}/{x}/{y}.png'
NE_FILES = ['ne_10m_admin_0_map_units', 'ne_10m_lakes', 'ne_10m_lakes_europe',
            'ne_10m_rivers_lake_centerlines', 'ne_10m_rivers_europe', 'ne_10m_roads',
            'ne_10m_railroads']

# --------------------------------------------------------------------------- projection

R = 6371.0088          # km, mean Earth radius
LON0, LAT0 = -4.0, 54.5
# the map frame, in projected km (x east, y south) before the shift to the top-left corner
FRAME = {'west': (-10.9, 53.6), 'east': (2.25, 52.4), 'north': (-4.0, 61.0), 'south': (-4.0, 49.75)}


def tm(lon, lat):
    """Spherical transverse Mercator: degrees -> (x east, y north) km."""
    lam = np.radians(np.asarray(lon, float) - LON0)
    phi = np.radians(np.asarray(lat, float))
    b = np.cos(phi) * np.sin(lam)
    x = 0.5 * R * np.log((1 + b) / (1 - b))
    y = R * (np.arctan2(np.tan(phi), np.cos(lam)) - math.radians(LAT0))
    return x, y


def tm_inverse(x, y):
    d = y / R + math.radians(LAT0)
    lat = np.degrees(np.arcsin(np.sin(d) / np.cosh(x / R)))
    lon = LON0 + np.degrees(np.arctan2(np.sinh(x / R), np.cos(d)))
    return lon, lat


X0 = float(tm(*FRAME['west'])[0])
X1 = float(tm(*FRAME['east'])[0])
Y_TOP = float(tm(*FRAME['north'])[1])
Y_BOTTOM = float(tm(*FRAME['south'])[1])
W, H = round(X1 - X0), round(Y_TOP - Y_BOTTOM)


def to_map(lon, lat):
    """Degrees -> map units (km from the frame's top-left corner, y down)."""
    x, y = tm(lon, lat)
    return x - X0, Y_TOP - y


def from_map(mx, my):
    return tm_inverse(np.asarray(mx) + X0, Y_TOP - np.asarray(my))


def project(geom):
    return ops.transform(lambda x, y, z=None: to_map(x, y), geom)


VIEW = box(0, 0, W, H)
# the sea and the neighbouring coasts reach past the frame, so wide and tall screens see ocean
EXT = (-700, -350, W + 700, H + 350)
EXT_BOX = box(*EXT)
LONLAT_WINDOW = box(-26, 44.5, 16, 66.5)

# --------------------------------------------------------------------------- inputs


def fetch(cache):
    os.makedirs(os.path.join(cache, 'ne'), exist_ok=True)
    os.makedirs(os.path.join(cache, 'dem'), exist_ok=True)
    for name in NE_FILES:
        path = os.path.join(cache, 'ne', name + '.geojson')
        if not os.path.exists(path):
            print('download', name)
            urllib.request.urlretrieve(NE_URL.format(name), path)
    for x, y in dem_tiles():
        path = os.path.join(cache, 'dem', f'8_{x}_{y}.png')
        if not os.path.exists(path):
            urllib.request.urlretrieve(DEM_URL.format(z=8, x=x, y=y), path)


def dem_tiles(z=8):
    n = 2 ** z
    ex0, ey0, ex1, ey1 = EXT
    edge = np.linspace(0, 1, 50)
    xs = np.concatenate([ex0 + (ex1 - ex0) * edge, np.full(50, ex1), ex0 + (ex1 - ex0) * edge, np.full(50, ex0)])
    ys = np.concatenate([np.full(50, ey0), ey0 + (ey1 - ey0) * edge, np.full(50, ey1), ey0 + (ey1 - ey0) * edge])
    lons, lats = from_map(xs, ys)
    lon_w, lon_e = lons.min() - 0.5, lons.max() + 0.5
    lat_s, lat_n = lats.min() - 0.3, min(lats.max() + 0.3, 84)
    x0, x1 = int((lon_w + 180) / 360 * n), int((lon_e + 180) / 360 * n)
    y0, y1 = int(merc_y(lat_n) * n), int(merc_y(lat_s) * n)
    return [(x, y) for x in range(x0, x1 + 1) for y in range(y0, y1 + 1)]


def merc_y(lat):
    phi = np.radians(lat)
    return (1 - np.log(np.tan(phi) + 1 / np.cos(phi)) / math.pi) / 2


def load(cache, name, keep=lambda p: True):
    fc = json.load(open(os.path.join(cache, 'ne', name + '.geojson')))
    out = []
    for f in fc['features']:
        if not f.get('geometry'):
            continue
        g = shape(f['geometry'])
        if g.intersects(LONLAT_WINDOW) and keep(f['properties']):
            out.append((f['properties'], g.intersection(LONLAT_WINDOW)))
    return out


# --------------------------------------------------------------------------- vectors


def d_of(geom, closed=None, digits=1):
    """SVG path data for a (multi)polygon or (multi)line in map units."""
    parts = []

    def ring(coords, close):
        pts = [(round(x, digits), round(y, digits)) for x, y in coords]
        dedup = [pts[0]]
        for p in pts[1:]:
            if p != dedup[-1]:
                dedup.append(p)
        if close and len(dedup) > 1 and dedup[0] == dedup[-1]:
            dedup = dedup[:-1]
        if len(dedup) < 2:
            return
        s = 'M' + ' '.join(f'{fmt(x)},{fmt(y)}' for x, y in dedup[:1])
        s += 'L' + ' '.join(f'{fmt(x)},{fmt(y)}' for x, y in dedup[1:])
        parts.append(s + ('Z' if close else ''))

    for g in getattr(geom, 'geoms', [geom]):
        if isinstance(g, Polygon):
            ring(g.exterior.coords, True)
            for hole in g.interiors:
                ring(hole.coords, True)
        elif isinstance(g, LineString):
            ring(g.coords, False)
        elif hasattr(g, 'geoms'):
            parts.append(d_of(g, closed, digits))
    return ''.join(parts)


def fmt(v):
    s = f'{v:.1f}'
    return s[:-2] if s.endswith('.0') else s


def polys(geom):
    return [g for g in getattr(geom, 'geoms', [geom]) if isinstance(g, Polygon) and not g.is_empty]


def lines(geom):
    out = []
    for g in getattr(geom, 'geoms', [geom]):
        if isinstance(g, LineString) and not g.is_empty:
            out.append(g)
        elif isinstance(g, (MultiLineString,)) or hasattr(g, 'geoms'):
            out += lines(g)
    return out


COUNTRIES = {'ENG': ('england', 'England'), 'SCT': ('scotland', 'Scotland'),
             'WLS': ('wales', 'Wales'), 'NIR': ('northern-ireland', 'Northern Ireland'),
             'IRL': ('ireland', 'Ireland'), 'IMN': ('isle-of-man', 'Isle of Man')}


def build_vectors(cache):
    units = load(cache, 'ne_10m_admin_0_map_units')
    countries, neighbours = {}, []
    for p, g in units:
        code = p.get('GU_A3')
        geom = project(g)
        if code in COUNTRIES:
            countries[code] = geom.intersection(VIEW.buffer(40)).buffer(0)
        else:
            geom = geom.intersection(EXT_BOX.buffer(20))
            if not geom.is_empty:
                neighbours.append(geom.buffer(0))
    land = unary_union(list(countries.values()))
    # drop specks: islands smaller than a km2 clutter the coast at this scale
    land = MultiPolygon([q for q in polys(land) if q.area >= 1.0])
    land_s = land.simplify(0.22, preserve_topology=True)
    neighbours_s = unary_union(neighbours).simplify(0.6, preserve_topology=True)
    neighbours_s = MultiPolygon([q for q in polys(neighbours_s) if q.area >= 3.0])

    country_out = []
    for code, (cid, name) in COUNTRIES.items():
        c = countries[code]
        country_out.append({'id': cid, 'name': name, 'areaKm2': round(c.area)})

    # internal borders: shared edges of neighbouring units
    borders = []
    pairs = [('ENG', 'SCT'), ('ENG', 'WLS'), ('NIR', 'IRL')]
    for a, b in pairs:
        shared = countries[a].boundary.intersection(countries[b].buffer(0.05))
        shared = ops.linemerge(MultiLineString(lines(shared))) if lines(shared) else shared
        borders += [ln.simplify(0.3) for ln in lines(shared) if ln.length > 2]

    # coast rings for the drawing animation, longest first
    rings = sorted((LineString(q.exterior.coords) for q in polys(land_s)), key=lambda r: -r.length)
    coast = [d_of(r) + 'Z' for r in rings if r.length > 25]
    coast_small = ''.join(d_of(r) + 'Z' for r in rings if r.length <= 25)

    # coastal ripples, offset outlines of the land in the sea
    ripples = []
    for dist in (3.5, 9.0):
        out = land.buffer(dist, quad_segs=4).simplify(1.0)
        ring_lines = [LineString(q.exterior.coords) for q in polys(out) if q.exterior.length > 30]
        ripples.append(d_of(MultiLineString(ring_lines).intersection(VIEW)))

    lake_geoms = [project(g) for _, g in load(cache, 'ne_10m_lakes') + load(cache, 'ne_10m_lakes_europe')]
    lakes = unary_union(lake_geoms).intersection(land.buffer(0.2))
    lakes = MultiPolygon([q for q in polys(lakes) if q.area >= 0.6]).simplify(0.12)

    rivers = {}
    for p, g in load(cache, 'ne_10m_rivers_lake_centerlines') + load(cache, 'ne_10m_rivers_europe'):
        name = p.get('name') or p.get('name_en') or ''
        geom = project(g).intersection(land.buffer(0.6))
        for ln in lines(geom):
            if ln.length > 3:
                rivers.setdefault(name, []).append(ln.simplify(0.25))
    river_out = [{'name': n, 'd': d_of(MultiLineString(ls))} for n, ls in sorted(rivers.items())
                 if n not in ('Caledonian Canal',)]

    roads = {'major': [], 'minor': [], 'ferry': []}
    for p, g in load(cache, 'ne_10m_roads'):
        kind = p.get('type') or ''
        geom = project(g)
        if kind.startswith('Ferry'):
            # the short crossings (Irish Sea, Hebrides, Channel); long North Sea routes clutter
            if 5 < geom.length < 260:
                roads['ferry'] += [ln.simplify(0.5) for ln in lines(geom.intersection(VIEW))]
            continue
        target = 'major' if kind == 'Major Highway' else 'minor' if kind == 'Secondary Highway' else None
        if target:
            clipped = geom.intersection(land.buffer(0.3))
            tol = 0.35 if target == 'major' else 0.6
            roads[target] += [ln.simplify(tol) for ln in lines(clipped) if ln.length > 1.5]

    rail = []
    for p, g in load(cache, 'ne_10m_railroads'):
        clipped = project(g).intersection(land.buffer(0.3))
        rail += [ln.simplify(0.5) for ln in lines(clipped) if ln.length > 1.5]

    data = {
        'source': 'Natural Earth 1:10m (public domain); terrain: AWS Terrain Tiles',
        'projection': {'type': 'transverse-mercator', 'sphere': R, 'lon0': LON0, 'lat0': LAT0,
                       'x0': round(X0, 4), 'yTop': round(Y_TOP, 4)},
        'size': [W, H],
        'extent': list(EXT),
        'land': d_of(land_s),
        'ireland': d_of(countries['IRL'].simplify(0.22, preserve_topology=True)),
        'neighbours': d_of(neighbours_s),
        'countries': country_out,
        'borders': d_of(MultiLineString(borders)),
        'coast': coast,
        'coastSmall': coast_small,
        'ripples': ripples,
        'lakes': d_of(lakes),
        'rivers': river_out,
        'roads': {k: d_of(MultiLineString(v)) for k, v in roads.items()},
        'rail': d_of(MultiLineString(rail)),
    }
    return data, land, unary_union(neighbours)


# --------------------------------------------------------------------------- rasters


def dem_mosaic(cache, z=8):
    tiles = dem_tiles(z)
    xs = sorted({x for x, _ in tiles})
    ys = sorted({y for _, y in tiles})
    mosaic = np.zeros((len(ys) * 256, len(xs) * 256), np.float32)
    for x, y in tiles:
        a = np.asarray(Image.open(os.path.join(cache, 'dem', f'{z}_{x}_{y}.png')).convert('RGB'),
                       np.float32)
        h = a[..., 0] * 256 + a[..., 1] + a[..., 2] / 256 - 32768
        mosaic[(y - ys[0]) * 256:(y - ys[0] + 1) * 256, (x - xs[0]) * 256:(x - xs[0] + 1) * 256] = h
    return mosaic, xs[0] * 256, ys[0] * 256, 256 * 2 ** z


def sample(img, gx, gy):
    """Bilinear sample of img at fractional pixel coordinates."""
    h, w = img.shape
    gx = np.clip(gx - 0.5, 0, w - 1.001)
    gy = np.clip(gy - 0.5, 0, h - 1.001)
    x0, y0 = np.floor(gx).astype(int), np.floor(gy).astype(int)
    fx, fy = gx - x0, gy - y0
    a, b = img[y0, x0], img[y0, x0 + 1]
    c, d = img[y0 + 1, x0], img[y0 + 1, x0 + 1]
    return (a * (1 - fx) + b * fx) * (1 - fy) + (c * (1 - fx) + d * fx) * fy


def heights(cache, px_per_km, frame=(0, 0, None, None)):
    mosaic, gx0, gy0, world = dem_mosaic(cache)
    fx0, fy0, fx1, fy1 = frame[0], frame[1], frame[2] if frame[2] is not None else W, frame[3] if frame[3] is not None else H
    w, h = int(round((fx1 - fx0) * px_per_km)), int(round((fy1 - fy0) * px_per_km))
    my, mx = np.mgrid[0:h, 0:w].astype(np.float64)
    lon, lat = from_map(fx0 + (mx + 0.5) / px_per_km, fy0 + (my + 0.5) / px_per_km)
    gx = (lon + 180) / 360 * world - gx0
    gy = merc_y(lat) * world - gy0
    return sample(mosaic, gx, gy).astype(np.float32)


def blur(a, sigma):
    """Gaussian blur (three box passes per axis, edges clamped)."""
    a = np.asarray(a, np.float32)
    if sigma <= 0:
        return a
    n = 3
    w_ideal = math.sqrt(12 * sigma * sigma / n + 1)
    wl = int(w_ideal) - (1 - int(w_ideal) % 2)       # largest odd width below the ideal
    m = round((12 * sigma * sigma - n * wl * wl - 4 * n * wl - 3 * n) / (-4 * wl - 4))
    for i in range(n):
        r = ((wl if i < m else wl + 2) - 1) // 2
        if r < 1:
            continue
        for axis in (0, 1):
            pad = [(0, 0), (0, 0)]
            pad[axis] = (r + 1, r)
            c = np.cumsum(np.pad(a, pad, mode='edge'), axis=axis, dtype=np.float64)
            hi = np.take(c, np.arange(2 * r + 1, c.shape[axis]), axis=axis)
            lo = np.take(c, np.arange(0, c.shape[axis] - 2 * r - 1), axis=axis)
            a = ((hi - lo) / (2 * r + 1)).astype(np.float32)
    return a


def hillshade(z, px_m, exaggeration, azimuth=315.0, altitude=42.0):
    gy, gx = np.gradient(z * exaggeration, px_m)
    slope = np.arctan(np.hypot(gx, gy))
    aspect = np.arctan2(-gx, gy)
    az, alt = math.radians(azimuth), math.radians(altitude)
    shade = (math.sin(alt) * np.cos(slope)
             + math.cos(alt) * np.sin(slope) * np.cos(az - aspect - math.pi / 2))
    return np.clip(shade, 0, 1)


def ramp(values, stops):
    xs = np.array([s[0] for s in stops], np.float32)
    out = np.zeros(values.shape + (3,), np.float32)
    for c in range(3):
        out[..., c] = np.interp(values, xs, np.array([s[1][c] for s in stops], np.float32))
    return out


def hexc(s):
    return tuple(int(s[i:i + 2], 16) for i in (1, 3, 5))


LAND_RAMP = [(0, hexc('#a7cf8c')), (40, hexc('#9fca86')), (120, hexc('#a3c47f')),
             (250, hexc('#b2c283')), (420, hexc('#c1bd89')), (620, hexc('#c9b994')),
             (850, hexc('#d4c5aa')), (1100, hexc('#e4dacb')), (1400, hexc('#f1ece4'))]
SEA_RAMP = [(0, hexc('#b4e0e9')), (20, hexc('#a3d6e3')), (60, hexc('#8ecadd')),
            (120, hexc('#7dbdd6')), (200, hexc('#6eb0ce')), (600, hexc('#5fa2c5')),
            (1500, hexc('#5495bc')), (3000, hexc('#4b8ab3'))]


def mask(geom, px_per_km, w, h, ss=3, origin=(0, 0)):
    img = Image.new('L', (w * ss, h * ss), 0)
    draw = ImageDraw.Draw(img)
    k = px_per_km * ss
    ox, oy = origin
    for q in polys(geom):
        draw.polygon([((x - ox) * k, (y - oy) * k) for x, y in q.exterior.coords], fill=255)
        for hole in q.interiors:
            draw.polygon([((x - ox) * k, (y - oy) * k) for x, y in hole.coords], fill=0)
    return np.asarray(img.resize((w, h), Image.LANCZOS), np.float32) / 255


def grain(shape_, amount, seed):
    rng = np.random.default_rng(seed)
    n = rng.standard_normal(shape_).astype(np.float32)
    return blur(n, 0.6) * amount


def build_terrain(cache, land, px_per_km=2.0):
    z = heights(cache, px_per_km)
    h_, w_ = z.shape
    alpha = mask(land, px_per_km, w_, h_)
    zl = np.maximum(z, 0)
    zl = blur(zl, 0.7)
    px_m = 1000.0 / px_per_km
    shade = 0.6 * hillshade(zl, px_m, 4.0) + 0.4 * hillshade(zl, px_m, 4.0, azimuth=270, altitude=55)
    flat = math.sin(math.radians(42)) * 0.6 + math.sin(math.radians(55)) * 0.4
    rel = shade - flat                                  # 0 on flat ground, + lit, - shaded
    col = ramp(zl, LAND_RAMP)
    lit = np.clip(rel, 0, 1)[..., None]
    dark = np.clip(-rel, 0, 1)[..., None]
    col = col + lit * 1.6 * (np.array([255, 250, 232], np.float32) - col)
    col = col * (1 - dark * 1.15) + dark * 1.15 * np.array([86, 104, 112], np.float32) * 0.6
    # gentle darkening toward the coast keeps the coastline crisp against the light sea
    edge = blur(alpha, 2.5 * px_per_km)
    col *= (0.93 + 0.07 * np.clip((edge - 0.5) * 2, 0, 1))[..., None]
    col += grain((h_, w_), 2.2, 7)[..., None]
    rgba = np.dstack([np.clip(col, 0, 255), alpha * 255]).astype(np.uint8)
    return Image.fromarray(rgba, 'RGBA')


def build_sea(cache, land, px_per_km=0.8):
    z = heights(cache, px_per_km, EXT)
    h_, w_ = z.shape
    on_land = mask(land, px_per_km, w_, h_, origin=EXT[:2])
    depth = np.maximum(-blur(z, 1.2), 0)
    # under the land the sea carries on as shallow water, so before the land is drawn in the
    # coastline reads as a line on open water rather than a bright island
    depth = depth * (1 - on_land) + 45 * on_land
    col = ramp(depth, SEA_RAMP)
    shade = hillshade(-depth, 1000.0 / px_per_km, 14.0)
    col *= (0.965 + 0.07 * (shade - 0.65))[..., None]
    # a light rim along the coasts, in the water only
    near = blur(on_land, 3.0 * px_per_km) * (1 - on_land)
    col += np.clip(near * 2.2, 0, 1)[..., None] * 0.35 * (np.array([214, 238, 242], np.float32) - col)
    col += grain((h_, w_), 1.6, 11)[..., None]
    return Image.fromarray(np.clip(col, 0, 255).astype(np.uint8), 'RGB')


# --------------------------------------------------------------------------- main


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--cache', default=os.path.join(os.path.dirname(os.path.abspath(__file__)), '.cache'))
    ap.add_argument('--no-rasters', action='store_true')
    args = ap.parse_args(argv)
    fetch(args.cache)
    data, land, neighbours = build_vectors(args.cache)
    os.makedirs(os.path.dirname(OUT_JSON), exist_ok=True)
    with open(OUT_JSON, 'w') as f:
        json.dump(data, f, separators=(',', ':'))
    print(f'{os.path.relpath(OUT_JSON, ROOT)}: {os.path.getsize(OUT_JSON) // 1024} KB, '
          f'{W} x {H} km, {len(data["coast"])} coast rings, {len(data["rivers"])} rivers')
    if args.no_rasters:
        return
    os.makedirs(OUT_IMG, exist_ok=True)
    terrain = build_terrain(args.cache, land)
    terrain.save(os.path.join(OUT_IMG, 'terrain.webp'), quality=82, method=6)
    sea = build_sea(args.cache, unary_union([land, neighbours]))
    sea.save(os.path.join(OUT_IMG, 'sea.webp'), quality=84, method=6)
    for name in ('terrain.webp', 'sea.webp'):
        p = os.path.join(OUT_IMG, name)
        im = Image.open(p)
        print(f'public/map/{name}: {im.size[0]} x {im.size[1]}, {os.path.getsize(p) // 1024} KB')


if __name__ == '__main__':
    main(sys.argv[1:])
