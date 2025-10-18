import csv


def csv_to_markdown(csv_file_path, markdown_file_path):
    with open(csv_file_path, "r") as csv_file:
        reader = csv.reader(csv_file)
        rows = list(reader)

    # 获取列宽以便对齐
    col_widths = [max(len(str(row[i])) for row in rows) for i in range(len(rows[0]))]

    # 生成 Markdown 表头和分隔符
    header = (
        "| "
        + " | ".join(f"{row[i].ljust(col_widths[i])}" for i, row in enumerate(rows[0]))
        + " |"
    )
    separator = "| " + " | ".join("-" * col_width for col_width in col_widths) + " |"

    # 生成 Markdown 数据行
    data_rows = [
        "| "
        + " | ".join(f"{cell.ljust(col_widths[i])}" for i, cell in enumerate(row))
        + " |"
        for row in rows[1:]
    ]

    # 将 Markdown 表格写入文件
    with open(markdown_file_path, "w", encoding="utf-8") as markdown_file:
        markdown_file.write(header + "\n")
        markdown_file.write(separator + "\n")
        markdown_file.write("\n".join(data_rows) + "\n")


# 示例调用
csv_to_markdown("aaa.csv", "aaa.md")
