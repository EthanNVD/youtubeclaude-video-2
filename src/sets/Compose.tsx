import React, { useEffect, useState } from 'react';
import { continueRender, delayRender, staticFile } from 'remotion';
import { INK } from '../theme';
import { rnd } from '../lib/anim';
import { Drawing, type Part } from '../props/Drawing';

/**
 * A composed landscape (`"compose"` story places, see library/README.md and playbook/library.md): built in layers from far to
 * near so any region can be drawn without a hand-made set:
 *
 *   sky (by time) → painted plates (sky / far / mid pictures, optional) → procedural far layers (hills, mountains, jungle,
 *   treeline, palms, sea, town) → haze → ground (grass, laterite, sand, paddy, mud, dry, jungle_floor, snow) → road →
 *   far rows of library assets (trees, houses…) drawn small and softened by the haze.
 *
 * Rows that stand among the people (depth below the far zone) are NOT drawn here: the compiler makes them ordinary
 * drawing elements, so people walk in front of and behind them. Same 2400x1400 canvas as every set (x -240..2160).
 */
const X0 = -240, Y0 = -160, W = 2400, H = 1400;

type RowItem = { x: number; y: number; s: number; flip?: boolean; phase?: number };
type SetRow = { parts: Part[]; items: RowItem[] };
type Plate = { src: string; layer?: string; x?: number; y?: number; w?: number; h?: number; opacity?: number; drift?: number };
type Road = { kind?: string; y?: number; w?: number; away?: boolean; x?: number; vx?: number; bw?: number };

const SKY: Record<string, [string, string]> = {
  day: ['#8ec2dd', '#e6f0ea'], dawn: ['#7a8fc0', '#f6c99a'], dusk: ['#5b5a8a', '#f0a66a'], night: ['#0f1a33', '#2c3d63'],
  storm: ['#59636e', '#9aa4ab'], overcast: ['#a7b2b8', '#dde1dc'], snow: ['#b9c7d3', '#e9eef2'],
};
const GROUND: Record<string, [string, string, string]> = {
  // base, patches, tufts
  grass: ['#83a04e', '#739243', '#5e7d36'], laterite: ['#b9713f', '#a5622f', '#8a7a3a'], sand: ['#e4d09c', '#d6c088', '#b9a66a'],
  paddy: ['#93b65c', '#86aeb8', '#6f9a44'], mud: ['#6f5b45', '#5f4c39', '#55603a'], dry: ['#bfac70', '#ad9a60', '#8f8a4a'],
  jungle_floor: ['#58733b', '#4a6432', '#3c5528'], snow: ['#e9eef2', '#d8dfe5', '#c4ccd2'],
};
const ROAD: Record<string, [string, string]> = {
  laterite: ['#c97d45', '#a2602f'], dirt: ['#ad8f62', '#8c704a'], tarmac: ['#6c6c68', '#565652'], cobbles: ['#8c8579', '#6e675c'], sand: ['#dcc792', '#c0a974'],
};

/** images must be loaded before a frame is rendered (SVG <image> does not tell Remotion when it is ready) */
const PlateImage: React.FC<{ p: Plate; hz: number; t: number }> = ({ p, hz, t }) => {
  const url = staticFile(p.src);
  const [handle] = useState(() => delayRender('plate ' + p.src));
  useEffect(() => {
    const im = new Image();
    im.onload = () => continueRender(handle);
    im.onerror = () => continueRender(handle);
    im.src = url;
  }, [url, handle]);
  const layer = p.layer ?? 'far';
  // default placement by layer: the sky fills the top, far sits on the horizon, mid comes a little lower
  const h = p.h ?? (layer === 'sky' ? hz - Y0 + 60 : layer === 'far' ? 420 : 520);
  const y = p.y ?? (layer === 'sky' ? Y0 : layer === 'far' ? hz - h + 40 : hz - h + 140);
  const x = (p.x ?? X0) + ((p.drift ?? 0) * t) % W;
  return <image href={url} x={x} y={y} width={p.w ?? W} height={h} preserveAspectRatio="none" opacity={p.opacity ?? 1} />;
};

