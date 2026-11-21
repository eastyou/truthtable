"""命令行入口：打印真值表、分析表达式或生成练习纸。"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Optional, Sequence

from .model import (
    TruthTableError,
    build_table,
    format_table,
    parse_expression_lines,
)
from .render import render_sheet


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="truthtable",
        description="真值表工具：解析布尔表达式，打印真值表或生成可打印练习纸。",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    eval_cmd = sub.add_parser("eval", help="打印表达式的真值表")
    eval_cmd.add_argument("expression", help="布尔表达式，如 'A and (B or not C)'")
    eval_cmd.add_argument("--symbols", choices=["10", "tf"], default="10", help="结果符号")

    info = sub.add_parser("info", help="显示变量、行数与表达式类型")
    info.add_argument("expression", help="布尔表达式")

    sheet = sub.add_parser("sheet", help="生成 A4 真值表练习纸")
    sheet.add_argument("expressions", help="表达式文件，每行一个，支持 # 注释")
    sheet.add_argument("-o", "--output", default="truthtable-sheet.html")
    sheet.add_argument("--title", default="真值表练习")
    sheet.add_argument("--answers", action="store_true", help="附加答案页")
    return parser


def _read_lines(path: str) -> str:
    try:
        return Path(path).read_text(encoding="utf-8")
    except OSError as exc:
        raise TruthTableError("无法读取表达式文件：%s" % exc)
    except UnicodeDecodeError as exc:
        raise TruthTableError("文件编码不是 UTF-8：%s" % exc)


def _write(path: str, content: str) -> int:
    try:
        target = Path(path)
        if target.parent and not target.parent.exists():
            target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
    except OSError as exc:
        print("写入失败：%s" % exc, file=sys.stderr)
        return 1
    print("已生成 %s" % path)
    return 0


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        if args.command == "eval":
            table = build_table(args.expression)
            print(format_table(table, args.symbols))
            return 0

        if args.command == "info":
            table = build_table(args.expression)
            if table.is_tautology:
                kind = "重言式"
            elif table.is_contradiction:
                kind = "矛盾式"
            else:
                kind = "可满足式"
            print("表达式：%s" % table.expression)
            print("变量：%s" % (" ".join(table.variables) if table.variables else "无"))
            print("行数：%d" % table.row_count)
            print("类型：%s" % kind)
            print("可满足：%s" % ("是" if table.is_satisfiable else "否"))
            return 0

        if args.command == "sheet":
            expressions = parse_expression_lines(_read_lines(args.expressions))
            content = render_sheet(expressions, title=args.title, answers=args.answers)
            return _write(args.output, content)
    except TruthTableError as exc:
        print("参数错误：%s" % exc, file=sys.stderr)
        return 2

    print("未知命令", file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main())
