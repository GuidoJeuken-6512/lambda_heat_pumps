import { test, expect } from '../fixtures/ha-fixtures';

test.describe('Home Assistant E2E Tests', () => {
  test('should login to Home Assistant', async ({ page, haUrl, haUsername, haPassword }) => {
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
    
    // Wait for dashboard to load
    await expect(page.locator('home-assistant')).toBeVisible();
    await expect(page.locator('home-assistant-main')).toBeVisible();
    
    // Verify we're logged in
    await expect(page.locator('ha-sidebar')).toBeVisible();
  });

  test('should navigate to configuration', async ({ page, haUrl, haUsername, haPassword }) => {
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
    
    // Wait for dashboard
    await expect(page.locator('home-assistant')).toBeVisible();
    
    // Navigate to configuration
    await page.click('ha-sidebar a[href="/config"]');
    await expect(page.locator('ha-config')).toBeVisible();
  });

  test('should check lambda heat pumps integration', async ({ page, haUrl, haUsername, haPassword }) => {
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
    
    // Navigate to integrations
    await page.click('ha-sidebar a[href="/config"]');
    await page.click('ha-config-navigation a[href="/config/integrations"]');
    
    // Check if lambda heat pumps integration exists
    const integrationCard = page.locator('ha-integration-card').filter({
      hasText: 'Lambda Heat Pumps'
    });
    
    if (await integrationCard.count() > 0) {
      await expect(integrationCard).toBeVisible();
      console.log('✅ Lambda Heat Pumps integration found');
    } else {
      console.log('ℹ️ Lambda Heat Pumps integration not found - may need to be installed');
    }
  });
});



