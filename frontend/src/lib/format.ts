import type { Algorithm, Criterion } from "./api";

const number = new Intl.NumberFormat("en-US");

export const fmt = (n: number) => number.format(Math.round(n));
export const dzd = (n: number) => `${number.format(Math.round(n))} DZD`;
export const ms = (n: number) => (n < 10 ? `${n.toFixed(1)} ms` : `${Math.round(n)} ms`);

export const ALGORITHMS: Record<Algorithm, { name: string; tagline: string; description: string }> = {
  astar: {
    name: "A* search",
    tagline: "Optimal",
    description: "Exact best matches, scoring only a few dozen items via admissible bounds.",
  },
  greedy: {
    name: "Greedy",
    tagline: "Fast, approximate",
    description: "Follows the heuristic alone. Cheap, but can miss better matches.",
  },
  csp: {
    name: "Constraints",
    tagline: "Strict filters",
    description: "Hard limits on sector, contract, education, distance, salary and experience.",
  },
  exhaustive: {
    name: "Exhaustive",
    tagline: "Baseline",
    description: "Scores every item. Used to verify the other algorithms.",
  },
};

export const CRITERIA: Record<Criterion, { label: string; description: string }> = {
  skills: { label: "Skills", description: "Share of the job's required skills that are covered (TF-IDF soft matching)." },
  location: { label: "Location", description: "Decays with road distance between the two cities." },
  experience: { label: "Experience", description: "Inside the required range; penalised below it, mildly above it." },
  education: { label: "Education", description: "Penalised for each level below the requirement." },
  salary: { label: "Salary", description: "Penalised when the offer is below the expectation." },
  sector: { label: "Sector", description: "Same sector or not." },
  contract_type: { label: "Contract", description: "Same contract type or not." },
};

export const CRITERIA_ORDER: Criterion[] = [
  "skills",
  "location",
  "experience",
  "education",
  "salary",
  "sector",
  "contract_type",
];

export const RELAXED_LABELS: Record<string, string> = {
  max_distance_km: "distance limit",
  experience_slack: "experience range",
  min_salary_ratio: "salary floor",
  education: "education requirement",
  same_contract: "contract type",
  same_sector: "sector",
};

export function scoreTone(score: number) {
  if (score >= 75) return { text: "text-accent", bar: "bg-accent" };
  if (score >= 50) return { text: "text-ochre", bar: "bg-ochre" };
  return { text: "text-signal", bar: "bg-signal" };
}
