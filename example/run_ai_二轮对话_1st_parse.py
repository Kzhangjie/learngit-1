from run_batch.run_code import RunCode

file_id = "cjYW3aNruLB8" # 文件
sheetname = "二轮对话示例"
必须有的列名 = ["第一轮回答"] # 表示会跳过用例编号为空的行，可以多个，可根据需求修改
输出列名 = "解析param_d" # 表示会跳过"答案"列已经有内容的行。
输出列编号 = "e" # 表示从把答案写到C列
import re
def run_one(row):
    match = re.search(r'\d+', str(row["第一轮回答"]))
    if match:
        return [str(match.group())]
    else:
        return [""]

if __name__ == '__main__':
    code = RunCode(file_id=file_id,sheetname=sheetname,must_have_columns=必须有的列名,skip_col_name=输出列名,clo_num_to_write=输出列编号)
    code.run_one = run_one
    code.run()