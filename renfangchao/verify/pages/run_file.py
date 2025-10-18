import io
import sys
import threading
from contextlib import redirect_stderr, redirect_stdout

import streamlit as st

from renfangchao.verify.gen_1_answer import run_batch_verification
from renfangchao.verify.streamlit_utils import authorize

isvaild, username, is_admin = authorize()  # type: ignore
if isvaild:
    st.session_state.username = username
    st.session_state.is_admin = is_admin
else:
    st.error(str("无权限"))
    st.stop()
st.title("消息类型自动化")
from urllib.parse import ParseResult, urlparse, urlunparse


def remove_query_params(url):
    parsed_url = urlparse(url)
    new_url = parsed_url._replace(query="")
    return urlunparse(new_url)


# 参数输入
# st.header("参数设置")

is_test = st.checkbox(
    "测试环境", value=False, help="勾选表示测试环境，取消表示灰度环境"
)
branch = st.text_input("测试分支", value="master", placeholder="输入分支名称")
run_wps_sid = st.text_input(
    "run_wps_sid",
    value="",
    placeholder="如果要使用指定用户，请输入wps_sid",
).strip()
test_doc_link = remove_query_params(
    st.text_input(
        "测试文档链接",
        value="",
        placeholder="输入测试文档的完整链接",
    ).strip()
)

# 执行按钮
if st.button("开始批量验证", type="primary"):
    # 参数校验
    if not test_doc_link:
        st.error("测试文档链接不能为空！")
        st.stop()

    # 从链接中提取file_id
    try:
        file_id = test_doc_link.split("/")[-1]
        if not file_id:
            st.error("无法从链接中提取有效的文件ID！")
            st.stop()
    except Exception as e:
        st.error(f"解析链接失败: {str(e)}")
        st.stop()

    # 创建输出容器
    output_container = st.container()
    with output_container:
        st.subheader("执行日志")
        log_placeholder = st.empty()

    # 捕获输出
    output_buffer = io.StringIO()

    try:
        with redirect_stdout(output_buffer), redirect_stderr(output_buffer):
            # 显示文档链接
            st.markdown(f"🔗 [点击查看进度和结果]({test_doc_link})")

            with st.spinner("正在运行批量验证..."):
                # 运行批量验证
                run_batch_verification(
                    file_id,
                    is_test=is_test,
                    branch=branch,
                    run_wps_sid=run_wps_sid,
                )

                # 更新最终输出
                log_placeholder.text_area(
                    "输出日志", output_buffer.getvalue(), height=300
                )

            st.success("批量验证完成！")

            # 再次提醒查看结果
            st.success("✅ 验证完成！请点击上方链接查看最终结果")

    except Exception as e:
        st.error(f"执行过程中出现错误: {str(e)}")

    except Exception as e:
        st.error(f"执行过程中出现错误: {str(e)}")
        # 显示错误时的输出
        if output_buffer.getvalue():
            log_placeholder.text_area("输出日志", output_buffer.getvalue(), height=300)
