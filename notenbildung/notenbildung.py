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
import itertools
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import matplotlib.dates as mdates

class NoteEntity(np.ndarray):
    def __new__(cls, note, system=None):
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
        
class AttributGeneric:
    _type = None
    long = None

    @classmethod
    def __str__(cls):
        return cls._print()

    @classmethod
    def __repr__(cls):
        return cls._print()

    @classmethod
    def _print(cls):
        return f"{cls.long}"

class AttributM(AttributGeneric):
    _type = 'm'
    long = 'mündlich'

class AttributS(AttributGeneric):
    _type = 's'
    long = 'schriftlich'

class AttributP(AttributGeneric):
    _type = 'p'
    long = 'fachpraktisch'

class LeistungGeneric:
    def __init__(self, **kwargs):
        missing_args = ", ".join([arg for arg in ['note', 'system', 'date'] if arg not in kwargs])
        if any(arg not in kwargs for arg in ['note', 'system', 'date']):
            raise ValueError(f"Die Argumente '{missing_args}' müssen angegeben werden.")

        note = kwargs.get('note')
        system = kwargs.get('system')
        self.date = self._parse_date(kwargs.get('date'))
        self._art = None
        self._is_punctual = True
        
        self.status = VerbesserungStatus(kwargs.get('status','---'))
        self.note = NoteEntity(note, system)
        self.nr = kwargs.get('nr')
        self.von = None
        self.bis = None
        
    def _parse_date(self, date_str):
        if isinstance(date_str, datetime):
            return date_str
        try:
            return datetime.strptime(date_str, "%Y-%m-%d")
        except (ValueError, TypeError):
            raise ValueError("Ungültiges Datumsformat")

    def _as_dict(self):
        return {
            'date': self.date,
            'art': self._art,
            'status': self.status.text,
            'note': self.note,
            'nr': self.nr,
            'von': self.von,
            'bis': self.bis,
        }

    def __str__(self):
        return self._print()

    def __repr__(self):
        return self._print()

    def _print(self):
        output = f"{self.note}; {self._art}"
        
        if self.nr is not None:
            output = f"{output}; nr {self.nr}"
            
            if self.status._enabled:
                output += f", Status: {self.status}"
        
        return f'({output})'
        
class LeistungM(LeistungGeneric):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._art = 'm'
        self._attribut = AttributM
        self.status._disable()          
        
        self.von = self._parse_date(kwargs.get('von') or self.date)
        self.bis = self._parse_date(kwargs.get('bis') or self.date)
        
        if self.von > self.bis:
            raise ValueError(f"Ungültiger Zeitraum für die mündlichen noten.")
            
        if self.von != self.bis:
            self._is_punctual = False      
        
class LeistungKA(LeistungGeneric):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._art = 'KA'
        self._attribut = AttributS

class LeistungGFS(LeistungKA):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._art = 'GFS'
        self._attribut = AttributP
        self.status._disable()

class LeistungKT(LeistungGeneric):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._art = 'KT'
        self._attribut = AttributS

class LeistungP(LeistungKT):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._attribut = AttributP
        self.status._disable()

        
class LimitsGeneric:
    _type = None
    limits =   [
                    {
                     'sum' : [AttributM,AttributS,AttributP],
                     'min' : 1,
                     'max' : None,
                    },
                ]

    @classmethod
    def check_limits(cls, leistungen):
        limits = cls.limits.copy()
        for limit in limits:
            sum_attributes = 0
            for leistung in leistungen:
                if any(isinstance(obj, item) or obj == item for obj in [leistung, leistung._attribut] for item in limit['sum']):
                    sum_attributes += 1
            limit['result'] = sum_attributes
            limit['passed'] = True
            limit['softfail'] = False
            limit['hardfail'] = False
            
            
            if limit['min'] is not None and sum_attributes < limit['min']:
                limit['passed'] = False
                limit['softfail'] = True
    
            
            if limit['max'] is not None and sum_attributes > limit['max']:
                limit['passed'] = False
                limit['hardfail'] = True
                
        result = {
                  'passed' : all(limit['passed'] for limit in limits), 
                  'softfail' : any(limit['softfail'] for limit in limits),                  
                  'hardfail' : any(limit['hardfail'] for limit in limits),                  
                  'result':limits,
                  }
        
        return result
    
class LimitsKernfach(LimitsGeneric):
    _type = 'Kernfach'
    limits = LimitsGeneric.limits + [
        {
            'sum': [AttributM],
            'min': 1,
            'max': None,
        },
        {
            'sum': [LeistungKA],
            'min': 4,
            'max': None,
        },
    ]
    
class LimitsNichtkernfach(LimitsGeneric):
    _type = 'Nichtkernfach'
    limits = LimitsGeneric.limits =  [ 
                        {
                         'sum' : [AttributS],
                         'min' : None,
                         'max' : 4,
                        },
                        {
                         'sum' : [AttributM],
                         'min' : 1,
                         'max' : None,
                        },
                    ]
    
class LimitsLK(LimitsGeneric):
    _type = 'LK'
    limits = LimitsGeneric.limits + [
        {
            'sum': [AttributM],
            'min': 1,
            'max': None,
        },
        {
            'sum': [LeistungKA],
            'min': 2,
            'max': None,
        },
    ]
        
