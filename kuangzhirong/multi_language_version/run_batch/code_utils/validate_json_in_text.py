import json
from genson import SchemaBuilder
from jsonschema import validate
from jsonschema.exceptions import ValidationError
import re

# 自动生成schema的方法
def generate_schema_from_example(json_example):
    builder = SchemaBuilder()
    builder.add_object(json_example)
    return builder.to_schema()

# 校验方法，返回元组
def validate_json(json_str, schema):
    try:
        json_data = json.loads(json_str)
        validate(instance=json_data, schema=schema)
        return [True, ""]
    except ValidationError as e:
        return [False, str(e)]
    except json.JSONDecodeError as e:
        return [False, "无效的JSON字符串: " + str(e)]

def extract_json_from_text(text):
    json_str_match = re.search(r"```json\s+(.+?)\s*```", text, re.DOTALL)
    if json_str_match:
        return json_str_match.group(1)
    else:
        return "{}"

def func(text, json_example):
    json_str = extract_json_from_text(text)
    schema = generate_schema_from_example(json_example)
    return validate_json(json_str, schema)

if __name__ == "__main__":
    # 示例JSON
    json_example = {
        "annex": [
            {
                "highlightSentence": "示例句子",
                "reasons": "示例原因"
            }
        ]
    }

    # 使用示例
    text = "这里是一段包含JSON的文本 ```json {\"annex\": [{\"highlightSentence\": \"示例句子\", \"reasons\": \"示例原因\"}]} ```"
    result = func(text, json_example)
    print(result)
