// Purpose: real-browser reviewer, applicant intake, job editing, source review and download regressions.
// Index: expect@3, test@3, AxeBuilder@4, readFileSync@5, page@7, info@13, page@13, captured@20, response@21, input@24, row@25, panel@29, pending@34, report@36, row@37, row@41, region@48, node@51, node@53, page@68, release@71, observed@72, held@73, resolve@73, requested@74, resolve@74, first@75, route@76, response@77, page@96, page@119, pending@123, result@125, info@133, page@133, info@155, page@155, page@169, stage@170, result@174, info@181, page@181, page@187
import { test, expect } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';
import { readFileSync } from 'node:fs';

test.beforeEach(async ({ page }) => {
  await page.goto('/#token=synthetic_browser_session_0123456789_abcdef');
  await expect(page.getByRole('heading', { name: 'Evidence-ranked queue' })).toBeVisible();
});

/** Compare an actual SQL capture, preserve user selection order, and discard stale rubric responses. */
test('two-record comparison uses one rubric and keeps source review human led', async ({ page }, info) => {
  await expect(page.locator('.sidebar small')).toContainText('v0.3.0');
  expect((await (await page.request.get('/health')).json()).version).toBe('0.3.0');
  await page.getByLabel('Compare A101', { exact: true }).check();
  expect(page.getByRole('button', { name: 'Capture selected evidence' })).toBeDisabled();
  await page.getByLabel('Compare A102', { exact: true }).check();
  expect(page.getByLabel('Compare A103', { exact: true })).toBeDisabled();
  const captured = page.waitForResponse(
    (response) => response.url().includes('/api/comparison?') && response.status() === 200,
  );
  await page.getByRole('button', { name: 'Capture selected evidence' }).click();
  const input = await (await captured).json();
  expect(input.applicants.map((row: { applicant: { id: string } }) => row.applicant.id)).toEqual([
    'A101',
    'A102',
  ]);
  const panel = page.getByRole('region', { name: 'Criterion evidence comparison', exact: true });
  await expect(panel.getByRole('button', { name: 'Download private comparison JSON' })).toBeVisible();
  await panel
    .getByLabel('Human review observations (optional, private export only)')
    .fill('Verify source contribution; ask an accessible work sample if needed.');
  const pending = page.waitForEvent('download');
  await panel.getByRole('button', { name: 'Download private comparison JSON' }).click();
  const report = JSON.parse(readFileSync((await (await pending).path())!, 'utf8'));
  expect(report.records.map((row: { id: string }) => row.id)).toEqual(['A101', 'A102']);
  expect(report.reviewer_observations).toContain('Verify source contribution');
  expect(
    report.records.every(
      (row: object) => !('display_name' in row) && !('rank' in row) && !('sources' in row),
    ),
  ).toBe(true);
  expect((await new AxeBuilder({ page }).include('.comparison-card').analyze()).violations).toEqual([]);
  if (info.project.name === 'chromium')
    await panel.screenshot({ path: 'artifacts/practical-20261109/comparison.png' });
  await page.setViewportSize({ width: 320, height: 800 });
  const region = page.getByRole('region', { name: 'Scrollable criterion comparison' });
  await region.focus();
  await expect(region).toBeFocused();
  expect(await region.evaluate((node) => node.scrollWidth > node.clientWidth)).toBe(true);
  await page.keyboard.press('ArrowRight');
  await expect.poll(() => region.evaluate((node) => node.scrollLeft)).toBeGreaterThan(0);
  await page.getByLabel('Selected role').selectOption('embedded');
  await expect(panel.getByRole('button', { name: 'Download private comparison JSON' })).toHaveCount(0);
  await panel.getByRole('button', { name: 'Capture selected evidence' }).click();
  await expect(panel.getByRole('button', { name: 'Download private comparison JSON' })).toBeVisible();
  await expect(panel.getByLabel('Human review observations (optional, private export only)')).toHaveValue('');
  await page.getByRole('button', { name: 'Clear comparison selection' }).click();
  await expect(panel).toHaveCount(0);
});

/** Delay a genuine backend response to model a user switching rubrics during hashing/fetch. */
test.describe('controlled response delay', () => {
  // Page routes cannot intercept requests owned by a service worker (Playwright network guide).
  // Only this fault-injection context blocks SW; all ordinary/PWA/private-account tests keep it enabled.
  test.use({ serviceWorkers: 'block' });
  test('comparison ignores an old in-flight rubric capture', async ({ page }) => {
    await page.getByLabel('Compare A101', { exact: true }).check();
    await page.getByLabel('Compare A102', { exact: true }).check();
    let release!: () => void;
    let observed!: () => void;
    const held = new Promise<void>((resolve) => (release = resolve)),
      requested = new Promise<void>((resolve) => (observed = resolve));
    let first = true;
    await page.route('**/api/comparison**', async (route) => {
      const response = await route.fetch();
      if (first) {
        first = false;
        observed();
        await held;
      }
      await route.fulfill({ response });
    });
    await page.getByRole('button', { name: 'Capture selected evidence' }).click();
    await requested;
    await page.getByLabel('Selected role').selectOption('embedded');
    release();
    await expect(page.getByRole('button', { name: 'Download private comparison JSON' })).toHaveCount(0);
    await page.getByRole('button', { name: 'Capture selected evidence' }).click();
    await expect(page.getByRole('button', { name: 'Download private comparison JSON' })).toBeVisible();
  });
});

