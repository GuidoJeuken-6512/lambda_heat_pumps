import { test as base, expect } from '@playwright/test';
import { getHAConfig } from '../config';

export interface FastLoginFixtures {
  haUrl: string;
  haUsername: string;
  haPassword: string;
  isLoggedIn: boolean;
}

export const test = base.extend<FastLoginFixtures>({
  haUrl: async ({}, use) => {
    const config = getHAConfig();
    await use(config.url);
  },

  haUsername: async ({}, use) => {
    const config = getHAConfig();
    await use(config.username);
  },

  haPassword: async ({}, use) => {
    const config = getHAConfig();
    await use(config.password);
  },

  isLoggedIn: async ({ page, haUrl }, use) => {
    // Check if already logged in
    await page.goto(haUrl);
    
    // Wait for page to load
    await page.waitForLoadState('networkidle', { timeout: 5000 });
    
    // Check if we're already authenticated
    const isAuthenticated = await page.locator('home-assistant').isVisible({ timeout: 2000 }).catch(() => false);
    
    if (isAuthenticated) {
      console.log('✅ Already logged in to Home Assistant');
      await use(true);
    } else {
      console.log('ℹ️ Not logged in, will need authentication');
      await use(false);
    }
  },
});

export { expect };

















