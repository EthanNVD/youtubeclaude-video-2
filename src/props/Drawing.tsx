import React from 'react';
import { INK, FONT } from '../theme';

/**
 * Declarative drawings: things the engine has no prop for, described in JSON by the writer (cards/_film.json "drawings")
 * or kept in the living library (library/<type>/<id>/asset.json, see library/README.md). Same style as every other prop:
 * flat fills, INK outlines. Assets imported from images (tools/lib.py import) are drawings too (path parts).
 *
 * Coordinates are in the drawing's own units; (0, 0) is where it stands on the ground (bottom centre), y grows downward,
 * so a 120-unit-high box is {"rect": [-60, -120, 120, 120]}. A man is about 260 units tall.
 *
 *   {"rect": [x, y, w, h], "r": 8}       {"circle": [cx, cy, r]}      {"ellipse": [cx, cy, rx, ry]}
 *   {"poly": [[x, y], ...]}              {"line": [[x, y], ...], "width": 8}   {"path": "M0 0 L10 10 Z"}
 *   {"text": "BROT", "at": [x, y], "size": 24, "font": "cond|title|hand|mono"}
 *   any part: "fill", "stroke" (false = none), "width" (outline, default 4), "opacity",
 *   motion: "spin": deg/s around "center" (wheels, propellers), "flicker": 0..1 (flames: scale around the base),
 *           "sway": degrees around "pivot" (flags, smoke), "blink": seconds per on/off (lamps), "drift": px/s along x (clouds),
           "bob": px up and down (a boat, an engine idling), "period": seconds per cycle (sway/bob), "phase": seconds of offset
 *   groups: {"group": [parts…], "at": [x, y], "id": "wheel_front"} moves, spins or sways several parts together around its own
 *           origin (spin/sway centre and pivot are in the group's coordinates) — wheels, a tree crown, a turret, a flag
 */
export type Part = {
  rect?: number[]; circle?: number[]; ellipse?: number[]; poly?: number[][]; line?: number[][]; path?: string;
  text?: string; at?: number[]; size?: number; font?: string; anchor?: 'start' | 'middle' | 'end';
  fill?: string; stroke?: string | false; width?: number; opacity?: number; r?: number;
  spin?: number; center?: number[]; flicker?: number; sway?: number; pivot?: number[]; blink?: number; drift?: number;
  bob?: number; period?: number; phase?: number;
  group?: Part[]; id?: string; scale?: number;
};

const FONTS: Record<string, string> = { cond: FONT.cond, title: FONT.title, hand: FONT.hand, mono: FONT.mono, book: FONT.book };

const centerOf = (p: Part): [number, number] => {
  if (p.center) return [p.center[0], p.center[1]];
  if (p.circle) return [p.circle[0], p.circle[1]];
  if (p.ellipse) return [p.ellipse[0], p.ellipse[1]];
  if (p.rect) return [p.rect[0] + p.rect[2] / 2, p.rect[1] + p.rect[3] / 2];
  if (p.poly?.length) return [p.poly.reduce((s, q) => s + q[0], 0) / p.poly.length, p.poly.reduce((s, q) => s + q[1], 0) / p.poly.length];
  return [0, 0];
};

const PartView: React.FC<{ p: Part; t: number }> = ({ p, t: t0 }) => {
  const t = t0 + (p.phase ?? 0);
  if (p.blink && Math.floor(t / p.blink) % 2 === 1) return null;
  if (p.group) {
    // a group moves as one: translate to "at", then the motion around the group's own centre/pivot
    const tr: string[] = [];
    if (p.at) tr.push(`translate(${p.at[0]} ${p.at[1]})`);
    if (p.bob) tr.push(`translate(0 ${Math.sin((t / (p.period ?? 1.6)) * Math.PI * 2) * p.bob})`);
    if (p.spin) { const [cx, cy] = p.center ?? [0, 0]; tr.push(`rotate(${(t * p.spin) % 360} ${cx} ${cy})`); }
    if (p.sway) { const [cx, cy] = p.pivot ?? [0, 0]; tr.push(`rotate(${Math.sin((t / (p.period ?? 3.7)) * Math.PI * 2) * p.sway} ${cx} ${cy})`); }
    if (p.scale) tr.push(`scale(${p.scale})`);
    return <g transform={tr.join(' ') || undefined} opacity={p.opacity}>{p.group.map((q, i) => <PartView key={i} p={q} t={t0} />)}</g>;
  }
  const stroke = p.stroke === false ? 'none' : (p.stroke ?? INK);
  const sw = p.width ?? 4;
  const style = { fill: p.fill ?? 'none', stroke, strokeWidth: sw, opacity: p.opacity, strokeLinejoin: 'round' as const, strokeLinecap: 'round' as const };
  let node: React.ReactNode = null;
  if (p.rect) node = <rect x={p.rect[0]} y={p.rect[1]} width={p.rect[2]} height={p.rect[3]} rx={p.r} {...style} />;
  else if (p.circle) node = <circle cx={p.circle[0]} cy={p.circle[1]} r={p.circle[2]} {...style} />;
  else if (p.ellipse) node = <ellipse cx={p.ellipse[0]} cy={p.ellipse[1]} rx={p.ellipse[2]} ry={p.ellipse[3]} {...style} />;
  else if (p.poly) node = <polygon points={p.poly.map((q) => q.join(',')).join(' ')} {...style} />;
  else if (p.line) node = <polyline points={p.line.map((q) => q.join(',')).join(' ')} fill="none" stroke={p.stroke === false ? 'none' : (p.stroke ?? p.fill ?? INK)} strokeWidth={p.width ?? 6} opacity={p.opacity} strokeLinecap="round" strokeLinejoin="round" />;
  else if (p.path) node = <path d={p.path} {...style} />;
  else if (p.text !== undefined) {
    const [x, y] = p.at ?? [0, 0];
    node = <text x={x} y={y} textAnchor={p.anchor ?? 'middle'} fontFamily={FONTS[p.font ?? 'cond'] ?? FONT.cond} fontWeight={700} fontSize={p.size ?? 24} fill={p.fill ?? INK} opacity={p.opacity}>{p.text}</text>;
  }
  const tr: string[] = [];
  if (p.drift) tr.push(`translate(${(t * p.drift) % 2400} 0)`);
  if (p.spin) { const [cx, cy] = centerOf(p); tr.push(`rotate(${(t * p.spin) % 360} ${cx} ${cy})`); }
  if (p.bob) tr.push(`translate(0 ${Math.sin((t / (p.period ?? 1.6)) * Math.PI * 2) * p.bob})`);
  if (p.sway) { const [cx, cy] = p.pivot ?? centerOf(p); tr.push(`rotate(${Math.sin((t / (p.period ?? 3.7)) * Math.PI * 2) * p.sway} ${cx} ${cy})`); }
  if (p.flicker) {
    const [cx] = centerOf(p);
    const base = p.pivot ? p.pivot[1] : 0;
    const k = 1 + (Math.sin(t * 13) * 0.6 + Math.sin(t * 7.3) * 0.4) * 0.12 * p.flicker;
    tr.push(`translate(${cx} ${base}) scale(${1 + (k - 1) * 0.4} ${k}) translate(${-cx} ${-base})`);
  }
  return tr.length ? <g transform={tr.join(' ')}>{node}</g> : <>{node}</>;
};

export const Drawing: React.FC<{ parts: Part[]; t: number }> = ({ parts, t }) => (
  <g>{(parts ?? []).map((p, i) => <PartView key={i} p={p} t={t} />)}</g>
);
