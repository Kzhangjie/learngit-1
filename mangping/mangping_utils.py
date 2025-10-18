def r2qs(r):
    qs = r["问题"].split("ask:")
    qs = [q.strip() for q in qs if q.strip()]
    return qs


import json


def r2qcs(r):
    qcrs = r["其他参数"].split("ask:")
    if not qcrs:
        return True, []
    qcs = []
    error = ""
    for qc in qcrs:
        qc_stripped = qc.strip()
        if qc_stripped:
            try:
                # 支持Python风格的布尔值，转换为JSON格式
                qc_normalized = qc_stripped.replace("True", "true").replace(
                    "False", "false"
                )
                # 保持JSON格式，只去除前后空白
                # print(f"正在解析JSON: {qc_normalized[:100]}...")  # 只显示前100个字符用于调试
                parsed_json = json.loads(qc_normalized)
                qcs.append(parsed_json)
            except json.JSONDecodeError as e:
                print(f"JSON解析失败: {e}")
                print(f"问题字符串: {qc_stripped}")
                return False, f"JSON解析失败，请检查输入数据。{qc_stripped}"
    return True, qcs


def r2q(r):
    return r["问题"].strip("ask:").strip()


import time


def chat_retry(msg, func, count=10):
    for attempt in range(1, count + 1):
        try:
            return func(msg)
        except Exception as e:
            print(f"第 {attempt} 次重试失败，错误信息: {e}")
            time.sleep(3)
    raise RuntimeError("已超过最大重试次数")


if __name__ == "__main__":
    # 测试 r2qcs 函数 - JSON格式 (小写true)
    qcs1 = """{
    "reasoning": true,
    "thinking": "auto",
    "context": {
        "enable_canvas_mode": true,
        "agent": "WPP",
        "file_code": "001004000"
    }
}"""
    r1 = {"其他参数": qcs1}
    print("JSON格式测试:", r2qcs(r1))

    # 测试 r2qcs 函数 - Python格式 (大写True)
    qcs2 = """{
    "reasoning": True,
    "thinking": "auto",
    "context": {
        "enable_canvas_mode": True,
        "agent": "WPP",
        "file_code": "001004000"
    }
}"""
    r2 = {"其他参数": qcs2}
    print("Python格式测试:", r2qcs(r2))
