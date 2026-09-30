# Architecture and decisions

## Context

Two users need the same evidence in different forms: a reviewer prioritizes a pool; an applicant learns how to substantiate skills. The design must support efficient bulk operations without turning keywords, identity or incomplete schooling into unsupported hiring conclusions.

The v0.1 deployment is explicitly one local operator, one process and a private SQLite database. It is not a public multi-tenant recruitment platform.

## Data flow

```text
Authorized document / professional export
    → bounded trusted parser → preserved private source + unreviewed proposals
    → human citation/quality review → validated structured professional claims
    → approved skill rubric → deterministic advisory coverage + review flags
    → queue / coaching / factual draft / source-linked report

Optional AI branch:
reviewed claims → canonical IDs + kinds/levels + temporary evidence IDs
    → consented provider → constrained action/citation validation → human-reviewed advice
```

Personal/free-form source content, applicant names, school chronology, contact details, actual record IDs and job description text do not cross the AI boundary. The caller chooses a server-configured provider; the browser cannot configure destinations or credentials.

## ADR-001: deterministic rank, AI-assisted coaching

Selected a reproducible reviewed-evidence rubric over opaque LLM scores or resume keyword counts. Evidence strengths are 1/2/3/4 for declared/practiced/demonstrated/assessed. For each criterion, take the strongest reviewed claim, divide by the target, cap at 1, multiply by its approved weight, sum, and divide by total weight. Multiply by 100. Missing evidence contributes zero *coverage* with clarification context, not an assertion of inability.

Alternatives: a model-only ranking is less auditable and harder to keep independent of protected information; keyword counts reward repetition and do not demonstrate quality. The chosen design requires deliberate human source review and does not automatically read/grade arbitrary portfolios. This trade-off is visible in the product rather than disguised as fully autonomous AI.

Required gaps and ambiguity are review flags, never automatic rejection. Equal scores share a competition rank; IDs stabilize display order only. Rubric fingerprints use only criteria, so irrelevant job-title changes do not alter the fingerprint.

## ADR-002: Python + TypeScript + SQL

Python provides mature document parsing, validated contracts and straightforward property tests. TypeScript gives maintainable browser contracts without a platform-specific IDE. React renders escaped text; raw sources never become HTML. SQLite gives atomic transactions and optimistic revisions without requiring a cloud account. HTML/CSS offers responsive presentation and printable downloads. JavaScript uses the TypeScript compiler AST for documentation checks.

A native Rust/C++ ranking core was not justified by the measured workload. The 10,000-record synthetic benchmark completes well below one second on the development machine. This is not a reason to add extra languages to every repository.

## ADR-003: preserve sources, constrain derived fields

Keep source text privately for verification and correction; standardized claims must cite a source. This avoids silently discarding context while keeping ranking inputs clean. Education outcomes use explicit status values. No inference is made from school names, dates, transferred credits or major changes. Verified employment duration is separate and does not enter scoring.

TXT/MD, DOCX and PDF are bounded and parsed as data in a trusted subprocess. No uploaded code, macro or embedded object is run. Scanned content is flagged. Windows uses a process timeout but lacks the Linux worker's hard memory cap; production Windows document processing needs an appropriate containment boundary.

## Complexity and capacity

Per applicant scoring is O(E+C) for E claims and C criteria. Ranking is O(N(E+C) + N log N); memory holds a local pool and its assessments. Queue filters run after ranking so displayed ranks retain the full-pool meaning. Duplicate claims do not accumulate points. Resume ordering is O(E log E). Best-evidence lookup uses a dictionary rather than repeated scans.

SQLite loads validated JSON records once per queue request. No N+1 source fetches or network requests occur in ranking. Jobs are small. This simple approach is bounded at 10,000 records, 150 claims, 30 sources and 200,000 combined source characters per record. Very large real records may use substantially more memory than the small synthetic benchmark. A production service should store/projection-query normalized evidence separately, cache assessments keyed by rubric/record revisions, and isolate document workers. Do not infer a production SLA from the microbenchmark.

## Extension contracts

Taxonomy changes are code-reviewed additions to professional skill IDs, with corresponding validation/privacy tests. They are not arbitrary user-supplied scoring text. New provider adapters must preserve payload minimization, consent, bounded output, redirect policy and citation validation. New parsers must preserve unknowns and have adversarial fixtures. No adapter may bypass source access restrictions.

Source headers and generated maps document lexical declarations and written variables with exact locations. They do not pretend to trace every dynamic value or attribute. Regenerate after formatting; CI checks map drift.
