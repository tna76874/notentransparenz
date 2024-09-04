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
    parser = argparse.ArgumentParser(description='Get Git version information for a given path')
    parser.add_argument('path', help='Path to the directory to get Git version information for')

    args = parser.parse_args()
    
    version_info = GitVersion(args.path)
    print(version_info.version())

if __name__ == "__main__":
    main()
