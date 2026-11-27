import React from 'react';
import { Weather, type WeatherSpec } from '../fx/Weather';
import type { CameraKey, CastMember, LonLat, Scene } from '../types';
import { resolveKeys, clamp, easeFn, partialPolyline, smoothNoise } from '../lib/anim';
import { SetBackground } from '../sets/Sets';
import { Foreground } from '../sets/Rich';
import { MapLayer, makeProjection, PaperOverlay } from '../map/MapLayer';
import { ElementView, type Ctx } from './Elements';
import { DateBadge, PlaceTag } from '../overlays/Overlays';
import { resolveWorld, personScaleAt, vehicleScaleFor, VEH, PERSON_H, GROUND_FX, type WorldCtx } from '../lib/depth';
import type { ElementBase } from '../types';
import { FONT, INK, C } from '../theme';

const HUD_KINDS = new Set(['date', 'namecard', 'caption', 'stat', 'note', 'binoculars']);

export const cameraAt = (keys: CameraKey[] | undefined, t: number, base: Record<string, unknown>) =>
  resolveKeys(base, (keys ?? []) as never, t) as { x: number; y: number; zoom: number; rotate?: number; center?: LonLat; shake?: number; span?: number };

export const TINTS: Record<string, string> = {
  sepia: 'sepia(0.85) saturate(0.8) contrast(0.95)',
  grey: 'grayscale(0.85) brightness(0.92)',
  cold: 'saturate(0.7) hue-rotate(-12deg) brightness(0.95)',
  warm: 'sepia(0.25) saturate(1.1)',
  night: 'brightness(0.6) saturate(0.7) hue-rotate(-15deg)',
  red: 'sepia(0.4) saturate(2) hue-rotate(-30deg)',
};

/**
 * Coverage inside one scene (the reference grammar: wide → close on the reaction → insert → wide, joined by hard cuts).
 * A shot frames a subject by size instead of raw camera numbers:
 *   { t, on: "id" | index | [ids], size: wide|full|medium|close|ecu, frameX: -0.5..0.5 (where the subject sits),
 *     push: zoom gain over the shot (default 0.04), panX/panY: px drift over the shot, track: follow the subject,
 *     dy: shift the frame centre (px), shake, rotate } — or raw { t, x, y, zoom }.
 */
