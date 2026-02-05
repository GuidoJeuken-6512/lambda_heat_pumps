---
title: "Lambda Heizkurven-Card"
---

# Lambda Heizkurven-Card (Vorlage)

<div style="display: flex; gap: 20px; align-items: flex-start; margin: 20px 0; flex-wrap: wrap;">
  <div style="flex: 0 0 320px;">
    <img src="../../assets/heizkurven_card_de.png" alt="Heizkurven-Card Vorschau" style="width: 100%; height: auto; border-radius: 8px;">
  </div>
  <div style="flex: 1; min-width: 280px;">
    <p>Diese Vorlage fügt eine <strong>Lovelace-Custom-Card</strong> ein, die die <strong>Heizkurve</strong> einer Lambda-Wärmepumpe darstellt: eine Linie durch drei Stützpunkte (z. B. 22/35, 0/41, -22/50) und einen <strong>dicken Punkt</strong> für den aktuellen Betriebspunkt (X = Außentemperatur, Y = berechnete Vorlauftemperatur).</p>
    
  </div>
</div>
<li><strong>X-Achse:</strong> Außentemperatur (z. B. 22 °C bis -22 °C)</li>
<li><strong>Y-Achse:</strong> Vorlauftemperatur (z. B. 10 °C bis 75 °C)</li>
<li><strong>Linie:</strong> Heizkurve durch die drei konfigurierbaren Punkte (Y-Werte aus Sensoren oder fest)</li>
<li><strong>Punkt:</strong> Aktueller Wert aus den Sensoren <code>eu08l_ambient_temperature_calculated</code> (X) und <code>eu08l_hc1_heating_curve_flow_line_temperature_calc</code> (Y)</li>
---

