// =====================================================================
// Lambda Cockpit Card – overview of a Lambda heat pump, shipped with the
// lambda_heat_pumps integration (served from its frontend/ folder).
// Card:  type: custom:lambda-cockpit-card
//
// The integration writes the card's config when it creates the "Lambda
// Cockpit" dashboard: an `entities:` map from each slot below to the entity
// id it found in the entity registry, and `features:` saying which of the
// integration's functions are switched on. Every slot can be overridden in
// the card YAML; a slot without an entity hides what depends on it.
// =====================================================================

const LCC_VERSION = "3.7.0";

// The slots the card reads. Filled from the card config.
const LCC_SLOTS = [
  "op", "hpstate", "err", "errnum", "heizstab", "vl", "rl", "flow", "rating", "heat", "power", "cop",
  "at", "at1h", "atcalc", "pv_surplus", "ww_top", "ww_low", "ww_set", "ww_state", "ww_zirk",
  "ww_zirk_pump", "ww_climate", "ww_pv_offset", "buf_top", "buf_low", "buf_max", "buf_state",
  "buf_pv_offset", "hc_vl", "hc_rl", "hc_soll", "hc_state", "offset", "pv_offset", "room", "room_set",
  "raum_soll", "curve_m22", "curve_0", "curve_p22", "curve_calc", "wfp_at", "strom_hz", "strom_ww",
  "strom_abt", "strom_kuehl", "strom_sb", "waerme_hz", "waerme_ww", "waerme_abt", "waerme_kuehl",
  "starts_hz", "starts_ww", "umschalt", "abtau_tag", "lz_hz", "lz_ww", "lz_abt", "lz_hs", "e_in",
  "e_out", "hz_in", "hz_out", "ww_in", "ww_out", "cnt_abtau", "p_ww_ein", "p_ww_aus", "p_ww_max",
  "p_buf_ein25", "p_buf_ein50", "p_buf_aus", "p_buf_off", "p_hk_ein", "p_hk_aus", "p_hk_spr",
  "p_hk_grenze", "p_hk_max", "pv_source",
  // Not from the integration; only shown when set in the card YAML.
  "pv_power", "bat_soc", "bat_charge", "bat_discharge", "src_pv", "src_bat", "src_grid", "netz_tag",
  "eigen_tag", "sun",
];

// ---------------------------------------------------------------------
// Texts
// ---------------------------------------------------------------------
const LCC_TEXT = {
  de: {
    pv_power: "PV-Strom", charging: "lädt", delivering: "liefert",
    wfp_at: "AT Wärmefahrplan", at_calc: "AT berechnet", at_actual: "AT ist",
    set_ww: "Soll WW", set_flow: "Soll-VL", flow: "VL", ret: "RL", compressor: "Verdichter",
    output: "Abgabe", cop: "AZ", input: "Aufnahme", power_today: "Strom heute", cop_day: "AZ Tag",
    pv_surplus: "PV-Überschuss", none: "kein", defrosts: "Abtauungen", runtime_today: "Laufzeit heute",
    heating_rod: "Heizstab", hot_water: "Brauchwasser", buffer: "Puffer", floor: "Heizkreis",
    setpoint: "Solltemperatur", pv_increase: "PV-Erhöhung", room_setpoint: "Raum-Soll",
    circ: "Zirku", circ_runs: "läuft", ago: "vor {0} min",
    src_now: "STROMQUELLE AKTUELL", hp_idle: "WP ruht", storage: "Speicher", grid: "Netz",
    tariff_title: "NETZENTGELT-FENSTER", tariff_left: "Noch {0} in dieser Tarifzone",
    actions: "AKTIONEN",
    functions_btn: "Funktionen & Zähler", active: "aktiv",
    runtimes: "LAUFZEITEN HEUTE", rt_heating: "Heizen", rt_dhw: "Warmwasser", rt_defrost: "Abtauen",
    rt_rod: "Heizstab", rt_rest: "Ruhe/Sonst.", starts_heating: "Starts Heizen", starts_dhw: "Starts WW",
    switches: "Umschaltungen", energy_today: "ENERGIE HEUTE", power: "Strom", heat: "Wärme",
    heating: "Heizen", origin_today: "HERKUNFT HEUTE", pv_storage: "PV + Speicher",
    efficiency: "EFFIZIENZ (ZÄHLER)", jaz: "JAZ", total: "gesamt", since_ha: "seit HA",
    curve_title: "HEIZKURVE", curve: "Heizkurve", wfp_none: "Wärmefahrplan: keine Verschiebung",
    curve_offset: "Offset Heizkurve",
    sp_title: "SCHALTPUNKTE AKTUELL", pv_active: "PV aktiv", without_pv: "ohne PV",
    no_data: "keine Daten", sp_running: "läuft – Stopp ab {0} °C (noch {1} K)",
    sp_met: "Start-Bedingung erfüllt ({0} K unter Start)", sp_wait: "wartet – Start unter {0} °C (noch {1} K)",
    start: "Start", stop: "Stopp", middle: "oben", top: "oben", set: "Soll", incl_pv: "inkl. +{0} K PV",
    rl_set: "RL-Soll", heat_limit: "Heizgrenze",
    sp_info_ww: "Soll = eingestellte WW-Temperatur{0}. Start = Soll + Einschalthysterese ({1} K), Stopp = Soll + Ausschalthysterese ({2} K). Vergleich mit dem Fühler oben.",
    sp_info_ww_pv: " + PV-Erhöhung",
    sp_info_buf: "Soll = Soll-VL Heizkreis + Solltemperaturoffset ({0} K){1}. Die Einschalthysterese wird zwischen {2} K (bei 25 °C) und {3} K (bei 50 °C) linear gerechnet – so wie die Lambda „T-Ein“ anzeigt. Stopp = Soll + Ausschalthysterese. In den ersten 20 min nach einem Start hebt die Lambda die Ausschaltschwelle zusätzlich an.",
    sp_info_buf_pv: " + PV-Offset Puffer",
    sp_info_hc: "RL-Soll = Soll-VL ({0} °C, enthält Offset und ggf. PV-Erhöhung) − Spreizung ({1} K). Anforderung ab RL-Soll + Einschalthysterese ({2} K), Ende bei RL-Soll + Ausschalthysterese ({3} K). Heizbetrieb nur, solange die berechnete AT unter der Heizgrenze liegt. Annahme: Lambda wertet hier den Rücklauf aus.",
    sp_copy_hint: "Die Hysterese- und Grenzwerte sind Kopien der Lambda-Einstellungen (nicht per Modbus lesbar). Bitte einmal vom Display übernehmen: Gerät → Konfiguration.",
    limits: "GRENZWERTE", info: "Info", buf_max: "Puffer max.", hc_max: "Heizkreis max. VL",
    ww_max: "WW max. Soll", heat_limit_at: "Heizgrenze AT", tag_lambda: "Lambda", tag_copy: "Kopie",
    limits_info: "<b>Lambda</b> = wird direkt in die Lambda geschrieben.<br><b>Kopie</b> = für diese Werte gibt es kein Modbus-Register. Sie sind eine Kopie der Lambda-Einstellung und werden für die Berechnungen im Cockpit genutzt (z. B. Heizgrenze ✓/✗ bei den Schaltpunkten). Eine Änderung hier verstellt die Lambda nicht – bitte in der Lambda selbst mitändern.",
    limits_hint: "Lambda = schreibt in die WP · Kopie = nur Anzeige/Berechnung",
    popup_title: "Funktionen & Zähler", counters: "ZÄHLER", defrosts_today: "Abtauungen heute",
    defrosts_total: "Abtauungen gesamt", runtime_since: "Laufzeit seit Start", idle_since: "Stillstand seit",
    all_entities: "Alle Lambda-Entitäten", functions: "Funktionen der Integration",
    functions_sub: "Ein- und Ausschalten unter Einstellungen → Geräte & Dienste → Lambda → Konfigurieren",
    on: "an", off: "aus",
    fn_pv: "PV-Überschuss an Lambda",
    fn_pv_info: "Die Integration schickt alle paar Sekunden den Überschuss aus dem gewählten Sensor an den E-Manager der Lambda (Register 102). Darauf reagieren die PV-Erhöhungen von WW, Puffer und Heizkreis.",
    fn_room: "Raumtemperatur an Lambda",
    fn_room_info: "Die Integration schickt die Raumtemperatur des gewählten Fühlers an die Lambda (Register 5004, Raumaufschaltung).",
    foot: "Lambda Cockpit v{0} · Tippen auf einen Wert öffnet den Verlauf", error: "Lambda Cockpit Fehler",
    just_now: "gerade eben", since_min: "seit {0} min", since_h: "seit {0} h {1} min", since_d: "seit {0} d {1} h",
    never: "nie",
  },
  en: {
    pv_power: "PV power", charging: "charging", delivering: "delivering",
    wfp_at: "OT schedule", at_calc: "OT calculated", at_actual: "OT actual",
    set_ww: "DHW set", set_flow: "Flow set", flow: "Flow", ret: "Return", compressor: "Compressor",
    output: "Output", cop: "COP", input: "Input", power_today: "Power today", cop_day: "COP today",
    pv_surplus: "PV surplus", none: "none", defrosts: "Defrosts", runtime_today: "Runtime today",
    heating_rod: "Heating rod", hot_water: "Hot water", buffer: "Buffer", floor: "Heating circuit",
    setpoint: "Setpoint", pv_increase: "PV increase", room_setpoint: "Room setpoint",
    circ: "Circ.", circ_runs: "running", ago: "{0} min ago",
    src_now: "POWER SOURCE NOW", hp_idle: "HP idle", storage: "Battery", grid: "Grid",
    tariff_title: "GRID TARIFF WINDOWS", tariff_left: "{0} left in this tariff zone",
    actions: "ACTIONS",
    functions_btn: "Functions & counters", active: "on",
    runtimes: "RUNTIMES TODAY", rt_heating: "Heating", rt_dhw: "Hot water", rt_defrost: "Defrost",
    rt_rod: "Heating rod", rt_rest: "Idle/other", starts_heating: "heating starts", starts_dhw: "DHW starts",
    switches: "switches", energy_today: "ENERGY TODAY", power: "Power", heat: "Heat",
    heating: "Heating", origin_today: "ORIGIN TODAY", pv_storage: "PV + battery",
    efficiency: "EFFICIENCY (COUNTERS)", jaz: "SCOP", total: "total", since_ha: "since HA",
    curve_title: "HEATING CURVE", curve: "Heating curve", wfp_none: "Heating schedule: no shift",
    curve_offset: "Heating curve offset",
    sp_title: "SWITCHING POINTS", pv_active: "PV active", without_pv: "without PV",
    no_data: "no data", sp_running: "running – stops at {0} °C ({1} K to go)",
    sp_met: "start condition met ({0} K below start)", sp_wait: "waiting – starts below {0} °C ({1} K to go)",
    start: "Start", stop: "Stop", middle: "top", top: "top", set: "Set", incl_pv: "incl. +{0} K PV",
    rl_set: "Return set", heat_limit: "Heating limit",
    sp_info_ww: "Set = configured hot water temperature{0}. Start = set + switch-on hysteresis ({1} K), stop = set + switch-off hysteresis ({2} K). Compared with the top sensor.",
    sp_info_ww_pv: " + PV increase",
    sp_info_buf: "Set = heating circuit flow set + setpoint offset ({0} K){1}. The switch-on hysteresis is interpolated between {2} K (at 25 °C) and {3} K (at 50 °C), as the Lambda shows “T-On”. Stop = set + switch-off hysteresis. In the first 20 min after a start the Lambda raises the switch-off threshold further.",
    sp_info_buf_pv: " + PV buffer offset",
    sp_info_hc: "Return set = flow set ({0} °C, includes offset and any PV increase) − spread ({1} K). Request from return set + switch-on hysteresis ({2} K), end at return set + switch-off hysteresis ({3} K). Heating only while the calculated outside temperature is below the heating limit. Assumption: the Lambda evaluates the return here.",
    sp_copy_hint: "The hysteresis and limit values are copies of the Lambda's settings (not readable over Modbus). Copy them from the display once: device → configuration.",
    limits: "LIMITS", info: "Info", buf_max: "Buffer max.", hc_max: "Circuit max. flow",
    ww_max: "DHW max. set", heat_limit_at: "Heating limit OT", tag_lambda: "Lambda", tag_copy: "copy",
    limits_info: "<b>Lambda</b> = written to the Lambda directly.<br><b>Copy</b> = these values have no Modbus register. They copy the Lambda's setting and are used for the cockpit's calculations (e.g. heating limit ✓/✗ in the switching points). Changing them here does not change the Lambda – change it there as well.",
    limits_hint: "Lambda = writes to the HP · copy = display/calculation only",
    popup_title: "Functions & counters", counters: "COUNTERS", defrosts_today: "Defrosts today",
    defrosts_total: "Defrosts total", runtime_since: "Running since start", idle_since: "Idle since",
    all_entities: "All Lambda entities", functions: "Integration functions",
    functions_sub: "Switch on and off under Settings → Devices & services → Lambda → Configure",
    on: "on", off: "off",
    fn_pv: "PV surplus to Lambda",
    fn_pv_info: "Every few seconds the integration sends the surplus from the chosen sensor to the Lambda's energy manager (register 102). The PV increases of hot water, buffer and heating circuit react to it.",
    fn_room: "Room temperature to Lambda",
    fn_room_info: "The integration sends the room temperature of the chosen sensor to the Lambda (register 5004, room influence).",
    foot: "Lambda Cockpit v{0} · tap a value for its history", error: "Lambda Cockpit error",
    just_now: "just now", since_min: "for {0} min", since_h: "for {0} h {1} min", since_d: "for {0} d {1} h",
    never: "never",
  },
};
let LCC_LANG = "de";
function L(key, ...args) {
  const t = (LCC_TEXT[LCC_LANG] || LCC_TEXT.de)[key] ?? LCC_TEXT.de[key] ?? key;
  return args.length ? t.replace(/\{(\d)\}/g, (_, i) => args[i]) : t;
}
// How long after a circulation run the card still mentions it.
const LCC_CIRC_RECENT_MS = 30 * 60000;

