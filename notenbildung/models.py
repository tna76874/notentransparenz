#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Notenberechnung Modelle
"""
import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))
from notenbildung.nvo import *
from notenbildung.lerngruppenverwaltung import *
    
class Notenberechnung(NotenberechnungGeneric):
    _leistungs_types = {
                            'KA' : [LeistungKA, LeistungGFS, LeistungKAP],
                            'KT' : [LeistungKT, LeistungS, LeistungKTP],
                            'm'  : [LeistungM],
                            }
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def _calculate(self):       
        # Calculate
        result = Note(datum=self.noten[-1].date, system=self.system)
        
        verbesserung_is_enabled = any(note.status._enabled for note in self.noten) and self._v_enabled
        
        # Filtern der Noten nach Art
        noten_ka = self._get_leistung_for_types(*self._leistungs_types.get('KA'))
        noten_kt = self._get_leistung_for_types(*self._leistungs_types.get('KT'))
        noten_muendlich = self._get_leistung_for_types(*self._leistungs_types.get('m'))
        
        # Ermitteln der Anzahl der verschiedenen Leistungsarten
        n_KA = len(noten_ka)
        n_KT = len(noten_kt)
        n_m = len(noten_muendlich)

        # Validate count
        if len(self.noten)!=n_KA+n_KT+n_m:
            raise ValueError("Counting Error")
                
        # mündliche Note
        m_m = Weight(*noten_muendlich)

        # Randfall: nur mündliche Noten
        if (n_KA + n_KT==0) and n_m>0:
            result.update(gesamtnote=m_m.mean, m_m=m_m.mean)
            return result
        # Randfall: keine Noten
        elif (n_KA + n_KT + n_m == 0):
            return None
        
        # Berechnung der Mittelwerte von KT und KA
        w_s = n_KT * self.w_s0/self.n_KT_0 if n_KT < self.n_KT_0 else self.w_s0
        
        KA = Weight(*noten_ka).set_weight_for_each(1)
        KT = Weight(*noten_kt).set_weight(w_s)

        m_s1 = KA+KT
        
        if (verbesserung_is_enabled==True) and (self.w_th != 0):
            w_v3 = abs(m_s1.mean._get_system_range()/self.w_th) if (m_s1.mean!=None) else None
            self._verbesserungen = [ LeistungV(mean=m_s1.mean, status = note.status, system = note.system, w_th = self.w_th, date=note.date) for note in self.noten ]
            V = Weight(*self._verbesserungen).set_weight(w_v3)
        
            # schriftliche Note berechnen
            m_s = m_s1+V
        else:
            # schriftliche Note
            m_s = m_s1
        
        # Gesamtnote berechnen
        GN = m_s.set_weight(self.w_sm) + m_m.set_weight(1)        
        
        result.update(m_s1=m_s1.mean, m_s=m_s.mean, gesamtnote=GN.mean, m_m = m_m.mean)
        return result
    
class NotenberechnungSimple(NotenberechnungGeneric):
    _leistungs_types = {
                            'KA' : [LeistungKA, LeistungGFS],
                            'KT' : [LeistungKT],
                            'm'  : [LeistungM],
                            }
    def __init__(self, **kwargs):
        kwargs['v_enabled'] = False
        super().__init__(**kwargs)


    def _calculate(self):       
        # Calculate
        result = Note(datum=self.noten[-1].date, system=self.system)
        
        # Filtern der Noten nach Art
        noten_ka = self._get_weight_for_types(*self._leistungs_types.get('KA'))
        noten_kt = self._get_weight_for_types(*self._leistungs_types.get('KT'))
        noten_muendlich = self._get_weight_for_types(*self._leistungs_types.get('m'))

        
        # Randfall: nur mündliche Noten
        if (noten_ka._n + noten_kt._n==0) and noten_muendlich._n>0:
            result.update( gesamtnote=noten_muendlich.mean, m_m=noten_muendlich.mean )
            return result
        # Randfall: keine Noten
        elif (noten_ka._n + noten_kt._n + noten_muendlich._n == 0):
            return None
        
        # Berechnung Mittelwert schriftliche Note
        w_s = noten_kt._n * self.w_s0/self.n_KT_0 if noten_kt._n < self.n_KT_0 else self.w_s0
        noten_ka.normalize()
        noten_kt.set_weight(w_s)
        m_s = noten_ka + noten_kt
        
        m_s.set_weight(self.w_sm)
        noten_muendlich.set_weight(1)
        
        # Berechnung der Gesamtnote
        gesamtnote = m_s + noten_muendlich
                
        result.update(m_s=m_s.mean, m_m = noten_muendlich.mean, gesamtnote=gesamtnote.mean)

        return result

if __name__ == "__main__":
    pass
    # Beispiel
    self = Notenberechnung(w_s0=1, w_sm=3, system = SystemN, v_enabled=True, w_th = 0.4, fach=FachM)
    self.note_hinzufuegen(art='KA', date = '2024-04-10', note=2.5, status='fertig')
    self.note_hinzufuegen(art='KA', date = '2024-04-15', note=2.5, status='fertig')
    self.note_hinzufuegen(art='KA', date = '2024-03-01', note=4, status='fertig')
    self.note_hinzufuegen(art='GFS', date = '2024-03-05', note=3.25)
    self.note_hinzufuegen(art='KA', date = '2024-03-15', note=5, status='uv')
    self.note_hinzufuegen(art='KTP', date = '2024-02-01', note=4)
    self.note_hinzufuegen(art='KT', date = '2024-01-01', note=2.75, status='fehlt')
    self.note_hinzufuegen(art='m', date = '2023-10-05', von = '2023-09-01', note=3.0)
    self.note_hinzufuegen(art='m', date = '2023-12-05', von = '2023-10-06', note=3.25)
    self.note_hinzufuegen(art='m', date = '2024-05-01', von = '2023-12-06', note=3.5)
    
    # self.to(SystemNP)
    
    gesamtnote = self.berechne_gesamtnote()
    print(gesamtnote)
    self.plot_time_series()
    
    check = NotenberechnungLegacy(w_s0=1, w_sm=3, system = SystemN, v_enabled=True, w_th = 0.4, fach=FachM)
    check.noten = self.noten.copy()
    checknote = check.berechne_gesamtnote()
    if checknote.gesamtnote!=gesamtnote.gesamtnote:
        raise ValueError("Check failed")

