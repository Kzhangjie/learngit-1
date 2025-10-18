import json


def extract_data_types(input_text):
    # 按空行分割输入文本，得到每个事件块
    events = input_text.strip().split("\n\n")
    data_types = []

    for event in events:
        lines = event.split("\n")
        if len(lines) < 2:
            continue

        # 检查数据行
        data_line = lines[1]
        if not data_line.startswith("data:"):
            continue

        # 提取data:后面的内容
        data_str = data_line[5:].strip()

        # 跳过空数据（空对象或空字符串）
        if not data_str or data_str == "{}":
            continue

        # 尝试解析JSON数据
        try:
            data = json.loads(data_str)
        except json.JSONDecodeError as e:
            print(f"JSON解析错误: {e}")
            print(f"原始数据: {repr(data_str)}")
            continue

        # 打印解析后的数据（只显示关键信息）
        if isinstance(data, dict) and "type" in data:
            print(f"成功解析 - 类型: {data['type']}")
            if "data" in data and data["data"]:
                # 显示data字段的前50个字符
                data_preview = (
                    str(data["data"])[:50] + "..."
                    if len(str(data["data"])) > 50
                    else str(data["data"])
                )
                print(f"  数据预览: {repr(data_preview)}")

        # 检查是否包含type字段
        if isinstance(data, dict) and "type" in data:
            data_types.append(data["type"])

    return data_types


