// Six travel moments, each a 600 x 400 illustration with its own light: the airport, a taxi in
// the rain, a café, a hotel, a landmark and a market street. Each exports the spots where Coco
// can stand.
import { memo, type ReactNode } from 'react';
import { rng } from '../lib/anim';
import { DAY } from './palette';
import { BigBen, LondonEye } from './london/Landmarks';
import { Person, Taxi, Tree } from './london/Street';

export const VW = 600;
export const VH = 400;

type V = { t: number; still?: boolean };

const Frame = ({ id, children }: { id: string; children: ReactNode }) => (
  <svg viewBox={`0 0 ${VW} ${VH}`} preserveAspectRatio="xMidYMid slice" aria-hidden>
    <defs>
      <clipPath id={`vclip-${id}`}>
        <rect width={VW} height={VH} />
      </clipPath>
    </defs>
    <g clipPath={`url(#vclip-${id})`}>{children}</g>
  </svg>
);

// ---------------------------------------------------------------- 1. airport and passport control

export const AIRPORT = { perch: { x: 432, y: 214 }, stamp: { x: 470, y: 236 } };

export const Airport = memo(function Airport({ t, still, stamp = 0 }: V & { stamp?: number }) {
  const time = still ? 0 : t;
  const planeX = 40 + ((time * 26) % 760) - 200;
  return (
    <Frame id="airport">
      <defs>
        <linearGradient id="ap-sky" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0" stopColor="#8fcbea" />
          <stop offset="1" stopColor="#e3f3f8" />
        </linearGradient>
        <linearGradient id="ap-floor" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0" stopColor="#dfe5ea" />
          <stop offset="1" stopColor="#c3ccd4" />
        </linearGradient>
      </defs>
      <rect width={VW} height={250} fill="url(#ap-sky)" />
      <rect y={196} width={VW} height={30} fill="#b8c6cf" />
      <rect y={214} width={VW} height={12} fill="#9fb0bb" />
      {/* a plane taxiing outside */}
      <g transform={`translate(${planeX} 196)`}>
        <path d="M0 -16 Q4 -26 30 -26 H150 Q166 -26 170 -16 Q166 -8 150 -8 H30 Q4 -8 0 -16Z" fill="#fbfbfb" />
        <path d="M120 -26 L150 -56 H162 L150 -26Z" fill="#2f6f9f" />
        <path d="M70 -14 L110 -2 H122 L96 -14Z" fill="#dfe6ec" />
        {Array.from({ length: 9 }).map((_, i) => (
          <circle key={i} cx={36 + i * 10} cy={-19} r={2} fill="#6d8aa0" />
        ))}
        <rect x={40} y={-6} width={4} height={6} fill="#555" />
        <rect x={120} y={-6} width={4} height={6} fill="#555" />
      </g>
      {/* the glass wall */}
      {Array.from({ length: 9 }).map((_, i) => (
        <rect key={i} x={i * 75 - 4} y={0} width={8} height={250} fill="#f4f8fa" />
      ))}
      <rect y={120} width={VW} height={5} fill="#f4f8fa" />
      <rect y={244} width={VW} height={10} fill="#e8eef2" />
      <rect y={250} width={VW} height={150} fill="url(#ap-floor)" />
      {Array.from({ length: 8 }).map((_, i) => (
        <rect key={i} x={i * 75 + 10} y={252} width={50} height={140} fill="#ffffff" opacity={0.25} />
      ))}
      {/* signs */}
      <g transform="translate(40 18)">
        <rect width={168} height={34} rx={4} fill="#1d2733" />
        <text x={12} y={23} fontFamily="var(--font-ui)" fontWeight={800} fontSize={15} fill="#ffd34d">
          ← Arrivals · Exit
        </text>
      </g>
      <g transform="translate(330 60)">
        <rect width={220} height={34} rx={4} fill="#ffd34d" />
        <text x={110} y={23} textAnchor="middle" fontFamily="var(--font-ui)" fontWeight={900} fontSize={14} letterSpacing={1.2} fill="#1d2733">
          PASSPORT CONTROL
        </text>
      </g>
      {/* queue belts */}
      {[60, 150, 240].map((x) => (
        <g key={x}>
          <rect x={x - 3} y={292} width={6} height={52} fill="#7c8791" />
          <rect x={x - 9} y={340} width={18} height={6} rx={3} fill="#5a636c" />
        </g>
      ))}
      <path d="M60 298 H240" stroke="#2d4f8a" strokeWidth={6} />
      {/* the booth */}
      <g transform="translate(400 222)">
        <rect x={0} y={0} width={180} height={150} fill="#3f5568" />
        <rect x={-6} y={-6} width={192} height={12} rx={3} fill="#d9dee3" />
        <rect x={10} y={-70} width={160} height={66} fill="#cfe8f3" opacity={0.55} stroke="#e9f4f8" strokeWidth={3} />
        <circle cx={120} cy={-36} r={18} fill="#d8a27c" />
        <path d="M100 -42 Q120 -66 140 -42Z" fill="#1d2b40" />
        <rect x={98} y={-48} width={44} height={6} rx={2} fill="#1d2b40" />
        <path d="M96 -6 Q120 -26 144 -6Z" fill="#1d2b40" />
      </g>
      {/* the passport being stamped */}
      <g transform={`translate(${AIRPORT.stamp.x} ${AIRPORT.stamp.y - 20})`}>
        <rect x={-30} y={-10} width={44} height={30} rx={3} fill="#6e1f2b" transform="rotate(-8)" />
        <g transform={`translate(26 ${-34 + 22 * stamp})`}>
          <rect x={-8} y={-26} width={16} height={22} rx={4} fill="#7a4b2a" />
          <rect x={-12} y={-6} width={24} height={8} rx={2} fill="#2b2f36" />
        </g>
      </g>
      {/* a traveller waiting */}
      <g transform="translate(150 340) scale(2.3)">
        <Person seed={3} />
      </g>
      <rect x={174} y={300} width={34} height={42} rx={5} fill="#cf4339" />
      <rect x={186} y={290} width={10} height={12} rx={2} fill="none" stroke="#555" strokeWidth={3} />
    </Frame>
  );
});

