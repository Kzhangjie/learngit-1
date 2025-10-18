from run_batch.run_ai import RunAi
import airsheet
from utils.gateway_api_v2_stream import GateWayAPI
from datetime import datetime
from types import MethodType

file_id = "cezuqhYeITqh"

sheetname = "用例"
必须有的列名 = ["问题", "回答", "产出"]
输出列名 = "模型判定"
输出列编号 = "G"
生词次数 = 1


def _get_current_date_desc() -> str:
    # 获取当前时间
    now = datetime.now()
    # 英文星期转中文星期的映射
    day_map = {
        "Monday": "星期一",
        "Tuesday": "星期二",
        "Wednesday": "星期三",
        "Thursday": "星期四",
        "Friday": "星期五",
        "Saturday": "星期六",
        "Sunday": "星期日",
    }
    # 获取英文星期名称
    english_day = now.strftime("%A")
    # 映射为中文
    chinese_day = day_map[english_day]
    # 格式化日期并附加中文星期
    current_date_desc = now.strftime(f"%Y 年 %m 月 %d 日 {chinese_day}")
    return current_date_desc


今天日期 = _get_current_date_desc()

system = """## 无
""".format(
    今天日期=今天日期
)

print(system)

Prompt = """




# 任务
把要分析的内容，严格按分析标准和示例进行分析，并必须按照输出格式进行输出，不能进行额外备注

# 要分析的内容
问题：{{.question}}
回答：{{.answer}}
产出：{{.bt}}

# 分析背景说明： 
问题和回答是一个会话，产出是对这个会话进行的概况，需要分析产出有没有很好的概况会话

# 分析标准
请结合【分析背景说明】进行严格分析。
最终标准是：产出中内容
1、内容是否概括合理，有无偏离会话主题或者幻觉的情况

# 输出格式（严格按照）
请严格按照以下格式范例输出，以便程序自动提取结果：
判定：通过  + 对应解释
判定：有错误   错误情况：存在幻觉/偏离会话主题 + 对应解释
"""

model = "Doubao-1.5-pro-32k"
context = f"{system}"
version = ""
llm_arguments = {
    "temperature": 0.1,
    "max_tokens": 8000,
    "top_p": 0.1,
    "bot_setting": [{"bot_name": "WPS 灵犀", "content": f"{system}"}],
}

sec_text = {
    "from": "AI_WPS_SMARTASSISTANT",
    "scene": "pc_web_file",
    "extra_text": ["搜索拆词"],
}

import re  # 别忘了引入


def run_one(self, row):
    try:
        row_index = row["row_index"]
        replacements = {
            "{{.question}}": row.get("问题", ""),
            "{{.answer}}": row.get("回答", ""),
            "{{.bt}}": row.get("产出", ""),
        }

        prompt_text = Prompt
        for key, val in replacements.items():
            prompt_text = prompt_text.replace(key, val)

        model_message = [{"role": "user", "name": "user", "content": prompt_text}]

        api = GateWayAPI(retry_count=1)
        success, content, others = api.chat_msgs(
            model, model_message, context, llm_arguments, version, sec_text
        )

        airsheet.write_xl(
            content, f"{self.clo_num_to_write}{row_index}", sheet_name=self.sheetname
        )

    except Exception as e:
        print(f"处理 row_index={row.get('row_index')} 时出错: {e}")


if __name__ == "__main__":
    ss = [sheetname]
    for s in ss:
        ai = RunAi(
            file_id=file_id,
            sheetname=s,
            must_have_columns=必须有的列名,
            skip_col_name=输出列名,
            clo_num_to_write=输出列编号,
            max_workers=4,
        )
        ai.run_one = MethodType(run_one, ai)  # 将 run_one 方法绑定到 ai 对象
        ai.run()
