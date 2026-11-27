import React from 'react';
import { rnd } from '../lib/anim';

/**
 * Weather over the whole frame (screen coordinates, drawn above the world, below the captions).
 *
 *   "weather": "rain"                                        a name with its usual strength
 *   "weather": {"kind": "rain", "amount": 0.9, "wind": 0.4}  amount 0..1 (drizzle 0.3 · rain 0.6 · downpour 1), wind -1..1 (slant / drift)
 *
 * kinds: rain · drizzle · downpour · snow · blizzard · haze · fog · dust · sandstorm · ash · leaves · petals · lightning
 * ("flash": [seconds…] for lightning at exact moments; otherwise a flash every few seconds). In a composed place the far
 * distance also fades into the haze/fog/dust (src/sets/Compose.tsx). Indoors (rooms) nothing falls.
 */
export type WeatherSpec = string | { kind?: string; amount?: number; wind?: number; flash?: number[] };

const DEFAULT_AMOUNT: Record<string, number> = { drizzle: 0.3, rain: 0.6, downpour: 1, snow: 0.5, blizzard: 1, haze: 0.6, fog: 0.6, dust: 0.5, sandstorm: 1, ash: 0.5, leaves: 0.5, petals: 0.5, lightning: 0.9 };
export const WEATHER_KINDS = Object.keys(DEFAULT_AMOUNT);

export const weatherOf = (w: WeatherSpec | undefined) => {
  if (!w) return null;
  const kind = typeof w === 'string' ? w : w.kind ?? 'rain';
  const amount = (typeof w === 'object' && w.amount !== undefined ? w.amount : DEFAULT_AMOUNT[kind]) ?? 0.5;
  const wind = typeof w === 'object' && w.wind !== undefined ? w.wind : kind === 'sandstorm' || kind === 'blizzard' ? 0.8 : 0.2;
  return { kind, amount, wind, flash: typeof w === 'object' ? w.flash : undefined };
};

const Veil: React.FC<{ c: string; top: number; bottom: number; id: string }> = ({ c, top, bottom, id }) => (
  <g>
    <defs>
      <linearGradient id={id} x1="0" y1="0" x2="0" y2="1">
        <stop offset="0" stopColor={c} stopOpacity={top} />
        <stop offset="1" stopColor={c} stopOpacity={bottom} />
      </linearGradient>
    </defs>
    <rect x={-20} y={-20} width={1960} height={1120} fill={`url(#${id})`} />
  </g>
);

const Falling: React.FC<{ n: number; t: number; seed: string; speed: number; wind: number; draw: (x: number, y: number, i: number) => React.ReactNode }> = ({ n, t, seed, speed, wind, draw }) => (
  <g>
    {Array.from({ length: n }, (_, i) => {
      const sp = speed * (0.8 + rnd(seed, i, 's') * 0.4);
      const y = ((rnd(seed, i, 'y') * 1200 + t * sp) % 1200) - 60;
      const x = ((((rnd(seed, i) * 2300 + (y + 60) * wind) % 2300) + 2300) % 2300) - 190;
      return <React.Fragment key={i}>{draw(x, y, i)}</React.Fragment>;
    })}
  </g>
);

