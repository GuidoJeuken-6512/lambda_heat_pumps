// =====================================================================
// Lambda Entities Card – every entity of the lambda_heat_pumps integration,
// grouped by module like the Lambda controller, with search and an (i)
// explanation. Shipped with the integration (frontend/ folder).
// Card:  type: custom:lambda-entities-card
// Options: config_entry (only that controller), back_path (the back button).
// =====================================================================
const LEC_VERSION = "3.7.0";

const LEC_T = {
  de: {
    title: "λ Lambda – alle Entitäten", count: "{0} Einträge · sortiert nach Modulen wie in der Lambda-Regelung · ⓘ = Erklärung",
    search: "🔍 Suchen (Name oder Entität) …", back: "← Cockpit", foot: "Lambda Entitäten v{0} · Tippen auf Name/Wert öffnet den Verlauf",
    g_hp: "Wärmepumpe", g_hp_sub: "Modul WP · Register 1000 ff.", g_boil: "Brauchwasser", g_boil_sub: "Modul WW · Register 2000 ff.",
    g_buff: "Puffer", g_buff_sub: "Modul Puffer · Register 3000 ff.", g_sol: "Solar", g_sol_sub: "Modul Solar · Register 4000 ff.",
    g_hc: "Heizkreis", g_hc_sub: "Modul Heizkreis · Register 5000 ff.", g_amb: "Außen & E-Manager", g_amb_sub: "Register 0 ff. / 100 ff.",
    g_en: "Energie & Effizienz", g_en_sub: "berechnet in Home Assistant", g_lz: "Laufzeiten, Starts & Zähler", g_lz_sub: "berechnet in Home Assistant",
    s_mess: "📡 Messwerte aus der Lambda", s_calc: "🧮 Berechnet in Home Assistant", s_set: "🎛️ Einstellungen & Bedienung",
    s_stat: "📊 Zeiträume", s_disabled: "deaktiviert",
    p_total: "Gesamt", p_hourly: "Stunde", p_2h: "2 h", p_4h: "4 h", p_daily: "Tag", p_yesterday: "Gestern", p_monthly: "Monat", p_yearly: "Jahr",
    gen_mess: "Wert direkt aus der Lambda (Modbus).", gen_calc: "Berechnet von der Integration in Home Assistant.",
    gen_set: "Einstellung. Register-Werte werden in die Lambda geschrieben, „Kopien“ nur für die Berechnung genutzt.",
    gen_stat: "Die Zeiträume setzen sich automatisch zurück (Stunde, Tag, Monat, Jahr).",
  },
  en: {
    title: "λ Lambda – all entities", count: "{0} entries · sorted by module like the Lambda controller · ⓘ = explanation",
    search: "🔍 Search (name or entity) …", back: "← Cockpit", foot: "Lambda Entities v{0} · tap name/value for its history",
    g_hp: "Heat pump", g_hp_sub: "HP module · registers 1000+", g_boil: "Hot water", g_boil_sub: "DHW module · registers 2000+",
    g_buff: "Buffer", g_buff_sub: "Buffer module · registers 3000+", g_sol: "Solar", g_sol_sub: "Solar module · registers 4000+",
    g_hc: "Heating circuit", g_hc_sub: "Heating circuit module · registers 5000+", g_amb: "Outside & energy manager", g_amb_sub: "registers 0+ / 100+",
    g_en: "Energy & efficiency", g_en_sub: "calculated in Home Assistant", g_lz: "Runtimes, starts & counters", g_lz_sub: "calculated in Home Assistant",
    s_mess: "📡 Measured by the Lambda", s_calc: "🧮 Calculated in Home Assistant", s_set: "🎛️ Settings & controls",
    s_stat: "📊 Periods", s_disabled: "disabled",
    p_total: "Total", p_hourly: "Hour", p_2h: "2 h", p_4h: "4 h", p_daily: "Day", p_yesterday: "Yesterday", p_monthly: "Month", p_yearly: "Year",
    gen_mess: "Value read directly from the Lambda (Modbus).", gen_calc: "Calculated by the integration in Home Assistant.",
    gen_set: "Setting. Register values are written to the Lambda, “copies” are only used for calculations.",
    gen_stat: "The periods reset automatically (hour, day, month, year).",
  },
};
let LEC_LANG = "de";
function LT(k, ...a) {
  const t = (LEC_T[LEC_LANG] || LEC_T.de)[k] ?? LEC_T.de[k] ?? k;
  return a.length ? t.replace(/\{(\d)\}/g, (_, i) => a[i]) : t;
}

