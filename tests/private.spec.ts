// Purpose: Jason Stys — end-to-end real accounts, encrypted sync, local parsing, exports and isolation.
// Index: Page@3, expect@3, test@3, AxeBuilder@4, strToU8@5, zipSync@5, readFileSync@6, readdirSync@6, randomUUID@7, password@8, phrase@9, aliases@10, page@14, asset@16, name@17, worker@21, workerReady@21, url@23, worker@30, scope@36, event@37, observed@42, owned@43, marker@44, reject@48, resolve@48, parsed@49, metadata@50, timer@51, event@52, reply@52, event@65, windowAck@65, page@89, editor@98, edited@99, before@105, requests@106, request@107, panel@118, pending@122, report@124, vectors@125, record@126, expected@127, vector@128, row@135, row@142, browser@161, page@161, signedState@166, vectors@167, vector@168, reportContext@171, reportPage@172, panel@183, event@187, report@189, field@190, info@200, page@200, request@200, page@216, signUp@216, alias@217, registered@223, response@224, page@235, unlock@235, value@235, loadExamples@242, page@242, page@254, browser@255, requests@257, request@258, alias@261, body@265, parsed@266, context@280, other@281, result@285, otherVault@287, firstVault@288, signedIn@296, response@297, page@306, destinations@308, r@309, marker@314, saves@326, r@327, d@333, download@336, file@338, text@339, page@345, docx@349, page@377, browser@378, downloaded@384, backup@386, manifest@397, state@401, context@402, second@403, observed@406, changed@407, page@420, info@421
import { test, expect, type Page } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';
import { zipSync, strToU8 } from 'fflate';
import { readFileSync, readdirSync } from 'node:fs';
import { randomUUID } from 'node:crypto';
const password = 'synthetic-only-login-password-2026';
const phrase = 'six random synthetic words keep documents private';
const aliases = new Set<string>();

/** Verify the actual built parser's dedicated channel, rather than treating it as Window.postMessage. */
test('dedicated parser keeps empty-origin parent messages separate from window messages', async ({
  page,
}) => {
  const asset = readdirSync('dist/assets').find(
    (name) => name.startsWith('private-parser.worker-') && name.endsWith('.js'),
  );
  if (!asset) throw new Error('Built parser worker asset is missing');
  await page.goto('/');
  const workerReady = page.waitForEvent('worker', { predicate: (worker) => worker.url().includes(asset) });
  await page.evaluate(
    (url) => {
      (window as unknown as { parserProofWorker: Worker }).parserProofWorker = new Worker(url, {
        type: 'module',
      });
    },
    new URL('/assets/' + asset, page.url()).href,
  );
  const worker = await workerReady;
  try {
    await expect
      .poll(() => worker.evaluate(() => typeof self.onmessage), { timeout: 10000 })
      .toBe('function');
    await worker.evaluate(() => {
      const scope = globalThis as unknown as DedicatedWorkerGlobalScope;
      scope.addEventListener('message', (event) => {
        // These are observed protocol facts for the test oracle, not an application origin allowlist.
        scope.postMessage({ parserProof: true, origin: event.origin, sourceNull: event.source === null });
      });
    });
    const observed = await page.evaluate(async () => {
      const owned = (window as unknown as { parserProofWorker: Worker }).parserProofWorker;
      const marker = crypto.randomUUID();
      return await new Promise<{
        parsed: { text: string };
        metadata: { origin: string; sourceNull: boolean };
      }>((resolve, reject) => {
        let parsed: { text: string } | undefined;
        let metadata: { origin: string; sourceNull: boolean } | undefined;
        const timer = setTimeout(() => reject(new Error('Dedicated parser proof timed out')), 10000);
        const reply = (event: MessageEvent) => {
          if (event.data.parserProof) metadata = event.data;
          else if (event.data.error) {
            clearTimeout(timer);
            reject(new Error('Actual parser rejected the synthetic text'));
          } else parsed = event.data;
          if (parsed && metadata) {
            clearTimeout(timer);
            owned.removeEventListener('message', reply);
            resolve({ parsed, metadata });
          }
        };
        owned.addEventListener('message', reply);
        const windowAck = (event: MessageEvent) => {
          if (event.origin !== location.origin || event.source !== window || event.data.marker !== marker)
            return;
          window.removeEventListener('message', windowAck);
          owned.postMessage({ filename: 'synthetic.txt', content: btoa('Synthetic Python project') });
        };
        window.addEventListener('message', windowAck);
        window.postMessage(
          { marker, filename: 'injected.txt', content: btoa('Window injection must not parse') },
          location.origin,
        );
      });
    });
    expect(observed.parsed.text).toBe('Synthetic Python project');
    expect(observed.metadata).toMatchObject({ origin: '', sourceNull: true });
  } finally {
    await page.evaluate(() => {
      (window as unknown as { parserProofWorker: Worker }).parserProofWorker.terminate();
    });
  }
});

