import { createContext, useContext, useLayoutEffect, useRef, useState, type ReactNode } from 'react';

export interface Camera {
  /** stage point at the centre of the view */
  x: number;
  y: number;
  /** 1 = the stage just covers the view */
  zoom: number;
}

export interface Viewport {
  width: number;
  height: number;
  portrait: boolean;
}

const ViewportContext = createContext<Viewport>({ width: 1280, height: 800, portrait: false });
export const useViewport = () => useContext(ViewportContext);

/** Size of the element, kept current with a ResizeObserver. */
export function useSize<T extends HTMLElement>() {
  const ref = useRef<T>(null);
  const [size, setSize] = useState({ width: 0, height: 0 });
  useLayoutEffect(() => {
    const el = ref.current!;
    const update = () => setSize({ width: el.clientWidth, height: el.clientHeight });
    update();
    const ro = new ResizeObserver(update);
    ro.observe(el);
    return () => ro.disconnect();
  }, []);
  return [ref, size] as const;
}

export function ViewportProvider({ children }: { children: ReactNode }) {
  const [ref, size] = useSize<HTMLDivElement>();
  const value: Viewport = { ...size, portrait: size.height > size.width * 1.05 };
  return (
    <div ref={ref} className="viewport">
      <ViewportContext.Provider value={value}>{size.width > 0 && children}</ViewportContext.Provider>
    </div>
  );
}

interface StageProps {
  /** design size of the scene */
  width: number;
  height: number;
  camera: Camera;
  children: ReactNode;
  className?: string;
}

/**
 * A fixed-size scene scaled to cover the viewport and framed by a camera. Children are laid out
 * in stage pixels; the camera centres a stage point, and is kept inside the stage so no edge shows.
 */
export function Stage({ width, height, camera, children, className }: StageProps) {
  const vp = useViewport();
  const cover = Math.max(vp.width / width, vp.height / height);
  const s = cover * Math.max(camera.zoom, 1);
  const halfW = vp.width / s / 2;
  const halfH = vp.height / s / 2;
  const cx = Math.min(Math.max(camera.x, halfW), width - halfW);
  const cy = Math.min(Math.max(camera.y, halfH), height - halfH);
  const tx = vp.width / 2 - cx * s;
  const ty = vp.height / 2 - cy * s;
  return (
    <div className={`stage${className ? ` ${className}` : ''}`}>
      <div
        className="stage__world"
        style={{ width, height, transform: `translate(${tx}px, ${ty}px) scale(${s})` }}
      >
        {children}
      </div>
    </div>
  );
}
