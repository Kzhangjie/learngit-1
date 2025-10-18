import requests
import json
import time
from utils.retry_none import retry_if_empty
from utils import getLogger
import os

logger = getLogger(os.path.splitext(os.path.basename(__file__))[0])


# @retry_if_empty
def chat(msgs):
    url = "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions"
    key = "sk-63088a95d90746f194f5effc2314608d"

    # 准备请求头
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer " + key,
    }

    # 准备请求体
    data = {
        "model": "qwen3-235b-a22b",
        "messages": msgs,
        "stream": True,
        "temperature": 0.6,
    }
    response = requests.post(url, headers=headers, json=data, stream=True)
    # print(111, response.text)
    logger.info(f"request payload : {msgs},response: {response.text} ")
    content = ""
    reasoning_content = ""
    id = ""
    if "text/event-stream" in response.headers.get("content-type"):  # type: ignore
        for chunk in response.iter_lines():
            if chunk:
                chunkStr = chunk.decode("utf-8")[6:]
                if chunkStr == "[DONE]":
                    break
                jo = json.loads(chunkStr)
                if not id:
                    id = jo["id"]
                delta = jo["choices"][0]["delta"]
                if "content" in delta and delta["content"]:
                    content += delta["content"]
                if "reasoning_content" in delta and delta["reasoning_content"]:
                    reasoning_content += delta["reasoning_content"]
        return (
            True,
            content,
            {"reasoning_content": reasoning_content, "content": content, "id": id},
        )
    else:
        return False, response.text, {"reasoning_content": "", "content": "", "id": ""}


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
    content = """介绍鲁迅"""
    for i in range(1):
        print(chat([{"role": "user", "content": content}]))
