import { ArrowRight, RotateCcw, Search, TriangleAlert } from "lucide-react";
import { useRef, useState, type FormEvent } from "react";
import { AlgorithmPicker } from "../components/AlgorithmPicker";
import { ResultCard, ResultSkeleton } from "../components/ResultCard";
import { SkillInput } from "../components/SkillInput";
import { Button, Card, ErrorBanner, Field, Input, SectionTitle, Select } from "../components/ui";
import { api, ApiError, type Algorithm, type Direction, type Match, type Options, type SearchStats, type Stats } from "../lib/api";
import { ALGORITHMS, fmt, ms, RELAXED_LABELS } from "../lib/format";

const PAGE = 10;

interface Form {
  skills: string[];
  experience: string;
  experienceMin: string;
  experienceMax: string;
  education: string;
  city: string;
  sector: string;
  contract: string;
  salary: string;
  algorithm: Algorithm;
  maxKm: string;
}

const EMPTY: Form = {
  skills: [],
  experience: "",
  experienceMin: "",
  experienceMax: "",
  education: "",
  city: "",
  sector: "",
  contract: "",
  salary: "",
  algorithm: "astar",
  maxKm: "300",
};

const EXAMPLES: Record<Direction, Partial<Form>> = {
  seeker_to_job: {
    skills: ["Inventory Management", "Retail Buying", "SQL"],
    experience: "4",
    education: "17",
    city: "Oran",
    sector: "Retail",
    salary: "70000",
  },
  job_to_seeker: {
    skills: ["Risk Management", "Financial Modeling"],
    experienceMin: "3",
    experienceMax: "8",
    education: "17",
    city: "Algiers",
    sector: "Banking & Finance",
    salary: "90000",
  },
};

const num = (s: string) => (s.trim() === "" ? null : Number(s));

function payload(direction: Direction, f: Form) {
  const common = {
    skills: f.skills,
    education: num(f.education),
    city: f.city || null,
    sector: f.sector || null,
    contract_type: f.contract || null,
    salary: num(f.salary),
    algorithm: f.algorithm,
    max_distance_km: f.algorithm === "csp" ? num(f.maxKm) : null,
  };
  return direction === "seeker_to_job"
    ? { ...common, experience: num(f.experience) }
    : { ...common, experience_min: num(f.experienceMin), experience_max: num(f.experienceMax) };
}

interface Results {
  matches: Match[];
  stats: SearchStats;
  hasMore: boolean;
  body: Record<string, unknown>;
}

