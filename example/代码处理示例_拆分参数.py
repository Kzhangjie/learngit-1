import re
from run_batch.run_code import RunCode

def func(text, keys=["ppt_theme", "text", "title", "title1", "title2", "title3", "input"]):
    # 构建正则表达式，匹配所有键名，后跟任意非贪婪字符序列，直到遇到下一个键名或字符串末尾
    keys_pattern = '|'.join([f'{key}：' for key in keys])
    pattern = f'({keys_pattern})(.*?)(?={keys_pattern}|$)'

    # 使用正则表达式查找所有匹配项
    matches = re.finditer(pattern, text, re.DOTALL)

    # 先将匹配项转换为临时字典，以便快速查找值
    temp_dict = {}
    for match in matches:
        key = match.group(1).rstrip('：')  # 移除键名后的冒号
        value = match.group(2).strip()
        temp_dict[key] = value

    # 按照 keys 参数中的顺序构建结果数组，如果键不存在则添加空字符串
    result_array = [temp_dict.get(key, "") for key in keys]

    return result_array

# --------这块调试func跑----start---------

# if __name__ == "__main__":
#     text = """ppt_theme：q
# title：接口类型&错误
# input：类型"""
#     print(func(text,["ppt_theme", "title", "input"]))

# --------这块调试func跑----end---------


# --------这块批量跑----start---------
file_id = "cjYW3aNruLB8" # 文件
sheetname = "代码处理示例_拆分参数"
必须有的列名 = ["参数"] # 表示会跳过用例编号为空的行，可以多个，可根据需求修改
输出列名 = "input" # 表示会跳过"答案"列已经有内容的行。
输出列编号 = "B" # 表示从把答案写到C列
WPS_SID = None
# WPS_SID = "你的WPS_SID" # 如果不想给任方超文档编辑权限，求去掉这行注释，传入自己WPS_SID
def run_one(row):
    return func(row["参数"],["input","text"])   

if __name__ == "__main__":
    code = RunCode(file_id=file_id,sheetname=sheetname,must_have_columns=必须有的列名,skip_col_name=输出列名,clo_num_to_write=输出列编号,wps_sid=WPS_SID)
    code.run_one = run_one
    code.run()

# --------这块批量跑----end---------