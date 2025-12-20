---
title: "Installation"
---

# Installation

## Voraussetzungen

### HACS Installation

Die Lambda Heat Pumps Integration wird über HACS (Home Assistant Community Store) installiert. HACS ist ein Add-on für Home Assistant, das die Installation und Verwaltung von benutzerdefinierten Integrationen, Themes und anderen Add-ons vereinfacht.

**HACS Installation:**

Die Installation von HACS hängt von Ihrer Home Assistant Installation ab:

- **Home Assistant Operating System / Supervised**: Verwenden Sie das HACS Add-on aus dem Add-on Store
- **Container**: Verwenden Sie das HACS Download-Skript im Terminal
- **Core**: Verwenden Sie das HACS Download-Skript im Terminal

Detaillierte Installationsanweisungen für alle Installationstypen finden Sie in der [HACS Dokumentation](https://www.hacs.xyz/docs/use/download/download/){:target="_blank" rel="noopener noreferrer"}.

**Nach der HACS Installation:**

1. Starten Sie Home Assistant neu
2. Gehen Sie zu **Einstellungen** → **Geräte & Dienste**
3. Klicken Sie auf **Integration hinzufügen** und suchen Sie nach "HACS"
4. Folgen Sie den Anweisungen zur Einrichtung von HACS

## Installation der Lambda Heat Pumps Integration

Nachdem HACS installiert und eingerichtet ist, können Sie die Lambda Heat Pumps Integration installieren:

1. **Öffnen Sie HACS:**
   - Gehen Sie zu **HACS** im Seitenmenü von Home Assistant
   - Oder navigieren Sie zu **Einstellungen** → **HACS**

2. **Integration suchen:**
   - Klicken Sie auf **Integrationen** (oder **Integrations**)
   - Klicken Sie auf die drei Punkte (⋮) oben rechts
   - Wählen Sie **Custom repositories** (Benutzerdefinierte Repositories)

3. **Repository hinzufügen:**
   - Geben Sie im Feld **Repository** ein: `https://github.com/GuidoJeuken-6512/lambda_heat_pumps`
   - Wählen Sie als **Category**: **Integration**
   - Klicken Sie auf **Add** (Hinzufügen)

4. **Integration installieren:**
   - Suchen Sie nach "Lambda Heat Pumps" oder "lambda heat pumps"
   - Klicken Sie auf die Integration
   - Klicken Sie auf **Download** (Herunterladen)
   - Warten Sie, bis der Download abgeschlossen ist

5. **Home Assistant neu starten:**
   - Starten Sie Home Assistant vollständig neu
   - Dies ist erforderlich, damit die Integration erkannt wird

6. **Integration einrichten:**
   - Nach dem Neustart gehen Sie zu **Einstellungen** → **Geräte & Dienste**
   - Klicken Sie auf **Integration hinzufügen**
   - Suchen Sie nach "Lambda Heat Pumps"
   - Folgen Sie den Anweisungen zur Konfiguration (siehe [Konfiguration](configuration.md))

## Nächste Schritte

Nach der erfolgreichen Installation können Sie:

- Die Integration konfigurieren (siehe [Konfiguration](configuration.md))
- Die verfügbaren Features erkunden (siehe [Features](features.md))
- Die Heizkurven-Konfiguration einrichten (siehe [Heizkurve](heating-curve.md))

