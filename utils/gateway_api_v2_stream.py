import os
import socket
import time
import traceback
from typing import Dict, List, Tuple, Union

import requests
from dotenv import load_dotenv

load_dotenv()
import json
import shlex

from utils import getLogger

logger = getLogger(os.path.splitext(os.path.basename(__file__))[0])
AI_GATEWAY_TOKEN_V2 = os.environ["AI_GATEWAY_TOKEN_V2"]
AI_GATEWAY_PRODUCT_NAME_V2 = os.environ["AI_GATEWAY_PRODUCT_NAME_V2"]
AI_GATEWAY_UID_V2 = os.environ["AI_GATEWAY_UID_V2"]
AI_GATEWAY_INTENTION_CODE_V2 = os.environ["AI_GATEWAY_INTENTION_CODE_V2"]

GATE_WAY_HEADERS = {
    "Authorization": f"Bearer {AI_GATEWAY_TOKEN_V2}",
    "AIGC-GATEWAY-WPS-UID": AI_GATEWAY_UID_V2,
    "AIGC-GATEWAY-PRODUCT-NAME": AI_GATEWAY_PRODUCT_NAME_V2,
    "AIGC-GATEWAY-INTENTION-CODE": AI_GATEWAY_INTENTION_CODE_V2,
    "Content-Type": "application/json",
}
import base64
import random
import time

import sseclient

# SEC_TEXT  ={
#         "from": "AI_WPS_COPILOTPRO",
#         "scene": "",
#     }
# SEC_TEXT  ={
#     "from": "AI_WPS_PDF",
#     "scene": "user_question",
#     }
SEC_TEXT = {
    "from": "",
}


def get_local_ip_last_two_parts():
    try:
        # 创建一个socket对象
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # 使用Google的公共DNS服务器地址来获取本地IP地址
        # 这里不会真的发送出去任何数据包
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
    finally:
        s.close()

    # 分割IP地址为四部分
    ip_parts = local_ip.split(".")
    # 获取后两位
    last_two_parts = ".".join(ip_parts[-2:])
    return last_two_parts


ip_address = get_local_ip_last_two_parts()


def generate_request_id():
    # Get the current time as a timestamp
    timestamp = str(int(time.time()))

    # Get the local IP address
    # ip_address = get_local_ip_last_two_parts()

    # Generate a 12-digit hexadecimal random number
    random_hex = "".join(random.choices("0123456789abcdef", k=12))

    # Combine them to form the request ID
    request_id = timestamp + "_" + ip_address + "_" + random_hex
    return request_id