export type Shot = {
  t: number; on?: string | number | (string | number)[]; size?: string; frameX?: number; frameY?: number; push?: number; panX?: number; panY?: number;
  track?: boolean; dy?: number; dx?: number; shake?: number; rotate?: number; x?: number; y?: number; zoom?: number; free?: boolean;
};
const SIZE: Record<string, [number, number]> = {
  // visible height in subject heights, frame centre height above the feet (subject heights)
  full: [1.45, 0.5], medium: [0.92, 0.6], mediumclose: [0.72, 0.66], close: [0.56, 0.7], ecu: [0.38, 0.69],
};
const subjectAt = (els: ElementBase[], ref: string | number, t: number, world?: WorldCtx) => {
  const el = typeof ref === 'number' ? els[ref] : els.find((e) => e.id === ref);
  if (!el) return null;
  const k = resolveKeys(el, el.keys, t) as ElementBase;
  const x = (k.x as number) ?? 960, y = (k.y as number) ?? 900;
  let s = k.scale as number | undefined;
  if (s === undefined && world && (el.kind === 'actor' || el.kind === 'vehicle' || el.kind === 'crowd') && !el.at) {
    const ps = personScaleAt(world, y) * ((el.depthScale as number) ?? 1);
    s = el.kind === 'vehicle' ? vehicleScaleFor((el.type as string) ?? 'tank', ps, world.vehicles) : ps;
  }
  s = s ?? 1;
  const H = el.kind === 'vehicle' ? (VEH[(el.type as string) ?? 'tank']?.h ?? 200) * s
    : el.kind === 'actor' ? (el.seated ? 235 : el.kneel ? 250 : PERSON_H) * s
    : ((el.h as number) ?? 200) * s;
  const W = el.kind === 'vehicle' ? (VEH[(el.type as string) ?? 'tank']?.L ?? 400) * s : el.kind === 'actor' ? 150 * s : ((el.w as number) ?? 200) * s;
  // props/documents are centred on their origin, people and vehicles stand on it
  const centred = !(el.kind === 'actor' || el.kind === 'vehicle' || el.kind === 'crowd');
  return { x, y: centred ? y + H / 2 : y, H, W };
};
export const shotCamera = (shots: Shot[], els: ElementBase[], t: number, dur: number, world?: WorldCtx, pick?: number) => {
  const sorted = [...shots].sort((a, b) => a.t - b.t);
  let i = 0;
  for (let j = 0; j < sorted.length; j++) if (sorted[j].t <= t) i = j;
  // a shot dissolve renders the outgoing shot (pick) under the incoming one for ~0.6 s
  if (pick !== undefined && pick >= 0 && pick < sorted.length) i = pick;
  const sh = sorted[i];
  const tEnd = sorted[i + 1]?.t ?? dur;
  const p = clamp((t - sh.t) / Math.max(0.1, tEnd - sh.t));
  const pe = easeFn('inOut', p);
  let x = sh.x ?? 960, y = sh.y ?? 540, zoom = sh.zoom ?? 1;
  const refs = sh.on === undefined ? [] : Array.isArray(sh.on) ? sh.on : [sh.on];
  const at = sh.track ? t : sh.t + 0.01;
  let subs = refs.map((r) => subjectAt(els, r, at, world)).filter(Boolean) as { x: number; y: number; H: number; W: number }[];
  if (sh.track && subs.length) {
    // a camera operator follows with a little lag: average the subject over the last ~0.4 s
    const lagged = [0.1, 0.2, 0.3, 0.4].map((d) => refs.map((r) => subjectAt(els, r, Math.max(sh.t, t - d), world)).filter(Boolean) as typeof subs);
    subs = subs.map((q, i) => ({ ...q, x: (q.x * 2 + lagged.reduce((a, l) => a + (l[i]?.x ?? q.x), 0)) / 6 }));
  }
  if (subs.length && (sh.size ?? 'medium') !== 'wide') {
    const [vis, cen] = SIZE[sh.size ?? 'medium'] ?? SIZE.medium;
    if (subs.length === 1) {
      const s0 = subs[0];
      zoom = sh.zoom ?? 1080 / (vis * s0.H);
      y = s0.y - cen * s0.H;
      x = s0.x;
    } else {
      // group: fit everyone's heads and bodies down to the chosen size
      const Hm = Math.max(...subs.map((q) => q.H));
      const x0 = Math.min(...subs.map((q) => q.x - q.W * 0.55)), x1 = Math.max(...subs.map((q) => q.x + q.W * 0.55));
      const top = Math.min(...subs.map((q) => q.y - q.H * 1.04));
      const bot = Math.max(...subs.map((q) => q.y - q.H * (1 - vis) * 0.95));
      zoom = sh.zoom ?? Math.min(1920 / ((x1 - x0) * 1.12), 1080 / ((bot - top) * 1.08));
      x = (x0 + x1) / 2;
      y = (top + bot) / 2 + Hm * 0.02;
    }
  } else if (subs.length && sh.size === 'wide') {
    x = sh.x ?? subs[0].x;
  }
  zoom = Math.max(0.6, zoom * (1 + (sh.push ?? 0.04) * pe));
  x += -(sh.frameX ?? 0) * (1920 / zoom) + (sh.dx ?? 0) + (sh.panX ?? 0) * pe;
  y += -(sh.frameY ?? 0) * (1080 / zoom) + (sh.dy ?? 0) + (sh.panY ?? 0) * pe;
  if (!sh.free && zoom >= 1) {
    // keep the frame inside the drawn set
    const hw = 960 / zoom, hh = 540 / zoom;
    x = clamp(x, -230 + hw, 2150 - hw);
    y = clamp(y, -150 + hh, 1230 - hh);
  }
  return { x, y, zoom, rotate: sh.rotate ?? 0, shake: sh.shake ?? 0, cut: sh.t };
};

