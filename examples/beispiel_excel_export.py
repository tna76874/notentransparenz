#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Beispiel Excel Export
"""

from notenbildung.excel import *

ExcelFileLoader("meine_notenliste.xlsx").export()