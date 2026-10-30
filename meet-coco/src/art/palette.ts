// Colour sets for the illustrated scenes. Every London piece takes a palette, so the same city
// draws in daylight, at sunset or in the rain.

export interface CityPalette {
  name: 'day' | 'sunset' | 'rain';
  sky: [string, string, string];
  sun: string;
  sunGlow: string;
  cloud: string;
  cloudShade: string;
  haze: string;
  hazeFar: string;
  stone: string;
  stoneShade: string;
  stoneLight: string;
  roof: string;
  gold: string;
  glass: string;
  glassShade: string;
  glassLight: string;
  brick: string[];
  window: string;
  windowLit: string;
  /** share of windows lit */
  lit: number;
  water: [string, string, string];
  waterLine: string;
  wall: string;
  wallTop: string;
  pavement: string;
  road: string;
  roadLine: string;
  tree: [string, string, string];
  trunk: string;
  red: string;
  redShade: string;
  black: string;
  ink: string;
  /** 0 = flat daylight, 1 = low warm sun from the right */
  warmth: number;
}

export const DAY: CityPalette = {
  name: 'day',
  sky: ['#6fb7e4', '#a9d8f0', '#e8f4f2'],
  sun: '#fff6d8',
  sunGlow: 'rgba(255, 244, 210, 0.55)',
  cloud: '#ffffff',
  cloudShade: '#dbe9f3',
  haze: '#a9c3d6',
  hazeFar: '#c4d7e4',
  stone: '#dcc79e',
  stoneShade: '#b9a274',
  stoneLight: '#efe0bd',
  roof: '#4c5866',
  gold: '#e1b04a',
  glass: '#8fc3d9',
  glassShade: '#5f97b3',
  glassLight: '#d6eef5',
  brick: ['#b8644c', '#c98a62', '#d9b48a', '#e7d6b8', '#9f5a48', '#c7c2b4'],
  window: '#4f6577',
  windowLit: '#ffd789',
  lit: 0.04,
  water: ['#5f9cbf', '#4a87ad', '#3a7299'],
  waterLine: 'rgba(255,255,255,0.55)',
  wall: '#b9ad97',
  wallTop: '#d8cfbd',
  pavement: '#cfc6b4',
  road: '#5c6168',
  roadLine: '#f1ead9',
  tree: ['#6fa45a', '#4f8a4a', '#3b6f3e'],
  trunk: '#6b4b36',
  red: '#d6382f',
  redShade: '#a82822',
  black: '#23262c',
  ink: '#1d2733',
  warmth: 0,
};

export const SUNSET: CityPalette = {
  name: 'sunset',
  sky: ['#36406f', '#c76a73', '#ffb36b'],
  sun: '#fff0c4',
  sunGlow: 'rgba(255, 190, 110, 0.6)',
  cloud: '#f7b08a',
  cloudShade: '#a0607a',
  haze: '#7d5a78',
  hazeFar: '#a9707e',
  stone: '#e3a873',
  stoneShade: '#9c6458',
  stoneLight: '#ffcf8f',
  roof: '#3d3450',
  gold: '#ffd07a',
  glass: '#e79a7f',
  glassShade: '#8a5a72',
  glassLight: '#ffd5a8',
  brick: ['#9a4f4c', '#b0695b', '#c08a72', '#d2a585', '#7f4448', '#a2867f'],
  window: '#4b3a55',
  windowLit: '#ffd27c',
  lit: 0.42,
  water: ['#e39a7c', '#a8617a', '#4f4a74'],
  waterLine: 'rgba(255,214,160,0.75)',
  wall: '#7e6070',
  wallTop: '#a57f82',
  pavement: '#8c6c74',
  road: '#463c4f',
  roadLine: '#e8c49c',
  tree: ['#6a6a58', '#4f5650', '#3d4448'],
  trunk: '#3e2f36',
  red: '#d2463c',
  redShade: '#8f2d33',
  black: '#1e1b26',
  ink: '#1e1b26',
  warmth: 1,
};

export const RAIN: CityPalette = {
  ...DAY,
  name: 'rain',
  sky: ['#59677a', '#7b8899', '#a3adb8'],
  sun: '#d9dde2',
  sunGlow: 'rgba(220,226,232,0.2)',
  cloud: '#9aa4b1',
  cloudShade: '#7a8492',
  haze: '#8592a2',
  hazeFar: '#9aa5b3',
  stone: '#a9a08e',
  stoneShade: '#7f7868',
  stoneLight: '#c4bba7',
  window: '#3e4b58',
  lit: 0.3,
  water: ['#6f8597', '#5b7184', '#4a5e70'],
  wall: '#7a7d80',
  wallTop: '#94979a',
  pavement: '#6e737a',
  road: '#3c4148',
  tree: ['#5c7b5a', '#48664a', '#38533c'],
};