// ---------------------------------------------------------------- 2. a taxi in the rain

// the cab's rear passenger window (the cab is drawn at (150, 344), scaled 3.1)
export const TAXI = { window: { x: 264, y: 200, w: 64, h: 47 } };

export const TaxiRain = memo(function TaxiRain({ t, still }: V) {
  const time = still ? 0 : t;
  const r = rng(31);
  const drops = Array.from({ length: 70 }, () => ({ x: r() * 700 - 50, y: r() * 420, l: 10 + r() * 16, s: 260 + r() * 160 }));
  const shops = ['#f3c56a', '#ef9f5c', '#9fd3e0', '#f3c56a', '#e8b26a'];
  return (
    <Frame id="taxi">
      <defs>
        <linearGradient id="tx-sky" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0" stopColor="#2f3e55" />
          <stop offset="1" stopColor="#5c6c82" />
        </linearGradient>
        <linearGradient id="tx-road" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0" stopColor="#3a4352" />
          <stop offset="1" stopColor="#1f2530" />
        </linearGradient>
      </defs>
      <rect width={VW} height={VH} fill="url(#tx-sky)" />
      {/* terraced shopfronts */}
      {[0, 1, 2, 3, 4].map((i) => (
        <g key={i} transform={`translate(${i * 124 - 10} 40)`}>
          <rect width={120} height={210} fill={['#4b4f63', '#5a4c58', '#45556a', '#584a4f', '#4a5560'][i]} />
          {[0, 1].map((row) =>
            [0, 1, 2].map((c) => <rect key={`${row}${c}`} x={14 + c * 34} y={18 + row * 46} width={22} height={30} rx={2} fill={(i + row + c) % 3 === 0 ? '#f6cf7c' : '#2c3442'} opacity={0.9} />),
          )}
          <rect x={8} y={130} width={104} height={74} rx={3} fill={shops[i]} opacity={0.85} />
          <rect x={8} y={120} width={104} height={14} fill="#22293a" />
        </g>
      ))}
      <rect y={250} width={VW} height={18} fill="#6f7886" />
      <rect y={268} width={VW} height={132} fill="url(#tx-road)" />
      {/* reflections of the lit shops on the wet road */}
      {[0, 1, 2, 3, 4].map((i) => (
        <rect key={i} x={i * 124 + 6} y={270} width={96} height={120} fill={shops[i]} opacity={0.16} />
      ))}
      {Array.from({ length: 14 }).map((_, i) => (
        <rect key={i} x={20 + i * 44} y={300 + (i % 3) * 22} width={30} height={2} fill="#9fb3c8" opacity={0.25 + 0.2 * Math.sin(time * 2 + i)} />
      ))}
      {/* the cab */}
      <g transform="translate(150 344) scale(3.1)">
        <Taxi pal={{ ...DAY, name: 'rain' }} />
      </g>
      <path d="M470 316 L600 300 L600 340Z" fill="#fff6c8" opacity={0.25} />
      <rect x={140} y={348} width={330} height={10} fill="#000" opacity={0.25} />
      <rect x={150} y={360} width={320} height={40} fill="#23262c" opacity={0.35} />
      {/* someone under an umbrella */}
      <g transform="translate(70 262) scale(2.2)">
        <Person seed={9} umbrella phase={time * 3} />
      </g>
      {/* rain */}
      <g stroke="#cfe0ef" strokeWidth={1.4} opacity={0.55}>
        {drops.map((d, i) => {
          const y = (d.y + time * d.s) % 440 - 20;
          return <line key={i} x1={d.x + y * 0.18} y1={y} x2={d.x + (y + d.l) * 0.18} y2={y + d.l} />;
        })}
      </g>
    </Frame>
  );
});