const LCC_LOCALE = () => (LCC_LANG === "de" ? "de-DE" : "en-GB");

// The controller's state labels, as the integration's enum sensors report them.
const LCC_STATE_TEXT = {
  de: {
    stby: "Bereit", ch: "Heizbetrieb", heating: "Heizbetrieb", dhw: "Brauchwasser", cc: "Kühlbetrieb",
    cooling: "Kühlbetrieb", circulate: "Umwälzung", defrost: "Abtauung", off: "Aus", frost: "Frostschutz",
    "stby-frost": "Bereit (Frostschutz)", summer: "Sommerbetrieb", holiday: "Urlaub", error: "Störung",
    warning: "Warnung", "info-message": "Info", "time-block": "Sperrzeit", "release-block": "Freigabesperre",
    "mintemp-block": "Mindesttemperatur-Sperre", "firmware-download": "Firmware-Update", legio: "Legionellenschutz",
    "prio-stop": "Pause (Vorrang)", "prompt-dhw": "WW sofort", "trailing-stop": "Nachlauf", "temp-lock": "Temperatursperre",
    eco: "Eco", floordry: "Estrichtrocknung", "max-temp": "Max.-Temperatur", service: "Service",
    "ch-summer": "Sommer (Heizen)", "cc-winter": "Winter (Kühlen)", "release-off": "Freigabe aus",
    "time-off": "Zeitprogramm aus", "stby-heating": "Bereit (Heizen)", "stby-eco": "Bereit (Eco)",
    "stby-cooling": "Bereit (Kühlen)", "stby-floordry": "Bereit (Estrich)", none: "Ok",
    unavailable: "nicht erreichbar", unknown: "unbekannt",
  },
  en: {
    stby: "Standby", ch: "Heating", heating: "Heating", dhw: "Hot water", cc: "Cooling", cooling: "Cooling",
    circulate: "Circulation", defrost: "Defrost", off: "Off", frost: "Frost protection",
    "stby-frost": "Standby (frost)", summer: "Summer", holiday: "Holiday", error: "Fault", warning: "Warning",
    "info-message": "Info", "time-block": "Time block", "release-block": "Release block",
    "mintemp-block": "Min. temperature block", "firmware-download": "Firmware update", legio: "Legionella",
    "prio-stop": "Paused (priority)", "prompt-dhw": "DHW now", "trailing-stop": "Run-on", "temp-lock": "Temperature lock",
    eco: "Eco", floordry: "Floor drying", "max-temp": "Max. temperature", service: "Service",
    "ch-summer": "Summer (heating)", "cc-winter": "Winter (cooling)", "release-off": "Release off",
    "time-off": "Schedule off", "stby-heating": "Standby (heating)", "stby-eco": "Standby (eco)",
    "stby-cooling": "Standby (cooling)", "stby-floordry": "Standby (floor drying)", none: "Ok",
    unavailable: "unavailable", unknown: "unknown",
  },
};
function lccState(t) {
  const k = String(t ?? "").trim().toLowerCase();
  const table = LCC_STATE_TEXT[LCC_LANG] || LCC_STATE_TEXT.de;
  return table[k] || String(t ?? "");
}
window.LCC_STATE = lccState;

// Heat pump operating state label -> [colour, mode]
const LCC_OP = {
  stby: ["#94a3b8", "idle"], ch: ["#fb923c", "heat"], dhw: ["#38bdf8", "ww"], cc: ["#22d3ee", "cool"],
  circulate: ["#a78bfa", "circ"], defrost: ["#7dd3fc", "defrost"], off: ["#6b7280", "off"],
  frost: ["#93c5fd", "idle"], "stby-frost": ["#93c5fd", "idle"], summer: ["#facc15", "idle"],
  holiday: ["#facc15", "idle"], error: ["#ef4444", "error"], warning: ["#f59e0b", "error"],
  "info-message": ["#94a3b8", "idle"], "time-block": ["#c084fc", "block"], "release-block": ["#c084fc", "block"],
  "mintemp-block": ["#c084fc", "block"], "firmware-download": ["#94a3b8", "idle"],
};

function lccEsc(s) {
  return String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
}
function lccFmt(v, d = 1) {
  if (v === null || v === undefined || Number.isNaN(v)) return "–";
  return Number(v).toLocaleString(LCC_LOCALE(), { minimumFractionDigits: d, maximumFractionDigits: d });
}
function lccClamp(v, a, b) {
  return Math.min(b, Math.max(a, v));
}
function lccDur(ms) {
  if (!(ms >= 0)) return "";
  const m = Math.floor(ms / 60000);
  if (m < 1) return L("just_now");
  if (m < 60) return L("since_min", m);
  const h = Math.floor(m / 60);
  if (h < 24) return L("since_h", h, m % 60);
  return L("since_d", Math.floor(h / 24), h % 24);
}
function lccDurHM(h) {
  if (!(h >= 0)) return "–";
  const t = Math.round(h * 60);
  const hh = Math.floor(t / 60);
  const mm = t % 60;
  return hh ? `${hh} h ${mm} min` : `${mm} min`;
}
function lccHours(h) {
  if (!(h >= 0)) return "–";
  const hh = Math.floor(h);
  const mm = Math.round((h - hh) * 60);
  if (hh === 0) return `${mm} min`;
  return `${hh} h ${String(mm).padStart(2, "0")}`;
}
// Temperature -> colour (cold blue, warm red)
function lccTempColor(t, lo = 20, hi = 55) {
  if (Number.isNaN(t)) return "#475569";
  const x = lccClamp((t - lo) / (hi - lo), 0, 1);
  const stops = [
    [0, [59, 130, 246]],
    [0.4, [45, 212, 191]],
    [0.65, [250, 204, 21]],
    [0.82, [251, 146, 60]],
    [1, [239, 68, 68]],
  ];
  for (let i = 1; i < stops.length; i++) {
    if (x <= stops[i][0]) {
      const [p0, c0] = stops[i - 1];
      const [p1, c1] = stops[i];
      const f = (x - p0) / (p1 - p0);
      const c = c0.map((v, k) => Math.round(v + (c1[k] - v) * f));
      return `rgb(${c[0]},${c[1]},${c[2]})`;
    }
  }
  return "rgb(239,68,68)";
}

class LambdaCockpitCard extends HTMLElement {
  setConfig(config) {
    config = config || {};
    this._config = {
      details_path: "",
      wp_soll_offset: 1, // flow set of HP/buffer = circuit flow set + 1 K, if the setting is missing
      tariffs: { standard: { name: "Standard", price: null, color: "#60a5fa" }, windows: [] },
      ...config,
      entities: { sun: "sun.sun", ...(config.entities || {}) },
      features: {
        room_thermostat: !!(config.features && config.features.room_thermostat),
        pv_surplus: !!(config.features && config.features.pv_surplus),
      },
    };
    this._sig = "";
    if (!this.shadowRoot) {
      this.attachShadow({ mode: "open" });
      this.shadowRoot.addEventListener("click", (ev) => this._onClick(ev));
      // A render replaces the whole card. One landing between pressing and
      // releasing a button would swallow the click, so none happens while a
      // button is held; the one that was due follows on release.
      this.shadowRoot.addEventListener("pointerdown", () => (this._held = true));
      const release = () => {
        this._held = false;
        if (this._due) this._scheduleRender();
      };
      this.shadowRoot.addEventListener("pointerup", release);
      this.shadowRoot.addEventListener("pointercancel", release);
      this.shadowRoot.addEventListener("pointerleave", release);
    }
  }

  // At most one render a second, and never while a button is held.
  _scheduleRender() {
    this._due = true;
    if (this._held || this._timer) return;
    const wait = Math.max(0, (this._lastRender || 0) + 1000 - Date.now());
    this._timer = setTimeout(() => {
      this._timer = null;
      if (this._held) return;
      this._due = false;
      this._lastRender = Date.now();
      this._render();
    }, wait);
  }

  static getStubConfig() {
    return { entities: {}, features: {} };
  }

  set hass(hass) {
    this._hass = hass;
    const lang = String((hass.locale && hass.locale.language) || hass.language || "de");
    LCC_LANG = lang.startsWith("de") ? "de" : "en";
    if (!this._resolved && !Object.keys(this._config.entities).some((k) => k !== "sun")) {
      this._autoResolve();
    }
    const ids = Object.values(this._config.entities);
    const minute = Math.floor(Date.now() / 60000);
    const sig =
      LCC_LANG + "|" + minute + "|" +
      ids.map((id) => {
        const s = hass.states[id];
        return s ? s.state + (s.attributes && s.attributes.temperature) : "";
      }).join("|");
    if (sig === this._sig) return;
    this._sig = sig;
    this._scheduleRender();
  }

  // A card added by hand, without the integration's entity map: find the
  // first controller's entities by their unique id suffix.
  _autoResolve() {
    this._resolved = true;
    const reg = this._hass.entities || {};
    const mine = Object.values(reg).filter((e) => e.platform === "lambda_heat_pumps");
    const find = (domain, suffix) => {
      const hit = mine.find((e) => e.entity_id.startsWith(domain + ".") && e.entity_id.endsWith(suffix));
      return hit ? hit.entity_id : undefined;
    };
    const s = (k) => find("sensor", k);
    const n = (k) => find("number", k);
    const map = {
      op: s("_hp1_operating_state"), err: s("_hp1_error_state"), errnum: s("_hp1_error_number"),
      heizstab: s("_hp1_relais_state_2nd_heating_stage"), vl: s("_hp1_flow_line_temperature"),
      rl: s("_hp1_return_line_temperature"), rating: s("_hp1_compressor_unit_rating"),
      heat: s("_hp1_actual_heating_capacity"), power: s("_hp1_inverter_power_consumption"), cop: s("_hp1_cop"),
      at: s("_hp1_energy_source_inlet_temperature"), atcalc: s("_ambient_temperature_calculated"),
      pv_surplus: s("_emgr_actual_power"), ww_top: s("_boil1_actual_high_temperature"),
      ww_low: s("_boil1_actual_low_temperature"), ww_set: s("_boil1_target_high_temperature"),
      ww_state: s("_boil1_operating_state"), ww_zirk_pump: s("_boil1_actual_circulation_pump_state"),
      ww_climate: find("climate", "_boil1_hot_water"), buf_top: s("_buff1_actual_high_temperature"),
      buf_low: s("_buff1_actual_low_temperature"), buf_state: s("_buff1_operating_state"),
      buf_max: n("_buff1_maximum_buffer_temp_number"), hc_vl: s("_hc1_flow_line_temperature"),
      hc_rl: s("_hc1_return_line_temperature"), hc_soll: s("_hc1_target_temp_flow_line"),
      hc_state: s("_hc1_operating_state"), offset: n("_hc1_flow_line_offset_temperature_number"),
      room_set: s("_hc1_target_room_temperature"), raum_soll: n("_hc1_target_room_temperature_number"),
      curve_m22: n("_hc1_heating_curve_cold_outside_temp_number"),
      curve_0: n("_hc1_heating_curve_mid_outside_temp_number"),
      curve_p22: n("_hc1_heating_curve_warm_outside_temp_number"),
      wfp_at: s("_hc1_schedule_outside_temperature_calc"),
      strom_hz: s("_hp1_heating_energy_daily"), strom_ww: s("_hp1_hot_water_energy_daily"),
      waerme_hz: s("_hp1_heating_thermal_energy_daily"), waerme_ww: s("_hp1_hot_water_thermal_energy_daily"),
      starts_hz: s("_hp1_heating_cycling_daily"), starts_ww: s("_hp1_hot_water_cycling_daily"),
      umschalt: s("_hp1_heating_to_hot_water_cycling_daily"), abtau_tag: s("_hp1_defrost_cycling_daily"),
      lz_hz: s("_hp1_heating_runtime_daily"), lz_ww: s("_hp1_hot_water_runtime_daily"),
      lz_abt: s("_hp1_defrost_runtime_daily"), lz_hs: s("_hp1_heating_rod_runtime_daily"),
      e_in: s("_hp1_compressor_power_consumption_accumulated"),
      e_out: s("_hp1_compressor_thermal_energy_output_accumulated"),
      hz_in: s("_hp1_heating_energy_total"), hz_out: s("_hp1_heating_thermal_energy_total"),
      ww_in: s("_hp1_hot_water_energy_total"), ww_out: s("_hp1_hot_water_thermal_energy_total"),
      cnt_abtau: s("_hp1_defrost_cycling_total"),
    };
    for (const [k, v] of Object.entries(map)) if (v && !this._config.entities[k]) this._config.entities[k] = v;
  }

