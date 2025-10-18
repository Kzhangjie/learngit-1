import pandas as pd
import json
import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from airsheet_sdk import airsheet
from dotenv import load_dotenv
from typing import Dict, List, Any, Tuple



# 加载环境变量
load_dotenv()
WPS_SID = os.getenv("WPS_SID")

# 配置常量
FILE_ID = "ce2dd3WBW1vW"

# 定义所有需要处理的工作表
SHEET_NAMES = [
    "chat",
    "data_analysis", 
    "table_operation",
    "websearch",
    "generate_ppt",
    "generate_image",
    "generate_mindmap",
    "url_fetch"
]

# 定义所有支持的功能类型
SUPPORTED_FUNCTIONS = {
    "chat", "generate_ppt", "url_fetch", "help", 
    "generate_mindmap", "generate_image", "websearch", 
    "data_analysis", "table_operation"
}

# 定义统计维度
STATISTICS_COLUMNS = [
    "websearch", "chat", "generate_ppt", "url_fetch",
    "data_analysis", "table_operation", "generate_mindmap", 
    "generate_image", "多分发", "没分发", "其他"
]


def initialize_case_statistics() -> Dict[str, int]:
    """
    初始化单个case类型的统计字典
    
    Returns:
        Dict[str, int]: 包含所有统计维度的初始化字典
    """
    return {
        "总数": 0,
        "websearch": 0,
        "chat": 0, 
        "generate_ppt": 0,
        "url_fetch": 0,
        "data_analysis": 0,
        "table_operation": 0,
        "generate_mindmap": 0,
        "generate_image": 0,
        "多分发": 0,
        "没分发": 0,
        "其他": 0
    }


def parse_function_data(func_item: Any) -> Tuple[str, Dict]:
    """
    解析函数数据，支持字符串JSON和字典两种格式
    
    Args:
        func_item: 函数项，可能是字符串JSON或字典
        
    Returns:
        Tuple[str, Dict]: 函数名和解析后的字典
    """
    try:
        if isinstance(func_item, str):
            # 检查是否为空字符串
            if func_item == "":
                return "", {}
            func_json = json.loads(func_item)
            func_name = func_json.get("function", "")
            return func_name, func_json
        elif isinstance(func_item, dict):
            func_name = func_item.get("function", "")
            return func_name, func_item
        else:
            print(f"不支持的函数数据类型: {type(func_item)}")
            return "", {}
    except json.JSONDecodeError as e:
        print(f"JSON解析错误: {e}")
        return "", {}


def is_case_match(case_type: str, func_name: str) -> bool:
    """
    判断case类型与函数名是否匹配
    
    Args:
        case_type: 断言的case类型
        func_name: 实际调度的函数名
        
    Returns:
        bool: 是否匹配
    """
    # 精确匹配
    if case_type == func_name:
        return True
    
    # 处理包含"/"的复合case类型
    if "/" in case_type:
        parts = case_type.split("/")
        return func_name in parts
    
    return False


def update_statistics_for_function(case_statistics: Dict, case_type: str, 
                                 func_name: str, func_json: Dict) -> bool:
    """
    根据函数调度结果更新统计信息
    
    Args:
        case_statistics: 全局统计字典
        case_type: case类型
        func_name: 函数名
        func_json: 函数详细信息
        
    Returns:
        bool: 是否匹配成功
    """
    # 确保case_type在统计中存在
    if case_type not in case_statistics:
        case_statistics[case_type] = initialize_case_statistics()
    
    # 累计总数
    case_statistics[case_type]["总数"] += 1
    
    # 处理一般情况
    if func_name in case_statistics[case_type]:
        case_statistics[case_type][func_name] += 1
        # 判断是否匹配
        return is_case_match(case_type, func_name)
    elif func_name not in SUPPORTED_FUNCTIONS:
        # case_statistics[case_type]["其他"] += 1
        return False
    
    return True