class VerbesserungStatus:
    def __init__(self, text):
        self.text = text if text != None else '---'
        self._check()
    
    def _check(self):
        self._enabled = True if self.text != "---" else False
        self.status = True if self.text == "fertig" else False if self.text == "fehlt" else None        
    
    def _disable(self):
        self.text = '---'
        self._check()

    def __str__(self):
        return self._print()

    def __repr__(self):
        return self._print()

    def _print(self):
        return f"{self.text}"
        
class FachGeneric:
    name = None
    long = None
    limits = None
    @classmethod
    def _get_name(cls):
        if cls.long is not None:
            return cls.long
        return ''

class FachM(FachGeneric):
    name = 'M'
    long = 'Mathematik'
    limits = LimitsKernfach

class FachPH(FachGeneric):
    name = 'Ph'
    long = 'Physik'
    limits = LimitsNichtkernfach

class FachPHLK(FachGeneric):
    name = 'Ph'
    long = 'Physik'
    limits = LimitsLK

class FachINF(FachGeneric):
    name = 'Inf'
    long = 'Informatik'
    limits = LimitsNichtkernfach
    

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
        
        checks = self._fach.limits.check_limits(self.noten)

        if not checks['passed']:
            if show_warnings==True:
                _ = [print(f"Warnung: Zu wenige Leistungen: {limit['sum']}: Anzahl der Leistungen {limit['result']}<{limit['min']}") if not limit['passed'] and limit['softfail'] else None for limit in checks['result']]

            _ = [print(f"Fehler: zu viele Leistungen: {limit['sum']}: Anzahl der Leistungen {limit['result']}>{limit['max']}") for limit in checks['result'] if not limit['passed'] and limit['hardfail']]
            
            if any(not limit['passed'] and limit['hardfail'] for limit in checks['result']):
                raise ValueError("Fehler: zu viele Leistungen")
        
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
                leistung_obj = LeistungM(**pars)
            elif art == 'KA':
                leistung_obj = LeistungKA(**pars)
            elif art == 'KT':
                leistung_obj = LeistungKT(**pars)
            elif art == 'P':
                leistung_obj = LeistungP(**pars)
            elif art == 'GFS':
                leistung_obj = LeistungGFS(**pars)
            else:
                raise ValueError(f'Ungültige Art der Note: {art}')

            self.noten.append(leistung_obj)
            self._sort_grade_after_date()
            self._set_SJ()
        else:
            raise ValueError(f'Fehlende Informationen. Bitte geben Sie {" und ".join(mandatory_keys)} an.')

    def mittelwert(self, noten):
        noten_werte = np.array([float(note.note) for note in noten])
        if len(noten_werte)==0:
            return None
        return np.mean(noten_werte)

    def berechne_gesamtnote(self, show_warnings = True):
        #First run checks on noten
        self._check_time_range()
        _ = self._check_limits(show_warnings = show_warnings)
        
        # Calculate
        result = Note(datum=self.noten[-1].date)
        verbesserung_enabled = any(note.status._enabled for note in self.noten) and self._v_enabled
        
        # Filtern der Noten nach Art
        noten_ka = list(filter(lambda x: isinstance(x, LeistungKA) or isinstance(x, LeistungGFS), self.noten))
        noten_kt = list(filter(lambda x: isinstance(x, LeistungKT) or isinstance(x, LeistungP), self.noten))
        noten_muendlich = list(filter(lambda x: isinstance(x, LeistungM), self.noten))

        
        # Zählen der verschiedenen Statusarten
        verbesserung_enabled = [note for note in self.noten if note.status._enabled]
        n_v_g = len(verbesserung_enabled)
        n_v_o = len([note for note in verbesserung_enabled if note.status.status==None])
        n_v_1 = len([note for note in verbesserung_enabled if note.status.status==False])
        n_v_2 = len([note for note in verbesserung_enabled if note.status.status==True])

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
        if not isinstance(self._notenberechnung, Notenberechnung):
            raise ValueError("Für {self.sid} {self.vorname} {self.nachname} wurden noch keine Noten gesetzt.")     
            
        self._notenberechnung.plot_time_series(sid=self, parent = parent, **kwargs)
        
    def get_dataframe(self):
        return self._notenberechnung._get_dataframe()

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
    self = Notenberechnung(w_s0=1, w_sm=3, system = 'N', v_enabled=True, w_th = 0.4, fach=FachM)
    self.note_hinzufuegen(art='KA', date = '2024-04-10', note=3, status='fertig')
    self.note_hinzufuegen(art='KA', date = '2024-04-15', note=2.5, status='fertig')
    self.note_hinzufuegen(art='KA', date = '2024-03-01', note=4, status='fertig')
    self.note_hinzufuegen(art='GFS', date = '2024-03-05', note=3.25)
    self.note_hinzufuegen(art='KA', date = '2024-03-15', note=5, status='uv')
    self.note_hinzufuegen(art='P', date = '2024-02-01', note=4)
    self.note_hinzufuegen(art='KT', date = '2024-01-01', note=2.75, status='fehlt')
    self.note_hinzufuegen(art='m', date = '2023-10-05', von = '2023-09-01', note=3.0)
    self.note_hinzufuegen(art='m', date = '2023-12-05', von = '2023-10-06', note=3.25)
    self.note_hinzufuegen(art='m', date = '2024-05-01', von = '2023-12-06', note=3.5)
    
    gesamtnote = self.berechne_gesamtnote()
    print(gesamtnote)
    self.plot_time_series()
    
