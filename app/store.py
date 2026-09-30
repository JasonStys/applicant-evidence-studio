"""Transactional SQLite persistence, bounded batches and optimistic edit protection.

Source content stays local. Audit metadata intentionally excludes resume text.
"""

# Index: sqlite3@7, contextmanager@8, Path@9, Applicant@11, Job@11, Store@14, Store.__init__@17, Store.__init__.path@17, Store.__init__.self@17, Store.__init__.connection@21, Store.connect@25, Store.connect.self@25, Store.connect.connection@27, Store.applicants@34, Store.applicants.self@34, Store.applicants.connection@36, Store.applicants.row@39, Store.applicant@42, Store.applicant.identifier@42, Store.applicant.self@42, Store.applicant.connection@44, Store.applicant.row@45, Store.save_applicant@52, Store.save_applicant.applicant@52, Store.save_applicant.revision@52, Store.save_applicant.self@52, Store.save_applicant.connection@54, Store.save_applicant.cursor@55, Store.import_applicants@63, Store.import_applicants.applicants@63, Store.import_applicants.replace@63, Store.import_applicants.self@63, Store.import_applicants.applicant@65, Store.import_applicants.identifiers@65, Store.import_applicants.connection@68, Store.import_applicants.count@70, Store.import_applicants.existing@71, Store.import_applicants.row@71, Store.import_applicants.applicant@74, Store.delete@85, Store.delete.identifier@85, Store.delete.self@85, Store.delete.connection@87, Store.delete.cursor@88, Store.save_job@93, Store.save_job.job@93, Store.save_job.self@93, Store.save_job.connection@95, Store.jobs@102, Store.jobs.self@102, Store.jobs.connection@104, Store.jobs.row@107, Store.job@110, Store.job.identifier@110, Store.job.self@110, Store.job.job@112
import sqlite3
from contextlib import contextmanager
from pathlib import Path

from app.models import Applicant, Job


class Store:
    """Open short-lived database connections; parameter-bind every caller value."""

    def __init__(self, path: Path):
        """Create only the selected data directory and initialize additive schema."""
        self.path = path
        path.parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as connection:
            connection.executescript(Path(__file__).with_name("schema.sql").read_text(encoding="utf-8"))

    @contextmanager
    def connect(self):
        """Return a context-managed connection with a bounded lock wait."""
        connection = sqlite3.connect(self.path, timeout=5)
        try:
            with connection:
                yield connection
        finally:
            connection.close()

    def applicants(self) -> list[Applicant]:
        """Load validated records for a bounded local ranking; never cache private text in browsers."""
        with self.connect() as connection:
            return [
                Applicant.model_validate_json(row[0])
                for row in connection.execute("SELECT body FROM applicants ORDER BY id")
            ]

    def applicant(self, identifier: str) -> tuple[Applicant, int]:
        """Fetch a single record and its revision, or fail explicitly."""
        with self.connect() as connection:
            row = connection.execute(
                "SELECT body,revision FROM applicants WHERE id=?", (identifier,)
            ).fetchone()
        if not row:
            raise KeyError(identifier)
        return Applicant.model_validate_json(row[0]), row[1]

    def save_applicant(self, applicant: Applicant, revision: int):
        """Compare-and-swap a reviewed record; stale editors cannot overwrite newer work."""
        with self.connect() as connection:
            cursor = connection.execute(
                "UPDATE applicants SET body=?,revision=revision+1,updated=CURRENT_TIMESTAMP WHERE id=? AND revision=?",
                (applicant.model_dump_json(), applicant.id, revision),
            )
            if cursor.rowcount != 1:
                raise ValueError("Record changed or disappeared; reload before editing")
            connection.execute("INSERT INTO events(action,record_id) VALUES('update',?)", (applicant.id,))

    def import_applicants(self, applicants: list[Applicant], replace: bool = False):
        """Atomically import unique records; replacement is explicit and revision-preserving."""
        identifiers = [applicant.id for applicant in applicants]
        if len(identifiers) != len(set(identifiers)):
            raise ValueError("Duplicate applicant IDs in batch")
        with self.connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            count = connection.execute("SELECT COUNT(*) FROM applicants").fetchone()[0]
            existing = {row[0] for row in connection.execute("SELECT id FROM applicants")}
            if count + len(set(identifiers) - existing) > 10000:
                raise ValueError("Local capacity is 10,000 records; archive/export before importing more")
            for applicant in applicants:
                if not replace and applicant.id in existing:
                    raise ValueError(
                        "An applicant ID already exists; choose explicit replacement or a new ID"
                    )
                connection.execute(
                    "INSERT INTO applicants(id,body) VALUES(?,?) ON CONFLICT(id) DO UPDATE SET body=excluded.body,revision=applicants.revision+1,updated=CURRENT_TIMESTAMP",
                    (applicant.id, applicant.model_dump_json()),
                )
                connection.execute("INSERT INTO events(action,record_id) VALUES('import',?)", (applicant.id,))

    def delete(self, identifier: str):
        """Explicitly remove one applicant; WAL/filesystem erasure is not a secure wipe."""
        with self.connect() as connection:
            cursor = connection.execute("DELETE FROM applicants WHERE id=?", (identifier,))
            if not cursor.rowcount:
                raise KeyError(identifier)
            connection.execute("INSERT INTO events(action,record_id) VALUES('delete',?)", (identifier,))

    def save_job(self, job: Job):
        """Upsert a validated taxonomy-only rubric and record a metadata audit event."""
        with self.connect() as connection:
            connection.execute(
                "INSERT INTO jobs(id,body) VALUES(?,?) ON CONFLICT(id) DO UPDATE SET body=excluded.body",
                (job.id, job.model_dump_json()),
            )
            connection.execute("INSERT INTO events(action,record_id) VALUES('job',?)", (job.id,))

    def jobs(self) -> list[Job]:
        """List job configurations in deterministic order."""
        with self.connect() as connection:
            return [
                Job.model_validate_json(row[0])
                for row in connection.execute("SELECT body FROM jobs ORDER BY id")
            ]

    def job(self, identifier: str) -> Job:
        """Resolve a job explicitly; missing jobs never silently change a rubric."""
        for job in self.jobs():
            if job.id == identifier:
                return job
        raise KeyError(identifier)
