import React from 'react';
import { C, INK, nation, FONT } from '../theme';
import { rnd } from '../lib/anim';
import { Flag } from '../props/Props';
import { RICH_SETS, RichSet, Lighting } from './Rich';
import { RoomKit, TownKit } from './Kit';
import { ComposeSet } from './Compose';

/**
 * Parametric backgrounds. Drawn on a 2400x1400 canvas centered on the 1920x1080 frame
 * (x -240..2160, y -160..1240) so the camera can push/pan without showing edges.
 * Ground line (where actors stand) defaults to y=900.
 */
export type SetProps = { kind: string; time?: string; t: number; [k: string]: unknown };

const X0 = -240, Y0 = -160, W = 2400, H = 1400;

const Sky: React.FC<{ time?: string; id: string; horizon?: number }> = ({ time = 'day', id, horizon = 700 }) => {
  const g: Record<string, [string, string]> = {
    day: [C.skyTop, '#d7ecf4'],
    dusk: ['#5b5a8a', '#f0a66a'],
    dawn: ['#7a8fc0', '#f6c99a'],
    night: ['#0f1a33', '#2c3d63'],
    storm: ['#59636e', '#9aa4ab'],
    snow: ['#b9c7d3', '#e9eef2'],
  };
  const [a, b] = g[time] ?? g.day;
  return (
    <g>
      <defs>
        <linearGradient id={id} x1="0" y1="0" x2="0" y2="1">
          <stop offset="0" stopColor={a} />
          <stop offset="1" stopColor={b} />
        </linearGradient>
      </defs>
      <rect x={X0} y={Y0} width={W} height={horizon - Y0 + 40} fill={`url(#${id})`} />
      {time === 'night'
        ? Array.from({ length: 70 }, (_, i) => (
            <circle key={i} cx={X0 + rnd('s', i) * W} cy={Y0 + rnd('y', i) * (horizon - Y0 - 100)} r={1 + rnd('r', i) * 2} fill="#fff" opacity={0.4 + rnd('o', i) * 0.5} />
          ))
        : null}
    </g>
  );
};

export const Cloud: React.FC<{ x: number; y: number; s?: number; tone?: string }> = ({ x, y, s = 1, tone = '#fdfdfb' }) => (
  <g transform={`translate(${x} ${y}) scale(${s})`}>
    <path d="M-120 30 Q-130 -10 -90 -14 Q-80 -60 -30 -50 Q-10 -90 40 -66 Q90 -80 100 -30 Q140 -24 130 30 Z" fill={tone} />
    <path d="M-120 30 Q0 44 130 30 Q0 18 -120 30 Z" fill="#dfe6ea" opacity={0.8} />
  </g>
);

const Clouds: React.FC<{ t: number; n?: number; y?: number; tone?: string; seed?: string }> = ({ t, n = 6, y = 120, tone, seed = 'c' }) => (
  <g>
    {Array.from({ length: n }, (_, i) => {
      const sp = 6 + rnd(seed, i, 'sp') * 10;
      const x = ((X0 + rnd(seed, i) * W + t * sp) % W + W) % W + X0;
      return <Cloud key={i} x={x} y={y + rnd(seed, i, 'y') * 260} s={0.5 + rnd(seed, i, 's') * 0.9} tone={tone} />;
    })}
  </g>
);

const Hills: React.FC<{ y: number; color: string; amp?: number; seed?: string; dark?: string }> = ({ y, color, amp = 60, seed = 'h' }) => {
  const pts: string[] = [];
  for (let i = 0; i <= 12; i++) {
    const x = X0 + (W / 12) * i;
    pts.push(`${x} ${y - amp * (0.4 + rnd(seed, i) * 0.6)}`);
  }
  return <path d={`M${X0} ${Y0 + H} L${X0} ${y} Q${pts.join(' T')} L${X0 + W} ${Y0 + H} Z`.replace('Q' + pts[0], 'L' + pts[0] + ' Q' + pts[1]).replace(' T' + pts[1], '')} fill={color} />;
};

const Pole: React.FC<{ x: number; y: number; h: number }> = ({ x, y, h }) => {
  // telegraph pole: tall post, two short cross-arms with insulators at the very top (never reads as a grave cross)
  const w = Math.max(2, h / 34);
  return (
    <g strokeLinecap="round">
      <line x1={x} y1={y} x2={x} y2={y - h} stroke="#5a4030" strokeWidth={w} />
      {[0.04, 0.12].map((k) => (
        <g key={k}>
          <line x1={x - h * 0.13} y1={y - h * (1 - k)} x2={x + h * 0.13} y2={y - h * (1 - k)} stroke="#5a4030" strokeWidth={w * 0.8} />
          {[-0.11, -0.04, 0.04, 0.11].map((q) => <circle key={q} cx={x + h * q} cy={y - h * (1 - k) - w} r={w * 0.7} fill="#e9e4d4" />)}
        </g>
      ))}
    </g>
  );
};

