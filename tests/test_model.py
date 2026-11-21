"""模型层测试：词法、优先级、求值、真值表与错误处理。"""

from __future__ import annotations

import unittest

from truthtable.model import (
    TruthTableError,
    build_table,
    evaluate,
    format_table,
    parse,
    parse_expression_lines,
    tokenize,
)


def val(expression: str, **assignment: bool) -> bool:
    return evaluate(expression, assignment)


class TokenizeTest(unittest.TestCase):
    def test_letters_become_variables(self) -> None:
        tokens = tokenize("a")
        self.assertEqual(tokens[0].kind, "VAR")
        self.assertEqual(tokens[0].text, "A")

    def test_keyword_operators(self) -> None:
        kinds = [token.kind for token in tokenize("A and B or not C")]
        self.assertEqual(kinds, ["VAR", "AND", "VAR", "OR", "NOT", "VAR", "EOF"])

    def test_symbol_operators(self) -> None:
        kinds = [token.kind for token in tokenize("A && B || !C ^ D -> E <-> F")]
        self.assertEqual(
            kinds,
            [
                "VAR",
                "AND",
                "VAR",
                "OR",
                "NOT",
                "VAR",
                "XOR",
                "VAR",
                "IMPLIES",
                "VAR",
                "IFF",
                "VAR",
                "EOF",
            ],
        )

    def test_unicode_operators(self) -> None:
        kinds = [token.kind for token in tokenize("¬A ∧ B ∨ C → D ↔ E ⊕ F")]
        self.assertEqual(
            kinds,
            [
                "NOT",
                "VAR",
                "AND",
                "VAR",
                "OR",
                "VAR",
                "IMPLIES",
                "VAR",
                "IFF",
                "VAR",
                "XOR",
                "VAR",
                "EOF",
            ],
        )

    def test_reject_non_string(self) -> None:
        with self.assertRaises(TruthTableError):
            tokenize(None)  # type: ignore[arg-type]

    def test_reject_empty(self) -> None:
        with self.assertRaises(TruthTableError):
            tokenize("   ")

    def test_reject_long_expression(self) -> None:
        with self.assertRaises(TruthTableError):
            tokenize("A" * 501)

    def test_reject_unknown_character(self) -> None:
        with self.assertRaises(TruthTableError):
            tokenize("A @ B")

    def test_reject_multi_letter_word(self) -> None:
        with self.assertRaises(TruthTableError):
            tokenize("A and foo")

    def test_positions_are_recorded(self) -> None:
        tokens = tokenize("A and B")
        self.assertEqual(tokens[1].position, 2)


class OperatorTest(unittest.TestCase):
    def test_and(self) -> None:
        self.assertTrue(val("A and B", A=True, B=True))
        self.assertFalse(val("A and B", A=True, B=False))

    def test_or(self) -> None:
        self.assertTrue(val("A or B", A=False, B=True))
        self.assertFalse(val("A or B", A=False, B=False))

    def test_not(self) -> None:
        self.assertTrue(val("not A", A=False))
        self.assertFalse(val("not A", A=True))

    def test_xor(self) -> None:
        self.assertTrue(val("A xor B", A=True, B=False))
        self.assertFalse(val("A xor B", A=True, B=True))

    def test_implication_truth_table(self) -> None:
        self.assertFalse(val("A -> B", A=True, B=False))
        self.assertTrue(val("A -> B", A=False, B=False))
        self.assertTrue(val("A -> B", A=False, B=True))
        self.assertTrue(val("A -> B", A=True, B=True))

    def test_biconditional(self) -> None:
        self.assertTrue(val("A <-> B", A=True, B=True))
        self.assertTrue(val("A <-> B", A=False, B=False))
        self.assertFalse(val("A <-> B", A=True, B=False))

    def test_star_and_plus(self) -> None:
        self.assertTrue(val("A * B", A=True, B=True))
        self.assertTrue(val("A + B", A=False, B=True))


class PrecedenceTest(unittest.TestCase):
    def test_and_before_or(self) -> None:
        self.assertTrue(val("A or B and C", A=True, B=False, C=False))
        self.assertFalse(val("(A or B) and C", A=True, B=False, C=False))

    def test_not_binds_tighter_than_and(self) -> None:
        self.assertFalse(val("not A and B", A=True, B=False))
        self.assertTrue(val("not (A and B)", A=True, B=False))

    def test_implies_is_right_associative(self) -> None:
        self.assertTrue(val("A -> B -> C", A=False, B=False, C=False))

    def test_iff_is_lowest(self) -> None:
        self.assertFalse(val("A -> B <-> C", A=False, B=True, C=False))

    def test_parentheses_override(self) -> None:
        self.assertTrue(val("not (A or B)", A=False, B=False))

    def test_double_negation(self) -> None:
        self.assertTrue(val("not not A", A=True))


