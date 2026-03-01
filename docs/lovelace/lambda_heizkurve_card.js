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
      // Jeder Punkt: [x, y] oder [x, "entity.id"] – Y aus Sensor
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
        const xs = this._config.entity_x.split(".").pop();
        const ys = this._config.entity_y.split(".").pop();
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
