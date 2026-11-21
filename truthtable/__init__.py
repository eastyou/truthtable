"""truthtable：布尔表达式解析、真值表与练习纸。"""

from .model import (
    MAX_VARIABLES,
    TruthTable,
    TruthTableError,
    build_table,
    evaluate,
    format_table,
    parse,
    parse_expression_lines,
    tokenize,
)
from .render import render_sheet, render_table_html

__all__ = [
    "MAX_VARIABLES",
    "TruthTable",
    "TruthTableError",
    "build_table",
    "evaluate",
    "format_table",
    "parse",
    "parse_expression_lines",
    "tokenize",
    "render_sheet",
    "render_table_html",
]

__version__ = "0.1.0"
