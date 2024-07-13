#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Beispiel: Notenberechnung
"""
from notenbildung.nvo import *

leistungen_ka =  [
                  LeistungKA(note=NoteEntity(2, system='N'), date='2024-05-05'),
                  LeistungKA(note=NoteEntity(2, system='N'), date='2024-05-05'),
                 ]

leistungen_kt =  [
                  LeistungKT(note=NoteEntity(2, system='N'), date='2024-05-05'),
                  LeistungKT(note=NoteEntity(2, system='N'), date='2024-05-05'),
                 ]

leistungen_m =  [
                  LeistungM(note=NoteEntity(1, system='N'), date='2024-05-05'),
                  LeistungM(note=NoteEntity(1, system='N'), date='2024-05-05'),
                 ]

KA = Weight(*leistungen_ka).set_weight_for_each(1)
KT = Weight(*leistungen_kt).set_weight(0.5)

ms1 = (KA+KT)
w_th = 0.4

leistungen_v =  [
                  LeistungV(mean=ms1.mean, status = 'fertig', system = 'N', w_th = w_th, date='2024-05-05'),
                  LeistungV(mean=ms1.mean, status = 'fehlt', system = 'N', w_th = w_th, date='2024-05-05'),
                  LeistungV(mean=ms1.mean, status = '---', system = 'N', w_th = w_th, date='2024-05-05'),
                  LeistungV(mean=ms1.mean, status = 'uv', system = 'N', w_th = w_th, date='2024-05-05'),
                ]
V = Weight(*leistungen_v)
w_v3 = abs(V.mean._get_system_range()/w_th)

m_s = ms1+V.set_weight(w_v3)

M = Weight(*leistungen_m)
GN = m_s.set_weight(3) + M.set_weight(1)