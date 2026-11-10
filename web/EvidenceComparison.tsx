// Purpose: explicit two-record human review with citations, clarification prompts and private export.
// File: EvidenceComparison.tsx. Author: Jason Stys. Variables: reports/observations remain transient browser state.
// Index: useEffect@4, useRef@4, useState@4, api@5, ComparisonCapture@6, ComparisonReport@6, buildComparison@6, fingerprint@7, saveFile@8, Job@9, EvidenceComparison@12, ids@13, job@14, busy@15, onOpen@16, id@21, binding@23, capture@24, setCapture@24, loading@25, setLoading@25, error@26, setError@26, observations@27, setObservations@27, epoch@28, report@29, compare@42, ticket@44, input@50, index@55, row@55, next@59, reason@61, exportReport@70, row@74, row@102, criterion@110, index@110, record@119, row@120, i@135, warning@135, record@161, flag@177, question@185, event@206
import { useEffect, useRef, useState } from 'react';
import { api } from './api';
import { buildComparison, type ComparisonCapture, type ComparisonReport } from './comparison';
import { fingerprint } from './private-domain';
import { saveFile } from './vault';
import type { Job } from './types';

/** Discard comparisons across changed selection/rubric, mutations, locks or stale async completion. */
export default function EvidenceComparison({
  ids,
  job,
  busy,
  onOpen,
}: {
  ids: string[];
  job: Job | undefined;
  busy: boolean;
  onOpen: (id: string) => void;
}) {
  const binding = JSON.stringify({ ids, job });
  const [capture, setCapture] = useState<{ binding: string; report: ComparisonReport } | null>(null);
  const [loading, setLoading] = useState(false),
    [error, setError] = useState(''),
    [observations, setObservations] = useState('');
  const epoch = useRef(0);
  const report = capture?.binding === binding && !busy ? capture.report : null;
  useEffect(() => {
    epoch.current++;
    setCapture(null);
    setError('');
    setLoading(false);
    setObservations('');
    return () => {
      epoch.current++;
    };
  }, [binding, busy]);

  /** Private mode dispatches wholly within the unlocked browser; developer mode reads an SQL snapshot. */
  async function compare() {
    if (!job || ids.length !== 2 || busy || loading) return;
    const ticket = ++epoch.current;
    setLoading(true);
    setCapture(null);
    setError('');
    setObservations('');
    try {
      const input = await api<ComparisonCapture>(
        'comparison?' + new URLSearchParams({ job_id: job.id, left: ids[0], right: ids[1] }),
      );
      if (
        input.job.id !== job.id ||
        input.applicants.some((row, index) => row.applicant.id !== ids[index]) ||
        (await fingerprint(input.job)) !== (await fingerprint(job))
      )
        throw new Error('Records or rubric changed; reload your selection before comparing.');
      const next = await buildComparison(input);
      if (ticket === epoch.current) setCapture({ binding, report: next });
    } catch (reason) {
      if (ticket === epoch.current)
        setError(reason instanceof Error ? reason.message : 'Comparison unavailable.');
    } finally {
      if (ticket === epoch.current) setLoading(false);
    }
  }

  /** Export the displayed snapshot/observations without another request or a database mutation. */
  function exportReport() {
    if (!report || busy || loading) return;
    saveFile(
      JSON.stringify({ ...report, reviewer_observations: observations.slice(0, 2000) }, null, 2),
      `evidence-comparison-${report.records.map((row) => row.id).join('-')}.json`,
    );
  }

  return (
    <section className="card comparison-card" aria-labelledby="comparison-heading">
      <h2 id="comparison-heading">Criterion evidence comparison</h2>
      <p>
        Selected record IDs: {ids.join(', ') || 'none'}. Choose exactly two records in the queue. Selection
        order is preserved; this view does not choose a winner.
      </p>
      <button onClick={() => void compare()} disabled={ids.length !== 2 || !job || busy || loading}>
        {loading ? 'Capturing evidence…' : 'Capture selected evidence'}
      </button>
      {error && <p role="alert">{error}</p>}
      {report && (
        <>
          <p>
            Captured <time dateTime={report.captured_at}>{report.captured_at}</time> for {report.rubric.title}
            ; rubric fingerprint <code>{report.rubric.hash}</code>. Refresh the capture after edits.
          </p>
          <p>{report.notice}</p>
          <div className="table-wrap" role="region" aria-label="Scrollable criterion comparison" tabIndex={0}>
            <table>
              <caption>Reviewed evidence against the same captured rubric</caption>
              <thead>
                <tr>
                  <th scope="col">Criterion</th>
                  {report.records.map((row) => (
                    <th scope="col" key={row.id}>
                      {row.id}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {report.rubric.criteria.map((criterion, index) => (
                  <tr key={criterion.skill}>
                    <th scope="row">
                      {report.records[0].criteria[index].label}
                      <small>
                        Target {criterion.target}; weight {criterion.weight};{' '}
                        {criterion.required ? 'required evidence' : 'optional evidence'}
                      </small>
                    </th>
                    {report.records.map((record) => {
                      const row = record.criteria[index];
                      return (
                        <td key={record.id}>
                          <strong>{Math.round(row.attainment * 100)}% target coverage</strong>
                          {row.best_support ? (
                            <>
                              <p>
                                {row.best_support.level} · {row.best_support.kind.replaceAll('_', ' ')}
                              </p>
                              <p>{row.best_support.summary}</p>
                              <p>
                                Evidence {row.best_support.evidence_id}; source {row.best_support.source.id}:{' '}
                                {row.best_support.source.label}; location{' '}
                                {row.best_support.locator || 'not supplied — verify original'}.
                              </p>
                              {row.best_support.source.warnings.map((warning, i) => (
                                <p className="review-flag" key={i}>
                                  Source warning: {warning}
                                </p>
                              ))}
                            </>
                          ) : (
                            <p>Not yet evidenced. Ability remains unknown.</p>
                          )}
                          <small>
                            {row.other_reviewed_claims} other reviewed claims; {row.unreviewed_claims}{' '}
                            unreviewed claims excluded. Duplicates do not increase coverage.
                          </small>
                        </td>
                      );
                    })}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <p>
            Opening an original record clears this comparison and its observations. Download first if you want
            to keep them.
          </p>
          <div className="comparison-context">
            {report.records.map((record) => (
              <section key={record.id} aria-label={`Review context ${record.id}`}>
                <h3>
                  {record.id} · {record.score}% recorded evidence coverage
                </h3>
                <p>
                  Record revision {record.revision}; review state {record.review_status.replaceAll('_', ' ')}.
                </p>
                <details>
                  <summary>Captured record fingerprint</summary>
                  <code>{record.record_sha256}</code>
                  <p>
                    Fingerprint identifies this private snapshot, including omitted fields. It is not a
                    ranking input or anonymization.
                  </p>
                </details>
                {record.flags.map((flag) => (
                  <p className="review-flag" key={flag}>
                    {flag}
                  </p>
                ))}
                <h4>Clarifications to consider</h4>
                {record.clarifications.length ? (
                  <ul>
                    {record.clarifications.map((question) => (
                      <li key={question}>{question}</li>
                    ))}
                  </ul>
                ) : (
                  <p>
                    No rule-based clarification prompts. This is not independent verification or hiring
                    approval.
                  </p>
                )}
                <button className="secondary" onClick={() => onOpen(record.id)} disabled={busy}>
                  Open original record {record.id}
                </button>
              </section>
            ))}
          </div>
          <label>
            Human review observations (optional, private export only)
            <textarea
              maxLength={2000}
              value={observations}
              onChange={(event) => setObservations(event.target.value)}
            />
          </label>
          <p>
            Observations are transient until downloaded; they do not change records, rankings or account data.
            JSON is unencrypted and may contain personal evidence: keep it private.
          </p>
          <button className="secondary" onClick={exportReport}>
            Download private comparison JSON
          </button>
        </>
      )}
    </section>
  );
}
