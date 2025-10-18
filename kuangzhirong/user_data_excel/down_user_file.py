import asyncio
import re
from urllib.parse import urlparse
import hashlib
import gzip
import io
import os
import sys
import time
import requests
from requests.exceptions import ConnectionError
sys.path.append(os.path.abspath('D:\PEProject\llm_qa\kuangzhirong'))
from api.corexl import async_save_as
from dotenv import load_dotenv
from abc import ABC, abstractmethod
from typing import List, Dict, Tuple, Optional, Set
from dataclasses import dataclass
from airsheet_sdk import airsheet
load_dotenv()

import json
from api.driverlib import PrivyDrive
import pandas as pd

WPS_SID = os.environ["WPS_SID"]


# ==================== 配置管理 ====================
@dataclass
class AppConfig:
    """应用配置"""
    wps_sid: str
    drive_group_id: str = "2431733826"
    drive_parent_id: str = "384244849009"
    
    # 阻止的用户ID列表
    blocked_user_ids: Set[int] = None
    
    # 过滤问题列表
    filter_questions: List[str] = None
    
    def __post_init__(self):
        if self.blocked_user_ids is None:
            self.blocked_user_ids = {
                1385942755, 1385942459, 1385943631, 1388246358, 1388383710, 1388247360, 1388247377,
                1388383663, 1493809835, 1384379492, 1384379148, 1388383683, 1388247748, 1457509623,
                1461627669, 1478434997, 1508681112, 1576662533, 1579664567, 1583067065, 1589674436,
                1589875968, 1388382829, 1384379462, 1388384470, 1384380262, 1466641772, 1511642230,
                1511446215, 1512878100, 1571458883, 1385941891, 1388384214, 1388384497, 1388384477,
                1384382245, 1385942844, 1385147975, 1389712262, 1557445525, 1558846248, 1384379684,
                1388247508, 1384379245, 1384382336, 1512296358
            }
        
        if self.filter_questions is None:
            self.filter_questions = [
                '从数据中能得出什么结论', '给我推荐图表', "数据呈现出哪些变化趋势", "检查数据是否有异常",
                "检查数据中是否有异常", "帮我做一些有业务价值的图表", "从业务角度可以分析哪些关键问题", "给我推荐一些图表"
            ]


# ==================== 接口定义 ====================
class IAPIClient(ABC):
    """API客户端接口"""
    
    @abstractmethod
    def get_sessions(self, start_time: str, end_time: str, offset: int, limit: int) -> List[Dict]:
        pass
    
    @abstractmethod
    def get_session_messages(self, session_id: str) -> List[Dict]:
        pass
    
    @abstractmethod
    def get_message_content_url(self, session_id: str, message_id: str) -> str:
        pass


class IFileUploader(ABC):
    """文件上传接口"""
    
    @abstractmethod
    def upload(self, file_path: str) -> str:
        pass


class IMessageFilter(ABC):
    """消息过滤器接口"""
    
    @abstractmethod
    def should_filter(self, messages: List[Dict]) -> bool:
        pass


class IMessageConverter(ABC):
    """消息转换器接口"""
    
    @abstractmethod
    def convert(self, messages: List[Dict]) -> Tuple:
        pass


# ==================== 核心实现 ====================
class RequestSigner:
    """请求签名器 - 单一职责：签名逻辑"""
    
    def __init__(self, ak: str, sk: str):
        self._ak = ak
        self._sk = sk
    
    def sign(self, req: requests.Request) -> requests.PreparedRequest:
        if not isinstance(req, requests.Request):
            raise TypeError(f"{type(req)} not requests.Request")
        
        md5 = self._calculate_md5(req)
        date = str(int(time.time()))
        ct = "application/json"
        authorization = "aigc:" + hashlib.sha1((self._sk + md5 + ct + date).encode()).hexdigest()
        
        headers = {
            "Content-Type": ct,
            "Date": date,
            "Authorization": authorization,
            "Content-Md5": md5,
            "Access-Id": self._ak,
        }
        
        prepare = req.prepare()
        prepare.headers.update(headers)
        return prepare
    
    def _calculate_md5(self, req: requests.Request) -> str:
        if req.method == "get":
            uri = urlparse(req.url)
            path_with_query = uri.path + (f"?{uri.query}" if uri.query else "")
            return hashlib.md5(path_with_query.encode()).hexdigest()
        else:
            data = req.data
            if not data and req.json is not None:
                data = json.dumps(data)
            return hashlib.md5(data.encode()).hexdigest()


