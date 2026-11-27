import React from 'react';
import { Drawing, type Part } from '../props/Drawing';
import { INK, SKIN, nation } from '../theme';
import { rnd, clamp } from '../lib/anim';

/**
 * Chibi puppet in the reference-channel style: a big round head sitting directly on a small tapered body
 * (the chin overlaps the collar — no neck gap), thin rubber-hose arms and legs drawn as smooth curves,
 * small mitten hands. Origin = between the feet. Height ≈ 280 px at scale 1 (hats add more).
 *
 * Motion: poses blend (easeOutBack) from the previous pose, idle hands drift, talking adds beat gestures
 * and head nods, walking/running uses a stride cycle with bent knees, lean and counter-swinging arms.
 */
export type CharSpec = {
  nation?: string;
  outfit?: string; // tunic | suit | navy | navywhite | coat | sailor | civil | dress | party | armor | robe | pilot | tweed
  color?: string; // jacket color override
  pants?: string;
  skin?: string;
  hair?: string; // side | back | bald | baldtop | short | part | curly | bun | long | messy | tousled | none
  hairColor?: string;
  facial?: string; // toothbrush | walrus | pencil | handlebar | beard | goatee | stubble | none
  hat?: string; // peaked | garrison | helmet_de | helmet_us | helmet_uk | helmet_su | helmet_jp | navy | navy_white | beret | bicorne | kepi | ushanka | fedora | tophat | pith | sailor | pilot | roman | crown | flatcap | none
  hatColor?: string;
  badge?: string; // hat badge color
  glasses?: string; // round | pince | sun | none
  extra?: string[]; // cigar pipe medals armband epaulettes tie bowtie scarf monocle wrinkles jowls blush vest
  eyes?: string; // dot | lid | big
  build?: number; // 0.85 thin .. 1.3 fat
  age?: number; // 0 young .. 1 old (wrinkles, grey)
  female?: boolean;
  scarf?: string; // scarf colour (with extra 'scarf')
  vest?: string; // vest colour (tweed / suit with extra 'vest')
  shadeFace?: boolean; // pale face with cool grey shading on the lower half (narrator style)
  tie?: string; // tie colour for trench / suit
  /** sleeve colour (default: the jacket); the skin colour = bare arms (a singlet, a sleeveless vest) */
  armColor?: string;
  /** costume pieces drawn on the rig (library/costumes): slot back | hips | body | headback | head; parts in that slot's frame */
  wear?: { slot: string; parts: Part[]; above?: boolean }[];
};

export type CharState = {
  pose?: string;
  prevPose?: string; // pose we are blending from
  poseK?: number; // 0..1 blend progress (1 = settled)
  expr?: string;
  talk?: boolean;
  walk?: number; // >0 = walking (set automatically when x/at is keyframed)
  run?: boolean;
  dir?: number; // walking direction in local space: 1 = right, -1 = left
  look?: number; // -1 left .. 1 right (pupil offset)
  view?: 'front' | 'back';
  seated?: boolean;
  kneel?: boolean;
  /** seconds since the held rifle last fired (a muzzle flash shows for ~0.07 s); undefined = not firing */
  muzzle?: number;
  headMove?: string; // nod | shake | tilt
  /** 3/4 view of the face: -1 (turned to screen-left) .. 1 (turned to screen-right); 0 = full front */
  turn?: number;
  /** seconds since the expression last changed (drives the anticipation squash + take) */
  exprAge?: number;
  /** size of the take on an expression change (default 1) */
  take?: number;
  /** stride phase in radians, driven by the distance walked (falls back to time) */
  gait?: number;
  /** seconds the current pose change lasts (for overlap timing) */
  poseDur?: number;
  /** the pose change moves the hands far: add a little anticipation */
  bigMove?: boolean;
  /** walking style: shuffle (hungry, exhausted) | march (parade) | limp (wounded) | sneak (crouched) */
  gaitStyle?: string;
  /** riding a bicycle: sits higher (on the saddle) and the feet go round the crank */
  ride?: boolean;
  /** pedal angle in radians (follows the distance ridden) */
  pedal?: number;
  /** the thing ridden (a bicycle), drawn under the rider: its parts and anchors in its own units (seat = under the hips,
   *  crank = the centre the feet go round), its size; `travel` = distance ridden in the rider's units (turns roll wheels) */
  rideWith?: { parts: Part[]; seat?: number[]; crank?: number[]; size?: number };
  rideTravel?: number;
};

export type Held = { node: React.ReactNode; scale?: number; rotate?: number; dx?: number; dy?: number; both?: boolean; grip?: number;
  /** long arms: prop-local x of the right-hand grip and the left-hand grip on the axis y = 0 */
  grips?: [number, number] };

const Lw = 4;
const ARM_INK = 16.5, ARM_FILL = 9.5;
const LEG_INK = 19, LEG_FILL = 11.5;

type V = { x: number; y: number };
// 2-bone IK: returns joint position given root, end target, lengths, bend direction
function ik(sx: number, sy: number, hx: number, hy: number, l1: number, l2: number, bend: number) {
  let dx = hx - sx, dy = hy - sy;
  let d = Math.hypot(dx, dy) || 0.001;
  const max = l1 + l2 - 0.5;
  if (d > max) {
    dx *= max / d;
    dy *= max / d;
    hx = sx + dx;
    hy = sy + dy;
    d = max;
  }
  const a = (l1 * l1 - l2 * l2 + d * d) / (2 * d);
  const h = Math.sqrt(Math.max(0, l1 * l1 - a * a));
  const mx = sx + (dx * a) / d, my = sy + (dy * a) / d;
  const ex = mx + (bend * h * -dy) / d, ey = my + (bend * h * dx) / d;
  return { ex, ey, hx, hy };
}

/**
 * Arms that reach toward the viewer. A chibi arm is short: with a hand held in front of the chest or the face (holding a
 * crate, cards, binoculars, hands clasped or in the pockets) a full-length two-bone arm can only get there by throwing the
 * elbow out sideways and folding the forearm back: a "chicken-wing" loop. A real arm in that position points toward the
 * camera, so it is drawn foreshortened: a short tube from the shoulder to the hand with a gentle bend (at most
 * 0.45·d/2 + 5 px), the elbow bowing down and outward, never up or inward.
 */
function softIk(sx: number, sy: number, hx: number, hy: number, l1: number, l2: number, side: number) {
  let dx = hx - sx, dy = hy - sy;
  let d = Math.hypot(dx, dy) || 0.001;
  const max = l1 + l2 - 0.5;
  if (d > max) {
    dx *= max / d;
    dy *= max / d;
    hx = sx + dx;
    hy = sy + dy;
    d = max;
  }
  const full = Math.sqrt(Math.max(0, ((l1 + l2) / 2) ** 2 - (d / 2) ** 2));
  const sag = Math.min(full, 0.45 * (d / 2) + 5);
  const nx = -dy / d, ny = dx / d;
  // of the two sides of the shoulder→hand line, take the one that points down and away from the body
  const sgn = nx * side * 0.55 + ny >= 0 ? 1 : -1;
  return { ex: (sx + hx) / 2 + sgn * nx * sag, ey: (sy + hy) / 2 + sgn * ny * sag, hx, hy };
}
/** poses whose look IS the elbow sticking out (akimbo, salute, a hand to the ear or the head): keep the bent two-bone arm */
const ELBOW_OUT = new Set(['hips', 'salute', 'phone', 'listen', 'tiphat', 'scratch', 'wipe', 'head', 'facepalm', 'chin', 'think']);

/** Smooth rubber-hose limb: quadratic curve from root through the IK joint to the end. */
function hose(r: V, j: V, e: V, k = 0.62) {
  // control point between the chord midpoint and the point that would pass through the joint: soft rubber-hose bend
  const mx = (r.x + e.x) / 2, my = (r.y + e.y) / 2;
  const c = { x: mx + (2 * j.x - mx - mx) * k, y: my + (2 * j.y - my - my) * k };
  return { d: `M${r.x} ${r.y} Q${c.x} ${c.y} ${e.x} ${e.y}`, c };
}
function qpts(r: V, c: V, e: V, t0: number, t1: number, n = 10): string {
  const out: string[] = [];
  for (let i = 0; i <= n; i++) {
    const t = t0 + ((t1 - t0) * i) / n;
    const u = 1 - t;
    out.push(`${i ? 'L' : 'M'}${u * u * r.x + 2 * u * t * c.x + t * t * e.x} ${u * u * r.y + 2 * u * t * c.y + t * t * e.y}`);
  }
  return out.join(' ');
}

type HandShape = 'mitten' | 'open' | 'fist' | 'point' | 'grip' | 'none';
type Pose = { r: [number, number]; l: [number, number]; rb?: number; lb?: number; rh?: HandShape; lh?: HandShape; behind?: boolean; tilt?: number;
  /** long-arm poses: the held rifle runs from the right hand at `rifleAng` degrees; 'two' = the left hand grips the handguard */
  rifle?: 'two' | 'one'; rifleAng?: number; rifleBehind?: boolean };
