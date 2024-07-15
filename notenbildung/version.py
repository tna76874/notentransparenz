#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Versioning Classes
"""

import os
import subprocess
from datetime import datetime, timedelta
from dateutil import parser
import argparse
import sys
import requests
sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))
from notenbildung.info import *

class TransparenzPDF:
    def __init__(self, save_dir=None):
        if save_dir is None:
            self.save_dir = os.getcwd()
        else:
            self.save_dir = save_dir

        if not os.path.exists(self.save_dir):
            os.makedirs(self.save_dir)
        
        self.url = f'https://transparenz.hilberg.eu/{PackageInfo.version}/files/tex/notentransparenz.pdf'
        
        self._check_download()

    def _check_download(self):
        try:
            response = requests.head(self.url)
            if response.status_code == 200:
                self._download_file()
            else:
                print("Die Datei ist nicht erreichbar.")
        except requests.ConnectionError:
            print("Verbindung fehlgeschlagen.")

    def _download_file(self):
        response = requests.get(self.url)
        file_name = self.url.split('/')[-1]
        file_path = os.path.join(self.save_dir, file_name)
        with open(file_path, 'wb') as file:
            file.write(response.content)
        print(f"Die Datei wurde erfolgreich heruntergeladen und unter {file_path} gespeichert.")

class GitVersion:
    def __init__(self, path):
        if not os.path.exists(path):
            raise FileNotFoundError(f"Der angegebene Pfad '{path}' existiert nicht.")
        
        self.path = path
        self.change_date = None
        self.commit_hash = None
        self.change_count = 0
        
        self._get_last_change_date()
        self._get_change_count()
        self.write_to_file()

    def _get_last_change_date(self):
        result = subprocess.run(['git', 'log', '-1', '--format=%cd %H', '--date=iso', '--' ,self.path], stdout=subprocess.PIPE)
        last_change_info = result.stdout.decode('utf-8').strip().split()
        last_change_date_str = " ".join(last_change_info[:-1])
        self.commit_hash = last_change_info[-1]
        self.change_date = parser.parse(last_change_date_str)

    def _get_change_count(self):
        from_time = self.change_date.strftime('%Y-%m-%d')
        to_time = (self.change_date + timedelta(days=1)).strftime('%Y-%m-%d')
        result = subprocess.run(['git', 'log', f'--since="{from_time} 00:00:00"', f'--until="{to_time} 00:00:00"', '--format=%cd', '--', self.path], stdout=subprocess.PIPE)
        changes_today = result.stdout.decode('utf-8').strip().split('\n')
        self.change_count = len(changes_today)

    def _get_git_root(self):
        result = subprocess.run(['git', 'rev-parse', '--show-toplevel'], stdout=subprocess.PIPE)
        git_root = result.stdout.decode('utf-8').strip()
        return os.path.abspath(git_root)
    
    def _get_info_file(self):
        return os.path.join(self._get_git_root(), 'notenbildung' ,'info.py')
    
    def checkout_info_file(self):
        subprocess.run(['git', 'checkout', self._get_info_file()])
    
    def write_to_file(self):
        with open(self._get_info_file(), 'w') as f:
            f.write("class PackageInfo:\n")
            f.write(f'    version = "{self.version()}"\n')
            f.write(f'    hash = "{self.commit_hash}"\n')
    
    def version(self):
        return f'{self.change_date.strftime("%Y-%m-%d")}v{int(self.change_count)}'

    def _print(self):
        return self.version()
    
    def __str__(self):
        return self._print()

    def __repr__(self):
        return self._print()

def main():
    parser = argparse.ArgumentParser(description='Get Git version information for a given path')
    parser.add_argument('path', help='Path to the directory to get Git version information for')

    args = parser.parse_args()
    
    version_info = GitVersion(args.path)
    print(version_info.version())

if __name__ == "__main__":
    pass
    self = TransparenzPDF('/tmp')
    # self = GitVersion('../docs/files/')
    # main()