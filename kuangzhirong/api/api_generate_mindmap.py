import requests
from logging import getLogger
import json
import os
import re
import time
from sseclient import SSEClient
from dotenv import load_dotenv
from typing import Optional, Dict, List, Generator, Protocol, Any
from abc import ABC, abstractmethod
from dataclasses import dataclass
import urllib3

# from copilot.api2 import WPS_SID_TEST
# 禁用 InsecureRequestWarning 警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

load_dotenv()

logger = getLogger(os.path.splitext(os.path.basename(__file__))[0])
WPS_SID = os.environ.get("WPS_SID")
# WPS_SID_TEST = os.environ.get("WPS_SID_TEST")
WPS_SID_TEST = "V02Sf9YTKj37P5mxJEgaS8RJ9uvjUmk00a481a4b00110778d3"


# 数据传输对象 (DTO)
@dataclass
class CompletionRequest:
    """完成请求的数据传输对象"""
    question: str
    file_id: List[str]
    active_sheet: Optional[str] = None
    context_agent: str = "et"
    enable_canvas_mode: bool = True
    with_mcp: bool = True


@dataclass
class CompletionResult:
    """完成结果的数据传输对象"""
    messages: List[Dict[str, Any]] = None
    event_messages: List[Dict[str, Any]] = None
    function_name: str = ""
    function_code: str = ""
    operation_message: str = ""
    recommend_questions: str = ""
    assistant_text: str = ""
    code_events: List[str] = None
    error_information: List[Dict[str, Any]] = None
    _function_codes: List[str] = None  # 内部列表，用于跟踪所有function_code
    
    def __post_init__(self):
        if self.messages is None:
            self.messages = []
        if self.code_events is None:
            self.code_events = []
        if self.error_information is None:
            self.error_information = []
        if self._function_codes is None:
            self._function_codes = []
        if self.event_messages is None:
            self.event_messages = []
    
    def add_function_code(self, code: str):
        """添加function_code到内部列表"""
        if code and code not in self._function_codes:
            self._function_codes.append(code)
            # 用空格连接所有的function_code
            self.function_code = " ".join(self._function_codes)
    
    def add_message(self, role: str, message_type: str, content: str):
        """添加消息到messages列表"""
        message = {
            "role": role,
            "type": message_type,
            "content": content
        }
        self.messages.append(message)


@dataclass
class SSEEventData:
    """SSE事件数据"""
    event_type: str
    data_type: Optional[str] = None
    data: Any = None


# 抽象接口
class EventHandler(Protocol):
    """事件处理器接口"""
    def can_handle(self, event_data: SSEEventData) -> bool:
        """判断是否可以处理该事件"""
        ...
    
    def handle(self, event_data: SSEEventData, result: CompletionResult) -> None:
        """处理事件"""
        ...


class OperationNotifier(Protocol):
    """操作通知器接口"""
    def notify_operation_result(self, session_id: str, operation_id: str) -> Dict[str, Any]:
        """通知操作结果"""
        ...


class SessionManager(Protocol):
    """会话管理器接口"""
    def create_session(self) -> Optional[str]:
        """创建会话"""
        ...
    
    def close_session(self, session_id: str) -> None:
        """关闭会话"""
        ...


# 具体实现类
class CodeEventHandler:
    """代码事件处理器"""
    def can_handle(self, event_data: SSEEventData) -> bool:
        return event_data.event_type == "execution" and event_data.data_type == "code"
    
    def handle(self, event_data: SSEEventData, result: CompletionResult) -> None:
        try:
            function_name_sse = json.loads(event_data.data).get("function")
            if function_name_sse != "stop":
                result.function_name = function_name_sse
        except (json.JSONDecodeError, AttributeError) as e:
            logger.warning(f"处理代码事件失败: {e}")


