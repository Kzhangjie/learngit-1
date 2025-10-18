from dataclasses import asdict, dataclass
import os
import json
from typing import Generator, Literal, Callable
import requests
import sseclient
import inspect
from pprint import pprint

@dataclass
class Parameter:
    type:Literal['string','int']
    description:str
    required:bool = True

@dataclass
class Function:
    name:str
    description:str
    properties:dict[str,dict]
    #call:Callable[[any],None]

    def to_dict(self) -> dict:
        d = {
            'type': 'function',
            'function': {
                'name': self.name,
                'description': self.description,
                'parameters': {}
            },
        }

        if self.properties:
            parameters = {
                'type': 'object',
                'properties': {},
                'required': []
            }
            for k, v in self.properties.items():
                parameters['properties'][k] = v
                if 'required' in v:
                    parameters['required'].append(k)
            d['function']['parameters'] = parameters
        return d

@dataclass
class ToolCall:
    name:str = ''
    arguments:str = ''
    index:int = -1
    id:str = ''

    def to_dict(self) -> dict:
        return {
            'type': 'function',
            'function':{
                'name': self.name,
                'arguments': self.arguments,
            },
            'index': self.index,
            'id': self.id,
        }

@dataclass
class ChatMessage:
    role:Literal['system','user','assistant','tool']
    content:str|None = None
    tool_call_id:str|None = None
    reasoning_content:str|None = None
    tool_calls:list[ToolCall]|None = None

    def to_dict(self) -> dict:
        msg = {
            'role': self.role,
        }
        if self.content:
            msg['content'] = self.content
        if self.tool_call_id:
            msg['tool_call_id'] = self.tool_call_id
        if self.tool_calls:
            msg['tool_calls'] = [x.to_dict() for x in self.tool_calls]
        return msg

class Tool:
    name:str
    description:str
    properties:dict[str,dict]

    def __call__(self, **kwargs):
        raise NotImplementedError()

    def history_res_map(self, execution):
        return execution

    def clean_up(self):
        pass

__tools__: dict[str, type[Tool]] = {}

def list_tools() -> list[str]:
    return [name for name in __tools__.keys()]

def register_tool(clz: type[Tool]):
    __tools__[clz.name] = clz

def concat_tool_calls(src:list[ToolCall]) -> list[ToolCall]:
    dst:list[ToolCall] = []
    for delta in src:
        while len(dst) <= delta.index:
            dst.append(ToolCall())

        target = dst[delta.index]
        if delta.name:
            target.name += delta.name
        if delta.index != -1:
            target.index = delta.index
        if delta.id:
            target.id += delta.id
        if delta.arguments:
            target.arguments += delta.arguments
    #print('merge_tool_calls', dst)
    return dst

class ChatCompletion:
    def generate(self, messages:list[ChatMessage], tools:list[Function]|None = None) -> Generator[ChatMessage,None,None]:
        raise NotImplementedError()

