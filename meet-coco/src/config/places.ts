// Places on the UK map, with real coordinates (degrees, WGS84). The route between stops follows
// real travel corridors (the M40 and Chiltern line, the West Coast Main Line), so the drawn line
// is believable rather than a straight hop.

export type LonLat = [number, number];

export interface Stop {
  id: string;
  name: string;
  country: 'England' | 'Scotland';
  lonlat: LonLat;
  /** what Coco does there */
  blurb: string;
  /** English the learner practises at this stop */
  practise: string[];
  /** label side, to keep clear of the line */
  labelSide?: 'left' | 'right';
}

export const STOPS: Stop[] = [
  {
    id: 'london',
    name: 'London',
    country: 'England',
    lonlat: [-0.1276, 51.5072],
    blurb: 'Landing at the airport, a taxi into town, tea by the Thames.',
    practise: ['Passport control', 'Taking a taxi', 'Ordering in a café', 'Checking in'],
    labelSide: 'right',
  },
  {
    id: 'oxford',
    name: 'Oxford',
    country: 'England',
    lonlat: [-1.2577, 51.752],
    blurb: 'Colleges, bookshops and a punt on the river.',
    practise: ['Asking for directions', 'Library and bookshop English', 'Small talk'],
    labelSide: 'left',
  },
  {
    id: 'birmingham',
    name: 'Birmingham',
    country: 'England',
    lonlat: [-1.8904, 52.4862],
    blurb: 'Canals, markets and the busy Bullring.',
    practise: ['Shopping and prices', 'Markets', 'Public transport'],
    labelSide: 'right',
  },
  {
    id: 'manchester',
    name: 'Manchester',
    country: 'England',
    lonlat: [-2.2426, 53.4808],
    blurb: 'Music, football and red-brick mills.',
    practise: ['Making plans with friends', 'Tickets and events', 'Talking about sport'],
    labelSide: 'right',
  },
  {
    id: 'liverpool',
    name: 'Liverpool',
    country: 'England',
    lonlat: [-2.9916, 53.4084],
    blurb: 'The docks, the ferry across the Mersey and a lot of music history.',
    practise: ['Museums and tours', 'Ferries and timetables', 'Telling stories'],
    labelSide: 'left',
  },
  {
    id: 'edinburgh',
    name: 'Edinburgh',
    country: 'Scotland',
    lonlat: [-3.1883, 55.9533],
    blurb: 'A castle on a rock, closes and wynds, and a summer full of festivals.',
    practise: ['Booking a tour', 'Festival English', 'Weather talk'],
    labelSide: 'right',
  },
];

/** Waypoints between consecutive stops (excluding the stops themselves). */
export const CORRIDORS: Record<string, LonLat[]> = {
  // London to Oxford along the M40 / Chiltern line, past High Wycombe
  'london-oxford': [[-0.33, 51.53], [-0.55, 51.57], [-0.7482, 51.6286], [-0.98, 51.69]],
  // Oxford to Birmingham: Banbury, Leamington Spa, Solihull
  'oxford-birmingham': [[-1.28, 51.9], [-1.3398, 52.0629], [-1.52, 52.2852], [-1.7776, 52.4118]],
  // Birmingham to Manchester on the West Coast Main Line: Wolverhampton, Stafford, Stoke, Macclesfield
  'birmingham-manchester': [[-2.1288, 52.5862], [-2.117, 52.8072], [-2.1794, 53.0027], [-2.127, 53.2587], [-2.1575, 53.4106]],
  // Manchester to Liverpool on the first inter-city line: Newton-le-Willows, Rainhill
  'manchester-liverpool': [[-2.45, 53.47], [-2.6383, 53.4537], [-2.7667, 53.4167]],
  // Liverpool to Edinburgh: Wigan, Preston, Lancaster, Oxenholme, Penrith, Carlisle, Lockerbie, Carstairs
  'liverpool-edinburgh': [
    [-2.6325, 53.545], [-2.7031, 53.7632], [-2.8007, 54.0466], [-2.7457, 54.328], [-2.752, 54.6641],
    [-2.9329, 54.8925], [-3.355, 55.121], [-3.441, 55.3333], [-3.669, 55.695], [-3.35, 55.9],
  ],
};

export interface Place {
  name: string;
  lonlat: LonLat;
  /** zoom level at which the label shows (1 = the whole map) */
  minZoom?: number;
  align?: 'left' | 'right' | 'center';
}

