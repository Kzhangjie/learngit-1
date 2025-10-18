import streamlit as st
import re


def extract_html_code(text_list):
    """从字符串列表中提取 ```html ... ``` 代码块"""
    if not isinstance(text_list, list) or not text_list:
        return None

    # 合并列表所有元素（处理可能的多行输入）
    full_text = "".join(text_list)

    # 正则匹配优化：支持 ```html 后直接换行或转义换行
    pattern = r"```html\s*?\n([\s\S]*?)\n\s*?```"  # 匹配 ```html 后任意空白+换行，到结尾换行+```
    match = re.search(pattern, full_text, re.DOTALL)  # re.DOTALL 让.匹配换行符

    if match:
        html_code = match.group(1).strip()  # 去除首尾空白
        return html_code
    return None


def main():
    st.set_page_config(page_title="HTML提取预览工具", layout="wide", page_icon="📄")
    st.title("📄 HTML 代码提取与实时预览工具")

    st.markdown("### 使用说明")
    st.markdown("- 输入格式：包含 ```html ... ``` 代码块的字符串列表（支持多行）")
    st.markdown(
        "- 示例输入：`['```html\\n<!DOCTYPE html>...\\n```']` 或直接粘贴带换行的列表"
    )

    # 输入区域增强：支持更大高度和更友好的提示
    user_input = st.text_area(
        "请输入包含 HTML 代码块的字符串列表",
        height=300,
        placeholder="示例输入（可直接复制）：\n['```html\n<!DOCTYPE html>\n<html>...\n</html>\n```']",
    )

    if user_input:
        try:
            # 安全转换：使用ast.literal_eval替代eval，防止代码注入
            from ast import literal_eval

            text_list = literal_eval(user_input)

            html_code = extract_html_code(text_list)

            if html_code:
                st.success("✅ 成功提取到 HTML 代码块")

                # 分栏显示：代码预览和结构预览
                code_col, preview_col = st.columns([1, 1])

                with code_col:
                    st.subheader("📝 原始代码")
                    st.code(html_code, language="html")

                with preview_col:
                    st.subheader("🖥️ 预览效果")
                    st.components.v1.html(html_code, height=600, scrolling=True)
            else:
                st.warning(
                    "⚠️ 未检测到合法的 HTML 代码块（请检查是否包含 ```html ... ``` 包裹的内容）"
                )

        except Exception as e:
            st.error(f"❌ 输入解析失败：{str(e)}")
            st.markdown(
                "请检查：\n- 输入是否为合法的字符串列表\n- 代码块是否用 ```html ... ``` 正确包裹\n- 特殊符号是否转义正确"
            )


if __name__ == "__main__":
    main()