  getCardSize() {
    return 24;
  }
  getGridOptions() {
    return { columns: "full" };
  }

  // ---------- Helpers ----------
  _id(key) {
    return this._config.entities[key] || "";
  }
  _st(key) {
    const id = this._id(key);
    return id && this._hass ? this._hass.states[id] : undefined;
  }
  _has(key) {
    return !!this._st(key);
  }
  _n(key) {
    const s = this._st(key);
    if (!s) return NaN;
    const v = parseFloat(String(s.state).replace(",", "."));
    if (Number.isNaN(v)) return NaN;
    // A circuit without a request reports a flow setpoint of 0.
    if (key === "hc_soll" && v <= 0) return NaN;
    return v;
  }
  // Solar surplus in W, positive while there is one. With the encoding "neg"
  // the controller takes a surplus as negative and grid draw as positive.
  _surplus() {
    const v = this._n("pv_surplus");
    const s = this._st("pv_surplus");
    return s && s.attributes && s.attributes.pv_surplus_mode === "neg" ? -v : v;
  }
  _t(key) {
    const s = this._st(key);
    return s ? s.state : "unavailable";
  }
  _f(name) {
    return !!this._config.features[name];
  }

  _op() {
    const raw = this._t("op");
    const k = String(raw).trim().toLowerCase();
    const [color, mode] = LCC_OP[k] || ["#94a3b8", "idle"];
    return { raw, text: lccState(raw), color, mode };
  }

  _tariffNow() {
    const tf = this._config.tariffs;
    const d = new Date();
    const h = d.getHours() + d.getMinutes() / 60;
    for (const w of tf.windows) {
      if (h >= w.from && h < w.to) return { ...w, endsIn: w.to - h };
    }
    const next = tf.windows
      .map((w) => ({ ...w, start: w.from > h ? w.from : w.from + 24 }))
      .sort((a, b) => a.start - b.start)[0];
    return { ...tf.standard, endsIn: next ? next.start - h : 24 - h, from: null };
  }

  // ---------- Interaction ----------
  _onClick(ev) {
    const el = ev.composedPath().find((n) => n.dataset && (n.dataset.act || n.dataset.ent));
    if (!el) return;
    const act = el.dataset.act;
    const ent = el.dataset.ent;
    ev.stopPropagation();
    if (act === "num") {
      // A number entity: step by its own step, within its own bounds.
      const s = this._hass.states[ent];
      if (!s) return;
      const cur = this._pendVal(ent);
      if (Number.isNaN(cur)) return;
      const step = parseFloat(el.dataset.step) || parseFloat(s.attributes.step) || 0.5;
      let v = Math.round((cur + step * parseFloat(el.dataset.dir)) * 10) / 10;
      const min = parseFloat(s.attributes.min);
      const max = parseFloat(s.attributes.max);
      if (!Number.isNaN(min)) v = Math.max(min, v);
      if (!Number.isNaN(max)) v = Math.min(max, v);
      this._hass.callService(ent.split(".")[0], "set_value", { entity_id: ent, value: v });
      this._pend = this._pend || {};
      this._pend[ent] = { v, t: Date.now() };
      this._render();
    } else if (act === "clim") {
      const c = this._hass.states[ent];
      if (!c) return;
      const cur = this._pendVal(ent);
      const v = lccClamp(cur + parseFloat(el.dataset.dir), parseFloat(c.attributes.min_temp) || 40, parseFloat(c.attributes.max_temp) || 60);
      this._hass.callService("climate", "set_temperature", { entity_id: ent, temperature: v });
      this._pend = this._pend || {};
      this._pend[ent] = { v, t: Date.now() };
      this._render();
    } else if (act === "sec") {
      this._sec = this._sec || {};
      this._sec[el.dataset.key] = !this._sec[el.dataset.key];
      this._render();
    } else if (act === "info") {
      this._info = this._info || {};
      this._info[el.dataset.key] = !this._info[el.dataset.key];
      this._render();
    } else if (act === "nav") {
      this._popup = false;
      this._render();
      history.pushState(null, "", el.dataset.path);
      window.dispatchEvent(new CustomEvent("location-changed", { bubbles: true, composed: true }));
    } else if (act === "noop") {
      return;
    } else if (act === "popup") {
      this._popup = "functions";
      this._render();
    } else if (act === "close-popup") {
      this._popup = false;
      this._render();
    } else if (ent) {
      this.dispatchEvent(new CustomEvent("hass-more-info", { bubbles: true, composed: true, detail: { entityId: ent } }));
    }
  }
  _bufOff() {
    const v = this._n("p_buf_off");
    return Number.isNaN(v) ? this._config.wp_soll_offset : v;
  }

  // The current value, including a change just written and not read back yet.
  _pendVal(id) {
    const s = this._hass.states[id];
    let v = NaN;
    if (s) v = id.startsWith("climate.") ? parseFloat(s.attributes.temperature) : parseFloat(s.state);
    const p = this._pend && this._pend[id];
    if (p) {
      if (Math.abs(p.v - v) < 0.05 || Date.now() - p.t > 90000) delete this._pend[id];
      else return p.v;
    }
    return v;
  }

  // Heating curve: three points at +22 / 0 / -22 °C, linear between them
  _curve(t) {
    const m22 = this._n("curve_m22");
    const z = this._n("curve_0");
    const p22 = this._n("curve_p22");
    const x = lccClamp(t, -22, 22);
    return x >= 0 ? z + ((p22 - z) * x) / 22 : z + ((m22 - z) * -x) / 22;
  }
  // The outside temperature the controller's heating schedule assumes; the
  // integration computes it (sensor "heating schedule outside temperature").
  _atWfp() {
    return this._n("wfp_at");
  }

  _ctl(label, valTxt, attrs, ent) {
    return `<div class="cstep"><span>${label}</span>
      <button ${attrs} data-dir="-1" data-ent="${lccEsc(ent)}">−</button>
      <b data-ent="${lccEsc(ent)}">${valTxt}</b>
      <button ${attrs} data-dir="1" data-ent="${lccEsc(ent)}">+</button></div>`;
  }
  // A control for a number entity, or nothing if the entity is not there.
  _numCtl(label, key, unit, step) {
    const id = this._id(key);
    if (!id || !this._hass.states[id]) return "";
    const v = this._pendVal(id);
    const pend = this._pend && this._pend[id];
    const d = unit === "" ? 0 : 1;
    const txt = `${v > 0 && unit === "K" ? "+" : ""}${lccFmt(v, d)}${unit === "K" ? " K" : unit === "°" ? "°" : ""}${pend ? ' <i class="sync">⟳</i>' : ""}`;
    return this._ctl(label, txt, `data-act="num"${step ? ` data-step="${step}"` : ""}`, id);
  }

  _info_(key, text) {
    const open = this._info && this._info[key];
    return `<span class="ibtn ${open ? "on" : ""}" data-act="info" data-key="${key}">i</span>${open ? `<div class="itxt">${text}</div>` : ""}`;
  }

  _wwBase() {
    const c = this._st("ww_climate");
    const t = c ? parseFloat(c.attributes.temperature) : NaN;
    return Number.isNaN(t) ? this._n("ww_set") : t;
  }

  // Circulation pump: running, or ended within the last half hour
  _zirkInfo() {
    const s = this._st("ww_zirk_pump");
    if (!s) return { mode: "idle" };
    if (/^(on|1)$/i.test(String(s.state).trim())) return { mode: "run" };
    const ago = Date.now() - new Date(s.last_changed).getTime();
    return ago < LCC_CIRC_RECENT_MS ? { mode: "pause", ago } : { mode: "idle" };
  }

  _flash(el) {
    el.classList.add("flash");
    setTimeout(() => el.classList.remove("flash"), 700);
  }

  // ---------- Building blocks ----------
  _heroUnit(op, rating) {
    const running = rating > 0 || this._n("power") > 30;
    const speed = running ? lccClamp(2.6 - rating / 50, 0.35, 2.6) : 0;
    const col = op.color;
    const slats = [];
    for (let y = 12; y <= 118; y += 6.2) slats.push(`<line x1="8" x2="130" y1="${y.toFixed(1)}" y2="${y.toFixed(1)}"/>`);
    const branches = [
      "M24 120 C 34 92, 22 60, 34 6",
      "M32 72 C 44 56, 58 40, 54 6",
      "M66 120 C 60 88, 80 58, 88 6",
      "M82 62 C 100 50, 112 34, 118 6",
      "M40 120 C 66 102, 98 96, 130 78",
      "M14 54 C 22 42, 26 30, 20 6",
      "M98 96 C 108 76, 120 66, 130 42",
    ];
    return `
    <svg class="unit" viewBox="0 0 138 200" aria-hidden="true">
      <defs>
        <radialGradient id="uglow" cx="50%" cy="40%" r="60%">
          <stop offset="0%" stop-color="${col}" stop-opacity=".45"/>
          <stop offset="100%" stop-color="${col}" stop-opacity="0"/>
        </radialGradient>
        <linearGradient id="usteel" x1="0" y1="0" x2="1" y2="0">
          <stop offset="0" stop-color="#4b525b"/><stop offset=".3" stop-color="#8c949e"/><stop offset=".62" stop-color="#5f6770"/><stop offset=".9" stop-color="#c3cad2"/><stop offset="1" stop-color="#e5e7eb"/>
        </linearGradient>
        <linearGradient id="ubranch" x1="0" y1="1" x2="1" y2="0">
          <stop offset="0" stop-color="#8b95a1"/><stop offset=".5" stop-color="#f1f5f9"/><stop offset="1" stop-color="#9ca3af"/>
        </linearGradient>
        <clipPath id="ugrill"><rect x="8" y="6" width="122" height="114"/></clipPath>
      </defs>
      <ellipse cx="69" cy="90" rx="70" ry="98" fill="url(#uglow)" class="${running ? "pulse" : ""}"/>
      <path d="M12 2 H126 L134 9 V192 L127 198 H11 L4 192 V9 Z" fill="#05080d" stroke="#9aa3ad" stroke-width="1.3"/>
      <g clip-path="url(#ugrill)">
        <rect x="8" y="6" width="122" height="114" fill="#04070b"/>
        <circle cx="68" cy="62" r="48" fill="none" stroke="#1e3a5f" stroke-width="2" opacity=".7"/>
        <g class="fan" style="transform-origin:68px 62px;${running ? `animation-duration:${speed}s` : "animation:none"}">
          ${[0, 72, 144, 216, 288]
            .map((a) => `<path transform="rotate(${a} 68 62)" d="M68 62 C 71 42, 87 28, 102 33 C 96 49, 81 59, 68 62 Z" fill="#1f2937" stroke="#3b4a5e" stroke-width=".8"/>`)
            .join("")}
          <circle cx="68" cy="62" r="6" fill="#111827" stroke="#475569"/>
        </g>
        <g stroke="#b4bcc5" stroke-width="2.3" opacity=".92">${slats.join("")}</g>
        <g stroke="url(#ubranch)" stroke-width="3.4" fill="none" stroke-linecap="round">${branches.map((d) => `<path d="${d}"/>`).join("")}</g>
      </g>
      <path d="M8 120 H130 V191 L125 195 H13 L8 191 Z" fill="url(#usteel)"/>
      <line x1="8" x2="130" y1="120" y2="120" stroke="#e2e8f0" stroke-width="1"/>
      <line x1="118" x2="118" y1="121" y2="194" stroke="#d1d5db" stroke-width=".8" opacity=".6"/>
      <circle cx="122" cy="130" r="2.4" fill="${col}" class="pulse"/>
      ${op.mode === "defrost" ? `<text x="68" y="70" text-anchor="middle" font-size="24" class="spin-slow">❄️</text>` : ""}
    </svg>`;
  }

  _ring(pct, color, label, value, sub = "", ent = "") {
    const r = 34;
    const c = 2 * Math.PI * r;
    const p = lccClamp(Number.isNaN(pct) ? 0 : pct, 0, 1);
    return `
    <div class="ring" ${ent ? `data-ent="${lccEsc(ent)}"` : ""}>
      <svg viewBox="0 0 84 84">
        <circle cx="42" cy="42" r="${r}" stroke="#1e293b" stroke-width="8" fill="none"/>
        <circle cx="42" cy="42" r="${r}" stroke="${color}" stroke-width="8" fill="none" stroke-linecap="round"
          stroke-dasharray="${c * p} ${c}" transform="rotate(-90 42 42)" style="filter:drop-shadow(0 0 4px ${color})"/>
      </svg>
      <div class="ringtxt"><b>${value}</b><span>${label}</span>${sub ? `<em>${sub}</em>` : ""}</div>
    </div>`;
  }

  // ---------- Header ----------
  _pvBadge() {
    if (!this._has("pv_power")) return "";
    const pv = this._n("pv_power");
    const on = pv > 0;
    const night = this._t("sun") === "below_horizon";
    const icon = on ? "☀️" : night ? "🌙" : "☁️";
    const kw = Number.isNaN(pv) ? "–" : pv >= 1000 ? `${lccFmt(pv / 1000, 2)}<small>kW</small>` : `${lccFmt(pv, 0)}<small>W</small>`;
    return `<div class="pvbadge ${on ? "on" : ""}" data-ent="${lccEsc(this._id("pv_power"))}">
      <i class="${on ? "spin8" : ""}">${icon}</i><div><span>${L("pv_power")}</span><b>${kw}</b></div></div>`;
  }

