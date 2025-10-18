import utils.constants as constants
import airsheet
import pandas as pd
import re
# import gptapi
import json
import os
import pandas
import datetime
from collections import defaultdict
import airsheet
# WPS_SID = ''
file_id = "ceTi5q98u9Sl"
sheetname = "websearch_验证集"
sheetname1 = "创建文件_验证集"
sheetname2 = "保存PPT_验证集"
sheetname3 = "URL_fetch_验证集"
sheetname4 = "chat_验证集"
sheetname5 = "人设_验证集"
sheetname6 = "数理计算_验证集"
必须有的列名 = ["模型调度断言总体"] 

def get_df(file_id,sheet_name,wps_sid=constants.WPS_SID):
    airsheet.init(file_id=file_id, wps_sid=wps_sid, sheet_name=sheet_name)
    df = airsheet.xl("A:ZZ", headers=True, sheet_name=[sheet_name])  
    # df = df.dropna(axis=1, how='all')
    df['行号'] = range(0, len(df))
    df = df[df['问题'] != '']
    for col in 必须有的列名:
        df = df[df[col].notna() & (df[col] != "")]
    df.fillna("", inplace = True)
    print (df)
    return df


#统计用例分布（意图断言跑完后再统计）、概率统计（lops跑完后再统计）
if __name__ == '__main__':
    ss = [sheetname,sheetname1,sheetname2,sheetname3,sheetname5,sheetname6]
    # ss = [sheetname]
    final_output_all = {
        "function": [],
        "总分": [],
        "得分": [],
        "<0.8数量": []
    }
    function_count = defaultdict(int)
    function_score = defaultdict(float)
    less_than_0_8_count = defaultdict(int)
    for s in ss:
        output_all = {
            "用例分类": [],
            "总数": [],
            "占比": [],
            "通过数": [],
            "通过率": []
        }
        case_count = {}
        case_pass = {}
        df = get_df(file_id,s,constants.WPS_SID)

        # 循环统计
        for i, row in df.iterrows():
            row = row.to_dict()
            # checklist = str(row.get('checklist', ''))
            # result_message = str(row.get("WPS答案可视化",""))
            line_number = int(row.get('行号'))
            try:
            # 统计全部sheet
                data = json.loads(row.get('置信度结果', ''))
                    # 解析并统计 function 值
                for key, values in data.items():
                    for value in values:
                        func_prob_tokens = value["func_prob_token"].split(',')
                        func_prob = value["func_prob"]
                        for token in func_prob_tokens:
                            function_count[token] += 1
                            function_score[token] += round(func_prob, 5)
                            if func_prob < 0.8:
                                less_than_0_8_count[token] += 1
                # 用例分布，仅测试这几个sheet                 
                if s in [sheetname,sheetname1,sheetname2,sheetname5]:
                    case = str(row.get('二级分类')).splitlines()
                    check = str(row.get('模型调度断言总体'))
                    check_r = str(row.get('模型调度断言详情'))
                    for category in case:
                        if category != "空" and category != "？":
                            if category in case_count:
                                case_count[category] += 1
                            else:
                                case_count[category] = 1
                                case_pass[category] = 0  # 初始化通过数为0
        
                    # 校验逻辑
                    if check == "是":
                        for category in case:
                            if category != "空" and category != "？":
                                case_pass[category] += 1  # 全部分类通过数+1
                    else:
                        # 遍历 check_r 每一行，提取其中的数字并处理逻辑
                        failed_indices = set()  # 存储提取出的行号索引
        
                        for line in check_r:
                            # 使用正则表达式提取行中的数字
                            match = re.search(r'\d+', line)
                            if match:
                                check_r_index = int(match.group()) - 1  # 假设 check_r 是1-based index
                                if 0 <= check_r_index < len(case):
                                    failed_indices.add(check_r_index)  # 收集需要过滤的行号
        
                        # 更新通过数，跳过提取出的行
                        for i, category in enumerate(case):
                            if i not in failed_indices and category != "空" and category != "？":
                                case_pass[category] += 1  # 其他分类通过数+1
            except json.JSONDecodeError:
                print("JSON 解析错误")
        
        # 计算分类总数的汇总
        total_count = sum(case_count.values())

        # 汇总输出结果并计算占比和通过率
        for category in case_count:
            total = case_count[category]
            passed = case_pass[category]
            proportion = (total / total_count) * 100 if total_count > 0 else 0  # 占比
            pass_rate = (passed / total) * 100 if total > 0 else 0  # 通过率

            output_all["用例分类"].append(category)
            output_all["总数"].append(total)
            output_all["占比"].append(f"{proportion:.2f}%")
            output_all["通过数"].append(passed)
            output_all["通过率"].append(f"{pass_rate:.2f}%")

        # 将结果转换为DataFrame展示
        output_df = pd.DataFrame(output_all)
        if s == sheetname:
            airsheet.write_xl(output_df, f"D5", sheet_name="用例分布")  #搜索
        if s == sheetname1:
            airsheet.write_xl(output_df, f"K5", sheet_name="用例分布")  #创建文件
        if s == sheetname2:
            airsheet.write_xl(output_df, f"R5", sheet_name="用例分布")  # ppt
        if s == sheetname5:
            airsheet.write_xl(output_df, f"Y5", sheet_name="用例分布")  # 人设

    for func_token in function_count.keys():
        final_output_all["function"].append(func_token)
        final_output_all["总分"].append(function_count[func_token])
        final_output_all["得分"].append(function_score[func_token])
        final_output_all["<0.8数量"].append(less_than_0_8_count[func_token])

    # 转换为DataFrame以便后续处理
    df = pd.DataFrame(final_output_all)

    airsheet.write_xl(df, f"W3", sheet_name="统计")