// Hand targets for the character's screen-right (r) and screen-left (l) arm, in body coords.
// Shoulders sit at (±31, -156); head centre (0, -206), chin ≈ -157, eyes ≈ -210, mouth ≈ -173, hips -98.
export const POSES: Record<string, Pose> = {
  idle: { r: [40, -82], l: [-40, -82] },
  hips: { r: [34, -106], l: [-34, -106], rb: -1, lb: -1, rh: 'fist', lh: 'fist' },
  point: { r: [122, -176], l: [-44, -92], rh: 'point' },
  pointL: { r: [44, -92], l: [-122, -176], lh: 'point' },
  pointUp: { r: [66, -262], l: [-44, -92], rh: 'point', tilt: -4 },
  pointDown: { r: [96, -104], l: [-44, -92], rh: 'point', tilt: 5 },
  pointSelf: { r: [12, -132], l: [-44, -92], rb: -1, rh: 'point' },
  raise: { r: [78, -246], l: [-44, -92], rh: 'open' },
  cheer: { r: [86, -244], l: [-86, -244], rh: 'fist', lh: 'fist', tilt: -3 },
  chin: { r: [14, -150], l: [-24, -120], rb: -1, lb: 1, rh: 'fist', tilt: 5 },
  think: { r: [16, -154], l: [-18, -124], rb: -1, lb: 1, rh: 'point', tilt: 7 },
  head: { r: [62, -232], l: [-62, -232], rb: -1, lb: -1, rh: 'open', lh: 'open' },
  face: { r: [26, -196], l: [-26, -196], rb: 1, lb: -1, rh: 'open', lh: 'open', tilt: 4 },
  facepalm: { r: [12, -206], l: [-44, -92], rb: -1, rh: 'open', tilt: 8 },
  cross: { r: [-30, -124], l: [30, -130], rb: 1, lb: -1, rh: 'none', lh: 'mitten' },
  hold: { r: [18, -122], l: [-18, -122], rb: 1, lb: -1, rh: 'grip', lh: 'grip' },
  holdUp: { r: [40, -250], l: [-40, -250], rb: -1, lb: -1, rh: 'grip', lh: 'grip', tilt: -3 },
  carry: { r: [40, -128], l: [-40, -128], rb: 1, lb: -1, rh: 'grip', lh: 'grip' },
  show: { r: [100, -150], l: [-44, -92], rb: -1, rh: 'grip' },
  talk: { r: [72, -144], l: [-44, -92], rb: -1, rh: 'open' },
  talk2: { r: [72, -144], l: [-72, -144], rb: -1, lb: -1, rh: 'open', lh: 'open' },
  explain: { r: [80, -148], l: [-30, -124], rb: -1, lb: -1, rh: 'open', lh: 'mitten' },
  shrug: { r: [88, -136], l: [-88, -136], rb: -1, lb: -1, rh: 'open', lh: 'open', tilt: 8 },
  present: { r: [114, -136], l: [-44, -92], rb: -1, rh: 'open' },
  offer: { r: [96, -122], l: [-44, -92], rb: -1, rh: 'open', tilt: 5 },
  salute: { r: [44, -236], l: [-44, -92], rb: 1, rh: 'open' },
  phone: { r: [58, -200], l: [-44, -92], rb: 1, rh: 'grip', tilt: 6 },
  binoculars: { r: [22, -212], l: [-22, -212], rb: 1, lb: -1, rh: 'grip', lh: 'grip' },
  wave: { r: [80, -246], l: [-44, -92], rh: 'open' },
  write: { r: [22, -108], l: [-28, -112], rb: 1, lb: -1, rh: 'grip', lh: 'mitten', tilt: 8 },
  typing: { r: [22, -112], l: [-22, -112], rb: 1, lb: -1, tilt: 6 },
  fist: { r: [42, -152], l: [-42, -152], rb: 1, lb: -1, rh: 'fist', lh: 'fist' },
  slam: { r: [64, -96], l: [-44, -92], rh: 'fist' },
  cower: { r: [30, -196], l: [-30, -196], rb: 1, lb: -1, rh: 'open', lh: 'open', tilt: -6 },
  wipe: { r: [-6, -238], l: [-44, -92], rb: 1, rh: 'open', tilt: -4 },
  drink: { r: [10, -168], l: [-44, -92], rb: 1, rh: 'grip', tilt: -8 },
  smoke: { r: [26, -168], l: [-30, -124], rb: 1, lb: -1, rh: 'grip' },
  behind: { r: [16, -112], l: [-16, -112], rb: -1, lb: 1, rh: 'none', lh: 'none', behind: true },
  pockets: { r: [36, -104], l: [-36, -104], rb: -1, lb: 1, rh: 'none', lh: 'none' },
  reach: { r: [128, -128], l: [-44, -92], rb: -1, rh: 'open' },
  stop: { r: [104, -168], l: [-44, -92], rb: -1, rh: 'open' },
  beg: { r: [22, -150], l: [-22, -150], rb: 1, lb: -1, rh: 'fist', lh: 'fist', tilt: -5 },
  rub: { r: [10, -132], l: [-10, -132], rb: 1, lb: -1, rh: 'mitten', lh: 'mitten' },
  scratch: { r: [50, -258], l: [-44, -92], rb: -1, rh: 'mitten', tilt: 6 },
  count: { r: [72, -148], l: [-44, -92], rb: -1, rh: 'point' },
  surrender: { r: [70, -250], l: [-70, -250], rb: -1, lb: -1, rh: 'open', lh: 'open', tilt: -4 },
  // ---- everyday business and gestures (creative scenes; cycles are animated in the life block) ----
  stir: { r: [62, -112], l: [-38, -116], rb: -1, lb: 1, rh: 'grip', lh: 'grip', tilt: 7 },
  ladle: { r: [70, -126], l: [-40, -100], rb: -1, rh: 'grip', tilt: 5 },
  eat: { r: [12, -150], l: [-14, -122], rb: 1, lb: -1, rh: 'grip', lh: 'grip', tilt: 4 },
  peel: { r: [30, -116], l: [-12, -120], rb: 1, lb: -1, rh: 'grip', lh: 'grip', tilt: 9 },
  knock: { r: [96, -176], l: [-44, -92], rb: -1, rh: 'fist' },
  hammer: { r: [70, -150], l: [-24, -116], rb: -1, lb: -1, rh: 'fist', lh: 'grip', tilt: 6 },
  pray: { r: [5, -152], l: [-5, -152], rb: 1, lb: -1, rh: 'open', lh: 'open', tilt: 7 },
  cry: { r: [22, -198], l: [-22, -198], rb: 1, lb: -1, rh: 'open', lh: 'open', tilt: 9 },
  heart: { r: [-4, -146], l: [-42, -92], rb: 1, rh: 'open', tilt: 3 },
  palms: { r: [72, -126], l: [-72, -126], rb: -1, lb: -1, rh: 'open', lh: 'open', tilt: 3 },
  lean: { r: [58, -100], l: [-58, -100], rb: -1, lb: -1, rh: 'open', lh: 'open', tilt: 6 },
  comfort: { r: [114, -172], l: [-42, -92], rb: -1, rh: 'open', tilt: 6 },
  give: { r: [110, -130], l: [-42, -92], rb: -1, rh: 'grip' },
  beckon: { r: [86, -152], l: [-42, -92], rb: -1, rh: 'open' },
  pointdown: { r: [94, -104], l: [-36, -98], rb: -1, rh: 'point', tilt: 9 },
  warm: { r: [60, -128], l: [-60, -128], rb: -1, lb: -1, rh: 'open', lh: 'open', tilt: 3 },
  shiver: { r: [-30, -124], l: [30, -130], rb: 1, lb: -1, rh: 'none', lh: 'mitten', tilt: -2 },
  clap: { r: [18, -148], l: [-18, -148], rb: 1, lb: -1, rh: 'open', lh: 'open' },
  wring: { r: [10, -118], l: [-10, -120], rb: 1, lb: -1, rh: 'mitten', lh: 'mitten', tilt: 4 },
  listen: { r: [46, -204], l: [-42, -92], rb: 1, rh: 'open', tilt: 10 },
  reachup: { r: [84, -262], l: [-42, -92], rb: -1, rh: 'open', tilt: -6 },
  cradle: { r: [34, -134], l: [-30, -126], rb: 1, lb: -1, rh: 'grip', lh: 'grip', tilt: 6 },
  sack: { r: [64, -186], l: [-42, -92], rb: 1, rh: 'grip', tilt: -5 },
  tiphat: { r: [34, -252], l: [-42, -92], rb: 1, rh: 'grip' },
  push: { r: [96, -142], l: [70, -136], rb: -1, lb: -1, rh: 'open', lh: 'open', tilt: -4 },
  pull: { r: [78, -122], l: [54, -126], rb: -1, lb: -1, rh: 'grip', lh: 'grip', tilt: 5 },
  gasp: { r: [12, -178], l: [-42, -92], rb: 1, rh: 'open', tilt: -4 },
  read: { r: [28, -140], l: [-28, -140], rb: 1, lb: -1, rh: 'grip', lh: 'grip', tilt: 6 },
  wait: { r: [10, -102], l: [-10, -104], rb: 1, lb: -1, rh: 'mitten', lh: 'mitten' },
  basket: { r: [44, -112], l: [-42, -92], rb: -1, rh: 'grip' },
  ride: { r: [74, -112], l: [62, -110], rb: -1, lb: -1, rh: 'grip', lh: 'grip', tilt: -2 },
  dig: { r: [40, -112], l: [6, -150], rb: -1, lb: 1, rh: 'grip', lh: 'grip', tilt: 8 },
  thumbsup: { r: [66, -150], l: [-44, -92], rb: -1, rh: 'fist' },
  // rifle drill (use with holds: "rifle"): port arms across the chest, aiming, slope arms on the shoulder, bayonet charge, at ease
  port: { r: [36, -96], l: [-30, -150], rb: 1, lb: -1, rh: 'grip', lh: 'grip', rifle: 'two', rifleAng: -122 },
  aim: { r: [16, -160], l: [48, -158], rb: 1, lb: -1, rh: 'grip', lh: 'grip', rifle: 'two', rifleAng: -3, tilt: 5 },
  shoulder: { r: [62, -108], l: [-40, -86], rb: 1, rh: 'grip', rifle: 'one', rifleAng: -60 },
  charge: { r: [10, -112], l: [40, -128], rb: 1, lb: -1, rh: 'grip', lh: 'grip', rifle: 'two', rifleAng: -18, tilt: -4 },
  ease: { r: [46, -96], l: [-40, -86], rb: -1, rh: 'grip', rifle: 'one', rifleAng: -84 },
};

const shade = (hex: string, k: number) => {
  const m = hex.replace('#', '');
  if (m.length !== 6) return hex;
  const n = parseInt(m, 16);
  const f = (v: number) => Math.round(clamp(k < 0 ? v * (1 + k) : v + (255 - v) * k, 0, 255));
  const r = f((n >> 16) & 255), g = f((n >> 8) & 255), b = f(n & 255);
  return '#' + ((1 << 24) | (r << 16) | (g << 8) | b).toString(16).slice(1);
};
const lerp = (a: number, b: number, k: number) => a + (b - a) * k;
/**
 * Pose blend curve: optional anticipation (a small move the other way), a smooth ease into the new pose,
 * reaching it a little early and settling with a 4 % overshoot — slow in, slow out, follow-through.
 */
const poseEase = (k: number, anticipate = false) => {
  const x = clamp(k, 0, 1);
  const A = anticipate ? 0.14 : 0;
  if (x < A) return -0.06 * Math.sin((Math.PI * x) / A);
  const u = (x - A) / (1 - A);
  const v = Math.min(1, u / 0.86);
  const base = v * v * v * (v * (6 * v - 15) + 10);
  const over = u > 0.86 ? 0.04 * Math.sin((Math.PI * (u - 0.86)) / 0.14) : 0;
  return base + over;
};

const Hand: React.FC<{ x: number; y: number; ang: number; shape: HandShape; skin: string; side: number }> = ({ x, y, ang, shape, skin, side }) => {
  if (shape === 'none') return null;
  const deg = (ang * 180) / Math.PI;
  // the thumb is drawn BEHIND the palm so only a small bump shows (never a separate ball on top)
  const thumb = (cx: number, cy: number, rx: number, ry: number, rot: number) => (
    <ellipse cx={cx} cy={cy * side} rx={rx} ry={ry} transform={`rotate(${rot * side} ${cx} ${cy * side})`} fill={skin} stroke={INK} strokeWidth={2.6} />
  );
  return (
    <g transform={`translate(${x} ${y}) rotate(${deg})`}>
      {shape === 'point' ? (
        <g>
          <rect x={4} y={-4} width={20} height={8} rx={4} fill={skin} stroke={INK} strokeWidth={2.8} />
          {thumb(5, -8, 5, 3.6, -25)}
          <ellipse cx={4} cy={0} rx={9.5} ry={8.5} fill={skin} stroke={INK} strokeWidth={3} />
        </g>
      ) : shape === 'open' ? (
        <g>
          {thumb(5, -9.5, 6.5, 3.8, -38)}
          <path d="M-3 -8 Q9 -12 16 -6 Q19 0 16 6 Q9 12 -3 8 Q-6 0 -3 -8 Z" fill={skin} stroke={INK} strokeWidth={3} strokeLinejoin="round" />
          <path d="M9 -3.5 h6 M9 1.5 h6" stroke={INK} strokeWidth={1.6} strokeOpacity={0.35} strokeLinecap="round" />
        </g>
      ) : shape === 'fist' ? (
        <g>
          <circle cx={5} cy={0} r={10} fill={skin} stroke={INK} strokeWidth={3} />
          <path d="M10 -5 v10" stroke={INK} strokeWidth={1.8} strokeOpacity={0.45} strokeLinecap="round" />
        </g>
      ) : shape === 'grip' ? (
        <ellipse cx={5} cy={0} rx={9.5} ry={8.5} fill={skin} stroke={INK} strokeWidth={3} />
      ) : (
        <g>
          {thumb(4, -7.5, 5, 3.6, -30)}
          <ellipse cx={5} cy={0} rx={10} ry={8.6} fill={skin} stroke={INK} strokeWidth={3} />
        </g>
      )}
    </g>
  );
};

