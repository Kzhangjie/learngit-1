import pandas as pd
import json
import openpyxl
from openpyxl import Workbook
from openpyxl.cell.cell import ILLEGAL_CHARACTERS_RE
import re
from datetime import datetime


def clean_text(text):
    """清理文本中的非法字符"""
    if text is None:
        return ""
    text_str = str(text)
    try:
        return ILLEGAL_CHARACTERS_RE.sub('', text_str)
    except Exception:
        return re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", "", text_str)


def parse_origin_data(origin_data_str):
    """解析 OriginData JSON 字段"""
    try:
        if origin_data_str and origin_data_str != '':
            return json.loads(origin_data_str)
        return {}
    except (json.JSONDecodeError, TypeError):
        return {}


def format_message_content(row):
    """格式化消息内容"""
    content = clean_text(row.get('Content', ''))
    role = row.get('Role', '')
    msg_type = row.get('Type', '')
    create_time = row.get('MessageCreateTime', '')
    
    # 构建消息信息
    message_info = {
        'MessageID': row.get('MessageID', ''),
        'Role': role,
        'Type': msg_type,
        'Content': content,
        'CreateTime': create_time,
        'MessageStatus': row.get('MessageStatus', ''),
        'GroupID': row.get('GroupID', '')
    }
    
    # 解析 OriginData
    origin_data = parse_origin_data(row.get('OriginData', ''))
    if origin_data:
        message_info['OriginData'] = origin_data
    
    return message_info


def aggregate_sidebar_sessions(csv_file_path):
    """
    聚合 sidebar CSV 数据按 SessionID 分组
    
    Args:
        csv_file_path: CSV 文件路径
        
    Returns:
        dict: 按 SessionID 分组的会话数据
    """
    print(f"开始处理文件: {csv_file_path}")
    
    # 读取CSV文件
    df = pd.read_csv(csv_file_path, encoding='utf-8-sig')
    print(f"总共读取 {len(df)} 行数据")
    
    # 按SessionID分组
    session_dict = {}
    
    for index, row in df.iterrows():
        session_id = str(row['SessionID'])
        
        # 如果session不存在，创建新的session
        if session_id not in session_dict:
            session_dict[session_id] = {
                'SessionInfo': {
                    'SessionID': session_id,
                    'SessionStatus': row.get('SessionStatus', ''),
                    'CreatorID': row.get('CreatorID', ''),
                    'SessionCreateTime': row.get('SessionCreateTime', ''),
                    'CompanyID': row.get('CompanyID', ''),
                    'SessionTitle': clean_text(row.get('SessionTitle', '')),
                    'AgentID': row.get('AgentID', ''),
                    'SourceType': row.get('SourceType', ''),
                    'SessionType': row.get('SessionType', ''),
                },
                'Messages': []
            }
        
        # 格式化并添加消息
        message = format_message_content(row)
        session_dict[session_id]['Messages'].append(message)
    
    # 按消息创建时间排序每个session的消息
    for session_id in session_dict:
        session_dict[session_id]['Messages'].sort(
            key=lambda x: x.get('CreateTime', ''), 
            reverse=False
        )
    
    print(f"共处理了 {len(session_dict)} 个会话")
    
    return session_dict


