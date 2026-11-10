import { ArrowUpRight, Info } from "lucide-react";
import { CRITERION_ICONS } from "../components/Score";
import { Card, Page } from "../components/ui";
import type { Options, Stats } from "../lib/api";
import { CRITERIA, CRITERIA_ORDER, fmt } from "../lib/format";

const REPO = "https://github.com/HassaneAitAhmed/Job-Matching-AI-Platform/blob/main";

const ALGOS: { mark: string; name: string; fact: string; body: string }[] = [
  {
    mark: "A*",
    name: "A* search",
    fact: "Exactly optimal",
    body:
      "Searches a tree that groups items by sector, contract, education and city. Each node carries bounds that never over-estimate the cost of the items below it, so A* returns the true top results while scoring only a few dozen items.",
  },
  {
    mark: "G",
    name: "Greedy best-first",
    fact: "Fast, approximate",
    body:
      "Uses the same tree, but follows the heuristic alone and ignores the cost so far. It does little work, but its top 10 reaches only about 73–79% of the optimal score.",
  },
  {
    mark: "C",
    name: "Constraint satisfaction",
    fact: "Strict filters",
    body:
      "Turns sector, contract, education, distance, salary and experience into hard rules. It prunes with node consistency and forward checking, then ranks what's left. If too little survives, it relaxes rules one by one and tells you which ones.",
  },
  {
    mark: "GA",
    name: "Genetic algorithm",
    fact: "Batch assignment",
    body:
      "Assigns many seekers to openings at once. That problem has an exact solution (the Hungarian algorithm), so the GA is reported as a percentage of the true optimum: about 92–100% here.",
  },
];

export function HowItWorksPage({ options, stats }: { options: Options | null; stats: Stats | null }) {
  const seekerW = options?.weights.seeker_to_job;
  const employerW = options?.weights.job_to_seeker;

  return (
    <Page
      eyebrow="How it works"
      title={
        <>
          Every score, <mark>explained.</mark>
        </>
      }
      lead="Each match gets a score from 0 to 100, built from seven criteria. The weights depend on who's searching, and every result shows its own breakdown."
    >
      <Card className="overflow-hidden">
        <div className="grid grid-cols-[minmax(0,1fr)_5.5rem_5.5rem] gap-4 border-b border-line bg-sunken/60 px-5 py-3 text-xs font-semibold text-muted sm:grid-cols-[minmax(0,1fr)_10rem_10rem]">
          <span>Criterion</span>
          <span>Seeker weight</span>
          <span>Employer weight</span>
        </div>
        <ul className="divide-y divide-line">
          {CRITERIA_ORDER.map((c) => {
            const Icon = CRITERION_ICONS[c];
            return (
              <li
                key={c}
                className="grid grid-cols-[minmax(0,1fr)_5.5rem_5.5rem] items-center gap-4 px-5 py-4 sm:grid-cols-[minmax(0,1fr)_10rem_10rem]"
              >
                <div className="flex min-w-0 items-start gap-3">
                  <span className="flex size-9 shrink-0 items-center justify-center rounded-xl bg-cobalt-soft text-link">
                    <Icon className="size-4" aria-hidden />
                  </span>
                  <div className="min-w-0">
                    <p className="font-bold">{CRITERIA[c].label}</p>
                    <p className="text-sm text-muted">{CRITERIA[c].description}</p>
                  </div>
                </div>
                <WeightBar value={seekerW?.[c]} />
                <WeightBar value={employerW?.[c]} />
              </li>
            );
          })}
        </ul>
      </Card>

      <h2 className="mt-16 text-3xl font-[800] tracking-[-0.03em]">Four algorithms</h2>
      <div className="mt-5 grid gap-4 md:grid-cols-2">
        {ALGOS.map(({ mark, name, fact, body }) => (
          <Card key={name} className="p-6">
            <div className="flex items-center gap-3">
              <span className="flex size-11 shrink-0 items-center justify-center rounded-xl bg-band text-base font-[800] text-lime">
                {mark}
              </span>
              <div>
                <h3 className="font-bold">{name}</h3>
                <p className="text-xs font-semibold text-link">{fact}</p>
              </div>
            </div>
            <p className="mt-4 text-sm leading-relaxed text-muted">{body}</p>
          </Card>
        ))}
      </div>

      <div className="mt-16 flex gap-4 rounded-2xl border border-amber/30 bg-amber-soft p-5">
        <Info className="mt-0.5 size-5 shrink-0 text-amber" aria-hidden />
        <div className="text-sm">
          <p className="font-bold text-amber">About the data</p>
          <p className="mt-1 leading-relaxed">
            The bundled datasets ({stats ? fmt(stats.total_jobs) : "754"} postings, {stats ? fmt(stats.total_seekers) : "8,124"}{" "}
            seekers) appear to be synthetic, and {stats ? fmt(stats.jobs_without_skills) : "435"} postings list no skills.
            The scores demonstrate how the algorithms behave; they aren't evidence of real hiring quality.
          </p>
          <div className="mt-3 flex flex-wrap gap-5 font-semibold">
            <a className="inline-flex items-center gap-1 hover:underline" href={`${REPO}/docs/BENCHMARKS.md`} target="_blank" rel="noreferrer">
              Benchmarks <ArrowUpRight className="size-4" aria-hidden />
            </a>
            <a className="inline-flex items-center gap-1 hover:underline" href={`${REPO}/docs/DATA.md`} target="_blank" rel="noreferrer">
              Data quality report <ArrowUpRight className="size-4" aria-hidden />
            </a>
          </div>
        </div>
      </div>
    </Page>
  );
}

function WeightBar({ value }: { value?: number }) {
  return (
    <div className="flex items-center gap-2.5">
      <span className="h-2 flex-1 overflow-hidden rounded-full bg-sunken">
        <span className="block h-full rounded-full bg-cobalt" style={{ width: `${((value ?? 0) / 25) * 100}%` }} />
      </span>
      <span className="w-10 text-right text-sm font-bold">{value !== undefined ? `${value}%` : "–"}</span>
    </div>
  );
}
