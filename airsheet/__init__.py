# local package
from airsheet.hijack import xl as hijack_xl, write_xl as hijack_write_xl
from airsheet.util import *
from airsheet.playground import init as playground_init
from airsheet.weboffice import *

from pandas.api.extensions import (
    register_extension_dtype,
    register_series_accessor,
    ExtensionDtype,
    ExtensionArray,
    ExtensionScalarOpsMixin,
)
from pandas._typing import (
    DtypeObj,
    type_t,
)
from bs4 import BeautifulSoup as __BeautifulSoup

__version__ = "0.0.1"


import base64 as __base64
import builtins as __builtins
import inspect as __inspect
import io as __io
import json as __json
import math as __math
import sys as __sys
import types as __types
from typing import Any, Optional, TypeVar, Union

import IPython.display as __ipython_display
import matplotlib as __mpl

# import matplotlib.figure as __figure
import matplotlib.artist as __artist
import numpy as __np
import pandas as __pd

__builtins.__xl = hijack_xl
__builtins.__write_xl = hijack_write_xl


# 因为所有的代码都是在一个 python 环境中运行的，这里的所有代码，都会影响用户的代码

# import seaborn as __sns

# DBT 自定义类型用，先不写别名了

__original_print = __builtins.print


class __Event:
    def __init__(self, event: str, data: str):
        self.event = event
        self.data = data


class __EchartsOptions:
    def __init__(self, chart: "__Base") -> None:
        self.chart = chart

    def _repr_echarts_(self):
        import datetime
        from typing import Iterable
        from pyecharts.commons import utils
        from pyecharts.options.series_options import BasicOpts
        from pyecharts.types import Sequence
        import simplejson

        # copy from pyecharts.charts.base.default, but change it when using JsCode
        def default(o):
            if isinstance(o, (datetime.date, datetime.datetime)):
                return o.isoformat()
            if isinstance(o, utils.JsCode):
                # return o.replace("\\n|\\t", "").replace(r"\\n", "\n").replace(r"\\t", "\t").js_code
                return ""
            if isinstance(o, BasicOpts):
                if isinstance(o.opts, Sequence):
                    return [utils.remove_key_with_none_value(item) for item in o.opts]
                else:
                    return utils.remove_key_with_none_value(o.opts)

        charts = self.chart if isinstance(self.chart, Iterable) else (self.chart,)
        for chart in charts:
            # 修改自 Base.dump_options
            options = simplejson.dumps(
                chart.get_options(), default=default, ignore_nan=True
            )
            data = {"options": simplejson.RawJSON(options)}
            yield simplejson.dumps(data)


# hook


def __setup():
    from pyecharts.charts.base import Base
    from pyecharts.components import Image
    from pyecharts.components.table import Table
    from pyecharts.charts.composite_charts.tab import Tab
    from pyecharts.charts.composite_charts.page import Page

    setattr(Image, "render", lambda self, *args, **kwargs: self.render_notebook())
    setattr(Table, "render", lambda self, *args, **kwargs: self.render_notebook())
    setattr(Tab, "render", lambda self, *args, **kwargs: self.render_notebook())
    setattr(Page, "render", lambda self, *args, **kwargs: self.render_notebook())
    setattr(Base, "render", lambda self, *args, **kwargs: self.render_notebook())

    setattr(
        Page,
        "render_notebook",
        lambda self, *args, **kwargs: __EchartsOptions(self._charts),
    )
    setattr(
        Base, "render_notebook", lambda self, *args, **kwargs: __EchartsOptions(self)
    )


__setup()


def __html_safe(html: str) -> str:
    soup = __BeautifulSoup(html, "html.parser")

    # 过滤掉 <style /> 和 <script />
    for element in soup.find_all():
        if element.name == "script" or element.name == "style":
            element.extract()
        else:
            # 过滤掉 DOM 上的:
            # 1. style 属性
            # 2. onxxx 属性
            element.attrs = {
                k: v
                for k, v in element.attrs.items()
                if not k.startswith("on") and not k == "style"
            }

    return str(soup)