// ---------------------------------------------------------------- 3. a café

export const CAFE = { perch: { x: 398, y: 318 }, cup: { x: 300, y: 312 } };

export const Cafe = memo(function Cafe({ t, still }: V) {
  const time = still ? 0 : t;
  return (
    <Frame id="cafe">
      <defs>
        <radialGradient id="cf-glow" cx="0.3" cy="0.1" r="0.9">
          <stop offset="0" stopColor="#ffd9a0" />
          <stop offset="1" stopColor="#b8703c" />
        </radialGradient>
      </defs>
      <rect width={VW} height={VH} fill="url(#cf-glow)" />
      <rect y={170} width={VW} height={100} fill="#8a4f2c" opacity={0.35} />
      {Array.from({ length: 12 }).map((_, i) => (
        <rect key={i} x={i * 52} y={170} width={3} height={100} fill="#5c3018" opacity={0.25} />
      ))}
      {/* window onto the street */}
      <rect x={40} y={40} width={200} height={124} rx={6} fill="#a9d1e2" />
      <rect x={40} y={110} width={200} height={54} fill="#cfc2a8" />
      <rect x={136} y={40} width={8} height={124} fill="#6b3c22" />
      <rect x={34} y={34} width={212} height={136} rx={8} fill="none" stroke="#6b3c22" strokeWidth={10} />
      <text x={140} y={84} textAnchor="middle" fontFamily="var(--font-display)" fontStyle="italic" fontWeight={600} fontSize={20} fill="#6b3c22" opacity={0.8}>
        Tea Room
      </text>
      {/* chalkboard */}
      <g transform="translate(300 40)">
        <rect width={150} height={110} rx={6} fill="#2e3a33" stroke="#8a5a34" strokeWidth={8} />
        <text x={75} y={30} textAnchor="middle" fontFamily="var(--font-hand)" fontSize={22} fill="#f6efe1">
          Today
        </text>
        {['Pot of tea  2.80', 'Scone  3.20', 'Toast  2.50'].map((l, i) => (
          <text key={l} x={14} y={56 + i * 18} fontFamily="var(--font-hand)" fontSize={16} fill="#f6efe1" opacity={0.9}>
            {l}
          </text>
        ))}
      </g>
      {/* pendant lamps */}
      {[500, 560].map((x, i) => (
        <g key={x}>
          <line x1={x} y1={0} x2={x} y2={60 + i * 16} stroke="#3a2416" strokeWidth={2} />
          <circle cx={x} cy={76 + i * 16} r={38} fill="#ffe2a2" opacity={0.25} />
          <path d={`M${x - 18} ${78 + i * 16} Q${x} ${50 + i * 16} ${x + 18} ${78 + i * 16}Z`} fill="#3a5a46" />
          <circle cx={x} cy={80 + i * 16} r={6} fill="#fff1c8" />
        </g>
      ))}
      {/* the cake counter */}
      <g transform="translate(470 196)">
        <rect width={140} height={90} fill="#f2e1c4" opacity={0.6} />
        <rect y={-4} width={140} height={6} fill="#6b3c22" />
        <path d="M14 40 a18 10 0 0 1 36 0 v14 h-36z" fill="#f3d4a0" />
        <rect x={14} y={44} width={36} height={6} fill="#d4475a" />
        <path d="M70 52 q16 -20 32 0z" fill="#e2a85e" />
        <path d="M108 52 q12 -18 24 0z" fill="#e2a85e" />
      </g>
      {/* the table */}
      <rect y={300} width={VW} height={100} fill="#6e3d22" />
      <rect y={300} width={VW} height={10} fill="#8c5634" />
      {/* teapot */}
      <g transform="translate(170 312)">
        <ellipse cx={0} cy={-34} rx={46} ry={38} fill="#f4f0e6" />
        <path d="M40 -44 q36 -6 34 -32" stroke="#f4f0e6" strokeWidth={9} fill="none" strokeLinecap="round" />
        <path d="M-44 -50 q-30 10 -6 34" stroke="#f4f0e6" strokeWidth={8} fill="none" />
        <ellipse cx={0} cy={-70} rx={22} ry={6} fill="#e8e1d2" />
        <circle cx={0} cy={-78} r={6} fill="#e8e1d2" />
        <path d="M-30 -30 h60" stroke="#3f6f9f" strokeWidth={4} opacity={0.6} />
        <ellipse cx={0} cy={0} rx={48} ry={6} fill="#000" opacity={0.15} />
      </g>
      {/* cup of tea with steam */}
      <g transform={`translate(${CAFE.cup.x} ${CAFE.cup.y})`}>
        <ellipse cx={0} cy={2} rx={44} ry={9} fill="#f4f0e6" />
        <path d="M-26 -34 h52 l-6 32 h-40z" fill="#f4f0e6" />
        <ellipse cx={0} cy={-34} rx={26} ry={6} fill="#8a4a22" />
        <path d="M26 -28 q16 2 12 14 q-4 8 -14 6" stroke="#f4f0e6" strokeWidth={5} fill="none" />
        {[0, 1].map((i) => {
          const k = ((time * 0.6 + i * 0.5) % 1);
          return <path key={i} d={`M${-6 + i * 12} ${-44 - k * 40} q8 -10 0 -20 q-8 -10 0 -20`} stroke="#fff" strokeWidth={4} fill="none" strokeLinecap="round" opacity={0.5 * Math.sin(k * Math.PI)} />;
        })}
      </g>
      {/* a scone with jam and cream */}
      <g transform="translate(470 318)">
        <ellipse rx={50} ry={10} fill="#f4f0e6" />
        <path d="M-26 -4 q0 -26 26 -26 q26 0 26 26z" fill="#d9a35c" />
        <path d="M-22 -18 q22 -10 44 0 q-22 6 -44 0z" fill="#fff6e2" />
        <path d="M-18 -24 q18 -8 36 0 q-18 5 -36 0z" fill="#b5283a" />
      </g>
    </Frame>
  );
});

