import airsheet
import traceback
from utils.gateway_api_v2_stream import GateWayAPI
from concurrent.futures import ThreadPoolExecutor
import traceback
from run_batch.run_base import RunBase
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed
import gc


class RunAi(RunBase):
    def __init__(
        self,
        file_id,
        sheetname,
        must_have_columns,
        skip_col_name,
        clo_num_to_write,
        max_workers=6,
        wps_sid=None,
    ):
        super().__init__(
            file_id=file_id,
            sheetname=sheetname,
            must_have_columns=must_have_columns,
            skip_col_name=skip_col_name,
            clo_num_to_write=clo_num_to_write,
            wps_sid=wps_sid,
        )
        self.max_workers = max_workers
        self.api = GateWayAPI(retry_count=10)
        self.prompt = None
        self.prompt_param_colname_map = {}
        self.model = None
        self.system_setting = None
        self.version = None
        self.llm_arguments_map = {}
        self.llm_version_map = {}
        self.mode_col_name = "模型"
        self.sec_text = {"from": ""}

    def filter_datas(self, datas):
        if self.skip_col_name:
            return [d for d in datas if not d[self.skip_col_name]]
        else:
            return datas

    def run(self, run_count=2000):
        # 设置最大行数据，防止太大
        datas = self.get_inputs()
        datas = self.filter_datas(datas)
        if run_count:
            datas = datas[:run_count]
        gc.collect()
        print(f"要处理{len(datas)}行数据")
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = [executor.submit(self.run_one_try, i) for i in datas]
            for future in tqdm(as_completed(futures), total=len(futures)):
                result = future.result()

    def run_one_try(self, row):
        try:
            self.run_one(row)
        except Exception as e:
            print(traceback.format_exception(e))

    def run_one(self, row):
        try:
            p = self.row_to_prompt(row)
            model, system_setting, llm_arguments, version = self.row_to_model_info(row)
            success, result, response = self.api.chat_text(
                model=model,
                text=p,
                context=system_setting,
                llm_arguments=llm_arguments,
                version=version,
                sec_text=self.sec_text,
            )
            if result.startswith("-"):
                result = "'" + result
            airsheet.write_xl(
                [result],
                f'{self.clo_num_to_write}{row["row_index"]}',
                sheet_name=self.sheetname,
            )
        except Exception as e:
            print(traceback.format_exception(e))

    def row_to_prompt(self, row):
        p = self.prompt
        for k, v in self.prompt_param_colname_map.items():
            p = p.replace("{^" + k + "^}", str(row[v]))
        return p

    def row_to_model_info(self, row):
        model = self.model or row[self.mode_col_name]
        system_setting = self.system_setting
        llm_arguments = self.llm_arguments_map.get(model, {})
        version = self.llm_version_map.get(model, "")
        return model, system_setting, llm_arguments, version
