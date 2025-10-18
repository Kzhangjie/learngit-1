import requests
import os
from typing import Optional, Dict, List, Any
from airsheet_sdk.airsheet.util import parse_range_to_index


class WebOfficeError(Exception):
    """
    定义内部错误
    TODO liangzuobin 看看有没有其它更好的方式隐藏掉内部的异常
    """

    def __init__(self, error_message):
        self.error_message = error_message

    def __str__(self):
        return f"Request WebOfficeAPI failed: {self.error_message}"


class Range:
    def __init__(
        self,
        rows_from: Optional[int],
        rows_to: Optional[int],
        columns_from: Optional[int],
        columns_to: Optional[int],
    ) -> None:
        self.rows_from = rows_from
        self.rows_to = rows_to
        self.columns_from = columns_from
        self.columns_to = columns_to

    @classmethod
    def parse(cls, range: str = '') -> 'Range':
        (
            rows_from,
            rows_to,
            columns_from,
            columns_to,
        ) = parse_range_to_index(range=range)

        return cls(
            rows_from=rows_from,
            rows_to=rows_to,
            columns_from=columns_from,
            columns_to=columns_to,
        )

    @classmethod
    def from_dict(cls, data: Dict = {}) -> 'Range':
        return cls(
            rows_from=data.get("rowFrom"),
            rows_to=data.get("rowTo"),
            columns_from=data.get("colFrom"),
            columns_to=data.get("colTo"),
        )

    def set_none_value_with_others(self, other: 'Range') -> 'Range':
        return Range(
            rows_from=self.rows_from if self.rows_from is not None else other.rows_from,
            rows_to=self.rows_to if self.rows_to is not None else other.rows_to,
            columns_from=self.columns_from if self.columns_from is not None else other.columns_from,
            columns_to=self.columns_to if self.columns_to is not None else other.columns_to,
        )

    def total_rows(self) -> int:
        rows_from = 0 if self.rows_from is None else self.rows_from
        rows_to = 0 if self.rows_to is None else self.rows_to
        return abs(rows_to - rows_from) + 1

    def total_columns(self) -> int:
        columns_from = 0 if self.columns_from is None else self.columns_from
        columns_to = 0 if self.columns_to is None else self.columns_to
        return abs(columns_to - columns_from) + 1

    def single_cell(self) -> bool:
        return self.total_columns() == 1 and self.total_rows() == 1

    def __str__(self) -> str:
        return f"rows:[{self.rows_from},{self.rows_to}], columns:[{self.columns_from},{self.columns_to}]"

    def __repr__(self) -> str:
        return self.__str__()


class ValueInfo:
    def __init__(self, t: str = "", v: Any = None) -> None:
        self.t = t
        self.v = v

    @classmethod
    def from_dict(cls, data: dict = {}) -> 'ValueInfo':
        t = data.get("type", "")
        v = data.get("value", "")

        return cls(t, v)


class Cell:
    range: Range = None
    cell_text: str  # 单元格显示值

    # original
    original_row: int = 0
    original_column: int = 0
    original_value: str = ''

    is_cell_pic: bool = False
    number_format: str = ""

    info: ValueInfo = None,

    def __init__(self, cell_text: str = '', range: Range = None):
        self.cell_text = cell_text
        self.range = range

    @classmethod
    def from_dict(cls, data: dict = {}) -> 'Cell':
        cell = cls(
            cell_text=data.get("cellText", ""),
            range=Range.from_dict(data),
        )

        cell.original_row = data.get("originRow")
        cell.original_column = data.get("originCol")
        cell.original_value = data.get("originalCellValue")

        cell.is_cell_pic = data.get("isCellPic")
        cell.number_format = data.get("numFormat")

        cell.info = ValueInfo.from_dict(data.get("understandableType", {}))

        return cell

    def __str__(self) -> str:
        return f"Cell(range={self.range}, cell_text={self.cell_text})"

    def __repr__(self) -> str:
        return self.__str__()

    def value_on_type(self) -> Any:
        """
        内核返回的数据是带有类型的：
        type == double 返回的是数值类型
        type == bool 返回的是布尔类型
        其它返回的都是字符串
        """
        return self.cell_text if self.info is None or self.info.t == "" else self.info.v


