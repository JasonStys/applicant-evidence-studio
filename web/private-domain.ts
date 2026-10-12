// Purpose: Jason Stys — local deterministic evidence review; no resume text leaves the device.
// Index: validBatch@3, validJob@3, syntheticApplicants@4, syntheticJobs@5, Applicant@6, Assessment@6, Coaching@6, Job@6, Level@6, extractPrivate@7, accountRequest@8, seal@8, skills@10, notice@48, points@50, Workspace@51, workspace@57, key@58, salt@59, revision@60, pending@61, generation@62, unsaved@63, validateWorkspace@66, value@66, data@69, i@83, batch@84, a@87, a@89, s@91, sources@91, e@94, n@95, s@95, e@96, a@102, id@102, j@104, job@105, c@108, c@109, emptyWorkspace@117, demoWorkspace@122, applicants@123, a@128, bindWorkspace@133, value@134, secret@135, kdfSalt@136, observedRevision@137, lockWorkspace@148, isPrivateWorkspace@156, snapshot@159, encryptedBackup@165, change@171, copy@171, mutate@171, epoch@172, task@173, copy@175, result@176, checked@177, envelope@178, saved@181, digits@193, pythonRound@193, value@193, buffer@195, bits@197, exponent@198, numerator@199, denominator@200, rounded@203, remainder@204, applicant@210, assessPrivate@210, job@210, best@211, e@212, c@215, criteria@215, e@216, score@226, c@227, n@227, c@228, n@228, flags@231, e@232, e@234, e@236, s@238, c@240, gaps@240, fingerprint@259, job@259, value@260, c@264, b@279, description@286, recommend@286, aliases@287, text@295, chosen@296, s@296, term@297, skill@301, applicant@310, coach@310, job@310, gaps@311, c@313, c@314, skill@330, escape@345, value@345, c@348, a@351, job@351, resumePrivate@351, items@352, e@353, x@355, y@355, c@356, c@357, e@368, e@381, input@405, method@405, path@405, privateAPI@405, url@406, route@407, data@408, body@409, selectedJob@410, j@411, job@411, a@413, result@414, copy@425, job@426, j@427, hash@437, rows@438, a@439, a@440, b@440, last@441, position@442, i@443, row@443, q@451, skill@452, status@453, a@454, byId@454, filtered@455, r@455, a@456, e@459, offset@463, copy@471, batch@472, a@474, x@475, x@477, copy@485, x@488, copy@493, x@494
import { validBatch, validJob } from './validators.generated.js';
import syntheticApplicants from '../examples/applicants.json';
import syntheticJobs from '../examples/jobs.json';
import type { Applicant, Assessment, Coaching, Job, Level } from './types';
import { extractPrivate } from './private-ingest';
import { accountRequest, seal } from './vault';

export const skills: Record<string, string> = {
  python: 'Python',
  cpp: 'C++',
  csharp: 'C#',
  java: 'Java',
  javascript: 'JavaScript',
  typescript: 'TypeScript',
  rust: 'Rust',
  assembly: 'Assembly',
  php: 'PHP',
  bash: 'Bash',
  sql: 'SQL',
  html_css: 'HTML / CSS',
  testing: 'Automated testing',
  api_design: 'API design',
  security: 'Application security',
  accessibility: 'Accessibility',
  documentation: 'Documentation',
  git_ci: 'Git / CI',
  cloud: 'Cloud deployment',
  containers: 'Containers',
  data_analysis: 'Data analysis',
  statistics: 'Statistics',
  machine_learning: 'Machine learning',
  deep_learning: 'Deep learning',
  embedded: 'Embedded software',
  protocols: 'Industrial protocols',
  linux: 'Linux',
  game_engine: 'Game engines',
  graphics: 'Graphics programming',
  frontend: 'Frontend development',
  backend: 'Backend development',
  mobile: 'Mobile development',
  requirements: 'Requirements analysis',
  customer_support: 'Customer support',
  sales_analysis: 'Sales analysis',
  technical_writing: 'Technical writing',
};
export const notice =
  'Advisory evidence ranking only. Read the original application and cited work before making a hiring decision.';
const points: Record<Level, number> = { declared: 1, practiced: 2, demonstrated: 3, assessed: 4 };
export interface Workspace {
  version: 1;
  applicants: Applicant[];
  jobs: Job[];
  revisions: Record<string, number>;
}
let workspace: Workspace | null = null;
let key: CryptoKey | null = null;
let salt = '';
let revision = 0;
let pending: Promise<unknown> = Promise.resolve();
let generation = 0;
let unsaved: Workspace | null = null;