export const Character: React.FC<{ spec: CharSpec; state: CharState; t: number; seed?: string; held?: Held }> = ({ spec, state, t, seed = 'c', held }) => {
  const nat = nation(spec.nation);
  const outfit = spec.outfit ?? 'tunic';
  const jacket = spec.color ?? (outfit === 'navy' ? nat.navy : outfit === 'navywhite' || outfit === 'sailor' ? '#f3f1ea' : outfit === 'suit' ? '#3b3a3f' : outfit === 'civil' ? '#c9b48a' : outfit === 'party' ? '#8a6a3e' : outfit === 'tweed' ? '#7b5a3c' : outfit === 'trench' ? '#c49a5e' : nat.uniform);
  const pants = spec.pants ?? (outfit === 'navywhite' || outfit === 'sailor' ? '#f3f1ea' : outfit === 'suit' || outfit === 'navy' ? shade(jacket, -0.15) : outfit === 'civil' ? '#5a5048' : outfit === 'tweed' ? '#3f3a36' : outfit === 'trench' ? '#3b4252' : shade(jacket, -0.22));
  const skin = spec.skin ?? SKIN;
  const hairC = spec.hairColor ?? ((spec.age ?? 0) > 0.7 ? '#c9c4bc' : '#3a2e26');
  const build = spec.build ?? 1;
  const extra = new Set(spec.extra ?? []);
  const expr = state.expr ?? 'neutral';
  const poseName = state.pose ?? 'idle';
  const pose = POSES[poseName] ?? POSES.idle;
  const prev = POSES[state.prevPose ?? poseName] ?? pose;
  const kRaw = state.poseK ?? 1;
  // overlapping action: the leading (right) hand starts first, the other hand follows ~0.08 s later
  const pd = state.poseDur ?? 0.6;
  const k = poseEase(kRaw, !!state.bigMove);
  const kLeft = poseEase(clamp((kRaw * pd - 0.08) / Math.max(0.1, pd - 0.08)), !!state.bigMove);
  const back = state.view === 'back';
  const r1 = rnd(seed), r2 = rnd(seed, 1), r3 = rnd(seed, 2);
  const turn = clamp(state.turn ?? 0, -1, 1);
  // a take on every expression change: a quick squash (anticipation), a stretch, then a damped settle
  let takeSx = 1, takeSy = 1;
  {
    const a = state.exprAge ?? 99, amt = state.take ?? 1;
    if (a >= 0 && a < 0.9 && amt > 0) {
      const sq = a < 0.09 ? Math.sin((a / 0.09) * Math.PI * 0.5) : Math.exp(-(a - 0.09) * 6.5) * Math.cos((a - 0.09) * 19);
      takeSy = 1 - 0.035 * amt * (a < 0.09 ? sq : -sq);
      takeSx = 1 + 0.025 * amt * (a < 0.09 ? sq : -sq * 0.7);
    }
  }

  // ---------- motion ----------
  // walk amount 0..1: the stride opens as the character speeds up and closes as it stops (no on/off snap)
  const wAmt = state.seated || state.kneel ? 0 : clamp(state.walk ?? 0);
  const walking = wAmt > 0.02;
  const run = walking && !!state.run;
  const dir = state.dir ?? 1;
  const freq = run ? 2.7 : 1.75; // stride cycles per second (only when the gait is not distance-driven)
  const ph = state.gait !== undefined ? state.gait + r1 * 6 : t * Math.PI * 2 * freq + r1 * 6;
  // walking styles change the stride, the lift of the feet, the lean and the arm swing (not the speed: that is the path)
  const gs = run ? '' : state.gaitStyle ?? '';
  const gStride = gs === 'shuffle' ? 0.55 : gs === 'march' ? 1.18 : gs === 'limp' ? 0.75 : gs === 'sneak' ? 0.8 : 1;
  const gLift = gs === 'shuffle' ? 0.3 : gs === 'march' ? 1.4 : gs === 'sneak' ? 0.7 : 1;
  const armSw = gs === 'shuffle' ? 0.35 : gs === 'march' ? 1.55 : gs === 'sneak' ? 0.45 : gs === 'limp' ? 0.7 : 1;
  const stride = (run ? 30 : 19) * wAmt * gStride;
  const lift = (run ? 26 : 13) * wAmt * gLift;
  const idleBob = Math.sin(t * 1.7 + r2 * 6) * 1.1;
  const limpDip = gs === 'limp' ? Math.max(0, Math.sin(ph)) * 8 : 0;
  const bob = walking ? lerp(idleBob, (Math.abs(Math.cos(ph)) - 0.5) * (run ? -9 : -5) + limpDip, wAmt) : idleBob;
  const gLean = gs === 'shuffle' ? 5 : gs === 'sneak' ? 8 : gs === 'march' ? 0.5 : gs === 'limp' ? 3.5 + Math.sin(ph) * 3 : 2.5;
  // shivering with cold: a fine tremor of the whole body
  const shiverX = poseName === 'shiver' ? Math.sin(t * 31) * 1.3 + Math.sin(t * 23) * 0.8 : 0;
  const lean = (walking ? lerp(Math.sin(t * 0.83 + r3 * 6) * 0.7, dir * (run ? 8 : gLean), wAmt) : Math.sin(t * 0.83 + r3 * 6) * 0.7) + shiverX;
  const breathe = 1 + Math.sin(t * 1.7 + r2 * 6) * 0.01;
  const bp = 3.2 + r3 * 2;
  const blink = (t + rnd(seed, 4) * bp) % bp < 0.12;
  const talkOpen = state.talk ? (Math.sin(t * 17 + rnd(seed, 5)) * 0.5 + 0.5) * (Math.sin(t * 5.3) * 0.3 + 0.7) : 0;
  const look = (state.look ?? 0) * 4;

  const hipY = -98;
  const shY = -172;
  const hy = shY - 34; // head centre: chin (hy+49) overlaps the collar
  const tw = 29 * build; // shoulder half-width
  const bw = 37 * build; // hem half-width
  const shX = tw + 2;
  const shoulderY = shY + 16;
  const L1 = 42, L2 = 41;

  // ---------- hand targets (pose blend + life) ----------
  let [rx, ry] = [lerp(prev.r[0], pose.r[0], k), lerp(prev.r[1], pose.r[1], k)];
  let [lx, ly] = [lerp(prev.l[0], pose.l[0], kLeft), lerp(prev.l[1], pose.l[1], kLeft)];
  const rb = kRaw < 0.5 ? prev.rb ?? 1 : pose.rb ?? 1;
  const lb = kRaw < 0.5 ? prev.lb ?? 1 : pose.lb ?? 1;
  const rh: HandShape = (kRaw < 0.5 ? prev.rh : pose.rh) ?? 'mitten';
  const lh: HandShape = (kRaw < 0.5 ? prev.lh : pose.lh) ?? 'mitten';
  // idle drift so hands are never frozen
  rx += Math.sin(t * 1.3 + r1 * 9) * 2.2;
  ry += Math.sin(t * 1.9 + r2 * 9) * 2;
  lx += Math.sin(t * 1.1 + r3 * 9) * 2.2;
  ly += Math.sin(t * 1.7 + r1 * 7) * 2;
  // talking: beat gestures on the free hand
  const restingR = poseName === 'idle' || poseName === 'hips' || poseName === 'pockets';
  if (state.talk && poseName === 'idle' && !walking) {
    const beat = Math.pow(0.5 - 0.5 * Math.cos((t / 2.6 + r2) * Math.PI * 2), 2);
    rx = lerp(rx, 66 + Math.sin(t * 3.1) * 6, beat * 0.85);
    ry = lerp(ry, -140 + Math.sin(t * 4.3) * 7, beat * 0.85);
  }
  if (poseName === 'talk' || poseName === 'talk2' || poseName === 'explain') {
    rx += Math.sin(t * 2.6 + 1) * 9 + Math.sin(t * 5.3) * 3;
    ry += Math.sin(t * 3.4) * 9;
    if (poseName === 'talk2') { lx -= Math.sin(t * 2.4 + 2) * 8; ly += Math.sin(t * 3.0 + 1) * 8; }
  }
  if (poseName === 'wave') rx += Math.sin(t * 9) * 18;
  if (poseName === 'write') { rx += Math.sin(t * 11) * 6; ry += Math.cos(t * 7) * 3; }
  if (poseName === 'typing') { ry += Math.abs(Math.sin(t * 13)) * -7; ly += Math.abs(Math.sin(t * 13 + 1.6)) * -7; }
  if (poseName === 'fist' || poseName === 'cheer') { const q = Math.abs(Math.sin(t * 6)) * 10; ry -= q; ly -= q; }
  if (poseName === 'head' || poseName === 'cower') { rx += Math.sin(t * 7) * 3; lx -= Math.sin(t * 7) * 3; }
  if (poseName === 'shrug') { const q = Math.max(0, Math.sin(t * 2.2)) * 8; ry -= q; ly -= q; }
  if (poseName === 'slam') { const q = Math.max(0, Math.sin(t * 5)) ** 3 * 34; ry -= q; }
  if (poseName === 'rub') { rx += Math.sin(t * 9) * 6; lx -= Math.sin(t * 9) * 6; }
  if (poseName === 'scratch') { rx += Math.sin(t * 14) * 4; }
  if (poseName === 'count') { ry += (Math.floor(t * 1.6) % 2) * -10; }
  // business cycles: they fade in as the hands arrive, so a pose change never starts mid-stroke
  {
    const settle = clamp(kRaw * 1.6, 0, 1);
    switch (poseName) {
      case 'stir': rx += Math.cos(t * 4.4) * 11 * settle; ry += Math.sin(t * 4.4) * 4 * settle; break;
      case 'ladle': { const q = Math.sin(t * 2.4); rx += q * 14 * settle; ry += (-Math.abs(q) * 20 + 8) * settle; break; }
      case 'eat': { const q = Math.pow(Math.max(0, Math.sin(t * 2.2)), 1.5); rx += (q * 6 - 6) * settle; ry += (-q * 28 + 16) * settle; break; }
      case 'peel': rx += Math.sin(t * 6.5) * 7 * settle; ry += Math.max(0, Math.sin(t * 6.5)) * 3 * settle; break;
      case 'knock': { const g = (t % 1.7) < 0.75 ? Math.pow(Math.max(0, Math.sin(t * 13)), 3) : 0; rx += g * 12 * settle; break; }
      case 'hammer': { const q = Math.abs(Math.sin(t * 3.6)); ry -= q * 46 * settle; rx -= q * 10 * settle; break; }
      case 'cry': ry += Math.sin(t * 7.5) * 2.5; ly += Math.sin(t * 7.5 + 0.4) * 2.5; break;
      case 'clap': { const q = Math.abs(Math.sin(t * 7)); rx += q * 22 * settle; lx -= q * 22 * settle; break; }
      case 'wring': rx += Math.cos(t * 5) * 5; ry += Math.sin(t * 5) * 4; lx -= Math.cos(t * 5) * 5; ly -= Math.sin(t * 5) * 3; break;
      case 'warm': rx += Math.sin(t * 7) * 4; lx -= Math.sin(t * 7) * 4; break;
      case 'beckon': { const q = Math.max(0, Math.sin(t * 6)); rx -= q * 14 * settle; ry -= q * 6 * settle; break; }
      case 'palms': if (state.talk) { const q = Math.sin(t * 3.2); ry += q * 7; ly += q * 7; } break;
      case 'pray': ry += Math.sin(t * 1.3) * 1.5; ly += Math.sin(t * 1.3) * 1.5; break;
      case 'shiver': rx += Math.sin(t * 29) * 1.2; lx += Math.sin(t * 27) * 1.2; break;
      case 'read': ry += Math.sin(t * 0.9) * 2; ly += Math.sin(t * 0.9) * 2; break;
      case 'comfort': ry += Math.sin(t * 2.1) * 3 * settle; break;
      case 'dig': { const q = Math.sin(t * 4.2), c = Math.cos(t * 4.2); ry += q * 18 * settle; ly += q * 18 * settle; rx += c * 6 * settle; lx += c * 6 * settle; break; }
      default: break;
    }
  }

  // walking / running arm swing (only when the arms are free)
  if (walking) {
    const pr = ph, pl = ph + Math.PI, w = wAmt;
    if (restingR || state.pose === undefined) {
      if (run) {
        rx = lerp(rx, 30 - dir * Math.sin(pr) * 24, w); ry = lerp(ry, -136 - Math.abs(Math.sin(pr)) * 10, w);
        lx = lerp(lx, -30 - dir * Math.sin(pl) * 24, w); ly = lerp(ly, -136 - Math.abs(Math.sin(pl)) * 10, w);
      } else {
        rx = lerp(rx, 36 - dir * Math.sin(pr) * 18 * armSw, w); ry = lerp(ry, -86 - Math.abs(Math.sin(pr)) * 8 * armSw + (gs === 'shuffle' ? 6 : 0), w);
        lx = lerp(lx, -36 - dir * Math.sin(pl) * 18 * armSw, w); ly = lerp(ly, -86 - Math.abs(Math.sin(pl)) * 8 * armSw + (gs === 'shuffle' ? 6 : 0), w);
      }
    } else if (poseName !== 'carry' && poseName !== 'hold' && poseName !== 'holdUp' && pose.rifle !== 'two') {
      // keep the gesture on the right hand, swing the left one
      lx = lerp(lx, -36 - dir * Math.sin(pl) * 15, w); ly = lerp(ly, -86 - Math.abs(Math.sin(pl)) * 6, w);
    }
  }

  // long arms: the rifle hangs from the right hand at the pose angle; two-handed poses put the left hand on the handguard
  // the rifle shows once the hands are close to the grip: early when coming from another rifle pose, late when the hands
  // were elsewhere (hands on the head → aim: no rifle floating across the face mid-move)
  const rifleOn = !!held?.grips && !!pose.rifle && kRaw > (prev.rifle ? 0.35 : 0.8);
  const rAng = ((pose.rifleAng ?? 0) * Math.PI) / 180;
  if (rifleOn && held?.grips && pose.rifle === 'two') {
    const len = (held.grips[1] - held.grips[0]) * (held.scale ?? 0.6);
    lx = rx + Math.cos(rAng) * len;
    ly = ry + Math.sin(rAng) * len;
  }
  // flat props (paper, telegram, folder…) are held by their side edges, not with both hands in the middle
  const twoHands = held ? held.both ?? (poseName === 'hold' || poseName === 'holdUp' || poseName === 'carry') : false;
  if (held?.grip && twoHands) {
    const half = held.grip * (held.scale ?? 0.55) * 0.92;
    const cx = (rx + lx) / 2, cy = (ry + ly) / 2;
    rx = cx + half; lx = cx - half; ry = cy; ly = cy;
  }
  const bw2 = build ** 0.3;
  let R = ik(shX, shoulderY, rx * bw2, ry, L1, L2, run ? -dir : -rb);
  let Lf = ik(-shX, shoulderY, lx * bw2, ly, L1, L2, run ? -dir : lb);
  // arms toward the viewer are foreshortened (softIk) except in elbow-out poses, rifle handling and running;
  // the change between the two kinds of arm follows the pose blend, so an elbow never pops
  {
    const isSoft = (name: string, q: Pose) => !ELBOW_OUT.has(name) && !q.rifle;
    const f = run ? 0 : lerp(isSoft(state.prevPose ?? poseName, prev) ? 1 : 0, isSoft(poseName, pose) ? 1 : 0, clamp(kRaw * 1.25, 0, 1));
    if (f > 0) {
      const sR = softIk(shX, shoulderY, rx * bw2, ry, L1, L2, 1);
      const sL = softIk(-shX, shoulderY, lx * bw2, ly, L1, L2, -1);
      R = { ex: lerp(R.ex, sR.ex, f), ey: lerp(R.ey, sR.ey, f), hx: lerp(R.hx, sR.hx, f), hy: lerp(R.hy, sR.hy, f) };
      Lf = { ex: lerp(Lf.ex, sL.ex, f), ey: lerp(Lf.ey, sL.ey, f), hx: lerp(Lf.hx, sL.hx, f), hy: lerp(Lf.hy, sL.hy, f) };
    }
  }
  // folded arms: fixed elbows at the sides, forearms stacked across the chest
  const folded = (n?: string) => n === 'cross' || n === 'shiver';
  const crossK = folded(poseName) ? (folded(state.prevPose) ? 1 : clamp(kRaw * 1.4, 0, 1)) : folded(state.prevPose) ? 1 - clamp(kRaw * 1.4, 0, 1) : 0;
  if (crossK > 0) {
    const mixJ = (a: typeof R, b: typeof R) => ({ ex: lerp(a.ex, b.ex, crossK), ey: lerp(a.ey, b.ey, crossK), hx: lerp(a.hx, b.hx, crossK), hy: lerp(a.hy, b.hy, crossK) });
    const breath = Math.sin(t * 1.7 + r2 * 6) * 1.5;
    R = mixJ(R, { ex: bw - 2, ey: -114 + breath, hx: -bw + 12, hy: -128 + breath });
    Lf = mixJ(Lf, { ex: -bw + 2, ey: -118 + breath, hx: bw - 12, hy: -133 + breath });
  }
  const armK = crossK > 0.5 ? 0.95 : 0.62;

  const sleeve = spec.armColor ?? jacket;
  const sleeveDark = shade(jacket, -0.25);

  const armPath = (side: number, e: { ex: number; ey: number; hx: number; hy: number }) => hose({ x: side * shX, y: shoulderY }, { x: e.ex, y: e.ey }, { x: e.hx, y: e.hy }, armK);
  const armTube = (side: number, e: { ex: number; ey: number; hx: number; hy: number }) => {
    const { d } = armPath(side, e);
    return (
      <g key={'a' + side}>
        <path d={d} stroke={INK} strokeWidth={ARM_INK} fill="none" strokeLinecap="round" />
        <path d={d} stroke={sleeve} strokeWidth={ARM_FILL} fill="none" strokeLinecap="round" />
      </g>
    );
  };
  const handOf = (side: number, e: { ex: number; ey: number; hx: number; hy: number }, shape: HandShape) => {
    const { c } = armPath(side, e);
    const ang = Math.atan2(e.hy - c.y, e.hx - c.x);
    return <Hand key={'h' + side} x={e.hx} y={e.hy} ang={ang} shape={shape} skin={skin} side={side} />;
  };

  // ---------- legs ----------
  const shoeC = outfit === 'suit' || outfit === 'civil' || outfit === 'dress' || outfit === 'tweed' ? '#2a2420' : '#2b2522';
  const booted = outfit === 'tunic' || outfit === 'coat' || outfit === 'pilot' || outfit === 'party';
  // riding: the hips sit on the seat (default: the library bicycle, seat 40 units behind the middle, 130 up; crank 10 behind, 50 up)
  const rw = state.ride ? state.rideWith : undefined;
  const rSize = rw?.size ?? 1;
  const seat = rw?.seat ?? [-40, -130];
  const crank = rw?.crank ?? [-10, -50];
  const rideLift = state.ride ? seat[1] * rSize + 96 : 0;
  const leg = (s: number) => {
    const hip = { x: s * 12 * build, y: hipY + bob + 6 + rideLift };
    let foot: V;
    let bend = -dir;
    if (state.ride) {
      // the crank of the bicycle is 30 units ahead of the saddle, 50 up; the pedals go round it, half a turn apart
      const a = (state.pedal ?? 0) + (s > 0 ? 0 : Math.PI);
      foot = { x: (crank[0] - seat[0]) * rSize + Math.cos(a) * 17 * rSize, y: crank[1] * rSize + Math.sin(a) * 17 * rSize };
      const j = ik(hip.x, hip.y, foot.x, foot.y, 46, 46, -1);
      const { d } = hose(hip, { x: j.ex, y: j.ey }, { x: j.hx, y: j.hy }, 0.7);
      return (
        <g key={'l' + s}>
          <path d={d} stroke={INK} strokeWidth={LEG_INK} fill="none" strokeLinecap="round" />
          <path d={d} stroke={pants} strokeWidth={LEG_FILL} fill="none" strokeLinecap="round" />
          <ellipse cx={j.hx + 4} cy={j.hy + 3} rx={13} ry={7} fill={shoeC} stroke={INK} strokeWidth={3} />
        </g>
      );
    }
    if (state.seated) {
      foot = { x: s * 22, y: hipY + 54 };
      const knee = { x: s * 22, y: hipY + 16 };
      const d = `M${hip.x} ${hip.y} L${knee.x} ${knee.y} L${foot.x} ${foot.y}`;
      return (
        <g key={'l' + s}>
          <path d={d} stroke={INK} strokeWidth={LEG_INK} fill="none" strokeLinecap="round" strokeLinejoin="round" />
          <path d={d} stroke={pants} strokeWidth={LEG_FILL} fill="none" strokeLinecap="round" strokeLinejoin="round" />
          <ellipse cx={foot.x + s * 3} cy={foot.y + 4} rx={14} ry={8} fill={shoeC} stroke={INK} strokeWidth={3} />
        </g>
      );
    }
    if (state.kneel) {
      const knee = { x: s * 18, y: -6 };
      const d = `M${hip.x} ${hip.y + 44} Q${s * 20} ${hip.y + 70} ${knee.x} ${knee.y}`;
      return (
        <g key={'l' + s}>
          <path d={d} stroke={INK} strokeWidth={LEG_INK} fill="none" strokeLinecap="round" />
          <path d={d} stroke={pants} strokeWidth={LEG_FILL} fill="none" strokeLinecap="round" />
          <ellipse cx={knee.x} cy={knee.y} rx={12} ry={7} fill={pants} stroke={INK} strokeWidth={3} />
        </g>
      );
    }
    if (walking) {
      // feet come back under the hips as the stride closes
      const p = ph + (s > 0 ? 0 : Math.PI);
      foot = { x: lerp(s * 15 * build, s * 10, wAmt) + dir * stride * Math.sin(p), y: -6 - Math.max(0, Math.cos(p)) * lift };
    } else {
      foot = { x: s * 15 * build, y: -6 };
      bend = -s; // knees bow slightly outward when standing
    }
    const j = ik(hip.x, hip.y, foot.x, foot.y, walking ? 46 : 44, walking ? 46 : 44, bend);
    const { d, c } = hose(hip, { x: j.ex, y: j.ey }, { x: j.hx, y: j.hy }, walking ? 0.75 : 0.3);
    const fx = j.hx, fy = j.hy;
    const toe = walking ? dir : s * 0.4;
    const footAng = walking ? Math.max(0, Math.cos(ph + (s > 0 ? 0 : Math.PI))) * dir * -16 * wAmt : 0;
    return (
      <g key={'l' + s}>
        <path d={d} stroke={INK} strokeWidth={LEG_INK} fill="none" strokeLinecap="round" />
        <path d={d} stroke={pants} strokeWidth={LEG_FILL} fill="none" strokeLinecap="round" />
        {booted ? <path d={qpts(hip, c, { x: fx, y: fy }, 0.62, 1)} stroke={shoeC} strokeWidth={LEG_FILL + 2} fill="none" strokeLinecap="round" /> : null}
        <g transform={`translate(${fx} ${fy}) rotate(${footAng})`}>
          <path d={`M${-10 + toe * -3} 2 Q${-10 + toe * -3} -8 ${toe * 4} -8 Q${12 + toe * 8} -8 ${14 + toe * 8} 2 Q${14 + toe * 8} 8 ${toe * 3} 8 L${-8 + toe * -3} 8 Q${-11 + toe * -3} 8 ${-10 + toe * -3} 2 Z`} fill={shoeC} stroke={INK} strokeWidth={3} strokeLinejoin="round" />
        </g>
      </g>
    );
  };

  const torso = `M${-tw} ${shY - 2} C${-tw - 2} ${shY - 12} ${tw + 2} ${shY - 12} ${tw} ${shY - 2} C${tw + 4} ${shY + 10} ${bw - 2} ${hipY - 30} ${bw + 1} ${hipY + 4} Q0 ${hipY + 13} ${-bw - 1} ${hipY + 4} C${-bw + 2} ${hipY - 30} ${-tw - 4} ${shY + 10} ${-tw} ${shY - 2} Z`;

  // head tilt: pose bias + talking nods + explicit head moves
  let tilt = (prev.tilt ?? 0) + ((pose.tilt ?? 0) - (prev.tilt ?? 0)) * clamp(kRaw * 1.5, 0, 1);
  if (expr === 'worried' || expr === 'sad') tilt -= 3;
  if (expr === 'smug') tilt += 4;
  if (state.talk) tilt += Math.sin(t * 4.1 + r2 * 5) * 2.2;
  let headDy = 0, headDx = 0;
  if (state.headMove === 'nod') headDy = Math.max(0, Math.sin(t * 7)) * 7;
  if (state.headMove === 'shake') headDx = Math.sin(t * 9) * 7;
  if (state.headMove === 'tilt') tilt += 9;
  if (walking) tilt += Math.sin(ph * 2) * 1.5;

  const body = (
    <g>
      {outfit === 'trench' ? <path d={`M${-tw - 4} ${shY - 2} C${-tw - 8} ${shY + 20} ${-bw - 14} ${-46} ${-bw - 16} ${-38} Q${-bw} ${-30} -6 ${-34} L6 ${-34} Q${bw} ${-30} ${bw + 16} ${-38} C${bw + 14} ${-46} ${tw + 8} ${shY + 20} ${tw + 4} ${shY - 2} Z`} fill={jacket} stroke={INK} strokeWidth={Lw} strokeLinejoin="round" /> : null}
      {outfit === 'coat' ? <path d={`M${-tw - 4} ${shY - 2} C${-tw - 8} ${shY + 20} ${-bw - 16} ${-40} ${-bw - 14} ${-30} Q0 ${-22} ${bw + 14} ${-30} C${bw + 16} ${-40} ${tw + 8} ${shY + 20} ${tw + 4} ${shY - 2} Z`} fill={jacket} stroke={INK} strokeWidth={Lw} /> : null}
      {outfit === 'dress' ? <path d={`M${-tw} ${shY} L${tw} ${shY} L${bw + 22} ${-30} Q0 ${-22} ${-bw - 22} ${-30} Z`} fill={jacket} stroke={INK} strokeWidth={Lw} /> : null}
      <path d={torso} fill={jacket} stroke={INK} strokeWidth={Lw} strokeLinejoin="round" transform={`scale(${breathe} 1)`} />
      <path d={`M${tw - 6} ${shY + 6} C${tw} ${shY + 20} ${bw - 6} ${hipY - 26} ${bw - 3} ${hipY + 3} L${bw} ${hipY + 4} C${bw - 2} ${hipY - 30} ${tw + 3} ${shY + 10} ${tw} ${shY}`} fill={sleeveDark} opacity={0.4} />
      {back ? null : <Outfit outfit={outfit} jacket={jacket} shY={shY} hipY={hipY} w={bw} nat={spec.nation} extra={extra} vest={spec.vest} tie={spec.tie} />}
      {extra.has('armband') ? (
        <g>
          <path d={`M${tw - 6} ${shY + 26} l14 3 l-2 14 l-14 -3 z`} fill="#c8352b" stroke={INK} strokeWidth={2.5} />
          <circle cx={tw + 1} cy={shY + 35} r={4} fill="#fff" />
        </g>
      ) : null}
    </g>
  );

  const scarf = extra.has('scarf') && !back ? (
    <g>
      <path d={`M${-tw - 6} ${shY + 4} Q0 ${shY + 24} ${tw + 6} ${shY + 4} L${tw + 4} ${shY - 8} Q0 ${shY + 8} ${-tw - 4} ${shY - 8} Z`} fill={spec.scarf ?? '#b8322a'} stroke={INK} strokeWidth={3} strokeLinejoin="round" />
      <path d={`M${tw - 6} ${shY + 10} q${6 + Math.sin(t * 2.3) * 2} 22 ${2 + Math.sin(t * 2.3) * 3} 50 l14 -2 q${2 + Math.sin(t * 2.3 + 0.5) * 2} -26 -4 -50 z`} fill={spec.scarf ?? '#b8322a'} stroke={INK} strokeWidth={3} strokeLinejoin="round" />
      <path d={`M${tw - 2} ${shY + 54} l12 -2 M${tw - 1} ${shY + 49} l12 -2`} stroke="#fff" strokeOpacity={0.5} strokeWidth={2} />
    </g>
  ) : null;

  const heldNode = held && rifleOn && held.grips ? (
    <g transform={`translate(${R.hx} ${R.hy}) rotate(${(rAng * 180) / Math.PI}) scale(${held.scale ?? 0.6}) translate(${-held.grips[0]} 0)`}>
      {held.node}
      {state.muzzle !== undefined && state.muzzle >= 0 && state.muzzle < 0.08 ? (
        <g transform="translate(172 -6)" opacity={1 - state.muzzle / 0.08}>
          <path d="M0 0 L60 -26 L120 0 L60 26 Z" fill="#ffe28a" />
          <path d="M0 0 L34 -40 L48 0 L34 40 Z" fill="#ffb347" />
          <circle r={24} fill="#fff6c8" />
        </g>
      ) : null}
    </g>
  ) : held ? (() => {
    const two = held.both ?? (poseName === 'hold' || poseName === 'holdUp' || poseName === 'carry' || poseName === 'binoculars');
    // one hand on a flat prop: hold it by its inner edge so the hand never covers the writing
    const hx = two ? (R.hx + Lf.hx) / 2 : R.hx - (held.grip ? held.grip * (held.scale ?? 0.55) * 0.85 : 0);
    const hyy = two ? (R.hy + Lf.hy) / 2 : R.hy;
    return <g transform={`translate(${hx + (held.dx ?? 0)} ${hyy + (held.dy ?? 0)}) rotate(${held.rotate ?? 0}) scale(${held.scale ?? 0.55})`}>{held.node}</g>;
  })() : null;

  const behindArms = pose.behind && kRaw > 0.5;
  // costume pieces: body slots are drawn in the body frame (feet at 0, shoulders at -172, hips at -98); head slots in the
  // head frame (head centre at 0; top of the head -74, chin +50, ears at x ±66). hips pieces go under the torso unless "above".
  const wearOf = (slot: string, above?: boolean, dy = 0) => {
    const ws = (spec.wear ?? []).filter((w) => w.slot === slot && (above === undefined || !!w.above === above));
    if (!ws.length) return null;
    return <g transform={dy ? `translate(0 ${dy})` : undefined}>{ws.map((w, i) => <Drawing key={i} parts={w.parts} t={t} />)}</g>;
  };
  // a load carried on the shoulder (a sack) sits behind the head, not across the face; the hand is still drawn over it
  const onShoulder = poseName === 'sack' && kRaw > 0.5;
  return (
    <g>
      <ellipse cx={0} cy={2} rx={54 * build} ry={9} fill="#000" opacity={0.16} />
      {rw ? (
        <g transform={`translate(${-seat[0] * rSize} 0) scale(${rSize})`}>
          <Drawing parts={rw.parts} t={t} travel={(state.rideTravel ?? 0) / rSize} />
        </g>
      ) : null}
      <g transform={`rotate(${lean} 0 0) scale(${takeSx} ${takeSy})`}>
        {wearOf('back')}
        {[-1, 1].map(leg)}
        <g transform={`translate(0 ${bob + (state.kneel ? 44 : 0) + rideLift})`}>
          {wearOf('hips', false)}
          {back || behindArms ? (
            <>
              {armTube(-1, Lf)}
              {armTube(1, R)}
            </>
          ) : null}
          {(pose.rifleBehind && rifleOn) || onShoulder ? heldNode : null}
          {body}
          {wearOf('hips', true)}
          {scarf}
          {wearOf('body')}
          <g transform={`translate(${headDx} ${headDy}) rotate(${tilt} 0 ${hy + 46})`}>
            {wearOf('headback', undefined, hy)}
            <Head spec={spec} expr={expr} blink={blink} talk={talkOpen} look={look + turn * 3} hy={hy} hairC={hairC} skin={skin} back={back} extra={extra} t={t} seed={seed} turn={turn} />
            {wearOf('head', undefined, hy)}
          </g>
          {back || behindArms ? null : (
            <>
              {armTube(-1, Lf)}
              {armTube(1, R)}
            </>
          )}
          {(pose.rifleBehind && rifleOn) || onShoulder ? null : heldNode}
          {back || behindArms ? null : (
            <>
              {handOf(-1, Lf, lh)}
              {handOf(1, R, rh)}
            </>
          )}
        </g>
      </g>
    </g>
  );
};