class OpenAI(ChatCompletion):
    def __init__(self, model:str, token:str, endpoint:str, temperature: float = 0.1):
        self.__model = model
        self.__token = token
        self.__url = endpoint
        self.__temperature = temperature

    def request(self, messages:list[ChatMessage], tools:list[Function]|None, stream:bool, max_tokens:int) -> requests.Response:
        headers = {
            'Authorization': f'Bearer {self.__token}',
        }
        if len(messages) == 0:
            raise Exception('empty messages!')

        body = {
            'model': self.__model,
            'stream': stream,
            'messages': [x.to_dict() for x in messages],
            'temperature': self.__temperature,
        }
        if tools:
            body['tools'] = [x.to_dict() for x in tools]
            #body['tool_choice'] = 'auto'

        if max_tokens is not None:
            body['max_tokens'] = max_tokens
        # pprint(body)

        resp = requests.post(self.__url, stream=stream, json=body, headers=headers, timeout=30)
        if resp.status_code != 200:
            raise Exception(f'{resp.status_code}: {resp.text}')
        return resp

    def generate(self, messages:list[ChatMessage], tools:list[Function]|None = None) -> Generator[ChatMessage,None,None]:
        resp = self.request(messages, tools, stream=True, max_tokens=8000)
        sse = sseclient.SSEClient(resp)
        done = False

        content = ''
        reasoning_content = ''
        #all_tool_calls:list[ToolCall] = []

        for ev in sse.events():
            if ev.data == '[DONE]':
                done = True
                break
            #print('[SSE]', ev.data)
            event = json.loads(ev.data)
            if event['object'] == 'chat.completion.chunk':
                choice = event['choices'][0]
                if 'delta' in choice:
                    delta:dict = choice['delta']
                    #print('[chat.completion.chunk]:', delta)
                    reasoning_content = delta.get('reasoning_content', None)
                    if reasoning_content is not None:
                        yield ChatMessage(role='assistant',reasoning_content=reasoning_content)

                    content = delta.get('content', None)
                    if content is not None:
                        yield ChatMessage(role='assistant',content=content)

                    tool_calls = delta.get('tool_calls', None)
                    if tool_calls:
                        #print(tool_calls)
                        for tool_call in tool_calls:
                            #if tool_call['type'] != 'function':
                            #    continue

                            func = tool_call['function']
                            tc = ToolCall(
                                name=func.get('name', ''),
                                arguments=func.get('arguments', ''),
                                index=tool_call.get('index',-1),
                                id=tool_call.get('id',''),
                            )
                            yield ChatMessage(role='assistant', tool_calls=[tc])
                            #all_tool_calls.append(tc)
                            #print('[SSE]:', tc)
                            #"tool_calls":[{"function":{"name":"web_search","arguments":"{\"query\": \""},"index":0,"id":"call_caf20c5531e94507b2679e","type":"function"}]
                            #"tool_calls":[{"function":{"arguments":null},"index":0,"id":"","type":"function"}]},"index":0}]


                if 'finish_reason' in choice and choice['finish_reason']:
                    done = True
                    break

        if not done:
            raise EOFError('nodata')
        #if all_tool_calls:
        #    all_tool_calls = concat_tool_calls(all_tool_calls)
        #    yield ChatMessage(role='assistant', tool_calls=all_tool_calls)