/** Validate JSON schemas plus taxonomy/citation/uniqueness invariants, without guessing private facts. */
export function validateWorkspace(value: unknown): Workspace {
  if (new TextEncoder().encode(JSON.stringify(value)).length > 8 * 1024 * 1024)
    throw new Error('Workspace exceeds 8 MiB.');
  const data = structuredClone(value) as Workspace;
  if (
    !data ||
    data.version !== 1 ||
    Object.keys(data).sort().join(',') !== 'applicants,jobs,revisions,version' ||
    !Array.isArray(data.applicants) ||
    data.applicants.length > 1000 ||
    !Array.isArray(data.jobs) ||
    data.jobs.length > 100 ||
    !data.revisions ||
    typeof data.revisions !== 'object' ||
    Array.isArray(data.revisions)
  )
    throw new Error('Invalid workspace structure.');
  for (let i = 0; i < data.applicants.length; i += 100) {
    const batch = { applicants: data.applicants.slice(i, i + 100), replace: false };
    if (!validBatch(batch)) throw new Error('Applicant fields do not match the documented schema.');
  }
  if (new Set(data.applicants.map((a) => a.id)).size !== data.applicants.length)
    throw new Error('Duplicate applicant IDs.');
  for (const a of data.applicants) {
    if (['__proto__', 'constructor', 'prototype'].includes(a.id)) throw new Error('Reserved applicant ID.');
    const sources = new Set(a.sources.map((s) => s.id));
    if (
      sources.size !== a.sources.length ||
      new Set(a.evidence.map((e) => e.id)).size !== a.evidence.length ||
      a.sources.reduce((n, s) => n + s.text.length, 0) > 200000 ||
      a.evidence.some((e) => !sources.has(e.source_id) || !Object.hasOwn(skills, e.skill))
    )
      throw new Error('Invalid citations, skill or source limits.');
    if (!Number.isSafeInteger(data.revisions[a.id]) || data.revisions[a.id] < 1)
      throw new Error('Invalid applicant revision.');
  }
  if (Object.keys(data.revisions).some((id) => !data.applicants.some((a) => a.id === id)))
    throw new Error('Unexpected revision ID.');
  if (new Set(data.jobs.map((j) => j.id)).size !== data.jobs.length) throw new Error('Duplicate job IDs.');
  for (const job of data.jobs) {
    if (
      !validJob(job) ||
      job.criteria.some((c) => !Object.hasOwn(skills, c.skill)) ||
      new Set(job.criteria.map((c) => c.skill)).size !== job.criteria.length
    )
      throw new Error('Invalid job rubric: choose distinct professional skills.');
  }
  return data;
}

/** Empty accounts have no sample applicants; loading examples is always an explicit action. */
export function emptyWorkspace(): Workspace {
  return { version: 1, applicants: [], jobs: [], revisions: {} };
}

/** Create a separate copy of published fictional examples, never real runtime data. */
export function demoWorkspace(): Workspace {
  const applicants = structuredClone(syntheticApplicants.applicants) as Applicant[];
  return validateWorkspace({
    version: 1,
    applicants,
    jobs: syntheticJobs,
    revisions: Object.fromEntries(applicants.map((a) => [a.id, 1])),
  });
}

/** Bind an unlocked workspace in memory; independent keys are never exported to account APIs. */
export function bindWorkspace(
  value: Workspace,
  secret: CryptoKey,
  kdfSalt: string,
  observedRevision: number,
) {
  workspace = validateWorkspace(value);
  key = secret;
  salt = kdfSalt;
  revision = observedRevision;
  unsaved = null;
  generation++;
}

/** Drop references and invalidate pending operations; JS cannot promise a secure memory wipe. */
export function lockWorkspace() {
  workspace = null;
  key = null;
  salt = '';
  revision = 0;
  unsaved = null;
  generation++;
}
export function isPrivateWorkspace() {
  return workspace !== null;
}
export function snapshot() {
  if (!workspace) throw new Error('Unlock your workspace.');
  return structuredClone(workspace);
}

/** Encrypt/export a stable copy, including edits after a conflict; caller never receives the key. */
export async function encryptedBackup() {
  if (!key) throw new Error('Workspace is locked.');
  return seal(unsaved || snapshot(), key, salt);
}

