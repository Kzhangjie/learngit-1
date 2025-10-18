# 主程序
# 主要实现streamlit前端渲染
import os

import altair as alt
import matplotlib.pyplot as plt
import streamlit as st

import LongClient
import TwoReady
import zhiliang

# 评分分析模块
from Ready import (
    clean_invalid_user_input,
    extract_mini_search_command,
    import_csv_to_db,
)

# 设置中文字体，正常显示负号
plt.rcParams["font.family"] = "SimHei"

# 页面设置
st.set_page_config(page_title="划词数据处理与分析平台", layout="wide")
st.title("📊 划词数据处理与分析平台")

DB_PATH = "dialog_data.db"

# ------ 状态展示区 ------
status_placeholder = st.container()


# ------ 数据准备 ------
def run_ready_steps():
    with status_placeholder:
        with st.spinner("📥 步骤1/3：导入 CSV 到数据库..."):
            import_csv_to_db()
            st.success("✅ 步骤1：CSV 导入完成")

        with st.spinner("🧹 步骤2/3：清洗无效用户输入..."):
            clean_invalid_user_input()
            st.success("✅ 步骤2：清洗完成")

        with st.spinner("🔍 步骤3/3：提取 mini_search 指令数据..."):
            extract_mini_search_command()
            st.success("✅ 步骤3：提取完成")


if os.path.exists(DB_PATH):
    with status_placeholder:
        st.info(f"🗃️ 数据库 `{DB_PATH}` 已存在，跳过数据清洗步骤")
else:
    run_ready_steps()

st.divider()

# -------- 横向三列：Tab1-Tab3 --------
col1, col2, col3 = st.columns(3)

with col1:
    st.subheader("📏 划词长度分布")
    df_len = LongClient.analyze_length_distribution()
    st.dataframe(df_len.set_index("length_category"), use_container_width=True)
    chart = (
        alt.Chart(df_len)
        .mark_bar()
        .encode(
            x=alt.X(
                "length_category:N",
                sort=df_len["length_category"].tolist(),
                axis=alt.Axis(labelAngle=0),
            ),
            y="count:Q",
            tooltip=["length_category", "count"],
        )
        .properties(width=300, height=300)
    )
    st.altair_chart(chart, use_container_width=True)

with col2:
    st.subheader("🧩 用户使用平台分布")
    df_client, valid_df, invalid_df = LongClient.analyze_client_type()
    st.dataframe(df_client.set_index("client_type"), use_container_width=True)
    chart = (
        alt.Chart(df_client)
        .mark_bar()
        .encode(
            x=alt.X(
                "client_type:N",
                sort=df_client["client_type"].tolist(),
                axis=alt.Axis(labelAngle=0),
            ),
            y="count:Q",
            tooltip=["client_type", "count"],
        )
        .properties(width=300, height=300)
    )
    st.altair_chart(chart, use_container_width=True)
    st.markdown(
        f"""
    📦 总数：**{len(valid_df) + len(invalid_df)}**  
    ✅ 有效：**{len(valid_df)}**  
    🚫 无效：**{len(invalid_df)}**
    """
    )

with col3:
    st.subheader("🔄 单轮/多轮对话分析")
    df_all = TwoReady.extract_mini_search_sessions()
    turn_df = TwoReady.classify_dialog_turns(df_all)
    st.markdown(
        f"""
    - 总会话：**{turn_df['SessionID'].nunique()}**
    - 单轮：**{(turn_df['type'] == '单轮').sum()}**
    - 多轮：**{(turn_df['type'] == '多轮').sum()}**
    """
    )
    # 饼图展示单轮/多轮占比（使用 matplotlib）
    type_counts = turn_df["type"].value_counts()
    labels = type_counts.index.tolist()
    sizes = type_counts.values.tolist()
    colors = ["#66c2a5", "#fc8d62"]  # 可自定义颜色

    fig, ax = plt.subplots()
    ax.pie(
        sizes,
        labels=labels,
        autopct="%1.1f%%",
        startangle=90,
        colors=colors,
        textprops={"fontsize": 10},
    )
    ax.axis("equal")  # 保证饼图是圆的
    st.pyplot(fig)

st.divider()

# -------- 横向两列：Tab4-Tab5 --------
col4, col5 = st.columns(2)


with col4:
    st.subheader("📋 chat/websearch 分发情况")
    type_summary, type_details = TwoReady.analyze_second_assistant_type(df_all)

    st.markdown(
        f"""
    - `chat` 类型：**{type_summary['chat']}**
    - `websearch` 类型：**{type_summary['websearch']}**
    - 其他类型：**{type_summary['其他']}**
    """
    )

    # 条形图数据准备
    labels = ["chat", "websearch", "其他"]
    values = [type_summary["chat"], type_summary["websearch"], type_summary["其他"]]
    colors = ["#66b3ff", "#99ff99", "#ffcc99"]

    fig, ax = plt.subplots()
    ax.bar(labels, values, color=colors)
    ax.set_ylabel("数量")
    ax.set_title("chat / websearch / 其他 类型分布")
    for i, v in enumerate(values):
        ax.text(
            i, v + max(values) * 0.01, str(v), ha="center", va="bottom"
        )  # 显示具体数值
    st.pyplot(fig)


with col5:
    st.subheader("⭐ 生成回答质量分析")
    if not zhiliang.check_panding_table_exist():
        st.warning("⚠️ 表 `panding` 不存在，请先运行评分分析")

        if st.button("📤 导出结构化记录至 Excel"):
            zhiliang.export_structured_records()
            st.success("✅ 已导出至 text.xlsx，请在 Excel 中检查或运行打分流程")

        if st.button("🧠 执行评分流程（需已导出 Excel）"):
            with st.spinner("正在评分..."):
                zhiliang.run_all()
            st.success("✅ 分析完成，评分已写入数据库")
    else:
        df_score = zhiliang.load_panding_data()
        if df_score.empty:
            st.info("无评分数据")
        else:
            figs, avg_scores = zhiliang.analyze_and_prepare_figs(df_score)
            st.markdown("### 📊 平均评分")
            for name, avg in avg_scores.items():
                st.markdown(f"- **{name}** 平均分：`{avg:.2f}`")

            st.markdown("### 📈 评分分布柱状图")
            cols = st.columns(len(figs))
            for i, (name, fig) in enumerate(figs.items()):
                with cols[i]:
                    st.markdown(f"**{name}**")
                    st.pyplot(fig)
