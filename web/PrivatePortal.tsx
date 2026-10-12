// Purpose: Jason Stys — real account login, independent vault unlock, help and install controls.
// Index: useEffect@3, useState@3, App@4, accountRequest@5, base64@5, derive@5, saveFile@5, seal@5, unseal@5, validateEnvelope@5, bindWorkspace@7, demoWorkspace@8, emptyWorkspace@9, encryptedBackup@10, lockWorkspace@11, validateWorkspace@12, Help@16, PrivatePortal@88, checking@89, setChecking@89, account@90, setAccount@90, setUnlocked@91, unlocked@91, mode@92, setMode@92, setUsername@93, username@93, password@94, setPassword@94, phrase@95, setPhrase@95, lastPassword@96, setLastPassword@96, recovery@97, setRecovery@97, recoveryInput@98, setRecoveryInput@98, error@99, setError@99, busy@100, setBusy@100, message@101, setMessage@101, setSettings@102, settings@102, deletePassword@103, setDeletePassword@103, confirmDelete@104, setConfirmDelete@104, samplesConfirmed@105, setSamplesConfirmed@105, run@108, task@108, e@114, lock@122, active@133, value@135, timer@149, renew@150, hide@160, events@163, e@164, e@169, authenticate@175, result@177, result@189, unlock@198, stored@200, salt@201, key@204, value@205, revision@208, result@210, newPhrase@223, replaceWorkspace@223, value@223, stored@226, current@228, key@229, checked@231, saved@232, m@323, event@338, e@349, e@363, e@373, e@398, e@412, e@447, e@454, e@470, file@471, envelope@476, key@477, e@500, e@507
import { useEffect, useState } from 'react';
import App from './App';
import { accountRequest, base64, derive, saveFile, seal, unseal, validateEnvelope } from './vault';
import {
  bindWorkspace,
  demoWorkspace,
  emptyWorkspace,
  encryptedBackup,
  lockWorkspace,
  validateWorkspace,
} from './private-domain';

/** Explain privacy/recovery/install boundaries without promising impossible host immunity. */
function Help() {
  return (
    <details className="account-help">
      <summary>Help, privacy & installation</summary>
      <h2>Your private workspace</h2>
      <ol>
        <li>
          Create an account alias and a unique login password (15+ characters). Save the once-shown login
          recovery code in your password manager.
        </li>
        <li>
          Choose a DIFFERENT vault phrase (20+ characters; six random words recommended). It encrypts
          documents on your device. Neither Jason nor the server receives it. Losing it loses your documents;
          login recovery cannot decrypt them.
        </li>
        <li>
          Create a job rubric in Job criteria, or explicitly load fictional examples. Import only resumes you
          have permission to process. Review extracted text and approve source-linked claims before scoring.
        </li>
        <li>
          Use the review queue and coaching tabs. Scores are evidence coverage, not hiring decisions, legal
          compliance, or predicted performance. Always read original applications yourself.
        </li>
        <li>
          Export an encrypted backup regularly. Resume/report downloads are UNENCRYPTED private files: protect
          them and do not publish them.
        </li>
      </ol>
      <p>
        Processing is local. No trackers, ads, analytics, external AI or silent source lookups are enabled in
        private mode. GitHub/LinkedIn evidence must be pasted from an authorized export. No sharing is
        enabled; another user cannot open your account workspace.
      </p>
      <p>
        The host can see your alias, password hash, encrypted size and request timing; infrastructure may
        retain IP access logs. Encryption is not anonymity. A malicious future host, compromised
        browser/extension, weak vault phrase or infected device can defeat browser privacy. No site can block
        your own browser extensions. Review source and use a verified local build if you need independence
        from a host.
      </p>
      <h3>Install the app</h3>
      <p>
        On supported desktop/Android browsers, use the browser's Install app command. On iOS/iPadOS, use Share
        → Add to Home Screen. The installed web app requires the account service; private responses are never
        cached. Alternatively download a native local launcher from the GitHub release matching your OS,
        verify its SHA-256, then launch it; it needs no Python or Node installation.
      </p>
      <p>
        Unsigned community builds may trigger OS warnings; do not bypass warnings without verifying the
        publisher and checksum. Account login passwords can be reset using the recovery code. Vault phrases
        have no reset/backdoor. Contact Jason without sending resumes, passwords, recovery codes or private
        documents.
      </p>
      <p>
        Created by{' '}
        <a href="https://github.com/JasonStys" rel="noreferrer">
          Jason Stys
        </a>{' '}
        ·{' '}
        <a href="https://www.linkedin.com/in/jason-stys-31b30b351/" rel="noreferrer">
          Contact on LinkedIn
        </a>{' '}
        ·{' '}
        <a href="https://github.com/JasonStys/applicant-evidence-studio/releases" rel="noreferrer">
          Downloads & checksums
        </a>
      </p>
    </details>
  );
}