export const CITIES: Place[] = [
  { name: 'Glasgow', lonlat: [-4.2518, 55.8642], align: 'left' },
  { name: 'Cardiff', lonlat: [-3.1791, 51.4816], align: 'left' },
  { name: 'Belfast', lonlat: [-5.9301, 54.5973], align: 'right' },
  { name: 'Dublin', lonlat: [-6.2603, 53.3498], align: 'right' },
  { name: 'Bristol', lonlat: [-2.5879, 51.4545], align: 'left', minZoom: 1.4 },
  { name: 'Leeds', lonlat: [-1.5491, 53.8008], align: 'right', minZoom: 1.4 },
  { name: 'Newcastle', lonlat: [-1.6178, 54.9783], align: 'right' },
  { name: 'Aberdeen', lonlat: [-2.0943, 57.1497], align: 'right' },
  { name: 'Inverness', lonlat: [-4.2247, 57.4778], align: 'right', minZoom: 1.2 },
  { name: 'Cork', lonlat: [-8.4756, 51.8985], align: 'right' },
  { name: 'Galway', lonlat: [-9.0568, 53.2707], align: 'right', minZoom: 1.3 },
  { name: 'Plymouth', lonlat: [-4.1427, 50.3755], align: 'left', minZoom: 1.4 },
  { name: 'Southampton', lonlat: [-1.4044, 50.9097], align: 'left', minZoom: 1.6 },
  { name: 'Norwich', lonlat: [1.2974, 52.6309], align: 'left', minZoom: 1.4 },
  { name: 'York', lonlat: [-1.0873, 53.96], align: 'right', minZoom: 1.6 },
  { name: 'Cambridge', lonlat: [0.1218, 52.2053], align: 'right', minZoom: 1.6 },
  { name: 'Swansea', lonlat: [-3.9436, 51.6214], align: 'left', minZoom: 1.6 },
  { name: 'Dundee', lonlat: [-2.9707, 56.462], align: 'right', minZoom: 1.5 },
  { name: 'Brighton', lonlat: [-0.1372, 50.8225], align: 'right', minZoom: 1.8 },
  { name: 'Derry', lonlat: [-7.3086, 54.9966], align: 'left', minZoom: 1.6 },
  { name: 'Limerick', lonlat: [-8.6267, 52.6638], align: 'right', minZoom: 1.6 },
  { name: 'Exeter', lonlat: [-3.5339, 50.7184], align: 'right', minZoom: 1.8 },
  { name: 'Nottingham', lonlat: [-1.1581, 52.9548], align: 'right', minZoom: 1.8 },
  { name: 'Sheffield', lonlat: [-1.4701, 53.3811], align: 'right', minZoom: 2.2 },
  { name: 'Carlisle', lonlat: [-2.9329, 54.8925], align: 'left', minZoom: 1.8 },
  { name: 'Lerwick', lonlat: [-1.145, 60.155], align: 'left', minZoom: 1.2 },
  { name: 'Kirkwall', lonlat: [-2.96, 58.981], align: 'right', minZoom: 1.5 },
  { name: 'Stornoway', lonlat: [-6.389, 58.209], align: 'right', minZoom: 1.5 },
];

export const COUNTRY_LABELS: Array<Place & { uk: boolean }> = [
  { name: 'Scotland', lonlat: [-4.35, 56.85], uk: true },
  { name: 'England', lonlat: [-1.35, 52.85], uk: true },
  { name: 'Wales', lonlat: [-3.75, 52.32], uk: true },
  { name: 'Northern Ireland', lonlat: [-6.9, 54.74], uk: true },
  { name: 'Ireland', lonlat: [-8.15, 53.2], uk: false },
];

export const SEA_LABELS: Array<Place & { size: 'ocean' | 'sea' | 'channel' }> = [
  { name: 'North Sea', lonlat: [1.6, 56.1], size: 'sea' },
  { name: 'Irish Sea', lonlat: [-5.05, 53.75], size: 'sea' },
  { name: 'English Channel', lonlat: [-2.6, 50.18], size: 'channel' },
  { name: 'Atlantic Ocean', lonlat: [-9.7, 56.3], size: 'ocean' },
  { name: 'Celtic Sea', lonlat: [-7.1, 50.85], size: 'channel', minZoom: 1.3 },
  { name: 'Bristol Channel', lonlat: [-4.1, 51.33], size: 'channel', minZoom: 2.2 },
];

