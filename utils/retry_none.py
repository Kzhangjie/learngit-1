from functools import wraps
import time

def retry_if_empty(max_attempts=3, delay_seconds=1):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            attempts = 0
            while attempts < max_attempts:
                result = func(*args, **kwargs)
                if result is not None and result != "":
                    return result
                attempts += 1
                time.sleep(delay_seconds)
                print(f"Attempt {attempts}: Retrying...")
            return ""
        return wrapper
    return decorator

# @retry_if_empty(max_attempts=5, delay_seconds=2)
# def test_function():
#     # 这里可以模拟返回None或空字符串来测试装饰器
#     # 返回None或""以测试重试机制
#     return ""

# # 调用函数
# result = test_function()
# print("Final result:", result) 