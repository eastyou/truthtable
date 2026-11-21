"""渲染层测试：表格行数、答案显隐与练习纸限制。"""

from __future__ import annotations

import unittest

from truthtable.model import build_table
from truthtable.render import render_sheet, render_table_html


class TableHtmlTest(unittest.TestCase):
    def test_row_count(self) -> None:
        html = render_table_html(build_table("A and B"))
        self.assertEqual(html.count("<tr>"), 5)

    def test_header_columns(self) -> None:
        html = render_table_html(build_table("A and B"))
        self.assertIn("<th>A</th><th>B</th><th>结果</th>", html)

    def test_result_cells_blank(self) -> None:
        html = render_table_html(build_table("A and B"))
        self.assertEqual(html.count('<td class="result"></td>'), 4)

    def test_result_cells_filled(self) -> None:
        html = render_table_html(build_table("A and B"), answers=True)
        self.assertEqual(html.count('<td class="result"></td>'), 0)
        self.assertEqual(html.count('result filled'), 4)

    def test_false_before_true_order(self) -> None:
        html = render_table_html(build_table("A"))
        rows = html.split("<tbody>")[1]
        self.assertLess(rows.index("F"), rows.index("T"))

    def test_rejects_wrong_type(self) -> None:
        with self.assertRaises(ValueError):
            render_table_html("A and B")  # type: ignore[arg-type]


class SheetTest(unittest.TestCase):
    def test_cards_and_tables(self) -> None:
        html = render_sheet(["A and B", "A or B"])
        self.assertEqual(html.count('<div class="card">'), 2)
        self.assertEqual(html.count("<table"), 2)

    def test_answers_hidden(self) -> None:
        html = render_sheet(["A and B"])
        self.assertNotIn("参考答案", html)
        self.assertNotIn("result filled", html)

    def test_answers_page(self) -> None:
        html = render_sheet(["A and B"], answers=True)
        self.assertIn("参考答案", html)
        self.assertIn("filled", html)

    def test_tautology_tag(self) -> None:
        html = render_sheet(["A or not A"], answers=True)
        self.assertIn("重言式", html)

    def test_contradiction_tag(self) -> None:
        html = render_sheet(["A and not A"], answers=True)
        self.assertIn("矛盾式", html)

    def test_satisfiable_tag(self) -> None:
        html = render_sheet(["A and B"], answers=True)
        self.assertIn("可满足式", html)

    def test_expression_is_escaped(self) -> None:
        html = render_sheet(["A -> B"])
        self.assertIn("A -&gt; B", html)
        self.assertNotIn("A -> B", html)

    def test_title_is_escaped(self) -> None:
        html = render_sheet(["A"], title="<b>x</b>")
        self.assertIn("&lt;b&gt;", html)

    def test_empty_rejected(self) -> None:
        with self.assertRaises(ValueError):
            render_sheet([])

    def test_too_many_expressions(self) -> None:
        with self.assertRaises(ValueError):
            render_sheet(["A"] * 11)

    def test_too_many_variables(self) -> None:
        with self.assertRaises(ValueError):
            render_sheet(["A and B and C and D and E"])

    def test_print_css(self) -> None:
        html = render_sheet(["A"])
        self.assertIn("@page", html)
        self.assertIn("@media print", html)


if __name__ == "__main__":
    unittest.main()
