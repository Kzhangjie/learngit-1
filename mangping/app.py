import streamlit as st
from dotenv import load_dotenv

load_dotenv()
import os
import sys
import airsheet
import re
import random
import traceback
import datetime
from streamlit_server_state import (
    server_state,
    server_state_lock,
)
from streamlit import runtime
from streamlit.runtime.scriptrunner import get_script_run_ctx
import json

st.set_page_config(page_title="盲评工具", layout="wide")


def get_remote_ip() -> str:
    """Get remote ip."""

    try:
        xff = st.context.headers.get("X-Forwarded-For", "")
        if xff:
            return xff.split(",")[0].strip()
        ctx = get_script_run_ctx()
        if ctx is None:
            return ""

        session_info = runtime.get_instance().get_client(ctx.session_id)
        if session_info is None:
            return ""
    except Exception as e:
        return ""

    return session_info.request.remote_ip  # type: ignore


param_wps_sid = os.environ["WPS_SID"]
import sys

# 检查是否有自定义命令行参数传入
if len(sys.argv) > 1:
    param_url = sys.argv[1]
else:
    param_url = os.environ.get("APP_PARAM_URL", "https://365.kdocs.cn/l/cp203rE6R5qw")


reason_len_limit = int(os.environ.get("APP_REASON_LEN_LIMIT", 10))
reason_len_limit = 0
答案_A = "答案A"
答案_B = "答案B"

config_question_cloumn = "问题"
config_answer_a_cloumn = 答案_A
config_answer_b_cloumn = 答案_B
config_result_cloumn = "盲评结果"
config_result_cloumn_no = "P"
config_sheet_name = "盲评记录_open"


if "reason" not in st.session_state:
    st.session_state.reason = ""
st.session_state.ip = get_remote_ip()

status_completed = "completed"
status_showing = "showing"
status_not_completed = "not_completed"


# Function to inject custom CSS
def inject_custom_css():
    custom_css = """
        <style>
            /* Custom CSS for horizontal radio buttons */
            .stRadio > div {
                display: flex;
                flex-direction: row;
            }
            /* Custom CSS for scrollable text areas */
            .stTextArea > div > div {
                height: 300px;
                overflow-y: auto;
            }
        </style>
    """
    st.markdown(custom_css, unsafe_allow_html=True)


def get_datas(file_id, wps_sid):
    airsheet.init(file_id=file_id, wps_sid=wps_sid, sheet_name=config_sheet_name)
    df = airsheet.xl("A:ZZ", headers=True, sheet_name=[config_sheet_name])
    columns_to_drop = [col for col in df.columns if col == "" or col is None]  # type: ignore
    df = df.drop(columns=columns_to_drop)  # type: ignore
    df["row_index"] = df.index + 2
    for col in [
        config_question_cloumn,
        config_answer_a_cloumn,
        config_answer_b_cloumn,
    ]:
        df = df.dropna(subset=[col])
    df.fillna("", inplace=True)
    # df = df[df[config_result_cloumn] == ""]
    datas = df.to_dict(orient="records")

    return datas


# Function to fetch data from the provided URL
def fetch_data(url, wps_sid):
    try:
        pattern = r"/l/(\w+)"
        match = re.search(pattern, url)
        if not match:
            print("DEBUG: 正则未匹配到 fid，url=", url)
            return
        fid = match.group(1)
        datas = get_datas(fid, wps_sid)
        return datas
    except Exception as e:
        traceback.print_exc()
        print("DEBUG: fetch_data 捕获到异常:", e)
        st.error(f"获取数据失败")
        return []


# Function for submitting the annotation
def submit_annotation(choice, reasons, reason, others):
    try:
        options = {
            "答案A好": st.session_state.data["显示的答案A"],
            "答案B好": st.session_state.data["显示的答案B"],
            "平局": "平局",
        }
        r1 = options[choice]

        A有幻觉 = others.get("A有幻觉", False)
        B有幻觉 = others.get("B有幻觉", False)
        huans = [A有幻觉, B有幻觉]
        if st.session_state.data["显示的答案A"] != 答案_A:
            huans = [B有幻觉, A有幻觉]

        result = [
            st.session_state.ip,
            st.session_state.user_name,
            r1,
            reasons,
            reason,
            st.session_state.data["显示的答案A"],
            st.session_state.data["显示的答案B"],
        ]
        result.extend(huans)
        with open("./mangping/log.jsonl", "a", encoding="utf-8") as f:
            log = {
                "time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "ip": st.session_state.ip,
                "user_name": st.session_state.user_name,
                "row_index": st.session_state.data["row_index"],
                "result": result,
                "param_url": param_url,
            }
            f.write(json.dumps(log, ensure_ascii=False) + "\n")
        airsheet.write_xl(
            result,
            f'{config_result_cloumn_no}{st.session_state.data["row_index"]}',
            sheet_name=config_sheet_name,
        )
        sumbit_data(st.session_state.data["row_index"], r1, reasons, reason)
        return True
    except Exception as e:
        traceback.print_exc()
        st.error(f"写表格失败:{str(e)}")
    return False