def process_new_format_data(case_list: List[str], check_data: List, 
                          case_statistics: Dict, question: str) -> bool:
    """
    处理新格式数据（check_data为列表）
    主要统计不同SUPPORTED_FUNCTIONS的各种分发结果
    
    Args:
        case_list: 预期断言列表
        check_data: 实际模型调度结果列表
        case_statistics: 全局统计字典
        question: 用例编号
        
    Returns:
        bool: 是否全部通过
    """
    is_passed = True

    # 判断case_list和check_data是否长度一致
    if len(case_list) != len(check_data):
        print(f"断言和调度结果长度不一致, case_list: {case_list}, check_data: {check_data}")
        return False
    
    # 处理每个case断言
    for case_index, case_item in enumerate(case_list):
        # 获取实际分发结果
        actual_result = check_data[case_index]
        
        # 检查是否为空字符串，统计到"没分发"
        if actual_result == "":
            expected_func = case_item.strip()
            # 处理包含"/"的复合case类型
            if "/" in expected_func:
                expected_func = expected_func.split("/")[0]  # 取第一个作为统计对象
            # 处理包含空格的多分发case类型
            if " " in expected_func:
                expected_func = expected_func.split(" ")[0]  # 取第一个作为统计对象
                
            if expected_func not in case_statistics:
                case_statistics[expected_func] = initialize_case_statistics()
            
            case_statistics[expected_func]["总数"] += 1
            case_statistics[expected_func]["没分发"] += 1
            is_passed = False
            print(f"检测到没分发 - 用例: {question}, 预期: {expected_func}, 实际: 空字符串")
            continue
        
        # 解析预期结果
        if "/" in case_item:
            # 包含/的情况，认为是并列意图
            expected_functions = case_item.split("/")
            
            # 遍历每个预期功能，检查是否包含空格（多分发）
            matched = False
            for expected_func in expected_functions:
                if " " in expected_func:
                    # 单个function包含空格，执行多分发逻辑
                    split_cases_multi = expected_func.split(" ")
                    split_actual_result = actual_result.split(" ")
                    
                    if len(split_cases_multi) == 1 and len(split_actual_result) > 1:
                        # 多分发情况：case_list长度为1，但split_actual_result > 1
                        for sub_expected_func in split_cases_multi:
                            if sub_expected_func not in case_statistics:
                                case_statistics[sub_expected_func] = initialize_case_statistics()
                            
                            # case_statistics[sub_expected_func]["总数"] += 1
                            case_statistics[sub_expected_func]["多分发"] += 1
                            
                            # 同时统计实际分发结果
                            if actual_result in SUPPORTED_FUNCTIONS:
                                case_statistics[sub_expected_func][actual_result] += 1
                            
                            is_passed = False
                            print(f"检测到多分发 - 用例: {question}, 预期: {split_cases_multi}, 实际: {actual_result}")
                        matched = True

                    elif len(split_actual_result) == len(split_cases_multi) and len(split_actual_result) > 1:
                        for index, sub_expected_func in enumerate(split_cases_multi):
                            if sub_expected_func not in case_statistics:
                                case_statistics[sub_expected_func] = initialize_case_statistics()

                            case_statistics[sub_expected_func]["总数"] += 1
                            except_case = split_cases_multi[index]

                            if sub_expected_func in SUPPORTED_FUNCTIONS:
                                case_statistics[except_case][sub_expected_func] += 1
                            else:
                                is_passed = False
                                print(f"检测到多分发 - 用例: {question}, 预期: {split_cases_multi}, 实际: {split_actual_result}")
                        matched = True

                    elif len(split_actual_result) == 1 and len(split_cases_multi) > 1:
                        # 暂时都放到其他
                        if expected_func not in case_statistics:
                            case_statistics[expected_func] = initialize_case_statistics()
                        # case_statistics[expected_func]["总数"] += 1
                        if actual_result in SUPPORTED_FUNCTIONS and actual_result == expected_func:
                            case_statistics[expected_func][actual_result] += 1
                        else:
                            case_statistics[expected_func][actual_result] += 1
                            is_passed = False
                            print(f"检测到多分发 - 用例: {question}, 预期: {split_cases_multi}, 实际: {split_actual_result}")
                        matched = True

                    else:
                        # 正常单一预期情况（在多分发context中）
                        if expected_func not in case_statistics:
                            case_statistics[expected_func] = initialize_case_statistics()
                        
                        case_statistics[expected_func]["总数"] += 1
                        
                        # 根据实际结果进行统计
                        if actual_result in SUPPORTED_FUNCTIONS:
                            case_statistics[expected_func][actual_result] += 1
                            
                            # 检查是否匹配
                            if actual_result != expected_func:
                                is_passed = False
                        else:
                            is_passed = False
                        matched = True
                else:
                    # 单个function不包含空格，检查是否匹配
                    if actual_result == expected_func:
                        # 匹配成功，只为匹配的功能统计
                        if actual_result not in case_statistics:
                            case_statistics[actual_result] = initialize_case_statistics()
                        
                        case_statistics[actual_result]["总数"] += 1
                        
                        if actual_result in SUPPORTED_FUNCTIONS:
                            case_statistics[actual_result][actual_result] += 1
                        matched = True
            
            # 如果没有匹配到任何预期功能，为第一个预期功能统计错误结果
            if not matched:
                first_expected = expected_functions[0]
                if first_expected not in case_statistics:
                    case_statistics[first_expected] = initialize_case_statistics()
                
                case_statistics[first_expected]["总数"] += 1
                
                if actual_result in SUPPORTED_FUNCTIONS:
                    case_statistics[first_expected][actual_result] += 1
                
                is_passed = False
        else:
            # 不包含/的情况
            split_cases_multi = case_item.split(" ")
            split_actual_result = actual_result.split(" ")
            if len(case_list) == 1 and len(split_actual_result) > 1:
                # 多分发情况：case_list长度为1，但split_cases_multi > 1
                for expected_func in split_cases_multi:
                    if expected_func not in case_statistics:
                        case_statistics[expected_func] = initialize_case_statistics()
                    
                    # case_statistics[expected_func]["总数"] += 1
                    case_statistics[expected_func]["多分发"] += 1
                    
                    # 同时统计实际分发结果
                    if actual_result in SUPPORTED_FUNCTIONS:
                        case_statistics[expected_func][actual_result] += 1
                    
                    is_passed = False
                    print(f"检测到多分发 - 用例: {question}, 预期: {split_cases_multi}, 实际: {actual_result}")

            elif len(split_actual_result)  == len(split_cases_multi) and len(split_actual_result) > 1:
                # 多分发情况：分发结果数量相同
                for index, expected_func in enumerate(split_cases_multi):
                    if expected_func not in case_statistics:
                        case_statistics[expected_func] = initialize_case_statistics()

                    case_statistics[expected_func]["总数"] += 1
                    except_case = split_cases_multi[index]

                    if expected_func in SUPPORTED_FUNCTIONS:
                        case_statistics[except_case][expected_func] += 1
                    
            else:
                # 正常单一预期情况
                expected_func = case_item.strip()
                
                if expected_func not in case_statistics:
                    case_statistics[expected_func] = initialize_case_statistics()
                
                case_statistics[expected_func]["总数"] += 1
                
                # 根据实际结果进行统计
                if actual_result in SUPPORTED_FUNCTIONS:
                    case_statistics[expected_func][actual_result] += 1
                    
                    # 检查是否匹配
                    if actual_result != expected_func:
                        is_passed = False
                else:
                    # 分发到不支持的功能
                    case_statistics[expected_func]["其他"] += 1
                    is_passed = False
    
    return is_passed


