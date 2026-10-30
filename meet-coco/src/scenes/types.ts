import type { ComponentType } from 'react';
import type { Ambience } from '../audio/sound';
import type { SceneConfig } from '../config/story';

export interface SceneProps {
  /** seconds since the scene started (frozen while it fades out) */
  t: number;
  /** the scene is current (false while it fades out behind the next one) */
  active: boolean;
  /** reduced motion: no camera moves or flights, gentle fades instead */
  reduced: boolean;
  /** the scene asks the story to wait (e.g. while someone explores the map) */
  onHold?: (hold: boolean) => void;
  onNext?: () => void;
  onRestart?: () => void;
  /** jump to a scene (0-based) at a time */
  onGo?: (index: number, t?: number) => void;
}

export interface SceneDef {
  config: SceneConfig;
  Component: ComponentType<SceneProps>;
  ambience: Ambience;
}
