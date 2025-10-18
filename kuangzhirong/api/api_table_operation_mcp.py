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

# 禁用 InsecureRequestWarning 警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

load_dotenv()

logger = getLogger(os.path.splitext(os.path.basename(__file__))[0])
WPS_SID = os.environ.get("WPS_SID")
WPS_SID_TEST = os.environ.get("WPS_SID_TEST")


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
    function_name: str = ""
    function_code: str = ""
    operation_message: str = ""
    recommend_questions: str = ""
    assistant_text: str = ""
    code_events: List[str] = None
    error_information: List[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.code_events is None:
            self.code_events = []
        if self.error_information is None:
            self.error_information = []


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


# 具体实现类 - 原有的事件处理器
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
        return event_data.event_type == "execution" and event_data.data_type == "table_operation_code_start"
    
    def handle(self, event_data: SSEEventData, result: CompletionResult) -> None:
        result.function_code = "table_operation"

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
        result.code_events.append('{"function":"generate_mindmap"}')


class PPTOutlineEventHandler:
    """PPT大纲事件处理器"""
    def can_handle(self, event_data: SSEEventData) -> bool:
        return event_data.event_type == "execution" and event_data.data_type == "ppt_outline_start"
    
    def handle(self, event_data: SSEEventData, result: CompletionResult) -> None:
        result.code_events.append('{"function":"generate_ppt"}')


class ImageStartEventHandler:
    """图像开始事件处理器"""
    def can_handle(self, event_data: SSEEventData) -> bool:
        return event_data.event_type == "execution" and event_data.data_type == "image_start"
    
    def handle(self, event_data: SSEEventData, result: CompletionResult) -> None:
        result.code_events.append('{"function":"generate_image"}')


class GeneratePPTEventHandler:
    """生成PPT事件处理器"""
    def __init__(self):
        self.findimage = False
    
    def can_handle(self, event_data: SSEEventData) -> bool:
        return event_data.event_type == "execution" and event_data.data_type == "generate_ppt"
    
    def handle(self, event_data: SSEEventData, result: CompletionResult) -> None:
        if not self.findimage:
            result.code_events.append('{"function":"generate_image"}')
            self.findimage = True


class URLFetchEventHandler:
    """URL获取事件处理器"""
    def can_handle(self, event_data: SSEEventData) -> bool:
        return event_data.event_type == "execution" and event_data.data_type == "url_fetch"
    
    def handle(self, event_data: SSEEventData, result: CompletionResult) -> None:
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
        result.code_events.append('{"function":"aidocs_search"}')


class ToolCallStartEventHandler:
    """工具调用开始事件处理器 - 原版本"""
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


class ToolCallEventHandler:
    """新的工具调用事件处理器 - 处理完整的tool_call事件"""
    def can_handle(self, event_data: SSEEventData) -> bool:
        return event_data.event_type == "execution" and event_data.data_type == "tool_call_start"
    
    def handle(self, event_data: SSEEventData, result: CompletionResult) -> None:
        try:
            tool_call_data = event_data.data
            logger.info(f"处理tool_call事件: {tool_call_data}")
            
            # 提取工具调用信息
            server_name = tool_call_data.get("server_name", "")
            server_id = tool_call_data.get("server_id", "")
            tool_id = tool_call_data.get("tool_id", "")
            tool_name = tool_call_data.get("tool_name", "")
            arguments = tool_call_data.get("arguments", "")
            is_internal = tool_call_data.get("is_internal", False)
            
            # 提取tool_call对象信息
            tool_call = tool_call_data.get("tool_call", {})
            call_type = tool_call.get("type", "")
            call_id = tool_call.get("id", "")
            call_index = tool_call.get("index", 0)
            function_info = tool_call.get("function", {})
            function_name = function_info.get("name", "")
            function_arguments = function_info.get("arguments", "")
            
            # 构建工具调用事件信息
            tool_call_event = {
                "function": "tool_call",
                "server_name": server_name,
                "server_id": server_id,
                "tool_id": tool_id,
                "tool_name": tool_name,
                "arguments": arguments,
                "is_internal": is_internal,
                "tool_call": {
                    "type": call_type,
                    "id": call_id,
                    "index": call_index,
                    "function": {
                        "name": function_name,
                        "arguments": function_arguments
                    }
                }
            }
            
            result.code_events.append(json.dumps(tool_call_event, ensure_ascii=False, indent=4))
            
            # 如果是表格操作，记录特殊信息
            if tool_id == "table_operation":
                logger.info(f"检测到表格操作工具调用: {function_name}")
                # 可以在这里添加特殊的表格操作处理逻辑
                
        except (AttributeError, TypeError, json.JSONDecodeError) as e:
            logger.error(f"处理tool_call事件失败: {e}")


class ErrorEventHandler:
    """错误事件处理器"""
    def can_handle(self, event_data: SSEEventData) -> bool:
        # 处理包含 result 字段的事件（通常是错误信息）
        return (event_data.event_type == "execution" and 
                isinstance(event_data.data, dict) and 
                event_data.data.get("result") is not None)
    
    def handle(self, event_data: SSEEventData, result: CompletionResult) -> None:
        result.error_information.append(event_data.data)


class SSEEventProcessor:
    """SSE事件处理器"""
    def __init__(self):
        self.handlers: List[EventHandler] = []
        self.has_code_event = False  # 跟踪是否有code事件
        self.has_text_event = False  # 跟踪是否有text事件
    
    def add_handler(self, handler: EventHandler) -> None:
        """添加事件处理器"""
        self.handlers.append(handler)
    
    def process_event(self, sse_event, result: CompletionResult) -> bool:
        """处理SSE事件，返回是否应该继续处理"""
        logger.debug(f"处理事件: {sse_event.event}, 数据: {sse_event.data}")
        
        if sse_event.event == "finish":
            # 在结束时检查是否需要设置function_code为chat
            if self.has_text_event and not self.has_code_event and not result.function_code:
                result.function_code = "chat"
                logger.info("检测到只有text事件没有code事件，设置function_code为chat")
            return False
        
        # 跳过 ping 事件
        if sse_event.event == "ping" and sse_event.data == "{}":
            return True
        
        if sse_event.event != "execution":
            return True
        
        try:
            event_data_dict = json.loads(sse_event.data)
            event_data = SSEEventData(
                event_type=sse_event.event,
                data_type=event_data_dict.get("type"),
                data=event_data_dict.get("data")
            )
            
            # 跟踪事件类型
            if event_data.data_type == "code":
                self.has_code_event = True
            elif event_data.data_type == "text":
                self.has_text_event = True
            
            # 尝试所有处理器
            for handler in self.handlers:
                if handler.can_handle(event_data):
                    handler.handle(event_data, result)
                    break
                    
        except json.JSONDecodeError:
            logger.warning(f"JSON解析失败: {sse_event.data}")
        
        return True


class RequestBuilder:
    """请求构建器"""
    @staticmethod
    def build_completion_request(request: CompletionRequest) -> Dict[str, Any]:
        """构建完成请求数据"""
        return {
            "question": request.question,
            "context": {
                "agent": request.context_agent,
                "file_id": {"id": str(request.file_id[0]), "type": "file"},
                "et_args": {
                    "active_sheet": str(request.active_sheet) if request.active_sheet else "",
                    "selection_range_list": [
                        {"start_row": 12, "start_col": 14, "end_row": 16, "end_col": 18}
                    ],
                    "tables_key": "20250427/8bauob73e829e5ad7b56f3a21f8d2a1b0de3a2 ",
                    "tables_encoding": "gzip",
                    "active_cell": "A38",
                    "all_sheet_name": ["Sheet1"],
                },
                "enable_canvas_mode": request.enable_canvas_mode,
            },
            "with_mcp": request.with_mcp,
        }


class HeadersFactory:
    """请求头工厂"""
    @staticmethod
    def create_headers(is_test: bool, model_url: str, search_engines: str = "") -> Dict[str, str]:
        wps_sid = WPS_SID_TEST if is_test else WPS_SID
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:126.0) Gecko/20100101 Firefox/126.0",
            "Accept": "*/*",
            "Accept-Language": "zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2",
            "Accept-Encoding": "gzip, deflate, br, zstd",
            "Referer": "https://lingxi.wps.cn/",
            "Origin": "https://lingxi.wps.cn",
            "Connection": "keep-alive",
            "X-Cc-Region": "zj2",
            "Cookie": (
                f"wps_sid={wps_sid};wps_sid_prod={wps_sid};debug_api=1;search_engines={search_engines}"
                if is_test
                else f"wps_sid={wps_sid};debug_api=1"
            ),
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-site",
            "Priority": "u=1",
            "X-Cc-Version": "2",
            "Client-Type": "pc_web",
            "Content-Type": "application/json",
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
        
        # 原有的事件处理器
        processor.add_handler(CodeEventHandler())
        processor.add_handler(TextEventHandler())
        processor.add_handler(TableOperationEventHandler())
        processor.add_handler(ClientOperationEventHandler(self, session_id))
        processor.add_handler(OperationResultEventHandler())
        processor.add_handler(RecommendEventHandler())
        
        # 新增的事件处理器
        processor.add_handler(WebSearchEventHandler())
        processor.add_handler(MindMapEventHandler())
        processor.add_handler(PPTOutlineEventHandler())
        processor.add_handler(ImageStartEventHandler())
        processor.add_handler(GeneratePPTEventHandler())
        processor.add_handler(URLFetchEventHandler())
        processor.add_handler(AiDocsSearchEventHandler())
        processor.add_handler(ToolCallStartEventHandler())  # 原版本的tool_call_start
        processor.add_handler(ToolCallEventHandler())       # 新版本的tool_call
        processor.add_handler(ErrorEventHandler())
        
        result = CompletionResult()
        
        try:
            response_sse = self.request_session.post(url, json=data, stream=True)
            sse_events = SSEClient(response_sse)
            
            for sse_event in sse_events.events():
                logger.debug(f"sse_event: {sse_event.event}, data: {sse_event.data}")
                
                if not processor.process_event(sse_event, result):
                    break
                    
        except requests.exceptions.RequestException as e:
            logger.error(f"请求失败: {e}")
        
        logger.info(f"code_events: {result.code_events}")
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
        error_information_list = [result.error_information for result in results]
        
        return (
            self.history(session_id),
            json.dumps(function_names, ensure_ascii=False, indent=4),
            json.dumps(function_codes, ensure_ascii=False, indent=4),
            json.dumps(operation_messages, ensure_ascii=False, indent=4),
            json.dumps(recommend_questions_list, ensure_ascii=False, indent=4),
            json.dumps(code_events_list, ensure_ascii=False, indent=4),
            json.dumps(error_information_list, ensure_ascii=False, indent=4),
            session_id,
        )


if __name__ == "__main__":
    cc = Copilot(is_test=True)
    r = cc.questions(
        ["[上传](wps365://files/cqQb5VLdIyiq)A1标红"], active_sheet="仓库盘点"
    )
    print(r) 