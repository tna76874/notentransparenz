#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Beispiel: Notenberechnung
"""
from notenbildung.nvo import *

leistungen_ka =  [
                  LeistungKA(note=NoteEntity(2, system=SystemN), date='2024-05-05'),
                  LeistungKA(note=NoteEntity(2, system=SystemN), date='2024-05-05'),
                  LeistungGFS(note=NoteEntity(2, system=SystemN), date='2024-05-05'),
                 ]

leistungen_kt =  [
                  LeistungKT(note=NoteEntity(2, system=SystemN), date='2024-05-05'),
                  LeistungKT(note=NoteEntity(2, system=SystemN), date='2024-05-05'),
                 ]

leistungen_m =  [
                  LeistungM(note=NoteEntity(1, system=SystemN), date='2024-05-05'),
                  LeistungM(note=NoteEntity(1, system=SystemN), date='2024-05-05'),
                 ]

KA = Weight(*leistungen_ka).normalize()
KT = Weight(*leistungen_kt).set_weight(1)

ms1 = (KA+KT)
w_th = 0.4
w_v3 = abs(ms1.mean._get_system_range()/w_th) if ms1.mean!=None else None


leistungen_v =  [
                  LeistungV(mean=ms1.mean, status = 'fertig', system = SystemN, w_th = w_th, date='2024-05-05'),
                  LeistungV(mean=ms1.mean, status = 'fehlt', system = SystemN, w_th = w_th, date='2024-05-05'),
                  LeistungV(mean=ms1.mean, status = '---', system = SystemN, w_th = w_th, date='2024-05-05'),
                  LeistungV(mean=ms1.mean, status = 'uv', system = SystemN, w_th = w_th, date='2024-05-05'),
                ]
V = Weight(*leistungen_v).set_weight(w_v3)

m_s = ms1+V

M = Weight(*leistungen_m)
GN = m_s.set_weight(4) + M.set_weight(1)
print(GN)
print(GN.calculate_percents())