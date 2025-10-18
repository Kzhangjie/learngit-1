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
from renfangchao.cc_server.as_utils import split_string

load_dotenv()


class RunCC(RunBase):

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
        self.case_id_col = "用例编号"
        super().__init__(
            file_id=file_id,
            sheetname=sheetname,
            must_have_columns=[self.case_id_col],
            skip_col_name=skip_col_name,
            clo_num_to_write=clo_num_to_write,
        )
        self.max_workers = max_workers
        self.api = Copilot(is_test=is_test, custom_headers=custom_headers)

    def insert_case(self, case, cases):
        if not self.skip_col_name or any(not d.get(self.skip_col_name) for d in case):
            cases.append(case)

    def filter_datas(self, datas):
        cases = []
        last_case = []
        datas = [d for d in datas if d.get(self.case_id_col)]

        for d in datas:
            if last_case and d.get(self.case_id_col) == last_case[0].get(
                self.case_id_col
            ):
                last_case.append(d)
            else:
                if last_case:
                    self.insert_case(last_case, cases)
                last_case = [d]

        if last_case:
            self.insert_case(last_case, cases)

        return cases

    def run(self, run_count=2000):
        # 设置最大行数据，防止太大
        datas = self.get_inputs()
        datas = self.filter_datas(datas)
        if run_count:
            datas = datas[:run_count]
        gc.collect()
        print(f"要处理{len(datas)}行数据")
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = [executor.submit(self.run_one, i) for i in datas]
            for future in tqdm(as_completed(futures), total=len(futures)):
                result = future.result()

    def run_one(self, rows):
        try:
            session_id = self.api.create_session()
            for row in rows:
                question = row.get("question", "").strip("ask:").strip()
                file_ids = row.get("file_ids", "").strip()
                file_ids = file_ids.split(",") if file_ids else []
                collect_ids = row.get("collect_ids", "").strip()
                collect_ids = collect_ids.split(",") if collect_ids else []
                command = row.get("command", "").strip()
                command_args = row.get("command_args", "").strip()
                command_args = json.loads(command_args) if command_args else {}
                group_id = row.get("group_id", "").strip()
                reference_search_id = row.get("reference_search_id", "").strip()
                events, request_id = self.api.completions(
                    session_id=session_id,
                    question=question,
                    file_ids=file_ids,
                    collect_ids=collect_ids,
                    command=command,
                    command_args=command_args,
                    group_id=group_id,
                    reference_search_id=reference_search_id,
                )
                evs = events[:1]
                pre_event = evs[-1]
                for e in events[1:]:
                    typ = e.event
                    data = e.data
                    if (
                        pre_event.event == "execution"
                        and pre_event.data["type"] == "text"
                        and typ == "execution"
                        and data["type"] == "text"
                    ):
                        pre_event.data["data"] += data["data"]
                    else:
                        evs.append(e)
                        pre_event = evs[-1]
                # print(111, evs)
                group_id = ""
                for ev in evs:
                    if ev.data.get("group_id"):
                        group_id = ev.data["group_id"]
                        break
                evs_dict = [ev.to_dict() for ev in evs]

                result = json.dumps(evs_dict, ensure_ascii=False, indent=2)
                r = [
                    "'" + str(session_id),
                    "'" + group_id,
                    request_id,
                ]
                r.extend(split_string(result))

                airsheet.write_xl(
                    r,
                    f'{self.clo_num_to_write}{row["row_index"]}',
                    sheet_name=self.sheetname,
                )
        except Exception as e:
            print(traceback.format_exception(e))