class TextEventHandler:
    """文本事件处理器"""
    def __init__(self):
        self.findimage = False
    
    def can_handle(self, event_data: SSEEventData) -> bool:
        return event_data.event_type == "execution" and event_data.data_type == "text"
    
    def handle(self, event_data: SSEEventData, result: CompletionResult) -> None:
        result.assistant_text += str(event_data.data)
        
        # 检查文本中是否包含图片链接
        if not self.findimage:
            pattern_image = r'!\[.*?\]\(https://weboffice-kdocs-openapi-test\..*?'
            if re.findall(pattern_image, str(event_data.data)):
                result.code_events.append('{"function":"generate_image"}')
                self.findimage = True


class TableOperationEventHandler:
    """表格操作事件处理器"""
    def can_handle(self, event_data: SSEEventData) -> bool:
        return event_data.event_type == "execution" and  "table_operation_start" == event_data.data_type
    
    def handle(self, event_data: SSEEventData, result: CompletionResult) -> None:
        result.add_function_code("table_operation")


class ClientOperationEventHandler:
    """客户端操作事件处理器"""
    def __init__(self, operation_notifier: OperationNotifier, session_id: str):
        self.operation_notifier = operation_notifier
        self.session_id = session_id
    
    def can_handle(self, event_data: SSEEventData) -> bool:
        return event_data.event_type == "execution" and event_data.data_type == "client_operation"
    
    def handle(self, event_data: SSEEventData, result: CompletionResult) -> None:
        try:
            operation_id = event_data.data.get("operation_id")
            operation_result = self.operation_notifier.notify_operation_result(
                self.session_id, operation_id
            )
            if operation_result.get("result") == "ok":
                logger.info("操作成功")
        except (AttributeError, TypeError) as e:
            logger.error(f"处理客户端操作事件失败: {e}")


class OperationResultEventHandler:
    """操作结果事件处理器"""
    def can_handle(self, event_data: SSEEventData) -> bool:
        return event_data.event_type == "execution" and event_data.data_type == "operation_result"
    
    def handle(self, event_data: SSEEventData, result: CompletionResult) -> None:
        try:
            result.operation_message = event_data.data.get("message", "")
        except AttributeError:
            logger.warning("无法获取操作结果消息")


class DataAnalysisResultEventHandler:
    """数据分析事件处理器"""
    def can_handle(self, event_data: SSEEventData) -> bool:
        return event_data.event_type == "execution" and "data_analysis_start" == event_data.data_type
    
    def handle(self, event_data: SSEEventData, result: CompletionResult) -> None:
        result.add_function_code("data_analysis")


class RecommendEventHandler:
    """推荐事件处理器"""
    def can_handle(self, event_data: SSEEventData) -> bool:
        return event_data.event_type == "execution" and event_data.data_type == "recommend"
    
    def handle(self, event_data: SSEEventData, result: CompletionResult) -> None:
        result.recommend_questions = str(event_data.data)


# 新增的事件处理器 - 来自 gen_prompt.py 的逻辑
class WebSearchEventHandler:
    """网络搜索事件处理器"""
    def __init__(self):
        self.websearch = False
    
    def can_handle(self, event_data: SSEEventData) -> bool:
        return event_data.event_type == "execution" and event_data.data_type == "websearch"
    
    def handle(self, event_data: SSEEventData, result: CompletionResult) -> None:
        result.add_function_code("websearch")
        if not self.websearch:
            try:
                content_websearch = {
                    "function": "websearch",
                    "query": event_data.data.get("query", "")
                }
                result.code_events.append(json.dumps(content_websearch, ensure_ascii=False, indent=4))
                self.websearch = True
            except (AttributeError, TypeError) as e:
                logger.warning(f"处理网络搜索事件失败: {e}")


class MindMapEventHandler:
    """思维导图事件处理器"""
    def can_handle(self, event_data: SSEEventData) -> bool:
        return event_data.event_type == "execution" and event_data.data_type == "mind_map_start"
    
    def handle(self, event_data: SSEEventData, result: CompletionResult) -> None:
        result.add_function_code("generate_mindmap")
        result.code_events.append('{"function":"generate_mindmap"}')


