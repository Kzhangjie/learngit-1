提问 = """# 指令

您是一位专家评估员。您的任务是评估由AI智能助手生成的响应的质量。我们将为您提供用户与AI智能助手之间的对话，以及一个详细的checklist，其中包含了对每个问题答案的具体要求。

# AI智能助手的任务

AI智能助手是一个通过与用户进行文本对话来提供帮助的程序，它可以使用 websearch（进行网络搜索并总结）、url_fetch(获取指定的URL内容)、upload_files（读取用户消息中一个或多个格式为"[文件名](wps365://files/文件id)"的文档链接的内容）、create_file（创建word或PPT文件,不支持创建多个,多个文件的创建需要合并到一份文件里面）和chat（与大型语言模型进行对话）这5个function来回答用户的问题。


通常情况下，AI智能助手应该根据用户意图和对话上文合理地选择调用一个或多个function中生成回答；
少数情况下，AI助手可以不借助任何function直接回答用户的问题；
当用户要求超出AI智能助手能力时，应该直接拒绝。

## 在以下情况下使用websearch：
    1. 用户询问有关当前事件或需要实时信息的内容（包括但不限于天气、体育比分等）
    2. 用户询问一个AI智能助手的任务完全不熟悉的术语（这可能是新的）
    3. 用户明确要求搜索
## 在以下情况下使用url_fetch：
    1. 用户想让AI智能助手访问一个链接
## 在以下情况下使用upload_files:
    1. 当用户消息包含一个或多个格式为"[文件名](wps365://files/文件id)"的文档链接时
## 在以下情况下使用create_file：
    1. 当用户明确需要生成文件或保存文件时,只支持创建word文件(type为"document")和PPT文件(type为"slides")
## 在以下不使用任何function: 
    1. 当用户只是当招呼或询问AI智能助手的功能时，应该不使用任何function,直接回答。
    2. 当用户要求超出AI智能助手能力时，应该不使用任何function,直接拒绝。例如：用户想让AI智能助手访问一个链接。
    3. 非常简单的上下文中，且用户问题过于简单，且无明确意义，3个条件同时满足可以不使用任何function,直接回答。
## 以上情况之外,使用chat

# 用户与人工智能之间的对话
{^conversation^}

# 评估   

## checklist 

<|begin_of_checklist|>

{^checklist^}

<|end_of_checklist|>

请使用此checklist指导您的评估，确保对每个问题答案的具体要求进行逐一检查，但不要将您的评估限制在checklist上。

## 规则 

您应该根据checklist中的每项要求，逐一评估人工智能的响应是否满足这些要求，并给出每项要求的评估结果。

## 输出格式 
首先，请输出您对模型响应的分析，然后总结您的评估；最后，请写下您对评估的评分。

请严格按照以下json格式填写占位符以提供您的评估结果：
```json
{
  "checklist结果": [
    {
      "要求描述": "[描述要求1]",
      "是否通过": "[是/否]",
      "理由": "[具体理由1]"
    },
    {
      "要求描述": "[描述要求2]",
      "是否通过": "[是/否]",
      "理由": "[具体理由2]"
    }
    // ... 其他要求
  ],
  "其他分析": "[其他分析内容]",
  "其他明显缺陷": "[如果有其他明显缺陷请描述，否则填写'无']",
  "总体是否通过": "[所有chekclist都通过且无明显缺陷填'是'，否则填'否']"
}
```"""

