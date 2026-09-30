# Local operations and AI setup

## Launch and data boundaries

Follow the README installation instructions, build the browser UI, seed a **new** synthetic data directory if desired, and run `applicant-studio serve --data runtime/demo --port 8014`. The session URL includes a random per-process token. Treat it as private. The launcher never binds to a public interface. Use another data directory for real authorized records; runtime storage and generated artifacts are ignored by Git.

The local application requires its Python service even on a mobile browser; it is not a standalone mobile package. Do not change the listener to a public host to obtain remote access. A production HTTPS gateway with appropriate identity/authorization and storage controls is a separate, reviewed deployment project.

## Optional model configuration

No model is bundled or silently downloaded. Ranking, templates and downloads work without a model. The following settings belong to the trusted server environment, not a browser form or a committed `.env` file:

| Setting | Meaning |
| --- | --- |
| `AES_AI_KIND` | `ollama` (default) or `compatible` for a chat-completions-shaped API. |
| `AES_AI_URL` | Full chat endpoint. Default is `http://127.0.0.1:11434/api/chat`. Remote endpoints require HTTPS. No URL credentials/query/fragment. |
| `AES_AI_MODEL` | Explicit model ID. Empty means AI is unconfigured, not a mocked real model. |
| `AES_AI_KEY` | Optional server-only bearer key. Never enter it in applicant records, job text or Git. |
| `AES_SESSION_TOKEN` | Optional strong local session token (32+ characters); normally generated per process. Use a secret, not the synthetic test token. |
| `AES_TEST_PORT` | Browser-test-only port override (default 8015), separate from the user preview. |

For an already installed local Ollama model, set `AES_AI_MODEL` to its actual name and restart this app process. Do not assume any model is installed. For a compatible hosted API, set the kind, full HTTPS endpoint, model and key in a private environment. Some APIs differ in request/response schema and need a reviewed adapter; “compatible” does not mean every API automatically works.

The user must enable applicant AI consent, save it and explicitly request coaching. The payload contains canonical skill IDs, target/weight/required flags and reviewed evidence kind/level, with temporary IDs. It has no resume text or personal/profile text. The model returns JSON suggestions choosing approved action codes and matching evidence references. Free-form scores/claims, fabricated citations and unsupported actions are rejected. Suggestions are not persisted automatically and require human verification. No adapter calls tools or executes model-generated code.

Timeouts are 5 seconds for connection and 30 seconds for AI network operations; output is capped at 250 KB. These are HTTP operation bounds, not a guaranteed global deadline against a malicious trickle server. Only configure trusted endpoints. Verify provider pricing/privacy/retention before calls; this application does not enforce a monetary spending budget.

## Storage and recovery

SQLite uses parameterized queries and WAL. Connections close after each operation. Back up the private database using SQLite's backup API or while the application is stopped; copying only a live main file while omitting WAL can lose recent data. Keep backups encrypted and access-controlled. A restore should use a **new** private directory and the stopped application's matching version; validate record counts, source references and a representative queue before adopting it.

Keep runtime/exports out of source control. Logical record deletion is available through the authenticated API, not a bulk automatic purge; it does not wipe backups/WAL or downloaded drafts. Establish an appropriate retention policy separately. Audit metadata includes local record IDs, actions and timestamps; protect it because an ID may identify a person.

Optimistic edits reject stale revisions. On a “record changed” response, reload the record, compare changes and deliberately reapply corrections. Bulk imports roll back on conflicts; the explicit replacement option is an upsert, not an append-only history system. Full versioned applicant histories are not implemented in v0.1.

## Troubleshooting

| Symptom | Action |
| --- | --- |
| Authorization error | Open the current launcher session link or enter its current token. Restarting the app changes generated tokens. |
| Untrusted Host/Origin | Use the exact printed `127.0.0.1:port` origin, not another hostname/port or cross-origin page. |
| Blank/no-text PDF | Provide an authorized OCR/text export, inspect original visual content and add reviewed claims manually. |
| No skill proposals | Explicit section prefixes are required. Add professional claims manually rather than pretending arbitrary NLP extraction succeeded. |
| Duplicate ID import | Choose a new ID or explicitly authorize replacement; no partial batch was committed. |
| AI setup/validation error | Check consent/model/endpoint protocol and model JSON support. Invalid citations/actions fail closed. Offline review remains available. |
| GitHub unavailable/rate limited | Retry later or paste an applicant-authorized professional export. No access controls are bypassed. |
| Browser tests cannot create Firefox pages locally | A Windows restricted-process context can fail before app loading. Use an unrestricted trusted test process or the Linux Actions browser job; never mark a runtime failure as a passed app test. |
| Map drift after editing | Format first, then run Python/TypeScript map generators and their checks. Maps contain lexical declarations/variables, not all dynamic values. |

## Safe updates and rollback

Back up private data, run all checks and review dependency/behavior changes before updating. The schema is additive in this version; repeated initialization preserves data. Roll back application source/build and use a validated backup in a separate directory if a migration or evidence-boundary regression occurs. Keep the last working data directory until the replacement is verified. A broken ranking boundary, private-data leak, failed core workflow or incorrect record update is a stop-use trigger, not something to suppress for a green dashboard.
