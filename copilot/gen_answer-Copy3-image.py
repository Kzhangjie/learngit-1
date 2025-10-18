from types import MethodType
from run_batch.run_ai import RunAi
from itertools import islice
import re


file_id = "cubuqWiVDIri"
sheetname6 = "qvq_max对比豆包"
# 闲聊 创作 反馈群
# sheetname = "豆包"
# sheetname6 = "tencent,doubao"


必须有的列名 = ["问题"] 
输出列名 = "qvq_max回答"
# doubao-1.5-vision-pro回答   qvq-72b-preview回答
输出列编号 = "H"
# 新版本回答C 旧版本回答E MM版本回答G MM6.5版本回答I

# 输出列名 = "新版本-message1"
# 输出列编号 = "M"

from api import questions
import airsheet
import traceback
import json
from gen_prompt import convert_messages_for_gpt,extra_codes,extra_codes_from_logs
from copilot.code_session import history_to_chat_messages,trans_chat_messages_2_messages,history_to_model_messages
from api2 import Copilot
cc = Copilot(is_test=True,model_url="",custom_headers={},search_engines="")
# cc = Copilot(is_test=False,model_url="",custom_headers={},search_engines="")

def fileids(text):
    valid_canvas = {"PDFcanvas", "WPPcanvas", "ETcanvas", "WPScanvas"}
    data = {}
    match = re.search(r"https://kdocs\.cn/l/([\w]+)", text)
    if match:
        fid = match.group(1)
        if "1" not in data:
            data["1"] = {"canvas": "", "fids": []}
        data["1"] = {"canvas": "", "fids": [fid]}
            
    # current_index = None  # 记录当前处理的序号
    
    # for line in text.split("\n"):
    #     line = line.strip()  # 清除前后空格，避免匹配问题

    #     # 匹配 "序号：名称 链接" 形式
    #     match = re.search(r"^(\d+)：(\S*)\s*(https://www\.kdocs\.cn/l/[\w]+)", line)
    #     if match:
    #         index, canvas, link = match.groups()
    #         fid = link.split("/")[-1]
    #         current_index = index  # 更新当前处理的序号
            
    #         # 初始化该序号的数据
    #         if index not in data:
    #             data[index] = {"canvas": "", "fids": []}

    #         # 仅当 canvas 合法时赋值
    #         if canvas in valid_canvas:
    #             data[index]["canvas"] = canvas

    #         # 添加链接 ID
    #         data[index]["fids"].append(fid)
    #         continue  # 进入下一个循环

    #     # 匹配单独的链接（无序号）
    #     match_link = re.search(r"https://www\.kdocs\.cn/l/([\w]+)", line)
    #     if match_link and current_index:
    #         fid = match_link.group(1)
    #         data[current_index]["fids"].append(fid)

    return data

def process_questions(qs, data):
    print ("进来合并链接和问题了!!!!!")
    result_qs = []
    print ("有提取到链接的吧！！！！",data)

    for i, q in enumerate(qs, start=1):  # 从 1 开始匹配序号
        index = str(i)
        q = q.strip()  # 去除问题前后空格
        print ("现在到底是啥序号啊！！",index)

        if index in data:  # 只有 data 里存在该序号时才处理
            canvas = data[index]["canvas"]
            fids = data[index]["fids"]
            print ("开始提取链接了！！！",canvas,fids)

            # 处理 fids 追加部分
            file_links = []
            for fid in fids:
                if canvas:  # canvas 不为空
                    file_links.append(f"[文件名]({canvas})(wps365://files/{fid})")
                else:  # canvas 为空
                    file_links.append(f"[文件名](wps365://files/{fid})")

            # 拼接 fids 信息到当前问题前面
            fids_str = " ".join(file_links)  # 多个 fids 之间用空格连接
            q = f"{fids_str} {q}" if fids_str else q  # 如果 fids_str 为空，就不拼接

        result_qs.append(q)

    return result_qs
def run_one(self,row):
    
    try:
        file_urls = row["图片链接"]
        print (file_urls)
        file_data={}
        if file_urls:
            file_data = fileids(file_urls)
            # print (file_data)

        row_index = row["row_index"]
        qs = row["问题"].split("ask:")
        qs = [q.strip() for q in qs if q]
        if file_data:
            qs = process_questions(qs, file_data)
            # print (qs)
        # qs = [q.strip() for q in qs if q]

        answer,logs,s_id = cc.questions(qs)
        # fileinfo = row["文件url内容"]
        # result = json.dumps(answer,ensure_ascii=False,indent=4)
        # r1 = result[:30000]
        # r2 = result[30000:60000]
        # r3 = result[60000:90000]
        # r4 = result[90000:120000]

        # message = history_to_model_messages(answer,fileinfo)
        # model_message = json.dumps(message,ensure_ascii=False,indent=4)     
        # m1 = model_message[:30000]
        # m2 = model_message[30000:60000]
        # m3 = model_message[60000:90000]
        # m4 = model_message[90000:120000]
        # content = next(msg["content"] for msg in reversed(json.loads(answer)) if msg["role"] == "assistant" and msg["type"] == "text")
        code= extra_codes(answer)
        # airsheet.write_xl(code, f'H{row["row_index"]}', sheet_name=self.sheetname)
        content_list = [
            msg["content"]
            for msg in answer.get("data", {}).get("list", [])
            if msg.get("role") == "assistant" and msg.get("type") in {
                "text", "execution", "long_writer", "ppt_outline_text",
                "mind_map", "ppt_outline_text_v2"
            }
        ]
        airsheet.write_xl(content_list, f'{self.clo_num_to_write}{row["row_index"]}', sheet_name=self.sheetname)
        # content = 
        # content = next(
        #     msg["content"]
        #     for msg in islice(reversed(answer.get("data", {}).get("list", [])), 1, None)  # 跳过第一个，返回第二个
        #     if msg.get("role") == "assistant"
        # )
        # code = next(
        #     (msg["content"] for msg in answer.get("data", {}).get("list", []) if msg.get("type") == "code"),
        #     None  # 如果没有找到符合条件的消息，返回 None
        # )
        # reason = next(
        #     (msg["content"] for msg in answer.get("data", {}).get("list", []) if msg.get("type") == "reasoning"),
        #     None  # 如果没有找到符合条件的消息，返回 None
        # )
        # if reason:
        #      reason = json.loads(reason).get("text","")
        # airsheet.write_xl([code,content], f'{self.clo_num_to_write}{row["row_index"]}', sheet_name=self.sheetname)
        # airsheet.write_xl(content, f'{self.clo_num_to_write}{row["row_index"]}', sheet_name=self.sheetname)
        # airsheet.write_xl([r1,r2,r3,r4,content], f'{self.clo_num_to_write}{row["row_index"]}', sheet_name=self.sheetname)
        # airsheet.write_xl([m1,m2,m3,m4,content], f'{self.clo_num_to_write}{row["row_index"]}', sheet_name=self.sheetname)

    except Exception as e:
        print(traceback.format_exception(e))

if __name__ == '__main__':
    # ss = [sheetname1,sheetname2,sheetname3,sheetname4,sheetname5,sheetname]
    ss = [sheetname6]
    # ss = [sheetname5]
    for s in ss:
        ai = RunAi(file_id=file_id,sheetname=s,must_have_columns=必须有的列名,skip_col_name=输出列名,clo_num_to_write=输出列编号,max_workers=10)
        ai.run_one = MethodType(run_one, ai)
        ai.run()