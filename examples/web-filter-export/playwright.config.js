const { defineConfig } = require('@playwright/test');

module.exports = defineConfig({
  testDir: './browser-tests',
  fullyParallel: false,
  workers: 1,
  retries: 0,
  timeout: 15000,
  outputDir: '.runs/playwright',
  reporter: [['list'], ['json', { outputFile: '.runs/playwright-report.json' }]],
  use: {
    baseURL: 'http://127.0.0.1:8765',
    browserName: 'chromium',
    trace: process.env.CAPTURE_BROWSER_EVIDENCE === '1' ? 'retain-on-failure' : 'off',
    screenshot: process.env.CAPTURE_BROWSER_EVIDENCE === '1' ? 'only-on-failure' : 'off',
  },
  webServer: {
    command: 'python3 server.py --port 8765 --log-dir .runs/browser-server',
    url: 'http://127.0.0.1:8765/health',
    reuseExistingServer: false,
    timeout: 10000,
  },
});