def __get_formatter_method(obj, method_name):
    try:
        method = getattr(obj, method_name, None)
    except Exception:
        return None
    if __inspect.isclass(obj) and not isinstance(method, __types.MethodType):
        return None
    if not callable(method):
        return None
    return method


def __print_single_argument(obj) -> bool:
    # __original_print(f"_single_argument_display: {str(obj)} -> {dir(obj)}")
    if obj is None:
        obj = {"type": "image", "data": "None"}
        __original_print(__json.dumps(obj), flush=True)
        return True

    # xl 能返回 dict[str, pd.DataFrame] 了，单独处理一下打印问题
    if isinstance(obj, dict) and set(
        [isinstance(x, __pd.DataFrame) for x in obj.values()]
    ) == {True}:
        for k, v in obj.items():
            obj = {"type": "text", "data": k}
            __original_print(__json.dumps(obj, ensure_ascii=False), flush=True)
            __print_single_argument(v)
        return True

    # if isinstance(obj, __figure.Figure):
    if hasattr(obj, "savefig") and callable(getattr(obj, "savefig")):
        fd = __io.BytesIO()
        obj.savefig(fd)
        img = "data:image/png;base64," + __base64.b64encode(fd.getvalue()).decode(
            "utf-8"
        )
        fd.close()
        obj = {"type": "image", "data": img}
        __original_print(__json.dumps(obj), flush=True)
        return True

    if isinstance(obj, __artist.Artist):
        fig = obj.get_figure()
        __print_single_argument(fig)
        return True

    if isinstance(obj, __EchartsOptions):
        for options in obj._repr_echarts_():
            j = {"type": "echarts", "data": options}
            __original_print(__json.dumps(j), flush=True)
        return True

    # mimebundle > svg > png > jpeg > pretty > html > json
    if repr_method := __get_formatter_method(obj, "_repr_mimebundle_"):
        data = repr_method()
        if type(data) is tuple:
            data = data[0]
        if data is not None:
            for k, v in data.items():
                # loop just once
                img = f"{k};base64,{v}"
                obj = {"type": "image", "data": img}
                __original_print(__json.dumps(obj), flush=True)
                return True

    if repr_method := __get_formatter_method(obj, "_repr_svg_"):
        data = repr_method()
        if type(data) is tuple:
            data = data[0]
        if data is not None:
            img = "data:image/image/svg+xml;base64," + data
            obj = {"type": "image", "data": img}
            __original_print(__json.dumps(obj), flush=True)
            return True

    if repr_method := __get_formatter_method(obj, "_repr_png_"):
        data = repr_method()
        if type(data) is tuple:
            data = data[0]
        if data is not None:
            img = "data:image/png;base64," + data
            obj = {"type": "image", "data": img}
            __original_print(__json.dumps(obj), flush=True)
            return True

    if repr_method := __get_formatter_method(obj, "_repr_jpeg_"):
        data = repr_method()
        if type(data) is tuple:
            data = data[0]
        if data is not None:
            img = "data:image/jpeg;base64," + data
            obj = {"type": "image", "data": img}
            __original_print(__json.dumps(obj), flush=True)
            return True

    if repr_method := __get_formatter_method(obj, "_repr_pretty_"):
        data = repr_method()
        if data is not None:
            obj = {"type": "text", "data": data}
            __original_print(__json.dumps(obj), flush=True)
            return True

    if repr_method := __get_formatter_method(obj, "_repr_html_"):
        data = repr_method()
        if data is not None:
            data = __html_safe(
                data
            )  # fixme 这里以后在兼容 notebook 情况下可能有坑，比如 pyecharts 输出内容就是 script
            obj = {"type": "html", "data": data}
            __original_print(__json.dumps(obj), flush=True)
            return True

    if repr_method := __get_formatter_method(obj, "_repr_json_"):
        data = repr_method()
        if data is not None:
            obj = {"type": "text", "data": data}
            __original_print(__json.dumps(obj), flush=True)
            return True

    return False


