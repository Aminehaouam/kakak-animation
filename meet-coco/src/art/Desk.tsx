// The opening scene: a travel journal, a passport, a boarding pass, a paper map and a cup of tea
// on a wooden desk, seen from above.
import { memo } from 'react';
import { rng } from '../lib/anim';
import { MAP, ROUTE, STOP_POINTS } from '../components/map/geo';

export const DESK_W = 1600;
export const DESK_H = 1000;

/** The journal: spine at x = JOURNAL.x; each page is JOURNAL.w x JOURNAL.h. */
export const JOURNAL = { x: 760, y: 170, w: 440, h: 600, tilt: -2 };
export const TICKET = { x: 1205, y: 560, w: 380, h: 160, tilt: -8 };

/** A point on the ticket (in its own unrotated frame) as it lies on the desk. */
function onTicket(px: number, py: number) {
  const cx = TICKET.x + TICKET.w / 2;
  const cy = TICKET.y + TICKET.h / 2;
  const a = (TICKET.tilt * Math.PI) / 180;
  const dx = TICKET.x + px - cx;
  const dy = TICKET.y + py - cy;
  return { x: cx + dx * Math.cos(a) - dy * Math.sin(a), y: cy + dx * Math.sin(a) + dy * Math.cos(a) };
}

/** Points on the desk (stage units) the scenes use. */
export const DESK = {
  /** where Coco's ink silhouette stands on the right page */
  page: { x: JOURNAL.x + JOURNAL.w * 0.52, y: JOURNAL.y + JOURNAL.h * 0.78 },
  /** on the boarding pass, beside the word LONDON (so it stays readable) */
  ticket: onTicket(64, 104),
  journalCentre: { x: JOURNAL.x + 10, y: JOURNAL.y + JOURNAL.h / 2 },
};

/** `lift` scales how far the shadow falls: 1 for the journal and the documents, less for thin paper. */
function softShadow(x: number, y: number, w: number, h: number, r: number, tilt = 0, lift = 1) {
  return (
    <g transform={`rotate(${tilt} ${x + w / 2} ${y + h / 2})`}>
      {[22, 14, 7].map((s, i) => (
        <rect key={i} x={x + 10 * lift - (s * lift) / 2} y={y + 16 * lift - (s * lift) / 2} width={w + s * lift} height={h + s * lift} rx={r + (s * lift) / 2} fill="#240e02" opacity={0.07 + i * 0.03} />
      ))}
    </g>
  );
}

const Wood = memo(function Wood() {
  const r = rng(9);
  const grain = Array.from({ length: 70 }, (_, i) => {
    const y = (i / 70) * DESK_H + r() * 10;
    const amp = 3 + r() * 9;
    const ph = r() * 6;
    const pts = Array.from({ length: 17 }, (_, k) => `${k * 100},${(y + Math.sin(k * 0.7 + ph) * amp).toFixed(1)}`);
    return { d: 'M' + pts.join(' L'), o: 0.05 + r() * 0.1, w: 1 + r() * 2.5, dark: r() < 0.6 };
  });
  return (
    <g>
      <defs>
        <linearGradient id="wood" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0" stopColor="#a05f30" />
          <stop offset="0.5" stopColor="#8a4e24" />
          <stop offset="1" stopColor="#6c3919" />
        </linearGradient>
        <radialGradient id="lamp" cx="0.3" cy="0.22" r="0.85">
          <stop offset="0" stopColor="#ffd59a" stopOpacity="0.38" />
          <stop offset="0.45" stopColor="#ffc277" stopOpacity="0.12" />
          <stop offset="1" stopColor="#170903" stopOpacity="0.5" />
        </radialGradient>
      </defs>
      <rect width={DESK_W} height={DESK_H} fill="url(#wood)" />
      {grain.map((g, i) => (
        <path key={i} d={g.d} stroke={g.dark ? '#4a2309' : '#c7874d'} strokeWidth={g.w} opacity={g.o} fill="none" />
      ))}
      {[380, 860, 1340].map((x) => (
        <line key={x} x1={x} y1={0} x2={x + 6} y2={DESK_H} stroke="#3a1c09" strokeWidth={2} opacity={0.35} />
      ))}
      <ellipse cx={240} cy={720} rx={22} ry={9} fill="#4a2309" opacity={0.25} />
      <ellipse cx={1240} cy={180} rx={16} ry={7} fill="#4a2309" opacity={0.22} />
    </g>
  );
});

