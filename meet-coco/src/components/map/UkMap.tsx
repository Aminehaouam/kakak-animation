import { Fragment, memo, useCallback, useEffect, useLayoutEffect, useMemo, useRef, useState, type ReactNode } from 'react';
import { CITIES, COUNTRY_LABELS, ISLAND_LABELS, REGION_LABELS, SEA_LABELS, STOPS, type LonLat } from '../../config/places';
import { clamp, ease, progress } from '../../lib/anim';
import type { Pt } from '../../lib/path';
import { sound } from '../../audio/sound';
import { CocoActor } from '../coco/CocoActor';
import type { CocoCue, CocoMode } from '../coco/Coco';
import { EXTENT, MAP, ROUTE, STOP_POINTS, TREES, WAVES } from './geo';
import { MAP_H, MAP_W, toMap } from './projection';
import './map.css';

/** When each layer appears, in seconds of `reveal`. */
export const REVEAL = {
  ocean: 0,
  coast: 0.7,
  land: 2.9,
  terrain: 3.6,
  water: 4.3,
  forests: 4.9,
  roads: 5.4,
  labels: 6.0,
  markers: 7.0,
  done: 8.4,
};

export interface MapCamera {
  /** centre, in map units (km from the top-left corner) */
  x: number;
  y: number;
  /** 1 = the whole map fits */
  zoom: number;
}

export interface MapCoco {
  at: Pt;
  mode: CocoMode;
  facing: 'left' | 'right';
  tilt?: number;
  cue?: CocoCue;
}

export interface UkMapProps {
  /** seconds into the staged reveal (Infinity: everything shown) */
  reveal?: number;
  /** how much of the route is drawn, 0..1 */
  route?: number;
  /** how much of the route shows faintly, as the plan ahead, 0..1 */
  routePlanned?: number;
  completed?: string[];
  current?: string | null;
  /** a camera the story drives; people can still take over when interactive */
  camera?: MapCamera | null;
  /** change it to drop a camera someone set by hand */
  cameraKey?: string | number;
  interactive?: boolean;
  coco?: MapCoco | null;
  reduced?: boolean;
  /** room kept free of the map when fitting it (px) */
  padding?: { top?: number; right?: number; bottom?: number; left?: number };
  onInteract?: () => void;
  onSelect?: (id: string | null) => void;
  /** extra screen-space overlay, given a map -> screen function */
  overlay?: (toScreen: (p: Pt) => Pt, scale: number) => ReactNode;
  className?: string;
}

const ZMIN = 0.85;
const ZMAX = 10; // for people zooming; the story's own camera may dive further
const ZMAX_STORY = 18;
const COAST_RINGS = MAP.coast;

export function cameraOn(lonlat: LonLat, zoom: number): MapCamera {
  const p = toMap(lonlat);
  return { x: p.x, y: p.y, zoom };
}

