// London landmarks drawn as flat, lightly shaded elevations. Each stands on its base at (0, 0)
// and rises into negative y; place it with a transform.
import { memo } from 'react';
import type { CityPalette } from '../palette';

type P = { pal: CityPalette };

/** The Elizabeth Tower (Big Ben): about 70 wide, 400 tall. The clock tells `minutes`. */
export const BigBen = memo(function BigBen({ pal, minutes = 600 }: P & { minutes?: number }) {
  const hour = ((minutes / 60) % 12) * 30;
  const min = (minutes % 60) * 6;
  const shaft = Array.from({ length: 7 });
  return (
    <g>
      {/* shaft */}
      <rect x={-26} y={-236} width={52} height={236} fill={pal.stone} />
      <rect x={10} y={-236} width={16} height={236} fill={pal.stoneShade} opacity={0.55} />
      {shaft.map((_, i) => (
        <g key={i} transform={`translate(0 ${-26 - i * 30})`}>
          <rect x={-19} y={-20} width={4} height={20} fill={pal.stoneShade} opacity={0.6} />
          <rect x={-8} y={-22} width={5} height={22} rx={2.5} fill={pal.window} opacity={0.75} />
          <rect x={3} y={-22} width={5} height={22} rx={2.5} fill={pal.window} opacity={0.75} />
          <rect x={15} y={-20} width={4} height={20} fill={pal.stoneShade} opacity={0.6} />
          <rect x={-24} y={-2} width={48} height={2} fill={pal.stoneLight} opacity={0.6} />
        </g>
      ))}
      {/* clock stage */}
      <rect x={-33} y={-300} width={66} height={64} fill={pal.stone} />
      <rect x={14} y={-300} width={19} height={64} fill={pal.stoneShade} opacity={0.5} />
      <rect x={-35} y={-240} width={70} height={5} fill={pal.gold} />
      <rect x={-35} y={-302} width={70} height={5} fill={pal.gold} />
      <circle cx={0} cy={-268} r={25} fill={pal.gold} />
      <circle cx={0} cy={-268} r={21.5} fill={pal.name === 'sunset' ? '#fff3d6' : '#fbf7ea'} />
      {Array.from({ length: 12 }).map((_, i) => (
        <rect key={i} x={-1} y={-288} width={2} height={4.5} fill={pal.ink} transform={`rotate(${i * 30} 0 -268)`} />
      ))}
      <rect x={-1.4} y={-280} width={2.8} height={12} rx={1.4} fill={pal.ink} transform={`rotate(${hour} 0 -268)`} />
      <rect x={-1} y={-286} width={2} height={18} rx={1} fill={pal.ink} transform={`rotate(${min} 0 -268)`} />
      <circle cx={0} cy={-268} r={2.2} fill={pal.gold} />
      {/* belfry */}
      <rect x={-29} y={-334} width={58} height={34} fill={pal.stone} />
      {[-18, -6, 6].map((x) => (
        <path key={x} d={`M${x} -304v-20a6 6 0 0 1 12 0v20z`} fill={pal.window} opacity={0.85} />
      ))}
      <rect x={-31} y={-337} width={62} height={4} fill={pal.gold} />
      {/* spire */}
      <path d="M-30 -337 L0 -398 L30 -337Z" fill={pal.roof} />
      <path d="M0 -398 L30 -337 H12Z" fill="#000" opacity={0.18} />
      <path d="M-14 -345 L0 -372 L14 -345Z" fill={pal.gold} opacity={0.85} />
      {[-30, 30].map((x) => (
        <path key={x} d={`M${x - 4} -337 L${x} -362 L${x + 4} -337Z`} fill={pal.roof} />
      ))}
      <rect x={-1.5} y={-418} width={3} height={22} fill={pal.gold} />
      <circle cx={0} cy={-418} r={3} fill={pal.gold} />
    </g>
  );
});

