// Purpose: reviewer queue, source-linked records, rubric editor, private intake and applicant coaching.
// Variables hold explicit user state; rankings remain server-calculated and no hiring actions are offered.
// Index: useEffect@4, useState@4, api@5, authorize@5, download@5, encode@5, EducationEditor@6, isPrivateWorkspace@7, AIResult@9, Applicant@10, Assessment@11, Coaching@12, Config@13, Criterion@14, Evidence@15, Job@16, Level@17, Queue@18, Source@19, levels@22, explanations@23, emptyApplicant@29, viewNames@41, View@48, LevelSelect@51, value@52, onChange@53, label@54, value@57, event@63, level@64, App@75, config@76, setConfig@76, jobs@77, setJobs@77, jobId@78, setJobId@78, setView@79, view@79, queue@80, setQueue@80, search@81, setSearch@81, setSkill@82, skill@82, setStatus@83, status@83, offset@84, setOffset@84, record@85, setRecord@85, revision@86, setRevision@86, selected@87, setSelected@87, error@88, setError@88, message@89, setMessage@89, busy@90, setBusy@90, access@91, setAccess@91, editJob@92, setEditJob@92, coaching@93, setCoaching@93, general@94, setGeneral@94, ai@95, setAI@95, draft@96, setDraft@96, raw@97, setRaw@97, replace@98, setReplace@98, recordJSON@99, setRecordJSON@99, setSourceText@100, sourceText@100, setSourceKind@101, sourceKind@101, repoURL@102, setRepoURL@102, newSkill@103, setNewSkill@103, newSummary@104, setNewSummary@104, newSource@105, setNewSource@105, newKind@106, setNewKind@106, current@107, job@107, item@108, selectedAssessment@108, run@111, task@111, problem@117, initialize@124, settings@125, roles@126, job@129, loadQueue@132, identifier@141, select@141, data@142, active@157, value@162, problem@165, active@177, value@180, problem@183, saveRecord@193, value@193, file@200, intake@200, result@202, attachSource@228, source@228, event@240, index@254, key@254, label@254, event@297, job@303, event@337, event@387, event@398, key@404, label@404, event@415, item@438, flag@524, criterion@535, education@560, index@560, evidence@600, index@600, value@613, item@616, position@616, event@627, item@630, position@630, source@643, warning@648, event@662, key@663, label@663, event@672, source@673, event@684, kind@687, event@701, event@737, event@749, event@761, event@785, result@794, education@815, event@824, event@849, event@885, file@886, event@898, event@906, event@913, warning@917, event@955, event@966, file@967, event@980, value@988, result@989, event@1036, event@1043, event@1052, result@1060, criterion@1073, index@1073, event@1079, item@1082, position@1082, key@1088, label@1088, event@1102, item@1105, position@1105, target@1115, item@1118, position@1118, event@1128, item@1131, position@1131, _@1145, position@1145, next@1158, criterion@1159, key@1159, level@1190, event@1217, advice@1245, advice@1251, project@1259, step@1263, event@1289, index@1318, suggestion@1318
import { useEffect, useState } from 'react';
import { api, authorize, download, encode } from './api';
import EducationEditor from './EducationEditor';
import { isPrivateWorkspace } from './private-domain';
import type {
  AIResult,
  Applicant,
  Assessment,
  Coaching,
  Config,
  Criterion,
  Evidence,
  Job,
  Level,
  Queue,
  Source,
} from './types';

const levels: Level[] = ['declared', 'practiced', 'demonstrated', 'assessed'];
const explanations: Record<Level, string> = {
  declared: 'A stated skill; quality not demonstrated.',
  practiced: 'Relevant coursework or practice with a cited example.',
  demonstrated: 'A reproducible artifact with explained contribution and tests.',
  assessed: 'A reviewer-checked work sample meets a documented rubric.',
};
const emptyApplicant: Applicant = {
  id: '',
  display_name: '',
  consent_sources: false,
  consent_ai: false,
  sources: [],
  evidence: [],
  education: [],
  verified_employment_months: null,
  notes: '',
  review_status: 'pending',
};
const viewNames = {
  queue: 'Review queue',
  intake: 'Applicant intake',
  jobs: 'Job criteria',
  coach: 'Applicant coaching',
  guide: 'Method & privacy',
};
type View = keyof typeof viewNames;

/** Render a simple level picker with explicit, evidence-based meanings. */
function LevelSelect({
  value,
  onChange,
  label,
}: {
  value: Level;
  onChange: (value: Level) => void;
  label: string;
}) {
  return (
    <label>
      {label}
      <select value={value} onChange={(event) => onChange(event.target.value as Level)}>
        {levels.map((level) => (
          <option key={level} value={level}>
            {level}
          </option>
        ))}
      </select>
    </label>
  );
}

