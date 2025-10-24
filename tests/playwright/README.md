# Playwright Tests für Lambda Heat Pumps

Diese Test-Suite umfasst alle drei Playwright-Testarten für das Lambda Heat Pumps Home Assistant Custom Component.

## Test-Arten

### 1. E2E Tests (End-to-End Tests)
- **Datei**: `tests/playwright/e2e/`
- **Zweck**: Vollständige Benutzer-Workflows testen
- **Beispiele**:
  - Home Assistant Login
  - Dashboard Navigation
  - Lambda Heat Pumps Integration
  - Entity Management
  - Climate Controls

### 2. API Tests
- **Datei**: `tests/playwright/api/`
- **Zweck**: REST API und Backend-Funktionalität testen
- **Beispiele**:
  - Home Assistant API Konfiguration
  - Entity States abrufen
  - Service Calls testen
  - Modbus-Verbindung prüfen
  - Energieverbrauch-Sensoren validieren

### 3. Visual Regression Tests
- **Datei**: `tests/playwright/visual/`
- **Zweck**: UI-Änderungen erkennen und Screenshots vergleichen
- **Beispiele**:
  - Dashboard Layout
  - Lambda Heat Pumps Cards
  - Climate Controls
  - Sensor Visualizations
  - Mobile Responsiveness

## Setup

### 1. Dependencies installieren
```bash
npm install
```

### 2. Playwright Browser installieren
```bash
npm run test:install
```

### 3. Environment Variables setzen
```bash
# .env Datei erstellen
HA_URL=http://localhost:8123
HA_USERNAME=admin
HA_PASSWORD=password
HA_TOKEN=your-long-lived-access-token
```

## Test-Ausführung

### Alle Tests ausführen
```bash
npm test
```

### Spezifische Test-Arten
```bash
# E2E Tests
npm run test:e2e

# API Tests
npm run test:api

# Visual Tests
npm run test:visual
```

### Interaktive Tests
```bash
# UI Mode
npm run test:ui

# Headed Mode (Browser sichtbar)
npm run test:headed

# Debug Mode
npm run test:debug
```

### Test Reports
```bash
# HTML Report anzeigen
npm run test:report
```

## Test-Konfiguration

### Browser Support
- Chrome/Chromium
- Firefox
- Safari/WebKit
- Microsoft Edge
- Mobile Chrome
- Mobile Safari

### Test-Features
- **Parallel Execution**: Tests laufen parallel für bessere Performance
- **Retry Logic**: Automatische Wiederholung bei Fehlern
- **Screenshots**: Automatische Screenshots bei Fehlern
- **Video Recording**: Video-Aufnahme bei Fehlern
- **Trace Viewer**: Detaillierte Test-Traces für Debugging

## Test-Struktur

```
tests/playwright/
├── fixtures/
│   └── ha-fixtures.ts          # Home Assistant Test-Fixtures
├── e2e/
│   ├── home-assistant-login.spec.ts
│   └── lambda-heat-pumps-dashboard.spec.ts
├── api/
│   ├── home-assistant-api.spec.ts
│   └── lambda-heat-pumps-modbus.spec.ts
├── visual/
│   ├── dashboard-visual.spec.ts
│   └── lambda-heat-pumps-visual.spec.ts
└── README.md
```

## Test-Daten

### Lambda Heat Pumps Entities
Die Tests suchen nach folgenden Entity-Typen:
- `climate.lambda_*` - Klima-Entitäten
- `sensor.lambda_*` - Sensor-Entitäten
- `binary_sensor.lambda_*` - Binary Sensor-Entitäten
- `switch.lambda_*` - Switch-Entitäten

### Erwartete Sensoren
- Temperatur-Sensoren
- Energieverbrauch-Sensoren
- Betriebsmodus-Sensoren
- Zyklus-Sensoren
- Power-Consumption-Sensoren

## CI/CD Integration

### GitHub Actions
```yaml
name: Playwright Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
      - run: npm install
      - run: npm run test:install
      - run: npm test
```

### Docker Support
```dockerfile
FROM mcr.microsoft.com/playwright:v1.40.0-focal
COPY . .
RUN npm install
CMD ["npm", "test"]
```

## Debugging

### Test-Debugging
```bash
# Einzelnen Test debuggen
npx playwright test tests/playwright/e2e/home-assistant-login.spec.ts --debug

# Spezifischen Test debuggen
npx playwright test --grep "should login to Home Assistant" --debug
```

### Trace Viewer
```bash
# Trace anzeigen
npx playwright show-trace test-results/trace.zip
```

### Screenshots und Videos
- Screenshots: `test-results/`
- Videos: `test-results/`
- Traces: `test-results/`

## Best Practices

### Test-Writing
1. **Atomic Tests**: Jeder Test sollte unabhängig sein
2. **Clear Assertions**: Klare und spezifische Assertions
3. **Proper Waiting**: Warten auf Elemente statt feste Delays
4. **Data Cleanup**: Tests sollten sich selbst aufräumen

### Performance
1. **Parallel Execution**: Tests parallel ausführen
2. **Selective Testing**: Nur relevante Tests ausführen
3. **Resource Management**: Browser-Ressourcen effizient nutzen

### Maintenance
1. **Regular Updates**: Playwright regelmäßig aktualisieren
2. **Test Review**: Tests regelmäßig überprüfen
3. **Documentation**: Test-Dokumentation aktuell halten

## Troubleshooting

### Häufige Probleme
1. **Login-Fehler**: HA_URL, HA_USERNAME, HA_PASSWORD prüfen
2. **API-Fehler**: HA_TOKEN prüfen
3. **Element nicht gefunden**: Wartezeiten erhöhen
4. **Screenshot-Fehler**: Animations deaktivieren

### Debug-Commands
```bash
# Browser starten
npx playwright codegen

# Test-Report anzeigen
npx playwright show-report

# Trace anzeigen
npx playwright show-trace
```





