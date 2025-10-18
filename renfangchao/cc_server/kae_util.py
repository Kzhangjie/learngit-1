kae_cookie = "wpsqing_autoLoginV1=1; _ku=1; cid=41000207; uid=1388383710; wps_sid=; ajs_anonymous_id=7196f451-bf8d-48b0-b674-6f5f5a60123d; token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6NDM2LCJjb21wYW55X3VzZXJfaWQiOjEzODgzODM3MTAsInBob25lIjoiIiwibmlja25hbWUiOiLku7vmlrnotoUiLCJkZXBhcnRtZW50X25hbWUiOiLph5HlsbHlip7lhazova_ku7bmnInpmZDlhazlj7gv5Lqn5ZOB5ZKM5oqA5pyv5aeU5ZGY5LyaL-eglOWPkeS4reWPsOS6i-S4mumDqC_mqKHlnovlupTnlKjnoJTlj5Hpg6gvQ29waWxvdCDnoJTlj5Ev5qih5Z6L56CU5Y-R57uEIiwiaXNfYWRtaW4iOmZhbHNlLCJzZWNyZXQiOiIiLCJ1c2VybmFtZSI6InJlbmZhbmdjaGFvIiwidGhpcmRfdW5pb25faWQiOiIxMzg4MzgzNzEwIiwiZW1haWwiOiJyZW5mYW5nY2hhb0B3cHMuY24iLCJpc19jb21wYW55X2FjY291bnQiOnRydWUsImV4cCI6MTczNTIyNDY4MSwiaXNzIjoiS0FTIn0.PgQp_SzZfNkW2-ox4E7nHDLWtvVQPOCNYzVBlbmmXVo; _c_WBKFRo=4rHY9TUav5n2wlZCYEWvyneKdeHreMm6vCnBGKQl; exp=259200; coa_id=0; ks_local_token=hJDZN8PwbT8BtxWk52hezW5sttjsNKcM; sre_mfa_sid=rXpl0RSPMeJuKYPoQbH3XWpxhDe0ADlK; nexp=129600; plusua=UExVU1VBLzEuMCAod2ViLXBsdXM6Y2hyb21lXzEzNi4wLjAuMDsgV2luZG93cyAxMDpXaW5kb3dzIDEwOyBPV1JqWkRrMlpqVmhNVEF6WVRZNVl3PT06QXBwbGVXZWJLaXQgNTM3LjM2KSBBcHBsZVdlYktpdC81MzcuMzY=; sre_user_sid=RaizxlBFGXTqV6XXr3bJXq8E3XkgFPFP; cv=qwczQmfNVeMmQsxyOBRu1-Bo2hTsoM5oslP3e37hS9XrMEbvNjHNAbun_6FB2yrkpu9OHr.tJaeCHo_l6k; kso_sid=TKS-f0fsGOgQ0x7Oqdg00poTTKS7TroIK5p_J_SKvFGq6K93mD-W0MTPlZY2IrbesWNoYXQFR7NFIQoUYa2EZIXoWrDT12y7wlMgwZynQNr-T2KwY2N9Y2J9R9ouTKS-IQAfTd_cv6Ppnspct7RqV7ph1WtG7_tEBY1IOvXdbg8BGBf_GvekTUrfUr0_KK.ZH4Xz-KTicV3uFQcktQf0awB5oLYgMBOmeaz4VYi3_Ie36Cg8vSFL4JGpD9V7n-SiS9uqRhnXsvA092EJzpnJK; tfstk=g9zII3_iUpvCJuuJNDfZGf7dLWg7R172FQG8i7Lew23KPYw8IHorU7p8w7Ha80uLU897LRySq6DreYwzwk5NuZP3t40-Pt7VuRZJZoyS90LJ6_hrOBCZvl6ulMgR3t7Za6SqA4er2fZ115HiNbpKe83tXjH9Jee-pcptZb0-y8npBVhEGpK-v0HO1bDte438e5CsaAH-N3RswMM3O6cX5ozkUvPKCUL8JamIhzKyPUwx9Da89AZQAPGIAxnaBuVaJRP88ymGXhgu_ow72-BwYvEjGRi4AtTQhJc8NbeCoIMTR7asxlR2l5iSdlUKfQL8MWqEXuwCdHDLYRim6cd5ofyqBW4Lf_vT9-kIJfnNksNt2lznmyW9RqE0T2r8HO-EpoGR4eYqhXCvVCiDPfMV11tkq1MV_FjH-cAnvfcC0116pumKsfMV11tkqDhiOO511pEl."
import copy
import os
from datetime import datetime, timedelta

