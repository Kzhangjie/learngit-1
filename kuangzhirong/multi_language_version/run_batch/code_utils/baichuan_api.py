import requests
import json

def baichuan(model, content):
    url = 'https://api.baichuan-ai.com/v1/chat/completions'
    api_key='sk-a784866e25f55e31b66b92042a482029'
    
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {api_key}'  # 使用f-string插入api_key
    }
    
    data = {
        "model": model,
        "messages": [
            { "role": "user", "content": content }
        ],
        # "temperature": 0.3,
        "stream": False
    }
    
    response = requests.post(url, headers=headers, data=json.dumps(data))
    response_json = response.json()
    
    # 确保API响应中包含所需的数据路径
    if 'choices' in response_json and len(response_json['choices']) > 0 and 'message' in response_json['choices'][0] and 'content' in response_json['choices'][0]['message']:
        return response_json['choices'][0]['message']['content']
    else:
        return "无法获取有效响应或响应格式不符预期。"


if __name__ == '__main__':
    model = 'Baichuan2-Turbo'
    content = "你好"
    print(baichuan(model, content))