const canopy = (hz: number, seed: string, n: number, r0: number, r1: number, lift: number) =>
  Array.from({ length: n }, (_, i) => {
    const x = X0 + (W / (n - 1)) * i + (rnd(seed, i) - 0.5) * 40;
    const r = r0 + rnd(seed, i, 'r') * (r1 - r0);
    return { x, y: hz - lift - rnd(seed, i, 'y') * lift * 0.6, r };
  });

const Far: React.FC<{ kind: string; hz: number; k: number; t: number; dark: boolean }> = ({ kind, hz, k, dark }) => {
  const sd = `${kind}${k}`;
  const tint = (c: string) => (dark ? '#3a4560' : c);
  switch (kind) {
    case 'hills':
    case 'mountains': {
      const pts: string[] = [];
      const amp = kind === 'mountains' ? 330 : 120;
      const n = kind === 'mountains' ? 9 : 7;
      for (let i = 0; i <= n; i++) pts.push(`${X0 + (W / n) * i} ${hz - amp * (0.35 + rnd(sd, i) * 0.65)}`);
      const d = kind === 'mountains' ? `M${X0} ${hz + 20} L${pts.join(' L')} L${X0 + W} ${hz + 20} Z` : `M${X0} ${hz + 20} L${pts[0]} ${pts.slice(1).map((q, i) => `Q${X0 + (W / n) * (i + 0.5)} ${hz - amp * (0.6 + rnd(sd, i, 'q') * 0.5)} ${q}`).join(' ')} L${X0 + W} ${hz + 20} Z`;
      return <path d={d} fill={tint(kind === 'mountains' ? '#97a6bd' : '#9cb39e')} opacity={0.9} />;
    }
    case 'jungle':
    case 'treeline': {
      const big = kind === 'jungle';
      const cs = canopy(hz, sd, big ? 34 : 46, big ? 46 : 26, big ? 92 : 48, big ? 70 : 26);
      return (
        <g>
          {cs.map((c, i) => <circle key={i} cx={c.x} cy={c.y} r={c.r} fill={tint(big ? (i % 3 ? '#4f7040' : '#5b7d4a') : '#7d9b62')} />)}
          <rect x={X0} y={hz - (big ? 40 : 14)} width={W} height={60} fill={tint(big ? '#4a6a3c' : '#77955c')} />
        </g>
      );
    }
    case 'palms': {
      return (
        <g fill="none" stroke={tint('#5e7c52')} strokeLinecap="round">
          {Array.from({ length: 16 }, (_, i) => {
            const x = X0 + 80 + i * 150 + (rnd(sd, i) - 0.5) * 70, h = 110 + rnd(sd, i, 'h') * 90, lean = (rnd(sd, i, 'l') - 0.5) * 40;
            return (
              <g key={i}>
                <path d={`M${x} ${hz + 10} Q${x + lean * 0.3} ${hz - h * 0.6} ${x + lean} ${hz - h}`} strokeWidth={7} />
                {[-150, -115, -70, -30, 10].map((a, j) => <path key={j} transform={`translate(${x + lean} ${hz - h}) rotate(${a})`} d="M0 0 Q30 -12 58 6" strokeWidth={9} />)}
              </g>
            );
          })}
        </g>
      );
    }
    case 'sea':
      return (
        <g>
          <rect x={X0} y={hz - 70} width={W} height={110} fill={tint('#7fa9bf')} />
          {Array.from({ length: 10 }, (_, i) => <line key={i} x1={X0 + rnd(sd, i) * W} y1={hz - 60 + rnd(sd, i, 'y') * 90} x2={X0 + rnd(sd, i) * W + 80} y2={hz - 60 + rnd(sd, i, 'y') * 90} stroke="#cfe2ea" strokeWidth={3} opacity={0.6} />)}
        </g>
      );
    case 'town':
      return (
        <g fill={tint('#a99d8c')}>
          {Array.from({ length: 22 }, (_, i) => {
            const x = X0 + i * 112, h = 50 + rnd(sd, i) * 70;
            return <path key={i} d={`M${x} ${hz + 10} V${hz - h} L${x + 50} ${hz - h - 30} L${x + 104} ${hz - h} V${hz + 10} Z`} />;
          })}
        </g>
      );
    default:
      return null;
  }
};