export const UkMap = memo(function UkMap({
  reveal = Infinity,
  route = 0,
  routePlanned = 0,
  completed = [],
  current = null,
  camera = null,
  cameraKey,
  interactive = false,
  coco = null,
  reduced = false,
  padding,
  onInteract,
  onSelect,
  overlay,
  className,
}: UkMapProps) {
  const ref = useRef<HTMLDivElement>(null);
  const [size, setSize] = useState({ w: 0, h: 0 });
  const [userCam, setUserCam] = useState<MapCamera | null>(null);
  const [selected, setSelected] = useState<string | null>(null);
  const [hovered, setHovered] = useState<string | null>(null);

  useLayoutEffect(() => {
    const el = ref.current!;
    const update = () => setSize({ w: el.clientWidth, h: el.clientHeight });
    update();
    const ro = new ResizeObserver(update);
    ro.observe(el);
    return () => ro.disconnect();
  }, []);

  useEffect(() => setUserCam(null), [cameraKey]);

  const pad = { top: 0, right: 0, bottom: 0, left: 0, ...padding };
  const fit = Math.max(Math.min((size.w - pad.left - pad.right) / MAP_W, (size.h - pad.top - pad.bottom) / MAP_H), 0.05);
  const home: MapCamera = {
    x: MAP_W / 2 + (pad.right - pad.left) / (2 * fit),
    y: MAP_H / 2 + (pad.bottom - pad.top) / (2 * fit),
    zoom: 1,
  };

  const clampCam = useCallback(
    (c: MapCamera, zmax = ZMAX): MapCamera => {
      const zoom = clamp(c.zoom, ZMIN, zmax);
      const s = fit * zoom;
      const hw = size.w / (2 * s);
      const hh = size.h / (2 * s);
      const cx = EXTENT.x1 - EXTENT.x0 > 2 * hw ? clamp(c.x, EXTENT.x0 + hw, EXTENT.x1 - hw) : (EXTENT.x0 + EXTENT.x1) / 2;
      const cy = EXTENT.y1 - EXTENT.y0 > 2 * hh ? clamp(c.y, EXTENT.y0 + hh, EXTENT.y1 - hh) : (EXTENT.y0 + EXTENT.y1) / 2;
      return { x: cx, y: cy, zoom };
    },
    [fit, size.w, size.h],
  );

  const cam = userCam ? clampCam(userCam) : clampCam(camera ?? home, ZMAX_STORY);
  const s = fit * cam.zoom;
  const tx = size.w / 2 - cam.x * s;
  const ty = size.h / 2 - cam.y * s;
  const toScreen = useCallback((p: Pt): Pt => ({ x: p.x * s + tx, y: p.y * s + ty }), [s, tx, ty]);

  // ---- gestures: drag to pan, wheel / pinch / double-click to zoom
  const camRef = useRef(cam);
  camRef.current = cam;
  const touched = useRef(false);
  const takeOver = useCallback(() => {
    if (!touched.current) {
      touched.current = true;
      onInteract?.();
    }
  }, [onInteract]);
  useEffect(() => {
    touched.current = false;
  }, [cameraKey]);

  const zoomAt = useCallback(
    (factor: number, px: number, py: number) => {
      const c = camRef.current;
      const s0 = fit * c.zoom;
      const wx = c.x + (px - size.w / 2) / s0;
      const wy = c.y + (py - size.h / 2) / s0;
      const zoom = clamp(c.zoom * factor, ZMIN, ZMAX);
      const s1 = fit * zoom;
      setUserCam(clampCam({ x: wx - (px - size.w / 2) / s1, y: wy - (py - size.h / 2) / s1, zoom }));
      takeOver();
    },
    [fit, size.w, size.h, clampCam, takeOver],
  );

  useEffect(() => {
    const el = ref.current;
    if (!el || !interactive) return;
    const onWheel = (e: WheelEvent) => {
      e.preventDefault();
      const r = el.getBoundingClientRect();
      zoomAt(Math.exp(-e.deltaY * (e.deltaMode === 1 ? 0.05 : 0.0018)), e.clientX - r.left, e.clientY - r.top);
    };
    el.addEventListener('wheel', onWheel, { passive: false });
    return () => el.removeEventListener('wheel', onWheel);
  }, [interactive, zoomAt]);

  const pointers = useRef(new Map<number, Pt>());
  const pinch = useRef<{ d: number; mid: Pt } | null>(null);
  const onPointerDown = (e: React.PointerEvent) => {
    if (!interactive || (e.target as HTMLElement).closest('button, a, .map-card')) return;
    (e.currentTarget as HTMLElement).setPointerCapture(e.pointerId);
    pointers.current.set(e.pointerId, { x: e.clientX, y: e.clientY });
    pinch.current = null;
  };
  const onPointerMove = (e: React.PointerEvent) => {
    const prev = pointers.current.get(e.pointerId);
    if (!prev) return;
    const next = { x: e.clientX, y: e.clientY };
    pointers.current.set(e.pointerId, next);
    const pts = [...pointers.current.values()];
    const c = camRef.current;
    if (pts.length === 1) {
      const sNow = fit * c.zoom;
      if (Math.hypot(next.x - prev.x, next.y - prev.y) < 0.5) return;
      setUserCam(clampCam({ x: c.x - (next.x - prev.x) / sNow, y: c.y - (next.y - prev.y) / sNow, zoom: c.zoom }));
      takeOver();
    } else if (pts.length === 2) {
      const r = ref.current!.getBoundingClientRect();
      const d = Math.hypot(pts[0].x - pts[1].x, pts[0].y - pts[1].y);
      const mid = { x: (pts[0].x + pts[1].x) / 2 - r.left, y: (pts[0].y + pts[1].y) / 2 - r.top };
      if (pinch.current) {
        const sNow = fit * c.zoom;
        const panned = { ...c, x: c.x - (mid.x - pinch.current.mid.x) / sNow, y: c.y - (mid.y - pinch.current.mid.y) / sNow };
        camRef.current = clampCam(panned);
        zoomAt(d / pinch.current.d, mid.x, mid.y);
      }
      pinch.current = { d, mid };
    }
  };
  const onPointerUp = (e: React.PointerEvent) => {
    pointers.current.delete(e.pointerId);
    pinch.current = null;
  };
  const onKeyDown = (e: React.KeyboardEvent) => {
    if (!interactive) return;
    const step = 60 / s;
    const c = camRef.current;
    const moves: Record<string, Partial<MapCamera>> = {
      ArrowLeft: { x: c.x - step },
      ArrowRight: { x: c.x + step },
      ArrowUp: { y: c.y - step },
      ArrowDown: { y: c.y + step },
    };
    if (moves[e.key]) {
      e.preventDefault();
      e.stopPropagation();
      setUserCam(clampCam({ ...c, ...moves[e.key] }));
      takeOver();
    } else if (e.key === '+' || e.key === '=') zoomAt(1.4, size.w / 2, size.h / 2);
    else if (e.key === '-' || e.key === '_') zoomAt(1 / 1.4, size.w / 2, size.h / 2);
    else if (e.key === 'Escape' && selected) select(null);
  };

  const select = (id: string | null) => {
    setSelected(id);
    onSelect?.(id);
    if (id) {
      sound.play('ding', { volume: 0.6 });
      takeOver();
    }
  };

  // ---- reveal
  const r = reveal;
  const at = (key: keyof typeof REVEAL, dur = 1) => (reduced ? (r >= REVEAL[key] ? 1 : 0) : ease.out(progress(r, REVEAL[key], dur)));
  const oOcean = at('ocean', 1.2);
  const pCoast = reduced ? (r >= REVEAL.coast ? 1 : 0) : ease.inOut(progress(r, REVEAL.coast, 2.6));
  const oLand = at('land', 1.2);
  const oTerrain = at('terrain', 1.6);
  const oWater = at('water', 1.4);
  const oForest = at('forests', 1.2);
  const oRoads = at('roads', 1.2);
  const oLabels = at('labels', 1.3);
  const px = 1 / s; // one screen pixel in map units

  const routeD = useMemo(() => (route > 0 ? ROUTE.d(route) : ''), [route]);
  const plannedD = useMemo(() => (routePlanned > 0 ? ROUTE.d(routePlanned) : ''), [routePlanned]);
  const visibleStops = STOPS.map((stop, i) => ({ stop, i, p: STOP_POINTS[stop.id], appear: reduced ? (r >= REVEAL.markers ? 1 : 0) : ease.outBack(progress(r, REVEAL.markers + i * 0.18, 0.55)) }));

  const inView = (p: Pt, m = 80) => p.x > -m && p.y > -m && p.x < size.w + m && p.y < size.h + m;

  // scale bar: a round distance close to 110 px
  const kmPer110 = 110 / s;
  const nice = [5, 10, 20, 25, 50, 100, 150, 200, 250, 300].find((v) => v >= kmPer110 * 0.6) ?? 300;
  const bar = nice * s;

  const sel = selected ? STOPS.find((x) => x.id === selected) : null;
  const selPos = sel ? toScreen(STOP_POINTS[sel.id]) : null;

  return (
    <div
      ref={ref}
      className={`ukmap${interactive ? ' ukmap--interactive' : ''}${reduced ? ' ukmap--reduced' : ''}${className ? ` ${className}` : ''}`}
      onPointerDown={onPointerDown}
      onPointerMove={onPointerMove}
      onPointerUp={onPointerUp}
      onPointerCancel={onPointerUp}
      onDoubleClick={(e) => {
        if (!interactive || (e.target as HTMLElement).closest('button, .map-card')) return;
        const rect = ref.current!.getBoundingClientRect();
        zoomAt(1.8, e.clientX - rect.left, e.clientY - rect.top);
      }}
      onKeyDown={onKeyDown}
      tabIndex={interactive ? 0 : -1}
      role={interactive ? 'application' : 'img'}
      aria-label="Map of the United Kingdom and Ireland. Use the arrow keys to pan, plus and minus to zoom, and Tab to reach the stops."
    >
      {size.w > 0 && (
        <svg className="ukmap__svg" width={size.w} height={size.h} aria-hidden>
          <defs>
            <linearGradient id="routeGlow" x1="0" x2="1">
              <stop offset="0" stopColor="#ffe9b0" />
              <stop offset="1" stopColor="#fff4d8" />
            </linearGradient>
            <symbol id="tree-c" viewBox="-6 -14 12 15" overflow="visible">
              <path d="M0-13.5 5 -3.2H-5z" />
              <path d="M0-9.5 5.8 0H-5.8z" />
            </symbol>
            <symbol id="tree-d" viewBox="-6 -14 12 15" overflow="visible">
              <circle cx="0" cy="-7.2" r="5.6" />
              <circle cx="-2.6" cy="-4.4" r="3.4" />
              <circle cx="2.8" cy="-4.2" r="3.6" />
            </symbol>
          </defs>
          <g transform={`translate(${tx} ${ty}) scale(${s})`}>
            <image
              href={`${import.meta.env.BASE_URL}map/sea.webp`}
              x={EXTENT.x0}
              y={EXTENT.y0}
              width={EXTENT.x1 - EXTENT.x0}
              height={EXTENT.y1 - EXTENT.y0}
              preserveAspectRatio="none"
              opacity={oOcean}
            />
            <g className="ukmap__ripples" opacity={oOcean * (0.35 + 0.65 * oLand)} strokeWidth={px * 0.9}>
              {MAP.ripples.map((d, i) => (
                <path key={i} d={d} opacity={i === 0 ? 0.55 : 0.3} />
              ))}
            </g>
            <g className="ukmap__waves" opacity={oOcean * 0.9}>
              {WAVES.map((w, i) => (
                <path
                  key={i}
                  className="ukmap__wave"
                  style={{ animationDelay: `${-(i * 0.73) % 6}s` }}
                  d={`M${w.x - 7 * px * 6},${w.y} q${3.5 * px * 6},${-3 * px * 6} ${7 * px * 6},0 t${7 * px * 6},0`}
                  strokeWidth={px * 1.1}
                />
              ))}
            </g>
            <path className="ukmap__neighbours" d={MAP.neighbours} opacity={oLand * 0.95} strokeWidth={px * 0.8} />
            <path className="ukmap__land-shadow" d={MAP.land} transform={`translate(${1.2 * px} ${2.4 * px})`} opacity={oLand * 0.5} />
            <path className="ukmap__land" d={MAP.land} opacity={oLand} />
            <image
              href={`${import.meta.env.BASE_URL}map/terrain.webp`}
              x={0}
              y={0}
              width={MAP_W}
              height={MAP_H}
              preserveAspectRatio="none"
              opacity={oTerrain}
            />
            <path className="ukmap__ireland" d={IRELAND_D} opacity={oTerrain * 0.2} />
            <g opacity={oWater}>
              <path className="ukmap__lakes" d={MAP.lakes} strokeWidth={px * 0.6} />
              {MAP.rivers.map((rv) => (
                <path key={rv.name} className="ukmap__river" d={rv.d} strokeWidth={px * (rv.name === 'Thames' || rv.name === 'Severn' || rv.name === 'Shannon' ? 1.6 : 1.1)} />
              ))}
            </g>
            <g opacity={oRoads}>
              <path className="ukmap__road-minor" d={MAP.roads.minor} strokeWidth={px * 0.55} opacity={clamp(0.25 + (cam.zoom - 1) * 0.35, 0.25, 0.85)} />
              <path className="ukmap__road" d={MAP.roads.major} strokeWidth={px * 1.0} />
              <path className="ukmap__rail" d={MAP.rail} strokeWidth={px * 0.9} strokeDasharray={`${px * 3.2} ${px * 2.2}`} />
              <path className="ukmap__ferry" d={MAP.roads.ferry} strokeWidth={px * 0.9} strokeDasharray={`${px * 1.2} ${px * 3.4}`} />
            </g>
            <path className="ukmap__borders" d={MAP.borders} strokeWidth={px * 1.3} strokeDasharray={`${px * 5} ${px * 3}`} style={{ opacity: oLand * 0.8 }} />
            <g className="ukmap__coast" strokeWidth={px * 1.15} opacity={oOcean}>
              {COAST_RINGS.map((d, i) => (
                <path key={i} d={d} pathLength={1} strokeDasharray="1 1" strokeDashoffset={1 - pCoast} />
              ))}
              <path d={MAP.coastSmall} opacity={pCoast} />
            </g>
            <g className="ukmap__trees" opacity={oForest}>
              {TREES.map((tr, i) => {
                const grow = reduced ? 1 : ease.outBack(progress(r, REVEAL.forests + (i % 17) * 0.04, 0.5));
                const k = Math.max(tr.s * 0.62 * grow, 0.001) * clamp(1.1 / Math.sqrt(cam.zoom), 0.55, 1.1);
                return (
                  <use
                    key={i}
                    href={tr.conifer ? '#tree-c' : '#tree-d'}
                    x={-6}
                    y={-14}
                    width={12}
                    height={15}
                    transform={`translate(${tr.x} ${tr.y}) scale(${k})`}
                    className={tr.tone < 0.5 ? 'ukmap__tree' : 'ukmap__tree ukmap__tree--b'}
                  />
                );
              })}
            </g>
            {plannedD && (
              <path d={plannedD} className="ukmap__route-planned" strokeWidth={px * 2.2} strokeDasharray={`${px * 1.5} ${px * 6}`} />
            )}
            {routeD && (
              <g className="ukmap__route">
                <path d={routeD} className="ukmap__route-casing" strokeWidth={px * 7} />
                <path d={routeD} className="ukmap__route-line" strokeWidth={px * 2.6} strokeDasharray={`${px * 9} ${px * 6}`} />
              </g>
            )}
            {selected && (
              <circle cx={STOP_POINTS[selected].x} cy={STOP_POINTS[selected].y} r={px * 24} className="ukmap__halo" strokeWidth={px * 1.5} />
            )}
          </g>
        </svg>
      )}

      {size.w > 0 && (
        <div className="ukmap__labels" aria-hidden style={{ opacity: oLabels }}>
          {placeLabels({ cam, size, toScreen, stopBoxes: visibleStops.map(({ stop, p }) => stopBox(stop, toScreen(p))) })}
        </div>
      )}

      {size.w > 0 && (
        <div className="ukmap__stops">
          {visibleStops.map(({ stop, i, p, appear }) => {
            const q = toScreen(p);
            if (appear <= 0 || !inView(q)) return null;
            const done = completed.includes(stop.id);
            const cls = ['map-stop', `map-stop--${stop.labelSide ?? 'right'}`, done && 'is-done', current === stop.id && 'is-current', selected === stop.id && 'is-selected', hovered === stop.id && 'is-hover']
              .filter(Boolean)
              .join(' ');
            return (
              <button
                key={stop.id}
                className={cls}
                style={{ transform: `translate(${q.x}px, ${q.y}px) scale(${appear})`, opacity: clamp(appear * 1.5) }}
                onClick={() => (interactive ? select(selected === stop.id ? null : stop.id) : undefined)}
                onMouseEnter={() => setHovered(stop.id)}
                onMouseLeave={() => setHovered(null)}
                onFocus={() => setHovered(stop.id)}
                onBlur={() => setHovered(null)}
                tabIndex={interactive ? 0 : -1}
                aria-label={`Stop ${i + 1}: ${stop.name}${done ? ', visited' : ''}`}
                aria-expanded={selected === stop.id}
              >
                <span className="map-stop__pin">{done ? <CheckIcon /> : i + 1}</span>
                <span className="map-stop__name">{stop.name}</span>
              </button>
            );
          })}
        </div>
      )}

      {coco && size.w > 0 && (
        <CocoActor
          state={{ ...offset(toScreen(coco.at), 0, -13), mode: coco.mode, facing: coco.facing, tilt: coco.tilt ?? 0, scale: 1 }}
          height={clamp(Math.min(size.w, size.h) * 0.15, 74, 128)}
          cue={coco.cue}
          still={reduced}
          className="ukmap__coco"
        />
      )}

      {overlay?.(toScreen, s)}

      {sel && selPos && (
        <MapCard
          key={sel.id}
          stopIndex={STOPS.indexOf(sel)}
          done={completed.includes(sel.id)}
          anchor={selPos}
          size={size}
          onClose={() => select(null)}
        />
      )}

      {interactive && (
        <div className="ukmap__ui">
          <button onClick={() => zoomAt(1.5, size.w / 2, size.h / 2)} aria-label="Zoom in">
            +
          </button>
          <button onClick={() => zoomAt(1 / 1.5, size.w / 2, size.h / 2)} aria-label="Zoom out">
            −
          </button>
          <button
            onClick={() => {
              setUserCam(null);
              select(null);
            }}
            aria-label="Reset the view"
            className="ukmap__reset"
          >
            <svg viewBox="0 0 24 24" width="18" height="18" aria-hidden>
              <path d="M12 5a7 7 0 1 1-6.6 4.7l1.9.6A5 5 0 1 0 12 7v3L7.5 6 12 2z" fill="currentColor" />
            </svg>
          </button>
        </div>
      )}

      <div className="ukmap__legend" style={{ opacity: oLabels }} aria-hidden>
        <svg className="ukmap__compass" viewBox="-20 -20 40 40" width="40" height="40">
          <circle r="17" fill="rgb(255 252 244 / 0.82)" stroke="rgb(28 38 51 / 0.35)" />
          <path d="M0-14 4 0H-4z" fill="#c8483e" />
          <path d="M0 14 4 0H-4z" fill="#33414f" />
          <text y="-6.5" textAnchor="middle" fontSize="7" fontWeight="700" fill="#fff" dy="-9">
            N
          </text>
        </svg>
        <div className="ukmap__scale">
          <span style={{ width: bar }} />
          <b>
            {nice} km · {Math.round(nice * 0.621)} mi
          </b>
        </div>
      </div>
      <p className="ukmap__credit">Natural Earth · AWS Terrain Tiles</p>
    </div>
  );
});

