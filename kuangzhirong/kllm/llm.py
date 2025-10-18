from typing import Literal, Generator, List
from dataclasses import dataclass, asdict, fields
import requests
import sseclient
import json
from pprint import pprint
import time
from base64 import b64encode
from copy import deepcopy
import logging
from .config import AutoConfig

log_level_str = AutoConfig.get("log_level")
log_level = logging.INFO
if log_level_str:
    log_level = logging.getLevelNamesMapping()[log_level_str.upper()]
_logger = logging.getLogger("kllm")
_logger.setLevel(log_level)

Production = "https://ai-copilot-gateway.ksord.com"
Development = "http://ai-gateway.wps.cn"

BotName = "AI"
UserName = "用户"


class AIGatewayError(Exception):
    def __init__(self, code: str, msg: str, task_id: str = "", external_id: str = ""):
        super().__init__(
            f"code:{code} message:{msg} task_id:{task_id} external_id:{external_id}"
        )


def to_data_url(path: str | bytes) -> str:
    if isinstance(path, str):
        with open(path, "rb") as f:
            data = b64encode(f.read()).decode("utf8")
            return "data:image/png;base64," + data
    else:
        data = b64encode(path).decode("utf8")
        return "data:image/png;base64," + data




@dataclass
class ModelConfig:
    model: str
    token: str
    provider: str = ""
    version: str = ""
    endpoint: str = ""


@dataclass
class MessageContent:
    type: Literal["text", "image", "image_url"]
    content: str
    detail: str = ""


@dataclass
class ChatMessage:
    role: Literal["user", "assistant", "system"] = "user"
    type: Literal["text", "execution", "code", "stop", "reasoning_content"] = "text"
    content: str | List[MessageContent] = ""

    def add_image(self, image: bytes) -> "ChatMessage":
        data = b64encode(image).decode("utf8")
        image_data = "data:image/png;base64," + data

        if isinstance(self.content, str):
            self.content = [MessageContent(type="text", content=self.content)]

        self.content.append(MessageContent(type="image", content=image_data))
        return self


ChatMessageStream = Generator[ChatMessage, None, None]
ChatStream = Generator[ChatMessage, None, None]
ChatMessages = List[ChatMessage | dict]

@dataclass
class ChatParameters:
    top_p: float | None = None
    top_k: float | None = None
    max_tokens: int | None = None
    temperature: float | None = None
    extended: dict | None = None
    stop: str | list[str] | None = None
    version: str | None = None
    examples: ChatMessages | None = None
    #    tools:list = None
    #    tool_choice:Literal['none','auto'] = None

    user_id: str = "9031"
    product_name: str = "365wps-copilotchat-web"
    intention_code: str = "365wps_cc_chat"
    from_: str = "AI_APPLICATION_TOOLS"
    scene: str = "conversational_bots"


def to_string_stream(
    stream: ChatStream, delay=0.01
) -> Generator[str | MessageContent, None, None]:
    for m in stream:
        for c in m.content:
            yield c
            time.sleep(delay)


def print_stream(stream: ChatStream, delay=0.01):
    for m in stream:
        for c in m.content:
            print(c, end="", flush=True)
            time.sleep(delay)

    print(end="", flush=True)


class ChatModel:
    def chat(
        self, messages: ChatMessages, params: ChatParameters | None = None
    ) -> ChatMessage:
        raise NotImplementedError()

    def chat_stream(
        self, messages: ChatMessages, params: ChatParameters | None = None
    ) -> Generator[ChatMessage, None, None]:
        raise NotImplementedError()


class ChatSession:
    def __init__(self, model: ChatModel, history: List[ChatMessage] | None = None):
        self.__model = model
        if history is None:
            self.__history = []
        else:
            self.__history = history

    @property
    def history(self) -> List[ChatMessage]:
        return self.__history

    def to_stream(
        self, stream: ChatStream, first: ChatMessage
    ) -> Generator[str, None, None]:
        yield first.content
        for m in stream:
            for c in m.content:
                yield c
                time.sleep(0.01)

    def chat_stream(self, prompt: str) -> Generator[str, None, None]:
        history = deepcopy(self.__history)
        history.append(ChatMessage(role="user", content=prompt))
        full_content = ""
        for m in self.__model.chat_stream(history):
            full_content += m.content
            for c in m.content:
                yield c
                time.sleep(0.01)

        history.append(ChatMessage(role="assistant", content=full_content))
        self.__history = history

    def chat(self, prompt: str) -> str:
        history = deepcopy(self.__history)
        history.append(ChatMessage(role="user", content=prompt))

        m = self.__model.chat(history)
        history.append(ChatMessage(role="assistant", content=m.content))
        self.__history = history

        return m.content


