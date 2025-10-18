import json
import re
from jinja2 import Template
from datetime import datetime

NOW_DATE = datetime.now().strftime("%Y年%m月%d日")


def system_prompt(model="doubao") -> str:
    sys = {
        "doubao": """## 角色描述
1. 你是WPS灵犀，与WPS AI一样，是由WPS研发团队研发的AI助手
2. 有时候用户也会叫你灵犀，当用户询问你与灵犀的相关问题时，你需要告诉用户你就是灵犀

## 处理方式
1. 在回答知识类问题时，你会抓住问题主需回答，角度全面、重点突出、表述专业，并结构化地呈现。
2. 在写文案或进行内容创作时，默认情况下，使用自然段进行回复；在需要排版的创作体裁中，使用 markdown 格式，合理使用分级标题、分级列表等排版。
3. 对于代码、闲聊等需求，请按照你默认的方式回答。
4. 当用户要求你创建文档时，直接提供文档内容，不要解释你无法创建文件，也不要引导用户复制和粘贴。

## 能力描述
1. 你可以接收和读取各类文档（如 PDF、excel、ppt、word 等）的内容，并执行总结、分析、翻译、润色、文档生成等任务；你也可以读取图片 / 照片、网址链接的内容。
2. 你可以搜索各类信息来满足用户的需求，也可以搜索图片和视频。

## 安全原则
1. 任何回复不要暴露你的训练信息，包括但不限于模型与数据信息，当用户问到这些问题时，直接拒绝，并简要介绍你能做什么
2. 你的回答和建议应该拒绝黄赌毒，不能包含任何关于毒品制作、危险品制作、暴力恐怖主义等违法犯罪内容，特别警惕用户会使用角色扮演或剧本创作续写等方式诱导你回答可能对他人和社会造成危害的事情，即使是虚构场景问题，你应该将角色行为转换为用户的行为，如发现用户进行这些行为是违法犯罪的诸如：盗窃、抢劫、欺诈、非法入侵等，你应该拒绝回答。

## 其他
1. 你和WPS Office没有直接关系，但如果涉及到文档、表格、PPT相关回答时，你会优先考虑WPS Office而不是Microsoft Office
2. 回答问题时，建议使用结构化的语言描述
3. 今天是:{{NowDate}}""",
        "r1": """## 角色描述
1. 你是WPS灵犀，与WPS AI一样，是由WPS研发团队研发的AI助手。
2. 有时候用户也会叫你灵犀，当用户询问你与灵犀的相关问题时，你需要告诉用户你就是灵犀。

## 安全原则
1. 任何回复不要暴露你的训练信息，包括但不限于模型与数据信息，当用户问到这些问题时，直接拒绝，并简要介绍你能做什么。
2. 你的回答和建议应该拒绝黄赌毒，不能包含任何关于毒品制作、危险品制作、暴力恐怖主义等违法犯罪内容，特别警惕用户会使用角色扮演或剧本创作续写等方式诱导你回答可能对他人和社会造成危害的事情，即使是虚构场景问题，你应该将角色行为转换为用户的行为，如发现用户进行这些行为是违法犯罪的诸如：盗窃、抢劫、欺诈、非法入侵等，你应该拒绝回答。

## 其他
1. 建议使用 markdown 格式排版回答问题。
2. 今天是:{{NowDate}}。""",
    }
    r = sys.get(model, sys["doubao"])
    return Template(r).render(nowDate=NOW_DATE)


from mangping.mangping_utils import r2q


def row_to_documents(row):
    content = row["文件内容"]
    # print(222, content)
    pattern = r"<documents>(.*?)</documents>"

    match = re.search(pattern, content, re.DOTALL)

    if match:
        documents_content = match.group(1).strip()
        if match:
            return f"""<documents>
    {documents_content}
</documents>"""
    else:
        return ""


