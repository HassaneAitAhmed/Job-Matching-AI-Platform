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

/** The match score as a solid tile: lime for strong matches, amber for fair, coral for weak. */
export function ScoreTile({ score }: { score: number }) {
  const tone = scoreTone(score);
  return (
    <div
      className={cn("flex size-16 shrink-0 flex-col items-center justify-center rounded-2xl", tone.tile)}
      aria-label={`Match score ${Math.round(score)} out of 100`}
    >
      <span className="text-[1.65rem] leading-none font-[800] tracking-tight">{Math.round(score)}</span>
      <span className="mt-0.5 text-[10px] font-semibold opacity-70">match</span>
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
          <div key={c} className="flex items-center gap-3 text-[13px]" title={CRITERIA[c].description}>
            <Icon className="size-4 shrink-0 text-faint" aria-hidden />
            <span className="w-20 shrink-0 font-semibold">{CRITERIA[c].label}</span>
            <span className="h-1.5 flex-1 overflow-hidden rounded-full bg-sunken">
              <span className={cn("block h-full rounded-full", tone.bar)} style={{ width: `${score}%` }} />
            </span>
            <span className="w-8 shrink-0 text-right font-bold">{Math.round(score)}</span>
            <span className="w-10 shrink-0 text-right text-xs text-faint">×{Math.round(weight)}%</span>
          </div>
        );
      })}
    </div>
  );
}
