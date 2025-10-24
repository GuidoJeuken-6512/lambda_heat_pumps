// Load environment variables
import dotenv from 'dotenv';
dotenv.config();

// Central configuration for Playwright tests
export const config = {
  // Home Assistant Configuration
  ha: {
    url: process.env.HA_URL || 'http://localhost:8123',
    username: process.env.HA_USERNAME || 'playwright',
    password: process.env.HA_PASSWORD || 'halo&71',
    token: process.env.HA_TOKEN || 'your-long-lived-access-token',
  },
  
  // Playwright Configuration
  playwright: {
    headless: process.env.HEADLESS === 'true' || true,
    browser: process.env.BROWSER || 'chromium',
    timeout: parseInt(process.env.TIMEOUT || '30000'),
  },
  
  // Test Configuration
  test: {
    env: process.env.TEST_ENV || 'development',
    debug: process.env.DEBUG === 'true' || false,
  }
};

// Helper functions for configuration
export const getHAConfig = () => config.ha;
export const getPlaywrightConfig = () => config.playwright;
export const getTestConfig = () => config.test;

// Environment validation
export const validateConfig = () => {
  const ha = config.ha;
  
  if (!ha.url) {
    throw new Error('HA_URL is required');
  }
  
  if (!ha.username) {
    throw new Error('HA_USERNAME is required');
  }
  
  if (!ha.password) {
    throw new Error('HA_PASSWORD is required');
  }
  
  console.log('✅ Configuration validated successfully');
  console.log(`   HA URL: ${ha.url}`);
  console.log(`   HA Username: ${ha.username}`);
  console.log(`   Test Environment: ${config.test.env}`);
  
  return true;
};
