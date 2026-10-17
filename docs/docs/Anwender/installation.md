---
title: "Installation"
---

# Installation

*Zuletzt geändert am 17.10.2026*

## Voraussetzungen

- **Home Assistant 2026.9.0 oder neuer.** Version 3.5 der Integration nutzt die überarbeitete Modbus-Anbindung dieser Home-Assistant-Version und lässt sich auf älteren Versionen nicht installieren.
- **HACS** (Home Assistant Community Store).
- Die Lambda ist per Netzwerk erreichbar, und **Modbus TCP** ist an der Lambda aktiviert (Standard-Port 502).

### HACS Installation

Die Lambda Wärmepumpen Integration wird über HACS installiert. HACS ist eine Erweiterung für Home Assistant, die die Installation und Verwaltung von benutzerdefinierten Integrationen, Themes und anderen Erweiterungen vereinfacht.

Die Installation von HACS hängt von Ihrer Home Assistant Installation ab. Die Anleitung für alle Installationstypen finden Sie in der [HACS Dokumentation](https://www.hacs.xyz/docs/use/download/download/){:target="_blank" rel="noopener noreferrer"}.

## Installation der Lambda Wärmepumpen Integration

Nachdem HACS installiert und eingerichtet ist:

1. **HACS öffnen:** im Seitenmenü von Home Assistant auf **HACS** klicken.
2. **Integration herunterladen:**
    - Nach „Lambda Heat Pumps“ suchen und die Integration öffnen.
    - Auf **Herunterladen** klicken und warten, bis der Download abgeschlossen ist.
3. **Home Assistant neu starten.** Das ist nach der ersten Installation nötig, damit Home Assistant die Integration kennt.
4. **Integration einrichten:**
    - Wird Ihre Lambda im Netzwerk erkannt, schlägt Home Assistant sie unter **Einstellungen** → **Geräte & Dienste** als **Entdeckt** vor. Ein Klick auf **Hinzufügen** startet die Einrichtung mit bereits eingetragener IP-Adresse.
    - Andernfalls: **Einstellungen** → **Geräte & Dienste** → **Integration hinzufügen** → „Lambda Heat Pumps“.
    - Weiter mit der [initialen Konfiguration](initiale-konfiguration.md).

## Update von Version 2.x

Beim ersten Start nach dem Update übernimmt die Integration Ihren bestehenden Eintrag automatisch: Entitäts-IDs und Verlauf bleiben erhalten. Vor dem Update ein Backup erstellen. Was danach zu prüfen ist (Firmware-Version, Statistik-Hinweise unter **Reparaturen**, weggefallene Entitäten), steht im Abschnitt „Update von 2.x auf 3.5.x“ des [Changelogs](https://github.com/GuidoJeuken-6512/lambda_heat_pumps/blob/main/CHANGELOG.md){:target="_blank" rel="noopener noreferrer"} und auf der Seite [Firmware-Version ändern](firmware-wechsel.md).

## Nächste Schritte

- Die Integration einrichten: [initiale Konfiguration](initiale-konfiguration.md)
- Die verfügbaren Features erkunden: [Features](features.md)
- Die Heizkurve eintragen: [Heizkurve](heizkurve.md)
