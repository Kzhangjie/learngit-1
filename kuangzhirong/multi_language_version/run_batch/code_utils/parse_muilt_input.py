import re
import json
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

if __name__ == "__main__":
    text = """ppt_theme：q
title：接口类型&错误
input：类型"""

    print(func(text,["ppt_theme", "title", "input"]))

