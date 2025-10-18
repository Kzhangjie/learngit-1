import requests
import hashlib
import time
import hashlib
from requests.models import PreparedRequest
import os
import pandas
import json
import asyncio
import aiohttp

sk = "mN3kxczhFd9JksaHr4dEU3iwErqmdsa6"
ip = 'https://10.13.34.11'
url = 'https://10.13.34.11/api/aigc/developer/testxl'

headers = {
    'Host': 'web.wps.cn',
    'Cookie': 'solution_branch=solution-amd-test-et-rw',
    'Access-Id': 'weboffice',
    'Authorization': '',
    'Date': '1722422514',
    'Content-Md5': 'xxxxx',
}


def sign(reqmd5, contenttype, date):
    hashSum = hashlib.sha1()
    hashSum.update(sk.encode('utf-8'))
    hashSum.update(reqmd5.encode('utf-8'))
    hashSum.update(contenttype.encode('utf-8'))
    hashSum.update(date.encode('utf-8'))
    return hashSum.hexdigest()


def get_md5_from_file_path(path: str) -> str:
    with open(path, 'rb') as f:
        files = {
            'file': f
        }
        req = PreparedRequest()
        req.prepare(method='POST', url=url, headers=headers, files=files)

        body_md5 = hashlib.md5(req.body).hexdigest()
        return body_md5


def get_date() -> str:
    timestamp = str(int(time.time()))
    return timestamp


def add_query_params(url, params):
    from urllib.parse import urlencode, urljoin, urlparse, parse_qsl
    # 解析URL
    url_parts = list(urlparse(url))

    # 解析已有的查询参数
    query = dict(parse_qsl(url_parts[4]))

    # 更新查询参数
    query.update(params)

    # 编码查询参数
    url_parts[4] = urlencode(query)

    # 重新组合URL
    return urljoin(url, url_parts[2] + '?' + url_parts[4])


def full_url(sheet_name: str = None, range: str = None) -> str:
    map = {}
    if sheet_name:
        map['sheet_name'] = sheet_name
    if range:
        map['range'] = range

    u = add_query_params(url, map)
    return u


def resultMaping(json) -> dict[str, pandas.DataFrame]:
    # 存储DataFrame的字典
    sheets = {}

    # 遍历每个sheet
    for sheet in json['sheets']:
        sheet_name = sheet['sheet_name']
        table_data = sheet['table']['data']
        headers = sheet['table']['headers']

        transposed_data = [list(row) for row in zip(*table_data)]
        # 将表格数据转换为DataFrame
        if headers:
            df = pandas.DataFrame(transposed_data[1:], columns=transposed_data[0])
        else:
            df = pandas.DataFrame(transposed_data)

        # 将DataFrame存储在字典中
        sheets[sheet_name] = df
    return sheets


def v4ResultMapping(json) -> dict[str, pandas.DataFrame]:
    sheets = {}

    for sheet in json['sheets']:
        sheet_name = sheet['name']
        table_data = sheet['data']
        transposed_data = [list(row) for row in zip(*table_data)]
        df = pandas.DataFrame(transposed_data)

        sheets[sheet_name] = df
    return sheets


def v4JsonRead(path: str) -> dict[str, pandas.DataFrame] | None:
    try:
        with open(path, 'r') as f:
            j = json.load(f)
            return v4ResultMapping(j)
    except Exception:
        return None


async def asyncxl(path: str, sheets_name: str = None, range: str = None) -> dict[str, pandas.DataFrame]:
    j = v4JsonRead(path)
    if j:
        return j

    h = headers.copy()
    body_md5 = get_md5_from_file_path(path)
    h['Content-Md5'] = body_md5

    d = get_date()
    h['Date'] = d

    s = sign(body_md5, 'multipart/form-data', d)
    h['Authorization'] = 'aigc:' + s

    u = url

    map = {}
    if sheets_name:
        map['sheet_name'] = sheets_name
    if range:
        map['range'] = range

    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers, params=map, data={'file': open(path, 'rb')},
                                ssl=False) as response:
            if response.status != 200:
                print(response.headers)
                raise Exception(await response.text())
            j = await response.json()
            return resultMaping(j)


async def async_save_as(source: str, dst: str):
    content = await asyncxl(source)
    with pandas.ExcelWriter(dst) as writer:
        for sheet_name, df in content.items():
            df.to_excel(writer, sheet_name=sheet_name, index=False, header=False)


def xl(path: str, sheets_name: str = None, range: str = None) -> dict[str, pandas.DataFrame]:
    j = v4JsonRead(path)
    if j:
        return j

    h = headers.copy()
    body_md5 = get_md5_from_file_path(path)
    h['Content-Md5'] = body_md5

    d = get_date()
    h['Date'] = d

    s = sign(body_md5, 'multipart/form-data', d)
    h['Authorization'] = 'aigc:' + s

    u = url

    map = {}
    if sheets_name:
        map['sheet_name'] = sheets_name
    if range:
        map['range'] = range

    with open(path, 'rb') as f:
        files = {
            'file': f
        }
        req = PreparedRequest()
        req.prepare(method='POST', url=u, headers=h, files=files, params=map)
        response = requests.session().send(req, verify=False)

        if response.status_code != 200:
            print(response.headers)
            raise Exception(response.text)
        j = response.json()
        return resultMaping(j)


def save_as(source: str, dst: str):
    save_path = dst + ".xlsx"
    content = xl(source)
    if content != {}:
        with pandas.ExcelWriter(save_path, engine="openpyxl") as writer:
            for sheet_name, df in content.items():
                df.to_excel(writer, sheet_name=sheet_name, index=False, header=False)