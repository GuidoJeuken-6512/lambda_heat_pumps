---
title: "Modbus-Serialisierung - Technische Dokumentation"
---

# Modbus-Serialisierung - Technische Dokumentation

*Zuletzt geändert am 06.09.2026*

**Stand:** Release 3.5.3 (Rewrite auf [`modbus-connection`](https://github.com/home-assistant-libs/modbus-connection)/`tmodbus`, Branch `3.5`; Hintergrund zum Rewrite: [Issue #99](https://github.com/GuidoJeuken-6512/lambda_heat_pumps/issues/99))

Diese Dokumentation beschreibt zwei Modbus-Fehlerklassen, die der Rewrite
eingeführt hatte: Race Conditions/Transaction-ID-Mismatches bei gleichzeitigen
Requests (behoben in 3.5.2, unten) und den falschen Funktionscode bei
Schreibvorgängen (behoben in 3.5.3, [siehe unten](#fc16-statt-fc06-bei-schreibvorgängen)).

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

## Zusammenfassung (Pacing)

1. ✅ `modbus-connection`s Pacer serialisiert Reads und Writes nur, wenn ein
   Zeitabstand konfiguriert ist — der Default (`0.0`) tut das **nicht**.
2. ✅ Die Integration setzt seit `3.5.2` ein `message_spacing` von 50 ms bei
   Verbindungsaufbau, damit der Pacer tatsächlich sperrt.
3. ⚠️ Wer `ModbusConnection` an anderer Stelle neu instanziiert (z. B. für ein
   Diagnose-Werkzeug), muss dasselbe tun — sonst ist die neue Verbindung
   wieder unserialisiert.

## FC16 statt FC06 bei Schreibvorgängen

### Der Fehler: falscher Funktionscode

Bis einschließlich 3.5.2 schrieb jedes einzelne, schreibbare Register über
`ModbusUnit.write_register()` — **Function Code 0x06 (Write Single
Register)**. Lambdas eigene Modbus-Dokumentation ist an dieser Stelle
eindeutig:

> Alle Schreiboperationen müssen mit dem Funktionscode 0x10 (Dezimal 16)
> „write multiple registers" durchgeführt werden, auch wenn nur ein einzelnes
> Register beschrieben wird.

FC06 wird von der Lambda also gar nicht implementiert — sie beantwortet es mit
Exception Code 0x01 (Illegal Function). Live gegen echte Hardware (Firmware
`V0.0.8-3K`) reproduzierbar, alle ~9 Sekunden:

```
Could not send the room temperature to circuit 1: write_register(5004, 243): Modbus Exception 0x01 for function code 0x06
```

Betroffen war jedes schreibbare Feld im Registermodell: die
Raumthermostat-Steuerung (`room_device_temperature`, Register 5004), der
PV-Überschuss-Export, sämtliche Warmwasser-/Heizkreis-/Kühlkreis-Sollwerte,
der Vorlauf-Offset sowie der generische `write_modbus_register`-Service. Der
Vor-3.5-Code (`pymodbus`-basiert) hatte dieses Problem nie, weil er
ausnahmslos über `client.write_registers()` (FC16) schrieb, auch für ein
einzelnes Register.

### Die Behebung

`modbus-connection` sieht für genau diesen Fall ein Feld-Flag vor
(`model/_writing.py`, Version 4.10.0):

```python
words = field.encode(value, scale_exponent)
if field.force_fc16 or len(words) > 1:
    await unit.write_registers(address, words)
else:
    await unit.write_register(address, words[0])
```

Jedes `writable=True`-Feld in `lambda_modbus/` (`heating_circuit.py`,
`boiler.py`, `buffer.py`, `solar.py`, `heat_pump.py` inkl.
`HeatPumpCapacityLimits`) setzt seit 3.5.3 zusätzlich `force_fc16=True`. Die
zwei Stellen mit direktem Schreibzugriff unter Umgehung des Feldmodells
(`services.py`: PV-Überschuss-Writer und der generische
Register-Schreib-Service) rufen jetzt `unit.write_registers(address,
[value])` statt `unit.write_register(address, value)` auf.

Ein `PackedBitsField` (gepacktes Bit-Register mit Read-Modify-Write) existiert
im aktuellen Modell nicht — der eine FC06-Sonderpfad in `write_register_field()`,
der `force_fc16` ignoriert (Read-Modify-Write eines gepackten Registers über
FC06), kommt hier also nie zum Tragen.

### Verifikation

Ohne HA-Fixtures, direkt gegen `modbus_connection.mock.MockModbusUnit`
(`WriteEvent.function_code`):

```
address=5004 function_code=16 values=[242]   # room_device_temperature
address=2050 function_code=16 values=[550]   # boiler target_high_temperature
```

Live gegen echte Hardware (Firmware `V0.0.8-3K`): Der
Raumtemperatur-Schreibzugriff (Register 5004) sowie eine
Warmwasser-Sollwertänderung über `climate.set_temperature`
(`climate.<prefix>_boil1_hot_water`) kamen nach dem Fix korrekt an — der
Controller liest den neu gesetzten Sollwert im nächsten Poll unverändert
zurück, statt weiter den alten Wert zu melden.

## Zusammenfassung (Funktionscode)

1. ✅ Lambda implementiert FC06 (Write Single Register) nicht — nur FC10/0x10
   (Write Multiple Registers), auch für ein einzelnes Register.
2. ✅ Jedes `writable=True`-Feld setzt seit `3.5.3` `force_fc16=True`; die
   zwei direkten `write_register()`-Aufrufe in `services.py` wurden auf
   `write_registers()` umgestellt.
3. ⚠️ Ein neues schreibbares Feld im Registermodell braucht `force_fc16=True`
   — ohne das schreibt es standardmäßig über FC06 und scheitert auf echter
   Hardware.