/** The Palace of Westminster's river front: `width` long, with Victoria Tower at the far end. */
export const Parliament = memo(function Parliament({ pal, width = 640 }: P & { width?: number }) {
  const bays = Math.floor(width / 32);
  return (
    <g>
      {/* Victoria Tower */}
      <g transform="translate(40 0)">
        <rect x={-38} y={-300} width={76} height={300} fill={pal.stone} />
        <rect x={14} y={-300} width={24} height={300} fill={pal.stoneShade} opacity={0.5} />
        {Array.from({ length: 6 }).map((_, i) => (
          <g key={i}>
            <path d={`M-14 ${-40 - i * 42}v-24a7 7 0 0 1 14 0v24z`} fill={pal.window} opacity={0.75} />
            <path d={`M4 ${-40 - i * 42}v-24a7 7 0 0 1 14 0v24z`} fill={pal.window} opacity={0.75} />
          </g>
        ))}
        {[-38, 38].map((x) => (
          <g key={x}>
            <rect x={x - 6} y={-322} width={12} height={22} fill={pal.stone} />
            <path d={`M${x - 6} -322 L${x} -346 L${x + 6} -322Z`} fill={pal.roof} />
          </g>
        ))}
        <rect x={-40} y={-304} width={80} height={5} fill={pal.gold} />
        <rect x={-1} y={-372} width={2} height={50} fill={pal.ink} />
        <path d="M1 -372 h22 v13 h-22z" fill={pal.red} />
        <path d="M1 -372 l22 13 M23 -372 l-22 13" stroke="#fff" strokeWidth={2} />
        <path d="M12 -372 v13 M1 -365.5 h22" stroke="#fff" strokeWidth={3.2} />
        <path d="M12 -372 v13 M1 -365.5 h22" stroke={pal.red} strokeWidth={1.6} />
      </g>
      {/* the long front */}
      <rect x={70} y={-112} width={width - 70} height={112} fill={pal.stone} />
      <rect x={70} y={-30} width={width - 70} height={30} fill={pal.stoneShade} opacity={0.45} />
      {Array.from({ length: bays }).map((_, i) => {
        const x = 78 + i * 32;
        if (x > width - 16) return null;
        const tall = i % 5 === 2;
        return (
          <g key={i}>
            <rect x={x - 2} y={tall ? -140 : -126} width={4} height={tall ? 140 : 126} fill={pal.stoneLight} opacity={0.7} />
            <path d={`M${x - 3} ${tall ? -140 : -126} L${x} ${tall ? -156 : -138} L${x + 3} ${tall ? -140 : -126}Z`} fill={pal.roof} />
            {[-96, -64, -32].map((y) => (
              <path key={y} d={`M${x + 8} ${y + 22}v-16a5 5 0 0 1 10 0v16z`} fill={pal.window} opacity={0.72} />
            ))}
          </g>
        );
      })}
      <rect x={70} y={-116} width={width - 70} height={6} fill={pal.roof} />
      {/* central lantern */}
      <g transform={`translate(${width * 0.55} -112)`}>
        <rect x={-14} y={-60} width={28} height={60} fill={pal.stone} />
        <path d="M-16 -60 L0 -118 L16 -60Z" fill={pal.roof} />
        <rect x={-1} y={-130} width={2} height={14} fill={pal.gold} />
      </g>
    </g>
  );
});

/** The London Eye: rim radius 200; `angle` turns the wheel (degrees). */
export const LondonEye = memo(function LondonEye({ pal, angle = 0 }: P & { angle?: number }) {
  const R = 200;
  const n = 32;
  const hubY = -R - 34;
  return (
    <g>
      {/* the A-frame leaning in from the bank, with its back-stays */}
      <path d={`M0 ${hubY} L-70 0 M0 ${hubY} L-34 0`} stroke={pal.glassLight} strokeWidth={6} strokeLinecap="round" />
      <path d={`M-70 0 L-34 0 M-62 -60 L-38 -60 M-54 -120 L-40 -120`} stroke={pal.glassLight} strokeWidth={3} />
      <path d={`M0 ${hubY} L-150 -6`} stroke={pal.glassLight} strokeWidth={1.4} opacity={0.8} />
      <g transform={`translate(0 ${hubY}) rotate(${angle})`}>
        <circle r={R} fill="none" stroke={pal.glassLight} strokeWidth={5} />
        <circle r={R - 9} fill="none" stroke={pal.glassLight} strokeWidth={2} opacity={0.8} />
        {Array.from({ length: n }).map((_, i) => {
          const a = (i / n) * Math.PI * 2;
          return <line key={i} x1={0} y1={0} x2={Math.cos(a) * (R - 9)} y2={Math.sin(a) * (R - 9)} stroke={pal.glassLight} strokeWidth={1.1} opacity={0.75} />;
        })}
      </g>
      {/* capsules hang level as the wheel turns */}
      {Array.from({ length: n }).map((_, i) => {
        const a = (i / n) * Math.PI * 2 + (angle * Math.PI) / 180;
        const x = Math.cos(a) * (R + 9);
        const y = hubY + Math.sin(a) * (R + 9);
        return (
          <g key={i} transform={`translate(${x} ${y})`}>
            <rect x={-8} y={-5.5} width={16} height={11} rx={5.5} fill={pal.glass} stroke={pal.glassLight} strokeWidth={1.2} />
            <rect x={-6} y={-3.5} width={12} height={3} rx={1.5} fill={pal.glassLight} opacity={0.7} />
          </g>
        );
      })}
      <circle cx={0} cy={hubY} r={14} fill={pal.glassLight} />
      <circle cx={0} cy={hubY} r={7} fill={pal.ink} opacity={0.6} />
      <rect x={-96} y={-8} width={124} height={8} fill={pal.wall} />
    </g>
  );
});

