---
title: "Manuelle Installation"
---

# Manuelle Installation

Diese Anleitung beschreibt, wie Sie die Lambda Heat Pumps Integration manuell ohne HACS installieren können.

!!! tip "Einfachere Installation mit HACS"
    Falls Sie HACS bereits installiert haben, können Sie die Integration einfacher über HACS installieren. 
    Siehe: [Installation über HACS](../anwender/installation.md#installation-der-lambda-heat-pumps-integration)

## Voraussetzungen

- Zugriff auf Ihre Home Assistant Installation (SSH, Terminal oder Dateizugriff)
- Kenntnisse im Umgang mit Dateisystemen und Git

## Installation

### 1. GitHub Repository öffnen

Öffnen Sie das GitHub Repository der Lambda Heat Pumps Integration:

**Repository URL:** [https://github.com/GuidoJeuken-6512/lambda_heat_pumps](https://github.com/GuidoJeuken-6512/lambda_heat_pumps){:target="_blank" rel="noopener noreferrer"}

### 2. Branch auswählen

1. Klicken Sie auf das **Branch-Dropdown-Menü** (standardmäßig zeigt es "main" oder den aktuellen Branch)
2. Wählen Sie den gewünschten Branch:
   - **`main`**: Stabile Version (empfohlen für Produktionsumgebungen)
   - **`dev`** oder andere Branches: Entwicklungsversionen (nur für Tests)

### 3. Repository herunterladen

Sie haben mehrere Möglichkeiten, das Repository herunterzuladen:

#### Option A: ZIP-Datei herunterladen (einfachste Methode)

1. Klicken Sie auf den grünen Button **"Code"** oben rechts im Repository
2. Wählen Sie **"Download ZIP"**
3. Entpacken Sie die ZIP-Datei auf Ihrem Computer

#### Option B: Git Clone (für Entwickler)

```bash
git clone https://github.com/GuidoJeuken-6512/lambda_heat_pumps.git
cd lambda_heat_pumps
git checkout main  # oder den gewünschten Branch
```

### 4. Integration in Home Assistant kopieren

1. **Navigieren Sie zum `custom_components` Verzeichnis:**
   - **Home Assistant Operating System / Supervised:**
     - Pfad: `/config/custom_components/`
   - **Container:**
     - Pfad: `/config/custom_components/` (innerhalb des Containers)
   - **Core:**
     - Pfad: `<home-assistant-config>/custom_components/`

2. **Erstellen Sie das Verzeichnis (falls es nicht existiert):**
   ```bash
   mkdir -p /config/custom_components
   ```

3. **Kopieren Sie den Integration-Ordner:**
   - Aus dem heruntergeladenen Repository kopieren Sie den gesamten Ordner `custom_components/lambda_heat_pumps/`
   - Ziel: `/config/custom_components/lambda_heat_pumps/`
   
   **Struktur sollte so aussehen:**
   ```
   /config/
     └── custom_components/
         └── lambda_heat_pumps/
             ├── __init__.py
             ├── manifest.json
             ├── config_flow.py
             └── ... (weitere Dateien)
   ```

4. **Berechtigungen setzen (falls nötig):**
   ```bash
   chmod -R 755 /config/custom_components/lambda_heat_pumps
   ```

### 5. Home Assistant neu starten

1. Starten Sie Home Assistant vollständig neu
2. Dies ist erforderlich, damit die Integration erkannt wird

### 6. Integration einrichten

Nach dem Neustart:

1. Gehen Sie zu **Einstellungen** → **Geräte & Dienste**
2. Klicken Sie auf **Integration hinzufügen**
3. Suchen Sie nach **"Lambda Heat Pumps"**
4. Folgen Sie den Anweisungen zur Konfiguration

## Aktualisierung

Um die Integration zu aktualisieren:

1. Laden Sie die neueste Version vom GitHub Repository herunter
2. Ersetzen Sie den Inhalt des Ordners `/config/custom_components/lambda_heat_pumps/` mit der neuen Version
3. Starten Sie Home Assistant neu

**Hinweis:** Bei Verwendung von Git können Sie auch einfach einen `git pull` im Repository-Verzeichnis durchführen und die Dateien erneut kopieren.

## Fehlerbehebung

### Integration wird nicht erkannt

- Überprüfen Sie, ob der Ordner `lambda_heat_pumps` direkt unter `custom_components/` liegt
- Überprüfen Sie, ob die Datei `manifest.json` im Ordner vorhanden ist
- Überprüfen Sie die Home Assistant Logs auf Fehlermeldungen
- Stellen Sie sicher, dass Home Assistant vollständig neu gestartet wurde

### Berechtigungsfehler

- Stellen Sie sicher, dass der Benutzer, der Home Assistant ausführt, Lese- und Ausführungsrechte auf den Dateien hat
- Verwenden Sie `chmod -R 755` auf dem `lambda_heat_pumps` Ordner

## Weitere Informationen

- [GitHub Repository](https://github.com/GuidoJeuken-6512/lambda_heat_pumps){:target="_blank" rel="noopener noreferrer"}
- [Releases](https://github.com/GuidoJeuken-6512/lambda_heat_pumps/releases){:target="_blank" rel="noopener noreferrer"}