/** Coordinate user-initiated tasks, safe errors and the current local review workspace. */
export default function App() {
  const [config, setConfig] = useState<Config | null>(null),
    [jobs, setJobs] = useState<Job[]>([]),
    [jobId, setJobId] = useState('software');
  const [view, setView] = useState<View>('queue'),
    [queue, setQueue] = useState<Queue | null>(null),
    [search, setSearch] = useState(''),
    [skill, setSkill] = useState(''),
    [status, setStatus] = useState(''),
    [offset, setOffset] = useState(0);
  const [record, setRecord] = useState<Applicant | null>(null),
    [revision, setRevision] = useState(1),
    [selected, setSelected] = useState('');
  const [error, setError] = useState(''),
    [message, setMessage] = useState(''),
    [busy, setBusy] = useState(false),
    [access, setAccess] = useState('');
  const [editJob, setEditJob] = useState<Job | null>(null),
    [coaching, setCoaching] = useState<Coaching | null>(null),
    [general, setGeneral] = useState(false),
    [ai, setAI] = useState<AIResult | null>(null);
  const [draft, setDraft] = useState<Applicant>({ ...emptyApplicant }),
    [raw, setRaw] = useState(''),
    [replace, setReplace] = useState(false),
    [recordJSON, setRecordJSON] = useState('');
  const [sourceText, setSourceText] = useState(''),
    [sourceKind, setSourceKind] = useState<Source['kind']>('linkedin'),
    [repoURL, setRepoURL] = useState('');
  const [newSkill, setNewSkill] = useState('python'),
    [newSummary, setNewSummary] = useState(''),
    [newSource, setNewSource] = useState(''),
    [newKind, setNewKind] = useState<Evidence['kind']>('project');
  const current = jobs.find((job) => job.id === jobId);
  const selectedAssessment = queue?.items.find((item) => item.applicant_id === selected);

  /** Wrap explicit user actions; do not call external providers in background effects. */
  async function run(task: () => Promise<void>) {
    setError('');
    setMessage('');
    setBusy(true);
    try {
      await task();
    } catch (problem) {
      setError(problem instanceof Error ? problem.message : 'Operation failed.');
    } finally {
      setBusy(false);
    }
  }
  /** Load only configuration and rubrics; choosing another role never rewrites evidence. */
  async function initialize() {
    const settings = await api<Config>('config');
    const roles = await api<Job[]>('jobs');
    setConfig(settings);
    setJobs(roles);
    if (roles.length && !roles.some((job) => job.id === jobId)) setJobId(roles[0].id);
  }
  /** Reload a filtered page from the server without locally inventing scores. */
  async function loadQueue() {
    if (!jobId) return;
    setQueue(
      await api<Queue>(
        'queue?' + new URLSearchParams({ job_id: jobId, q: search, skill, status, offset: String(offset) }),
      ),
    );
  }
  /** Load a selected record and its optimistic-lock version, clearing stale AI advice. */
  async function select(identifier: string) {
    const data = await api<{ applicant: Applicant; revision: number }>(
      'applicants/' + encodeURIComponent(identifier),
    );
    setRecord(data.applicant);
    setRevision(data.revision);
    setSelected(identifier);
    setRecordJSON(JSON.stringify(data.applicant, null, 2));
    setAI(null);
    setCoaching(null);
    setNewSource(data.applicant.sources[0]?.id || '');
  }
  useEffect(() => {
    void run(initialize);
  }, []);
  useEffect(() => {
    let active = true;
    if (config && jobId) {
      api<Queue>(
        'queue?' + new URLSearchParams({ job_id: jobId, q: search, skill, status, offset: String(offset) }),
      )
        .then((value) => {
          if (active) setQueue(value);
        })
        .catch((problem) => {
          if (active) setError(String(problem.message));
        });
    }
    return () => {
      active = false;
    };
  }, [config, jobId, search, skill, status, offset]);
  useEffect(() => {
    setEditJob(current ? structuredClone(current) : null);
  }, [current]);
  useEffect(() => {
    let active = true;
    if (selected && view === 'coach') {
      api<Coaching>('coach/' + selected + (general ? '' : '?job_id=' + jobId))
        .then((value) => {
          if (active) setCoaching(value);
        })
        .catch((problem) => {
          if (active) setError(problem.message);
        });
    }
    return () => {
      active = false;
    };
  }, [selected, view, jobId, general]);

  /** Save a full reviewed record, then reload both its revision and advisory queue. */
  async function saveRecord(value: Applicant) {
    await api('applicants/' + value.id, 'PUT', { applicant: value, revision });
    await select(value.id);
    await loadQueue();
    setMessage('Record saved. Advisory scores recalculated from reviewed evidence.');
  }
  /** Import one resume into an editable, unreviewed draft; no qualifications are inferred. */
  async function intake(file: File) {
    setDraft({ ...emptyApplicant });
    const result = await api<{ text: string; warnings: string[]; proposals: Evidence[]; filename: string }>(
      'ingest',
      'POST',
      { filename: file.name, content: await encode(file) },
    );
    setDraft({
      ...emptyApplicant,
      id: 'candidate_' + crypto.randomUUID().slice(0, 8),
      display_name: '',
      sources: [
        {
          id: 'resume',
          kind: 'resume',
          label: result.filename,
          text: result.text,
          url: '',
          warnings: result.warnings,
        },
      ],
      evidence: result.proposals,
    });
    setMessage(
      'Text extracted. Verify the source, applicant identity and claims before saving. Proposed claims are unreviewed.',
    );
  }
  /** Attach explicitly authorized professional text; free text never enters scoring or AI prompts. */
  async function attachSource(source: Source) {
    if (!record) return;
    await saveRecord({ ...record, sources: [...record.sources, source] });
    setSourceText('');
  }

  return (
    <div className="shell">
      <aside className="sidebar">
        <a
          className="brand"
          href="#"
          onClick={(event) => {
            event.preventDefault();
            setView('queue');
          }}
        >
          <img src="/icon.svg" alt="" />
          <span>
            Applicant
            <br />
            Evidence Studio
          </span>
        </a>
        <div className="workspace-label">LOCAL REVIEW WORKSPACE</div>
        <nav aria-label="Workspace">
          {Object.entries(viewNames).map(([key, label], index) => (
            <button
              key={key}
              className={view === key ? 'nav active' : 'nav'}
              aria-current={view === key ? 'page' : undefined}
              onClick={() => setView(key as View)}
            >
              <span aria-hidden="true" className="nav-number">
                0{index + 1}
              </span>
              {label}
            </button>
          ))}
        </nav>
        <div className="sidebar-note">
          <span className="live-dot" /> Human-led review
          <p>
            Evidence helps you prioritize.
            <br />
            People make the decisions.
          </p>
        </div>
        <small>
          v0.2 · Created by{' '}
          <a href="https://github.com/JasonStys" rel="noreferrer">
            Jason Stys
          </a>
          <br />
          <a href="https://www.linkedin.com/in/jason-stys-31b30b351/" rel="noreferrer">
            Contact & profile
          </a>
        </small>
      </aside>
      <main>
        <header className="topbar">
          <div>
            <div className="eyebrow">PROFESSIONAL EVIDENCE, IN CONTEXT</div>
            <h1>{viewNames[view]}</h1>
          </div>
          <label className="role-picker">
            Selected role
            <select
              value={jobId}
              onChange={(event) => {
                setJobId(event.target.value);
                setOffset(0);
                setAI(null);
              }}
            >
              {jobs.map((job) => (
                <option key={job.id} value={job.id}>
                  {job.title}
                </option>
              ))}
            </select>
          </label>
        </header>
        <div className="advisory">
          <span className="tag">ADVISORY</span>
          <p>
            {config?.notice ||
              'Review original applications and cited work. This tool does not hire or reject applicants.'}
          </p>
        </div>
        {error && (
          <div role="alert" className="error">
            {error}
          </div>
        )}
        {message && (
          <div role="status" className="success">
            {message}
          </div>
        )}
        {!config && (
          <section className="card">
            <h2>Authorize this local session</h2>
            <p>
              Use the session link printed by the launcher, or enter its session token. No applicant data is
              stored in browser storage.
            </p>
            <label>
              Session token
              <input type="password" value={access} onChange={(event) => setAccess(event.target.value)} />
            </label>
            <button
              onClick={() =>
                void run(async () => {
                  authorize(access);
                  setAccess('');
                  await initialize();
                })
              }
            >
              Connect
            </button>
          </section>
        )}
        {config && view === 'queue' && (
          <>
            <section className="stats" aria-label="Queue overview">
              <div>
                <span>APPLICANTS IN POOL</span>
                <strong>{queue?.pool_total ?? '—'}</strong>
                <small>Local, source-linked records</small>
              </div>
              <div>
                <span>VISIBLE MATCHES</span>
                <strong>{queue?.total ?? '—'}</strong>
                <small>After your search and filters</small>
              </div>
              <div>
                <span>RUBRIC</span>
                <strong>
                  {current?.criteria.length ?? 0} <em>skills</em>
                </strong>
                <small>No identity-based scoring</small>
              </div>
            </section>
            <div className="review-grid">
              <section className="card queue-card">
                <div className="section-head">
                  <div>
                    <h2>Evidence-ranked queue</h2>
                    <p>Highest rubric coverage first. Ties share a rank.</p>
                  </div>
                  <span className="subtle">Names hidden in queue</span>
                </div>
                <div className="filters">
                  <label>
                    Search applicant ID or name
                    <input
                      value={search}
                      onChange={(event) => {
                        setSearch(event.target.value);
                        setOffset(0);
                      }}
                      placeholder="Search records…"
                    />
                  </label>
                  <label>
                    Reviewed skill
                    <select
                      value={skill}
                      onChange={(event) => {
                        setSkill(event.target.value);
                        setOffset(0);
                      }}
                    >
                      <option value="">All skills</option>
                      {Object.entries(config.skills).map(([key, label]) => (
                        <option key={key} value={key}>
                          {label}
                        </option>
                      ))}
                    </select>
                  </label>
                  <label>
                    Evidence status
                    <select
                      value={status}
                      onChange={(event) => {
                        setStatus(event.target.value);
                        setOffset(0);
                      }}
                    >
                      <option value="">All statuses</option>
                      <option value="needs_review">Needs human review</option>
                      <option value="strong_evidence">Strong evidence</option>
                      <option value="partial_evidence">Partial evidence</option>
                    </select>
                  </label>
                </div>
                <div className="table-wrap">
                  <table>
                    <thead>
                      <tr>
                        <th scope="col">Rank / ID</th>
                        <th scope="col">Coverage</th>
                        <th scope="col">Review context</th>
                        <th scope="col">Open</th>
                      </tr>
                    </thead>
                    <tbody>
                      {queue?.items.map((item) => (
                        <tr
                          key={item.applicant_id}
                          className={selected === item.applicant_id ? 'selected' : ''}
                        >
                          <td>
                            <span className="rank">{item.rank}</span>
                            <strong>{item.applicant_id}</strong>
                          </td>
                          <td>
                            <strong>{item.score}%</strong>
                            <div className="bar" aria-hidden="true">
                              <i style={{ width: item.score + '%' }} />
                            </div>
                          </td>
                          <td>
                            <span className={'pill ' + item.status}>{item.status.replaceAll('_', ' ')}</span>
                            <small>{item.required_gaps.length} required evidence gaps</small>
                          </td>
                          <td>
                            <button
                              className="secondary compact"
                              aria-label={'Review ' + item.applicant_id}
                              onClick={() => void run(() => select(item.applicant_id))}
                            >
                              Review →
                            </button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                  {queue?.items.length === 0 && (
                    <p className="empty">
                      No matching records. Clear filters or import authorized applicants.
                    </p>
                  )}
                </div>
                <div className="pagination">
                  <button
                    className="secondary"
                    disabled={offset === 0}
                    onClick={() => setOffset(Math.max(0, offset - 25))}
                  >
                    Previous
                  </button>
                  <span>
                    {offset + 1}–{Math.min(offset + 25, queue?.total ?? 0)} of {queue?.total ?? 0}
                  </span>
                  <button
                    className="secondary"
                    disabled={offset + 25 >= (queue?.total ?? 0)}
                    onClick={() => setOffset(offset + 25)}
                  >
                    Next
                  </button>
                </div>
              </section>
              <section className={record ? 'card context-card has-record' : 'card context-card'}>
                <div className="eyebrow">SELECTED RECORD</div>
                <h2>{record?.id || 'Look past the keyword list'}</h2>
                {!record ? (
                  <>
                    <p>
                      Select an applicant to inspect skill evidence, transfer context and original source
                      text.
                    </p>
                    <div className="illustration" aria-hidden="true">
                      <span>source</span>
                      <i>→</i>
                      <span>evidence</span>
                      <i>→</i>
                      <span>review</span>
                    </div>
                    <p className="muted">No missing evidence is treated as proof of inability.</p>
                  </>
                ) : (
                  <>
                    <p>{record.display_name}</p>
                    <p className="muted">Identity is displayed for review, never used in the score.</p>
                    {selectedAssessment && (
                      <>
                        <div className="big-score">
                          {selectedAssessment.score}
                          <span>/100 coverage</span>
                        </div>
                        {selectedAssessment.flags.map((flag) => (
                          <p className="review-flag" key={flag}>
                            {flag}
                          </p>
                        ))}
                      </>
                    )}
                    <button onClick={() => setView('coach')}>Open coaching & draft</button>
                    {selectedAssessment && (
                      <details>
                        <summary>Score breakdown & citations</summary>
                        {selectedAssessment.criteria.map((criterion) => (
                          <p key={criterion.skill}>
                            <strong>{criterion.label}:</strong> {Math.round(criterion.attainment * 100)}%
                            target coverage · weight {criterion.weight} · target {criterion.target} · evidence{' '}
                            {criterion.evidence_id || 'not yet evidenced'}
                          </p>
                        ))}
                        <button
                          className="secondary"
                          onClick={() =>
                            void run(() =>
                              download(
                                'report/' + record.id + '?job_id=' + jobId,
                                'advisory-report-' + record.id + '.json',
                              ),
                            )
                          }
                        >
                          Download advisory report
                        </button>
                      </details>
                    )}
                    <details>
                      <summary>Education / transitions</summary>
                      {record.education.length ? (
                        record.education.map((education, index) => (
                          <div className="education" key={index}>
                            <strong>{education.institution}</strong>
                            <p>
                              {education.program} · {education.status.replaceAll('_', ' ')}
                            </p>
                            {education.transferred_to && <p>Transferred to: {education.transferred_to}</p>}
                            <small>{education.notes}</small>
                          </div>
                        ))
                      ) : (
                        <p>Not supplied. No outcome inferred.</p>
                      )}
                      <p>
                        Verified employment:{' '}
                        {record.verified_employment_months === null
                          ? 'not supplied'
                          : record.verified_employment_months + ' months'}
                        . Project practice is recorded separately.
                      </p>
                    </details>
                  </>
                )}
              </section>
            </div>
            {record && (
              <section className="card record-card">
                <div className="section-head">
                  <div>
                    <h2>Evidence & source review · {record.id}</h2>
                    <p>
                      Confirm the source before marking a claim reviewed. Quality levels are human-checked,
                      not keyword counts.
                    </p>
                  </div>
                  <button disabled={busy} onClick={() => void run(() => saveRecord(record))}>
                    Save evidence review
                  </button>
                </div>
                <div className="evidence-grid">
                  {record.evidence.map((evidence, index) => (
                    <article className="evidence" key={evidence.id}>
                      <div className="section-head">
                        <h3>{config.skills[evidence.skill]}</h3>
                        <span className="subtle">{evidence.kind.replace('_', ' ')}</span>
                      </div>
                      <p>{evidence.summary}</p>
                      <small>
                        Source {evidence.source_id} · {evidence.locator || 'locator not supplied'}
                      </small>
                      <LevelSelect
                        label={'Evidence strength ' + evidence.id}
                        value={evidence.level}
                        onChange={(value) =>
                          setRecord({
                            ...record,
                            evidence: record.evidence.map((item, position) =>
                              position === index ? { ...item, level: value } : item,
                            ),
                          })
                        }
                      />
                      <small>{explanations[evidence.level]}</small>
                      <label className="check">
                        <input
                          type="checkbox"
                          checked={evidence.reviewed}
                          onChange={(event) =>
                            setRecord({
                              ...record,
                              evidence: record.evidence.map((item, position) =>
                                position === index ? { ...item, reviewed: event.target.checked } : item,
                              ),
                            })
                          }
                        />
                        I checked this claim against its source
                      </label>
                    </article>
                  ))}
                </div>
                <details open>
                  <summary>Original professional sources</summary>
                  {record.sources.map((source) => (
                    <details key={source.id}>
                      <summary>
                        {source.label} · {source.kind}
                      </summary>
                      {source.warnings.map((warning) => (
                        <p className="review-flag" key={warning}>
                          {warning}
                        </p>
                      ))}
                      <pre>{source.text}</pre>
                    </details>
                  ))}
                </details>
                <details>
                  <summary>Add a source-linked claim</summary>
                  <div className="form-grid">
                    <label>
                      Skill
                      <select value={newSkill} onChange={(event) => setNewSkill(event.target.value)}>
                        {Object.entries(config.skills).map(([key, label]) => (
                          <option key={key} value={key}>
                            {label}
                          </option>
                        ))}
                      </select>
                    </label>
                    <label>
                      Claim source
                      <select value={newSource} onChange={(event) => setNewSource(event.target.value)}>
                        {record.sources.map((source) => (
                          <option key={source.id} value={source.id}>
                            {source.label}
                          </option>
                        ))}
                      </select>
                    </label>
                    <label>
                      Evidence kind
                      <select
                        value={newKind}
                        onChange={(event) => setNewKind(event.target.value as Evidence['kind'])}
                      >
                        {['project', 'coursework', 'employment', 'certification', 'work_sample'].map(
                          (kind) => (
                            <option key={kind} value={kind}>
                              {kind}
                            </option>
                          ),
                        )}
                      </select>
                    </label>
                  </div>
                  <label>
                    Professional claim / own contribution
                    <textarea
                      value={newSummary}
                      maxLength={1200}
                      onChange={(event) => setNewSummary(event.target.value)}
                    />
                  </label>
                  <button
                    disabled={!newSummary.trim() || !newSource || busy}
                    onClick={() =>
                      void run(async () => {
                        await saveRecord({
                          ...record,
                          evidence: [
                            ...record.evidence,
                            {
                              id: 'e_' + crypto.randomUUID().slice(0, 8),
                              skill: newSkill,
                              kind: newKind,
                              summary: newSummary,
                              source_id: newSource,
                              locator: 'Human-added; verify cited source',
                              level: 'declared',
                              reviewed: false,
                            },
                          ],
                        });
                        setNewSummary('');
                      })
                    }
                  >
                    Add unreviewed claim
                  </button>
                </details>
                <details>
                  <summary>Attach authorized LinkedIn text or a GitHub repository</summary>
                  <label className="check">
                    <input
                      type="checkbox"
                      checked={record.consent_sources}
                      onChange={(event) => setRecord({ ...record, consent_sources: event.target.checked })}
                    />
                    Applicant authorized these professional sources
                  </label>
                  <p>
                    LinkedIn login and access restrictions are not bypassed. Paste an applicant-provided
                    professional export; no broad people search.
                  </p>
                  <label>
                    Professional source type
                    <select
                      value={sourceKind}
                      onChange={(event) => setSourceKind(event.target.value as Source['kind'])}
                    >
                      <option value="linkedin">LinkedIn professional export</option>
                      <option value="work_sample">Work sample</option>
                      <option value="other">Other authorized professional text</option>
                    </select>
                  </label>
                  <label>
                    Professional source text
                    <textarea
                      value={sourceText}
                      maxLength={80000}
                      onChange={(event) => setSourceText(event.target.value)}
                    />
                  </label>
                  <button
                    disabled={!record.consent_sources || !sourceText.trim() || busy}
                    onClick={() =>
                      void run(() =>
                        attachSource({
                          id: 's_' + crypto.randomUUID().slice(0, 8),
                          label: 'Authorized professional text',
                          kind: sourceKind,
                          text: sourceText,
                          url: '',
                          warnings: ['Human review required; no claims inferred automatically.'],
                        }),
                      )
                    }
                  >
                    Attach source
                  </button>
                  <label>
                    Exact public GitHub repository URL
                    <input
                      value={repoURL}
                      onChange={(event) => setRepoURL(event.target.value)}
                      placeholder="https://github.com/owner/repository"
                    />
                  </label>
                  <button
                    className="secondary"
                    disabled={!record.consent_sources || !repoURL || busy}
                    onClick={() =>
                      void run(async () => {
                        const result = await api<{
                          text: string;
                          url: string;
                          label: string;
                          warnings: string[];
                        }>('github', 'POST', { url: repoURL, authorized: record.consent_sources });
                        await attachSource({
                          id: 's_' + crypto.randomUUID().slice(0, 8),
                          kind: 'github',
                          ...result,
                        });
                      })
                    }
                  >
                    Import authorized README
                  </button>
                </details>
                <details>
                  <summary>Edit education and transitions</summary>
                  <EducationEditor
                    records={record.education}
                    onChange={(education) => setRecord({ ...record, education })}
                  />
                  <label>
                    Verified employment duration (months; leave blank if unknown)
                    <input
                      type="number"
                      min="0"
                      max="1200"
                      value={record.verified_employment_months ?? ''}
                      onChange={(event) =>
                        setRecord({
                          ...record,
                          verified_employment_months:
                            event.target.value === '' ? null : Number(event.target.value),
                        })
                      }
                    />
                  </label>
                  <p>Employment duration is retained separately and never inferred from project practice.</p>
                  <button disabled={busy} onClick={() => void run(() => saveRecord(record))}>
                    Save education context
                  </button>
                </details>
                <details>
                  <summary>Edit normalized record / consent</summary>
                  <p>
                    Edit the structured record to correct transfer chronology, add education and record
                    consent. Invalid fields are rejected; identity and education never influence ranking.
                  </p>
                  <label>
                    Normalized applicant JSON
                    <textarea
                      className="code-input"
                      value={recordJSON}
                      onChange={(event) => setRecordJSON(event.target.value)}
                      rows={16}
                    />
                  </label>
                  <button
                    disabled={busy}
                    onClick={() => void run(() => saveRecord(JSON.parse(recordJSON) as Applicant))}
                  >
                    Validate & save record
                  </button>
                  <button
                    className="secondary"
                    onClick={() =>
                      void run(() => download('export/' + record.id, 'applicant-' + record.id + '.json'))
                    }
                  >
                    Download structured record
                  </button>
                </details>
              </section>
            )}
          </>
        )}
        {config && view === 'intake' && (
          <div className="two-columns">
            <section className="card">
              <h2>Resume intake</h2>
              <p>
                TXT/MD, text-based PDF and DOCX · up to 2 MB. Scanned pages and unclear formatting are
                flagged, not guessed.
              </p>
              <label className="upload">
                Choose resume file
                <input
                  type="file"
                  accept=".txt,.md,.pdf,.docx"
                  onChange={(event) => {
                    const file = event.target.files?.[0];
                    if (file) void run(() => intake(file));
                    event.target.value = '';
                  }}
                />
              </label>
              {draft.sources.length > 0 && (
                <>
                  <label>
                    Applicant ID
                    <input
                      value={draft.id}
                      onChange={(event) => setDraft({ ...draft, id: event.target.value })}
                    />
                  </label>
                  <label>
                    Applicant display name
                    <input
                      value={draft.display_name}
                      maxLength={240}
                      onChange={(event) => setDraft({ ...draft, display_name: event.target.value })}
                    />
                  </label>
                  <label className="check">
                    <input
                      type="checkbox"
                      checked={draft.consent_sources}
                      onChange={(event) => setDraft({ ...draft, consent_sources: event.target.checked })}
                    />
                    I have authorization to process this applicant's supplied professional information
                  </label>
                  {draft.sources[0].warnings.map((warning) => (
                    <p className="review-flag" key={warning}>
                      {warning}
                    </p>
                  ))}
                  <pre>{draft.sources[0].text}</pre>
                  <p>
                    {draft.evidence.length} unreviewed skill mentions proposed. Manually add claims when
                    headings are unsupported. No degree or employment duration inferred.
                  </p>
                  <button
                    disabled={!draft.consent_sources || !draft.display_name.trim() || busy}
                    onClick={() =>
                      void run(async () => {
                        await api('import', 'POST', { applicants: [draft], replace: false });
                        await select(draft.id);
                        await loadQueue();
                        setView('queue');
                        setDraft({ ...emptyApplicant });
                        setMessage('Applicant imported for source review. No automated hiring outcome.');
                      })
                    }
                  >
                    Save & review applicant
                  </button>
                </>
              )}
            </section>
            <section className="card">
              <h2>High-volume structured import</h2>
              <p>
                Import up to 100 normalized records per batch, with an atomic transaction and duplicate
                checks. Workspace capacity: {config.capacity} applicants (encrypted size limits also apply).
              </p>
              <label>
                Batch JSON
                <textarea
                  value={raw}
                  onChange={(event) => setRaw(event.target.value)}
                  className="code-input"
                  rows={14}
                  placeholder={'{"applicants": [...], "replace": false}'}
                />
              </label>
              <label>
                Load authorized JSON file
                <input
                  type="file"
                  accept=".json"
                  onChange={(event) => {
                    const file = event.target.files?.[0];
                    if (file)
                      void run(async () => {
                        if (file.size > 3_000_000) throw new Error('Batch file exceeds 3 MB.');
                        setRaw(await file.text());
                      });
                  }}
                />
              </label>
              <label className="check">
                <input
                  type="checkbox"
                  checked={replace}
                  onChange={(event) => setReplace(event.target.checked)}
                />
                Explicitly replace records with matching IDs
              </label>
              <button
                disabled={!raw.trim() || busy}
                onClick={() =>
                  void run(async () => {
                    const value = JSON.parse(raw) as { applicants: Applicant[] };
                    const result = await api<{ imported: number }>('import', 'POST', {
                      applicants: value.applicants,
                      replace,
                    });
                    setMessage('Imported ' + result.imported + ' records.');
                    await loadQueue();
                  })
                }
              >
                Validate & import batch
              </button>
              <p className="muted">
                Use the downloaded standardized record as a schema example. Real applicant data belongs in
                private runtime storage, never in Git.
              </p>
            </section>
          </div>
        )}
        {config && view === 'jobs' && (
          <section className="card">
            <div className="section-head">
              <div>
                <h2>Transparent job rubric</h2>
                <p>Choose only relevant skills. Required means “clarify gaps,” not “automatically reject.”</p>
              </div>
              <button
                className="secondary"
                onClick={() =>
                  setEditJob({
                    id: 'job_' + crypto.randomUUID().slice(0, 8),
                    title: 'New role',
                    description: '',
                    criteria: [{ skill: 'requirements', weight: 3, target: 'demonstrated', required: true }],
                  })
                }
              >
                New role
              </button>
            </div>
            {editJob && (
              <>
                <div className="form-grid">
                  <label>
                    Job title
                    <input
                      value={editJob.title}
                      maxLength={240}
                      onChange={(event) => setEditJob({ ...editJob, title: event.target.value })}
                    />
                  </label>
                  <label>
                    Job ID
                    <input
                      value={editJob.id}
                      onChange={(event) => setEditJob({ ...editJob, id: event.target.value })}
                    />
                  </label>
                </div>
                <label>
                  Job description / required qualifications
                  <textarea
                    value={editJob.description}
                    maxLength={10000}
                    onChange={(event) => setEditJob({ ...editJob, description: event.target.value })}
                  />
                </label>
                <button
                  className="secondary"
                  disabled={busy}
                  onClick={() =>
                    void run(async () => {
                      const result = await api<{ criteria: Criterion[]; notice: string }>(
                        'recommend',
                        'POST',
                        { description: editJob.description },
                      );
                      setEditJob({ ...editJob, criteria: result.criteria });
                      setMessage(result.notice);
                    })
                  }
                >
                  Suggest draft criteria
                </button>
                <div className="rubric">
                  {editJob.criteria.map((criterion, index) => (
                    <div className="criterion" key={index}>
                      <label>
                        Skill {index + 1}
                        <select
                          value={criterion.skill}
                          onChange={(event) =>
                            setEditJob({
                              ...editJob,
                              criteria: editJob.criteria.map((item, position) =>
                                position === index ? { ...item, skill: event.target.value } : item,
                              ),
                            })
                          }
                        >
                          {Object.entries(config.skills).map(([key, label]) => (
                            <option key={key} value={key}>
                              {label}
                            </option>
                          ))}
                        </select>
                      </label>
                      <label>
                        Weight
                        <input
                          type="number"
                          min="1"
                          max="10"
                          value={criterion.weight}
                          onChange={(event) =>
                            setEditJob({
                              ...editJob,
                              criteria: editJob.criteria.map((item, position) =>
                                position === index ? { ...item, weight: Number(event.target.value) } : item,
                              ),
                            })
                          }
                        />
                      </label>
                      <LevelSelect
                        label={'Target level ' + (index + 1)}
                        value={criterion.target}
                        onChange={(target) =>
                          setEditJob({
                            ...editJob,
                            criteria: editJob.criteria.map((item, position) =>
                              position === index ? { ...item, target } : item,
                            ),
                          })
                        }
                      />
                      <label className="check">
                        <input
                          type="checkbox"
                          checked={criterion.required}
                          onChange={(event) =>
                            setEditJob({
                              ...editJob,
                              criteria: editJob.criteria.map((item, position) =>
                                position === index ? { ...item, required: event.target.checked } : item,
                              ),
                            })
                          }
                        />
                        Required evidence
                      </label>
                      <button
                        className="secondary"
                        disabled={editJob.criteria.length === 1}
                        onClick={() =>
                          setEditJob({
                            ...editJob,
                            criteria: editJob.criteria.filter((_, position) => position !== index),
                          })
                        }
                      >
                        Remove
                      </button>
                    </div>
                  ))}
                </div>
                <button
                  className="secondary"
                  disabled={editJob.criteria.length >= Object.keys(config.skills).length}
                  onClick={() => {
                    const next = Object.keys(config.skills).find(
                      (key) => !editJob.criteria.some((criterion) => criterion.skill === key),
                    );
                    if (next)
                      setEditJob({
                        ...editJob,
                        criteria: [
                          ...editJob.criteria,
                          { skill: next, weight: 3, target: 'demonstrated', required: false },
                        ],
                      });
                  }}
                >
                  Add criterion
                </button>
                <button
                  disabled={busy}
                  onClick={() =>
                    void run(async () => {
                      await api('jobs', 'POST', editJob);
                      await initialize();
                      setJobId(editJob.id);
                      setMessage(
                        'Job rubric saved. Review its relevance before using it for hiring support.',
                      );
                    })
                  }
                >
                  Save approved rubric
                </button>
                <details>
                  <summary>Evidence-level definitions</summary>
                  {levels.map((level) => (
                    <p key={level}>
                      <strong>{level}:</strong> {explanations[level]}
                    </p>
                  ))}
                </details>
              </>
            )}
          </section>
        )}
        {config && view === 'coach' && (
          <section className="card">
            <div className="section-head">
              <div>
                <h2>{record ? 'Applicant coaching · ' + record.id : 'Select an applicant first'}</h2>
                <p>Practical improvements and factual drafts, not invented accomplishments.</p>
              </div>
              <button className="secondary" onClick={() => setView('queue')}>
                Choose applicant
              </button>
            </div>
            {record && (
              <>
                <label className="check">
                  <input
                    type="checkbox"
                    checked={general}
                    onChange={(event) => {
                      setGeneral(event.target.checked);
                      setAI(null);
                    }}
                  />
                  General advice, without tailoring to a selected role
                </label>
                <button
                  onClick={() =>
                    void run(() =>
                      download(
                        'resume/' + record.id + (general ? '' : '?job_id=' + jobId),
                        'resume-draft-' + record.id + '.html',
                      ),
                    )
                  }
                >
                  Download tailored resume draft
                </button>
                <small className="block">
                  Printable HTML; review facts and print to PDF. No source formatting, protected traits or
                  unreviewed claims are copied into the draft.
                </small>
                {coaching && (
                  <div className="two-columns">
                    <div>
                      <h3>Resume improvements</h3>
                      <ul>
                        {[...coaching.advice, ...coaching.resume].map((advice) => (
                          <li key={advice}>{advice}</li>
                        ))}
                      </ul>
                      <h3>LinkedIn / profile presentation</h3>
                      <ul>
                        {coaching.linkedin.map((advice) => (
                          <li key={advice}>{advice}</li>
                        ))}
                      </ul>
                    </div>
                    <div>
                      <h3>Portfolio demonstrations to add</h3>
                      {coaching.projects.length ? (
                        coaching.projects.map((project) => (
                          <article className="project" key={project.skill}>
                            <h4>{project.title}</h4>
                            <ol>
                              {project.steps.map((step) => (
                                <li key={step}>{step}</li>
                              ))}
                            </ol>
                          </article>
                        ))
                      ) : (
                        <p>
                          Document your current work with tests, limitations and your contribution. Select a
                          role to see evidence-gap projects.
                        </p>
                      )}
                    </div>
                  </div>
                )}
                <div className="ai-panel">
                  <h3>Optional AI evidence coaching</h3>
                  <p>
                    The model sees skill IDs, evidence kinds/levels and the rubric only—not names, resume
                    text, education, dates or source links. It returns constrained improvement actions; the
                    score remains reproducible. Provider fees may apply.
                  </p>
                  <label className="check">
                    <input
                      type="checkbox"
                      checked={record.consent_ai}
                      onChange={(event) => setRecord({ ...record, consent_ai: event.target.checked })}
                    />
                    Applicant explicitly consents to this structured AI processing
                  </label>
                  <button
                    className="secondary"
                    disabled={busy || !record.consent_ai}
                    onClick={() =>
                      void run(async () => {
                        await saveRecord(record);
                        setAI(
                          await api<AIResult>('ai', 'POST', {
                            job_id: jobId,
                            applicant_id: record.id,
                            consent: true,
                          }),
                        );
                      })
                    }
                  >
                    {config.ai_configured
                      ? 'Request AI coaching'
                      : 'Request AI coaching (server model required)'}
                  </button>
                  {ai && (
                    <>
                      <p>
                        {ai.provider} · {ai.model} · AI suggestions require human verification.
                      </p>
                      {ai.suggestions.map((suggestion, index) => (
                        <p key={index}>
                          <strong>{config.skills[suggestion.skill]}:</strong> {suggestion.text}{' '}
                          <small>Citations: {suggestion.evidence_ids.join(', ') || 'evidence gap'}</small>
                        </p>
                      ))}
                    </>
                  )}
                </div>
              </>
            )}
          </section>
        )}
        {config && view === 'guide' && (
          <section className="card readable">
            <h2>What the score means</h2>
            <p>
              Coverage = 100 × the weighted average of reviewed evidence strength divided by target strength,
              capped at 1 per skill. Each skill uses only its strongest reviewed claim. Repeating keywords or
              copying a project does not multiply the score. Equal scores share a rank.
            </p>
            <h3>Professional evidence, not identity</h3>
            <p>
              Name, gender, race, age, disability, religion, address, school prestige, photos, followers and
              social popularity are not ranking fields. Education chronology is retained for reviewers, but is
              not converted into employment years or used as a hidden feature. Only vetted professional skill
              IDs can be configured.
            </p>
            <h3>Missing information stays unknown</h3>
            <p>
              Unreviewed claims, inaccessible profiles, scanned documents, uncertain degrees and missing
              transfer destinations trigger review. Do not confuse missing evidence with inability. Ask for
              accessible work samples or clarification when appropriate.
            </p>
            <h3>Human review remains essential</h3>
            <p>
              Read the highest-ranked applications and cited work yourself. Rankings and AI advice can be
              wrong and can reflect incomplete evidence or a poorly chosen rubric. Validate the role
              requirements, offer correction paths and appropriate accommodations, and make your own hiring
              decisions. This prototype does not claim to be bias-free, legally compliant or a validated
              predictor of job success.
            </p>
            <h3>Privacy boundary</h3>
            {isPrivateWorkspace() ? (
              <p>
                Documents are decrypted and processed on this device. Only encrypted workspace ciphertext is
                synchronized to your account. Your independent vault phrase is not sent to the service.
                Private mode disables all external AI and source lookups; paste authorized exports instead.
                See Account & backups for recovery, deletion, installation and limitations. Ordinary downloads
                are unencrypted private files.
              </p>
            ) : (
              <p>
                This is a single-user loopback application, not a public recruitment service. Records stay in
                a private local SQLite file; optional AI calls require consent. Do not publish applicant data.
                LinkedIn intake uses authorized professional text/export, not access-control bypassing. GitHub
                intake reads one authorized public README and never runs applicant code.
              </p>
            )}
            <h3>Production deployment</h3>
            <p>
              Production use needs organizational authentication, role-based access, encryption and retention
              policies, accessibility evaluation, security review, jurisdiction-specific review, appeals and
              real-world validation. The development workflow and limits are documented in the repository.
            </p>
          </section>
        )}
        <footer>
          Evidence before assumptions. <span>Local-first · Transparent rubric · Human decisions</span>
        </footer>
      </main>
    </div>
  );
}
