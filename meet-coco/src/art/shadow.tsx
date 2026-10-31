// Soft shadows for the illustrations: a few flat shapes stacked at low opacity, so an edge fades
// out without a gradient or a blur. The light comes from the upper left, as in the existing
// shading, so shadows lean a little to the right and down.

interface ContactProps {
  cx: number;
  cy: number;
  rx: number;
  ry: number;
  color: string;
  /** 1 = the standard soft contact shadow */
  strength?: number;
}

/** A soft contact shadow where something meets the ground. */
export function Contact({ cx, cy, rx, ry, color, strength = 1 }: ContactProps) {
  return (
    <g fill={color}>
      <ellipse cx={cx} cy={cy} rx={rx} ry={ry} fillOpacity={0.07 * strength} />
      <ellipse cx={cx} cy={cy} rx={rx * 0.8} ry={ry * 0.72} fillOpacity={0.08 * strength} />
      <ellipse cx={cx} cy={cy} rx={rx * 0.58} ry={ry * 0.48} fillOpacity={0.1 * strength} />
    </g>
  );
}

/** A soft shadow behind a raised rectangle (a sign, a board, a frame), cast down and right. */
export function Drop({ x, y, w, h, r = 0, color, dx = 4, dy = 6, spread = 10, strength = 1 }: { x: number; y: number; w: number; h: number; r?: number; color: string; dx?: number; dy?: number; spread?: number; strength?: number }) {
  return (
    <g fill={color}>
      {[1, 0.6, 0.3].map((k, i) => (
        <rect key={i} x={x + dx - (spread * k) / 2} y={y + dy - (spread * k) / 2} width={w + spread * k} height={h + spread * k} rx={r + (spread * k) / 2} fillOpacity={(0.05 + i * 0.02) * strength} />
      ))}
    </g>
  );
}

/** A soft band of shade just under an overhang (an awning, a counter's lip, a kerb). */
export function Band({ x, y, w, h, color, strength = 1 }: { x: number; y: number; w: number; h: number; color: string; strength?: number }) {
  return (
    <g fill={color}>
      <rect x={x} y={y} width={w} height={h} fillOpacity={0.06 * strength} />
      <rect x={x} y={y} width={w} height={h * 0.62} fillOpacity={0.06 * strength} />
      <rect x={x} y={y} width={w} height={h * 0.3} fillOpacity={0.06 * strength} />
    </g>
  );
}