const LEC_GROUPS = [
  { key: "hp", icon: "♨️" },
  { key: "boil", icon: "🚿" },
  { key: "buff", icon: "🧱" },
  { key: "sol", icon: "☀️" },
  { key: "hc", icon: "📈" },
  { key: "amb", icon: "🌡️" },
  { key: "en", icon: "⚡" },
  { key: "lz", icon: "⏱️" },
];

// Explanations by the entity's translation key: [de, en]
const LEC_INFO = {
  operating_state: ["Betriebszustand des Moduls (Heizen, Warmwasser, Abtauen, Bereit …). Grundlage für Zähler und Laufzeiten.", "Operating state of the module (heating, hot water, defrost, standby …). The counters and runtimes are based on it."],
  state: ["Interner Status der Regelung (z. B. REGULATION = Regelbetrieb).", "Internal controller state (e.g. REGULATION)."],
  error_state: ["Fehlerzustand. NONE = keine Störung.", "Error state. NONE = no fault."],
  error_number: ["Fehlernummer, 0 = kein Fehler.", "Error number, 0 = no error."],
  flow_line_temperature: ["Vorlauftemperatur.", "Flow temperature."],
  return_line_temperature: ["Rücklauftemperatur.", "Return temperature."],
  volume_flow_heat_sink: ["Volumenstrom auf der Heizungsseite.", "Volume flow on the heating side."],
  energy_source_inlet_temperature: ["Eintrittstemperatur der Energiequelle (bei Luft-WP: Außenluft an der Außeneinheit).", "Energy source inlet temperature (air-source: outside air at the outdoor unit)."],
  compressor_unit_rating: ["Verdichterleistung in Prozent.", "Compressor rating in percent."],
  actual_heating_capacity: ["Aktuelle Heizleistung (Wärmeabgabe).", "Current heating capacity (heat output)."],
  inverter_power_consumption: ["Elektrische Leistungsaufnahme des Inverters.", "Electrical power drawn by the inverter."],
  cop: ["Momentane Arbeitszahl (COP) laut Lambda.", "Momentary coefficient of performance (COP) reported by the Lambda."],
  relais_state_2nd_heating_stage: ["Relais der 2. Heizstufe (Heizstab).", "Relay of the second heating stage (heating rod)."],
  compressor_power_consumption_accumulated: ["Stromzähler der Lambda seit Inbetriebnahme (Wh).", "The Lambda's own electricity counter since commissioning (Wh)."],
  compressor_thermal_energy_output_accumulated: ["Wärmezähler der Lambda seit Inbetriebnahme (Wh).", "The Lambda's own heat counter since commissioning (Wh)."],
  actual_high_temperature: ["Speichertemperatur oben.", "Tank temperature at the top."],
  actual_low_temperature: ["Speichertemperatur unten.", "Tank temperature at the bottom."],
  actual_circulation_temperature: ["Zirkulationstemperatur.", "Circulation temperature."],
  actual_circulation_pump_state: ["Zirkulationspumpe an/aus.", "Circulation pump on/off."],
  target_high_temperature: ["Eingestellte Warmwasser-Solltemperatur (Register 2050).", "Configured hot water setpoint (register 2050)."],
  maximum_buffer_temp: ["Maximale Puffertemperatur (Register 3050).", "Maximum buffer temperature (register 3050)."],
  target_temp_flow_line: ["Soll-Vorlauf des Heizkreises aus der Heizkurve inkl. Offset und PV (Register 5007). Grundlage für die Außentemperatur des Wärmefahrplans.", "Flow setpoint of the circuit from the heating curve incl. offset and PV (register 5007). Basis of the heating schedule outside temperature."],
  set_flow_line_offset_temperature: ["Heizkurven-Offset (Register 5050).", "Heating curve offset (register 5050)."],
  flow_line_offset_temperature: ["Heizkurven-Offset, wird in die Lambda geschrieben (Register 5050).", "Heating curve offset, written to the Lambda (register 5050)."],
  target_room_temperature: ["Raum-Soll Heizen (Register 5051).", "Room setpoint heating (register 5051)."],
  heating_curve_cold_outside_temp: ["Heizkurve: Vorlauf bei −22 °C. Kopie der Lambda-Einstellung.", "Heating curve: flow at −22 °C. Copy of the Lambda setting."],
  heating_curve_mid_outside_temp: ["Heizkurve: Vorlauf bei 0 °C. Kopie der Lambda-Einstellung.", "Heating curve: flow at 0 °C. Copy of the Lambda setting."],
  heating_curve_warm_outside_temp: ["Heizkurve: Vorlauf bei +22 °C. Kopie der Lambda-Einstellung.", "Heating curve: flow at +22 °C. Copy of the Lambda setting."],
  heating_curve_flow_line_temperature_calc: ["Soll-Vorlauf aus der Heizkurve, berechnet von der Integration.", "Flow setpoint from the heating curve, calculated by the integration."],
  schedule_outside_temperature_calc: ["Außentemperatur, mit der die Lambda laut Wärmefahrplan gerade rechnet. Aus dem Soll-Vorlauf (5007) zurückgerechnet (ca. ±0,4 K).", "Outside temperature the Lambda's heating schedule currently uses, calculated back from the flow setpoint (5007), about ±0.4 K."],
  ambient_temperature_calculated: ["Berechnete Außentemperatur der Lambda (gedämpft).", "The Lambda's calculated (damped) outside temperature."],
  ambient_temperature_1h: ["Mittlere Außentemperatur der letzten Stunde.", "Average outside temperature over the last hour."],
  emgr_actual_power: ["PV-Überschuss, den die Integration an die Lambda schickt (Register 102).", "PV surplus the integration sends to the Lambda (register 102)."],
  emgr_actual_power_consumption: ["Aktuelle Leistungsaufnahme laut E-Manager.", "Current power consumption according to the energy manager."],
  emgr_power_consumption_setpoint: ["Sollleistung des E-Managers (nur in „Automatik“).", "Power setpoint of the energy manager (only in “automatic”)."],
  dhw_switch_on_hysteresis: ["Kopie der Lambda-Einstellung, nur für die Schaltpunkte im Cockpit.", "Copy of the Lambda setting, only for the cockpit's switching points."],
};

