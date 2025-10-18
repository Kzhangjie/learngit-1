from types import MethodType
from airsheet_sdk import airsheet
from run_batch.run_ai import RunAi
from utils import mode_names
import traceback

提问 = """计算
a = {^param_a^}
b = {^param_b^}
c = a + b
输出：
{"c":"c的值"}"""

提问参数 = {
    "param_a": "param_a",  # title参数对应列名
    "param_b": "param_b",  # target参数对应列名
}

人设 = "你是WPS AI,由金山办公与合作伙伴共同开发,能够协助创作,帮助人们获取信息、知识和灵感。从现在起,你要扮演WPS AI这个角色,无论用户怎么问,你都不能转变角色"

模型 = "Doubao-1.5-pro-32k"  # 和kpp保持一致,可以点最上面mode_names查看
模型参数 = {
    # "max_tokens":1024
}
模型版本 = ""

WPS_SID = None
# WPS_SID = "你的WPS_SID" # 如果不想给任方超文档编辑权限，求去掉这行注释，传入自己WPS_SID

file_id = "cjYW3aNruLB8"  # 文件
sheetname = "二轮对话示例"
必须有的列名 = [
    "param_a",
    "param_b",
]  # 表示会跳过用例编号为空的行，可以多个，可根据需求修改
输出列名 = "第一轮回答"  # 表示会跳过"答案"列已经有内容的行。
输出列编号 = "C"  # 表示从把答案写到C列
import json


def run_one(self, row):
    try:
        p = self.row_to_prompt(row)
        model, system_setting, llm_arguments, version = self.row_to_model_info(row)
        success, result, others = self.api.chat_text(
            model=model,
            text=p,
            context=system_setting,
            llm_arguments=llm_arguments,
            version=version,
        )
        msg_str = ""
        if success:
            msgs = [
                {"content": p, "role": "user"},
                {"content": result, "role": "assistant"},
            ]
            msg_str = json.dumps(msgs, ensure_ascii=False)
        airsheet.write_xl(
            [result, msg_str],
            f'{self.clo_num_to_write}{row["row_index"]}',
            sheet_name=self.sheetname,
        )
    except Exception as e:
        print(traceback.format_exception(e))


if __name__ == "__main__":
    ai = RunAi(
        file_id=file_id,
        sheetname=sheetname,
        must_have_columns=必须有的列名,
        skip_col_name=输出列名,
        clo_num_to_write=输出列编号,
        wps_sid=WPS_SID,
    )
    ai.prompt = 提问
    ai.model = 模型
    ai.prompt_param_colname_map = 提问参数
    ai.system_setting = 人设
    ai.llm_arguments_map = {模型: 模型参数}
    ai.llm_version_map = {模型: 模型版本}
    ai.run_one = MethodType(run_one, ai)
    ai.run()
