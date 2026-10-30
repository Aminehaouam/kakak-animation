// Procedural sound: every effect and ambience is synthesised with WebAudio, so there are no
// recordings or music to license. Nothing plays until the listener turns sound on (the
// AudioContext is created by that click).

export type Sfx = 'whoosh' | 'flap' | 'chirp' | 'squawk' | 'page' | 'pop' | 'ding' | 'bell' | 'pen' | 'stamp' | 'tick';
export type Ambience = 'desk' | 'city' | 'sea' | 'rain' | 'cafe' | 'evening' | null;

class SoundEngine {
  private ctx: AudioContext;
  private master: GainNode;
  private noise: AudioBuffer;
  private bed: { name: Ambience; stop: () => void } | null = null;

  constructor() {
    const Ctx = window.AudioContext || (window as unknown as { webkitAudioContext: typeof AudioContext }).webkitAudioContext;
    this.ctx = new Ctx();
    this.master = this.ctx.createGain();
    this.master.gain.value = 0;
    const comp = this.ctx.createDynamicsCompressor();
    comp.threshold.value = -16;
    this.master.connect(comp).connect(this.ctx.destination);
    // two seconds of white noise, reused by every noisy sound
    const len = this.ctx.sampleRate * 2;
    this.noise = this.ctx.createBuffer(1, len, this.ctx.sampleRate);
    const data = this.noise.getChannelData(0);
    for (let i = 0; i < len; i++) data[i] = Math.random() * 2 - 1;
  }

  setOn(on: boolean) {
    const now = this.ctx.currentTime;
    if (on && this.ctx.state === 'suspended') void this.ctx.resume();
    this.master.gain.cancelScheduledValues(now);
    this.master.gain.setTargetAtTime(on ? 0.7 : 0, now, 0.15);
  }

  private env(gain: GainNode, at: number, attack: number, hold: number, release: number, peak: number) {
    gain.gain.setValueAtTime(0.0001, at);
    gain.gain.exponentialRampToValueAtTime(peak, at + attack);
    gain.gain.setValueAtTime(peak, at + attack + hold);
    gain.gain.exponentialRampToValueAtTime(0.0001, at + attack + hold + release);
  }

  private noiseSource(at: number, duration: number) {
    const src = this.ctx.createBufferSource();
    src.buffer = this.noise;
    src.loop = true;
    src.start(at, Math.random() * 1.5);
    src.stop(at + duration + 0.05);
    return src;
  }

  private tone(type: OscillatorType, freq: number, at: number, duration: number, peak: number, dest: AudioNode = this.master) {
    const osc = this.ctx.createOscillator();
    osc.type = type;
    osc.frequency.setValueAtTime(freq, at);
    const g = this.ctx.createGain();
    this.env(g, at, 0.005, 0, duration, peak);
    osc.connect(g).connect(dest);
    osc.start(at);
    osc.stop(at + duration + 0.05);
    return osc;
  }

