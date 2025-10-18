from logger_utils import getLogger
import time

logger = getLogger("kae_logs_only")
from renfangchao.cc_server.kae_util import Kae


def parse_http_log_catch():
    pass


import json


def parse(log):
    try:
        # 找到 HTTP body 开始的标志
        body_start = log.index("{")
        body_end = log.rindex("}")
        http_body = log[body_start : body_end + 1]
        http_body = http_body.replace('\\"', '"')
        print("HTTP Body:", http_body)
        # 解析 JSON 数据
        body_json = json.loads(http_body)

        return body_json
    except ValueError as e:
        print("解析错误：", log, e)
        return None


if __name__ == "__main__":
    with open("./renfangchao/cc_server/trace_ids.txt", "r", encoding="utf8") as f:
        trace_ids = f.readlines()
    trace_ids = [trace_id.strip() for trace_id in trace_ids]
    kae = Kae("goprod", logger=logger, parse_http_log_catch=parse_http_log_catch)
    qs = []
    for trace_id in trace_ids:
        time.sleep(1)
        logs = kae.get_session_logs_only(f"{trace_id}  AND Mozilla", delta_time=5000)
        log = [log for log in logs if "client request body" in log][0]
        jsonlog = parse(log)
        j = json.dumps(jsonlog, ensure_ascii=True)
        # qs.append(json.dumps(jsonlog, ensure_ascii=False))
        with open("./renfangchao/cc_server/questions.jsonl", "a", encoding="utf8") as f:
            f.write(j + "\n")