class WorkSheet:
    sheet_name: str = ''
    sheet_id: int = 0
    sheet_index: int = 0
    sheet_type: str = ''

    hidden: bool = False
    protected: bool = False

    # used range
    range: Range = None

    def __init__(
        self,
        sheet_name: str,
        sheet_id: int,
        sheet_index: int,
        sheet_type: Optional[str] = '',
        hidden: Optional[bool] = False,
        protected: Optional[bool] = False,
        range: Optional[Range] = None,
    ) -> None:
        self.sheet_name = sheet_name
        self.sheet_id = sheet_id
        self.sheet_index = sheet_index
        self.sheet_type = sheet_type
        self.hidden = hidden
        self.protected = protected
        self.range = range

    @classmethod
    def from_dict(cls, data: dict) -> 'WorkSheet':
        sheet = cls(
            sheet_name=data.get("sheetName"),
            sheet_id=data.get("sheetId"),
            sheet_index=data.get("sheetIdx"),
            sheet_type=data.get("sheetType", ""),
            hidden=not data.get("isVisible", True),
            protected=data.get("isProtected", False),
            range=Range.from_dict(data),
        )
        return sheet


class Client:
    def __init__(self, wps_sid: str, weboffice_branch: str):
        weboffice_host = os.getenv("weboffice_host", "https://www.kdocs.cn")
        session = requests.session()

        session.headers.update({
            "origin": weboffice_host,
            "x-user-token": wps_sid,
        })

        if weboffice_branch:
            session.cookies.set("weboffice_branch", weboffice_branch, domain=".kdocs.cn")
            session.cookies.set("weboffice_branch", weboffice_branch, domain=".wps.cn")

        self._host = weboffice_host
        self._session = session

    def do_core_exec(self, file_id: str, args: Optional[Dict]) -> Dict:
        url = f"{self._host}/api/v3/office/file/{file_id}/core/execute"

        try:
            response = self._session.post(url=url, json=args, timeout=600)
        except requests.exceptions.RequestException as e:
            raise WebOfficeError(f"send request failed: {e}")

        try:
            body = response.json()
        except requests.exceptions.JSONDecodeError:
            raise WebOfficeError(f"Response[{response.status_code}]")

        result = body.get("result", "unknown")
        if str(result).lower() != "ok":
            raise WebOfficeError(result)

        return body

    def get_worksheets(self, file_id: str) -> List[WorkSheet]:
        response = self.do_core_exec(file_id, args={
            "command": "http.et.getSheetsInfo",
            "param": {},
        })

        try:
            dicts = response.get("detail").get("sheetsInfo")
            sheets = [WorkSheet.from_dict(x) for x in dicts if x is not None]
            sheets = sorted(sheets, key=lambda sheet: sheet.sheet_index)
            return sheets
        except:
            raise SystemError("invalid response")

    def get_range_cells(self, file_id: str, sheet_id: int, range: Range) -> List[Cell]:
        response = self.do_core_exec(file_id=file_id, args={
            "command": "http.et.getRangeData",
            "param": {
                "sheetId": sheet_id,
                "range": {
                    "rowFrom": range.rows_from,
                    "rowTo": range.rows_to,
                    "colFrom": range.columns_from,
                    "colTo": range.columns_to,
                },
            },
        })

        try:
            cells = list(response.get("detail").get("rangeData"))
            cells = [Cell.from_dict(x) for x in cells if x is not None]

            # 排序，确保每一列的行、列的顺序是对的
            return sorted(cells, key=lambda x: (x.range.rows_from, x.range.columns_from))
        except:
            raise SystemError("Invalid response from WebOffice")

    def update_range_cells(self, file_id: str, sheet_id: int, cells: List[Cell]):
        if len(cells) == 0:
            raise ValueError("Invalid cells for update")

        self.do_core_exec(file_id=file_id, args={
            "command": "http.et.updateRangeData",
            "param": {
                "sheetId": sheet_id,
                "rangeData": [{
                    "opType": "formula",
                    "rowFrom": cell.range.rows_from,
                    "rowTo": cell.range.rows_to,
                    "colFrom": cell.range.columns_from,
                    "colTo": cell.range.columns_to,
                    "formula": f"{cell.cell_text}",
                } for cell in cells],
            }
        })

    def add_worksheet(self,
                      file_id: str,
                      sheet_name: Optional[str] = None,
                      after_sheet_id: Optional[int] = None) -> int:

        param = {
            "type": "xlWorksheet",
            "defColWidth": 1335,
        }
        if after_sheet_id is None:
            param["end"] = True
        else:
            param["after"] = {"sheetId": after_sheet_id}

        resp = self.do_core_exec(file_id=file_id, args={
            "command": "http.et.addSheet",
            "param": param,
        })

        new_sheet_id = resp.get("detail").get("sheetId")

        if sheet_name is not None and sheet_name != "":
            self.update_worksheet_name(file_id=file_id,
                                       sheet_id=new_sheet_id,
                                       sheet_name=sheet_name)

        return new_sheet_id

    def update_worksheet_name(self, file_id: str, sheet_id: int, sheet_name: str) -> None:
        self.do_core_exec(file_id=file_id, args={
            "command": "http.et.addSheet",
            "param": {
                "sheetId": sheet_id,
                "name": sheet_name,
            },
        })
