import time

import requests
import schedule

import airsheet
from renfangchao.verify.file_operations import copy_file
from renfangchao.verify.gen_1_answer import run_batch_verification
from renfangchao.verify.rerun import copy_failed_cases
from renfangchao.verify.send_report import send_report
from run_batch.as_utils import get_df


def main(is_test=True, branch="master"):
    file = copy_file(is_test)
    if file:
        run_batch_verification(file["file_id"], is_test=is_test, branch=branch)
        copy_failed_cases(file["file_id"])
        run_batch_verification(
            file["file_id"],
            is_test=is_test,
            branch=branch,
            sheet_names=["重试"],
        )
        send_report(file["file_id"], is_test=is_test, branch=branch)  # type: ignore


def scheduled_task():
    """定时任务函数"""
    print(f"开始执行定时任务 - {time.strftime('%Y-%m-%d %H:%M:%S')}")
    main()


def scheduled_task_test():
    """测试环境定时任务函数"""
    print(f"开始执行测试环境定时任务 - {time.strftime('%Y-%m-%d %H:%M:%S')}")
    main(is_test=True)


def scheduled_task_prod():
    """灰度环境定时任务函数"""
    print(f"开始执行灰度环境定时任务 - {time.strftime('%Y-%m-%d %H:%M:%S')}")
    main(is_test=False)


if __name__ == "__main__":
    # 设置定时任务 - 每天的9点、10点、16点、21点执行
    # schedule.every().day.at("09:00").do(scheduled_task_test)
    # schedule.every().day.at("10:00").do(scheduled_task_test)
    # schedule.every().day.at("14:00").do(scheduled_task_test)
    # schedule.every().day.at("21:00").do(scheduled_task_test)

    schedule.every().day.at("10:00").do(scheduled_task_prod)
    # schedule.every().day.at("10:00").do(scheduled_task_prod)
    schedule.every().day.at("16:00").do(scheduled_task_prod)
    # schedule.every().day.at("21:00").do(scheduled_task_prod)

    print("定时任务已启动，每天10点、16点、21点执行测试和灰度环境任务...")
    print("按 Ctrl+C 停止程序")

    # 先执行一次
    # scheduled_task_test()
    # scheduled_task_prod()

    # 持续运行定时任务
    while True:
        schedule.run_pending()
        time.sleep(60)  # 每分钟检查一次
