#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Notenberechnung
"""
import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))
from notenbildung.models import *

class NotenberechnungFTW(NotenberechnungGeneric):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def _calculate(self):       
        noten_ka = self._get_leistung_for_types(LeistungKA, LeistungGFS)
        noten_kt = self._get_leistung_for_types(LeistungKT, LeistungP)
        noten_muendlich = self._get_leistung_for_types(LeistungM)

        m_KA = self.mittelwert(noten_ka)
        m_KT = self.mittelwert(noten_kt)
        m_m = self.mittelwert(noten_muendlich)

        result = Note(datum=self.noten[-1].date, gesamtnote=1)
        
        return result

class LimitsTest(LimitsGeneric):
    _type = 'TestLimit'
    limits = LimitsGeneric.limits + [
        {
            'sum': [AttributM],
            'min': 1,
            'max': None,
        },
        {
            'sum': [LeistungKA],
            'min': 6,
            'max': 10,
        },
        {
            'sum': [AttributS],
            'min': 2,
            'max': 4,
        },
    ]

class FachTest(FachGeneric):
    name = 'TST'
    long = 'Testfach'
    limits = LimitsTest

meinfach = FachTest
note = NotenberechnungFTW(w_s0=1, w_sm=3, system = 'N', v_enabled=True, w_th = 0.4, fach=meinfach)
# note = NotenberechnungSimple(w_s0=1, w_sm=3, system = 'N', v_enabled=True, w_th = 0.4, fach=meinfach)
note.note_hinzufuegen(art='KA', date = '2024-04-10', note=3, status='fertig')
note.note_hinzufuegen(art='KA', date = '2024-04-15', note=2.5, status='fertig')
# Wenn die nächste Zeile einkommentiert wird, dann erscheint ein Fehler nach den obigen Limits
# note.note_hinzufuegen(art='KA', date = '2024-03-01', note=4, status='fertig')
note.note_hinzufuegen(art='P', date = '2024-03-15', note=5, status='fertig')
note.note_hinzufuegen(art='KT', date = '2024-02-01', note=4)
note.note_hinzufuegen(art='KT', date = '2024-01-01', note=2.75, status='fertig')
note.note_hinzufuegen(art='m', date = '2023-09-01', note=3.0)
note.note_hinzufuegen(art='m', date = '2023-10-01', note=3.25)
note.note_hinzufuegen(art='m', date = '2023-11-01', note=3.5)

gesamtnote = note.berechne_gesamtnote()
print(gesamtnote)

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
    