class GatewayV2(ChatModel):
    def __init__(self, config: ModelConfig):
        self.config = config

    def __str__(self):
        return self.config.model

    def build_url(self) -> str:
        return f"{self.config.endpoint}/api/v2/llm/chat"

    def build_headers(self, params: ChatParameters) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.config.token}",
            "AI-Gateway-Uid": params.user_id,
            "AI-Gateway-Product-Name": params.product_name,
            "AI-Gateway-Intention-Code": params.intention_code,
            # "X-Action-Id": ,
        }

    def build_base_llm_arguments(self, params: ChatParameters) -> dict:
        args = {}
        if params.top_p is not None:
            args["top_p"] = params.top_p
        if params.top_k is not None:
            args["top_k"] = params.top_k
        if params.max_tokens is not None:
            args["max_tokens"] = params.max_tokens
        if params.temperature is not None:
            args["temperature"] = params.temperature
        if params.stop is not None:
            if isinstance(params.stop, str):
                args["stop"] = [params.stop]
            elif isinstance(params.stop, list):
                args["stop"] = params.stop

        return args

    def build_message(self, messages: List[ChatMessage]) -> tuple[str | None, list]:
        system_prompt = ""
        new_messages = []

        if self.config.provider == "minimax":
            for m in messages:
                if m.role == "user":
                    new_messages.append(
                        {"role": "user", "name": UserName, "content": m.content}
                    )
                elif m.role == "assistant":
                    new_messages.append(
                        {"role": "assistant", "name": BotName, "content": m.content}
                    )
                elif m.role == "system":
                    system_prompt = m.content
        elif self.config.provider == "shangtang":
            for m in messages:
                if m.role == "user":
                    new_messages.append(
                        {"role": "user", "name": m.type, "content": m.content}
                    )
                elif m.role == "assistant":
                    new_messages.append(
                        {"role": "assistant", "name": m.type, "content": m.content}
                    )
                elif m.role == "system":
                    system_prompt = None
                    new_messages.append(
                        {"role": "system", "name": m.type, "content": m.content}
                    )

        else:
            for m in messages:
                if m.role == "user":
                    new_messages.append({"role": "user", "content": m.content})
                elif m.role == "assistant":
                    new_messages.append({"role": "assistant", "content": m.content})
                elif m.role == "system":
                    system_prompt = m.content

        if self.config.provider == "minimax" and system_prompt == "":
            system_prompt = "MM智能助理是一款由MiniMax自研的，没有调用其他产品的接口的大型语言模型。MiniMax是一家中国科技公司，一直致力于进行大模型相关的研究。"
        return system_prompt, new_messages

    def build_body(
        self, messages: List[ChatMessage], params: ChatParameters, stream: bool
    ) -> dict:
        global BotName
        if params.extended is not None:
            if "bot_setting" in params.extended:
                bs = params.extended["bot_setting"]
                if len(bs) > 0 and "bot_name" in bs[0]:
                    bot_name = bs[0]["bot_name"]
                    BotName = bot_name

        system_prompt, new_messages = self.build_message(messages)

        if params.extended is not None:
            extended_llm_arguments = {
                **params.extended
            } 
        elif self.config.provider == "minimax":
            extended_llm_arguments = {
                "bot_setting": [
                    {
                        "bot_name": BotName,
                        "content": system_prompt,
                    }
                ],
                "reply_constraints": {
                    "sender_type": "BOT",
                    "sender_name": BotName,
                },
                "mask_sensitive_info": False,
                "sample_messages": [],
            }
            if self.config.provider == "shangtang":
                if not system_prompt:
                    system_prompt = "你是由WPS创建的AI模型"

        else:
            extended_llm_arguments = {}

        if params.examples is not None:
            for m in params.examples:
                if isinstance(m, dict):
                    msg = {"role": m["role"], "content": m["content"], "name": ""} 
                    if "name" in m:
                        msg["name"] = m["name"]

                    new_messages.append(
                        msg
                    )
                elif isinstance(m, ChatMessage):
                    msg = { "role": m.role, "content": m.content, "name": ""}
                    new_messages.append(
                        msg
                    )

        body = {
            "stream": stream,
            "model": self.config.model,
            "provider": self.config.provider,
            "context": system_prompt,
            "messages": new_messages,
            "base_llm_arguments": self.build_base_llm_arguments(params),
            "extended_llm_arguments": {
                f"{self.config.provider}_{self.config.model}": extended_llm_arguments,
            },
            "sec_text": {
                "from": params.from_,
                "scene": params.scene,
                "extra_text": [""],
            },
        }
        if self.config.provider == "shangtang":
            del body["context"]
        if self.config.version:
            body["version"] = self.config.version
        return body

    def request(
        self, messages: ChatMessages, params: ChatParameters | None, stream: bool
    ) -> requests.Response:
        if params is None:
            params = ChatParameters()
        chat_messages = []
        for m in messages:
            if isinstance(m, ChatMessage):
                chat_messages.append(m)
            elif isinstance(m, dict):
                chat_messages.append(ChatMessage(role=m["role"], content=m["content"]))

        url = self.build_url()
        headers = self.build_headers(params)
        body = self.build_body(chat_messages, params, stream)

        with open("llm.log", "a", encoding="utf-8") as f:
            f.write(f"POST {url}\n")
            for k, v in headers.items():
                f.write(f"{k}: {v}\n")
            json.dump(body, f, indent="  ", ensure_ascii=False)
            f.write("\n")

        _logger.debug("url:\n%s\nheaders:\n%s\nbody:\n%s", url, headers, body)
        # print(json.dumps(body, indent=2, ensure_ascii=False))
        resp = requests.post(url, headers=headers, json=body, stream=stream)
        if resp.status_code != 200:
            err = resp.json()
            raise AIGatewayError(
                code=err.get("code", "Unknown"),
                msg=err.get("message", "unknown"),
                task_id=err.get("task_id", ""),
                external_id=err.get("external_id", ""),
            )
        return resp

    def chat(
        self, messages: ChatMessages, params: ChatParameters | None = None
    ) -> ChatMessage:
        resp = self.request(messages, params, False)
        rs = resp.json()
        _logger.debug("response:%s", rs)
        if rs["code"] != "Success":
            raise Exception(rs["message"])
        content = rs["choices"][0]["text"]
        reasoning_content = rs["choices"][0].get("reasoning_content", "")
        if reasoning_content:
            content = f"<reasoning_content>{reasoning_content}</reasoning_content>\n{content}"
        return ChatMessage(role="assistant", type="text", content=content)

    def chat_stream(
        self, messages: ChatMessages, params: ChatParameters | None = None
    ) -> Generator[ChatMessage, None, None]:
        resp = self.request(messages, params, True)
        sse = sseclient.SSEClient(resp)
        cot_started = False
        cot_ended = False
        for e in sse.events():
            _logger.debug("SSE event:%s data:%s", e.event, e.data)
            rs = json.loads(e.data)

            if rs["code"] != "Success":
                raise AIGatewayError(
                    code=rs.get("code", "Unknown"),
                    msg=rs.get("message", "unknown"),
                    task_id=rs.get("task_id", ""),
                    external_id=rs.get("external_id", ""),
                )
            reasoning_content = rs["choices"][0].get("reasoning_content", "")
            if reasoning_content:
                if not cot_started:
                    # yield ChatMessage(role='assistant', type='reasoning_content', content='<thinking>')
                    cot_started = True
                yield ChatMessage(
                    role="assistant",
                    type="reasoning_content",
                    content=reasoning_content,
                )
                continue
            if cot_started and not cot_ended:
                # yield ChatMessage(role='assistant', type='reasoning_content', content='</thinking>')
                cot_ended = True
            content = rs["choices"][0]["text"]
            yield ChatMessage(role="assistant", type="text", content=content)
        # print("输出：", rs)