class PPTOutlineEventHandler:
    """PPT大纲事件处理器"""
    def can_handle(self, event_data: SSEEventData) -> bool:
        return event_data.event_type == "execution" and event_data.data_type == "ppt_outline_start"
    
    def handle(self, event_data: SSEEventData, result: CompletionResult) -> None:
        result.add_function_code("generate_ppt")
        result.code_events.append('{"function":"generate_ppt"}')


class ImageStartEventHandler:
    """图像开始事件处理器"""
    def can_handle(self, event_data: SSEEventData) -> bool:
        return event_data.event_type == "execution" and event_data.data_type == "image_start"
    
    def handle(self, event_data: SSEEventData, result: CompletionResult) -> None:
        result.add_function_code("generate_image")
        result.code_events.append('{"function":"generate_image"}')


class GeneratePPTEventHandler:
    """生成PPT事件处理器"""
    def __init__(self):
        self.findimage = False
    
    def can_handle(self, event_data: SSEEventData) -> bool:
        return event_data.event_type == "execution" and event_data.data_type == "generate_ppt"
    
    def handle(self, event_data: SSEEventData, result: CompletionResult) -> None:
        result.add_function_code("generate_ppt")
        if not self.findimage:
            result.code_events.append('{"function":"generate_image"}')
            self.findimage = True


class URLFetchEventHandler:
    """URL获取事件处理器"""
    def can_handle(self, event_data: SSEEventData) -> bool:
        return event_data.event_type == "execution" and event_data.data_type == "url_fetch"
    
    def handle(self, event_data: SSEEventData, result: CompletionResult) -> None:
        result.add_function_code("url_fetch")
        try:
            content_url = {
                "function": "url_fetch",
                "url": event_data.data.get("url", "")
            }
            result.code_events.append(json.dumps(content_url, ensure_ascii=False, indent=4))
        except (AttributeError, TypeError) as e:
            logger.warning(f"处理URL获取事件失败: {e}")


class AiDocsSearchEventHandler:
    """AI文档搜索事件处理器"""
    def can_handle(self, event_data: SSEEventData) -> bool:
        return event_data.event_type == "execution" and event_data.data_type == "aidocs_search_start"
    
    def handle(self, event_data: SSEEventData, result: CompletionResult) -> None:
        result.add_function_code("aidocs_search")
        result.code_events.append('{"function":"aidocs_search"}')


class ToolCallEventHandler:
    """工具调用事件处理器"""
    def can_handle(self, event_data: SSEEventData) -> bool:
        return event_data.event_type == "execution" and event_data.data_type == "tool_call_start"
    
    def handle(self, event_data: SSEEventData, result: CompletionResult) -> None:
        try:
            content_tool_call = event_data.data
            logger.info(f"content_tool_call: {content_tool_call}")
            
            server_name = content_tool_call.get("server_name", "")
            tool_name = content_tool_call.get("tool_name", "")
            
            content_tool = {
                "function": server_name,
                "tool_name": tool_name
            }
            result.code_events.append(json.dumps(content_tool, ensure_ascii=False, indent=4))
        except (AttributeError, TypeError) as e:
            logger.warning(f"处理工具调用事件失败: {e}")


class ErrorEventHandler:
    """错误事件处理器"""
    def can_handle(self, event_data: SSEEventData) -> bool:
        # 处理包含 result 字段的事件（通常是错误信息）
        return (event_data.event_type == "execution" and 
                isinstance(event_data.data, dict) and 
                event_data.data.get("result") is not None)
    
    def handle(self, event_data: SSEEventData, result: CompletionResult) -> None:
        result.error_information.append(event_data.data)


