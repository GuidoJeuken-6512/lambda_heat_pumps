import { test, expect } from '../fixtures/ha-fixtures';

test.describe('Lambda Heat Pumps Dashboard Tests', () => {
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

  test('should display lambda heat pumps entities', async ({ page }) => {
    // Navigate to entities page
    await page.click('ha-sidebar a[href="/config"]');
    await page.click('ha-config-navigation a[href="/config/entities"]');
    
    // Search for lambda heat pumps entities
    await page.fill('ha-search-input input', 'lambda');
    
    // Check if entities are visible
    const entities = page.locator('ha-entity-registry-table ha-entity-registry-table-row');
    await expect(entities.first()).toBeVisible();
    
    // Verify entity names contain lambda
    const entityNames = await entities.locator('mwc-list-item').allTextContents();
    const lambdaEntities = entityNames.filter(name => 
      name.toLowerCase().includes('lambda') || 
      name.toLowerCase().includes('heat pump')
    );
    
    expect(lambdaEntities.length).toBeGreaterThan(0);
    console.log(`✅ Found ${lambdaEntities.length} Lambda Heat Pump entities`);
  });

  test('should create lambda heat pumps dashboard card', async ({ page }) => {
    // Navigate to dashboard
    await page.click('ha-sidebar a[href="/lovelace"]');
    
    // Click edit dashboard
    await page.click('ha-button[title="Edit Dashboard"]');
    
    // Add new card
    await page.click('ha-button[title="Add Card"]');
    
    // Select entities card
    await page.click('ha-card-picker ha-card-picker-card[type="entities"]');
    
    // Configure card
    await page.fill('ha-card-picker ha-card-picker-card[type="entities"] input', 'Lambda Heat Pumps');
    
    // Add lambda entities to card
    const entityPicker = page.locator('ha-entity-picker');
    await entityPicker.click();
    
    // Search for lambda entities
    await page.fill('ha-entity-picker input', 'lambda');
    
    // Select first lambda entity
    const firstEntity = page.locator('ha-entity-picker mwc-list-item').first();
    await firstEntity.click();
    
    // Save card
    await page.click('ha-button[title="Save"]');
    
    // Verify card was created
    await expect(page.locator('ha-card[header="Lambda Heat Pumps"]')).toBeVisible();
  });

  test('should test lambda heat pumps climate controls', async ({ page }) => {
    // Navigate to entities
    await page.click('ha-sidebar a[href="/config"]');
    await page.click('ha-config-navigation a[href="/config/entities"]');
    
    // Search for climate entities
    await page.fill('ha-search-input input', 'climate.lambda');
    
    const climateEntities = page.locator('ha-entity-registry-table ha-entity-registry-table-row');
    
    if (await climateEntities.count() > 0) {
      // Click on first climate entity
      await climateEntities.first().click();
      
      // Check if entity details are visible
      await expect(page.locator('ha-entity-editor')).toBeVisible();
      
      // Verify entity type is climate
      const entityType = page.locator('ha-entity-editor ha-formfield[label="Entity ID"] input');
      await expect(entityType).toHaveValue(/^climate\./);
      
      console.log('✅ Lambda Heat Pump climate entity found and accessible');
    } else {
      console.log('ℹ️ No Lambda Heat Pump climate entities found');
    }
  });

  test('should test lambda heat pumps sensor data', async ({ page }) => {
    // Navigate to developer tools
    await page.click('ha-sidebar a[href="/developer-tools"]');
    
    // Go to states tab
    await page.click('ha-tabs ha-tab[role="tab"]:has-text("States")');
    
    // Search for lambda entities
    await page.fill('ha-search-input input', 'lambda');
    
    const stateEntities = page.locator('ha-state-picker mwc-list-item');
    
    if (await stateEntities.count() > 0) {
      // Check first lambda entity state
      const firstEntity = stateEntities.first();
      await firstEntity.click();
      
      // Verify state data is displayed
      await expect(page.locator('ha-state-info')).toBeVisible();
      
      // Check if state has valid data
      const stateValue = page.locator('ha-state-info .state-value');
      await expect(stateValue).toBeVisible();
      
      console.log('✅ Lambda Heat Pump sensor data accessible');
    } else {
      console.log('ℹ️ No Lambda Heat Pump sensor entities found');
    }
  });
});



