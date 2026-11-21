"""真值表的 HTML 排版与 A4 练习纸。"""

from __future__ import annotations

import html
from typing import List, Sequence

from .model import TruthTable, TruthTableError, build_table

MAX_SHEET_ITEMS = 10
MAX_SHEET_VARIABLES = 4


def _mark(value: bool) -> str:
    return "T" if value else "F"


def render_table_html(table: TruthTable, answers: bool = False) -> str:
    """把一张真值表渲染成 HTML 表格，未作答时结果列留空。"""

    if not isinstance(table, TruthTable):
        raise TruthTableError("table 必须是 TruthTable")
    head = "".join("<th>%s</th>" % html.escape(name) for name in table.variables)
    head += "<th>结果</th>"
    body: List[str] = []
    for values, result in table.rows:
        cells = "".join("<td>%s</td>" % _mark(value) for value in values)
        if answers:
            cells += '<td class="result filled">%s</td>' % _mark(result)
        else:
            cells += '<td class="result"></td>'
        body.append("<tr>%s</tr>" % cells)
    return (
        '<table class="tt"><thead><tr>%s</tr></thead><tbody>%s</tbody></table>'
        % (head, "".join(body))
    )


def _classify(table: TruthTable) -> str:
    if table.is_tautology:
        return "重言式"
    if table.is_contradiction:
        return "矛盾式"
    return "可满足式"


def render_sheet(
    expressions: Sequence[str],
    title: str = "真值表练习",
    answers: bool = False,
) -> str:
    """生成 A4 练习纸；answers 为真时附加完整答案页。"""

    if not expressions:
        raise TruthTableError("至少需要一个表达式")
    if len(expressions) > MAX_SHEET_ITEMS:
        raise TruthTableError("一张练习纸最多 %d 道题" % MAX_SHEET_ITEMS)
    tables: List[TruthTable] = []
    for expression in expressions:
        table = build_table(expression)
        if len(table.variables) > MAX_SHEET_VARIABLES:
            raise TruthTableError(
                "练习纸最多支持 %d 个变量：%s" % (MAX_SHEET_VARIABLES, expression)
            )
        tables.append(table)

    safe_title = html.escape(title)
    cards: List[str] = []
    for index, table in enumerate(tables, start=1):
        cards.append(
            '<div class="card"><div class="no">%d</div>'
            '<div class="expr"><code>%s</code></div>%s'
            '<div class="question">判断：□ 重言式　□ 矛盾式　□ 可满足式</div></div>'
            % (index, html.escape(table.expression), render_table_html(table))
        )

    answer_block = ""
    if answers:
        items: List[str] = []
        for index, table in enumerate(tables, start=1):
            items.append(
                '<div class="answer-item"><h3>%d. %s <span class="tag">%s</span></h3>%s</div>'
                % (
                    index,
                    html.escape(table.expression),
                    _classify(table),
                    render_table_html(table, answers=True),
                )
            )
        answer_block = (
            '<section class="answers"><h2>参考答案</h2>%s</section>' % "".join(items)
        )

    return """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>%s</title>
<style>
  @page { size: A4; margin: 10mm; }
  * { box-sizing: border-box; }
  body { margin: 0; background: #eef0f4; color: #22262e;
         font-family: "Noto Sans SC", "PingFang SC", "Microsoft YaHei", sans-serif; }
  .sheet { width: 190mm; margin: 0 auto; background: #fff; padding: 8mm;
           box-shadow: 0 2px 12px rgba(0,0,0,.12); }
  h1 { font-size: 21px; margin: 0 0 2mm; }
  .hint { font-size: 12px; color: #666; margin-bottom: 4mm; }
  .meta { font-size: 12px; display: flex; gap: 8mm; margin-bottom: 4mm; }
  .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 3mm; }
  .card { border: 1px solid #dde1e8; border-radius: 3px; padding: 3mm;
          position: relative; break-inside: avoid; page-break-inside: avoid; }
  .card .no { position: absolute; right: 2mm; top: 2mm; color: #aab; font-size: 12px; }
  .expr { font-size: 14px; margin-bottom: 2mm; padding-right: 8mm; }
  .expr code { font-family: "SFMono-Regular", Consolas, monospace; color: #1a4d8f; }
  table.tt { width: 100%%; border-collapse: collapse; font-size: 12px;
             font-family: "SFMono-Regular", Consolas, monospace; }
  table.tt th, table.tt td { border: 1px solid #c9cfda; padding: 1mm 0;
                             text-align: center; }
  table.tt th { background: #f2f5fa; font-weight: 600; }
  table.tt td.result { width: 18mm; }
  table.tt td.filled { background: #f7f9fc; }
  .question { font-size: 11px; color: #556; margin-top: 2mm; }
  .answers { margin-top: 6mm; page-break-before: always; }
  .answers h2 { font-size: 17px; margin: 0 0 3mm; }
  .answer-item { margin-bottom: 4mm; break-inside: avoid; }
  .answer-item h3 { font-size: 13px; margin: 0 0 1.5mm; font-family: monospace; }
  .tag { font-family: inherit; font-size: 11px; font-weight: normal;
         color: #8a5a00; background: #fff3d6; padding: 0 2mm; border-radius: 2px; }
  @media print { body { background: #fff; } .sheet { box-shadow: none;
                 width: auto; padding: 0; } }
</style>
</head>
<body>
<div class="sheet">
  <h1>%s</h1>
  <div class="hint">按变量取值逐行填入 T / F，并判断表达式属于哪一类。</div>
  <div class="meta"><span>姓名：____________</span><span>班级：____________</span>
    <span>日期：____________</span></div>
  <div class="grid">%s</div>
  %s
</div>
</body>
</html>
""" % (safe_title, safe_title, "".join(cards), answer_block)
