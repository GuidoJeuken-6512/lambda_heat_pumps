import { test, expect } from '../fixtures/ha-fixtures';

test.describe('Home Assistant Visual Regression Tests', () => {
  test.beforeEach(async ({ page, haUrl, haUsername, haPassword }) => {
    // Login to Home Assistant using OAuth flow
    await page.goto('http://localhost:8123/auth/authorize?response_type=code&redirect_uri=http%3A%2F%2Flocalhost%3A8123%2F%3Fauth_callback%3D1&client_id=http%3A%2F%2Flocalhost%3A8123%2F&state=eyJoYXNzVXJsIjoiaHR0cDovL2xvY2FsaG9zdDo4MTIzIiwiY2xpZW50SWQiOiJodHRwOi8vbG9jYWxob3N0OjgxMjMvIn0%3D');
    
    // Fill username
    await page.getByLabel('').fill(haUsername);
    await page.getByLabel('').press('Tab');
    
    // Fill password
    await page.locator('label').filter({ hasText: 'Passwort' }).click();
    await page.getByRole('textbox', { name: 'Passwort' }).fill(haPassword);
    
    // Click login button
    await page.getByRole('button', { name: 'Anmelden' }).click();
    
    // Wait for Home Assistant to load
    await expect(page.locator('home-assistant')).toBeVisible({ timeout: 30000 });
  });

  test('should match dashboard layout', async ({ page }) => {
    // Navigate to dashboard
    await page.click('ha-sidebar a[href="/lovelace"]');
    
    // Wait for dashboard to load
    await expect(page.locator('hui-root')).toBeVisible();
    
    // Take full page screenshot
    await expect(page).toHaveScreenshot('dashboard-layout.png', {
      fullPage: true,
      animations: 'disabled'
    });
  });

  test('should match lambda heat pumps card visual', async ({ page }) => {
    // Navigate to dashboard
    await page.click('ha-sidebar a[href="/lovelace"]');
    
    // Look for lambda heat pumps card
    const lambdaCard = page.locator('ha-card').filter({
      hasText: 'Lambda Heat Pumps'
    });
    
    if (await lambdaCard.count() > 0) {
      await expect(lambdaCard).toBeVisible();
      
      // Take screenshot of the card
      await expect(lambdaCard).toHaveScreenshot('lambda-heat-pumps-card.png', {
        animations: 'disabled'
      });
    } else {
      console.log('ℹ️ Lambda Heat Pumps card not found - creating test card');
      
      // Create a test card for visual testing
      await page.click('ha-button[title="Edit Dashboard"]');
      await page.click('ha-button[title="Add Card"]');
      await page.click('ha-card-picker ha-card-picker-card[type="entities"]');
      
      // Configure card
      await page.fill('ha-card-picker ha-card-picker-card[type="entities"] input', 'Lambda Heat Pumps Test');
      await page.click('ha-button[title="Save"]');
      
      // Take screenshot of the new card
      const testCard = page.locator('ha-card').filter({
        hasText: 'Lambda Heat Pumps Test'
      });
      await expect(testCard).toHaveScreenshot('lambda-heat-pumps-test-card.png', {
        animations: 'disabled'
      });
    }
  });

  test('should match climate entity card visual', async ({ page }) => {
    // Navigate to entities
    await page.click('ha-sidebar a[href="/config"]');
    await page.click('ha-config-navigation a[href="/config/entities"]');
    
    // Search for climate entities
    await page.fill('ha-search-input input', 'climate.lambda');
    
    const climateEntities = page.locator('ha-entity-registry-table ha-entity-registry-table-row');
    
    if (await climateEntities.count() > 0) {
      // Take screenshot of climate entities table
      await expect(page.locator('ha-entity-registry-table')).toHaveScreenshot('climate-entities-table.png', {
        animations: 'disabled'
      });
      
      // Click on first climate entity
      await climateEntities.first().click();
      
      // Take screenshot of entity editor
      await expect(page.locator('ha-entity-editor')).toHaveScreenshot('climate-entity-editor.png', {
        animations: 'disabled'
      });
    } else {
      console.log('ℹ️ No Lambda Heat Pump climate entities found for visual testing');
    }
  });

  test('should match sensor entities visual', async ({ page }) => {
    // Navigate to entities
    await page.click('ha-sidebar a[href="/config"]');
    await page.click('ha-config-navigation a[href="/config/entities"]');
    
    // Search for sensor entities
    await page.fill('ha-search-input input', 'sensor.lambda');
    
    const sensorEntities = page.locator('ha-entity-registry-table ha-entity-registry-table-row');
    
    if (await sensorEntities.count() > 0) {
      // Take screenshot of sensor entities table
      await expect(page.locator('ha-entity-registry-table')).toHaveScreenshot('sensor-entities-table.png', {
        animations: 'disabled'
      });
    } else {
      console.log('ℹ️ No Lambda Heat Pump sensor entities found for visual testing');
    }
  });

  test('should match integrations page visual', async ({ page }) => {
    // Navigate to integrations
    await page.click('ha-sidebar a[href="/config"]');
    await page.click('ha-config-navigation a[href="/config/integrations"]');
    
    // Take screenshot of integrations page
    await expect(page.locator('ha-config-integrations')).toHaveScreenshot('integrations-page.png', {
      animations: 'disabled'
    });
    
    // Look for lambda heat pumps integration
    const lambdaIntegration = page.locator('ha-integration-card').filter({
      hasText: 'Lambda Heat Pumps'
    });
    
    if (await lambdaIntegration.count() > 0) {
      // Take screenshot of lambda integration card
      await expect(lambdaIntegration).toHaveScreenshot('lambda-integration-card.png', {
        animations: 'disabled'
      });
    }
  });

  test('should match developer tools visual', async ({ page }) => {
    // Navigate to developer tools
    await page.click('ha-sidebar a[href="/developer-tools"]');
    
    // Take screenshot of developer tools
    await expect(page.locator('ha-panel-developer-tools')).toHaveScreenshot('developer-tools.png', {
      animations: 'disabled'
    });
    
    // Go to states tab
    await page.click('ha-tabs ha-tab[role="tab"]:has-text("States")');
    
    // Search for lambda entities
    await page.fill('ha-search-input input', 'lambda');
    
    // Take screenshot of states page
    await expect(page.locator('ha-panel-developer-tools')).toHaveScreenshot('developer-tools-states.png', {
      animations: 'disabled'
    });
  });

  test('should match mobile dashboard visual', async ({ page }) => {
    // Set mobile viewport
    await page.setViewportSize({ width: 375, height: 667 });
    
    // Navigate to dashboard
    await page.click('ha-sidebar a[href="/lovelace"]');
    
    // Take mobile screenshot
    await expect(page).toHaveScreenshot('mobile-dashboard.png', {
      fullPage: true,
      animations: 'disabled'
    });
  });

  test('should match dark theme visual', async ({ page }) => {
    // Navigate to dashboard
    await page.click('ha-sidebar a[href="/lovelace"]');
    
    // Toggle dark theme if available
    const themeToggle = page.locator('ha-button[title="Toggle Theme"]');
    if (await themeToggle.count() > 0) {
      await themeToggle.click();
      
      // Take screenshot in dark theme
      await expect(page).toHaveScreenshot('dark-theme-dashboard.png', {
        fullPage: true,
        animations: 'disabled'
      });
    } else {
      console.log('ℹ️ Dark theme toggle not found');
    }
  });

  test('should match lambda heat pumps service call visual', async ({ page }) => {
    // Navigate to developer tools
    await page.click('ha-sidebar a[href="/developer-tools"]');
    
    // Go to services tab
    await page.click('ha-tabs ha-tab[role="tab"]:has-text("Services")');
    
    // Search for lambda services
    await page.fill('ha-service-picker input', 'lambda');
    
    // Take screenshot of services
    await expect(page.locator('ha-panel-developer-tools')).toHaveScreenshot('lambda-services.png', {
      animations: 'disabled'
    });
  });

  test('should match entity states visual', async ({ page }) => {
    // Navigate to developer tools
    await page.click('ha-sidebar a[href="/developer-tools"]');
    
    // Go to states tab
    await page.click('ha-tabs ha-tab[role="tab"]:has-text("States")');
    
    // Search for lambda entities
    await page.fill('ha-search-input input', 'lambda');
    
    // Select first lambda entity
    const firstEntity = page.locator('ha-state-picker mwc-list-item').first();
    if (await firstEntity.count() > 0) {
      await firstEntity.click();
      
      // Take screenshot of entity state info
      await expect(page.locator('ha-state-info')).toHaveScreenshot('lambda-entity-state.png', {
        animations: 'disabled'
      });
    }
  });
});



