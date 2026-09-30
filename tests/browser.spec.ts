// Purpose: real-browser reviewer, applicant intake, job editing, source review and download regressions.
// Index: expect@3, test@3, AxeBuilder@4, page@6, page@12, page@35, pending@39, result@41, info@49, page@49, info@71, page@71, page@85, stage@86, result@90, info@97, page@97, page@103
import { test, expect } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';

test.beforeEach(async ({ page }) => {
  await page.goto('/#token=synthetic_browser_session_0123456789_abcdef');
  await expect(page.getByRole('heading', { name: 'Evidence-ranked queue' })).toBeVisible();
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
