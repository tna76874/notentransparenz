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
# Defintion von Notensystemen
#
#
class SystemGeneric:
    good = None
    bad = None
    name = None
    _convert_to = []

    @classmethod
    def add_convert_to(cls, *new_convert_to):
        cls._convert_to = list(set(list(cls._convert_to) + list(new_convert_to)))
    
    @classmethod
    def _value_to_norm(cls, z):
        if z == None:
            return None
        norm = (abs((z - cls.bad)) / cls._get_range())
        if not 0 <= norm <= 1:
            raise ValueError("Die normierte Note muss zwischen 0 und 1 liegen")
        return norm

    @classmethod
    def _norm_to_value(cls, norm):
        if norm == None:
            return None
        if not 0 <= norm <= 1:
            raise ValueError("Die normierte Note muss zwischen 0 und 1 liegen")
        if not cls._is_inverted():
            return norm * cls._get_range() + cls.bad
        else:
            return cls.bad - norm * cls._get_range()

    @classmethod
    def _is_inverted(cls):
        return cls.bad>cls.good
            
    @classmethod
    def _get_range(cls):
        return abs(cls.good-cls.bad)

    @classmethod
    def _get_lims(cls):
        lim_min = min(cls.good, cls.bad)
        lim_max = max(cls.good, cls.bad)
        return [lim_min, lim_max]

    @classmethod
    def __str__(cls):
        return cls._print()

    @classmethod
    def __repr__(cls):
        return cls._print()

    @classmethod
    def _print(cls):
        return f"{cls.name}"

class SystemN(SystemGeneric):
    name = 'N'
    good = 1
    bad = 6

class SystemNPS(SystemGeneric):
    name = 'N Pseudo'
    good = float(2/3)
    bad = float(5+2/3)

class SystemNP(SystemGeneric):
    name = 'NP'
    good = 15
    bad = 0
    
class SystemNORM(SystemGeneric):
    name = 'norm'
    good = 1
    bad = 0

SystemN.add_convert_to(SystemNORM)
SystemNPS.add_convert_to(SystemNORM, SystemNP, SystemN)
SystemNP.add_convert_to(SystemNORM, SystemNPS)
SystemNORM.add_convert_to(SystemNORM, SystemNP, SystemN, SystemNPS)

##########################################
##########################################
    
#
#
# Default Config Values
#
#

class ConfigNVO:
    w_th = 0.25
    w_s0 = 1
    w_sm = 3
    n_KT_0 = 3
    v_enabled = True
    system = SystemN

    @classmethod
    def update(cls, new_values):
        for key, value in new_values.items():
            if hasattr(cls, key):
                setattr(cls, key, value)

    @classmethod
    def get_config(cls):
        return {
            'w_th': cls.w_th,
            'w_s0': cls.w_s0,
            'w_sm': cls.w_sm,
            'n_KT_0' : cls.n_KT_0,
            'v_enabled': cls.v_enabled,
            'system': cls.system,
        }

##########################################
##########################################

#
#
# NoteEntity stellt sicher, dass eine gültige Zahl als Note übergeben wurde. Es gibt Methoden um entsprechend die Leistung in Text auszugeben.
#
#
class NoteEntity(np.ndarray):
    def __new__(cls, note, system = ConfigNVO.system):
        if not issubclass(system, SystemGeneric):
            raise ValueError(f'Das System muss ein Objekt der SystemGeneric-Klasse sein.')
            
        if note==None:
            note = np.nan
            norm = None
        else:
            sys_min, sys_max = system._get_lims()
            if not sys_min <= note <= sys_max:
                raise ValueError(f'Die Note >{note}< muss zwischen {sys_min} und {sys_max} liegen.')
            norm = system._value_to_norm(note)
        
        obj = np.asarray(float(note)).view(cls)
        obj.system = system
        obj._norm = norm
        return obj

    def to(self, newsystem):
        if not issubclass(newsystem, SystemGeneric):
            raise ValueError(f'Das System muss eine Instanz der SystemGeneric-Klasse sein.')
        
        if newsystem!=self.system:
            if newsystem not in self.system._convert_to:
                raise ValueError(f'{self.system} kann nicht zu {newsystem} kovertiert werden.')
            
            if self.system==SystemNPS and newsystem==SystemN:
                print("WARNING: Inkonsistent System conversion")
                new_note = self
                if new_note<1 or new_note>5.5:
                    new_note = np.round(new_note)
            else:
                new_note = newsystem._norm_to_value(self._norm)
                       
            self.itemset(new_note)
            self.system = newsystem
    
    def _get_system_range(self):
        return self.system._get_range()

    def _round(self,number):
        if number % 1 == 0.5:
            if self.system == SystemN:
                return np.ceil(number)
            elif self.system == SystemNP:
                return np.floor(number)
        else:
            return np.round(number)

    def gerundet(self):
        result = dict()
        Z = self._round(float(self))
        if self.system == SystemN:
            HJ = self._round(float(self) * 4) / 4
            result.update({'HJ': {'v': HJ, 's': self._num_to_string(HJ)}, 'Z': {'v': Z, 's': self._num_to_string(Z, ints=True)}})
        elif self.system == SystemNP:
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
        if self.system == SystemNP:
            return str(int(self._round(note)))
        elif self.system == SystemN:
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
        else:
            raise ValueError("Unknows System")

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
        self._type = []
        
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
        return_weight = Weight(combined).set_type(list(set(self._type+other._type))).set_weight(new_weight)
        return return_weight

    def set_weight(self, w):
        self.w = w if self.mean is not None else None
        return self

    def set_weight_for_each(self, w):
        self.w = w * self._n if self.mean is not None else None
        return self

    def normalize(self):
        self.w = self._n if self.mean is not None else None
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
    def __init__(self, text, due=None):
        self._text = text if text != None else '---'
        self.text = None
        self.due = self._parse_date(due) if due is not None else None
        self._check()
    
    def _check(self):
        self._enabled = True if self._text != "---" else False
        self.status = True if self._text == "fertig" else False if self._text == "fehlt" else None    
        self.text = self._text

        if (self.due is not None) and self._enabled:
            current_date = datetime.now()
            if current_date > self.due and self._text == 'offen':
                self.text = 'fehlt'
                self.status = False
            elif current_date < self.due:
                self.text = f'offen bis {self.due.strftime("%d.%m.%Y")}'
    
    def _disable(self):
        self.text = '---'
        self._text = '---'
        self._check()

    def _parse_date(self, date_str):
        if isinstance(date_str, datetime):
            return date_str
        try:
            return datetime.strptime(date_str, "%Y-%m-%d")
        except (ValueError, TypeError):
            raise ValueError("Ungültiges Datumsformat")

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
        
        self.status = VerbesserungStatus(kwargs.get('status','---'), due = kwargs.get('due'))
        
        self.nr = kwargs.get('nr')
        self._nr = None
        self.von = None
        self.bis = None

    def to(self, newsystem):
        if not issubclass(newsystem, SystemGeneric):
            raise ValueError(f'Das System muss eine Instanz der SystemGeneric-Klasse sein.')
            
        self.note.to(newsystem)     
        self.system = newsystem
        
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
            'due': self.status.due,
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
    _art = 'm'
    _attribut = AttributM
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.status._disable()          
        
        self.von = self._parse_date(kwargs.get('von') or self.date)
        self.bis = self._parse_date(kwargs.get('bis') or self.date)
        
        if self.von > self.bis:
            raise ValueError(f"Ungültiger Zeitraum für die mündlichen noten.")
            
        if self.von != self.bis:
            self._is_punctual = False   

        self._art = 'm'
        self._attribut = AttributM
        