class GatewayMultiModal(GatewayV2):
    def build_url(self) -> str:
        return f"{self.config.endpoint}/api/v2/llm/multimodal"

    def build_body(
        self, messages: List[ChatMessage], params: ChatParameters, stream: bool
    ) -> dict:
        new_messages = []
        system_prompt = ""
        for m in messages:
            if isinstance(m, dict):
                m = ChatMessage(role=m["role"], content=m["content"])

            if m.role == "assistant":
                new_messages.append({"role": m.role, "content": m.content})
            elif m.role == "user":
                new_messages.append({"role": m.role, "content": m.content})
            elif m.role == "system":
                system_prompt = m.content

        if params.extended is not None:
            extended_llm_arguments = {
                **params.extended
            } 
        else:
            extended_llm_arguments = {}

        body = {
            "stream": stream,
            "model": self.config.model,
            "provider": self.config.provider,
            "context": system_prompt,
            "messages": new_messages,
            "base_llm_arguments": self.build_base_llm_arguments(params),
            "extended_llm_arguments": {
                f"{self.config.provider}_{self.config.model}": extended_llm_arguments,
            },
            "sec_text": {
                "from": params.from_,
                "scene": params.scene,
                "extra_text": [""],
            },
        }
        print(json.dumps(body,ensure_ascii=False,indent=2))
        if self.config.version != "":
            body["version"] = self.config.version
        return body
    