export const REGION_LABELS: Place[] = [
  { name: 'Scottish Highlands', lonlat: [-4.9, 57.55] },
  { name: 'Grampian Mountains', lonlat: [-3.75, 56.83], minZoom: 1.6 },
  { name: 'Cairngorms', lonlat: [-3.65, 57.08], minZoom: 2.2 },
  { name: 'Southern Uplands', lonlat: [-3.5, 55.38], minZoom: 1.3 },
  { name: 'Lake District', lonlat: [-3.08, 54.5], minZoom: 1.3 },
  { name: 'Pennines', lonlat: [-2.08, 54.3] },
  { name: 'Peak District', lonlat: [-1.78, 53.3], minZoom: 1.8 },
  { name: 'North York Moors', lonlat: [-0.9, 54.37], minZoom: 1.8 },
  { name: 'Snowdonia', lonlat: [-3.95, 53.05], minZoom: 1.3 },
  { name: 'Cambrian Mountains', lonlat: [-3.72, 52.38], minZoom: 1.8 },
  { name: 'Brecon Beacons', lonlat: [-3.45, 51.9], minZoom: 1.8 },
  { name: 'Dartmoor', lonlat: [-3.92, 50.58], minZoom: 1.6 },
  { name: 'Mourne Mountains', lonlat: [-6.0, 54.17], minZoom: 2.2 },
  { name: 'Wicklow Mountains', lonlat: [-6.38, 53.03], minZoom: 1.6 },
];

export const ISLAND_LABELS: Place[] = [
  { name: 'Shetland', lonlat: [-0.55, 60.38] },
  { name: 'Orkney', lonlat: [-2.2, 59.15] },
  { name: 'Outer Hebrides', lonlat: [-7.15, 57.8], align: 'left' },
  { name: 'Isle of Skye', lonlat: [-6.75, 57.25], minZoom: 1.6 },
  { name: 'Isle of Man', lonlat: [-4.1, 54.0], align: 'left', minZoom: 1.2 },
  { name: 'Anglesey', lonlat: [-4.9, 53.32], minZoom: 1.8 },
  { name: 'Isle of Wight', lonlat: [-1.3, 50.55], minZoom: 1.8 },
  { name: 'Isles of Scilly', lonlat: [-6.31, 49.85], minZoom: 1.6 },
];

/** Real forests and woodland parks: [name, lon, lat, radius km] (drawn as tree clusters). */
export const FORESTS: Array<[string, number, number, number]> = [
  ['New Forest', -1.6, 50.87, 9],
  ['Forest of Dean', -2.54, 51.79, 6],
  ['Savernake Forest', -1.68, 51.4, 4],
  ['Ashdown Forest', 0.03, 51.06, 5],
  ['Epping Forest', 0.05, 51.66, 4],
  ['Thetford Forest', 0.67, 52.45, 9],
  ['Sherwood Forest', -1.07, 53.2, 6],
  ['Cannock Chase', -2.0, 52.75, 5],
  ['Wyre Forest', -2.35, 52.4, 4],
  ['Kielder Forest', -2.5, 55.2, 13],
  ['Hamsterley Forest', -1.93, 54.67, 5],
  ['Dalby Forest', -0.68, 54.27, 7],
  ['Grizedale Forest', -3.03, 54.33, 5],
  ['Gwydir Forest', -3.85, 53.1, 6],
  ['Coed y Brenin', -3.88, 52.82, 6],
  ['Galloway Forest', -4.45, 55.1, 14],
  ['Queen Elizabeth Forest Park', -4.45, 56.2, 9],
  ['Argyll Forest', -4.95, 56.15, 8],
  ['Tay Forest', -3.9, 56.7, 10],
  ['Cairngorms pinewoods', -3.75, 57.15, 11],
  ['Glen Affric', -4.95, 57.27, 8],
  ['Tollymore Forest', -5.95, 54.22, 4],
  ['Glenariff Forest', -6.1, 55.05, 5],
  ['Wicklow forests', -6.35, 53.0, 9],
  ['Killarney woods', -9.55, 52.0, 7],
  ['Slieve Bloom', -7.6, 53.1, 6],
];