/** Actual owner-only comparison/export stays browser-local and matches independent Python assessments. */
test('private comparison exports citations and unknowns without plaintext requests or writes', async ({
  page,
}) => {
  await signUp(page);
  await unlock(page);
  await loadExamples(page);
  await expect(page.locator('.sidebar small')).toContainText('v0.3.1');
  expect((await (await page.request.get('/health')).json()).version).toBe('0.3.1');
  await page.getByRole('button', { name: 'Review A101', exact: true }).click();
  await page.getByText('Edit normalized record / consent', { exact: true }).click();
  const editor = page.getByLabel('Normalized applicant JSON');
  const edited = JSON.parse(await editor.inputValue());
  edited.evidence[0].summary = '<img src="https://unexpected.example/pixel"> synthetic evidence';
  edited.sources[0].label = 'Source <script>not executable</script>';
  await editor.fill(JSON.stringify(edited));
  await page.getByRole('button', { name: 'Validate & save record', exact: true }).click();
  await expect(page.getByRole('status')).toContainText('Record saved');
  const before = await (await page.request.get('/vault/workspace')).json();
  const requests: string[] = [];
  page.on('request', (request) => {
    if (
      request.url().includes('/api/') ||
      request.method() === 'PUT' ||
      new URL(request.url()).origin !== new URL(page.url()).origin
    )
      requests.push(request.url());
  });
  await page.getByLabel('Compare A101', { exact: true }).check();
  await page.getByLabel('Compare A102', { exact: true }).check();
  await page.getByRole('button', { name: 'Capture selected evidence' }).click();
  const panel = page.getByRole('region', { name: 'Criterion evidence comparison', exact: true });
  await expect(panel.getByRole('button', { name: 'Download private comparison JSON' })).toBeVisible();
  await expect(panel).toContainText('<img src="https://unexpected.example/pixel"> synthetic evidence');
  await expect(panel.locator('img, script, iframe')).toHaveCount(0);
  const pending = page.waitForEvent('download');
  await panel.getByRole('button', { name: 'Download private comparison JSON' }).click();
  const report = JSON.parse(readFileSync((await (await pending).path())!, 'utf8'));
  const vectors = JSON.parse(readFileSync('tests/fixtures/parity.json', 'utf8'));
  for (const record of report.records) {
    const expected = vectors.find(
      (vector: { job: { id: string }; applicant: { id: string } }) =>
        vector.job.id === 'software' && vector.applicant.id === record.id,
    ).assessment;
    expect(record.score).toBe(expected.score);
    expect(report.rubric.hash).toBe(expected.rubric_hash);
    expect(
      record.criteria.map(
        (row: { skill: string; attainment: number; best_support: { evidence_id: string } | null }) => ({
          skill: row.skill,
          attainment: row.attainment,
          evidence_id: row.best_support?.evidence_id ?? null,
        }),
      ),
    ).toEqual(
      expected.criteria.map((row: { skill: string; attainment: number; evidence_id: string | null }) => ({
        skill: row.skill,
        attainment: row.attainment,
        evidence_id: row.evidence_id,
      })),
    );
    expect(record.record_sha256).toMatch(/^[0-9a-f]{64}$/);
    expect(record).not.toHaveProperty('rank');
    expect(record).not.toHaveProperty('display_name');
    expect(record).not.toHaveProperty('sources');
  }
  expect((await new AxeBuilder({ page }).include('.comparison-card').analyze()).violations).toEqual([]);
  expect(requests).toEqual([]);
  expect((await (await page.request.get('/vault/workspace')).json()).revision).toBe(before.revision);
  await page.getByRole('button', { name: 'Lock workspace' }).click();
  await expect(page.getByRole('button', { name: 'Download private comparison JSON' })).toHaveCount(0);
  await expect(page.getByLabel('Compare A101', { exact: true })).toHaveCount(0);
});

