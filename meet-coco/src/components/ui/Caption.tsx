import { fade, tween } from '../../lib/anim';
import type { CaptionLine } from '../../config/story';
import './ui.css';

interface CaptionProps {
  lines: CaptionLine[];
  t: number;
  place: 'top' | 'bottom' | 'center';
  tone?: 'light' | 'dark';
  /** hide the caption from this time on */
  until?: number;
  reduced?: boolean;
}

/** Story text: each line rises and fades in at its time. Screen readers get it as a live region. */
export function Caption({ lines, t, place, tone = 'light', until = Infinity, reduced }: CaptionProps) {
  if (!lines.length) return null;
  const visible = lines.filter((l) => t >= l.at - 0.05);
  const places = [...new Set(lines.map((l) => l.place ?? place))];
  return (
    <>
      <p className="sr-only" aria-live="polite">
        {visible.map((l) => l.text).join(' ')}
      </p>
      {places.map((where) => (
        <div key={where} className={`caption caption--${where}${tone === 'dark' && where !== 'center' ? ' caption--dark' : ''}${where !== place ? ' caption--accent' : ''}`}>
          {lines.filter((l) => (l.place ?? place) === where).map((line) => renderLine(line, t, until, reduced))}
        </div>
      ))}
    </>
  );
}

function renderLine(line: CaptionLine, t: number, until: number, reduced?: boolean) {
  const o = fade(t, line.at, 0.9, until, 0.6);
  const rise = reduced ? 0 : tween(t, line.at, 1.1, 14, 0, 'out');
  return (
    <p
      key={line.text}
      aria-hidden
      className={`caption__line${line.big ? ' caption__line--big' : ''}`}
      style={{ opacity: o, transform: `translateY(${rise}px)`, letterSpacing: line.big && !reduced ? `${tween(t, line.at, 1.6, 0.04, 0, 'out')}em` : undefined }}
    >
      {line.text}
    </p>
  );
}