export const ComposeSet: React.FC<{ p: Record<string, unknown>; t: number }> = ({ p, t }) => {
  const hz = (p.horizon as number) ?? 560;
  const time = (p.time as string) ?? 'day';
  const dark = time === 'night';
  const w = p.weather as string | { kind?: string; amount?: number } | undefined;
  const wk = typeof w === 'string' ? w : w?.kind;
  const amt = typeof w === 'object' && w?.amount !== undefined ? w.amount : 0.6;
  const skyKey = wk === 'rain' || wk === 'downpour' || wk === 'lightning' ? 'storm' : wk === 'fog' || wk === 'haze' ? (time === 'day' ? 'overcast' : time) : time;
  const [s0, s1] = SKY[skyKey] ?? SKY.day;
  const far = (Array.isArray(p.far) ? p.far : p.far ? [p.far] : ['hills']) as string[];
  const [g0, g1, g2] = GROUND[(p.ground as string) ?? 'grass'] ?? GROUND.grass;
  const plates = (p.plates as Plate[]) ?? [];
  const rows = (p.setRows as SetRow[]) ?? [];
  const road = p.road as Road | undefined;
  const id = `cmp${(p.seed as number) ?? 0}${hz}`;
  const ps = (y: number) => Math.max(0.04, (y - hz) / Math.max(1, 915 - hz));
  // haze: how much the far distance fades into the sky colour (humid tropics, fog, dust)
  const hazeAmt = wk === 'haze' ? 0.35 + amt * 0.35 : wk === 'fog' ? 0.5 + amt * 0.4 : wk === 'dust' || wk === 'sandstorm' ? 0.4 + amt * 0.3 : ((p.haze as number) ?? 0.18);
  const hazeC = wk === 'dust' || wk === 'sandstorm' ? '#d8b98a' : dark ? '#2c3d63' : '#eef0e8';
  return (
    <g>
      <defs>
        <linearGradient id={id + 's'} x1="0" y1="0" x2="0" y2="1">
          <stop offset="0" stopColor={s0} />
          <stop offset="1" stopColor={s1} />
        </linearGradient>
        <linearGradient id={id + 'h'} x1="0" y1="0" x2="0" y2="1">
          <stop offset="0" stopColor={hazeC} stopOpacity={hazeAmt * 0.35} />
          <stop offset="0.75" stopColor={hazeC} stopOpacity={hazeAmt} />
          <stop offset="1" stopColor={hazeC} stopOpacity={hazeAmt * 0.5} />
        </linearGradient>
        <linearGradient id={id + 'g'} x1="0" y1="0" x2="0" y2="1">
          <stop offset="0" stopColor={g1} />
          <stop offset="0.35" stopColor={g0} />
          <stop offset="1" stopColor={g0} />
        </linearGradient>
      </defs>
      <rect x={X0} y={Y0} width={W} height={hz - Y0 + 60} fill={`url(#${id}s)`} />
      {time === 'dusk' || time === 'dawn' ? <circle cx={1380} cy={hz - 90} r={110} fill="#ffd9a0" opacity={0.8} /> : null}
      {time === 'day' && !wk ? Array.from({ length: 4 }, (_, i) => (
        <ellipse key={i} cx={((X0 + rnd(id, i) * W + t * (5 + i * 2)) % W + W) % W + X0} cy={60 + rnd(id, i, 'y') * 200} rx={120 + rnd(id, i, 'r') * 90} ry={26} fill="#fbfbf6" opacity={0.75} />
      )) : null}
      {plates.filter((q) => (q.layer ?? 'far') === 'sky').map((q, i) => <PlateImage key={'s' + i} p={q} hz={hz} t={t} />)}
      {far.map((f, i) => <Far key={f + i} kind={f} hz={hz + i * 8} k={i} t={t} dark={dark} />)}
      {plates.filter((q) => (q.layer ?? 'far') === 'far').map((q, i) => <PlateImage key={'f' + i} p={q} hz={hz} t={t} />)}
      <rect x={X0} y={Y0} width={W} height={hz - Y0 + 40} fill={`url(#${id}h)`} />
      <rect x={X0} y={hz} width={W} height={Y0 + H - hz} fill={`url(#${id}g)`} />
      {plates.filter((q) => q.layer === 'mid').map((q, i) => <PlateImage key={'m' + i} p={q} hz={hz} t={t} />)}
      {/* ground texture: patches and tufts, smaller towards the horizon */}
      {Array.from({ length: 26 }, (_, i) => {
        const y = hz + 20 + Math.pow(rnd(id, i, 'py'), 1.4) * (Y0 + H - hz - 20);
        const s = ps(y);
        return <ellipse key={'p' + i} cx={X0 + rnd(id, i, 'px') * W} cy={y} rx={(90 + rnd(id, i, 'pr') * 140) * s} ry={(10 + rnd(id, i, 'pq') * 12) * s} fill={g1} opacity={0.7} />;
      })}
      {(p.ground as string) !== 'sand' && (p.ground as string) !== 'snow' ? Array.from({ length: 40 }, (_, i) => {
        const y = hz + 30 + Math.pow(rnd(id, i, 'ty'), 1.2) * (Y0 + H - hz - 30);
        const s = ps(y), x = X0 + rnd(id, i, 'tx') * W;
        return <path key={'t' + i} d={`M${x - 10 * s} ${y} l${4 * s} ${-16 * s} M${x} ${y} l${0} ${-22 * s} M${x + 10 * s} ${y} l${-4 * s} ${-16 * s}`} stroke={g2} strokeWidth={Math.max(1, 3 * s)} strokeLinecap="round" />;
      }) : null}
      {road ? <RoadView r={road} hz={hz} ps={ps} /> : null}
      {rows.map((r, i) => (
        <g key={'r' + i}>
          {r.items.map((it, j) => (
            <g key={j} transform={`translate(${it.x} ${it.y}) scale(${it.flip ? -it.s : it.s} ${it.s})`}>
              <Drawing parts={r.parts} t={t + (it.phase ?? 0)} />
            </g>
          ))}
        </g>
      ))}
      {/* far rows sit in the haze too */}
      {rows.length ? <rect x={X0} y={Y0} width={W} height={hz - Y0 + 120} fill={hazeC} opacity={hazeAmt * 0.45} /> : null}
    </g>
  );
};

