import os

import requests
import urllib3

# 禁用SSL警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
from urllib.parse import ParseResult, urlparse, urlunparse

from utils import getLogger

logger = getLogger(os.path.splitext(os.path.basename(__file__))[0])
from dotenv import load_dotenv

load_dotenv()


def get_file_id(url):
    parsed_url = urlparse(url)
    new_url = parsed_url._replace(query="")
    return urlunparse(new_url).split("/")[-1]  # type: ignore


class FileParser:
    def __init__(self, wps_sid: str, is_test: bool = False):
        client = requests.session()

        # 全局禁用SSL验证
        client.verify = False
        # setup cookie
        client.cookies.set("wps_sid", wps_sid, domain=".kdocs.cn")
        client.cookies.set("wps_sid", wps_sid, domain=".wps.cn")
        client.cookies.set("csrf", "123")
        client.headers = {
            "Origin": "https://365.kdocs.cn",
            "Accept": "*/*",
            "Host": "365.kdocs.cn",
        }

        if is_test:
            self.host = "120.92.124.158"
        else:
            self.host = "365.kdocs.cn"

        self.client = client

    def get_file_meta(self, file_id):
        body = {
            "fileid": file_id,
        }
        resp = self.client.get(
            f"https://{self.host}/api/v7/files/{file_id}/meta",
            json=body,
        )
        logger.info(f"获取文件信息返回结果: {resp.text}")
        file_meta = None
        try:
            file_meta = resp.json()
            logger.info(f"{file_meta}")
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
            f"https://{self.host}/api/v7/drives/{drive_id}/files/{file_id}/content",
            params=params,
        )
        logger.info(f"解析文件返回结果: {resp.text}")
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
            f"https://{self.host}/api/v7/longtask/drives/{drive_id}/files/{file_id}/content",
            params=params,
        )
        logger.info(f"解析文件返回结果: {resp.text}")
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

    def get_file_infos(self, url):
        file_id = get_file_id(url)
        logger.info(f"提取出来的文件id：{file_id}")
        file_meta = self.get_file_meta(file_id)
        file_info = self.get_file_info_long(
            drive_id=file_meta["drive_id"], file_id=file_id, format="markdown"  # type: ignore
        )
        logger.info(f"{file_info}")
        return {"文件名": file_meta["name"], "文件内容": file_info["markdown"]}


if __name__ == "__main__":
    url = "https://365.kdocs.cn/l/ckuCK42YfOfR"
    wps_sid = os.environ["WPS_SID_TEST"]
    fp = FileParser(wps_sid, is_test=True)
    r1 = fp.get_file_infos(url)

    logger.info(f"111, {r1}")