class AIGateway(ChatCompletion):
    def __init__(self, model:str, provider:str, temperature: float = 0.1, token:str|None=None, reasoning: bool = False):
        if not token:
            from kuangzhirong.kllm.config import AutoConfig
            t = AutoConfig.get("llm.token")
            if not isinstance(t, str):
                raise Exception('token is None')
            token = t

        self.__model = model
        self.__token = token
        self.__url = f"http://ai-gateway.wps.cn/api/v2/llm/chat"
        self.__provider = provider
        self.__temperature = temperature
        self.__reasoning = reasoning


    def build_messages(self, messages: list[ChatMessage]) -> tuple[str | None, list]:
        system_prompt = ""
        new_messages = []

        def tool_calls_to_json(tool_calls):
            return [tool_call.to_dict() for tool_call in tool_calls]

        for m in messages:
            if m.role == "user":
                new_messages.append(m.to_dict())
            elif m.role == "assistant":
                new_messages.append(m.to_dict())
            elif m.role =='tool':
                new_messages.append(m.to_dict())
            elif m.role == "system":
                system_prompt = m.content
        return system_prompt, new_messages

    def build_body(self, messages: list[ChatMessage], tools: list[Function], stream: bool) -> dict:
        
        system_prompt, new_messages = self.build_messages(messages)
        # new_messages = [x.to_dict() for x in messages]

        extended_llm_arguments = {
            "parameters": {
                "enable_thinking": True
            }
        } if self.__reasoning else {}

        body = {
            "stream": stream,
            "model": self.__model,
            "provider": self.__provider,
            "context": system_prompt,
            "messages": new_messages,
            "base_llm_arguments": {
                "max_tokens": 8000,
            },
            "extended_llm_arguments": {
                f"{self.__provider}_{self.__model}": extended_llm_arguments,
            },
            "sec_text": {
                "from": 'AI_APPLICATION_TOOLS',
                "scene": 'conversational_bots',
                "extra_text": [""],
            },
            "temperature": self.__temperature,
        }
        if tools:
            body['tools'] = [x.to_dict() for x in tools]
        if self.__model == "deepseek-reasoner":
            body['version'] = "0528"
        elif self.__model == "deepseek-chat":
            body['version'] = "0324"
        if self.__model == "Doubao-Seed-1.6":
            extended_llm_arguments['thinking'] = {"type": "enabled"}
            # extended_llm_arguments['thinking'] = {"type": "disabled"}
            # extended_llm_arguments['thinking'] = {"type": "auto"}
        return body

    def request(self, messages: list[ChatMessage], tools: list[Function]|None=None, stream: bool=True) -> requests.Response:
        headers = {
            "Authorization": f"Bearer {self.__token}",
            # 'AI-Gateway-Uid': '9003',
            'AI-Gateway-Uid': '9031',
            'AI-Gateway-Product-Name': '365wps-copilotchat-web',
            'AIGC-GATEWAY-UI-POSITION': 'menu-1',
            'AI-Gateway-Intention-Code': '365wps_cc_chat',
            # "X-Action-Id": ,
        }
        # pprint(headers)
        body = self.build_body(messages, tools, stream)
        pprint(body)
        resp = requests.post(self.__url, headers=headers, json=body, stream=stream)
        if resp.status_code != 200:
            err = resp.json()
            raise Exception(err.get("message", "unknown"))
        return resp

    def generate(self, messages:list[ChatMessage], tools:list[Function]|None = None) -> Generator[ChatMessage,None,None]:
        resp = self.request(messages, tools, True)
        sse = sseclient.SSEClient(resp)
        for e in sse.events():
            rs = json.loads(e.data)
            # print('[SSE]', rs)

            if rs["code"] != "Success":
                raise Exception(rs.get("message", "unknown"))

            reasoning_content = rs["choices"][0].get("reasoning_content", '')
            if reasoning_content:
                yield ChatMessage(role="assistant", reasoning_content=reasoning_content)
            content = rs["choices"][0].get("text", '')
            if content:
                yield ChatMessage(role="assistant", content=content)

            tool_calls = rs["choices"][0].get('tool_calls', None)
            if tool_calls:
                #print(tool_calls)
                for tool_call in tool_calls:
                    #if tool_call['type'] != 'function':
                    #    continue

                    func = tool_call['function']
                    tc = ToolCall(
                        name=func.get('name', ''),
                        arguments=func.get('arguments', ''),
                        index=tool_call.get('index',-1),
                        id=tool_call.get('id',''),
                    )
                    yield ChatMessage(role='assistant', tool_calls=[tc])

        print('[SSE] complete')
        # print("输出：", rs)

def model_by_name(name:str, temperature: float = 0.1, reasoning:bool=False) -> ChatCompletion:
    if name == 'qwen3-235b-a22b':
        # return OpenAI('qwen3-235b-a22b', os.environ.get('DASHSCOPE_API_KEY', ''), 'https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions', temperature=temperature)
        return AIGateway(model='qwen-plus-latest', provider='ali', temperature=temperature, reasoning=reasoning)
    elif name == 'deepseek-reasoner':
        return AIGateway(model='deepseek-reasoner', provider='deepseek', temperature=temperature, reasoning=reasoning)
    elif name == 'deepseek-chat':
        return AIGateway(model='deepseek-chat', provider='deepseek', temperature=temperature, reasoning=reasoning)
    elif name == 'doubao-1.5-thinking-pro':
         return AIGateway(model='doubao-1.5-thinking-pro', provider='doubao', temperature=temperature, reasoning=True)
    elif name == 'Doubao-Seed-1.6':
        return AIGateway(model='Doubao-Seed-1.6', provider='doubao', temperature=temperature, reasoning=False)
    elif name == 'Doubao-Seed-1.6-thinking':
        return AIGateway(model='Doubao-Seed-1.6-thinking', provider='doubao', temperature=temperature, reasoning=True)
        # return OpenAI('ep-m-20250506145749-zvght', os.environ.get('ARK_DOUBAO_API_KEY', ''), 'https://ark.cn-beijing.volces.com/api/v3/chat/completions', temperature=temperature)
    elif name == 'qwen3-8b':
        return OpenAI('code_interpreter_qwen3', '', 'http://120.92.122.107:30818/kas/kmnjuopc906vfp7vdhr3pfqjpr5c/v1/chat/completions?model=code_interpreter_qwen3', temperature=temperature)
    else:
        raise Exception(f'unknown model {name}')

