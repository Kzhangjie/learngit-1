import requests
import sseclient

body = {
    "model": "copilot365",
    "stop": ["<|endofblock|>", "<|endofmessage|>"],
    # "logprobs": True,
    # "top_logprobs": 6,
    "max_new_tokens": 4096,
    "temperature": 0.01,
    "messages": [
        # {"role": "system", "type": "text", "content": ""},
        {
            "role": "user",
            "type": "text",
            "content": "!a",
        },
    ],
    "stream": False,
}

test_url = "http://120.92.122.107:30818/kas/ybsjuqhgzi9-qkatvhtcdydnav5x/api/chat/completions?model=latest"
gray_url = (
    "http://kmd-api.kas.wps.cn/api/11129-v3/MbSvPI/api/chat/completions?model=canvas"
)
is_test = False
url = test_url if is_test else gray_url
resp = requests.post(url, json=body)
import json

print(resp.text)
# print(resp.json())

# stream = sseclient.SSEClient(resp)
# ts = []
# for event in stream.events():
#     if event.data == "[DONE]":
#         continue
#     print(event.data)
#     data = json.loads(event.data)
#     # print(111,data["data"]["choices"][0]["delta"])
#     ts.append(data["data"]["choices"][0]["delta"])

# print("".join(ts))

# 0.01
"""data:{"data":{"id":"yXwMcNt6nQ3sebna7rhzHS","object":"chat.completion.chunk","created":1726190288,"model":"copilot365","choices":[{"index":0,"role":"assistant","type":"code","delta":"help","logprobs":{"content":[{"token":"help","bytes":[104,101,108,112],"logprob":0.0,"top_logprobs":[]}]},"finish_reason":null}]},"status":{"code":0,"message":"ok"}}"""

# 1
"""data:{"data":{"id":"h3r4UpLEERprsjxLed2JcK","object":"chat.completion.chunk","created":1726190314,"model":"copilot365","choices":[{"index":0,"role":"assistant","type":"code","delta":"help","logprobs":{"content":[{"token":"help","bytes":[104,101,108,112],"logprob":-0.012634309008717537,"top_logprobs":[{"token":"chat","bytes":[99,104,97,116],"logprob":-4.409545421600342},{"token":"generate","bytes":[103,101,110,101,114,97,116,101],"logprob":-7.933357238769531}]}]},"finish_reason":null}]},"status":{"code":0,"message":"ok"}}"""