/** Serialize edits; sync ciphertext first, then commit memory. Never silently overwrite conflicts. */
async function mutate(change: (copy: Workspace) => unknown): Promise<unknown> {
  const epoch = generation;
  const task = pending.then(async () => {
    if (!key || epoch !== generation) throw new Error('Workspace locked. Reopen before editing.');
    const copy = snapshot();
    const result = change(copy);
    const checked = validateWorkspace(copy);
    const envelope = await seal(checked, key, salt);
    if (epoch !== generation) throw new Error('Workspace locked.');
    unsaved = checked;
    const saved = await accountRequest<{ revision: number }>('workspace', 'PUT', { envelope, revision });
    if (epoch !== generation) throw new Error('Workspace locked.');
    workspace = checked;
    revision = saved.revision;
    unsaved = null;
    return result;
  });
  pending = task.catch(() => undefined);
  return task;
}

/** Round the exact positive IEEE-754 value as Python does, including half-even ties. */
function pythonRound(value: number, digits: number) {
  if (value === 0) return 0;
  const buffer = new DataView(new ArrayBuffer(8));
  buffer.setFloat64(0, value, false);
  const bits = buffer.getBigUint64(0, false);
  const exponent = Number((bits >> 52n) & 2047n) - 1023 - 52;
  let numerator = ((bits & ((1n << 52n) - 1n)) | (1n << 52n)) * 10n ** BigInt(digits);
  let denominator = 1n;
  if (exponent >= 0) numerator <<= BigInt(exponent);
  else denominator <<= BigInt(-exponent);
  let rounded = numerator / denominator;
  const remainder = numerator % denominator;
  if (remainder * 2n > denominator || (remainder * 2n === denominator && rounded % 2n)) rounded++;
  return Number(rounded) / 10 ** digits;
}

/** Match Python's documented rounded attainment/weighted score and uncertainty, including shared ties. */
export function assessPrivate(applicant: Applicant, job: Job): Assessment {
  const best = new Map<string, Applicant['evidence'][number]>();
  for (const e of applicant.evidence)
    if (e.reviewed && (!best.has(e.skill) || points[e.level] > points[best.get(e.skill)!.level]))
      best.set(e.skill, e);
  const criteria = job.criteria.map((c) => {
    const e = best.get(c.skill);
    return {
      ...c,
      label: skills[c.skill],
      attainment: e ? pythonRound(Math.min(1, points[e.level] / points[c.target]), 4) : 0,
      evidence_id: e?.id || null,
      source_id: e?.source_id || null,
      level: e?.level || 'not_evidenced',
    };
  });
  const score = pythonRound(
    (100 * criteria.reduce((n, c) => n + c.weight * c.attainment, 0)) /
      criteria.reduce((n, c) => n + c.weight, 0),
    1,
  );
  const flags: string[] = [];
  if (applicant.evidence.some((e) => !e.reviewed))
    flags.push('Unreviewed claims are excluded from scoring; inspect their sources.');
  if (applicant.education.some((e) => e.status === 'unclear'))
    flags.push('Education outcome unclear: ask the applicant rather than assuming a degree or failure.');
  if (applicant.education.some((e) => e.status === 'transferred' && !e.transferred_to))
    flags.push('Transfer destination missing: clarify the chronology; no degree is inferred.');
  if (applicant.sources.some((s) => s.warnings.length))
    flags.push('A source has extraction or access warnings; check the original document.');
  const gaps = criteria.filter((c) => c.required && c.attainment < 1).map((c) => c.skill);
  if (gaps.length)
    flags.push(
      'Required evidence gaps need clarification or a relevant work sample, not automatic rejection.',
    );
  return {
    applicant_id: applicant.id,
    score,
    rank: 0,
    criteria,
    flags,
    required_gaps: gaps,
    status: flags.length ? 'needs_review' : score >= 80 ? 'strong_evidence' : 'partial_evidence',
    rubric_hash: '',
    method: 'reviewed-evidence-rubric-v1',
  };
}

/** Hash the same canonical JSON as Python, so reports are reproducible across runtimes. */
async function fingerprint(job: Job) {
  const value =
    '[' +
    job.criteria
      .map(
        (c) =>
          '{"required": ' +
          String(c.required) +
          ', "skill": ' +
          JSON.stringify(c.skill) +
          ', "target": ' +
          JSON.stringify(c.target) +
          ', "weight": ' +
          c.weight +
          '}',
      )
      .join(', ') +
    ']';
  return Array.from(
    new Uint8Array(await crypto.subtle.digest('SHA-256', new TextEncoder().encode(value))),
    (b) => b.toString(16).padStart(2, '0'),
  )
    .join('')
    .slice(0, 16);
}