class GateWayAPI:
    def __init__(
        self,
        url_prefix="http://aigc-gateway-test.ksord.com",
        retry_count: int = 3,
        retry_interval: int = 1,
    ):
        self.chat_url = f"{url_prefix}/api/v2/llm/chat"
        self.completion_url = f"{url_prefix}/api/v2/llm/completions"
        self.multimodal_url = f"{url_prefix}/api/v2/llm/multimodal"
        self.session = requests.Session()
        self.session.headers.update(GATE_WAY_HEADERS)
        self.model_provider_map = {
            "gpt-35-turbo": "azure",
            "gpt-35-turbo-16k": "azure",
            "gpt-4": "azure",
            "gpt-4o": "azure",
            "gpt-4o-mini": "azure",
            "gpt-4-32k": "azure",
            "o1-mini": "azure",
            "o1-preview": "azure",
            "o3": "azure",
            "ernie-bot": "baidu",
            "ernie-bot-turbo": "baidu",  # 不建议使用，支持的qps低
            "ernie-bot-4": "baidu",
            "ernie-bot-4-8k": "baidu",
            "ernie-3.5-128k": "baidu",
            "ernie-speed-128k": "baidu",
            "abab5.5-chat": "minimax",
            "abab5.5-chat-pre": "minimax",
            "abab5.5-chat-pro": "minimax",
            "abab6-chat": "minimax",
            "abab6.5-chat": "minimax",
            "abab6.5s-chat": "minimax",
            "abab7-chat-preview": "minimax",
            "abab6.5s-chat-wps": "minimax-zone",  # 目前不能用，要专门申请
            "spark-desk": "spark",
            "chatglm-turbo": "zhipu",
            "chatglm-pro": "zhipu",
            "glm-4": "zhipu",
            "glm-4-air": "zhipu",
            "glm-3-turbo": "zhipu",
            "chatglm-wps": "zhipu",
            "glm-4-plus": "zhipu",
            "chat-bison": "google",
            "claude": "aws",
            "claude-instant": "aws",
            "qwen-turbo": "ali",
            "qwen-plus": "ali",
            "qwen-max": "ali",
            "qwen-max-longcontext": "ali",
            "sky-chat-3.5": "sky",
            "sky-search": "sky",
            "SenseChat-Code-365-WPS": "shangtang",
            "SenseChat-Code-Excel-WPS": "shangtang",
            "qingqiu-summary": "wps",
            "qingqiu-72b": "wps",
            "qingqiu-assistant": "wps",
            "claude-3-haiku": "aws",
            "claude-3-sonnet": "aws",
            "claude-3-opus": "aws",
            "claude-3-5-sonnet": "aws",
            "claude-sonnet-4": "aws",
            "claude-opus-4": "aws",
            "qwen1.5-72b-chat-2abf83e5-prod": "ali-zone",
            "chatglm3-130b-wps": "zhipu-zone",
            "chatglm3-130b-wps-0613": "zhipu-zone",
            "Doubao-pro-32k": "doubao",
            "Doubao-pro-128k": "doubao",
            "Doubao-pro-256k": "doubao",
            "Doubao-1.5-pro-32k": "doubao",
            "Doubao-1.5-pro-256k": "doubao",
            "Doubao-Seed-1.6": "doubao",
            "Doubao-Seed-1.6-thinking": "doubao",
            "Doubao-1.5-pro-32k-withSearch": "doubao",
            "Doubao-1.5-vision-pro-32k": "doubao",
            "step-1v-8k": "stepfun",
            "deepseek-chat": "deepseek",
            "deepseek-reasoner": "deepseek",
            "deepseek-chat-ark": "deepseek",
            "deepseek-reasoner-ark": "deepseek",
            "deepseek-reasoner-baidu": "deepseek",
            "deepseek-reasoner-tencent": "deepseek",
            "deepseek-reasoner-ali": "deepseek",
            "deepseek-reasoner-azure": "deepseek",
            "deepseek-reasoner-huawei": "deepseek",
            "deepseek-chat-ali": "deepseek",
            "deepseek-chat-azure": "deepseek",
            "deepseek-r1-distill-qwen-32b": "deepseek",
        }
        self.model_alias_to_name_map = {
            "gpt3.5": "gpt-35-turbo",
            "gpt3.5-16k": "gpt-35-turbo-16k",
            "gpt4": "gpt-4",
            "gpt4-32k": "gpt-4-32k",
            "baidu": "ernie-bot",
            "baidu3.5": "ernie-bot",
            "baidu-turbo": "ernie-bot-turbo",  # 不建议使用，支持的qps低
            "baidu4": "ernie-bot-4",
            "baidu4-8k": "ernie-bot-4-8k",
            "baidu-speed-128k": "ernie-speed-128k",
            "abab5": "abab5-chat",
            "abab5.5": "abab5.5-chat",
            "abab5.5-pre": "abab5.5-chat-pre",
            "abab5.5-pro": "abab5.5-chat-pro",
            "abab6": "abab6-chat",
            "spark-desk": "spark-desk",
            "chatglm": "chatglm-turbo",
            "glm4": "glm-4",
            "glm3-turbo": "glm-3-turbo",
            "glm-pro": "chatglm-pro",
            "bison": "chat-bison",
            "claude2": "claude",
            "claude1": "claude-instant",
            "qwen": "qwen-turbo",
            "qwen-plus": "qwen-plus",
            "sky3.5": "sky-chat-3.5",
            "sky-search": "sky-search",  # stream参数不管用
            "shangtang-365": "SenseChat-Code-365-WPS",  # 没调
            "shangtang-Excel": "SenseChat-Code-Excel-WPS",  # 没调
            "qingqiu": "qingqiu-summary",
            "qingqiu72b": "qingqiu-72b",
            "haiku": "claude-3-haiku",
            "sonnet": "claude-3-sonnet",
            "opus": "claude-3-opus",
        }
        self.version_map = {
            "gpt-4": "0125-Preview",
            "gpt-4o": "2024-05-13",
            "gpt-4o-mini": "2024-07-18",
            "gpt-4-32k": "0314",
            "o1-mini": "2024-09-12",
            "o1-preview": "2024-09-12",
            "o3": "2025-04-16",
            "spark-desk": "v1.1",
            "claude": "v2",
            "claude-instant": "v1",
            "claude-3-haiku": "20240307-v1:0",
            "claude-3-sonnet": "20240229-v1:0",
            "claude-3-opus": "20240229-v1:0",
            "claude-3-5-sonnet": "20240620-v1:0",
            "claude-opus-4": "20250514-v1:0",
            "claude-sonnet-4": "20250514-v1:0",
        }
        self.retry_count = retry_count
        self.retry_interval = retry_interval
        self.base_llm_arguments_keys = {
            "temperature",
            "max_tokens",
            "top_p",
            "top_k",
            "stop",
        }
        self.stream = True

    def get_model_details(self, model_or_alias: str) -> Union[str, str]:
        # 先尝试直接从model_provider_map找
        # model_or_alias = model_or_alias.lower()
        if model_or_alias in self.model_provider_map:
            return model_or_alias, self.model_provider_map[model_or_alias]

        # 如果直接查找失败，尝试从model_alias_to_name_map找正式名称
        model_name = self.model_alias_to_name_map.get(model_or_alias, "")
        if model_name and model_name in self.model_provider_map:
            return model_name, self.model_provider_map[model_name]

        logger.error(
            f"模型{model_or_alias}不存在,请确保和KPP名字一样。如果是新模型，找任方超添加。"
        )
        raise ValueError(
            f"模型{model_or_alias}不存在,请确保和KPP名字一样。如果是新模型，找任方超添加。"
        )

    def _split_additional_args(self, additional_args: Dict) -> Tuple[Dict, Dict]:
        base_llm_args = {
            key: val
            for key, val in additional_args.items()
            if key in self.base_llm_arguments_keys
        }
        other_llm_args = {
            key: val
            for key, val in additional_args.items()
            if key not in self.base_llm_arguments_keys
        }
        return base_llm_args, other_llm_args

    def _config_minimax(self, model, context, other_llm_args, messages):
        msgs = []
        for m in messages:
            if m.get("name"):
                msgs.append(m)
            else:
                if m.get("role") == "user":
                    msgs.append({**m, "name": "用户"})
                else:
                    msgs.append({**m, "name": "WPSAI"})
        messages = msgs
        if not other_llm_args.get("bot_setting"):
            if not context:
                context = "WPSAI是金山办公与合作伙伴共同开发的AI工作助理,WPSAI能够理解自然语言并生成对应的回复,回复思路清晰,逻辑严密,推理精确。"
            if model == "abab5.5-chat":
                other_llm_args["role_meta"] = {"user_name": "用户", "bot_name": "WPSAI"}
            else:
                other_llm_args["bot_setting"] = [
                    {"bot_name": "WPSAI", "content": context}
                ]
        return context, other_llm_args, messages

    def chat_msgs(
        self,
        model: str,
        messages: List[Dict],
        context: str = "",
        llm_arguments: Dict = {},
        version: str = "",
        sec_text=SEC_TEXT,
    ) -> Tuple[bool, str, dict]:
        payload = self.prepare_payload(
            model, messages, context, llm_arguments, version, sec_text
        )
        return self._send_request_and_parse_response(self.chat_url, payload)

    def prepare_payload(
        self,
        model: str,
        messages: List[Dict],
        context: str = "",
        llm_arguments: Dict = {},
        version: str = "",
        sec_text=SEC_TEXT,
    ) -> Dict:
        model, provider = self.get_model_details(model)
        if "claude" in model:
            if not llm_arguments.get("anthropic_version"):
                llm_arguments["anthropic_version"] = "bedrock-2023-05-31"
            if not llm_arguments.get("max_tokens"):
                llm_arguments["max_tokens"] = 4096
        extended_llm_arguments_name = f"{provider}_{model}"
        base_llm_args, other_llm_args = self._split_additional_args(llm_arguments)

        if provider.startswith("minimax"):
            context, other_llm_args, messages = self._config_minimax(
                model, context, other_llm_args, messages
            )
        if model in ["claude", "claude-instant"] and not other_llm_args.get(
            "max_tokens_to_sample"
        ):
            other_llm_args["max_tokens_to_sample"] = 4096
        if not version:
            version = self.version_map.get(model, "")
        payload = {
            "stream": self.stream,
            "context": context,
            "provider": provider,
            "model": model,
            "version": version,
            "base_llm_arguments": base_llm_args,
            "extended_llm_arguments": {},
            "sec_text": sec_text,
            "retry_strategy": {"retry_count": 0, "timeout": 0},
        }

        if other_llm_args:
            payload["extended_llm_arguments"][
                extended_llm_arguments_name
            ] = other_llm_args
        if messages:
            payload["messages"] = messages
        return payload

    def chat_text(
        self,
        model: str,
        text: str,
        context: str = "",
        llm_arguments: Dict = {},
        version: str = "",
        sec_text=SEC_TEXT,
    ) -> Tuple[bool, str, Dict]:
        if (
            "claude" in model.lower()
            or "gpt-4o" in model.lower()
            or (model == "gpt-4" and version in ["turbo-2024-04-09", "vision-preview"])
        ):
            return self.multi_text(model, text, context, llm_arguments, version)
        messages = [{"content": text, "role": "user"}]
        return self.chat_msgs(
            model, messages, context, llm_arguments, version, sec_text=sec_text
        )

    def completion(self, model: str, context: str = "") -> Tuple[bool, str, Dict]:
        payload = self.prepare_payload(model, [], context)
        return self._send_request_and_parse_response(self.completion_url, payload)

    def multi_text(
        self,
        model: str,
        text: str,
        context: str = "",
        llm_arguments: Dict = {},
        version: str = "",
    ) -> Tuple[bool, str, Dict]:
        messages = [{"content": text, "role": "user", "name": ""}]
        return self.multi_msgs(model, messages, context, llm_arguments, version)

    def multi_msgs(
        self,
        model: str,
        messages: List[Dict],
        context: str = "",
        llm_arguments: Dict = {},
        version: str = "",
    ) -> Tuple[bool, str, dict]:
        msgs = []
        for m in messages:
            role = m["role"]
            if role == "system":
                role = "assistant"
            if isinstance(m.get("content"), str):
                m2 = {
                    "role": role,
                    "content": [{"type": "text", "content": m["content"]}],
                    "name": "",
                }
            else:
                m2 = m
            msgs.append(m2)
        if msgs[0].get("role") == "assistant":
            msgs.pop(0)
        payload = self.prepare_payload(model, msgs, context, llm_arguments, version)
        return self._send_request_and_parse_response(self.multimodal_url, payload)

    def request_once(self, url, payload: Dict) -> Tuple[bool, str, Dict]:
        success = True
        text_contents = []
        reasoning_contents = []
        references = []
        json_responses = []
        cost_times = {
            "cost_first_response": 0.0,
            "cost_first_token": 0.0,
            "cost_last_token": 0.0,
            "cost_first_reason": 0.0,
            "cost_last_reason": 0.0,
            "cost_first_text": 0.0,
            "cost_last_text": 0.0,
        }
        usage = {"completion_tokens": 0, "prompt_tokens": 0, "total_tokens": 0}
        try:
            request_id = generate_request_id()
            headers = {"Client-Request-Id": request_id}
            logger.debug(f"Request ID: {request_id} payload: {payload}")

            # 生成并打印curl命令
            # curl_command = self.convert_to_curl(url, payload, headers)
            # logger.info(f"CURL command: {curl_command}")

            start = time.time()

            response = self.session.post(
                url, json=payload, headers=headers, stream=self.stream
            )

            cost_times["cost_first_response"] = time.time() - start

            if not self.stream:
                try:
                    logger.info(
                        f"request_id: {request_id}, cost_times: {cost_times},responses: {response.text}"
                    )
                    resobj = response.json()
                    # print(222, resobj)
                    text_contents = resobj["choices"][0].get("text", "")
                    reasoning_content = resobj["choices"][0].get(
                        "reasoning_content", ""
                    )
                    usage = resobj.get("usage", usage)
                    references = resobj["choices"][0].get("references", [])
                    return (
                        success,
                        text_contents,
                        {
                            "cost_times": cost_times,
                            "usage": usage,
                            "responses": resobj,
                            "reasoning_content": reasoning_content,
                            "references": references,
                        },
                    )
                except Exception as e:
                    logger.error(traceback.format_exc())
                    return (
                        False,
                        f"$ERROR$_{request_id}_{response.text}",
                        {
                            "cost_times": cost_times,
                            "usage": usage,
                            "responses": json_responses,
                        },
                    )
            if response.status_code != 200:
                logger.error(
                    f"Request ID: {request_id} cost_times:{cost_times},status_code:{response.status_code}, response error: {response.text}"
                )
                return (
                    False,
                    f"$ERROR$_{request_id}_{response.text}",
                    {
                        "cost_times": cost_times,
                        "usage": usage,
                        "responses": json_responses,
                    },
                )
            stream = sseclient.SSEClient(response)
            usage = None

            for event in stream.events():
                if not cost_times["cost_first_token"]:
                    cost_times["cost_first_token"] = time.time() - start
                cost_times["cost_last_token"] = time.time() - start
                # logger.debug(f"Request ID: {request_id} cost:{end_time-start_time} response: {event.data}")
                resobj = json.loads(event.data)
                # print(111, resobj)
                json_responses.append(resobj)
                code = resobj.get("code", "")
                msg = resobj.get("message", "")
                if code == "Success" and "choices" in resobj:
                    success = True
                    text = resobj["choices"][0].get("text", "")
                    refs = resobj["choices"][0].get("references", "")
                    if refs:
                        references.extend(refs)
                    reason = resobj["choices"][0].get("reasoning_content", "")
                    t = time.time()
                    if text:
                        if cost_times["cost_first_text"] == 0:
                            cost_times["cost_first_text"] = t - start
                        cost_times["cost_last_text"] = t - start
                    elif reason:
                        if cost_times["cost_first_reason"] == 0:
                            cost_times["cost_first_reason"] = t - start
                        cost_times["cost_last_reason"] = t - start

                    text_contents.append(text)
                    reasoning_contents.append(reason)
                    usage = resobj.get("usage", None)
                else:
                    success = False
                    logger.warning(
                        f"Request ID: {request_id}: event error {event.data} "
                    )
                    text_contents.append("$ERROR$_" + msg)
                    if "OverPromptLengthError" in resobj.get("code", ""):
                        success = True
            logger.debug(
                f"request_id: {request_id}, cost_times: {cost_times},usage:{usage}, responses: {json_responses}"
            )
        except requests.RequestException as e:
            logger.error(traceback.format_exc())
        return (
            success,
            "".join(text_contents),
            {
                "cost_times": cost_times,
                "usage": usage,
                "responses": json_responses,
                "reasoning_content": "".join(reasoning_contents),
                "references": references,
            },
        )

    def _send_request_and_parse_response(
        self, url, payload: Dict
    ) -> Tuple[bool, str, Dict]:
        success = True
        text_content = ""
        others = {}
        for attempt in range(self.retry_count + 1):
            success, text_content, others = self.request_once(url, payload)
            if success:
                break
            if attempt < self.retry_count and self.retry_interval > 0:
                random_number = random.randint(
                    self.retry_interval, self.retry_interval + 3
                )
                time.sleep(random_number)
            if "模型限流错误" in text_content:
                text_content = f"$ERROR$_{text_content}"
                random_number = random.randint(1, 2)
                logger.warning(f"模型限流错误，等待{random_number}s后重试")
                time.sleep(random_number)

            logger.warning(f"重试 {attempt + 1} / {self.retry_count}")
        return success, text_content, others

    def image_file_to_content(self, file_path):
        file_type = os.path.splitext(file_path)[1][1:]
        with open(file_path, "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read())
            return f"data:image/{file_type};base64,{encoded_string.decode('utf-8')}"

    def chat_image(
        self,
        model: str,
        image_path: str,
        text: str,
        context: str = "",
        llm_arguments: Dict = {},
        version: str = "",
    ) -> Tuple[bool, str, Dict]:
        image_content = self.image_file_to_content(image_path)
        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "image", "content": image_content},
                    {"type": "text", "content": text},
                ],
            },
            # {
            #     "role": "user",
            #     "content": [
            #         # {"type": "image", "content": image_content},
            #         {"type": "text", "content": text},
            #     ],
            # },
        ]
        if llm_arguments.get("max_tokens") is None:
            llm_arguments["max_tokens"] = 4096
        return self.multi_msgs(model, messages, context, llm_arguments, version)

    def convert_to_curl(self, url: str, payload: Dict, headers: Dict) -> str:
        """将请求转换为curl命令"""
        # 构造基础curl命令
        curl_command = f'curl -X POST "{url}"'

        # 添加headers
        all_headers = {**self.session.headers, **headers}
        for key, value in all_headers.items():
            # 使用shlex.quote确保值被正确引用
            curl_command += f' -H {shlex.quote(f"{key}: {value}")}'

        # 添加body
        body_json = json.dumps(payload, ensure_ascii=False)
        curl_command += f" --data {shlex.quote(body_json)}"

        return curl_command


