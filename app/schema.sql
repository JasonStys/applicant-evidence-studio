-- Local private storage. All user values are parameter-bound, never SQL fragments.
-- Tables: applicants/jobs hold validated JSON; events holds non-content audit metadata.
-- Locations: WAL setting@5; applicants@6 (id@7, body@7, revision@7, updated@8);
-- jobs@10 (id/body@10); events@11 (sequence/action/record_id@12, created@13).
PRAGMA journal_mode=WAL;
CREATE TABLE IF NOT EXISTS applicants (
    id TEXT PRIMARY KEY, body TEXT NOT NULL, revision INTEGER NOT NULL DEFAULT 1,
    updated TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS jobs (id TEXT PRIMARY KEY, body TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS events (
    sequence INTEGER PRIMARY KEY AUTOINCREMENT, action TEXT NOT NULL, record_id TEXT NOT NULL,
    created TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
