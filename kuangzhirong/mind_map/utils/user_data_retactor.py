"""
WPS Copilot用户数据分析工具
"""

import pandas as pd
import random
import re
import json
import os
import gzip
import shutil
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path
from abc import ABC, abstractmethod
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


@dataclass
class Config:
    """配置类，集中管理所有配置信息"""
    def __init__(self,file_directory: str = r"D:\lingxi\user_data_sidebar\侧边栏"):
        self.file_directory = file_directory
        
    wps_sid: str = ""
    valid_assistant_types: set = None
    
    def __post_init__(self):
        if self.valid_assistant_types is None:
            self.valid_assistant_types = {
                "text", "execution", "long_writer", "ppt_outline_text", "mind_map",
                "ppt_outline_text_v2", "canvas_replacement", "call_summary",
                "docx_edit_operation", "data_analysis", "tabel_operation"
            }


@dataclass
class SessionData:
    """会话数据结构"""
    session_id: str
    session_create_time: str
    creator_id: int
    company_id: int
    question_round: int
    selection_content: str
    questions: str
    codes: str
    command: str
    agent: str
    client_type: str
    file_content: str
    edit_response: str
    assistant_responses: List[str]


class DataFilter(ABC):
    """数据过滤器抽象基类"""
    
    @abstractmethod
    def filter(self, df: pd.DataFrame) -> pd.DataFrame:
        pass


class ETAgentFilter(DataFilter):
    """ET代理过滤器"""
    
    def filter(self, df: pd.DataFrame) -> pd.DataFrame:
        """过滤包含ET代理的用户数据"""
        try:
            filtered_session_ids = df[
                (df['Role'] == 'user') & 
                (df['OriginData'].str.contains(r'"agent":"et"', flags=re.IGNORECASE))
            ]['SessionID']
            return df[df['SessionID'].isin(filtered_session_ids)]
        except Exception as e:
            logger.error(f"过滤数据时出错: {e}")
            return df.copy()


class FileProcessor(ABC):
    """文件处理器抽象基类"""
    
    @abstractmethod
    def process(self, file_path: str) -> bool:
        pass


