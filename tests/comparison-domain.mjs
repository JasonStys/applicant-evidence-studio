// Purpose: independently verify criterion arithmetic, evidence provenance, exclusions and invalid input.
// File: comparison-domain.mjs. Author: Jason Stys. Variables: all records and synthetic sources are disposable.
// Index: test@4, assert@5, pathToFileURL@6, buildComparison@7, fixture@10, source@11, evidence@19, id@19, level@19, reviewed@19, skill@19, evidence@29, id@29, person@29, input@73, before@74, report@75, row@86, text@91, marker@92, input@109, original@110, changed@123, text@127, text@129, same@131, tied@134, row@137, input@143, pending@144, changes@147, data@148, data@149, data@150, data@151, data@152, data@153, data@154, data@155, data@156, change@158, data@159
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { pathToFileURL } from 'node:url';
const { buildComparison } = await import(pathToFileURL(process.env.AES_COMPARISON_MODULE).href);

/** Construct hand-calculated 3:1 weight cases:2/3 Python practice and1/4 testing declaration. */
function fixture() {
  const source = {
    id: 'S1',
    label: 'Authorized work sample',
    kind: 'work_sample',
    text: 'PRIVATE_SOURCE_BODY',
    url: '',
    warnings: ['Verify contribution ownership'],
  };
  const evidence = (id, skill, level, reviewed = true) => ({
    id,
    skill,
    level,
    reviewed,
    kind: 'coursework',
    summary: 'Synthetic skill demonstration',
    source_id: 'S1',
    locator: 'README section2',
  });
  const person = (id, evidence) => ({
    id,
    display_name: 'PRIVATE_IDENTITY',
    consent_sources: true,
    consent_ai: false,
    sources: [source],
    evidence,
    education: [],
    verified_employment_months: null,
    notes: 'PRIVATE_NOTES',
    review_status: 'pending',
  });
  return {
    job: {
      id: 'J1',
      title: 'Synthetic software role',
      description: 'PRIVATE_DESCRIPTION',
      criteria: [
        { skill: 'python', weight: 3, target: 'demonstrated', required: true },
        { skill: 'testing', weight: 1, target: 'assessed', required: true },
      ],
    },
    applicants: [
      {
        applicant: person('A1', [
          evidence('E1', 'python', 'practiced'),
          evidence('E2', 'python', 'practiced'),
          evidence('E3', 'testing', 'assessed', false),
        ]),
        revision: 2,
      },
      {
        applicant: person('B1', [
          evidence('E1', 'python', 'assessed'),
          evidence('E2', 'testing', 'declared'),
        ]),
        revision: 3,
      },
    ],
    captured_at: '2026-11-09T12:00:00Z',
  };
}

test('hand-calculated scores/coverage and exact strongest citations, not repeated claims', async () => {
  const input = fixture();
  const before = structuredClone(input);
  const report = await buildComparison(input);
  assert.deepEqual(input, before);
  assert.equal(report.records[0].score, 50);
  assert.equal(report.records[1].score, 81.2);
  assert.equal(report.records[0].criteria[0].attainment, 0.6667);
  assert.equal(report.records[1].criteria[1].attainment, 0.25);
  assert.equal(report.records[0].criteria[0].best_support.evidence_id, 'E1');
  assert.equal(report.records[0].criteria[0].other_reviewed_claims, 1);
  assert.equal(report.records[0].criteria[1].best_support, null);
  assert.equal(report.records[0].criteria[1].unreviewed_claims, 1);
  assert.deepEqual(
    report.records.map((row) => row.revision),
    [2, 3],
  );
  assert.match(report.records[0].record_sha256, /^[0-9a-f]{64}$/);
  assert.match(report.rubric.hash, /^[0-9a-f]{16}$/);
  const text = JSON.stringify(report);
  for (const marker of [
    'PRIVATE_IDENTITY',
    'PRIVATE_SOURCE_BODY',
    'PRIVATE_NOTES',
    'PRIVATE_DESCRIPTION',
    'verified_employment_months',
  ])
    assert.ok(!text.includes(marker));
  assert.equal(
    report.records[0].criteria[0].best_support.source.warnings[0],
    'Verify contribution ownership',
  );
  assert.equal(report.records[0].criteria[0].best_support.locator, 'README section2');
  assert.ok(!('rank' in report.records[0]));
});

test('identity/chronology/employment do not change scores; ambiguous facts produce clarification only', async () => {
  const input = fixture();
  const original = await buildComparison(input);
  input.applicants[0].applicant.display_name = 'Changed identity';
  input.applicants[0].applicant.verified_employment_months = 240;
  input.applicants[0].applicant.education = [
    {
      institution: 'University A',
      program: 'Changed major',
      status: 'transferred',
      transferred_to: '',
      notes: 'No degree claim',
    },
    { institution: 'University B', program: 'Coursework', status: 'unclear', transferred_to: '', notes: '' },
  ];
  const changed = await buildComparison(input);
  assert.equal(changed.records[0].score, original.records[0].score);
  assert.notEqual(changed.records[0].record_sha256, original.records[0].record_sha256);
  assert.equal(changed.records[0].clarifications.length, 4);
  assert.ok(changed.records[0].clarifications.some((text) => text.includes('transfer destination')));
  assert.ok(
    changed.records[0].clarifications.some((text) => text.includes('No degree or failure is inferred')),
  );
  const same = fixture();
  same.applicants[1].applicant = structuredClone(same.applicants[0].applicant);
  same.applicants[1].applicant.id = 'B1';
  const tied = await buildComparison(same);
  assert.equal(tied.records[0].score, tied.records[1].score);
  assert.deepEqual(
    tied.records.map((row) => row.id),
    ['A1', 'B1'],
  );
});

test('clones input before hashing and refuses malformed or unauthorized captures', async () => {
  const input = fixture();
  const pending = buildComparison(input);
  input.applicants[0].applicant.evidence[0].level = 'assessed';
  assert.equal((await pending).records[0].score, 50);
  const changes = [
    (data) => data.applicants.pop(),
    (data) => (data.applicants[1].applicant.id = 'A1'),
    (data) => (data.applicants[0].revision = 0),
    (data) => (data.applicants[0].applicant.consent_sources = false),
    (data) => (data.applicants[0].applicant.evidence[0].source_id = 'missing'),
    (data) => data.job.criteria.push({ ...data.job.criteria[0] }),
    (data) => (data.job.criteria[0].skill = 'gender'),
    (data) => (data.captured_at = '2026-11-09T12:00:00'),
    (data) => (data.captured_at = 'invalid'),
  ];
  for (const change of changes) {
    const data = fixture();
    change(data);
    await assert.rejects(buildComparison(data));
  }
});