export const Weather: React.FC<{ w: WeatherSpec; t: number; seed?: string }> = ({ w, t, seed = 'wx' }) => {
  const W = weatherOf(w);
  if (!W) return null;
  const { kind, amount: a, wind } = W;
  const id = `wx_${seed}_${kind}`;
  switch (kind) {
    case 'drizzle':
    case 'rain':
    case 'downpour':
    case 'lightning': {
      const n = Math.round(40 + 320 * a);
      const len = 16 + 34 * a;
      const flashes = kind === 'lightning' ? W.flash ?? Array.from({ length: 12 }, (_, i) => 1.2 + i * 4.2 + rnd(seed, i, 'f') * 2) : [];
      const since = flashes.filter((f) => f <= t).map((f) => t - f);
      const fa = since.length ? Math.min(...since) : 99;
      const flash = fa < 0.35 ? (fa < 0.06 || (fa > 0.12 && fa < 0.18) ? 0.55 : 0.2) * (1 - fa / 0.35) : 0;
      const bx = 300 + rnd(seed, Math.floor(t / 4), 'bx') * 1300;
      return (
        <g>
          <Veil c="#5d6670" top={0.1 + 0.22 * a} bottom={0.04 + 0.1 * a} id={id} />
          <Falling n={n} t={t} seed={seed} speed={850 + 550 * a} wind={wind * 0.35} draw={(x, y, i) => (
            <line x1={x} y1={y} x2={x + len * wind * 0.35} y2={y + len} stroke="#d3e3ee" strokeWidth={a > 0.8 ? 3 : 2.2} opacity={0.35 + 0.35 * rnd(seed, i, 'o')} strokeLinecap="round" />
          )} />
          {a > 0.5 ? Array.from({ length: Math.round(30 * a) }, (_, i) => {
            const life = 0.35, k = ((t + rnd(seed, i, 'sp') * life) % life) / life;
            const x = rnd(seed, i, 'sx') * 1920, y = 760 + rnd(seed, i, 'sy') * 320;
            return <ellipse key={i} cx={x} cy={y} rx={4 + k * 14} ry={1.5 + k * 3} fill="none" stroke="#e3eef5" strokeWidth={2} opacity={(1 - k) * 0.6} />;
          }) : null}
          {flash > 0 ? (
            <g>
              <rect x={-20} y={-20} width={1960} height={1120} fill="#f4f7ff" opacity={flash} />
              {fa < 0.2 ? <path d={`M${bx} -10 L${bx - 40} 160 L${bx + 10} 170 L${bx - 50} 380 L${bx + 5} 390 L${bx - 30} 560`} stroke="#fffbe8" strokeWidth={6} fill="none" opacity={0.9} /> : null}
            </g>
          ) : null}
        </g>
      );
    }
    case 'snow':
    case 'blizzard':
    case 'ash': {
      const ash = kind === 'ash';
      return (
        <g>
          {kind === 'blizzard' ? <Veil c="#eef3f7" top={0.35 * a} bottom={0.2 * a} id={id} /> : null}
          {ash ? <Veil c="#6a645e" top={0.18 * a} bottom={0.08 * a} id={id} /> : null}
          <Falling n={Math.round(40 + 200 * a)} t={t} seed={seed} speed={ash ? 45 : 70 + 120 * (kind === 'blizzard' ? 1 : 0)} wind={wind * (kind === 'blizzard' ? 1.6 : 0.4)} draw={(x, y, i) => (
            <circle cx={x + Math.sin(t * 1.3 + i) * 14} cy={y} r={(ash ? 2 : 2.5) + rnd(seed, i, 'r') * (ash ? 2.5 : 4)} fill={ash ? '#8a847c' : '#fff'} opacity={ash ? 0.7 : 0.88} />
          )} />
        </g>
      );
    }
    case 'haze':
      // humid tropical haze: soft, warm, strongest towards the horizon (the composed place fades the distance itself)
      return <Veil c="#f3efe3" top={0.16 * a} bottom={0.04 * a} id={id} />;
    case 'fog':
      return (
        <g>
          <Veil c="#e8ece9" top={0.28 * a} bottom={0.42 * a} id={id} />
          {Array.from({ length: 6 }, (_, i) => {
            const x = ((rnd(seed, i) * 2600 + t * (14 + i * 4) * (wind >= 0 ? 1 : -1)) % 2600 + 2600) % 2600 - 340;
            return <ellipse key={i} cx={x} cy={560 + rnd(seed, i, 'y') * 420} rx={420 + rnd(seed, i, 'r') * 300} ry={70 + rnd(seed, i, 'q') * 50} fill="#f2f4f2" opacity={0.22 * a + 0.1} />;
          })}
        </g>
      );
    case 'dust':
    case 'sandstorm': {
      const storm = kind === 'sandstorm';
      return (
        <g>
          <Veil c="#cfae7c" top={(storm ? 0.45 : 0.16) * a} bottom={(storm ? 0.3 : 0.08) * a} id={id} />
          {Array.from({ length: Math.round((storm ? 160 : 40) * a) }, (_, i) => {
            const sp = (storm ? 900 : 90) * (0.7 + rnd(seed, i, 's') * 0.6);
            const x = ((rnd(seed, i) * 2200 + t * sp * (wind >= 0 ? 1 : -1)) % 2200 + 2200) % 2200 - 140;
            const y = rnd(seed, i, 'y') * 1080 + Math.sin(t * 2 + i) * 8;
            return storm
              ? <line key={i} x1={x} y1={y} x2={x - 40} y2={y + 2} stroke="#e2c79a" strokeWidth={2} opacity={0.5} />
              : <circle key={i} cx={x} cy={y} r={1.5 + rnd(seed, i, 'r') * 2.5} fill="#e9d2a6" opacity={0.6} />;
          })}
        </g>
      );
    }
    case 'leaves':
    case 'petals': {
      const cs = kind === 'petals' ? ['#f2b8c6', '#f7d3dc', '#ffffff'] : ['#7a9a3a', '#c9a33a', '#b8652f', '#8aa04a'];
      return (
        <g>
          {Array.from({ length: Math.round(8 + 24 * a) }, (_, i) => {
            const sp = 60 + rnd(seed, i, 's') * 60;
            const y = ((rnd(seed, i, 'y') * 1200 + t * sp) % 1200) - 60;
            const x = ((rnd(seed, i) * 2300 + t * 120 * (wind >= 0 ? 1 : -1) * (0.5 + a) + Math.sin(t * 1.7 + i) * 40) % 2300 + 2300) % 2300 - 190;
            const r = (t * (90 + rnd(seed, i, 'rr') * 160) + i * 40) % 360;
            return (
              <g key={i} transform={`translate(${x} ${y}) rotate(${r}) scale(1 ${0.4 + 0.6 * Math.abs(Math.sin(t * 2 + i))})`}>
                <path d={kind === 'petals' ? 'M0 -7 Q6 0 0 7 Q-6 0 0 -7 Z' : 'M0 -11 Q9 -2 0 11 Q-9 -2 0 -11 Z'} fill={cs[i % cs.length]} stroke="#2a2622" strokeWidth={1.2} />
              </g>
            );
          })}
        </g>
      );
    }
    default:
      return null;
  }
};
