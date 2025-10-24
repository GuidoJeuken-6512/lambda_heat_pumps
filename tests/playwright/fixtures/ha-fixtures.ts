import { test as base, expect } from '@playwright/test';
import axios from 'axios';
import { getHAConfig, validateConfig } from '../config';

export interface HomeAssistantFixtures {
  haApi: any;
  haToken: string;
  haUrl: string;
  haUsername: string;
  haPassword: string;
}

export const test = base.extend<HomeAssistantFixtures>({
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

  haToken: async ({}, use) => {
    const config = getHAConfig();
    await use(config.token);
  },

  haApi: async ({ haUrl, haToken }, use) => {
    const api = axios.create({
      baseURL: `${haUrl}/api`,
      headers: {
        'Authorization': `Bearer ${haToken}`,
        'Content-Type': 'application/json',
      },
    });

    // Test API connection
    try {
      await api.get('/');
      console.log('✅ Home Assistant API connection successful');
    } catch (error) {
      console.error('❌ Home Assistant API connection failed:', error);
      throw error;
    }

    await use(api);
  },
});

export { expect };