const PaperMap = memo(function PaperMap() {
  const w = 300;
  const h = 400;
  const k = Math.min((w - 40) / 879, (h - 50) / 1251);
  const london = STOP_POINTS.london;
  return (
    <g transform="translate(70 120) rotate(-7 150 200)">
      {softShadow(0, 0, w, h, 6)}
      <rect width={w} height={h} rx={4} fill="#f3ead6" />
      <g transform={`translate(${(w - 879 * k) / 2} 30) scale(${k})`}>
        <rect x={-20} y={-20} width={919} height={1291} fill="#cfe3e6" />
        <path d={MAP.landLow} fill="#cfdcb3" stroke="#6f93a4" strokeWidth={3.5} />
        <path d={MAP.ireland} fill="#efe8d4" opacity={0.6} />
        <path d={MAP.borders} fill="none" stroke="#a46a54" strokeWidth={3} strokeDasharray="10 7" />
        <path d={ROUTE.d()} fill="none" stroke="#cf4339" strokeWidth={6} strokeDasharray="14 10" strokeLinecap="round" />
        <circle cx={london.x} cy={london.y} r={14} fill="#cf4339" />
        <circle cx={london.x} cy={london.y} r={42} fill="none" stroke="#cf4339" strokeWidth={5} strokeDasharray="60 12" />
      </g>
      <text x={20} y={22} fontFamily="var(--font-display)" fontSize={15} fontWeight={600} fill="#4a3a2a" letterSpacing={2}>
        GREAT BRITAIN &amp; IRELAND
      </text>
      {/* creases */}
      <line x1={w / 2} y1={0} x2={w / 2} y2={h} stroke="#9c8a6a" strokeWidth={1.2} opacity={0.4} />
      <line x1={0} y1={h / 2} x2={w} y2={h / 2} stroke="#9c8a6a" strokeWidth={1.2} opacity={0.4} />
      <rect x={w / 2} y={0} width={w / 2} height={h / 2} fill="#000" opacity={0.04} />
      <rect x={0} y={h / 2} width={w / 2} height={h / 2} fill="#000" opacity={0.035} />
    </g>
  );
});

const Passport = memo(function Passport() {
  return (
    <g transform="translate(1290 90) rotate(9 115 150)">
      {softShadow(0, 0, 230, 310, 14)}
      <rect width={230} height={310} rx={14} fill="#6b0e22" />
      <rect x={10} y={10} width={210} height={290} rx={9} fill="none" stroke="#ebaf35" strokeWidth={1.4} opacity={0.6} />
      <circle cx={115} cy={150} r={44} fill="none" stroke="#ebaf35" strokeWidth={3} />
      <circle cx={115} cy={150} r={30} fill="none" stroke="#ebaf35" strokeWidth={2} />
      <path d="M85 150 h60 M115 120 q-22 30 0 60 q22 -30 0 -60" fill="none" stroke="#ebaf35" strokeWidth={2} />
      <text x={115} y={240} textAnchor="middle" fontFamily="var(--font-display)" fontWeight={600} fontSize={22} letterSpacing={5} fill="#e9c071">
        PASSPORT
      </text>
      <text x={115} y={60} textAnchor="middle" fontFamily="var(--font-ui)" fontWeight={700} fontSize={11} letterSpacing={3} fill="#e9c071" opacity={0.85}>
        TRAVEL DOCUMENT
      </text>
      <rect x={-4} y={190} width={60} height={42} rx={3} fill="#f6efe0" transform="rotate(-14 26 211)" />
      <text x={2} y={216} fontFamily="var(--font-hand)" fontSize={17} fill="#3d5a7a" transform="rotate(-14 26 211)">
        ✈ boarding
      </text>
    </g>
  );
});