def __print(*args, sep=" ", end="\n", file=None, flush=False):
    if len(args) == 0:
        __original_print(r'{"type": "text", "data": "\n"}', flush=True)
        return

    if len(args) > 1:
        data = [str(arg) for arg in args]
        data = data if sep is None else sep.join(data)
        data = data if end is None else data + end
        obj = {"type": "text", "data": data}
        __original_print(
            __json.dumps(obj, ensure_ascii=False),
            # file=file, # file argument not supported
            flush=True,
        )
        return

    if isinstance(args[0], __pd.Series):
        """
        通过 Series 构造一个 DataFrame，保持打印的样式一致
        默认给一个 Column 用来显示，应该是安全的，
        获取行数据 row = df.iloc[[1]] 返回的是 DataFrame
        """
        ok = __print_single_argument(__pd.DataFrame({"": args[0]}))
    else:
        ok = __print_single_argument(args[0])

    if not ok:
        data = str(args[0])
        data = data if end is None else data + end
        obj = {"type": "text", "data": data}
        __original_print(
            __json.dumps(obj, ensure_ascii=False),
            file=file,
            flush=True,
        )


# TODO liangzuobin 先不注入 builtins.print
# __builtins.print = __print


__original_display = __ipython_display.display


def __display(
    *objs,
    include=None,
    exclude=None,
    metadata=None,
    transient=None,
    display_id=None,
    raw=False,
    clear=False,
    **kwargs,
):
    if len(objs) == 0:
        return

    if len(objs) > 1:
        __print(objs)

    # 重要，如果最后一个表达式没有返回值不能打印
    if objs[0] is None:
        return

    __print(objs[0])


# python 没有 display 方法
display = __display
__builtins.display = __display

# 如果用 cgo 执行脚本的方式，这里需要放出来
__sys.displayhook = __display

# 替换 ipython 的 display
__ipython_display.display = __display
__mpl.use("module://matplotlib_inline.backend_inline")


# print(__mpl.get_backend())


def __except_hook(typ, val, tb):
    import traceback

    __original_print(
        "Traceback (most recent call last):", file=__sys.stderr, flush=True
    )

    frm = traceback.format_tb(tb, limit=10)
    frm = "".join(frm)
    __original_print(frm, file=__sys.stderr, flush=True)

    if typ is None:
        typ = "Exception"
    elif hasattr(typ, "__name__"):
        typ = typ.__name__
    else:
        typ = str(typ)

    __original_print(f"{typ}: {val}", file=__sys.stderr, flush=True)


__sys.excepthook = __except_hook

'''
def __trace_back(err):
    import sys
    import traceback

    try:
        lines = traceback.format_exception(err)
    except:
        # fallback
        lines = traceback.format_exception_only(err)

    excludes = [
        "sandbox/builtin.py",
        "__exec_script",
        "__compile_and_run_code",
    ]

    def contains_exclude(line):
        for exclude in excludes:
            if exclude in line:
                return True
        return False

    lines = [line for line in lines if not contains_exclude(line)]

    # 这里有问题
    __original_print(''.json(lines), file=sys.stderr, flush=True)


def __exec_script(source: str, filename: str = "<file>") -> int:
    """
    cgo main.main 触发执行用户脚本
    """
    import sys
    sys_displayhook = sys.displayhook
    sys.displayhook = __display
    try:
        __compile_and_run_code(source, filename)
        return 0
    except Exception as err:
        __trace_back(err)
    finally:
        sys.displayhook = sys_displayhook


def __compile_and_run_code(source: str, filename: str):
    import ast
    PyCF_DONT_IMPLY_DEDENT = 0x200
    PyCF_ALLOW_INCOMPLETE_INPUT = 0x4000
    PyCF_ONLY_AST = ast.PyCF_ONLY_AST

    nodes = compile(
        source=source,
        filename=filename,
        flags=PyCF_DONT_IMPLY_DEDENT | PyCF_ALLOW_INCOMPLETE_INPUT | PyCF_ONLY_AST,
        mode="exec",
    )

    nodes = nodes.body

    if isinstance(nodes[-1], ast.Expr):
        exec_nodes = nodes[:-1]
        interactive_nodes = nodes[-1:]
    else:
        exec_nodes = nodes
        interactive_nodes = []

    to_run = []
    for node in exec_nodes:
        to_run.append((node, "exec"))
    for node in interactive_nodes:
        to_run.append((node, "single"))

    for node, mode in to_run:
        if mode == "exec":
            mod = ast.Module([node], [])
        elif mode == "single":
            mod = ast.Interactive([node])
        else:
            continue

        code = compile(mod, filename=filename, mode=mode, dont_inherit=True)
        exec(code)
'''