class GatewayWithCache(GatewayV2):
    def build_url(self) -> str:
        return f"{self.config.endpoint}/api/v2/llm/chat/createCache"
    
    def build_body(
        self, messages: List[ChatMessage], params: ChatParameters, stream: bool
    ) -> dict:
        new_messages = []
        for m in messages:
            if isinstance(m, dict):
                m = ChatMessage(role=m["role"], content=m["content"])

            new_messages.append({"role": m.role, "content": m.content})

        model = self.config.model.split("-create")[0]
        body = {
            "stream": stream,
            "model": model,
            "provider": self.config.provider,
            "context": "",
            "messages": new_messages,
        }
        return body

    def chat(
        self, messages: ChatMessages, params: ChatParameters | None = None
    ) -> ChatMessage:
        resp = self.request(messages, params, False)
        rs = resp.json()
        _logger.debug("response:%s", rs)
        if rs["code"] != "Success":
            raise Exception(rs["message"])
        content = rs["external_id"]
        return ChatMessage(role="assistant", type="text", content=content)


class MinimaxModel(ChatModel):
    def __init__(self, config: ModelConfig):
        self._config = config

    def _chat_competion_v2(
        self, messages: list[ChatMessage], params: ChatParameters | None, stream: bool
    ) -> requests.Response:
        url = "https://api.minimax.chat/v1/text/chatcompletion_v2"
        headers = {
            "Authorization": f"Bearer {self._config.token}",
        }
        body = {
            "stream": stream,
            "model": self._config.model,
            "messages": [{"role": x.role, "content": x.content} for x in messages],
        }
        if params:
            if params.max_tokens is not None:
                body["max_tokens"] = params.max_tokens
            if params.temperature is not None:
                body["temperature"] = params.temperature
        return requests.post(url, headers=headers, json=body, stream=stream)

    def chat(
        self, messages: list[ChatMessage], params: ChatParameters = None
    ) -> ChatMessage:
        resp = self._chat_competion_v2(messages, params, False).json()
        return ChatMessage(
            role="assistant", content=resp["choices"][0]["message"]["content"]
        )

    def chat_stream(
        self, messages: list[ChatMessage], params: ChatParameters = None
    ) -> Generator[ChatMessage, None, None]:
        resp = self._chat_competion_v2(messages, params, True)
        for e in sseclient.SSEClient(resp).events():
            # print("[SSE]", e.data)
            data = json.loads(e.data)
            if "choices" in data:
                choice = data["choices"][0]
                delta = choice["delta"]["content"]
                yield ChatMessage(role="assistant", content=delta)
                if "finish_reason" in choice:
                    break
            else:
                if data["base_resp"]["status_code"] != 0:
                    raise Exception(data["base_resp"]["status_msg"])


@dataclass
class ModelFactory:
    provider: str
    factory: ...
    versions: list[str]

    def __str__(self):
        return self.provider

    def create(self, config: ModelConfig) -> ChatModel:
        config.provider = self.provider
        if config.version:
            # if version specified, check if valid
            if config.version not in self.versions:
                raise TypeError(f"invalid version, must be one of {self.versions}")
        else:
            # no version specified, choose first one
            if len(self.versions) > 0:
                config.version = self.versions[0]
        return self.factory(config)


