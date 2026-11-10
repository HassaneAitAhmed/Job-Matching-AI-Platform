// Typed client for the Flask JSON API (see webapp/app.py).

export type Direction = "seeker_to_job" | "job_to_seeker";
export type Algorithm = "astar" | "greedy" | "csp" | "exhaustive";
export type Criterion =
  | "sector"
  | "contract_type"
  | "education"
  | "location"
  | "experience"
  | "salary"
  | "skills";

export interface Option<T = string> {
  value: T;
  label: string;
}

export interface Options {
  sectors: string[];
  cities: string[];
  contract_types: Option[];
  education_levels: Option<number>[];
  algorithms: Algorithm[];
  criteria: Criterion[];
  weights: Record<Direction, Record<Criterion, number>>;
}

export interface Stats {
  total_jobs: number;
  total_seekers: number;
  sectors: number;
  cities: number;
  jobs_without_skills: number;
  skill_vocabulary: number;
  tree_nodes: Record<Direction, number>;
}

export type Breakdown = Record<Criterion, { score: number; weight: number }>;

interface MatchBase {
  id: number;
  department: string;
  sector: string;
  contract_type: string;
  city: string;
  skills: string[];
  matched_skills: string[];
  skills_listed: boolean;
  match_score: number;
  breakdown: Breakdown;
}

export interface JobMatch extends MatchBase {
  type: "job";
  title: string;
  experience_required: [number, number];
  education_required: string;
  salary: number;
  posts: number;
}

export interface SeekerMatch extends MatchBase {
  type: "seeker";
  experience_years: number;
  education: string;
  salary_expectation: number;
  languages: string[];
}

export type Match = JobMatch | SeekerMatch;

export interface SearchStats {
  algorithm: Algorithm;
  nodes_expanded: number;
  nodes_generated: number;
  items_scored: number;
  max_frontier: number;
  elapsed_ms: number;
  solutions?: number;
  pruned_by_node_consistency?: number;
  pruned_by_forward_checking?: number;
  relaxed_constraints?: string[];
}

export interface SearchResponse {
  direction: Direction;
  algorithm: Algorithm;
  offset: number;
  limit: number;
  matches: Match[];
  has_more: boolean;
  stats: SearchStats;
}

export interface AssignMethod {
  method: string;
  total_score: number;
  pct_of_optimal: number;
  assigned: number;
  elapsed_ms: number;
  generations_to_best?: number;
}

export interface AssignResponse {
  n_seekers: number;
  n_jobs: number;
  total_posts: number;
  results: AssignMethod[];
  ga_history: number[];
  optimal_pairs: { seeker_id: number; job_id: number; job_title: string; score: number; ga_agrees: boolean }[];
}

export class ApiError extends Error {}

async function request<T>(path: string, body?: unknown): Promise<T> {
  let response: Response;
  try {
    response = await fetch(path, {
      method: body === undefined ? "GET" : "POST",
      headers: body === undefined ? undefined : { "Content-Type": "application/json" },
      body: body === undefined ? undefined : JSON.stringify(body),
    });
  } catch {
    throw new ApiError("Can't reach the server. Is the Flask app running?");
  }
  const data = await response.json().catch(() => null);
  if (!response.ok) {
    throw new ApiError(data?.error ?? `Request failed (${response.status})`);
  }
  return data as T;
}

export const api = {
  options: () => request<Options>("/api/options"),
  stats: () => request<Stats>("/api/stats"),
  skills: () => request<string[]>("/api/skills"),
  search: (direction: Direction, body: Record<string, unknown>) =>
    request<SearchResponse>(
      direction === "seeker_to_job" ? "/api/match/seeker-to-jobs" : "/api/match/job-to-seekers",
      body,
    ),
  assign: (body: Record<string, unknown>) => request<AssignResponse>("/api/assign", body),
};
