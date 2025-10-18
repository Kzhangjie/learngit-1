import requests
from dotenv import load_dotenv
load_dotenv()
from utils import getLogger
import json
import os
logger = getLogger(os.path.splitext(os.path.basename(__file__))[0])
WPS_SID = os.environ["WPS_SID"]
WPS_SID_TEST = os.environ["WPS_TEST_SID"]
import urllib3

# 禁用 InsecureRequestWarning 警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
import sseclient
def get_test_url(url):
    return url.replace("copilot.wps.cn", "120.92.124.158")
def get_headers(is_test,model_url):
    wps_sid = WPS_SID_TEST if is_test else WPS_SID
    headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:126.0) Gecko/20100101 Firefox/126.0',
    'Accept': '*/*',
    'Accept-Language': 'zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2',
    'Accept-Encoding': 'gzip, deflate, br, zstd',
    'Referer': 'https://copilot.wps.cn/',
    'Origin': 'https://copilot.wps.cn',
    'Connection': 'keep-alive',
    'Cookie': f'wps_sid={wps_sid};wps_sid_prod={wps_sid};debug_api=1' if is_test else f'wps_sid={wps_sid}',
    'Sec-Fetch-Dest': 'empty',
    'Sec-Fetch-Mode': 'cors',
    'Sec-Fetch-Site': 'same-site',
    'Priority': 'u=1',
    # 'Content-Length': '0',
    # 'x-cc-branch':'wgr'
    }
    if is_test:
        headers['Host'] = 'copilot.wps.cn'
    if model_url:
        headers['Cookie'] = headers['Cookie'] + f";model_url={model_url}"
    # print(111,headers)
    return headers

def create_session(is_test=False,model_url=""):
    url = "https://copilot.wps.cn/api/aigc/v3/assistant/sessions"
    if is_test:
        url = get_test_url(url)
    response = requests.post(url, headers=get_headers(is_test,model_url),verify=False)
    return response.json()["data"]['session_id']
def question(session_id, question,is_test=False,model_url=""):
    url = f'https://copilot.wps.cn/api/aigc/v3/assistant/sessions/{session_id}/completions'
    if is_test:
        url = get_test_url(url)
    data = {"question": question}
    
    try:
        response = requests.post(url, headers=get_headers(is_test,model_url), json=data,verify=False)
        response.raise_for_status()
        response.encoding = 'utf-8'
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
    

def history(session_id,is_test=False,model_url=""):
    url = f'https://copilot.wps.cn/api/aigc/v3/assistant/sessions/{session_id}/messages'
    if is_test:
        url = get_test_url(url)
    return requests.get(url, headers=get_headers(is_test,model_url),verify=False).json()
    

def questions(questions,is_test=False,model_url=""):
    session_id = create_session(is_test,model_url)
    for q in questions:
        r = question(session_id,q,is_test,model_url)
    return history(session_id,is_test,model_url)
if __name__ == '__main__':
    r = questions(["根据红楼梦，创建PPT大纲"],is_test=True,model_url="http://10.8.254.24:30818/kas/rozsxlc6k5p-ay7kqtbtx7sfcolq/api/chat/completions?model=0724_fp_v1")
    print(r)