// ---- labels: placed in priority order, skipping any that would collide with one already placed

type Box = [number, number, number, number]; // x, y, w, h
const hits = (a: Box, b: Box, m = 4) => a[0] < b[0] + b[2] + m && b[0] < a[0] + a[2] + m && a[1] < b[1] + b[3] + m && b[1] < a[1] + a[3] + m;

function stopBox(stop: (typeof STOPS)[number], q: Pt): Box {
  const w = 30 + 7 + stop.name.length * 8.6 + 18;
  return stop.labelSide === 'left' ? [q.x - w + 15, q.y - 15, w, 30] : [q.x - 15, q.y - 15, w, 30];
}

function placeLabels({ cam, size, toScreen, stopBoxes }: { cam: MapCamera; size: { w: number; h: number }; toScreen: (p: Pt) => Pt; stopBoxes: Box[] }) {
  const narrow = size.w < 620;
  const taken: Box[] = [...stopBoxes];
  const out: ReactNode[] = [];
  const gate = (minZoom = 1) => clamp((cam.zoom - minZoom + 0.18) / 0.18);
  const visible = (b: Box) => b[0] + b[2] > -20 && b[1] + b[3] > -20 && b[0] < size.w + 20 && b[1] < size.h + 20;
  const place = (key: string, box: Box, node: (o: number) => ReactNode, opacity: number) => {
    if (opacity <= 0 || !visible(box) || taken.some((b) => hits(b, box))) return;
    taken.push(box);
    out.push(<Fragment key={key}>{node(opacity)}</Fragment>);
  };

  const countrySize = clamp(11 + cam.zoom * 2.4, narrow ? 11 : 12, 20);
  const countrySpacing = narrow ? 0.2 : 0.34;
  for (const l of COUNTRY_LABELS) {
    const p = toScreen(toMap(l.lonlat));
    const w = l.name.length * countrySize * (0.68 + countrySpacing);
    const h = countrySize * 1.25 + (l.uk ? 0 : 14);
    place(
      l.name,
      [p.x - w / 2, p.y - h / 2, w, h],
      () => (
        <span className={`map-label map-label--country${l.uk ? '' : ' map-label--ireland'}`} style={{ transform: `translate(${p.x}px, ${p.y}px) translate(-50%, -50%)`, fontSize: `${countrySize}px`, letterSpacing: `${countrySpacing}em` }}>
          {l.name}
          {!l.uk && <small>not part of the UK</small>}
        </span>
      ),
      1,
    );
  }
  for (const l of SEA_LABELS) {
    const p = toScreen(toMap(l.lonlat));
    const fs = narrow ? 11.5 : l.size === 'ocean' ? 15 : l.size === 'sea' ? 14 : 12;
    const ls = narrow ? 0.18 : l.size === 'ocean' ? 0.5 : l.size === 'sea' ? 0.32 : 0.22;
    const w = l.name.length * fs * (0.62 + ls);
    place(
      l.name,
      [p.x - w / 2, p.y - fs * 0.7, w, fs * 1.4],
      (o) => (
        <span className={`map-label map-label--sea map-label--${l.size}`} style={{ transform: `translate(${p.x}px, ${p.y}px) translate(-50%, -50%)`, opacity: o, fontSize: fs, letterSpacing: `${ls}em` }}>
          {l.name}
        </span>
      ),
      gate(l.minZoom),
    );
  }
  for (const c of CITIES) {
    const p = toScreen(toMap(c.lonlat));
    const w = 12 + c.name.length * 6.6;
    const left = c.align === 'left';
    place(
      c.name,
      [left ? p.x - w + 3.5 : p.x - 3.5, p.y - 8, w, 16],
      (o) => (
        <span className={`map-city map-city--${c.align ?? 'right'}`} style={{ transform: `translate(${p.x}px, ${p.y}px)`, opacity: o }}>
          <i />
          <b>{c.name}</b>
        </span>
      ),
      gate(c.minZoom),
    );
  }
  for (const l of [...ISLAND_LABELS, ...REGION_LABELS]) {
    const p = toScreen(toMap(l.lonlat));
    const w = l.name.length * 6.1;
    const align = l.align ?? 'center';
    const x = align === 'center' ? p.x - w / 2 : align === 'right' ? p.x + 4 : p.x - 4 - w;
    place(
      l.name,
      [x, p.y - 8, w, 16],
      (o) => (
        <span className={`map-label map-label--region map-label--${align}`} style={{ transform: `translate(${p.x}px, ${p.y}px)`, opacity: o }}>
          {l.name}
        </span>
      ),
      gate(l.minZoom) * (cam.zoom > 3.2 && !l.minZoom ? 0.6 : 1),
    );
  }
  return out;
}