  play(name: Sfx, opts: { volume?: number; duration?: number } = {}) {
    if (this.ctx.state !== 'running') return;
    const t = this.ctx.currentTime + 0.01;
    const v = opts.volume ?? 1;
    switch (name) {
      case 'whoosh': {
        const src = this.noiseSource(t, 0.9);
        const bp = this.ctx.createBiquadFilter();
        bp.type = 'bandpass';
        bp.Q.value = 1.2;
        bp.frequency.setValueAtTime(300, t);
        bp.frequency.exponentialRampToValueAtTime(2400, t + 0.35);
        bp.frequency.exponentialRampToValueAtTime(500, t + 0.85);
        const g = this.ctx.createGain();
        this.env(g, t, 0.25, 0.05, 0.55, 0.32 * v);
        src.connect(bp).connect(g).connect(this.master);
        break;
      }
      case 'flap': {
        for (let i = 0; i < 4; i++) {
          const at = t + i * 0.13;
          const src = this.noiseSource(at, 0.12);
          const lp = this.ctx.createBiquadFilter();
          lp.type = 'lowpass';
          lp.frequency.value = 900 - i * 90;
          const g = this.ctx.createGain();
          this.env(g, at, 0.012, 0.01, 0.09, 0.35 * v * (1 - i * 0.15));
          src.connect(lp).connect(g).connect(this.master);
        }
        break;
      }
      case 'chirp':
      case 'squawk': {
        const notes = name === 'chirp' ? [[2300, 3300], [2600, 3600]] : [[900, 1500], [1300, 700]];
        notes.forEach(([f0, f1], i) => {
          const at = t + i * (name === 'chirp' ? 0.11 : 0.16);
          const osc = this.ctx.createOscillator();
          osc.type = name === 'chirp' ? 'sine' : 'sawtooth';
          osc.frequency.setValueAtTime(f0, at);
          osc.frequency.exponentialRampToValueAtTime(f1, at + 0.08);
          const g = this.ctx.createGain();
          this.env(g, at, 0.008, 0.03, 0.07, (name === 'chirp' ? 0.12 : 0.05) * v);
          let out: AudioNode = g;
          if (name === 'squawk') {
            const bp = this.ctx.createBiquadFilter();
            bp.type = 'bandpass';
            bp.frequency.value = 1400;
            g.connect(bp);
            out = bp;
          }
          osc.connect(g);
          out.connect(this.master);
          osc.start(at);
          osc.stop(at + 0.2);
        });
        break;
      }
      case 'page': {
        const src = this.noiseSource(t, 0.55);
        const hp = this.ctx.createBiquadFilter();
        hp.type = 'highpass';
        hp.frequency.value = 1800;
        const g = this.ctx.createGain();
        this.env(g, t, 0.08, 0.12, 0.3, 0.16 * v);
        src.connect(hp).connect(g).connect(this.master);
        break;
      }
      case 'pop': {
        const osc = this.tone('sine', 620, t, 0.14, 0.2 * v);
        osc.frequency.exponentialRampToValueAtTime(320, t + 0.12);
        break;
      }
      case 'tick': {
        this.tone('triangle', 1650, t, 0.05, 0.06 * v);
        break;
      }
      case 'ding': {
        [1, 2.76, 5.4].forEach((r, i) => this.tone('sine', 880 * r, t, 1.2 / (i + 1), (0.14 / (i + 1)) * v));
        break;
      }
      case 'bell': {
        // a deep tower bell: inharmonic partials over a low E
        [1, 2.0, 2.4, 3.0, 4.2].forEach((r, i) => this.tone('sine', 164.8 * r, t, 3.2 / (1 + i * 0.6), (0.16 / (1 + i)) * v));
        break;
      }
      case 'stamp': {
        const src = this.noiseSource(t, 0.12);
        const lp = this.ctx.createBiquadFilter();
        lp.type = 'lowpass';
        lp.frequency.value = 500;
        const g = this.ctx.createGain();
        this.env(g, t, 0.004, 0.02, 0.09, 0.5 * v);
        src.connect(lp).connect(g).connect(this.master);
        this.tone('sine', 110, t, 0.12, 0.25 * v);
        break;
      }
      case 'pen': {
        const d = opts.duration ?? 1.5;
        const src = this.noiseSource(t, d);
        const bp = this.ctx.createBiquadFilter();
        bp.type = 'bandpass';
        bp.frequency.value = 3200;
        bp.Q.value = 0.8;
        const g = this.ctx.createGain();
        g.gain.setValueAtTime(0.0001, t);
        for (let s = 0; s < d; s += 0.09) g.gain.setValueAtTime((0.02 + Math.random() * 0.03) * v, t + s);
        g.gain.setValueAtTime(0.0001, t + d);
        src.connect(bp).connect(g).connect(this.master);
        break;
      }
    }
  }