/** User-approved drafts from a closed vocabulary; text is never an automatic scoring input. */
function recommend(description: string) {
  const aliases: Record<string, string[]> = {
    cpp: ['c++'],
    csharp: ['c#'],
    html_css: ['html', 'css'],
    api_design: ['api', 'rest'],
    git_ci: ['git', 'ci/cd'],
    testing: ['test', 'tests', 'testing'],
  };
  const text = description.toLowerCase();
  const chosen = Object.keys(skills).filter((s) =>
    (aliases[s] || [s.replaceAll('_', ' '), skills[s].toLowerCase()]).some((term) =>
      new RegExp('(^|[^\\w])' + term.replace(/[.*+?^${}()|[\]\\]/g, '\\$&') + '($|[^\\w])').test(text),
    ),
  );
  return (chosen.length ? chosen : ['requirements', 'documentation']).map((skill) => ({
    skill,
    weight: 1,
    target: 'demonstrated' as Level,
    required: true,
  }));
}

/** Truth-preserving coaching from reviewed claims and rubric gaps, never invented employment. */
function coach(applicant: Applicant, job?: Job): Coaching {
  const gaps = job
    ? assessPrivate(applicant, job)
        .criteria.filter((c) => c.attainment < 1)
        .map((c) => c.skill)
    : [];
  return {
    advice: [
      'Show your own contribution, design trade-offs, reproducible setup and test results.',
      'Keep employment duration separate from coursework and project practice; never invent years or credentials.',
      'Label transfers and current study explicitly; verify completed degrees.',
    ],
    linkedin: [
      'Add a projects section with your responsibilities, links and substantiated measured results.',
      'Describe coursework as coursework, not paid employment.',
    ],
    resume: [
      'Lead with reviewed relevant skills. Verify every fact before submission.',
      'Use a single-column layout and consistent headings.',
    ],
    projects: gaps.slice(0, 8).map((skill) => ({
      skill,
      title: skills[skill] + ' evidence lab',
      steps: [
        'Build a job-relevant example demonstrating ' + skills[skill] + '; explain your own contribution.',
        'Include unit, integration, negative-input and regression tests plus CI.',
        'Record reproducible benchmarks, limitations, security and design trade-offs.',
        'Publish only data/code you have permission to share; report observed outcomes.',
      ],
    })),
    general: !job,
  };
}

