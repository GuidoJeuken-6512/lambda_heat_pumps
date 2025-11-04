import { test, expect } from './fixtures/fast-login';

test.describe('Quick Home Assistant Test', () => {
  test('should load Home Assistant quickly', async ({ page, haUrl, isLoggedIn }) => {
    // Navigate to Home Assistant
    await page.goto(haUrl);
    
    if (!isLoggedIn) {
      console.log('⚠️ Not logged in - this test will fail in UI mode');
      // Skip the test if not logged in
      test.skip();
    }
    
    // Wait for Home Assistant to load
    await expect(page.locator('home-assistant')).toBeVisible({ timeout: 10000 });
    
    // Check if sidebar is visible (indicates successful login)
    await expect(page.locator('ha-sidebar')).toBeVisible({ timeout: 5000 });
    
    console.log('✅ Home Assistant loaded successfully');
  });

  test('should navigate to dashboard', async ({ page, haUrl, isLoggedIn }) => {
    await page.goto(haUrl);
    
    if (!isLoggedIn) {
      test.skip();
    }
    
    // Navigate to dashboard
    await page.click('ha-sidebar a[href="/lovelace"]');
    
    // Wait for dashboard to load
    await expect(page.locator('hui-root')).toBeVisible({ timeout: 5000 });
    
    console.log('✅ Dashboard loaded successfully');
  });

  test('should check for lambda heat pumps entities', async ({ page, haUrl, isLoggedIn }) => {
    await page.goto(haUrl);
    
    if (!isLoggedIn) {
      test.skip();
    }
    
    // Navigate to entities
    await page.click('ha-sidebar a[href="/config"]');
    await page.click('ha-config-navigation a[href="/config/entities"]');
    
    // Search for lambda entities
    await page.fill('ha-search-input input', 'lambda');
    
    // Wait for search results
    await page.waitForTimeout(1000);
    
    // Check if any lambda entities are found
    const entities = page.locator('ha-entity-registry-table ha-entity-registry-table-row');
    const count = await entities.count();
    
    console.log(`✅ Found ${count} entities matching 'lambda'`);
    
    if (count > 0) {
      console.log('✅ Lambda Heat Pumps entities found');
    } else {
      console.log('ℹ️ No Lambda Heat Pumps entities found');
    }
  });
});


















