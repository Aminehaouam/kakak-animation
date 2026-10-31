import { Assets, Sprite, Texture } from 'pixi.js';

/** One painted asset: its file, size, and where its anchor point sits in the image. */
export interface Art {
  file: string;
  w: number;
  h: number;
  ax: number;
  ay: number;
  [extra: string]: unknown;
}

export type Manifest = Record<string, Art>;

export interface Library {
  man: Manifest;
  tex: Record<string, Texture>;
  /** a sprite of the named asset, anchored where the painting says */
  sprite(name: string): Sprite;
}

const BASE = import.meta.env.BASE_URL;

export async function loadLibrary(extra: Record<string, string>): Promise<Library> {
  const man: Manifest = await (await fetch(`${BASE}art/manifest.json`)).json();
  const entries: Array<[string, string]> = [...Object.entries(man).map(([k, a]) => [k, `${BASE}${a.file}`] as [string, string]), ...Object.entries(extra).map(([k, f]) => [k, `${BASE}${f}`] as [string, string])];
  const loaded = await Assets.load<Texture>(entries.map(([, url]) => url));
  const tex: Record<string, Texture> = {};
  for (const [name, url] of entries) tex[name] = loaded[url];
  return {
    man,
    tex,
    sprite(name: string) {
      const a = man[name];
      const s = new Sprite(tex[name]);
      if (a) s.anchor.set(a.ax / a.w, a.ay / a.h);
      return s;
    },
  };
}