**⚠️Nutzug der Card ohne Lambda-Integration:** Wenn Sie die Heizkurven-Card ohne diese Home-Assistsnt-Integration für die Lambda nutzen möchten, können Sie die Vorlauftemperatur mit einem **Template-Sensor** berechnen. Siehe [Template-Sensor ohne Lambda-Integration (Standalone)](../Entwickler/heizkurve.md#template-sensor-ohne-lambda-integration-standalone).

## Einrichtung

### Schritt 1: Ordner und JS-Modul anlegen

1. Im Home-Assistant-**Konfigurationsverzeichnis** (z. B. `config/`) den Ordner **`www`** anlegen, falls er noch nicht existiert.
2. Darin eine Datei **`lambda_heizkurve_card.js`** anlegen.
3. Den **vollständigen JavaScript-Code** (siehe Abschnitt [„JavaScript-Modul (Code)“](#javascript-modul-code) weiter unten) in diese Datei kopieren und speichern.

   **Alternativ:** Die Datei aus dem Repo verwenden: **`docs/lovelace/lambda_heizkurve_card.js`** nach **`config/www/lambda_heizkurve_card.js`** kopieren.

### Schritt 2: Ressource in Lovelace eintragen

1. **Einstellungen** → **Dashboard** → **⋮** (oben rechts) → **Ressourcen**.
2. **„+ Ressource hinzufügen“**.
3. **URL:** `/local/lambda_heizkurve_card.js`  
   (bei späteren Updates z. B. `/local/lambda_heizkurve_card.js?v=2`, damit der Browser die neue Version lädt).
4. **Speichern**.  
   Bei Meldung „Ressourcen neu laden“: bestätigen.

### Schritt 3: Karte ins Dashboard einfügen

- **Option A – Neues Dashboard:** Siehe [„Einbindung der Karte“](#einbindung-der-karte) → Option A (Dashboard importieren).
- **Option B – Bestehendes Dashboard:** Ansicht bearbeiten → **„+ Karte hinzufügen“** → **„Code bearbeiten“** → YAML der Karte (siehe [„YAML (Copy & Paste)“](#yaml-copy-paste)) einfügen.

### Schritt 4: Entity-IDs anpassen

In der Karten-Konfiguration anpassen:

- **`entity_x`:** Außentemperatur-Sensor (z. B. `sensor.eu08l_ambient_temperature_calculated`).
- **`entity_y`:** Berechnete Vorlauftemperatur des Heizkreises (z. B. `sensor.eu08l_hc1_heating_curve_flow_line_temperature_calc`).
- **`curve_points`:** Bei mehreren Heizkreisen ggf. `hc1`, `hc2` usw. in den Entity-IDs verwenden.

**Hinweis:** Nach Änderung der **.js-Datei** ist **kein Neustart von Home Assistant** nötig. Im Browser **Hard-Reload** (Strg+Shift+R bzw. Strg+F5) ausführen, damit die neue Version der Card geladen wird.

---

## JavaScript-Modul (Code)

Der folgende Code ist das komplette JS-Modul für die Heizkurven-Card. Zum Einrichten: In die Datei **`config/www/lambda_heizkurve_card.js`** kopieren und speichern.

```javascript
/**
 * Lambda Heizkurve Card – Lovelace Custom Card
 * Zeigt Heizkurve (Linie durch 3 Punkte) und aktuellen Betriebspunkt (X = Außentemperatur, Y = Vorlauftemperatur).
 *
 * Voraussetzung: In Lovelace als Ressource einbinden (z. B. /local/lambda_heizkurve_card.js).
 * Konfiguration: type: custom:lambda-heizkurve-card, entity_x, entity_y, curve_points, x_range, y_range.
 */
(function () {
  class LambdaHeizkurveCard extends HTMLElement {
    static getStubConfig() {
      return {
        entity_x: "sensor.eu08l_ambient_temperature_calculated",
        entity_y: "sensor.eu08l_hc1_heating_curve_flow_line_temperature_calc",
        curve_points: [
          [22, "number.eu08l_hc1_heating_curve_warm_outside_temp"],
          [0, "number.eu08l_hc1_heating_curve_mid_outside_temp"],
          [-22, "number.eu08l_hc1_heating_curve_cold_outside_temp"],
        ],
        x_range: [22, -22],
        y_range: [10, 75],
        title: "Heizkurve",
        x_label: "Außentemperatur °C",
        y_label: "Vorlauf °C",
      };
    }

    setConfig(config) {
      if (!config.entity_x || !config.entity_y) {
        throw new Error("entity_x und entity_y sind erforderlich.");
      }
      this._config = {
        ...LambdaHeizkurveCard.getStubConfig(),
        ...config,
      };
      const raw = this._config.curve_points;
      if (Array.isArray(raw) && raw.length >= 2) {
        const first = raw[0];
        if (typeof first === "number" || typeof first === "string") {
          this._curvePoints = [];
          for (let i = 0; i + 1 < raw.length; i += 2)
            this._curvePoints.push([raw[i], raw[i + 1]]);
        } else {
          this._curvePoints = raw;
        }
      } else {
        this._curvePoints = [[22, 35], [0, 41], [-22, 50]];
      }
      this._xRange = this._config.x_range || [22, -22];
      this._yRange = this._config.y_range || [10, 75];
      if (this._canvas) this._redraw();
    }

    set hass(hass) {
      this._hass = hass;
      if (this._canvas) this._redraw();
    }

    getCardSize() {
      return 4;
    }

    connectedCallback() {
      if (!this._config) return;
      this._build();
    }

    _build() {
      if (this._root) this.removeChild(this._root);
      this._root = document.createElement("div");
      this._root.style.cssText = "padding: 8px; box-sizing: border-box;";

      const title = document.createElement("div");
      title.style.cssText =
        "font-size: 16px; font-weight: 600; margin-bottom: 8px;";
      title.textContent = this._config.title || "Heizkurve";
      this._root.appendChild(title);

      const wrap = document.createElement("div");
      wrap.style.cssText =
        "position: relative; width: 100%; min-height: 280px;";
      this._canvas = document.createElement("canvas");
      this._canvas.style.cssText =
        "width: 100%; height: 280px; display: block;";
      wrap.appendChild(this._canvas);
      this._root.appendChild(wrap);

      const values = document.createElement("div");
      values.style.cssText =
        "display: flex; justify-content: space-between; margin-top: 8px; font-size: 12px; color: var(--secondary-text-color);";
      this._valuesEl = values;
      this._root.appendChild(values);

      this.appendChild(this._root);
      this._redraw();
    }

    _getEntityState(entityId) {
      if (!this._hass || !entityId) return null;
      let id = String(entityId).trim();
      if (id && !id.includes(".")) id = "number." + id;
      const state = this._hass.states[id];
      if (!state || state.state === "unavailable" || state.state === "unknown")
        return null;
      const n = parseFloat(String(state.state).replace(",", "."));
      return isNaN(n) ? null : n;
    }

    _resolveCurvePoint(point, fallbackY) {
      if (!Array.isArray(point) || point.length < 2) return null;
      const [x, yOrEntity] = point;
      const xNum = parseFloat(x);
      if (isNaN(xNum)) return null;
      let y = null;
      if (typeof yOrEntity === "string") {
        y = this._getEntityState(yOrEntity);
      } else if (typeof yOrEntity === "object" && yOrEntity != null && typeof yOrEntity.entity === "string") {
        y = this._getEntityState(yOrEntity.entity);
      } else {
        y = parseFloat(yOrEntity);
      }
      if (y != null && !isNaN(y)) return [xNum, y];
      if (fallbackY != null && !isNaN(fallbackY)) return [xNum, fallbackY];
      return [xNum, 40];
    }

    _redraw() {
      if (!this._canvas || !this._config) return;
      const ctx = this._canvas.getContext("2d");
      const dpr = window.devicePixelRatio || 1;
      const rect = this._canvas.getBoundingClientRect();
      const w = rect.width;
      const h = rect.height;
      this._canvas.width = w * dpr;
      this._canvas.height = h * dpr;
      ctx.scale(dpr, dpr);

      const padding = { left: 44, right: 16, top: 16, bottom: 32 };
      const graphW = w - padding.left - padding.right;
      const graphH = h - padding.top - padding.bottom;

      const xLeft = this._xRange[0];
      const xRight = this._xRange[1];
      const xNumMin = Math.min(xLeft, xRight);
      const xNumMax = Math.max(xLeft, xRight);
      const yMin = Math.min(this._yRange[0], this._yRange[1]);
      const yMax = Math.max(this._yRange[0], this._yRange[1]);

      const toX = (x) =>
        padding.left +
        ((x - xLeft) / (xRight - xLeft)) * graphW;
      const toY = (y) =>
        padding.top +
        graphH -
        ((y - yMin) / (yMax - yMin)) * graphH;

      ctx.clearRect(0, 0, w, h);

      const textColor =
        getComputedStyle(document.body).getPropertyValue(
          "--primary-text-color"
        ) || "#e1e1e1";
      const gridColor =
        getComputedStyle(document.body).getPropertyValue(
          "--divider-color"
        ) || "rgba(255,255,255,0.15)";
      const lineColor = "#ffffff";
      const pointColor = "#e53935";
      const pointStroke = "#fff";

      ctx.strokeStyle = gridColor;
      ctx.lineWidth = 1;
      ctx.font = "11px sans-serif";
      ctx.fillStyle = textColor;

      for (let x = Math.ceil(xNumMin); x <= xNumMax; x += 2) {
        const px = toX(x);
        ctx.beginPath();
        ctx.moveTo(px, padding.top);
        ctx.lineTo(px, padding.top + graphH);
        ctx.stroke();
      }
      for (let y = Math.ceil(yMin); y <= yMax; y += 5) {
        const py = toY(y);
        ctx.beginPath();
        ctx.moveTo(padding.left, py);
        ctx.lineTo(padding.left + graphW, py);
        ctx.stroke();
      }

      ctx.textAlign = "center";
      ctx.fillText(
        this._config.x_label || "Außentemperatur °C",
        padding.left + graphW / 2,
        h - 8
      );
      ctx.save();
      ctx.translate(12, padding.top + graphH / 2);
      ctx.rotate(-Math.PI / 2);
      ctx.textAlign = "center";
      ctx.fillText(
        this._config.y_label || "Vorlauf °C",
        0,
        0
      );
      ctx.restore();

      ctx.textAlign = "right";
      for (let x = Math.ceil(xNumMin); x <= xNumMax; x += 2) {
        ctx.fillText(String(x), toX(x) - 4, padding.top + graphH + 14);
      }
      for (let y = Math.ceil(yMin); y <= yMax; y += 5) {
        ctx.fillText(String(y), padding.left - 6, toY(y) + 4);
      }

      ctx.strokeStyle = lineColor;
      ctx.lineWidth = 2;
      const yMinR = Math.min(this._yRange[0], this._yRange[1]);
      const yMaxR = Math.max(this._yRange[0], this._yRange[1]);
      const fallbackY = (yMinR + yMaxR) / 2;
      const resolvedPoints = this._curvePoints
        .map((p) => this._resolveCurvePoint(p, fallbackY))
        .filter((p) => p != null);
      ctx.beginPath();
      for (let i = 0; i < resolvedPoints.length; i++) {
        const [x, y] = resolvedPoints[i];
        const px = toX(x);
        const py = toY(y);
        if (i === 0) ctx.moveTo(px, py);
        else ctx.lineTo(px, py);
      }
      ctx.stroke();

      const xVal = this._getEntityState(this._config.entity_x);
      const yVal = this._getEntityState(this._config.entity_y);

      if (xVal != null && yVal != null) {
        const cx = toX(xVal);
        const cy = toY(yVal);
        const inRange =
          xVal >= xNumMin &&
          xVal <= xNumMax &&
          yVal >= yMin &&
          yVal <= yMax;
        if (inRange) {
          ctx.fillStyle = pointStroke;
          ctx.beginPath();
          ctx.arc(cx, cy, 10, 0, Math.PI * 2);
          ctx.fill();
          ctx.fillStyle = pointColor;
          ctx.beginPath();
          ctx.arc(cx, cy, 7, 0, Math.PI * 2);
          ctx.fill();
        }
      }

      if (this._valuesEl) {
        this._valuesEl.innerHTML = `
          <span>Außen: ${xVal != null ? xVal.toFixed(1) + " °C" : "–"}</span>
          <span>Vorlauf: ${yVal != null ? yVal.toFixed(1) + " °C" : "–"}</span>
        `;
      }
    }
  }

  customElements.define("lambda-heizkurve-card", LambdaHeizkurveCard);

  if (window.customCards) {
    window.customCards = window.customCards || [];
    window.customCards.push({
      type: "lambda-heizkurve-card",
      name: "Lambda Heizkurve",
      description: "Heizkurve mit Linie und aktuellem Betriebspunkt (Außen- / Vorlauftemperatur).",
      preview: true,
    });
  }
})();
```

Der gleiche Code liegt im Repo unter **`docs/lovelace/lambda_heizkurve_card.js`** – du kannst die Datei von dort nach `config/www/` kopieren oder den obigen Block in eine neue Datei einfügen.

---

## Voraussetzungen (Kurz)

- **Ressource:** `/local/lambda_heizkurve_card.js` (Datei unter **`config/www/`**).
- **Entity-IDs:** `entity_x`, `entity_y` und ggf. `curve_points` an deine Integration anpassen (z. B. `eu08l`, `hc1`).

## Einbindung der Karte

**Option A – Neues Dashboard nur mit Heizkurve (Import)**  
- **Einstellungen** → **Dashboard** → **„+ Dashboard“** → **„Importieren“**  
- Inhalt der Datei **`docs/lovelace/dashboard_heizkurve.yaml`** einfügen und speichern.  
- Das Dashboard hat eine Ansicht mit nur dieser Karte. Entity-IDs ggf. danach anpassen.

**Option B – Karte in bestehendes Dashboard**  
1. Bestehendes Dashboard bearbeiten → gewünschte Ansicht → **„+ Karte hinzufügen“**.  
2. Unten **„Code bearbeiten“** (bzw. YAML) wählen.  
3. Nur den Karten-Block (ab `type: custom:lambda-heizkurve-card` bis `y_label`) aus dem YAML unten einfügen – **nicht** die ganze Datei `heizkurve_card.yaml` als Dashboard importieren (dann kommt der Fehler „Expected an array value at views“).  
4. Entity-IDs und ggf. Stützpunkte anpassen.

## YAML (Copy & Paste)

```yaml
type: custom:lambda-heizkurve-card
title: Heizkurve
entity_x: sensor.eu08l_ambient_temperature_calculated
entity_y: sensor.eu08l_hc1_heating_curve_flow_line_temperature_calc
curve_points:
  - [22, "number.eu08l_hc1_heating_curve_warm_outside_temp"]   # X=22 °C, Y aus Number
  - [0, "number.eu08l_hc1_heating_curve_mid_outside_temp"]    # X=0 °C, Y aus Number
  - [-22, "number.eu08l_hc1_heating_curve_cold_outside_temp"] # X=-22 °C, Y aus Number
x_range: [22, -22]
y_range: [10, 75]
x_label: Außentemperatur °C
y_label: Vorlauf °C
```

## Optionen

| Option         | Beschreibung |
|----------------|--------------|
| `entity_x`     | Sensor für die X-Achse (Außentemperatur). |
| `entity_y`     | Sensor für die Y-Achse (Vorlauftemperatur). |
| `curve_points` | Liste von Punkten: `[X °C, Y]` – Y entweder fester Wert (Zahl) oder Entity-ID (String) für Vorlauf aus Sensor/Number, z. B. `[22, "number.eu08l_hc1_heating_curve_warm_outside_temp"]` (mind. 2 Punkte). |
| `x_range`     | X-Achse Bereich, z. B. `[22, -22]`. |
| `y_range`     | Y-Achse Bereich, z. B. `[10, 75]`. |
| `title`       | Titel über der Grafik. |
| `x_label`     | Beschriftung X-Achse. |
| `y_label`     | Beschriftung Y-Achse. |

Die Card nutzt **keine externen Bibliotheken** (reines Canvas), funktioniert offline und passt sich dem Home-Assistant-Theme an.