export const Tree: React.FC<{ x: number; y: number; s?: number; kind?: string; snow?: boolean }> = ({ x, y, s = 1, kind = 'round', snow }) => (
  <g transform={`translate(${x} ${y}) scale(${s})`}>
    {kind === 'pine' ? (
      <g>
        <rect x={-8} y={-30} width={16} height={30} fill="#5a3e2a" />
        <path d="M0 -190 L60 -30 L-60 -30 Z" fill={snow ? '#4d6b5a' : '#3f6b45'} stroke={INK} strokeWidth={3} strokeLinejoin="round" />
        <path d="M0 -150 L48 -70 L-48 -70 Z" fill={snow ? '#5b7a69' : '#4c7d52'} />
        {snow ? <path d="M0 -190 L22 -132 Q0 -126 -22 -132 Z" fill="#f2f6f8" /> : null}
      </g>
    ) : kind === 'bare' ? (
      <g stroke="#4a3a2e" strokeWidth={8} strokeLinecap="round" fill="none">
        <path d="M0 0 L0 -120 M0 -70 L-40 -120 M0 -90 L36 -150 M-20 -96 L-30 -150" />
      </g>
    ) : kind === 'palm' ? (
      <g>
        <path d="M0 0 Q10 -100 30 -200" stroke="#7a5a3a" strokeWidth={14} fill="none" />
        {[-150, -110, -60, -20, 30].map((a, i) => (
          <path key={i} transform={`translate(30 -200) rotate(${a})`} d="M0 0 Q60 -20 110 10 Q60 0 0 0" fill="#4f8a3a" stroke={INK} strokeWidth={3} />
        ))}
      </g>
    ) : (
      <g>
        <rect x={-9} y={-60} width={18} height={60} fill="#6b4a32" stroke={INK} strokeWidth={3} />
        <circle cx={0} cy={-110} r={62} fill="#5f9446" stroke={INK} strokeWidth={3} />
        <circle cx={-34} cy={-80} r={38} fill="#5f9446" stroke={INK} strokeWidth={3} />
        <circle cx={34} cy={-84} r={40} fill="#5f9446" stroke={INK} strokeWidth={3} />
        <circle cx={-14} cy={-128} r={26} fill="#77ad59" />
      </g>
    )}
  </g>
);

const House: React.FC<{ x: number; y: number; s?: number; wall?: string; roof?: string; snow?: boolean }> = ({ x, y, s = 1, wall = '#c98f62', roof = '#6a5a5a', snow }) => (
  <g transform={`translate(${x} ${y}) scale(${s})`}>
    <rect x={-60} y={-80} width={120} height={80} fill={wall} stroke={INK} strokeWidth={3} />
    <path d="M-72 -78 L0 -130 L72 -78 Z" fill={snow ? '#f1f4f6' : roof} stroke={INK} strokeWidth={3} />
    <rect x={-40} y={-56} width={26} height={24} fill="#8fc0dc" stroke={INK} strokeWidth={2.5} />
    <rect x={14} y={-56} width={26} height={24} fill="#8fc0dc" stroke={INK} strokeWidth={2.5} />
    <rect x={-10} y={-34} width={20} height={34} fill="#5a3e2a" stroke={INK} strokeWidth={2.5} />
  </g>
);

const Window: React.FC<{ x: number; y: number; w: number; h: number; time?: string; frame?: string; curtains?: string }> = ({ x, y, w, h, time = 'day', frame = '#f2ecdf', curtains }) => (
  <g>
    <rect x={x} y={y} width={w} height={h} fill={time === 'night' ? '#1c2b4a' : time === 'dusk' ? '#f0b07a' : '#bfe0ef'} stroke={INK} strokeWidth={4} />
    {time !== 'night' ? <path d={`M${x} ${y + h * 0.75} Q${x + w * 0.3} ${y + h * 0.62} ${x + w * 0.6} ${y + h * 0.72} T${x + w} ${y + h * 0.68} V${y + h} H${x} Z`} fill="#8db86a" opacity={0.85} /> : null}
    {time === 'night' ? <circle cx={x + w * 0.7} cy={y + h * 0.25} r={14} fill="#f4f0d8" /> : null}
    <path d={`M${x + w / 2} ${y} V${y + h} M${x} ${y + h / 2} H${x + w}`} stroke={frame} strokeWidth={10} />
    <rect x={x} y={y} width={w} height={h} fill="none" stroke={frame} strokeWidth={12} />
    <rect x={x - 6} y={y - 6} width={w + 12} height={h + 12} fill="none" stroke={INK} strokeWidth={3} />
    {curtains ? (
      <g fill={curtains} stroke={INK} strokeWidth={3}>
        <path d={`M${x - 30} ${y - 20} H${x + 24} Q${x + 10} ${y + h / 2} ${x + 30} ${y + h + 20} H${x - 30} Z`} />
        <path d={`M${x + w + 30} ${y - 20} H${x + w - 24} Q${x + w - 10} ${y + h / 2} ${x + w - 30} ${y + h + 20} H${x + w + 30} Z`} />
      </g>
    ) : null}
  </g>
);

export const WallClock: React.FC<{ x: number; y: number; r?: number; t: number; time?: string }> = ({ x, y, r = 46, t, time }) => {
  let h = 10, m = 10;
  if (typeof time === 'string' && /\d+:\d+/.test(time)) {
    const [hh, mm] = time.split(':').map(Number);
    h = hh; m = mm + t / 60;
  } else m = 10 + t * 0.5;
  const ma = (m / 60) * 360, ha = ((h % 12) / 12) * 360 + (m / 60) * 30;
  return (
    <g transform={`translate(${x} ${y})`}>
      <circle r={r} fill="#fbf8f0" stroke={INK} strokeWidth={5} />
      <circle r={r - 7} fill="none" stroke="#8a6a4a" strokeWidth={2} />
      {Array.from({ length: 12 }, (_, i) => <line key={i} x1={0} y1={-r + 10} x2={0} y2={-r + 17} stroke={INK} strokeWidth={3} transform={`rotate(${i * 30})`} />)}
      <line x1={0} y1={0} x2={0} y2={-r * 0.5} stroke={INK} strokeWidth={5} strokeLinecap="round" transform={`rotate(${ha})`} />
      <line x1={0} y1={0} x2={0} y2={-r * 0.78} stroke={INK} strokeWidth={3} strokeLinecap="round" transform={`rotate(${ma})`} />
      <circle r={4} fill={INK} />
    </g>
  );
};

const Floor: React.FC<{ y: number; color: string; boards?: boolean }> = ({ y, color, boards }) => (
  <g>
    <rect x={X0} y={y} width={W} height={Y0 + H - y} fill={color} />
    <rect x={X0} y={y} width={W} height={8} fill="#000" opacity={0.15} />
    {boards ? Array.from({ length: 22 }, (_, i) => <line key={i} x1={X0 + i * 120} y1={y} x2={X0 + i * 120 - 160} y2={Y0 + H} stroke="#000" opacity={0.08} strokeWidth={4} />) : null}
  </g>
);