class ArkModel:
    def __init__(self, config: ModelConfig):
        model2ep = {
            "deepseek-v3": "ep-20250205102543-lcndc",
            "deepseek-r1": "ep-20250205102115-cmb9z",
            "deepseek-r1-distill-qwen-32b": "ep-20250207145251-v9qvh",
        }
        if config.model not in model2ep:
            ep = ""
        else:
            ep = model2ep[config.model]
        self._model = ep
        self._token = "1ca8b973-f6d6-4c92-8471-8f7d8193d380"
        self._url = "https://ark.cn-beijing.volces.com/api/v3/chat/completions"

    def request(
        self,
        messages: list,
        temperature: float = None,
        stop: str = None,
        stream: bool = False,
    ) -> requests.Response:
        headers = {
            "Authorization": f"Bearer {self._token}",
        }
        if len(messages) == 0:
            raise Exception("empty messages!")

        body = {
            "model": self._model,
            "stream": stream,
            "messages": messages,
            "max_tokens": 4096,
        }
        # print('body:', body)

        if temperature is not None:
            body["temperature"] = temperature
        if stop is not None:
            body["stop"] = [stop]

        with open("llm.log", "a", encoding="utf-8") as f:
            f.write(f"POST {self._url}\n")
            for k, v in headers.items():
                f.write(f"{k}: {v}\n")
            json.dump(body, f, indent="  ", ensure_ascii=False)
            f.write("\n")

        resp = requests.post(
            self._url, stream=stream, json=body, headers=headers, timeout=30
        )
        if resp.status_code != 200:
            raise Exception(f"{resp.status_code}: {resp.text}")
        return resp

    def chat(self, messages: list, params: ChatParameters = None) -> ChatMessage:
        resp = self.request(messages, params.temperature, None, False)
        event = resp.json()
        choice = event["choices"][0]["message"]
        return ChatMessage(content=choice.get("content", ""))

    def chat_stream(
        self, messages: list, params: ChatParameters = None
    ) -> Generator[ChatMessage, None, None]:
        resp = self.request(messages, params.temperature, None, True)
        sse = sseclient.SSEClient(resp)
        done = False

        content = ""
        reasoning_content = ""
        buffered = ""

        for ev in sse.events():
            if ev.data == "[DONE]":
                done = True
                break
            event = json.loads(ev.data)
            if event["object"] == "chat.completion.chunk":
                choice = event["choices"][0]
                if "delta" in choice:
                    delta = choice["delta"]
                    # print('[chat.completion.chunk]:', delta.get('content', ''))
                    delta_content = delta.get("content", "")
                    buffered += delta_content
                    content += delta_content
                    reasoning_content += delta.get("reasoning_content", "")

                    if c := delta.get("reasoning_content"):
                        yield ChatMessage("assistant", "reasoning_content", c)
                    if c := delta.get("content"):
                        yield ChatMessage("assistant", "text", c)

                if "finish_reason" in choice and choice["finish_reason"]:
                    done = True
                    break

        if not done:
            raise EOFError("nodata")


class Deepseek(ArkModel):
    def __init__(self, config: ModelConfig):
        super().__init__(config)
        model2ep = {
            "deepseek-v3-original": "deepseek-chat",
            "deepseek-r1-original": "deepseek-reasoner",
        }
        ep = model2ep[config.model]
        self._model = ep
        self._token = "xxx"
        self._url = "https://api.deepseek.com/chat/completions"


