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
from notenbildung.version import *

def main():
    parser = argparse.ArgumentParser(description=f'Notentransparenz CLI - Version {PackageInfo.version}')
    parser.add_argument('-f', '--file', type=str, help='Dateipfad der Excel Datei')
    parser.add_argument('-d', '--download', action='store_true', help='Dokument zur Notentransparenz herunterladen')
    
    args = parser.parse_args()
    
    if args.file:
        excel_loader = ExcelFileLoader(args.file)
        excel_loader.export()
        
    if args.download:
        TransparenzPDF()

if __name__ == "__main__":
    main()