function lecEsc(s) {
  return String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
}
function lecLocale() {
  return LEC_LANG === "de" ? "de-DE" : "en-GB";
}
function lecVal(st) {
  if (!st) return "–";
  const u = st.attributes.unit_of_measurement || "";
  let v = st.state;
  const n = parseFloat(String(v).replace(",", "."));
  if (!Number.isNaN(n) && /^-?[\d.,]+$/.test(String(v))) {
    const d = Math.abs(n) >= 1000 ? 0 : Math.abs(n) >= 100 ? 1 : 2;
    v = n.toLocaleString(lecLocale(), { maximumFractionDigits: d });
  } else if (window.LCC_STATE) {
    v = window.LCC_STATE(v);
  }
  return `${lecEsc(v)}${u ? ` <small>${lecEsc(u)}</small>` : ""}`;
}

const LEC_PERIODS = ["total", "hourly", "2h", "4h", "daily", "yesterday", "monthly", "yearly"];
const LEC_PERIOD_RE = new RegExp(`^(.*)_(${LEC_PERIODS.join("|")})$`);

class LambdaEntitiesCard extends HTMLElement {
  setConfig(config) {
    this._config = config || {};
    this._open = { hp: true };
    this._info = {};
    this._q = "";
    if (!this.shadowRoot) {
      this.attachShadow({ mode: "open" });
      this.shadowRoot.addEventListener("click", (e) => this._click(e));
      this.shadowRoot.addEventListener("input", (e) => {
        if (e.target.id === "q") {
          this._q = e.target.value.toLowerCase();
          this._render();
        }
      });
    }
  }
  set hass(h) {
    this._hass = h;
    const lang = String((h.locale && h.locale.language) || h.language || "de");
    LEC_LANG = lang.startsWith("de") ? "de" : "en";
    const now = Date.now();
    if (this._last && now - this._last < 5000) {
      clearTimeout(this._t);
      this._t = setTimeout(() => this._render(), 5000);
      return;
    }
    this._last = now;
    this._render();
  }
  getCardSize() {
    return 30;
  }
  getGridOptions() {
    return { columns: "full" };
  }

