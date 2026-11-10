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
  { route: "how", label: "Method", short: "How" },
];

function Wordmark({ className }: { className?: string }) {
  return (
    <span className={cn("font-display font-[520] tracking-[-0.03em] italic", className)}>
      jobmatch<span className="text-signal not-italic">.</span>
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
      <header className="sticky top-0 z-30 border-b border-line bg-paper/90 backdrop-blur-md">
        <div className="mx-auto flex h-14 max-w-6xl items-stretch gap-5 px-4 sm:gap-10 sm:px-6">
          <a href="#/jobs" className="flex items-center text-[1.3rem] leading-none sm:text-[1.45rem]" aria-label="jobmatch home">
            <Wordmark />
          </a>

          <nav className="-mb-px flex items-stretch gap-3.5 overflow-x-auto sm:gap-7" aria-label="Main">
            {NAV.map((n, i) => {
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
                    "group relative flex items-center gap-1.5 border-b-2 text-sm whitespace-nowrap transition",
                    active ? "border-accent text-ink" : "border-transparent text-muted hover:text-ink",
                  )}
                >
                  <span
                    className={cn(
                      "hidden font-mono text-[10.5px] sm:inline",
                      active ? "text-accent" : "text-faint group-hover:text-muted",
                    )}
                  >
                    0{i + 1}
                  </span>
                  <span className="sm:hidden">{n.short}</span>
                  <span className="hidden sm:inline">{n.label}</span>
                </a>
              );
            })}
          </nav>

          <div className="ml-auto flex items-center gap-4">
            {stats && (
              <span className="hidden font-mono text-[11px] text-muted lg:inline">
                {fmt(stats.total_jobs)} jobs <span className="text-faint">·</span> {fmt(stats.total_seekers)} people
              </span>
            )}
            <button
              type="button"
              onClick={toggleTheme}
              aria-label={dark ? "Switch to light theme" : "Switch to dark theme"}
              className="flex size-8 items-center justify-center rounded-full border border-line text-muted transition hover:border-ink hover:text-ink"
            >
              {dark ? <Sun className="size-3.5" /> : <Moon className="size-3.5" />}
            </button>
          </div>
        </div>
      </header>

      {bootError && (
        <div className="border-b border-signal/30 bg-signal-soft px-4 py-2 text-center text-sm text-signal">
          Can't reach the API. Start the backend with <code className="font-mono">python webapp/app.py</code> and reload.
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

      <footer className="border-t border-line">
        <div className="mx-auto flex max-w-6xl flex-col gap-2 px-4 py-6 sm:flex-row sm:items-center sm:justify-between sm:px-6">
          <Wordmark className="text-lg" />
          {stats && (
            <span className="font-mono text-[11px] text-muted tabular-nums">
              {fmt(stats.total_jobs)} postings · {fmt(stats.total_seekers)} seekers · {stats.cities} cities ·{" "}
              {stats.sectors} sectors
            </span>
          )}
        </div>
      </footer>
    </div>
  );
}