/** Keep keys/data only in the active view; lock after ten idle minutes or explicit sign-out. */
export default function PrivatePortal() {
  const [checking, setChecking] = useState(true),
    [account, setAccount] = useState(''),
    [unlocked, setUnlocked] = useState(false);
  const [mode, setMode] = useState<'login' | 'register' | 'reset'>('login');
  const [username, setUsername] = useState(''),
    [password, setPassword] = useState(''),
    [phrase, setPhrase] = useState('');
  const [lastPassword, setLastPassword] = useState(''),
    [recovery, setRecovery] = useState(''),
    [recoveryInput, setRecoveryInput] = useState('');
  const [error, setError] = useState(''),
    [busy, setBusy] = useState(false),
    [message, setMessage] = useState('');
  const [settings, setSettings] = useState(false),
    [deletePassword, setDeletePassword] = useState(''),
    [confirmDelete, setConfirmDelete] = useState(false);
  const [samplesConfirmed, setSamplesConfirmed] = useState(false);

  /** One task at a time; error text is controlled and never includes submitted credentials. */
  async function run(task: () => Promise<void>) {
    setBusy(true);
    setError('');
    setMessage('');
    try {
      await task();
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Operation failed.');
    } finally {
      setBusy(false);
    }
  }

  /** Clear UI and drop non-extractable key references. Garbage collection is not secure erasure. */
  function lock() {
    lockWorkspace();
    setUnlocked(false);
    setPhrase('');
    setLastPassword('');
    setSettings(false);
    setDeletePassword('');
    setConfirmDelete(false);
  }

  useEffect(() => {
    let active = true;
    accountRequest<{ username: string }>('account')
      .then((value) => {
        if (active) setAccount(value.username);
      })
      .catch(() => undefined)
      .finally(() => {
        if (active) setChecking(false);
      });
    return () => {
      active = false;
      lockWorkspace();
    };
  }, []);
  useEffect(() => {
    if (!unlocked) return;
    let timer: ReturnType<typeof setTimeout>;
    const renew = () => {
      clearTimeout(timer);
      timer = setTimeout(
        () => {
          lock();
          setMessage('Workspace locked after ten minutes of inactivity.');
        },
        10 * 60 * 1000,
      );
    };
    const hide = () => {
      if (document.visibilityState === 'hidden') renew();
    };
    const events = ['pointerdown', 'keydown', 'touchstart'] as const;
    events.forEach((e) => window.addEventListener(e, renew));
    document.addEventListener('visibilitychange', hide);
    renew();
    return () => {
      clearTimeout(timer);
      events.forEach((e) => window.removeEventListener(e, renew));
      document.removeEventListener('visibilitychange', hide);
    };
  }, [unlocked]);

  /** Authenticate; login recovery rotates credentials, not document encryption. */
  async function authenticate() {
    if (mode === 'reset') {
      const result = await accountRequest<{ recovery: string }>('reset', 'POST', {
        username,
        password,
        recovery: recoveryInput,
      });
      setRecovery(result.recovery);
      setRecoveryInput('');
      setPassword('');
      setMode('login');
      setMessage('Password reset; save your new recovery code and sign in.');
      return;
    }
    const result = await accountRequest<{ recovery?: string }>(mode, 'POST', { username, password });
    setLastPassword(password);
    setPassword('');
    setAccount(username);
    setMode('login');
    setRecovery(result.recovery || '');
  }

  /** Unlock or initialize; all plaintext validation and cryptography happen in this browser. */
  async function unlock() {
    if (phrase === lastPassword) throw new Error('Your vault phrase must differ from your login password.');
    const stored = await accountRequest<{ envelope: unknown; revision: number }>('workspace');
    const salt = stored.envelope
      ? validateEnvelope(stored.envelope).salt
      : base64(crypto.getRandomValues(new Uint8Array(16)));
    const key = await derive(phrase, salt);
    const value = stored.envelope
      ? validateWorkspace(await unseal(validateEnvelope(stored.envelope), key))
      : emptyWorkspace();
    let revision = stored.revision;
    if (!stored.envelope) {
      const result = await accountRequest<{ revision: number }>('workspace', 'PUT', {
        envelope: await seal(value, key, salt),
        revision,
      });
      revision = result.revision;
    }
    bindWorkspace(value, key, salt, revision);
    setPhrase('');
    setLastPassword('');
    setUnlocked(true);
  }

  /** Replace only with explicit confirmation; imports need their own vault phrase and current CAS. */
  async function replaceWorkspace(value: unknown, newPhrase: string) {
    if (newPhrase.length < 20)
      throw new Error('Enter your current vault phrase in the backup settings first.');
    const stored = await accountRequest<{ envelope: unknown; revision: number }>('workspace');
    if (!stored.envelope) throw new Error('Open a workspace first.');
    const current = validateEnvelope(stored.envelope);
    const key = await derive(newPhrase, current.salt);
    await unseal(current, key); // Verify ownership key before allowing a replacement.
    const checked = validateWorkspace(value);
    const saved = await accountRequest<{ revision: number }>('workspace', 'PUT', {
      envelope: await seal(checked, key, current.salt),
      revision: stored.revision,
    });
    void saved;
    lockWorkspace();
    setPhrase('');
    setSamplesConfirmed(false);
    setUnlocked(false);
    setMessage('Workspace replaced. Unlock again to refresh the review view.');
  }

  return (
    <>
      <header className="account-bar">
        <strong>Applicant Evidence Studio</strong>
        <span>
          by{' '}
          <a href="https://github.com/JasonStys" rel="noreferrer">
            Jason Stys
          </a>
        </span>
        {account && (
          <>
            <span>Signed in as {account}</span>
            {unlocked && (
              <button disabled={busy} onClick={lock}>
                Lock workspace
              </button>
            )}
            <button
              disabled={busy}
              onClick={() => {
                setSettings(!settings);
                setError('');
              }}
            >
              Account & backups
            </button>
            <button
              disabled={busy}
              onClick={() =>
                void run(async () => {
                  await accountRequest('logout', 'POST', {});
                  lock();
                  setAccount('');
                  setRecovery('');
                })
              }
            >
              Sign out
            </button>
          </>
        )}
      </header>
      {error && (
        <div className="account-alert" role="alert">
          {error}
        </div>
      )}
      {message && (
        <div className="account-alert" role="status">
          {message}
        </div>
      )}
      {recovery && (
        <section className="account-card" aria-label="Login recovery code">
          <h2>Save your login recovery code</h2>
          <p>This is shown only now. It recovers account login, NOT your vault phrase.</p>
          <code className="recovery-code">{recovery}</code>
          <button
            onClick={() => {
              setRecovery('');
              setMessage('Recovery code dismissed. Keep your saved copy private.');
            }}
          >
            I saved it privately
          </button>
        </section>
      )}
      {checking ? (
        <main className="account-card">Checking account session…</main>
      ) : !account ? (
        <main className="account-card">
          <div className="eyebrow">PRIVATE BY DESIGN · HUMAN-LED REVIEW</div>
          <h1>Make professional evidence easier to review.</h1>
          <p>
            Job rubrics, source-linked resumes and practical coaching, with private documents processed on
            your device.
          </p>
          <div className="account-tabs">
            {(['login', 'register', 'reset'] as const).map((m) => (
              <button
                key={m}
                aria-pressed={mode === m}
                onClick={() => {
                  setMode(m);
                  setError('');
                  setPassword('');
                }}
              >
                {m === 'login' ? 'Sign in' : m === 'register' ? 'Create account' : 'Recover login'}
              </button>
            ))}
          </div>
          <form
            onSubmit={(event) => {
              event.preventDefault();
              void run(authenticate);
            }}
          >
            <label>
              Account alias
              <input
                required
                autoComplete="username"
                value={username}
                onChange={(e) => setUsername(e.target.value.toLowerCase())}
                pattern="[a-z0-9]([a-z0-9_]|-){2,39}"
                maxLength={40}
              />
            </label>
            <label>
              {mode === 'reset' ? 'New login password' : 'Login password'}
              <input
                required
                type="password"
                autoComplete={mode === 'login' ? 'current-password' : 'new-password'}
                minLength={15}
                maxLength={128}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
              />
            </label>
            {mode === 'reset' && (
              <label>
                Login recovery code
                <input
                  required
                  autoComplete="off"
                  value={recoveryInput}
                  onChange={(e) => setRecoveryInput(e.target.value)}
                />
              </label>
            )}
            <button disabled={busy} type="submit">
              {busy
                ? 'Please wait…'
                : mode === 'login'
                  ? 'Sign in securely'
                  : mode === 'register'
                    ? 'Register account'
                    : 'Reset login password'}
            </button>
          </form>
          <Help />
        </main>
      ) : !unlocked ? (
        <main className="account-card">
          <h1>Unlock your private workspace</h1>
          <p>
            For a new account, choose a DIFFERENT vault phrase. For an existing workspace, enter the phrase
            you chose. Use six random words. It never leaves this browser. There is no vault reset or
            administrator recovery.
          </p>
          <form
            onSubmit={(e) => {
              e.preventDefault();
              void run(unlock);
            }}
          >
            <label>
              Vault phrase
              <input
                required
                type="password"
                autoComplete="off"
                minLength={20}
                maxLength={256}
                value={phrase}
                onChange={(e) => setPhrase(e.target.value)}
              />
            </label>
            <button disabled={busy}>Unlock or create workspace</button>
          </form>
          <Help />
        </main>
      ) : (
        <App />
      )}
      {account && settings && (
        <section className="account-card" aria-label="Account and encrypted backups">
          <h2>Account & encrypted backups</h2>
          {unlocked && (
            <>
              <button
                disabled={busy}
                onClick={() =>
                  void run(async () =>
                    saveFile(JSON.stringify(await encryptedBackup()), 'applicant-workspace.encrypted.json'),
                  )
                }
              >
                Download encrypted backup
              </button>
              <p>
                Replacement overwrites your entire workspace. Export a backup first, then enter your current
                vault phrase to authorize replacement.
              </p>
              <label>
                Current vault phrase for replacement
                <input
                  type="password"
                  autoComplete="off"
                  value={phrase}
                  onChange={(e) => setPhrase(e.target.value)}
                />
              </label>
              <label>
                <input
                  type="checkbox"
                  checked={samplesConfirmed}
                  onChange={(e) => setSamplesConfirmed(e.target.checked)}
                />
                I exported a backup and approve replacing the workspace
              </label>
              <button
                disabled={busy || !samplesConfirmed}
                onClick={() => void run(() => replaceWorkspace(demoWorkspace(), phrase))}
              >
                Replace with fictional examples
              </button>
              <label>
                Restore encrypted backup
                <input
                  type="file"
                  accept=".json"
                  disabled={busy || !samplesConfirmed}
                  onChange={(e) => {
                    const file = e.target.files?.[0];
                    e.target.value = '';
                    if (file)
                      void run(async () => {
                        if (file.size > 11201000) throw new Error('Backup exceeds the size limit.');
                        const envelope = validateEnvelope(JSON.parse(await file.text()));
                        const key = await derive(phrase, envelope.salt);
                        await replaceWorkspace(await unseal(envelope, key), phrase);
                      });
                  }}
                />
              </label>
              <p>
                Restore requires the SAME phrase for the backup and current workspace. To use a different
                backup phrase, restore into a new account initialized with that phrase.
              </p>
            </>
          )}
          <h3>Delete account</h3>
          <p>
            Permanently deletes live account credentials, sessions and encrypted workspace. Host backups may
            persist for the host's documented retention period. There is no undo.
          </p>
          <label>
            Current login password for deletion
            <input
              type="password"
              autoComplete="current-password"
              value={deletePassword}
              onChange={(e) => setDeletePassword(e.target.value)}
            />
          </label>
          <label>
            <input
              type="checkbox"
              checked={confirmDelete}
              onChange={(e) => setConfirmDelete(e.target.checked)}
            />
            I approve permanent account deletion
          </label>
          <button
            disabled={busy || !confirmDelete}
            onClick={() =>
              void run(async () => {
                await accountRequest('account', 'DELETE', { password: deletePassword });
                lock();
                setAccount('');
                setRecovery('');
                setMessage('Live account and encrypted workspace deleted.');
              })
            }
          >
            Permanently delete my account
          </button>
          <Help />
        </section>
      )}
    </>
  );
}
