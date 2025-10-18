import json
import traceback
from types import MethodType

import airsheet
from copilot.api2_rfc import Copilot
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
    ["你看看目录页内容，然后总结企业历史事件回顾要点"], "cq90JvzJwGk4"
)
print(f"https://lingxi.wps.cn/chat/{r[2]}")  # type: ignore


# r = api.question("8699548058058853", "搜一下黄飞鸿", context_file_id="ck9oADxwIBB9")
