import re
r1 = r"[a-zA-Z\u4e00-\u9fff]"
r2 = r"[a-zA-Z\u4e00-\u9fff\u3400-\u4dbf\u20000-\u2a6df]"
ccc = re.compile(r1).match("㐭")
print(ccc)
ccc = re.compile(r2).match("㐭")
print(ccc)

import re
import unicodedata
import emoji

def check_langs(text: str) -> bool:
    """约束只能中英文字符及emoji和空白符

    :param text: 用户输入
    :return: False 表示非法输入
    """
    # 使用正则表达式匹配所有的中文、英文和空格字符
    non_emoji_text = re.sub(r'[a-zA-Z\u4e00-\u9fff\u3400-\u4dbf\u20000-\u2a6df\s]', '', text)
    
    # 剩下的内容如果全是emoji或为空，表示合法
    if all(emoji.is_emoji(char) for char in non_emoji_text):
        return True

    return False

def check_langs(text: str):
    """约束只能中英文字符

    :param text: 用户输入
    :return: False 表示非法输入
    """
    # 正则表达式匹配英文和中文字符
    allowed_pattern = re.compile(r"[a-zA-Z\u4e00-\u9fff\u3400-\u4dbf\u20000-\u2a6df]")

    for char in text:
        char_category = unicodedata.category(char)
        # 检查字符是否为标点、数字、标记、分隔符、英文、中文或emoji
        if not (
            not char_category.startswith("L")
            or allowed_pattern.match(char)
            or emoji.is_emoji(char)
            or char.isspace()
        ):  # 允许空白字符
            return False
    return True
c = check_langs("勉強")
print(c)
from langdetect import detect, DetectorFactory

# Optional: Set seed to make results reproducible
DetectorFactory.seed = 0

# Example: Detect language of a string
text = "愛人is ok"
language = detect(text)
print(f"The detected language is: {language}")

