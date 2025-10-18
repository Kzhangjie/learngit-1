import json
import os
import traceback
from types import MethodType

import airsheet
from copilot.api2_rfc import Copilot
from run_batch.run_ai import RunAi

api = Copilot(
    is_test=True,
    model_url="",
    wps_sid=os.environ["WPS_SID"],  # 账号 14701234567
    custom_headers={"x-cc-region": "cc_copilot_2505"},
    search_engines="",
    agent="WPP",
)
fff = []
for i in range(1, 10):
    historys, rs, session_id = api.questions(
        ["这个ppt主色是蓝色，再搭两个辅助色，让页面丰富些，又不能太花哨"],
        "ceBYdbj0NlXl",
    )  #  type: ignore
    session_id = str(session_id)
    group_funcs = {}
    # print(111, session_id, historys)
    for history in historys["data"]["list"]:
        if history["type"] == "code":
            # print(44444, history["content"])
            try:
                func = json.loads(history["content"])
                fff.append(func)
                group_id = history.get("group_id", "default")
                group_funcs.setdefault(group_id, []).append(func)
            except Exception as e:
                print(f"处理history项时出错: {e}")
    group_funcs = list(group_funcs.values())
    print(f"https://lingxi.wps.cn/chat/{session_id}")  # type: ignore

for r in fff:
    print(1110)
    print(r)
    print(2222)
# r = api.question("8699548058058853", "搜一下黄飞鸿", context_file_id="ck9oADxwIBB9")
