#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Beispiel: Noten mit Lerngruppen
"""
from notenbildung.notenbildung import *

# es gibt die Fächer FachM(), FachPH() und FachINF()
# eine fachpraktische Leistung P wird als Kurztest gezählt, zählt jedoch nicht in die Anzahl der schriftlichen Leistungen mit hinein.

meinfach = FachM
note = Notenberechnung(w_s0=1, w_sm=3, system = 'N', v_enabled=True, w_th = 0.4, fach=meinfach)
note.note_hinzufuegen(art='KA', date = '2024-04-10', note=3, status='fertig')
note.note_hinzufuegen(art='KA', date = '2024-04-15', note=2.5, status='fertig')
note.note_hinzufuegen(art='KA', date = '2024-03-01', note=4, status='fertig')
note.note_hinzufuegen(art='P', date = '2024-03-15', note=5, status='fertig')
note.note_hinzufuegen(art='KT', date = '2024-02-01', note=4)
note.note_hinzufuegen(art='KT', date = '2024-01-01', note=2.75, status='fertig')
note.note_hinzufuegen(art='m', date = '2023-09-01', note=3.0)
note.note_hinzufuegen(art='m', date = '2023-10-01', note=3.25)
note.note_hinzufuegen(art='m', date = '2023-11-01', note=3.5)

schueler1 = SchuelerEntity(sid=1, vorname='Max', nachname='Mustermann')
schueler1.setze_note(note)

schueler2 = SchuelerEntity(sid='abc', vorname='Mini', nachname='Musterfrau')
schueler2.setze_note(note)

lerngruppe1 = LerngruppeEntity(stufe=7, fach=meinfach, zug='A')

lerngruppe1.update_sid(schueler1)
lerngruppe1.update_sid(schueler2)

lerngruppe1.plot_sid(1)
lerngruppe1.plot_sid('abc')

print(lerngruppe1.get_dataframe())
print(schueler1.get_dataframe())