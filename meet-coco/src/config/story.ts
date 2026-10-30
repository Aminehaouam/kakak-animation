// The story: nine scenes, their copy and how long each plays before the next one starts.
// Times are seconds from the start of the scene.

export interface CaptionLine {
  text: string;
  at: number;
  /** a larger, display-type line */
  big?: boolean;
  /** put this line somewhere other than the scene's caption place */
  place?: 'top' | 'bottom' | 'center';
}

export interface SceneConfig {
  id: string;
  title: string;
  duration: number;
  captions: CaptionLine[];
  /** where the caption sits */
  captionPlace: 'top' | 'bottom' | 'center';
  /** dark text for light scenes */
  captionTone?: 'light' | 'dark';
}

export const STORY: SceneConfig[] = [
  {
    id: 'journal',
    title: 'The journal',
    duration: 8.5,
    captionPlace: 'bottom',
    captions: [{ text: 'Every great adventure starts somewhere...', at: 1.2, big: true }],
  },
  {
    id: 'meet',
    title: 'Meet Coco',
    duration: 8.5,
    captionPlace: 'bottom',
    captions: [
      { text: 'Meet Coco.', at: 4.6, big: true },
      { text: 'Your little companion on a big adventure.', at: 5.6 },
    ],
  },
  {
    id: 'arrival',
    title: 'Arrival',
    duration: 10,
    captionPlace: 'top',
    captions: [{ text: "Well... looks like we're in England!", at: 5.4, big: true }],
  },
  {
    id: 'map',
    title: 'The map',
    duration: 21,
    captionPlace: 'top',
    captions: [],
  },
  {
    id: 'london',
    title: 'London',
    duration: 9.5,
    captionPlace: 'top',
    captions: [{ text: "Let's explore London first!", at: 4.4, big: true }],
  },
  {
    id: 'experiences',
    title: 'Experiences',
    duration: 15,
    captionPlace: 'top',
    captionTone: 'dark',
    captions: [],
  },
  {
    id: 'live-it',
    title: 'Live it',
    duration: 11,
    captionPlace: 'top',
    captionTone: 'dark',
    captions: [
      { text: "Don't just learn English.", at: 1.0, big: true },
      { text: 'Live it.', at: 7.4, big: true, place: 'center' },
    ],
  },
  {
    id: 'journey',
    title: 'The journey',
    duration: 11,
    captionPlace: 'top',
    captions: [{ text: 'One journey. Countless experiences.', at: 6.0, big: true }],
  },
  {
    id: 'finale',
    title: 'Start',
    duration: 9,
    captionPlace: 'center',
    captions: [],
  },
];

export const FINALE = {
  title: 'MEET COCO',
  subtitle: 'Learn English. Explore the world.',
  button: 'START YOUR ADVENTURE',
};