class __Cell:
    def __init__(self, v=None, t="string"):
        self.v = v
        self.t = t

    def __repr__(self):
        return f"(v={self.v}, t={self.t})"


def __parse_data_to_cells(
    data: object, force_primary: bool = False
) -> tuple([List[__Cell], int]):
    if data is None:
        return [__Cell("", "string")], 1

    if isinstance(data, str):
        return [__Cell(data, "string")], 1

    if isinstance(data, bytes):
        return [__Cell(str(data), "string")], 1

    if isinstance(data, int) or isinstance(data, float) or isinstance(data, complex):
        if __pd.isna(data):
            return [__Cell("", "string")], 1
        return [__Cell(data, "double")], 1

    if isinstance(data, bool):
        return [__Cell(data, "bool")], 1

    if isinstance(data, __pd.Timestamp):
        return [__Cell(data.strftime("%Y-%m-%d %H:%M:%S"), "datatime")], 1

    if isinstance(data, __pd._libs.tslibs.nattype.NaTType):
        return [__Cell(data, "string")], 1

    if isinstance(data, __pd.Series):
        if force_primary:
            raise ValueError("too many dimensions in data")

        cells = []
        num_rows = 0

        with_index = not isinstance(data.index, __pd.RangeIndex)
        for index, value in data.items():
            if with_index:
                cells.extend(__parse_data_to_cells(index, True)[0])
            cells.extend(__parse_data_to_cells(value, True)[0])
            num_rows = num_rows + 1

        return cells, num_rows

    if isinstance(data, __pd.DataFrame):
        if force_primary:
            raise ValueError("too many dimensions in data")

        cells = []
        num_rows = 0

        with_index = not isinstance(data.index, __pd.RangeIndex)

        # pandas.DataFrame.columns
        columns = data.columns
        if not isinstance(columns, __pd.RangeIndex):
            if with_index:
                """
                如果要处理 index，columns 前边要加一个 index 的空 cell
                """
                cells.extend(__parse_data_to_cells("", True)[0])
            num_rows = num_rows + 1
            for column in columns:
                cells.extend(__parse_data_to_cells(column, True)[0])

        # pandas.DataFrame.data
        for row in data.itertuples(index=with_index):
            num_rows = num_rows + 1
            for item in row:
                cells.extend(__parse_data_to_cells(item, True)[0])

        return cells, num_rows

    if isinstance(data, list) or isinstance(data, tuple) or isinstance(data, set):
        if force_primary:
            raise ValueError("too many dimensions in data")

        arr = __np.asarray(list(data))
        if arr.ndim == 1:
            cells = []
            previous_length = None
            for item in data:
                subset, subset_length = __parse_data_to_cells(item, True)
                if previous_length is None:
                    previous_length = subset_length
                elif previous_length != subset_length:
                    raise ValueError("")
                cells.extend(subset)
            return cells, 1
        if arr.ndim == 2:
            return __parse_data_to_cells(__pd.DataFrame(arr))
        raise ValueError("too many dimensions in data")

    if isinstance(data, dict):
        if force_primary:
            raise ValueError("too many dimensions in data")
        arr = __np.asarray(list(data.values()))
        if arr.ndim == 1:
            cells = []
            for item in data.keys():
                cells.extend(__parse_data_to_cells(item)[0])
            for item in arr.flat:
                cells.extend(__parse_data_to_cells(item)[0])
            return cells, 2
        if arr.ndim == 2:
            return __parse_data_to_cells(__pd.DataFrame(data))
        else:
            raise ValueError("too many dimensions in data")

    # fallback
    v = repr(data)
    t = "string"
    return [__Cell(v, t)], 1


