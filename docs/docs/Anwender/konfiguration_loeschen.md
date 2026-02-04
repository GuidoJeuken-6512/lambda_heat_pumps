---
title: "Konfiguration löschen"
---

# Konfiguration löschen

Falls Sie die Lambda Wärmepumpen Integration aus Home Assistant entfernen möchten, können Sie dies über die Home Assistant Benutzeroberfläche durchführen.

## Integration entfernen

### Schritt 1: Integration öffnen

<div style="display: flex; gap: 20px; align-items: flex-start; margin: 20px 0; flex-wrap: wrap;">
  <div style="flex: 0 0 50%; min-width: 300px;">
    <img src="../../assets/delete_config_de.png" alt="Integration löschen" style="width: 100%; height: auto; border-radius: 8px;">
  </div>
  <div style="flex: 1; min-width: 300px;">
    <ol>
      <li><strong>Öffnen Sie Home Assistant:</strong>
        <ul>
          <li>Gehen Sie zu <strong>Einstellungen</strong> → <strong>Geräte & Dienste</strong></li>
          <li>Suchen Sie nach Ihrer Lambda-Integration</li>
          <li>Klicken Sie auf die Integration</li>
        </ul>
      </li>
    </ol>

    <h3>Schritt 2: Integration löschen</h3>

    <ol>
      <li><strong>Integration löschen:</strong>
        <ul>
          <li>Klicken Sie auf die drei Punkte (Menü) oben rechts</li>
          <li>Wählen Sie <strong>Integration löschen</strong> aus</li>
          <li>Bestätigen Sie die Löschung</li>
        </ul>
      </li>
    </ol>
  </div>
</div>

### Schritt 3: Bestätigung

Nach dem Löschen werden:
- Alle Entitäten der Integration entfernt
- Alle Sensoren, Number-Entities und Climate-Entities gelöscht

## Schritt 4: manuelle Nacharbeiten
- Automatisierungen, die diese Entitäten verwenden, müssen manuell angepasst werden
- Die Konfigurationsdatei `lambda_wp_config.yaml` bleibt erhalten, sie kann gelöscht werden. Sie wird bei einer Neueinrichtung mir den standard Einstellungen wieder angelegt.

### Historische Daten

Historische Daten, die in Home Assistant gespeichert wurden, bleiben erhalten. Falls Sie diese ebenfalls löschen möchten, müssen Sie dies über die Home Assistant Datenbank-Verwaltung durchführen.

## Integration erneut hinzufügen

Falls Sie die Integration später erneut hinzufügen möchten, können Sie dies über die [Initiale Konfiguration](initiale-konfiguration.md) durchführen. Alle Einstellungen müssen neu konfiguriert werden.