const Ticket = memo(function Ticket() {
  const { x, y, w, h, tilt } = TICKET;
  const r = rng(4);
  return (
    <g transform={`translate(${x} ${y}) rotate(${tilt} ${w / 2} ${h / 2})`}>
      {softShadow(0, 0, w, h, 10)}
      <rect width={w} height={h} rx={10} fill="#fbf6ea" />
      <path d={`M0 10 a10 10 0 0 1 10 -10 H${w - 10} a10 10 0 0 1 10 10 V40 H0Z`} fill="#104b6b" />
      <text x={18} y={27} fontFamily="var(--font-ui)" fontWeight={800} fontSize={14} letterSpacing={3} fill="#fff">
        BOARDING PASS
      </text>
      <text x={w - 102} y={27} fontFamily="var(--font-ui)" fontWeight={700} fontSize={12} fill="#cfe3ee">
        FLIGHT CC 001
      </text>
      <text x={18} y={64} fontFamily="var(--font-ui)" fontWeight={700} fontSize={10} letterSpacing={1.5} fill="#7a8794">
        FROM
      </text>
      <text x={18} y={84} fontFamily="var(--font-ui)" fontWeight={800} fontSize={16} fill="#23303c">
        HOME
      </text>
      <path d="M86 78 h36 m-9 -7 9 7 -9 7" stroke="#cf4339" strokeWidth={2.4} fill="none" strokeLinecap="round" />
      <text x={136} y={64} fontFamily="var(--font-ui)" fontWeight={700} fontSize={10} letterSpacing={1.5} fill="#7a8794">
        TO
      </text>
      <text x={128} y={118} fontFamily="var(--font-display)" fontWeight={700} fontSize={40} letterSpacing={1.5} fill="#cf4339">
        LONDON
      </text>
      <text x={18} y={144} fontFamily="var(--font-ui)" fontWeight={700} fontSize={11} fill="#5b6773">
        GATE 12 · SEAT 7A · WINDOW
      </text>
      <line x1={w - 108} y1={46} x2={w - 108} y2={h - 8} stroke="#b9b2a1" strokeWidth={2} strokeDasharray="5 5" />
      {Array.from({ length: 30 }).map((_, i) => (
        <rect key={i} x={w - 92 + i * 2.6} y={56} width={r() < 0.5 ? 1.2 : 2} height={72} fill="#1b2935" />
      ))}
      <text x={w - 54} y={146} textAnchor="middle" fontFamily="var(--font-ui)" fontWeight={800} fontSize={12} fill="#23303c">
        LHR
      </text>
    </g>
  );
});

const Tea = memo(function Tea() {
  return (
    <g transform="translate(270 790)">
      <ellipse cx={8} cy={14} rx={118} ry={112} fill="#240e02" opacity={0.18} />
      <circle r={112} fill="#f7f3ec" />
      <circle r={96} fill="none" stroke="#155892" strokeWidth={3} opacity={0.5} />
      <circle r={74} fill="#fdfbf6" />
      <path d="M70 -14 q46 0 46 22 q0 22 -46 22" fill="none" stroke="#f1ece2" strokeWidth={14} />
      <circle r={60} fill="#9c551a" />
      <circle r={60} fill="none" stroke="#d7c7ad" strokeWidth={4} />
      <ellipse cx={-18} cy={-20} rx={24} ry={10} fill="#fff" opacity={0.22} transform="rotate(-30)" />
      <rect x={-150} y={70} width={70} height={22} rx={4} fill="#f0e2c6" transform="rotate(-24 -115 81)" />
    </g>
  );
});

const Pencil = memo(function Pencil() {
  return (
    <g transform="translate(560 860) rotate(-18)">
      <rect x={0} y={-9} width={230} height={18} rx={2} fill="#240e02" opacity={0.2} transform="translate(6 10)" />
      <rect x={0} y={-9} width={200} height={18} fill="#f3b537" />
      <rect x={0} y={-9} width={200} height={6} fill="#ffcf63" />
      <rect x={-26} y={-9} width={26} height={18} rx={4} fill="#f87f82" />
      <rect x={-6} y={-10} width={12} height={20} fill="#b9b9b9" />
      <path d="M200 -9 L232 0 L200 9Z" fill="#f8d697" />
      <path d="M222 -3 L232 0 L222 3Z" fill="#2c2c2c" />
    </g>
  );
});