/** Verify anonymous queue, review context and original transfer evidence. */
test('queue filters and transfer-aware source review', async ({ page }) => {
  await page.getByLabel('Search applicant ID or name').fill('A10');
  await expect(page.locator('tbody tr')).toHaveCount(6);
  await page.getByLabel('Search applicant ID or name').fill('A101');
  await expect(page.locator('tbody tr')).toHaveCount(1);
  await page.getByRole('button', { name: 'Review A101', exact: true }).click();
  await expect(page.getByRole('heading', { name: 'Evidence & source review · A101' })).toBeVisible();
  await page.getByText('Education / transitions', { exact: true }).click();
  await expect(
    page.locator('.education small').filter({ hasText: 'Changed major; credits transferred.' }),
  ).toBeVisible();
  await page.getByRole('button', { name: 'Save evidence review' }).click();
  await expect(page.getByRole('status')).toContainText('Record saved');
  await page.getByText('Edit education and transitions', { exact: true }).click();
  await expect(page.getByLabel('Education outcome 1')).toHaveValue('transferred');
  await page
    .getByLabel('Chronology / major change / degree notes 1')
    .fill('Changed major; credits transferred. No degree awarded by the first school is claimed.');
  await page.getByRole('button', { name: 'Save education context', exact: true }).click();
  await expect(page.getByRole('status')).toContainText('Record saved');
});

/** Exercise a real private HTML download and general/tailored applicant coaching. */
test('coaching factual download and no silent AI calls', async ({ page }) => {
  await page.getByRole('button', { name: 'Review A105', exact: true }).click();
  await page.getByRole('button', { name: 'Applicant coaching', exact: true }).click();
  await expect(page.getByRole('heading', { name: 'Portfolio demonstrations to add' })).toBeVisible();
  const pending = page.waitForEvent('download');
  await page.getByRole('button', { name: 'Download tailored resume draft' }).click();
  const result = await pending;
  expect(result.suggestedFilename()).toBe('resume-draft-A105.html');
  await expect(page.getByRole('button', { name: /Request AI coaching/ })).toBeDisabled();
  await page.getByLabel('General advice, without tailoring to a selected role').check();
  await expect(page.getByText('Select a role to see evidence-gap projects.', { exact: false })).toBeVisible();
});

/** Verify upload extraction creates unreviewed evidence and requires explicit authorization. */
test('synthetic text resume intake', async ({ page }, info) => {
  await page.getByRole('button', { name: 'Applicant intake', exact: true }).click();
  await page.getByLabel('Choose resume file').setInputFiles({
    name: 'synthetic.txt',
    mimeType: 'text/plain',
    buffer: Buffer.from('Synthetic applicant\nProject: Python implementation with validation'),
  });
  await expect(page.getByLabel('Applicant ID', { exact: true })).toBeVisible();
  await page.getByLabel('Applicant ID', { exact: true }).fill('B_' + info.project.name);
  await page.getByLabel('Applicant display name').fill('Synthetic test record');
  await expect(page.getByRole('button', { name: 'Save & review applicant' })).toBeDisabled();
  await page
    .getByLabel("I have authorization to process this applicant's supplied professional information")
    .check();
  await page.getByRole('button', { name: 'Save & review applicant' }).click();
  await expect(
    page.getByRole('heading', { name: 'Evidence & source review · B_' + info.project.name }),
  ).toBeVisible();
  await expect(page.getByLabel('I checked this claim against its source')).not.toBeChecked();
});

/** Confirm criteria recommendations remain editable drafts and can be saved explicitly. */
test('job criteria draft and approved save', async ({ page }, info) => {
  await page.getByRole('button', { name: 'Job criteria', exact: true }).click();
  await page.getByRole('button', { name: 'New role', exact: true }).click();
  await page.getByLabel('Job ID', { exact: true }).fill('job_' + info.project.name);
  await page.getByLabel('Job title', { exact: true }).fill('Synthetic analyst');
  await page.getByLabel('Job description / required qualifications').fill('Python SQL testing');
  await page.getByRole('button', { name: 'Suggest draft criteria' }).click();
  await expect(page.getByRole('status')).toContainText('Draft');
  await expect(page.locator('.criterion')).toHaveCount(3);
  await page.getByRole('button', { name: 'Save approved rubric' }).click();
  await expect(page.getByRole('status')).toContainText('Job rubric saved');
});

/** Check automated accessibility on the core surface, selected record and coaching. */
test('accessibility and responsive layout', async ({ page }) => {
  for (const stage of ['queue', 'record', 'coaching']) {
    if (stage === 'record') await page.getByRole('button', { name: 'Review A101', exact: true }).click();
    if (stage === 'coaching')
      await page.getByRole('button', { name: 'Applicant coaching', exact: true }).click();
    const result = await new AxeBuilder({ page }).withTags(['wcag2a', 'wcag2aa', 'wcag21aa']).analyze();
    expect(result.violations).toEqual([]);
  }
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1)).toBe(true);
});

/** Capture the genuine built UI as a local verification artifact. */
test('visual evidence', async ({ page }, info) => {
  await page.screenshot({ path: 'artifacts/' + info.project.name + '-queue.png', fullPage: true });
  await expect(page.getByRole('heading', { name: 'Review queue', exact: true })).toBeVisible();
});

/** A new launcher session link must replace a stale token even in an existing browser tab. */
test('session link replaces stale authorization', async ({ page }) => {
  await page.goto('/#token=invalid_session_for_test');
  await expect(page.getByRole('heading', { name: 'Authorize this local session' })).toBeVisible();
  await page.goto('/#token=synthetic_browser_session_0123456789_abcdef');
  await expect(page.getByRole('heading', { name: 'Evidence-ranked queue' })).toBeVisible();
});
