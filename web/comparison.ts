// Purpose: bounded read-only criterion/evidence comparison, with exact snapshot provenance and unknowns.
// File: comparison.ts. Author: Jason Stys. Variables: captured input clones never mutate account records.
// Index: assessPrivate@4, fingerprint@4, validateWorkspace@4, Applicant@5, Assessment@5, Evidence@5, Job@5, Source@5, ComparisonCapture@7, CriterionComparison@12, ComparisonReport@30, comparisonNotice@47, canonical@51, value@51, a@57, b@57, item@58, key@58, applicant@66, assessment@66, clarifications@66, questions@67, row@68, row@70, entry@73, index@73, buildComparison@87, input@87, capture@88, row@102, row@103, row@105, records@107, applicant@108, revision@108, assessment@109, digest@110, byte@114, criterion@121, evidence@122, item@122, item@123, source@123, item@148, item@151
import { assessPrivate, fingerprint, validateWorkspace } from './private-domain';
import type { Applicant, Assessment, Evidence, Job, Source } from './types';

export interface ComparisonCapture {
  job: Job;
  applicants: { applicant: Applicant; revision: number }[];
  captured_at: string;
}
export interface CriterionComparison {
  skill: string;
  label: string;
  target: string;
  weight: number;
  required: boolean;
  attainment: number;
  best_support: {
    evidence_id: string;
    level: string;
    kind: Evidence['kind'];
    summary: string;
    locator: string;
    source: { id: string; label: string; kind: Source['kind']; warnings: string[] };
  } | null;
  other_reviewed_claims: number;
  unreviewed_claims: number;
}
export interface ComparisonReport {
  schema_version: 1;
  method: 'criterion-evidence-comparison-v1';
  captured_at: string;
  rubric: { id: string; title: string; hash: string; criteria: Job['criteria'] };
  records: {
    id: string;
    revision: number;
    record_sha256: string;
    score: number;
    review_status: Applicant['review_status'];
    flags: string[];
    clarifications: string[];
    criteria: CriterionComparison[];
  }[];
  notice: string;
}
export const comparisonNotice =
  'Advisory evidence comparison, not a hire/reject recommendation. Missing evidence means unknown ability. Read original applications and sources yourself. Only reviewed job-relevant claims affect coverage; education never becomes paid experience. This unencrypted private export is not anonymized or signed. It omits names, raw source bodies, personal notes and employment-month totals; evidence summaries/labels may still contain personal information.';

/** Canonicalize bounded JSON fields for an in-browser provenance digest, never a ranking input. */
function canonical(value: unknown): string {
  if (Array.isArray(value)) return '[' + value.map(canonical).join(',') + ']';
  if (value !== null && typeof value === 'object')
    return (
      '{' +
      Object.entries(value)
        .sort(([a], [b]) => (a < b ? -1 : a > b ? 1 : 0))
        .map(([key, item]) => JSON.stringify(key) + ':' + canonical(item))
        .join(',') +
      '}'
    );
  return JSON.stringify(value);
}

/** Derive factual clarification prompts without guessing degrees, experience years or protected traits. */
function clarifications(applicant: Applicant, assessment: Assessment): string[] {
  const questions = assessment.criteria
    .filter((row) => row.attainment < 1)
    .map(
      (row) =>
        `Please clarify ${row.label} with an authorized source or accessible work sample; current reviewed evidence does not fully meet this rubric target.`,
    );
  applicant.education.forEach((entry, index) => {
    if (entry.status === 'unclear')
      questions.push(
        `Education entry ${index + 1}: please clarify the stated outcome. No degree or failure is inferred.`,
      );
    if (entry.status === 'transferred' && !entry.transferred_to.trim())
      questions.push(
        `Education entry ${index + 1}: please clarify the transfer destination and chronology. No degree or failure is inferred.`,
      );
  });
  return questions;
}

/** Validate and clone one two-record snapshot before asynchronous hashing; do not alter scores or records. */
export async function buildComparison(input: ComparisonCapture): Promise<ComparisonReport> {
  const capture = structuredClone(input);
  if (
    capture.applicants.length !== 2 ||
    capture.applicants[0].applicant.id === capture.applicants[1].applicant.id
  )
    throw new Error('Choose exactly two different applicant records.');
  if (
    !/(?:Z|[+-]\d{2}:\d{2})$/.test(capture.captured_at) ||
    !Number.isFinite(Date.parse(capture.captured_at))
  )
    throw new Error('Invalid capture timestamp.');
  validateWorkspace({
    version: 1,
    jobs: [capture.job],
    applicants: capture.applicants.map((row) => row.applicant),
    revisions: Object.fromEntries(capture.applicants.map((row) => [row.applicant.id, row.revision])),
  });
  if (capture.applicants.some((row) => !row.applicant.consent_sources))
    throw new Error('Both records require confirmed processing authorization.');
  const records = await Promise.all(
    capture.applicants.map(async ({ applicant, revision }) => {
      const assessment = assessPrivate(applicant, capture.job);
      const digest = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(canonical(applicant)));
      return {
        id: applicant.id,
        revision,
        record_sha256: Array.from(new Uint8Array(digest), (byte) => byte.toString(16).padStart(2, '0')).join(
          '',
        ),
        score: assessment.score,
        review_status: applicant.review_status,
        flags: assessment.flags,
        clarifications: clarifications(applicant, assessment),
        criteria: assessment.criteria.map((criterion) => {
          const evidence = applicant.evidence.find((item) => item.id === criterion.evidence_id);
          const source = evidence ? applicant.sources.find((item) => item.id === evidence.source_id) : null;
          return {
            skill: criterion.skill,
            label: criterion.label,
            target: criterion.target,
            weight: criterion.weight,
            required: criterion.required,
            attainment: criterion.attainment,
            best_support:
              evidence && source
                ? {
                    evidence_id: evidence.id,
                    level: evidence.level,
                    kind: evidence.kind,
                    summary: evidence.summary,
                    locator: evidence.locator,
                    source: {
                      id: source.id,
                      label: source.label,
                      kind: source.kind,
                      warnings: source.warnings,
                    },
                  }
                : null,
            other_reviewed_claims: applicant.evidence.filter(
              (item) => item.skill === criterion.skill && item.reviewed && item.id !== evidence?.id,
            ).length,
            unreviewed_claims: applicant.evidence.filter(
              (item) => item.skill === criterion.skill && !item.reviewed,
            ).length,
          };
        }),
      };
    }),
  );
  return {
    schema_version: 1,
    method: 'criterion-evidence-comparison-v1',
    captured_at: capture.captured_at,
    rubric: {
      id: capture.job.id,
      title: capture.job.title,
      hash: await fingerprint(capture.job),
      criteria: capture.job.criteria,
    },
    records,
    notice: comparisonNotice,
  };
}