class CSVProcessor(FileProcessor):
    """CSV文件处理器"""
    
    def __init__(self, config: Config, data_filter: DataFilter):
        self.config = config
        self.data_filter = data_filter
        self.session_parser = SessionDataParser(config)
    
    def process(self, file_path: str) -> bool:
        """处理CSV文件并转换为Excel"""
        try:
            df = self._load_csv(file_path)
            if df is None:
                return False
            
            filtered_df = self.data_filter.filter(df)
            sessions = self.session_parser.parse(filtered_df)
            
            output_path = self._get_output_path(file_path)
            self._save_to_excel(sessions, output_path)
            
            logger.info(f"成功处理文件: {file_path} -> {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"处理文件 {file_path} 时出错: {e}")
            return False
    
    def _load_csv(self, file_path: str) -> Optional[pd.DataFrame]:
        """加载CSV文件"""
        try:
            header = pd.read_csv(file_path, nrows=0)
            df = pd.read_csv(file_path, skiprows=1, header=None)
            df.columns = header.columns
            df.fillna("", inplace=True)
            return df
        except pd.errors.EmptyDataError:
            logger.warning(f"文件为空或只有表头: {file_path}")
            return None
        except FileNotFoundError:
            logger.error(f"文件不存在: {file_path}")
            return None
    
    def _get_output_path(self, input_path: str) -> str:
        """生成输出文件路径"""
        return os.path.splitext(input_path)[0] + ".xlsx"
    
    def _save_to_excel(self, sessions: List[SessionData], output_path: str):
        """保存到Excel文件"""
        data = [self._session_to_dict(session) for session in sessions]
        df = pd.DataFrame(data)
        df = df.applymap(self._clean_illegal_chars)
        df.to_excel(output_path, index=False)
    
    @staticmethod
    def _clean_illegal_chars(val: Any) -> Any:
        """清理非法字符"""
        if isinstance(val, str):
            return re.sub(r"[\x00-\x08\x0B\x0C\x0E-\x1F]", "", val)
        return val
    
    def _session_to_dict(self, session: SessionData) -> Dict[str, Any]:
        """将会话数据转换为字典"""
        result = {
            "SessionID": f"'{session.session_id}",
            "SessionCreateTime": session.session_create_time,
            "CreatorID": session.creator_id,
            "CompanyID": session.company_id,
            "问题轮次": session.question_round,
            "划词内容": session.selection_content,
            "问题": session.questions.strip(),
            "code": session.codes.strip(),
            "command": session.command,
            "agent": session.agent,
            "client_type": session.client_type,
            "文件内容": session.file_content,
            "编辑回答": session.edit_response,
        }
        
        # 添加助手回答
        for idx, response in enumerate(session.assistant_responses):
            result[f"第{idx + 1}个回答"] = response
            
        return result


class SessionDataParser:
    """会话数据解析器"""
    
    def __init__(self, config: Config):
        self.config = config
    
    def parse(self, df: pd.DataFrame) -> List[SessionData]:
        """解析DataFrame为会话数据列表"""
        df['行号'] = range(len(df))
        sessions = []
        current_session = self._init_session_state()
        
        for _, row in df.iterrows():
            row_dict = row.to_dict()
            
            if self._is_new_session(current_session, row_dict):
                if self._has_valid_data(current_session):
                    sessions.append(self._create_session_data(current_session))
                current_session = self._init_session_state()
                current_session['session_id'] = row_dict.get('SessionID')
            
            self._process_row(current_session, row_dict)
        
        # 处理最后一个会话
        if self._has_valid_data(current_session):
            sessions.append(self._create_session_data(current_session))
        
        return sessions
    
    def _init_session_state(self) -> Dict[str, Any]:
        """初始化会话状态"""
        return {
            'session_id': 0,
            'session_create_time': "2025/4/25 14:00:00",
            'creator_id': 0,
            'company_id': 0,
            'question_round': 0,
            'selection_content': "",
            'file_content': "",
            'questions': "",
            'codes': "",
            'command': "",
            'agent': "",
            'client_type': "",
            'assistant_responses': [],
            'canvas_replacement': "",
        }
    
    def _is_new_session(self, current_session: Dict, row_dict: Dict) -> bool:
        """判断是否为新会话"""
        return (current_session['session_id'] != 0 and 
                current_session['session_id'] != row_dict.get('SessionID'))
    
    def _has_valid_data(self, session: Dict) -> bool:
        """判断会话是否有有效数据"""
        return bool(session['questions'] and session['codes'])
    
    def _process_row(self, session: Dict, row_dict: Dict):
        """处理单行数据"""
        role = row_dict.get('Role')
        content_type = row_dict.get('Type')
        
        # 更新会话基本信息
        self._update_session_info(session, row_dict)
        
        if role == "user":
            self._process_user_message(session, row_dict)
        elif role == "assistant":
            self._process_assistant_message(session, row_dict, content_type)
    
    def _update_session_info(self, session: Dict, row_dict: Dict):
        """更新会话基本信息"""
        session['creator_id'] = row_dict.get('CreatorID', 0)
        session['company_id'] = row_dict.get('CompanyID', 0)
        session['session_create_time'] = row_dict.get('SessionCreateTime', session['session_create_time'])
    
    def _process_user_message(self, session: Dict, row_dict: Dict):
        """处理用户消息"""
        try:
            origin_data = json.loads(row_dict.get('OriginData', '{}'))
            
            # 更新代理和客户端信息
            session['agent'] = origin_data.get("context_args", {}).get("agent", "")
            session['client_type'] = origin_data.get("client_type", "")
            session['command'] += f"{origin_data.get('command', '')} "
            
            # 处理文件信息
            file_names = self._extract_file_names(origin_data)
            formatted_names = ' '.join(f'[{name}](wps365://files/)' for name in file_names)
            
            # 处理划词内容
            selection = origin_data.get("command_args", {}).get("selection", "")
            session['selection_content'] = selection
            
            # 添加问题
            content = row_dict.get('Content', '')
            session['questions'] += f'ask:{formatted_names}{content}\n'
            session['question_round'] += 1
            
        except json.JSONDecodeError as e:
            logger.warning(f"解析OriginData失败: {e}")
    
    def _process_assistant_message(self, session: Dict, row_dict: Dict, content_type: str):
        """处理助手消息"""
        content = row_dict.get('Content', '')
        
        if content_type == "tool_call":
            self._process_tool_call(session, content)
        elif content_type == "parsefile":
            self._process_parse_file(session, row_dict)
        elif content_type in self.config.valid_assistant_types:
            self._process_assistant_response(session, content, content_type)
    
    def _process_tool_call(self, session: Dict, content: str):
        """处理工具调用"""
        try:
            tool_call = json.loads(content)
            tool_id = tool_call.get("request", {}).get("tool_id", "")
            session['codes'] += f'{tool_id} '
        except json.JSONDecodeError:
            logger.warning("解析tool_call失败")
    
    def _process_parse_file(self, session: Dict, row_dict: Dict):
        """处理文件解析"""
        try:
            origin_data = json.loads(row_dict.get('OriginData', '{}'))
            file_info = origin_data["files"][0]
            session['file_content'] += str(file_info["content"]) + '\n'
            
            # 更新问题中的文件名
            file_name = file_info["result"]["name"]
            formatted_name = f'[{file_name}](wps365://files/)'
            self._insert_file_name_in_questions(session, formatted_name)
            
        except (json.JSONDecodeError, KeyError, IndexError) as e:
            logger.warning(f"解析parsefile失败: {e}")
    
    def _process_assistant_response(self, session: Dict, content: str, content_type: str):
        """处理助手回复"""
        if content_type in {"canvas_replacement", "docx_edit_operation"}:
            try:
                session['canvas_replacement'] = json.dumps(
                    json.loads(content), ensure_ascii=False, indent=4
                )
            except json.JSONDecodeError:
                session['canvas_replacement'] = content
        else:
            session['assistant_responses'].append(content)
    
    def _extract_file_names(self, origin_data: Dict) -> List[str]:
        """提取文件名列表"""
        if not isinstance(origin_data, dict):
            return []
        
        file_infos = origin_data.get("file_infos", [])
        return [f.get("file_name", "") for f in file_infos if f.get("file_name")]
    
    def _insert_file_name_in_questions(self, session: Dict, file_name: str):
        """在问题中插入文件名"""
        matches = list(re.finditer(r'ask:', session['questions']))
        if matches:
            last_pos = matches[-1].end()
            questions = session['questions']
            session['questions'] = questions[:last_pos] + file_name + questions[last_pos:]
    
    def _create_session_data(self, session: Dict) -> SessionData:
        """创建会话数据对象"""
        return SessionData(
            session_id=str(session['session_id']),
            session_create_time=session['session_create_time'],
            creator_id=session['creator_id'],
            company_id=session['company_id'],
            question_round=session['question_round'],
            selection_content=session['selection_content'],
            questions=session['questions'],
            codes=session['codes'],
            command=session['command'],
            agent=session['agent'],
            client_type=session['client_type'],
            file_content=session['file_content'],
            edit_response=session['canvas_replacement'],
            assistant_responses=session['assistant_responses']
        )


class FileManager:
    """文件管理器"""
    
    def __init__(self, config: Config):
        self.config = config
    
    def decompress_gz_files(self, directory: str) -> bool:
        """批量解压gz文件"""
        success_count = 0
        total_count = 0
        
        for filename in os.listdir(directory):
            if filename.endswith(".gz"):
                total_count += 1
                if self._decompress_single_gz(directory, filename):
                    success_count += 1
        
        logger.info(f"解压完成: {success_count}/{total_count} 个文件成功")
        return success_count == total_count
    
    def _decompress_single_gz(self, directory: str, filename: str) -> bool:
        """解压单个gz文件"""
        try:
            gz_path = os.path.join(directory, filename)
            output_filename = os.path.splitext(filename)[0]
            output_path = os.path.join(directory, output_filename)
            
            with gzip.open(gz_path, 'rb') as f_in:
                with open(output_path, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
            
            logger.info(f"解压成功: {filename} -> {output_filename}")
            return True
            
        except Exception as e:
            logger.error(f"解压 {filename} 失败: {e}")
            return False
    
    def merge_xlsx_files(self, directory: str, output_filename: str = "merged_data.xlsx") -> bool:
        """合并Excel文件"""
        try:
            xlsx_files = self._find_xlsx_files(directory)
            if not xlsx_files:
                logger.warning("未找到任何xlsx文件")
                return False
            
            merged_data = []
            for file_path in xlsx_files:
                df = pd.read_excel(file_path)
                merged_data.append(df)
                logger.info(f"读取文件: {os.path.basename(file_path)}, 行数: {len(df)}")
            
            merged_df = pd.concat(merged_data, ignore_index=True)
            output_path = os.path.join(directory, output_filename)
            merged_df.to_excel(output_path, index=False)
            
            logger.info(f"合并完成! 总行数: {len(merged_df)}, 输出文件: {output_filename}")
            return True
            
        except Exception as e:
            logger.error(f"合并Excel文件失败: {e}")
            return False
    
    def _find_xlsx_files(self, directory: str) -> List[str]:
        """查找目录下的所有xlsx文件"""
        xlsx_files = []
        for filename in os.listdir(directory):
            if filename.endswith(".xlsx") and not filename.startswith("merged_"):
                xlsx_files.append(os.path.join(directory, filename))
        return xlsx_files


class DataProcessor:
    """主数据处理器"""
    
    def __init__(self, config: Config):
        self.config = config
        self.file_manager = FileManager(config)
        self.csv_processor = CSVProcessor(config, ETAgentFilter())
    
    def process_directory(self, directory: str = None) -> bool:
        """处理目录中的所有文件"""
        if directory is None:
            directory = self.config.file_directory
        
        try:
            # 1. 解压gz文件
            logger.info("开始解压gz文件...")
            self.file_manager.decompress_gz_files(directory)
            
            # 2. 处理CSV文件
            logger.info("开始处理CSV文件...")
            csv_files = self._find_csv_files(directory)
            success_count = 0
            
            for csv_file in csv_files:
                if self.csv_processor.process(csv_file):
                    success_count += 1
            
            logger.info(f"CSV处理完成: {success_count}/{len(csv_files)} 个文件成功")
            
            # 3. 合并Excel文件
            logger.info("开始合并Excel文件...")
            self.file_manager.merge_xlsx_files(directory)
            
            return True
            
        except Exception as e:
            logger.error(f"处理目录失败: {e}")
            return False
    
    def _find_csv_files(self, directory: str) -> List[str]:
        """查找目录下的所有CSV文件"""
        csv_files = []
        for filename in os.listdir(directory):
            if filename.endswith(".csv"):
                csv_files.append(os.path.join(directory, filename))
        return csv_files


def main():
    """主函数"""
    config = Config()
    processor = DataProcessor(config)
    
    success = processor.process_directory()
    if success:
        logger.info("所有处理完成!")
    else:
        logger.error("处理过程中出现错误!")


if __name__ == '__main__':
    main()
