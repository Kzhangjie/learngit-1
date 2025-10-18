import re


def compare_string(pattern, target):
    """
    比较两个字符串

    Args:
        pattern (str): 模式字符串，如果以^开头则作为正则表达式
        target (str): 目标字符串

    Returns:
        tuple: (是否相等, 差异详情)
    """
    if pattern.startswith("^"):
        # 正则匹配模式
        regex_pattern = pattern
        try:
            match = re.match(regex_pattern, target)
            if match:
                return True, "正则匹配成功"
            else:
                # 正则匹配失败时，尝试分析具体差异
                # 移除正则符号，按分号分割进行部分匹配分析
                pattern_clean = (
                    pattern.replace("^", "")
                    .replace("$", "")
                    .replace("+", "")
                    .replace("(", "")
                    .replace(")", "")
                )
                pattern_parts = pattern_clean.split(";")
                target_parts = target.split(";")

                # 找出可能的差异位置
                differences = []
                min_parts = min(len(pattern_parts), len(target_parts))

                for i in range(min_parts):
                    if pattern_parts[i] and pattern_parts[i] not in target_parts[i]:
                        differences.append(
                            f"第{i+1}个部分可能不匹配: 期望包含'{pattern_parts[i]}', 实际'{target_parts[i]}'"
                        )
                        break

                if len(pattern_parts) != len(target_parts):
                    differences.append(
                        f"部分数量可能不匹配: 正则期望模式有{len(pattern_parts)}个基础部分, 目标有{len(target_parts)}个部分"
                    )

                if not differences:
                    differences.append("正则表达式结构不匹配，可能是重复模式或顺序问题")

                return False, f"正则匹配失败: {'; '.join(differences)}"
        except re.error as e:
            return False, f"正则表达式错误: {e}"
    else:
        # 普通字符串比较
        if pattern == target:
            return True, "字符串完全相等"

        # 用分号分割后逐个对比
        pattern_parts = pattern.split(";")
        target_parts = target.split(";")

        # 找出第一个不匹配的部分
        min_parts = min(len(pattern_parts), len(target_parts))

        for i in range(min_parts):
            if pattern_parts[i] != target_parts[i]:
                return (
                    False,
                    f"第{i+1}个部分不匹配: 期望'{pattern_parts[i]}', 实际'{target_parts[i]}'",
                )

        # 处理部分数量不同的情况
        if len(pattern_parts) != len(target_parts):
            if len(pattern_parts) > len(target_parts):
                return (
                    False,
                    f"缺少部分: 期望{len(pattern_parts)}个部分, 实际{len(target_parts)}个部分, 缺少'{';'.join(pattern_parts[min_parts:])}'",
                )
            else:
                return (
                    False,
                    f"多余部分: 期望{len(pattern_parts)}个部分, 实际{len(target_parts)}个部分, 多余'{';'.join(target_parts[min_parts:])}'",
                )

        return False, "未知差异"


def compare_strings(pattern, target):
    """
    比较两个多行字符串，逐行调用compare_string

    Args:
        pattern (str): 模式字符串（可能包含多行）
        target (str): 目标字符串（可能包含多行）

    Returns:
        tuple: (所有行是否都匹配, 详细差异信息)
    """
    pattern_lines = [line.strip() for line in pattern.strip().split("\n")]
    target_lines = [line.strip() for line in target.strip().split("\n")]

    all_match = True
    details = []

    max_lines = max(len(pattern_lines), len(target_lines))

    for i in range(max_lines):
        # 获取当前行，如果不存在则使用空字符串
        pattern_line = pattern_lines[i] if i < len(pattern_lines) else ""
        target_line = target_lines[i] if i < len(target_lines) else ""

        # 调用单行比较函数
        is_match, diff_detail = compare_string(pattern_line, target_line)
        if not is_match and (
            "image_start" in pattern_line and "GenImageLimit" in target_line
        ):
            is_match = True

        if not is_match:
            all_match = False
            details.append(f"第{i+1}行: {diff_detail}")
        # else:
        #     details.append(f"第{i+1}行: {diff_detail}")

    # 如果行数不同，记录差异
    if len(pattern_lines) != len(target_lines):
        all_match = False
        details.append(
            f"行数不同: 期望{len(pattern_lines)}行, 实际{len(target_lines)}行"
        )
    print(1111, details)

    return all_match, "\n".join(details)


a = """^user;canvas_edit_start;(canvas_replacement_start;canvas_replacement;canvas_replacement_end;)+canvas_edit_end;text_start;text;text_end;end;recommend_start;recommend;recommend_end$
user;canvas_edit_start;canvas_replacement_start;canvas_replacement;canvas_replacement_end;canvas_replacement_start;canvas_replacement;canvas_replacement_end;canvas_replacement_start;canvas_replacement;canvas_replacement_end;canvas_replacement_start;canvas_replacement;canvas_replacement_end;canvas_edit_end;text_start;text;text_end;end;recommend_start;recommend;recommend_end
"""
b = """user;canvas_edit_start1;canvas_replacement_start;canvas_replacement;canvas_replacement_end;canvas_replacement_start;canvas_replacement;canvas_replacement_end;canvas_replacement_start;canvas_replacement;canvas_replacement_end;canvas_replacement_start;canvas_replacement;canvas_replacement_end;canvas_edit_end;text_start;text;text_end;end;recommend_start;recommend;recommend_end
user;canvas_edit_start;canvas_replacement_start;canvas_replacement;canvas_replacement_end;canvas_replacement_start;canvas_replacement;canvas_replacement_end;canvas_replacement_start;canvas_replacement;canvas_replacement_end;canvas_replacement_start;canvas_replacement;canvas_replacement_end;canvas_edit_end;text_start;text;text_end;end;recommend_start;recommend_end"""

# 测试示例
if __name__ == "__main__":
    # 测试普通比较
    result1, diff1 = compare_strings(a, b)
    print(f"比较结果: {result1}")
    print(f"差异详情: {diff1}")