const Wall: React.FC<{ color: string; y?: number; wainscot?: string; paper?: boolean }> = ({ color, y = 780, wainscot, paper }) => (
  <g>
    <rect x={X0} y={Y0} width={W} height={y - Y0} fill={color} />
    {paper ? Array.from({ length: 30 }, (_, i) => <line key={i} x1={X0 + i * 80} y1={Y0} x2={X0 + i * 80} y2={y} stroke="#000" opacity={0.04} strokeWidth={18} />) : null}
    {wainscot ? (
      <g>
        <rect x={X0} y={y - 220} width={W} height={220} fill={wainscot} />
        <rect x={X0} y={y - 226} width={W} height={12} fill="#000" opacity={0.18} />
        {Array.from({ length: 16 }, (_, i) => <rect key={i} x={X0 + 30 + i * 160} y={y - 190} width={120} height={160} fill="none" stroke="#000" opacity={0.12} strokeWidth={4} />)}
      </g>
    ) : null}
  </g>
);

export const Desk: React.FC<{ x: number; y: number; w?: number; color?: string; cloth?: string }> = ({ x, y, w = 900, color = C.wood, cloth }) => (
  <g>
    <rect x={x - w / 2} y={y} width={w} height={34} fill={cloth ?? C.woodLight} stroke={INK} strokeWidth={4} />
    <rect x={x - w / 2 + 10} y={y + 34} width={w - 20} height={260} fill={cloth ? shadeC(cloth) : color} stroke={INK} strokeWidth={4} />
    {cloth ? null : <rect x={x - w / 2 + 40} y={y + 70} width={w - 80} height={6} fill="#000" opacity={0.15} />}
  </g>
);
const shadeC = (c: string) => (c === '#3f6b45' ? '#2f5235' : c === '#2f6b3a' ? '#24522c' : c);

const Bookshelf: React.FC<{ x: number; y: number }> = ({ x, y }) => (
  <g transform={`translate(${x} ${y})`}>
    <rect x={0} y={0} width={240} height={420} fill="#6b4428" stroke={INK} strokeWidth={4} />
    {[0, 1, 2, 3].map((r) => (
      <g key={r}>
        <rect x={10} y={10 + r * 102} width={220} height={92} fill="#4a2e1a" />
        {Array.from({ length: 9 }, (_, i) => (
          <rect key={i} x={14 + i * 24} y={24 + r * 102 + rnd(r, i) * 14} width={20} height={78 - rnd(r, i) * 14} fill={['#8b2e2e', '#2e4a6b', '#4f6b3a', '#a8873a', '#6b3a5a'][(i + r) % 5]} stroke={INK} strokeWidth={1.5} />
        ))}
      </g>
    ))}
  </g>
);

const Portrait: React.FC<{ x: number; y: number; w?: number; h?: number; flagOf?: string }> = ({ x, y, w = 150, h = 190, flagOf }) => (
  <g transform={`translate(${x} ${y})`}>
    <rect x={-w / 2 - 12} y={-h / 2 - 12} width={w + 24} height={h + 24} fill="#b8892e" stroke={INK} strokeWidth={4} />
    <rect x={-w / 2} y={-h / 2} width={w} height={h} fill={flagOf ? '#ddd' : '#5a4a3a'} stroke={INK} strokeWidth={2} />
    {flagOf ? <g transform={`translate(${-w / 2 + 10} ${-h / 2 + 30})`}><Flag nation={flagOf} w={w - 20} h={(w - 20) * 0.66} t={0} still /></g> : (
      <g>
        <circle cx={0} cy={-10} r={40} fill="#e8d2b8" />
        <path d={`M${-w / 2 + 14} ${h / 2} Q0 ${10} ${w / 2 - 14} ${h / 2}`} fill="#2a2a2a" />
      </g>
    )}
  </g>
);

const WallMap: React.FC<{ x: number; y: number; w?: number; h?: number; label?: string }> = ({ x, y, w = 520, h = 330, label }) => (
  <g transform={`translate(${x} ${y})`}>
    <rect x={-w / 2} y={-h / 2} width={w} height={h} fill="#cfe1e8" stroke={INK} strokeWidth={5} />
    <path d={`M${-w / 2 + 40} ${-h / 2 + 60} q60 -30 120 0 t110 30 q40 50 -10 90 t-120 20 q-60 -20 -90 -80 z M${40} ${-30} q50 -40 120 -20 q40 40 10 100 q-60 40 -110 0 z`} fill="#e8dcb8" stroke="#8a7a5a" strokeWidth={3} />
    <path d={`M${-w / 2 + 120} ${10} Q0 ${-60} ${110} ${20}`} stroke={C.red} strokeWidth={6} fill="none" strokeDasharray="14 10" />
    {[0, 1, 2].map((i) => <circle key={i} cx={-w / 2 + 90 + i * 140} cy={-h / 2 + 20} r={7} fill={C.red} stroke={INK} strokeWidth={2} />)}
    {label ? <text x={0} y={h / 2 - 16} textAnchor="middle" fontFamily={FONT.hand} fontSize={30} fill={INK}>{label}</text> : null}
  </g>
);

const Lamp: React.FC<{ x: number; y: number; on?: boolean }> = ({ x, y, on = true }) => (
  <g transform={`translate(${x} ${y})`}>
    <line x1={0} y1={-400} x2={0} y2={-40} stroke={INK} strokeWidth={3} />
    <path d="M-50 0 L-26 -44 L26 -44 L50 0 Z" fill="#3f5a4a" stroke={INK} strokeWidth={4} />
    {on ? <path d="M-50 0 L-300 520 L300 520 L50 0 Z" fill="#fff6c8" opacity={0.12} /> : null}
    <ellipse cx={0} cy={2} rx={22} ry={8} fill="#fff4b0" />
  </g>
);