def echarts(
    options: dict,
) -> "pyecharts.charts.base.Base":  # I don't want to import on startup, just for typing
    from pyecharts.charts.base import Base

    if not isinstance(options, dict):
        raise TypeError("options must be a dict")

    chart = Base()
    chart.options = options
    return chart


__builtins.echarts = echarts

TypeVarStrOrList = TypeVar("TypeVarStrOrList", str, List[str])


def xl(
    range: str = "",
    headers: bool = False,
    sheet_name: TypeVarStrOrList = "",
    book_url: str = "",
    start_row: Optional[int] = None,
    start_column: Optional[int] = None,
) -> Union[__pd.DataFrame, Dict[str, __pd.DataFrame]]:
    if sheet_name is not None and isinstance(sheet_name, list) and len(sheet_name) == 0:
        return __pd.DataFrame  # sheet_name = []

    if isinstance(sheet_name, str):
        sheet_name = [sheet_name]

    if start_row is None:
        start_row = -1
    if start_column is None:
        start_column = -1

    return __builtins.__xl(
        range, headers, sheet_name, book_url, start_row, -1, start_column, -1
    )


__builtins.xl = xl


def write_xl(
    data: any,
    range: str = "",
    new_sheet: bool = False,
    sheet_name: str = "",
    overfill: bool = True,
    book_url: str = "",
    start_row: Optional[int] = None,
    start_column: Optional[int] = None,
) -> None:
    """
    将数据回写到表格
    """
    limit = 1000000  # 1M

    if (
        isinstance(data, __pd.DataFrame) or isinstance(data, __pd.Series)
    ) and data.size > limit:
        raise ValueError("too many data to write")
    if (
        isinstance(data, list)
        or isinstance(data, tuple)
        or isinstance(data, dict)
        or isinstance(data, set)
    ) and len(data) > limit:
        raise ValueError("too many data to write")

    if start_row is None:
        start_row = -1
    if start_column is None:
        start_column = -1

    if hasattr(__np, "warnings"):
        # numpy 1.23.5 需要，否则只会报 warning
        __np.warnings.filterwarnings("error", category=__np.VisibleDeprecationWarning)
        try:
            cells, num_rows = __parse_data_to_cells(data)
        finally:
            __np.warnings.filterwarnings(
                "default", category=__np.VisibleDeprecationWarning
            )
        __builtins.__write_xl(
            cells,
            num_rows,
            range,
            new_sheet,
            sheet_name,
            overfill,
            book_url,
            start_row,
            -1,
            start_column,
            -1,
        )
    else:
        cells, num_rows = __parse_data_to_cells(data)
        __builtins.__write_xl(
            cells,
            num_rows,
            range,
            new_sheet,
            sheet_name,
            overfill,
            book_url,
            start_row,
            -1,
            start_column,
            -1,
        )


__builtins.write_xl = write_xl


def dbt(
    field: TypeVarStrOrList = None,
    sheet_name: TypeVarStrOrList = "",
    book_url: str = "",
) -> Union[__pd.DataFrame, Dict[str, __pd.DataFrame]]:
    """
    read records in db sheet into a pandas.DataFrame or a dict of pandas.DataFrame
    """
    if field is not None and isinstance(field, list) and len(field) == 0:
        # returns a empty df
        return __pd.DataFrame()
    if isinstance(field, str):
        field = [field]

    if isinstance(sheet_name, str):
        sheet_name = [sheet_name]

    return __builtins.__list_db_records(field, sheet_name, book_url)


class __RecordField:
    def __init__(self, f, v, t):
        self.f = f  # field
        self.v = v  # value
        self.t = t  # type


class __Record:
    def __init__(self, id):
        self.id = id
        self.fs = []


