import { test, expect } from '../fixtures/ha-fixtures';

test.describe('Lambda Heat Pumps Visual Regression Tests', () => {
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

  test('should match lambda heat pumps climate control visual', async ({ page }) => {
    // Navigate to dashboard
    await page.click('ha-sidebar a[href="/lovelace"]');
    
    // Look for climate entities
    const climateEntities = page.locator('ha-card').filter({
      hasText: 'climate'
    });
    
    if (await climateEntities.count() > 0) {
      // Take screenshot of climate control
      await expect(climateEntities.first()).toHaveScreenshot('lambda-climate-control.png', {
        animations: 'disabled'
      });
    } else {
      console.log('ℹ️ No climate entities found for visual testing');
    }
  });

  test('should match lambda heat pumps sensor cards visual', async ({ page }) => {
    // Navigate to dashboard
    await page.click('ha-sidebar a[href="/lovelace"]');
    
    // Look for sensor cards
    const sensorCards = page.locator('ha-card').filter({
      hasText: 'sensor'
    });
    
    if (await sensorCards.count() > 0) {
      // Take screenshot of sensor cards
      await expect(sensorCards.first()).toHaveScreenshot('lambda-sensor-cards.png', {
        animations: 'disabled'
      });
    } else {
      console.log('ℹ️ No sensor cards found for visual testing');
    }
  });

  test('should match lambda heat pumps energy consumption visual', async ({ page }) => {
    // Navigate to dashboard
    await page.click('ha-sidebar a[href="/lovelace"]');
    
    // Look for energy consumption cards
    const energyCards = page.locator('ha-card').filter({
      hasText: 'energy'
    });
    
    if (await energyCards.count() > 0) {
      // Take screenshot of energy consumption
      await expect(energyCards.first()).toHaveScreenshot('lambda-energy-consumption.png', {
        animations: 'disabled'
      });
    } else {
      console.log('ℹ️ No energy consumption cards found for visual testing');
    }
  });

  test('should match lambda heat pumps temperature sensors visual', async ({ page }) => {
    // Navigate to dashboard
    await page.click('ha-sidebar a[href="/lovelace"]');
    
    // Look for temperature sensor cards
    const tempCards = page.locator('ha-card').filter({
      hasText: 'temperature'
    });
    
    if (await tempCards.count() > 0) {
      // Take screenshot of temperature sensors
      await expect(tempCards.first()).toHaveScreenshot('lambda-temperature-sensors.png', {
        animations: 'disabled'
      });
    } else {
      console.log('ℹ️ No temperature sensor cards found for visual testing');
    }
  });

  test('should match lambda heat pumps operating mode visual', async ({ page }) => {
    // Navigate to dashboard
    await page.click('ha-sidebar a[href="/lovelace"]');
    
    // Look for operating mode cards
    const modeCards = page.locator('ha-card').filter({
      hasText: 'mode'
    });
    
    if (await modeCards.count() > 0) {
      // Take screenshot of operating mode
      await expect(modeCards.first()).toHaveScreenshot('lambda-operating-mode.png', {
        animations: 'disabled'
      });
    } else {
      console.log('ℹ️ No operating mode cards found for visual testing');
    }
  });

  test('should match lambda heat pumps cycling sensors visual', async ({ page }) => {
    // Navigate to dashboard
    await page.click('ha-sidebar a[href="/lovelace"]');
    
    // Look for cycling sensor cards
    const cyclingCards = page.locator('ha-card').filter({
      hasText: 'cycle'
    });
    
    if (await cyclingCards.count() > 0) {
      // Take screenshot of cycling sensors
      await expect(cyclingCards.first()).toHaveScreenshot('lambda-cycling-sensors.png', {
        animations: 'disabled'
      });
    } else {
      console.log('ℹ️ No cycling sensor cards found for visual testing');
    }
  });

  test('should match lambda heat pumps power consumption visual', async ({ page }) => {
    // Navigate to dashboard
    await page.click('ha-sidebar a[href="/lovelace"]');
    
    // Look for power consumption cards
    const powerCards = page.locator('ha-card').filter({
      hasText: 'power'
    });
    
    if (await powerCards.count() > 0) {
      // Take screenshot of power consumption
      await expect(powerCards.first()).toHaveScreenshot('lambda-power-consumption.png', {
        animations: 'disabled'
      });
    } else {
      console.log('ℹ️ No power consumption cards found for visual testing');
    }
  });

  test('should match lambda heat pumps historical data visual', async ({ page }) => {
    // Navigate to dashboard
    await page.click('ha-sidebar a[href="/lovelace"]');
    
    // Look for historical data cards
    const historyCards = page.locator('ha-card').filter({
      hasText: 'history'
    });
    
    if (await historyCards.count() > 0) {
      // Take screenshot of historical data
      await expect(historyCards.first()).toHaveScreenshot('lambda-historical-data.png', {
        animations: 'disabled'
      });
    } else {
      console.log('ℹ️ No historical data cards found for visual testing');
    }
  });

  test('should match lambda heat pumps configuration visual', async ({ page }) => {
    // Navigate to configuration
    await page.click('ha-sidebar a[href="/config"]');
    await page.click('ha-config-navigation a[href="/config/integrations"]');
    
    // Look for lambda heat pumps integration
    const lambdaIntegration = page.locator('ha-integration-card').filter({
      hasText: 'Lambda Heat Pumps'
    });
    
    if (await lambdaIntegration.count() > 0) {
      // Click on integration
      await lambdaIntegration.click();
      
      // Take screenshot of integration configuration
      await expect(page.locator('ha-integration-panel')).toHaveScreenshot('lambda-integration-config.png', {
        animations: 'disabled'
      });
    } else {
      console.log('ℹ️ Lambda Heat Pumps integration not found for visual testing');
    }
  });

  test('should match lambda heat pumps entity registry visual', async ({ page }) => {
    // Navigate to entities
    await page.click('ha-sidebar a[href="/config"]');
    await page.click('ha-config-navigation a[href="/config/entities"]');
    
    // Search for lambda entities
    await page.fill('ha-search-input input', 'lambda');
    
    // Take screenshot of entity registry
    await expect(page.locator('ha-entity-registry-table')).toHaveScreenshot('lambda-entity-registry.png', {
      animations: 'disabled'
    });
  });

  test('should match lambda heat pumps service calls visual', async ({ page }) => {
    // Navigate to developer tools
    await page.click('ha-sidebar a[href="/developer-tools"]');
    
    // Go to services tab
    await page.click('ha-tabs ha-tab[role="tab"]:has-text("Services")');
    
    // Search for lambda services
    await page.fill('ha-service-picker input', 'lambda');
    
    // Take screenshot of services
    await expect(page.locator('ha-panel-developer-tools')).toHaveScreenshot('lambda-service-calls.png', {
      animations: 'disabled'
    });
  });

  test('should match lambda heat pumps events visual', async ({ page }) => {
    // Navigate to developer tools
    await page.click('ha-sidebar a[href="/developer-tools"]');
    
    // Go to events tab
    await page.click('ha-tabs ha-tab[role="tab"]:has-text("Events")');
    
    // Search for lambda events
    await page.fill('ha-event-picker input', 'lambda');
    
    // Take screenshot of events
    await expect(page.locator('ha-panel-developer-tools')).toHaveScreenshot('lambda-events.png', {
      animations: 'disabled'
    });
  });

  test('should match lambda heat pumps logs visual', async ({ page }) => {
    // Navigate to developer tools
    await page.click('ha-sidebar a[href="/developer-tools"]');
    
    // Go to logs tab
    await page.click('ha-tabs ha-tab[role="tab"]:has-text("Logs")');
    
    // Search for lambda logs
    await page.fill('ha-log-picker input', 'lambda');
    
    // Take screenshot of logs
    await expect(page.locator('ha-panel-developer-tools')).toHaveScreenshot('lambda-logs.png', {
      animations: 'disabled'
    });
  });
});