class MessageBuilderEventHandler:
    """消息构建事件处理器 - 将SSE事件转换为消息格式"""
    def __init__(self):
        self.message_buffer = []  # 消息缓冲区，用于临时存储消息
        self.user_question_added = False  # 标记是否已添加用户问题
        self.active_sessions = {}  # 跟踪活跃的start-end会话 {type: True/False}
    
    def can_handle(self, event_data: SSEEventData) -> bool:
        # 只处理execution类型的事件，但不与其他处理器冲突
        # 这个处理器是被动的，用于构建消息，不影响原有的功能逻辑
        return event_data.event_type == "execution"
    
    def handle(self, event_data: SSEEventData, result: CompletionResult) -> None:
        """根据事件类型构建不同的消息 - 被动处理，不干扰其他处理器"""
        data_type = event_data.data_type
        # 忽略type为ignore的消息
        if data_type == "ignore":
            return
        
        # 根据data_type确定消息的role和type
        message_info = self._determine_message_info(data_type, event_data.data)
        
        if message_info:
            role, msg_type, content = message_info
            if content:  # 只有内容不为空才添加消息
                # 如果在活跃会话中，或者是可合并类型，则尝试合并
                self._add_to_buffer(role, msg_type, content)
        
        # 重要：这个处理器是被动的，不会修改result的其他字段
        # 不会干扰function_code、function_name等的获取
    
    def _determine_message_info(self, data_type: str, data: Any) -> tuple:
        """根据data_type确定消息信息，返回(role, type, content)"""
        
        # 处理用户请求类型
        if data_type == "user":
            if data and isinstance(data, dict):
                user_request = data.get("user_request", {})
                content = user_request.get("content", "")
                if content:
                    return ("user", "text", content)
        
        # 处理文本类型 - 助手回复
        elif "text" in data_type:
            if data:  # data可能是字符串
                return ("assistant", data_type, str(data))
        
        else:
            if data:
                try: 
                    content = json.loads(data).get("content", "")
                except Exception as e:
                    content = str(data)
                finally:
                    return ("assistant", data_type, content)
            return None
        
        return None
    
    def _add_to_buffer(self, role: str, msg_type: str, content: str):
        """添加消息到缓冲区，如果与上一条消息类型相同则合并"""
        if not content.strip():
            return
            
        # 检查是否可以与上一条消息合并
        can_merge = (self.message_buffer and 
                    self.message_buffer[-1]["role"] == role and 
                    self.message_buffer[-1]["type"] == msg_type)
        
        if can_merge:
            # 合并内容
            self.message_buffer[-1]["content"] += content
        else:
            # 添加新消息
            self.message_buffer.append({
                "role": role,
                "type": msg_type,
                "content": content
            })
    
    def finalize_messages(self, result: CompletionResult, original_question: str = "", file_id_list: List[str] = None):
        """在处理完成后，整理和添加最终消息"""
        
        # 先处理用户文件信息（如果还没有从事件中获取到）
        if file_id_list and not any(msg["role"] == "user" and msg["type"] == "file" for msg in self.message_buffer):
            file_name = self._extract_file_name_from_question(original_question, file_id_list)
            if file_name:
                # 在消息开头插入文件信息
                self.message_buffer.insert(0, {
                    "role": "user",
                    "type": "file", 
                    "content": file_name
                })
        
        # 处理用户问题描述（只有在没有用户描述时才添加）
        has_user_description = any(msg["role"] == "user" and msg["type"] == "description" for msg in self.message_buffer)
        
        if original_question and not has_user_description and not self.user_question_added:
            cleaned_question = self._clean_question_text(original_question)
            if cleaned_question:
                # 查找合适的位置插入用户描述
                insert_index = 0
                for i, msg in enumerate(self.message_buffer):
                    if msg["role"] == "user" and msg["type"] == "file":
                        insert_index = i + 1
                        break
                
                self.message_buffer.insert(insert_index, {
                    "role": "user",
                    "type": "description",
                    "content": cleaned_question
                })
                self.user_question_added = True
        
        # 将缓冲区的消息添加到结果中
        for msg in self.message_buffer:
            result.add_message(msg["role"], msg["type"], msg["content"])
    
    def _extract_file_name_from_question(self, original_question: str, file_id_list: List[str]) -> str:
        """从原始问题中提取文件名"""
        import re
        patterns = [
            r"\[([^\]]+)\]\(wps365://files/([^\)]+)\)",  # 通用模式，捕获文件名和ID
            r'\[([^\]]+)\]\((https?://\S+?)\)',  # 链接模式
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, original_question)
            if matches:
                for match in matches:
                    if isinstance(match, tuple) and len(match) >= 2:
                        potential_name = match[0]
                        # 过滤掉一些特殊的前缀，提取真实文件名
                        if not potential_name.startswith(('上传', '数据分析', '表格canvas', 'PDFcanvas')):
                            return potential_name
                        else:
                            # 如果是特殊前缀，尝试提取后面的部分
                            clean_name = re.sub(r'^(上传|数据分析|表格canvas|PDFcanvas)', '', potential_name).strip()
                            if clean_name:
                                return clean_name
        
        # 如果无法提取文件名，使用file_id
        if file_id_list:
            return f"文件ID: {file_id_list[0]}"
        
        return ""
    
    def _clean_question_text(self, original_question: str) -> str:
        """清理问题文本，移除文件链接部分"""
        import re
        cleaned_question = original_question
        patterns = [
            r"\[上传[^\]]*\]\(wps365://files/([^\)]+)\)",
            r'\[数据分析[^\]]*\]\((https?://\S+?)\)',
            r'\[[^\]]*\]\(wps365://files/([^\)]+)\)',
            r'\[表格canvas[^\]]*\]\(wps365://files/([^\)]+)\)',
            r'\[PDFcanvas[^\]]*\]\(wps365://files/([^\)]+)\)'
        ]
        
        for pattern in patterns:
            cleaned_question = re.sub(pattern, '', cleaned_question).strip()
        
        return cleaned_question


