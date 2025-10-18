import hashlib
import time
import json
import os
from typing import Literal, List
from io import IOBase, StringIO
import requests
import base64
import re
import html
from . import colors


def id_to_gcp(id: str) -> int:
    if id == "":
        return -1

    idx = len(id) - 1
    pos = ""
    while idx >= 0:
        if id[idx].isdigit():
            pos = id[idx:]
            idx -= 1
        else:
            break

    if pos == "":
        return -1
    else:
        return int(pos)


def decimal_to_base26(decimal_number):
    base26_number = ""
    while decimal_number > 0:
        remainder = decimal_number % 26
        # 余数对应的字母，A对应0，B对应1，以此类推
        base26_digit = chr(remainder + 65)
        base26_number = base26_digit + base26_number
        decimal_number = decimal_number // 26
    return base26_number if base26_number else "A"


def base64padding(encode: str) -> str:
    reminder = len(encode) % 4
    if reminder == 2:
        return encode + "=="
    elif reminder == 3:
        return encode + "="
    return encode


def base64decode(encode: str) -> bytes:
    return base64.b64decode(base64padding(encode))


BlockType = Literal["para", "table", "component", "textbox", "drawing"]


def _to_class_list(d: dict, key: str, cls) -> list:
    if key not in d:
        return []
    v = d[key]
    if v is None:
        return []
    return [cls(x) for x in v]


class Node(dict):
    @property
    def outline_level(self) -> int:
        return self.get("outline_level", 10)

    @property
    def blocks(self) -> List["Block"]:
        return _to_class_list(self, "blocks", Block)

    @property
    def children(self) -> List["Node"]:
        return _to_class_list(self, "children", Node)


class RunProp(dict):
    @property
    def size(self) -> float:
        return self.get("size", 0)

    @property
    def color(self) -> int:
        return self.get("color", "")

    @property
    def font_ascii(self) -> str:
        return self.get("font_ascii", "")

    @property
    def font_east_asia(self) -> str:
        return self.get("font_east_asia", "")

    @property
    def bold(self) -> bool:
        return self.get("bold", False)

    @property
    def italic(self) -> bool:
        return self.get("italic", False)

    @property
    def underline(self) -> bool:
        return self.get("underline", False)

    @property
    def strike(self) -> bool:
        return self.get("strike", False)


class Run(dict):
    @property
    def prop(self) -> RunProp:
        return RunProp(self.get("prop", {}))

    @property
    def text(self) -> str:
        return self.get("text", "")

    @property
    def id(self) -> str:
        return self.get("id", "")


ParaAlignment = Literal[
    "left", "right", "center", "justify", "distribute", "fill", "center_continuous"
]


class ParaIndent(dict):
    @property
    def abs_first_indent(self) -> int:
        return self.get("abs_first_indent", 0)

    @property
    def rel_first_indent(self) -> int:
        return self.get("rel_first_indent", 0)

    @property
    def abs_left_indent(self) -> int:
        return self.get("abs_left_indent", 0)

    @property
    def rel_left_indent(self) -> int:
        return self.get("rel_left_indent", 0)


class ParaProp(dict):
    @property
    def alignment(self) -> ParaAlignment:
        return self.get("alignment", "")

    @property
    def def_run_prop(self) -> RunProp:
        return RunProp(self.get("def_run_prop", {}))

    @property
    def outline_level(self) -> int:
        return self.get("outline_level", 10)

    @property
    def list_string(self) -> int:
        return self.get("list_string", "")

    @property
    def indent(self) -> ParaIndent:
        return ParaIndent(self.get("indent", {}))


class Para(dict):
    @property
    def runs(self) -> List[Run]:
        return _to_class_list(self, "runs", Run)

    @property
    def prop(self) -> ParaProp:
        return ParaProp(self.get("prop", {}))


class TableCell(dict):
    @property
    def blocks(self) -> List["Block"]:
        return _to_class_list(self, "blocks", Block)

    @property
    def row_span(self) -> int:
        return self.get("row_span", 1)

    @property
    def col_span(self) -> int:
        return self.get("col_span", 1)


class TableRow(dict):
    @property
    def cells(self) -> List[TableCell]:
        return _to_class_list(self, "cells", TableCell)


class Table(dict):
    @property
    def rows(self) -> List[TableRow]:
        return _to_class_list(self, "rows", TableRow)


class Textbox(dict):
    @property
    def blocks(self) -> List["Block"]:
        return _to_class_list(self, "blocks", Block)


ComponentType = Literal["image", "audio", "video"]


class Reference(dict):
    @property
    def id(self) -> str:
        return self.get("id", "")

    @property
    def type(self) -> str:
        return self.get("type", "")


class Hyperlink(dict):
    @property
    def display_text(self) -> str:
        return self.get("display_text", "")

    @property
    def target(self) -> str:
        return self.get("target", "")

    @property
    def references(self) -> list[Reference]:
        return _to_class_list(self, "references", Reference)


class Media(dict):
    @property
    def id(self) -> str:
        return self["id"]

    @property
    def data(self) -> str:
        return self.get("data")

    @property
    def mime_type(self) -> str:
        return self.get("mime_type")

    @property
    def url(self) -> str:
        return self.get("url")


class Component(dict):
    @property
    def type(self) -> ComponentType:
        return self.get("type", "")

    @property
    def media_id(self) -> str:
        return self["media_id"]


class Drawing(dict):
    @property
    def media_id(self) -> str:
        return self.get("media_id")

    @property
    def type(self) -> str:
        return self.get("type")

    @property
    def url(self) -> str:
        return self.get("url")


class Block(dict):
    @property
    def type(self) -> BlockType:
        return self["type"]

    @property
    def para(self) -> Para:
        return Para(self["para"])

    @property
    def table(self) -> Table:
        return Table(self["table"])

    @property
    def component(self) -> Component:
        return Component(self["component"])

    @property
    def textbox(self) -> Textbox:
        return Textbox(self["textbox"])

    @property
    def drawing(self) -> Drawing:
        return Drawing(self["drawing"])

    @property
    def id(self) -> str:
        return self.get("id", "")


class Comment(dict):
    pass