const RoadView: React.FC<{ r: Road; hz: number; ps: (y: number) => number }> = ({ r, hz, ps }) => {
  const [c0, c1] = ROAD[r.kind ?? 'laterite'] ?? ROAD.laterite;
  if (r.away) {
    // a road going away from us: wide at the bottom of the frame, a point at the horizon
    const x = r.x ?? 960, vx = r.vx ?? x, bw = r.bw ?? 900;
    return (
      <g>
        <path d={`M${x - bw / 2} 1240 L${vx - 10} ${hz} L${vx + 10} ${hz} L${x + bw / 2} 1240 Z`} fill={c0} />
        <path d={`M${x - bw / 2} 1240 L${vx - 10} ${hz} M${vx + 10} ${hz} L${x + bw / 2} 1240`} stroke={c1} strokeWidth={10} opacity={0.6} />
        <path d={`M${x - bw * 0.18} 1240 L${vx - 3} ${hz} M${x + bw * 0.2} 1240 L${vx + 3} ${hz}`} stroke={c1} strokeWidth={6} opacity={0.35} />
      </g>
    );
  }
  // a road across the frame at a depth (people and cyclists pass along it)
  const y = r.y ?? 900, w = (r.w ?? 150) * ps(y);
  return (
    <g>
      <rect x={X0} y={y - w / 2} width={W} height={w} fill={c0} />
      <rect x={X0} y={y - w / 2} width={W} height={Math.max(2, w * 0.08)} fill={c1} opacity={0.7} />
      <rect x={X0} y={y + w / 2 - Math.max(2, w * 0.06)} width={W} height={Math.max(2, w * 0.06)} fill={c1} opacity={0.5} />
      {Array.from({ length: 14 }, (_, i) => (
        <path key={i} d={`M${X0 + i * 180 + 40} ${y - w * 0.15} q60 ${w * 0.05} 130 0`} stroke={c1} strokeWidth={Math.max(1.5, w * 0.03)} fill="none" opacity={0.45} />
      ))}
      <line x1={X0} y1={y - w / 2} x2={X0 + W} y2={y - w / 2} stroke={INK} strokeWidth={2} opacity={0.25} />
    </g>
  );
};