  _battery() {
    if (!this._has("bat_soc")) return "";
    const soc = this._n("bat_soc");
    const ch = this._n("bat_charge") || 0;
    const dis = this._n("bat_discharge") || 0;
    const p = lccClamp(Number.isNaN(soc) ? 0 : soc, 0, 100);
    const col = p < 20 ? "#ef4444" : p < 50 ? "#f59e0b" : "#22c55e";
    const mode = ch > 5 ? "charge" : dis > 5 ? "discharge" : "idle";
    const txt = mode === "charge" ? `⚡ ${L("charging")} ${lccFmt(ch, 0)} W` : mode === "discharge" ? `▼ ${L("delivering")} ${lccFmt(dis, 0)} W` : "";
    const w = 96;
    return `<div class="batt ${mode}" data-ent="${lccEsc(this._id("bat_soc"))}">
      <svg viewBox="0 0 110 40">
        <defs><linearGradient id="bfill" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#fff" stop-opacity=".35"/><stop offset=".5" stop-color="#fff" stop-opacity="0"/></linearGradient></defs>
        <rect x="2" y="4" width="100" height="32" rx="7" fill="#0b1220" stroke="#94a3b8" stroke-width="2"/>
        <rect x="103" y="13" width="5" height="14" rx="2" fill="#94a3b8"/>
        <rect x="5" y="7" width="${(w - 2) * p / 100}" height="26" rx="5" fill="${col}" class="${mode === "charge" ? "pulse" : ""}" style="filter:drop-shadow(0 0 6px ${col})"/>
        <rect x="5" y="7" width="${(w - 2) * p / 100}" height="26" rx="5" fill="url(#bfill)"/>
        ${mode === "charge" ? `<path d="M56 9 L46 22 H53 L49 31 L60 17 H53 Z" fill="#fff" opacity=".9"/>` : ""}
        <text x="52" y="26" text-anchor="middle" class="btxt" ${mode === "charge" ? 'dx="-18"' : ""}>${Number.isNaN(soc) ? "–" : lccFmt(soc, 0) + "%"}</text>
      </svg>
      ${txt ? `<span>${txt}</span>` : ""}
    </div>`;
  }

  _box(x, y, w, h, val, d = 1) {
    return `<rect x="${x}" y="${y}" width="${w}" height="${h}" rx="2" class="vbox"/><text x="${x + w / 2}" y="${y + h / 2 + 5}" text-anchor="middle" class="vtxt">${lccFmt(val, d)}</text>`;
  }

  _ctrlTiles() {
    const wwTop = this._n("ww_top");
    const wwState = this._t("ww_state");
    const bTop = this._n("buf_top");
    const bLow = this._n("buf_low");
    const bState = this._t("buf_state");
    const hcVl = this._n("hc_vl");
    const hcRl = this._n("hc_rl");
    const hcSoll = this._n("hc_soll");
    const room = this._f("room_thermostat") ? this._n("room") : NaN;
    const roomSet = this._n("room_set");
    const hcState = this._t("hc_state");
    const showWw = this._has("ww_top") || this._has("ww_state");
    const showBuf = this._has("buf_top") || this._has("buf_state");
    const showHc = this._has("hc_vl") || this._has("hc_state");
    // Circulation: a short note while the pump runs or has just run
    const zk = this._zirkInfo();
    let zTxt = "";
    if (zk.mode === "run") zTxt = L("circ_runs");
    else if (zk.mode === "pause") zTxt = L("ago", Math.round(zk.ago / 60000));
    const hcRun = /^(heating|eco)$/i.test(String(hcState).trim());
    const wwRun = !/stby|off|unknown|unavail/i.test(wwState);
    const bRun = !/stby|off|unknown|unavail/i.test(bState);
    const pump = (x, y, on) =>
      `<circle cx="${x}" cy="${y}" r="7" fill="${on ? "#a3e635" : "#e5e7eb"}" stroke="#111827" stroke-width="1.2" class="${on ? "pulse" : ""}"/><path d="M${x - 3} ${y - 4} L${x + 4} ${y} L${x - 3} ${y + 4} Z" fill="#111827"/>`;
    let coil = "M84 60";
    for (let i = 0; i < 9; i++) coil += ` L${i % 2 ? 84 : 116} ${60 + i * 7 + 3.5}`;
    let mea = "M52 54 V16";
    let my = 16;
    for (let i = 1; i <= 11; i++) {
      my = my === 16 ? 54 : 16;
      mea += ` H${52 + i * 8} V${my}`;
    }
    const st = (s, on) => `<span class="cstate ${on ? "on" : ""}">${lccEsc(lccState(s))}</span>`;
    const ww = !showWw ? "" : `
      <div class="ctrl" data-ent="${lccEsc(this._id("ww_top"))}">
        <div class="cbar"><span class="cval">◀ ${lccFmt(this._wwBase(), 1)}°</span>${st(wwState, wwRun)}</div>
        <div class="cimg"><svg viewBox="0 0 200 150">
          <defs><linearGradient id="cww" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#ef4444"/><stop offset=".55" stop-color="#a855f7"/><stop offset="1" stop-color="#3b82f6"/></linearGradient></defs>
          <path d="M100 14 V4 H150" class="pr"/>
          <rect x="70" y="14" width="60" height="120" rx="24" fill="url(#cww)" opacity=".85" stroke="#cbd5e1" stroke-width="1.5"/>
          <path d="${coil}" fill="none" stroke="#7c3aed" stroke-width="3" opacity=".9"/>
          <path d="M14 40 H70" class="pr"/>${pump(40, 40, wwRun)}
          <path d="M100 134 V146 H150" class="pb"/>
          <path d="M14 116 H70" class="pb"/>
          <circle cx="134" cy="74" r="3" fill="#f8fafc"/>
          ${zTxt ? `<text x="140" y="71" class="ztxt">${L("circ")}</text><text x="140" y="83" class="ztxt ${zk.mode}">${zTxt}</text>` : ""}
          ${this._box(74, 62, 52, 22, wwTop)}
        </svg></div>
        ${this._has("ww_climate")
          ? this._ctl(`🌡️ ${L("setpoint")}`, `${lccFmt(this._pendVal(this._id("ww_climate")), 0)}°`, 'data-act="clim"', this._id("ww_climate"))
          : ""}
        ${this._numCtl(`☀️ ${L("pv_increase")}`, "ww_pv_offset", "K", 0.5)}
        <div class="cfoot">${L("hot_water")}</div>
      </div>`;
    const buf = !showBuf ? "" : `
      <div class="ctrl" data-ent="${lccEsc(this._id("buf_top"))}">
        <div class="cbar"><span class="cval">◀ ${lccFmt(hcSoll + this._bufOff(), 1)}°</span>${st(bState, bRun)}</div>
        <div class="cimg"><svg viewBox="0 0 200 150">
          <defs><linearGradient id="cbf" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#6b7280"/><stop offset=".45" stop-color="#d1d5db"/><stop offset="1" stop-color="#4b5563"/></linearGradient></defs>
          <rect x="84" y="14" width="86" height="122" rx="10" fill="url(#cbf)" stroke="#e5e7eb" stroke-width="1"/>
          <ellipse cx="127" cy="16" rx="43" ry="6" fill="#e5e7eb" opacity=".6"/>
          <path d="M10 40 H96" class="pr"/>${pump(46, 40, bRun)}<circle cx="96" cy="40" r="4" fill="#111827"/>
          <path d="M10 112 H96" class="pb"/><circle cx="96" cy="112" r="4" fill="#111827"/>
          ${this._box(104, 29, 52, 22, bTop)}
          ${this._box(104, 101, 52, 22, bLow)}
        </svg></div>
        ${this._numCtl(`☀️ ${L("pv_increase")}`, "buf_pv_offset", "K", 0.5)}
        <div class="cfoot">${L("buffer")}</div>
      </div>`;
    const hc = !showHc ? "" : `
      <div class="ctrl" data-ent="${lccEsc(this._id("hc_vl"))}">
        <div class="cbar"><span class="cval">◀ ${lccFmt(hcSoll, 1)}°</span>${st(hcState, hcRun)}</div>
        <div class="cimg"><svg viewBox="0 0 200 150">
          <defs><linearGradient id="chk" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#3b82f6"/><stop offset="1" stop-color="#ef4444"/></linearGradient></defs>
          <path d="${mea}" fill="none" stroke="url(#chk)" stroke-width="3"/>
          <path d="M14 136 H186" class="pr"/><path d="M14 144 H186" class="pb"/>
          <path d="M52 54 V144" class="pb"/><path d="M140 54 V136" class="pr"/>
          ${pump(140, 124, hcRun)}
          <text x="57" y="64" class="plbl">${L("ret")}</text><text x="135" y="64" text-anchor="end" class="plbl">${L("flow")}</text>
          ${this._box(4, 70, 44, 22, hcRl)}
          ${this._box(92, 70, 44, 22, hcVl)}
          ${this._f("room_thermostat") ? this._box(150, 70, 46, 22, room) : ""}
          <path d="M147 108 l6 -6 v12 z" fill="#cbd5e1"/>
          ${this._box(152, 97, 44, 22, roomSet)}
        </svg></div>
        ${this._numCtl(`🎯 ${L("room_setpoint")}`, "raum_soll", "°", 0.5)}
        ${this._numCtl(`☀️ ${L("pv_increase")}`, "pv_offset", "K", 0.5)}
        <div class="cfoot">${L("floor")}</div>
      </div>`;
    return `<div class="ctrls">${ww}${buf}${hc}</div>`;
  }

  _renderPopup() {
    const opS = this._st("op");
    const running = ["heat", "ww", "defrost", "cool"].includes(this._op().mode);
    const runTxt = opS ? lccDur(Date.now() - new Date(opS.last_changed).getTime()) : "–";
    const runLbl = running ? L("runtime_since") : L("idle_since");
    const fn = (key, name, icon, info, ext = "") => {
      const on = this._f(key);
      const ik = "fn_" + key;
      const open = this._info && this._info[ik];
      return `<div class="arow ${on ? "on" : ""}">
        <div class="arow1">
          <span class="emo">${icon}</span>
          <div class="aname"><b>${lccEsc(name)}</b><em>${on ? L("on") : L("off")}</em></div>
          <span class="ibtn ${open ? "on" : ""}" data-act="info" data-key="${lccEsc(ik)}">i</span>
          <div class="sw" data-act="noop"><i></i></div>
        </div>
        ${open ? `<div class="itxt">${info}</div>` : ""}
        ${on ? ext : ""}
      </div>`;
    };
    const nOn = ["pv_surplus", "room_thermostat"].filter((k) => this._f(k)).length;
    return `
    <div class="modal" data-act="close-popup">
      <div class="mbox" data-act="noop">
        <div class="mhead"><b>🤖 ${L("popup_title")}</b><span class="mx" data-act="close-popup">✕</span></div>
        <div class="panel">
          <div class="ph">🧮 ${L("counters")}</div>
          <div class="counters c3">
            <div data-ent="${lccEsc(this._id("abtau_tag"))}"><b>${lccFmt(this._n("abtau_tag"), 0)}</b><span>${L("defrosts_today")}</span></div>
            <div data-ent="${lccEsc(this._id("cnt_abtau"))}"><b>${lccFmt(this._n("cnt_abtau"), 0)}</b><span>${L("defrosts_total")}</span></div>
            <div data-ent="${lccEsc(this._id("op"))}"><b>${lccEsc(runTxt)}</b><span>${runLbl}</span></div>
          </div>
        </div>
        ${this._config.details_path ? `<button class="act ghost wide" data-act="nav" data-path="${lccEsc(this._config.details_path)}"><span>📋</span>${L("all_entities")}</button>` : ""}
        <div class="agrp">
          <div class="agh"><span>🎛️</span><div><b>${L("functions")}</b><em>${L("functions_sub")}</em></div><i>${nOn}/2 ${L("active")}</i></div>
          <div class="agb">
            ${fn("pv_surplus", L("fn_pv"), "☀️", L("fn_pv_info"))}
            ${fn("room_thermostat", L("fn_room"), "🏠", L("fn_room_info"))}
          </div>
        </div>
      </div>
    </div>`;
  }

  _sum(keys) {
    const vals = keys.map((k) => this._n(k)).filter((v) => !Number.isNaN(v));
    return vals.length ? vals.reduce((a, b) => a + b, 0) : NaN;
  }
  _powerToday() {
    return this._sum(["strom_hz", "strom_ww", "strom_abt", "strom_kuehl", "strom_sb"]);
  }
  _heatToday() {
    return this._sum(["waerme_hz", "waerme_ww", "waerme_abt", "waerme_kuehl"]);
  }