test('browser reports match all 18 Python reference assessments', async ({ page, browser }) => {
  test.setTimeout(120000); // Eighteen complete unlock/review/export workflows, not one interaction.
  await signUp(page);
  await unlock(page);
  await loadExamples(page);
  const signedState = await page.context().storageState();
  const vectors = JSON.parse(readFileSync('tests/fixtures/parity.json', 'utf8'));
  for (const vector of vectors) {
    // One download per tab: do not disable Chromium's multiple-download protection
    // just to export 18 reports at machine speed. Still exercise every real UI export.
    const reportContext = await browser.newContext({ storageState: signedState });
    const reportPage = await reportContext.newPage();
    try {
      expect(reportPage.viewportSize()).toEqual(page.viewportSize());
      // Firefox can miss a lifecycle notification although the document, scripts
      // and account requests completed (200 in the retained synthetic trace).
      // Assert application readiness instead of waiting on that browser event.
      await reportPage.goto(page.url(), { waitUntil: 'commit', timeout: 10000 });
      await expect(reportPage.getByRole('heading', { name: 'Unlock your private workspace' })).toBeVisible();
      await unlock(reportPage);
      await reportPage.getByLabel('Selected role').selectOption(vector.job.id);
      await reportPage.getByRole('button', { name: 'Review ' + vector.applicant.id, exact: true }).click();
      const panel = reportPage.locator('details').filter({
        has: reportPage.getByRole('button', { name: 'Download advisory report', includeHidden: true }),
      });
      if ((await panel.getAttribute('open')) === null) await panel.locator('summary').click();
      const event = reportPage.waitForEvent('download', { timeout: 10000 });
      await reportPage.getByRole('button', { name: 'Download advisory report' }).click();
      const report = JSON.parse(readFileSync((await (await event).path())!, 'utf8'));
      for (const field of ['score', 'status', 'flags', 'required_gaps', 'criteria', 'rubric_hash', 'method'])
        expect(report[field], vector.job.id + '/' + vector.applicant.id + '/' + field).toEqual(
          vector.assessment[field],
        );
    } finally {
      await reportContext.close();
    }
  }
});

test.afterEach(async ({ page, request }, info) => {
  if (info.status === info.expectedStatus) return;
  // Only readiness/status metadata from this disposable service; never cookies or document bodies.
  try {
    console.log('Synthetic QA failure diagnostics', {
      profile: info.project.name,
      page: page.url(),
      health_status: (await request.get('/health', { timeout: 3000 })).status(),
      ui_status: (await request.get('/', { timeout: 3000 })).status(),
    });
  } catch {
    console.log('Synthetic QA diagnostic request unavailable');
  }
});

/** Create independent disposable accounts for every browser; never use real credentials. */
async function signUp(page: Page) {
  const alias = 'test_' + randomUUID().replaceAll('-', '').slice(0, 20);
  aliases.add(alias);
  await page.goto('/', { waitUntil: 'domcontentloaded' });
  await page.getByRole('button', { name: 'Create account', exact: true }).click();
  await page.getByLabel('Account alias', { exact: true }).fill(alias);
  await page.getByLabel('Login password', { exact: true }).fill(password);
  const registered = page.waitForResponse(
    (response) => response.url().endsWith('/vault/register') && response.request().method() === 'POST',
  );
  await page.getByRole('button', { name: 'Register account', exact: true }).click();
  expect((await registered).status(), 'real registration must succeed').toBe(200);
  await expect(page.getByRole('heading', { name: 'Unlock your private workspace' })).toBeVisible();
  await expect(page.getByRole('heading', { name: 'Save your login recovery code' })).toBeVisible();
  await page.getByRole('button', { name: 'I saved it privately' }).click();
  return alias;
}

/** Unlock with a distinct vault phrase; server login and document decryption are separate. */
async function unlock(page: Page, value = phrase) {
  await page.getByLabel('Vault phrase', { exact: true }).fill(value);
  await page.getByRole('button', { name: 'Unlock or create workspace' }).click();
  await expect(page.getByRole('heading', { name: 'Review queue', exact: true })).toBeVisible();
}

/** Load fictional examples only after an explicit replacement confirmation. */
async function loadExamples(page: Page) {
  await page.getByRole('button', { name: 'Account & backups' }).click();
  await page.getByLabel('Current vault phrase for replacement').fill(phrase);
  await page.getByLabel('I exported a backup and approve replacing the workspace').check();
  await page.getByRole('button', { name: 'Replace with fictional examples' }).click();
  await expect(page.getByRole('heading', { name: 'Unlock your private workspace' })).toBeVisible();
  await page.getByRole('button', { name: 'Account & backups' }).click();
  await unlock(page);
  await expect(page.getByRole('button', { name: 'Review A101', exact: true })).toBeVisible();
}

