
from run_batch.run_ai import RunAi
from run_batch.run_ai_msgs import RunAiMsgs
import utils.constants as constants
import airsheet
from utils import mode_names
from utils.gateway_api_v2_stream import GateWayAPI
from datetime import datetime
import concurrent.futures
import json
from types import MethodType
# from qiuxiaona.lingxi_ppt import levels_counts,seclevels_counts,text_res,text_wordcounts
import concurrent.futures
import threading
import copy
import re
from concurrent.futures import ThreadPoolExecutor

file_id = "caOqCHlVx6A2"
sheetname = "会话标题"
sheetname1 = ""
sheetname2 = ""
sheetname3 = ""
sheetname4 = ""
必须有的列名 = ["问题","回答"] 
输出列名 = "minimax"
输出列编号 = "D"
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

system = """你是一个总结高手，请根据对话内容为对话取一个标题，标题应该拒绝黄赌毒，不能包含任何关于毒品制作、危险品制作、暴力恐怖主义等违法犯罪内容
""".format(今天日期=今天日期)

print (system)

Prompt = """# 你的角色
对话标题生成器

# 任务
请根据我和你之间的问答，生成符合对话内容主旨的标题，不要回答其他问题

# 对话内容
<我>{q}</我>
<你>{ans}</你>

# 要求
- 生成的标题字数限制在5-20个字符之间
- 标题应直接反映对话的核心内容，无需添加额外信息或细节
- 标题为纯文本，不能使用Markdown格式
- 不能带任何前缀、特殊字符或符号，且不需要使用引号括起来
"""

model = "abab6.5s-chat"
# model = "Doubao-1.5-pro-32k"
context  = f"{system}"
version = ""
llm_arguments = {
    'temperature': 0.1, 
    'max_tokens': 8000,
    'bot_setting': [{
        'bot_name': 'WPS 灵犀', 
        'content': f"{system}"}]
}

sec_text = {
        "from": "AI_WPS_SMARTASSISTANT",
        "scene": "pc_web_file",
        "extra_text": ["搜索拆词"]
        }

def run_one(self,row):
    try:
        row_index = row["row_index"]
        raw_question = row.get("问题", "")
        raw_answer = row.get("回答", "")
        
        prompt_text = Prompt.replace("{q}", raw_question)
        prompt_text = prompt_text.replace("{ans}", raw_answer)
        
        #自己处理下model_message
        model_message = [
        {
            "role": "user",
            "name": "user",
            "content": prompt_text
        }
        ]
        

        api = GateWayAPI(retry_count=1)
        #调用大模型
        success, content ,others = api.chat_msgs(model, model_message, context, llm_arguments,version,sec_text)
        
        #content是输出的内容，直接写回表格
        airsheet.write_xl(content, f'{self.clo_num_to_write}{row["row_index"]}', sheet_name=self.sheetname)

    except json.JSONDecodeError:
        print("JSON 解析错误")
   
if __name__ == '__main__':
    ss = [sheetname]
    for s in ss:
        ai = RunAi(file_id=file_id,sheetname=s,must_have_columns=必须有的列名,skip_col_name=输出列名,clo_num_to_write=输出列编号,max_workers=4)
        ai.run_one = MethodType(run_one, ai)
        ai.run()
    