class ConsoleAPIClient(IAPIClient):
    """控制台API客户端 - 单一职责：API交互"""
    
    def __init__(self, ak: str, sk: str, host: str = "https://www.kdocs.cn"):
        self._host = host
        self._signer = RequestSigner(ak, sk)
    
    def get_sessions(self, start_time: str, end_time: str, offset: int = 0, limit: int = 200) -> List[Dict]:
        url = f"{self._host}/api/aigc/developer/analysis/sessions?from={start_time}&to={end_time}&offset={offset}&limit={limit}"
        req = requests.Request("get", url)
        prepare = self._signer.sign(req)
        
        with requests.sessions.Session() as session:
            resp = session.send(prepare)
        
        try:
            return resp.json()
        except json.JSONDecodeError as e:
            print(f"Failed to decode response: {resp.text}")
            return []
    
    def get_session_messages(self, session_id: str) -> List[Dict]:
        url = f"{self._host}/api/aigc/developer/analysis/sessions/{session_id}/messages"
        req = requests.Request("get", url)
        prepare = self._signer.sign(req)
        
        with requests.sessions.Session() as session:
            resp = session.send(prepare)
        return resp.json()
    
    def get_message_content_url(self, session_id: str, message_id: str) -> str:
        url = f"{self._host}/api/aigc/developer/analysis/sessions/{session_id}/messages/{message_id}/content"
        req = requests.Request("get", url)
        prepare = self._signer.sign(req)
        
        with requests.sessions.Session() as session:
            resp = session.send(prepare)
        return resp.json().get("url", "")


class RetryableAPIClient(IAPIClient):
    """带重试机制的API客户端装饰器"""
    
    def __init__(self, client: IAPIClient, max_retries: int = 3, wait_time: int = 5):
        self._client = client
        self._max_retries = max_retries
        self._wait_time = wait_time
    
    def get_sessions(self, start_time: str, end_time: str, offset: int = 0, limit: int = 200) -> List[Dict]:
        return self._client.get_sessions(start_time, end_time, offset, limit)
    
    def get_session_messages(self, session_id: str) -> List[Dict]:
        attempts = 0
        while attempts < self._max_retries:
            try:
                return self._client.get_session_messages(session_id)
            except ConnectionError as e:
                attempts += 1
                print(f"Connection error: {e}. Retrying {attempts}/{self._max_retries} in {self._wait_time}s...")
                time.sleep(self._wait_time)
        
        raise ConnectionError(f"Failed after {self._max_retries} attempts")
    
    def get_message_content_url(self, session_id: str, message_id: str) -> str:
        return self._client.get_message_content_url(session_id, message_id)


class DriveFileUploader(IFileUploader):
    """文件上传器 - 单一职责：文件上传"""
    
    def __init__(self, config: AppConfig):
        self._config = config
    
    def upload(self, file_path: str) -> str:
        try:
            drive = PrivyDrive(
                wps_sid=self._config.wps_sid,
                group_id=self._config.drive_group_id,
                parent_id=self._config.drive_parent_id
            )
            return drive.upload(file_path)
        except Exception as e:
            print(f"Failed to upload file {file_path}: {e}")
            return ""


class RecommendationQuestionFilter(IMessageFilter):
    """推荐问题过滤器"""
    
    def __init__(self, config: AppConfig):
        self._filter_questions = config.filter_questions
    
    def should_filter(self, messages: List[Dict]) -> bool:
        user_texts = self._extract_user_texts(messages)
        
        if len(user_texts) == 1:
            cleaned_text = re.sub(r"现在开始分析当前文件中名为'.*?'的工作表，我的问题是：", "", user_texts[0])
            return cleaned_text in self._filter_questions
        
        return False
    
    def _extract_user_texts(self, messages: List[Dict]) -> List[str]:
        user_texts = []
        for msg in messages:
            if msg.get("role") == "user" and msg.get("name") == "text":
                content = msg.get("content", "")
                user_texts.append(content)
        return user_texts


