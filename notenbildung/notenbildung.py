#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Notenberechnung
"""
import numpy as np
from datetime import datetime

class Note:
    def __init__(self, **kwargs):
        self.m_s1, self.m_s, self.m_m, self.gesamtnote = (kwargs.get(key, None) for key in ['m_s1', 'm_s', 'm_m', 'gesamtnote'])

    def _print(self):
        return f'm_s1={self.m_s1}, m_s={self.m_s}, m_m={self.m_m}, gesamtnote={self.gesamtnote}'

    def update(self, **kwargs):
        self.m_s1, self.m_s, self.m_m, self.gesamtnote = (kwargs.get(key, getattr(self, key)) for key in ['m_s1', 'm_s', 'm_m', 'gesamtnote'])

    def __str__(self):
        return self._print()

    def __repr__(self):
        return self._print()

class Notenberechnung:
    def __init__(self, w_s0 = 1, w_sm = 3, system = 'N', schranke = 0.25):
        if system not in ['N', 'NP']:
            raise ValueError("Das System muss entweder 'N' oder 'NP' sein.")
        if not 0 <= schranke < 0.5:
            raise ValueError("Die Schranke muss im Bereich  [0; 0.5) liegen.")
        if not 0 <= float(w_s0) <= 2:
            raise ValueError("w_s0 muss in  [0; 2] liegen.")
        if not 1 <= float(w_sm) <= 4:
            raise ValueError("w_s0 muss in  [1; 4] liegen.")
        self.w_s0 = float(w_s0)
        self.w_sm = float(w_sm)
        self.schranke = schranke
        self.system = system
        self.noten = []

    def parse_date(self, date_str):
        if isinstance(date_str, datetime):
            return date_str
        try:
            return datetime.strptime(date_str, "%Y-%m-%d")
        except (ValueError, TypeError):
            raise ValueError("Ungültiges Datumsformat")

    def note_hinzufuegen(self, **kwargs):
        mandatory_keys = ['art', 'note', 'date']
        if all(key in kwargs for key in mandatory_keys):
            note_dict = {
                'art': kwargs.get('art'),
                'note': kwargs.get('note'),
                'status': kwargs.get('status'),
                'datum': self.parse_date(kwargs.get('date')),
            }
            if kwargs.get('art') in ['m', 'GFS']:
                note_dict['status'] = '---'
            self.noten.append(note_dict)
        else:
            raise ValueError(f'Fehlende Informationen. Bitte geben Sie {" und ".join(mandatory_keys)} an.')

    def mittelwert(self, noten):
        noten_werte = np.array([note.get('note') for note in noten if isinstance(note.get('note'), (int, float))])
        if len(noten_werte)==0:
            return None
        return np.mean(noten_werte)

    def berechne_gesamtnote(self):
        result = Note()
        
        # Filtern der Noten nach Art
        noten_ka = [note for note in self.noten if note.get('art') in ['KA', 'GFS']]
        noten_kt = [note for note in self.noten if note.get('art') in ['KT']]
        noten_muendlich = [note for note in self.noten if note.get('art') == 'm']
        
        # Zählen der verschiedenen Statusarten
        n_v_g = len([note.get('status') for note in self.noten if not note.get('status') == '---'])
        n_v_o = len([note.get('status') for note in self.noten if not note.get('status') in ['---', 'fehlt', 'fertig']])
        n_v_1 = len([note.get('status') for note in self.noten if note.get('status') == 'fehlt'])
        n_v_2 = len([note.get('status') for note in self.noten if note.get('status') == 'fertig'])

        # Ermitteln der Anzahl der verschiedenen Leistungsarten
        n_KA = len(noten_ka)
        n_KT = len(noten_kt)
        n_m = len(noten_muendlich)
        
        # Berechnung der Durchschnittsnote für jede Leistungsart
        m_KA = self.mittelwert(noten_ka) or 0
        m_KT = self.mittelwert(noten_kt) or 0
        m_m = self.mittelwert(noten_muendlich) or 0
        
        # Gewichtung für mündliche Noten
        w_m = 0 if n_m==0 else 1

        # Berechnung der Mittelwerte von KT und KA
        if n_KA + n_KT==0:
            return None
        w_s = 0 if n_KT == 0 else self.w_s0/2 if n_KT == 1 else self.w_s0
        m_s1 = (n_KA * m_KA + w_s * m_KT) / (n_KA + w_s)

        # Berechnung des Diskretisierungsfaktors
        w_d = abs(0.5 - (m_s1 % 1)) / 0.25
        
        # Berechnen der Gewichte je nach Notensystem
        if self.system=='N':
            w_v1 = 0 if w_d > 1 else np.ceil(m_s1) if w_d <= 1 else 0
            w_v2 = 0 if w_d > 1 else np.floor(m_s1) if w_d <= 1 else 0
        elif self.system=='NP':
            w_v1 = 0 if w_d > 1 else np.floor(m_s1) if w_d <= 1 else 0
            w_v2 = 0 if w_d > 1 else np.ceil(m_s1) if w_d <= 1 else 0
        w_v3 = 0 if w_d >= 1 else 10 if w_d < 1 else 0
        
        if n_v_g != 0:
            diskretisierung = (n_v_1 * w_v1 + n_v_o * m_s1 + n_v_2 * w_v2)/n_v_g
        else:
            diskretisierung = 0
        
        # Berechnung der schriftlichen Note
        m_s = (n_KA * m_KA + w_s * m_KT + w_v3 * diskretisierung ) / (n_KA + w_s + w_v3)

        # Berechnung der Gesamtnote
        gesamtnote = (self.w_sm * m_s + m_m) / (self.w_sm + w_m)
                
        result.update(m_s1=m_s1, m_s=m_s, gesamtnote=gesamtnote, m_m = m_m)

        return result

if __name__ == "__main__":
    # Beispiel
    
    self = Notenberechnung(w_s0=1, w_sm=3, system = 'N')
    self.note_hinzufuegen(art='KA', date = '2024-04-10', note=5, status='fertig')
    self.note_hinzufuegen(art='KA', date = '2024-04-15', note=6, status='fertig')
    self.note_hinzufuegen(art='KA', date = '2024-03-01', note=3, status='fertig')
    self.note_hinzufuegen(art='KA', date = '2024-03-15', note=5, status='fertig')
    self.note_hinzufuegen(art='KT', date = '2024-02-01', note=4, status='fertig')
    self.note_hinzufuegen(art='KT', date = '2024-01-01', note=2.75, status='fertig')
    self.note_hinzufuegen(art='m', date = '2023-09-01', note=3.0)
    self.note_hinzufuegen(art='m', date = '2023-10-01', note=3.25)
    self.note_hinzufuegen(art='m', date = '2023-11-01', note=3.5)
    
    gesamtnote = self.berechne_gesamtnote()
    print(gesamtnote)
