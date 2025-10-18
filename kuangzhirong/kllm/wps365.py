from urllib.parse import urlencode
from typing import Generator, Literal, Type, TypeVar
from dataclasses import dataclass, asdict, fields, is_dataclass
import requests
from pprint import pprint

T = TypeVar('T')

def to_dataclass(data: dict[str, any], dc_cls: Type[T], ) -> T:
    """
    将字典转换为指定的dataclass实例。
    这个函数递归地处理嵌套的dataclass。
    """
    # 准备构造dataclass所需的参数
    init_args = {}
 
    for f in fields(dc_cls):
        if f.name in data:
            field_value = data[f.name]
            field_type = f.type
 
            if is_dataclass(field_type):
                # 如果字段是dataclass，递归调用from_dict处理
                init_args[f.name] = to_dataclass(field_value, field_type)
            elif isinstance(field_value, list):
                # 字段是列表，检查列表项的类型是否为dataclass
                list_item_type = field_type.__args__[0]
                if is_dataclass(list_item_type):
                    init_args[f.name] = [to_dataclass(item, list_item_type) for item in field_value]
                else:
                    init_args[f.name] = field_value
            else:
                # 否则，直接赋值
                init_args[f.name] = field_value
 
    return dc_cls(**init_args)

@dataclass
class FileMeta:
    id:str
    drive_id:str
    name:str
    link_url:str

@dataclass
class User:
    id:str
    avatar:str

@dataclass
class File:
    ctime:int
    drive_id:str
    id:str
    link_id:str
    link_url:str
    mtime:int
    name:str
    parent_id:str
    shared:bool
    size:int
    type:str
    version:int

class Highlights:
    file_name:str = None
    file_content:str = None

@dataclass
class SearchFileResultItem:
    file:File
    highlights:Highlights = None

@dataclass
class SearchFileResult:
    items:list[SearchFileResultItem]
    next_page_token:str
    total:int


@dataclass
class SheetInfo:
    id:int
    index:int
    name:str
    type:str

class Client:
    def __init__(self, wps_sid:str):
        self.__cookies = {
            "wps_sid": wps_sid,
        }

    def __request(self, method:Literal['get', 'post'], url:str, body:dict = None, params:dict = None):
        headers = {
            'Origin': 'https://web.wps.cn'
        }
        resp = requests.request(method, url, cookies=self.__cookies, headers=headers, params=params, json=body)
        rs = resp.json()
        if 'api.wps.cn' in url:
            if rs['code'] != 0:
                raise Exception(f"{rs['code']}: {rs['msg']}")
            return rs['data']
        elif 'www.kdocs.cn' in url:
            if rs['result'] != 'ok':
                raise Exception(f"{rs['result']}: {rs['msg']}")
            return rs
        else:
            raise Exception(f"unsupported enpoint: {url}")
    
    def search_files(self, keyword:str, type:Literal['file_name','content','all'], file_type:Literal['folder','file','shortcut']) -> SearchFileResult:
        data = self.__request('get', 'https://api.wps.cn/v7/files/search', params={'keyword':keyword,'type':type,'file_type':file_type})
        return to_dataclass(data, SearchFileResult)
    
    def get_current_user(self) -> User:
        data = self.__request('get', 'https://api.wps.cn/v7/users/current')
        return User(id=data['id'], avatar=data['avatar'])
        
    def get_file_meta(self, file_id:str) -> FileMeta:
        data = self.__request('get', f'https://api.wps.cn/v7/files/{file_id}/meta')
        return FileMeta(id=data['id'], drive_id=data['drive_id'], name=data['name'], link_url=data['link_url'])
    
    def get_file_download(self, drive_id:str, file_id:str) -> bytes:
        data = self.__request('get', f'https://api.wps.cn/v7/drives/{drive_id}/files/{file_id}/download')
        url = data['url']
        return requests.get(url, cookies=self.__cookies).content
    
    def get_file_content(self, drive_id:str, file_id:str, format:Literal['markdown', 'kdc'], include_elements:list[str] = None) -> any:
        if include_elements:
            include_elements = ','.join(include_elements)
        else:
            include_elements = ""

        params = {
            'format': format,
            'include_elements': include_elements,
        }
        rs = self.__request('get', f'https://api.wps.cn/v7/longtask/drives/{drive_id}/files/{file_id}/content', params=params)
        if format == 'markdown':
            return rs['markdown']
        else:
            return rs
        
    def _get_sheet_id_by_name(self, file_id:str, sheet_name:str) -> int:
        body = {
            "command": "http.et.getSheetsInfo",
            "param": {
            }
        }
        rs = self.__request('post', f'https://www.kdocs.cn/api/v3/office/file/{file_id}/core/execute', body=body)
        for sheet in rs['detail']['sheetsInfo']:
            if sheet['sheetName'] == sheet_name:
                return sheet['sheetId']
        
        raise Exception(f'sheet not found: {sheet_name}')
    
    def get_worksheets(self, file_id:str) -> list[SheetInfo]:
        body = {
            "command": "http.et.getSheetsInfo",
            "param": {
            }
        }
        rs = self.__request('post', f'https://www.kdocs.cn/api/v3/office/file/{file_id}/core/execute', body=body)

        sheets = []
        for sheet in rs['detail']['sheetsInfo']:
            if sheet['sheetType'] == 'et':
                sheets.append(SheetInfo(id=sheet['sheetId'], index=sheet['sheetIdx'], name=sheet['sheetName'], type=sheet['sheetType']))
        return sheets
        
        raise Exception(f'sheet not found: {sheet_name}')

    def update_cell_value(self, file_id:str, sheet_id:int, row_idx:int, col_idx:int, value:str):
        body = {
            "command": "http.et.updateRangeData",
            "param": {
                "sheetId": sheet_id,             
                "rangeData": [
                    {
                        "opType": "formula",      
                        "rowFrom": row_idx,            
                        "rowTo": row_idx,              
                        "colFrom": col_idx,             
                        "colTo": col_idx,               
                        "formula": value     
                    },
                ]
            }
        }
        self.__request('post', f'https://www.kdocs.cn/api/v3/office/file/{file_id}/core/execute', body=body)