// ---------------------------------------------------------------- 4. the hotel reception

export const HOTEL = { perch: { x: 300, y: 262 }, bell: { x: 250, y: 262 } };

export const Hotel = memo(function Hotel({ t, still }: V) {
  const time = still ? 0 : t;
  return (
    <Frame id="hotel">
      <defs>
        <linearGradient id="ht-wall" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0" stopColor="#1f4a3a" />
          <stop offset="1" stopColor="#163a2d" />
        </linearGradient>
        <linearGradient id="ht-marble" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0" stopColor="#f6f1e6" />
          <stop offset="1" stopColor="#dcd3c2" />
        </linearGradient>
      </defs>
      <rect width={VW} height={VH} fill="url(#ht-wall)" />
      {/* panelled walls with brass trim */}
      {[30, 170, 450].map((x) => (
        <rect key={x} x={x} y={40} width={120} height={150} fill="none" stroke="#c9a45a" strokeWidth={2} opacity={0.55} />
      ))}
      {/* key rack */}
      <g transform="translate(200 40)">
        <rect width={200} height={120} fill="#2a5b48" stroke="#c9a45a" strokeWidth={3} />
        {Array.from({ length: 4 }).map((_, row) =>
          Array.from({ length: 6 }).map((_, c) => (
            <g key={`${row}${c}`}>
              <rect x={8 + c * 32} y={8 + row * 28} width={26} height={22} fill="#1d4637" />
              {(row + c) % 3 !== 1 && <path d={`M${21 + c * 32} ${14 + row * 28} v10 m-3 -2 h6`} stroke="#e2c27a" strokeWidth={2} />}
            </g>
          )),
        )}
      </g>
      <text x={300} y={30} textAnchor="middle" fontFamily="var(--font-display)" fontWeight={600} fontSize={18} letterSpacing={6} fill="#e2c27a">
        RECEPTION
      </text>
      {/* wall lights */}
      {[90, 510].map((x) => (
        <g key={x}>
          <circle cx={x} cy={90} r={44} fill="#ffe0a0" opacity={0.18 + 0.03 * Math.sin(time * 2)} />
          <path d={`M${x - 10} 96 h20 l-4 -20 h-12z`} fill="#f6dfa4" />
          <rect x={x - 2} y={96} width={4} height={18} fill="#c9a45a" />
        </g>
      ))}
      {/* a palm */}
      <g transform="translate(560 300)">
        <rect x={-22} y={-40} width={44} height={40} rx={4} fill="#c9a45a" />
        {[-60, -30, 0, 30, 60].map((a) => (
          <path key={a} d="M0 -40 q10 -50 0 -100" stroke="#3f7a52" strokeWidth={9} fill="none" transform={`rotate(${a} 0 -40)`} strokeLinecap="round" />
        ))}
      </g>
      {/* receptionist */}
      <g transform="translate(330 230)">
        <path d="M-26 0 Q0 -40 26 0Z" fill="#14342a" />
        <circle cx={0} cy={-44} r={16} fill="#a86f4c" />
        <path d="M-16 -48 a16 16 0 0 1 32 0 q-16 -8 -32 0z" fill="#2a1d16" />
        <rect x={-6} y={-24} width={12} height={8} fill="#f6f1e6" />
      </g>
      {/* the desk */}
      <rect x={60} y={262} width={420} height={140} fill="#2b2f36" />
      <rect x={50} y={250} width={440} height={16} rx={3} fill="url(#ht-marble)" />
      <rect x={70} y={280} width={400} height={2} fill="#c9a45a" opacity={0.7} />
      {/* brass bell and a guest book */}
      <g transform={`translate(${HOTEL.bell.x} ${HOTEL.bell.y - 12})`}>
        <ellipse cx={0} cy={10} rx={18} ry={4} fill="#8a6a2a" />
        <path d="M-15 8 a15 15 0 0 1 30 0z" fill="#e2b85a" />
        <circle cx={0} cy={-8} r={3} fill="#e2b85a" />
      </g>
      <g transform="translate(140 236)">
        <rect width={70} height={14} rx={2} fill="#7a2230" transform="skewX(-20)" />
        <rect y={-3} width={70} height={4} fill="#f6f1e6" transform="skewX(-20)" />
      </g>
      {/* luggage trolley */}
      <g transform="translate(20 400)">
        <rect x={0} y={-130} width={6} height={130} fill="#c9a45a" />
        <path d="M0 -130 q40 -24 80 0" stroke="#c9a45a" strokeWidth={6} fill="none" />
        <rect x={74} y={-130} width={6} height={130} fill="#c9a45a" />
        <rect x={6} y={-74} width={56} height={46} rx={6} fill="#cf4339" />
        <rect x={12} y={-112} width={46} height={36} rx={6} fill="#2f6f8f" />
      </g>
    </Frame>
  );
});

