import { defineConfig, devices } from '@playwright/test';
import './setup';

/**
 * Optimized configuration for Playwright UI mode
 * Faster startup and better performance
 */
export default defineConfig({
  testDir: './',
  /* Run tests in files in parallel */
  fullyParallel: false, // Disable parallel for UI mode
  /* Fail the build on CI if you accidentally left test.only in the source code. */
  forbidOnly: false,
  /* No retries in UI mode */
  retries: 0,
  /* Single worker for UI mode */
  workers: 1,
  /* Shorter timeout for UI mode */
  timeout: 15000,
  
  /* Reporter optimized for UI */
  reporter: [
    ['html', { open: 'never' }], // Don't auto-open HTML report
    ['list'] // Simple list reporter
  ],
  
  /* Shared settings optimized for UI mode */
  use: {
    /* Base URL to use in actions like `await page.goto('/')`. */
    baseURL: process.env.HA_URL || 'http://localhost:8123',
    /* No trace in UI mode for speed */
    trace: 'off',
    /* No screenshots in UI mode for speed */
    screenshot: 'off',
    /* No video in UI mode for speed */
    video: 'off',
    /* Faster timeouts */
    actionTimeout: 5000,
    navigationTimeout: 10000,
  },

  /* Only Chromium for UI mode - faster startup */
  projects: [
    {
      name: 'chromium',
      use: { 
        ...devices['Desktop Chrome'],
        // Faster browser options
        launchOptions: {
          args: [
            '--no-sandbox',
            '--disable-dev-shm-usage',
            '--disable-gpu',
            '--disable-web-security',
            '--disable-features=VizDisplayCompositor'
          ]
        }
      },
    },
  ],

  /* WebServer removed - using Home Assistant directly */
});


