__models__: dict[str, ModelFactory] = {
    "abab7-chat-preview": ModelFactory("minimax", GatewayV2, []),
    "abab6.5s-chat": ModelFactory("minimax", GatewayV2, []),
    "abab6.5-chat": ModelFactory("minimax", GatewayV2, []),
    # 'gpt-4': ModelFactory('azure', GatewayMultiModal, ['turbo-2024-04-09']),
    "gpt-4": ModelFactory("azure", GatewayV2, ["turbo-2024-04-09"]),
    "gpt-4o": ModelFactory("azure", GatewayV2, ["2024-05-13"]),
    # 'gpt-4o': ModelFactory( 'azure', GatewayMultiModal, ['2024-05-13']),
    "claude-3-5-sonnet": ModelFactory("aws", GatewayV2, ["20240620-v1:0"]),
    "glm-4": ModelFactory("zhipu", GatewayV2, []),
    "glm-4-air": ModelFactory("zhipu", GatewayV2, []),
    "chatglm-wps": ModelFactory("zhipu", GatewayV2, []),
    "ernie-lite-8k": ModelFactory("baidu", GatewayV2, []),
    "ernie-bot-4": ModelFactory("baidu", GatewayV2, []),
    "ernie-3.5-128k": ModelFactory("baidu", GatewayV2, []),
    "Doubao-pro-32k": ModelFactory("doubao", GatewayV2, []),
    "Doubao-pro-128k": ModelFactory("doubao", GatewayV2, []),
    "Doubao-pro-256k": ModelFactory("doubao", GatewayV2, []),
    "Doubao-vision-pro-32k": ModelFactory("doubao", GatewayMultiModal, []),
    "Doubao-1.5-pro-32k": ModelFactory("doubao", GatewayV2, []),
    "Doubao-1.5-pro-256k": ModelFactory("doubao", GatewayV2, []),
    "Doubao-1.5-vision-pro-32k": ModelFactory("doubao", GatewayMultiModal, []),
    "doubao-1.5-thinking-pro-m-250428": ModelFactory("doubao", GatewayV2, []),
    
    "doubao-1.5-thinking-pro": ModelFactory("doubao", GatewayV2, []),
    "step-1v-8k": ModelFactory("stepfun", GatewayMultiModal, []),
    "step-1v-32k": ModelFactory("stepfun", GatewayMultiModal, []),
    "deepseek-chat": ModelFactory("deepseek", GatewayV2, ["0324"]),
    "deepseek-chat-ark": ModelFactory("deepseek", ArkModel, []),
    "deepseek-chat-ali": ModelFactory("deepseek", GatewayV2, ["0324"]),
    "deepseek-reasoner": ModelFactory("deepseek", GatewayV2, ["0528"]),
    "deepseek-r1-distill-qwen-32b": ModelFactory("deepseek", ArkModel, []),
    "deepseek-reasoner-ark": ModelFactory("deepseek", GatewayV2, []),
    "deepseek-reasoner-ali": ModelFactory("deepseek", GatewayV2, []),
    "SenseChat-Code-Excel-WPS": ModelFactory("shangtang", GatewayV2, []),
    "deepseek-v3-original": ModelFactory("deepseek", Deepseek, []),
    "qwq-32b": ModelFactory("ali", GatewayV2, []),
    "Doubao-1.5-pro-32k-cache": ModelFactory("doubao", GatewayV2, []),
    "Doubao-1.5-pro-32k-cache-create": ModelFactory("doubao", GatewayWithCache, []),
    "qwen-plus-latest": ModelFactory("ali", GatewayV2, []),
}

GatewayTypes = Literal["product", "test"]


def providers() -> list[str]:
    providers = []
    for f in __models__.values():
        if f.provider not in providers:
            providers.append(f.provider)
    return providers


def provider_models(proivder: str) -> list[str]:
    names = []
    for name, f in __models__.items():
        if f.provider == proivder:
            names.append(name)
    return names


def model_versions(name: str) -> list[str]:
    for n, f in __models__.items():
        if n == name:
            return f.versions
    return []


def model(name: str, token: str, endpoint: str = Development) -> "ChatModel":
    config = ModelConfig(model=name, token=token, endpoint=endpoint, version="")
    for n, f in __models__.items():
        if n == name:
            return f.create(config)
    raise Exception(f"unknown model: {name}")


class AutoChatModel:
    def __init__(
        self, name: str, token: str, endpoint: str = Development
    ) -> "AutoChatModel":
        config = ModelConfig(model=name, token=token, endpoint=endpoint, version="")
        for n, f in __models__.items():
            if n == name:
                self._model = f.create(config)
                return
        raise Exception(f"unknown model: {name}")

    def __call__(
        self, messages: ChatMessages, params: ChatParameters, stream: bool
    ) -> str | Generator[ChatMessage, None, None]:
        if stream:
            for c in self._model.chat_stream(messages, params):
                yield c
        else:
            return self._model.chat(messages, params)

    def chat_stream(
        self, messages: ChatMessages, params: ChatParameters = None
    ) -> Generator[ChatMessage, None, None]:
        for m in self._model.chat_stream(messages, params):
            yield m

    def chat(
        self, messages: ChatMessages, params: ChatParameters = None
    ) -> ChatMessage:
        resp = self._model.chat(messages, params)
        return resp