def parse_checklist(raw_string):
    # Define a regex pattern to match different types of colons
    colon_pattern = r'[::：∶﹕︓︔]'
    # Split the raw string into lines and remove empty lines
    lines = [line for line in raw_string.strip().split('\n') if line]

    result = {}
    ans_no_items = {}

    for line in lines:
        # print(f"Processing line: {line}")
        # Update the regex to include different types of colons
        match = re.match(rf'^(\d+)(.*?答案{colon_pattern})(.*)', line)
        if match:
            # New question detected
            ans_no = int(match.group(1))
            item_type = match.group(2).strip()
            item_text = match.group(3).strip()
            # print(f"Found new item: ans_no={ans_no}, item_type={item_type}, item_text={item_text}")

            current_item = {
                'type': item_type[:-1],
                'text': item_text,
                'ans_no': ans_no
            }
            if ans_no not in ans_no_items:
                ans_no_items[ans_no] = []
            ans_no_items[ans_no].append(current_item)
            # print(f"Added item: {current_item}")
        else:
            # Line does not match expected pattern
            print(f"No match found for line: {line}")

    # Convert the dictionary to a dictionary and sort by ans_no
    for ans_no in sorted(ans_no_items):
        result[ans_no] = ans_no_items[ans_no]
        # print(f"Added items for ans_no={ans_no} to result")

    return result

def parse_search(text):
    text = text.strip()
    ts = text.split("\n")
    ts = [t.strip() for t in ts]
    ts = [t for t in ts if t]
    return ts

def gen_template(questions,checklistes,searchs,saves,url_fetchs,question_type,is_test):
    lines = []
    for index,q in enumerate(questions):
        checklist = checklistes.get(index+1,[])
        for check in checklist:
            text = check["text"].strip()
            if text and text != "无":
                at = f"回答{check['ans_no']}的text应与{check['type']}一致。{check['type']}为：{check['text']}"
                lines.append(at)
        s = searchs[index] if index < len(searchs) else "不要求"
        if s == "是":
            st1 = f"有一个回答{index+1}的code使用websearch function,该function每个参数的取值符合用户意图和对话上文。"
            lines.append(st1)
        s = saves[index] if index < len(saves) else "不要求"
        if s == "是":
            st = f"有一个回答{index+1}的code使用create_file function,该function每个参数的取值符合用户意图和对话上文。"
            lines.append(st)
        s = url_fetchs[index] if index < len(url_fetchs) else "不要求"
        if s == "是":
            st = f"有一个回答{index+1}的code使用url_fetch function,该function每个参数的取值符合用户意图和对话上文。"
            lines.append(st)
        # 这里用代码判断，减少GPT-4的负担
        # elif s == "否":
        #     st = f"回答{index+1}的extraInfo不应使用websearch function。"
        #     lines.append(st)
    others = ["所有回答都正确理解了用户意图","所有回答都是有用的，准确的，清晰的，完整的，有逻辑的。","所有回答都不含有明显错误","所有回答都不包含任何不相关的信息。"]
    lines.extend(others)
    formatted_list = [f"{index + 1}. {element}" for index, element in enumerate(lines)]
    return "\n".join(formatted_list)
def parse_question(text:str):
    if not text:
        return []
    qs = text.split("ask:")
    qs = [q.strip() for q in qs if q]
    return qs
   
def gen_checklist(row,is_test):
    questions = parse_question(row["问题"])
    checklistes = parse_checklist(row["checklist"])
    # print(111,answers)
    searchs = parse_search(row.get("是否需要websearch",""))
    saves = parse_search(row.get("是否需要创建文件",""))
    url_fetchs = parse_search(row.get("是否需要url_fetch",""))
    question_type = row["问题类型"]
    return gen_template(questions=questions,checklistes=checklistes,searchs=searchs,saves=saves,url_fetchs=url_fetchs,question_type=question_type,is_test=is_test)

def gen_question_answer_pairs(messages):
    question_answer_pairs = []
    qap = {}
    for message in messages['data']['list']:
        if message.get("role") is None:
            continue
        # print(333,message)     
        if message['role'] == 'user':
            if qap:
                question_answer_pairs.append(qap)
            qap ={}
            qap["q"] = message
            qap["a"] = []
            
        else:
            qap["a"].append(message)
    if qap:
        question_answer_pairs.append(qap)
    return question_answer_pairs
    

def convert_messages_for_gpt(messages):
    all_text = []
    question_answer_pairs = gen_question_answer_pairs(messages)
    # print(444,question_answer_pairs)
    for i,qap in enumerate(question_answer_pairs):
        texts = []
        q = qap["q"]
        aa = qap["a"]
        index = i+1
        texts.append(f"## 问题{index}\n{q}\n\n## 回答{index}")
        for a in aa:
            texts.append(f"### 回答{index}的{a['type']}\n\n{a}\n")
        texts.append("---------------------------")
        all_text.extend(texts)
    return "\n".join(all_text)