def __parse_data_to_record_field(field, data) -> __RecordField:
    if isinstance(data, str):
        return __RecordField(field, data, "MultiLineText")

    if isinstance(data, bytes):
        return __RecordField(field, data, "MultiLineText")

    if isinstance(data, int) or isinstance(data, float) or isinstance(data, complex):
        if __math.isnan(data):
            return __RecordField(field, "", "MultiLineText")
        else:
            return __RecordField(field, data, "Number")

    if isinstance(data, bool):
        return __RecordField(field, data, "Checkbox")

    if isinstance(data, __pd.Timestamp):
        return __RecordField(field, data.strftime("%Y/%m/%d %H:%M:%S"), "Date")

    return __RecordField(field, repr(data), "MultiLineText")


def __parse_data_to_record(
    data, check_rid: bool = False, fields: dict = None
) -> __Record:
    if not isinstance(data, dict):
        raise TypeError(f"invalid type of data: {type(data)}")

    if len(data) == 0:
        raise ValueError(f"invalid value of data: {type(data)}")

    rid = data.get("_rid", "")
    if check_rid and (rid is None or rid == ""):
        raise ValueError("no _rid in your data")

    record = __Record(rid)
    record.fs = [__parse_data_to_record_field(k, v) for k, v in data.items()]
    if fields is not None:
        for elm in record.fs:
            elm.t = fields.get(elm.f, elm.t)

    return record


def update_dbt(
    data: Union[Dict[str, Any], List[Dict[str, Any]], __pd.DataFrame],
    sheet_name: str = "",
) -> None:
    """
    update record(s) in db sheet
    """
    if data is None:
        raise ValueError("your data is None")
    if isinstance(data, dict):
        data = [__parse_data_to_record(data, True)]
    elif isinstance(data, list):
        data = [__parse_data_to_record(elm, True) for elm in data]
    elif isinstance(data, __pd.DataFrame):
        fields = data.dbt_fields if hasattr(data, "dbt_fields") else None
        index = data.index
        if isinstance(index, __pd.RangeIndex):
            raise ValueError(
                "your DataFrame doesn't have the index, which should contain row_id(s) in"
            )

        data = data.reset_index(names=["_rid"]).to_dict(orient="records")
        data = [__parse_data_to_record(elm, True, fields) for elm in data]
    else:
        raise TypeError("invalid type of data")

    __builtins.__update_db_records(data, sheet_name)


def insert_dbt(
    data: Union[Dict[str, Any], List[Dict[str, Any]], __pd.DataFrame],
    sheet_name: str = "",
    new_sheet: bool = False,
) -> None:
    """
    insert new record(s) into db sheet
    """
    if data is None:
        raise ValueError("your data is None")
    if isinstance(data, dict):
        data = [__parse_data_to_record(data)]
    elif isinstance(data, list):
        data = [__parse_data_to_record(elm) for elm in data]
    elif isinstance(data, __pd.DataFrame):
        fields = data.dbt_fields if hasattr(data, "dbt_fields") else None
        columns = data.columns
        data = [
            __parse_data_to_record({k: v for k, v in zip(columns, row)}, False, fields)
            for row in data.itertuples(index=False)
        ]
    else:
        raise TypeError("invalid type of data")

    __builtins.__create_db_records(data, sheet_name, new_sheet)


def batch_get_attachmnt_temporary_urls(attachments: List[Any] = []) -> Dict[str, str]:
    """
    这里加前缀，在 class 里就找不到了
    """
    return __builtins__.__batch_get_attachmnt_temporary_urls(attachments)


