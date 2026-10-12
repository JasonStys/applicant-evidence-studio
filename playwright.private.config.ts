// Purpose: Jason Stys — real-account privacy, crypto, parser, mobile and installability browser matrix.
// Index: defineConfig@3, devices@3, firstPort@4, profiles@7, index@12, profile@12, profile@25, profile@32
import { defineConfig, devices } from '@playwright/test';
const firstPort = Number(process.env.AES_PRIVATE_TEST_PORT || '8025');
// Keep each profile's disposable account database and abuse counters independent.
// The production limits stay enabled; a four-browser login burst is not one user.
const profiles = [
  { name: 'chromium', use: { ...devices['Desktop Chrome'] } },
  { name: 'firefox', use: { ...devices['Desktop Firefox'] } },
  { name: 'webkit', use: { ...devices['Desktop Safari'] } },
  { name: 'mobile', use: { ...devices['iPhone 13'], defaultBrowserType: 'chromium' as const } },
].map((profile, index) => ({
  ...profile,
  port: firstPort + index,
  origin: 'http://127.0.0.1:' + (firstPort + index),
}));
export default defineConfig({
  testDir: 'tests',
  testMatch: 'private.spec.ts',
  fullyParallel: false,
  workers: 1,
  timeout: 60000,
  reporter: [['list'], ['html', { outputFolder: 'playwright-report/private', open: 'never' }]],
  use: { trace: 'retain-on-failure' },
  webServer: profiles.map((profile) => ({
    command: 'python scripts/private_browser_server.py',
    env: { AES_PRIVATE_TEST_PORT: String(profile.port) },
    url: profile.origin + '/health',
    reuseExistingServer: false,
    timeout: 30000,
  })),
  projects: profiles.map((profile) => ({
    name: profile.name,
    use: { ...profile.use, baseURL: profile.origin },
  })),
});