/** Tower Bridge: span of 520 between the outer piers; the deck sits at y = 0. */
export const TowerBridge = memo(function TowerBridge({ pal, lift = 0 }: P & { lift?: number }) {
  const tower = (x: number) => (
    <g transform={`translate(${x} 0)`}>
      <rect x={-34} y={-210} width={68} height={250} fill={pal.stone} />
      <rect x={10} y={-210} width={24} height={250} fill={pal.stoneShade} opacity={0.5} />
      {[-168, -120, -72].map((y) => (
        <g key={y}>
          <path d={`M-16 ${y + 30}v-20a6 6 0 0 1 12 0v20z`} fill={pal.window} opacity={0.8} />
          <path d={`M4 ${y + 30}v-20a6 6 0 0 1 12 0v20z`} fill={pal.window} opacity={0.8} />
        </g>
      ))}
      <path d="M-30 -26 h60 v-24 a30 30 0 0 0 -60 0z" fill={pal.water[2]} opacity={0.55} />
      {[-34, 34].map((tx) => (
        <g key={tx}>
          <rect x={tx - 8} y={-236} width={16} height={28} fill={pal.stone} />
          <path d={`M${tx - 9} -236 L${tx} -262 L${tx + 9} -236Z`} fill={pal.roof} />
          <rect x={tx - 1} y={-270} width={2} height={10} fill={pal.gold} />
        </g>
      ))}
      <path d="M-24 -210 L0 -258 L24 -210Z" fill={pal.roof} />
      <rect x={-1} y={-272} width={2} height={16} fill={pal.gold} />
      <rect x={-36} y={-214} width={72} height={6} fill={pal.gold} opacity={0.8} />
      <rect x={-40} y={30} width={80} height={14} fill={pal.wall} />
    </g>
  );
  const blue = pal.name === 'sunset' ? '#749cd0' : '#489ddf';
  return (
    <g>
      {/* suspension chains to the banks */}
      <path d="M-34 -150 Q-150 -40 -260 -10" fill="none" stroke={blue} strokeWidth={9} />
      <path d="M554 -150 Q670 -40 780 -10" fill="none" stroke={blue} strokeWidth={9} />
      {Array.from({ length: 9 }).map((_, i) => (
        <g key={i} stroke={blue} strokeWidth={2.2}>
          <line x1={-60 - i * 22} y1={-125 + i * 13} x2={-60 - i * 22} y2={-2} />
          <line x1={580 + i * 22} y1={-125 + i * 13} x2={580 + i * 22} y2={-2} />
        </g>
      ))}
      <rect x={-270} y={-10} width={240} height={12} fill={pal.wall} />
      <rect x={550} y={-10} width={240} height={12} fill={pal.wall} />
      {/* high walkways */}
      {[-192, -170].map((y) => (
        <g key={y}>
          <rect x={0} y={y} width={520} height={14} fill={blue} />
          {Array.from({ length: 26 }).map((_, i) => (
            <line key={i} x1={10 + i * 20} y1={y + 1} x2={20 + i * 20} y2={y + 13} stroke="#fff" strokeWidth={1.6} opacity={0.55} />
          ))}
        </g>
      ))}
      {/* the bascules (they lift for tall ships) */}
      <g transform={`rotate(${-lift} 34 -6)`}>
        <rect x={34} y={-12} width={226} height={12} fill={pal.road} />
        <rect x={34} y={-14} width={226} height={3} fill={blue} />
      </g>
      <g transform={`rotate(${lift} 486 -6)`}>
        <rect x={260} y={-12} width={226} height={12} fill={pal.road} />
        <rect x={260} y={-14} width={226} height={3} fill={blue} />
      </g>
      {tower(0)}
      {tower(520)}
    </g>
  );
});