test('real accounts, ciphertext-only traffic, lock and independent-user isolation', async ({
  page,
  browser,
}) => {
  const requests: string[] = [];
  page.on('request', (request) => {
    if (request.method() === 'PUT') requests.push(request.postData() || '');
  });
  const alias = await signUp(page);
  await unlock(page);
  await loadExamples(page);
  expect(requests.length).toBeGreaterThan(0);
  for (const body of requests) {
    const parsed = JSON.parse(body);
    expect(Object.keys(parsed).sort()).toEqual(['envelope', 'revision']);
    expect(body).not.toContain('Morgan Rivera');
    expect(body).not.toContain(phrase);
    expect(Object.keys(parsed.envelope).sort()).toEqual(['ciphertext', 'iv', 'salt', 'version']);
  }
  expect(await page.evaluate(() => Object.keys(localStorage))).toEqual([]);
  expect(await page.evaluate(() => document.cookie)).not.toContain('session');
  await page.getByRole('button', { name: 'Lock workspace' }).click();
  await expect(page.getByRole('button', { name: 'Review A101', exact: true })).toHaveCount(0);
  await page.getByLabel('Vault phrase', { exact: true }).fill('wrong independent vault phrase');
  await page.getByRole('button', { name: 'Unlock or create workspace' }).click();
  await expect(page.getByRole('alert')).toContainText('Cannot unlock');
  await unlock(page);
  const context = await browser.newContext();
  const other = await context.newPage();
  await other.goto(page.url(), { waitUntil: 'domcontentloaded' });
  await signUp(other);
  await unlock(other);
  const result = await other.request.get('/vault/workspace');
  expect(result.status()).toBe(200);
  const otherVault = await result.json();
  const firstVault = await (await page.request.get('/vault/workspace')).json();
  expect(otherVault.envelope.ciphertext).not.toEqual(firstVault.envelope.ciphertext);
  await expect(other.getByRole('button', { name: 'Review A101', exact: true })).toHaveCount(0);
  await context.close();
  await page.getByRole('button', { name: 'Sign out', exact: true }).click();
  await expect(page.getByLabel('Account alias', { exact: true })).toBeVisible();
  await page.getByLabel('Account alias', { exact: true }).fill(alias);
  await page.getByLabel('Login password', { exact: true }).fill(password);
  const signedIn = page.waitForResponse(
    (response) => response.url().endsWith('/vault/login') && response.request().method() === 'POST',
  );
  await page.getByRole('button', { name: 'Sign in securely' }).click();
  expect((await signedIn).status(), 'real reauthentication must succeed').toBe(200);
  await unlock(page);
  await expect(page.getByRole('button', { name: 'Review A101', exact: true })).toBeVisible();
});

test('local document intake, professional evidence review, factual exports and no third-party calls', async ({
  page,
}) => {
  const destinations: string[] = [];
  page.on('request', (r) => destinations.push(new URL(r.url()).origin));
  await signUp(page);
  await unlock(page);
  await loadExamples(page);
  await page.getByRole('button', { name: 'Applicant intake', exact: true }).click();
  const marker = 'PRIVATE_RESUME_SENTINEL_DO_NOT_UPLOAD';
  await page.getByLabel('Choose resume file').setInputFiles({
    name: 'synthetic.txt',
    mimeType: 'text/plain',
    buffer: Buffer.from(marker + '\nProject: Python validation and testing'),
  });
  await expect(page.locator('pre').filter({ hasText: marker })).toBeVisible();
  await page.getByLabel('Applicant ID', { exact: true }).fill('B_private');
  await page.getByLabel('Applicant display name').fill('Private synthetic applicant');
  await page
    .getByLabel("I have authorization to process this applicant's supplied professional information")
    .check();
  const saves: string[] = [];
  page.on('request', (r) => {
    if (r.method() === 'PUT') saves.push(r.postData() || '');
  });
  await page.getByRole('button', { name: 'Save & review applicant' }).click();
  await expect(page.getByRole('heading', { name: 'Evidence & source review · B_private' })).toBeVisible();
  expect(saves.join('')).not.toContain(marker);
  expect(destinations.every((d) => d === new URL(page.url()).origin)).toBe(true);
  await page.getByRole('button', { name: 'Review A105', exact: true }).click();
  await page.getByRole('button', { name: 'Applicant coaching', exact: true }).click();
  const download = page.waitForEvent('download');
  await page.getByRole('button', { name: 'Download tailored resume draft' }).click();
  const file = await download;
  const text = readFileSync((await file.path())!, 'utf8');
  expect(text).toContain('coursework and projects are not converted into employment years');
  expect(text).not.toContain('<script');
  await expect(page.getByRole('button', { name: /Request AI coaching/ })).toBeDisabled();
});