  _renderTop() {
    const op = this._op();
    const rating = this._n("rating");
    const opState = this._st("op");
    const since = opState ? lccDur(Date.now() - new Date(opState.last_changed).getTime()) : "";
    const err = this._t("err");
    const errOk = /^(ok|none|0|unknown|unavailable)$/i.test(String(err).trim());
    const vl = this._n("vl");
    const rl = this._n("rl");
    const power = this._n("power");
    const heat = this._n("heat");
    const cop = this._n("cop");
    const heizstab = this._t("heizstab");

    // Power sources (optional, from the card YAML)
    const pv = Math.max(0, this._n("src_pv") || 0);
    const bat = Math.max(0, this._n("src_bat") || 0);
    const grid = Math.max(0, this._n("src_grid") || 0);
    const sum = pv + bat + grid;

    // Tariff (optional, from the card YAML)
    const tn = this._tariffNow();
    const tf = this._config.tariffs;
    const now = new Date();
    const nowPos = ((now.getHours() + now.getMinutes() / 60) / 24) * 100;
    let segs = "";
    let cursor = 0;
    const wins = [...tf.windows].sort((a, b) => a.from - b.from);
    for (const w of wins) {
      if (w.from > cursor) segs += `<div class="seg" style="left:${(cursor / 24) * 100}%;width:${((w.from - cursor) / 24) * 100}%;background:${tf.standard.color}">${lccFmt(tf.standard.price, 2)}</div>`;
      segs += `<div class="seg" style="left:${(w.from / 24) * 100}%;width:${((w.to - w.from) / 24) * 100}%;background:${w.color}">${lccFmt(w.price, 2)}</div>`;
      cursor = w.to;
    }
    if (cursor < 24) segs += `<div class="seg" style="left:${(cursor / 24) * 100}%;width:${((24 - cursor) / 24) * 100}%;background:${tf.standard.color}">${lccFmt(tf.standard.price, 2)}</div>`;

    const wwNow = op.mode === "ww";
    const fnOn = ["pv_surplus", "room_thermostat"].filter((k) => this._f(k)).length;

    const cell = (key, label, value, extra = "") =>
      `<div class="bd" data-ent="${lccEsc(this._id(key))}"><span>${label}</span><b>${value}</b>${extra}</div>`;

    const hsOn = this._has("heizstab") && !/^(aus|off|0|unknown|unavailable)$/i.test(String(heizstab).trim());
    const alerts = [
      !errOk ? `<span class="badge bad" data-ent="${lccEsc(this._id("err"))}">⚠ ${lccEsc(lccState(err))} #${lccEsc(this._t("errnum"))}</span>` : "",
      hsOn ? `<span class="badge warn" data-ent="${lccEsc(this._id("heizstab"))}">🔥 ${L("heating_rod")}</span>` : "",
    ].join("");
    const surplus = this._surplus();
    const pvOn = surplus > 0;
    const night = this._t("sun") === "below_horizon";
    const pvIcon = pvOn ? '<i class="pvi sun">☀️</i>' : night ? '<i class="pvi moon">🌙</i>' : '<i class="pvi cloud">☁️</i>';
    const sTag = this._powerToday();
    const dayAz = sTag > 0.05 ? this._heatToday() / sTag : NaN;
    const pvText = pvOn ? `${lccFmt(surplus, 0)}<small>W</small>` : night ? "" : L("none");
    const runToday = this._sum(["lz_hz", "lz_ww", "lz_abt"]);
    const hasLeft = this._has("pv_power") || this._has("bat_soc");

    return `
    <div class="hero" style="--op:${op.color}">
      <div class="leftcol">
        ${this._pvBadge()}
        <div class="unitbox">${this._heroUnit(op, rating)}</div>
        ${this._battery()}
      </div>
      <div class="herotxt">
        <div class="hhead">
          <div class="opline" data-ent="${lccEsc(this._id("op"))}"><span class="dot"></span>${lccEsc(op.text)}</div>
          ${alerts}
          <div class="since">${lccEsc(since)}</div>
        </div>
        <div class="atrow">
          ${this._has("wfp_at") ? `<div class="wfp" data-ent="${lccEsc(this._id("wfp_at"))}"><span>${L("wfp_at")}</span><b>${lccFmt(this._atWfp(), 1)}°</b></div>` : ""}
          <div data-ent="${lccEsc(this._id("atcalc"))}"><span>${L("at_calc")}</span><b>${lccFmt(this._n("atcalc"), 1)}°</b></div>
          <div data-ent="${lccEsc(this._id("at"))}"><span>${L("at_actual")}</span><b>${lccFmt(this._n("at"), 1)}°</b></div>
        </div>
        <div class="bgrid">
          ${wwNow
            ? cell("ww_set", L("set_ww"), `${lccFmt(this._wwBase() + (pvOn ? this._n("ww_pv_offset") || 0 : 0), 1)}<small>°C</small>`)
            : cell("hc_soll", L("set_flow"), `${lccFmt(this._n("hc_soll") + this._bufOff(), 1)}<small>°C</small>`)}
          ${cell("vl", L("flow"), `<em class="vlred">${lccFmt(vl, 1)}</em><small>°C</small>`)}
          ${cell("rl", L("ret"), `<em style="color:${lccTempColor(rl, 15, 55)}">${lccFmt(rl, 1)}</em><small>°C</small>`)}
          ${cell("rating", L("compressor"), `${lccFmt(rating, 0)}<small>%</small>`, `<div class="mini"><i style="width:${lccClamp(rating || 0, 0, 100)}%"></i></div>`)}
          ${cell("heat", L("output"), `${lccFmt(heat, 2)}<small>kW</small>`)}
          ${cell("cop", L("cop"), `<em class="${cop >= 4 ? "good" : ""}">${lccFmt(Number.isNaN(cop) ? NaN : Math.max(0, cop), 2)}</em>`)}
          ${cell("power", L("input"), `${lccFmt(Number.isNaN(power) ? NaN : power / 1000, 2)}<small>kW</small>`)}
          ${cell("strom_hz", L("power_today"), `${lccFmt(sTag, 2)}<small>kWh</small>`)}
          ${cell("waerme_hz", L("cop_day"), `<em class="${dayAz >= 4 ? "good" : ""}">${lccFmt(dayAz, 2)}</em>`)}
          ${this._f("pv_surplus")
            ? `<div class="bd pvtile ${pvOn ? "glow" : night ? "night" : ""}" data-ent="${lccEsc(this._id("pv_surplus"))}"><span>${L("pv_surplus")}</span><b>${pvIcon} ${pvText}</b></div>`
            : cell("lz_hz", L("runtime_today"), `${lccHours(runToday)}`)}
          ${cell("abtau_tag", L("defrosts"), `${lccFmt(this._n("abtau_tag"), 0)} <small>❄️</small>`)}
          ${cell("umschalt", L("switches"), `${lccFmt(this._n("umschalt"), 0)} <small>🔁</small>`)}
        </div>
      </div>
    </div>

    ${this._ctrlTiles()}

    <div class="row2 curverow">
      ${this._tileHeizkurve()}
      ${this._tileSchaltpunkte()}
    </div>

    <div class="row2">
      ${this._has("src_pv") || this._has("src_grid") ? `<div class="panel">
        <div class="ph">🔌 ${L("src_now")} <span>${sum > 0 ? lccFmt(sum, 0) + " W" : L("hp_idle")}</span></div>
        <div class="srcbar">
          ${sum > 0
            ? `<i style="width:${(pv / sum) * 100}%;background:#fbbf24" data-ent="${lccEsc(this._id("src_pv"))}"></i><i style="width:${(bat / sum) * 100}%;background:#34d399" data-ent="${lccEsc(this._id("src_bat"))}"></i><i style="width:${(grid / sum) * 100}%;background:#f87171" data-ent="${lccEsc(this._id("src_grid"))}"></i>`
            : `<i style="width:100%;background:#1e293b"></i>`}
        </div>
        <div class="legend"><span><i style="background:#fbbf24"></i>PV ${lccFmt(pv, 0)} W</span><span><i style="background:#34d399"></i>${L("storage")} ${lccFmt(bat, 0)} W</span><span><i style="background:#f87171"></i>${L("grid")} ${lccFmt(grid, 0)} W</span></div>
      </div>` : ""}
      ${tf.windows.length || tf.standard.price != null ? `<div class="panel">
        <div class="ph">💶 ${L("tariff_title")} <span style="color:${tn.color}">${lccEsc(tn.name)} · ${lccFmt(tn.price, 2)} ct</span></div>
        <div class="tbar">${segs}<div class="needle" style="left:${nowPos}%"></div></div>
        <div class="tticks"><span>0</span><span>6</span><span>12</span><span>18</span><span>24</span></div>
        <div class="tleft" style="color:${tn.color}">${L("tariff_left", lccDurHM(tn.endsIn))}</div>
      </div>` : ""}
    </div>

    <div class="panel">
      <div class="ph">🎛️ ${L("actions")}</div>
      <div class="actions">
        <button class="act ghost" data-act="popup"><span>🤖</span>${L("functions_btn")}<em>${fnOn} ${L("active")}</em></button>
      </div>
    </div>`;
  }

  // ---------- Tiles ----------
  _tileRuntime() {
    const parts = [
      [L("rt_heating"), this._n("lz_hz"), "#fb923c", "lz_hz"],
      [L("rt_dhw"), this._n("lz_ww"), "#38bdf8", "lz_ww"],
      [L("rt_defrost"), this._n("lz_abt"), "#7dd3fc", "lz_abt"],
      [L("rt_rod"), this._n("lz_hs"), "#ef4444", "lz_hs"],
    ];
    const now = new Date();
    const elapsed = now.getHours() + now.getMinutes() / 60;
    const total = Math.max(elapsed, parts.reduce((s, p) => s + (p[1] || 0), 0)) || 1;
    const run = (parts[0][1] || 0) + (parts[1][1] || 0) + (parts[2][1] || 0);
    const r = 40;
    const c = 2 * Math.PI * r;
    let acc = 0;
    const donut = parts
      .map(([, h, col]) => {
        const f = (h || 0) / total;
        const s = `<circle cx="50" cy="50" r="${r}" fill="none" stroke="${col}" stroke-width="14" stroke-dasharray="${c * f} ${c}" stroke-dashoffset="${-c * acc}" transform="rotate(-90 50 50)"/>`;
        acc += f;
        return s;
      })
      .join("");
    const rest = Math.max(0, elapsed - parts.reduce((s, p) => s + (p[1] || 0), 0) + (parts[3][1] || 0));
    return `
    <div class="tile">
      <div class="th"><span>⏱️ ${L("runtimes")}</span><em>${lccFmt((run / Math.max(elapsed, 0.01)) * 100, 0)} % ${L("active")}</em></div>
      <div class="rt">
        <svg viewBox="0 0 100 100" class="donut"><circle cx="50" cy="50" r="${r}" fill="none" stroke="#0f172a" stroke-width="14"/>${donut}
          <text x="50" y="48" text-anchor="middle" class="dv">${lccHours(run)}</text><text x="50" y="62" text-anchor="middle" class="dl">${L("compressor")}</text></svg>
        <div class="rtl">${parts
          .map(([n, h, col, k]) => `<div data-ent="${lccEsc(this._id(k))}"><i style="background:${col}"></i><span>${n}</span><b>${lccHours(h)}</b></div>`)
          .join("")}<div><i style="background:#334155"></i><span>${L("rt_rest")}</span><b>${lccHours(rest)}</b></div></div>
      </div>
      <div class="chips">
        <span data-ent="${lccEsc(this._id("starts_hz"))}">🔥 ${lccFmt(this._n("starts_hz"), 0)} ${L("starts_heating")}</span>
        <span data-ent="${lccEsc(this._id("starts_ww"))}">🚿 ${lccFmt(this._n("starts_ww"), 0)} ${L("starts_dhw")}</span>
        <span data-ent="${lccEsc(this._id("umschalt"))}">🔁 ${lccFmt(this._n("umschalt"), 0)} ${L("switches")}</span>
      </div>
    </div>`;
  }

  _tileEnergy() {
    const sHz = this._n("strom_hz");
    const sWw = this._n("strom_ww");
    const wHz = this._n("waerme_hz");
    const wWw = this._n("waerme_ww");
    const netz = this._n("netz_tag");
    const eigen = this._n("eigen_tag");
    const tot = this._powerToday();
    const copHz = sHz > 0.05 ? wHz / sHz : NaN;
    const copWw = sWw > 0.05 ? wWw / sWw : NaN;
    const maxS = Math.max(sHz || 0, sWw || 0, 0.1);
    const maxW = Math.max(wHz || 0, wWw || 0, 0.1);
    const bar = (label, s, w, cop, col, ks, kw) => `
      <div class="ebar">
        <div class="eh"><b>${label}</b><span>${L("cop")} ${lccFmt(cop, 2)}</span></div>
        <div class="eline" data-ent="${lccEsc(this._id(ks))}"><em>${L("power")}</em><div><i style="width:${((s || 0) / maxS) * 100}%;background:#facc15"></i></div><b>${lccFmt(s, 2)} kWh</b></div>
        <div class="eline" data-ent="${lccEsc(this._id(kw))}"><em>${L("heat")}</em><div><i style="width:${((w || 0) / maxW) * 100}%;background:${col}"></i></div><b>${lccFmt(w, 1)} kWh</b></div>
      </div>`;
    const origin = this._has("netz_tag") || this._has("eigen_tag");
    const otot = (netz || 0) + (eigen || 0);
    return `
    <div class="tile">
      <div class="th"><span>⚡ ${L("energy_today")}</span><em>${lccFmt(tot, 2)} kWh</em></div>
      ${bar(`🔥 ${L("heating")}`, sHz, wHz, copHz, "#fb923c", "strom_hz", "waerme_hz")}
      ${bar(`🚿 ${L("hot_water")}`, sWw, wWw, copWw, "#38bdf8", "strom_ww", "waerme_ww")}
      ${origin ? `<div class="ph" style="margin-top:10px">${L("origin_today")}</div>
      <div class="srcbar">${otot > 0 ? `<i style="width:${(eigen / otot) * 100}%;background:#34d399" data-ent="${lccEsc(this._id("eigen_tag"))}"></i><i style="width:${(netz / otot) * 100}%;background:#f87171" data-ent="${lccEsc(this._id("netz_tag"))}"></i>` : `<i style="width:100%;background:#1e293b"></i>`}</div>
      <div class="legend"><span><i style="background:#34d399"></i>${L("pv_storage")} ${lccFmt(eigen, 2)} kWh</span><span><i style="background:#f87171"></i>${L("grid")} ${lccFmt(netz, 2)} kWh</span></div>` : ""}
    </div>`;
  }