const Outfit: React.FC<{ outfit: string; jacket: string; shY: number; hipY: number; w: number; nat?: string; extra: Set<string>; vest?: string; tie?: string }> = ({ outfit, jacket, shY, hipY, w, extra, vest, tie }) => {
  const dark = shade(jacket, -0.3);
  const btn = outfit === 'navy' ? '#e3b94a' : outfit === 'navywhite' ? '#d9b44a' : shade(jacket, -0.45);
  switch (outfit) {
    case 'trench':
      return (
        <g>
          {/* open trench coat: wide lapels, white shirt, tie, belt with buckle, double-breasted buttons */}
          <path d={`M-14 ${shY - 4} L0 ${shY + 30} L14 ${shY - 4} Z`} fill="#f4f1ea" stroke={INK} strokeWidth={2.5} />
          <path d={`M-4 ${shY + 4} L4 ${shY + 4} L6 ${shY + 30} L0 ${shY + 38} L-6 ${shY + 30} Z`} fill={tie ?? '#24365a'} stroke={INK} strokeWidth={2} />
          <path d={`M-14 ${shY - 6} L-30 ${shY + 8} L-12 ${shY + 40} L-2 ${shY + 34} Z M14 ${shY - 6} L30 ${shY + 8} L12 ${shY + 40} L2 ${shY + 34} Z`} fill={shade(jacket, -0.12)} stroke={INK} strokeWidth={3} strokeLinejoin="round" />
          {[0, 1].map((i) => <g key={i}><circle cx={-16} cy={shY + 48 + i * 14} r={3} fill={shade(jacket, -0.45)} /><circle cx={16} cy={shY + 48 + i * 14} r={3} fill={shade(jacket, -0.45)} /></g>)}
          <path d={`M${-w - 1} ${hipY - 16} L${w + 1} ${hipY - 16}`} stroke={shade(jacket, -0.3)} strokeWidth={10} />
          <rect x={-9} y={hipY - 23} width={18} height={14} rx={2} fill="none" stroke="#5a4a2a" strokeWidth={3} />
          <path d={`M${-w + 4} ${shY + 14} q8 10 0 22 M${w - 4} ${shY + 14} q-8 10 0 22`} stroke={shade(jacket, -0.25)} strokeWidth={3} fill="none" />
        </g>
      );
    case 'tweed':
      return (
        <g>
          {/* open tweed jacket over a knitted vest and shirt */}
          <path d={`M-20 ${shY - 2} L-15 ${hipY - 4} L15 ${hipY - 4} L20 ${shY - 2} Z`} fill={vest ?? '#c99a3a'} stroke={INK} strokeWidth={3} strokeLinejoin="round" />
          <path d={`M-12 ${shY - 4} L0 ${shY + 18} L12 ${shY - 4} Z`} fill="#f4f1ea" stroke={INK} strokeWidth={2.5} />
          <path d={`M-4 ${shY + 4} L4 ${shY + 4} L5 ${shY + 22} L0 ${shY + 28} L-5 ${shY + 22} Z`} fill="#2c4a6b" stroke={INK} strokeWidth={2} />
          {[0, 1, 2].map((i) => <circle key={i} cx={0} cy={shY + 38 + i * 14} r={2.6} fill={INK} opacity={0.7} />)}
          <path d={`M-22 ${shY - 4} L-8 ${shY + 34} M22 ${shY - 4} L8 ${shY + 34}`} stroke={INK} strokeWidth={3} />
          <path d={`M${-w + 6} ${shY + 44} h16 M${w - 22} ${shY + 44} h16`} stroke={INK} strokeWidth={2.5} strokeOpacity={0.6} />
          {[0, 1, 2, 3, 4].map((i) => <path key={i} d={`M${-w + 2 + i * 3} ${shY + 10 + i * 12} l6 4 M${w - 8 - i * 3} ${shY + 10 + i * 12} l6 4`} stroke="#fff" strokeOpacity={0.12} strokeWidth={2} />)}
        </g>
      );
    case 'suit':
      return (
        <g>
          {extra.has('vest') ? <path d={`M-18 ${shY} L-14 ${hipY - 6} L14 ${hipY - 6} L18 ${shY} Z`} fill={vest ?? '#5a4a3a'} stroke={INK} strokeWidth={2.5} /> : null}
          <path d={`M-14 ${shY - 4} L0 ${shY + 34} L14 ${shY - 4} Z`} fill="#f4f1ea" stroke={INK} strokeWidth={3} />
          {extra.has('bowtie') ? (
            <path d={`M-12 ${shY + 2} L0 ${shY + 7} L12 ${shY + 2} L12 ${shY + 14} L0 ${shY + 9} L-12 ${shY + 14} Z`} fill="#8b1d24" stroke={INK} strokeWidth={2.5} />
          ) : (
            <path d={`M-5 ${shY + 2} L5 ${shY + 2} L7 ${shY + 34} L0 ${shY + 42} L-7 ${shY + 34} Z`} fill={extra.has('redtie') ? '#a8262a' : '#3c4a6b'} stroke={INK} strokeWidth={2.5} />
          )}
          <path d={`M-18 ${shY - 4} L-2 ${shY + 44} M18 ${shY - 4} L2 ${shY + 44}`} stroke={INK} strokeWidth={3} />
          <circle cx={0} cy={shY + 56} r={3} fill={INK} />
        </g>
      );
    case 'navy':
    case 'navywhite':
      return (
        <g>
          <path d={`M-12 ${shY - 4} L0 ${shY + 20} L12 ${shY - 4}`} fill="#f4f1ea" stroke={INK} strokeWidth={3} />
          {outfit === 'navy' ? <path d={`M-4 ${shY + 2} L4 ${shY + 2} L5 ${shY + 22} L-5 ${shY + 22} Z`} fill="#1b1b1b" /> : null}
          {[0, 1, 2].map((i) => (
            <g key={i}>
              <circle cx={-11} cy={shY + 30 + i * 18} r={3.4} fill={btn} stroke={INK} strokeWidth={1.5} />
              <circle cx={11} cy={shY + 30 + i * 18} r={3.4} fill={btn} stroke={INK} strokeWidth={1.5} />
            </g>
          ))}
          {outfit === 'navywhite' ? (
            <path d={`M-26 ${shY + 4} l12 0 M14 ${shY + 4} l12 0`} stroke="#2a3550" strokeWidth={5} />
          ) : (
            <path d={`M${-w + 4} ${hipY - 8} l14 0 M${w - 18} ${hipY - 8} l14 0`} stroke="#e3b94a" strokeWidth={3} />
          )}
        </g>
      );
    case 'sailor':
      return (
        <g>
          <path d={`M-30 ${shY - 2} L30 ${shY - 2} L22 ${shY + 22} L0 ${shY + 38} L-22 ${shY + 22} Z`} fill="#2c3f6b" stroke={INK} strokeWidth={3} />
          <path d={`M-24 ${shY + 18} L0 ${shY + 33} L24 ${shY + 18}`} stroke="#fff" strokeWidth={2.5} fill="none" />
          <path d={`M-6 ${shY + 34} L0 ${shY + 48} L6 ${shY + 34} Z`} fill="#1b1b1b" />
        </g>
      );
    case 'civil':
      return (
        <g>
          <path d={`M-12 ${shY - 4} L0 ${shY + 12} L12 ${shY - 4}`} fill="none" stroke={INK} strokeWidth={3} />
          <path d={`M0 ${shY + 12} L0 ${hipY}`} stroke={dark} strokeWidth={2} />
          {[0, 1, 2].map((i) => <circle key={i} cx={4} cy={shY + 24 + i * 16} r={2.4} fill={dark} />)}
        </g>
      );
    case 'dress':
    case 'robe':
      return <path d={`M-10 ${shY - 4} Q0 ${shY + 12} 10 ${shY - 4}`} fill="none" stroke={INK} strokeWidth={3} />;
    case 'armor':
      return (
        <g>
          {[0, 1, 2, 3].map((i) => <path key={i} d={`M${-w + 2} ${shY + 18 + i * 15} Q0 ${shY + 26 + i * 15} ${w - 2} ${shY + 18 + i * 15}`} stroke={INK} strokeWidth={2.5} fill="none" />)}
        </g>
      );
    default: {
      // military tunic: collar, buttons, pockets, belt
      const party = outfit === 'party';
      return (
        <g>
          <path d={`M-16 ${shY - 4} L0 ${shY + 22} L16 ${shY - 4}`} fill={party ? '#f0ece2' : shade(jacket, -0.1)} stroke={INK} strokeWidth={3} />
          {party || extra.has('tie') ? <path d={`M-4 ${shY + 4} L4 ${shY + 4} L5 ${shY + 22} L0 ${shY + 26} L-5 ${shY + 22} Z`} fill="#3a2b22" /> : null}
          <path d={`M-16 ${shY - 2} l-8 8 l8 4 z M16 ${shY - 2} l8 8 l-8 4 z`} fill={dark} stroke={INK} strokeWidth={2} />
          {[0, 1, 2, 3].map((i) => <circle key={i} cx={0} cy={shY + 30 + i * 13} r={2.8} fill={btn} />)}
          <path d={`M-28 ${shY + 30} h18 v12 h-18 z M10 ${shY + 30} h18 v12 h-18 z`} fill="none" stroke={dark} strokeWidth={2.5} />
          <path d={`M${-w - 1} ${hipY - 12} L${w + 1} ${hipY - 12}`} stroke="#3a2b22" strokeWidth={8} />
          <rect x={-7} y={hipY - 17} width={14} height={10} rx={2} fill="#c9a24a" stroke={INK} strokeWidth={1.5} />
          {extra.has('medals') ? (
            <g>
              {[0, 1, 2].map((i) => (
                <g key={i}>
                  <rect x={-30 + i * 7} y={shY + 14} width={6} height={9} fill={['#c8352b', '#3a6ea5', '#e3b94a'][i]} />
                  <circle cx={-27 + i * 7} cy={shY + 27} r={3.5} fill="#e3b94a" stroke={INK} strokeWidth={1} />
                </g>
              ))}
            </g>
          ) : null}
          {extra.has('epaulettes') ? <path d={`M-40 ${shY - 2} h16 M24 ${shY - 2} h16`} stroke="#e3b94a" strokeWidth={6} strokeLinecap="round" /> : null}
          {extra.has('ironcross') ? <path d={`M-4 ${shY + 2} h8 v-0 M0 ${shY - 2} v8`} stroke="#1b1b1b" strokeWidth={4} /> : null}
          {extra.has('star') ? <circle cx={-20} cy={shY + 20} r={5} fill="#e3b94a" stroke={INK} strokeWidth={1.5} /> : null}
        </g>
      );
    }
  }
};

