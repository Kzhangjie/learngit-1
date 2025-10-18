from abc import abstractmethod
from run_batch.run_code import RunCode
from run_batch.code_utils.validate_json_in_text import func




file_id = "cjYW3aNruLB8" # 文件
sheetname = "代码处理示例_校验json"
必须有的列名 = ["结果"] # 表示会跳过用例编号为空的行，可以多个，可根据需求修改
输出列名 = "JSON是否合法"  # 表示会跳过"答案"列已经有内容的行，为空表示所有行都会处理
输出列编号 = "B" # 表示从把答案写到C列
WPS_SID = None
# WPS_SID = "你的WPS_SID" # 如果不想给任方超文档编辑权限，求去掉这行注释，传入自己WPS_SID
json_example = {
    "annex": [
        {
            "highlightSentence": "示例句子",
            "reasons": "示例原因"
        }
    ]
}
def run_one(row):
    return func(row["结果"],json_example)   

if __name__ == '__main__':
    code = RunCode(file_id=file_id,sheetname=sheetname,must_have_columns=必须有的列名,skip_col_name=输出列名,clo_num_to_write=输出列编号,wps_sid=WPS_SID)
    code.run_one = run_one
    code.run()
        