const Stamps = memo(function Stamps() {
  return (
    <g>
      <g transform="translate(560 70) rotate(6)">
        {softShadow(0, 0, 84, 100, 2, 0, 0.4)}
        <rect width={84} height={100} fill="#fbf6ea" stroke="#d9cdb4" strokeDasharray="4 3" strokeWidth={3} />
        <rect x={9} y={9} width={66} height={70} fill="#da2925" />
        <circle cx={42} cy={44} r={18} fill="#fbf6ea" opacity={0.85} />
        <text x={42} y={92} textAnchor="middle" fontSize={10} fontWeight={800} fill="#23303c" fontFamily="var(--font-ui)">
          1st
        </text>
      </g>
      <g transform="translate(470 120) rotate(-10)">
        {softShadow(0, 0, 70, 86, 2, 0, 0.4)}
        <rect width={70} height={86} fill="#fbf6ea" stroke="#d9cdb4" strokeDasharray="4 3" strokeWidth={3} />
        <rect x={8} y={8} width={54} height={58} fill="#1b6c91" />
        <path d="M14 56 l14 -22 10 12 8 -10 12 20z" fill="#ecd998" />
      </g>
    </g>
  );
});

/** The open spread under the cover: notes and doodles on the left, the drawing page on the right. */
const Pages = memo(function Pages({ writing }: { writing: number }) {
  const { x, y, w, h } = JOURNAL;
  const lines = ['Day 1 — England!', 'Things to try:', '☐ a proper cup of tea', '☐ a red bus ride', '☐ say "cheers!"'];
  return (
    <g>
      <rect x={x - w} y={y} width={w * 2} height={h} rx={6} fill="#f6eedc" />
      <rect x={x - w} y={y} width={w} height={h} fill="url(#page-left)" />
      <rect x={x} y={y} width={w} height={h} fill="url(#page-right)" />
      {Array.from({ length: 16 }).map((_, i) => (
        <g key={i} stroke="#b7cde2" strokeWidth={1.2} opacity={0.55}>
          <line x1={x - w + 34} y1={y + 70 + i * 32} x2={x - 26} y2={y + 70 + i * 32} />
          <line x1={x + 26} y1={y + 70 + i * 32} x2={x + w - 34} y2={y + 70 + i * 32} />
        </g>
      ))}
      <line x1={x - w + 70} y1={y + 20} x2={x - w + 70} y2={y + h - 20} stroke="#f49c99" strokeWidth={1.6} opacity={0.6} />
      <defs>
        <clipPath id="write-clip">
          <rect x={x - w} y={y} width={w * Math.min(writing * 1.15, 1)} height={h} />
        </clipPath>
      </defs>
      <g clipPath="url(#write-clip)" fontFamily="var(--font-hand)" fill="#2c3e57">
        {lines.map((l, i) => (
          <text key={i} x={x - w + 84} y={y + 96 + i * 64} fontSize={i === 0 ? 38 : 31} fontWeight={i === 0 ? 700 : 500}>
            {l}
          </text>
        ))}
        {/* a little clock tower doodle */}
        <g transform={`translate(${x - 120} ${y + h - 70})`} stroke="#2c3e57" strokeWidth={2.4} fill="none" strokeLinecap="round">
          <path d="M-14 0 V-90 H14 V0 M-18 -90 H18 L0 -124Z M0 -72 m-9 0 a9 9 0 1 0 18 0 a9 9 0 1 0 -18 0 M0 -72 v-5 M0 -72 h4" />
          <path d="M-60 0 H60" />
        </g>
      </g>
      <rect x={x - 3} y={y} width={6} height={h} fill="#ccb993" opacity={0.6} />
    </g>
  );
});

export interface DeskProps {
  /** 0 closed .. 1 fully open */
  open: number;
  /** 0..1 handwriting on the left page */
  writing: number;
  /** 0..1 the elastic band sliding off */
  band: number;
  t: number;
}