const Head: React.FC<{
  spec: CharSpec; expr: string; blink: boolean; talk: number; look: number; hy: number; hairC: string; skin: string; back: boolean; extra: Set<string>; t: number; seed: string; turn?: number;
}> = ({ spec, expr, blink, talk, look, hy, hairC, skin, back, extra, t, seed, turn = 0 }) => {
  const rx = 68, ry = 63;
  const jowl = extra.has('jowls') || (spec.build ?? 1) > 1.15;
  const age = spec.age ?? 0.3;
  const face = jowl
    ? `M${-rx} ${hy - 6} C${-rx} ${hy - 106} ${rx} ${hy - 106} ${rx} ${hy - 6} C${rx + 4} ${hy + 62} ${-rx - 4} ${hy + 62} ${-rx} ${hy - 6} Z`
    : `M${-rx} ${hy} C${-rx} ${hy - 98} ${rx} ${hy - 98} ${rx} ${hy} C${rx} ${hy + 66} ${-rx} ${hy + 66} ${-rx} ${hy} Z`;
  const hat = spec.hat ?? 'none';
  const hatC = spec.hatColor ?? nation(spec.nation).uniform;

  if (back) {
    return (
      <g>
        <path d={face} fill={hat === 'pilot' ? '#7a4a2a' : hairC} stroke={INK} strokeWidth={Lw} />
        <ellipse cx={-rx + 2} cy={hy + 4} rx={8} ry={13} fill={skin} stroke={INK} strokeWidth={3} />
        <ellipse cx={rx - 2} cy={hy + 4} rx={8} ry={13} fill={skin} stroke={INK} strokeWidth={3} />
        <Hat kind={hat} color={hatC} hy={hy} badge={spec.badge} nationKey={spec.nation} back />
      </g>
    );
  }

  const eyeY = hy - 4;
  const skinLid = skin;
  const ex = 24;
  const eyesKind = spec.eyes ?? 'dot';
  const sweat = expr === 'worried' || expr === 'sweat' || expr === 'panic' || expr === 'nervous' || expr === 'grin';
  const browY = eyeY - 22 + (expr === 'shocked' || expr === 'panic' ? -8 : 0);
  const browC = hairC === '#c9c4bc' ? '#9a948c' : hairC;
  const brow = (s: number) => {
    let a = 0; // tilt: positive = inner end down (angry)
    if (expr === 'angry' || expr === 'determined' || expr === 'smug') a = 8;
    if (expr === 'worried' || expr === 'sad' || expr === 'cry' || expr === 'panic' || expr === 'nervous' || expr === 'sweat') a = -9;
    const ix = s * 8, ox = s * 38;
    return <path key={s} d={`M${ix} ${browY + a} Q${s * 23} ${browY - 5} ${ox} ${browY - a * 0.4}`} stroke={browC} strokeWidth={extra.has('thickbrows') ? 8 : 5} fill="none" strokeLinecap="round" />;
  };
  const eye = (s: number) => {
    const x = s * ex + look;
    if (eyesKind === 'heavy' && !(expr === 'happy' || expr === 'laugh' || expr === 'cry')) {
      // sardonic heavy-lidded eye: white oval, small pupil, upper lid covers a share of it
      const wide = expr === 'shocked' || expr === 'panic';
      const rxE = 15, ryE = wide ? 17 : 13;
      let lid = expr === 'smug' || expr === 'tired' ? 0.6 : expr === 'angry' || expr === 'determined' ? 0.5 : expr === 'worried' || expr === 'sad' || expr === 'nervous' ? 0.32 : wide ? 0 : 0.44;
      if (blink) lid = 1;
      const tilt = expr === 'angry' || expr === 'determined' ? s * -5 : expr === 'worried' || expr === 'sad' || expr === 'nervous' ? s * 5 : 0;
      const lidY = eyeY - ryE + 2 * ryE * lid;
      const cid = `ec${s}_${seed.replace(/[^a-zA-Z0-9]/g, "")}_${Math.round(look)}`;
      return (
        <g key={s}>
          <defs>
            <clipPath id={cid}><ellipse cx={x} cy={eyeY} rx={rxE} ry={ryE} /></clipPath>
          </defs>
          <ellipse cx={x} cy={eyeY} rx={rxE} ry={ryE} fill="#fff" />
          <g clipPath={`url(#${cid})`}>
            <circle cx={x + look * 0.9 + s * -1.5} cy={eyeY + (wide ? 0 : 3)} r={wide ? 3.6 : 5.2} fill={INK} />
            <path d={`M${x - rxE - 2} ${eyeY - ryE - 4} H${x + rxE + 2} V${lidY - tilt} L${x - rxE - 2} ${lidY + tilt} Z`} fill={skinLid} />
          </g>
          <ellipse cx={x} cy={eyeY} rx={rxE} ry={ryE} fill="none" stroke={INK} strokeWidth={3} />
          {lid > 0.05 ? <path d={`M${x - rxE - 3} ${lidY + tilt} L${x + rxE + 3} ${lidY - tilt}`} stroke={INK} strokeWidth={4.5} strokeLinecap="round" /> : null}
          <path d={`M${x - 10} ${eyeY + ryE + 6} Q${x} ${eyeY + ryE + 10} ${x + 10} ${eyeY + ryE + 5}`} stroke="#9a9aa6" strokeWidth={2.5} fill="none" strokeLinecap="round" opacity={0.7} />
        </g>
      );
    }
    if (blink || expr === 'happy' || expr === 'laugh') return <path key={s} d={`M${x - 9} ${eyeY + (expr === 'happy' || expr === 'laugh' ? 3 : 0)} Q${x} ${eyeY - (expr === 'happy' || expr === 'laugh' ? 9 : -3)} ${x + 9} ${eyeY + (expr === 'happy' || expr === 'laugh' ? 3 : 0)}`} stroke={INK} strokeWidth={4} fill="none" strokeLinecap="round" />;
    if (expr === 'cry' || expr === 'sad') return <path key={s} d={`M${x - 9} ${eyeY} Q${x} ${eyeY + 6} ${x + 9} ${eyeY}`} stroke={INK} strokeWidth={4} fill="none" strokeLinecap="round" />;
    if (expr === 'shocked' || expr === 'panic' || eyesKind === 'big')
      return (
        <g key={s}>
          <ellipse cx={x} cy={eyeY} rx={12} ry={14} fill="#fff" stroke={INK} strokeWidth={3} />
          <circle cx={x + look * 0.6} cy={eyeY + 1} r={expr === 'panic' ? 3.5 : 5} fill={INK} />
        </g>
      );
    if (eyesKind === 'lid' || expr === 'smug' || expr === 'tired')
      return (
        <g key={s}>
          <path d={`M${x - 11} ${eyeY - 1} Q${x} ${eyeY - 7} ${x + 11} ${eyeY - 1}`} stroke={INK} strokeWidth={4} fill="none" strokeLinecap="round" />
          <path d={`M${x - 7} ${eyeY + 1} Q${x} ${eyeY + 5} ${x + 7} ${eyeY + 1}`} stroke={INK} strokeWidth={3.5} fill="none" strokeLinecap="round" />
        </g>
      );
    return <ellipse key={s} cx={x} cy={eyeY} rx={expr === 'angry' ? 5 : 5.5} ry={expr === 'angry' ? 5 : 7} fill={INK} />;
  };

  const my = hy + 33;
  let mouth: React.ReactNode;
  const open = Math.max(talk, expr === 'shocked' || expr === 'panic' || expr === 'shout' || expr === 'laugh' ? 1 : 0);
  if (open > 0.15) {
    const h = 4 + open * (expr === 'shout' || expr === 'panic' ? 16 : 10);
    mouth = (
      <g>
        <ellipse cx={0} cy={my + 2} rx={expr === 'shocked' ? 8 : 11} ry={h} fill="#6b2a26" stroke={INK} strokeWidth={3} />
        <ellipse cx={0} cy={my + 2 + h * 0.5} rx={6} ry={Math.max(1, h * 0.35)} fill="#d9787a" />
      </g>
    );
  } else if (expr === 'grin') {
    // forced nervous grin: wide mouth with teeth
    mouth = (
      <g>
        <path d={`M-26 ${my - 6} Q0 ${my + 22} 26 ${my - 6} Z`} fill="#fff" stroke={INK} strokeWidth={4} strokeLinejoin="round" />
        <path d={`M-22 ${my - 1} Q0 ${my + 6} 22 ${my - 1}`} stroke={INK} strokeWidth={2} fill="none" />
        {[-12, 0, 12].map((x) => <line key={x} x1={x} y1={my - 4} x2={x} y2={my + 8} stroke={INK} strokeWidth={1.8} />)}
      </g>
    );
  } else if (expr === 'happy' || expr === 'smile' || expr === 'smug') {
    mouth = <path d={`M-14 ${my - 2} Q0 ${my + (expr === 'smug' ? 5 : 11)} 14 ${my - (expr === 'smug' ? 6 : 2)}`} stroke={INK} strokeWidth={4} fill="none" strokeLinecap="round" />;
  } else if (expr === 'angry' || expr === 'determined') {
    mouth = expr === 'angry' ? (
      <g>
        <rect x={-13} y={my - 4} width={26} height={11} rx={3} fill="#fff" stroke={INK} strokeWidth={3} />
        <path d={`M-13 ${my + 1.5} h26`} stroke={INK} strokeWidth={1.5} />
      </g>
    ) : <path d={`M-12 ${my} h24`} stroke={INK} strokeWidth={4} strokeLinecap="round" />;
  } else if (expr === 'sad' || expr === 'cry' || expr === 'worried' || expr === 'nervous') {
    mouth = expr === 'nervous'
      ? <path d={`M-14 ${my} q4 -5 8 0 q4 5 8 0 q4 -5 8 0`} stroke={INK} strokeWidth={3.5} fill="none" strokeLinecap="round" />
      : <path d={`M-12 ${my + 4} Q0 ${my - 6} 12 ${my + 4}`} stroke={INK} strokeWidth={4} fill="none" strokeLinecap="round" />;
  } else {
    mouth = <path d={`M-9 ${my} Q0 ${my + 3} 9 ${my}`} stroke={INK} strokeWidth={3.5} fill="none" strokeLinecap="round" />;
  }

  const redFace = expr === 'angry' || expr === 'rage';
  return (
    <g>
      {/* ears */}
      {turn > -0.55 ? <ellipse cx={-rx + 1 + Math.max(0, turn) * 22} cy={hy + 2} rx={9} ry={14} fill={skin} stroke={INK} strokeWidth={3} /> : null}
      {turn < 0.55 ? <ellipse cx={rx - 1 + Math.min(0, turn) * 22} cy={hy + 2} rx={9} ry={14} fill={skin} stroke={INK} strokeWidth={3} /> : null}
      <path d={face} fill={skin} stroke={INK} strokeWidth={Lw} />
      {turn !== 0 ? (
        // the side of the head turned away: a soft darker crescent + the ear moved onto the cheek
        <g>
          <defs><clipPath id={`fc_${seed.replace(/[^a-zA-Z0-9]/g, '')}`}><path d={face} /></clipPath></defs>
          <g clipPath={`url(#fc_${seed.replace(/[^a-zA-Z0-9]/g, '')})`}>
            <ellipse cx={-Math.sign(turn) * (rx + 30 - Math.abs(turn) * 34)} cy={hy + 6} rx={46} ry={90} fill="#8a6a58" opacity={0.18 * Math.abs(turn) + 0.06} />
          </g>
        </g>
      ) : null}
      {redFace ? <path d={face} fill="#e0504a" opacity={0.28} /> : null}
      {/* chin shade */}
      {spec.shadeFace ? (
        <path d={`M${-rx + 2} ${hy + 6} Q${-rx + 10} ${hy + 46} 0 ${hy + 50} Q${rx - 10} ${hy + 46} ${rx - 2} ${hy + 6} Q${rx - 18} ${hy + 30} 0 ${hy + 34} Q${-rx + 18} ${hy + 30} ${-rx + 2} ${hy + 6} Z`} fill="#b9bfcf" opacity={0.42} />
      ) : (
        <path d={`M${-rx + 16} ${hy + 34} Q0 ${hy + 66} ${rx - 16} ${hy + 34} Q0 ${hy + 56} ${-rx + 16} ${hy + 34}`} fill="#e6bfa2" opacity={0.55} />
      )}
      <g transform={`translate(${turn * 21} 0)`}>
      {extra.has('freckles') ? (
        <g fill="#c9946e" opacity={0.75}>
          {[[-44, 14], [-36, 20], [-50, 22], [-40, 28], [44, 14], [36, 20], [50, 22], [40, 28]].map(([fx, fy], i) => <circle key={i} cx={fx} cy={hy + fy} r={2.2} />)}
        </g>
      ) : null}
      {extra.has('stubble') || spec.facial === 'stubble' ? <path d={`M${-rx + 12} ${hy + 24} Q0 ${hy + 66} ${rx - 12} ${hy + 24} Q0 ${hy + 46} ${-rx + 12} ${hy + 24}`} fill="#8c7f72" opacity={0.35} /> : null}
      {extra.has('blush') || expr === 'happy' || expr === 'smile' ? (
        <>
          <ellipse cx={-40} cy={hy + 14} rx={10} ry={6} fill="#ef8f8f" opacity={0.45} />
          <ellipse cx={40} cy={hy + 14} rx={10} ry={6} fill="#ef8f8f" opacity={0.45} />
        </>
      ) : null}
      {age > 0.55 || extra.has('wrinkles') ? (
        <g stroke="#b88f74" strokeWidth={2.5} fill="none" strokeLinecap="round">
          <path d={`M-18 ${hy - 44} q18 -5 36 0`} />
          <path d={`M-14 ${hy - 37} q14 -4 28 0`} />
          <path d={`M-36 ${eyeY + 12} q5 3 10 0 M26 ${eyeY + 12} q5 3 10 0`} />
          <path d={`M-22 ${my - 10} q-6 6 -4 12 M22 ${my - 10} q6 6 4 12`} />
        </g>
      ) : null}
      </g>
      <Hair kind={spec.hair ?? 'short'} color={hairC} hy={hy} rx={rx} hat={hat} />
      <g transform={`translate(${turn * 21} 0)`}>
      {[-1, 1].map(brow)}
      {[-1, 1].map((s2) => {
        // the far eye is foreshortened
        const far = turn !== 0 && Math.sign(turn) !== s2;
        const k2 = far ? 1 - 0.28 * Math.abs(turn) : 1;
        return <g key={s2} transform={`translate(${s2 * ex} 0) scale(${k2} 1) translate(${-s2 * ex} 0)`}>{eye(s2)}</g>;
      })}
      {/* nose */}
      <path d={`M-3 ${hy + 8} q4 5 8 0`} stroke="#b88f74" strokeWidth={3} fill="none" strokeLinecap="round" />
      <Facial kind={spec.facial ?? 'none'} color={hairC === '#c9c4bc' ? '#a29c94' : hairC} my={my} />
      {mouth}
      {spec.glasses && spec.glasses !== 'none' ? <Glasses kind={spec.glasses} eyeY={eyeY} ex={ex} /> : null}
      {extra.has('monocle') ? <circle cx={ex} cy={eyeY} r={13} fill="#dfeff7" opacity={0.6} stroke={INK} strokeWidth={2.5} /> : null}
      {extra.has('cigar') ? (
        <g>
          <path d={`M14 ${my + 2} l42 8`} stroke={INK} strokeWidth={10} strokeLinecap="round" />
          <path d={`M14 ${my + 2} l42 8`} stroke="#7a4a28" strokeWidth={6} strokeLinecap="round" />
          <circle cx={57} cy={my + 10} r={3} fill="#f08a3a" />
          <circle cx={64 + Math.sin(t * 2) * 3} cy={my - 8 - ((t * 20) % 30)} r={4 + ((t * 20) % 30) / 8} fill="#ddd" opacity={0.6 - ((t * 20) % 30) / 60} />
        </g>
      ) : null}
      {extra.has('pipe') ? <path d={`M10 ${my + 4} q20 6 30 0 v-14 h12 v18 q-4 8 -14 6`} fill="#5a3a22" stroke={INK} strokeWidth={3} /> : null}
      {extra.has('cigarette') ? <path d={`M12 ${my + 2} l46 -10`} stroke="#1b1b1b" strokeWidth={4} /> : null}
      {sweat ? <Sweat hy={hy} t={t} /> : null}
      </g>
      {expr === 'cry' ? (
        <g fill="#7cc4f0" stroke={INK} strokeWidth={2}>
          <path d={`M${-ex - 4} ${eyeY + 6} q-6 ${14 + ((t * 30) % 20)} 0 ${18 + ((t * 30) % 20)} q6 -4 0 ${-18 - ((t * 30) % 20)}`} />
          <path d={`M${ex + 4} ${eyeY + 6} q-6 ${14 + ((t * 30 + 9) % 20)} 0 ${18 + ((t * 30 + 9) % 20)} q6 -4 0 ${-18 - ((t * 30 + 9) % 20)}`} />
        </g>
      ) : null}
      <Hat kind={hat} color={hatC} hy={hy} badge={spec.badge} nationKey={spec.nation} />
      {extra.has('pencil') ? (
        <g transform={`translate(${rx + 14} ${hy - 2}) rotate(-24)`}>
          <rect x={-4} y={-34} width={9} height={46} fill="#f2c230" stroke={INK} strokeWidth={2.5} />
          <path d="M-4 12 L0.5 24 L5 12 Z" fill="#e9cfa8" stroke={INK} strokeWidth={2.5} strokeLinejoin="round" />
          <rect x={-4} y={-42} width={9} height={9} fill="#e88a8a" stroke={INK} strokeWidth={2.5} />
        </g>
      ) : null}
      {expr === 'angry' || expr === 'rage' ? <path d={`M${rx - 18} ${hy - 62} l10 -6 m-4 14 l12 -2 m-20 -16 l2 -12`} stroke="#c8352b" strokeWidth={4} strokeLinecap="round" /> : null}
    </g>
  );
};