test('browser DOCX/PDF parsing is local; malformed and scanned input stays uncertain', async ({ page }) => {
  await signUp(page);
  await unlock(page);
  await page.getByRole('button', { name: 'Applicant intake', exact: true }).click();
  const docx = zipSync({
    'word/document.xml': strToU8(
      '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:body><w:p><w:r><w:t>Project: Python &amp; testing</w:t></w:r></w:p></w:body></w:document>',
    ),
  });
  await page.getByLabel('Choose resume file').setInputFiles({
    name: 'synthetic.docx',
    mimeType: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    buffer: Buffer.from(docx),
  });
  await expect(page.locator('pre').filter({ hasText: 'Project: Python & testing' })).toBeVisible();
  await page.getByLabel('Choose resume file').setInputFiles({
    name: 'bad.pdf',
    mimeType: 'application/pdf',
    buffer: Buffer.from('malformed PRIVATE_TEXT'),
  });
  await expect(page.getByRole('alert')).toContainText('Cannot safely read');
  await page.getByLabel('Choose resume file').setInputFiles('tests/fixtures/synthetic-resume.pdf');
  await expect(page.locator('pre').filter({ hasText: 'Python' })).toBeVisible();
  await page.getByLabel('Choose resume file').setInputFiles({
    name: 'not-supported.html',
    mimeType: 'text/html',
    buffer: Buffer.from('<script>alert(1)</script>'),
  });
  await expect(page.getByRole('alert')).toContainText('Cannot safely read');
});

test('encrypted backup tamper detection, conflict protection and installed-web-app manifest', async ({
  page,
  browser,
}) => {
  await signUp(page);
  await unlock(page);
  await loadExamples(page);
  await page.getByRole('button', { name: 'Account & backups' }).click();
  const downloaded = page.waitForEvent('download');
  await page.getByRole('button', { name: 'Download encrypted backup' }).click();
  const backup = JSON.parse(readFileSync((await (await downloaded).path())!, 'utf8'));
  expect(JSON.stringify(backup)).not.toContain('Morgan Rivera');
  await page.getByLabel('Current vault phrase for replacement').fill(phrase);
  await page.getByLabel('I exported a backup and approve replacing the workspace').check();
  backup.ciphertext = (backup.ciphertext[0] === 'A' ? 'B' : 'A') + backup.ciphertext.slice(1);
  await page.getByLabel('Restore encrypted backup').setInputFiles({
    name: 'tampered.json',
    mimeType: 'application/json',
    buffer: Buffer.from(JSON.stringify(backup)),
  });
  await expect(page.getByRole('alert')).toContainText('Cannot unlock');
  const manifest = await (await page.request.get('/manifest.webmanifest')).json();
  expect(manifest.display).toBe('standalone');
  expect(manifest.name).toContain('Jason Stys');
  expect(await page.evaluate(async () => !!(await navigator.serviceWorker.ready))).toBe(true);
  const state = await page.context().storageState();
  const context = await browser.newContext({ storageState: state });
  const second = await context.newPage();
  await second.goto(page.url(), { waitUntil: 'domcontentloaded' });
  await unlock(second);
  const observed = await (await page.request.get('/vault/workspace')).json();
  const changed = await second.request.put('/vault/workspace', {
    headers: { Origin: new URL(page.url()).origin, 'X-AES-Request': 'v1' },
    data: { envelope: observed.envelope, revision: observed.revision },
  });
  expect(changed.status()).toBe(200);
  await page.getByRole('button', { name: 'Account & backups' }).click();
  await page.getByRole('button', { name: 'Review A101', exact: true }).click();
  await page.getByRole('button', { name: 'Save evidence review' }).click();
  await expect(page.getByRole('alert')).toContainText('Another device changed');
  await context.close();
});

test('accessible sign-in and private workspace, author contact and account deletion', async ({
  page,
}, info) => {
  await page.goto('/', { waitUntil: 'domcontentloaded' });
  await expect(page.getByRole('button', { name: 'Create account', exact: true })).toBeVisible();
  expect((await new AxeBuilder({ page }).analyze()).violations).toEqual([]);
  await signUp(page);
  await unlock(page);
  await loadExamples(page);
  expect((await new AxeBuilder({ page }).analyze()).violations).toEqual([]);
  await page.screenshot({ path: 'artifacts/private-' + info.project.name + '.png', fullPage: true });
  await page.getByRole('button', { name: 'Account & backups' }).click();
  await page.getByLabel('Current login password for deletion').fill(password);
  await page.getByLabel('I approve permanent account deletion').check();
  await page.getByRole('button', { name: 'Permanently delete my account' }).click();
  await expect(page.getByLabel('Account alias', { exact: true })).toBeVisible();
  expect((await page.request.get('/vault/account')).status()).toBe(401);
});
