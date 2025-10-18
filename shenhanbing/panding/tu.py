import streamlit as st
import re
from streamlit_mermaid import st_mermaid


def extract_mermaid_code(text):
    # 清除开头和结尾的引号
    text = text.strip().strip('"').strip("'")

    # 还原转义字符（如 \n、\"）
    try:
        text = bytes(text, "utf-8").decode("unicode_escape")
    except Exception:
        pass

    # 尝试修复编码错误导致的中文乱码
    try:
        text = text.encode("latin1").decode("utf-8")
    except Exception:
        pass

    # 提取 mermaid 代码块
    pattern = r"```mermaid\s*([\s\S]*?)```"
    match = re.search(pattern, text)
    if match:
        return match.group(1).strip()
    else:
        return text.strip()  # fallback：直接当作 Mermaid 内容返回


def main():
    st.set_page_config(page_title="Mermaid 图渲染器", layout="wide")
    st.title("🧭 Mermaid 图渲染器（支持转义字符串 & 中文乱码修复）")

    user_input = st.text_area(
        "请输入 Mermaid 字符串（支持 \\n 和中文乱码）",
        height=400,
        placeholder='例如：```mermaid\\ngraph TD\\n A["出发前"] --> B["准备"]\\n```',
    )

    if user_input:
        mermaid_code = extract_mermaid_code(user_input)

        if mermaid_code:
            col1, col2 = st.columns(2)

            with col1:
                st.subheader("✅ 提取的 Mermaid 代码")
                st.code(mermaid_code, language="mermaid")

            with col2:
                st.subheader("📈 渲染结果")
                try:
                    st_mermaid(mermaid_code)
                except Exception as e:
                    st.error(f"渲染失败：{e}")
        else:
            st.warning("⚠️ 未检测到 Mermaid 图代码")


if __name__ == "__main__":
    main()