const Sweat: React.FC<{ hy: number; t: number }> = ({ hy, t }) => {
  const k = (t * 0.9) % 1;
  return (
    <g>
      <path d={`M78 ${hy - 50} q-11 18 0 24 q11 -6 0 -24`} fill="#8fd0f5" stroke={INK} strokeWidth={2.5} />
      <path d={`M-74 ${hy - 30 + k * 30} q-8 13 0 18 q8 -5 0 -18`} fill="#8fd0f5" stroke={INK} strokeWidth={2.5} opacity={1 - k} />
    </g>
  );
};

const Hair: React.FC<{ kind: string; color: string; hy: number; rx: number; hat: string }> = ({ kind, color, hy, rx, hat }) => {
  const top = hy - 72;
  const covered = hat !== 'none' && hat !== 'beret' && hat !== 'garrison';
  switch (kind) {
    case 'none':
      return null;
    case 'bald':
    case 'baldtop':
      return (
        <g fill={color} stroke={INK} strokeWidth={3}>
          <path d={`M${-rx + 1} ${hy - 4} q-2 -26 14 -36 q-2 16 2 36 z`} />
          <path d={`M${rx - 1} ${hy - 4} q2 -26 -14 -36 q2 16 -2 36 z`} />
          {kind === 'baldtop' ? <path d={`M-14 ${top - 1} q14 -6 28 0`} fill="none" strokeWidth={2.5} stroke={color} /> : null}
          {kind === 'bald' ? <ellipse cx={-22} cy={top + 10} rx={14} ry={6} fill="#fff" stroke="none" opacity={0.45} /> : null}
        </g>
      );
    case 'side':
      // dark cap of hair with a heavy fringe swept to one side
      return (
        <g>
          <path d={`M${-rx} ${hy - 2} C${-rx - 4} ${hy - 104} ${rx + 4} ${hy - 104} ${rx} ${hy - 2} C${rx - 6} ${hy - 30} ${rx - 14} ${hy - 38} ${rx - 22} ${hy - 44} L${-30} ${hy - 22} C${-46} ${hy - 30} ${-rx + 6} ${hy - 30} ${-rx} ${hy - 2} Z`} fill={color} stroke={INK} strokeWidth={Lw} />
          <path d={`M${rx - 8} ${hy - 50} C${30} ${hy - 44} ${-6} ${hy - 30} ${-34} ${hy - 12} C${-30} ${hy - 30} ${-14} ${hy - 50} ${8} ${hy - 62} Z`} fill={color} stroke={INK} strokeWidth={3} strokeLinejoin="round" />
          <path d={`M${-10} ${hy - 70} Q${20} ${hy - 66} ${rx - 24} ${hy - 52}`} stroke="#fff" strokeOpacity={0.25} strokeWidth={4} fill="none" />
        </g>
      );
    case 'back':
      return (
        <g>
          <path d={`M${-rx - 2} ${hy - 4} C${-rx - 6} ${hy - 108} ${rx + 6} ${hy - 108} ${rx + 2} ${hy - 4} C${rx - 6} ${hy - 40} ${rx - 16} ${hy - 50} 0 ${hy - 50} C${-rx + 16} ${hy - 50} ${-rx + 6} ${hy - 40} ${-rx - 2} ${hy - 4} Z`} fill={color} stroke={INK} strokeWidth={Lw} />
          <path d={`M-30 ${hy - 70} q30 -10 60 0 M-40 ${hy - 60} q40 -12 80 0`} stroke="#fff" strokeOpacity={0.22} strokeWidth={3} fill="none" />
        </g>
      );
    case 'part':
      return (
        <path d={`M${-rx} ${hy - 4} C${-rx - 4} ${hy - 106} ${rx + 4} ${hy - 106} ${rx} ${hy - 4} C${rx - 4} ${hy - 34} ${rx - 12} ${hy - 44} ${-12} ${hy - 48} L${-20} ${hy - 62} C${-34} ${hy - 44} ${-rx + 4} ${hy - 34} ${-rx} ${hy - 4} Z`} fill={color} stroke={INK} strokeWidth={Lw} />
      );
    case 'curly':
      return (
        <g fill={color} stroke={INK} strokeWidth={3}>
          {[-56, -34, -12, 12, 34, 56].map((x, i) => <circle key={i} cx={x} cy={top + 8 + Math.abs(x) * 0.35} r={17} />)}
        </g>
      );
    case 'bun':
    case 'long':
      return (
        <g>
          {kind === 'long' ? <path d={`M${-rx - 6} ${hy - 10} Q${-rx - 14} ${hy + 60} ${-rx + 10} ${hy + 70} L${rx - 10} ${hy + 70} Q${rx + 14} ${hy + 60} ${rx + 6} ${hy - 10} Z`} fill={color} stroke={INK} strokeWidth={Lw} /> : <circle cx={0} cy={top - 12} r={20} fill={color} stroke={INK} strokeWidth={Lw} />}
          <path d={`M${-rx} ${hy - 4} C${-rx - 4} ${hy - 106} ${rx + 4} ${hy - 106} ${rx} ${hy - 4} C${rx - 10} ${hy - 40} ${10} ${hy - 50} 0 ${hy - 46} C${-10} ${hy - 50} ${-rx + 10} ${hy - 40} ${-rx} ${hy - 4} Z`} fill={color} stroke={INK} strokeWidth={Lw} />
        </g>
      );
    case 'tousled':
      // full brown mop with a swept fringe and a cowlick — the host's silhouette
      return (
        <g>
          <path d={`M${-rx - 3} ${hy + 2} C${-rx - 8} ${hy - 110} ${rx + 8} ${hy - 110} ${rx + 3} ${hy + 2} C${rx - 2} ${hy - 22} ${rx - 10} ${hy - 34} ${rx - 18} ${hy - 38} Q${20} ${hy - 30} ${-6} ${hy - 44} Q${-20} ${hy - 26} ${-40} ${hy - 34} C${-52} ${hy - 30} ${-rx + 2} ${hy - 22} ${-rx - 3} ${hy + 2} Z`} fill={color} stroke={INK} strokeWidth={Lw} strokeLinejoin="round" />
          <path d={`M${-4} ${top + 2} q-6 -26 14 -34 q-6 14 4 22 q6 -18 22 -16 q-14 8 -10 26 z`} fill={color} stroke={INK} strokeWidth={3} strokeLinejoin="round" />
          <path d={`M${-34} ${hy - 62} Q0 ${hy - 76} ${34} ${hy - 62}`} stroke="#fff" strokeOpacity={0.22} strokeWidth={5} fill="none" strokeLinecap="round" />
        </g>
      );
    case 'messy':
      return <path d={`M${-rx} ${hy - 6} l4 -40 l10 8 l6 -30 l12 16 l10 -24 l12 18 l12 -20 l8 20 l14 -12 l2 30 l12 -4 l-6 36 Q0 ${hy - 46} ${-rx} ${hy - 6} Z`} fill={color} stroke={INK} strokeWidth={Lw} strokeLinejoin="round" />;
    default: // short
      if (covered) return <path d={`M${-rx + 1} ${hy - 14} q2 -22 12 -30 L${-rx + 11} ${hy - 12} Z M${rx - 1} ${hy - 14} q-2 -22 -12 -30 L${rx - 11} ${hy - 12} Z`} fill={color} stroke={INK} strokeWidth={3} strokeLinejoin="round" />;
      return <path d={`M${-rx} ${hy - 6} C${-rx - 4} ${hy - 106} ${rx + 4} ${hy - 106} ${rx} ${hy - 6} C${rx - 8} ${hy - 38} ${rx - 20} ${hy - 44} 0 ${hy - 44} C${-rx + 20} ${hy - 44} ${-rx + 8} ${hy - 38} ${-rx} ${hy - 6} Z`} fill={color} stroke={INK} strokeWidth={Lw} />;
  }
};

