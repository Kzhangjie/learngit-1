from typing import Tuple, Optional
import re

# ATTENTION 这个正则还是有漏洞，获取到 range 之后还是要检查一下
# TODO liangzuobin 这里之后可能还要添加对 sheet 名的支持
_regex = "^\${0,1}([A-Za-z]*)\${0,1}([0-9]*):{0,1}\${0,1}([A-Za-z]*)\${0,1}([0-9]*)$"
_pattern = re.compile(_regex)


def column_letter_to_number(column_name: str) -> int:
    """
    将列名转成列序号，例如：
    A -> 1
    Z -> 26
    AA -> 27
    """
    if len(column_name) == 0:
        return 0

    current = (ord(column_name[:1].upper()) - ord("A") + 1) * (
        26 ** (len(column_name) - 1)
    )
    rest = column_letter_to_number(column_name=column_name[1:])

    return current + rest


def column_number_to_letter(column_number: int) -> str:
    """
    将列序号转成列名，例如：
    1 -> A
    26 -> Z
    27 -> AA
    """
    if column_number <= 0:
        return ""
    if column_number <= 26:
        return chr(ord("A") + column_number - 1)

    mod = (column_number - 1) % 26

    return column_number_to_letter((column_number - mod) // 26) + chr(ord("A") + mod)


def number_to_index(n: int) -> int:
    """
    将行或列序号转成列的索引值，例如：
    1 -> 0
    2 -> 1
    """
    if n <= 0:
        raise ValueError(f"Invalid row or column number: {n}")
    return n - 1


def index_to_number(i: int) -> int:
    """
    将行或列的索引值转成序号，例如：
    0 -> 1
    1 -> 2
    """
    if i < 0:
        raise ValueError(f"Invalid row or column index: {i}")
    return i + 1


def parse_range_to_index(
    range: str,
) -> Tuple[Optional[int], Optional[int], Optional[int], Optional[int]]:
    """
    将用户输入的区域，转换成行和列的索引值，索引值是从 0 开始的。例如：
    A1:C5 -> (0, 2, 0, 4)
    """
    range = range.replace(" ", "")
    if range.startswith(":") or range.endswith(":"):
        raise ValueError(f"Invalid range expression: {range}")

    rows_from, columns_from, rows_to, columns_to = (
        None,
        None,
        None,
        None,
    )  # init index to None

    group = _pattern.match(range)
    if group:
        if group[1] != "":
            columns_from = number_to_index(column_letter_to_number(group[1]))
        if group[2] != "":
            rows_from = number_to_index(int(group[2]))
        if group[3] != "":
            columns_to = number_to_index(column_letter_to_number(group[3]))
        if group[4] != "":
            rows_to = number_to_index(int(group[4]))

        # 正则覆盖不到的异常情况：
        ok: bool = False
        if ":" in range:
            # 用户输入的是一个选区，例如：A1:A10
            rows_from, rows_to, rows_ok = _check_and_normalize(rows_from, rows_to)
            columns_from, columns_to, columns_ok = _check_and_normalize(
                columns_from, columns_to
            )
            ok = rows_ok and columns_ok
        else:
            # 用户输入的不是一个选区，而是一个单元格地址，比如：A1
            if rows_from is not None and columns_from is not None:
                rows_to = rows_from
                columns_to = columns_from
                ok = True

        if ok:
            return rows_from, rows_to, columns_from, columns_to

    raise ValueError(f"Invalid range expression: {range}")


def _check_and_normalize(a, b):
    if a is None and b is None:
        return (a, b, True)

    if a is not None and b is not None:
        return (a, b, True) if a <= b else (b, a, True)

    return (None, None, False)


# FIXME liangzuobin 记得删掉
# if __name__ == "__main__":
#     pass

#     good_ranges = [
#         "A1 : C2",
#         "A1:A10",
#         "A1",
#         "C2:A1",
#         "a:A",
#         "1:10",
#         "$A1:B10",
#         "$A$1:$DB$10",
#         "A:Z",
#         "A:AA",
#     ]

#     bad_ranges = [
#         "C:A1",
#         "C",
#         "$$1:$DB$10",
#         ":C2",
#         "C2:",
#         "1:D",
#         "1:D2",
#         "1:D2",
#     ]

#     print("should passed")
#     for range in good_ranges:
#         print(f"range: {range}, pased: {parse_range_to_index(range)}")

#     print("should failed")
#     for range in bad_ranges:
#         try:
#             print(f"range: {range}, pased: {parse_range_to_index(range)}")
#         except Exception as e:
#             print(f"range: {range}, failed: {e}")

#     # s = "AAA"
#     # n = column_name_to_column_number(s)
#     # print(f"{s}, {n}, {column_number_to_column_name(n)}")
