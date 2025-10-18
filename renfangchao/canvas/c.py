import streamlit as st
import requests
import time
import traceback
from utils import getLogger
import os
import zipfile
import json

logger = getLogger(os.path.splitext(os.path.basename(__file__))[0])
format_key_dict = {
    "markdown": "markdown",
    "kdc": "doc",
    "plain": "plain",
}
from urllib.parse import urlparse, urlunparse, ParseResult


def wps_export_pdf(fileinfo, format="markdown") -> dict:

    page_start = fileinfo.get("page_start")
    page_end = fileinfo.get("page_end")
    file_name = fileinfo.get("name")
    file_content = fileinfo.get("content")
    weboffice_branch = fileinfo.get("weboffice_branch")
    disable_pdf_detection = fileinfo.get("disable_pdf_detection", False)
    enable_core_export_md = fileinfo.get("enable_core_export_md", False)
    enable_upload_medias = fileinfo.get("enable_upload_medias", True)
    include_elements = fileinfo.get("include_elements", "textbox,para,table")
    enable_multi_threading = str(fileinfo.get("enable_multi_threading", False)).lower()
    enable_html_format_table = str(
        fileinfo.get("enable_html_format_table", False)
    ).lower()
    convert_options = {
        "disable_pdf_detection": disable_pdf_detection,
        "enable_core_export_md": enable_core_export_md,
        "enable_upload_medias": enable_upload_medias,
        "fixed_chunk_size": fileinfo.get("fixed_chunk_size", True),
    }
    if page_start and page_end:
        page_range = f"{page_start}-{page_end}"
        convert_options["page_range"] = page_range
    is_test = fileinfo.get("is_test")
    api = "https://api.wps.cn/v7/longtask/exporter/export_file_content"
    headers = {}
    if is_test:
        api = "https://10.13.34.11/office-exporter/v7/exporter/export_file_content"
        headers = {
            "host": "www.kdocs.cn",
            "Cookie": f"weboffice_branch={weboffice_branch}",
        }
        if weboffice_branch == "doc-exporter-migrations":
            headers["weboffice-branch-env"] = "doc-exporter-migrations"
    d = {
        "format": format,
        "filename": file_name,
        "include_elements": include_elements,
        "enable_multi_threading": enable_multi_threading,
        "convert_options": json.dumps(convert_options),
        "enable_html_format_table": enable_html_format_table,
    }
    print("kdc请求参数", json.dumps(d, ensure_ascii=False))

    # response = requests.post(
    #     api,
    #     data=d,
    #     files={
    #         "form_file": (file_name, file_content),
    #     },
    #     headers=headers,
    #     verify=False,
    # )
    req = requests.Request(
        "POST",
        api,
        data=d,
        files={
            "form_file": (file_name, file_content),
        },
        headers=headers,
        # verify=False,
    )

    # 使用 prepare 准备请求
    prepared = req.prepare()

    # 创建一个 Session 对象
    with requests.Session() as session:
        # 发送准备好的请求
        start_time = time.time()
        response = session.send(prepared, verify=False)

    is_json = False
    response_data = ""
    error_msg = ""
    try:
        response_data = response.json()
        is_json = True
    except Exception as e:
        print(traceback.format_exception(e))
        response_data = "报错了:" + response.text
        error_msg = response.text
    # print(f"{is_json}文件路径---",filepath,"response:",response.text)
    end_time = time.time()
    # print(111, response.text)
    # 打印请求信息
    # logger.info(f"Request URL: {prepared.url}")
    # logger.info(f"Request Headers: {prepared.headers}")
    # logger.info(f"Request Body: {prepared.body}")

    # # 打印响应信息
    # logger.info(f"Response Status Code: {response.status_code}")
    # logger.info(f"Response Body: {response.text}")
    cost_time = end_time - start_time
    success = False
    logger.info(f"response_data: {response_data}")
    attachment_url = ""
    src_format_detail = ""
    try:
        if is_json:
            key = format_key_dict.get(format)
            data = response_data["data"].get(key, "")
            if key == "doc":
                data = json.dumps(data, ensure_ascii=False, indent=4)
            attachment_url = response_data["data"].get("attachment_url", "")
            src_format_detail = response_data["data"].get("src_format_detail", "")
            success = True
        else:
            data = response_data
            success = False
    except Exception as e:
        print(traceback.format_exception(e))
        if response:
            data = response.text[:30000]
        else:
            data = "报错了:" + response.text
        # data = "\n".join(traceback.format_exception(e))
    logger.info(f"attachment_url: {attachment_url}")

    return {
        "data": data,
        "others": {
            "src_format_detail": src_format_detail,
            "attachment_url": attachment_url,
        },
        "error_msg": error_msg,
        "cost_time": cost_time,
        "start_time": start_time,
        "end_time": end_time,
        "success": success,
    }


fileinfo = {
    "name": "test.pptx",
    "content": open(
        r"D:\download\样张\wpp\综合样张_2k\5 进出口货物报关单申报项目介绍（检务共享版）.pptx",
        "rb",
    ).read(),
    "weboffice_branch": "doc-exporter-migrations",
    "is_test": True,
}

r = wps_export_pdf(fileinfo, format="kdc")
with open("test.json", "w") as f:
    f.write(r["data"])