@register_series_accessor("attachments")
class DBTFieldAttributeAccessor:
    def __init__(self, pandas_obj) -> None:
        self._obj = pandas_obj

    def temporary_url(self):
        """
        获取 Series 上的附件 URL，目前只有 dbt 的
        """
        import pandas as pd

        def convert_to_attachment_item(x) -> Dict[str, Any]:
            return {
                "file_id": getattr(x, "file_id", ""),
                "key": getattr(x, "upload_id", ""),
                "source": getattr(x, "source", ""),
                "mime_type": getattr(x, "mime_type", ""),
            }

        """
        TODO liangzuobin 这里的逻辑有点别扭
        先将 Series（元素是 []) 处理成一个 attachments []
        通过这个 attachments 去查询
        """
        attachments = []
        for elm in self._obj:
            if hasattr(elm, "attachments"):
                if isinstance(elm.attachments, list):
                    for x in elm.attachments:
                        attachments.append(convert_to_attachment_item(x))
                else:
                    attachments.append(convert_to_attachment_item(x))

        if len(attachments) == 0:
            urls = {}
        else:
            urls = batch_get_attachmnt_temporary_urls(attachments)

        def get_url_or_empty(x):
            file_id = getattr(x, "file_id", "")
            upload_id = getattr(x, "upload_id", "")
            if file_id == "" or upload_id == "":
                return ""
            return urls.get(f"{file_id}-{upload_id}", "")

        data = []
        for elm in self._obj:
            if hasattr(elm, "attachments"):
                if isinstance(elm.attachments, list):
                    data.append([get_url_or_empty(x) for x in elm.attachments])
                else:
                    data.append(get_url_or_empty(elm.attachments))
            else:
                data.append("")
        return pd.Series(data=data)


class DBTBaseDtype(ExtensionDtype):
    """
    标记类
    """

    @classmethod
    def _from_values_and_dtype(cls, values, dtype) -> Any: ...

    def __str__(self) -> str: ...

    """
    The interface includes the following abstract methods that must
    be implemented by subclasses:

    * type
    * name
    * construct_array_type
    """

    @property
    def type(self) -> type_t[ExtensionDtype]: ...

    @property
    def name(self) -> str: ...

    @classmethod
    def construct_array_type(cls) -> type_t[ExtensionArray]: ...

    """
    The following attributes and methods influence the behavior of the dtype in
    pandas operations

    * _is_numeric
    * _is_boolean
    * _get_common_dtype
    """

    @property
    def _is_numeric(self) -> bool:
        return False

    @property
    def _is_boolean(self) -> bool:
        return False

    def _get_common_dtype(self, dtypes: List[DtypeObj]) -> Optional[DtypeObj]:
        if not all(isinstance(x, type(self)) for x in dtypes):
            return None

        return self

    @classmethod
    def construct_from_string(
        cls: type_t[ExtensionDtype], string: str
    ) -> ExtensionDtype:
        if not isinstance(string, str):
            raise TypeError(
                f"'construct_from_string' expects a string, got {type(string)}"
            )
        if string != cls.name:
            raise TypeError(f"Cannot construct a '{cls.name}' from '{string}'")
        return cls()


class DBTAttachment:
    def __init__(
        self,
        file_id: str = "",  # 父文档
        upload_id: str = "",
        file_name: str = "",
        size: int = 0,
        source: str = "",
        mime_type: str = "",
        link_url: str = "",
        img_size: str = "",
    ) -> None:
        if not isinstance(file_id, str):
            raise TypeError("file_id must be a str")
        self.file_id = file_id
        self.upload_id = upload_id
        self.file_name = file_name
        self.size = size
        self.source = source
        self.mime_type = mime_type
        self.link_url = link_url
        self.img_size = img_size

    def __str__(self) -> str:
        return self.file_name

    @classmethod
    def _from_dict(cls, data: Dict[str, any] = {}) -> "DBTAttachment":
        return cls(
            file_id=data.get("file_id", ""),
            upload_id=data.get("upload_id", ""),
            file_name=data.get("file_name", ""),
            size=data.get("size", 0),
            source=data.get("source", ""),
            mime_type=data.get("mime_type", ""),
            link_url=data.get("link_url", ""),
            img_size=data.get("img_size", ""),
        )

    @classmethod
    def _from_value(cls, value) -> "DBTAttachment":
        if value is None:
            return None
        if isinstance(value, DBTAttachment):
            return cls(
                file_id=value.file_id,
                upload_id=value.upload_id,
                file_name=value.file_name,
                size=value.size,
                source=value.source,
                mime_type=value.mime_type,
                link_url=value.link_url,
                img_size=value.img_size,
            )
        if isinstance(value, dict):
            # FIXME liangzuobin 这里可能有问题
            return cls(**value)
        raise ValueError(f"Cannot construct DBTAttachment from {type(value)}")