def process_old_format_data(case_list: List[str], check_data: Dict, 
                          case_statistics: Dict, question: str, line_number: int) -> bool:
    """
    处理旧格式数据（check_data为字典）
    
    Args:
        case_list: 断言列表
        check_data: 模型调度结果字典
        case_statistics: 全局统计字典
        question: 用例编号
        line_number: 行号
        
    Returns:
        bool: 是否全部通过
    """
    is_passed = True
    
    # 预处理：构建修正后的case列表
    modified_case_list = []
    for case_index, case_item in enumerate(case_list, start=1):
        split_cases = case_item.split()
        check_key = str(case_index)
        
        # 检查是否存在对应的调度结果
        if check_key in check_data:
            functions_in_check = check_data[check_key]
            # 如果调度结果比断言多，添加"more"标记
            if len(functions_in_check) > len(split_cases):
                print(f"意图多分发, functions_in_check: {functions_in_check}, split_cases: {split_cases}")
                split_cases.append("more")
        
        modified_case_list.append(" ".join(split_cases))
    
    # 处理每个修正后的case
    for case_index, case_item in enumerate(modified_case_list, start=1):
        split_cases = case_item.split()
        check_key = str(case_index)
        
        if check_key in check_data:
            functions_in_check = check_data[check_key]
            
            # 处理每个意图
            for func_index, case_type in enumerate(split_cases):
                if func_index < len(functions_in_check):
                    # 解析函数数据
                    func_name, func_json = parse_function_data(functions_in_check[func_index])
                    
                    if func_name:
                        # 更新统计并检查匹配
                        match_result = update_statistics_for_function(
                            case_statistics, case_type, func_name, func_json
                        )
                        if not match_result:
                            is_passed = False
                    else:
                        # 函数名为空，统计到"没分发"
                        if case_type not in case_statistics:
                            case_statistics[case_type] = initialize_case_statistics()
                        
                        case_statistics[case_type]["总数"] += 1
                        case_statistics[case_type]["没分发"] += 1
                        is_passed = False
                        print(f"检测到没分发 - 用例: {question}, 断言: {case_type}, 函数名为空")
                        continue
                else:
                    # 没有对应的函数调度
                    if case_type not in case_statistics:
                        case_statistics[case_type] = initialize_case_statistics()
                    
                    case_statistics[case_type]["总数"] += 1
                    case_statistics[case_type]["没分发"] += 1
                    is_passed = False
                    print(f"没分发 - 用例: {question}, 断言: {case_type}")
        else:
            # 整个case都没有对应的调度结果
            is_passed = False
            print(f"无调度结果 - 用例: {question}")
    
    return is_passed


