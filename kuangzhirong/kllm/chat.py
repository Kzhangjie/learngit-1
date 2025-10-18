from .llm import AutoChatModel, ChatMessage, ChatParameters, Development
from .config import AutoConfig
from typing import Generator,Literal

ModelNames = Literal[
    #minimax
    'abab7-chat-preview',
    'abab6.5s-chat',
    'abab6.5-chat',
    #azure
    'gpt-4',
    'gpt-4o',
    #aws
    'claude-3-5-sonnet',
    #zhipu
    'glm-4',
    'glm-4-air',
    'chatglm-wps',
    #baidu
    'ernie-lite-8k',
    'ernie-bot-4',
    'ernie-3.5-128k',
    #doubao
    'Doubao-pro-32k',
    'Doubao-vision-pro-32k',
    'Doubao-pro-128k',
    'Doubao-pro-256k',
    'Doubao-vision-pro-32k',
    'Doubao-1.5-pro-32k',
    'Doubao-1.5-pro-256k',
    'Doubao-1.5-vision-pro-32k',
    "doubao-1.5-thinking-pro"
    #stepfun
    'step-1v-8k',
    'step-1v-32k',    
    #deepseek
    'deepseek-chat',
    'deepseek-reasoner',
    'deepseek-reasoner-ark',
    'deepseek-reasoner-ali',
    'deepseek-chat',
    'deepseek-chat-ark',
    'deepseek-chat-ali',
    'deepseek-r1-distill-qwen-32b',
    'deepseek-v3-original',
    #ali
    'qwq-32b',
    'qwen-plus-latest',
    #sensetime
    'SenseChat-Code-Excel-WPS'
]

class ChatCompletion:
    def __init__(self, model:ModelNames, token:str, endpoint: str = Development):
        self._model = AutoChatModel(model, token=token, endpoint=endpoint)

    def __call__(self, messages:list, stream:bool=False, **kwargs) -> ChatMessage|Generator[ChatMessage,None,None]:
        params = ChatParameters(**kwargs)
        chat_messages = []
        for m in messages:
            if isinstance(m, ChatMessage):
                chat_messages.append(m)
            elif isinstance(m, dict):
                chat_messages.append(ChatMessage(role=m['role'],content=m['content']))
            else:
                raise TypeError('invalid message type' + str(type(m)))
        if len(chat_messages) == 0:
            raise Exception('messages is not allow empty')
        
        if stream:
            return self._model.chat_stream(messages, params)
        else:
            return self._model.chat(messages,params)


def completion(model:ModelNames, token:str|None = None, endpoint: str = Development) -> ChatCompletion:
    if token is None:
        token = AutoConfig.get("llm.token")
        if token is None:
            raise Exception("No token")
    return ChatCompletion(model, token, endpoint)

Role = Literal['system','user','assistant']
Images = list[bytes|str]

def message(role:Role, content='', images:Images=None) -> ChatMessage:
    msg = ChatMessage(role=role, content=content)
    if images is not None:
        for img in images:
            msg.add_image(img)
    return msg
