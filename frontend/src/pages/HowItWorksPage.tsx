import { ArrowUpRight } from "lucide-react";
import { CRITERION_ICONS } from "../components/Score";
import { SectionTitle } from "../components/ui";
import type { Options, Stats } from "../lib/api";
import { CRITERIA, CRITERIA_ORDER, fmt } from "../lib/format";

const REPO = "https://github.com/HassaneAitAhmed/Job-Matching-AI-Platform/blob/main";

const ALGOS: { mark: string; name: string; fact: string; body: string }[] = [
  {
    mark: "A*",
    name: "A* search",
    fact: "exactly optimal",
    body:
      "Searches a tree that groups items by sector, contract, education and city. Each node carries bounds that never over-estimate the cost of the items below it, so A* returns the true top results while scoring only a few dozen items.",
  },
  {
    mark: "G",
    name: "Greedy best-first",
    fact: "fast, approximate",
    body:
      "Uses the same tree, but follows the heuristic alone and ignores the cost so far. It does little work, but its top 10 reaches only about 73–79% of the optimal score.",
  },
  {
    mark: "C",
    name: "Constraint satisfaction",
    fact: "strict filters",
    body:
      "Turns sector, contract, education, distance, salary and experience into hard rules. It prunes with node consistency and forward checking, then ranks what's left. If too little survives, it relaxes rules one by one and tells you which ones.",
  },
  {
    mark: "GA",
    name: "Genetic algorithm",
    fact: "batch assignment",
    body:
      "Assigns many seekers to openings at once. That problem has an exact solution (the Hungarian algorithm), so the GA is reported as a percentage of the true optimum: about 92–100% here.",
  },
];

export function HowItWorksPage({ options, stats }: { options: Options | null; stats: Stats | null }) {
  const seekerW = options?.weights.seeker_to_job;
  const employerW = options?.weights.job_to_seeker;

  return (
    <div className="mx-auto max-w-6xl px-4 py-12 sm:px-6 lg:py-16">
      <SectionTitle
        index="04"
        eyebrow="Method"
        title={
          <>
            How the <em>matching</em> works.
          </>
        }
      >
        Every match gets a score from 0 to 100, built from seven criteria. The weights depend on who's searching, and
        every result shows its own breakdown.
      </SectionTitle>

      <section className="mt-14">
        <div className="grid grid-cols-[minmax(0,1fr)_5.5rem_5.5rem] gap-4 border-b border-ink pb-2 font-mono text-[10.5px] tracking-[0.08em] text-muted uppercase sm:grid-cols-[minmax(0,1fr)_10rem_10rem]">
          <span>Criterion</span>
          <span>Seeker view</span>
          <span>Employer view</span>
        </div>
        <ul className="divide-y divide-line">
          {CRITERIA_ORDER.map((c) => {
            const Icon = CRITERION_ICONS[c];
            return (
              <li
                key={c}
                className="grid grid-cols-[minmax(0,1fr)_5.5rem_5.5rem] items-center gap-4 py-4 sm:grid-cols-[minmax(0,1fr)_10rem_10rem]"
              >
                <div className="flex min-w-0 items-start gap-3">
                  <Icon className="mt-1 size-4 shrink-0 text-faint" aria-hidden />
                  <div className="min-w-0">
                    <p className="font-display text-lg leading-snug font-[480]">{CRITERIA[c].label}</p>
                    <p className="text-sm text-muted">{CRITERIA[c].description}</p>
                  </div>
                </div>
                <WeightBar value={seekerW?.[c]} />
                <WeightBar value={employerW?.[c]} />
              </li>
            );
          })}
        </ul>
      </section>

      <h2 className="mt-20 font-display text-3xl font-[420] tracking-[-0.01em]">
        Four <em className="text-accent">algorithms</em>.
      </h2>
      <div className="mt-6 grid gap-px overflow-hidden rounded-lg border border-line bg-line md:grid-cols-2">
        {ALGOS.map(({ mark, name, fact, body }) => (
          <div key={name} className="bg-surface p-6">
            <div className="flex items-baseline gap-3">
              <span className="font-display text-3xl leading-none font-[450] text-accent italic">{mark}</span>
              <h3 className="font-medium">{name}</h3>
              <span className="ml-auto font-mono text-[10.5px] tracking-[0.06em] text-muted uppercase">{fact}</span>
            </div>
            <p className="mt-3 text-sm leading-relaxed text-muted">{body}</p>
          </div>
        ))}
      </div>

      <aside className="mt-20 border-l-2 border-ochre pl-5">
        <p className="font-mono text-[11px] tracking-[0.08em] text-ochre uppercase">About the data</p>
        <p className="mt-2 max-w-3xl text-[15px] leading-relaxed">
          The bundled datasets ({stats ? fmt(stats.total_jobs) : "754"} postings, {stats ? fmt(stats.total_seekers) : "8,124"}{" "}
          seekers) appear to be synthetic, and {stats ? fmt(stats.jobs_without_skills) : "435"} postings list no skills.
          The scores demonstrate how the algorithms behave; they aren't evidence of real hiring quality.
        </p>
        <div className="mt-3 flex flex-wrap gap-5 text-sm font-medium">
          <a className="inline-flex items-center gap-1 underline decoration-line underline-offset-4 hover:decoration-ink" href={`${REPO}/docs/BENCHMARKS.md`} target="_blank" rel="noreferrer">
            Benchmarks <ArrowUpRight className="size-3.5" aria-hidden />
          </a>
          <a className="inline-flex items-center gap-1 underline decoration-line underline-offset-4 hover:decoration-ink" href={`${REPO}/docs/DATA.md`} target="_blank" rel="noreferrer">
            Data quality report <ArrowUpRight className="size-3.5" aria-hidden />
          </a>
        </div>
      </aside>
    </div>
  );
}

function WeightBar({ value }: { value?: number }) {
  return (
    <div className="flex items-center gap-3">
      <span className="h-[3px] flex-1 bg-sunken">
        <span className="block h-full bg-accent" style={{ width: `${((value ?? 0) / 25) * 100}%` }} />
      </span>
      <span className="w-9 text-right font-mono text-xs tabular-nums">{value !== undefined ? `${value}` : "–"}</span>
    </div>
  );
}
