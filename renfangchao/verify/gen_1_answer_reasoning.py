import json
import os
import traceback
from types import MethodType

import airsheet
from copilot.api2_rfc import Copilot
from mangping.mangping_utils import chat_retry, r2qcs, r2qs
from renfangchao.cc_server.as_utils import obj_to_strs, split_string
from renfangchao.verify.parse_sse import parse_rs, verify_card
from run_batch.run_ai import RunAi


def row_to_args(row, key, length, is_json=False, default_value="copy"):
    r = row.get(key, "").strip()
    if r:
        c = r.split("\n")
        if is_json:
            c = [json.loads(x) for x in c if x.strip()]
        else:
            c = [x.strip() for x in c if x.strip()]
        # print(666, c)
        if len(c) == 1 and default_value == "copy":
            return [c[0]] * length
        elif len(c) >= length:
            return c[:length]
        else:
            print(777)
            return c + default_value * (length - len(c))
    return []


import random
import time


def write_with_retry(data, cell_range, sheet_name, retry_count=3):
    print(f"尝试写入数据到 {sheet_name} 的 {cell_range}，数据: {data}", retry_count)
    for i in range(retry_count):
        try:
            airsheet.write_xl(data, cell_range, sheet_name=sheet_name)
            return True
        except Exception as e:
            print(f"写入重试失败，尝试第{i+1}次: {e}")
            time.sleep(random.randint(1, 3))  # 等待1到3秒后重试
            if i == retry_count - 1:
                print("重试次数已达上限，写入失败。")
    return False


def run_one(
    self, row, api: Copilot, default_question_config, 输出列编号, 返回列编号, 卡片列编号
):
    qs = r2qs(row)
    context_file_id = row.get("context_file_id", "")
    # context_file_id = ""
    context_agent = row.get("context_agent", "")
    count = len(qs)
    thinkings = row_to_args(row, "thinking", count, default_value="copy")
    file_idss = row_to_args(row, "file_ids", count, is_json=True, default_value=[])  # type: ignore
    card_types = row_to_args(row, "card_type", count, is_json=False, default_value="")
    # print(555, card_types)

    # if file_url:
    #     context_file_id = file_url.split("/")[-1].strip("")

    success, question_configs = r2qcs(row)
    if not success:
        write_with_retry(
            [f"问题配置解析失败: {question_configs}"],
            f'{输出列编号}{row["row_index"]}',
            sheet_name=self.sheetname,
        )
        return

    if not question_configs:
        qs = [{**default_question_config, "question": q} for q in qs]
    else:
        if len(question_configs) == 1:
            qs = [
                {**question_configs[0], **default_question_config, "question": q}  # type: ignore
                for q in qs
            ]
        elif len(question_configs) == len(qs):
            qs = [
                {**qc, **default_question_config, "question": q}  # type: ignore
                for qc, q in zip(question_configs, qs)
            ]
        else:
            raise ValueError(
                f"第{row['row_index']}行问题数量({len(qs)})与配置数量({len(question_configs)})不匹配，请检查输入数据。"
            )
    for i in range(len(qs)):
        qs[i]["reasoning"] = thinkings[i] == "enabled"
        qs[i]["file_ids"] = file_idss[i] if file_idss else []
        qs[i]["card_type"] = card_types[i] if card_types else ""

    # api.agent = context_agent if context_agent else ""
    historys, rsa, session_id = api.questions(
        questions=qs,
        context_file_id=context_file_id,
        with_history=False,
        agent=context_agent if context_agent else None,
    )  # type: ignore
    rsb = []
    cards = []
    for rs in rsa:
        if rs[0] == "ppt":
            cards.append(rs)
        else:
            rsb.append(rs)
    # print(222, cards)
    qsr = json.dumps(qs, ensure_ascii=False, indent=2)
    session_id = str(session_id)
    results = ["'" + session_id, f"https://lingxi.wps.cn/chat/{session_id}", qsr]
    request_ids = [r[1] for r in rsb]
    request_ids_str = "\n".join(request_ids)
    rs = [r[0] for r in rsb]
    typesa = parse_rs(rs)
    # typesa是二维数组，转成字符串
    typesa_str = "\n".join([";".join(t) for t in typesa])
    errors = []
    asserts_str = row.get("返回消息类型断言", "")

    is_assertion_same, assertion_differences = compare_strings(asserts_str, typesa_str)
    is_pass = "pass" if is_assertion_same else "fail"
    card_results = []
    card_errors = []
    for card in cards:
        card_type, card_json = card
        if card_type == "ppt":
            result, errors = verify_card(card_json)
            card_results.append(result)
            card_errors.append("\n\n".join(errors))
    card_results_str = "pass" if all(card_results) else "fail"
    card_errors_str = json.dumps(card_errors, ensure_ascii=False, indent=2)
    results.extend(
        [
            request_ids_str,
            typesa_str,
            is_pass,
            assertion_differences if assertion_differences else "",
            card_results_str,
            card_errors_str,
        ]
    )

    write_with_retry(
        results,
        f'{输出列编号}{row["row_index"]}',
        sheet_name=self.sheetname,
    )
    rss = "\n\n".join(
        [f"_______________req{i+1}_______________\n\n{rt}" for i, rt in enumerate(rs)]
    )
    write_with_retry(
        split_string(rss),
        f'{返回列编号}{row["row_index"]}',
        sheet_name=self.sheetname,
    )
    if cards:
        cardss = "\n\n".join(
            [
                f"_______________req{i+1}_______________\n\n{rt}"
                for i, rt in enumerate(cards)
            ]
        )
        write_with_retry(
            split_string(cardss),
            f'{卡片列编号}{row["row_index"]}',
            sheet_name=self.sheetname,
        )


