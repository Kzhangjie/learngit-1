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
from renfangchao.cc_server.kae_util import Kae
from renfangchao.cc_server.as_utils import obj_to_strs
from renfangchao.cc_server.kae_logs_go import logger, parse_http_log_catch
from run_batch.run_ai import RunAi


class RunLog(RunAi):

    def __init__(
        self,
        file_id,
        sheetname,
        skip_col_name,
        clo_num_to_write,
        max_workers=1,
        env="gotest",
    ):
        super().__init__(
            file_id=file_id,
            sheetname=sheetname,
            must_have_columns=["x-request-id"],
            skip_col_name=skip_col_name,
            clo_num_to_write=clo_num_to_write,
            max_workers=max_workers,
        )
        self.kae = Kae(
            env=env, logger=logger, parse_http_log_catch=parse_http_log_catch
        )

    def run_one(self, row):
        try:
            request_id = row["x-request-id"]
            reqs = self.kae.get_session_reqs_go(request_id, 10000, wait=0)
            planners = [
                r
                for r in reqs
                if r["request"]["headers"]["Host"]
                in ["10.8.254.24:30818", "kmd-api.kas.wps.cn"]
                and (
                    r["request"]["url"].startswith("/kas")
                    or r["request"]["url"].startswith("/api")
                )
            ]
            minimaxs = [
                r
                for r in reqs
                if r["request"]["headers"]["Host"]
                in [
                    "api.minimax.chat",
                    "aigc-gateway-test.ksord.com",
                    "ai-copilot-gateway.ksord.com",
                ]
            ]
            pr = obj_to_strs(planners, with_start=True)
            mr = obj_to_strs(minimaxs, with_start=True)
            ar = obj_to_strs(reqs, indent=0, with_start=True, max_size=15)
            airsheet.write_xl(
                pr,
                f"{self.clo_num_to_write[0]}{row['row_index']}",
                sheet_name=self.sheetname,
            )
            airsheet.write_xl(
                mr,
                f"{self.clo_num_to_write[1]}{row['row_index']}",
                sheet_name=self.sheetname,
            )
            airsheet.write_xl(
                ar,
                f"{self.clo_num_to_write[2]}{row['row_index']}",
                sheet_name=self.sheetname,
            )

        except Exception as e:
            print(traceback.format_exception(e))
