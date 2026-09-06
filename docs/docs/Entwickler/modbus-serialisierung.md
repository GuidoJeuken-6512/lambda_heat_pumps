---
title: "Modbus-Serialisierung - Technische Dokumentation"
---

# Modbus-Serialisierung - Technische Dokumentation

*Zuletzt geändert am 06.09.2026*

Diese Dokumentation beschreibt, wie die Lambda Heat Pumps Integration (ab dem
Rewrite auf Basis von `modbus-connection`/`tmodbus`, Branch `3.5`) Race
Conditions und Transaction-ID-Mismatches bei gleichzeitigen Modbus-Requests
vermeidet — und einen Konfigurationsfehler, der genau das bis einschließlich
`3.4.1`/Version 3.5.1 **nicht** getan hat.

!!! info "Für die alte (2.8.x) Architektur"
    Diese Seite beschrieb bis Version 3.5.1 die Locking-Strategie der
    Vor-Rewrite-Integration (`modbus_utils.py`, zwei eigene `asyncio.Lock`s um
    einen `pymodbus`-Client). Diese Datei existiert seit dem Rewrite nicht mehr
    — die Modbus-Kommunikation läuft jetzt vollständig über die externe
    Bibliothek [`modbus-connection`](https://github.com/home-assistant-libs/modbus-connection)
    mit dem `tmodbus`-Backend. Die Seite ist unten für die neue Architektur
    neu geschrieben.

## Übersicht

`modbus-connection` serialisiert Requests nicht standardmäßig über ein
eigenes, immer aktives Lock in der Integration, sondern über einen **Pacer**,
der Teil jeder `ModbusConnection`-Instanz ist. Der Pacer serialisiert nur dann
wirklich, wenn ihm ein Zeitabstand (`message_spacing` bzw. `unit_spacing`
größer als 0) mitgegeben wird — ohne das ist er ein reiner Durchreicher ohne
Sperrwirkung.

## Der Fehler: Pacer-Lock war inaktiv

### Quellcode-Fund

In `modbus_connection/_pacing.py` (Version 4.10.0, wie in `requirements.txt`
gefordert) sieht `Pacer.paced()` so aus (gekürzt):

```python
class Pacer:
    def __init__(self, message_spacing: float = 0.0) -> None:
        self._message_spacing = message_spacing
        self._lock = asyncio.Lock()
        ...

    @asynccontextmanager
    async def paced(self, unit_id: int) -> AsyncIterator[None]:
        unit_spacing = self._unit_spacing.get(unit_id, 0.0)
        if not self._message_spacing and not unit_spacing:
            yield          # <-- kein Lock, kein Warten: einfach durchreichen
            return
        async with self._lock:
            ...
```

`BaseModbusConnection.__init__` (in `_client.py`) reicht `message_spacing`
unverändert an den `Pacer` durch, mit Default `0.0`:

```python
def __init__(
    self, params, *, timeout: float = 10,
    message_spacing: float = 0.0, connect_delay: float = 0.0,
) -> None:
    ...
    self._pacer = Pacer(message_spacing)
```

Die Integration hat die Verbindung bis Version 3.5.1 so aufgebaut:

```python
connection = ModbusConnection(
    ModbusTcpParams(host=entry.data[CONF_HOST], port=port)
)
```

— **ohne** `message_spacing` oder `unit_spacing` zu setzen. Damit griff der
`asyncio.Lock` des Pacers nie: `paced()` hat bei jedem Read/Write sofort
`yield` ausgeführt, ohne zu warten oder zu sperren.

### Warum das ein Problem ist

Der Poll-Loop des Coordinators (volle und schnelle Abfrage) und der
Schreib-Timer für PV-Überschuss-/Raumtemperatur-Vorgaben (`services.py`)
laufen mit unabhängigen Intervallen auf **derselben** `ModbusConnection`. Ohne
Sperre können beide gleichzeitig ein Modbus-Request/Response auf derselben
TCP-Verbindung anstoßen — exakt dieselbe Fehlerklasse wie das ursprünglich in
der Vor-Rewrite-Integration behobene [Issue #105](https://github.com/GuidoJeuken-6512/lambda_heat_pumps/issues/105)
(Transaction-ID-Desync: ein Schreibvorgang wird als erfolgreich geloggt, kommt
am Gerät aber sporadisch nie an).

Ob `tmodbus` selbst intern noch zusätzlich puffert oder in eine Warteschlange
stellt, war ohne Einsicht in dessen Quellcode nicht abschließend zu klären;
verlassen sollte man sich darauf nicht — der Pacer ist der einzige
Serialisierungs-Mechanismus, den `modbus-connection` öffentlich dokumentiert
und den diese Integration selbst kontrollieren kann.

## Die Behebung

`custom_components/lambda_heat_pumps/__init__.py` übergibt der
`ModbusConnection` jetzt explizit ein `message_spacing` von 50 ms
(`DEFAULT_MODBUS_MESSAGE_SPACING` in `const.py`):

```python
connection = ModbusConnection(
    ModbusTcpParams(host=entry.data[CONF_HOST], port=port),
    message_spacing=DEFAULT_MODBUS_MESSAGE_SPACING,
)
```

Damit nimmt `paced()` bei jedem Request den `asyncio.Lock`, wartet die
konfigurierte Mindestlücke ab und serialisiert so alle Reads und Writes auf
der Verbindung — Poll-Loop und Schreib-Timer können sich nicht mehr
überschneiden. 50 ms sind gegenüber den Mehrsekunden-Intervallen von Poll- und
Schreib-Timer nicht wahrnehmbar.

Ein Regressionstest (`tests/test_init.py::test_the_connection_paces_its_requests`)
stellt sicher, dass die Integration `ModbusConnection` nie wieder ohne ein
gesetztes `message_spacing` aufbaut.

### Config-Flow-Verbindung ausgenommen

Der einmalige Prüf-Read in `config_flow.py::async_can_connect()` (beim
Einrichten der Integration) läuft auf einer eigenen, kurzlebigen Verbindung
ohne parallelen Schreib- oder Poll-Vorgang — dort besteht die Race-Bedingung
nicht, weshalb dort bewusst kein `message_spacing` gesetzt wurde.

## Zusammenfassung

1. ✅ `modbus-connection`s Pacer serialisiert Reads und Writes nur, wenn ein
   Zeitabstand konfiguriert ist — der Default (`0.0`) tut das **nicht**.
2. ✅ Die Integration setzt seit `3.5.2` ein `message_spacing` von 50 ms bei
   Verbindungsaufbau, damit der Pacer tatsächlich sperrt.
3. ⚠️ Wer `ModbusConnection` an anderer Stelle neu instanziiert (z. B. für ein
   Diagnose-Werkzeug), muss dasselbe tun — sonst ist die neue Verbindung
   wieder unserialisiert.
