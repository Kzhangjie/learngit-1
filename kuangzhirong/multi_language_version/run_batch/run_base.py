from abc import abstractmethod
from utils_lingxi import constants as constants

from airsheet_sdk import airsheet


class RunBase:
    def __init__(
        self,
        file_id,
        sheetname,
        must_have_columns,
        skip_col_name,
        clo_num_to_write,
        wps_sid=None,
    ):
        self.file_id = file_id
        self.sheetname = sheetname
        self.must_have_columns = must_have_columns
        self.skip_col_name = skip_col_name
        self.clo_num_to_write = clo_num_to_write
        self.wps_sid = wps_sid or constants.WPS_SID

    def get_inputs(self):
        airsheet.init(
            file_id=self.file_id, wps_sid=self.wps_sid, sheet_name=self.sheetname
        )
        df = airsheet.xl("A:FZ", headers=True, sheet_name=[self.sheetname])
        columns_to_drop = [col for col in df.columns if col == "" or col is None]
        df = df.drop(columns=columns_to_drop)
        for col in self.must_have_columns:
            df = df.dropna(subset=[col])
        df["row_index"] = df.index + 2
        df.fillna("", inplace=True)
        datas = df.to_dict(orient="records")
        return datas

    @abstractmethod
    def run_code(self):
        raise NotImplementedError
