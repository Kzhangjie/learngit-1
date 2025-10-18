import re
import pandas as pd
from typing import Optional, List, Dict, Union, TypeVar
from airsheet_sdk.airsheet import playground, weboffice, util


book_url_pattern = r"(https://)?(web.wps.cn|www.kdocs.cn|kdocs.cn)/(view/)?(p/([0-9]+)|l/([0-9a-zA-Z]+))(\?.*)?$"


def _extrace_file_id_from_book_url(book_url: str) -> str:
    book_url = book_url.strip()
    group = re.findall(book_url_pattern, book_url)
    if len(group) >= 7:
        s = group[5] if group[5] != "" else group[6]
        if s != "":
            return s
    raise ValueError(f"invalid book_url: {book_url}")


def _replace_negative_to_none(v: Optional[int]) -> Optional[int]:
    """
    为了兼容 cgo 里 int 初始值设置为 -1 的问题
    以后准备改掉 cgo 里的实现
    """
    if v is None:
        return None
    if v == -1:
        return None
    return v


def xl(
    range_desc: str = "",
    headers: bool = False,
    sheet_name: List[str] = None,
    book_url: str = "",
    start_row: Optional[int] = None,
    end_row: Optional[int] = None,
    start_column: Optional[int] = None,
    end_column: Optional[int] = None,
) -> Union[pd.DataFrame, Dict[str, pd.DataFrame]]:
    start_row = _replace_negative_to_none(start_row)
    end_row = _replace_negative_to_none(end_row)
    start_column = _replace_negative_to_none(start_column)
    end_column = _replace_negative_to_none(end_column)

    if range_desc != "":
        rng = weboffice.Range.parse(range=range_desc)
    else:
        rng = weboffice.Range(start_row, end_row, start_column, end_column)

    file_id = playground.current_file_id()
    if book_url != "":
        file_id = _extrace_file_id_from_book_url(book_url=book_url)

    wb = playground.get_workbook(file_id=file_id)

    if sheet_name is None:
        sheet_name = [sheet.sheet_info.sheet_name for sheet in wb.worksheets]

    sheet_name = [
        name if name != "" else playground.activate_sheet() for name in sheet_name
    ]

    # 先遍历一次，用来判断 sheet 是否存在
    sheets = []
    for name in sheet_name:
        sheet = wb.get_worksheet(name)
        if sheet is None:
            raise ValueError(f"sheet with name {name} not exist")
        sheets.append(sheet)

    ds = {}
    for sheet in sheets:
        ds[sheet.sheet_info.sheet_name] = _compose_dataframe_for_sheet(
            sheet, rng, headers
        )
    # ds = {sheet.sheet_info.sheet_name: _compose_dataframe_for_sheet(sheet, rng, headers) for sheet in sheets}

    if len(sheet_name) > 0:
        return ds.get(sheet_name[0])
    return ds


def _compose_dataframe_for_sheet(
    sheet: playground.WorkSheet, query_range: weboffice.Range, headers: bool = False
) -> pd.DataFrame:
    query_range = query_range.set_none_value_with_others(sheet.sheet_info.range)

    cells = sheet.get_range_cells(query_range=query_range)

    # 获取表头的参数的默认值
    with_headers, headers_row = (True, 1) if headers else (False, 0)

    header_index: int = None
    header_columns: List[str] = None

    default_cell_value = float("nan")
    total_rows = query_range.total_rows()
    total_columns = query_range.total_columns()

    # 初始化用于构造 DataFrame 的 data
    data = [
        [default_cell_value for _ in range(0, total_columns)] for _ in range(total_rows)
    ]

    # 初始化 DataFrame 的 columns
    if with_headers:
        # 当前 cells 里的第 headers_row 行为表头
        header_index = query_range.rows_from + util.number_to_index(headers_row)
        header_columns = ["" for _ in range(0, total_columns)]

    for cell in cells:
        column_index = cell.range.columns_from - query_range.columns_from

        if cell.range.rows_from == header_index:
            header_columns[column_index] = cell.value_on_type()
        else:
            row_index = cell.range.rows_from - query_range.rows_from
            data[row_index][column_index] = cell.value_on_type()

    # 有表头，数据区域的长度要 -1
    if header_index is not None:
        data = (
            data[1:]
            if header_index == 0
            else data[:header_index] + data[header_index + 1:]
        )

    return pd.DataFrame(data=data, columns=header_columns)


TypeVarStrOrList = TypeVar("TypeVarStrOrList", str, List[str])


def write_xl(
    cells: List[object],
    num_rows,
    range_desc,
    new_sheet: bool,
    sheet_name: TypeVarStrOrList,
    overfill: bool = False,
    book_url: str = "",
    start_row: int = -1,
    end_row: int = -1,
    start_column: int = -1,
    end_column: int = -1,
) -> None:
    start_row = _replace_negative_to_none(start_row)
    end_row = _replace_negative_to_none(end_row)
    start_column = _replace_negative_to_none(start_column)
    end_column = _replace_negative_to_none(end_column)

    num_columns = len(cells) / num_rows
    if len(cells) != num_rows * num_columns:
        raise ValueError("invalid num_rows for cells")

    if range_desc != "":
        rng = weboffice.Range.parse(range_desc)
    else:
        if end_row is None:
            end_row = start_row
        if end_column is None:
            end_column = start_column

        rng = weboffice.Range(
            rows_from=start_row,
            rows_to=end_row,
            columns_from=start_column,
            columns_to=end_column,
        )

    file_id = playground.current_file_id()
    if book_url != "":
        file_id = _extrace_file_id_from_book_url(book_url)

    if new_sheet:
        # 如果是 new_sheet 尝试设置一下默认值 A1
        rng = rng.set_none_value_with_others(weboffice.Range(0, 0, 0, 0))

    if num_rows == 1 and len(cells) != 1:
        if rng.single_cell():
            """
            do nothing
            """
        elif rng.total_rows() == 1 and rng.total_columns() > 1:
            """
            do nothing
            """
        elif rng.total_columns() > 1 and rng.total_rows() > 1:
            num_columns, num_rows = num_rows, num_columns
        elif not overfill:
            num_rows, num_columns = rng.total_rows(), rng.total_columns()
        else:
            raise ValueError(
                f"the range [{rng}] is too small for your ddata[{len(cells)}], but it cannot be inferred which direction to overfill"
            )

    if new_sheet:
        sheet = playground.add_worksheet(file_id=file_id, sheet_name=sheet_name)
    else:
        if sheet_name == "":
            sheet_name = playground.activate_sheet()
        sheet = playground.get_workbook(file_id).get_worksheet(sheet_name)

    cells_to_update = []
    column, row, idx = 0, 0, 0
    while idx < len(cells):
        if column < num_columns:
            cell = cells[idx]
            tr = row + rng.rows_from
            tc = column + rng.columns_from

            cell_text = str(getattr(cell, "v", ""))
            r = weboffice.Range(tr, tr, tc, tc)
            cells_to_update.append(weboffice.Cell(cell_text=cell_text, range=r))

            column = column + 1
            idx = idx + 1
        else:
            row = row + 1
            column = 0

    sheet.update_range_cells(cells=cells_to_update)