const Facial: React.FC<{ kind: string; color: string; my: number }> = ({ kind, color, my }) => {
  const y = my - 9;
  switch (kind) {
    case 'toothbrush':
      return <rect x={-10} y={y - 6} width={20} height={11} rx={2} fill={color} stroke={INK} strokeWidth={2} />;
    case 'walrus':
      return <path d={`M-34 ${y + 10} Q-26 ${y - 12} 0 ${y - 4} Q26 ${y - 12} 34 ${y + 10} Q20 ${y + 2} 0 ${y + 6} Q-20 ${y + 2} -34 ${y + 10} Z`} fill={color} stroke={INK} strokeWidth={2.5} />;
    case 'pencil':
      return <path d={`M-16 ${y + 2} Q0 ${y - 4} 16 ${y + 2}`} stroke={color} strokeWidth={4} fill="none" strokeLinecap="round" />;
    case 'handlebar':
      return <path d={`M0 ${y} Q-20 ${y - 6} -30 ${y + 2} q-6 -10 2 -14 M0 ${y} Q20 ${y - 6} 30 ${y + 2} q6 -10 -2 -14`} stroke={color} strokeWidth={6} fill="none" strokeLinecap="round" />;
    case 'beard':
      return <path d={`M-60 ${y - 16} Q-58 ${y + 44} 0 ${y + 52} Q58 ${y + 44} 60 ${y - 16} Q46 ${y + 18} 20 ${y + 2} Q0 ${y - 4} -20 ${y + 2} Q-46 ${y + 18} -60 ${y - 16} Z`} fill={color} stroke={INK} strokeWidth={3} />;
    case 'goatee':
      return <path d={`M-10 ${y + 22} Q0 ${y + 44} 10 ${y + 22} Z M-18 ${y + 2} Q0 ${y - 6} 18 ${y + 2}`} fill={color} stroke={color} strokeWidth={4} />;
    default:
      return null;
  }
};

const Glasses: React.FC<{ kind: string; eyeY: number; ex: number }> = ({ kind, eyeY, ex }) => {
  if (kind === 'sun')
    return (
      <g>
        <path d={`M${-ex - 18} ${eyeY - 9} h34 l-4 18 h-26 z M${ex - 16} ${eyeY - 9} h34 l-4 18 h-26 z`} fill="#1b1b1b" stroke={INK} strokeWidth={2} />
        <path d={`M-2 ${eyeY - 6} h4`} stroke={INK} strokeWidth={3} />
      </g>
    );
  const r = kind === 'pince' ? 11 : 15;
  return (
    <g fill="#e8f4fa" fillOpacity={0.35} stroke={INK} strokeWidth={3}>
      <circle cx={-ex} cy={eyeY} r={r} />
      <circle cx={ex} cy={eyeY} r={r} />
      <path d={`M${-ex + r} ${eyeY - 2} Q0 ${eyeY - 8} ${ex - r} ${eyeY - 2}`} fill="none" />
      {kind === 'round' ? <path d={`M${-ex - r} ${eyeY - 2} l-24 -4 M${ex + r} ${eyeY - 2} l24 -4`} fill="none" /> : null}
    </g>
  );
};