from renfangchao.verify.result_compare import compare_strings


def run_batch_verification(file_id, is_test=True, branch="", run_wps_sid=None):
    """运行批量验证任务

    Args:
        file_id (str): 文件ID
        wps_sid (str, optional): WPS会话ID，如果不提供则使用环境变量
        sheet_names (list, optional): 要处理的工作表名称列表，默认为["thinking_enabled"]
    """
    print(f"开始批量验证 - 文件ID: {file_id}, 测试环境: {is_test}, 分支: {branch}")

    # 默认配置
    default_question_config = {
        # "command_args": {"disable_websearch": False},
        # "reasoning": False,
        # "thinking": "auto",
        # "context": {
        #     "enable_canvas_mode": True,
        #     "agent": "WPP",
        #     "file_code": "001004000",
        #     # "file_id": {"id": "1155576226052579328", "type": "object"},
        # },
    }

    必须有的列名 = ["问题"]
    输出列名 = "session_id"
    输出列编号 = "R"
    返回列编号 = "AK"
    卡片列编号 = "AU"

    sheet_names = ["thinking_disabled", "thinking_enabled"]
    # sheet_names = ["thinking_disabled"]

    # 获取WPS会话ID
    sid_name = "WPS_SID_TEST_DB" if is_test else "WPS_SID"
    if not run_wps_sid:
        run_wps_sid = os.environ.get(sid_name, "")
    file_wps_sid = os.environ.get("wps_sid", "")
    airsheet.init(file_id=file_id, wps_sid=file_wps_sid, sheet_name="报告")
    write_with_retry(
        [is_test],
        f"B6",
        sheet_name="报告",
    )
    write_with_retry(
        [branch],
        f"B7",
        sheet_name="报告",
    )

    # 创建API实例

    api = Copilot(
        is_test=is_test,
        wps_sid=run_wps_sid,
        custom_headers={"X-Cc-Region": branch},
    )

    # 为run_one函数绑定参数
    def run_one_with_params(self, row):
        return run_one(
            self, row, api, default_question_config, 输出列编号, 返回列编号, 卡片列编号
        )

    for sheetname in sheet_names:
        ai = RunAi(
            file_id=file_id,
            sheetname=sheetname,
            must_have_columns=必须有的列名,
            skip_col_name=输出列名,
            clo_num_to_write=输出列编号,
            max_workers=10,
        )
        ai.run_one = MethodType(run_one_with_params, ai)
        ai.run()


if __name__ == "__main__":
    # 默认文件ID，用于直接运行脚本
    default_file_id = "canT6ZPrtNas"
    run_batch_verification(
        default_file_id,
        is_test=True,
        run_wps_sid="",
    )
    # c = api.history("8670977635057844")
    # print(c)
    # row = {"file_ids": '["crpyEFOkjTwQ"]'}
    # print(row_to_args(row, "file_ids", 1, is_json=True))
