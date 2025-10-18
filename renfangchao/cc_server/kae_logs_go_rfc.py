import copy
from datetime import datetime, timedelta
import os
import requests
import logging
from kae_util import Kae, kae_cookie, default_config, configs, get_time_data


import re
import json
import time
import traceback

from logger_utils import getLogger

logger = getLogger("kae_logs_go")
# logger = logging


def parse_chunked_body(chunked_body):
    return chunked_body.split("\\r\\n")[1]


def parse_http_log_catch(log_text):
    try:
        return parse_http_log(log_text)
    except Exception as e:
        logger.error(f"parse_http_log error {traceback.format_exception(e)}")
        logger.error(log_text)
        return None


def parse_http_log(log_text):
    # 按双换行符分割请求和响应部分
    logger.info("log_text")
    logger.info(type(log_text))
    log_text = log_text.split("msg=", 1)[1]
    log_text = log_text.split('" func="')[0]
    log_text = log_text.replace("\\r\\n", "\n")
    log_text = log_text.replace("\\\\u003c", "<")

    log_text = log_text.replace("\\\\u003e", ">")
    lines = []

    for line in log_text.split("\n"):
        if line.startswith("{"):
            try:
                l = line.replace('\\"', '"')
                l = l.replace('\\"', '"')
                l = json.loads(l)
                lines.append(json.dumps(l, ensure_ascii=False, indent=4))
            except Exception as e:
                lines.append(line)
        else:
            lines.append(line)
    documents = []
    patterns = [
        r"<document_content>(.*?)</document_content>",
        r"<document>(.*?)</document>",
    ]
    for line in lines:
        for pattern in patterns:
            matches = re.findall(pattern, line, flags=re.DOTALL)
            if matches:
                for match in matches:
                    # print(111, match)
                    # Replace the matched content with a placeholder
                    doc = match.replace("\\\\n", "\n")
                    doc = doc.replace("\\n", "\n")
                    documents.append(doc)
            # else:
        #     lines_new.append(line)
    # with open("k_logs_doc.txt", "w", encoding="utf8") as f:
    #     f.write("\n\n\n\n".join(documents))
    docs = "-----document_content-------".join(documents)
    log_text = "\n".join(lines)
    logger.info(log_text)

    return log_text, docs


# Add main method for testing
if __name__ == "__main__":
    # Create a Kae instance for the "gray" environment
    kae = Kae("beta", logger=logger, parse_http_log_catch=parse_http_log_catch)

    result = kae.get_session_reqs_raw(
        " tokens ",
        delta_time=100000,
        wait=0,
    )
    # result = [r for r in result if r["request"]["url"].startswith("/kas")]
    # # Print the result
    # print("Logs retrieved:")
    r0 = [r[0] for r in result]
    r1 = [r[1] for r in result]
    r0 = "\n\n".join(r0)
    r1 = "\n-----reqs------\n".join(r1)
    with open("k_logs_go_rfc.txt", "w", encoding="utf8") as f:
        f.write(r0)
    with open("k_logs_doc_rfc.txt", "w", encoding="utf8") as f:
        f.write(r1)
    # print(r)
