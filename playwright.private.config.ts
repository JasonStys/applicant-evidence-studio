// Purpose: Jason Stys — real-account privacy, crypto, parser, mobile and installability browser matrix.
// Index: defineConfig@3, devices@3, origin@4
import { defineConfig, devices } from '@playwright/test';
const origin = 'http://127.0.0.1:' + (process.env.AES_PRIVATE_TEST_PORT || '8025');
export default defineConfig({
  testDir: 'tests',
  testMatch: 'private.spec.ts',
  fullyParallel: false,
  workers: 1,
  timeout: 60000,
  reporter: [['list'], ['html', { outputFolder: 'playwright-report/private', open: 'never' }]],
  use: { baseURL: origin, trace: 'retain-on-failure' },
  webServer: {
    command: 'python scripts/private_browser_server.py',
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
