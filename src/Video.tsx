import React from 'react';
import { AbsoluteFill, Img, staticFile, useCurrentFrame, useVideoConfig } from 'remotion';
import type { Plan, Scene } from './types';
import { SceneView, TINTS } from './scene/SceneView';
import { clamp, easeFn } from './lib/anim';
import { inflatePlan } from './lib/plan';

export type VideoProps = { plan: Plan };

const TD = 0.6; // scene transition duration (s); a scene may set transitionDur

const findScene = (scenes: Scene[], T: number) => {
  let lo = 0, hi = scenes.length - 1, ans = 0;
  while (lo <= hi) {
    const m = (lo + hi) >> 1;
    if (scenes[m].start <= T) {
      ans = m;
      lo = m + 1;
    } else hi = m - 1;
  }
  return ans;
};

/** film looks (meta.grade, from cards/_film.json "look": {"grade": ...}) — each film can have its own colour */
const GRADES: Record<string, string | undefined> = {
  film: 'saturate(0.8) sepia(0.24) contrast(1.1) brightness(0.95)',
  warm: 'saturate(0.88) sepia(0.34) contrast(1.08) brightness(0.96)',
  cold: 'saturate(0.72) sepia(0.1) hue-rotate(-10deg) contrast(1.1) brightness(0.95)',
  bleak: 'saturate(0.55) sepia(0.18) contrast(1.14) brightness(0.93)',
  sepia: 'saturate(0.6) sepia(0.55) contrast(1.08) brightness(0.95)',
  vivid: 'saturate(0.95) sepia(0.12) contrast(1.06) brightness(0.98)',
  none: undefined,
};
const SD = 0.6; // shot dissolve duration (s) — the reference films reframe inside a place with 0.4-0.9 s dissolves, not hard cuts

const SceneLayer: React.FC<{ scene: Scene; t: number; plan: Plan; shotPick?: number; noHud?: boolean; style?: React.CSSProperties }> = ({ scene, t, plan, shotPick, noHud, style }) => (
  <AbsoluteFill style={{ filter: scene.tint ? TINTS[scene.tint] : undefined, ...style }}>
    <SceneView scene={scene} t={t} cast={plan.cast} shotPick={shotPick} noHud={noHud} />
  </AbsoluteFill>
);

/** A scene; when `scene.shotDissolve` is set, each change of set-up dissolves from the previous framing over SD seconds. */
const Layer: React.FC<{ scene: Scene; t: number; plan: Plan; style?: React.CSSProperties }> = ({ scene, t, plan, style }) => {
  const shots = ((scene as { shots?: { t: number }[] }).shots ?? []).map((q) => q.t).sort((a, b) => a - b);
  if ((scene as { shotDissolve?: boolean }).shotDissolve && shots.length > 1) {
    for (let j = 1; j < shots.length; j++) {
      const a = t - shots[j];
      if (a >= 0 && a < SD) {
        return (
          <AbsoluteFill style={style}>
            <SceneLayer scene={scene} t={t} plan={plan} shotPick={j - 1} noHud />
            <SceneLayer scene={scene} t={t} plan={plan} style={{ opacity: easeFn('inOut', a / SD) }} />
          </AbsoluteFill>
        );
      }
    }
  }
  return <SceneLayer scene={scene} t={t} plan={plan} style={style} />;
};

export const Video: React.FC<VideoProps> = ({ plan: packed }) => {
  // drawings are stored once in the plan and referenced ("@d3"): put them back once per plan
  const plan = React.useMemo(() => inflatePlan(packed), [packed]);
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const T = frame / fps;
  const scenes = plan.scenes;
  if (!scenes.length) return <AbsoluteFill style={{ background: '#222' }} />;
  const i = findScene(scenes, T);
  const sc = scenes[i];
  const t = T - sc.start;
  const prev = i > 0 ? scenes[i - 1] : null;
  const tr = sc.transition ?? 'cut';
  const td = ((sc as { transitionDur?: number }).transitionDur ?? TD);
  const inTr = prev && tr !== 'cut' && t < td;
  const k = clamp(t / td);
  const grain = plan.meta.grain ?? 0.5;

  let content: React.ReactNode;
  if (inTr && prev && (tr === 'fade' || tr === 'wipe')) {
    content = (
      <>
        <Layer scene={prev} t={T - prev.start} plan={plan} />
        <Layer scene={sc} t={t} plan={plan} style={tr === 'fade' ? { opacity: easeFn('inOut', k) } : { clipPath: `inset(0 ${(1 - easeFn('inOut', k)) * 100}% 0 0)` }} />
      </>
    );
  } else if (inTr && prev && tr === 'dip') {
    content = (
      <>
        {k < 0.5 ? <Layer scene={prev} t={T - prev.start} plan={plan} /> : <Layer scene={sc} t={t} plan={plan} />}
        <AbsoluteFill style={{ background: '#000', opacity: 1 - Math.abs(k - 0.5) * 2 }} />
      </>
    );
  } else {
    content = <Layer scene={sc} t={t} plan={plan} />;
  }

  return (
    <AbsoluteFill style={{ background: '#111' }}>
      {/* film grade: warm, slightly desaturated (meta.grade: 'film' default | 'none') — strong warm grade like the reference */}
      <AbsoluteFill style={{ filter: GRADES[plan.meta.grade ?? 'film'] ?? GRADES.film }}>{content}</AbsoluteFill>
      {tr === 'flash' && t < 0.25 ? <AbsoluteFill style={{ background: '#fff', opacity: 1 - t / 0.25 }} /> : null}
      {grain > 0 ? (
        <AbsoluteFill style={{ mixBlendMode: 'multiply', opacity: grain * 0.55, pointerEvents: 'none' }}>
          <Img src={staticFile('textures/grain.png')} style={{ width: '120%', height: '120%', transform: `translate(${-((frame * 37) % 100) / 10}%, ${-((frame * 53) % 100) / 10}%)` }} />
        </AbsoluteFill>
      ) : null}
      <AbsoluteFill style={{ background: 'radial-gradient(ellipse at center, rgba(0,0,0,0) 50%, rgba(22,12,2,0.55) 100%)', pointerEvents: 'none' }} />
    </AbsoluteFill>
  );
};
