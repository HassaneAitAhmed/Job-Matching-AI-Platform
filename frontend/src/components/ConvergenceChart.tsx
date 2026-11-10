/** GA best-so-far fitness per generation, against the optimal and greedy totals. */
export function ConvergenceChart({
  history,
  generations,
  optimal,
  greedy,
}: {
  history: number[];
  generations: number;
  optimal: number;
  greedy: number;
}) {
  const W = 640;
  const H = 240;
  const pad = { top: 16, right: 16, bottom: 32, left: 48 };
  const lo = Math.min(...history, greedy) * 0.995;
  const hi = optimal * 1.003;
  const x = (i: number) => pad.left + (i / Math.max(1, history.length - 1)) * (W - pad.left - pad.right);
  const y = (v: number) => pad.top + (1 - (v - lo) / (hi - lo || 1)) * (H - pad.top - pad.bottom);
  const path = history.map((v, i) => `${i ? "L" : "M"}${x(i).toFixed(1)},${y(v).toFixed(1)}`).join(" ");
  const ticks = [lo, (lo + hi) / 2, hi];

  return (
    <figure>
      <svg viewBox={`0 0 ${W} ${H}`} className="w-full" role="img" aria-label="Genetic algorithm convergence chart">
        {ticks.map((t) => (
          <g key={t}>
            <line x1={pad.left} x2={W - pad.right} y1={y(t)} y2={y(t)} className="stroke-line" />
            <text x={pad.left - 8} y={y(t)} textAnchor="end" dominantBaseline="middle" className="fill-faint font-mono text-[11px]">
              {t.toFixed(1)}
            </text>
          </g>
        ))}
        <text x={pad.left} y={H - 8} className="fill-faint font-mono text-[11px]">
          0
        </text>
        <text x={W - pad.right} y={H - 8} textAnchor="end" className="fill-faint font-mono text-[11px]">
          {generations} generations
        </text>

        <line x1={pad.left} x2={W - pad.right} y1={y(optimal)} y2={y(optimal)} strokeDasharray="6 4" className="stroke-ink" strokeWidth={1.5} />
        <line x1={pad.left} x2={W - pad.right} y1={y(greedy)} y2={y(greedy)} strokeDasharray="2 4" className="stroke-ochre" strokeWidth={1.5} />
        <path d={path} fill="none" className="stroke-accent" strokeWidth={2.5} strokeLinejoin="round" />
      </svg>
      <figcaption className="mt-2 flex flex-wrap gap-4 font-mono text-[11px] text-muted">
        <Legend className="bg-accent" label="GA best so far" />
        <Legend className="bg-ink" label="Optimal (Hungarian)" />
        <Legend className="bg-ochre" label="Greedy" />
      </figcaption>
    </figure>
  );
}

function Legend({ className, label }: { className: string; label: string }) {
  return (
    <span className="inline-flex items-center gap-1.5">
      <span className={`h-0.5 w-4 rounded ${className}`} />
      {label}
    </span>
  );
}
