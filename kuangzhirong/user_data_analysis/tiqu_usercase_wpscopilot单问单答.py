import pandas as pd
import random
from datetime import datetime
import re
import json
import os
import sys
import pandas
import datetime
from dotenv import load_dotenv
import zipfile
import gzip
import shutil
load_dotenv()
WPS_SID = ''
file_id = "ciydt4eSxlMW"
# 原始文件所在的目录
file_directory = r"D:\lingxi\user_data_sidebar\侧边栏"


def run(input_filename,output_filename):
    input_file_path = file_directory + "\\" + input_filename
    output_file_path = file_directory + "\\" + output_filename

    try:
        # 先读取表头

        header = pd.read_csv(input_file_path, nrows=0)

        # 再读取数据部分

        df = pd.read_csv(input_file_path, skiprows=1,
                         header=None)

        # 给数据部分加上表头
        df.columns = header.columns

        df.fillna("", inplace=True)


        filtered_groupid = df[(df['Role'] == 'user') & (df['OriginData'].str.contains(r'"agent":"et"', flags=re.IGNORECASE))]['SessionID']
        # filtered_groupid = df[(df['Type'] == 'tool_call') & (df['Content'].str.contains('mindmap'))]['SessionID']



        final_df = df[df['SessionID'].isin(filtered_groupid)]

        #不需要过滤数据的时候，copy一下
        # final_df = df.copy()
        final_df['行号'] = range(0, len(final_df))

        print(final_df)
        nowSessionID = 0
        file_content = ""
        questions = ""
        codes = ""
        command = ""
        agent = ""
        client_type = ""
        selection_str=""
        lunci = 0
        data = []
        assistant_responses = []
        message = ""
        canvas_replacement = ""
        valid_assistant_types = {"text", "execution", "long_writer", "ppt_outline_text", "mind_map",
                                 "ppt_outline_text_v2","canvas_replacement","call_summary","docx_edit_operation","data_analysis", "tabel_operation"}
        CreatorID = 0
        CompanyID = 0
        SessionCreateTime = "2025/4/25 14:00:00"
        codetype = False

        for i, row in final_df.iterrows():

            row = row.to_dict()
            line_number = int(row.get('行号'))
            Content = row.get('Content')
            GroupID = row.get('GroupID')
            SessionID = row.get('SessionID')
            Type = row.get('Type')
            Role = row.get('Role')
            origin_data = row.get('OriginData')
            CreatorID = row.get('CreatorID')
            CompanyID = row.get('CompanyID')
            SessionCreateTime = row.get('SessionCreateTime')

            # 初始化GroupID

            if nowSessionID == 0:
                nowSessionID = SessionID

            if SessionID == nowSessionID:
                if Role == "user":
                    if assistant_responses:
                        data.append({
                            "SessionID": f'\'{nowSessionID}',
                            "SessionCreateTime": SessionCreateTime,
                            "CreatorID": CreatorID,
                            "CompanyID": CompanyID,
                             "问题轮次": lunci,
                            "划词内容":selection_str,
                            "问题": questions.strip(),
                            "code": codes.strip(),
                            "command": command,
                            "agent": agent,
                            "client_type":client_type,
                            "文件内容": file_content,
                            "编辑回答":canvas_replacement,
                            **{f"第{idx + 1}个回答": assistant_responses[idx] if idx < len(assistant_responses) else ""
                               for idx
                               in
                               range(len(assistant_responses))}
                        })
                    lunci +=1
                    file_content = ""
                    questions = ""
                    codes = ""
                    command = ""
                    # agent = ""
                    assistant_responses = []
                    canvas_replacement = ""
                    origin_data_json = json.loads(origin_data)
                    agent = origin_data_json.get("context_args",{}).get("agent","")
                    client_type = origin_data_json.get("client_type","")
                    if origin_data_json and isinstance(origin_data_json, dict):
                        file_infos = origin_data_json.get("file_infos", [])
                        quote_files = origin_data_json.get("quote_files", [])
                        command += f"{origin_data_json.get("command", "")} "
                        if file_infos:
                            # 提取每个文件的 file_name
                            file_names = [f.get("file_name", "") for f in file_infos if f.get("file_name", "")]
                            # print(file_names)
                        else:
                            file_names = []  # 如果 file_infos 为空，设置为空列表
                    else:
                        file_names = []  # 如果 origin_data_json 不是有效字典或为 None，给空列表

                    # 格式化文件名为 [文件名](wps365://files/)
                    formatted_names = ' '.join(f'[{name}](wps365://files/)' for name in file_names)

                    # 划词区域
                    selection = origin_data_json.get("command_args", {}).get("selection", "")
                    if selection:
                        selection_str = selection

                    else:
                        selection_str = ""
                    # questions += f'ask:{selection_str}{formatted_names}{Content}\n'
                    questions += f'ask:{formatted_names}{Content}\n'
                    if codes != "":
                        codes += '\n'
                        command += '\n'


                if Role == "assistant" and Type == "tool_call":
                    tool_call = json.loads(Content)
                    codes += f'{tool_call.get("request", {}).get("tool_id", "")} '


                if Role == "assistant" and Type == "parsefile":
                    fileinfo = json.loads(origin_data)
                    # print(fileinfo)
                    file_content += str(fileinfo["files"][0]["content"]) + '\n'
                    file_name = fileinfo["files"][0]["result"]["name"]
                    formatted_names = f'[{file_name}](wps365://files/)'
                    matches = list(re.finditer(r'ask:', questions))
                    if matches:
                        last_pos = matches[-1].end()
                        questions = questions[:last_pos] + formatted_names + questions[last_pos:]
                    # questions += f'ask:{formatted_names}{Content}\n'

                if Role == "assistant" and Type in valid_assistant_types:
                    # 追加到 assistant_responses 中

                    if Type in{ "canvas_replacement","docx_edit_operation"}:
                        canvas_replacement = json.dumps(json.loads(Content),ensure_ascii=False,indent=4)
                        # canvas_replacement += json.dumps(Content,ensure_ascii=False,indent=4)+'\n'


                    else:
                        assistant_responses.append(Content)
                    codetype = False


            else:
                data.append({
                    "SessionID": f'\'{nowSessionID}',
                    "SessionCreateTime": SessionCreateTime,
                    "CreatorID": CreatorID,
                    "CompanyID": CompanyID,
                     "问题轮次": lunci,
                    "划词内容": selection_str,
                    "问题": questions.strip(),
                    "code": codes.strip(),
                    "command": command,
                    "agent": agent,
                    "client_type": client_type,
                    "文件内容": file_content,
                    "编辑回答": canvas_replacement,
                    **{f"第{idx + 1}个回答": assistant_responses[idx] if idx < len(assistant_responses) else ""
                       for idx
                       in
                       range(len(assistant_responses))}
                })
                lunci = 0
                file_content = ""
                questions = ""
                codes = ""
                command = ""
                assistant_responses = []
                canvas_replacement = ""
                nowSessionID = SessionID
                if Role == "user":
                    if assistant_responses:
                        data.append({
                            "SessionID": f'\'{nowSessionID}',
                            "SessionCreateTime": SessionCreateTime,
                            "CreatorID": CreatorID,
                            "CompanyID": CompanyID,
                             "问题轮次": lunci,
                            "划词内容": selection_str,
                            "问题": questions.strip(),
                            "code": codes.strip(),
                            "command": command,
                            "agent": agent,
                            "client_type": client_type,
                            "文件内容": file_content,
                            "编辑回答": canvas_replacement,
                            **{f"第{idx + 1}个回答": assistant_responses[idx] if idx < len(assistant_responses) else ""
                               for idx
                               in
                               range(len(assistant_responses))}
                        })
                    lunci += 1
                    file_content = ""
                    questions = ""
                    codes = ""
                    command = ""
                    # agent = ""
                    assistant_responses = []
                    canvas_replacement = ""
                    # print(Content)
                    origin_data_json = json.loads(origin_data)
                    agent = origin_data_json.get("context_args", {}).get("agent", "")
                    client_type = origin_data_json.get("client_type", "")

                    if origin_data_json and isinstance(origin_data_json, dict):

                        file_infos = origin_data_json.get("file_infos", [])
                        quote_files = origin_data_json.get("quote_files", [])
                        command += f"{origin_data_json.get("command", "")} "

                        if file_infos:
                            # 提取每个文件的 file_name
                            file_names = [f.get("file_name", "") for f in file_infos if f.get("file_name", "")]
                            print(file_names)

                        else:
                            file_names = []  # 如果 file_infos 为空，设置为空列表
                    else:
                        file_names = []  # 如果 origin_data_json 不是有效字典或为 None，给空列表

                    # 格式化文件名为 [文件名](wps365://files/)
                    formatted_names = ' '.join(f'[{name}](wps365://files/)' for name in file_names)

                    selection = origin_data_json.get("command_args", {}).get("selection", "")
                    if selection:
                        selection_str = selection
                    else:
                        selection_str = ""

                    questions += f'ask:{formatted_names}{Content}\n'
                    if codes != "":
                        codes += '\n'
                        command += '\n'

                if Role == "assistant" and Type == "tool_call":
                    tool_call = json.loads(Content)
                    codes += f'{tool_call.get("request", {}).get("tool_id", "")} '
                    codetype = True
                if Role == "assistant" and Type == "parsefile":
                    fileinfo = json.loads(origin_data)
                    file_content += str(fileinfo["files"][0]["content"]) + '\n'
                    file_name = fileinfo["files"][0]["result"]["name"]
                    # print (fileinfo)
                    formatted_names = f'[{file_name}](wps365://files/)'
                    matches = list(re.finditer(r'ask:', questions))
                    if matches:
                        last_pos = matches[-1].end()
                        questions = questions[:last_pos] + formatted_names + questions[last_pos:]
                    # questions += f'ask:{formatted_names}{Content}\n'

                if Role == "assistant" and Type in valid_assistant_types:
                    # 追加到 assistant_responses 中

                    if Type in {"canvas_replacement","docx_edit_operation"}:
                        canvas_replacement = json.dumps(Content,ensure_ascii=False,indent=4)

                    else:
                        assistant_responses.append(Content)

                    codetype = False

        if questions and codes:
            data.append({
                "SessionID": f'\'{nowSessionID}',
                "SessionCreateTime": SessionCreateTime,
                "CreatorID": CreatorID,
                "CompanyID": CompanyID,
                "问题轮次": lunci,
                "划词内容": selection_str,
                "问题": questions.strip(),
                "code": codes.strip(),
                "command": command,
                "agent": agent,
                "client_type": client_type,
                "文件内容": file_content,
                "编辑回答": canvas_replacement,
                **{f"第{idx + 1}个回答": assistant_responses[idx] if idx < len(assistant_responses) else ""
                   for idx
                   in
                   range(len(assistant_responses))}
            })


        # 全量
        output_df = pd.DataFrame(data)

        def clean_illegal_chars(val):
            if isinstance(val, str):
                return re.sub(r"[\x00-\x08\x0B\x0C\x0E-\x1F]", "", val)
            return val

        # 对 DataFrame 应用清理（这行加在写入前）
        output_df = output_df.applymap(clean_illegal_chars)
        # 创建本地表格文件，并写入
        output_df.to_excel(output_file_path, index=False)

    except FileNotFoundError:
        print(f"错误: 找不到文件 {input_file_path}")
    except pd.errors.EmptyDataError:
        # 如果文件为空或者只有表头，pandas可能会抛出这个异常
        print(f"警告: 文件 '{input_filename}' 为空或只有表头，已跳过此文件。")
    except Exception as e:
        print(f"处理文件 {input_filename} 时发生未知错误: {e}")


