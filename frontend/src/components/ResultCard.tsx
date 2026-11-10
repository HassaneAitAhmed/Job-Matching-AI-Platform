import {
  BriefcaseBusiness,
  Building2,
  Check,
  ChevronDown,
  FileText,
  GraduationCap,
  Languages,
  MapPin,
  Users,
  type LucideIcon,
} from "lucide-react";
import { useState } from "react";
import type { Match } from "../lib/api";
import { dzd } from "../lib/format";
import { Breakdown, ScoreTile } from "./Score";
import { Badge, Card, cn } from "./ui";

const MAX_SKILLS = 8;

function Meta({ icon: Icon, children }: { icon: LucideIcon; children: React.ReactNode }) {
  return (
    <span className="inline-flex items-center gap-1.5 text-sm text-muted">
      <Icon className="size-4 text-faint" aria-hidden />
      {children}
    </span>
  );
}

export function ResultCard({ match, rank }: { match: Match; rank: number }) {
  const [open, setOpen] = useState(false);
  const matched = new Set(match.matched_skills.map((s) => s.toLowerCase()));
  // Show matched skills first.
  const skills = [...match.skills].sort(
    (a, b) => Number(matched.has(b.toLowerCase())) - Number(matched.has(a.toLowerCase())),
  );
  const shown = open ? skills : skills.slice(0, MAX_SKILLS);
  const isJob = match.type === "job";

  return (
    <Card className="animate-fade-up overflow-hidden transition hover:border-cobalt/40">
      <div className="flex gap-4 p-5 sm:gap-5">
        <ScoreTile score={match.match_score} />
        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-start justify-between gap-x-4 gap-y-1">
            <div className="min-w-0">
              <h3 className="text-lg leading-snug font-bold tracking-[-0.015em]">
                {isJob ? match.title : `Candidate ${match.id}`}
              </h3>
              <p className="truncate text-sm text-muted">
                <span className="text-faint">#{rank}</span>
                <span className="mx-1.5 text-faint">·</span>
                {match.department}
              </p>
            </div>
            <div className="sm:text-right">
              <p className="text-base font-bold whitespace-nowrap">
                {isJob ? dzd(match.salary) : dzd(match.salary_expectation)}
              </p>
              <p className="text-xs text-faint">{isJob ? "offered" : "expected"}</p>
            </div>
          </div>

          <div className="mt-3 flex flex-wrap gap-x-4 gap-y-1.5">
            <Meta icon={MapPin}>{match.city}</Meta>
            <Meta icon={Building2}>{match.sector}</Meta>
            <Meta icon={FileText}>{match.contract_type}</Meta>
            {isJob ? (
              <>
                <Meta icon={BriefcaseBusiness}>
                  {match.experience_required[0]}–{match.experience_required[1]} yrs
                </Meta>
                <Meta icon={GraduationCap}>{match.education_required}</Meta>
                <Meta icon={Users}>
                  {match.posts} opening{match.posts === 1 ? "" : "s"}
                </Meta>
              </>
            ) : (
              <>
                <Meta icon={BriefcaseBusiness}>{match.experience_years} yrs</Meta>
                <Meta icon={GraduationCap}>{match.education}</Meta>
                {match.languages.length > 0 && <Meta icon={Languages}>{match.languages.join(", ")}</Meta>}
              </>
            )}
          </div>

          <div className="mt-3.5 flex flex-wrap gap-1.5">
            {!match.skills_listed ? (
              <Badge tone="amber">No skills listed · counted as a weak skills match</Badge>
            ) : (
              <>
                {shown.map((s) => {
                  const hit = matched.has(s.toLowerCase());
                  return (
                    <Badge key={s} tone={hit ? "lime" : "neutral"}>
                      {hit && <Check className="size-3.5" strokeWidth={3} aria-label="matches" />}
                      {s}
                    </Badge>
                  );
                })}
                {!open && skills.length > MAX_SKILLS && <Badge>+{skills.length - MAX_SKILLS}</Badge>}
              </>
            )}
          </div>
        </div>
      </div>

      <button
        type="button"
        onClick={() => setOpen((o) => !o)}
        aria-expanded={open}
        className="flex w-full items-center justify-between border-t border-line px-5 py-3 text-[13px] font-semibold text-link transition hover:bg-cobalt-soft/60"
      >
        {open ? "Hide breakdown" : "Why this match?"}
        <ChevronDown className={cn("size-4 transition", open && "rotate-180")} aria-hidden />
      </button>
      {open && (
        <div className="border-t border-line bg-sunken/50 px-5 py-4">
          <Breakdown data={match.breakdown} />
          <p className="mt-4 text-xs text-faint">
            The score is the weighted average of these seven criteria; ×% is each one's weight.
          </p>
        </div>
      )}
    </Card>
  );
}

export function ResultSkeleton() {
  return (
    <Card className="p-5">
      <div className="flex animate-pulse gap-5">
        <div className="size-16 rounded-2xl bg-sunken" />
        <div className="flex-1 space-y-3">
          <div className="h-5 w-1/3 rounded-lg bg-sunken" />
          <div className="h-3 w-1/2 rounded-lg bg-sunken" />
          <div className="flex gap-2">
            <div className="h-6 w-20 rounded-lg bg-sunken" />
            <div className="h-6 w-24 rounded-lg bg-sunken" />
            <div className="h-6 w-16 rounded-lg bg-sunken" />
          </div>
        </div>
      </div>
    </Card>
  );
}
