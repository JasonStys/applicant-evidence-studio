// Purpose: Jason Stys — actual extracted native app, WebCrypto comparison/export and lock acceptance.
// Index: assert@3, createHash@4, randomUUID@4, execFile@5, spawn@5, lstat@6, mkdtemp@6, readFile@6, rm@6, tmpdir@7, path@8, fileURLToPath@9, promisify@10, chromium@11, expect@11, AxeBuilder@12, root@14, binary@15, version@16, runFile@17, folder@20, child@21, browser@28, stopping@29, started@30, canonical@33, value@33, key@40, readiness@48, reject@49, resolve@49, timer@50, pending@54, error@55, bytes@64, lines@71, line@73, match@74, exercise@88, origin@88, healthResponse@89, health@91, context@95, outside@96, route@97, page@104, errors@107, error@108, password@109, phrase@110, registered@117, r@118, unlock@123, editor@139, edited@140, before@146, writes@151, r@152, panel@158, download@161, report@163, vectors@164, r@166, record@169, v@170, vector@170, r@175, r@176, input@178, other@192, origin@217, deadline@218, result@220, _@222, reject@222, error@243, resolve@248, resolve@249, error@254, target@259
import assert from 'node:assert/strict';
import { createHash, randomUUID } from 'node:crypto';
import { spawn, execFile } from 'node:child_process';
import { mkdtemp, readFile, rm, lstat } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { promisify } from 'node:util';
import { chromium, expect } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const binary = path.resolve(process.argv[2] || '');
const version = process.argv[3];
const runFile = promisify(execFile);
if (!/^\d+\.\d+\.\d+$/.test(version || '') || !(await lstat(binary)).isFile())
  throw new Error('Select a verified native binary and exact product version.');
const folder = await mkdtemp(path.join(tmpdir(), 'aes-native-ui-'));
const child = spawn(binary, [], {
  cwd: folder,
  windowsHide: true,
  detached: process.platform !== 'win32',
  env: { ...process.env, AES_NO_BROWSER: '1', AES_DESKTOP_DATA: path.join(folder, 'accounts') },
  stdio: ['ignore', 'pipe', 'pipe'],
});
let browser;
let stopping = false;
const started = performance.now();

/** Hash the supplied record using sorted JSON keys and Node's independent SHA-256 implementation. */
function canonical(value) {
  if (Array.isArray(value)) return '[' + value.map(canonical).join(',') + ']';
  if (value !== null && typeof value === 'object')
    return (
      '{' +
      Object.keys(value)
        .sort()
        .map((key) => JSON.stringify(key) + ':' + canonical(value[key]))
        .join(',') +
      '}'
    );
  return JSON.stringify(value);
}

/** A fresh bound port must be announced by this exact child before any HTTP request. */
function readiness() {
  return new Promise((resolve, reject) => {
    const timer = setTimeout(
      () => reject(new Error('Native child did not announce readiness within 60 seconds.')),
      60_000,
    );
    let pending = '';
    child.once('error', (error) => {
      clearTimeout(timer);
      reject(error);
    });
    child.once('exit', () => {
      clearTimeout(timer);
      if (!stopping) reject(new Error('Native child exited before acceptance completed.'));
    });
    child.stderr.on('data', () => {}); // Drain bounded process pipes; never print account/service output.
    child.stdout.on('data', (bytes) => {
      pending += bytes.toString('utf8');
      if (pending.length > 65_536) {
        clearTimeout(timer);
        reject(new Error('Unexpected native readiness output.'));
        return;
      }
      const lines = pending.split(/\r?\n/);
      pending = lines.pop() || '';
      for (const line of lines) {
        const match =
          /^Applicant Evidence Studio by Jason Stys is running at (http:\/\/127\.0\.0\.1:([0-9]{4,5}))$/.exec(
            line,
          );
        if (match && Number(match[2]) >= 1024 && Number(match[2]) <= 65535) {
          clearTimeout(timer);
          resolve(match[1]);
        }
      }
    });
  });
}