def batch_decompress_gz_to_current_directory(source_folder):
    """
    批量解压指定文件夹中的所有 .gz 文件，解压到源文件夹。

    Args:
        source_folder (str): 包含 .gz 文件的源文件夹路径。
    """
    # 遍历源文件夹中的所有文件
    for filename in os.listdir(source_folder):
        # 检查文件是否为 .gz 格式
        if filename.endswith(".gz"):
            gz_file_path = os.path.join(source_folder, filename)

            # 获取解压后文件的名称（移除 .gz 后缀）
            output_filename = os.path.splitext(filename)[0]
            output_file_path = os.path.join(source_folder, output_filename)

            try:
                with gzip.open(gz_file_path, 'rb') as f_in:
                    with open(output_file_path, 'wb') as f_out:
                        print(f"正在解压: {filename} -> {output_filename}")
                        shutil.copyfileobj(f_in, f_out)
                        print(f"解压完成: {output_filename}")
            except gzip.BadGzipFile:
                print(f"警告: 文件 {filename} 不是一个有效的 .gz 文件，已跳过。")
            except Exception as e:
                print(f"解压文件 {filename} 时发生错误: {e}")

def merge_xlsx_files(file_directory):
    # 遍历file_directory目录下的xlsx文件，合并为一个xlsx
    xlsx_files = []
    merged_data = []
    
    # 遍历目录，找到所有xlsx文件
    for filename in os.listdir(file_directory):
        if filename.endswith(".xlsx"):
            file_path = os.path.join(file_directory, filename)
            xlsx_files.append(file_path)
            print(f"发现xlsx文件: {filename}")
    
    if not xlsx_files:
        print("未找到任何xlsx文件")
        return
    
    print(f"共找到 {len(xlsx_files)} 个xlsx文件，开始合并...")
    
    # 读取并合并所有xlsx文件
    for file_path in xlsx_files:
        try:
            df = pd.read_excel(file_path)
            merged_data.append(df)
            print(f"已读取: {os.path.basename(file_path)}, 行数: {len(df)}")
        except Exception as e:
            print(f"读取文件 {os.path.basename(file_path)} 时出错: {e}")
    
    if merged_data:
        # 合并所有数据
        merged_df = pd.concat(merged_data, ignore_index=True)
        
        # 生成合并后的文件名
        merged_filename = "merged_data.xlsx"
        merged_file_path = os.path.join(file_directory, merged_filename)
        
        # 写入合并后的文件
        merged_df.to_excel(merged_file_path, index=False)
        print(f"合并完成! 总行数: {len(merged_df)}, 输出文件: {merged_filename}")
    else:
        print("没有成功读取任何数据")
    


if __name__ == '__main__':
    # 解压
    batch_decompress_gz_to_current_directory(file_directory)
    #提取
    for filename in os.listdir(file_directory):
        # 检查文件是否以 .csv 结尾
        if filename.endswith(".csv"):
            # 设置输入和输出文件名
            input_filename = filename
            output_filename = os.path.splitext(filename)[0] + ".xlsx"
            # 调用 run 函数处理文件
            print(f'csv文件名:{input_filename}')
            print(f'xlsx文件名:{output_filename}')
            run(input_filename, output_filename)

    merge_xlsx_files(file_directory)





