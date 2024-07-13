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

class NotenberechnungLegacy(NotenberechnungGeneric):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def _calculate(self):       
        # Calculate
        result = Note(datum=self.noten[-1].date)
        verbesserung_enabled = any(note.status._enabled for note in self.noten) and self._v_enabled
        
        # Filtern der Noten nach Art
        noten_ka = self._get_leistung_for_types(LeistungKA, LeistungGFS)
        noten_kt = self._get_leistung_for_types(LeistungKT, LeistungP)
        noten_muendlich = self._get_leistung_for_types(LeistungM)
        
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
    
class Notenberechnung(NotenberechnungGeneric):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def _calculate(self):       
        # Calculate
        result = Note(datum=self.noten[-1].date)
        
        # Filtern der Noten nach Art
        noten_ka = self._get_leistung_for_types(LeistungKA, LeistungGFS)
        noten_kt = self._get_leistung_for_types(LeistungKT, LeistungP)
        noten_muendlich = self._get_leistung_for_types(LeistungM)

        # Ermitteln der Anzahl der verschiedenen Leistungsarten
        n_KA = len(noten_ka)
        n_KT = len(noten_kt)
        n_m = len(noten_muendlich)
                
        # mündliche Note
        m_m = Weight(*noten_muendlich)

        # Randfall: nur mündliche Noten
        if (n_KA + n_KT==0) and n_m>0:
            result.update( gesamtnote=m_m.mean, m_m=m_m.mean)
            return result
        # Randfall: keine Noten
        elif (n_KA + n_KT + n_m == 0):
            return None
        
        # Berechnung der Mittelwerte von KT und KA
        w_s = n_KT * self.w_s0/self.n_KT_0 if n_KT < self.n_KT_0 else self.w_s0
        
        KA = Weight(*noten_ka).set_weight_for_each(1)
        KT = Weight(*noten_kt).set_weight(w_s)

        m_s1 = KA+KT
        w_v3 = abs(m_s1.mean._get_system_range()/self.w_th) if m_s1.mean!=None else None
        
        self._verbesserungen = [ LeistungV(mean=m_s1.mean, status = note.status, system = note.system, w_th = self.w_th, date=note.date) for note in self.noten ]
            
        V = Weight(*self._verbesserungen).set_weight(w_v3)
        
        # schriftliche Note berechnen
        m_s = m_s1+V
        
        # Gesamtnote berechnen
        GN = m_s.set_weight(self.w_sm) + m_m.set_weight(1)        
        
        result.update(m_s1=m_s1.mean, m_s=m_s.mean, gesamtnote=GN.mean, m_m = m_m.mean)
        return result
    
class NotenberechnungSimple(NotenberechnungGeneric):
    def __init__(self, **kwargs):
        kwargs['v_enabled'] = False
        super().__init__(**kwargs)

    def _calculate(self):       
        # Calculate
        result = Note(datum=self.noten[-1].date)
        
        # Filtern der Noten nach Art
        noten_ka = self._get_leistung_for_types(LeistungKA, LeistungGFS)
        noten_kt = self._get_leistung_for_types(LeistungKT, LeistungP)
        noten_muendlich = self._get_leistung_for_types(LeistungM)
        

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
        
        # Berechnung Mittelwert schriftliche Note
        w_s = n_KT * self.w_s0/self.n_KT_0 if n_KT < self.n_KT_0 else self.w_s0
        m_s = (n_KA * m_KA + w_s * m_KT) / (n_KA + w_s)


        # Berechnung der Gesamtnote
        gesamtnote = (self.w_sm * m_s + w_m * m_m) / (self.w_sm + w_m)
                
        result.update(m_s=m_s, m_m = m_m, gesamtnote=gesamtnote)

        return result

if __name__ == "__main__":
    pass
    # Beispiel
    self = Notenberechnung(w_s0=1, w_sm=3, system = 'N', v_enabled=True, w_th = 0.4, fach=FachM)
    self.note_hinzufuegen(art='KA', date = '2024-04-10', note=2.5, status='fertig')
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
    
    check = NotenberechnungLegacy(w_s0=1, w_sm=3, system = 'N', v_enabled=True, w_th = 0.4, fach=FachM)
    check.noten = self.noten
    checknote = check.berechne_gesamtnote()
    print(f'CHECK: {checknote.gesamtnote==gesamtnote.gesamtnote}')