// Ireland (the Republic) is lightly veiled so the United Kingdom reads as one country
const IRELAND_D = MAP.ireland;

const offset = (p: Pt, dx: number, dy: number): Pt => ({ x: p.x + dx, y: p.y + dy });

function CheckIcon() {
  return (
    <svg viewBox="0 0 16 16" width="13" height="13" aria-hidden>
      <path d="M3 8.5 6.4 12 13 4.5" fill="none" stroke="currentColor" strokeWidth="2.4" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

function MapCard({ stopIndex, done, anchor, size, onClose }: { stopIndex: number; done: boolean; anchor: Pt; size: { w: number; h: number }; onClose: () => void }) {
  const stop = STOPS[stopIndex];
  const narrow = size.w < 620;
  const right = anchor.x < size.w * 0.58;
  const style = narrow
    ? undefined
    : {
        left: right ? anchor.x + 34 : undefined,
        right: right ? undefined : size.w - anchor.x + 34,
        top: clamp(anchor.y - 90, 16, size.h - 330),
      };
  return (
    <aside className={`map-card${narrow ? ' map-card--sheet' : ''}`} style={style} role="dialog" aria-label={`${stop.name}, stop ${stopIndex + 1}`}>
      <button className="map-card__close" onClick={onClose} aria-label="Close">
        ×
      </button>
      <p className="map-card__kicker">
        Stop {stopIndex + 1} of {STOPS.length} · {stop.country}
        {done && <span className="map-card__done">Visited</span>}
      </p>
      <h3 className="map-card__title">{stop.name}</h3>
      <p className="map-card__blurb">{stop.blurb}</p>
      <p className="map-card__sub">You'll practise</p>
      <ul className="map-card__list">
        {stop.practise.map((p) => (
          <li key={p}>{p}</li>
        ))}
      </ul>
    </aside>
  );
}