import requests

default_config = {
    "size": 10000,
    "offset": 0,
    "storage": "es-cn-north-1-beijing-zjy1",
    "log_from": ["kae"],
    "sort_by": [{"key": "@timestamp", "desc": False}],
}
configs = {
    "test": {
        "log_pools": ["k8s_shared_wq_test_solution_dochelper-dev-cc"],
        "log_instance": "k8s_shared_wq_test_solution_dochelper-dev-cc",
    },
    "gray": {
        "log_pools": ["k8s_wq_prod_solution_dochelper"],
        "log_instance": "k8s_wq_prod_solution_dochelper",
    },
    "prod": {
        "log_pools": ["k8s_wq_prod_solution-green_docheloer-server"],
        "log_instance": "k8s_wq_prod_solution-green_docheloer-server",
    },
    "gotest": {
        "log_pools": ["k8s_shared_wq_test_solution_copliot-chat"],
        "log_instance": "k8s_shared_wq_test_solution_copliot-chat",
    },
    "gogray": {
        "log_pools": ["k8s_wq_prod_solution-gray_copilot-session"],
        "log_instance": "k8s_wq_prod_solution-gray_copilot-session",
    },
    "goprod": {
        "log_pools": ["k8s_wq_prod_solution_copilot-chat-prod"],
        "log_instance": "k8s_wq_prod_solution_copilot-chat-prod",
    },
    "wry": {
        "log_pools": ["k8s_shared_wq_test_solution_copliot-chat-wry"],
        "log_instance": "k8s_shared_wq_test_solution_copliot-chat-wry",
    },
    "wry-temp": {
        "log_pools": ["k8s_shared_wq_test_solution_copliot-chat-wry-temp"],
        "log_instance": "k8s_shared_wq_test_solution_copliot-chat-wry-temp",
    },
    "hzm": {
        "log_pools": ["k8s_shared_wq_test_solution_copliot-chat-hzm"],
        "log_instance": "k8s_shared_wq_test_solution_copliot-chat-hzm",
    },
    "hjy": {
        "log_pools": ["k8s_shared_wq_test_solution_copilot-session-hjy"],
        "log_instance": "k8s_shared_wq_test_solution_copilot-session-hjy",
    },
    "lj": {
        "log_pools": ["k8s_shared_wq_test_solution_copilot-session-lj"],
        "log_instance": "k8s_shared_wq_test_solution_copilot-session-lj",
    },
    "agent": {
        "log_pools": ["k8s_shared_wq_test_solution_copilot-session-ai-image"],
        "log_instance": "k8s_shared_wq_test_solution_copilot-session-ai-image",
    },
    "beta": {
        "log_pools": ["k8s_shared_wq_test_solution_copilot-session"],
        "log_instance": "k8s_shared_wq_test_solution_copilot-session",
    },
    "feature2": {
        "log_pools": ["k8s_shared_wq_test_solution_copliot-chat-feature2"],
        "log_instance": "k8s_shared_wq_test_solution_copliot-chat-feature2",
    },
    "dcl": {
        "log_pools": ["k8s_shared_wq_test_solution_copilot-chat-dcl"],
        "log_instance": "k8s_shared_wq_test_solution_copilot-chat-dcl",
    },
}


def get_time_data(delta=10):
    end_time = datetime.utcnow()
    # end_time = datetime.strptime("2025-05-16T14:25:00Z", "%Y-%m-%dT%H:%M:%SZ")
    start_time = end_time - timedelta(minutes=delta)
    time_data = {
        "start": start_time.isoformat() + "Z",
        "end": end_time.isoformat() + "Z",
    }
    return time_data


import json
import re
import time


