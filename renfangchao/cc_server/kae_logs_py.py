import copy
from datetime import datetime, timedelta
import requests
import logging

from kae_util import Kae, kae_cookie, default_config, configs, get_time_data


from logger_utils import getLogger
import json

logger = getLogger("kae_logs_py")


# logger = logging
def parse_http_log_catch(log_text):
    try:
        return parse_http_log(log_text)
    except Exception as e:
        logger.error(f"parse_http_log error {e}")
        return None


def parse_http_log(log_text):
    # 按双换行符分割请求和响应部分
    logger.info("log_text")
    logger.info(log_text)
    http_text = log_text.split("[request]\\n")[1]
    request_text, response_text = http_text.split("[response]\\n", 1)
    request_text = request_text.strip()
    response_text = response_text.strip()
    request_line, request_headers, request_body = request_text.split("\\n\\n", 2)
    # 解析请求部分
    # logger.error(111, request_line)
    # logger.error(666, request_headers)
    # logger.error(777, request_body)
    # request_body = request_body.replace("\\n", "")
    method, url = request_line.split(" ", 2)[:2]  # 只需要前两个部分
    headers = {}
    request_headers = request_headers.replace("\\n", "\n")
    for line in request_headers.split("\n"):
        if line.strip():  # 跳过空行
            key, value = line.split(": ", 1)
            headers[key] = value

    # 解析请求体（如果存在）
    req_body = None
    if request_body:
        if request_body.endswith("\\n"):
            request_body = request_body[:-2]
        req_body = json.loads(request_body)

    # 解析响应部分
    # print(2222,response_text)
    if "\\n\\n" in response_text:
        response_lines, response_body = response_text.split("\\n\\n", 1)
    else:
        response_lines = response_text
        response_body = None
    # response_lines = response_lines.replace("\\n","\n")
    # print(3333,response_lines)
    response_lines = response_lines.split("\\n")
    # print(4444,response_lines)
    response_status = response_lines[0].split(" ")[0]
    response_headers = {}
    for line in response_lines[1:]:
        if line.strip():  # 跳过空行
            key, value = line.split(": ", 1)
            response_headers[key] = value
    res_body = None
    if response_body:
        if response_body.endswith("\\n"):
            response_body = response_body[:-2]
        res_body = json.loads(response_body)
    # 返回解析结果
    return {
        "request": {
            "method": method,
            "url": url,
            "headers": headers,
            "body": req_body,
            "raw": request_text,
        },
        "response": {
            "status": response_status,
            "headers": response_headers,
            "body": res_body,
            "raw": response_text,
        },
    }


# Add main method for testing
if __name__ == "__main__":
    # Create a Kae instance for the "gray" environment
    kae = Kae("gray", logger=logger, parse_http_log_catch=parse_http_log_catch)

    result = kae.get_session_reqs_py("538845300647795063", 10000, wait=0)

    # # Print the result
    # print("Logs retrieved:")
    with open("k_logs_py.json", "w", encoding="utf8") as f:
        f.write(json.dumps(result, ensure_ascii=False, indent=4))
    print(json.dumps(result, ensure_ascii=False, indent=4))
