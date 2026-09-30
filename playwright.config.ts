// Purpose: isolated synthetic browser regression matrix; never uses a real applicant database.
// Index: defineConfig@3, devices@3, origin@4
import { defineConfig, devices } from '@playwright/test';
const origin = 'http://127.0.0.1:' + (process.env.AES_TEST_PORT || '8015');
export default defineConfig({
  testDir: 'tests',
  testMatch: 'browser.spec.ts',
  fullyParallel: false,
  workers: 1,
  reporter: [['list'], ['html', { open: 'never' }]],
  use: { baseURL: origin, trace: 'retain-on-failure' },
  webServer: {
    command: 'python scripts/browser_server.py',
    url: origin + '/health',
    reuseExistingServer: false,
    timeout: 30000,
  },
  projects: [
    { name: 'chromium', use: { ...devices['Desktop Chrome'] } },
    { name: 'firefox', use: { ...devices['Desktop Firefox'] } },
    { name: 'webkit', use: { ...devices['Desktop Safari'] } },
    { name: 'mobile', use: { ...devices['iPhone 13'], defaultBrowserType: 'chromium' } },
  ],
});
