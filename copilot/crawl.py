import hashlib
import json
from email.utils import formatdate
from urllib.parse import urlparse

import requests


def wps2_sign(req: requests.Request, ak, sk):
    """
    用法：
    req = requests.Request('get', url=url)
    req = requests.Request('put', url=url, data=data)
    req = requests.Request('put', url=url, json=object)
    req = wps2_sign(req, ak, sk)
    requests.session().send(req)
    """
    if not isinstance(req, requests.Request):
        raise TypeError(str(type(req)) + " not requests.Request")

    if req.method == "get":
        uri = urlparse(req.url)
        path_with_query = uri.path + (f"?{uri.query}" if uri.query else "")
        md5 = hashlib.md5(path_with_query.encode()).hexdigest()
    else:
        data = req.data
        if not data and req.json is not None:
            data = json.dumps(data)
        md5 = hashlib.md5(data.encode()).hexdigest()

    date = formatdate(timeval=None, localtime=False, usegmt=True)
    ct = "application/json"
    authorization = (
        f"WPS-2:{ak}:" + hashlib.sha1((sk + md5 + ct + date).encode()).hexdigest()
    )
    headers = {
        "Content-Type": ct,
        "Date": date,
        "Authorization": authorization,
        "Content-Md5": md5,
    }

    prepare = req.prepare()
    prepare.headers.update(headers)
    return prepare

def url_fetch(url1):
    ak = "AK20240507GVUGZP"
    sk = "7fdafb2d5afb062163be0504d1e93cc2"
    url = "http://120.92.124.158/office/v5/dev/ai/crawler/crawl"
    body = {
        "url": url1,
        "request": "smart",
        "return_format": "plain",
        "readability": True,
    }
    headers = {
        "Host": "aibot-api.wps.cn",
        "Content-Type": "application/json",
    }
    print (body)
    req = requests.Request("post", url=url, data=json.dumps(body), headers=headers)
    req = wps2_sign(req, ak, sk)
    print (req)
    resp = requests.session().send(req)
    print (resp)
    
    # print(resp.text)
    return resp.text

if __name__ == '__main__':
    url_content = url_fetch("https://mp.weixin.qq.com/s/Iwho8Q54m6BlCgWjMHYYzA")
    print (url_content)
    