class Agent:
    def get_history(self):
        return [x.to_dict() for x in self.__history]

    def __init__(self, model:ChatCompletion, system_prompt:str = '', tools:list[str] = []):
        self.__model = model
        self.__tools_names = tools
        self.__tools = {
            name: __tools__[name]() for name in tools
        }
        self.__history:list[ChatMessage] = []
        if system_prompt:
            self.__history.append(ChatMessage(role='system',content=system_prompt))

    def __del__(self):
        for name in self.__tools_names:
            tool = self.__tools[name]
            tool.clean_up()

    def clean_up(self):
        for name in self.__tools_names:
            tool = self.__tools[name]
            tool.clean_up()

    def call_tool(self, tool_call:ToolCall):
        tool = self.__tools[tool_call.name]

        args = json.loads(tool_call.arguments)
        execution = tool(**args)
        history_res = tool.history_res_map(execution)
        if not isinstance(execution, str):
            execution = json.dumps(execution, ensure_ascii=False)
        if not isinstance(history_res, str):
            history_res = json.dumps(history_res, ensure_ascii=False)
        return execution, history_res

    def started_chat(self) -> bool:
        return len(self.__history) > 1

    def chat(self, prompt:str) -> Generator[ChatMessage,None,None]:
        messages = self.__history + [ChatMessage(role='user',content=prompt)]
        tools:list[Function] = []
        for name in self.__tools_names:
            tool = self.__tools[name]
            sign = Function(name=tool.name,description=tool.description,properties=tool.properties)
            tools.append(sign)

        while True:
            reasoning_content = ''
            content = ''
            tool_calls:list[ToolCall] = []

            for m in self.__model.generate(messages, tools=tools):
                if m.reasoning_content:
                    reasoning_content += m.reasoning_content
                    yield ChatMessage(role='assistant',reasoning_content=m.reasoning_content)
                if m.content:
                    content += m.content
                    yield ChatMessage(role='assistant',content=m.content)
                if m.tool_calls:
                    tool_calls += m.tool_calls

            tool_calls = concat_tool_calls(tool_calls)
            messages.append(ChatMessage(role='assistant',content=content,tool_calls=tool_calls))
            yield ChatMessage(role='assistant',tool_calls=tool_calls)

            if tool_calls:
                for tool_call in tool_calls:
                    try:
                        execution, history_content = self.call_tool(tool_call)
                        m = ChatMessage(role='tool', content=execution, tool_call_id=tool_call.id)
                        history_m = ChatMessage(role='tool', content=history_content, tool_call_id=tool_call.id)
                        messages.append(history_m)
                        yield m
                    except:
                        m = ChatMessage(role='assistant', content='function call failed', tool_call_id=tool_call.id)
                        history_m = ChatMessage(role='tool', content='function call failed', tool_call_id=tool_call.id)
                        messages.append(history_m)
                        yield m
            else:
                break

        self.__history = messages

import streamlit as st

def to_streamlit(stream:Generator[ChatMessage,None,None]):
    content = ''
    try:
        m = next(stream)
        while True:
            if m.reasoning_content is not None:
                reasoning_content = ''
                with st.status('深度思考'):
                    output = st.empty()
                    while m.reasoning_content is not None:
                        #print(m)
                        reasoning_content += m.reasoning_content
                        output.code(reasoning_content,language=None,wrap_lines=True)
                        m = next(stream)
            elif m.content is not None:
                content = ''
                output = st.empty()
                while m.content is not None:
                    #print(m)
                    content += m.content
                    output.markdown(content)
                    m = next(stream)
            elif m.tool_calls is not None:
                for tool_call in m.tool_calls:
                    with st.status(f'**{tool_call.name}**: {tool_call.arguments}'):
                        tool_response = next(stream)
                        assert(tool_response.role == 'tool')
                        st.code(tool_response.content,language=None,wrap_lines=True)

                m = next(stream)
            else:
                raise Exception('XXX')
    except StopIteration:
        pass

    return content