def save_to_excel(session_dict, output_path):
    """
    将聚合的会话数据保存为Excel文件
    
    Args:
        session_dict: 聚合的会话数据
        output_path: 输出Excel文件路径
    """
    wb = Workbook()
    wb.remove(wb.active)  # 删除默认sheet
    
    # 统计信息
    total_sessions = len(session_dict)
    total_messages = sum(len(session['Messages']) for session in session_dict.values())
    
    # 创建汇总sheet
    summary_ws = wb.create_sheet(title="汇总信息")
    summary_ws.cell(row=1, column=1, value="统计项")
    summary_ws.cell(row=1, column=2, value="数量")
    summary_ws.cell(row=2, column=1, value="总会话数")
    summary_ws.cell(row=2, column=2, value=total_sessions)
    summary_ws.cell(row=3, column=1, value="总消息数")
    summary_ws.cell(row=3, column=2, value=total_messages)
    summary_ws.cell(row=4, column=1, value="处理时间")
    summary_ws.cell(row=4, column=2, value=datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    
    # 为每个session创建sheet（限制前50个session避免Excel sheet过多）
    session_count = 0
    for session_id, session_data in session_dict.items():
        if session_count >= 50:  # Excel最多支持的sheet数量有限
            print(f"已创建50个sheet，剩余会话将写入汇总数据...")
            break
            
        session_count += 1
        
        # 创建sheet名称（Excel限制31字符）
        sheet_name = f"Session_{session_id}"[:31]
        try:
            ws = wb.create_sheet(title=sheet_name)
        except:
            ws = wb.create_sheet(title=f"Session_{session_count}")
        
        current_row = 1
        
        # 写入会话信息
        session_info = session_data['SessionInfo']
        ws.cell(row=current_row, column=1, value="会话基本信息")
        current_row += 1
        
        for key, value in session_info.items():
            ws.cell(row=current_row, column=1, value=key)
            ws.cell(row=current_row, column=2, value=clean_text(str(value)))
            current_row += 1
        
        current_row += 1
        ws.cell(row=current_row, column=1, value="消息列表")
        current_row += 1
        
        # 写入消息头
        headers = ["消息ID", "角色", "类型", "内容", "创建时间", "状态", "分组ID"]
        for col, header in enumerate(headers, 1):
            ws.cell(row=current_row, column=col, value=header)
        current_row += 1
        
        # 写入消息内容
        for message in session_data['Messages']:
            ws.cell(row=current_row, column=1, value=message.get('MessageID', ''))
            ws.cell(row=current_row, column=2, value=message.get('Role', ''))
            ws.cell(row=current_row, column=3, value=message.get('Type', ''))
            
            # 处理长内容，截取前1000字符
            content = message.get('Content', '')
            if len(content) > 30000:
                content = content[:30000] + "...[截断]"
            ws.cell(row=current_row, column=4, value=content)
            
            ws.cell(row=current_row, column=5, value=message.get('CreateTime', ''))
            ws.cell(row=current_row, column=6, value=message.get('MessageStatus', ''))
            ws.cell(row=current_row, column=7, value=message.get('GroupID', ''))
            
            current_row += 1
            
            # 如果有OriginData，添加额外信息
            if 'OriginData' in message and message['OriginData']:
                ws.cell(row=current_row, column=1, value="OriginData")
                ws.cell(row=current_row, column=4, value=json.dumps(message['OriginData'], ensure_ascii=False, indent=2)[:30000])
                current_row += 1
        
        current_row += 2
    
    # 创建详细数据sheet（包含所有会话的简要信息）
    detail_ws = wb.create_sheet(title="所有会话详情")
    detail_headers = ["会话ID", "标题", "创建时间", "创建者ID", "消息数量", "最后消息时间", "会话类型"]
    for col, header in enumerate(detail_headers, 1):
        detail_ws.cell(row=1, column=col, value=header)
    
    detail_row = 2
    for session_id, session_data in session_dict.items():
        session_info = session_data['SessionInfo']
        messages = session_data['Messages']
        
        detail_ws.cell(row=detail_row, column=1, value=session_id)
        detail_ws.cell(row=detail_row, column=2, value=session_info.get('SessionTitle', ''))
        detail_ws.cell(row=detail_row, column=3, value=session_info.get('SessionCreateTime', ''))
        detail_ws.cell(row=detail_row, column=4, value=session_info.get('CreatorID', ''))
        detail_ws.cell(row=detail_row, column=5, value=len(messages))
        
        # 最后消息时间
        last_msg_time = messages[-1].get('CreateTime', '') if messages else ''
        detail_ws.cell(row=detail_row, column=6, value=last_msg_time)
        detail_ws.cell(row=detail_row, column=7, value=session_info.get('SessionType', ''))
        
        detail_row += 1
    
    # 保存文件
    wb.save(output_path)
    print(f"Excel文件已保存到: {output_path}")
    print(f"包含 {total_sessions} 个会话，{total_messages} 条消息")
    
    return output_path


if __name__ == "__main__":
    # 输入文件路径
    csv_file_path = r"D:\lingxi\user_data_sidebar\1757865600-1757869200-sidebar.csv"
    
    # 聚合会话数据
    session_dict = aggregate_sidebar_sessions(csv_file_path)
    
    # 输出Excel文件路径
    output_path = r"D:\lingxi\user_data_sidebar\sidebar_sessions_aggregated.xlsx"
    
    # 保存为Excel
    save_to_excel(session_dict, output_path)
    
    # 打印统计信息
    print("\n=== 处理完成 ===")
    print(f"总会话数: {len(session_dict)}")
    
    # 显示前5个会话的信息
    print("\n=== 前5个会话概览 ===")
    for i, (session_id, session_data) in enumerate(list(session_dict.items())[:5]):
        session_info = session_data['SessionInfo']
        messages = session_data['Messages']
        print(f"会话 {i+1}: {session_id}")
        print(f"  标题: {session_info.get('SessionTitle', '')[:50]}...")
        print(f"  消息数: {len(messages)}")
        print(f"  创建时间: {session_info.get('SessionCreateTime', '')}")
        print()