class BlockedUserFilter:
    """被阻止用户过滤器"""
    
    def __init__(self, config: AppConfig):
        self._blocked_user_ids = config.blocked_user_ids
    
    def is_blocked(self, user_id: int) -> bool:
        return user_id in self._blocked_user_ids


class JsonMessageConverter(IMessageConverter):
    """JSON格式消息转换器"""
    
    def convert(self, messages: List[Dict]) -> Tuple[List[Dict], str, List[str], str, List[Dict]]:
        """返回: (messages_format, file_name, user_prompt, assistant_text, code_list)"""
        file_name = ""
        messages_format = []
        user_prompt = []
        assistant_text = ""
        code_list = []
        
        for item in messages:
            if not isinstance(item, dict):
                continue
            
            try:
                role = item["role"]
                block_type = item["name"]
                content = item["content"]
                
                current_block = {
                    "role": role,
                    "type": block_type,
                    "content": content
                }
                
                if block_type == "file":
                    content_str = content.replace("'", '"')
                    file_name = os.path.basename(content_str)
                
                if role == "user" and block_type == "text":
                    user_prompt.append(content)
                
                if role == "assistant" and block_type == "text":
                    assistant_text += content
                
                if role == "assistant" and block_type == "code":
                    code_block = {
                        "role": role,
                        "type": block_type,
                        "content": content
                    }
                    code_list.append(code_block)
                
                messages_format.append(current_block)
                
            except KeyError as e:
                print(f"KeyError: {e} in item: {item}")
                continue
        
        return messages_format, file_name, user_prompt, assistant_text, code_list


# ==================== 服务层 ====================
class SessionService:
    """会话服务 - 统一管理会话相关操作"""
    
    def __init__(self, api_client: IAPIClient, user_filter: BlockedUserFilter):
        self._api_client = api_client
        self._user_filter = user_filter
    
    def fetch_sessions(self, start_time: str, end_time: str, offset: int = 0, limit: int = 100) -> List[Dict]:
        """获取所有符合条件的会话"""
        filtered_sessions = []
        
        while True:
            print(f"Fetching sessions {offset}...")
            sessions = self._api_client.get_sessions(start_time, end_time, offset, limit)
            
            if not sessions:
                break
            
            for sess in sessions:
                user_id = int(sess.get("user_id", 0))
                if not self._user_filter.is_blocked(user_id):
                    filtered_sessions.append(sess)
            
            offset += limit
        
        return filtered_sessions
    
    def fetch_session_ids(self, start_time: str, end_time: str) -> List[str]:
        """获取会话ID列表"""
        sessions = self.fetch_sessions(start_time, end_time)
        return [sess.get("session_id") for sess in sessions]


class FileDownloadService:
    """文件下载服务"""
    
    def __init__(self, api_client: IAPIClient, uploader: IFileUploader):
        self._api_client = api_client
        self._uploader = uploader
    
    async def download_and_upload(self, session_id: str, save_path: str) -> str:
        """下载会话中的文件并上传，返回上传链接"""
        os.makedirs(save_path, exist_ok=True)
        
        messages = self._api_client.get_session_messages(session_id)
        file_msg_id, file_name = self._extract_file_info(messages)
        
        if not file_name:
            return ""
        
        new_file_name = f"{session_id}_{file_name}"
        file_path = os.path.join(save_path, new_file_name)
        
        if os.path.exists(file_path):
            return self._uploader.upload(file_path)
        
        # 下载文件
        if not await self._download_file(session_id, file_msg_id, file_path):
            return ""
        
        return self._uploader.upload(file_path)
    
    def _extract_file_info(self, messages: List[Dict]) -> Tuple[Optional[str], str]:
        """提取文件消息ID和文件名"""
        for msg in messages:
            if msg.get('name') == 'file':
                file_msg_id = msg['id']
                content_str = msg["content"].replace("'", '"')
                file_name = os.path.basename(content_str)
                return file_msg_id, file_name
        return None, ""
    
    async def _download_file(self, session_id: str, file_msg_id: str, file_path: str) -> bool:
        """下载并保存文件"""
        try:
            url = self._api_client.get_message_content_url(session_id, file_msg_id)
            resp = requests.get(url)
            content = resp.content
            
            if resp.headers.get('x-kss-meta-Gzip'):
                with gzip.GzipFile(fileobj=io.BytesIO(content), mode='rb') as f:
                    content = f.read()
            
            ext = os.path.splitext(file_path)[1]
            fn = os.path.splitext(file_path)[0]
            tmp = fn + '_tmp' + ext
            
            with open(tmp, 'wb') as f:
                f.write(content)
            
            await async_save_as(tmp, file_path)
            os.remove(tmp)
            return True
            
        except Exception as e:
            print(f"Failed to download file {file_path}: {e}")
            return False