class SSEEventProcessor:
    """SSE事件处理器"""
    def __init__(self):
        self.handlers: List[EventHandler] = []
        self.has_code_event = False  # 跟踪是否有code事件
        self.has_text_event = False  # 跟踪是否有text事件
        self.message_builder = None  # 消息构建器引用
    
    def add_handler(self, handler: EventHandler) -> None:
        """添加事件处理器"""
        self.handlers.append(handler)
        # 保存消息构建器的引用
        if isinstance(handler, MessageBuilderEventHandler):
            self.message_builder = handler
    
    def process_event(self, sse_event, result: CompletionResult) -> bool:
        """处理SSE事件，返回是否应该继续处理"""
        logger.debug(f"处理事件: {sse_event.event}, 数据: {sse_event.data}")
        
        if sse_event.event == "finish":
            # 在结束时检查是否需要设置function_code为chat
            if self.has_text_event and not self.has_code_event and not result.function_code:
                result.add_function_code("chat")
                logger.info("检测到只有text事件没有code事件，设置function_code为chat")
            return False
        
        # 跳过 ping 事件和 aigc 事件
        if sse_event.event in ["ping", "aigc"] or sse_event.data == "{}":
            return True
        
        if sse_event.event != "execution":
            return True
        
        try:
            event_data_dict = json.loads(sse_event.data)
            print(event_data_dict)
            # 解析实际的数据结构
            event_type = sse_event.event
            data_type = event_data_dict.get("type")
            
            # 获取实际数据内容
            actual_data = event_data_dict.get("data")
            fallback_info = event_data_dict.get("fallback", {})
            operation = event_data_dict.get("operation", {})

            
            # print(f"event_data: type={data_type}, data={actual_data}, fallback={fallback_info}")
            
            event_data = SSEEventData(
                event_type=event_type,
                data_type=data_type,
                data=actual_data
            )

            # 跟踪事件类型
            if event_data.data_type == "code":
                self.has_code_event = True
            elif event_data.data_type in ["text", "mind_map"]:
                self.has_text_event = True
                
            # 尝试所有处理器
            for handler in self.handlers:
                if handler.can_handle(event_data):
                    handler.handle(event_data, result)
                    
        except json.JSONDecodeError as e:
            logger.warning(f"JSON解析失败: {e}, 数据: {sse_event.data[:100]}...")
        
        return True
    
    def finalize_processing(self, result: CompletionResult, original_question: str = "", file_id_list: List[str] = None):
        """完成处理后的清理工作"""
        if self.message_builder:
            self.message_builder.finalize_messages(result, original_question, file_id_list)


