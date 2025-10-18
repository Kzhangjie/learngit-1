from concurrent.futures import ThreadPoolExecutor, as_completed
from email.utils import formatdate
import hashlib
import json
from urllib.parse import urlparse
from .config import AutoConfig
from dataclasses import dataclass
import requests
from typing import Generator
import datetime

@dataclass
class Reference:
    url:str
    title:str
    summary:str
    time_desc:str
    favicon:str
    index:str = ""

class websearch:
    def __init__(self, wps_sid:str = None, token:str = None):
        if wps_sid is None:
            wps_sid = AutoConfig.get('wps_sid')
        if token is None:
            token = AutoConfig.get('lingxi.token')

        self.__headers = {
            'Cookie': f'wps_sid={wps_sid}',
            'Authorization': f'Bearer {token}',
        }

    def __call__(self, query:str):
        body = {
            'query': query,
        }
        resp = requests.post('https://copilot.wps.cn/api/aigc/v3/dev/websearch', json=body, headers=self.__headers)
        res = resp.json()
        if resp.status_code != 200:
            raise Exception(res['result'])
        return [ Reference(**x) for x in res['data']['references'] ]

@dataclass
class QA:
    question:str
    answer:str
    similarity:float

class help:
    def __init__(self, **kwargs):
        pass

    def __call__(self, query:str):
        token = AutoConfig.get('lingxi.token')
        headers = {
            'Authorization': f'Bearer {token}',
        }
        body = {
            'question': query,
        }
        resp = requests.post('https://lingxi.wps.cn/api/raghelper/recommend', json=body, headers=headers)
        if resp.status_code != 200:
            raise Exception("failed with status:" + resp.status_code)
        res = resp.json()
        return [ QA(**x) for x in res['qa_pairs'] ]

@dataclass
class AdminSession:
    client_type:str
    company_id:str
    create_time:str
    creator_id:str
    session_id:str
    session_title:str
    user_agent:str
    user_agent_info:dict

@dataclass
class AdminMessage:
    #message_id:str
    role:str
    type:str
    content:str
    #request_id:str

class admin:
    def __init__(self, wps_sid:str = None):
        if wps_sid is None:
            wps_sid = AutoConfig.get('wps_sid')
        self.__cookies = {
            'wps_sid': wps_sid,
        }

    def __request(self, method:str, url:str, **kwargs) -> dict:
        if 'cookies' not in kwargs:
            kwargs['cookies'] = self.__cookies
        resp = requests.request(method, url, **kwargs)
        res = resp.json()
        if res['result'] != 'ok':
            raise Exception(f"{res['result']}")
        return res['data']
        
    def sessions(self, date:datetime.datetime) -> Generator[AdminSession,None,None]:
        start_time = date
        end_time = date + datetime.timedelta(days=1)

        params = {
            'next_page_token': '0',
            'limit': 20,
            'start_time': int(start_time.timestamp()),
            'end_time': int(end_time.timestamp()),
            'order': 'desc'
        }

        while True:
            data = self.__request('GET', 'https://copilot.wps.cn/api/aigc/admin/cc/sessions', params=params)
            if not data['list']:
                return
            
            for s in data['list']:
                session = AdminSession(**s)
                create_time = datetime.datetime.strptime(session.create_time, "%Y-%m-%d %H:%M:%S")
                if create_time > end_time:
                    continue
                if create_time < start_time:
                    continue
            
                yield session
            params['next_page_token'] = str(data['next_page_token'])

    def messages(self, session_id:str) -> list[AdminMessage]:
        params = {
            'message_type': 'outside',
            'offset': 0,
            'limit': 100,
        }
        data = self.__request('GET', f'https://copilot.wps.cn/api/aigc/admin/cc/sessions/{session_id}/messages', params=params)
        if not data['list']:
            return []
        return [ AdminMessage(role=m['role'],type=m['type'],content=m['content']) for m in data['list'] ] 
    

@dataclass
class Action:
    function:str
    args:dict