class DataExportService:
    """数据导出服务"""
    
    def __init__(
        self,
        api_client: IAPIClient,
        session_service: SessionService,
        file_service: FileDownloadService,
        message_converter: IMessageConverter
    ):
        self._api_client = api_client
        self._session_service = session_service
        self._file_service = file_service
        self._message_converter = message_converter
    
    def export_to_excel(
        self,
        start_time: str,
        end_time: str,
        file_id: str,
        sheet_name: str,
        min_questions: int = 0
    ):
        """导出数据到Excel"""
        airsheet.init(file_id=file_id, wps_sid=WPS_SID, sheet_name=sheet_name)
        
        sessions = self._session_service.fetch_sessions(start_time, end_time)
        save_path = fr"D://PE//user_data//{start_time}_{end_time}"
        
        row_index = 2
        for session in sessions:
            try:
                session_id = session.get("session_id")
                messages = self._api_client.get_session_messages(session_id)
                
                if not messages:
                    continue
                
                # 转换消息格式
                messages_format, file_name, user_prompt, assistant_text, code_list = \
                    self._message_converter.convert(messages)
                
                question_times = len(user_prompt)
                if question_times < min_questions:
                    continue
                
                # 下载并上传文件
                link_url = asyncio.run(self._file_service.download_and_upload(session_id, save_path))
                
                # 写入Excel
                prompt_str = "\n".join(user_prompt)
                messages_str = json.dumps(messages_format, ensure_ascii=False, indent=4)
                
                data = [session_id, file_name, prompt_str, question_times, messages_str, link_url, assistant_text, str(code_list)]
                airsheet.write_xl(data, f"A{row_index}:H{row_index}", sheet_name=sheet_name)
                
                row_index += 1
                
            except Exception as e:
                print(f"Failed to process session {session.get('session_id')}: {e}")


# ==================== 工厂类 ====================
class ServiceFactory:
    """服务工厂 - 依赖注入容器"""
    
    @staticmethod
    def create_services(config: AppConfig) -> Dict:
        """创建所有服务实例"""
        # 创建基础服务
        api_client = ConsoleAPIClient("backend_console", 'b213a99a0ac94598a0283cfd77ea09ae')
        retryable_api_client = RetryableAPIClient(api_client)
        
        user_filter = BlockedUserFilter(config)
        uploader = DriveFileUploader(config)
        message_filter = RecommendationQuestionFilter(config)
        message_converter = JsonMessageConverter()
        
        # 创建业务服务
        session_service = SessionService(retryable_api_client, user_filter)
        file_service = FileDownloadService(retryable_api_client, uploader)
        export_service = DataExportService(
            retryable_api_client,
            session_service,
            file_service,
            message_converter
        )
        
        return {
            'api_client': retryable_api_client,
            'session_service': session_service,
            'file_service': file_service,
            'export_service': export_service,
            'message_filter': message_filter,
            'message_converter': message_converter
        }


# ==================== 向后兼容的遗留函数 ====================
def get_inputs(file_id: str, sheet_name: str) -> list:
    """遗留函数 - 保持向后兼容"""
    cases = []
    airsheet.init(file_id=file_id, wps_sid=WPS_SID, sheet_name=sheet_name)
    df = airsheet.xl("A:Z", headers=True, sheet_name=[sheet_name])
    df.fillna("", inplace=True)
    for i, row in df.iterrows():
        if row["商汤结论输出"] == "" or row["商汤结论输出"] == "nan":
            continue
        if pd.isna(row['question']):
            continue
        data = {
            "row_num": i + 2,
            "prompt": str(row['question']),
            "reference_answer": str(row['参考答案']),
            "sheet_name": sheet_name,
            "model_answer": str(row['商汤结论输出']),
        }
        cases.append(data)
    return cases


