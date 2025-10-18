from run_batch.run_ai import RunAi
import traceback
import airsheet
from types import MethodType

人设 = "请扮演单位新来的厨师。记住：王总不吃辣椒，李总不吃葱，张总不吃蒜,路总是广东人，孙总是山西人，白总是湖南人。"

模型列名="模型" #这列的内容要与kpp上的模型一样，或者点最上面mode_names查看
多个模型参数 ={}




def gen_msg(index):
    with open(f"./tongyong/renfangchao/memory/txts_1000/{index}_1000.txt", "r", encoding="utf-8") as f:
        content = f.read()
    return "又是新的一天，老厨师教你一些新菜，请学会它们，然后回答'学会了'即可，不要回答其他内容。\n"+content

def gen_msg_last():
    return "明天王总请孙总和白总吃饭，请为他们3人准备8道老厨师教你的菜，并说出理由。"
    



WPS_SID = None
# WPS_SID = "你的WPS_SID" # 如果不想给任方超文档编辑权限，求去掉这行注释，传入自己WPS_SID
file_id = "cimCyYu7JQIX" # 文件
sheetname = "1000字多轮_new"
必须有的列名 = ["提问前对话轮数"] # 表示会跳过用例编号为空的行，可以多个，可根据需求修改
输出列名 = "结果" # 表示会跳过"答案"列已经有内容的行。
输出列编号 = "C" # 表示从把答案写到C列
from utils import mode_names

def run_one(self,row):
    try:

        msgs = []
        guochengs = []
        error =False
        if row[模型列名] in [mode_names.GLM_3_TURBO,mode_names.GLM_4]:
            msgs.append({"content": 人设, "role": "system"})
        # for i in range(1, row["提问前对话轮数"]+1):
        #     msgs.append({"content": gen_msg(i), "role": "user"})
        #     success,result,resp = self.api.chat_msgs(row[模型列名], msgs, 人设)
        #     guochengs.append(result)
        #     if success:
        #         msgs.append({"content": result, "role": "assistant"})            
        #     else:
        #         error = True
        for i in range(1, row["提问前对话轮数"]+1):
            msgs.append({"content": gen_msg(i), "role": "user"})
            msgs.append({"content": "记住了", "role": "assistant"})
        # airsheet.write_xl(["\n\n".join(guochengs)], f'D{row["row_index"]}', sheet_name=self.sheetname)
        # if error:
        #     return
        msgs.append({"content": gen_msg_last(), "role": "user"})
        success,result,resp = self.api.chat_msgs(row[模型列名], msgs, 人设)
        airsheet.write_xl([result], f'{输出列编号}{row["row_index"]}', sheet_name=self.sheetname)
    except Exception as e:
        print(traceback.format_exception(e))


if __name__ == '__main__':
    ai = RunAi(file_id=file_id,sheetname=sheetname,must_have_columns=必须有的列名,skip_col_name=输出列名,clo_num_to_write=输出列编号,wps_sid=WPS_SID)
    # ai.prompt = 提问
    # ai.prompt_param_colname_map = 提问参数
    ai.system_setting = 人设    
    ai.mode_col_name = 模型列名
    ai.llm_arguments_map = 多个模型参数
    ai.max_workers = 12
    ai.run_one = MethodType(run_one, ai)

    ai.run()