class planning:
    def __init__(self, url:str = 'http://120.92.122.107:30818/kas/ybsjuqhgzi9-qkatvhtcdydnav5x/api/chat/completions?model=latest', model:str = 'copilot365'):
        self.__url = url
        self.__model = model

    def __call__(self, prompt:str, temperature:float = 0.01, max_tokens:int = 4096) -> Action:
        now = datetime.datetime.now().strftime('%Y年%m月%d日')
        body = {
            "model": self.__model,
            "temperature": temperature,
            "max_new_tokens": max_tokens,
            'stop': ["<|endofblock|>", "<|endofmessage|>"],
            'messages': [
                {
                    'role': 'system',
                    'type': 'text',
                    'content': f'今天是{now}',    
                },
                {
                    'role': "user",
                    "type": "text",
                    "content": prompt,
                },
            ],
            "stream": False
        }
        resp = requests.post(self.__url, json=body)
        if resp.status_code != 200:
            raise Exception(f"planner error:{resp.status_code},返回内容:{resp.text}")
        res = resp.json()
        extented = json.loads(res['choices'][0]["message"]["content"])
        return Action(function=extented['function'], args=extented)

def wps2signing(req:requests.Request, ak:str, sk:str):
    '''
    用法：
    req = requests.Request('get', url=url)
    req = requests.Request('put', url=url, data=data)
    req = requests.Request('put', url=url, json=object)
    req = wps2_sign(req, ak, sk)
    requests.session().send(req)
    '''
    if not isinstance(req, requests.Request):
        raise TypeError(str(type(req)) + " not requests.Request")

    if req.method == "get":
        uri = urlparse(req.url)
        path_with_query = uri.path + (f'?{uri.query}' if uri.query else '')
        md5 = hashlib.md5(path_with_query.encode()).hexdigest()
    else:
        data = req.data
        if not data and req.json is not None:
            data = json.dumps(data)
        md5 = hashlib.md5(data.encode()).hexdigest()

    date = formatdate(timeval=None, localtime=False, usegmt=True)
    ct = 'application/json'
    authorization = f'WPS-2:{ak}:' + hashlib.sha1((sk+md5+ct+date).encode()).hexdigest()
    headers = {
        "Content-Type": ct,
        "Date": date,
        "Authorization": authorization,
        "Content-Md5": md5
    }

    prepare = req.prepare()
    prepare.headers.update(headers)
    return prepare


@dataclass
class URLInfo:
    url:str
    title:str
    content:str

def fetch_website(url:str, timeout:float=5.0) -> URLInfo:
    access_key = 'AK20240507GVUGZP'
    secret_key = '7fdafb2d5afb062163be0504d1e93cc2'

    body = {
        "readability": True,
        "request": 'smart',
        "return_format": 'markdown',
        "url": url,
        "with_favicon": False,
        'enable_image_cache': True,
    }
    headers = {
        'Host': 'aibot-api.wps.cn',
        'Content-Type': 'application/json',
    }
    req = requests.Request(method='post', url='http://120.92.124.158/office/v5/dev/ai/crawler/crawl', data=json.dumps(body), headers=headers)
    prepare = wps2signing(req, access_key, secret_key)

    try:
        res = requests.session().send(prepare, timeout=timeout).json()
        if res['code'] != 0:
            return None
        info = res['data']['res_infos'][0]
        if info['status'] != 200:
            return None
        title = info['metadata'].get('title', '')
        content = info['content']
        return URLInfo(url=url, title=title, content=content)
    except:
        return None

def fetch_urls(urls:list[str], concurrency:int=5, timeout:float=5.0) -> list[URLInfo]:
    if len(urls) == 0:
        return []
    
    def run(url:str) -> URLInfo:
        access_key = 'AK20240507GVUGZP'
        secret_key = '7fdafb2d5afb062163be0504d1e93cc2'

        body = {
            "readability": True,
            "request": 'smart',
            "return_format": 'markdown',
            "url": url,
            "with_favicon": False,
            'enable_image_cache': True,
        }
        headers = {
            'Host': 'aibot-api.wps.cn',
            'Content-Type': 'application/json',
        }
        req = requests.Request(method='post', url='http://120.92.124.158/office/v5/dev/ai/crawler/crawl', data=json.dumps(body), headers=headers)
        prepare = wps2signing(req, access_key, secret_key)
        try:
            res = requests.session().send(prepare, timeout=timeout).json()
            if res['code'] != 0:
                return None
            info = res['data']['res_infos'][0]
            if 'status' in info and info['status'] != 200:
                return None
            title = info['metadata'].get('title', '')
            content = info['content']
            return URLInfo(url=url, title=title, content=content)
        except:
            return None
        
    with ThreadPoolExecutor(len(urls)) as executor:
        result:list[URLInfo] = []
        futures = [executor.submit(run, url) for url in urls]
                           
        for future in as_completed(futures):
            res = future.result()
            if res is not None:
                result.append(res)
        return result
