# User guide

## Private accounts and desktop app (0.2)

See [installation and account help](install.md). Register an alias with a unique
login password, privately save the random recovery code, then choose a different
long vault phrase. New accounts start empty: add a role and authorized applicants,
or explicitly replace the workspace with fictional examples via Account & backups.
Lock or sign out when finished. Only ciphertext syncs; private mode does not make
external AI/profile requests. Save encrypted backups and protect plaintext exports.
Login recovery cannot recover the independent vault phrase.

The reviewer/coaching workflows below are shared with the earlier local mode.
In private accounts, ignore the old session-link instructions: use login/unlock.
The private workspace caps at 1,000 applicants and 100 jobs within an 8 MiB total
budget. GitHub fetching, optional external AI and the 10,000-record capacity below
apply only to the separate **legacy developer mode**, never the public service.
Accounts are individually isolated; reviewer/coaching views are not team roles.

## Reviewer workflow

In private mode, sign in and unlock. In legacy developer mode, open the session link from the launcher. The review queue initially hides names; selecting a record reveals its source-linked details. Search accepts ID/name, filters accept reviewed skills and evidence status. These do not change the rank in the full pool. Ties share a rank.

Select a role, then open **Job criteria**. Edit its title/description, skill weights (1–10), target strength and required flags. **Suggest draft criteria** recognizes professional terms and returns an editable draft; inspect relevance before **Save approved rubric**. Adding or duplicating a skill cannot bypass the closed schema. Required gaps trigger clarification, not automatic disqualification.

Choose **Applicant intake** and upload TXT/MD, DOCX or a text PDF up to 2 MB. Verify identity, authorization and all parser warnings. Scanned PDF pages may return no text. Unknown layouts and unsupported formats require a manual/authorized text export. The parser retains source text but proposes claims only for explicit `Skills:`, `Project:`, `Coursework:`, `Experience:` and `Work sample:` lines. Ordinary resumes may require manually adding claims. No parser output is a completed evidence review.

Save the draft, inspect its source text and original file, and add source-linked professional claims. Choose an evidence kind and assess your own contribution/quality against the rubric:

| Strength | Meaning |
| --- | --- |
| Declared | Skill is stated, quality not demonstrated. |
| Practiced | Relevant coursework/practice with a cited example. |
| Demonstrated | Reproducible artifact, explained contribution and relevant tests. |
| Assessed | Reviewer-checked work sample meets a documented assessment rubric. |

Check **I checked this claim against its source** only after review. Save the review. A course is not intrinsically weaker than paid work; use demonstrated quality, not employment status, as the evidence-strength basis. Do not boost copied/group work without checking contribution. Repeating the same skill does not accumulate points.

**Score breakdown & citations** shows each criterion's target coverage and weight. Download the advisory report for its reproducible rubric fingerprint and evidence references. Read the original resume and cited work before deciding who to contact or hire.

## Education, major changes and career transitions

Use **Edit education and transitions** to correct structured facts through explicit fields, then **Save education context**. Enter separate education records with `completed`, `in_progress`, `transferred`, `coursework_only` or `unclear`. A transfer record can include its destination and notes explaining a major change/credits. Do not mark a first school's degree completed just because it appears in the resume; do not mark it failed either. The app retains this chronology for review and flags uncertainty. The normalized JSON editor remains available for advanced record/consent changes.

`verified_employment_months` is optional. Enter only a duration that has been checked. Projects/coursework remain competency evidence, not an automatically generated employment-equivalent year count. Unknown dates remain unknown.

## Professional sources

Explicitly record source authorization before attaching professional text or importing a public GitHub README. Paste applicant-provided LinkedIn professional exports; include relevant project/contribution text rather than personal biography. The app does not bypass inaccessible profiles. A fetched README remains an unreviewed source; add justified claims after inspecting relevant code/tests yourself.

## Bulk operations

The examples folder provides a consistent JSON batch format and generated schemas. Import a maximum of 100 records per request, within the 3 MB request bound. Batches are atomic: any conflict rejects the entire import. The explicit replacement checkbox allows intentional ID replacement; revisions increment rather than resetting. Do not import the built-in example IDs twice unless intentionally replacing synthetic data. Each record must have unique source/evidence IDs and valid citations.

The local pool caps at 10,000 records. It is not designed for concurrent organizational users or unlimited storage. Split large batches, review retention and measure actual document-heavy workloads before expansion.

## Applicant coaching

Select an applicant and open **Applicant coaching**. Choose a role or enable general advice. Inspect resume/profile tips and job-gap portfolio demonstrations. Build authentic work, document your contribution, include tests and actual measured outcomes, and publish only what you can share.

Download the HTML resume draft. It reorders reviewed skills around the selected role, uses a simple printable layout, preserves education qualifiers and excludes unreviewed claims. It does not invent achievements, numbers, credentials, employment dates or contact details. Add/verify any appropriate contact information yourself. Open locally and print to PDF if needed.

Optional AI coaching requires server setup and explicit applicant/operator consent. The model sees structured professional metadata only. Its constrained suggestions require human verification. A missing/unreachable provider does not disable offline ranking/coaching.

Private mode isolates each signed-in account, but has no employer/applicant organization roles or sharing. Those views are workflow surfaces, not authorization roles. The legacy local developer application has no user accounts. Neither mode claims multi-user organizational access management.