def process_single_sheet(sheet_name: str, case_statistics: Dict, failed_rows: List) -> None:
    """
    处理单个工作表的数据
    
    Args:
        sheet_name: 工作表名称
        case_statistics: 全局统计字典
        failed_rows: 失败用例列表
    """
    print(f"正在处理工作表: {sheet_name}")
    
    # 初始化并读取数据
    airsheet.init(file_id=FILE_ID, wps_sid=WPS_SID, sheet_name=sheet_name)
    df = airsheet.xl("A:BB", headers=True, sheet_name=sheet_name)
    
    # 数据预处理
    df['行号'] = range(0, len(df))
    
    # 过滤有效数据
    df = df[df['问题1'] != '']
    df = df[df['调度断言'] != '']
    df = df[df['模型调度断言总体'] != '']
    
    print(f"工作表 {sheet_name} 有效数据行数: {len(df)}")
    
    # 处理每一行数据
    for i, row in df.iterrows():
        row_dict = row.to_dict()
        line_number = int(row_dict.get('行号', 0))
        # 预期结果
        case_list = str(row_dict.get('调度断言', '')).splitlines()
        # 实际结果
        check_str = str(row_dict.get('模型调度结果', ''))
        question = row_dict.get('用例编号', '')
        prompts = row_dict.get('prompts', '')
        check_result = row_dict.get('模型调度断言总体', '')
        
        # 解析模型调度结果
        try:
            check_data = json.loads(check_str)
        except json.JSONDecodeError:
            print(f"行号 {line_number} 的调度结果JSON解析失败")
            continue
        
        # 根据数据格式选择处理方式
        if isinstance(check_data, list):
            # 新格式：check_data为列表
            is_passed = process_new_format_data(case_list, check_data, case_statistics, question)
        elif isinstance(check_data, dict):
            # 旧格式：check_data为字典
            is_passed = process_old_format_data(case_list, check_data, case_statistics, question, line_number)
        else:
            print(f"不支持的调度结果格式: {type(check_data)}")
            continue
        
        # 收集失败的用例
        if check_result != "是":
            failed_rows.append(row_dict)