class DocProp(dict):
    @property
    def page_count(self) -> int:
        return self.get("page_count", 0)

    @property
    def page_props(self) -> list:
        # todo
        return []


class Slide(dict):
    @property
    def shape_tree(self) -> List[Block]:
        return _to_class_list(self, "shape_tree", Block)

    @property
    def note_page(self) -> List[Block]:
        return _to_class_list(self, "note_page", Block)


class SlideContainer(dict):
    @property
    def category(self) -> str:
        return self.get("category", "")

    @property
    def slides(self) -> List[Slide]:
        return _to_class_list(self, "slides", Slide)


class Range(dict):
    @property
    def row_from(self) -> int:
        return self["row_spans"]["from"]

    @property
    def row_to(self) -> int:
        return self["row_spans"]["to"]

    @property
    def col_from(self) -> int:
        return self["col_spans"]["from"]

    @property
    def col_to(self) -> int:
        return self["col_spans"]["to"]

    def address(self) -> str:
        return f"{decimal_to_base26(self.col_from)}{self.row_from + 1}:{decimal_to_base26(self.col_to)}{self.row_to + 1}"


CellDataType = Literal["boolean", "date", "number", "error", "shared", "text", "handle"]


class Cell(dict):
    @property
    def col_index(self) -> int:
        return self["index"]

    @property
    def type(self) -> CellDataType:
        return self["type"]

    @property
    def value(self) -> str:
        return self["value"]


class SheetData(dict):
    @property
    def row_index(self) -> int:
        return self["index"]

    @property
    def cells(self) -> list[Cell]:
        return _to_class_list(self, "cells", Cell)


SheetType = Literal[
    "unknown",
    "grid",
    "dialog",
    "chart",
    "macro",
    "module",
    "griddb",
    "dashboard",
    "flexboard",
    "dashboard_db",
    "application",
    "workbench",
]


class Sheet(dict):
    @property
    def name(self) -> str:
        return self["name"]

    @property
    def id(self) -> int:
        return self["id"]

    @property
    def type(self) -> SheetType:
        return self["type"]

    @property
    def data(self) -> list[SheetData]:
        return _to_class_list(self, "data", SheetData)

    @property
    def merge_cells(self) -> list[Range]:
        return _to_class_list(self, "merge_cells", Range)

    @property
    def used_range(self) -> Range:
        if "used_range" in self:
            return Range(self["used_range"])
        else:
            return Range(
                {"col_spans": {"from": 0, "to": 0}, "row_spans": {"from": 0, "to": 0}}
            )

    def merge_area(self, row_idx: int, col_idx: int) -> Range:
        for m in self.merge_cells:
            if m.row_from == row_idx and m.col_from == col_idx:
                return m
        return None

    def cell_span(self, row_idx: int, col_idx: int) -> tuple[int, int]:
        for m in self.merge_cells:
            if m.row_from == row_idx and m.col_from == col_idx:
                return m.row_to - m.row_from + 1, m.col_to - m.col_from + 1
        return 1, 1


class SharedString(dict):
    @property
    def items(self) -> list[Run]:
        return _to_class_list(self, "items", Run)

    def text(self) -> str:
        text = ""
        for run in self.items:
            text += run.text
        return text


class Document(dict):
    @property
    def prop(self) -> DocProp:
        return DocProp(self.get("prop", {}))

    @property
    def blocks(self) -> List[Block]:
        return _to_class_list(self, "blocks", Block)

    def media(self, id: str) -> Media:
        for m in self.medias:
            if m.id == id:
                return m
        raise KeyError(f"media {id} not found")

    @property
    def medias(self) -> List[Media]:
        return _to_class_list(self, "medias", Media)

    @property
    def comments(self) -> List[Comment]:
        return _to_class_list(self, "comments", Comment)

    @property
    def slide_containers(self) -> List[SlideContainer]:
        return _to_class_list(self, "slide_containers", SlideContainer)

    @property
    def tree(self) -> Node:
        return Node(self["tree"])

    def to_html(self, media_dir: str) -> tuple[str, dict[str, bytes]]:
        out = StringIO()
        f = HTMLFormatter(self, media_dir)
        f.format(out)
        return out.getvalue(), f.images

    def to_markdown(self, media_dir: str) -> str:
        out = StringIO()
        MarkdownFormatter(self, media_dir).format(out)
        return out.getvalue()

    @property
    def sheets(self) -> list[Sheet]:
        return _to_class_list(self, "sheets", Sheet)

    @property
    def shared_strings(self) -> list[SharedString]:
        return _to_class_list(self, "shared_strings", SharedString)

    @property
    def hyperlinks(self) -> list[Hyperlink]:
        return _to_class_list(self, "hyperlinks", Hyperlink)


