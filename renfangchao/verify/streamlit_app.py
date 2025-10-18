import io
import sys
import threading
from contextlib import redirect_stderr, redirect_stdout

import streamlit as st

from renfangchao.verify.file_operations import copy_file
from renfangchao.verify.gen_1_answer import run_batch_verification
from renfangchao.verify.send_report import send_report
from renfangchao.verify.streamlit_utils import authorize

isvaild, username, is_admin = authorize()  # type: ignore
if isvaild:
    st.session_state.username = username
    st.session_state.is_admin = is_admin
else:
    st.error(str("无权限"))
    st.stop()
st.title("消息类型自动化")

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
is_send_report = st.checkbox("是否发送群消息", value=False)
from renfangchao.verify.gen_1_answer import run_batch_verification

# 执行按钮
if st.button("开始批量验证", type="primary"):
    # 参数校验
    # if not is_test and not run_wps_sid.strip():
    #     st.error("正式环境下，wps_sid 不能为空！")
    #     st.stop()

    # 创建输出容器
    output_container = st.container()
    with output_container:
        st.subheader("执行日志")
        log_placeholder = st.empty()

    # 捕获输出
    output_buffer = io.StringIO()

    try:
        with redirect_stdout(output_buffer), redirect_stderr(output_buffer):
            with st.spinner("正在复制文件..."):
                # 复制文件
                file = copy_file(is_test)

                # 实时显示输出
                log_placeholder.text_area(
                    "输出日志", output_buffer.getvalue(), height=200
                )

            if file:
                # st.success(f"文件复制成功！文件ID: {file['link_url']}")

                # 显示查看进度的链接
                if file.get("link_url"):
                    st.markdown(f"🔗 [点击查看进度和结果]({file['link_url']})")

                with st.spinner("正在运行批量验证..."):
                    # 运行批量验证
                    run_batch_verification(
                        file["file_id"],
                        is_test=is_test,
                        branch=branch,
                        run_wps_sid=run_wps_sid,
                    )

                    # 更新最终输出
                    log_placeholder.text_area(
                        "输出日志", output_buffer.getvalue(), height=300
                    )
                # send_report(file["file_id"], is_test=is_test, branch=branch)
                st.success("批量验证完成！")
                if is_send_report:
                    with st.spinner("正在发送报告..."):
                        send_report(
                            file["file_id"],
                            is_test=is_test,
                            branch=branch,
                        )
                        st.success("报告已发送！")

                # 再次提醒查看结果
                if file.get("link_url"):
                    st.success("✅ 验证完成！请点击上方链接查看最终结果")
            else:
                st.error("文件复制失败，请检查文件操作。")

    except Exception as e:
        st.error(f"执行过程中出现错误: {str(e)}")
        # 显示错误时的输出
        if output_buffer.getvalue():
            log_placeholder.text_area("输出日志", output_buffer.getvalue(), height=300)
