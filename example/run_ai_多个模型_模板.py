from run_batch.run_ai import RunAi
from utils import mode_names

提问 = """假如你是一个小学老师，请对参考教学难点适当改写，帮我生成一份新的{^title^}的教学难点。
要求：
1. 你只适当改写文本，但是不要改变文本意思。

教学难点参考如下：
{^target^}

格式参考：
#三、教学难点
1. <教学难点内容，使用markdown的有序列表。>"""

提问参数 = {
    "title": "title123",  # title参数对应列名
    "target": "target321",  # target参数对应列名
}

人设 = "你是WPS AI,由金山办公与合作伙伴共同开发,能够协助创作,帮助人们获取信息、知识和灵感。从现在起,你要扮演WPS AI这个角色,无论用户怎么问,你都不能转变角色"

模型列名 = "模型"  # 这列的内容要与kpp上的模型一样，或者点最上面mode_names查看
多个模型参数 = {
    # "ernie-bot-4": {
    #     "max_tokens":1024
    # },
    # "ernie-bot": {
    #     "max_tokens":1024
    # }
}
多个模型版本 = {"Doubao-1.5-pro-32k": "", "Doubao-1.5-pro-256k": ""}
WPS_SID = None
# WPS_SID = "你的WPS_SID" # 如果不想给任方超文档编辑权限，求去掉这行注释，传入自己WPS_SID
file_id = "cjYW3aNruLB8"  # 文件
sheetname = "多模型示例"
必须有的列名 = ["title123"]  # 表示会跳过用例编号为空的行，可以多个，可根据需求修改
输出列名 = "答案"  # 表示会跳过"答案"列已经有内容的行。
输出列编号 = "D"  # 表示从把答案写到D列

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
    ai.prompt_param_colname_map = 提问参数
    ai.system_setting = 人设
    ai.mode_col_name = 模型列名
    ai.llm_arguments_map = 多个模型参数
    ai.llm_version_map = 多个模型版本
    ai.run()