class HTMLFormatter:
    def __init__(self, doc: Document, media_dir: str):
        self.doc: Document = doc
        self.media_dir: str = media_dir
        self.images: dict[str, bytes] = {}
        self.content_len = 0

    def _parse_node(self, node: Node, out: IOBase):
        for n in node.blocks:
            self._parse_block(n, out)
        for c in node.children:
            self._parse_node(c, out)

    def _parse_block(self, block: Block, out: IOBase):
        match block.type:
            case "para":
                self._parse_para(block.para, out)
            case "table":
                self._parse_table(block.table, out)
            case "textbox":
                self._parse_textbox(block.textbox, out)
            case "component":
                self._parse_component(block.component, out)
            case "drawing":
                self._parse_drawing(block.drawing, out)

    def _join_cell_text(self, cell: TableCell) -> str:
        texts = []
        for block in cell.blocks:
            if block.type != "para":
                continue
            para_text = ""
            for run in block.para.runs:
                para_text += self._parse_run(run)
            texts.append(para_text + " ")
        return " ".join(texts)

    def _parse_table(self, table: Table, out: IOBase):
        out.write("<table>\n")
        for row in table.rows:
            out.write("<tr>")
            for cell in row.cells:
                cell_text = self._join_cell_text(cell)
                out.write(
                    f'<td rowspan="{cell.row_span}" colspan="{cell.col_span}">{cell_text}</td>'
                )
            out.write("</tr>\n")
        out.write("</table>\n")

    def _parse_textbox(self, textbox: Textbox, out: IOBase):
        lines = []
        for block in textbox.blocks:
            if block.type != "para":
                continue
            line = ""
            for run in block.para.runs:
                line += self._parse_run(run)
            lines.append(line)

        text = "\n".join(lines)
        out.write(f"<p>\n{text}\n</p>\n")

    def _parse_drawing(self, block: Drawing, out: IOBase):
        t = block.type
        if t == "image":
            media = self.doc.media(block.media_id)
            if media.url:
                url = media.url.replace("ks3-cn-beijing-internal", "ks3-cn-beijing")
                out.write(f'<img src="{url}">\n')
            elif media.data:
                self.images[media.id] = base64decode(media.data)
                out.write(f'<img src="{self.media_dir}/{media.id}">\n')

    def _parse_component(self, component: Component, out: IOBase):
        t = component["type"]
        if t == "image":
            media = self.doc.media(component.media_id)
            if media.url:
                url = media.url.replace("ks3-cn-beijing-internal", "ks3-cn-beijing")
                out.write(f'<img src="{url}">\n')
            elif media.data:
                self.images[media.id] = base64decode(media.data)
                out.write(f'<img src="{self.media_dir}/{media.id}">\n')
    
    def _parse_para(self, para: Para, out: IOBase):
        text = ""
        for run in para.runs:
            text += self._parse_run(run)

        html_tag = "p"
        match para.prop.outline_level:
            case 1:
                html_tag = "h1"
            case 2:
                html_tag = "h2"
            case 3:
                html_tag = "h3"
            case 4:
                html_tag = "h4"
            case 5:
                html_tag = "h5"

        out.write(f"<{html_tag}>{text}</{html_tag}>\n")

    def _parse_run(self, run: Run) -> str:
        text = run.text
        self.content_len += len(text)
        text = re.sub(
            "[\x0b\x0d\x07\x0c\x0f\x0e\x02\x05\x08\x01\x13\x14\x15\x03\x04\x1a\x1b]+",
            "",
            text,
        )
        text = html.escape(text)

        prop = run.prop

        styles = []
        tags = []
        if prop.bold:
            tags.append(("b", "</b>"))
        if prop.italic:
            tags.append(("i", "</i>"))
        if prop.underline:
            tags.append(("u", "</u>"))
        if prop.strike:
            tags.append(("s", "</s>"))

        opening_tags = "".join(f"<{opening}>" for opening, _ in tags)
        closing_tags = "".join(closing for _, closing in tags)

        return f"{opening_tags}{text}{closing_tags}"

    def format(self, out: IOBase):
        self._parse_node(self.doc.tree, out)

    def get_content_length(self):
        return self.content_len


class DocxHTMLFormatter(HTMLFormatter):
    DEFAULT_COLOR = ""
    DEFAULT_SIZE = 0
    DEFAULT_FONT_EAST_ASIA = ""
    DEFAULT_FONT_ASCII = ""
    DEFAULT_ALIGN = ""

    def __init__(self, doc: Document):
        super().__init__(doc, "")
        self.doc: Document = doc
        self.content_len = 0

    def get_hyperlinks_tag(self, run_id: str) -> str:
        for h in self.doc.hyperlinks:
            for r in h.references:
                try:
                    # print(r)
                    if r.id == run_id:
                        return h.target
                except Exception as e:
                    pass
        return ""

    def remove_field_codes(self, runs: list[Run]) -> list[Run]:
        clean_runs = []
        # Word文档域代码的状态
        # 0: 普通文本, 1: 域的代码区域, 2: 域的展示内容区域
        STATE_NORMAL = 0
        STATE_FIELD_CODE = 1
        STATE_FIELD_CONTENT = 2
        state = STATE_NORMAL
        for run in runs:
            if run.text == "\x13":
                state = STATE_FIELD_CODE
            if run.text == "\x14":
                state = STATE_FIELD_CONTENT
            if run.text == "\x15":
                state = STATE_NORMAL
            if state == STATE_NORMAL or state == STATE_FIELD_CONTENT:
                clean_runs.append(run)
        return clean_runs

    def _parse_block(self, block: Block, out: IOBase):
        match block.type:
            case "para":
                self._parse_para(block.para, out)
            case "table":
                self._parse_table(block.table, out)
            case "textbox":
                self._parse_textbox(block.textbox, out)
            case "component":
                self._parse_component(block.component, out)

    def _parse_component(self, component: Component, out: IOBase):
        t = component["type"]
        if t == "image":
            media = self.doc.media(component.media_id)
            self.images[media.id] = base64decode(media.data)
            out.write(f'<img id="{media.id}"/>\n')

    def _parse_table(self, table: Table, out: IOBase):
        out.write("<table>\n")
        for row in table.rows:
            out.write("<tr>")
            for cell in row.cells:
                cell_text = self._join_cell_text(cell)
                out.write(f"<td>{cell_text}</td>")
            out.write("</tr>\n")
        out.write("</table>\n")

    def _parse_para(self, para: Para, out: IOBase):
        text = ""
        for run in self.remove_field_codes(para.runs):
            text += self._parse_run(run)

        styles = []
        if (
            para.prop.alignment
            and para.prop.alignment != DocxHTMLFormatter.DEFAULT_ALIGN
        ):
            styles.append(f"text-align:{para.prop.alignment};")
        if para.prop.indent:
            indent = para.prop.indent
            abs_first_indent = indent.abs_first_indent
            rel_first_indent = indent.rel_first_indent
            abs_left_indent = indent.abs_left_indent
            rel_left_indent = indent.rel_left_indent

            if rel_first_indent != 0:
                styles.append(f"text-indent:{rel_first_indent / 100}em;")
            elif abs_first_indent != 0:
                styles.append(f"text-indent:{abs_first_indent / 20}pt;")

            if rel_left_indent != 0:
                styles.append(f"margin-left:{rel_left_indent / 100}em;")
            elif abs_left_indent != 0:
                styles.append(f"margin-left:{abs_left_indent / 20}pt;")

        html_tag = "p"
        match para.prop.outline_level:
            case 1:
                html_tag = "h1"
            case 2:
                html_tag = "h2"
            case 3:
                html_tag = "h3"
            case 4:
                html_tag = "h4"
            case 5:
                html_tag = "h5"

        if len(styles) > 0:
            style_attr = " ".join(styles)
            out.write(f'<{html_tag} style="{style_attr}">{text}</{html_tag}>\n')
        else:
            out.write(f"<{html_tag}>{text}</{html_tag}>\n")

    def _parse_run(self, run: Run) -> str:
        text = run.text
        self.content_len += len(text)
        if text == "\x0b":
            return "<br/>"
        text = re.sub(
            "[\x0b\x0d\x07\x0c\x0f\x0e\x02\x05\x08\x01\x13\x14\x15\x03\x04\x1a\x1b]+",
            "",
            text,
        )
        text = html.escape(text)

        prop = run.prop

        styles = []
        tags = []
        if prop.bold:
            tags.append(("b", "</b>"))
        if prop.italic:
            tags.append(("i", "</i>"))
        if prop.underline:
            tags.append(("u", "</u>"))
        if prop.strike:
            tags.append(("s", "</s>"))
        if prop.color and prop.color != DocxHTMLFormatter.DEFAULT_COLOR:
            try:
                color = colors.hex_to_name(prop.color)
            except Exception:
                color = prop.color[0:7]
            styles.append(f"color:{color}")
        if prop.size and prop.size != DocxHTMLFormatter.DEFAULT_SIZE:
            styles.append(f"font-size:{prop.size}pt")

        if (
            prop.font_east_asia
            and prop.font_east_asia != DocxHTMLFormatter.DEFAULT_FONT_EAST_ASIA
        ):
            styles.append(f"font-family:{prop.font_east_asia}")
        if prop.font_ascii and prop.font_ascii != DocxHTMLFormatter.DEFAULT_FONT_ASCII:
            styles.append(f"mso-ascii-font-family:{prop.font_ascii}")

        if len(styles) > 0 and len(tags) <= 0:
            tags.append(("span", "</span>"))

        style_str = f'style="{";".join(styles)}"' if styles else ""

        opening_tags = "".join(
            f"<{tag} {style_str}>" if i == 0 and style_str else f"<{tag}>"
            for i, (tag, _) in enumerate(reversed(tags))
        )
        closing_tags = "".join(closing for _, closing in tags)

        return f"{opening_tags}{text}{closing_tags}"


