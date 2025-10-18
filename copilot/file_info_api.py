import os
import re
import time
import typing
from dataclasses import dataclass

import requests

wps_sid = os.environ["WPS_SID"]
host_test = "120.92.124.158"


class FileInfo:
    content: str
    id: str
    name: str
    ext: str


def get_file_link_id(content):
    pattern = r"\(wps365://files/(.*?)\)"
    match = re.search(pattern, content)
    result = ""
    if match:
        result = match.group(1)
    return result


def get_file_link_id2(content):
    pattern = r'"file_url":\s*".*/l/([^"]+)"'
    match = re.search(pattern, content)
    result = ""
    if match:
        result = match.group(1)
    return result


class Client:
    def __init__(self, wps_sid: str):
        client = requests.session()

        # 设置连接池的大小
        adapter = requests.adapters.HTTPAdapter(pool_connections=50, pool_maxsize=50)
        client.mount("http://", adapter)
        client.mount("https://", adapter)
        # setup cookie
        client.cookies.set("wps_sid", wps_sid, domain=".kdocs.cn")
        client.cookies.set("wps_sid", wps_sid, domain=".wps.cn")
        client.cookies.set("csrf", "123")
        client.headers = {
            "Origin": "https://365.kdocs.cn",
            "Accept": "*/*",
            "Host": "365.kdocs.cn",
        }

        self.client = client
        self.cache = {}

    def get_file_meta(self, file_id):
        body = {
            "fileid": file_id,
        }
        resp = self.client.get(
            f"https://120.92.124.158/api/v7/files/{file_id}/meta",
            json=body,
            verify=False,
        )
        file_meta = None
        try:
            file_meta = resp.json()
            print(file_meta)
            return file_meta.get("data", "")
        except Exception as e:
            raise Exception(
                (
                    f"status_code: {resp.status_code} file_id: {file_id}, err: {e}, body: {resp.text}"
                )
            )

    def get_file_info(self, drive_id: str, file_id: str, format: str = "markdown"):
        params = {
            "format": format,
        }
        resp = self.client.get(
            f"https://120.92.124.158/api/v7/drives/{drive_id}/files/{file_id}/content",
            params=params,
            verify=False,
        )
        # print(2222, resp.text)
        file_info = None
        try:
            file_info = resp.json()
            return file_info.get("data", "")
        except Exception as e:
            raise Exception(
                (
                    f"status_code: {resp.status_code} file_id: {file_id}, err: {e}, body: {resp.text}"
                )
            )

    def get_file_info_long(self, drive_id: str, file_id: str, format: str = "markdown"):
        params = {
            "format": format,
        }
        resp = self.client.get(
            f"https://120.92.124.158/api/v7/longtask/drives/{drive_id}/files/{file_id}/content",
            params=params,
            verify=False,
        )
        # print(2222, resp.text)
        file_info = None
        try:
            file_info = resp.json()
            return file_info.get("data", "")
        except Exception as e:
            raise Exception(
                (
                    f"status_code: {resp.status_code} file_id: {file_id}, err: {e}, body: {resp.text}"
                )
            )


def get_file_infos(save_file_text):
    file_id = get_file_link_id2(save_file_text)
    print("提取出来的文件id：", file_id)
    client = Client(wps_sid=wps_sid)
    file_meta = client.get_file_meta(file_id)
    file_info = client.get_file_info(
        drive_id=file_meta["drive_id"], file_id=file_id, format="markdown"
    )
    print(file_info)
    return {"文件名": file_meta["name"], "文件内容": file_info["markdown"]}


def get_message_file(history: dict):
    result = {}
    user_counter = 0
    start_index = 0
    all_messages = history["data"]["list"]
    for i, x in enumerate(all_messages):
        if x.get("role") is None:
            continue
        if x.get("role") == "user":
            user_counter += 1
        if x.get("type") == "code" and "create_file" in x.get("content"):
            save_file_text = all_messages[i + 1].get("content", "")
            print(save_file_text)
            fileinfo = get_file_infos(save_file_text)
            key = f"第{str(user_counter)}个问题保存的文件"
            if key not in result:
                result[key] = []
            result[key].append(fileinfo)
    print(result)
    return result


import json

if __name__ == "__main__":
    client = Client(wps_sid=os.environ["WPS_SID"])
    r1 = client.get_file_meta("cj5uU7JkA7dl")
    print(r1)
    r = client.get_file_info(
        drive_id="2114685757",
        file_id="cj5uU7JkA7dl",
        format="markdown",
    )
    print(r)
    # with open("test.json", "w", encoding="utf-8") as f:
    #     f.write(json.dumps(r, ensure_ascii=False, indent=2))
    # print(r)
