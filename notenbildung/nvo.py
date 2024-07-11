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
    pprint.pprint(checks)