class SelectKDCFormatter(DocxHTMLFormatter):
    def __init__(
        self,
        doc: Document,
        start: int = 0,
        end: int = 0,
        with_orgin: str = True,
        start_lable: str = "【用户框选的文档区域的开始】",
        end_lable: str = "【用户框选的文档区域的结束】",
    ):
        super().__init__(doc)
        self.doc: Document = doc
        self.with_orgin = with_orgin
        self.start_lable = start_lable
        self.end_lable = end_lable
        self.offset_start = start
        self.offset_end = end

    def _placeholder_cleaner(self, text: str) -> str:
        return re.sub(
            "[\x0b\x0d\x07\x0c\x0f\x0e\x02\x05\x08\x01\x13\x14\x15\x03\x04\x1a\x1b]+",
            "",
            text,
        )

    def _offset_cleaner(self, run: Run) -> str:
        overlap_start = max(0, self.offset_start - id_to_gcp(run.id))
        overlap_end = min(len(run.text), self.offset_end - id_to_gcp(run.id))
        if overlap_start < overlap_end:
            if self.with_orgin:
                text = (
                    run.text[:overlap_start]
                    + self.start_lable
                    + run.text[overlap_start:overlap_end]
                    + self.end_lable
                    + run.text[overlap_end:]
                )
            else:
                text = run.text[overlap_start:overlap_end]
        else:
            if self.with_orgin:
                text = run.text
            else:
                text = None
        return text

    def _in_offset(self, run: Run) -> bool:
        overlap_start = max(0, self.offset_start - id_to_gcp(run.id))
        overlap_end = min(len(run.text), self.offset_end - id_to_gcp(run.id))
        if overlap_start < overlap_end:
            return True
        else:
            return False

    def _parse_block(self, block: Block, out: IOBase):
        match block.type:
            case "para":
                self._parse_para(block.para, out)
            case "table":
                self._parse_table(block.table, out)
            case "textbox":
                self._parse_textbox(block.textbox, out)

    def _cell_in_offset(
        self, cell: TableCell, offset_start: int, offset_end: int
    ) -> bool:
        for block in cell.blocks:
            if block.type != "para":
                continue
            for run in self.remove_field_codes(block.para.runs):
                if offset_start < (
                    id_to_gcp(run.id) + len(run.text)
                ) and offset_end > id_to_gcp(run.id):
                    return True

        return False

    def _join_cell_text(self, cell: TableCell, with_select: True) -> str:
        texts = []
        for block in cell.blocks:
            if block.type != "para":
                continue
            para_text = ""
            for run in self.remove_field_codes(block.para.runs):
                if with_select:
                    run_text = self._parse_run_with_offset(run)
                    if run_text is None:
                        continue
                    para_text += run_text
                else:
                    para_text += self._parse_run(run)
            texts.append(para_text + " ")
        return " ".join(texts)

    def _blocks_in_offset(self, blocks: list[Block]) -> bool:
        in_offset = False
        for block in blocks:
            if block.type != "para":
                continue
            for run in self.remove_field_codes(block.para.runs):
                if self._in_offset(run):
                    in_offset = True
        return in_offset

    def _parse_table(self, table: Table, out: IOBase):
        table_text = ""
        select_count = 0
        last_select_cell = None
        table_text += "<table>\n"

        for row in table.rows:
            table_text += "<tr>"
            for cell in row.cells:
                cell_text = self._join_cell_text(cell, with_select=False)
                td = f'<td rowspan="{cell.row_span}" colspan="{cell.col_span}">{cell_text}</td>'
                if self._blocks_in_offset(cell.blocks):
                    select_count += 1
                    last_select_cell = cell
                    last_select_idx = [len(table_text), len(table_text) + len(td)]
                table_text += td
            table_text += "</tr>\n"
        table_text += "</table>\n"

        if self.with_orgin:
            if select_count == 1:
                cell_text = self._join_cell_text(last_select_cell, with_select=True)
                td = f'<td rowspan="{last_select_cell.row_span}" colspan="{last_select_cell.col_span}">{cell_text}</td>'
                table_text = (
                    table_text[: last_select_idx[0]]
                    + td
                    + table_text[last_select_idx[1] :]
                )
            if select_count > 1:
                table_text = self.start_lable + table_text + self.end_lable
            out.write(table_text)
        else:
            if select_count == 1:
                out.write(self._join_cell_text(last_select_cell, with_select=True))
            if select_count > 1:
                out.write(table_text)

    def _parse_textbox(self, textbox: Textbox, out: IOBase):
        lines = []
        for block in textbox.blocks:
            if block.type != "para":
                continue
            line = ""
            for run in self.remove_field_codes(block.para.runs):
                run_text = self._parse_run_with_offset(run)
                if run_text is None:
                    continue
                line += run_text

            lines.append(line)
        text = "\n".join(lines)

        out.write(f"<p>{text}</p>\n")

    def _parse_para(self, para: Para, out: IOBase):
        text = ""

        in_offset = False
        for run in self.remove_field_codes(para.runs):
            run_text = self._parse_run_with_offset(run)
            if run_text is None:
                continue
            text += run_text
            in_offset = True

        if not in_offset:
            return

        styles = []
        if (
            para.prop.alignment
            and para.prop.alignment != DocxHTMLFormatter.DEFAULT_ALIGN
        ):
            styles.append(f"text-align:{para.prop.alignment};")
        if para.prop.indent:
            indent = para.prop.indent
            abs_first_indent = indent.abs_first_indent
            rel_first_indent = indent.rel_first_indent
            abs_left_indent = indent.abs_left_indent
            rel_left_indent = indent.rel_left_indent

            if rel_first_indent != 0:
                styles.append(f"text-indent:{rel_first_indent / 100}em;")
            elif abs_first_indent != 0:
                styles.append(f"text-indent:{abs_first_indent / 20}pt;")

            if rel_left_indent != 0:
                styles.append(f"margin-left:{rel_left_indent / 100}em;")
            elif abs_left_indent != 0:
                styles.append(f"margin-left:{abs_left_indent / 20}pt;")

        html_tag = "p"
        match para.prop.outline_level:
            case 1:
                html_tag = "h1"
            case 2:
                html_tag = "h2"
            case 3:
                html_tag = "h3"
            case 4:
                html_tag = "h4"
            case 5:
                html_tag = "h5"

        if len(styles) > 0:
            style_attr = " ".join(styles)
            out.write(f'<{html_tag} style="{style_attr}">{text}</{html_tag}>\n')
        else:
            out.write(f"<{html_tag}>{text}</{html_tag}>\n")

    def _parse_run_with_offset(self, run: Run) -> str:
        text = self._offset_cleaner(run)
        if text is None:
            return None
        if text == "\x0b":
            return "<br/>"
        text = self._placeholder_cleaner(text)

        text = html.escape(text)

        prop = run.prop

        styles = []
        tags = []
        if prop.bold:
            tags.append(("b", "</b>"))

        if prop.italic:
            tags.append(("i", "</i>"))

        if prop.underline:
            tags.append(("u", "</u>"))

        if prop.strike:
            tags.append(("s", "</s>"))

        if prop.color and prop.color != DocxHTMLFormatter.DEFAULT_COLOR:
            try:
                color = colors.hex_to_name(prop.color)
            except Exception:
                color = prop.color[0:7]
            styles.append(f"color:{color}")

        if prop.size and prop.size != DocxHTMLFormatter.DEFAULT_SIZE:
            styles.append(f"font-size:{prop.size}pt")

        if (
            prop.font_east_asia
            and prop.font_east_asia != DocxHTMLFormatter.DEFAULT_FONT_EAST_ASIA
        ):
            styles.append(f"font-family:{prop.font_east_asia}")
        if prop.font_ascii and prop.font_ascii != DocxHTMLFormatter.DEFAULT_FONT_ASCII:
            styles.append(f"mso-ascii-font-family:{prop.font_ascii}")

        if len(styles) > 0 and len(tags) <= 0:
            tags.append(("span", "</span>"))

        style_str = f'style="{";".join(styles)}"' if styles else ""

        opening_tags = "".join(
            f"<{tag} {style_str}>" if i == 0 and style_str else f"<{tag}>"
            for i, (tag, _) in enumerate(reversed(tags))
        )
        closing_tags = "".join(closing for _, closing in tags)

        return f"{opening_tags}{text}{closing_tags}"

    def _remove_middle_lable(self, text: str) -> str:
        start_id = text.find(self.start_lable)
        end_id = text.rfind(self.end_lable)
        return (
            text[: start_id + len(self.start_lable)]
            + text[start_id + len(self.start_lable) : end_id]
            .replace(self.start_lable, "")
            .replace(self.end_lable, "")
            + text[end_id:]
        )


