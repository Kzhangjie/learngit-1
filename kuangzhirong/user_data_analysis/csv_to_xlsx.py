import csv
import pandas as pd
from openpyxl import Workbook
from openpyxl.utils.dataframe import dataframe_to_rows
from openpyxl.cell.cell import ILLEGAL_CHARACTERS_RE
import os
import sys
import re
from typing import List, Tuple, Any


def split_long_text(text: str, max_chars: int = 20000) -> List[str]:
    """
    将超过最大字符数的文本分割成多个片段
    
    Args:
        text: 要分割的文本
        max_chars: 最大字符数，默认20000
    
    Returns:
        分割后的文本片段列表
    """
    if not isinstance(text, str):
        text = str(text) if text is not None else ""
    # 去除 Excel 不允许的控制字符，防止 openpyxl IllegalCharacterError
    try:
        text = ILLEGAL_CHARACTERS_RE.sub('', text)
    except Exception:
        # 极端情况下备用正则（与 openpyxl 定义一致）
        text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", "", text)
    
    if len(text) <= max_chars:
        return [text]
    
    segments = []
    for i in range(0, len(text), max_chars):
        segments.append(text[i:i + max_chars])
    
    return segments


def process_row_data(row: List[Any], max_chars: int = 20000) -> List[str]:
    """
    处理单行数据，将长文本分割到后续列中
    
    Args:
        row: 原始行数据
        max_chars: 最大字符数
    
    Returns:
        处理后的行数据，包含原列和扩展列
    """
    result_row = []
    
    for cell in row:
        cell_str = str(cell)
        segments = split_long_text(cell_str, max_chars)
        
        # 第一个片段放在原位置
        result_row.append(segments[0])
        
        # 后续片段放在接下来的列中
        for segment in segments[1:]:
            result_row.append(segment)
    
    return result_row


def csv_to_xlsx(csv_file_path: str, xlsx_file_path: str = None, max_chars: int = 20000, encoding: str = 'utf-8'):
    """
    将CSV文件转换为XLSX文件，自动处理超长文本
    
    Args:
        csv_file_path: CSV文件路径
        xlsx_file_path: XLSX文件路径，如果为None则自动生成
        max_chars: 单元格最大字符数，默认20000
        encoding: CSV文件编码，默认utf-8
    """
    if not os.path.exists(csv_file_path):
        raise FileNotFoundError(f"CSV文件不存在: {csv_file_path}")
    
    # 自动生成输出文件名
    if xlsx_file_path is None:
        base_name = os.path.splitext(csv_file_path)[0]
        xlsx_file_path = f"{base_name}.xlsx"
    
    print(f"开始转换: {csv_file_path} -> {xlsx_file_path}")
    print(f"最大字符数限制: {max_chars}")
    
    # 创建工作簿
    wb = Workbook()
    ws = wb.active
    ws.title = "Sheet1"
    
    # 统计信息
    total_rows = 0
    processed_rows = 0
    split_cells = 0
    
    try:
        # 设置CSV字段大小限制，尽可能大；部分平台上 sys.maxsize 会溢出，逐步回退
        try:
            csv.field_size_limit(sys.maxsize)
        except OverflowError:
            limit = 2 ** 31 - 1
            while True:
                try:
                    csv.field_size_limit(limit)
                    break
                except OverflowError:
                    limit = limit // 2
                    if limit < 1024 * 1024:
                        # 退到1MB也不行就放弃，让后续逻辑接手
                        break
        
        # 读取CSV文件
        with open(csv_file_path, 'r', encoding=encoding, newline='') as csvfile:
            # 尝试自动检测分隔符（失败则回退到逗号）
            sample = csvfile.read(4096)
            csvfile.seek(0)
            delimiter = ','
            try:
                if sample:
                    sniffer = csv.Sniffer()
                    delimiter = sniffer.sniff(sample).delimiter
            except csv.Error:
                delimiter = ','
            
            reader = csv.reader(csvfile, delimiter=delimiter)
            
            current_row = 1
            
            for row in reader:
                total_rows += 1
                
                # 处理当前行数据
                processed_row_data = process_row_data(row, max_chars)
                
                # 检查是否有分割
                split_cells += sum(
                    len(split_long_text(str(cell), max_chars)) - 1
                    for cell in row if isinstance(cell, str) and len(cell) > max_chars
                )
                
                # 写入处理后的行数据（清洗非法字符）
                for col_idx, cell_value in enumerate(processed_row_data, 1):
                    if cell_value is None:
                        safe_val = ""
                    else:
                        cell_str = str(cell_value)
                        try:
                            safe_val = ILLEGAL_CHARACTERS_RE.sub('', cell_str)
                        except Exception:
                            safe_val = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", "", cell_str)
                    ws.cell(row=current_row, column=col_idx, value=safe_val)
                
                current_row += 1
                processed_rows += 1
                
                # 进度提示
                if total_rows % 1000 == 0:
                    print(f"已处理 {total_rows} 行...")
    
    except UnicodeDecodeError:
        # 尝试其他编码
        print(f"使用 {encoding} 编码失败，尝试使用 gbk 编码...")
        try:
            return csv_to_xlsx(csv_file_path, xlsx_file_path, max_chars, 'gbk')
        except UnicodeDecodeError:
            print("尝试使用 latin-1 编码...")
            return csv_to_xlsx(csv_file_path, xlsx_file_path, max_chars, 'latin-1')
    
    except csv.Error as e:
        print(f"CSV解析错误: {e}")
        print("尝试使用pandas方式读取...")
        return csv_to_xlsx_pandas(csv_file_path, xlsx_file_path, max_chars, encoding)
    
    # 保存文件
    wb.save(xlsx_file_path)
    
    # 输出统计信息
    print(f"\n转换完成!")
    print(f"原始行数: {total_rows}")
    print(f"输出行数: {processed_rows}")
    print(f"分割的长文本单元格数: {split_cells}")
    print(f"输出文件: {xlsx_file_path}")
    
    return xlsx_file_path