/** Real user journey against only the compiled app's embedded UI and private service. */
async function exercise(origin) {
  const healthResponse = await fetch(origin + '/health', { signal: AbortSignal.timeout(5_000) });
  assert.equal(healthResponse.status, 200);
  const health = await healthResponse.json();
  assert.equal(health.version, version);
  assert.equal(health.mode, 'private-accounts');
  browser = await chromium.launch();
  const context = await browser.newContext({ baseURL: origin, acceptDownloads: true });
  const outside = [];
  await context.route('**/*', (route) => {
    if (new URL(route.request().url()).origin !== origin) {
      outside.push(route.request().url());
      return route.abort();
    }
    return route.continue();
  });
  const page = await context.newPage();
  page.setDefaultTimeout(8_000);
  page.setDefaultNavigationTimeout(15_000);
  const errors = [];
  page.on('pageerror', (error) => errors.push(error.name));
  const password = 'synthetic-only-native-password-2026';
  const phrase = 'native synthetic words keep fictional records private';
  await page.goto('/');
  await page.getByRole('button', { name: 'Create account', exact: true }).click();
  await page
    .getByLabel('Account alias', { exact: true })
    .fill('native_' + randomUUID().replaceAll('-', '').slice(0, 20));
  await page.getByLabel('Login password', { exact: true }).fill(password);
  const registered = page.waitForResponse(
    (r) => r.url().endsWith('/vault/register') && r.request().method() === 'POST',
  );
  await page.getByRole('button', { name: 'Register account', exact: true }).click();
  assert.equal((await registered).status(), 200);
  await page.getByRole('button', { name: 'I saved it privately' }).click();
  async function unlock() {
    await page.getByLabel('Vault phrase', { exact: true }).fill(phrase);
    await page.getByRole('button', { name: 'Unlock or create workspace' }).click();
    await expect(page.getByRole('heading', { name: 'Review queue', exact: true })).toBeVisible();
  }
  await unlock();
  await expect(page.locator('.sidebar small')).toContainText('v' + version);
  await page.getByRole('button', { name: 'Account & backups' }).click();
  await page.getByLabel('Current vault phrase for replacement').fill(phrase);
  await page.getByLabel('I exported a backup and approve replacing the workspace').check();
  await page.getByRole('button', { name: 'Replace with fictional examples' }).click();
  await expect(page.getByRole('heading', { name: 'Unlock your private workspace' })).toBeVisible();
  await page.getByRole('button', { name: 'Account & backups' }).click();
  await unlock();
  await page.getByRole('button', { name: 'Review A101', exact: true }).click();
  await page.getByText('Edit normalized record / consent', { exact: true }).click();
  const editor = page.getByLabel('Normalized applicant JSON');
  const edited = JSON.parse(await editor.inputValue());
  edited.evidence[0].summary = '<img src="https://unexpected.example/pixel"> synthetic native evidence';
  edited.sources[0].label = 'Source <script>inert native text</script>';
  await editor.fill(JSON.stringify(edited));
  await page.getByRole('button', { name: 'Validate & save record', exact: true }).click();
  await expect(page.getByRole('status')).toContainText('Record saved');
  const before = await (await context.request.get('/vault/workspace')).json();
  assert.deepEqual(Object.keys(before.envelope).sort(), ['ciphertext', 'iv', 'salt', 'version']);
  assert.ok(
    !JSON.stringify(before).includes(phrase) && !JSON.stringify(before).includes('synthetic native evidence'),
  );
  const writes = [];
  page.on('request', (r) => {
    if (r.method() === 'PUT' || new URL(r.url()).pathname.startsWith('/api/')) writes.push(r.method());
  });
  await page.getByLabel('Compare A101', { exact: true }).check();
  await page.getByLabel('Compare A102', { exact: true }).check();
  await page.getByRole('button', { name: 'Capture selected evidence' }).click();
  const panel = page.getByRole('region', { name: 'Criterion evidence comparison', exact: true });
  await expect(panel).toContainText(edited.evidence[0].summary);
  await expect(panel.locator('img, script, iframe')).toHaveCount(0);
  const download = page.waitForEvent('download');
  await panel.getByRole('button', { name: 'Download private comparison JSON', exact: true }).click();
  const report = JSON.parse(await readFile(await (await download).path(), 'utf8'));
  const vectors = JSON.parse(await readFile(path.join(root, 'tests/fixtures/parity.json'), 'utf8'));
  assert.deepEqual(
    report.records.map((r) => r.id),
    ['A101', 'A102'],
  );
  for (const record of report.records) {
    const vector = vectors.find((v) => v.job.id === 'software' && v.applicant.id === record.id);
    assert.ok(vector);
    assert.equal(record.score, vector.assessment.score);
    assert.equal(report.rubric.hash, vector.assessment.rubric_hash);
    assert.deepEqual(
      record.criteria.map((r) => [r.skill, r.attainment, r.best_support?.evidence_id ?? null]),
      vector.assessment.criteria.map((r) => [r.skill, r.attainment, r.evidence_id]),
    );
    const input = record.id === 'A101' ? edited : vector.applicant;
    assert.equal(record.record_sha256, createHash('sha256').update(canonical(input), 'utf8').digest('hex'));
    assert.ok(!('rank' in record) && !('display_name' in record) && !('sources' in record));
  }
  assert.equal((await (await context.request.get('/vault/workspace')).json()).revision, before.revision);
  assert.deepEqual(writes, []);
  assert.deepEqual(outside, []);
  assert.deepEqual(errors, []);
  assert.deepEqual((await new AxeBuilder({ page }).include('.comparison-card').analyze()).violations, []);
  await page.getByRole('button', { name: 'Lock workspace' }).click();
  await expect(page.getByRole('button', { name: 'Download private comparison JSON' })).toHaveCount(0);
  await unlock();
  await expect(page.getByLabel('Compare A101', { exact: true })).not.toBeChecked();
  await expect(page.getByRole('button', { name: 'Download private comparison JSON' })).toHaveCount(0);
  const other = await browser.newContext({ baseURL: origin });
  try {
    assert.equal((await other.request.get('/vault/workspace')).status(), 401);
  } finally {
    await other.close();
  }
  assert.equal(child.exitCode, null, 'The owned native service must remain alive throughout acceptance.');
  assert.equal(child.signalCode, null);
  return {
    version,
    compiled_native: true,
    real_webcrypto: true,
    record_ids: ['A101', 'A102'],
    exact_record_hashes: true,
    python_assessment_parity: true,
    read_only_capture: true,
    ciphertext_only_store: true,
    lock_reopen: true,
    unauthenticated_denied: true,
    outside_requests: outside.length,
    accessibility_violations: 0,
  };
}