def generate_output_report(case_statistics: Dict) -> pd.DataFrame:
    """
    生成最终的统计报告
    
    Args:
        case_statistics: 全局统计字典
        
    Returns:
        pd.DataFrame: 统计报告DataFrame
    """
    # 定义报告的行和列
    report_rows = [
        "websearch", "chat", "generate_ppt", "url_fetch",
        "data_analysis", "table_operation", "generate_mindmap", "generate_image"
    ]
    
    output_data = []
    
    for row_name in report_rows:
        if row_name == "chat/websearch":
            # 特殊处理复合类型
            chat_websearch_data = case_statistics.get("chat/websearch", {})
            websearch_chat_data = case_statistics.get("websearch/chat", {})
            
            # 汇总数据
            data = []
            for col in STATISTICS_COLUMNS:
                total_count = (chat_websearch_data.get(col, 0) + 
                             websearch_chat_data.get(col, 0))
                data.append(total_count)
            
            total = (chat_websearch_data.get("总数", 0) + 
                    websearch_chat_data.get("总数", 0))
            data.insert(0, total)
        elif row_name in case_statistics:
            # 正常情况
            stats = case_statistics[row_name]
            data = [stats.get(col, 0) for col in STATISTICS_COLUMNS]
            data.insert(0, stats.get("总数", 0))
        else:
            # 没有数据的情况
            data = [0] * (len(STATISTICS_COLUMNS) + 1)
        
        output_data.append(data)
    
    # 创建DataFrame
    columns = ["总数"] + STATISTICS_COLUMNS
    output_df = pd.DataFrame(output_data, index=report_rows, columns=columns)
    
    return output_df


def main():
    """
    主函数：执行完整的数据处理流程
    """
    print("开始执行模型调度断言统计分析...")
    
    # 初始化全局变量
    case_statistics = {}  # 全局统计字典
    failed_rows = []      # 失败用例列表
    
    # 处理每个工作表
    for sheet_name in SHEET_NAMES:
        try:
            process_single_sheet(sheet_name, case_statistics, failed_rows)
        except Exception as e:
            print(f"处理工作表 {sheet_name} 时发生错误: {e}")
            continue
    
    print(f"数据处理完成，共收集到 {len(failed_rows)} 个失败用例")
    
    # 生成统计报告
    print("正在生成统计报告...")
    output_df = generate_output_report(case_statistics)
    
    # 输出结果
    print("统计结果:")
    print(output_df)
    
    # 写入Excel
    try:
        numeric_data = pd.DataFrame(output_df.values)
        airsheet.write_xl(numeric_data, "D6", sheet_name="新统计")
        print("统计结果已写入工作表：新统计")
        
        if failed_rows:
            failed_df = pd.DataFrame(failed_rows)
            airsheet.write_xl(failed_df, "A1", sheet_name="Fail用例汇总")
            print("失败用例已写入工作表：Fail用例汇总")
    except Exception as e:
        print(f"写入Excel时发生错误: {e}")
    
    print("分析完成！")


if __name__ == '__main__':
    main()