class SimpleHTMLFormatter(HTMLFormatter):
    def __init__(self, doc: Document):
        super().__init__(doc, "")
        self.doc: Document = doc
        self.content_len = 0

    def _parse_block(self, block: Block, out: IOBase):
        match block.type:
            case "para":
                self._parse_para(block.para, out)
            case "table":
                self._parse_table(block.table, out)
            case "textbox":
                self._parse_textbox(block.textbox, out)

    def _parse_table(self, table: Table, out: IOBase):
        out.write("<table>\n")
        for row in table.rows:
            out.write("<tr>")
            for cell in row.cells:
                cell_text = self._join_cell_text(cell)
                out.write(f"<td>{cell_text}</td>")
            out.write("</tr>\n")
        out.write("</table>\n")

    def _parse_run(self, run: Run) -> str:
        text = run.text
        self.content_len += len(text)
        text = re.sub(
            "[\x0b\x0d\x07\x0c\x0f\x0e\x02\x05\x08\x01\x13\x14\x15\x03\x04\x1a\x1b]+",
            "",
            text,
        )
        text = html.escape(text)

        prop = run.prop

        styles = []
        tags = []
        if prop.bold:
            tags.append(("b", "</b>"))
        if prop.italic:
            tags.append(("i", "</i>"))
        if prop.underline:
            tags.append(("u", "</u>"))
        if prop.strike:
            tags.append(("s", "</s>"))
        if prop.color != "#000000ff":
            try:
                color = colors.hex_to_name(prop.color)
            except Exception:
                color = prop.color[0:7]
            styles.append(f"color:{color}")
        if prop.size != 10.5:
            styles.append(f"font-size:{prop.size}pt")

        # if prop.font_ascii != "Calibri":
        #     styles.append(f"mso-ascii-font-family:{prop.font_ascii}")
        # if prop.font_east_asia != "宋体":
        #     styles.append(f"font-family:{prop.font_east_asia}")

        if len(styles) > 0 and len(tags) <= 0:
            tags.append(("span", "</span>"))

        style_str = f'style="{";".join(styles)}"' if styles else ""

        opening_tags = "".join(
            f"<{tag} {style_str}>" if i == 0 and style_str else f"<{tag}>"
            for i, (tag, _) in enumerate(reversed(tags))
        )
        closing_tags = "".join(closing for _, closing in tags)

        return f"{opening_tags}{text}{closing_tags}"


