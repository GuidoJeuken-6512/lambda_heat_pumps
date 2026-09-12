---
title: "Nebenverbraucher (Lüfter, Pumpe, Standby) schätzen"
---

# Nebenverbraucher (Lüfter, Pumpe, Standby) schätzen

*Zuletzt geändert am 12.09.2026*

Die Lambda hat kein Modbus-Register für den Stromverbrauch einzelner
Nebenkomponenten – insbesondere nicht für den **Ventilator (Lüfter)** des
Energiequellenmoduls. Nur der **Verdichter** hat einen eigenen
Energiezähler (`compressor_power_consumption_accumulated`). Dieser Artikel
zeigt, wie man den restlichen Stromverbrauch trotzdem sichtbar machen kann –
und wo die Grenzen einer Schätzung liegen.

Hintergrund: [Issue #86](https://github.com/GuidoJeuken-6512/lambda_heat_pumps/issues/86).

> ⚠️ **Alle Prozentwerte in diesem Artikel stammen von genau einer
> Installation und sind nicht übertragbar.** Diese Anlage macht aktuell
> ausschließlich Warmwasser für eine Person, ein Mal täglich – kein
> Heizbetrieb. Das erklärt einen erheblichen Teil der weiter unten
> gezeigten Abweichungen vom Mittel. Eine andere Installation (andere
> Personenzahl, Heizbetrieb, Klimazone, Gebäudedämmung, PV-Nutzung, ggf.
> Heizstab) wird andere, unter Umständen sehr andere Werte haben. Die
> Zahlen unten dienen ausschließlich dazu, die **Methode** zu zeigen –
> nicht dazu, sie unverändert zu übernehmen.

---

## Best Practice: ein Zwischenzähler vor der Lambda

Die einzige Möglichkeit, den **tatsächlichen** Gesamtverbrauch der Lambda zu
messen, ist ein dedizierter Stromzähler in der Zuleitung – z. B. ein
Shelly 3EM (oder Pro 3EM), der ausschließlich den Stromkreis der
Wärmepumpe misst (nicht den ganzen Hausanschluss). Dieser Zähler erfasst
**alles**, was die Lambda verbraucht: Verdichter, Lüfter, Umwälzpumpe(n),
Regler-Elektronik/Standby und ggf. den elektrischen Heizstab.

Mit einem solchen Zwischenzähler lässt sich der Nebenverbrauch **exakt**
berechnen – keine Schätzung nötig:

```yaml
# configuration.yaml (Ausschnitt)
template:
  - sensor:
      - name: "Lambda Nebenverbraucher Energie (exakt)"
        unique_id: lambda_nebenverbraucher_energie_exakt
        unit_of_measurement: "kWh"
        device_class: energy
        state_class: total_increasing
        state: >
          {% set gesamt = states('sensor.MEIN_ZWISCHENZAEHLER_ENERGIE') | float(0) %}
          {% set verdichter = states('sensor.eu08l_hp1_compressor_power_consumption_accumulated') | float(0) / 1000 %}
          {{ (gesamt - verdichter) | round(2) }}
```

`sensor.MEIN_ZWISCHENZAEHLER_ENERGIE` durch den eigenen Energiesensor des
Zwischenzählers ersetzen (kWh, `state_class: total_increasing`). Da beide
Zähler nie exakt zum gleichen Zeitpunkt starten oder zurückgesetzt werden,
kann der berechnete Wert kurzzeitig leicht schwanken – über einen Monat
oder ein Jahr gemittelt ist er aber belastbar. **Das ist der einzige Weg
in diesem Artikel, der eine echte, für die eigene Anlage gültige Zahl
liefert** – alles Weitere unten ist Näherung.

### Den Zwischenzähler direkt in die Integration einbinden

Statt (oder zusätzlich zu) dem Template-Sensor oben lässt sich der
Zwischenzähler auch **nativ** in die Lambda-Integration einhängen: Die
Energieverbrauchs-Sensoren (`heating_energy_total`, `hot_water_energy_total`,
`cooling_energy_total`, `defrost_energy_total`, `stby_energy_total`, jeweils
auch täglich/monatlich/jährlich) lesen normalerweise den internen
Verdichter-Zähler, lassen sich aber pro Wärmepumpe auf einen **externen**
Quellsensor umstellen – z. B. genau den Shelly-Zwischenzähler:

```yaml
# lambda_wp_config.yaml (Ausschnitt)
energy_consumption_sensors:
  hp1:
    sensor_entity_id: "sensor.MEIN_ZWISCHENZAEHLER_ENERGIE"
```

Die Integration erkennt die Einheit des externen Sensors automatisch
(Wh/kWh/MWh) und ordnet die Deltas per Flankenerkennung weiterhin korrekt
der jeweiligen Betriebsart zu. Der Unterschied zum Template-Sensor oben:
Die eingebauten `..._energy_*`-Sensoren zeigen dann direkt den **gesamten**
Stromverbrauch der Lambda (Verdichter + Lüfter + Pumpe + Standby) je
Betriebsart – ganz ohne eigene Vorlage. Ausführlich beschrieben unter
[Energie- und Wärmeverbrauchsberechnung → Externe Sensoren konfigurieren](../Anwender/Energieverbrauchsberechnung.md#externe-sensoren-konfigurieren).

Für die Nebenverbraucher-Betrachtung in diesem Artikel bleibt der interne
`compressor_power_consumption_accumulated`-Sensor davon unberührt (er
existiert unabhängig weiter) – erst die **Differenz** aus externem
Zwischenzähler und diesem internen Sensor ergibt den Nebenverbrauch.

---

## Was ich aus echten Daten gelernt habe – und wie unrepräsentativ sie sind

Für [Issue #86](https://github.com/GuidoJeuken-6512/lambda_heat_pumps/issues/86)
habe ich genau diesen Vergleich auf einer Installation nachvollzogen, die
zufällig einen dedizierten Shelly 3EM vor der Lambda hat. Über die
Home-Assistant-Statistik-API (`ha_get_statistics`, Aggregation pro Monat)
ließen sich rund **23 Monate** Verlauf auswerten – das ist die **komplette
bisherige Historie** dieser Installation: sowohl der Zwischenzähler als
auch der Verdichter-Energiezähler der Integration beginnen erst im
Spätsommer/Herbst 2024 (Inbetriebnahme) – ein drittes Jahr existiert
schlicht nicht. Beide Sensoren liefern `state_class: total_increasing`,
sodass sich pro Kalendermonat einfach die jeweilige Differenz (`change`)
bilden lässt:

| Nebenverbraucher-Anteil am Gesamtverbrauch | Monate |
|---|---|
| ~15–20 % | Dezember, Januar, Februar (volle Heizlast) |
| ~21–29 % | März, April, Oktober, November (Übergangszeit) |
| ~31–52 % | Mai–September (kaum Heizbedarf, nur Warmwasser) |

Der Anteil schwankt also **um mehr als das Dreifache** übers Jahr – logisch,
denn Umwälzpumpe, Regler und Standby-Elektronik ziehen eine fast konstante
Grundlast, die im Sommer (wenig Verdichterlaufzeit) einen viel größeren
Anteil am (kleinen) Gesamtverbrauch ausmacht als im Winter.

Über zwei unabhängige, vollständige 12-Monats-Fenster (Okt.–Sep.) blieb der
**Jahres**-Anteil dagegen deutlich stabiler, bei rund **21–26 %** – aber
auch das war die Zeit, bevor auf dieser Anlage auf reinen
Warmwasserbetrieb für eine Person umgestellt wurde. **Selbst auf ein und
derselben Installation** verschiebt sich der Anteil also stark, sobald
sich die Nutzung ändert (hier: kein Heizbetrieb mehr, nur noch 1×
täglich Warmwasser für eine Person) – ein weiterer Beleg dafür, dass es
sich um eine Momentaufnahme handelt, nicht um eine feste Kenngröße.

Zusätzlich: Diese Zahl ist *nicht* direkt mit einer reinen
Lüfter-Schätzung vergleichbar (wie sie im Issue ursprünglich vorgeschlagen
wurde) – sie enthält zusätzlich Umwälzpumpe und Standby-Elektronik. Der
Lüfter allein macht davon nur einen Teil aus.

---

## Warum das kein Sensor der Integration wird

Ich nehme diese Schätzung **bewusst nicht** als eingebauten Sensor auf:

- Es gibt kein Register, das den Lüfter (oder die Pumpe, oder den Standby)
  isoliert misst – jede Herleitung bleibt eine Näherung ohne Messgrundlage.
- Die oben ermittelten Werte stammen von **einer** Installation mit ihrem
  eigenen, aktuell sehr untypischen Nutzungsprofil (nur Warmwasser, eine
  Person, ein Mal täglich) – siehe Warnhinweis oben. Auf einer anderen
  Anlage, oder auf derselben Anlage zu einer anderen Zeit, können sie
  deutlich abweichen.
- Ein fest eingebauter Sensor würde eine Genauigkeit vortäuschen, die die
  zugrunde liegenden Daten nicht hergeben.

**Aus demselben Grund verzichte ich bewusst darauf, unten fertige
Zahlenwerte zum Copy-&-Paste anzubieten.** Die beiden folgenden Varianten
zeigen nur die **Methode** – die Platzhalter darin müssen durch eigene,
selbst gemessene Werte ersetzt werden. Wer keine eigenen Werte hat (also
keinen Zwischenzähler zumindest für eine Kalibrierungsphase betrieben
hat), sollte auf die Näherung ganz verzichten und stattdessen dauerhaft
einen echten Zwischenzähler nutzen (siehe oben).

---

## Variante A: Methode – monatliche Eigenkalibrierung

Idee: ein monatsabhängiger Faktor, multipliziert mit der tatsächlichen
Verdichterenergie des laufenden Monats. Voraussetzung ist, dass man
**selbst** für mindestens ein Jahr einen Zwischenzähler betrieben (oder
weiterhin in Betrieb) hat, um die zwölf Monatsfaktoren für die eigene
Anlage zu ermitteln – nach dem Rechenweg aus dem Abschnitt oben
(`(Zwischenzähler_Monat − Verdichter_Monat) / Zwischenzähler_Monat`).

```yaml
# configuration.yaml (Ausschnitt)
utility_meter:
  lambda_verdichter_energie_monatlich:
    source: sensor.eu08l_hp1_compressor_power_consumption_accumulated
    cycle: monthly

template:
  - sensor:
      - name: "Lambda Nebenverbraucher geschätzt (Monatsfaktor)"
        unique_id: lambda_nebenverbraucher_monatsfaktor
        unit_of_measurement: "kWh"
        device_class: energy
        state_class: total
        state: >
          {# NICHT meine Beispielwerte übernehmen - durch eigene, #}
          {# selbst gemessene Monatsfaktoren ersetzen! #}
          {% set faktor = {
               1: 0.00, 2: 0.00, 3: 0.00, 4: 0.00, 5: 0.00, 6: 0.00,
               7: 0.00, 8: 0.00, 9: 0.00, 10: 0.00, 11: 0.00, 12: 0.00
             } %}
          {% set f = faktor.get(now().month, 0.0) %}
          {% set verdichter_monat = states('sensor.lambda_verdichter_energie_monatlich') | float(0) / 1000 %}
          {{ (verdichter_monat * f / (1 - f)) | round(2) if f > 0 else 0 }}
```

Ohne eingetragene eigene Faktoren liefert der Sensor bewusst `0` – erst
mit echten, selbst gemessenen Werten wird er sinnvoll.

---

## Variante B: Methode – Jahresmittel-Eigenkalibrierung

Einfacher, dafür ungenauer: ein einziger fester Faktor auf die gesamte
Verdichterenergie, ohne saisonale Unterscheidung – ebenfalls erst
sinnvoll mit einem selbst ermittelten Wert. Als `input_number`-Helfer,
damit er sich ohne YAML-Änderung anpassen lässt (Muster wie bei der
[Heizkurve](../Entwickler/heizkurve.md)):

```yaml
# configuration.yaml (Ausschnitt)
template:
  - sensor:
      - name: "Lambda Nebenverbraucher gesamt geschätzt (Jahresmittel)"
        unique_id: lambda_nebenverbraucher_jahresmittel
        unit_of_measurement: "kWh"
        device_class: energy
        state_class: total
        state: >
          {% set f = states('input_number.lambda_nebenverbraucher_faktor') | float(0) %}
          {% set verdichter = states('sensor.eu08l_hp1_compressor_power_consumption_accumulated') | float(0) / 1000 %}
          {{ (verdichter * f / (1 - f)) | round(1) if f > 0 else 0 }}
```

`input_number.lambda_nebenverbraucher_faktor` als Helfer anlegen (Min 0,
Max 0.6, Schritt 0.01, **Standardwert 0** – bewusst kein Vorschlagswert).
Den eigenen Faktor mit `(Zwischenzähler_gesamt − Verdichter_gesamt) /
Zwischenzähler_gesamt` über mindestens ein volles Jahr ermitteln und erst
dann eintragen.

---

## Fazit

- **Mit** Zwischenzähler: exakte Rechnung (siehe oben), keine Annahmen nötig
  – das ist der einzig verlässliche Weg.
- **Ohne** eigene, selbst gemessene Werte: die beiden Vorlagen oben sind
  reine Methodik-Vorlagen ohne sinnvollen Standardwert – meine eigenen
  Zahlen sind zu installationsspezifisch (und aktuell zu untypisch), um
  sie an andere weiterzugeben.
- Die beiden dafür genutzten Sensoren der Integration:
  `compressor_power_consumption_accumulated` (Verdichter-Energie) und,
  für die momentane Auslastung, `compressor_unit_rating` (EQM, %) – siehe
  [Sensoren-Übersicht](../Anwender/sensoren-uebersicht.md).
