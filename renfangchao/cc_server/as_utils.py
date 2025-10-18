import json


def split_string(text, length=30000, max_size=10, with_start=True):
    result = [text[i : i + length] for i in range(0, len(text), length)]
    if with_start:
        result = ["'" + part for part in result]
    return result[:max_size]


def obj_to_strs(obj, length=30000, indent=2, with_start=True, max_size=10):
    text = json.dumps(obj, ensure_ascii=False, indent=indent)
    return split_string(text, length, with_start=with_start)


def get_long_text(row, name, num=10):
    datas = []
    for i in range(num):
        key = f"{name}{i+1}"
        if key in row:
            content = row[key]
            if content.startswith("'"):
                content = content[1:]
            datas.append(content)
    return "".join(datas)