  // Where an entity belongs, from its id: the module block it sits in, or
  // the counters the integration computes.
  _place(entityId, key) {
    const obj = entityId.split(".")[1];
    const m = obj.match(/(?:^|_)(hp|boil|buff|sol|hc)\d+_/);
    const module = m ? m[1] : "amb";
    if (module === "hp" && /_(energy|thermal_energy|cop)(_|$)|^cop_calc$/.test(key || "")) return "en";
    if (module === "hp" && /_(cycling|runtime)(_|$)/.test(key || "")) return "lz";
    return module;
  }
  _kind(entityId, reg) {
    const domain = entityId.split(".")[0];
    if (domain !== "sensor" || reg.entity_category === "config") return "set";
    const key = reg.translation_key || "";
    if (/_(cycling|energy|thermal_energy|runtime|cop)_/.test(key + "_") || /_calc$/.test(key)) return "calc";
    return "mess";
  }

  _collect() {
    const res = {};
    LEC_GROUPS.forEach((g) => (res[g.key] = { mess: [], calc: [], set: [], stat: {} }));
    const devices = this._hass.devices || {};
    const entry = this._config.config_entry;
    for (const reg of Object.values(this._hass.entities || {})) {
      if (reg.platform !== "lambda_heat_pumps") continue;
      if (entry) {
        const dev = devices[reg.device_id];
        if (dev && dev.config_entries && !dev.config_entries.includes(entry)) continue;
      }
      const id = reg.entity_id;
      const st = this._hass.states[id];
      const key = reg.translation_key || id.split(".")[1];
      const g = this._place(id, key);
      const kind = this._kind(id, reg);
      const pm = kind === "calc" ? key.match(LEC_PERIOD_RE) : null;
      if (pm) {
        const base = `${g}|${id.replace(/_(total|hourly|2h|4h|daily|yesterday|monthly|yearly)$/, "")}`;
        res[g].stat[base] = res[g].stat[base] || { key: pm[1], per: {} };
        res[g].stat[base].per[pm[2]] = [id, st];
      } else res[g][kind].push([id, st, key]);
    }
    return res;
  }

  _name(id, st) {
    return (st && st.attributes.friendly_name) || id;
  }
  _match(id, st) {
    if (!this._q) return true;
    return `${id} ${this._name(id, st)}`.toLowerCase().includes(this._q);
  }
  _infoText(key, kind) {
    const k = /hysteresis|spread|limit_outside|maximum_flow|dhw_maximum|setpoint_offset/.test(key) ? "dhw_switch_on_hysteresis" : key;
    const t = LEC_INFO[k];
    if (t) return t[LEC_LANG === "de" ? 0 : 1];
    return LT(kind === "set" ? "gen_set" : kind === "calc" ? "gen_calc" : "gen_mess");
  }

  _row([id, st, key], kind) {
    const open = this._info[id];
    return `<div class="row">
      <div class="r1">
        <div class="nm" data-ent="${lecEsc(id)}"><b>${lecEsc(this._name(id, st))}</b><em>${lecEsc(id)}</em></div>
        <div class="vl" data-ent="${lecEsc(id)}">${st ? lecVal(st) : `<small>${LT("s_disabled")}</small>`}</div>
        <span class="ib ${open ? "on" : ""}" data-act="i" data-k="${lecEsc(id)}">i</span>
      </div>
      ${open ? `<div class="it">${this._infoText(key, kind)}</div>` : ""}
    </div>`;
  }
  _statRow(base, { key, per }) {
    const any = Object.values(per).find((p) => p[1]) || Object.values(per)[0];
    const name = this._name(any[0], any[1]).replace(/\s+(Total|Gesamt|Daily|Täglich|Hourly|Stündlich|Monthly|Monatlich|Yearly|Jährlich|Yesterday|Gestern|2h|4h)$/i, "");
    const k = "s_" + base;
    const open = this._info[k];
    const cells = LEC_PERIODS.filter((p) => per[p])
      .map((p) => {
        const [id, st] = per[p];
        return st
          ? `<div data-ent="${lecEsc(id)}"><span>${LT("p_" + p)}</span><b>${lecVal(st)}</b></div>`
          : `<div class="empty"><span>${LT("p_" + p)}</span><b>–</b></div>`;
      })
      .join("");
    return `<div class="row">
      <div class="r1"><div class="nm"><b>${lecEsc(name)}</b><em>${lecEsc(key)}</em></div><span class="ib ${open ? "on" : ""}" data-act="i" data-k="${lecEsc(k)}">i</span></div>
      <div class="per">${cells}</div>
      ${open ? `<div class="it">${LT("gen_calc")} ${LT("gen_stat")}</div>` : ""}
    </div>`;
  }