@register_extension_dtype
class DBTAttachmentDtype(DBTBaseDtype):
    name = "DBTAttachment"

    _metadata = "attachments"

    def __init__(self, attachments=[]) -> None:
        self.attachments = attachments

    def __repr__(self) -> str:
        return ", ".join([str(x) for x in self.attachments])

    def __str__(self) -> str:
        return self.name

    @classmethod
    def construct_array_type(cls) -> type_t[ExtensionArray]:
        return DBTFieldExtensionArray

    @property
    def type(self) -> type_t[DBTAttachment]:
        return DBTAttachment

    @classmethod
    def _from_values_and_dtype(
        cls, values=None, dtype: DtypeObj = None
    ) -> List["DBTAttachmentDtype"]:
        import pandas as pd

        return pd.array([cls._from_value(v) for v in values])

    @classmethod
    def _from_value(cls, value) -> "DBTAttachmentDtype":
        if isinstance(value, list):
            return cls(attachments=[DBTAttachment._from_value(v) for v in value])
        return cls()


class DBTBaseArray(ExtensionArray):
    def tolist(self):
        if self.ndim > 1:
            return [x.tolist() for x in self]
        return list(self.to_numpy())


class DBTFieldExtensionArray(DBTBaseArray, ExtensionScalarOpsMixin):
    def __init__(self, values, dtype, copy) -> None:
        if not isinstance(dtype, DBTBaseDtype):
            raise TypeError(f"invalid dtype of {dtype}")

        self.__data = dtype._from_values_and_dtype(values=values, dtype=dtype)
        self.__dtype = dtype

    @classmethod
    def _from_sequence(
        cls, scalars, *, dtype: Optional[DtypeObj] = None, copy: bool = False
    ) -> "DBTFieldExtensionArray":
        return cls(scalars, dtype, copy)

    @classmethod
    def _from_sequence_of_strings(
        cls, strings, *, dtype: Optional[DtypeObj] = None, copy: bool = False
    ):
        return cls._from_sequence(strings, dtype=dtype, copy=copy)

    @classmethod
    def _from_factorized(cls, values, original):
        raise NotImplementedError(cls)

    def copy(self):
        from copy import deepcopy

        return deepcopy(self)

    def __getitem__(self, item) -> Any:
        return self.__data.__getitem__(item)

    def __len__(self) -> int:
        return self.__data.__len__()

    @property
    def nbytes(self) -> int:
        import sys

        return sys.getsizeof(self)

    @property
    def dtype(self) -> ExtensionDtype:
        return self.__dtype

    def isna(self) -> "numpy.ndarray":
        import pandas as pd

        return pd.isna(self)

    def take(self, *args, **kwargs):
        # TODO
        raise NotImplemented

    def _concat_same_type(to_concat):
        # TODO
        raise NotImplemented

    def interpolate(self, *args, **kwargs):
        # TODO
        raise NotImplemented

    def _formatter(self, boxed: bool = False):
        # 强制使用 repr 打印内容
        return repr


DBTFieldExtensionArray._add_comparison_ops()


def _request(
    method: str,
    url: str,
    body: dict = None,
    json: dict = None,
    headers: dict = None,
    cookies: dict = None,
    stream: bool = None,
) -> "requests.Response":
    return __builtins.__internal_requests(
        method, url, body, json, headers, cookies, stream
    )


# 放在最后


def init(
    wps_sid: str, file_id: str, sheet_name: str, weboffice_branch: Optional[str] = None
):
    return playground_init(
        wps_sid=wps_sid,
        weboffice_branch=weboffice_branch,
        file_id=file_id,
        sheet_name=sheet_name,
    )
