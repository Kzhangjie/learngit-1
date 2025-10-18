import airsheet
import traceback
from run_batch.run_base import RunBase
import gc


class RunCode(RunBase):
    def __init__(
        self,
        file_id,
        sheetname,
        must_have_columns,
        skip_col_name,
        clo_num_to_write,
        to_sheetname=None,
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
        self.to_sheetname = to_sheetname or sheetname
        self.batch_size = 3000

    def batch_by_continuous_id_with_result(self, lst):
        if not lst:
            return []

        batches = []
        current_batch = [lst[0]]
        start_id = lst[0][0]

        for i in range(1, len(lst)):
            current_item = lst[i]
            current_id = current_item[0]
            previous_item = lst[i - 1]
            previous_id = previous_item[0]

            # 如果当前id和前一个id不连续或当前批次已满，则开始新的批次
            if (
                int(current_id) != int(previous_id) + 1
                or len(current_batch) >= self.batch_size
            ):
                # 使用元组(id, [batch_results])添加批次
                batches.append((start_id, [item[1] for item in current_batch]))
                current_batch = [current_item]
                start_id = current_id
            else:
                current_batch.append(current_item)

        # 添加最后一批
        batches.append((start_id, [item[1] for item in current_batch]))

        return batches

    def run(self, run_count=2000):
        # 设置最大3000行数据，防止太大
        datas = self.get_inputs()
        if self.skip_col_name:
            datas = [d for d in datas if not d[self.skip_col_name]]
        if run_count:
            datas = datas[:run_count]
        gc.collect()
        print(f"要处理{len(datas)}行数据")
        results_with_id = []
        if not datas:
            return
        row_num = datas[0]["row_index"]
        for d in datas:
            try:
                result = self.run_one(d)
                results_with_id.append((d["row_index"], result))
            except Exception as e:
                print(f"处理{d}发生异常")
                print(traceback.format_exception(e))
        batchs = self.batch_by_continuous_id_with_result(results_with_id)
        for batch in batchs:
            row_num, datas = batch
            try:
                # print(1111,f'{self.clo_num_to_write}{row_num}')
                airsheet.write_xl(
                    datas,
                    f"{self.clo_num_to_write}{row_num}",
                    sheet_name=self.to_sheetname,
                )
            except Exception as e:
                print(traceback.format_exception(e))

    def run_one(self, func, row):
        return func(row)
