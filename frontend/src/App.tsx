import { Moon, Sun } from "lucide-react";
import { useEffect, useState } from "react";
import { cn } from "./components/ui";
import { api, type Options, type Stats } from "./lib/api";
import { fmt } from "./lib/format";
import { useRoute, useTheme, type Route } from "./lib/hooks";
import { BatchPage } from "./pages/BatchPage";
import { HowItWorksPage } from "./pages/HowItWorksPage";
import { SearchPage } from "./pages/SearchPage";

const NAV: { route: Route; label: string; short: string }[] = [
  { route: "jobs", label: "Find jobs", short: "Jobs" },
  { route: "talent", label: "Find talent", short: "Talent" },
  { route: "batch", label: "Batch assign", short: "Batch" },
  { route: "how", label: "How it works", short: "How" },
];

/** Two overlapping discs, white and lime: a seeker and a job that match. */
function Mark({ className }: { className?: string }) {
  return (
    <svg viewBox="0 0 28 20" className={className} aria-hidden>
      <circle cx="10" cy="10" r="9" fill="white" />
      <circle cx="18" cy="10" r="9" fill="var(--lime)" />
    </svg>
  );
}

function Wordmark({ className }: { className?: string }) {
  return (
    <span className={cn("inline-flex items-center gap-2 font-[800] tracking-[-0.04em]", className)}>
      <Mark className="h-5 w-7" />
      <span className="hidden sm:inline">jobmatch</span>
    </span>
  );
}

export default function App() {
  const [route, navigate] = useRoute();
  const [dark, toggleTheme] = useTheme();
  const [options, setOptions] = useState<Options | null>(null);
  const [stats, setStats] = useState<Stats | null>(null);
  const [skills, setSkills] = useState<string[]>([]);
  const [bootError, setBootError] = useState(false);

  useEffect(() => {
    Promise.all([api.options(), api.stats(), api.skills()])
      .then(([o, s, sk]) => {
        setOptions(o);
        setStats(s);
        setSkills(sk);
      })
      .catch(() => setBootError(true));
  }, []);

  return (
    <div className="flex min-h-dvh flex-col">
      <header className="sticky top-0 z-30 bg-band text-on-cobalt">
        <div className="mx-auto flex h-16 max-w-6xl items-center gap-3 px-4 sm:gap-8 sm:px-6">
          <a href="#/jobs" className="text-[1.35rem] sm:text-2xl" aria-label="jobmatch home">
            <Wordmark />
          </a>

          <nav className="flex gap-0.5 overflow-x-auto rounded-full bg-black/15 p-1 sm:gap-1" aria-label="Main">
            {NAV.map((n) => {
              const active = route === n.route;
              return (
                <a
                  key={n.route}
                  href={`#/${n.route}`}
                  onClick={(e) => {
                    e.preventDefault();
                    navigate(n.route);
                  }}
                  aria-current={active ? "page" : undefined}
                  className={cn(
                    "rounded-full px-2.5 py-1.5 text-sm font-semibold whitespace-nowrap transition sm:px-4",
                    active ? "bg-white text-band shadow-sm" : "text-white/75 hover:text-white",
                  )}
                >
                  <span className="sm:hidden">{n.short}</span>
                  <span className="hidden sm:inline">{n.label}</span>
                </a>
              );
            })}
          </nav>

          <div className="ml-auto flex items-center gap-4">
            {stats && (
              <span className="hidden items-center gap-2 text-[13px] font-medium text-white/75 lg:inline-flex">
                <span className="size-2 rounded-full bg-lime" aria-hidden />
                {fmt(stats.total_jobs)} jobs · {fmt(stats.total_seekers)} people
              </span>
            )}
            <button
              type="button"
              onClick={toggleTheme}
              aria-label={dark ? "Switch to light theme" : "Switch to dark theme"}
              className="flex size-9 shrink-0 items-center justify-center rounded-full bg-white/12 text-white transition hover:bg-white/20"
            >
              {dark ? <Sun className="size-4" /> : <Moon className="size-4" />}
            </button>
          </div>
        </div>
      </header>

      {bootError && (
        <div className="bg-coral-soft px-4 py-2 text-center text-sm font-medium text-coral">
          Can't reach the API. Start the backend with <code>python webapp/app.py</code> and reload.
        </div>
      )}

      <main className="flex-1">
        {/* Both search pages stay mounted so each keeps its form and results when you switch tabs. */}
        <div hidden={route !== "jobs"}>
          <SearchPage direction="seeker_to_job" options={options} stats={stats} skills={skills} />
        </div>
        <div hidden={route !== "talent"}>
          <SearchPage direction="job_to_seeker" options={options} stats={stats} skills={skills} />
        </div>
        <div hidden={route !== "batch"}>
          <BatchPage options={options} />
        </div>
        {route === "how" && <HowItWorksPage options={options} stats={stats} />}
      </main>

      <footer className="border-t border-line bg-surface">
        <div className="mx-auto flex max-w-6xl flex-col gap-2 px-4 py-6 text-sm text-muted sm:flex-row sm:items-center sm:justify-between sm:px-6">
          <span className="font-[800] tracking-[-0.04em] text-ink">jobmatch</span>
          {stats && (
            <span className="">
              {fmt(stats.total_jobs)} postings · {fmt(stats.total_seekers)} seekers · {stats.cities} cities ·{" "}
              {stats.sectors} sectors
            </span>
          )}
        </div>
      </footer>
    </div>
  );
}