  // The frame with the search field is built once (and again only when the
  // language or the back link changes); later renders replace just the
  // count and the list. Replacing the field itself would drop its focus
  // and close the on-screen keyboard on every update.
  _render() {
    if (!this._hass) return;
    const data = this._collect();
    const sec = (title, body) => (body ? `<div class="sub">${title}</div>${body}` : "");
    const by = (a) => a.sort((x, y) => this._name(x[0], x[1]).localeCompare(this._name(y[0], y[1]), LEC_LANG));
    let total = 0;
    const groups = LEC_GROUPS.map((g) => {
      const d = data[g.key];
      const rows = (kind) => by(d[kind]).filter(([i, s]) => this._match(i, s)).map((r) => this._row(r, kind)).join("");
      const stat = Object.keys(d.stat)
        .sort()
        .filter((b) => Object.values(d.stat[b].per).some(([i, s]) => this._match(i, s)))
        .map((b) => this._statRow(b, d.stat[b]))
        .join("");
      const n = d.mess.length + d.calc.length + d.set.length + Object.keys(d.stat).length;
      total += n;
      if (!n) return "";
      const open = this._q ? true : !!this._open[g.key];
      const body = sec(LT("s_mess"), rows("mess")) + sec(LT("s_calc"), rows("calc")) + sec(LT("s_stat"), stat) + sec(LT("s_set"), rows("set"));
      if (this._q && !body) return "";
      return `<div class="grp ${g.key}">
        <div class="gh" data-act="g" data-k="${g.key}"><span class="gi">${g.icon}</span><div><b>${LT("g_" + g.key)}</b><em>${LT("g_" + g.key + "_sub")}</em></div><i>${n}</i><span class="chev">${open ? "▲" : "▼"}</span></div>
        ${open ? `<div class="gb">${body}</div>` : ""}
      </div>`;
    }).join("");
    const frame = `${LEC_LANG}|${this._config.back_path || ""}`;
    if (this._frame !== frame || !this.shadowRoot.getElementById("list")) {
      this._frame = frame;
      this.shadowRoot.innerHTML = `<style>${LEC_CSS}</style>
      <ha-card><div class="wrap">
        <div class="hd">${this._config.back_path ? `<button class="back" data-act="back">${LT("back")}</button>` : ""}<div><b>${LT("title")}</b><em id="count"></em></div></div>
        <input id="q" type="search" placeholder="${lecEsc(LT("search"))}" value="${lecEsc(this._q)}">
        <div id="list"></div>
        <div class="foot">${LT("foot", LEC_VERSION)}</div>
      </div></ha-card>`;
    }
    this.shadowRoot.getElementById("count").textContent = LT("count", total);
    this.shadowRoot.getElementById("list").innerHTML = groups;
  }

  _click(ev) {
    const el = ev.composedPath().find((n) => n.dataset && (n.dataset.act || n.dataset.ent));
    if (!el) return;
    const a = el.dataset.act;
    if (a === "back") {
      history.pushState(null, "", this._config.back_path);
      window.dispatchEvent(new CustomEvent("location-changed", { bubbles: true, composed: true }));
      return;
    }
    if (a === "g") {
      this._open[el.dataset.k] = !this._open[el.dataset.k];
      this._render();
    } else if (a === "i") {
      this._info[el.dataset.k] = !this._info[el.dataset.k];
      this._render();
    } else if (el.dataset.ent) {
      this.dispatchEvent(new CustomEvent("hass-more-info", { bubbles: true, composed: true, detail: { entityId: el.dataset.ent } }));
    }
  }
}