class RequestBuilder:
    """请求构建器"""
    @staticmethod
    def build_completion_request(request: CompletionRequest) -> Dict[str, Any]:
        """构建完成请求数据"""
        return {
            "question": request.question,
            "file_ids":request.file_id if request.file_id else [],
            "upload_ids":[],
            "collect_ids":[],
            "official_doc_ids":[],
            "thinking":"auto",
            "with_mcp":False,
            "command":""
        }


class HeadersFactory:
    """请求头工厂"""
    @staticmethod
    def create_headers(is_test: bool, model_url: str, search_engines: str = "") -> Dict[str, str]:
        wps_sid = WPS_SID_TEST if is_test else WPS_SID
        headers = {
            "Accept": "*/*",
            # "Accept-Language": "zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2",
            'Accept-language': 'zh-CN,zh;q=0.9',
            # "Accept-Language": "en-US,en;q=0.9",
            # "Accept-Language": "zh-HK,zh;q=0.9",
            #"Accept-Language": "ja-JP,ja;q=0.9",  #注意切换语言
            "Accept-Encoding": "gzip, deflate, br, zstd",
            "Referer": "https://lingxi.wps.cn/",
            "Origin": "https://lingxi.wps.cn",
            "Connection": "keep-alive",
            "X-Cc-Region": "master_old",
            "Cookie": f'lingxi_run_scene=dockpanel_v2; wps_sid={wps_sid};copilot_branch=feat-i18n-v2;copilot_server_branch=master_old;lang=zh-CN',#注意修改lang后面的语言
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-site",
            "Priority": "u=1",
            "X-Cc-Version": "2",
            "Client-Type": "WPP", #注意切换组件，ET/WPP/PDF/WPS/AP
            "Content-Type": "application/json",
            "X-Client-Lang": "zh-CN", # 中文
            # "X-Client-Lang": "zh-HK", # 中文繁体
            # "X-Client-Lang": "en-US", # 英文
            #"X-Client-Lang": "ja-JP", # 日文
        }
        if is_test:
            headers["Host"] = "lingxi.wps.cn"
        if model_url:
            headers["Cookie"] = headers["Cookie"] + f";model_url={model_url}"
        return headers


def replece_test_url(url):
    return url.replace("lingxi.wps.cn", "120.92.124.158")


