import { Check, Minus, Play } from "lucide-react";
import { useState, type FormEvent } from "react";
import { ConvergenceChart } from "../components/ConvergenceChart";
import { Button, Card, ErrorBanner, Field, Input, Page, Select, cn } from "../components/ui";
import { api, ApiError, type AssignResponse, type Options } from "../lib/api";
import { ms } from "../lib/format";

const METHOD_LABELS: Record<string, { name: string; note: string }> = {
  "optimal (Hungarian)": { name: "Optimal", note: "Hungarian algorithm, exact" },
  greedy: { name: "Greedy", note: "Best remaining pair first" },
  "genetic algorithm": { name: "Genetic algorithm", note: "Population 60, tournament selection" },
};

export function BatchPage({ options }: { options: Options | null }) {
  const [form, setForm] = useState({ seekers: "40", jobs: "15", sector: "", seed: "0", generations: "200" });
  const [result, setResult] = useState<AssignResponse | null>(null);
  const [ranGenerations, setRanGenerations] = useState(200);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const set = (k: keyof typeof form, v: string) => setForm((f) => ({ ...f, [k]: v }));

  async function submit(e: FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const generations = Number(form.generations) || 200;
      const res = await api.assign({
        n_seekers: Number(form.seekers) || 40,
        n_jobs: Number(form.jobs) || 15,
        sector: form.sector || null,
        seed: Number(form.seed) || 0,
        generations,
      });
      setResult(res);
      setRanGenerations(generations);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Something went wrong.");
    } finally {
      setLoading(false);
    }
  }

  const byMethod = Object.fromEntries((result?.results ?? []).map((r) => [r.method, r]));

  return (
    <Page
      eyebrow="Batch assignment"
      title={
        <>
          Fill every opening <mark>at once.</mark>
        </>
      }
      lead="Assign a batch of seekers to job posts, respecting how many openings each posting has. The exact optimum is computable, so the genetic algorithm is measured against it."
    >
      <Card>
        <form onSubmit={submit} className="grid items-end gap-4 p-5 sm:grid-cols-2 lg:grid-cols-6">
          <Field label="Seekers" htmlFor="b-seekers">
            <Input id="b-seekers" type="number" min={2} max={200} value={form.seekers} onChange={(e) => set("seekers", e.target.value)} />
          </Field>
          <Field label="Job postings" htmlFor="b-jobs">
            <Input id="b-jobs" type="number" min={1} max={100} value={form.jobs} onChange={(e) => set("jobs", e.target.value)} />
          </Field>
          <Field label="Sector" htmlFor="b-sector" className="lg:col-span-2">
            <Select id="b-sector" value={form.sector} onChange={(e) => set("sector", e.target.value)}>
              <option value="">All sectors</option>
              {options?.sectors.map((s) => (
                <option key={s}>{s}</option>
              ))}
            </Select>
          </Field>
          <Field label="Generations" htmlFor="b-gen">
            <Input id="b-gen" type="number" min={1} max={1000} value={form.generations} onChange={(e) => set("generations", e.target.value)} />
          </Field>
          <Field label="Random seed" htmlFor="b-seed">
            <Input id="b-seed" type="number" min={0} value={form.seed} onChange={(e) => set("seed", e.target.value)} />
          </Field>
          <div className="flex flex-wrap items-center justify-between gap-4 border-t border-line pt-4 sm:col-span-2 lg:col-span-6">
            <p className="text-xs text-faint">
              Pair score = average of the seeker's and the employer's view. The GA takes a few seconds.
            </p>
            <Button type="submit" loading={loading}>
              {!loading && <Play className="size-4" aria-hidden />}
              Run assignment
            </Button>
          </div>
        </form>
      </Card>

      {error && (
        <div className="mt-6">
          <ErrorBanner message={error} />
        </div>
      )}

      {!result && !loading && !error && (
        <Card className="mt-6 px-6 py-12 sm:px-10">
          <p className="max-w-lg text-2xl leading-snug font-[800] tracking-[-0.02em]">
            Compare the optimal, greedy and genetic-algorithm assignments, and watch the GA converge.
          </p>
          <p className="mt-2 text-sm text-muted">Pick a batch size above and run it.</p>
        </Card>
      )}

      {result && (
        <div className={cn("mt-8 space-y-6 transition", loading && "opacity-50")}>
          <p className="text-sm font-medium text-muted">
            {result.n_seekers} seekers · {result.n_jobs} postings · {result.total_posts} openings
          </p>

          <div className="grid gap-4 md:grid-cols-3">
            {result.results.map((r) => {
              const meta = METHOD_LABELS[r.method] ?? { name: r.method, note: "" };
              const optimal = r.method.startsWith("optimal");
              return (
                <div
                  key={r.method}
                  className={cn(
                    "animate-fade-up rounded-2xl border p-5",
                    optimal ? "border-transparent bg-band text-on-cobalt" : "border-line bg-surface",
                  )}
                >
                  <div className="flex items-center justify-between">
                    <h3 className="text-sm font-bold">{meta.name}</h3>
                    {optimal && (
                      <span className="rounded-md bg-lime px-1.5 py-0.5 text-[11px] font-bold text-lime-ink">Exact</span>
                    )}
                  </div>
                  <p className="mt-3 text-5xl leading-none font-[800] tracking-[-0.04em]">
                    {r.pct_of_optimal.toFixed(1)}
                    <span className={cn("ml-0.5 text-2xl", optimal ? "text-white/60" : "text-faint")}>%</span>
                  </p>
                  <p className={cn("mt-1.5 text-xs", optimal ? "text-white/70" : "text-muted")}>
                    of the optimal total score
                  </p>
                  <dl
                    className={cn(
                      "mt-5 grid grid-cols-2 gap-y-1.5 border-t pt-3 text-[13px]",
                      optimal ? "border-white/20" : "border-line",
                    )}
                  >
                    <dt className={optimal ? "text-white/70" : "text-muted"}>Time</dt>
                    <dd className="text-right font-semibold">{ms(r.elapsed_ms)}</dd>
                    <dt className={optimal ? "text-white/70" : "text-muted"}>Assigned</dt>
                    <dd className="text-right font-semibold">{r.assigned}</dd>
                    <dt className={optimal ? "text-white/70" : "text-muted"}>Total score</dt>
                    <dd className="text-right font-semibold">{r.total_score.toFixed(2)}</dd>
                  </dl>
                  <p className={cn("mt-3 text-xs", optimal ? "text-white/60" : "text-faint")}>{meta.note}</p>
                </div>
              );
            })}
          </div>

          <div className="grid gap-6 lg:grid-cols-5">
            <Card className="p-5 lg:col-span-3">
              <h3 className="text-lg font-[800] tracking-[-0.02em]">GA convergence</h3>
              <p className="mb-4 text-xs text-muted">Best total score found so far, per generation.</p>
              <ConvergenceChart
                history={result.ga_history}
                generations={ranGenerations}
                optimal={byMethod["optimal (Hungarian)"]?.total_score ?? 0}
                greedy={byMethod["greedy"]?.total_score ?? 0}
              />
            </Card>

            <Card className="overflow-hidden lg:col-span-2">
              <div className="p-5 pb-3">
                <h3 className="text-lg font-[800] tracking-[-0.02em]">Optimal pairs</h3>
                <p className="text-xs text-muted">Best-scoring pairs in the optimal assignment.</p>
              </div>
              <div className="max-h-80 overflow-auto">
                <table className="w-full text-sm">
                  <thead className="sticky top-0 bg-surface text-left text-xs text-muted">
                    <tr>
                      <th className="px-5 py-2 font-semibold">Seeker</th>
                      <th className="py-2 font-semibold">Job</th>
                      <th className="py-2 text-right font-semibold">Score</th>
                      <th className="px-5 py-2 text-right font-semibold">GA</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-line">
                    {result.optimal_pairs.map((p) => (
                      <tr key={`${p.seeker_id}-${p.job_id}`}>
                        <td className="px-5 py-2 text-muted">#{p.seeker_id}</td>
                        <td className="max-w-40 truncate py-2" title={p.job_title}>
                          {p.job_title}
                        </td>
                        <td className="py-2 text-right font-semibold">{p.score.toFixed(1)}</td>
                        <td className="px-5 py-2 text-right">
                          {p.ga_agrees ? (
                            <span className="ml-auto flex size-5 items-center justify-center rounded-full bg-lime text-lime-ink"><Check className="size-3" strokeWidth={3.5} aria-label="GA picked the same pair" /></span>
                          ) : (
                            <Minus className="ml-auto size-4 text-faint" aria-label="GA picked a different pair" />
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </Card>
          </div>
        </div>
      )}
    </Page>
  );
}
