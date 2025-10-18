import re
import os
import pandas as pd
from typing import Generator, Dict
from .wps365 import Client

class Row(dict):
    def __init__(self, d):
        super().__init__(d)

    def __setitem__(self, key, val):
        self.update(key, val)

    def update(self, key, val):
        raise NotImplementedError('')


def _load_kdocs(link_id:str, sheet_name:str, wps_sid:str) -> Generator[Row,None,None]:
    wps365 = Client(wps_sid)
    meta = wps365.get_file_meta(link_id)
    _, ext = os.path.splitext(meta.name)
    if ext != '.xlsx':
        raise TypeError(f'unsupported file: {meta.name}')
    
    worksheets = wps365.get_worksheets(link_id)
    sheet_id = None
    if sheet_name == '':
        sheet_id = worksheets[0].id
    else:
        for s in worksheets:
            if s.name == sheet_name:
                sheet_id = s.id
                break
        if sheet_id is None:
            raise TypeError(f'sheet not found: {sheet_name}')

    file_content = wps365.get_file_download(meta.drive_id, meta.id)
    df = pd.read_excel(file_content)

    for i, row in df.iterrows():
        class RowWrapper(Row):
            def update(self, key, val):
                col_idx = df.columns.get_loc(key)
                wps365.update_cell_value(link_id, sheet_id, i + 1, col_idx, val)
        
        yield RowWrapper(row.to_dict())

def _load_excel(path:str, sheet_name:str) -> Generator[Row,None,None]:
    file = pd.ExcelFile(path)
    if sheet_name == '':
        sheet_name = file.sheet_names[0]

    df = pd.read_excel(file, sheet_name=sheet_name)
    file.close()

    for i, row in df.iterrows():
        class RowWrapper(Row):            
            def update(self, key, val):
                df.iloc[i][key] = val
                df.to_excel(path, sheet_name, index=False)

        yield RowWrapper(row.to_dict())

    df.to_excel(path, sheet_name, index=False)

def load_dataset(url:str, sheet_name:str = '', **kwargs) -> Generator[Row,None,None]:
    if m := re.match(url, "https://kdocs.cn/l/(\w+)"):
        ds = _load_kdocs(m[1], sheet_name, kwargs['wps_sid'])
    else:
        ds = _load_excel(url, sheet_name)
    
    for row in ds:
        yield row