if __name__ == "__main__":
    api = GateWayAPI(retry_count=0)
    api.stream = True
    # text = "图片内容是什么"
    # ttt = """你好""" * 1024 * 65
    # ctx = """"""
    # text = "你是谁"*10000
    # text = "北京枪声"
    # import base64

    # dd = api.image_file_to_content("clmm.png")
    # print(222, dd[:100])
    # msgs = [
    #     {
    #         "role": "user",
    #         "content": [
    #             {"type": "image", "content": dd},
    #             {"type": "text", "content": "总结图片内容"},
    #         ],
    #     }
    # ]
    success, text, others = api.chat_text(
        model="claude-opus-4",
        text="介绍李白",
        # llm_arguments={"thinking": {"type":"enabled"}},
    )
    print(text)
    print(111, others.get("reasoning_content", ""))
    # success, text, others = api.chat_image(
    #     model="Doubao-1.5-vision-pro-32k",
    #     image_path="clmm.png",
    #     text="提取图片中的所有文字,详细描述图片的内容,这是什么电影",
    # )
    # print(success, text)
    # success, text,others  = api.chat_image(model='gpt-4',image_path="clmm.png",text="图片中是什么内容",version="turbo-2024-04-09",llm_arguments={"max_tokens":4096})
    # success, text,others  = api.chat_image(model='claude-3-opus',image_path="clmm.png",text="图片中是什么内容",llm_arguments={"max_tokens":4096})
    # api.stream = False
    # model = "deepseek-reasoner-baidu"
    # for model in [
    #     # "deepseek-reasoner-ark",
    #     # "deepseek-reasoner-baidu",
    #     # "deepseek-reasoner-tencent",
    #     "deepseek-reasoner-huawei",
    #     # "deepseek-reasoner-ali",
    # ]:
    #     print(model)
    #     success, text, others = api.chat_text(
    #         model=model,
    #         text=ttt,
    #         context=ctx,
    #         llm_arguments={"max_tokens": 8000},
    #     )
    #     print(success, text)
    #     print(others.get("usage"))

    # print(555, success, text)