# Initialize session state
if "data" not in st.session_state:
    st.session_state.data = {}
inject_custom_css()


def init_server_state():
    datas = fetch_data(param_url, param_wps_sid) or []
    with server_state_lock["datas"]:
        server_state.user_completed_count = {}
        for d in datas:
            random.seed(d["row_index"])
            if random.choice([True, False]):
                d["显示的答案A"] = 答案_B
                d["显示的答案B"] = 答案_A
            else:
                d["显示的答案A"] = 答案_A
                d["显示的答案B"] = 答案_B
            if d[config_result_cloumn]:
                d["status"] = status_completed
                user_name = d["用户名"]
                server_state.user_completed_count[user_name] = (
                    server_state.user_completed_count.setdefault(user_name, 0) + 1
                )
            elif d["row_index"] in server_state.showing_ids:
                d["status"] = status_showing
            else:
                d["status"] = status_not_completed
        server_state.datas = datas
        to_complete_count = len(
            [item for item in server_state.datas if item["status"] != status_completed]
        )
        print(f"初始化{len(datas)}条数据,剩余{to_complete_count}条数据")


def show_data(reinited=False):
    with server_state_lock["datas"]:
        item = None
        not_completed_items = [
            item
            for item in server_state.datas
            if item.get("status") == status_not_completed
        ]
        # 先去掉前一个再随机选一个
        if len(not_completed_items) > 1 and ("last_skip_id" in st.session_state):
            not_completed_items = [
                item
                for item in not_completed_items
                if item["row_index"] != st.session_state.last_skip_id
            ]
        if not_completed_items:
            item = random.choice(not_completed_items)
            print(
                f"{st.session_state.user_name}展示not_completed数据{item['row_index']},状态为{item['status']}"
            )
        else:
            print("没有not_completed 数据")
        if not item:
            print("尝试展示showing数据")
            showing_items = [
                item
                for item in server_state.datas
                if item.get("status") == status_showing
            ]
            # 先去掉前一个再随机选一个
            if len(showing_items) > 1 and ("last_skip_id" in st.session_state):
                showing_items = [
                    item
                    for item in showing_items
                    if item["row_index"] != st.session_state.last_skip_id
                ]
            if showing_items:
                item = random.choice(showing_items)
                print(
                    f"{st.session_state.user_name}展示showing数据{item['row_index']},状态为{item['status']}"
                )
            else:
                print("没有showing 数据")
        if item:
            item["status"] = status_showing
            server_state.showing_ids.append(item["row_index"])
            server_state.user_showing_ids.setdefault(
                st.session_state.user_name, []
            ).append(item["row_index"])
            print(f"{st.session_state.user_name}展示了{item['row_index']}")
            return item
        if not item:
            if not reinited:
                init_server_state()
                return show_data(reinited=True)

        return item


def sumbit_data(id, choice, reasons, reason):
    with server_state_lock["datas"]:
        data = next(
            (item for item in server_state.datas if item["row_index"] == id), None
        )
        if data:
            data["status"] = status_completed
            data["盲评结果"] = choice
            data["盲评理由"] = reasons
            data["说明"] = reason
            data["ip"] = st.session_state.ip
            data["用户名"] = st.session_state.user_name
            server_state.showing_ids = [
                item for item in server_state.showing_ids if item != id
            ]
            try:
                server_state.user_showing_ids.setdefault(
                    st.session_state.user_name, []
                ).remove(data["row_index"])
            except ValueError:
                pass
            user_name = st.session_state.user_name
            server_state.user_completed_count[user_name] = (
                server_state.user_completed_count.setdefault(user_name, 0) + 1
            )
            print(
                f"{st.session_state.user_name}提交了{id},选择{choice}，理由：{reasons}，其他理由：{reason}"
            )
            to_complete_count = len(
                [
                    item
                    for item in server_state.datas
                    if item["status"] != status_completed
                ]
            )
            print(f"剩余{to_complete_count}条数据")


def skip_data():
    if not st.session_state.data:
        return
    id = st.session_state.data["row_index"]
    st.session_state.last_skip_id = id
    print(f"{st.session_state.user_name}跳过了{id}")
    with server_state_lock["datas"]:
        try:
            server_state.showing_ids.remove(id)
        except ValueError:
            pass
        try:
            server_state.user_showing_ids.setdefault(
                st.session_state.user_name, []
            ).remove(id)
        except ValueError:
            pass
        data = next(
            (item for item in server_state.datas if item["row_index"] == id), None
        )
        if data:
            if data["status"] == status_completed:
                return
            if id not in server_state.showing_ids:
                data["status"] = status_not_completed


