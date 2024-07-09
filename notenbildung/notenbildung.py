#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Notenberechnung
"""
import os
import numpy as np
import pandas as pd
from datetime import datetime
import copy
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import matplotlib.dates as mdates

class NoteEntity(np.ndarray):
    def __new__(cls, note, system=None):
        # Validate note range based on the system
        if note==None:
            note = np.nan
        else:
            if system not in ['N', 'NP']:
                raise ValueError("Das System muss entweder 'N' oder 'NP' sein.")
            if system == 'N' and not (1 <= note <= 6):
                raise ValueError("Die Note muss zwischen 1 und 6 für das System 'N' liegen.")
            elif system == 'NP' and not (0 <= note <= 15):
                raise ValueError("Die Note muss zwischen 0 und 15 für das System 'NP' liegen.")
        
        obj = np.asarray(note).view(cls)
        obj.system = system
        return obj

    def gerundet(self):
        result = dict()
        Z = round(float(self))
        if self.system == 'N':
            HJ = round(float(self) * 4) / 4
            result.update({'HJ': {'v': HJ, 's': self._num_to_string(HJ)}, 'Z': {'v': Z, 's': self._num_to_string(Z, ints=True)}})
        elif self.system == 'NP':
            result.update({'Z': {'v': Z, 's': self._num_to_string(Z)}})
            result['HJ'] = result['Z']
        return result

    def _get_Z(self, text=False):
        if text:
            return self.gerundet().get('Z',{}).get('s')
        else:
            return self.gerundet().get('Z',{}).get('v')
        
    def _get_HJ(self, text=False):
        if text:
            return self.gerundet().get('HJ',{}).get('s')
        else:
            return self.gerundet().get('HJ',{}).get('v')

    def _num_to_string(self, note, ints=False):
        if self.system == 'NP':
            return str(int(round(note)))
        elif self.system == 'N':
            if (ints == True) or (note == round(note)):
                return str(int(round(note)))
            else:
                whole_number = int(note)
                decimal = note % 1
                if decimal <= 0.25:
                    return str(whole_number) + '-'
                elif decimal >= 0.75:
                    return str(whole_number + 1) + '+'
                elif 0.25 < decimal < 0.75:
                    return f'{int(whole_number)}-{int(whole_number + 1)}'
                else:
                    return str(whole_number)

    def __array_finalize__(self, obj):
        if obj is None:
            return
        self.system = getattr(obj, 'system', None)

    def __str__(self):
        return f"{self}"

    def __repr__(self):
        return self.__str__()

    def __round__(self):
        return round(float(self))

    def _operate(self, other, operation):
        if isinstance(other, NoteEntity):
            if self.system == other.system:
                result = operation(float(self), float(other))
                return NoteEntity(result, system = self.system)
            else:
                raise ValueError("Systeme sind nicht gleich und können nicht verrechnet werden")
        else:
            result = operation(float(self), float(other))
            return NoteEntity(result, system = self.system)

    def __add__(self, other):
        return self._operate(other, lambda x, y: x + y)

    def __sub__(self, other):
        return self._operate(other, lambda x, y: x - y)

    def __mul__(self, other):
        return self._operate(other, lambda x, y: x * y)

    def __truediv__(self, other):
        return self._operate(other, lambda x, y: x / y)

class Note:
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

class Notenberechnung:
    def __init__(self, w_sm = 3, w_th = 0.25, w_s0 = 1, n_KT_0 = 3, system = 'N', v_enabled = True):        
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

    def _set_SJ(self):
         dates = [note['datum'] for note in self.noten]
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
        self.noten.sort(key=lambda x: x['datum'])

    def parse_date(self, date_str):
        if isinstance(date_str, datetime):
            return date_str
        try:
            return datetime.strptime(date_str, "%Y-%m-%d")
        except (ValueError, TypeError):
            raise ValueError("Ungültiges Datumsformat")
            
    def add_from_excel(self, path):
        df = pd.read_excel(path)
        for _,row in df.iterrows():
            self.note_hinzufuegen(**row)

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
            self._set_SJ()
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
        w_s = n_KT * self.w_s0/self.n_KT_0 if n_KT < self.n_KT_0 else self.w_s0
        m_s1 = (n_KA * m_KA + w_s * m_KT) / (n_KA + w_s)

        # Berechnung des Diskretisierungsfaktors
        w_d = 1 if self.w_th == 0 else abs((0.5 - (m_s1 % 1)) / self.w_th) 
        
        # Berechnen der Gewichte je nach Notensystem
        m_h = (np.ceil(m_s1)+np.floor(m_s1))/2
        if self.system=='N':
            w_v1 = 0 if w_d >= 1 else m_h + self.w_th if w_d < 1 else 0
            w_v2 = 0 if w_d >= 1 else m_h - self.w_th if w_d < 1 else 0
            w_0 = 6 - 1
        elif self.system=='NP':
            w_v1 = 0 if w_d >= 1 else m_h - self.w_th if w_d < 1 else 0
            w_v2 = 0 if w_d >= 1 else m_h + self.w_th if w_d < 1 else 0
            w_0 = 15 - 0
            
        w_v3 = 0 if w_d >= 1 else abs(w_0/self.w_th) if w_d < 1 else 0
        
        if (not verbesserung_enabled) or (n_v_g == 0) or (self.w_th==0) or (w_d >= 1):
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
            ax.set_title(f'{sid.vorname} {sid.nachname}, {parent.kurs}, {parent.fach}, Schuljahr {self.sj_start.year}/{self.sj_ende.year}')
        elif (sid!=None):
            ax.set_title(f'{sid.vorname} {sid.nachname}, Schuljahr {self.sj_start.year}/{self.sj_ende.year}')
        else:
            ax.set_title(f'Entwicklung der Leistungen in dem Schuljahr {self.sj_start.year}/{self.sj_ende.year}')

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
        if not isinstance(self._notenberechnung, Notenberechnung):
            raise ValueError("Für {self.sid} {self.vorname} {self.nachname} wurden noch keine Noten gesetzt.")     
            
        self._notenberechnung.plot_time_series(sid=self, parent = parent, **kwargs)

    def setze_note(self, note):
        if not isinstance(note, Notenberechnung):
            raise ValueError("Das übergebene Objekt ist keine Instanz der Klasse Notenberechnung.")
        self._notenberechnung = note
        self.note = self._notenberechnung.berechne_gesamtnote()

class LerngruppeEntity:
    def __init__(self, **kwargs):
        self.stufe = int(kwargs.get('stufe', None)) if kwargs.get('stufe') is not None else None
        
        if self.stufe not in range(5, 13):
            raise ValueError("Die Stufe muss zwischen 5 und 12 liegen.")
        
        self._faecher = {
            'M': 'Mathematik',
            'Ph': 'Physik',
            'Inf': 'Informatik',
        }
        self.fach = kwargs.get('fach', None)
        if self.fach not in self._faecher:
            raise ValueError(f"Das angegebene Fach '{self.fach}' ist nicht gültig. Gültige Fächer sind: {', '.join(self._faecher.keys())}")
                    
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
                'fach': self.fach,
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
    # Beispiel
    self = Notenberechnung(w_s0=1, w_sm=3, system = 'N', v_enabled=True, w_th = 0.4)
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
    