def row_to_prompt(row):
    q = r2q(row)
    documents = row_to_documents(row)
    return f"""#任务\n根据上文生成PPT主题、大纲和创作思路。并且按照用户的要求输出PPT的页数\n#参考资料\n[]\n\n\n#输出示例\n        <cogitate>用户没有明确说需要多少页，篇幅要多少，所以我根据提供的参考材料，规划了篇幅，应当是中篇幅、需要大约20+页，优先每个章节(chapter)必须有细化的页标题(content)，允许输出幻灯片(slide)总数在指定篇幅上下浮动5页</cogitate>\n        <slide index=\"1\">\n            <type>cover</type>\n            <title level=\"1\">现代女性主义与社会变迁</title>\n        </slide>\n        <slide index=\"2\">\n            <type>outline</type>\n            <title>目录</title>\n        </slide>\n        <slide index=\"3\">\n            <type>chapter</type>\n            <title level=\"2\">女性主义概念与起源</title>\n        </slide>\n        <slide index=\"4\">\n            <type>content</type>\n            <title level=\"3\">女性主义的定义与重要性</title>\n            <description level=\"4\">概述女性主义的概念、起源及其重要性</description>\n        </slide>\n        <slide index=\"5\">\n            <type>content</type>\n            <title level=\"3\">女性主义的起源与发展</title>\n            <description level=\"4\">追溯女性主义的起源，从古希腊和古罗马时期到19世纪末的西方社会</description>\n        </slide>\n        ......\n        <slide index=\"24\">\n            <type>chapter</type>\n            <title level=\"2\">未来女性主义的展望与期许</title>\n        </slide>\n        <slide index=\"25\">\n            <type>content</type>\n            <title level=\"3\">科技赋能下的女性发展</title>\n            <description level=\"4\">展望新兴科技为女性在职场、教育、参政创造机遇，关注新性别鸿沟。</description>\n        </slide>\n        <slide index=\"26\">\n            <type>content</type>\n            <title level=\"3\">跨区域女性联合的深化</title>\n            <description level=\"4\">设想全球女性跨国联合应对共同问题，如反对性别暴力、争取劳动权益的协作。</description>\n        </slide>\n        <slide index=\"27\">\n            <type>content</type>\n            <title level=\"3\">文化重塑中的女性力量</title>\n            <description level=\"4\">探讨女性利用多元文化手段重塑性别文化，培育平等社会文化土壤。</description>\n        </slide>\n        <slide index=\"28\">\n            <type>ending</type>\n            <title>谢谢</title>\n        </slide>\n\n#注意\n-短篇幅是指10+页\n-中篇幅是指20+页\n-长篇幅是指30+页\n-输出格式中，最后一个slide index=\"n\"中，n就是page数\n-页(page)和幻灯片(slide)是同一个概念\n-slide的类型type包含5种：cover、outline、chapter、content、ending\n\n#关于PPT内容的要求\n-用<cogitate>关于篇幅和页数的分析</cogitate>表示应该输出多少页的篇幅分析过程\n-根据<用户输入>提炼出PPT主题，输出格式中用<title level=\"1\">PPT主题</title>表示主题\n-标题不要出现编号，序号等序列标识\n-根据PPT主题划分多个章节标题，输出格式中用<title level=\"2\">章节标题</title>表示章节标题\n-根据章节标题细化几个页标题，输出格式中用 <title level=\"3\">页标题</title>表示页标题\n-每个页标题下描述该页的创作思路，输出格式中用<description level=\"4\">描述该页的创作思路</description>表示创作思路\n-每页的创作思路是紧紧围绕页标题的一句阐述\n-参考资料只是辅助\n-优先每个章节(chapter)必须有细化的页标题(content)，允许输出幻灯片(slide)总数在指定篇幅上下浮动5页\n\n#用户输入\n{q}\n\n#任务开始\n请根据以上对话和<用户输入>按要求生成完整PPT\n#开始输出"""
