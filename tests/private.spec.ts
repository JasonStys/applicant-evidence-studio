// Purpose: Jason Stys — end-to-end real accounts, encrypted sync, local parsing, exports and isolation.
// Index: Page@3, expect@3, test@3, AxeBuilder@4, strToU8@5, zipSync@5, readFileSync@6, randomUUID@7, password@8, phrase@9, aliases@10, page@12, vectors@16, vector@17, reportPage@20, panel@26, event@30, report@32, field@33, page@44, signUp@44, alias@45, registered@51, response@52, page@63, unlock@63, value@63, loadExamples@70, page@70, page@82, browser@83, requests@85, request@86, alias@89, body@93, parsed@94, context@108, other@109, result@113, otherVault@115, firstVault@116, signedIn@124, response@125, page@134, destinations@136, r@137, marker@142, saves@154, r@155, d@161, download@164, file@166, text@167, page@173, docx@177, page@205, browser@206, downloaded@212, backup@214, manifest@225, state@229, context@230, second@231, observed@234, changed@235, page@248, info@249
import { test, expect, type Page } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';
import { zipSync, strToU8 } from 'fflate';
import { readFileSync } from 'node:fs';
import { randomUUID } from 'node:crypto';
const password = 'synthetic-only-login-password-2026';
const phrase = 'six random synthetic words keep documents private';
const aliases = new Set<string>();

test('browser reports match all 18 Python reference assessments', async ({ page }) => {
  await signUp(page);
  await unlock(page);
  await loadExamples(page);
  const vectors = JSON.parse(readFileSync('tests/fixtures/parity.json', 'utf8'));
  for (const vector of vectors) {
    // One download per tab: do not disable Chromium's multiple-download protection
    // just to export 18 reports at machine speed. Still exercise every real UI export.
    const reportPage = await page.context().newPage();
    try {
      await reportPage.goto(page.url());
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
      await reportPage.close();
    }
  }
});

/** Create independent disposable accounts for every browser; never use real credentials. */
async function signUp(page: Page) {
  const alias = 'test_' + randomUUID().replaceAll('-', '').slice(0, 20);
  aliases.add(alias);
  await page.goto('/');
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
  await other.goto(page.url());
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
  await second.goto(page.url());
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
  await page.goto('/');
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
