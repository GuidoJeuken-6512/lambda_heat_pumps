---
title: "PV Überschuss Steuerung"
---

# PV Überschuss Steuerung

Die Lambda kann ihre Leistung erhöhen, wenn PV-Überschuss vorliegt. 

Diese Integration unterstützt die Funktion, die Option muss in der Configuration der Lambda Wärmepumpen Integration aktiviert und konfiguriert werden. 
Weitere Informationen zur Konfiguration: [Optionen des Config Flow](optionen-config-flow.md)

Dazu schickt die Integration den PV-Überschuss an die Lambda Wärmepumpe, das Register 102 wird mit „W" PV Überschuss beschrieben.
Wird die Option aktvieuert, wird ein Sensor der Klasse „Power“ abgefragt, der den PV-Überschuss abbildet. 
Der Wert des Sensors kann in W oder kW sein, die Umrechnung wird automatisch vorgenommen. 

Die Lambda regelt dann ihre Leistung hoch, wenn viel PV Überschuss vorhanden ist. Die Art der Überschuss Steuerung muss zu der Konfiguration in der Lambda passen.

Sollte eure PV-Anlage negative Werte bei PV-Überschuss angeben, macht einen Template Sensor in Home Assistant, damit positive Werte an die Lambda übergeben werden.

Die Werte werden alle 9 sec an die Lambda gesendet. Wenn die Lambda keine Werte über einige Minuten empfängt, so erzeugt sie einen Fehler, daher die Option in der Lambda immer wieder deaktivieren, wenn sie nicht mehr eingesetzt wird.

<img src="../../assets/pv_surplus_de_1.png" alt="PV Überschuss Steuerung" style="width: 100%; height: auto; border-radius: 8px;">

In der Lambda müssen vorher folgende Einstellungen gesetzt sein, der PV-Überschuss ist dann auch in Oberfläche der Lambda sichtbar:

<img src="../../assets/pv_surplus_de_2.png" alt="PV Überschuss Steuerung Lambda" style="width: 100%; height: auto; border-radius: 8px;">