const Sea: React.FC<{ y: number; t: number; time?: string; color?: string }> = ({ y, t, time, color }) => {
  const top = time === 'night' ? '#1c3550' : color ?? C.sea;
  const bot = time === 'night' ? '#0f2236' : C.seaDeep;
  return (
    <g>
      <defs>
        <linearGradient id="seag" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0" stopColor={top} />
          <stop offset="1" stopColor={bot} />
        </linearGradient>
      </defs>
      <rect x={X0} y={y} width={W} height={Y0 + H - y} fill="url(#seag)" />
      {Array.from({ length: 46 }, (_, i) => {
        const yy = y + 20 + rnd('w', i) * (Y0 + H - y - 40);
        const k = (yy - y) / (Y0 + H - y);
        const x = ((X0 + rnd('wx', i) * W + t * (10 + k * 30)) % W + W) % W + X0;
        const len = 30 + k * 90;
        return <path key={i} d={`M${x} ${yy} q${len / 2} ${-6 - k * 6} ${len} 0`} stroke="#fff" strokeOpacity={0.25 + 0.25 * Math.sin(t * 2 + i)} strokeWidth={2 + k * 3} fill="none" strokeLinecap="round" />;
      })}
    </g>
  );
};

const Building: React.FC<{ x: number; y: number; w: number; h: number; c: string; night?: boolean; seed: number; ruin?: boolean }> = ({ x, y, w, h, c, night, seed, ruin }) => {
  const cols = Math.max(2, Math.floor(w / 46));
  const rows = Math.max(2, Math.floor(h / 60));
  const top = ruin ? `M${x} ${y} V${y - h + 30} l${w * 0.2} -30 l${w * 0.15} 50 l${w * 0.25} -40 l${w * 0.2} 60 l${w * 0.2} -20 V${y} Z` : `M${x} ${y} V${y - h} H${x + w} V${y} Z`;
  return (
    <g>
      <path d={top} fill={c} stroke={INK} strokeWidth={3} />
      {Array.from({ length: rows * cols }, (_, i) => {
        const r = Math.floor(i / cols), cc = i % cols;
        const wy = y - h + 30 + r * 60;
        if (ruin && wy < y - h + 70) return null;
        const lit = night && rnd(seed, i) > 0.55;
        return <rect key={i} x={x + 14 + cc * ((w - 28) / cols)} y={wy} width={(w - 28) / cols - 14} height={30} fill={lit ? '#f6d77a' : night ? '#24324d' : '#9fc4d8'} stroke={INK} strokeWidth={2} />;
      })}
    </g>
  );
};

export const SetBackground: React.FC<SetProps> = (p) => (
  <g>
    {RICH_SETS.has(p.kind) ? <RichSet {...p} /> : <BaseSet {...p} />}
    <Lighting {...p} />
  </g>
);

