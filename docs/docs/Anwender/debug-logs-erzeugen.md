---
title: "Debug Logs erzeugen"
---

# Debug Logs erzeugen

*Zuletzt geändert am 17.10.2026*

Um Fehler zu analysieren oder detaillierte Abläufe der Integration zu prüfen, können Sie die Debug-Protokollierung für Lambda Heat Pumps einschalten.

## Debug-Logging aktivieren

<div style="margin: 20px 0;">
  <a href="../assets/debug_logs_1.png" target="_blank" title="Bild vergrößern">
    <img src="../assets/debug_logs_1.png" alt="Drei-Punkte-Menü der Integration mit Option Debug Logging" style="width: 100%; max-width: 600px; height: auto; border-radius: 8px; cursor: pointer;">
  </a>
  <p><strong>Schritt 1:</strong> Öffnen Sie <strong>Einstellungen → Geräte & Dienste → Integrationen</strong>, wählen Sie die Integration <strong>Lambda Heat Pumps</strong> und klicken Sie oben rechts auf die <strong>drei Punkte (⋮)</strong>. Im Menü wählen Sie <strong>„Enable debug logging“</strong>.</p>
</div>

## Debug-Logging ist aktiv

<div style="margin: 20px 0;">
  <a href="../assets/debug_logs_2.png" target="_blank" title="Bild vergrößern">
    <img src="../assets/debug_logs_2.png" alt="Hinweisbanner: Debug logging enabled mit Schaltfläche Disable" style="width: 100%; max-width: 600px; height: auto; border-radius: 8px; cursor: pointer;">
  </a>
  <p><strong>Schritt 2:</strong> Wenn Debug-Logging aktiv ist, erscheint ein gelber Hinweisbanner <strong>„Debug logging enabled“</strong>. Über die Schaltfläche <strong>„Disable“</strong> können Sie die Debug-Ausgabe wieder abschalten. 
  <p></p>
  Der Browser startet dann automatisch einen Download der erzeugten Logs.</p>
</div>

## Diagnose herunterladen

Zusätzlich zum Log hilft bei vielen Fragen der **Diagnose-Download**: **Einstellungen** → **Geräte & Dienste** → Lambda Heat Pumps → **⋮** beim Eintrag → **Diagnose herunterladen**.

Die Datei enthält die Einstellungen des Eintrags (ohne IP-Adresse), die erkannten Module, das Ergebnis der letzten Abfrage und die **Rohwerte aller Register**, so wie sie von der Lambda kommen. Damit lässt sich z. B. prüfen, ob ein falsch angezeigter Wert schon von der Lambda so geliefert wird. Bitte hängen Sie Log und Diagnose an, wenn Sie ein [GitHub-Issue](https://github.com/GuidoJeuken-6512/lambda_heat_pumps/issues) erstellen.

