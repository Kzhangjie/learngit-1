import json
import traceback
from types import MethodType

import airsheet
from copilot.api2_rfc import Copilot
from renfangchao.canvas.gen_1_answer import parse_code
from run_batch.run_ai import RunAi

api = Copilot(
    is_test=True,
    model_url="",
    wps_sid="",
    custom_headers={"X-Cc-Region": "feat_copilot_cc_multi_agents"},
    search_engines="",
    agent="WPP",
)

historys, rs, session_id = api.questions(
    [
        {
            "question": "在你介绍的领头企业当中，耳熟能详的新能源车企“比亚迪”，具体分析一下这个车企",
            "command_args": {"disable_websearch": False},
        },
        {
            "question": "现在很多“滴滴”等打车软件上的车大部分是比亚迪，被人们戏称为滴滴车，为什么呢",
            "command_args": {"disable_websearch": False},
        },
        {
            "question": "找一下外国新能源车企有哪些很著名的，再生成思维导图",
            "command_args": {"disable_websearch": False},
        },
    ],
    "cfcuvQ34OWkY",
    with_history=False,
)  # type: ignore
session_id = str(session_id)
# print(111, session_id, historys)
# print(111, rs)
# print(rs[0])
parsed_results = [parse_code(r) for r in rs]
group_codes = [result[0] for result in parsed_results]
group_funcs = [result[1] for result in parsed_results]
print(f"https://lingxi.wps.cn/chat/{session_id}")  # type: ignore
print(group_funcs)
# r = api.question("8699548058058853", "搜一下黄飞鸿", context_file_id="ck9oADxwIBB9")
