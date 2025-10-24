import { test, expect } from '../fixtures/ha-fixtures';

test.describe('Home Assistant API Tests', () => {
  test('should get Home Assistant configuration', async ({ haApi }) => {
    const response = await haApi.get('/config');
    
    expect(response.status).toBe(200);
    expect(response.data).toHaveProperty('location_name');
    expect(response.data).toHaveProperty('time_zone');
    expect(response.data).toHaveProperty('version');
    
    console.log(`✅ HA Version: ${response.data.version}`);
    console.log(`✅ Location: ${response.data.location_name}`);
  });

  test('should get Home Assistant states', async ({ haApi }) => {
    const response = await haApi.get('/states');
    
    expect(response.status).toBe(200);
    expect(Array.isArray(response.data)).toBe(true);
    expect(response.data.length).toBeGreaterThan(0);
    
    console.log(`✅ Found ${response.data.length} entities`);
  });

  test('should get lambda heat pumps entities', async ({ haApi }) => {
    const response = await haApi.get('/states');
    
    expect(response.status).toBe(200);
    
    // Filter lambda heat pumps entities
    const lambdaEntities = response.data.filter((entity: any) => 
      entity.entity_id.toLowerCase().includes('lambda') ||
      entity.entity_id.toLowerCase().includes('heat_pump')
    );
    
    console.log(`✅ Found ${lambdaEntities.length} Lambda Heat Pump entities:`);
    lambdaEntities.forEach((entity: any) => {
      console.log(`  - ${entity.entity_id}: ${entity.state}`);
    });
    
    expect(lambdaEntities.length).toBeGreaterThan(0);
  });

  test('should get lambda heat pumps climate entities', async ({ haApi }) => {
    const response = await haApi.get('/states');
    
    expect(response.status).toBe(200);
    
    // Filter climate entities
    const climateEntities = response.data.filter((entity: any) => 
      entity.entity_id.startsWith('climate.') &&
      (entity.entity_id.toLowerCase().includes('lambda') ||
       entity.entity_id.toLowerCase().includes('heat_pump'))
    );
    
    console.log(`✅ Found ${climateEntities.length} Lambda Heat Pump climate entities:`);
    climateEntities.forEach((entity: any) => {
      console.log(`  - ${entity.entity_id}: ${entity.state}`);
      if (entity.attributes) {
        console.log(`    Attributes: ${JSON.stringify(entity.attributes, null, 2)}`);
      }
    });
  });

  test('should get lambda heat pumps sensor entities', async ({ haApi }) => {
    const response = await haApi.get('/states');
    
    expect(response.status).toBe(200);
    
    // Filter sensor entities
    const sensorEntities = response.data.filter((entity: any) => 
      entity.entity_id.startsWith('sensor.') &&
      (entity.entity_id.toLowerCase().includes('lambda') ||
       entity.entity_id.toLowerCase().includes('heat_pump'))
    );
    
    console.log(`✅ Found ${sensorEntities.length} Lambda Heat Pump sensor entities:`);
    sensorEntities.forEach((entity: any) => {
      console.log(`  - ${entity.entity_id}: ${entity.state} ${entity.attributes?.unit_of_measurement || ''}`);
    });
  });

  test('should test lambda heat pumps service calls', async ({ haApi }) => {
    // Get climate entities first
    const statesResponse = await haApi.get('/states');
    const climateEntities = statesResponse.data.filter((entity: any) => 
      entity.entity_id.startsWith('climate.') &&
      (entity.entity_id.toLowerCase().includes('lambda') ||
       entity.entity_id.toLowerCase().includes('heat_pump'))
    );
    
    if (climateEntities.length > 0) {
      const entityId = climateEntities[0].entity_id;
      
      // Test set temperature service
      const setTempResponse = await haApi.post('/services/climate/set_temperature', {
        entity_id: entityId,
        temperature: 22
      });
      
      expect(setTempResponse.status).toBe(200);
      console.log(`✅ Successfully called set_temperature for ${entityId}`);
      
      // Test set HVAC mode
      const setModeResponse = await haApi.post('/services/climate/set_hvac_mode', {
        entity_id: entityId,
        hvac_mode: 'heat'
      });
      
      expect(setModeResponse.status).toBe(200);
      console.log(`✅ Successfully called set_hvac_mode for ${entityId}`);
    } else {
      console.log('ℹ️ No Lambda Heat Pump climate entities found for service testing');
    }
  });

  test('should get lambda heat pumps integration info', async ({ haApi }) => {
    const response = await haApi.get('/config');
    
    expect(response.status).toBe(200);
    
    // Check if lambda heat pumps is in integrations
    const integrationsResponse = await haApi.get('/config/config_entries');
    
    expect(integrationsResponse.status).toBe(200);
    
    const lambdaIntegrations = integrationsResponse.data.filter((entry: any) => 
      entry.domain === 'lambda_heat_pumps' ||
      entry.title?.toLowerCase().includes('lambda') ||
      entry.title?.toLowerCase().includes('heat pump')
    );
    
    console.log(`✅ Found ${lambdaIntegrations.length} Lambda Heat Pump integrations:`);
    lambdaIntegrations.forEach((integration: any) => {
      console.log(`  - ${integration.title} (${integration.domain})`);
      console.log(`    State: ${integration.state}`);
      console.log(`    Source: ${integration.source}`);
    });
  });

  test('should test lambda heat pumps webhook/event handling', async ({ haApi }) => {
    // Test if we can trigger events
    const eventResponse = await haApi.post('/events/lambda_heat_pump_test', {
      test: true,
      timestamp: new Date().toISOString()
    });
    
    expect(eventResponse.status).toBe(200);
    console.log('✅ Lambda Heat Pump event handling test successful');
  });

  test('should validate lambda heat pumps entity attributes', async ({ haApi }) => {
    const response = await haApi.get('/states');
    
    expect(response.status).toBe(200);
    
    const lambdaEntities = response.data.filter((entity: any) => 
      entity.entity_id.toLowerCase().includes('lambda') ||
      entity.entity_id.toLowerCase().includes('heat_pump')
    );
    
    lambdaEntities.forEach((entity: any) => {
      console.log(`\n🔍 Validating entity: ${entity.entity_id}`);
      console.log(`  State: ${entity.state}`);
      console.log(`  Last Updated: ${entity.last_updated}`);
      console.log(`  Last Changed: ${entity.last_changed}`);
      
      if (entity.attributes) {
        console.log(`  Attributes:`);
        Object.entries(entity.attributes).forEach(([key, value]) => {
          console.log(`    ${key}: ${value}`);
        });
        
        // Validate required attributes for climate entities
        if (entity.entity_id.startsWith('climate.')) {
          expect(entity.attributes).toHaveProperty('hvac_modes');
          expect(entity.attributes).toHaveProperty('current_temperature');
          expect(entity.attributes).toHaveProperty('temperature');
          console.log(`  ✅ Climate entity attributes validated`);
        }
        
        // Validate required attributes for sensor entities
        if (entity.entity_id.startsWith('sensor.')) {
          expect(entity.attributes).toHaveProperty('unit_of_measurement');
          console.log(`  ✅ Sensor entity attributes validated`);
        }
      }
    });
  });
});





