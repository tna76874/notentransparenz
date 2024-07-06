#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Beispiel Excel
"""

from notenbildung.notenbildung import *

noten = Notenberechnung(w_s0=1, w_sm=3, system = 'N', v_enabled=True)
noten.add_from_excel('data.xlsx')

gesamtnote = noten.berechne_gesamtnote()
print(gesamtnote)
noten.plot_time_series()