class Kae:

    def __init__(self, env, logger, parse_http_log_catch):
        self.env = env
        self.url = (
            "https://sre.wps.cn/cloud-logging/api/v1/project/5010049/kae/get_logs"
        )
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:130.0) Gecko/20100101 Firefox/130.0",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2",
            "Accept-Encoding": "gzip, deflate, br, zstd",
            "Content-Type": "application/json",
            "Sre-Mfa-Request-Id": "1727245780120",
            "Origin": "https://sre.wps.cn",
            "Connection": "keep-alive",
            "Referer": "https://sre.wps.cn/kae/app-center/app-instance?team_id=5010049&id=10295&page=1&app_id=51903",
            "Cookie": kae_cookie,
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin",
            "Priority": "u=0",
            "TE": "trailers",
        }
        self.logger = logger
        self.parse_http_log_catch = parse_http_log_catch

    def get_logs(self, data={}):
        time_data = get_time_data()
        merged_data = {**default_config, **configs[self.env], **time_data, **data}
        print("query log", merged_data)
        response = requests.post(self.url, headers=self.headers, json=merged_data)
        rj = response.json()
        self.logger.info(f"get logs {rj}")
        if rj.get("code", "") == "get_cookie_err":
            print("cookie过期")
            exit()
        logs = [m["message"] for m in rj["logs"]]
        return logs

    def get_session_reqs_go(self, session_id, delta_time=10, wait=30, query="HTTP"):
        # 等日志落盘
        time.sleep(wait)
        reqs = self.get_session_logs_go(session_id, delta_time, query)
        self.logger.info(f"session_id {session_id} get {len(reqs)} logs")
        reqs_copy = copy.deepcopy(reqs)
        for r in reqs_copy:
            del r["request"]["raw"]
            del r["response"]["raw"]

        self.logger.info(f"session_id {session_id} get {len(reqs_copy)} logs")
        return reqs_copy

    def get_session_reqs_raw(
        self, session_id, delta_time=10, wait=30, query="HTTP", size=10000, offset=0
    ):
        # 等日志落盘
        time.sleep(wait)
        reqs = self.get_session_logs_go(session_id, delta_time, query, size, offset)
        self.logger.info(f"session_id {session_id} get {len(reqs)} logs")
        # reqs_copy = copy.deepcopy(reqs)
        # for r in reqs_copy:
        #     del r["request"]["raw"]
        #     del r["response"]["raw"]

        self.logger.info(f"session_id {session_id} get {len(reqs)} logs")
        return reqs

    def get_session_logs_go(
        self, session_id, delta_time=10, query=" ", size=10000, offset=0
    ):
        data = {"query": f"{session_id}"}
        if query:
            data = {"query": f"{session_id} AND {query}"}
        data["size"] = size
        data["offset"] = offset
        # data = {"query": f"{session_id}"}
        time_data = get_time_data(delta_time)
        merged_data = {**time_data, **data}
        logs = self.get_logs(merged_data)
        self.logger.info(logs)
        reqs = [self.parse_http_log_catch(log) for log in logs]
        reqs_return = [r for r in reqs if r]
        if len(reqs_return) != len(reqs):
            print(f"有解析{len(reqs) - len(reqs_return)}条错误的消息")
        return reqs_return

    def get_session_logs_only(self, query, delta_time=1000):
        data = {"query": f"{query}"}
        # data = {"query": f"{session_id}"}
        time_data = get_time_data(delta_time)
        merged_data = {**time_data, **data}
        logs = self.get_logs(merged_data)
        return logs
        # self.logger.info(logs)

    def get_session_logs_py(self, session_id, delta_time=10, query=""):
        data = {"query": f"{session_id}"}
        if query:
            data = {"query": f"{session_id} AND {query}"}
        # data = {"query": f"{session_id}"}
        time_data = get_time_data(delta_time)
        merged_data = {**time_data, **data}
        logs = self.get_logs(merged_data)
        self.logger.info(logs)
        reqs = [self.parse_http_log_catch(log) for log in logs]
        reqs_return = [r for r in reqs if r]
        if len(reqs_return) != len(reqs):
            print(f"有解析{len(reqs) - len(reqs_return)}条错误的消息")
        return reqs_return

    def get_session_reqs_py(self, session_id, delta_time=10, wait=30, query="common"):
        # 等日志落盘
        time.sleep(wait)
        reqs = self.get_session_logs_py(session_id, delta_time, query)
        reqs = [r for r in reqs if r]
        self.logger.info(f"session_id {session_id} get {len(reqs)} logs")
        reqs_copy = copy.deepcopy(reqs)
        for r in reqs_copy:
            del r["request"]["raw"]
            del r["response"]["raw"]

        self.logger.info(f"session_id {session_id} get {len(reqs_copy)} logs")
        return reqs_copy