try {
  const origin = await readiness();
  let deadline;
  try {
    const result = await Promise.race([
      exercise(origin),
      new Promise((_, reject) => {
        deadline = setTimeout(() => reject(new Error('Native UI journey exceeded 60 seconds.')), 60_000);
      }),
    ]);
    console.log(JSON.stringify({ ...result, elapsed_ms: Math.round(performance.now() - started) }));
  } finally {
    clearTimeout(deadline);
  }
} finally {
  stopping = true;
  if (browser) await browser.close();
  if (child.pid && child.exitCode === null && child.signalCode === null) {
    if (process.platform === 'win32') {
      await runFile(
        path.join(process.env.SystemRoot || 'C:/Windows', 'System32/taskkill.exe'),
        ['/PID', String(child.pid), '/T', '/F'],
        { windowsHide: true, timeout: 10_000 },
      ).catch(() => {});
    } else {
      try {
        process.kill(-child.pid, 'SIGTERM');
      } catch (error) {
        if (error.code !== 'ESRCH') throw error;
      }
    }
    await Promise.race([
      new Promise((resolve) => child.once('close', resolve)),
      new Promise((resolve) => setTimeout(resolve, 5_000)),
    ]);
    if (process.platform !== 'win32' && child.exitCode === null && child.signalCode === null) {
      try {
        process.kill(-child.pid, 'SIGKILL');
      } catch (error) {
        if (error.code !== 'ESRCH') throw error;
      }
    }
  }
  const target = path.resolve(folder);
  assert.ok(
    path.dirname(target) === path.resolve(tmpdir()) && path.basename(target).startsWith('aes-native-ui-'),
  );
  await rm(target, { recursive: true, force: true });
}