class SliceHtmlFormatter(HTMLFormatter):
    def __init__(self, doc: Document, media_dir: str, with_note: bool = False):
        super().__init__(doc, "")
        self.doc: Document = doc
        self.media_dir: str = media_dir
        self.images: dict[str, bytes] = {}
        self.with_note: bool = with_note

    def format(self, out: IOBase):
        for container in self.doc.slide_containers:
            if container.category == "slides":
                # 渲染正文幻灯片和备注
                self._parse_slide_container(container, out)

    def _parse_slide_container(self, slide_container: SlideContainer, out: IOBase):
        out.write(f"<slides>\n")
        for i, slide in enumerate(slide_container.slides):
            self._render_slide(slide, i + 1, out)
        out.write(f"</slides>\n")

    def _render_slide(self, slide: Slide, slide_id, out: IOBase):
        out.write(f'<slide index="{slide_id}">\n')

        def sort_blocks(blocks):
            return sorted(
                blocks,
                key=lambda block: (
                    block["bounding_box"]["y1"],
                    block["bounding_box"]["x1"],
                ),
            )

        for block in sort_blocks(slide.shape_tree):
            self._parse_block(block, out)
        if self.with_note:
            out.write(f"<note>")
            for block in slide.note_page:
                self._parse_block(block, out)
            out.write(f"</note>\n")
        out.write(f"</slide>\n")

    def _parse_block(self, block: Block, out: IOBase):
        match block.type:
            case "para":
                self._parse_para(block.para, out)
            case "table":
                self._parse_table(block.table, out)
            case "textbox":
                self._parse_textbox(block.textbox, out)

    def _parse_para(self, para: Para, out: IOBase):
        text = ""
        for run in para.runs:
            text += self._parse_run(run)
        if text.strip() == "":
            print(text.strip())
            return
        return super()._parse_para(run, out)
    def _parse_table(self, table: Table, out: IOBase):
        out.write("<table>\n")
        for row in table.rows:
            msg = ""
            for cell in row.cells:
                print(cell)
                cell_text = self._join_cell_text(cell)
                if len(cell_text.strip()) > 0:
                    msg += f"<td>{cell_text}</td>"
            if len(msg) > 0:
                out.write(f"<tr>\n{msg}</tr>\n")
        out.write("</table>\n")

    def _join_cell_text(self, cell: TableCell) -> str:
        texts = []
        for block in cell.blocks:
            if block.type == "para":
                para_text = ""
                for run in block.para.runs:
                    para_text += self._parse_run(run)
                texts.append(para_text + " ")
            if block.type == "textbox":
                for text_box in block.textbox.blocks:
                    para_text = ""
                    for run in text_box.para.runs:
                        para_text += self._parse_run(run)
                    texts.append(para_text + " ")
        return " ".join(texts)

    def _parse_textbox(self, textbox: Textbox, out: IOBase):
        lines = []
        for block in textbox.blocks:
            if block.type != "para":
                continue
            line = ""
            for run in block.para.runs:
                line += self._parse_run(run)
            if line.strip() != "":
                lines.append(line)
        if len(lines) <= 0:
            return
        text = "\n".join(lines)
        out.write(f"<p>\n{text}\n</p>\n")

    def _parse_para(self, para: Para, out: IOBase):
        text = ""
        for run in para.runs:
            text += self._parse_run(run)
        text = text.strip()
        html_tag = "p"
        match para.prop.outline_level:
            case 1:
                html_tag = "h1"
            case 2:
                html_tag = "h2"
            case 3:
                html_tag = "h3"
            case 4:
                html_tag = "h4"
            case 5:
                html_tag = "h5"
        out.write(f"<{html_tag}>{text}</{html_tag}>\n")

    def _parse_run(self, run):
        # 将母版内容进行过滤
        special_strings = [
            "a click to unlimited possibilities",
            "A CLICK TO UNLIMITED POSSIBILITIES",
            "单击此处",
            "添加副标题",
            "添加文档副标题",
            "单击此处编辑母版文本样式",
            "第二级",
            "第三级",
            "第四级",
            "第五级",
        ]
        text = run.text
        if text in special_strings:
            return ""
        text = run.text
        self.content_len += len(text)
        text = re.sub(
            "[\x0b\x0d\x07\x0c\x0f\x0e\x02\x05\x08\x01\x13\x14\x15\x03\x04\x1a\x1b]+",
            "",
            text,
        )
        text = html.escape(text)
        return f"<p>{text}</p>"


