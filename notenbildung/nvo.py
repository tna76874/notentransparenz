#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Module zur Notenbildungsverordnung
"""
import os
import numpy as np
from datetime import datetime
import copy
import pprint
#
#
# NoteEntity stellt sicher, dass eine gültige Zahl als Note übergeben wurde. Es gibt Methoden um entsprechend die Leistung in Text auszugeben.
#
#
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
    
    def _get_system_range(self):
        if self.system == 'N':
            return 6-1
        elif self.system == 'NP':
            return 15-0
        else:
            raise ValueError("System-Range Error")

    def _round(self,number):
        if number % 1 == 0.5:
            if self.system == 'N':
                return np.ceil(number)
            elif self.system == 'NP':
                return np.floor(number)
        else:
            return np.round(number)

    def gerundet(self):
        result = dict()
        Z = self._round(float(self))
        if self.system == 'N':
            HJ = self._round(float(self) * 4) / 4
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

    def _get_text(self):
        rounded_note = int(self._get_Z(text=False))
        if self.system == 'N':
            if rounded_note == 1:
                return "sehr gut"
            elif rounded_note == 2:
                return "gut"
            elif rounded_note == 3:
                return "befriedigend"
            elif rounded_note == 4:
                return "ausreichend"
            elif rounded_note == 5:
                return "mangelhaft"
            elif rounded_note == 6:
                return "ungenügend"
        elif self.system == 'NP':
            if 13 <= rounded_note <= 15:
                return "sehr gut"
            elif 10 <= rounded_note <= 12:
                return "gut"
            elif 7 <= rounded_note <= 9:
                return "befriedigend"
            elif 5 <= rounded_note <= 6:
                return "ausreichend"
            elif rounded_note == 4:
                return "schwach ausreichend"
            elif 1 <= rounded_note <= 3:
                return "mangelhaft"
            elif rounded_note == 0:
                return "ungenügend"
        return "Note nicht im gültigen Bereich für das System"

    def _num_to_string(self, note, ints=False):
        if self.system == 'NP':
            return str(int(self._round(note)))
        elif self.system == 'N':
            if (ints == True) or (note == self._round(note)):
                return str(int(self._round(note)))
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
        return self._round(float(self))

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
    
##########################################
##########################################
 
#
#
# Die Attribut Klassen klassifizieren die Leistung entweder als mündlich, schriftlich oder fachpraktisch
#
#
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
##########################################
##########################################

#
#
# Klasse zur Gewichtung
#
#
class Weight:
    def __init__(self, *noten):
        self.mean = None
        self.w = None
        self._n = len(noten)
        
        if not all(isinstance(obj, LeistungGeneric) or isinstance(obj, NoteEntity) for obj in noten):
            raise TypeError("Nicht alle Objekte sind Instanzen von LeistungGeneric oder NoteEntity")
        
        if all(isinstance(obj, LeistungGeneric) for obj in noten):
            self.mean = self._mean(list([note.note for note in noten]))
            self._type = [type(obj) for obj in noten]
            
        elif all(isinstance(obj, NoteEntity) for obj in noten):
            self.mean = self._mean(noten)
        else:
            raise TypeError("Nicht erlaubte Klasse")
        
        

    def __add__(self, other):
        if not isinstance(other, Weight):
            raise TypeError("Kann nur ein Weight-Objekt zu einem anderen Weight-Objekt hinzufügen")

        if self.mean is None and self.w is None:
            return other
        if other.mean is None and other.w is None:
            return self

        if self.mean is not None and other.mean is not None:
            if self.w is None or other.w is None:
                raise ValueError("Die Gewichtung muss angegeben sein.")

        new_weight = self.w + other.w
        combined = NoteEntity((float(self.mean)*self.w + float(other.mean)*other.w)/new_weight, system=self.mean.system)
        return_weight = Weight(combined).set_type(self._type+other._type).set_weight(new_weight)
        return return_weight

    def set_weight(self, w):
        self.w = w if self.mean is not None else None
        return self

    def set_weight_for_each(self, w):
        self.w = w * self._n if self.mean is not None else None
        return self

    def set_type(self, typelist):
        if not isinstance(typelist, list):
            raise TypeError("Es muss eine Liste übergeben werden")
        self._type = list(set(typelist))
        return self

    def _mean(self, noten):
        noten_werte = np.array([float(note) for note in noten if not np.isnan(float(note))])
        self._n = len(noten_werte)
        if len(noten_werte)==0:
            return None
        return NoteEntity(np.mean(noten_werte), system=noten[0].system)

    def __str__(self):
        return self._print()

    def __repr__(self):
        return self._print()

    def _print(self):
        return f"{self.w}*{self.mean}"

##########################################
##########################################

#
#
# Die Verbesserungs-Klasse setzt den Status der Verbesserung.
#
#
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

##########################################
##########################################

#
#
# Die Leistungs-Klassen enthalten sämtliche Informationen zu einer erhobenen Leistung inklusive des passenden Attributs.
#
#
class LeistungGeneric:
    last = None
    head = None
    def __init__(self, **kwargs):
        note = kwargs.get('note')
        self.system = kwargs.get('system')
        if isinstance(note, NoteEntity):
            self.note = note
            self.system = note.system
        else:
            self.note = NoteEntity(note, self.system)
        
        self.date = self._parse_date(kwargs.get('date'))
        self._art = None
        self._is_punctual = True
        
        self.status = VerbesserungStatus(kwargs.get('status','---'))
        
        self.nr = kwargs.get('nr')
        self._nr = None
        self.von = None
        self.bis = None
        
    def _get_nr(self):
        return self._nr or self.nr
        
    def _parse_date(self, date_str):
        if isinstance(date_str, datetime):
            return date_str
        try:
            return datetime.strptime(date_str, "%Y-%m-%d")
        except (ValueError, TypeError):
            raise ValueError("Ungültiges Datumsformat")
    
    def _get_date(self):
        return self.date

    def _as_dict(self):
        return {
            'date': self._get_date(),
            'art': self._art,
            'status': self.status.text,
            'note': self.note,
            'nr': self._get_nr(),
            'von': self.von,
            'bis': self.bis,
        }

    def __str__(self):
        return self._print()

    def __repr__(self):
        return self._print()

    def _print(self):
        output = f'{self.note}; {self._art}; {self.date.strftime("%d.%m.%Y")}'
        
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
        
class LeistungGFS(LeistungGeneric):
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

class LeistungP(LeistungGeneric):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._art = 'P'
        self._attribut = AttributP
        self.status._disable()

class LeistungKTP(LeistungGeneric):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._art = 'KTP'
        self._attribut = AttributP
        self.status._disable()

class LeistungKAP(LeistungGeneric):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._art = 'KAP'
        self._attribut = AttributP
        self.status._disable()

class LeistungV(LeistungGeneric):
    def __init__(self, **kwargs):
        mean = kwargs.get('mean')
        
        if isinstance(kwargs.get('status'), VerbesserungStatus):
            status = kwargs.get('status')
        else:
            status = VerbesserungStatus(kwargs.get('status','---'))
            
        system = kwargs.get('system')
        w_th = kwargs.get('w_th')
        self.w_th = w_th
        self.mean = mean
        if mean==None:
            raise ValueError("Der Mittelwert der schriftlichen Noten muss angegeben werden.")
        if w_th==None:
            raise ValueError("Die Schranke w_th muss angeeben werden.")
        mean = float(mean)
        m_h = (np.ceil(mean)+np.floor(mean))/2
        w_d = 1 if w_th == 0 else abs((0.5 - (mean % 1)) / w_th)

        if system=='N':
            w_v1 = None if w_d >= 1 else m_h + w_th if w_d < 1 else None
            w_v2 = None if w_d >= 1 else m_h - w_th if w_d < 1 else None
        elif system=='NP':
            w_v1 = None if w_d >= 1 else m_h - w_th if w_d < 1 else None
            w_v2 = None if w_d >= 1 else m_h + w_th if w_d < 1 else None
        
        if status._enabled == False or (w_d >= 1):
            kwargs['note'] = NoteEntity(None, system = system)
        else:
            if status.status==None:
                kwargs['note'] = NoteEntity(mean, system = system)
            elif status.status==False:
                kwargs['note'] = NoteEntity(w_v1, system = system)
            elif status.status==True:
                kwargs['note'] = NoteEntity(w_v2, system = system)
            else:
                raise ValueError("Fehler beim Initialisieren des Verbesserungsobjektes")
        
        super().__init__(**kwargs)
        self._art = 'V'
        self._attribut = AttributS
        self.status._disable()

    def _get_date(self):
        return None

##########################################
##########################################

#
#
# Die Limits sind Anforderungen aus der Notenbildungsverordnung die für verschiedene Fächerarten gelten müssen.
# Mit der Methode check_limits kann eine Liste aus Leistungsobjekten auf das entsprechende Limit getestet werden.
#
#       
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
    def _check_limits(cls, leistungen):
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

    @classmethod
    def check_limits(cls, leistungen, show_warnings=True):
        checks = cls._check_limits(leistungen)

        if not checks['passed']:
            if show_warnings==True:
                _ = [print(f"Warnung: Zu wenige Leistungen: {limit['sum']}: Anzahl der Leistungen {limit['result']}<{limit['min']}") if not limit['passed'] and limit['softfail'] else None for limit in checks['result']]

            _ = [print(f"Fehler: zu viele Leistungen: {limit['sum']}: Anzahl der Leistungen {limit['result']}>{limit['max']}") for limit in checks['result'] if not limit['passed'] and limit['hardfail']]
            
            if any(not limit['passed'] and limit['hardfail'] for limit in checks['result']):
                raise ValueError("Fehler: zu viele Leistungen")
        
        return checks
    
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
    limits = LimitsGeneric.limits +  [ 
                        {
                         'sum' : [LeistungKA, LeistungKT],
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
##########################################
##########################################

#
#
# Die Klassen für Fächer beinhalten entsprechende Limits und die Bezeichnung des Faches.
#
#
class FachGeneric:
    name = None
    long = None
    limits = None
    @classmethod
    def _get_name(cls):
        if cls.long is not None:
            return cls.long
        return ''
    
    @classmethod
    def __str__(cls):
        return f"Name: {self.name}, Long: {self.long}, Limits: {self.limits}"

    @classmethod
    def __repr__(cls):
        return cls._get_name()

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
    
if __name__ == "__main__":
    # Beispiel
    meine_note_1 = NoteEntity(2.25, system='N')
    meine_note_2 = NoteEntity(2.5, system='N')
    
    meine_leistungen =  [
                        LeistungM(note=meine_note_1, date='2024-05-05'),
                        LeistungKA(note=meine_note_2, date='2024-05-05'),
                        ]
    
    mein_fach = FachM
    
    checks = mein_fach.limits.check_limits(meine_leistungen)
    # pprint.pprint(checks)