const BaseSet: React.FC<SetProps> = (p) => {
  const { kind, t } = p;
  const time = (p.time as string) ?? 'day';
  const night = time === 'night';
  const groundY = (p.ground as number) ?? 900;
  const flagN = p.flag as string | undefined;
  const wall = (p.wall as string) ?? undefined;

  switch (kind) {
    // ---------------- kit: rooms and streets assembled from modules (src/sets/Kit.tsx) ----------------
    case 'room':
      return <RoomKit {...p} />;
    case 'town':
      return <TownKit {...p} />;
    // ---------------- composed landscapes: sky, plates, far layers, ground, road, far rows of assets (src/sets/Compose.tsx) ----------------
    case 'compose':
      return <ComposeSet p={p} t={t} />;
    // ---------------- interiors ----------------
    case 'office':
    case 'study': {
      return (
        <g>
          <Wall color={wall ?? '#cdb98f'} y={groundY - 120} wainscot="#8a5a33" paper />
          <Window x={1180} y={130} w={330} h={420} time={time} curtains="#7a2a2a" />
          {p.portrait !== false ? <Portrait x={560} y={300} flagOf={p.portraitFlag as string | undefined} /> : null}
          {flagN ? <g transform="translate(180 120)"><FlagStand nation={flagN} t={t} /></g> : null}
          {p.map ? <WallMap x={560} y={330} label={p.map as string} /> : null}
          <WallClock x={1650} y={220} t={t} time={p.clockTime as string} />
          <Floor y={groundY - 120} color="#6b4a32" boards />
          {p.shelf ? <Bookshelf x={1640} y={groundY - 540} /> : null}
          {p.desk !== false ? <Desk x={960} y={groundY - 60} w={(p.deskW as number) ?? 1100} /> : null}
          {p.lamp ? <Lamp x={960} y={240} /> : null}
          {night ? <rect x={X0} y={Y0} width={W} height={H} fill="#0a1430" opacity={0.35} /> : null}
        </g>
      );
    }
    case 'cabinet':
    case 'conference': {
      return (
        <g>
          <Wall color={wall ?? '#e8dcbc'} y={groundY - 160} wainscot="#7a5a3a" />
          {[220, 1340].map((x, i) => <Window key={i} x={x} y={120} w={300} h={380} time={time} curtains="#b08a3a" />)}
          <Portrait x={960} y={260} flagOf={p.portraitFlag as string | undefined} />
          <WallClock x={1720} y={300} t={t} time={p.clockTime as string} />
          <Floor y={groundY - 160} color="#7a2a2a" />
          <Desk x={960} y={groundY - 90} w={1700} cloth={(p.cloth as string) ?? '#2f6b3a'} />
        </g>
      );
    }
    case 'warroom':
    case 'bunker': {
      const bunker = kind === 'bunker';
      return (
        <g>
          <Wall color={wall ?? (bunker ? '#8e8a80' : '#4a4f55')} y={groundY - 120} />
          {bunker ? Array.from({ length: 14 }, (_, i) => <line key={i} x1={X0} y1={Y0 + i * 100} x2={X0 + W} y2={Y0 + i * 100} stroke="#000" opacity={0.08} strokeWidth={4} />) : null}
          <path d={`M${X0} 60 H${X0 + W}`} stroke="#6a6a6a" strokeWidth={22} />
          <path d={`M${X0} 100 H${X0 + W}`} stroke="#555" strokeWidth={12} />
          <WallMap x={960} y={360} w={900} h={460} label={p.map as string | undefined} />
          {bunker ? <Lamp x={480} y={200} /> : null}
          {flagN ? <g transform="translate(180 160)"><FlagStand nation={flagN} t={t} /></g> : null}
          <Floor y={groundY - 120} color={bunker ? '#5d5a52' : '#3a3632'} />
          {p.desk !== false ? <Desk x={960} y={groundY - 60} w={1300} color="#5a4030" /> : null}
          <rect x={X0} y={Y0} width={W} height={H} fill="#1a1408" opacity={bunker ? 0.18 : 0.1} />
        </g>
      );
    }
    case 'codebreak':
    case 'classroom': {
      return (
        <g>
          <Wall color={wall ?? '#b89a6a'} y={groundY - 120} />
          <rect x={460} y={120} width={1000} height={520} fill="#2f4a3a" stroke="#6b4a2a" strokeWidth={18} />
          <path d="M520 240 q40 -10 80 0 m40 0 q40 -10 80 0 M520 330 h300 M520 420 q120 -20 240 0" stroke="#e8efe8" strokeOpacity={0.35} strokeWidth={4} fill="none" />
          {[0, 1, 2, 3, 4].map((i) => <rect key={i} x={1560 + (i % 2) * 70} y={500 + Math.floor(i / 2) * 50} width={66} height={44} fill="#d9cfb8" stroke={INK} strokeWidth={3} />)}
          <WallClock x={1700} y={220} t={t} time={p.clockTime as string} />
          <Floor y={groundY - 120} color="#6b5a46" boards />
          {p.desk !== false ? <Desk x={760} y={groundY - 60} w={900} /> : null}
          <Lamp x={1200} y={150} />
        </g>
      );
    }
    case 'kitchen':
    case 'home': {
      return (
        <g>
          <Wall color={wall ?? '#e6d3a8'} y={groundY - 120} paper />
          <Window x={1240} y={180} w={300} h={320} time={time} curtains="#a85a4a" />
          <WallClock x={600} y={240} t={t} time={p.clockTime as string} />
          <rect x={360} y={420} width={160} height={110} rx={10} fill="#7a4a2a" stroke={INK} strokeWidth={4} />
          <circle cx={400} cy={475} r={26} fill="#d9c49a" stroke={INK} strokeWidth={3} />
          <rect x={440} y={445} width={60} height={14} fill="#2a2a2a" />
          <Floor y={groundY - 120} color="#8a6a4a" boards />
          {p.desk !== false ? <Desk x={960} y={groundY - 60} w={900} cloth="#e9e1cf" /> : null}
          {night ? <rect x={X0} y={Y0} width={W} height={H} fill="#0a1430" opacity={0.3} /> : null}
        </g>
      );
    }
    case 'factory': {
      return (
        <g>
          <Wall color={wall ?? '#8a8070'} y={groundY - 80} />
          {Array.from({ length: 9 }, (_, i) => <path key={i} d={`M${X0 + i * 300} ${Y0} L${X0 + i * 300 + 150} 120 L${X0 + i * 300 + 300} ${Y0}`} stroke="#5a5048" strokeWidth={14} fill="none" />)}
          <rect x={X0} y={110} width={W} height={20} fill="#5a5048" />
          {Array.from({ length: 6 }, (_, i) => <Window key={i} x={X0 + 120 + i * 400} y={200} w={220} h={160} time={time} />)}
          <Floor y={groundY - 80} color="#5a564e" />
          {[0, 1, 2].map((i) => (
            <g key={i} transform={`translate(${240 + i * 600} ${groundY - 80})`}>
              <rect x={-150} y={-230} width={300} height={230} fill="#6d7a6a" stroke={INK} strokeWidth={4} />
              <rect x={-110} y={-200} width={220} height={60} fill="#4a5448" stroke={INK} strokeWidth={3} />
              <circle cx={-70} cy={-80} r={34} fill="#3a4038" stroke={INK} strokeWidth={4} />
              <circle cx={50} cy={-80} r={24} fill="#c8352b" stroke={INK} strokeWidth={4} />
              <path d={`M-150 -20 h300`} stroke="#3a3a3a" strokeWidth={10} />
            </g>
          ))}
          <rect x={X0} y={groundY - 30} width={W} height={26} fill="#3a3a3a" />
          {Array.from({ length: 30 }, (_, i) => <circle key={i} cx={((X0 + i * 80 + t * 120) % W + W) % W + X0} cy={groundY - 17} r={8} fill="#666" stroke={INK} strokeWidth={2} />)}
        </g>
      );
    }
    case 'rally':
    case 'podium': {
      const nat = nation(flagN);
      return (
        <g>
          <Wall color={wall ?? '#3a3330'} y={groundY - 80} />
          {[260, 960, 1660].map((x, i) => (
            <g key={i}>
              {/* plain banners: the nation's own flag on top of a dark-blue drape with gold trim (no disc emblems) */}
              <rect x={x - 90} y={-100} width={180} height={720} fill="#2f3f5f" stroke={INK} strokeWidth={4} />
              <path d={`M${x - 78} -100 V608 M${x + 78} -100 V608`} stroke="#c9a24a" strokeWidth={6} />
              {flagN ? <g transform={`translate(${x - 80} 120)`}><Flag nation={flagN} w={160} h={106} t={t} still /></g> : null}
              <path d={`M${x - 90} 620 L${x} 680 L${x + 90} 620 Z`} fill="#2f3f5f" stroke={INK} strokeWidth={4} />
            </g>
          ))}
          <Floor y={groundY - 80} color="#4a3a32" />
          <path d={`M720 ${groundY - 80} L760 ${groundY - 330} H1160 L1200 ${groundY - 80} Z`} fill="#6b4a32" stroke={INK} strokeWidth={4} />
          {Array.from({ length: 40 }, (_, i) => <circle key={i} cx={X0 + 40 + i * 62} cy={groundY + 120 + (i % 2) * 30} r={36} fill="#2a2420" />)}
        </g>
      );
    }
    case 'studio':
    case 'paper':
    case 'void': {
      const c = (p.color as string) ?? (kind === 'paper' ? '#efe4c8' : '#e6dcc4');
      return (
        <g>
          <rect x={X0} y={Y0} width={W} height={H} fill={c} />
          <radialGradient id="vg"><stop offset="0.5" stopColor="#000" stopOpacity={0} /><stop offset="1" stopColor="#000" stopOpacity={0.22} /></radialGradient>
          <rect x={X0} y={Y0} width={W} height={H} fill="url(#vg)" />
        </g>
      );
    }
    case 'dark':
    case 'memorial': {
      return (
        <g>
          <rect x={X0} y={Y0} width={W} height={H} fill={(p.color as string) ?? '#14151a'} />
          <radialGradient id="mg"><stop offset="0" stopColor="#3a3020" stopOpacity={0.6} /><stop offset="1" stopColor="#000" stopOpacity={0} /></radialGradient>
          <ellipse cx={960} cy={600} rx={700} ry={500} fill="url(#mg)" />
        </g>
      );
    }
    // ---------------- exteriors ----------------
    case 'sea':
    case 'ocean': {
      const hz = (p.horizon as number) ?? 560;
      return (
        <g>
          <Sky time={time} id="skysea" horizon={hz} />
          {time !== 'night' ? <Clouds t={t} n={7} y={60} seed="sea" /> : null}
          <Sea y={hz} t={t} time={time} />
        </g>
      );
    }
    case 'sky':
    case 'air': {
      const hz = (p.horizon as number) ?? 1000;
      return (
        <g>
          <Sky time={time} id="skyair" horizon={hz} />
          <Clouds t={t * 4} n={9} y={-40} seed="air" />
          {p.below === 'sea' ? <Sea y={hz} t={t} time={time} /> : <Hills y={hz + 60} color="#8fae6a" amp={40} />}
          <Clouds t={t * 8} n={5} y={500} seed="air2" />
        </g>
      );
    }
    case 'beach': {
      return (
        <g>
          <Sky time={time} id="skyb" horizon={520} />
          <Clouds t={t} n={5} y={60} seed="b" />
          <Sea y={520} t={t} time={time} />
          <path d={`M${X0} 760 Q600 700 1200 740 T${X0 + W} 720 V${Y0 + H} H${X0} Z`} fill="#e3cc94" />
          <path d={`M${X0} 760 Q600 700 1200 740 T${X0 + W} 720`} stroke="#fff" strokeWidth={6} strokeOpacity={0.7} fill="none" />
          {p.cliffs ? <path d={`M1500 760 L1560 420 L1760 380 L1900 440 L${X0 + W} 420 V760 Z`} fill="#c9c0a8" stroke={INK} strokeWidth={4} /> : null}
        </g>
      );
    }
    case 'field':
    case 'countryside':
    case 'steppe':
    case 'snow':
    case 'desert':
    case 'mud': {
      const snow = kind === 'snow' || p.weather === 'snow';
      const desert = kind === 'desert';
      const mud = kind === 'mud';
      const hz = (p.horizon as number) ?? 600;
      const g1 = snow ? '#eef2f5' : desert ? '#e2c48a' : mud ? '#8a7050' : C.grass;
      const g2 = snow ? '#dfe6ec' : desert ? '#d4b072' : mud ? '#6e5638' : '#89a64c';
      const road = p.road !== false;
      return (
        <g>
          <Sky time={snow ? (time === 'day' ? 'snow' : time) : desert && time === 'day' ? 'day' : time} id="skyf" horizon={hz} />
          {desert ? <circle cx={1500} cy={180} r={70} fill="#fff4c8" /> : null}
          {!night ? <Clouds t={t} n={6} y={40} seed={kind} tone={snow ? '#f4f6f8' : undefined} /> : null}
          <Hills y={hz + 30} color={snow ? '#d4dde4' : desert ? '#d9b97c' : '#7f9c5a'} amp={70} seed="far" />
          <rect x={X0} y={hz + 30} width={W} height={Y0 + H - hz - 30} fill={g2} />
          <path d={`M${X0} ${hz + 60} Q600 ${hz + 20} 1200 ${hz + 70} T${X0 + W} ${hz + 50} V${Y0 + H} H${X0} Z`} fill={g1} />
          {road ? <path d={`M900 ${hz + 50} L1020 ${hz + 50} L1500 ${Y0 + H} L420 ${Y0 + H} Z`} fill={snow ? '#cfd6dc' : desert ? '#c9a466' : '#b9925f'} opacity={0.9} /> : null}
          {p.poles !== false && !desert ? (() => {
            const ps = Array.from({ length: 6 }, (_, i) => ({ x: 1080 + i * i * 34 + i * 30, y: hz + 60 + i * i * 22 + i * 12, h: 50 + i * 34 }));
            return (
              <g>
                {ps.slice(1).map((q, i) => {
                  const a0 = ps[i];
                  return [0.04, 0.12].map((k) => <path key={i + '_' + k} d={`M${a0.x} ${a0.y - a0.h * (1 - k)} Q${(a0.x + q.x) / 2} ${(a0.y - a0.h * (1 - k) + q.y - q.h * (1 - k)) / 2 + 6 + i * 3} ${q.x} ${q.y - q.h * (1 - k)}`} stroke="#3a3230" strokeWidth={1.2} fill="none" opacity={0.6} />);
                })}
                {ps.map((q, i) => <Pole key={i} x={q.x} y={q.y} h={q.h} />)}
              </g>
            );
          })() : null}
          {(p.houses ?? !desert) ? [[-60, hz + 52, 0.55], [180, hz + 46, 0.45], [1700, hz + 48, 0.5]].map(([x, y, s], i) => <House key={i} x={x} y={y} s={s} snow={snow} />) : null}
          {!desert ? [[300, hz + 220, 1], [1650, hz + 260, 1.2], [60, hz + 340, 1.4]].map(([x, y, s], i) => <Tree key={i} x={x} y={y} s={s} kind={snow ? (i % 2 ? 'bare' : 'pine') : (p.trees as string) ?? 'round'} snow={snow} />) : null}
          {desert ? [[200, hz + 200], [1500, hz + 180]].map(([x, y], i) => <path key={i} d={`M${x} ${y} q20 -40 40 0 q20 -60 50 0`} stroke="#7a8a4a" strokeWidth={10} fill="none" />) : null}
          {mud ? Array.from({ length: 10 }, (_, i) => <ellipse key={i} cx={200 + rnd('p', i) * 1600} cy={hz + 160 + rnd('q', i) * 400} rx={60 + rnd('r', i) * 80} ry={12 + rnd('s', i) * 10} fill="#5a4a3a" opacity={0.6} />) : null}
        </g>
      );
    }
    case 'jungle': {
      return (
        <g>
          <Sky time={time} id="skyj" horizon={500} />
          <rect x={X0} y={400} width={W} height={1000} fill="#4f7a3a" />
          {Array.from({ length: 14 }, (_, i) => <Tree key={i} x={X0 + i * 190 + rnd('j', i) * 60} y={560 + rnd('jy', i) * 200} s={1 + rnd('js', i) * 0.6} kind={i % 3 ? 'palm' : 'round'} />)}
          <rect x={X0} y={820} width={W} height={600} fill="#3f6630" />
        </g>
      );
    }
    case 'city':
    case 'ruins':
    case 'street': {
      const ruin = kind === 'ruins' || p.ruined === true;
      const hz = groundY - 60;
      return (
        <g>
          <Sky time={time} id="skyc" horizon={hz} />
          {!night ? <Clouds t={t} n={5} y={40} seed="city" /> : null}
          {Array.from({ length: 16 }, (_, i) => (
            <Building key={'b' + i} x={X0 + i * 160} y={hz - 120} w={150} h={200 + rnd('bh', i) * 240} c={night ? '#2a3448' : '#9aa2a8'} night={night} seed={i} ruin={ruin} />
          ))}
          {Array.from({ length: 9 }, (_, i) => (
            <Building key={'f' + i} x={X0 + i * 290} y={hz} w={260} h={280 + rnd('fh', i) * 220} c={['#c98f62', '#b9a27a', '#a86a52', '#d4c09a'][i % 4]} night={night} seed={i + 40} ruin={ruin} />
          ))}
          <rect x={X0} y={hz} width={W} height={Y0 + H - hz} fill="#7d7a74" />
          <rect x={X0} y={hz} width={W} height={30} fill="#a9a59c" />
          {ruin ? Array.from({ length: 18 }, (_, i) => <path key={i} d={`M${X0 + rnd('r', i) * W} ${hz + 40 + rnd('ry', i) * 300} l30 -30 l40 10 l20 30 z`} fill="#8a8278" stroke={INK} strokeWidth={2} />) : null}
          {night ? <rect x={X0} y={Y0} width={W} height={H} fill="#081025" opacity={0.25} /> : null}
        </g>
      );
    }
    case 'harbor':
    case 'dock': {
      return (
        <g>
          <Sky time={time} id="skyh" horizon={560} />
          {!night ? <Clouds t={t} n={5} y={50} seed="h" /> : null}
          <path d={`M${X0} 560 L300 470 L600 520 L1000 450 L1400 510 L1800 460 L${X0 + W} 520 V600 H${X0} Z`} fill="#8a9a8a" opacity={0.7} />
          <Sea y={560} t={t} time={time} />
          <rect x={X0} y={groundY - 60} width={W} height={Y0 + H - groundY + 60} fill="#8a7a62" stroke={INK} strokeWidth={4} />
          <rect x={X0} y={groundY - 60} width={W} height={18} fill="#6a5a46" />
          {[300, 1600].map((x, i) => (
            <g key={i} stroke={INK} strokeWidth={4} fill="#c8a03a">
              <path d={`M${x} ${groundY - 60} V200 M${x - 40} ${groundY - 60} L${x} 300 L${x + 40} ${groundY - 60}`} fill="none" stroke="#6a5a3a" strokeWidth={10} />
              <path d={`M${x - 60} 210 H${x + 380}`} stroke="#c8a03a" strokeWidth={16} />
              <line x1={x + 300} y1={210} x2={x + 300} y2={400} stroke={INK} strokeWidth={3} />
            </g>
          ))}
        </g>
      );
    }
    case 'nomansland': {
      // WW1 no man's land: churned grey-brown earth, water-filled craters, shattered stumps, wire pickets,
      // smoke columns drifting on the horizon. horizon: ground line height (lower it, e.g. 820, for figures against the sky)
      const snow = p.weather === 'snow';
      const hz = (p.horizon as number) ?? 560;
      const g1 = snow ? '#d9dcd8' : '#7a6650';
      const g2 = snow ? '#c4c8c2' : '#665440';
      const pit = snow ? '#9aa09a' : '#4a3c2e';
      const water = time === 'dusk' || time === 'dawn' ? '#d9a27a' : night ? '#2a3550' : '#8c9aa4';
      const dark = time === 'dusk' || time === 'dawn' || night;
      return (
        <g>
          <Sky time={time === 'day' ? (snow ? 'snow' : 'storm') : time} id="skyn" horizon={hz} />
          {time === 'dusk' || time === 'dawn' ? <circle cx={1380} cy={hz - 60} r={120} fill="#ffd9a0" opacity={0.85} /> : null}
          {/* smoke columns on the horizon (slow drift) */}
          {Array.from({ length: 5 }, (_, i) => {
            const x = X0 + 260 + i * 470 + rnd('nsx', i) * 120;
            return (
              <g key={i} opacity={dark ? 0.35 : 0.55}>
                {[0, 1, 2, 3].map((k) => (
                  <circle key={k} cx={x + k * 26 + Math.sin(t * 0.4 + i + k) * 10 + t * 4 * k} cy={hz + 10 - k * 70 - ((t * 6) % 30)} r={40 + k * 22} fill={dark ? '#6a5a5a' : '#8f8a84'} />
                ))}
              </g>
            );
          })}
          <Hills y={hz + 20} color={dark ? '#4a3c38' : snow ? '#b9bcb6' : '#6c604e'} amp={30} seed="nml" />
          <rect x={X0} y={hz + 20} width={W} height={Y0 + H - hz - 20} fill={dark ? '#4a3a2c' : g2} />
          <path d={`M${X0} ${hz + 40} Q500 ${hz + 10} 1100 ${hz + 46} T${X0 + W} ${hz + 30} V${Y0 + H} H${X0} Z`} fill={dark ? '#5a4634' : g1} />
          {/* craters, far small -> near big */}
          {Array.from({ length: 14 }, (_, i) => {
            const d = rnd('ncy', i);
            const y = hz + 60 + d * d * (Y0 + H - hz - 120);
            const r = 40 + d * 170;
            const x = X0 + rnd('ncx', i) * W;
            return (
              <g key={i}>
                <ellipse cx={x} cy={y - r * 0.05} rx={r * 1.08} ry={r * 0.26} fill={snow ? '#e8ebe8' : '#8a7458'} opacity={dark ? 0.5 : 1} />
                <ellipse cx={x} cy={y} rx={r} ry={r * 0.22} fill={pit} />
                {i % 3 === 0 ? <ellipse cx={x + r * 0.1} cy={y + r * 0.04} rx={r * 0.6} ry={r * 0.1} fill={water} opacity={0.75} /> : null}
              </g>
            );
          })}
          {/* shattered stumps */}
          {Array.from({ length: 7 }, (_, i) => {
            const d = rnd('nsy', i);
            const y = hz + 30 + d * 300;
            const s = 0.5 + d * 1.2;
            const x = X0 + 100 + rnd('nsx2', i) * (W - 200);
            return (
              <g key={i} transform={`translate(${x} ${y}) scale(${s})`}>
                <path d="M-14 0 L-10 -150 L-2 -170 L4 -140 L10 -160 L14 0 Z" fill={dark ? '#2e2420' : '#4a3a2e'} stroke={INK} strokeWidth={3} strokeLinejoin="round" />
                {i % 2 ? <path d="M-6 -100 L-46 -130" stroke={dark ? '#2e2420' : '#4a3a2e'} strokeWidth={8} strokeLinecap="round" /> : null}
              </g>
            );
          })}
          {/* wire pickets */}
          {p.wire !== false
            ? Array.from({ length: 9 }, (_, i) => {
                const x = X0 + 120 + i * 270;
                const y = hz + 130 + (i % 2) * 14;
                return (
                  <g key={i} stroke={dark ? '#20201e' : '#3a3530'} fill="none">
                    <line x1={x} y1={y} x2={x} y2={y - 64} strokeWidth={6} />
                    <path d={`M${x} ${y - 56} q60 22 120 -2 t150 4 M${x} ${y - 30} q70 -18 140 4 t130 -6`} strokeWidth={2} />
                  </g>
                );
              })
            : null}
          {snow ? Array.from({ length: 30 }, (_, i) => <ellipse key={i} cx={X0 + rnd('sn', i) * W} cy={hz + 60 + rnd('sny', i) * 700} rx={30 + rnd('snr', i) * 60} ry={6} fill="#f2f4f2" opacity={0.7} />) : null}
          {dark ? <rect x={X0} y={hz + 20} width={W} height={Y0 + H - hz} fill="#1a1020" opacity={0.18} /> : null}
        </g>
      );
    }
    case 'trench': {
      return (
        <g>
          <Sky time={time === 'day' ? 'storm' : time} id="skyt" horizon={420} />
          <rect x={X0} y={380} width={W} height={200} fill="#6e5a42" />
          {Array.from({ length: 30 }, (_, i) => <rect key={i} x={X0 + i * 84} y={350 + (i % 2) * 10} width={86} height={44} rx={14} fill="#c9b48a" stroke={INK} strokeWidth={3} />)}
          <rect x={X0} y={420} width={W} height={1000} fill="#7d6648" />
          {Array.from({ length: 24 }, (_, i) => <line key={i} x1={X0 + i * 110} y1={440} x2={X0 + i * 110} y2={groundY - 40} stroke="#5a4630" strokeWidth={10} />)}
          <rect x={X0} y={groundY - 40} width={W} height={300} fill="#5a4630" />
          {Array.from({ length: 30 }, (_, i) => <rect key={i} x={X0 + i * 90} y={groundY - 40} width={70} height={16} fill="#8a6a42" stroke={INK} strokeWidth={2} />)}
        </g>
      );
    }
    case 'railway':
    case 'station': {
      const hz = 640;
      return (
        <g>
          <Sky time={time} id="skyr" horizon={hz} />
          {!night ? <Clouds t={t} n={5} y={60} seed="r" /> : null}
          <Hills y={hz} color="#8fae6a" amp={60} seed="rr" />
          <rect x={X0} y={hz} width={W} height={Y0 + H - hz} fill="#9cb85a" />
          {Array.from({ length: 12 }, (_, i) => <Pole key={i} x={X0 + i * 220} y={hz + 140} h={160} />)}
          <rect x={X0} y={groundY - 20} width={W} height={50} fill="#8a7a6a" />
          {Array.from({ length: 50 }, (_, i) => <rect key={i} x={X0 + i * 50} y={groundY - 14} width={26} height={40} fill="#6b4a32" />)}
          <path d={`M${X0} ${groundY - 6} H${X0 + W} M${X0} ${groundY + 18} H${X0 + W}`} stroke="#4a4a4a" strokeWidth={8} />
        </g>
      );
    }
    default:
      return <rect x={X0} y={Y0} width={W} height={H} fill="#e6dcc4" />;
  }
};

export const FlagStand: React.FC<{ nation: string; t: number }> = ({ nation: n, t }) => (
  <g>
    <line x1={0} y1={0} x2={0} y2={560} stroke="#7a5a3a" strokeWidth={10} />
    <circle cx={0} cy={-6} r={10} fill="#c9a24a" stroke={INK} strokeWidth={3} />
    <g transform="translate(5 10)"><Flag nation={n} w={190} h={126} t={t} /></g>
  </g>
);