export function SearchPage({
  direction,
  options,
  stats,
  skills,
}: {
  direction: Direction;
  options: Options | null;
  stats: Stats | null;
  skills: string[];
}) {
  const seeker = direction === "seeker_to_job";
  const [form, setForm] = useState<Form>(EMPTY);
  const [results, setResults] = useState<Results | null>(null);
  const [loading, setLoading] = useState(false);
  const [loadingMore, setLoadingMore] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const resultsRef = useRef<HTMLElement>(null);

  const set = <K extends keyof Form>(key: K, value: Form[K]) => setForm((f) => ({ ...f, [key]: value }));

  async function run(body: Record<string, unknown>, append: boolean) {
    setError(null);
    if (append) setLoadingMore(true);
    else setLoading(true);
    try {
      const offset = append && results ? results.matches.length : 0;
      const res = await api.search(direction, { ...body, limit: PAGE, offset });
      setResults({
        matches: append && results ? [...results.matches, ...res.matches] : res.matches,
        stats: append && results ? results.stats : res.stats,
        hasMore: res.has_more,
        body,
      });
      // On small screens the results sit below the form; bring them into view.
      if (!append && window.matchMedia("(max-width: 1023px)").matches) {
        requestAnimationFrame(() => resultsRef.current?.scrollIntoView({ behavior: "smooth", block: "start" }));
      }
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Something went wrong.");
      if (!append) setResults(null);
    } finally {
      setLoading(false);
      setLoadingMore(false);
    }
  }

  const submit = (e?: FormEvent) => {
    e?.preventDefault();
    run(payload(direction, form), false);
  };

  const tryExample = () => {
    const next = { ...EMPTY, ...EXAMPLES[direction], algorithm: form.algorithm };
    setForm(next);
    run(payload(direction, next), false);
  };

  const total = stats ? (seeker ? stats.total_jobs : stats.total_seekers) : null;

  return (
    <div className="mx-auto max-w-6xl px-4 py-12 sm:px-6 lg:py-16">
      <SectionTitle
        index={seeker ? "01" : "02"}
        eyebrow={seeker ? "For job seekers" : "For employers"}
        title={
          seeker ? (
            <>
              Find work that <em>fits</em> you.
            </>
          ) : (
            <>
              Find people who <em>fit</em> the role.
            </>
          )
        }
      >
        {seeker
          ? "Describe your skills and expectations. We rank every posting on seven criteria and show you exactly why each one matches."
          : "Describe the role. We rank every candidate on seven criteria, weighted from the employer's point of view."}
      </SectionTitle>

      <div className="mt-12 grid items-start gap-8 lg:grid-cols-[minmax(0,22rem)_minmax(0,1fr)]">
        <Card className="lg:sticky lg:top-24">
          <form onSubmit={submit} className="space-y-4 p-5">
            <Field
              label={seeker ? "Your skills" : "Required skills"}
              htmlFor={`${direction}-skills`}
              hint="Press Enter or comma to add. Similar skills also count."
            >
              <SkillInput
                id={`${direction}-skills`}
                value={form.skills}
                onChange={(v) => set("skills", v)}
                suggestions={skills}
                placeholder={seeker ? "e.g. Inventory Management" : "e.g. Risk Management"}
              />
            </Field>

            {seeker ? (
              <Field label="Years of experience" htmlFor="exp">
                <Input
                  id="exp"
                  type="number"
                  min={0}
                  max={60}
                  inputMode="numeric"
                  value={form.experience}
                  onChange={(e) => set("experience", e.target.value)}
                  placeholder="4"
                  suffix="yrs"
                />
              </Field>
            ) : (
              <div className="grid grid-cols-2 gap-3">
                <Field label="Min experience" htmlFor="exp-min">
                  <Input
                    id="exp-min"
                    type="number"
                    min={0}
                    max={60}
                    value={form.experienceMin}
                    onChange={(e) => set("experienceMin", e.target.value)}
                    placeholder="2"
                    suffix="yrs"
                  />
                </Field>
                <Field label="Max experience" htmlFor="exp-max">
                  <Input
                    id="exp-max"
                    type="number"
                    min={0}
                    max={60}
                    value={form.experienceMax}
                    onChange={(e) => set("experienceMax", e.target.value)}
                    placeholder="6"
                    suffix="yrs"
                  />
                </Field>
              </div>
            )}

            <div className="grid grid-cols-2 gap-3">
              <Field label={seeker ? "Education" : "Required education"} htmlFor={`${direction}-edu`}>
                <Select id={`${direction}-edu`} value={form.education} onChange={(e) => set("education", e.target.value)}>
                  <option value="">Any</option>
                  {options?.education_levels.map((o) => (
                    <option key={o.value} value={o.value}>
                      {o.label}
                    </option>
                  ))}
                </Select>
              </Field>
              <Field label={seeker ? "City" : "Job location"} htmlFor={`${direction}-city`}>
                <Select id={`${direction}-city`} value={form.city} onChange={(e) => set("city", e.target.value)}>
                  <option value="">Anywhere</option>
                  {options?.cities.map((c) => (
                    <option key={c}>{c}</option>
                  ))}
                </Select>
              </Field>
            </div>

            <Field label="Sector" htmlFor={`${direction}-sector`}>
              <Select id={`${direction}-sector`} value={form.sector} onChange={(e) => set("sector", e.target.value)}>
                <option value="">Any sector</option>
                {options?.sectors.map((s) => (
                  <option key={s}>{s}</option>
                ))}
              </Select>
            </Field>

            <div className="grid grid-cols-2 gap-3">
              <Field label="Contract" htmlFor={`${direction}-contract`}>
                <Select id={`${direction}-contract`} value={form.contract} onChange={(e) => set("contract", e.target.value)}>
                  <option value="">Any type</option>
                  {options?.contract_types.map((c) => (
                    <option key={c.value} value={c.value}>
                      {c.label}
                    </option>
                  ))}
                </Select>
              </Field>
              <Field label={seeker ? "Expected salary" : "Offered salary"} htmlFor={`${direction}-salary`}>
                <Input
                  id={`${direction}-salary`}
                  type="number"
                  min={0}
                  step={1000}
                  value={form.salary}
                  onChange={(e) => set("salary", e.target.value)}
                  placeholder={seeker ? "70000" : "90000"}
                  suffix="DZD"
                />
              </Field>
            </div>

            <Field label="Algorithm" hint={ALGORITHMS[form.algorithm].description}>
              <AlgorithmPicker value={form.algorithm} onChange={(a) => set("algorithm", a)} />
            </Field>

            {form.algorithm === "csp" && (
              <Field label="Maximum distance" htmlFor={`${direction}-km`} hint="Relaxed automatically if too few results fit.">
                <Input
                  id={`${direction}-km`}
                  type="number"
                  min={0}
                  max={5000}
                  value={form.maxKm}
                  onChange={(e) => set("maxKm", e.target.value)}
                  suffix="km"
                />
              </Field>
            )}

            <div className="flex gap-2 pt-1">
              <Button type="submit" loading={loading} className="flex-1">
                {!loading && <Search className="size-4" aria-hidden />}
                {seeker ? "Find jobs" : "Find candidates"}
              </Button>
              <Button
                type="button"
                variant="secondary"
                onClick={() => {
                  setForm(EMPTY);
                  setResults(null);
                  setError(null);
                }}
                aria-label="Reset form"
                title="Reset"
              >
                <RotateCcw className="size-4" aria-hidden />
              </Button>
            </div>
          </form>
        </Card>

        <section ref={resultsRef} aria-live="polite" className="min-w-0 scroll-mt-20 space-y-4">
          {error && <ErrorBanner message={error} />}

          {loading && (
            <>
              <ResultSkeleton />
              <ResultSkeleton />
              <ResultSkeleton />
            </>
          )}

          {!loading && !results && !error && (
            <div className="rounded-lg border border-dashed border-line px-6 py-16 sm:px-10">
              <p className="font-mono text-[11px] tracking-[0.08em] text-faint uppercase">No search yet</p>
              <h2 className="mt-3 max-w-md font-display text-3xl leading-tight font-[420] tracking-[-0.01em]">
                {seeker ? (
                  <>
                    Your best matches will be <em className="text-accent">ranked</em> here.
                  </>
                ) : (
                  <>
                    Your best candidates will be <em className="text-accent">ranked</em> here.
                  </>
                )}
              </h2>
              <p className="mt-3 max-w-md text-sm leading-relaxed text-muted">
                Every field is optional; a blank field means no preference. Each result explains its score, criterion
                by criterion.
              </p>
              <Button variant="secondary" className="mt-6" onClick={tryExample}>
                Try an example
                <ArrowRight className="size-4" aria-hidden />
              </Button>
            </div>
          )}

          {!loading && results && (
            <>
              <div className="flex flex-wrap items-end justify-between gap-x-6 gap-y-2 border-b border-line pb-3">
                <h2 className="font-display text-2xl font-[450] tracking-[-0.01em]">
                  {results.matches.length ? (
                    <>
                      Top <em className="text-accent">{results.matches.length}</em> matches
                    </>
                  ) : (
                    "No matches"
                  )}
                </h2>
                <p className="font-mono text-[11px] text-muted tabular-nums">
                  <span className="text-ink">{ALGORITHMS[results.stats.algorithm].name}</span>
                  <Dot />
                  {ms(results.stats.elapsed_ms)}
                  <Dot />
                  {fmt(results.stats.items_scored)}
                  {total ? `/${fmt(total)}` : ""} scored
                  {results.stats.nodes_expanded > 0 && (
                    <>
                      <Dot />
                      {fmt(results.stats.nodes_expanded)} nodes
                    </>
                  )}
                  {results.stats.solutions !== undefined && (
                    <>
                      <Dot />
                      {fmt(results.stats.solutions)} fit all rules
                    </>
                  )}
                </p>
              </div>

              {results.stats.relaxed_constraints && results.stats.relaxed_constraints.length > 0 && (
                <div className="flex items-start gap-2 rounded-md bg-ochre-soft px-4 py-3 text-sm text-ochre">
                  <TriangleAlert className="mt-0.5 size-4 shrink-0" aria-hidden />
                  <span>
                    Too few results met every constraint, so these were relaxed:{" "}
                    <strong>{results.stats.relaxed_constraints.map((c) => RELAXED_LABELS[c] ?? c).join(", ")}</strong>.
                  </span>
                </div>
              )}

              {results.matches.map((m, i) => (
                <ResultCard key={`${m.type}-${m.id}`} match={m} rank={i + 1} />
              ))}

              {results.hasMore && (
                <div className="flex justify-center pt-2">
                  <Button variant="secondary" loading={loadingMore} onClick={() => run(results.body, true)}>
                    Load more
                  </Button>
                </div>
              )}
            </>
          )}
        </section>
      </div>
    </div>
  );
}

function Dot() {
  return <span className="mx-2 text-faint">·</span>;
}
