import requests
import json
import time
from utils.retry_none import retry_if_empty
from utils import getLogger
import os

logger = getLogger(os.path.splitext(os.path.basename(__file__))[0])


# @retry_if_empty
def chat(msgs):
    url = "https://ark.cn-beijing.volces.com/api/v3/chat/completions"
    key = "1ca8b973-f6d6-4c92-8471-8f7d8193d380"

    # 准备请求头
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer " + key,
    }

    # 准备请求体
    data = {
        "model": "doubao-1-5-thinking-pro-250415",
        "messages": msgs,
        "temperature": 0.6,
    }
    response = requests.post(url, headers=headers, json=data, stream=True)
    # print(111, response.text)
    logger.info(f"request payload : {msgs},response: {response.text} ")
    rj = response.json()
    return (
        True,
        rj["choices"][0]["message"]["content"],
        {
            "reasoning_content": rj["choices"][0]["message"]["reasoning_content"],
            "content": rj["choices"][0]["message"]["content"],
            "id": rj["id"],
        },
    )


def chat_text(prompt, context):
    return chat(
        [
            {
                "role": "system",
                "content": context,
            },
            {
                "role": "user",
                "content": prompt,
            },
        ]
    )


if __name__ == "__main__":
    content = """写2000字介绍鲁迅"""
    for i in range(10):
        print(think([{"role": "user", "content": content}]))