if "server_state_initialized" not in st.session_state:
    with server_state_lock["datas"]:
        if "datas" not in server_state:
            server_state.user_showing_ids = {}
            server_state.showing_ids = []
            init_server_state()


if "fetch_button_clicked" not in st.session_state:
    st.session_state.fetch_button_clicked = False

with st.expander("基础信息", expanded=True):
    st.text_input(
        "你的姓名:",
        "",
        key="user_name_raw",
        disabled=st.session_state.fetch_button_clicked,
    )
    st.session_state.user_name = st.session_state.user_name_raw.strip()
    st.number_input("要评测的数量:", 1, 1000, 30, key="target_count")
    st.markdown(
        """#### 评测方法
请选出对你最有用的回答，并勾选对应理由，若有其他理由可自行输入后，点击提交

若想跳过该题，先评测其他题目，可以点击“评测下一题”跳过
"""
    )
fetch_button = st.button("评测下一题")
if fetch_button:
    if not st.session_state.user_name:
        st.error("请输入姓名。")
        st.stop()
    if st.session_state.user_name == "lingxi_admin":
        st.markdown("""#### user_showing_ids""")
        st.json(server_state.user_showing_ids)
        st.markdown("""#### user_completed_count""")
        st.json(server_state.user_completed_count)
        st.markdown("""#### showing_ids""")
        st.json(server_state.showing_ids)
        st.table(server_state.datas)
        st.stop()
    if st.session_state.user_name == "lingxi_reload":
        init_server_state()
        st.stop()
    skip_data()
    st.session_state.data = show_data()
    # print(f"剩余{len(server_state.datas)}条数据")
if st.session_state.user_name:
    st.session_state.fetch_button_clicked = True
    if st.session_state.data:
        st.markdown(
            f"正在评测第{server_state.user_completed_count.get(st.session_state.user_name,0)+1}个题目,目标{st.session_state.    target_count}个"
        )
    else:
        st.markdown(
            f"你评测了{server_state.user_completed_count.get(st.session_state.user_name,0)}个题目,没有数据了。"
        )
else:
    st.markdown("请先输入姓名。")


def row_to_xml(row):
    content = row["文件内容"]
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


# 过滤掉无效的 XML 字符
def remove_invalid_xml_chars(text):
    # XML 1.0合法字符范围
    valid_xml_regex = re.compile(
        "[\x09\x0a\x0d\x20-\ud7ff\ue000-\ufffd]|[\U00010000-\U0010ffff]", re.UNICODE
    )
    return "".join(valid_xml_regex.findall(text))


from lxml import etree as ET


def xml_to_json(text):
    text = remove_invalid_xml_chars(text)
    # 创建一个解析器，启用 recover 选项
    parser = ET.XMLParser(recover=True)
    try:
        root = ET.fromstring(text, parser=parser)
    except ET.XMLSyntaxError:
        print("无法从 XML 文本中恢复有效的文档。")
        return []

    # 初始化存储文档信息的列表
    documents = []

    # 遍历每个 document 元素
    for doc_elem in root.findall("document"):
        doc_info = {
            "index": doc_elem.get("index"),
            "document_type": (
                doc_elem.find("document_type").text
                if doc_elem.find("document_type") is not None
                else None
            ),
            "document_name": (
                doc_elem.find("document_name").text
                if doc_elem.find("document_name") is not None
                else None
            ),
            "document_content": [],
        }

        content_elem = doc_elem.find("document_content")
        if content_elem is not None:
            # 检查 document_content 是否有 page 子元素
            page_elems = content_elem.findall("page")
            if page_elems:
                for page_elem in page_elems:
                    page_info = {
                        "index": page_elem.get("index"),
                        "text": page_elem.text.strip() if page_elem.text else "",
                    }
                    doc_info["document_content"].append(page_info)
            else:
                # 如果没有 page 子元素，直接获取文本
                doc_info["document_content"] = (
                    content_elem.text.strip() if content_elem.text else None
                )

        documents.append(doc_info)
    return documents


def remove_prefix_until_comma(text):
    """去掉字符串中第一个逗号和之前的所有内容（支持中文逗号和英文逗号）"""
    if isinstance(text, str):
        # 查找第一个中文逗号
        cn_comma_index = text.find("，")
        # 查找第一个英文逗号
        en_comma_index = text.find(",")

        # 确定哪个逗号先出现（如果两种逗号都存在）
        if cn_comma_index >= 0 and en_comma_index >= 0:
            comma_index = min(cn_comma_index, en_comma_index)
        elif cn_comma_index >= 0:  # 只有中文逗号
            comma_index = cn_comma_index
        elif en_comma_index >= 0:  # 只有英文逗号
            comma_index = en_comma_index
        else:  # 没有任何逗号
            return text

        return text[comma_index + 1 :].strip()
    return text


