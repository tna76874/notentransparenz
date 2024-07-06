#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Notenberechnung
"""
import os
import numpy as np
from datetime import datetime
import copy
import matplotlib.pyplot as plt

class Note:
    def __init__(self, **kwargs):
        self._keys = ['m_s1', 'm_s', 'm_m', 'gesamtnote', 'datum']
        self.m_s1, self.m_s, self.m_m, self.gesamtnote, self.datum = (kwargs.get(key, None) for key in self._keys)

    def _print(self):
        return f'm_s1={self.m_s1}, m_s={self.m_s}, m_m={self.m_m}, gesamtnote={self.gesamtnote}, datum={self.datum.strftime("%d.%m.%Y")}'

    def update(self, **kwargs):
        self.m_s1, self.m_s, self.m_m, self.gesamtnote, self.date = (kwargs.get(key, getattr(self, key)) for key in self._keys)

    def __str__(self):
        return self._print()

    def __repr__(self):
        return self._print()

class Notenberechnung:
    def __init__(self, w_s0 = 1, w_sm = 3, system = 'N', schranke = 0.25, SJ=None, v_enabled = True):        
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
        self.sj_start, self.sj_ende = self._set_zeitraum(SJ=SJ)
        self._v_enabled = v_enabled
        
    def _set_zeitraum(self, SJ=None):
        if SJ!=None:
            sj_start = datetime(int(SJ), 9, 1)
            sj_ende = datetime(int(SJ)+1, 7, 31)
            return sj_start, sj_ende
            
        heutiges_datum = datetime.now()
        stichtag_start = datetime(heutiges_datum.year, 7, 31)
        stichtag_ende = datetime(heutiges_datum.year, 9, 1)
        if (stichtag_start <= heutiges_datum < stichtag_ende) or (heutiges_datum >= stichtag_ende):
            sj_start = datetime(heutiges_datum.year, 9, 1)
            sj_ende = datetime(heutiges_datum.year+1, 7, 31)
        else:
            sj_start = datetime(heutiges_datum.year-1, 9, 1)
            sj_ende = datetime(heutiges_datum.year, 7, 31)
        return sj_start, sj_ende
        
    def _sort_grade_after_date(self):
        self.noten.sort(key=lambda x: x['datum'])

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
                'status': kwargs.get('status', '---'),
                'datum': self.parse_date(kwargs.get('date')),
            }
            if kwargs.get('art') in ['m', 'GFS']:
                note_dict['status'] = '---'
            self.noten.append(note_dict)
            self._sort_grade_after_date()
        else:
            raise ValueError(f'Fehlende Informationen. Bitte geben Sie {" und ".join(mandatory_keys)} an.')

    def mittelwert(self, noten):
        noten_werte = np.array([note.get('note') for note in noten if isinstance(note.get('note'), (int, float))])
        if len(noten_werte)==0:
            return None
        return np.mean(noten_werte)

    def berechne_gesamtnote(self):
        result = Note(datum=self.noten[-1].get('datum'))
        verbesserung_enabled = any(note['status'] != '---' for note in self.noten) and self._v_enabled
        
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

        # Randfall: nur mündliche Noten
        if (n_KA + n_KT==0) and n_m>0:
            result.update( gesamtnote=m_m, m_m=m_m )
            return result
        # Randfall: keine Noten
        elif (n_KA + n_KT + n_m == 0):
            return None
        
        # Berechnung der Mittelwerte von KT und KA
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
        
        if (not verbesserung_enabled) or (n_v_g == 0):
            w_v4 = 0
            w_v3 = 0
        else:
            w_v4 = (n_v_1 * w_v1 + n_v_o * m_s1 + n_v_2 * w_v2)/n_v_g
        
        # Berechnung der schriftlichen Note
        m_s = (n_KA * m_KA + w_s * m_KT + w_v3 * w_v4 ) / (n_KA + w_s + w_v3)

        # Berechnung der Gesamtnote
        gesamtnote = (self.w_sm * m_s + m_m) / (self.w_sm + w_m)
                
        result.update(m_s1=m_s1, m_s=m_s, gesamtnote=gesamtnote, m_m = self.mittelwert(noten_muendlich))

        return result
    
    def time_series(self):
        kopie = copy.deepcopy(self)
        kopie.noten = []
        
        # Liste für Ergebnisse
        ergebnisse = []
        
        for note in self.noten:
            try:
                kopie.noten.append(note)
                kopie._sort_grade_after_date()
                ergebnis = kopie.berechne_gesamtnote()
                ergebnisse.append(ergebnis)
            except ValueError as e:
                print(f"Fehler beim Hinzufügen der Note: {str(e)}")
        
        return ergebnisse
    
    def plot_time_series(self, save=None, formats = ['jpg'], **kwargs):
        cvars =         {
                        'bbox_inches'   : 'tight',
                        'pad_inches'    : 0.05/2.54,
                        'dpi'           : 500,
                        }
        cvars.update(kwargs)
        
        result = self.time_series()
        
        # Extrahiere Daten für den Plot
        dates = [entry.datum for entry in result]
        gesamtnoten = [entry.gesamtnote for entry in result]
        schriftlich = [entry.m_s for entry in result]
        muendlich = [entry.m_m for entry in result]

        # Erstelle die Figure und Subplots
        fig, ax = plt.subplots(figsize=(10, 6))
        
        # Erstelle Plots
        ax.plot(dates, gesamtnoten, marker='o', linestyle='-', color='r', label='Gesamtnote')
        ax.plot(dates, schriftlich, marker='.', linestyle='--', color='b', label='schriftlich')
        ax.plot(dates, muendlich, marker='+', linestyle=':', color='g', label='mündlich')


        # Setze die Zeitachsen-Begrenzungen
        ax.set_xlim(self.sj_start, self.sj_ende)
        
        # Y-Achsen Skalierung basierend auf noten.system
        if self.system == 'N':
            ax.set_ylim(1, 6)
            ax.invert_yaxis()
        elif self.system == 'NP':
            ax.set_ylim(0, 15)
        
        # Datumsformatierung der x-Achse
        fig.autofmt_xdate()
        
        # Achsenbeschriftungen und Titel
        ax.set_xlabel('Datum')
        ax.set_ylabel('Gesamtnote')
        ax.set_title(f'Entwicklung der Leistungen in dem Schuljahr {self.sj_start.year}/{self.sj_ende.year}')
        
        # Legende
        ax.legend()
        
        # Zeige den Plot an
        ax.grid(True)
        fig.tight_layout()

        # Speichern der Figur, falls save angegeben ist
        if save is not None:
            # Sicherstellen, dass der Ordner existiert
            save = os.path.abspath(save)
            os.makedirs(os.path.dirname(save), exist_ok=True)
            # Speichern der Figur
            for exp_format in list(set(['pdf','svg','jpg']).intersection(set(formats))):
                cvars['format'] = exp_format
                fig.savefig(save+'.'+exp_format, **cvars)
        else:
            # Anzeigen der Figur
            plt.show()

if __name__ == "__main__":
    # Beispiel
    self = Notenberechnung(w_s0=1, w_sm=3, system = 'N', v_enabled=True)
    self.note_hinzufuegen(art='KA', date = '2024-04-10', note=3, status='fertig')
    self.note_hinzufuegen(art='KA', date = '2024-04-15', note=2.5, status='fertig')
    self.note_hinzufuegen(art='KA', date = '2024-03-01', note=4, status='fertig')
    self.note_hinzufuegen(art='KA', date = '2024-03-15', note=5, status='fertig')
    self.note_hinzufuegen(art='KT', date = '2024-02-01', note=4)
    self.note_hinzufuegen(art='KT', date = '2024-01-01', note=2.75, status='fertig')
    self.note_hinzufuegen(art='m', date = '2023-09-01', note=3.0)
    self.note_hinzufuegen(art='m', date = '2023-10-01', note=3.25)
    self.note_hinzufuegen(art='m', date = '2023-11-01', note=3.5)
    
    gesamtnote = self.berechne_gesamtnote()
    print(gesamtnote)
    self.plot_time_series()