class ErrorTest(unittest.TestCase):
    def test_missing_operand(self) -> None:
        with self.assertRaises(TruthTableError):
            parse("A and")

    def test_unbalanced_left(self) -> None:
        with self.assertRaises(TruthTableError):
            parse("(A and B")

    def test_unbalanced_right(self) -> None:
        with self.assertRaises(TruthTableError):
            parse("A and B)")

    def test_trailing_tokens(self) -> None:
        with self.assertRaises(TruthTableError):
            parse("A B")

    def test_empty_parentheses(self) -> None:
        with self.assertRaises(TruthTableError):
            parse("()")

    def test_missing_assignment(self) -> None:
        with self.assertRaises(TruthTableError):
            evaluate("A and B", {"A": True})

    def test_non_boolean_assignment(self) -> None:
        with self.assertRaises(TruthTableError):
            evaluate("A", {"A": 1})  # type: ignore[dict-item]

    def test_invalid_key(self) -> None:
        with self.assertRaises(TruthTableError):
            evaluate("A", {"AB": True})

    def test_non_mapping(self) -> None:
        with self.assertRaises(TruthTableError):
            evaluate("A", None)  # type: ignore[arg-type]

    def test_too_many_variables(self) -> None:
        expression = " and ".join("ABCDEFGHI")
        with self.assertRaises(TruthTableError):
            build_table(expression)


class TableTest(unittest.TestCase):
    def test_variables_sorted(self) -> None:
        table = build_table("C and A or B")
        self.assertEqual(table.variables, ("A", "B", "C"))

    def test_row_count(self) -> None:
        self.assertEqual(build_table("A and B").row_count, 4)
        self.assertEqual(build_table("A or B or C").row_count, 8)

    def test_row_order(self) -> None:
        table = build_table("A and B")
        self.assertEqual(
            [values for values, _ in table.rows],
            [(False, False), (False, True), (True, False), (True, True)],
        )

    def test_and_results(self) -> None:
        table = build_table("A and B")
        self.assertEqual(table.results, (False, False, False, True))

    def test_tautology(self) -> None:
        table = build_table("A or not A")
        self.assertTrue(table.is_tautology)
        self.assertTrue(table.is_satisfiable)

    def test_contradiction(self) -> None:
        table = build_table("A and not A")
        self.assertTrue(table.is_contradiction)
        self.assertFalse(table.is_satisfiable)

    def test_neither(self) -> None:
        table = build_table("A")
        self.assertFalse(table.is_tautology)
        self.assertFalse(table.is_contradiction)
        self.assertTrue(table.is_satisfiable)

    def test_to_dict(self) -> None:
        data = build_table("A and B").to_dict()
        self.assertEqual(data["variables"], ["A", "B"])
        self.assertEqual(len(data["rows"]), 4)
        self.assertEqual(data["rows"][-1]["assignment"], {"A": True, "B": True})
        self.assertTrue(data["rows"][-1]["result"])

    def test_format_ascii(self) -> None:
        text = format_table(build_table("A and B"))
        lines = text.splitlines()
        self.assertEqual(len(lines), 5)
        self.assertIn("A B", lines[0])
        self.assertTrue(lines[-1].endswith("1"))

    def test_format_tf_symbols(self) -> None:
        text = format_table(build_table("A"), symbols="tf")
        self.assertIn("T", text)
        self.assertIn("F", text)

    def test_format_rejects_symbols(self) -> None:
        with self.assertRaises(TruthTableError):
            format_table(build_table("A"), symbols="yes")


class ExpressionLinesTest(unittest.TestCase):
    def test_comments_and_blanks(self) -> None:
        text = "# 题目\nA and B\n\nB or not A  # 第二题\n"
        self.assertEqual(
            parse_expression_lines(text),
            ["A and B", "B or not A"],
        )

    def test_empty_raises(self) -> None:
        with self.assertRaises(TruthTableError):
            parse_expression_lines("\n# 只有注释\n")

    def test_invalid_line_raises(self) -> None:
        with self.assertRaises(TruthTableError):
            parse_expression_lines("A and B\nA @ B")

    def test_non_string_raises(self) -> None:
        with self.assertRaises(TruthTableError):
            parse_expression_lines(3)  # type: ignore[arg-type]


if __name__ == "__main__":
    unittest.main()
