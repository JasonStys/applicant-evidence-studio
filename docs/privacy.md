# Privacy, security and human oversight

## Intended use

An advisory evidence-review aid and applicant coaching demonstration. Reviewers remain responsible for examining resumes and work samples, clarifying missing facts and making hiring decisions. The app has no hire/reject automation, candidate-contact automation or external hiring-system write integration. That boundary does not guarantee lawful or fair use.

## Input boundary

The scoring schema accepts only vetted professional skill IDs, evidence strength, reviewer confirmation and a job rubric. Name, race, gender, religion, disability, age, school prestige, home address, photographs, followers and social popularity are not scoring features. No sensitive trait is inferred. Coursework/projects can demonstrate the same competency as employment evidence, but are never converted into fictional employment years.

Raw documents may contain personal or sensitive information. They remain in private local source records for human verification, not model prompts or scoring inputs. Record IDs might be chosen by an operator and contain identity; the AI adapter therefore aliases them to temporary `e0`, `e1`, etc. It sends neither actual IDs nor applicant/job free text. Automated invariance tests check this boundary; they do not prove that all human rubrics or evidence judgments are unbiased.

## Consent and professional sources

Use applicant-supplied or explicitly authorized professional sources only. The GitHub adapter fetches a single exact public repository README through a fixed API hostname. It never follows a returned arbitrary download URL, runs code or builds a broad personal dossier. README claims are not proof of quality, authorship or contribution.

LinkedIn support is authorized professional text/export intake. There is no scraping, CAPTCHA/login bypass or claim that unavailable profiles were reviewed. When access fails, use an authorized export or ask the applicant; missing public profiles must not be treated as lack of skill.

AI calls require the record's AI consent and an explicit operator request. They are not triggered by upload, editing or page refresh. Provider setup is server-only, remote endpoints require HTTPS, redirects/proxy inheritance are disabled and streamed responses are capped. Review provider terms, retention and data locality before configuration. No live paid model calls or real applicant data were used in validation.

## Threat model and controls

| Risk | Control / remaining boundary |
| --- | --- |
| Unauthorized local HTTP access | Random 32+ character session token; private API authorization, explicit Host/Origin checks; loopback listener only. Other local processes can still be threats. |
| Credential/data exposure | No keys in browser configuration, no applicant browser caching, no access logs, no private-input echo in schema errors, gitignored runtime/exports. Local OS accounts/backup access still matter. |
| XSS/document markup | React renders source text; generated resume HTML escapes all facts. CSP denies remote script/object/frame content. |
| SQL injection/stale writes | Parameter-bound SQL, atomic batch transactions, compare-and-swap revisions. Database connections close deterministically. |
| Document bombs/active content | 2 MB upload cap; DOCX expansion/count/ratio limits; XML entity protection; no archive extraction/embedded execution; timed subprocess; Linux CPU/memory limits. Windows hard memory isolation is not implemented. |
| SSRF/profile probing | Exact authorized GitHub URL grammar and fixed API target; no arbitrary browser-controlled connector URL. AI endpoints are administrator environment settings, not public user input. |
| Model prompt injection/hallucination | No raw document/job-description prompts; schema-only canonical data; bounded output; known skill/action checks; matching citation checks; no unchecked free-form model decisions. |
| Wrong inference about education | Explicit outcomes/transfers, unknown flags, no degree or failure inference from dates/credits. Human verification is still required. |
| Rank overconfidence | Evidence coverage label, uncertainty flags, transparent weights/targets, ties and repeated human-review notices. This is not a validated job-performance prediction. |

## Retention and correction

Records are not uploaded automatically. Use a private data directory with appropriate OS permissions and encrypted storage. Export only to approved destinations. Correct records with source verification; optimistic revisions guard against stale edits. Deletion removes the selected record logically but is **not a secure wipe** of SQLite WAL, backups, browser downloads or storage media. Manage retention and backup disposal deliberately. Audit rows contain action/local-ID/time, not raw resume content; IDs may still identify a person and require protection.

## Before organizational hiring use

Obtain appropriate jurisdiction-specific review of hiring/privacy obligations, establish validated job-related rubrics, evaluate adverse outcomes and error rates, provide accessible alternatives/accommodations, add role-based authorization and tenant isolation, encrypt storage/transport, implement retention/access/deletion policies and correction/appeal paths, conduct penetration testing and real user/accessibility evaluation. Human review alone is not a substitute for these controls.