class XlsxHtmlFormatter(HTMLFormatter):
    def __init__(
        self,
        doc: Document,
        media_dir: str,
        max_rows: int = 20,
        max_cols: int = 20,
        max_length=30,
    ):
        super().__init__(doc, "")
        self.doc = doc
        self.media_dir = media_dir
        self.images = {}
        self.max_rows = max_rows
        self.max_cols = max_cols
        self.max_length = max_length

    def col_index_to_letter(self, index):
        column_letter = ""
        while index > 0:
            index, remainder = divmod(index - 1, 26)
            column_letter = chr(65 + remainder) + column_letter
        return column_letter

    def format(self, buf: IOBase):
        for i, sheet in enumerate(self.doc.sheets):
            if sheet.type != "grid":
                continue
            buf.write(f'<sheet name="{sheet.name}">\n<table>\n')
            for i, row in enumerate(sheet.data):
                if i >= self.max_rows:
                    break
                msg = ""
                for j, cell in enumerate(row.cells):
                    if j >= self.max_cols:
                        break
                    if "value" not in cell:
                        continue
                    else:
                        if cell.type == "shared":
                            idx = int(cell.value)
                            value = self.doc.shared_strings[idx].text()
                        else:
                            value = cell.value
                    if len(value) > 30:
                        value = value[:30] + "..."
                    if len(value) != 0:
                        msg += f"<td>{value}</td>"
                if len(msg) > 0:
                    buf.write(f"<tr>\n{msg}</tr>\n")
            buf.write(f"</table>\n</sheet>\n")


class EasyDocxHTMLFormatter(HTMLFormatter):
    def __init__(self, doc: Document):
        super().__init__(doc, "")
        self.doc: Document = doc
        self.content_len = 0

    def _parse_block(self, block: Block, out: IOBase):
        match block.type:
            case "para":
                self._parse_para(block.para, out)
            case "table":
                self._parse_table(block.table, out)
            case "textbox":
                self._parse_textbox(block.textbox, out)

    def _parse_para(self, para: Para, out: IOBase):
        text = ""
        for run in para.runs:
            text += self._parse_run(run)
        text = text.strip()
        html_tag = "p"
        match para.prop.outline_level:
            case 1:
                html_tag = "h1"
            case 2:
                html_tag = "h2"
            case 3:
                html_tag = "h3"
            case 4:
                html_tag = "h4"
            case 5:
                html_tag = "h5"
        out.write(f"<{html_tag}>{text}</{html_tag}>\n")

    def _parse_table(self, table: Table, out: IOBase):
        out.write("<table>\n")
        for row in table.rows:
            msg = ""
            for cell in row.cells:
                cell_text = self._join_cell_text(cell)
                if len(cell_text.strip()) > 0:
                    msg += f"<td>{cell_text}</td>"
            if len(msg) > 0:
                out.write(f"<tr>\n{msg}</tr>\n")
        out.write("</table>\n")

    def _join_cell_text(self, cell: TableCell) -> str:
        texts = []
        for block in cell.blocks:
            if block.type == "para":
                para_text = ""
                for run in block.para.runs:
                    para_text += self._parse_run(run)
                texts.append(para_text + " ")
            if block.type == "textbox":
                for text_box in block.textbox.blocks:
                    para_text = ""
                    for run in text_box.para.runs:
                        para_text += self._parse_run(run)
                    texts.append(para_text + " ")
        return " ".join(texts)
    
    def _parse_textbox(self, textbox: Textbox, out: IOBase):
        lines = []
        for block in textbox.blocks:
            if block.type != "para":
                continue
            line = ""
            for run in block.para.runs:
                line += self._parse_run(run)
            lines.append(line)

        text = "\n".join(lines)
        out.write(f"<p>{text}</p>\n")

    def _parse_run(self, run: Run) -> str:
        text = run.text
        self.content_len += len(text)
        text = re.sub(
            "[\x0b\x0d\x07\x0c\x0f\x0e\x02\x05\x08\x01\x13\x14\x15\x03\x04\x1a\x1b]+",
            "",
            text,
        )
        text = html.escape(text)
        return f"<p>{text}</p>"


class MarkdownFormatter:
    def __init__(self, doc: Document, media_dir: str):
        self.doc = doc
        self.media_dir = media_dir
        self.images = {}

    def format(self, out: IOBase):
        self._parse_node(self.doc.tree, out)

    def _parse_node(self, node: Node, out: IOBase):
        for n in node.blocks:
            self._parse_block(n, out)
        for c in node.children:
            self._parse_node(c, out)

    def _parse_block(self, block: Block, out: IOBase):
        match block.type:
            case "para":
                self._parse_para(block.para, out)
            case "table":
                self._parse_table(block.table, out)
            case "textbox":
                self._parse_textbox(block.textbox, out)
            case "component":
                self._parse_component(block.component, out)
            case "drawing":
                self._parse_drawing(block.component, out)

    def _join_cell_text(self, cell: TableCell) -> str:
        texts = []
        for block in cell.blocks:
            if block.type != "para":
                continue
            para_text = ""
            for run in block.para.runs:
                para_text += self._parse_run(run)
            texts.append(para_text + "<br>")
        return "<br>".join(texts)

    def _parse_table(self, table: Table) -> str:
        text = "\n<table>\n"
        for row in table.rows:
            text += "<tr>"
            for cell in row.cells:
                cell_text = self._join_cell_text(cell)
                text += f'<td rowspan="{cell.row_span}" colspan="{cell.col_span}">{cell_text}</td>'
            text += "</tr>\n"
        text += "</table>\n\n"
        return text

    def _parse_textbox(self, textbox: Textbox) -> str:
        lines = []
        for block in textbox.blocks:
            if block.type != "para":
                continue

            line = ""
            for run in block.para.runs:
                line += run.text
            lines.append(line)

        text = "\n".join(lines)
        return text + "\n\n"

    def _parse_drawing(self, block: Drawing, out: IOBase):
        t = block.type
        if t == "image":
            media = self.doc.media(block.media_id)
            if media.url:
                url = media.url.replace("ks3-cn-beijing-internal", "ks3-cn-beijing")
                out.write(f"![]({url})\n\n")
            elif media.data:
                self.images[media.id] = base64decode(media.data)
                out.write(f"![]({self.media_dir}/{media.id})\n\n")

    def _parse_component(self, block: Component, out: IOBase):
        t = block.type
        if t == "image":
            media = self.doc.media(block.media_id)
            if media.url:
                url = media.url.replace("ks3-cn-beijing-internal", "ks3-cn-beijing")
                out.write(f"![]({url})\n\n")
            elif media.data:
                self.images[media.id] = base64decode(media.data)
                out.write(f"![]({self.media_dir}/{media.id})\n\n")

    def _parse_para(self, para: Para) -> str:
        text = ""
        match para.prop.outline_level:
            case 1:
                text += "# "
            case 2:
                text += "## "
            case 3:
                text += "### "
            case 4:
                text += "#### "
            case 5:
                text += "##### "

        for run in para.runs:
            text += self._parse_run(run)

        text += "\n\n"
        return text

    def _parse_run(self, run: Run) -> str:
        text = run.text
        prop = run.prop

        if prop.bold:
            text = f"**{text}**"
        if prop.italic:
            text = f"){text}_"
        if prop.underline:
            text = f"<u>{text}</u>"
        if prop.strike:
            text = f"~~{text}~~"

        return text

    def format(self, out: IOBase):
        self._parse_node(self.doc.tree, out)


