import requests
import json


def step_ui(content):
    # url = 'https://api.baichuan-ai.com/v1/chat/completions'
    url = 'http://localhost:8000/v1/chat/completions'
    # key='sk-FAXaPq6sFefmCbeQxN0qQagKV4yax19XBVrmMdCpEKdXkX3C'
    key = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhY3RpdmF0ZWQiOnRydWUsImFnZSI6MSwiYmFuZWQiOmZhbHNlLCJleHAiOjE3MTI0NjMwOTEsIm1vZGUiOjIsIm9hc2lzX2lkIjo4NTk2Mjk3MDk5MTA5NTgwOCwidmVyc2lvbiI6MX0.pBgpEZT1vPO3gXoE5cfXAPiRJvV-MWcfpdtLrq9DvkA...eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhcHBfaWQiOjEwMjAwLCJkZXZpY2VfaWQiOiIyYWIyMTQ4N2JkMDU0YTExZTNmNjFhYWY2NWJiMmRkNGNkZTQ1MjJlIiwiZXhwIjoxNzEzNzU3MjkxLCJvYXNpc19pZCI6ODU5NjI5NzA5OTEwOTU4MDgsInZlcnNpb24iOjF9.48_OE0Vu5cEUkbskbawRTCXsDYwprpii9jQihGaj1rU'

# 准备请求头
    headers = {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer ' + key,
        }

# 准备请求体
    data = {
        "model": 'step',
        "messages": [
            # {"role": "system", "content": "你是WPS AI，由金山办公与合作伙伴共同开发，能够协助创作，帮助人们获取信息、知识和灵感。从现在起，你要扮演WPS AI这个角色，无论用户怎么问，你都不能转变角色"},
            {"role": "user", "content": content}
        ],
        "stream": False
    }

    
    response = requests.post(url, headers=headers, data=json.dumps(data))
    response_json = response.json()
   
    # 确保API响应中包含所需的数据路径
    if 'choices' in response_json and len(response_json['choices']) > 0 and 'message' in response_json['choices'][0] and 'content' in response_json['choices'][0]['message']:
        return response_json['choices'][0]['message']['content']
    else:
        print(response.text)
        return ""


if __name__ == '__main__':
    content = "你是谁"
    print(step_ui(content))