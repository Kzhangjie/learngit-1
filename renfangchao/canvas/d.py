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
    custom_headers={"X-Cc-Region": "zyz"},
    search_engines="",
    agent="",
)
historys, rs, session_id = api.questions(
    [
        {
            "question": "你好" * 1024 * 99,
            "reasoning": True,
        }
    ],
    "",
    with_history=False,
)  # type: ignore
print(session_id)
