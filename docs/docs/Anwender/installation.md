---
title: "Installation"
---

# Installation

## Voraussetzungen

### HACS Installation

Die Lambda Wärmepumpen Integration wird über den HACS (Home Assistant Community Store) installiert. HACS ist ein Add-on für Home Assistant, das die Installation und Verwaltung von benutzerdefinierten Integrationen, Themes und anderen Add-ons vereinfacht.

**HACS Installation:**

Die Installation von HACS hängt von Ihrer Home Assistant Installation ab:

- **Home Assistant Operating System / Supervised**: Verwenden Sie das HACS Add-on aus dem Add-on Store
- **Container**: Verwenden Sie das HACS Download-Skript im Terminal
- **Core**: Verwenden Sie das HACS Download-Skript im Terminal

Detaillierte Installationsanweisungen für alle Installationstypen finden Sie in der [HACS Dokumentation](https://www.hacs.xyz/docs/use/download/download/){:target="_blank" rel="noopener noreferrer"}.

**Nach der HACS Installation:**


## Installation der Lambda Wärmepumpen Integration

Nachdem HACS installiert und eingerichtet ist, können Sie die Lambda Wärmepumpen Integration installieren:

1. **Öffnen Sie HACS:**
   - Gehen Sie zu **HACS** im Seitenmenü von Home Assistant
   - Oder navigieren Sie zu **Einstellungen** → **HACS**

2. **Integration installieren:**
   - Suchen Sie nach "Lambda Heat Pumps" oder "lambda heat pumps"
   - Klicken Sie auf die Integration
   - Klicken Sie auf **Download** (Herunterladen)
   - Warten Sie, bis der Download abgeschlossen ist

3. **Home Assistant neu starten:**
   - Starten Sie Home Assistant vollständig neu
   - Dies ist erforderlich, damit die Integration erkannt wird

4. **Integration einrichten:**
   - Nach dem Neustart gehen Sie zu **Einstellungen** → **Geräte & Dienste**
   - Klicken Sie auf **Integration hinzufügen**
   - Suchen Sie nach "Lambda Heat Pumps"
   - Folgen Sie den Anweisungen zur Konfiguration (siehe [initiale Konfiguration](initiale-konfiguration.md))

## Nächste Schritte

Nach der erfolgreichen Installation können Sie:

- Die Integration konfigurieren (siehe [initiale Konfiguration](initiale-konfiguration.md))
- Die verfügbaren Features erkunden (siehe [Features](features.md))
- Die Heizkurven-Konfiguration einrichten (siehe [Heizkurve](heizkurve.md))