/** Escape all user content in inert downloadable HTML; no scripts or remote resources. */
function escape(value: string) {
  return value.replace(
    /[&<>"']/g,
    (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[c]!,
  );
}
export function resumePrivate(a: Applicant, job?: Job) {
  const items = a.evidence
    .filter((e) => e.reviewed)
    .sort(
      (x, y) =>
        Number(!job?.criteria.some((c) => c.skill === x.skill)) -
          Number(!job?.criteria.some((c) => c.skill === y.skill)) || x.skill.localeCompare(y.skill),
    );
  return (
    '<!doctype html><html lang="en"><meta charset="utf-8"><meta http-equiv="Content-Security-Policy" content="default-src \'none\'; style-src \'unsafe-inline\'"><title>Resume draft</title><body>' +
    '<p>Draft: verify all facts before use. Only reviewed claims included. Print to PDF if desired.</p><h1>' +
    escape(a.display_name) +
    '</h1><p>' +
    escape(job?.title || 'Professional skills and project evidence') +
    '</p><h2>Relevant evidence</h2><ul>' +
    items
      .map(
        (e) =>
          '<li><strong>' +
          escape(skills[e.skill]) +
          '</strong> (' +
          escape(e.kind) +
          '): ' +
          escape(e.summary) +
          '</li>',
      )
      .join('') +
    '</ul><h2>Education and transitions</h2><ul>' +
    a.education
      .map(
        (e) =>
          '<li>' +
          escape(
            e.institution +
              ' — ' +
              e.program +
              '; ' +
              e.status.replaceAll('_', ' ') +
              (e.transferred_to ? '; transferred to ' + e.transferred_to : '') +
              '. ' +
              e.notes,
          ) +
          '</li>',
      )
      .join('') +
    '</ul><h2>Employment duration</h2><p>' +
    (a.verified_employment_months === null
      ? 'Not supplied / not verified'
      : a.verified_employment_months + ' verified months') +
    '; coursework and projects are not converted into employment years.</p></body></html>'
  );
}

/** Fulfil the existing UI contract in browser memory; only mutations sync encrypted ciphertext. */
export async function privateAPI<T>(path: string, method = 'GET', input?: unknown): Promise<T> {
  const url = new URL(path, 'https://local.invalid/');
  const route = url.pathname.slice(1).split('/').map(decodeURIComponent);
  const data = snapshot();
  const body = input as Record<string, unknown>;
  const selectedJob = url.searchParams.get('job_id');
  const job = selectedJob ? data.jobs.find((j) => j.id === selectedJob) : undefined;
  if (selectedJob && !job) throw new Error('Select or create a valid job rubric.');
  const a = data.applicants.find((a) => a.id === route[1]);
  let result: unknown;
  if (route[0] === 'config')
    result = {
      skills,
      notice,
      ai_configured: false,
      capacity: 1000,
      file_types: ['txt', 'md', 'docx', 'pdf'],
    };
  else if (route[0] === 'jobs' && method === 'GET') result = data.jobs;
  else if (route[0] === 'jobs' && method === 'POST')
    return (await mutate((copy) => {
      const job = structuredClone(input) as Job;
      copy.jobs = [...copy.jobs.filter((j) => j.id !== job.id), job];
      return job;
    })) as T;
  else if (route[0] === 'recommend')
    result = {
      criteria: recommend(String(body.description || '')),
      notice: 'Draft; review relevance before saving.',
    };
  else if (route[0] === 'queue') {
    if (!job) throw new Error('Create a job rubric first.');
    const hash = await fingerprint(job);
    const rows = data.applicants
      .map((a) => assessPrivate(a, job))
      .sort((a, b) => b.score - a.score || (a.applicant_id < b.applicant_id ? -1 : 1));
    let last = -1,
      position = 0;
    rows.forEach((row, i) => {
      if (row.score !== last) {
        position = i + 1;
        last = row.score;
      }
      row.rank = position;
      row.rubric_hash = hash;
    });
    const q = (url.searchParams.get('q') || '').toLowerCase(),
      skill = url.searchParams.get('skill'),
      status = url.searchParams.get('status');
    const byId = new Map(data.applicants.map((a) => [a.id, a]));
    const filtered = rows.filter((r) => {
      const a = byId.get(r.applicant_id)!;
      return (
        (!q || (a.display_name + ' ' + a.id).toLowerCase().includes(q)) &&
        (!skill || a.evidence.some((e) => e.skill === skill && e.reviewed)) &&
        (!status || r.status === status)
      );
    });
    const offset = Math.max(0, Number(url.searchParams.get('offset') || 0));
    result = {
      total: filtered.length,
      pool_total: rows.length,
      items: filtered.slice(offset, offset + 25),
      notice,
    };
  } else if (route[0] === 'import')
    return (await mutate((copy) => {
      const batch = structuredClone(input) as { applicants: Applicant[]; replace?: boolean };
      if (!validBatch(batch)) throw new Error('Invalid applicant batch.');
      for (const a of batch.applicants) {
        if (copy.applicants.some((x) => x.id === a.id) && !batch.replace)
          throw new Error('Duplicate ID: explicitly approve replacement.');
        copy.applicants = [...copy.applicants.filter((x) => x.id !== a.id), a];
        copy.revisions[a.id] = (copy.revisions[a.id] || 0) + 1;
      }
      return { imported: batch.applicants.length };
    })) as T;
  else if (route[0] === 'applicants' && a && method === 'GET')
    result = { applicant: a, revision: data.revisions[a.id] };
  else if (route[0] === 'applicants' && a && method === 'PUT')
    return (await mutate((copy) => {
      if (copy.revisions[a.id] !== body.revision || (body.applicant as Applicant).id !== a.id)
        throw new Error('Stale edit or incorrect record ID.');
      copy.applicants = copy.applicants.map((x) => (x.id === a.id ? (body.applicant as Applicant) : x));
      copy.revisions[a.id]++;
      return { saved: true, revision: copy.revisions[a.id] };
    })) as T;
  else if (route[0] === 'applicants' && a && method === 'DELETE')
    return (await mutate((copy) => {
      copy.applicants = copy.applicants.filter((x) => x.id !== a.id);
      delete copy.revisions[a.id];
      return { deleted: true };
    })) as T;
  else if (route[0] === 'coach' && a) result = coach(a, job);
  else if (route[0] === 'report' && a && job)
    result = { ...assessPrivate(a, job), rubric_hash: await fingerprint(job), notice };
  else if (route[0] === 'resume' && a) result = resumePrivate(a, job);
  else if (route[0] === 'export' && a) result = a;
  else if (route[0] === 'ingest') result = await extractPrivate(String(body.filename), String(body.content));
  else if (route[0] === 'github' || route[0] === 'ai')
    throw new Error(
      'Private mode makes no third-party calls. Paste an authorized professional export as a source; use local coaching. External AI is available only in the separate trusted local developer mode.',
    );
  else throw new Error('Record or operation unavailable.');
  return result as T;
}