// ---------------------------------------------------------------- 5. a landmark in bright sun

export const LANDMARK = { perch: { x: 420, y: 300 } };

export const Landmark = memo(function Landmark({ t, still }: V) {
  const time = still ? 0 : t;
  return (
    <Frame id="landmark">
      <defs>
        <linearGradient id="lm-sky" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0" stopColor="#4fa3df" />
          <stop offset="1" stopColor="#bfe3f4" />
        </linearGradient>
      </defs>
      <rect width={VW} height={VH} fill="url(#lm-sky)" />
      <circle cx={520} cy={60} r={70} fill="#fff6d0" opacity={0.6} />
      <circle cx={520} cy={60} r={30} fill="#fffbe8" />
      <g transform="translate(470 250) scale(0.55)">
        <LondonEye pal={DAY} angle={time * 2} />
      </g>
      <g transform="translate(170 300) scale(0.72)">
        <BigBen pal={DAY} minutes={12 * 60} />
      </g>
      <rect y={250} width={VW} height={60} fill="#5f9cbf" />
      {Array.from({ length: 8 }).map((_, i) => (
        <rect key={i} x={((i * 90 + time * 20) % 680) - 40} y={262 + (i % 3) * 14} width={50} height={2.4} fill="#fff" opacity={0.6} />
      ))}
      <rect y={300} width={VW} height={100} fill="#d8cdb6" />
      <rect y={300} width={VW} height={10} fill="#b9ad97" />
      {/* tourists taking a photo */}
      <g transform="translate(300 380) scale(2.4)">
        <Person seed={14} />
      </g>
      <g transform="translate(330 380) scale(-2.3 2.3)">
        <Person seed={22} />
      </g>
      <rect x={286} y={318} width={20} height={14} rx={3} fill="#2b2f36" />
      <circle cx={296} cy={325} r={4} fill="#8fc3d9" />
      {Math.sin(time * 2.4) > 0.96 && <circle cx={296} cy={320} r={18} fill="#fff" opacity={0.7} />}
      <g transform="translate(560 390)">
        <Tree pal={DAY} size={0.9} seed={8} />
      </g>
    </Frame>
  );
});

