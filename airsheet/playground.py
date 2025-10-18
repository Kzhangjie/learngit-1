import threading
from typing import List
from airsheet import weboffice


class WorkSheet:
    def __init__(self, file_id: str, sheet: weboffice.WorkSheet):
        self.file_id = file_id
        self.sheet_info = sheet

    def get_range_cells(self, query_range: weboffice.Range):
        return _weboffice.get_range_cells(
            file_id=self.file_id, sheet_id=self.sheet_info.sheet_id, range=query_range
        )

    def update_range_cells(self, cells: List[weboffice.Cell]):
        return _weboffice.update_range_cells(
            file_id=self.file_id, sheet_id=self.sheet_info.sheet_id, cells=cells
        )


class WorkBook:
    def __init__(
        self,
        file_id: str,
        office_type: str = "",  # 暂时不需要，后边看情况添加一个获取 md 的能力
        worksheets: List[WorkSheet] = [],
    ):
        self.file_id = file_id
        self.office_type = office_type
        self.worksheets = worksheets

    def get_worksheet(self, sheet_name: str) -> WorkSheet:
        for sheet in self.worksheets:
            if sheet.sheet_info.sheet_name == sheet_name:
                return sheet
        return None


class Playground:
    def __init__(self, file_id: str, sheet_name: str):
        self.lock = threading.Lock()
        self.current_file_id = file_id
        self.activate_sheet = sheet_name
        self.workbooks = {}

    def get_workbook_locked(self, file_id: str, refresh: bool) -> WorkBook:
        if not refresh:
            wb = _playground.workbooks.get(file_id, None)
            if wb is not None:
                return wb

        worksheets = _weboffice.get_worksheets(file_id=file_id)
        worksheets = [WorkSheet(file_id=file_id, sheet=sheet) for sheet in worksheets]
        wb = WorkBook(file_id=file_id, worksheets=worksheets)
        _playground.workbooks[file_id] = wb
        return wb


_playground: Playground = None
_weboffice: weboffice.Client = None


def init(wps_sid: str, weboffice_branch: str, file_id: str, sheet_name: str):
    global _playground, _weboffice
    _playground = Playground(file_id=file_id, sheet_name=sheet_name)
    _weboffice = weboffice.Client(wps_sid=wps_sid, weboffice_branch=weboffice_branch)
    return _playground


def current_file_id() -> str:
    return _playground.current_file_id


def activate_sheet() -> str:
    return _playground.activate_sheet


def get_workbook(file_id: str) -> WorkBook:
    with _playground.lock:
        return _playground.get_workbook_locked(file_id, False)


def add_worksheet(file_id: str, sheet_name: str) -> WorkSheet:
    with _playground.lock:
        wb = _playground.get_workbook_locked(file_id, False)

        after_sheet_id = None
        if wb.file_id == _playground.current_file_id:
            after_sheet_id = wb.get_worksheet(
                _playground.activate_sheet
            ).sheet_info.sheet_id

        new_sheet_id = _weboffice.add_worksheet(
            file_id=file_id, sheet_name=sheet_name, after_sheet_id=after_sheet_id
        )

        wb = _playground.get_workbook_locked(file_id, True)

        for sheet in wb.worksheets:
            if sheet.sheet_info.sheet_id == new_sheet_id:
                return sheet
        raise SystemError(
            f"no new sheet found in workbook, new sheet_id: {new_sheet_id}"
        )