def extra_codes(messages):
    all_codes = {}
    question_answer_pairs = gen_question_answer_pairs(messages)
    # print(444,question_answer_pairs)
    for i,qap in enumerate(question_answer_pairs):
        codes = []
        q = qap["q"]
        aa = qap["a"]
        for a in aa:
            if  a["type"] == "code":
                codes.append(a["content"])
        index = i+1
        all_codes[index] = codes
    return json.dumps(all_codes,ensure_ascii=False,indent=4)

def extra_codes_from_log(sse_data):
    # 将字符串分割成单独的事件
    events = sse_data.split("\n\nevent:")

    # 遍历事件并提取type为code的数据
    code_events = []

    for event in events:
        if "data:" in event:
            data_part = event.split("data:")[1].strip()
            try:
                data_json = json.loads(data_part)
                if data_json.get("type") == "code":
                    try: 
                        code_json = json.loads(data_json.get("data"))
                        if code_json.get("function") == "stop":
                            pass
                        else:
                            code_events.append(data_json.get("data"))
                    except json.JSONDecodeError:
                        continue
            except json.JSONDecodeError:
                continue
    return code_events

def extra_codes_from_logs(logs):
    all_codes = {}
    for i,log in enumerate(logs):
        print(111,log)
        codes = ["error"]
        try:
            codes = extra_codes_from_log(log)
        except Exception as e:
            pass
        index = i+1
        all_codes[index] = codes
    return json.dumps(all_codes,ensure_ascii=False,indent=4)


def gen_prompt(row,is_test=False):
    p = 提问
    checklist = gen_checklist(row,is_test)
    p = p.replace("{^conversation^}", row["WPS答案可视化"]).replace("{^checklist^}", checklist)
    return p
import re
def extract_answer(text):
    pattern = r'"总体是否通过":\s*"([^"]*)"'
    match = re.search(pattern, text)
    if match:
        return match.group(1)
    else:
        return ""
    
def all_pass(datas):
    for data in datas:
        if data["是否通过"] != "是":
            return False
    return True
import json
def extract_answer_full(text):
    json_str = extract_json(text)
    result = json.loads(json_str)
    总体是否通过 = result["总体是否通过"]
    其他明显缺陷 = result["其他明显缺陷"]
    checklist结果 = result["checklist结果"]
    humans = checklist结果[:-4]
    commons = checklist结果[-4:]
    # print(111,commons)
    
    commons_pass = ['是' if c['是否通过'] == '是' else c['理由'] for c in commons]
    search = [s for s in humans if "websearch" in s["要求描述"]]
    search_pass = all_pass(search)
    ans = [s for s in humans if "websearch" not in s["要求描述"]]
    ans_pass = all_pass(ans)
    return [总体是否通过,search_pass,ans_pass,commons_pass[0],commons_pass[1],commons_pass[2],commons_pass[3],其他明显缺陷]
def extract_json(text):
    pattern = r'\{.*\}'
    match = re.search(pattern, text)
    if match:
        return match.group(0)
    else:
        return ""

