import type { SceneDef } from '../../scenes/types';
import './ui.css';

interface ControlsProps {
  scenes: SceneDef[];
  index: number;
  t: number;
  playing: boolean;
  sound: boolean;
  reduced: boolean;
  onGo: (i: number) => void;
  onPlay: (playing: boolean) => void;
  onSound: (on: boolean) => void;
  onReduced: (on: boolean) => void;
}

const Icon = ({ d, label }: { d: string; label: string }) => (
  <svg viewBox="0 0 24 24" width="20" height="20" aria-hidden focusable="false">
    <title>{label}</title>
    <path d={d} fill="currentColor" />
  </svg>
);

const ICONS = {
  prev: 'M15.4 5.4 9 12l6.4 6.6-1.4 1.4L6.2 12 14 4z',
  next: 'M8.6 18.6 15 12 8.6 5.4 10 4l7.8 8-7.8 8z',
  play: 'M8 5.5v13l10.5-6.5z',
  pause: 'M7 5h3.5v14H7zm6.5 0H17v14h-3.5z',
  soundOn: 'M4 9.5h3.5L12 5.5v13l-4.5-4H4zm11.2-1.7a5.5 5.5 0 0 1 0 8.4l-1.1-1.1a4 4 0 0 0 0-6.2zm2.4-2.4a8.8 8.8 0 0 1 0 13.2l-1.1-1.1a7.3 7.3 0 0 0 0-11z',
  soundOff: 'M4 9.5h3.5L12 5.5v13l-4.5-4H4zm11.3.2 1.1-1.1 2.3 2.3 2.3-2.3 1.1 1.1-2.3 2.3 2.3 2.3-1.1 1.1-2.3-2.3-2.3 2.3-1.1-1.1 2.3-2.3z',
  motion: 'M12 4a8 8 0 1 0 0 16 8 8 0 0 0 0-16zm0 1.6a6.4 6.4 0 0 1 0 12.8zM3 12h1.6M19.4 12H21',
};

export function Controls({ scenes, index, t, playing, sound, reduced, onGo, onPlay, onSound, onReduced }: ControlsProps) {
  const last = scenes.length - 1;
  return (
    <nav className="controls" aria-label="Story controls">
      <button className="controls__btn" onClick={() => onGo(index - 1)} disabled={index === 0} aria-label="Previous scene">
        <Icon d={ICONS.prev} label="Previous" />
      </button>
      <button className="controls__btn controls__btn--main" onClick={() => onPlay(!playing)} aria-label={playing ? 'Pause' : 'Play'}>
        <Icon d={playing ? ICONS.pause : ICONS.play} label={playing ? 'Pause' : 'Play'} />
      </button>
      <button className="controls__btn" onClick={() => onGo(index + 1)} disabled={index === last} aria-label="Next scene">
        <Icon d={ICONS.next} label="Next" />
      </button>
      <ol className="controls__progress">
        {scenes.map((s, i) => {
          const fill = i < index ? 1 : i > index ? 0 : Math.min(t / s.config.duration, 1);
          return (
            <li key={s.config.id}>
              <button
                className={`controls__seg${i === index ? ' is-current' : ''}`}
                onClick={() => onGo(i)}
                aria-label={`Scene ${i + 1}: ${s.config.title}`}
                aria-current={i === index ? 'step' : undefined}
              >
                <span style={{ transform: `scaleX(${fill})` }} />
              </button>
            </li>
          );
        })}
      </ol>
      <button className={`controls__btn${reduced ? ' is-on' : ''}`} onClick={() => onReduced(!reduced)} aria-pressed={reduced} aria-label="Reduce motion">
        <Icon d={ICONS.motion} label="Reduce motion" />
      </button>
      <button className={`controls__btn${sound ? ' is-on' : ''}`} onClick={() => onSound(!sound)} aria-pressed={sound} aria-label={sound ? 'Sound on' : 'Sound off'}>
        <Icon d={sound ? ICONS.soundOn : ICONS.soundOff} label={sound ? 'Sound on' : 'Sound off'} />
      </button>
    </nav>
  );
}