/** 30 St Mary Axe (the Gherkin): 70 wide, 230 tall. */
export const Gherkin = memo(function Gherkin({ pal }: P) {
  const d = 'M0 -232 C30 -228 42 -160 40 -100 C38 -50 26 -12 20 0 H-20 C-26 -12 -38 -50 -40 -100 C-42 -160 -30 -228 0 -232Z';
  return (
    <g>
      <defs>
        <clipPath id="gherkin-clip">
          <path d={d} />
        </clipPath>
      </defs>
      <path d={d} fill={pal.glass} />
      <g clipPath="url(#gherkin-clip)">
        <rect x={0} y={-240} width={44} height={240} fill={pal.glassShade} opacity={0.55} />
        {Array.from({ length: 16 }).map((_, i) => (
          <g key={i} stroke={pal.glassShade} strokeWidth={1.6} opacity={0.75}>
            <line x1={-60} y1={-260 + i * 22} x2={60} y2={-200 + i * 22} />
            <line x1={60} y1={-260 + i * 22} x2={-60} y2={-200 + i * 22} />
          </g>
        ))}
        <path d="M-30 -200 C-36 -150 -36 -60 -22 0" stroke={pal.glassLight} strokeWidth={5} fill="none" opacity={0.6} />
      </g>
    </g>
  );
});

/** The Shard: 110 wide, 360 tall. */
export const Shard = memo(function Shard({ pal }: P) {
  return (
    <g>
      <path d="M-55 0 L-6 -350 L2 -362 L6 -340 L55 0Z" fill={pal.glass} />
      <path d="M2 -362 L6 -340 L55 0 H8Z" fill={pal.glassShade} opacity={0.7} />
      <path d="M-55 0 L-6 -350 L-14 0Z" fill={pal.glassLight} opacity={0.45} />
      {Array.from({ length: 14 }).map((_, i) => {
        const y = -20 - i * 24;
        const half = 55 * (1 + y / 360);
        return <line key={i} x1={-half} y1={y} x2={half} y2={y} stroke={pal.glassShade} strokeWidth={1} opacity={0.4} />;
      })}
    </g>
  );
});

/** St Paul's Cathedral: dome and west towers, 260 wide, 250 tall. */
export const StPauls = memo(function StPauls({ pal }: P) {
  return (
    <g>
      <rect x={-130} y={-80} width={260} height={80} fill={pal.stoneLight} />
      <rect x={-130} y={-24} width={260} height={24} fill={pal.stoneShade} opacity={0.35} />
      {[-110, 110].map((x) => (
        <g key={x}>
          <rect x={x - 18} y={-150} width={36} height={70} fill={pal.stoneLight} />
          <path d={`M${x - 18} -150 Q${x} -190 ${x + 18} -150Z`} fill={pal.roof} />
          <rect x={x - 1} y={-200} width={2} height={14} fill={pal.gold} />
        </g>
      ))}
      <rect x={-60} y={-140} width={120} height={60} fill={pal.stoneLight} />
      {Array.from({ length: 9 }).map((_, i) => (
        <rect key={i} x={-54 + i * 13} y={-136} width={5} height={50} fill={pal.stoneShade} opacity={0.45} />
      ))}
      <path d="M-62 -140 A62 70 0 0 1 62 -140Z" fill={pal.roof} />
      <path d="M0 -210 A62 70 0 0 1 62 -140 H30 A40 60 0 0 0 0 -210Z" fill="#000" opacity={0.15} />
      <rect x={-9} y={-232} width={18} height={24} fill={pal.stoneLight} />
      <circle cx={0} cy={-238} r={7} fill={pal.gold} />
      <rect x={-1} y={-256} width={2} height={14} fill={pal.gold} />
    </g>
  );
});
