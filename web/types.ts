// Purpose: typed browser contracts mirror validated backend records; no sensitive scoring fields exist.
// Index: Level@3, Evidence@4, Source@14, Education@22, Applicant@29, Criterion@41, Job@47, Assessment@53, Queue@74, Config@80, Coaching@87, AIResult@94
export type Level = 'declared' | 'practiced' | 'demonstrated' | 'assessed';
export interface Evidence {
  id: string;
  skill: string;
  kind: 'project' | 'coursework' | 'employment' | 'certification' | 'work_sample';
  level: Level;
  summary: string;
  source_id: string;
  locator: string;
  reviewed: boolean;
}
export interface Source {
  id: string;
  label: string;
  kind: 'resume' | 'github' | 'linkedin' | 'work_sample' | 'other';
  text: string;
  url: string;
  warnings: string[];
}
export interface Education {
  institution: string;
  program: string;
  status: 'completed' | 'in_progress' | 'transferred' | 'coursework_only' | 'unclear';
  transferred_to: string;
  notes: string;
}
export interface Applicant {
  id: string;
  display_name: string;
  consent_sources: boolean;
  consent_ai: boolean;
  sources: Source[];
  evidence: Evidence[];
  education: Education[];
  verified_employment_months: number | null;
  notes: string;
  review_status: 'pending' | 'reviewed' | 'clarification_requested';
}
export interface Criterion {
  skill: string;
  weight: number;
  target: Level;
  required: boolean;
}
export interface Job {
  id: string;
  title: string;
  description: string;
  criteria: Criterion[];
}
export interface Assessment {
  applicant_id: string;
  score: number;
  rank: number;
  status: string;
  flags: string[];
  required_gaps: string[];
  rubric_hash: string;
  method: string;
  criteria: {
    skill: string;
    label: string;
    weight: number;
    target: string;
    attainment: number;
    evidence_id: string | null;
    source_id: string | null;
    level: string;
    required: boolean;
  }[];
}
export interface Queue {
  items: Assessment[];
  total: number;
  pool_total: number;
  notice: string;
}
export interface Config {
  skills: Record<string, string>;
  notice: string;
  ai_configured: boolean;
  capacity: number;
  file_types: string[];
}
export interface Coaching {
  advice: string[];
  linkedin: string[];
  resume: string[];
  projects: { skill: string; title: string; steps: string[] }[];
  general: boolean;
}
export interface AIResult {
  suggestions: { skill: string; evidence_ids: string[]; action: string; text: string }[];
  provider: string;
  model: string;
  method: string;
  unverified_ai: boolean;
}