def extract_rating(text):
    """遗留函数 - 从文本中提取字典"""
    pattern = r"(\{.*\})"
    try:
        match = re.search(pattern, text)
        if match:
            dictionary_str = match.group(1)
            print("matched: ", dictionary_str)
            result_dict = json.loads(dictionary_str.replace("'", '"'))
            return result_dict
        else:
            print("未找到匹配的字典")
            return {}
    except Exception as e:
        return {}


def upload_to_online(file_path):
    """遗留函数 - 上传文件到在线"""
    config = AppConfig(wps_sid=WPS_SID)
    uploader = DriveFileUploader(config)
    return uploader.upload(file_path)


def user_query_format(start_time, end_time):
    """遗留函数 - 用户查询格式化"""
    config = AppConfig(wps_sid=WPS_SID)
    services = ServiceFactory.create_services(config)
    
    services['export_service'].export_to_excel(
        start_time=start_time,
        end_time=end_time,
        file_id="ctX0ifQ6bPf8",
        sheet_name="0908",
        min_questions=0
    )


def user_query_format_0301(start_time, end_time):
    """遗留函数 - 需要3次及以上用户问题"""
    config = AppConfig(wps_sid=WPS_SID)
    services = ServiceFactory.create_services(config)
    
    export_service = services['export_service']
    api_client = services['api_client']
    session_service = services['session_service']
    file_service = services['file_service']
    message_converter = services['message_converter']
    
    file_id = "cbj4E050Xez6"
    sheet_name = "工作表4"
    airsheet.init(file_id=file_id, wps_sid=WPS_SID, sheet_name=sheet_name)
    
    sessions = session_service.fetch_sessions(start_time, end_time)
    save_path = fr"D://PE//user_data//{start_time}_{end_time}"
    
    row_num = 91
    for i, session in enumerate(sessions):
        try:
            session_id = session.get("session_id")
            account_id = session.get("user_id")
            create_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(session.get("create_time")))
            
            messages = api_client.get_session_messages(session_id)
            if not messages:
                continue
            
            messages_format, file_name, user_prompt, assistant_text, _ = message_converter.convert(messages)
            
            question_times = len(user_prompt)
            if question_times < 3:
                continue
            
            link_url = asyncio.run(file_service.download_and_upload(session_id, save_path))
            
            prompt_str = "\n".join(user_prompt)
            messages_str = json.dumps(messages_format, ensure_ascii=False, indent=4)
            
            data = [account_id, session_id, file_name, prompt_str, question_times, messages_str, link_url, assistant_text]
            airsheet.write_xl(data, f"A{i+row_num}:G{i+row_num}", sheet_name=sheet_name)
            
        except Exception as e:
            print(f"Failed to process session: {e}")


def save_user_data_to_excel(file_path):
    """从Excel表格中获取session_id，然后下载文件，并保存到指定路径"""
    save_path = fr"D://PE//user_data//xuxin_data"
    df = pd.read_excel(file_path)
    session_ids = df["session_id"].tolist()
    config = AppConfig(wps_sid=WPS_SID)
    services = ServiceFactory.create_services(config)
    
    export_service = services['export_service']
    api_client = services['api_client']
    session_service = services['session_service']
    file_service = services['file_service']
    message_converter = services['message_converter']
    
    file_id = "cbj4E050Xez6"
    sheet_name = "工作表4"
    airsheet.init(file_id=file_id, wps_sid=WPS_SID, sheet_name=sheet_name)
    row_num = 1
    for i, session_id in enumerate(session_ids):
        messages = api_client.get_session_messages(session_id)
        if not messages:
            continue
        
        messages_format, file_name, user_prompt, assistant_text, _ = message_converter.convert(messages)
        
        question_times = len(user_prompt)
        
        link_url = asyncio.run(file_service.download_and_upload(session_id, save_path))
        
        prompt_str = "\n".join(user_prompt)
        messages_str = json.dumps(messages_format, ensure_ascii=False, indent=4)
        
        data = [session_id, file_name, prompt_str, question_times, messages_str, link_url, assistant_text]
        airsheet.write_xl(data, f"A{i+row_num}:G{i+row_num}", sheet_name=sheet_name)
        
        


if __name__ == "__main__":
    # user_query_format("2025-09-08", "2025-09-09")
    file_path = r"D:\PE\user_data\xuxin_data\用户query标注.xlsx"
    save_user_data_to_excel(file_path)