export const Hat: React.FC<{ kind: string; color: string; hy: number; badge?: string; nationKey?: string; back?: boolean }> = ({ kind, color, hy, badge, nationKey, back }) => {
  const top = hy - 70;
  const dark = shade(color, -0.35);
  const nat = nation(nationKey);
  const b = badge ?? (nat.mark === 'star' ? '#c8352b' : nat.mark === 'whitestar' ? '#e3b94a' : '#d9c27a');
  const emblem = (x: number, y: number, s = 1) =>
    back ? null : nat.mark === 'star' ? (
      <path transform={`translate(${x} ${y}) scale(${s})`} d="M0 -10 L2.9 -3.1 L10 -3.1 L4.3 1.2 L6.5 8.1 L0 3.8 L-6.5 8.1 L-4.3 1.2 L-10 -3.1 L-2.9 -3.1 Z" fill="#c8352b" stroke={INK} strokeWidth={1.2} />
    ) : nat.mark === 'sun' ? (
      <path transform={`translate(${x} ${y}) scale(${s})`} d="M0 -9 L2.6 -2.8 L9 -2.8 L3.9 1.1 L5.8 7.3 L0 3.4 L-5.8 7.3 L-3.9 1.1 L-9 -2.8 L-2.6 -2.8 Z" fill="#e3b94a" stroke={INK} strokeWidth={1.2} />
    ) : (
      <ellipse cx={x} cy={y} rx={9 * s} ry={6 * s} fill={b} stroke={INK} strokeWidth={1.5} />
    );
  switch (kind) {
    case 'peaked':
    case 'navy':
    case 'navy_white': {
      const crown = kind === 'navy_white' ? '#f6f4ee' : kind === 'navy' ? '#1d2436' : color;
      const band = kind === 'peaked' ? (nat.mark === 'star' ? '#c8352b' : dark) : '#141414';
      return (
        <g>
          <path d={`M-80 ${top + 6} Q-84 ${top - 30} 0 ${top - 34} Q84 ${top - 30} 80 ${top + 6} Q0 ${top + 22} -80 ${top + 6} Z`} fill={crown} stroke={INK} strokeWidth={Lw} />
          <path d={`M-64 ${top + 4} L64 ${top + 4} L62 ${top + 24} Q0 ${top + 34} -62 ${top + 24} Z`} fill={band} stroke={INK} strokeWidth={Lw} />
          {back ? null : <path d={`M-58 ${top + 24} Q0 ${top + 50} 58 ${top + 24} Q0 ${top + 34} -58 ${top + 24} Z`} fill="#1b1b1b" stroke={INK} strokeWidth={3} />}
          {kind !== 'peaked' && !back ? <path d={`M-12 ${top + 2} l12 -12 l12 12 l-12 8 z`} fill="#e3b94a" stroke={INK} strokeWidth={1.5} /> : emblem(0, top + 13, 1)}
          {kind === 'peaked' && !back ? <path d={`M-22 ${top - 4} Q0 ${top - 16} 22 ${top - 4}`} stroke="#d9c27a" strokeWidth={3} fill="none" /> : null}
        </g>
      );
    }
    case 'garrison':
      return (
        <g>
          <path d={`M-58 ${top + 14} L-40 ${top - 18} L52 ${top - 12} L60 ${top + 14} Z`} fill={color} stroke={INK} strokeWidth={Lw} strokeLinejoin="round" />
          <path d={`M-58 ${top + 14} L60 ${top + 14} L58 ${top + 2} L-56 ${top + 2} Z`} fill={dark} stroke={INK} strokeWidth={3} />
          {emblem(-24, top - 2, 0.8)}
        </g>
      );
    case 'pickelhaube': {
      // 1914 German leather helmet: dome, brass spike, eagle plate, front and back peaks
      const lc = color === '#77796a' || color === '#55574a' ? '#2c2723' : color;
      return (
        <g>
          <path d={`M-78 ${top + 40} Q-60 ${top + 50} -40 ${top + 46} L-64 ${top + 34} Z`} fill={lc} stroke={INK} strokeWidth={Lw} strokeLinejoin="round" />
          <path d={`M-66 ${top + 38} L-66 ${top + 6} C-66 ${top - 48} 66 ${top - 48} 66 ${top + 6} L66 ${top + 38} Q0 ${top + 48} -66 ${top + 38} Z`} fill={lc} stroke={INK} strokeWidth={Lw} strokeLinejoin="round" />
          <path d={`M40 ${top + 44} Q72 ${top + 52} 96 ${top + 44} L88 ${top + 36} Q64 ${top + 40} 46 ${top + 36} Z`} fill={lc} stroke={INK} strokeWidth={3.5} strokeLinejoin="round" />
          <path d={`M-14 ${top - 34} L-8 ${top - 74} L0 ${top - 92} L8 ${top - 74} L14 ${top - 34} Z`} fill="#c9a24a" stroke={INK} strokeWidth={3} strokeLinejoin="round" />
          <rect x={-16} y={top - 40} width={32} height={9} rx={3} fill="#c9a24a" stroke={INK} strokeWidth={3} />
          <path d={`M-20 ${top - 6} Q0 ${top - 22} 20 ${top - 6} L14 ${top + 22} Q0 ${top + 30} -14 ${top + 22} Z`} fill="#c9a24a" stroke={INK} strokeWidth={3} />
          <path d={`M-40 ${top - 22} Q-14 ${top - 36} 14 ${top - 32}`} stroke="#fff" strokeOpacity={0.22} strokeWidth={6} fill="none" strokeLinecap="round" />
        </g>
      );
    }
    case 'helmet_de':
      return (
        <g>
          <path d={`M-74 ${top + 34} Q-86 ${top + 40} -88 ${top + 54} L-70 ${top + 48} L-70 ${top + 10} C-70 ${top - 50} 70 ${top - 50} 70 ${top + 10} L70 ${top + 48} L88 ${top + 54} Q86 ${top + 40} 74 ${top + 34} Z`} fill={color} stroke={INK} strokeWidth={Lw} strokeLinejoin="round" />
          <path d={`M-70 ${top + 22} Q0 ${top + 36} 70 ${top + 22}`} stroke={dark} strokeWidth={3} fill="none" />
          <path d={`M-40 ${top - 20} Q-10 ${top - 34} 20 ${top - 30}`} stroke="#fff" strokeOpacity={0.25} strokeWidth={6} fill="none" strokeLinecap="round" />
        </g>
      );
    case 'helmet_us':
    case 'helmet_su':
    case 'helmet_jp':
      return (
        <g>
          <path d={`M-80 ${top + 30} C-80 ${top - 52} 80 ${top - 52} 80 ${top + 30} Q0 ${top + 42} -80 ${top + 30} Z`} fill={color} stroke={INK} strokeWidth={Lw} />
          <path d={`M-84 ${top + 30} Q0 ${top + 46} 84 ${top + 30}`} stroke={INK} strokeWidth={6} fill="none" strokeLinecap="round" />
          {kind === 'helmet_su' ? <path d={`M0 ${top - 34} v20`} stroke={dark} strokeWidth={4} /> : null}
          {kind === 'helmet_us' ? <path d={`M-76 ${top + 4} Q0 ${top - 6} 76 ${top + 4}`} stroke={dark} strokeWidth={2} strokeDasharray="6 6" fill="none" /> : null}
          {kind !== 'helmet_us' ? emblem(0, top - 4, 1.1) : null}
          <path d={`M-44 ${top - 18} Q-14 ${top - 34} 18 ${top - 30}`} stroke="#fff" strokeOpacity={0.22} strokeWidth={6} fill="none" strokeLinecap="round" />
        </g>
      );
    case 'helmet_uk':
      return (
        <g>
          <path d={`M-104 ${top + 20} Q0 ${top + 46} 104 ${top + 20} Q0 ${top + 30} -104 ${top + 20} Z`} fill={color} stroke={INK} strokeWidth={Lw} />
          <path d={`M-58 ${top + 22} C-58 ${top - 40} 58 ${top - 40} 58 ${top + 22} Z`} fill={color} stroke={INK} strokeWidth={Lw} />
        </g>
      );
    case 'beret':
      return (
        <g>
          <path d={`M-74 ${top + 6} Q-90 ${top - 30} -10 ${top - 34} Q80 ${top - 36} 70 ${top + 2} Q0 ${top + 18} -74 ${top + 6} Z`} fill={color} stroke={INK} strokeWidth={Lw} />
          {emblem(34, top - 4, 0.8)}
        </g>
      );
    case 'kepi':
      return (
        <g>
          <path d={`M-50 ${top + 14} L-46 ${top - 34} Q0 ${top - 42} 46 ${top - 34} L50 ${top + 14} Z`} fill={color} stroke={INK} strokeWidth={Lw} />
          <path d={`M-50 ${top + 2} h100 v12 h-100 z`} fill={dark} stroke={INK} strokeWidth={3} />
          <path d={`M-48 ${top + 14} Q0 ${top + 40} 48 ${top + 14} Z`} fill="#1b1b1b" stroke={INK} strokeWidth={3} />
          <path d={`M-30 ${top - 20} h60`} stroke="#e3b94a" strokeWidth={3} />
        </g>
      );
    case 'bicorne':
      return (
        <g>
          <path d={`M-118 ${top + 18} Q-40 ${top - 58} 0 ${top - 50} Q40 ${top - 58} 118 ${top + 18} Q0 ${top - 6} -118 ${top + 18} Z`} fill="#1b1b1b" stroke={INK} strokeWidth={Lw} />
          <circle cx={30} cy={top - 18} r={10} fill="#0055a4" stroke="#fff" strokeWidth={3} />
        </g>
      );
    case 'ushanka':
      return (
        <g>
          <path d={`M-80 ${top + 50} L-80 ${top + 6} C-80 ${top - 46} 80 ${top - 46} 80 ${top + 6} L80 ${top + 50} L64 ${top + 50} L64 ${top + 14} L-64 ${top + 14} L-64 ${top + 50} Z`} fill="#6b5a46" stroke={INK} strokeWidth={Lw} />
          <path d={`M-72 ${top + 16} Q0 ${top - 4} 72 ${top + 16} L72 ${top - 6} Q0 ${top - 26} -72 ${top - 6} Z`} fill="#8a7860" stroke={INK} strokeWidth={3} />
          {emblem(0, top + 4, 0.9)}
        </g>
      );
    case 'fedora':
      return (
        <g>
          <path d={`M-100 ${top + 18} Q0 ${top + 38} 100 ${top + 18} Q0 ${top + 4} -100 ${top + 18} Z`} fill={color} stroke={INK} strokeWidth={Lw} />
          <path d={`M-56 ${top + 16} L-50 ${top - 30} Q0 ${top - 18} 50 ${top - 30} L56 ${top + 16} Z`} fill={color} stroke={INK} strokeWidth={Lw} />
          <path d={`M-56 ${top + 4} h112 v12 h-112 z`} fill="#1b1b1b" />
        </g>
      );
    case 'tophat':
      return (
        <g>
          <path d={`M-90 ${top + 14} Q0 ${top + 32} 90 ${top + 14} Q0 ${top} -90 ${top + 14} Z`} fill="#1b1b1b" stroke={INK} strokeWidth={Lw} />
          <rect x={-54} y={top - 76} width={108} height={92} rx={6} fill="#1b1b1b" stroke={INK} strokeWidth={Lw} />
          <rect x={-54} y={top - 4} width={108} height={12} fill="#5a1d1d" />
        </g>
      );
    case 'pith':
      return (
        <g>
          <path d={`M-102 ${top + 24} Q0 ${top + 46} 102 ${top + 24} Q0 ${top + 12} -102 ${top + 24} Z`} fill="#e6d9b0" stroke={INK} strokeWidth={Lw} />
          <path d={`M-66 ${top + 22} C-66 ${top - 54} 66 ${top - 54} 66 ${top + 22} Z`} fill="#e6d9b0" stroke={INK} strokeWidth={Lw} />
        </g>
      );
    case 'sailor':
      return (
        <g>
          <path d={`M-66 ${top + 12} Q-70 ${top - 28} 0 ${top - 30} Q70 ${top - 28} 66 ${top + 12} Q0 ${top + 22} -66 ${top + 12} Z`} fill="#f6f4ee" stroke={INK} strokeWidth={Lw} />
          <path d={`M-62 ${top + 10} Q0 ${top + 20} 62 ${top + 10}`} stroke="#2c3f6b" strokeWidth={4} fill="none" />
        </g>
      );
    case 'pilot':
      return (
        <g>
          <path d={`M-74 ${top + 60} L-74 ${top + 6} C-74 ${top - 46} 74 ${top - 46} 74 ${top + 6} L74 ${top + 60} Q60 ${top + 66} 58 ${top + 50} L58 ${top + 20} L-58 ${top + 20} L-58 ${top + 50} Q-60 ${top + 66} -74 ${top + 60} Z`} fill="#7a4a2a" stroke={INK} strokeWidth={Lw} />
          {back ? null : (
            <g>
              <path d={`M-70 ${top + 4} Q0 ${top - 14} 70 ${top + 4}`} stroke="#3a2a1a" strokeWidth={8} fill="none" />
              <circle cx={-24} cy={top - 4} r={15} fill="#a9d3ea" stroke={INK} strokeWidth={4} />
              <circle cx={24} cy={top - 4} r={15} fill="#a9d3ea" stroke={INK} strokeWidth={4} />
            </g>
          )}
          {back ? <path d={`M-70 ${top + 4} Q0 ${top - 14} 70 ${top + 4}`} stroke="#3a2a1a" strokeWidth={8} fill="none" /> : null}
        </g>
      );
    case 'roman':
      return (
        <g>
          <path d={`M-72 ${top + 40} L-72 ${top + 4} C-72 ${top - 48} 72 ${top - 48} 72 ${top + 4} L72 ${top + 40} L58 ${top + 40} L58 ${top + 14} L-58 ${top + 14} L-58 ${top + 40} Z`} fill="#c9a24a" stroke={INK} strokeWidth={Lw} />
          <path d={`M-10 ${top - 40} Q0 ${top - 90} 60 ${top - 70} Q40 ${top - 50} 10 ${top - 40} Z`} fill="#c8352b" stroke={INK} strokeWidth={3} />
        </g>
      );
    case 'crown':
      return <path d={`M-56 ${top + 8} L-60 ${top - 36} L-30 ${top - 14} L0 ${top - 44} L30 ${top - 14} L60 ${top - 36} L56 ${top + 8} Z`} fill="#e3b94a" stroke={INK} strokeWidth={Lw} strokeLinejoin="round" />;
    case 'flatcap':
    case 'newsboy':
      // puffy eight-panel newsboy cap tipped forward, button on top, short brim
      return (
        <g>
          <path d={`M-78 ${top + 22} Q-92 ${top - 34} -10 ${top - 40} Q86 ${top - 44} 84 ${top + 14} Q0 ${top + 30} -78 ${top + 22} Z`} fill={color} stroke={INK} strokeWidth={Lw} strokeLinejoin="round" />
          <path d={`M-6 ${top - 40} Q-24 ${top - 8} -40 ${top + 22} M-6 ${top - 40} Q22 ${top - 8} 30 ${top + 24} M-6 ${top - 40} Q-60 ${top - 22} -76 ${top + 6} M-6 ${top - 40} Q56 ${top - 26} 80 ${top + 2}`} stroke={shade(color, -0.3)} strokeWidth={2.5} fill="none" />
          <path d={`M-62 ${top + 20} Q0 ${top + 6} 70 ${top + 16} Q90 ${top + 26} 72 ${top + 36} Q0 ${top + 30} -60 ${top + 34} Z`} fill={shade(color, -0.25)} stroke={INK} strokeWidth={3.5} strokeLinejoin="round" />
          <ellipse cx={-6} cy={top - 40} rx={9} ry={5} fill={shade(color, -0.2)} stroke={INK} strokeWidth={2.5} />
          <path d={`M-50 ${top - 20} Q-20 ${top - 32} 20 ${top - 30}`} stroke="#fff" strokeOpacity={0.18} strokeWidth={6} fill="none" strokeLinecap="round" />
        </g>
      );
    case 'conical':
      return <path d={`M-110 ${top + 24} L0 ${top - 50} L110 ${top + 24} Q0 ${top + 34} -110 ${top + 24} Z`} fill="#d8c48a" stroke={INK} strokeWidth={Lw} strokeLinejoin="round" />;
    case 'pith_vn':
      return (
        <g>
          <path d={`M-98 ${top + 22} Q0 ${top + 42} 98 ${top + 22} Q0 ${top + 10} -98 ${top + 22} Z`} fill="#7d8a4a" stroke={INK} strokeWidth={Lw} />
          <path d={`M-64 ${top + 20} C-64 ${top - 50} 64 ${top - 50} 64 ${top + 20} Z`} fill="#7d8a4a" stroke={INK} strokeWidth={Lw} />
          {emblem(0, top - 6, 1)}
        </g>
      );
    default:
      return null;
  }
};
