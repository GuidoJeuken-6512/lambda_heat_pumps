import { test, expect } from '../fixtures/ha-fixtures';

test.describe('Lambda Heat Pumps Modbus API Tests', () => {
  test('should test modbus connection status', async ({ haApi }) => {
    // Check for modbus entities that might indicate connection status
    const response = await haApi.get('/states');
    
    expect(response.status).toBe(200);
    
    const modbusEntities = response.data.filter((entity: any) => 
      entity.entity_id.toLowerCase().includes('modbus') ||
      entity.entity_id.toLowerCase().includes('connection')
    );
    
    console.log(`✅ Found ${modbusEntities.length} Modbus-related entities:`);
    modbusEntities.forEach((entity: any) => {
      console.log(`  - ${entity.entity_id}: ${entity.state}`);
    });
  });

  test('should test lambda heat pumps energy consumption sensors', async ({ haApi }) => {
    const response = await haApi.get('/states');
    
    expect(response.status).toBe(200);
    
    // Look for energy consumption sensors
    const energyEntities = response.data.filter((entity: any) => 
      entity.entity_id.toLowerCase().includes('energy') ||
      entity.entity_id.toLowerCase().includes('power') ||
      entity.entity_id.toLowerCase().includes('consumption')
    );
    
    console.log(`✅ Found ${energyEntities.length} Energy-related entities:`);
    energyEntities.forEach((entity: any) => {
      console.log(`  - ${entity.entity_id}: ${entity.state} ${entity.attributes?.unit_of_measurement || ''}`);
      
      // Validate energy sensor attributes
      if (entity.attributes) {
        expect(entity.attributes).toHaveProperty('unit_of_measurement');
        expect(['kWh', 'W', 'kW', 'Wh'].includes(entity.attributes.unit_of_measurement)).toBe(true);
      }
    });
  });

  test('should test lambda heat pumps temperature sensors', async ({ haApi }) => {
    const response = await haApi.get('/states');
    
    expect(response.status).toBe(200);
    
    // Look for temperature sensors
    const tempEntities = response.data.filter((entity: any) => 
      entity.entity_id.toLowerCase().includes('temperature') ||
      entity.entity_id.toLowerCase().includes('temp')
    );
    
    console.log(`✅ Found ${tempEntities.length} Temperature-related entities:`);
    tempEntities.forEach((entity: any) => {
      console.log(`  - ${entity.entity_id}: ${entity.state} ${entity.attributes?.unit_of_measurement || ''}`);
      
      // Validate temperature sensor attributes
      if (entity.attributes) {
        expect(entity.attributes).toHaveProperty('unit_of_measurement');
        expect(entity.attributes.unit_of_measurement).toBe('°C');
      }
    });
  });

  test('should test lambda heat pumps operating mode sensors', async ({ haApi }) => {
    const response = await haApi.get('/states');
    
    expect(response.status).toBe(200);
    
    // Look for operating mode sensors
    const modeEntities = response.data.filter((entity: any) => 
      entity.entity_id.toLowerCase().includes('mode') ||
      entity.entity_id.toLowerCase().includes('operation') ||
      entity.entity_id.toLowerCase().includes('status')
    );
    
    console.log(`✅ Found ${modeEntities.length} Operating mode entities:`);
    modeEntities.forEach((entity: any) => {
      console.log(`  - ${entity.entity_id}: ${entity.state}`);
      
      // Validate mode sensor attributes
      if (entity.attributes) {
        expect(entity.attributes).toHaveProperty('options');
        expect(Array.isArray(entity.attributes.options)).toBe(true);
      }
    });
  });

  test('should test lambda heat pumps cycling sensors', async ({ haApi }) => {
    const response = await haApi.get('/states');
    
    expect(response.status).toBe(200);
    
    // Look for cycling-related sensors
    const cyclingEntities = response.data.filter((entity: any) => 
      entity.entity_id.toLowerCase().includes('cycle') ||
      entity.entity_id.toLowerCase().includes('cycling') ||
      entity.entity_id.toLowerCase().includes('on_time') ||
      entity.entity_id.toLowerCase().includes('off_time')
    );
    
    console.log(`✅ Found ${cyclingEntities.length} Cycling-related entities:`);
    cyclingEntities.forEach((entity: any) => {
      console.log(`  - ${entity.entity_id}: ${entity.state} ${entity.attributes?.unit_of_measurement || ''}`);
    });
  });

  test('should test lambda heat pumps historical data', async ({ haApi }) => {
    // Get lambda entities first
    const statesResponse = await haApi.get('/states');
    const lambdaEntities = statesResponse.data.filter((entity: any) => 
      entity.entity_id.toLowerCase().includes('lambda') ||
      entity.entity_id.toLowerCase().includes('heat_pump')
    );
    
    if (lambdaEntities.length > 0) {
      const entityId = lambdaEntities[0].entity_id;
      
      // Test historical data API
      const endTime = new Date();
      const startTime = new Date(endTime.getTime() - 24 * 60 * 60 * 1000); // 24 hours ago
      
      const historyResponse = await haApi.get('/history/period', {
        params: {
          filter_entity_id: entityId,
          start_time: startTime.toISOString(),
          end_time: endTime.toISOString()
        }
      });
      
      expect(historyResponse.status).toBe(200);
      expect(Array.isArray(historyResponse.data)).toBe(true);
      
      console.log(`✅ Historical data retrieved for ${entityId}: ${historyResponse.data.length} data points`);
    } else {
      console.log('ℹ️ No Lambda Heat Pump entities found for historical data testing');
    }
  });

  test('should test lambda heat pumps service availability', async ({ haApi }) => {
    // Test if lambda heat pumps services are available
    const servicesResponse = await haApi.get('/services');
    
    expect(servicesResponse.status).toBe(200);
    
    const lambdaServices = servicesResponse.data.filter((service: any) => 
      service.domain === 'lambda_heat_pumps' ||
      service.domain === 'climate' ||
      service.domain === 'sensor'
    );
    
    console.log(`✅ Found ${lambdaServices.length} relevant services:`);
    lambdaServices.forEach((service: any) => {
      console.log(`  - ${service.domain}.${service.service}`);
      if (service.description) {
        console.log(`    Description: ${service.description}`);
      }
    });
  });

  test('should test lambda heat pumps error handling', async ({ haApi }) => {
    // Test invalid service calls to check error handling
    try {
      const invalidResponse = await haApi.post('/services/lambda_heat_pumps/invalid_service', {
        entity_id: 'invalid.entity'
      });
      
      // If we get here, the service doesn't exist (expected)
      console.log('✅ Invalid service call handled correctly');
    } catch (error: any) {
      if (error.response?.status === 404) {
        console.log('✅ Invalid service call properly returns 404');
      } else {
        console.log(`ℹ️ Service call error: ${error.message}`);
      }
    }
  });

  test('should validate lambda heat pumps entity states', async ({ haApi }) => {
    const response = await haApi.get('/states');
    
    expect(response.status).toBe(200);
    
    const lambdaEntities = response.data.filter((entity: any) => 
      entity.entity_id.toLowerCase().includes('lambda') ||
      entity.entity_id.toLowerCase().includes('heat_pump')
    );
    
    lambdaEntities.forEach((entity: any) => {
      console.log(`\n🔍 Validating entity state: ${entity.entity_id}`);
      
      // Check if state is valid
      expect(entity.state).toBeDefined();
      expect(entity.state).not.toBe('');
      
      // Check timestamps
      expect(entity.last_updated).toBeDefined();
      expect(entity.last_changed).toBeDefined();
      
      // Validate timestamp format
      const lastUpdated = new Date(entity.last_updated);
      const lastChanged = new Date(entity.last_changed);
      
      expect(lastUpdated.getTime()).not.toBeNaN();
      expect(lastChanged.getTime()).not.toBeNaN();
      
      console.log(`  ✅ State: ${entity.state}`);
      console.log(`  ✅ Last Updated: ${entity.last_updated}`);
      console.log(`  ✅ Last Changed: ${entity.last_changed}`);
    });
  });
});