/** One scene rendered at scene-local time t (seconds). Draws into a 1920x1080 SVG. */
export const SceneView: React.FC<{ scene: Scene; t: number; cast?: Record<string, CastMember>; shotPick?: number; noHud?: boolean }> = ({ scene, t, cast, shotPick, noHud }) => {
  const dur = scene.end - scene.start;
  const els = scene.elements ?? [];
  let proj: Ctx['proj'];
  let world: React.ReactNode;
  let camT = '';
  let dofDef: React.ReactNode = null;

  if (scene.type === 'map' && scene.map) {
    const cam = scene.camera
      ? cameraAt(scene.camera, t, { center: scene.map.center, zoom: 1, span: scene.map.span })
      : { center: scene.map.center, zoom: 1 + 0.035 * (t / Math.max(1, dur)), span: scene.map.span };
    let center = (cam.center ?? scene.map.center) as LonLat;
    // map.follow = index of a route/arrow element: the camera rides along with its tip (reference: "the camera follows the ship")
    const fi = (scene.map as { follow?: number }).follow;
    const fel = fi !== undefined ? els[fi] : undefined;
    if (fel && Array.isArray(fel.path)) {
      const keyed = resolveKeys(fel, fel.keys, t) as typeof fel;
      const a = t - (fel.in ?? 0);
      const r = fel.enter === 'draw' ? easeFn('inOut', clamp(a / ((fel.dur as number) ?? 1.2))) : (keyed.progress as number) ?? 1;
      const tip = partialPolyline(fel.path as [number, number][], r).tip as [number, number];
      const lead = clamp(t / 0.9);
      center = [center[0] + (tip[0] - center[0]) * lead, center[1] + (tip[1] - center[1]) * lead];
    }
    proj = makeProjection(center, (cam.span as number) ?? scene.map.span, cam.zoom ?? 1);
    world = <MapLayer spec={scene.map} proj={proj} t={t} />;
  } else if (scene.type === 'title' || scene.type === 'chapter') {
    world = <ChapterCard scene={scene} t={t} />;
  } else {
    // no camera keys -> a slow, gentle push-in so the frame is never dead (reference style: 3-6 % over the shot)
    const shots = (scene as { shots?: Shot[] }).shots;
    const drift = !shots && !scene.camera && scene.set?.kind !== 'paper' && scene.set?.kind !== 'studio' && (scene.set?.drift as number) !== 0;
    const dz = (scene.set?.drift as number) ?? 0.045;
    const cam = shots?.length
      ? shotCamera(shots, els, t, dur, resolveWorld(scene.world, scene.set as never), shotPick)
      : drift
      ? { x: 960 + (scene.set?.driftX as number ?? 0) * (t / Math.max(1, dur)), y: 540, zoom: 1 + dz * (t / Math.max(1, dur)), rotate: 0, shake: 0 }
      : cameraAt(scene.camera, t, { x: 960, y: 540, zoom: 1, rotate: 0, shake: 0 });
    // impacts: `scene.impacts: [t, ...]` -> a short decaying camera jolt after each explosion
    const impulse = ((scene as { impacts?: number[] }).impacts ?? []).reduce((acc, ti) => (t >= ti && t - ti < 1.2 ? acc + 16 * Math.exp(-(t - ti) * 5) : acc), 0);
    const sh = (cam.shake ?? 0) + impulse;
    const jx = sh ? smoothNoise(t, 1.3) * sh : 0;
    const jy = sh ? smoothNoise(t, 4.1) * sh * 0.8 : 0;
    camT = `translate(${960 + jx} ${540 + jy}) scale(${cam.zoom}) rotate(${cam.rotate ?? 0}) translate(${-cam.x} ${-cam.y})`;
    // depth of field: the set is softly blurred so actors and props read sharp in front of it
    const flat = ['paper', 'studio', 'void', 'dark', 'memorial'].includes(scene.set?.kind ?? '');
    const dof = (scene.set?.dof as number) ?? (flat ? 0 : 1.6);
    world = scene.set ? (
      <g filter={dof > 0 ? `url(#dof_${scene.id})` : undefined}>
        <SetBackground {...scene.set} t={t} />
      </g>
    ) : <rect x={-240} y={-160} width={2400} height={1400} fill="#e6dcc4" />;
    dofDef = dof > 0 ? (
      <filter id={`dof_${scene.id}`} x="-5%" y="-5%" width="110%" height="110%">
        <feGaussianBlur stdDeviation={dof} />
      </filter>
    ) : null;
  }

  const ctx: Ctx = { t, dur, cast, proj, sceneId: scene.id, world: scene.type === 'stage' ? resolveWorld(scene.world, scene.set as never) : undefined };
  const worldEls0 = els.map((el, i) => ({ el, i })).filter(({ el }) => !el.hud && !HUD_KINDS.has(el.kind) && !el.front);
  // `front: true` = drawn after the set foreground (papers lying on a foreground desk, a hand reaching over it)
  const frontEls = els.map((el, i) => ({ el, i })).filter(({ el }) => !el.hud && !HUD_KINDS.has(el.kind) && !!el.front);
  // with a depth model, people and vehicles are drawn far → near (by their current ground y); other elements keep their slots
  // ground effects (a shell bursting, smoke from a gun) and props lying on the ground are part of that depth order too:
  // a burst behind a man is drawn behind him, one in front of him covers him (never a far explosion over a near face)
  const DEPTH_KINDS = new Set(['actor', 'vehicle', 'crowd', 'prop', 'drawing']);
  const inDepth = (el: ElementBase) => (DEPTH_KINDS.has(el.kind) || (el.kind === 'fx' && GROUND_FX.has(el.type as string))) && !el.fixedLayer;
  // without a world model only battle scenes are re-ordered (people, vehicles and ground bursts by their feet y), so a
  // shell landing far behind a sentry never covers him; other scenes keep the authored order
  const groundFx = (el: ElementBase) => el.kind === 'fx' && GROUND_FX.has(el.type as string);
  const sortable = ctx.world ? inDepth : (el: ElementBase) => (groundFx(el) || el.kind === 'actor' || el.kind === 'vehicle' || el.kind === 'crowd') && !el.fixedLayer;
  const worldEls = ctx.world || els.some(groundFx)
    ? (() => {
        const slots = worldEls0.map((w, k) => (sortable(w.el) ? k : -1)).filter((k) => k >= 0);
        // `depthY` overrides the sort depth (a man carried on a stretcher sorts with his bearers, not by his raised y)
        const items = slots.map((k) => worldEls0[k]).map((w) => ({ w, y: (w.el.depthY as number | undefined) ?? ((resolveKeys(w.el, w.el.keys, t) as { y?: number }).y ?? 900) }));
        items.sort((p, q) => p.y - q.y);
        const out = [...worldEls0];
        slots.forEach((k, j) => { out[k] = items[j].w; });
        return out;
      })()
    : worldEls0;
  const hudEls = noHud ? [] : els.map((el, i) => ({ el, i })).filter(({ el }) => el.hud || HUD_KINDS.has(el.kind));
  const weather = scene.set?.weather as WeatherSpec | undefined;

  const lbRaw = scene.letterbox;
  const lb = !!lbRaw;
  const lbH = lb ? 118 * clamp(t / 0.45, 0, 1) ** 0.6 : 0;
  const lbText = typeof lbRaw === 'string' ? lbRaw : lb ? [scene.date, scene.place].filter(Boolean).join(' — ').toUpperCase() : '';
  return (
    <svg viewBox="0 0 1920 1080" width="100%" height="100%" style={{ position: 'absolute', inset: 0 }}>
      <defs>
        {dofDef}
        <linearGradient id="flagshade" x1="0" x2="1">
          <stop offset="0" stopColor="#000" stopOpacity={0} />
          <stop offset="0.3" stopColor="#000" stopOpacity={0.5} />
          <stop offset="0.55" stopColor="#fff" stopOpacity={0.4} />
          <stop offset="0.8" stopColor="#000" stopOpacity={0.5} />
          <stop offset="1" stopColor="#000" stopOpacity={0} />
        </linearGradient>
      </defs>
      <g transform={camT || undefined}>
        {world}
        {worldEls.map(({ el, i }) => <ElementView key={i} el={el} ctx={ctx} index={i} />)}
        {scene.set?.fg ? <g transform={`translate(${(960 - ((cameraAt(scene.camera, t, { x: 960 }) as { x: number }).x ?? 960)) * 0.25} 0)`}><Foreground kind={scene.set.fg as string} t={t} side={scene.set.fgSide as string} /></g> : null}
        {frontEls.map(({ el, i }) => <ElementView key={'f' + i} el={el} ctx={ctx} index={i} />)}
      </g>
      {scene.type === 'map' && scene.map && (scene.map as { paper?: boolean }).paper !== false && scene.map.style !== 'poster' && scene.map.style !== 'dark' ? <PaperOverlay /> : null}
      {/* weather covers the whole screen: the fx element is centred on the frame by itself (x 960, y 540 by default),
          so it must NOT be wrapped in another translate (that pushed the rain into the bottom-right quarter) */}
      {weather && scene.set?.kind !== 'room' ? <Weather w={weather} t={t} seed={scene.id} /> : null}
      {hudEls.map(({ el, i }) => <ElementView key={'h' + i} el={el} ctx={ctx} index={i} />)}
      {!noHud && scene.tag ? <PlaceTag text={scene.tag as string} a={((scene.tagIn as number) ?? 0.3) < 0 ? 99 : t - ((scene.tagIn as number) ?? 0.3)} /> : null}
      {noHud ? null : lb ? (
        // cinema bars for dramatised moments; the caption replaces the date/place badges
        <g>
          <rect x={0} y={-10} width={1920} height={10 + lbH} fill="#0b0a09" />
          <rect x={0} y={1080 - lbH} width={1920} height={lbH + 10} fill="#0b0a09" />
          {lbText ? (
            <text x={960} y={1080 - lbH / 2 + 12} textAnchor="middle" fontFamily={FONT.mono} fontWeight={700} fontSize={34} letterSpacing={6} fill="#efe6d2" opacity={clamp((t - 0.3) / 0.5, 0, 1)}>{lbText}</text>
          ) : null}
        </g>
      ) : (
        <>
          {scene.date ? <DateBadge text={scene.date} a={t} /> : null}
          {scene.clock ? <DateBadge text={scene.clock} a={t} right /> : null}
          {scene.place ? <DateBadge text={scene.place} a={t - 0.2} y={scene.date ? 140 : 46} /> : null}
        </>
      )}
    </svg>
  );
};

const ChapterCard: React.FC<{ scene: Scene; t: number }> = ({ scene, t }) => {
  const k = Math.min(1, t / 0.6);
  return (
    <g>
      <rect x={-240} y={-160} width={2400} height={1400} fill="#1e1c1a" />
      <rect x={260} y={330} width={1400} height={420} fill="#efe4c8" stroke={INK} strokeWidth={8} transform={`rotate(-1 960 540)`} />
      <rect x={260} y={330} width={30} height={420} fill={C.red} transform={`rotate(-1 960 540)`} />
      {scene.subtitle ? <text x={960} y={450} textAnchor="middle" fontFamily={FONT.hand} fontSize={54} fill="#6a5a48" opacity={k}>{scene.subtitle}</text> : null}
      <text x={960} y={scene.subtitle ? 600 : 570} textAnchor="middle" fontFamily={FONT.heavy} fontSize={(scene.title?.length ?? 0) > 22 ? 96 : 124} fill={INK} opacity={k} letterSpacing={2}>{(scene.title ?? '').toUpperCase()}</text>
    </g>
  );
};
