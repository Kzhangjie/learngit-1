import airsheet
import traceback
from concurrent.futures import ThreadPoolExecutor
import traceback
from run_batch.run_base import RunBase
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed
import gc
from renfangchao.cc_server.copilot_api import Copilot
import json
from dotenv import load_dotenv

load_dotenv()

from renfangchao.cc_server.run_cc import RunCC
from renfangchao.cc_server.as_utils import split_string


class RunMsg(RunCC):

    def __init__(
        self,
        file_id,
        sheetname,
        skip_col_name,
        clo_num_to_write,
        max_workers=6,
        is_test=True,
        custom_headers={},
    ):
        super().__init__(
            file_id=file_id,
            sheetname=sheetname,
            skip_col_name=skip_col_name,
            clo_num_to_write=clo_num_to_write,
            max_workers=max_workers,
            is_test=is_test,
            custom_headers=custom_headers,
        )

    def insert_case(self, case, cases):
        if not self.skip_col_name or not case[-1].get(self.skip_col_name):
            cases.append(case)

    def run_one(self, rows):
        try:
            row = rows[0]
            session_id = row["resp_session_id"]
            msgs = self.api.get_messages(session_id)
            result = json.dumps(msgs, ensure_ascii=False, indent=2)
            r = split_string(result)
            for cr in rows:
                airsheet.write_xl(
                    r,
                    f"{self.clo_num_to_write}{cr['row_index']}",
                    sheet_name=self.sheetname,
                )
        except Exception as e:
            print(traceback.format_exception(e))
