import {
  Banknote,
  BriefcaseBusiness,
  Building2,
  FileText,
  GraduationCap,
  MapPin,
  Wrench,
  type LucideIcon,
} from "lucide-react";
import type { Breakdown as BreakdownData, Criterion } from "../lib/api";
import { CRITERIA, CRITERIA_ORDER, scoreTone } from "../lib/format";
import { cn } from "./ui";

export const CRITERION_ICONS: Record<Criterion, LucideIcon> = {
  skills: Wrench,
  location: MapPin,
  experience: BriefcaseBusiness,
  education: GraduationCap,
  salary: Banknote,
  sector: Building2,
  contract_type: FileText,
};

/** The match score as a large serif numeral over a thin bar. */
export function ScoreFigure({ score }: { score: number }) {
  const tone = scoreTone(score);
  const pct = Math.max(0, Math.min(100, score));
  return (
    <div className="w-14 shrink-0" aria-label={`Match score ${Math.round(score)} out of 100`}>
      <div className={cn("font-display text-[2.6rem] leading-none font-[450] tracking-tight tabular-nums", tone.text)}>
        {Math.round(score)}
      </div>
      <div className="mt-2 h-[3px] bg-sunken">
        <div className={cn("h-full", tone.bar)} style={{ width: `${pct}%`, transition: "width .6s ease" }} />
      </div>
      <div className="mt-1.5 font-mono text-[10px] tracking-[0.08em] text-faint uppercase">match</div>
    </div>
  );
}

export function Breakdown({ data }: { data: BreakdownData }) {
  return (
    <div className="grid gap-x-10 gap-y-3 sm:grid-cols-2">
      {CRITERIA_ORDER.map((c) => {
        const { score, weight } = data[c];
        const Icon = CRITERION_ICONS[c];
        const tone = scoreTone(score);
        return (
          <div key={c} className="flex items-center gap-3 text-xs" title={CRITERIA[c].description}>
            <Icon className="size-3.5 shrink-0 text-faint" aria-hidden />
            <span className="w-20 shrink-0 font-medium">{CRITERIA[c].label}</span>
            <span className="h-[3px] flex-1 bg-sunken">
              <span className={cn("block h-full", tone.bar)} style={{ width: `${score}%` }} />
            </span>
            <span className="w-9 shrink-0 text-right font-mono tabular-nums">{Math.round(score)}</span>
            <span className="w-10 shrink-0 text-right font-mono text-faint tabular-nums">×{Math.round(weight)}%</span>
          </div>
        );
      })}
    </div>
  );
}
