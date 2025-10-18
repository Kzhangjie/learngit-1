is_test = False
from copilot.api2_rfc import Copilot

api = Copilot(
    is_test=is_test,
    # wps_sid=run_wps_sid,
    # custom_headers={"X-Cc-Region": branch},
)
q = {
    "question": "不要搜索，根据以下主题生成思维导图：李白",
    "thinking": "enabled",
    "file_ids": [],
    "context": {"agent": None},
}
_, rs, id = api.questions([q], with_history=False)
print(rs)
print(id)
