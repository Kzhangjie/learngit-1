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
        send_report(file["file_id"], is_test=is_test, branch=branch, is_dev=True)  # type: ignore


main(False)