const LEC_CSS = `
:host{--card:#111c31;--card2:#0d1629;--line:#1f2d47;--txt:#e2e8f0;--mut:#8aa0bf}
ha-card{background:linear-gradient(180deg,#0b1324,#0f1b33);color:var(--txt);border-radius:22px;border:1px solid var(--line);overflow:hidden}
.wrap{padding:14px;display:flex;flex-direction:column;gap:10px;max-width:1100px;margin:0 auto}
.hd{display:flex;align-items:center;gap:12px}
.back{flex:none;padding:8px 14px;border-radius:12px;border:1px solid #27406b;background:linear-gradient(180deg,#183057,#122444);color:var(--txt);font:inherit;font-weight:600;cursor:pointer}
.hd b{font-size:20px;display:block}.hd em{font-style:normal;font-size:12px;color:var(--mut)}
#q{width:100%;box-sizing:border-box;padding:10px 14px;border-radius:12px;border:1px solid var(--line);background:var(--card2);color:var(--txt);font-size:14px;outline:none}
#q:focus{border-color:#5eead4}
#list{display:flex;flex-direction:column;gap:10px}
.grp{border:1px solid var(--line);border-radius:16px;background:var(--card);overflow:hidden}
.grp.alt,.grp.nb{border-style:dashed;opacity:.9}
.gh{display:flex;align-items:center;gap:10px;padding:12px 14px;cursor:pointer;background:linear-gradient(90deg,rgba(47,113,150,.35),transparent)}
.gi{font-size:22px}
.gh div{flex:1}.gh b{display:block;font-size:15px}.gh em{font-style:normal;font-size:11px;color:var(--mut)}
.gh i{font-style:normal;font-size:12px;padding:2px 9px;border-radius:999px;background:#1a2640;color:var(--mut)}
.chev{color:var(--mut);font-size:12px}
.gb{padding:4px 12px 12px}
.sub{font-size:11px;letter-spacing:.12em;color:var(--mut);font-weight:700;margin:12px 2px 6px;text-transform:uppercase}
.row{border:1px solid var(--line);border-radius:12px;background:var(--card2);padding:7px 10px;margin-bottom:5px}
.r1{display:flex;align-items:center;gap:10px}
.nm{flex:1;min-width:0;cursor:pointer}
.nm b{display:block;font-size:13px;font-weight:600;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.nm em{display:block;font-style:normal;font-size:10px;color:#5b6b85;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.vl{font-weight:700;font-size:14px;white-space:nowrap;cursor:pointer;text-align:right}
.vl small,.per small{font-size:.7em;color:var(--mut);font-weight:500}
.ib{flex:none;display:inline-flex;align-items:center;justify-content:center;width:20px;height:20px;border-radius:50%;border:1.5px solid #64748b;color:#94a3b8;font:italic 700 12px Georgia,serif;cursor:pointer}
.ib.on{border-color:#5eead4;color:#5eead4}
.it{margin-top:6px;padding:8px 10px;border-radius:10px;background:#0b1220;border:1px solid #155e75;font-size:12px;line-height:1.45;color:#cbd5e1}
.per{display:grid;grid-template-columns:repeat(4,1fr);gap:6px;margin-top:6px}
.per div{background:#0b1220;border-radius:8px;padding:4px 8px;cursor:pointer;min-width:0}
.per span{display:block;font-size:10px;color:var(--mut)}.per b{font-size:13px;white-space:nowrap}
.per .empty{opacity:.4}
.auto{opacity:.7}.auto.on{opacity:1;border-color:#155e75}
.emo{font-size:18px}
.sw{flex:none;width:40px;height:22px;border-radius:12px;background:#334155;position:relative;cursor:pointer}
.sw i{position:absolute;top:3px;left:3px;width:16px;height:16px;border-radius:50%;background:#cbd5e1;transition:left .2s}
.auto.on .sw{background:#14b8a6}.auto.on .sw i{left:21px;background:#fff}
.foot{text-align:center;font-size:11px;color:#475569}
@media (max-width:480px){.per{grid-template-columns:repeat(2,1fr)}}
`;

// Home Assistant loads this file before its own code. In browsers without
// scoped custom element registries (Firefox) it then replaces
// window.customElements with a polyfill that does not know elements defined
// before, and the card shows "Custom element doesn't exist". So define it again
// in whatever registry is current, until Home Assistant itself is up.
function lecDefine(name, cls) {
  const define = () => {
    const reg = window.customElements;
    if (!reg.get(name)) reg.define(name, cls);
  };
  define();
  let tries = 0;
  const timer = setInterval(() => {
    try {
      define();
    } catch (err) {
      console.warn(`${name}: define failed`, err);
    }
    if (window.customElements.get("home-assistant") || ++tries > 300) clearInterval(timer);
  }, 100);
}

lecDefine("lambda-entities-card", LambdaEntitiesCard);
window.customCards = window.customCards || [];
if (!window.customCards.find((c) => c.type === "lambda-entities-card"))
  window.customCards.push({ type: "lambda-entities-card", name: "Lambda Entities", description: "Every entity of the lambda_heat_pumps integration, grouped by module, with explanations" });