# 示例输入文本
input_example = """event:execution
data:{"data":{"model":"model-s","ab_test":"","user_request":{"content":"生成思维导图，主题是李白","reference_group_id":"9395827212550200"}},"fallback":{"type":"ignore","content":{}},"group_id":"","message_id":"601333011769725752","operation":{"type":"ignore"},"type":"user"}

event:ping
data:{}

event:execution
data:{"data":"","fallback":{"type":"text","content":""},"group_id":"9395828307591224","message_id":"601333019243972408","operation":{"type":"ignore"},"type":"mind_map_start"}

event:execution
data:{"data":"# 李白\n## 生平经历\n### 少年时期\n- 蜀中生活游历增长见识\n- 学习剑术文学展才华\n### 辞亲远游\n","fallback":{"type":"text","content":"# 李白\n## 生平经历\n### 少年时期\n- 蜀中生活游历增长见识\n- 学习剑术文学展才华\n### 辞亲远游\n"},"group_id":"9395828307591224","message_id":"601333019243972408","operation":{"type":"ignore"},"type":"mind_map"}

event:execution
data:{"data":"- 仗剑出蜀漫游四方\n- 结交豪杰开阔视野\n### 赐金放还\n- 供奉翰林仕途波折\n- 离开长安重归江湖\n","fallback":{"type":"text","content":"- 仗剑出蜀漫游四方\n- 结交豪杰开阔视野\n### 赐金放还\n- 供奉翰林仕途波折\n- 离开长安重归江湖\n"},"group_id":"9395828307591224","message_id":"601333019243972408","operation":{"type":"ignore"},"type":"mind_map"}

event:execution
data:{"data":"### 安史之乱\n- 入永王幕卷入纷争\n- 流放夜郎途中获赦\n## 诗歌风格\n### 豪放飘逸\n- 想象奇特意境开阔\n","fallback":{"type":"text","content":"### 安史之乱\n- 入永王幕卷入纷争\n- 流放夜郎途中获赦\n## 诗歌风格\n### 豪放飘逸\n- 想象奇特意境开阔\n"},"group_id":"9395828307591224","message_id":"601333019243972408","operation":{"type":"ignore"},"type":"mind_map"}

event:execution
data:{"data":"- 情感奔放洒脱不羁\n### 浪漫奇幻\n- 神话传说融入诗篇\n- 夸张手法增添奇幻\n### 清新自然\n- 语言质朴不假雕琢\n","fallback":{"type":"text","content":"- 情感奔放洒脱不羁\n### 浪漫奇幻\n- 神话传说融入诗篇\n- 夸张手法增添奇幻\n### 清新自然\n- 语言质朴不假雕琢\n"},"group_id":"9395828307591224","message_id":"601333019243972408","operation":{"type":"ignore"},"type":"mind_map"}

event:ping
data:{}

event:execution
data:{"data":"- 田园山水尽显纯真\n## 代表诗作\n### 饮酒抒怀\n- 将进酒叹时光之匆匆\n- 月下独酌享饮酒之乐\n","fallback":{"type":"text","content":"- 田园山水尽显纯真\n## 代表诗作\n### 饮酒抒怀\n- 将进酒叹时光之匆匆\n- 月下独酌享饮酒之乐\n"},"group_id":"9395828307591224","message_id":"601333019243972408","operation":{"type":"ignore"},"type":"mind_map"}

event:execution
data:{"data":"### 写景状物\n- 望庐山瀑布绘奇景\n- 蜀道难状山川之险\n### 思乡怀人\n- 静夜思表思乡之情\n- 赠汪伦显友情深厚\n","fallback":{"type":"text","content":"### 写景状物\n- 望庐山瀑布绘奇景\n- 蜀道难状山川之险\n### 思乡怀人\n- 静夜思表思乡之情\n- 赠汪伦显友情深厚\n"},"group_id":"9395828307591224","message_id":"601333019243972408","operation":{"type":"ignore"},"type":"mind_map"}

event:execution
data:{"data":"## 文学影响\n### 唐代诗坛\n- 引领浪漫主义诗风\n- 与杜甫并称李杜双星\n### 后世传承\n- 诗作流传千古受敬仰\n","fallback":{"type":"text","content":"## 文学影响\n### 唐代诗坛\n- 引领浪漫主义诗风\n- 与杜甫并称李杜双星\n### 后世传承\n- 诗作流传千古受敬仰\n"},"group_id":"9395828307591224","message_id":"601333019243972408","operation":{"type":"ignore"},"type":"mind_map"}

event:execution
data:{"data":"- 启发无数诗人之创作 ","fallback":{"type":"text","content":"- 启发无数诗人之创作 "},"group_id":"9395828307591224","message_id":"601333019243972408","operation":{"type":"ignore"},"type":"mind_map"}

event:execution
data:{"data":"","fallback":{"type":"text","content":""},"group_id":"9395828307591224","message_id":"601333019243972408","operation":{"type":"ignore"},"type":"mind_map_end"}

event:aigc
data:{"data":null,"fallback":{"type":"text","content":""},"group_id":"9395828307591224","message_id":"601333019243972408","operation":{"type":"ignore"},"type":"end"}

event:execution
data:{"data":null,"fallback":{"type":"ignore","content":{}},"group_id":"9395828307591224","message_id":"601333067918869304","operation":{"type":"ignore"},"type":"recommend_start"}

event:ping
data:{}

event:execution
data:{"data":"[\"补充李白少年时期学习细节\",\"李白豪放飘逸风格成因是啥\",\"李白对现代诗歌有何影响\"]","fallback":{"type":"ignore","content":{}},"group_id":"9395828307591224","message_id":"601333067918869304","operation":{"type":"ignore"},"type":"recommend"}

event:execution
data:{"data":null,"fallback":{"type":"ignore","content":{}},"group_id":"9395828307591224","message_id":"601333067918869304","operation":{"type":"ignore"},"type":"recommend_end"}

event:finish
data:

"""
from copilot.api2_rfc import Copilot

api = Copilot(
    is_test=True,
)
if __name__ == "__main__":
    # 调用函数并打印结果
    _, rs, _ = api.questions(["生成思维导图，主题是李白"])
    with open("output.json", "w", encoding="utf-8") as f:
        json.dump(rs[0], f, ensure_ascii=False, indent=2)
    # data_types = extract_data_types(input_example)
    # print(data_types)