模型 = "gpt-4"
模型参数 ={
    "temperature":0.0
}
if __name__ == "__main__":
    text = """"event:execution\ndata:{\"type\": \"user\", \"message_id\": \"524670410768271065\"}\n\nevent:aigc\ndata:{\"type\": \"code\", \"message_id\": \"524670412563433177\", \"delta\": \"{\\\"function\\\": \\\"url_fetch\\\", \\\"urls\\\": [\\\"https://mp.weixin.qq.com/s/Iwho8Q54m6BlCgWjMHYYzA\\\"]}\", \"group_id\": \"\"}\n\nevent:execution\ndata:{\"type\": \"url_fetch_start\", \"message_id\": \"524670412563498713\"}\n\nevent:execution\ndata:{\"type\": \"url_fetch\", \"data\": {\"url\": \"https://mp.weixin.qq.com/s/Iwho8Q54m6BlCgWjMHYYzA\", \"value\": {\"title\": \"体验完 Kimi 今天推出的浏览器插件，它可能会是打工人新的「摸鱼」神器\", \"content\": \"原创\\n                                                      \\n                                      莫崇宇\\n                                  \\n                                      \\n                        \\n              \\n                APPSO              \\n              \\n              \\n            \\n            \\n            \\n              \\n              \\n              \\n                          \\n                      \\n                        \\n                \\n        \\n\\n        \\n        \\n\\n\\n                \\n              \\n\\n    \\n\\n    \\n    \\n\\n    \\n    \\n  \\n  \\n  \\n\\n\\n  \\n  继续滑动看下一个\\n  \\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n  \\n  \\n        \\n                  \\n                                          \\n                                        \\n                  \\n                  \\n                      \\n                        APPSO                      \\n                    \\n                \\n    \\n        \\n      \\n  \\n      \\n        向上滑动看下一个\"}}, \"message_id\": \"524670412563498713\"}\n\nevent:execution\ndata:{\"type\": \"url_fetch_end\", \"message_id\": \"524670412563498713\"}\n\nevent:execution\ndata:{\"type\": \"text_start\", \"message_id\": \"524670412563498713\"}\n\nevent:execution\ndata:{\"type\": \"text\", \"data\": \"很\", \"message_id\": \"524670412563498713\"}\n\nevent:execution\ndata:{\"type\": \"text\", \"data\": \"抱歉，我无法直接提供下载地址和安装流程，因为我无法访问外部链接或执行网络搜索。不过，通常情况下，如果您想下载和安装微信公众号中提到的浏览器插件，您可以按照以下步骤操作：\\n\\n1. 打开微信公众号文章链接，找到文章中\", \"message_id\": \"524670412563498713\"}\n\nevent:execution\ndata:{\"type\": \"text\", \"data\": \"提到的插件信息。\\n2. 查看文章中是否有提供插件的下载链接或者安装说明。\\n3. 如果文章中提供了下载链接，点击链接通常会跳转到插件的官方网站或者下载页面。\\n4. 在下载页面上，根据提示选择适合您浏览器的插\", \"message_id\": \"524670412563498713\"}\n\nevent:execution\ndata:{\"type\": \"text\", \"data\": \"件版本进行下载。\\n5. 下载完成后，通常会有一个安装文件（如`.crx`文件），您需要在浏览器中打开该文件来安装插件。\\n6. 在浏览器的插件管理页面中，找到已下载的插件文件，点击安装。\\n7.\", \"message_id\": \"524670412563498713\"}\n\nevent:execution\ndata:{\"type\": \"text\", \"data\": \" 安装完成后，您可能需要重启浏览器或者重新启动插件，以确保插件正常工作。\\n\\n请注意，下载和安装插件时，确保来源可靠，避免下载可能含有恶意软件的插件。如果您在安装过程中遇到任何问题，建议查看浏览器的帮助文档或者联系插件的开发者获取\", \"message_id\": \"524670412563498713\"}\n\nevent:execution\ndata:{\"type\": \"text\", \"data\": \"帮助。\", \"message_id\": \"524670412563498713\"}\n\nevent:execution\ndata:{\"type\": \"text_end\", \"message_id\": \"524670412563498713\"}\n\nevent:aigc\ndata:{\"type\": \"end\", \"message_id\": \"524670412563433177\", \"delta\": \"\", \"group_id\": \"524670410701162201\"}\n\nevent:execution\ndata:{\"type\": \"recommend_start\", \"message_id\": \"524670421673527001\"}\n\nevent:execution\ndata:{\"type\": \"recommend\", \"data\": \"[]\", \"message_id\": \"524670421673527001\"}\n\nevent:execution\ndata:{\"type\": \"recommend_end\", \"data\": \"524670421673527001\"}\n\nevent:execution\ndata:{\"type\": \"finish\"}\n\n"""
    
    code =extra_codes_from_log(text)
    print(code)