  _tileEff() {
    const jaz = this._n("e_out") / this._n("e_in");
    const jHz = this._n("hz_out") / this._n("hz_in");
    const jWw = this._n("ww_out") / this._n("ww_in");
    const sc = (x) => lccClamp((x - 1) / 6, 0, 1);
    return `
    <div class="tile">
      <div class="th"><span>🏆 ${L("efficiency")}</span><em>${L("jaz")}</em></div>
      <div class="rings">
        ${this._ring(sc(jaz), "#a78bfa", L("total"), lccFmt(jaz, 2), "", this._id("e_out"))}
        ${this._ring(sc(jHz), "#fb923c", L("heating"), lccFmt(jHz, 2), L("since_ha"), this._id("hz_out"))}
        ${this._ring(sc(jWw), "#38bdf8", L("hot_water"), lccFmt(jWw, 2), L("since_ha"), this._id("ww_out"))}
      </div>
    </div>`;
  }

  _tileHeizkurve() {
    const W = 340;
    const H = 232;
    const pad = { l: 30, r: 30, t: 10, b: 58 };
    const ok = ["curve_m22", "curve_0", "curve_p22"].every((k) => !Number.isNaN(this._n(k)));
    // Scale the y axis to the curve, in steps of 5 K.
    const pts = ok ? [this._n("curve_m22"), this._n("curve_0"), this._n("curve_p22")] : [25, 35];
    const yMin = Math.min(15, Math.floor(Math.min(...pts) / 5) * 5);
    const yMax = Math.max(45, Math.ceil(Math.max(...pts) / 5) * 5);
    const X = (t) => pad.l + ((22 - t) / 44) * (W - pad.l - pad.r); // +22 on the left, -22 on the right, as on the Lambda
    const Y = (v) => pad.t + (1 - (lccClamp(v, yMin, yMax) - yMin) / (yMax - yMin)) * (H - pad.t - pad.b);
    const atW = this._atWfp();
    const atC = this._n("atcalc");
    const soll = this._n("hc_soll");
    const yBot = H - pad.b;
    const wfpActive = !Number.isNaN(atW) && !Number.isNaN(atC) && Math.abs(atW - atC) >= 0.3;
    let grid = "";
    for (let v = yMin; v <= yMax; v += 5) grid += `<line x1="${pad.l}" x2="${W - pad.r}" y1="${Y(v)}" y2="${Y(v)}" class="gl"/><text x="${pad.l - 4}" y="${Y(v) + 3}" text-anchor="end" class="gt">${v}</text><text x="${W - pad.r + 4}" y="${Y(v) + 3}" class="gt">${v}</text>`;
    for (let t = 20; t >= -20; t -= 4) grid += `<line x1="${X(t)}" x2="${X(t)}" y1="${pad.t}" y2="${yBot}" class="gl dash"/><text x="${X(t)}" y="${yBot + 11}" text-anchor="middle" class="gt">${t}</text>`;
    const path = `M${X(22)},${Y(this._curve(22))} L${X(0)},${Y(this._curve(0))} L${X(-22)},${Y(this._curve(-22))}`;
    let marks = "";
    if (ok && !Number.isNaN(atC)) marks += `<line x1="${X(atC)}" x2="${X(atC)}" y1="${yBot}" y2="${Y(this._curve(atC))}" stroke="#3b82f6" stroke-width="3"/>`;
    if (ok && wfpActive) marks += `<line x1="${X(atW)}" x2="${X(atW)}" y1="${yBot}" y2="${Y(this._curve(atW))}" stroke="#22c55e" stroke-width="3"/><circle cx="${X(atW)}" cy="${Y(this._curve(atW))}" r="4" fill="#22c55e" class="pulse"/>`;
    const box = (t, key) => {
      const cx = X(t);
      const v = this._n(key);
      return `<g data-ent="${lccEsc(this._id(key))}"><path d="M${cx - 22},${yBot + 26} L${cx},${yBot + 18} L${cx + 22},${yBot + 26} Z" fill="#9ca3af"/>
        <rect x="${cx - 24}" y="${yBot + 26}" width="48" height="20" fill="#e5e7eb" stroke="#6b7280"/>
        <text x="${cx}" y="${yBot + 40}" text-anchor="middle" class="ptxt">${lccFmt(v, 1)}</text></g>`;
    };
    return `
    <div class="tile hk">
      <div class="th"><span>📈 ${L("curve_title")}</span><em>${L("set_flow")} ${lccFmt(soll, 1)}°</em></div>
      <svg class="curve2" viewBox="0 0 ${W} ${H}">
        <rect x="${pad.l}" y="${pad.t}" width="${W - pad.l - pad.r}" height="${yBot - pad.t}" fill="#2b3138"/>
        ${grid}
        ${ok ? `<path d="${path}" class="cvr"/>` : ""}
        ${marks}
        ${box(20, "curve_p22")}${box(0, "curve_0")}${box(-20, "curve_m22")}
      </svg>
      <div class="legend"><span><i style="background:#ef4444"></i>${L("curve")}</span><span><i style="background:#3b82f6"></i>${L("at_calc")} ${lccFmt(atC, 1)}°</span><span><i style="background:#22c55e"></i>${wfpActive ? `${L("wfp_at")} ${lccFmt(atW, 1)}°` : L("wfp_none")}</span></div>
      <div class="hkoff">${this._numCtl(`📈 ${L("curve_offset")}`, "offset", "K", 0.5)}</div>
    </div>`;
  }

  _tileSchaltpunkte() {
    const pvOn = this._surplus() > 0;
    const blk = (title, ist, istLbl, ein, aus, running, extra, infoKey, infoTxt) => {
      const okv = [ein, aus].every((x) => !Number.isNaN(x));
      const lo = Math.min(ein, aus, Number.isNaN(ist) ? ein : ist) - 3;
      const hi = Math.max(ein, aus, Number.isNaN(ist) ? aus : ist) + 3;
      const P = (v) => lccClamp(((v - lo) / (hi - lo)) * 100, 0, 100);
      let status;
      if (!okv) status = L("no_data");
      else if (running) status = L("sp_running", lccFmt(aus, 1), lccFmt(Math.max(0, aus - ist), 1));
      else if (ist < ein) status = L("sp_met", lccFmt(ein - ist, 1));
      else status = L("sp_wait", lccFmt(ein, 1), lccFmt(ist - ein, 1));
      return `
      <div class="spblk ${running ? "run" : ""}">
        <div class="sph"><b>${title}</b>${this._info_(infoKey, infoTxt)}</div>
        <div class="spbar">
          ${okv ? `<i class="zone" style="left:${P(Math.min(ein, aus))}%;width:${Math.abs(P(aus) - P(ein))}%"></i>
          <i class="mk ein" style="left:${P(ein)}%"></i><i class="mk aus" style="left:${P(aus)}%"></i>` : ""}
          ${okv && !Number.isNaN(ist) ? `<i class="dot" style="left:${P(ist)}%"></i>` : ""}
        </div>
        <div class="spvals"><span class="cblue">${L("start")} &lt; ${lccFmt(ein, 1)}°</span><span>${istLbl} ${lccFmt(ist, 1)}°</span><span class="cred">${L("stop")} ≥ ${lccFmt(aus, 1)}°</span></div>
        <div class="spstat">${status}${extra ? ` · ${extra}` : ""}</div>
      </div>`;
    };
    const opMode = this._op().mode;
    const has = (k) => this._has(k);
    const missing = !["p_ww_ein", "p_buf_ein25", "p_hk_spr"].some(has);
    // Hot water
    const wwSet = this._wwBase();
    const wwPv = pvOn ? this._n("ww_pv_offset") || 0 : 0;
    const wwSoll = wwSet + wwPv;
    const wwEin = wwSoll + this._n("p_ww_ein");
    const wwAus = wwSoll + this._n("p_ww_aus");
    // Buffer
    const hcSoll = this._n("hc_soll");
    const bPv = pvOn ? this._n("buf_pv_offset") || 0 : 0;
    const bSoll = hcSoll + this._bufOff() + bPv;
    const h25 = this._n("p_buf_ein25");
    const h50 = this._n("p_buf_ein50");
    const bH = h25 + ((h50 - h25) * (lccClamp(bSoll, 25, 50) - 25)) / 25;
    const bEin = bSoll + bH;
    const bAus = bSoll + this._n("p_buf_aus");
    // Heating circuit
    const rlSoll = hcSoll - this._n("p_hk_spr");
    const hEin = rlSoll + this._n("p_hk_ein");
    const hAus = rlSoll + this._n("p_hk_aus");
    const grenze = this._n("p_hk_grenze");
    const atC = this._n("atcalc");
    return `
    <div class="tile sp">
      <div class="th"><span>🎯 ${L("sp_title")}</span><em>${pvOn ? `☀️ ${L("pv_active")}` : L("without_pv")}</em></div>
      ${missing ? `<div class="hint" style="margin-bottom:8px">${L("sp_copy_hint")}</div>` : ""}
      ${has("ww_top") ? blk(`🚿 ${L("hot_water")}`, this._n("ww_top"), L("top"), wwEin, wwAus, opMode === "ww", `${L("set")} ${lccFmt(wwSoll, 1)}°${wwPv ? ` (${L("incl_pv", lccFmt(wwPv, 1))})` : ""}`, "sp_ww",
        L("sp_info_ww", pvOn ? L("sp_info_ww_pv") : "", lccFmt(this._n("p_ww_ein"), 1), lccFmt(this._n("p_ww_aus"), 1))) : ""}
      ${has("buf_top") ? blk(`🧱 ${L("buffer")}`, this._n("buf_top"), L("top"), bEin, bAus, opMode === "heat", `${L("set")} ${lccFmt(bSoll, 1)}°`, "sp_buf",
        L("sp_info_buf", lccFmt(this._bufOff(), 1), pvOn ? L("sp_info_buf_pv") : "", lccFmt(h25, 1), lccFmt(h50, 1))) : ""}
      ${has("hc_rl") ? blk(`♨️ ${L("floor")}`, this._n("hc_rl"), L("ret"), hEin, hAus, false, `${L("rl_set")} ${lccFmt(rlSoll, 1)}° · ${L("heat_limit")} ${lccFmt(grenze, 1)}° ${atC < grenze ? "✓" : "✗"}`, "sp_hk",
        L("sp_info_hc", lccFmt(hcSoll, 1), lccFmt(this._n("p_hk_spr"), 1), lccFmt(this._n("p_hk_ein"), 1), lccFmt(this._n("p_hk_aus"), 1))) : ""}
    </div>`;
  }

  _tileGrenzen() {
    const tagL = `<small class="tag lam">${L("tag_lambda")}</small>`;
    const tagC = `<small class="tag cp">${L("tag_copy")}</small>`;
    const rows = [
      this._numCtl(`🧱 ${L("buf_max")} ${tagL}`, "buf_max", "°", 1),
      this._numCtl(`♨️ ${L("hc_max")} ${tagC}`, "p_hk_max", "°", 0.5),
      this._numCtl(`🚿 ${L("ww_max")} ${tagC}`, "p_ww_max", "°", 0.5),
      this._numCtl(`🌡️ ${L("heat_limit_at")} ${tagC}`, "p_hk_grenze", "°", 0.5),
    ].join("");
    if (!rows) return "";
    return `
    <div class="tile grz">
      <div class="th"><span>ℹ️ ${L("limits")}</span><em>${L("info")}</em></div>
      ${rows}
      <div class="hint">${this._info_("grz", L("limits_info"))} ${L("limits_hint")}</div>
    </div>`;
  }

