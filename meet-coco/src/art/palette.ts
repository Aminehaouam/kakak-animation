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
  /** the colour of soft shadows (contact shadows, overhangs) */
  shadow: string;
  /** 0 = flat daylight, 1 = low warm sun from the right */
  warmth: number;
}

export const DAY: CityPalette = {
  name: 'day',
  sky: ['#5eb8ef', '#a1d9f6', '#e8f4f2'],
  sun: '#fff6d8',
  sunGlow: 'rgba(255, 244, 210, 0.55)',
  cloud: '#ffffff',
  cloudShade: '#dbe9f3',
  haze: '#a8c3d7',
  hazeFar: '#c4d7e4',
  stone: '#e1c691',
  stoneShade: '#bfa163',
  stoneLight: '#f2e0b5',
  roof: '#475362',
  gold: '#e5af34',
  glass: '#80c5e2',
  glassShade: '#4b99bd',
  glassLight: '#d5eef6',
  brick: ['#c55737', '#d5844d', '#e1b179', '#ead6b2', '#a84f37', '#c7c2b4'],
  window: '#496276',
  windowLit: '#ffd789',
  lit: 0.04,
  water: ['#489ecb', '#2e87b9', '#1d70a3'],
  waterLine: 'rgba(255,255,255,0.55)',
  wall: '#baad95',
  wallTop: '#d8cfbc',
  pavement: '#cfc6b3',
  road: '#585d64',
  roadLine: '#f1ead8',
  tree: ['#62a843', '#3b8c35', '#256f2d'],
  trunk: '#6b4429',
  red: '#da2923',
  redShade: '#a61d19',
  black: '#1c1f25',
  ink: '#16202c',
  shadow: '#1f2a44',
  warmth: 0,
};

export const SUNSET: CityPalette = {
  name: 'sunset',
  sky: ['#313b74', '#d1616e', '#ffb36b'],
  sun: '#fff0c4',
  sunGlow: 'rgba(255, 190, 110, 0.6)',
  cloud: '#faaf86',
  cloudShade: '#a45c7a',
  haze: '#7e5779',
  hazeFar: '#ad6d7d',
  stone: '#efa35a',
  stoneShade: '#a45c4d',
  stoneLight: '#ffcf8f',
  roof: '#372c4d',
  gold: '#ffd07a',
  glass: '#f6926e',
  glassShade: '#8f5171',
  glassLight: '#ffd5a8',
  brick: ['#a34140', '#bb5f4e', '#cb8565', '#dca177', '#84373f', '#a4857d'],
  window: '#463252',
  windowLit: '#ffd27c',
  lit: 0.42,
  water: ['#f1926b', '#b25678', '#4a4278'],
  waterLine: 'rgba(255,214,160,0.75)',
  wall: '#7e5b6e',
  wallTop: '#a97c80',
  pavement: '#8d6872',
  road: '#40354a',
  roadLine: '#f0c18d',
  tree: ['#676754', '#4a514b', '#373e42'],
  trunk: '#37282f',
  red: '#df2a26',
  redShade: '#911827',
  black: '#17141f',
  ink: '#17141f',
  shadow: '#2a1733',
  warmth: 1,
};

export const RAIN: CityPalette = {
  ...DAY,
  name: 'rain',
  sky: ['#56657a', '#7a8899', '#a3adb8'],
  sun: '#d9dde2',
  sunGlow: 'rgba(220,226,232,0.2)',
  cloud: '#9aa4b1',
  cloudShade: '#7a8492',
  haze: '#8592a2',
  hazeFar: '#9aa5b3',
  stone: '#a9a08d',
  stoneShade: '#7e7666',
  stoneLight: '#c5bba6',
  window: '#384553',
  lit: 0.3,
  water: ['#6c8499', '#566f84', '#435a6e'],
  wall: '#797c7f',
  wallTop: '#94979a',
  pavement: '#6c7178',
  road: '#363b41',
  tree: ['#537b51', '#3d6441', '#2d4f33'],
  shadow: '#1b2230',
};