// ---------------------------------------------------------------- 6. markets and shops

export const MARKET = { sign: { x: 456, y: 96 }, signTop: { x: 470, y: 76 } };

export const Market = memo(function Market({ t, still }: V) {
  const time = still ? 0 : t;
  const fruit = ['#e4572e', '#f3a712', '#6aa84f', '#c13f5e', '#f2d24b'];
  const r = rng(17);
  return (
    <Frame id="market">
      <rect width={VW} height={VH} fill="#cfe7f0" />
      {/* shops */}
      {[
        { x: 0, w: 200, c: '#3d6f8f', name: 'BAKERY' },
        { x: 200, w: 200, c: '#8f3d4a', name: 'BOOKS' },
        { x: 400, w: 200, c: '#4c7a4c', name: 'FLOWERS' },
      ].map((s) => (
        <g key={s.name}>
          <rect x={s.x} y={20} width={s.w} height={250} fill={['#e9d5b5', '#d9b99a', '#e3cfae'][s.x / 200]} />
          {[0, 1].map((c) => (
            <rect key={c} x={s.x + 30 + c * 90} y={46} width={50} height={56} rx={3} fill="#4f6577" opacity={0.75} />
          ))}
          <rect x={s.x + 14} y={128} width={s.w - 28} height={30} fill={s.c} />
          <text x={s.x + s.w / 2} y={149} textAnchor="middle" fontFamily="var(--font-display)" fontWeight={700} fontSize={18} letterSpacing={3} fill="#fbf3e2">
            {s.name}
          </text>
          <rect x={s.x + 24} y={164} width={s.w - 48} height={106} fill="#f5d98f" opacity={0.75} />
        </g>
      ))}
      {/* the street sign Coco heads for */}
      <g transform={`translate(${MARKET.sign.x} ${MARKET.sign.y})`}>
        <rect x={-62} y={-20} width={124} height={40} rx={4} fill="#fbfbf7" stroke="#2b2f36" strokeWidth={3} />
        <text x={0} y={7} textAnchor="middle" fontFamily="var(--font-ui)" fontWeight={900} fontSize={16} letterSpacing={1} fill="#1d1f24">
          MARKET LANE
        </text>
        <text x={50} y={-6} textAnchor="middle" fontFamily="var(--font-ui)" fontWeight={900} fontSize={8} fill="#cf4339">
          W1
        </text>
      </g>
      {/* bunting */}
      <path d="M0 176 Q300 220 600 176" stroke="#555" strokeWidth={1.5} fill="none" />
      {Array.from({ length: 16 }).map((_, i) => {
        const x = 18 + i * 37;
        const y = 176 + Math.sin((x / 600) * Math.PI) * 44 * 0.5 + 3;
        return <path key={i} d={`M${x - 10} ${y} h20 l-10 ${16 + Math.sin(time * 3 + i) * 2}z`} fill={['#cf4339', '#f6f1e6', '#2f6f9f'][i % 3]} />;
      })}
      {/* market stalls */}
      {[30, 320].map((x, k) => (
        <g key={x} transform={`translate(${x} 250)`}>
          <path d={`M0 0 h250 l-12 -34 h-226z`} fill={k ? '#2f8f5b' : '#cf4339'} />
          {Array.from({ length: 6 }).map((_, i) => (
            <path key={i} d={`M${8 + i * 42} -34 h21 l4 34 h-21z`} fill="#fbf6ea" />
          ))}
          <rect x={10} y={0} width={6} height={110} fill="#6b4b36" />
          <rect x={234} y={0} width={6} height={110} fill="#6b4b36" />
          <rect x={0} y={74} width={250} height={36} fill="#b07a4a" />
          {Array.from({ length: 22 }).map((_, i) => (
            <circle key={i} cx={14 + (i % 11) * 22} cy={70 - Math.floor(i / 11) * 10 + r() * 3} r={9} fill={fruit[Math.floor(r() * fruit.length)]} />
          ))}
        </g>
      ))}
      <rect y={360} width={VW} height={40} fill="#b9ad97" />
      {[80, 220, 440].map((x, i) => (
        <g key={x} transform={`translate(${x + Math.sin(time * 0.8 + i) * 8} 392) scale(2.1)`}>
          <Person seed={30 + i} phase={time * 3 + i} />
        </g>
      ))}
    </Frame>
  );
});

export const VIGNETTES = [
  { id: 'airport', title: 'Airport & customs', phrase: "Here's my passport.", Component: Airport },
  { id: 'taxi', title: 'Taxi', phrase: 'Could you take me to Covent Garden, please?', Component: TaxiRain },
  { id: 'cafe', title: 'Café', phrase: 'A pot of tea and a scone, please.', Component: Cafe },
  { id: 'hotel', title: 'Hotel', phrase: 'Hi! I have a reservation for Coco.', Component: Hotel },
  { id: 'landmarks', title: 'Landmarks', phrase: 'Could you take a photo of us?', Component: Landmark },
  { id: 'city', title: 'Exploring the city', phrase: 'How much are the apples?', Component: Market },
] as const;