  ambience(name: Ambience) {
    if (this.bed?.name === name) return;
    this.bed?.stop();
    this.bed = null;
    if (!name) return;
    const t = this.ctx.currentTime;
    const out = this.ctx.createGain();
    out.gain.setValueAtTime(0.0001, t);
    out.gain.exponentialRampToValueAtTime(1, t + 1.5);
    out.connect(this.master);
    const nodes: Array<AudioScheduledSourceNode> = [];
    const timers: number[] = [];
    const bedNoise = (type: BiquadFilterType, freq: number, gain: number, q = 0.7) => {
      const src = this.ctx.createBufferSource();
      src.buffer = this.noise;
      src.loop = true;
      const f = this.ctx.createBiquadFilter();
      f.type = type;
      f.frequency.value = freq;
      f.Q.value = q;
      const g = this.ctx.createGain();
      g.gain.value = gain;
      src.connect(f).connect(g).connect(out);
      src.start();
      nodes.push(src);
      return g;
    };
    const lfo = (target: AudioParam, rate: number, depth: number) => {
      const o = this.ctx.createOscillator();
      o.frequency.value = rate;
      const g = this.ctx.createGain();
      g.gain.value = depth;
      o.connect(g).connect(target);
      o.start();
      nodes.push(o);
    };
    const every = (ms: number, fn: () => void) => timers.push(window.setInterval(fn, ms));
    switch (name) {
      case 'desk':
        bedNoise('lowpass', 400, 0.025);
        every(5200, () => Math.random() < 0.5 && this.play('tick', { volume: 0.4 }));
        break;
      case 'city': {
        const g = bedNoise('lowpass', 320, 0.07);
        lfo(g.gain, 0.08, 0.025);
        every(6400, () => Math.random() < 0.6 && this.play('chirp', { volume: 0.35 }));
        break;
      }
      case 'sea': {
        const g = bedNoise('lowpass', 650, 0.05);
        lfo(g.gain, 0.12, 0.04);
        break;
      }
      case 'rain':
        bedNoise('highpass', 2600, 0.05);
        bedNoise('lowpass', 260, 0.05);
        break;
      case 'cafe':
        bedNoise('bandpass', 900, 0.03, 0.4);
        every(3800, () => Math.random() < 0.4 && this.play('tick', { volume: 0.5 }));
        break;
      case 'evening': {
        // a slow, open chord: generated, not a melody
        [130.81, 196.0, 246.94, 329.63].forEach((f, i) => {
          const o = this.ctx.createOscillator();
          o.type = 'triangle';
          o.frequency.value = f;
          o.detune.value = (i - 1.5) * 4;
          const lp = this.ctx.createBiquadFilter();
          lp.type = 'lowpass';
          lp.frequency.value = 900;
          const g = this.ctx.createGain();
          g.gain.value = 0.022;
          lfo(g.gain, 0.05 + i * 0.013, 0.012);
          o.connect(lp).connect(g).connect(out);
          o.start();
          nodes.push(o);
        });
        bedNoise('lowpass', 260, 0.03);
        break;
      }
    }
    this.bed = {
      name,
      stop: () => {
        const now = this.ctx.currentTime;
        out.gain.cancelScheduledValues(now);
        out.gain.setTargetAtTime(0.0001, now, 0.4);
        timers.forEach(clearInterval);
        nodes.forEach((n) => n.stop(now + 2));
        window.setTimeout(() => out.disconnect(), 2200);
      },
    };
  }
}

let engine: SoundEngine | null = null;
let enabled = false;

/** Call from a click: creates the audio context on first use. */
export function setSoundEnabled(on: boolean) {
  if (on && !engine) engine = new SoundEngine();
  enabled = on;
  engine?.setOn(on);
}

export const sound = {
  play(name: Sfx, opts?: { volume?: number; duration?: number }) {
    if (enabled) engine?.play(name, opts);
  },
  ambience(name: Ambience) {
    engine?.ambience(enabled ? name : null);
  },
};
