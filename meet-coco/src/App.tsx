import { useCallback, useEffect, useRef, useState } from 'react';
import { setSoundEnabled, sound } from './audio/sound';
import { ViewportProvider } from './components/stage/Stage';
import { Caption } from './components/ui/Caption';
import { Controls } from './components/ui/Controls';
import { SCENES } from './scenes';
import { usePrefersReducedMotion, useSceneClock } from './lib/useStory';

const FADE = 0.9; // seconds of crossfade between scenes
const easeOut = (x: number) => 1 - (1 - x) ** 3;

// ?scene=4&t=6.5&pause=1&reduced=1 open the story at a given moment (handy for reviews)
const params = new URLSearchParams(window.location.search);
const START_SCENE = Math.min(Math.max(Number(params.get('scene') || 1) - 1, 0), SCENES.length - 1);
const START_T = Number(params.get('t') || 0);
const START_PAUSED = params.get('pause') === '1';
const FORCE_REDUCED = params.has('reduced') ? params.get('reduced') === '1' : null;

export default function App() {
  const [index, setIndex] = useState(START_SCENE);
  const [leaving, setLeaving] = useState<{ index: number; t: number } | null>(null);
  const [playing, setPlaying] = useState(!START_PAUSED);
  const [hold, setHold] = useState(false);
  const [soundOn, setSoundOn] = useState(false);
  const systemReduced = usePrefersReducedMotion();
  const [reducedPref, setReducedPref] = useState<boolean | null>(FORCE_REDUCED);
  const reduced = reducedPref ?? systemReduced;
  const [t, seek] = useSceneClock(index, playing, START_T);
  const tRef = useRef(t);
  tRef.current = t;

  const go = useCallback(
    (next: number, at = 0) => {
      if (next < 0 || next >= SCENES.length) return;
      setIndex((cur) => {
        if (cur !== next) setLeaving({ index: cur, t: tRef.current });
        return next;
      });
      setHold(false);
      seek(at);
    },
    [seek],
  );

  // the next scene starts when this one has played out (the map can hold it)
  const scene = SCENES[index];
  useEffect(() => {
    if (playing && !hold && t >= scene.config.duration && index < SCENES.length - 1) go(index + 1);
  }, [t, playing, hold, index, scene.config.duration, go]);

  // the outgoing scene stays under the incoming one until the crossfade is done
  useEffect(() => {
    if (leaving && t > FADE) setLeaving(null);
  }, [t, leaving]);

  useEffect(() => {
    sound.ambience(soundOn ? scene.ambience : null);
  }, [soundOn, scene.ambience]);

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.target instanceof HTMLElement && e.target.closest('input, textarea, [contenteditable]')) return;
      if (e.key === 'ArrowRight') go(index + 1);
      else if (e.key === 'ArrowLeft') go(index - 1);
      else if (e.key === ' ' && !(e.target instanceof HTMLButtonElement)) {
        e.preventDefault();
        setPlaying((p) => !p);
      } else if (e.key.toLowerCase() === 'm') toggleSound(!soundOn);
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  });

  // a small hook for automated reviews: window.__story.go(sceneIndex, t)
  useEffect(() => {
    (window as unknown as { __story: object }).__story = {
      go: (i: number, at = 0) => {
        go(i, at);
        setLeaving(null);
      },
      pause: () => setPlaying(false),
      play: () => setPlaying(true),
      get state() {
        return { index, t: tRef.current, playing, hold, reduced };
      },
    };
  });

  const toggleSound = (on: boolean) => {
    setSoundEnabled(on);
    setSoundOn(on);
  };

  const render = (i: number, time: number, active: boolean) => {
    const S = SCENES[i];
    const { Component, config } = S;
    const fadeIn = active && leaving ? Math.min(t / FADE, 1) : 1;
    // the incoming scene settles from a touch closer, the outgoing one drifts back
    const scale = reduced ? 1 : active ? 1 + 0.035 * (1 - easeOut(fadeIn)) : 1 - 0.02 * easeOut(Math.min(t / FADE, 1));
    return (
      <section
        key={config.id}
        className={`scene scene--${config.id}`}
        style={{ opacity: fadeIn, zIndex: active ? 2 : 1, transform: scale !== 1 ? `scale(${scale})` : undefined }}
        aria-hidden={!active}
        aria-label={active ? `Scene ${i + 1} of ${SCENES.length}: ${config.title}` : undefined}
      >
        <Component
          t={time}
          active={active}
          reduced={reduced}
          onHold={active ? setHold : undefined}
          onNext={active ? () => go(i + 1) : undefined}
          onRestart={active ? () => go(0) : undefined}
          onGo={active ? (n, at) => go(n, at ?? 0) : undefined}
        />
        <Caption lines={config.captions} t={time} place={config.captionPlace} tone={config.captionTone} until={config.duration - 0.7} reduced={reduced} />
      </section>
    );
  };

  return (
    <ViewportProvider>
      <main className="story">
        {leaving && leaving.index !== index && render(leaving.index, leaving.t, false)}
        {render(index, t, true)}
      </main>
      {hold && (
        <button className="continue" onClick={() => go(index + 1)}>
          Continue the story
          <svg viewBox="0 0 24 24" width="18" height="18" aria-hidden>
            <path d="M8.6 18.6 15 12 8.6 5.4 10 4l7.8 8-7.8 8z" fill="currentColor" />
          </svg>
        </button>
      )}
      <Controls
        scenes={SCENES}
        index={index}
        t={t}
        playing={playing}
        sound={soundOn}
        reduced={reduced}
        onGo={(i) => go(i)}
        onPlay={setPlaying}
        onSound={toggleSound}
        onReduced={(on) => setReducedPref(on)}
      />
    </ViewportProvider>
  );
}