class LeistungKA(LeistungGeneric):
    _art = 'KA'
    _attribut = AttributS
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._art = 'KA'
        self._attribut = AttributS
        
class LeistungGFS(LeistungGeneric):
    _art = 'GFS'
    _attribut = AttributP
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.status._disable()
        self._art = 'GFS'
        self._attribut = AttributP

class LeistungKAP(LeistungGeneric):
    _art = 'KAP'
    _attribut = AttributP
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.status._disable()
        self._art = 'KAP'
        self._attribut = AttributP

class LeistungKT(LeistungGeneric):
    _art = 'KT'
    _attribut = AttributS
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._art = 'KT'
        self._attribut = AttributS

class LeistungS(LeistungGeneric):
    _art = 'S'
    _attribut = AttributS
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.status._disable()
        self._art = 'S'
        self._attribut = AttributS

class LeistungKTP(LeistungGeneric):
    _art = 'KTP'
    _attribut = AttributP
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.status._disable()
        self._art = 'KTP'
        self._attribut = AttributP

class LeistungV(LeistungGeneric):
    _art = 'V'
    _attribut = AttributS
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

        if system==SystemN:
            w_v1 = None if w_d >= 1 else m_h + w_th if w_d < 1 else None
            w_v2 = None if w_d >= 1 else m_h - w_th if w_d < 1 else None
        elif system==SystemNP:
            w_v1 = None if w_d >= 1 else m_h - w_th if w_d < 1 else None
            w_v2 = None if w_d >= 1 else m_h + w_th if w_d < 1 else None
        else:
            raise ValueError("Invalid System Class for Verbesserung.")
        
        count = '---'
        if status._enabled == False or (w_d >= 1):
            kwargs['note'] = NoteEntity(None, system = system)
        else:
            if status.status==None:
                kwargs['note'] = NoteEntity(mean, system = system)
                count = None
            elif status.status==False:
                kwargs['note'] = NoteEntity(w_v1, system = system)
                count = False
            elif status.status==True:
                kwargs['note'] = NoteEntity(w_v2, system = system)
                count = True
            else:
                raise ValueError("Fehler beim Initialisieren des Verbesserungsobjektes")
        
        
        # cleanup kwargs
        if 'due' in kwargs:
            _ = kwargs.pop('due')
            kwargs['status'] = '---'
        
        # init parent class
        super().__init__(**kwargs)
        
        # class parameters
        self.status._disable()
        self.count = count
        self._art = 'V'
        self._attribut = AttributS

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
    def check_limits(cls, leistungen, show_warnings=True, info = {}):
        checks = cls._check_limits(leistungen)
        infoprint = "\n".join([f"{key}: {value}" for key, value in info.items()])

        if not checks['passed']:
            if show_warnings==True:
                _ = [print(f"{infoprint}\nWarnung: Zu wenige Leistungen: {limit['sum']}: Anzahl der Leistungen {limit['result']}<{limit['min']}") if not limit['passed'] and limit['softfail'] else None for limit in checks['result']]

            _ = [print(f"{infoprint}\nFehler: zu viele Leistungen: {limit['sum']}: Anzahl der Leistungen {limit['result']}>{limit['max']}") for limit in checks['result'] if not limit['passed'] and limit['hardfail']]
            
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
    meine_note_1 = NoteEntity(2.25, system=SystemN)
    meine_note_2 = NoteEntity(2.5, system=SystemN)
    
    meine_leistungen =  [
                        LeistungM(note=meine_note_1, date='2024-05-05'),
                        LeistungKA(note=meine_note_2, date='2024-05-05'),
                        ]
    
    mein_fach = FachM
    
    checks = mein_fach.limits.check_limits(meine_leistungen)
    # pprint.pprint(checks)