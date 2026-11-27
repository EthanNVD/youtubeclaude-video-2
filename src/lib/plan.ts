import type { Plan } from '../types';

/**
 * A compiled plan stores each drawing once (plan.drawings, written by tools/cardlib/compile.py) and refers to it as
 * "@d<n>" wherever a list of drawing parts is expected ("parts", "holdsDrawing"). This puts the parts back, once, when the
 * plan is loaded; plans without "drawings" are returned unchanged.
 */
const KEYS = new Set(['parts', 'holdsDrawing']);

export const inflatePlan = (plan: Plan): Plan => {
  const table = (plan as unknown as { drawings?: Record<string, unknown> }).drawings;
  if (!table) return plan;
  const walk = (v: unknown): unknown => {
    if (Array.isArray(v)) return v.map(walk);
    if (v && typeof v === 'object') {
      const o: Record<string, unknown> = {};
      for (const [k, x] of Object.entries(v as Record<string, unknown>)) {
        o[k] = KEYS.has(k) && typeof x === 'string' && x.startsWith('@') ? table[x.slice(1)] ?? [] : walk(x);
      }
      return o;
    }
    return v;
  };
  const { drawings: _omit, ...rest } = plan as unknown as Record<string, unknown>;
  return walk(rest) as Plan;
};
