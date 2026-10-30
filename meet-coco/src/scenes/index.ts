import { STORY } from '../config/story';
import { S3Arrival } from './S3Arrival';
import { S4Map } from './S4Map';
import { S5London } from './S5London';
import { S6Experiences } from './S6Experiences';
import { S7LiveIt } from './S7LiveIt';
import { S8Journey } from './S8Journey';
import { S9Finale } from './S9Finale';
import { S1Journal, S2Meet } from './SDesk';
import type { SceneDef } from './types';

const byId = (id: string) => STORY.find((s) => s.id === id)!;

export const SCENES: SceneDef[] = [
  { config: byId('journal'), Component: S1Journal, ambience: 'desk' },
  { config: byId('meet'), Component: S2Meet, ambience: 'desk' },
  { config: byId('arrival'), Component: S3Arrival, ambience: 'city' },
  { config: byId('map'), Component: S4Map, ambience: 'sea' },
  { config: byId('london'), Component: S5London, ambience: 'city' },
  { config: byId('experiences'), Component: S6Experiences, ambience: 'cafe' },
  { config: byId('live-it'), Component: S7LiveIt, ambience: 'rain' },
  { config: byId('journey'), Component: S8Journey, ambience: 'sea' },
  { config: byId('finale'), Component: S9Finale, ambience: 'evening' },
];
