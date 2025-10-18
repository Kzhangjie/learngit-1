import os

import requests

import airsheet
from run_batch.as_utils import get_df


def send(markdown, is_dev=False):
    dev_urls = [
        "https://365.kdocs.cn/woa/api/v1/webhook/send?key=16278d021548a90f0ce73db1ff948205"  # 个人
    ]
    urls = [
        "https://365.kdocs.cn/woa/api/v1/webhook/send?key=0f42fdc8a17d0e8d593effbd659fce78",  # 告警群
        "https://365.kdocs.cn/woa/api/v1/webhook/send?key=de9769e0dc8f61917329af273d09be32",  # 测试群
    ]
    if is_dev:
        urls = dev_urls
    data = {
        "msgtype": "markdown",
        "markdown": {"text": markdown},
    }
    for url in urls:
        resp = requests.post(
            url, json=data, headers={"Content-Type": "application/json"}
        )
        print(resp.text)


def send_report(file_id, is_test=True, branch="", is_dev=False):
    sheet_names = ["thinking_disabled", "thinking_enabled", "重试"]
    # sheet_names = ["thinking_enabled"]

    results = []
    total_pass_cnt = 0
    total_fail_cnt = 0
    total_run_cnt = 0
    total_all_cnt = 0
    failed_questions_by_端 = {}
    retry_failed_questions_by_端 = {}
    retry_results = None

    for sheet_name in sheet_names:
        df = get_df(file_id, sheet_name, drop_na=False)  # type: ignore
        print(f"Processing sheet: {sheet_name}, rows: {df.shape[0]}")
        # 打印表头
        print(df.columns.tolist())
        pass_cnt = df[df["是否通过"] == "pass"].shape[0]
        fail_cnt = df[df["是否通过"] == "fail"].shape[0]
        run_cnt = pass_cnt + fail_cnt
        all_cnt = df[df["问题"].notna()].shape[0]
        通过率 = pass_cnt / all_cnt if all_cnt > 0 else 0
        完成进度 = run_cnt / all_cnt if all_cnt > 0 else 0

        result_data = {
            "sheet": sheet_name,
            "pass_cnt": pass_cnt,
            "fail_cnt": fail_cnt,
            "run_cnt": run_cnt,
            "all_cnt": all_cnt,
            "通过率": 通过率,
            "完成进度": 完成进度,
        }

        if sheet_name == "重试":
            retry_results = result_data
        else:
            results.append(result_data)
            total_pass_cnt += pass_cnt
            total_fail_cnt += fail_cnt
            total_run_cnt += run_cnt
            total_all_cnt += all_cnt

        if fail_cnt > 0:
            failed_df = df[df["是否通过"] == "fail"]
            for _, row in failed_df.iterrows():
                端 = row.get("端", "未知")
                问题 = row["问题"]
                if sheet_name == "重试":
                    if 端 not in retry_failed_questions_by_端:
                        retry_failed_questions_by_端[端] = []
                    retry_failed_questions_by_端[端].append(问题)
                else:
                    if 端 not in failed_questions_by_端:
                        failed_questions_by_端[端] = []
                    failed_questions_by_端[端].append(问题)

    # 计算总计
    total_通过率 = total_pass_cnt / total_all_cnt if total_all_cnt > 0 else 0
    total_完成进度 = total_run_cnt / total_all_cnt if total_all_cnt > 0 else 0

    # 判断是否通过：区分首次通过和重试通过
    is_first_pass = total_pass_cnt == total_all_cnt
    is_retry_pass = (
        retry_results
        and retry_results["fail_cnt"] == 0
        and retry_results["all_cnt"] > 0
    )
    is_all_pass = is_first_pass or is_retry_pass

    # 整理成 markdown
    md = "# "
    md += "测试环境" if is_test else "灰度环境"
    md += f"  {branch} 分支 " if is_test else ""

    if is_first_pass:
        md += "一次通过"
    elif is_retry_pass:
        md += "重试通过"
    else:
        md += "不通过"

    md += "\n\n"

    # 首次结果
    md += "## 首次结果\n"
    md += "| sheet | 成功数| 失败数 | 通过率 |\n"
    md += "| --- | --- |--- | --- |\n"
    for r in results:
        md += f"| {r['sheet']} | {r['pass_cnt']} | {r['fail_cnt']} | {r['通过率']:.2%} |\n"
    md += f"| **总计** | {total_pass_cnt} | {total_fail_cnt} | {total_通过率:.2%} |\n"

    # 首次失败问题列表
    if failed_questions_by_端:
        md += "\n\n## 首次失败问题列表\n"
        for 端, questions in failed_questions_by_端.items():
            unique_questions = list(set(questions))  # 去重
            md += f"### {端}\n"
            for question in unique_questions:
                md += f"- {question}\n"
            md += "\n"

    # 重试结果
    if retry_results and retry_results["all_cnt"] > 0:
        md += "\n\n## 重试结果\n"
        md += "| sheet | 成功数| 失败数 | 通过率 |\n"
        md += "| --- | --- |--- | --- |\n"
        md += f"| {retry_results['sheet']} | {retry_results['pass_cnt']} | {retry_results['fail_cnt']} | {retry_results['通过率']:.2%} |\n"

    # 重试失败问题列表
    if retry_failed_questions_by_端:
        md += "\n\n## 重试失败问题列表\n"
        for 端, questions in retry_failed_questions_by_端.items():
            unique_questions = list(set(questions))  # 去重
            md += f"### {端}\n"
            for question in unique_questions:
                md += f"- {question}\n"
            md += "\n"

    link_url = f"https://365.kdocs.cn/l/{file_id}"
    md += f"\n\n[查看详情]({link_url})\n"
    print(md)
    send(md, is_dev)


if __name__ == "__main__":
    send_report("cfuaUo5Rd5e8", is_test=False, branch="", is_dev=True)  # 测试用的文件ID