class Workbook(dict):
    @property
    def sheets(self) -> list[Sheet]:
        return _to_class_list(self, "sheets", Sheet)

    @property
    def shared_strings(self) -> list[SharedString]:
        return _to_class_list(self, "shared_strings", SharedString)

    def to_json(self, max_rows: int = 100, max_cols: int = 20) -> dict:
        workbook = {"sheets": []}
        for i, sheet in enumerate(self.sheets):
            if sheet.type != "grid":
                continue

            cells = {}
            _sheet = {
                "name": sheet.name,
                "index": i + 1,
                "used_range": sheet.used_range.address(),
                "cells": cells,
            }

            for i, row in enumerate(sheet.data):
                if i >= max_rows:
                    break
                for j, cell in enumerate(row.cells):
                    if j >= max_cols:
                        break
                    if "value" not in cell:
                        continue
                    if cell.type == "shared":
                        idx = int(cell.value)
                        value = self.shared_strings[idx].text()
                    else:
                        value = cell.value

                    area = sheet.merge_area(row.row_index, cell.col_index)
                    if area is None:
                        addr = f"{decimal_to_base26(cell.col_index)}{row.row_index}"
                    else:
                        addr = area.address()
                    cells[addr] = value

            workbook["sheets"].append(_sheet)
        return workbook

        # 列索引转换为字母（A, B, C, ..., AA, AB, ...）

    def col_index_to_letter(self, index):
        column_letter = ""
        while index > 0:
            index, remainder = divmod(index - 1, 26)
            column_letter = chr(65 + remainder) + column_letter
        return column_letter

    def to_html(self, max_rows: int = 100, max_cols: int = 20) -> str:
        buf = StringIO()
        for i, sheet in enumerate(self.sheets):
            if sheet.type != "grid":
                continue
            buf.write(f'<sheet name="{sheet.name}" index="{i + 1}">\n<table>\n')
            for i, row in enumerate(sheet.data):
                if i >= max_rows:
                    break
                buf.write(f'<tr index="{row.row_index + 1}">\n')
                for j, cell in enumerate(row.cells):
                    if j >= max_cols:
                        break
                    if "value" not in cell:
                        value = ""
                    else:
                        if cell.type == "shared":
                            idx = int(cell.value)
                            value = self.shared_strings[idx].text()
                        else:
                            value = cell.value

                    row_span_str = ""
                    col_span_str = ""
                    row_span, col_span = sheet.cell_span(row.row_index, cell.col_index)
                    if row_span > 1:
                        row_span_str = f' rowspan="{row_span}"'
                    if col_span > 1:
                        col_span_str = f' colspan="{col_span}"'

                    column_letter = self.col_index_to_letter(cell.col_index + 1)
                    cell_id = f'id="{column_letter}{row.row_index + 1}"'

                    buf.write(
                        f'<td {cell_id}{row_span_str}{col_span_str}index="{cell.col_index + 1}"{row_span_str}{col_span_str}>{value}</td>'
                    )
                buf.write("</tr>\n")
            buf.write(f"</table>\n</sheet>\n")
        return buf.getvalue()


def _bytes_hash(content: bytes) -> str:
    h = hashlib.sha1()
    h.update(content)
    return h.hexdigest()


def to_kdc(name: str, content: bytes, include_elements: str, use_cache: bool) -> dict:
    start_time = time.time()
    file_hash = _bytes_hash(content)
    cache_path = f".cache/kdc_{file_hash}.json"

    if use_cache and os.path.exists(cache_path):
        with open(cache_path, "r", encoding="utf8") as f:
            data = json.load(f)
        return data

    data = {
        "format": "kdc",
        "include_elements": include_elements,
        "filename": name,
    }
    files = {
        "form_file": [name, content],
    }
    resp = requests.post(
        "https://api.wps.cn/v7/longtask/exporter/export_file_content",
        files=files,
        data=data,
    )
    data = resp.json()["data"]
    if use_cache:
        if not os.path.exists(".cache"):
            os.mkdir(".cache")
        cache_data = json.dumps(data, ensure_ascii=False, indent="  ")
        with open(cache_path, "w+", encoding="utf8") as f:
            f.write(cache_data)

    end_time = time.time()
    execution_time = end_time - start_time
    print(f"to kdc time: {execution_time} seconds")
    return data


def parse_workbook(
    name: str, content: bytes, include_elements: str = "all", use_cache: bool = False
) -> Workbook:
    data = to_kdc(name, content, include_elements, use_cache)
    return Workbook(data["doc"])


def parse_document(
    name: str, content: bytes, include_elements: str = "all", use_cache: bool = False
) -> Document:
    data = to_kdc(name, content, include_elements, use_cache)
    if "medias" in data["doc"]:
        for m in data["doc"]["medias"]:
            if "url" in m and m["url"]:
                media_url = m["url"].replace(
                    "ks3-cn-beijing-internal", "ks3-cn-beijing"
                )
                resp = requests.get(media_url)
                if resp.status_code != 200:
                    raise Exception(
                        f"fetch media {media_url} failed with {resp.status_code}"
                    )
                m["data"] = base64.b64encode(resp.content).decode("utf8")
                m["url"] = ""

    doc = Document(data["doc"])
    return doc


if __name__ == "__main__":
    file_name = r"/home/kafai/tools/WPSCopilot/图片.docx"
    content = open(file_name, "rb").read()
    buf = StringIO()
    doc = parse_document(file_name, content, "all", use_cache=True)
    XlsxHtmlFormatter(doc, media_dir="").format(buf)
    print(buf.getvalue())