  _render() {
    if (!this._hass || !this._config) return;
    const oldBox = this.shadowRoot.querySelector && this.shadowRoot.querySelector(".mbox");
    const keepScroll = oldBox ? oldBox.scrollTop : 0;
    let html;
    try {
      html = `
      <ha-card>
        <div class="wrap">
          ${this._renderTop()}
          <div class="tiles">
            ${this._tileRuntime()}
            ${this._tileEnergy()}
            ${this._tileEff()}
            ${this._tileGrenzen()}
          </div>
          <div class="foot">${L("foot", LCC_VERSION)}</div>
        </div>
        ${this._popup ? this._renderPopup() : ""}
      </ha-card>`;
    } catch (e) {
      html = `<ha-card><div style="padding:16px;color:#f87171">${L("error")}: ${lccEsc(e.message)}</div></ha-card>`;
      console.error(e);
    }
    this.shadowRoot.innerHTML = `<style>${LCC_CSS}</style>${html}`;
    if (keepScroll) {
      const nb = this.shadowRoot.querySelector(".mbox");
      if (nb) nb.scrollTop = keepScroll;
    }
  }
}

const LCC_CSS = `
:host{--bg1:#0b1324;--bg2:#0f1b33;--card:#111c31;--card2:#0d1629;--line:#1f2d47;--txt:#e2e8f0;--mut:#8aa0bf;--acc:#5eead4;}
ha-card{background:radial-gradient(1200px 500px at 0% 0%,#13284a 0%,transparent 60%),linear-gradient(180deg,var(--bg1),var(--bg2));color:var(--txt);border-radius:22px;border:1px solid var(--line);overflow:hidden;font-family:inherit}
.wrap{padding:16px;display:flex;flex-direction:column;gap:14px}
.eyebrow{font-size:11px;letter-spacing:.18em;color:var(--mut);font-weight:600}
small{font-size:.6em;color:var(--mut);margin-left:2px;font-weight:500}
[data-ent],[data-act]{cursor:pointer}
.hero{display:flex;align-items:stretch;gap:14px;padding:12px 14px;border-radius:18px;background:linear-gradient(135deg,color-mix(in srgb,var(--op) 18%,transparent),transparent 70%),var(--card2);border:1px solid color-mix(in srgb,var(--op) 35%,var(--line))}
.herol{display:flex;align-items:center;gap:14px;min-width:0}
.unit{width:100%;height:100%;display:block;filter:drop-shadow(0 4px 10px rgba(0,0,0,.5))}
.fan{transform-origin:58px 55px;animation:spin 1s linear infinite}
@keyframes spin{to{transform:rotate(360deg)}}
.pulse{animation:pulse 2.4s ease-in-out infinite}
@keyframes pulse{0%,100%{opacity:.55}50%{opacity:1}}
.spin-slow{animation:pulse 1.2s infinite}
.opline{font-size:28px;font-weight:800;display:flex;align-items:center;gap:10px;color:var(--op);text-shadow:0 0 18px color-mix(in srgb,var(--op) 50%,transparent)}
.dot{width:12px;height:12px;border-radius:50%;background:var(--op);box-shadow:0 0 12px var(--op);animation:pulse 1.6s infinite}
.since{color:var(--mut);font-size:13px;margin-top:2px}.raw{opacity:.6}
.badges{display:flex;gap:6px;flex-wrap:wrap;margin-top:8px}
.badge{font-size:12px;padding:4px 10px;border-radius:999px;background:#1a2640;border:1px solid var(--line);color:var(--mut)}
.badge.ok{color:#34d399;border-color:#065f46}.badge.bad{color:#fca5a5;border-color:#7f1d1d;background:#2a1215}.badge.warn{color:#fdba74;border-color:#7c2d12}
.heror{text-align:right;margin-left:auto}
.bigtemp{font-size:44px;font-weight:800;line-height:1}
.atsub{display:flex;flex-direction:column;font-size:12px;color:var(--mut);margin-top:4px}
.kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:10px}
.kpi,.tcell{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:10px 12px;display:flex;flex-direction:column;gap:4px;transition:transform .15s}
.kpi:hover,.tcell:hover,.tile:hover{transform:translateY(-2px)}
.kpi span,.tcell span{font-size:12px;color:var(--mut)}
.kpi b,.tcell b{font-size:22px;font-weight:700}
.kpi em{font-style:normal}
.good{color:#34d399;text-shadow:0 0 10px rgba(52,211,153,.4)}
.mini{height:5px;background:#1e293b;border-radius:4px;overflow:hidden}.mini i{display:block;height:100%;background:linear-gradient(90deg,#5eead4,#a78bfa);border-radius:4px;transition:width .6s}
.row2{display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:14px}
.panel{background:var(--card);border:1px solid var(--line);border-radius:16px;padding:12px 14px}
.ph{display:flex;justify-content:space-between;gap:8px;font-size:11px;letter-spacing:.14em;color:var(--mut);font-weight:700;margin-bottom:10px}
.ph span{letter-spacing:0;font-size:13px;color:var(--txt)}
.srcbar{display:flex;height:14px;border-radius:8px;overflow:hidden;background:#1e293b}
.srcbar i{display:block;height:100%;transition:width .6s}
.legend{display:flex;flex-wrap:wrap;gap:10px;font-size:12px;color:var(--mut);margin-top:8px}
.legend i{display:inline-block;width:9px;height:9px;border-radius:3px;margin-right:5px;vertical-align:middle}
.tbar{position:relative;height:24px;border-radius:8px;overflow:hidden;background:#1e293b}
.seg{position:absolute;top:0;bottom:0;opacity:.85;display:flex;align-items:center;justify-content:center;font-size:11px;font-weight:800;color:#0b1220;overflow:hidden;white-space:nowrap}
.tleft{margin-top:8px;font-size:13px;font-weight:700}
.needle{position:absolute;top:-2px;bottom:-2px;width:3px;background:#fff;box-shadow:0 0 8px #fff;border-radius:2px}
.tticks{display:flex;justify-content:space-between;font-size:10px;color:var(--mut);margin-top:3px}
.today{display:grid;grid-template-columns:repeat(auto-fit,minmax(120px,1fr));gap:10px}
.actions{display:flex;flex-wrap:wrap;gap:8px}
.act{flex:1 1 140px;display:flex;align-items:center;gap:8px;justify-content:center;padding:12px;border-radius:14px;border:1px solid #27406b;background:linear-gradient(180deg,#183057,#122444);color:var(--txt);font:inherit;font-weight:600;font-size:14px;cursor:pointer;position:relative}
.act span{font-size:18px}
.act em{font-style:normal;font-size:11px;color:#34d399;margin-left:4px}
.act.live{border-color:#10b981;box-shadow:0 0 14px rgba(16,185,129,.35)}
.act.ghost{background:transparent;border-style:dashed}
.flash{animation:flash .7s}
@keyframes flash{0%{box-shadow:0 0 0 0 rgba(94,234,212,.8)}100%{box-shadow:0 0 0 14px rgba(94,234,212,0)}}
.stepper{flex:1 1 200px;display:flex;align-items:center;gap:8px;justify-content:center;padding:8px 12px;border-radius:14px;border:1px solid var(--line);background:var(--card2)}
.stepper .slabel{font-size:13px;color:var(--mut);margin-right:auto}
.stepper button{width:36px;height:36px;border-radius:50%;border:1px solid #27406b;background:#183057;color:var(--txt);font-size:20px;cursor:pointer}
.stepper b{font-size:22px;min-width:64px;text-align:center}
.counters{display:grid;grid-template-columns:repeat(3,1fr);gap:8px}
.counters div{background:var(--card2);border-radius:12px;padding:8px;text-align:center;border:1px solid var(--line)}
.counters b{display:block;font-size:20px;color:#5eead4}
.counters span{font-size:11px;color:var(--mut)}
.autos{display:grid;grid-template-columns:repeat(auto-fill,minmax(210px,1fr));gap:8px}
.autos.small{margin-top:8px}
.auto{display:flex;align-items:center;justify-content:space-between;gap:8px;padding:8px 10px;border-radius:12px;background:var(--card2);border:1px solid var(--line);opacity:.7;transition:all .2s}
.auto.on{opacity:1;border-color:#155e75;background:linear-gradient(90deg,rgba(20,184,166,.12),transparent)}
.aname{display:flex;align-items:center;gap:8px;min-width:0}
.aname b{display:block;font-size:13px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.aname em{font-style:normal;font-size:11px;color:var(--mut)}
.emo{font-size:18px}
.sw{width:40px;height:22px;border-radius:12px;background:#334155;position:relative;flex:none;transition:background .2s}
.sw i{position:absolute;top:3px;left:3px;width:16px;height:16px;border-radius:50%;background:#cbd5e1;transition:left .2s}
.auto.on .sw{background:#14b8a6}.auto.on .sw i{left:21px;background:#fff}
.morebtn{margin-top:10px;font-size:12px;color:var(--mut);text-align:center;padding:6px;border-radius:10px;border:1px dashed var(--line)}
.tiles{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:14px}
.tile{background:linear-gradient(180deg,#122039,#0d172b);border:1px solid var(--line);border-radius:18px;padding:14px;transition:transform .15s;min-width:0}
.tile.wide{grid-column:span 2}
@media (max-width:700px){.tile.wide{grid-column:span 1}}
.th{display:flex;justify-content:space-between;align-items:center;font-size:12px;letter-spacing:.14em;font-weight:700;color:var(--mut);margin-bottom:10px}
.th em{font-style:normal;letter-spacing:0;font-size:12px;padding:3px 10px;border-radius:999px;background:#1a2640;color:var(--mut)}
.th em.hot{background:rgba(251,146,60,.15);color:#fdba74;box-shadow:0 0 10px rgba(251,146,60,.25)}
.tankwrap{display:flex;gap:10px;align-items:center}
.tank{width:110px;height:190px;flex:none}
.wave{animation:wave 3s ease-in-out infinite}
@keyframes wave{0%,100%{transform:translateX(0)}50%{transform:translateX(-9px)}}
.bubble{animation:bubble 3s linear infinite}
@keyframes bubble{0%{transform:translateY(0);opacity:0}20%{opacity:.4}100%{transform:translateY(-140px);opacity:0}}
.tanklabels{display:flex;flex-direction:column;gap:6px;flex:1}
.tl{display:flex;justify-content:space-between;align-items:baseline;padding:6px 10px;border-radius:10px;background:var(--card2);border:1px solid var(--line)}
.tl span{font-size:12px;color:var(--mut)}.tl b{font-size:18px}
.fun{margin-top:10px;font-size:13px;line-height:1.5}
.ducks{font-size:18px;letter-spacing:2px;line-height:1.3}
.hint{font-size:11px;color:var(--mut)}
.curve{width:100%;height:auto}
.gl{stroke:#1e2d47;stroke-width:1}.gt{fill:#64748b;font-size:10px}
.cv{fill:none;stroke:#38bdf8;stroke-width:3;filter:drop-shadow(0 0 4px #38bdf8)}
.cvo{fill:none;stroke:#a78bfa;stroke-width:2;stroke-dasharray:6 4}
.grid4{display:grid;grid-template-columns:repeat(auto-fit,minmax(120px,1fr));gap:8px;margin-top:10px}
.grid4 div{background:var(--card2);border:1px solid var(--line);border-radius:10px;padding:7px 10px;display:flex;flex-direction:column}
.grid4 span{font-size:11px;color:var(--mut)}.grid4 b{font-size:17px}
.cold{color:#60a5fa}.warm{color:#fb923c}
.gauge{width:100%;max-width:300px;display:block;margin:0 auto}
.gval{fill:#f8fafc;font-size:22px;font-weight:800}
.needleg{transition:all .8s}
.rt{display:flex;gap:12px;align-items:center}
.donut{width:120px;height:120px;flex:none}
.dv{fill:#f8fafc;font-size:13px;font-weight:700}.dl{fill:#64748b;font-size:8px}
.rtl{flex:1;display:flex;flex-direction:column;gap:5px}
.rtl div{display:flex;align-items:center;gap:6px;font-size:13px}
.rtl i{width:10px;height:10px;border-radius:3px}.rtl span{flex:1;color:var(--mut)}
.chips{display:flex;flex-wrap:wrap;gap:6px;margin-top:10px}
.chips span{font-size:12px;padding:4px 10px;border-radius:999px;background:var(--card2);border:1px solid var(--line)}
.ebar{margin-bottom:10px}
.eh{display:flex;justify-content:space-between;font-size:13px;margin-bottom:4px}.eh span{color:#34d399;font-weight:700}
.eline{display:grid;grid-template-columns:48px 1fr 80px;gap:8px;align-items:center;font-size:12px;margin:3px 0}
.eline em{font-style:normal;color:var(--mut)}
.eline div{height:9px;background:#1e293b;border-radius:5px;overflow:hidden}.eline div i{display:block;height:100%;border-radius:5px}
.eline b{text-align:right;font-weight:600}
.rings{display:flex;justify-content:space-around;gap:6px}
.ring{position:relative;width:96px;height:96px}
.ring svg{width:100%;height:100%}
.ringtxt{position:absolute;inset:0;display:flex;flex-direction:column;align-items:center;justify-content:center}
.ringtxt b{font-size:18px}.ringtxt span{font-size:10px;color:var(--mut)}.ringtxt em{font-size:9px}
.tblwrap{overflow-x:auto}
table{width:100%;border-collapse:collapse;font-size:13px}
th{font-size:11px;color:var(--mut);text-align:right;font-weight:600;padding:4px 6px}
th:first-child,td:first-child{text-align:left}
td{text-align:right;padding:7px 6px;border-top:1px solid var(--line)}
td.dim{color:var(--mut)}td.red{color:#fca5a5}
.abar{position:relative;height:18px;background:#1e293b;border-radius:6px;overflow:hidden;min-width:90px}
.abar i{position:absolute;left:0;top:0;bottom:0;background:linear-gradient(90deg,#10b981,#5eead4)}
.abar span{position:relative;font-size:11px;font-weight:700;padding-right:6px;line-height:18px}
.foot{text-align:center;font-size:11px;color:#475569}
.atrow .wfp{border-color:#3b82f6;background:rgba(59,130,246,.12)}
.atrow .wfp b{color:#93c5fd}
.sync{font-style:normal;color:#fbbf24;display:inline-block;animation:spin 1.2s linear infinite}
.curverow{grid-template-columns:repeat(auto-fit,minmax(320px,1fr))}
.curve2{width:100%;height:auto;display:block;border-radius:8px}
.gl.dash{stroke-dasharray:2 3}
.cvw{fill:none;stroke:#f8fafc;stroke-width:1.5;opacity:.7}
.cvr{fill:none;stroke:#ef4444;stroke-width:3}
.ptxt{fill:#111827;font-size:12px;font-weight:700}
.hkoff .cstep{border:1px solid var(--line);border-radius:10px;margin-top:8px}
.cvg{fill:none;stroke:#22c55e;stroke-width:3;filter:drop-shadow(0 0 4px rgba(34,197,94,.7))}
.grz .cstep{border:1px solid var(--line);border-radius:10px;margin-bottom:6px}
.tag{font-size:9px;padding:1px 6px;border-radius:999px;margin-left:4px;vertical-align:middle}
.tag.lam{background:#14532d;color:#86efac}.tag.cp{background:#1e293b;color:#94a3b8}
.agrp{border:1px solid var(--line);border-radius:14px;background:var(--card);overflow:hidden}
.agrp.alt{border-style:dashed}
.agh{display:flex;align-items:center;gap:10px;padding:10px 12px;cursor:pointer}
.agh>span:first-child{font-size:20px}
.agh div{flex:1}.agh b{display:block;font-size:14px}.agh em{font-style:normal;font-size:11px;color:var(--mut)}
.agh i{font-style:normal;font-size:11px;color:var(--mut)}
.chev{color:var(--mut);font-size:12px}
.agb{padding:0 10px 10px;display:flex;flex-direction:column;gap:6px}
.arow{border:1px solid var(--line);border-radius:12px;background:var(--card2);padding:6px 8px;opacity:.75}
.arow.on{opacity:1;border-color:#155e75}
.arow1{display:flex;align-items:center;gap:8px}
.arow1 .aname{flex:1;min-width:0;display:block}
.arow1 .aname b{display:block;font-size:13px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.arow1 .aname em{font-style:normal;font-size:11px;color:var(--mut)}
.arow.on .sw{background:#14b8a6}.arow.on .sw i{left:21px;background:#fff}
.aext{margin-top:6px}
.counters.c3{grid-template-columns:repeat(3,1fr)}
.act.wide{flex:none;width:100%}
.agrp.unter{border-style:dashed}
.agrp.unter .agrp{background:var(--card2)}
.aext .cstep{border:1px solid var(--line);border-radius:10px;margin-bottom:4px}
.hkpts{display:grid;grid-template-columns:repeat(3,1fr);gap:6px;margin-top:8px}
.hkpts .cstep{border:1px solid var(--line);border-radius:10px;padding:5px 6px;gap:4px;flex-wrap:wrap;justify-content:center}
.hkpts .cstep span{margin:0;width:100%;text-align:center}
.hkpts .cstep b{min-width:40px;font-size:15px}
.hkpts .cstep button{width:26px;height:26px;font-size:15px}
.ibtn{display:inline-flex;align-items:center;justify-content:center;width:18px;height:18px;border-radius:50%;border:1.5px solid #64748b;color:#94a3b8;font:italic 700 11px Georgia,serif;cursor:pointer;margin:0 4px;vertical-align:middle}
.ibtn.on{border-color:#5eead4;color:#5eead4}
.itxt{margin:6px 0;padding:8px 10px;border-radius:10px;background:#0b1220;border:1px solid #155e75;font-size:12px;line-height:1.45;color:#cbd5e1;font-style:normal}
.spblk{padding:8px 10px;border-radius:12px;background:var(--card2);border:1px solid var(--line);margin-bottom:8px}
.spblk.run{border-color:#10b981}
.sph{display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;font-size:13px;margin-bottom:6px}
.sph .itxt{width:100%}
.spbar{position:relative;height:10px;border-radius:6px;background:#1e293b;margin:8px 0 6px}
.spbar .zone{position:absolute;top:0;bottom:0;background:linear-gradient(90deg,rgba(59,130,246,.35),rgba(239,68,68,.35))}
.spbar .mk{position:absolute;top:-3px;bottom:-3px;width:3px;border-radius:2px;transform:translateX(-50%)}
.spbar .mk.ein{background:#3b82f6}.spbar .mk.aus{background:#ef4444}
.spbar .dot{position:absolute;top:50%;width:14px;height:14px;border-radius:50%;background:#f8fafc;border:3px solid #0b1220;transform:translate(-50%,-50%);box-shadow:0 0 8px #fff}
.spvals{display:flex;justify-content:space-between;font-size:12px}
.cblue{color:#60a5fa}.cred{color:#f87171}
.spstat{font-size:11px;color:var(--mut);margin-top:3px}
.unitbox{flex:none;aspect-ratio:138/200}
.atrow{display:flex;justify-content:center;gap:10px;margin:8px 0}
.atrow div{text-align:center;padding:4px 16px;border-radius:12px;background:rgba(13,22,41,.8);border:1px solid var(--line)}
.atrow span{display:block;font-size:11px;color:var(--mut)}.atrow b{font-size:20px}
.bgrid{display:grid;grid-template-columns:repeat(3,1fr);gap:6px}
.bcol{display:flex;flex-direction:column;gap:6px;min-width:0}
.bd.glow{border-color:#facc15;background:rgba(250,204,21,.12);box-shadow:0 0 14px rgba(250,204,21,.45)}
.bd.glow b{color:#fde047;text-shadow:0 0 10px rgba(250,204,21,.6)}
.bd .sub.on{color:#fde047}
.bgrid{grid-template-rows:repeat(4,1fr);grid-auto-flow:column}
.bgrid>.bd{justify-content:center;min-width:0;overflow:hidden}
.bgrid>.bd b{line-height:1.25;white-space:nowrap}
.bgrid>.bd span{white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.pvi{font-style:normal;font-size:1em;line-height:1;display:inline-block;vertical-align:-1px}
.leftcol{flex:none;width:124px;display:flex;flex-direction:column;align-items:center;justify-content:space-between;gap:8px}
.leftcol .unitbox{width:100%}
.pvbadge{width:100%;display:flex;align-items:center;gap:8px;padding:6px 8px;border-radius:12px;background:rgba(13,22,41,.8);border:1px solid var(--line)}
.pvbadge i{font-style:normal;font-size:22px;display:inline-block}
.pvbadge span{display:block;font-size:10px;color:var(--mut)}.pvbadge b{font-size:16px}
.pvbadge.on{border-color:#facc15;background:linear-gradient(135deg,rgba(250,204,21,.22),rgba(13,22,41,.8));box-shadow:0 0 14px rgba(250,204,21,.35)}
.pvbadge.on b{color:#fde047}
.spin8{animation:spin 8s linear infinite}
.batt{width:100%;text-align:center}
.batt svg{width:100%;height:auto;display:block}
.batt span{font-size:11px;color:var(--mut)}
.batt.charge span{color:#4ade80}.batt.discharge span{color:#fbbf24}
.btxt{fill:#f8fafc;font-size:14px;font-weight:800;paint-order:stroke;stroke:#0b1220;stroke-width:3px}
.pvi.sun{animation:spin 8s linear infinite;filter:drop-shadow(0 0 10px rgba(250,204,21,.8))}
.pvi.cloud{animation:drift 6s ease-in-out infinite;opacity:.85}
.pvi.moon{filter:drop-shadow(0 0 8px rgba(191,219,254,.6));animation:pulse 4s ease-in-out infinite}
@keyframes drift{0%,100%{transform:translateX(-4px)}50%{transform:translateX(4px)}}
.bd.night{}
.vlred{color:#f87171}
.hhead .badge{align-self:center}
.herotxt{flex:1;min-width:0;display:flex;flex-direction:column;justify-content:center}
.hhead{display:flex;align-items:baseline;gap:10px;flex-wrap:wrap}
.hhead .opline{font-size:24px}
.plbl{fill:#cbd5e1;font-size:9px;font-weight:700}
.ztxt{fill:#94a3b8;font-size:10px;font-weight:700}
.ztxt.run{fill:#34d399}.ztxt.pause{fill:#fbbf24}
.bdata{display:grid;grid-template-columns:repeat(auto-fit,minmax(92px,1fr));gap:6px;margin-top:8px}
.bd{background:rgba(13,22,41,.8);border:1px solid var(--line);border-radius:10px;padding:5px 9px;display:flex;flex-direction:column;gap:2px}
.bd span{font-size:11px;color:var(--mut)}.bd b{font-size:17px;font-weight:700;white-space:nowrap}.bd b em{font-style:normal}
.bd .sub{font-style:normal;font-size:10px;color:var(--mut)}
.ctrls{display:grid;grid-template-columns:repeat(auto-fit,minmax(230px,1fr));gap:12px}
.ctrl{background:#1a222d;border:1px solid #2a3a50;border-radius:12px;overflow:hidden;transition:transform .15s;display:flex;flex-direction:column}
.cimg{flex:1;display:flex;align-items:center;background:#242b34}
.cimg svg{flex:1}
.cstep{display:flex;align-items:center;gap:8px;padding:6px 10px;background:#232b36;border-top:1px solid #2a3a50}
.cstep span{font-size:12px;color:var(--mut);margin-right:auto}
.cstep button{width:30px;height:30px;border-radius:50%;border:1px solid #27406b;background:#183057;color:var(--txt);font-size:18px;cursor:pointer}
.cstep b{font-size:17px;min-width:50px;text-align:center}
.ctrl:hover{transform:translateY(-2px)}
.cbar{display:flex;justify-content:space-between;align-items:center;padding:5px 8px;background:linear-gradient(180deg,#2f7196,#1d4f6e)}
.cval{font-size:13px;font-weight:700;padding:1px 8px;border:1px solid #cbd5e1;border-radius:3px;background:#0f2233}
.cstate{font-size:11px;padding:2px 8px;border-radius:999px;background:rgba(15,23,42,.6);color:#cbd5e1}
.cstate.on{background:#14532d;color:#86efac}
.ctrl svg{display:block;width:100%;height:auto;max-height:190px;background:#242b34}
.cfoot{text-align:center;font-size:13px;padding:6px;background:#2b3440;color:#e5e7eb}
.vbox{fill:#2f3640;stroke:#9ca3af;stroke-width:1}
.vtxt{fill:#f1f5f9;font-size:14px;font-weight:700;font-family:ui-monospace,Menlo,Consolas,monospace}
.pr{fill:none;stroke:#ef4444;stroke-width:3}.pb{fill:none;stroke:#3b82f6;stroke-width:3}
.modal{position:fixed;inset:0;z-index:999;background:rgba(2,6,15,.72);backdrop-filter:blur(4px);display:flex;align-items:center;justify-content:center;padding:16px;cursor:default}
.mbox{width:min(900px,100%);max-height:88vh;overflow:auto;background:linear-gradient(180deg,#0f1b33,#0b1324);border:1px solid var(--line);border-radius:20px;padding:14px;display:flex;flex-direction:column;gap:12px;cursor:default}
.mhead{display:flex;justify-content:space-between;align-items:center;font-size:16px}
.mx{width:34px;height:34px;border-radius:50%;display:flex;align-items:center;justify-content:center;background:#1a2640;border:1px solid var(--line);cursor:pointer}
@media (max-width:480px){.leftcol{width:78px}.pvbadge{flex-direction:column;gap:2px;padding:4px;text-align:center}.pvbadge b{font-size:13px}.bd b{font-size:15px}.bd span{font-size:10px}.hhead .opline{font-size:19px}.atrow b{font-size:16px}.atrow div{padding:3px 10px}.hero{gap:8px;padding:10px}.counters{grid-template-columns:repeat(2,1fr)}.bd{padding:4px 7px}}
`;

// Home Assistant loads this file before its own code. In browsers without
// scoped custom element registries (Firefox) it then replaces
// window.customElements with a polyfill that does not know elements defined
// before, and the card shows "Custom element doesn't exist". So define it again
// in whatever registry is current, until Home Assistant itself is up.
function lccDefine(name, cls) {
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

lccDefine("lambda-cockpit-card", LambdaCockpitCard);
window.customCards = window.customCards || [];
if (!window.customCards.find((c) => c.type === "lambda-cockpit-card")) {
  window.customCards.push({
    type: "lambda-cockpit-card",
    name: "Lambda Cockpit",
    description: "Overview of a Lambda heat pump (lambda_heat_pumps integration)",
  });
}
console.info(`%c LAMBDA-COCKPIT %c v${LCC_VERSION} `, "background:#14b8a6;color:#fff;border-radius:3px 0 0 3px", "background:#0f172a;color:#5eead4;border-radius:0 3px 3px 0");