def csv_to_xlsx_pandas(csv_file_path: str, xlsx_file_path: str = None, max_chars: int = 20000, encoding: str = 'utf-8'):
    """
    使用pandas的方式转换CSV到XLSX（备选方案）
    
    Args:
        csv_file_path: CSV文件路径
        xlsx_file_path: XLSX文件路径
        max_chars: 单元格最大字符数
        encoding: 文件编码
    """
    if xlsx_file_path is None:
        base_name = os.path.splitext(csv_file_path)[0]
        xlsx_file_path = f"{base_name}_pandas.xlsx"
    
    try:
        # 设置CSV字段大小限制
        try:
            csv.field_size_limit(sys.maxsize)
        except OverflowError:
            csv.field_size_limit(2 ** 31 - 1)
        
        # 读取CSV，使用更宽松的参数
        df = pd.read_csv(
            csv_file_path,
            encoding=encoding,
            low_memory=False,
            engine='python',  # 使用python引擎更宽松
            on_bad_lines='skip'  # 跳过有问题的行
        )
        
        # 若无需分割，直接导出（先清洗非法字符）
        if not any(
            df[col].apply(lambda v: isinstance(v, str) and len(v) > max_chars).any()
            for col in df.columns
        ):
            df_clean = df.copy()
            for col in df_clean.columns:
                if df_clean[col].dtype == object:
                    df_clean[col] = df_clean[col].astype(str).apply(
                        lambda s: ILLEGAL_CHARACTERS_RE.sub('', s) if isinstance(s, str) else s
                    )
            df_clean.to_excel(xlsx_file_path, index=False, engine='openpyxl')
            print(f"转换完成: {xlsx_file_path}")
            return xlsx_file_path
        
        # 计算每列最大分段数
        max_segments_per_col = {}
        for col in df.columns:
            def count_segments(value: Any) -> int:
                if value is None or (isinstance(value, float) and pd.isna(value)):
                    return 1
                text = str(value)
                return max(1, (len(text) + max_chars - 1) // max_chars)
            max_segments_per_col[col] = int(df[col].apply(count_segments).max())
        
        # 构建新列名
        new_columns: List[str] = []
        for col in df.columns:
            new_columns.append(col)
            for i in range(1, max_segments_per_col[col]):
                new_columns.append(f"{col}_overflow_{i}")
        
        # 生成新数据
        expanded_rows: List[List[Any]] = []
        for _, row in df.iterrows():
            expanded_row: List[Any] = []
            for col in df.columns:
                value = row[col]
                if value is None or (isinstance(value, float) and pd.isna(value)):
                    segments = [""]
                else:
                    # 清洗非法字符后再分段
                    try:
                        value_str = ILLEGAL_CHARACTERS_RE.sub('', str(value))
                    except Exception:
                        value_str = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", "", str(value))
                    segments = split_long_text(value_str, max_chars)
                # 按该列最大分段数补齐
                needed = max_segments_per_col[col]
                if len(segments) < needed:
                    segments = segments + [""] * (needed - len(segments))
                expanded_row.extend(segments)
            expanded_rows.append(expanded_row)
        
        expanded_df = pd.DataFrame(expanded_rows, columns=new_columns)
        expanded_df.to_excel(xlsx_file_path, index=False, engine='openpyxl')
        print(f"转换完成: {xlsx_file_path}")
        return xlsx_file_path
        
    except Exception as e:
        print(f"pandas转换失败: {e}")
        return None


if __name__ == "__main__":
    # 测试代码
    csv_file_path = r"D:\lingxi\user_data_sidebar\1757865600-1757869200-sidebar.csv"
    # 默认用 utf-8-sig 处理 BOM
    csv_to_xlsx(csv_file_path, encoding='utf-8-sig')
