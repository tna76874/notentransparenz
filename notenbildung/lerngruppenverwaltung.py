#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Generische Notenberechnung
"""
import os
import sys

import numpy as np
import pandas as pd
from datetime import datetime
import copy
import itertools
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import matplotlib.dates as mdates

sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))
from notenbildung.nvo import *
        
class Note:
    """
    Diese Klasse speichert die berechneten Schnitte inklusive einer Gesamtnote.
    """
    def __init__(self, system = 'N', **kwargs):
        if system not in ['N', 'NP']:
            raise ValueError("Das System muss entweder 'N' oder 'NP' sein.")
        else:
            self.system = system
        
        self._keys = ['m_s1', 'm_s', 'm_m', 'gesamtnote', 'datum']
        

        for key in self._keys:
            value = kwargs.get(key, None)
            if isinstance(value, (int, float)) or value==None:
                setattr(self, key, NoteEntity(value, system=self.system))
            else:
                setattr(self, key, value)
        
    def _print(self):
        return f'm_s1={self.m_s1}, m_s={self.m_s}, m_m={self.m_m}, gesamtnote={self.gesamtnote}, datum={self.datum.strftime("%d.%m.%Y")}'

    def update(self, **kwargs):
        for key, value in kwargs.items():
            if key in self._keys and isinstance(value, (int, float)):
                setattr(self, key, NoteEntity(value, system=self.system))
            else:
                setattr(self, key, value)

    def __str__(self):
        return self._print()

    def __repr__(self):
        return self._print()

class NotenberechnungGeneric:
    """
    Mit dieser Klasse werden Noten berechnet und auf Gültigkeit der Notenbildungsverordnung überprüft.
    """
    def __init__(self, w_sm = 3, w_th = 0.25, w_s0 = 1, n_KT_0 = 3, system = 'N', v_enabled = True, fach=None):
        self._typ = None
        self._fach = None
        if fach is not None:
            if not issubclass(fach, FachGeneric):
                raise ValueError("Der übergebene Typ muss von der Klasse FachGeneric sein.")
            else:
                self._fach = fach
        if system not in ['N', 'NP']:
            raise ValueError("Das System muss entweder 'N' oder 'NP' sein.")
        if not 0 <= float(w_th) <= 0.5:
            raise ValueError("Die Schranke w_th muss im Bereich  [0; 0.5] liegen.")
        if not 0 <= float(w_s0) <= 2:
            raise ValueError("w_s0 muss in  [0; 2] liegen.")
        if not 1 <= float(w_sm) <= 4:
            raise ValueError("w_s0 muss in  [1; 4] liegen.")
        if not 1<= int(n_KT_0):
            raise ValueError("n_KT_0 muss größer als 0 sein.")
        self.n_KT_0 = int(n_KT_0)
        self.w_s0 = float(w_s0)
        self.w_sm = float(w_sm)
        self.w_th = float(w_th)
        self.system = system
        self.noten = []
        self.sj_start, self.sj_ende = None, None
        self._v_enabled = v_enabled
        self._art = ['m', 'KT', 'KA', 'GFS']
    
    def _check_time_range(self):
        noten_with_range = list(filter(lambda x: x._is_punctual==False, self.noten))
        for pair in itertools.combinations(noten_with_range, 2):
            if pair[0].von <= pair[1].bis and pair[0].bis >= pair[1].von:
                raise ValueError(f"Die Zeiträume der mündlichen Noten überschneiden sich: {pair[0]} von {pair[0].date} und {pair[1]} vom {pair[1].date}")
        
    def _check_limits(self, show_warnings = False):
        if self._fach==None:
            return None
        
        checks = self._fach.limits.check_limits(self.noten, show_warnings=show_warnings)
        
        return checks
            
    def _set_SJ(self):
         dates = [note.date for note in self.noten]
         min_date = min(dates)
         max_date = max(dates)
    
         if (max_date - min_date).days > 365:
             raise ValueError('Die hinzugefügten Noten liegen mehr als 1 Jahr auseinander.')
         
         SJ = min_date.year if min_date.month >= 9 else min_date.year - 1
    
         sj_start = datetime(SJ, 9, 1)
         sj_ende = datetime(SJ + 1, 7, 31)
            
         for date in dates:
             if not (sj_start <= date <= sj_ende):
                 raise ValueError('Alle Noten müssen sich innerhalb eines Schuljahres bewegen.')
                 
         self.sj_start, self.sj_ende = sj_start, sj_ende
                
    def _sort_grade_after_date(self):
        self.noten.sort(key=lambda x: x.date)
            
    def add_from_excel(self, path):
        df = pd.read_excel(path)
        for _,row in df.iterrows():
            self.note_hinzufuegen(**row)

    def _get_noten_filled_with_nr(self):
        updated_notenliste = self.noten.copy()
        for art in self._art:
            current_nr = 1
            filtered_noten = [note for note in updated_notenliste if note._art == art]
            filtered_noten.sort(key=lambda x: x.date)
            for note in filtered_noten:
                if note.nr is None:
                    last_note_same_art = next((n for n in reversed(filtered_noten) if n.nr is not None and n.date < note.date), None)
                    if last_note_same_art:
                        current_nr = last_note_same_art.nr + 1
                    note.nr = current_nr
                    current_nr += 1
        return updated_notenliste

    def _get_dataframe(self):
        return pd.DataFrame(self._get_list())

    def _get_list(self):
        noten = self._get_noten_filled_with_nr()
        return [note._as_dict() for note in noten]

    def _get_leistung_for_types(self, *args):
        return list(filter(lambda x: any(isinstance(x, arg) for arg in args), self.noten))
    
    def _update_handler_after_added_leistung(self):
        self._sort_grade_after_date()
        self._set_SJ()        
    
    def leistung_hinzufuegen(self, Leistung):
        if not isinstance(Leistung, LeistungGeneric):
            raise ValueError(f'Ungültiges Leistungsobjekt. Es muss ein Objekt der (Sub-)Klasse LeistungGeneric übergeben werden.')
        self.noten.append(Leistung)
        self._update_handler_after_added_leistung()

    def note_hinzufuegen(self, **kwargs):
        mandatory_keys = ['art', 'note', 'date']
        if all(key in kwargs for key in mandatory_keys):
            art = kwargs.get('art')
            note = kwargs.get('note')
            date = kwargs.get('date')
            
            pars = {
                    'note' : note,
                    'system': self.system,
                    'date' : date,
                    'status' : kwargs.get('status'),
                    'nr' : kwargs.get('nr'),
                    'von' : kwargs.get('von'),
                    'bis' : kwargs.get('bis'),
                    }
            
            if art == 'm':
                Leistung = LeistungM(**pars)
            elif art == 'KA':
                Leistung = LeistungKA(**pars)
            elif art == 'KT':
                Leistung = LeistungKT(**pars)
            elif art == 'P':
                Leistung = LeistungP(**pars)
            elif art == 'GFS':
                Leistung = LeistungGFS(**pars)
            else:
                raise ValueError(f'Ungültige Art der Note: {art}')
                
            self.noten.append(Leistung)
            self._update_handler_after_added_leistung()

        else:
            raise ValueError(f'Fehlende Informationen. Bitte geben Sie {" und ".join(mandatory_keys)} an.')

    def mittelwert(self, noten):
        noten_werte = np.array([float(note.note) for note in noten])
        if len(noten_werte)==0:
            return None
        return np.mean(noten_werte)

    def _calculate(self):
        """
        Dummy Methode zur Berechnung der Noten.
        """
        # Calculate
        result = Note(datum=self.noten[-1].date)

        #
        # HIER DEN ALGORITHMUS ZUR NOTENBERECHNUNG HINZUFÜGEN
        #
        
        return result
        

    def berechne_gesamtnote(self, show_warnings = True):
        #First run checks on noten
        self._check_time_range()
        _ = self._check_limits(show_warnings = show_warnings)
        
        result = self._calculate()
        if not isinstance(result, Note):
            raise ValueError(f'Die interne Notenberechnungsmethode muss ein Objekt der Klasse Note zurückgeben')
        
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
                ergebnis = kopie.berechne_gesamtnote(show_warnings=False)
                ergebnisse.append(ergebnis)
            except ValueError as e:
                print(f"Fehler beim Hinzufügen der Note: {str(e)}")
        
        return ergebnisse
    
    def plot_time_series(self, save=None, sid = None, parent = None, formats = ['jpg'], **kwargs):
        if not isinstance(sid, SchuelerEntity):
            sid = None
        if not isinstance(parent, LerngruppeEntity):
            parent = None
            
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
        ax.plot(dates[-1], result[-1].gesamtnote._get_Z(), marker='x', color='k', linestyle='None', label='Stand')

        # Setze die Zeitachsen-Begrenzungen
        ax.set_xlim(self.sj_start, self.sj_ende)
        
        # Y-Achsen Skalierung basierend auf noten.system
        if self.system == 'N':
            ax.set_ylim(1, 6)
            ax.invert_yaxis()
        elif self.system == 'NP':
            ax.set_ylim(0, 15)
        
        
        # Achsenbeschriftungen und Titel
        ax.set_xlabel('Datum')
        ax.set_ylabel('Gesamtnote')
        if (sid!=None) and (parent!=None):
            title = f'{sid.vorname} {sid.nachname}, {parent.kurs}, {parent.fach.name}, Schuljahr {self.sj_start.year}/{self.sj_ende.year}'
        elif (sid!=None):
            title = f'{sid.vorname} {sid.nachname}, Schuljahr {self.sj_start.year}/{self.sj_ende.year}'
        else:
            title = f'Entwicklung der Leistungen in dem Schuljahr {self.sj_start.year}/{self.sj_ende.year}'
        
        if self._typ != None:
            title += f', {self._typ._get_name()}'
        
        ax.set_title(title)

        # Legende
        ax.legend()
        
        ax.yaxis.set_minor_locator(plt.MultipleLocator(0.5))
        ax.grid(which='minor', axis='y', linestyle=':', linewidth=0.5, color='black')
        fig.tight_layout()
        
        if self._v_enabled:
            # Diskretisierungsbereich
            baseline = (np.ceil(float(gesamtnoten[-1]))+np.floor(float(gesamtnoten[-1])))/2
            xlims = ax.get_xlim()
            rect = patches.Rectangle((xlims[0], baseline - self.w_th), xlims[1]-xlims[0], 2*self.w_th, linewidth=1, edgecolor='none', facecolor='red', alpha=0.15)
            ax.add_patch(rect)

        # Datumsformatierung der x-Achse
        fig.autofmt_xdate()

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
            
class SchuelerEntity:
    def __init__(self, **kwargs):
        self.sid = kwargs.get('sid')
        self.vorname = kwargs.get('vorname')
        self.nachname = kwargs.get('nachname')
        self.note = None
        
        if None in (self.sid, self.vorname, self.nachname):
            raise ValueError("Alle Werte (sid, vorname, nachname) müssen beim Initialisieren gesetzt werden.")

    def _print(self):
        note = ""
        if self.note != None:
            note = f', {self.note.gesamtnote._get_HJ(text=True)}'
        return f"{self.vorname} {self.nachname}{note}"

    def __str__(self):
        return self._print()
    
    def __repr__(self):
        return self._print()
    
    def plot(self, parent = None, **kwargs):
        if not isinstance(self._notenberechnung, NotenberechnungGeneric):
            raise ValueError("Für {self.sid} {self.vorname} {self.nachname} wurden noch keine Noten gesetzt.")     
            
        self._notenberechnung.plot_time_series(sid=self, parent = parent, **kwargs)
        
    def get_dataframe(self):
        return self._notenberechnung._get_dataframe()

    def setze_note(self, note):
        if not isinstance(note, NotenberechnungGeneric):
            raise ValueError("Das übergebene Objekt ist keine Instanz der Klasse Notenberechnung.")
        self._notenberechnung = note
        self.note = self._notenberechnung.berechne_gesamtnote()

class LerngruppeEntity:
    def __init__(self, **kwargs):
        self.stufe = int(kwargs.get('stufe', None)) if kwargs.get('stufe') is not None else None
        
        if self.stufe not in range(5, 13):
            raise ValueError("Die Stufe muss zwischen 5 und 12 liegen.")
        
        self.fach = kwargs.get('fach', None)
        if not issubclass(self.fach, FachGeneric):
            raise ValueError(f"Bitte eine gültige Klasse für ein Fach übergeben.")
                    
        if self.stufe in [11, 12]:
            self.zug = None
            self.kurs = kwargs.get('kurs', None)
            if self.kurs is None:
                raise ValueError("Für Stufe 11 oder 12 muss der Kurs angegeben werden.")
        else:
            self.zug = kwargs.get('zug', None).lower() if kwargs.get('zug', None) else None
            self.kurs = self._name()
        
        self.schueler = dict()

    def _name(self):
        if self.stufe in range(5, 11):
            return f"{self.stufe:02d}{self.zug}"
        elif self.stufe in [11, 12]:
            return f"JGS{self.stufe}"
        else:
            raise ValueError("Ungültige Stufe")

    def update_sid(self, schueler_entity):
        if not isinstance(schueler_entity, SchuelerEntity):
            raise ValueError("Das hinzuzufügende Objekt muss eine Instanz der Klasse SchuelerEntity sein.")
        
        self.schueler[schueler_entity.sid] = schueler_entity
    
    def plot_sid(self, sid, **kwargs):
        if isinstance(sid, SchuelerEntity):
            if sid not in self.schueler.values():
                raise ValueError("Das Objekt ist nicht in der Lerngruppe enthalten!")
            sid.plot(parent=self, **kwargs)
            
        else: 
            if sid not in self.schueler.keys():
                raise ValueError("Dieses Objekt enthält keine sid {sid}")
        
            self.schueler[sid].plot(parent=self, **kwargs)

    def _export(self):
        export_list = []
        for schueler_entity in self.schueler.values():
            schueler_dict = {
                'sid': schueler_entity.sid,
                'vorname': schueler_entity.vorname,
                'nachname': schueler_entity.nachname,
                'stufe': self.stufe,
                'zug' : self.zug,
                'fach': self.fach.name if self.fach!=None else None,
                'klasse' : self._name(),
                'kurs' : self.kurs,
                'note_s' : float(schueler_entity.note.m_s),
                'note_m' : float(schueler_entity.note.m_m),
                'note' : float(schueler_entity.note.gesamtnote),
                'note_hj' : schueler_entity.note.gesamtnote._get_HJ(text=True),
                'note_z' : schueler_entity.note.gesamtnote._get_Z(text=True),
            }
            
            export_list.append(schueler_dict)
        
        return export_list
    
    def get_dataframe(self):
        return pd.DataFrame(self._export())
    
    def save_excel(self, path):
        path = os.path.abspath(os.path.splitext(path)[0] + '.xlsx')
        # Check if basedir of path exists, create if not
        basedir = os.path.dirname(path)
        if not os.path.exists(basedir):
            try:
                os.makedirs(basedir)
            except OSError as e:
                raise RuntimeError(f"Error creating directory {basedir}: {e}")

        # Check if directory was created
        if not os.path.exists(basedir):
            raise RuntimeError(f"Directory {basedir} could not be created.")
            
        df = self.get_dataframe()

        try:
            df.to_excel(path, index=False)
            print(f"DataFrame successfully exported to {path}")
        except Exception as e:
            raise RuntimeError(f"Error exporting DataFrame to Excel: {e}")

if __name__ == "__main__":
    pass
    # Beispiel
    self = NotenberechnungGeneric(w_s0=1, w_sm=3, system = 'N', v_enabled=True, w_th = 0.4, fach=FachM)
    self.note_hinzufuegen(art='KA', date = '2024-04-10', note=3, status='fertig')
    self.note_hinzufuegen(art='KA', date = '2024-04-15', note=2.5, status='fertig')
    # self.note_hinzufuegen(art='KA', date = '2024-03-01', note=4, status='fertig')
    # self.note_hinzufuegen(art='GFS', date = '2024-03-05', note=3.25)
    # self.note_hinzufuegen(art='KA', date = '2024-03-15', note=5, status='uv')
    # self.note_hinzufuegen(art='P', date = '2024-02-01', note=4)
    # self.note_hinzufuegen(art='KT', date = '2024-01-01', note=2.75, status='fehlt')
    # self.note_hinzufuegen(art='m', date = '2023-10-05', von = '2023-09-01', note=3.0)
    # self.note_hinzufuegen(art='m', date = '2023-12-05', von = '2023-10-06', note=3.25)
    # self.note_hinzufuegen(art='m', date = '2024-05-01', von = '2023-12-06', note=3.5)
    
    gesamtnote = self.berechne_gesamtnote()
    print(gesamtnote)