if st.session_state.data:
    with st.form("annotation_form", clear_on_submit=True):

        qs = st.session_state.data["问题"].split("ask:")
        qs = [q.strip() for q in qs if q.strip()]
        q = qs[0]
        st.subheader(f"问题: {q}")
        refs = []
        xml_text = row_to_xml(st.session_state.data)
        if xml_text:
            st.subheader("相关文档")
            parse_success = False

            try:
                refs = xml_to_json(xml_text)
                parse_success = True
            except Exception as e:
                print(f"{st.session_state.data['row_index']}解析文件内容失败", e)
            if parse_success:
                for ref in refs:
                    with st.expander(
                        f"{ref['document_type']}文档 {ref['index']}: {ref['document_name']}",
                        expanded=True,
                    ):
                        st.markdown(f"{ref['document_content']}")
            st.markdown("原始xml内容")
            with st.expander(
                f"原始xml内容",
                expanded=False,
            ):
                # st.error("内容失败")
                st.code(xml_text, language="xml")
        refs_str = (
            st.session_state.data["search_1"]
            + st.session_state.data["search_2"]
            + st.session_state.data["search_3"]
            + st.session_state.data["search_4"]
        )

        refs = json.loads(refs_str) if refs_str else []

        if refs:
            st.subheader("搜索结果")
            for ref in refs:
                with st.expander(ref["url"], expanded=False):
                    st.markdown(ref["summary"])
        st.markdown("---")
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("答案A")
            with st.expander("思考", expanded=True):
                st.markdown(
                    remove_prefix_until_comma(
                        st.session_state.data[
                            st.session_state.data["显示的答案A"].replace("答案", "理由")
                        ]
                    ),
                    unsafe_allow_html=True,
                )
            if (
                st.session_state.data[st.session_state.data["显示的答案A"]]
                .strip()
                .startswith("<cogitate>")
            ):
                st.code(
                    st.session_state.data[st.session_state.data["显示的答案A"]].strip(),
                    language="xml",
                )
            else:
                st.markdown(
                    st.session_state.data[st.session_state.data["显示的答案A"]],
                    unsafe_allow_html=True,
                )
        with col2:
            st.subheader("答案B")
            with st.expander("思考", expanded=True):
                st.markdown(
                    remove_prefix_until_comma(
                        st.session_state.data[
                            st.session_state.data["显示的答案B"].replace("答案", "理由")
                        ]
                    ),
                    unsafe_allow_html=True,
                )
            if (
                st.session_state.data[st.session_state.data["显示的答案A"]]
                .strip()
                .startswith("<cogitate>")
            ):
                st.code(
                    st.session_state.data[st.session_state.data["显示的答案B"]].strip(),
                    language="xml",
                )
            else:
                st.markdown(
                    st.session_state.data[st.session_state.data["显示的答案B"]],
                    unsafe_allow_html=True,
                )

        st.subheader("您的评判")

        st.radio(
            "请选择最佳答案:",
            ("答案A好", "答案B好", "平局"),
            key="choice",
            index=None,
        )
        st.checkbox(
            "A有幻觉",
            key="A_hallucination",
            help="捏造内容，或与事实/参考资料不符，请勾选。",
        )
        st.checkbox(
            "B有幻觉",
            key="B_hallucination",
            help="捏造内容，或与事实/参考资料不符，请勾选。",
        )
        st.markdown("勾选理由:")
        input_reasons = "准确专业、逻辑严密、深度全面、独特创新、表达流畅、主题相关、用户友好、实用性".split(
            "、"
        )
        selected_reasons = []
        for reason in input_reasons:
            if st.checkbox(reason):
                selected_reasons.append(reason)
        st.session_state.reasons = "\n".join(selected_reasons)
        st.text_input(
            f"其他理由:",
            key="reason",
            help="您必须写理由才能评判。",
        )
        others = {
            "A有幻觉": st.session_state.A_hallucination,
            "B有幻觉": st.session_state.B_hallucination,
        }
        submitted = st.form_submit_button("提交")
        if submitted:
            if not st.session_state.choice:
                st.error("请选择最佳答案。")
            # 先检查是否需要理由，且理由是否已提供
            elif len(st.session_state.reason) >= reason_len_limit:
                # 提交标注
                result = submit_annotation(
                    st.session_state.choice,
                    st.session_state.reasons,
                    st.session_state.reason,
                    others,
                )
                if result:
                    st.session_state.data = show_data()
                    st.rerun()
                else:
                    st.error("标注提交失败，请检查输入。")
            else:
                st.error(f"评判理由不能小于{reason_len_limit}个字")
