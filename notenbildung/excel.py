#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Excel Wrapper
"""
import os
import sys
import re
import argparse
sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))
from notenbildung.models import *

class ExcelSheetConfig:
    def __init__(self, df=None, sheet=None):
        self.parse_config = ConfigNVO.get_config()
        self.parse_config.update({'fach' : None})
        self.df = df
        self.sheet = sheet
        self.gruppe = None

        self.test_types = {
            'KA': LeistungKA,
            'KT': LeistungKT,
            'KAP': LeistungKAP,
            'KTP': LeistungKTP,
            'm': LeistungM,
        }
        self.parse_config = ConfigNVO.get_config()
        self.parse_config.update({'fach' : None})
        self.df = df
        self._load_and_validate_dataframe()
        self.parse_config['v_enabled'] = False
        
        self.info = self._parse_sheet_name()
        self.gruppe = LerngruppeEntity(stufe=self.info.get('stufe'), fach=self.parse_config.get('fach'), zug=self.info.get('zug'))
          
        self._init_sid()
    
    def _init_sid(self):
        dates = dict(zip(self.df.iloc[0,3:], self.df.iloc[1,3:]))
        types = {k:self._parse_type_and_number(k) for k in dates.keys()}

        for index in self.df.iloc[2:,0].index:
            sid = self.df.iloc[index,0]
            schueler = SchuelerEntity(sid=sid, vorname=self.df.iloc[index,1], nachname=self.df.iloc[index,2])
            noten = Notenberechnung(**self.parse_config)
            
            for column in range(3, self.df.shape[1]):
                typ_and_nr = types.get(self.df.iloc[0,column], {})
                date = self.df.iloc[1,column]
                note = self.df.iloc[index,column]
                if not pd.isnull(note):
                    noten.leistung_hinzufuegen(typ_and_nr.get('type')(system=self.parse_config.get('system'), note=note, nr=typ_and_nr.get('nr'),date=date))
            schueler.setze_note(noten)
            self.gruppe.update_sid(schueler)
            

    def _parse_type_and_number(self, key):
        match = re.match(r'([A-Za-z]+)(\d+)', key)
        if match:
            return {'type': self.test_types.get(match.group(1)), 'nr' : match.group(2)}
        else:
            return {}

    def _parse_sheet_name(self):
        match = re.search(r'(JGS|JG)?(11|12)|(\d{1})\s*([a-zA-Z])', self.sheet)
        if match:
            if match.group(1):
                stufe = match.group(2)
                zug = None
            elif match.group(3):
                stufe = match.group(3)
                zug = match.group(4)
            return {'stufe' : stufe, 'zug' : zug}
        else:
            return {'stufe' : None, 'zug' : None}
    
    def _load_and_validate_dataframe(self):
        try:
            df = self.df
            df.iloc[1, 3:] = pd.to_datetime(df.iloc[1, 3:])
            
            # Config prüfen
            if not all(df.iloc[i, j].startswith(tuple(list(self.parse_config.keys())+['-'])) for i in range(2) for j in range(3)):
                raise ValueError("In den linken oberen sechs Zellen muss jeweils '-' stehen.")
            
            for i in range(2):
                for j in range(3):
                    cell_value = df.iloc[i, j]
                    for key in self.parse_config.keys():
                        if cell_value.startswith(key):
                            key_value = cell_value.split('=')[-1].strip()
                            self.parse_config[key] = self._convert_and_update_config(key, key_value)

            if not all(isinstance(cell, str) and any(cell.startswith(prefix) and cell[len(prefix):].isdigit() for prefix in self.test_types.keys()) for cell in df.iloc[0, 3:]):
                raise ValueError(f'In der ersten Zeile muss der Test-Typ mit Nummer angegeben sein. Erlaubte Typen: {", ".join(self.test_types.keys())}')

            if not all(isinstance(cell, pd.Timestamp) for cell in df.iloc[1, 3:].values):
                raise ValueError("In der zweiten Zeile muss zu jedem Test ein gültiges Datum angegeben werden. z.B. YYYY-MM-DD")

            if not df.iloc[2:, 0].is_unique:
                raise ValueError("Nicht alle Schüler-IDs in der ersten Zeile sind eindeutig")
            
            # Prüfe ob die Zellen nur numerische werte enthalten
            for i in range(2, df.shape[0]):
                for j in range(3, df.shape[1]):
                    cell_value = df.iloc[i, j]
                    if isinstance(cell_value, str):
                        try:
                            float_value = float(cell_value)
                            df.iloc[i, j] = float_value
                        except ValueError:
                            raise ValueError(f"Der Wert '{cell_value}' in Zeile {i} und Spalte {j} kann nicht in einen Float umgewandelt werden.")

            return df

        except Exception as e:
            print(f"Fehler beim Validieren der Excel-Datei: {e}")
            return None

    def _convert_and_update_config(self, key, value):
        if key == 'w_th' or key == 'w_s0' or key == 'w_sm' or key == 'n_KT_0':
            try:
                value = float(value.replace(',','.'))
            except ValueError:
                raise ValueError(f"Fehler bei der Konvertierung von {key} zu eine Zahl")
        elif key == 'v_enabled':
            if value.lower() == 'true':
                value = True
            elif value.lower() == 'false':
                value = False
            else:
                raise ValueError(f"Fehler bei der Konvertierung von {key} zu bool")
        elif key == 'fach':
            if value == 'M':
                value = FachM
            elif value == 'PH':
                value = FachPH
            else:
                raise ValueError("Erlaubte Fächer sind M und PH")
                
        elif key == 'system':
            if value == 'N':
                value = SystemN
            elif value == 'NP':
                value = SystemNP
            else:
                raise ValueError("Erlaubte Notensysteme sind N und NP")
    
        return value

class ExcelFileLoader:
    def __init__(self, file_path):
        self.file_path = file_path
        self.klassen = []
        self._load_and_validate_excel_file()

    def export(self, typ='pdf'):
        for key, _ in enumerate(self.klassen):
            gruppe = self.klassen[key].gruppe
            dataframe = gruppe.get_dataframe()
            schuljahr = gruppe._get_sj()
            folder_name = os.path.join(os.path.dirname(self.file_path), f'{schuljahr}_{schuljahr+1}')
            if not os.path.exists(folder_name):
                os.makedirs(folder_name)
            file_name = f"{gruppe._name()}_{gruppe.fach.name}.xlsx"
            file_path = os.path.join(folder_name, file_name)
            with pd.ExcelWriter(file_path) as writer:
                dataframe.to_excel(writer, index=False, sheet_name='Gesamt')
                for schueler in gruppe.schueler.values():
                    schueler.get_dataframe().to_excel(writer, index=False, sheet_name=schueler._get_name())
            
            #Export Plots
            for sid in gruppe.schueler.keys():
                file_name = f"{gruppe._name()}_{gruppe.fach.name}_{gruppe.schueler[sid].nachname}_{gruppe.schueler[sid].vorname}"
                file_path = os.path.join(folder_name, file_name)
                gruppe.plot_sid(sid, save=file_path, formats=[typ])
    
    def _generate_nvo_objects(self):
        for idx, _ in enumerate(self.klassen):
            if self.klassen[idx].parse_config.get('fach')==None:
                raise ValueError("Das Fach muss angegeben sein.")
            self.klassen[idx]
        

    def _load_and_validate_excel_file(self):
        try:
            xls = pd.ExcelFile(self.file_path)
            for sheet_name in xls.sheet_names:
                df = pd.read_excel(xls, sheet_name, header=None)
                self.klassen.append(ExcelSheetConfig(df=df, sheet=sheet_name))

        except Exception as e:
            print(f"Fehler beim Laden der Excel-Datei: {e}")
            return None
        
def main():
    parser = argparse.ArgumentParser(description='Noten aus einer Excel-Datei berechnen und exportieren')
    parser.add_argument('file', type=str, help='Dateipfad der Excel Datei')
    
    args = parser.parse_args()
    
    excel_loader = ExcelFileLoader(args.file)
    excel_loader.export()

if __name__ == "__main__":
    self = ExcelFileLoader("../examples/meine_notenliste.xlsx")
    self.export()