export const Desk = memo(function Desk({ open, writing, band, t }: DeskProps) {
  const { x, y, w, h, tilt } = JOURNAL;
  const theta = open * Math.PI;
  const c = Math.cos(theta);
  const lift = Math.sin(theta);
  return (
    <svg viewBox={`0 0 ${DESK_W} ${DESK_H}`} preserveAspectRatio="xMidYMid slice" aria-hidden>
      <defs>
        <linearGradient id="page-left" x1="0" x2="1">
          <stop offset="0.75" stopColor="#000" stopOpacity="0" />
          <stop offset="1" stopColor="#7d5623" stopOpacity="0.18" />
        </linearGradient>
        <linearGradient id="page-right" x1="0" x2="1">
          <stop offset="0" stopColor="#7d5623" stopOpacity="0.2" />
          <stop offset="0.22" stopColor="#000" stopOpacity="0" />
        </linearGradient>
        <linearGradient id="cover" x1="0" x2="1" y1="0" y2="1">
          <stop offset="0" stopColor="#1b6a51" />
          <stop offset="1" stopColor="#114837" />
        </linearGradient>
      </defs>
      <Wood />
      <PaperMap />
      <Stamps />
      <Passport />
      <Tea />
      {/* steam over the tea */}
      {[0, 1, 2].map((i) => (
        <path
          key={i}
          d={`M${250 + i * 22} ${770 - ((t * 26 + i * 30) % 90)} q12 -16 0 -32 q-12 -16 0 -32`}
          stroke="#fff"
          strokeWidth={5}
          fill="none"
          strokeLinecap="round"
          opacity={0.18 * Math.sin((((t * 26 + i * 30) % 90) / 90) * Math.PI)}
        />
      ))}
      <Ticket />
      <Pencil />
      <g transform={`rotate(${tilt} ${x} ${y + h / 2})`}>
        {softShadow(x - w * Math.max(open * 1.2 - 0.2, 0), y, w + w * Math.max(open * 1.2 - 0.2, 0), h, 8)}
        {open > 0 ? <Pages writing={writing} /> : <rect x={x} y={y} width={w} height={h} fill="#f6eedc" />}
        {/* page block edge */}
        <rect x={x + w - 2} y={y + 4} width={8} height={h - 8} rx={2} fill="#e9dcc1" />
        {/* the cover swinging over the spine */}
        {c > -0.999 && (
          <g transform={`translate(${x} 0) scale(${c} 1) translate(${-x} 0)`}>
            {lift > 0.02 && c > 0 && <rect x={x} y={y + 8} width={w} height={h} fill="#240e02" opacity={0.2 * lift} />}
            <rect x={x} y={y - 6 * lift} width={w + 8} height={h + 12 * lift} rx={10} fill={c > 0 ? 'url(#cover)' : '#ebdcbc'} />
            {c > 0 && (
              <g>
                <rect x={x + 18} y={y + 18} width={w - 28} height={h - 36} rx={6} fill="none" stroke="#eac05c" strokeWidth={1.6} strokeDasharray="7 6" opacity={0.6} />
                <text x={x + w / 2} y={y + 180} textAnchor="middle" fontFamily="var(--font-display)" fontWeight={600} fontSize={46} fill="#e9c97f">
                  Travel
                </text>
                <text x={x + w / 2} y={y + 232} textAnchor="middle" fontFamily="var(--font-display)" fontWeight={600} fontSize={46} fill="#e9c97f">
                  Journal
                </text>
                <path d={`M${x + w / 2 - 50} ${y + 266} h100`} stroke="#e9c97f" strokeWidth={2} />
                <text x={x + w / 2} y={y + h - 70} textAnchor="middle" fontFamily="var(--font-hand)" fontSize={30} fill="#e9c97f" opacity={0.9}>
                  Coco &amp; me
                </text>
                <rect x={x + w - 64 + band * 90} y={y - 4} width={22} height={h + 8} rx={4} fill="#13161b" opacity={1 - band} />
              </g>
            )}
          </g>
        )}
        {/* ribbon bookmark */}
        <path d={`M${x + 120} ${y + h - 4} l0 70 l12 -12 l12 12 l0 -70`} fill="#d82825" />
      </g>
      <rect width={DESK_W} height={DESK_H} fill="url(#lamp)" />
    </svg>
  );
});