class Copilot:
    def __init__(
        self, is_test=True, model_url="", custom_headers={}, search_engines=""
    ):
        self.is_test = is_test
        self.model_url = model_url
        self.request_session = requests.Session()
        self.session_id = None
        self.headers = HeadersFactory.create_headers(is_test, model_url, search_engines)
        self.request_session.headers.update(self.headers)
        self.request_session.headers.update(custom_headers)
        self.request_session.verify = False
        self.host = "120.92.124.158" if self.is_test else "lingxi.wps.cn"

    def create_session(self) -> Optional[str]:
        """创建会话"""
        url = f"https://{self.host}/api/aigc/v3/assistant/sessions"
        try:
            response = self.request_session.post(url)
            res = response.json()
            if res.get("data") and res.get("data").get("session_id"):
                session_id = res["data"]["session_id"]
                logger.info(f"session_id：{session_id}")
                return session_id
            else:
                logger.error(
                    f"创建session失败: request—id：{response.headers.get('x-request-id')}，text: {response.text}"
                )
                return None
        except Exception as e:
            logger.error(f"创建session异常: {e}")
            return None

    def close_session(self, session_id: str) -> None:
        """关闭会话"""
        url = f"https://{self.host}/api/aigc/v3/assistant/sessions/{session_id}/close"
        try:
            response = self.request_session.post(url)
            res = response.json()
            if res.get("result") == "ok":
                logger.info("关闭会话成功")
            else:
                logger.error(f"关闭session失败,hint:{res.get('hint')},msg:{res.get('msg')}")
        except Exception as e:
            logger.error(f"关闭session异常: {e}")
    
    def notify_operation_result(self, session_id: str, operation_id: str) -> Dict[str, Any]:
        """通知操作结果"""
        url = f"https://{self.host}/api/aigc/v3/assistant/sessions/{session_id}/notify"
        data = {
            "operation_type": "table_operation",
            "operation_id": operation_id,
            "metadata": {
                "result": True,
                "message": "执行失败，请重试"
            }
        }
        try:
            response = self.request_session.post(url, json=data)
            return response.json()
        except Exception as e:
            logger.error(f"通知操作结果异常: {e}")
            return {"result": "error", "message": str(e)}

    def get_completion(self, session_id: str, question: str, file_id: List[str], active_sheet: Optional[str] = None) -> CompletionResult:
        """获取完成结果"""
        url = f"https://{self.host}/api/aigc/v3/assistant/sessions/{session_id}/completions"
        
        # 构建请求
        request = CompletionRequest(
            question=question,
            file_id=file_id,
            active_sheet=active_sheet
        )
        data = RequestBuilder.build_completion_request(request)
        
        # 初始化事件处理器
        processor = SSEEventProcessor()
        
        # 所有事件处理器，后续有新增事件处理器，请添加到此处
        processor.add_handler(DataAnalysisResultEventHandler())
        processor.add_handler(CodeEventHandler())
        processor.add_handler(TextEventHandler())
        processor.add_handler(TableOperationEventHandler())
        processor.add_handler(ClientOperationEventHandler(self, session_id))
        processor.add_handler(OperationResultEventHandler())
        processor.add_handler(RecommendEventHandler())
        processor.add_handler(WebSearchEventHandler())
        processor.add_handler(MindMapEventHandler())
        processor.add_handler(PPTOutlineEventHandler())
        processor.add_handler(ImageStartEventHandler())
        processor.add_handler(GeneratePPTEventHandler())
        processor.add_handler(URLFetchEventHandler())
        processor.add_handler(AiDocsSearchEventHandler())
        processor.add_handler(ToolCallEventHandler())
        processor.add_handler(ErrorEventHandler())
        processor.add_handler(MessageBuilderEventHandler())
        
        result = CompletionResult()
        
        try:
            response_sse = self.request_session.post(url, json=data, stream=True)
            sse_events = SSEClient(response_sse)
            
            for sse_event in sse_events.events():
                logger.debug(f"sse_event: {sse_event.event}, data: {sse_event.data}")
                if sse_event.event == "execution":
                    result.event_messages.append(sse_event.data)
                if not processor.process_event(sse_event, result):
                    break
            
            # 处理完成后，调用finalize_processing来整理消息
            processor.finalize_processing(result, question, file_id)
                    
        except requests.exceptions.RequestException as e:
            logger.error(f"请求失败: {e}")
        
        logger.info(f"code_events: {result.code_events}")
        logger.info(f"messages: {result.messages}")
        return result

    def history(self, session_id: str) -> Dict[str, Any]:
        """获取会话历史"""
        url = f"https://{self.host}/api/aigc/v3/assistant/sessions/{session_id}/messages"
        try:
            history_data = self.request_session.get(url).json()
            return {
                "data": {"list": [entry for entry in history_data["data"]["list"]]},
                "result": history_data["result"],
            }
        except Exception as e:
            logger.error(f"获取历史记录异常: {e}")
            return {"data": {"list": []}, "result": "error"}

    def questions(self, questions: List[str], active_sheet: str = "") -> Optional[tuple]:
        """处理问题列表"""
        logger.info(f"处理问题: {questions}")
        
        session_id = self._create_session_with_retry()
        if session_id is None:
            return None
        
        try:
            results = self._process_questions(questions, session_id, active_sheet)
            return self._format_results(session_id, results)
        finally:
            logger.info("----close session")
            self.close_session(session_id=session_id)

    def _create_session_with_retry(self, max_retries: int = 3) -> Optional[str]:
        """重试创建会话"""
        for _ in range(max_retries):
            try:
                session_id = self.create_session()
                if session_id:
                    return session_id
            except Exception as e:
                logger.error(f"创建session失败: {e}")
        return None

    def _process_questions(self, questions: List[str], session_id: str, active_sheet: str) -> List[CompletionResult]:
        """处理问题列表"""
        results = []
        
        for question_text in questions:
            file_id, processed_question = self._extract_file_info(question_text)
            
            if file_id:
                result = self.get_completion(session_id, processed_question, file_id, active_sheet)
                results.append(result)
        
        return results

    def _extract_file_info(self, question: str) -> tuple[List[str], str]:
        """提取文件信息"""
        patterns = [
            r"\[上传[^\]]*\]\(wps365://files/([^\)]+)\)",
            r'\[数据分析[^\]]*\]\((https?://\S+?)\)',
            r'\[[^\]]*\]\(wps365://files/([^\)]+)\)',
            r'\[表格canvas[^\]]*\]\(wps365://files/([^\)]+)\)',
            r'\[PDFcanvas[^\]]*\]\(wps365://files/([^\)]+)\)'
        ]
        
        for pattern in patterns:
            if re.findall(pattern, question):
                if "https?" in pattern:
                    pattern_file_ids = r"/l/([\w-]+)"
                else:
                    pattern_file_ids = r"wps365://files/(\w+)"
                
                file_id = re.findall(pattern_file_ids, question)
                processed_question = re.sub(pattern, '', question).strip()
                return file_id, processed_question
        
        return [], question

    def _format_results(self, session_id: str, results: List[CompletionResult]) -> tuple:
        """格式化结果"""
        function_names = [result.function_name for result in results]
        function_codes = [result.function_code for result in results]
        operation_messages = [result.operation_message for result in results]
        recommend_questions_list = [result.recommend_questions for result in results]
        code_events_list = [result.code_events for result in results]
        event_messages_list = [result.event_messages for result in results]
        messages_list = [result.messages for result in results]
        print(messages_list)
        return (
            json.dumps(event_messages_list, ensure_ascii=False, indent=4).replace("\\", ""),
            json.dumps(function_names, ensure_ascii=False, indent=4),
            json.dumps(function_codes, ensure_ascii=False, indent=4),
            json.dumps(operation_messages, ensure_ascii=False, indent=4),
            json.dumps(recommend_questions_list, ensure_ascii=False, indent=4),
            json.dumps(code_events_list, ensure_ascii=False, indent=4),
            json.dumps(messages_list, ensure_ascii=False, indent=4),
            session_id,
        )


if __name__ == "__main__":
    cc = Copilot(is_test=True)
    r = cc.questions(
        ["[上传](wps365://files/cqQb5VLdIyiq)A1标红"], active_sheet="仓库盘点"
    )
    print("返回结果:")
    print(f"历史记录: {r[0]}")
    print(f"function_names: {r[1]}")
    print(f"function_codes: {r[2]}")
    print(f"operation_messages: {r[3]}")
    print(f"recommend_questions: {r[4]}")
    print(f"code_events: {r[5]}")
    print(f"error_information: {r[6]}")
    print(f"messages: {r[7]}")  # 新增的消息字段
    print(f"session_id: {r[8]}")
