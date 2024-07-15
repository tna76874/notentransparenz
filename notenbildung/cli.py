#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CLI
"""
import os
import sys
import argparse
sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))
from notenbildung.excel import *

def main():
    parser = argparse.ArgumentParser(description='Noten aus einer Excel-Datei berechnen und exportieren')
    parser.add_argument('file', type=str, help='Dateipfad der Excel Datei')
    
    args = parser.parse_args()
    
    excel_loader = ExcelFileLoader(args.file)
    excel_loader.export()

if __name__ == "__main__":
    main()
