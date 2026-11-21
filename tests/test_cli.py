"""命令行测试：真值表输出、表达式分析与练习纸生成。"""

from __future__ import annotations

import contextlib
import io
import tempfile
import unittest
from pathlib import Path

from truthtable.cli import main


class EvalCommandTest(unittest.TestCase):
    def test_prints_table(self) -> None:
        buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer):
            code = main(["eval", "A and B"])
        output = buffer.getvalue()
        self.assertEqual(code, 0)
        self.assertIn("A B", output)
        self.assertEqual(len(output.strip().splitlines()), 5)

    def test_tf_symbols(self) -> None:
        buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer):
            code = main(["eval", "A", "--symbols", "tf"])
        self.assertEqual(code, 0)
        self.assertIn("T", buffer.getvalue())
        self.assertIn("F", buffer.getvalue())

    def test_invalid_expression(self) -> None:
        error = io.StringIO()
        with contextlib.redirect_stderr(error):
            code = main(["eval", "A and"])
        self.assertEqual(code, 2)
        self.assertIn("参数错误", error.getvalue())


class InfoCommandTest(unittest.TestCase):
    def test_tautology(self) -> None:
        buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer):
            code = main(["info", "A or not A"])
        output = buffer.getvalue()
        self.assertEqual(code, 0)
        self.assertIn("重言式", output)
        self.assertIn("行数：2", output)

    def test_contradiction(self) -> None:
        buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer):
            main(["info", "A and not A"])
        self.assertIn("矛盾式", buffer.getvalue())

    def test_three_variables(self) -> None:
        buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer):
            main(["info", "A and (B or C)"])
        output = buffer.getvalue()
        self.assertIn("变量：A B C", output)
        self.assertIn("行数：8", output)


class SheetCommandTest(unittest.TestCase):
    def _expressions(self, directory: str) -> Path:
        path = Path(directory) / "expressions.txt"
        path.write_text(
            "# 课堂练习\nA and B\nA or not B\nA -> B\n", encoding="utf-8"
        )
        return path

    def test_writes_sheet(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            source = self._expressions(tmp)
            target = Path(tmp) / "out" / "sheet.html"
            buffer = io.StringIO()
            with contextlib.redirect_stdout(buffer):
                code = main(["sheet", str(source), "-o", str(target)])
            self.assertEqual(code, 0)
            content = target.read_text(encoding="utf-8")
            self.assertEqual(content.count('<div class="card">'), 3)
            self.assertNotIn("参考答案", content)
            self.assertIn("已生成", buffer.getvalue())

    def test_answers_flag(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            source = self._expressions(tmp)
            target = Path(tmp) / "sheet.html"
            main(["sheet", str(source), "-o", str(target), "--answers"])
            content = target.read_text(encoding="utf-8")
            self.assertIn("参考答案", content)
            self.assertIn("filled", content)

    def test_missing_file(self) -> None:
        error = io.StringIO()
        with contextlib.redirect_stderr(error):
            code = main(["sheet", "/no/such/expressions.txt"])
        self.assertEqual(code, 2)
        self.assertIn("无法读取表达式文件", error.getvalue())

    def test_bad_expression_in_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "bad.txt"
            source.write_text("A and\n", encoding="utf-8")
            error = io.StringIO()
            with contextlib.redirect_stderr(error):
                code = main(["sheet", str(source), "-o", str(Path(tmp) / "x.html")])
            self.assertEqual(code, 2)

    def test_title_option(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            source = self._expressions(tmp)
            target = Path(tmp) / "sheet.html"
            main(["sheet", str(source), "-o", str(target), "--title", "逻辑小测"])
            self.assertIn("逻辑小测", target.read_text(encoding="utf-8"))


class ParserTest(unittest.TestCase):
    def test_help_exits_zero(self) -> None:
        with contextlib.redirect_stdout(io.StringIO()):
            with self.assertRaises(SystemExit) as caught:
                main(["--help"])
        self.assertEqual(caught.exception.code, 0)

    def test_missing_command_exits(self) -> None:
        with contextlib.redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit):
                main([])


if __name__ == "__main__":
    unittest.main()
