"""布尔表达式解析、求值与真值表。

支持的运算符（优先级由低到高）：
``<->`` / ``iff``、``->`` / ``implies``、``or`` / ``|``、``xor`` / ``^``、
``and`` / ``&``、``not`` / ``!``。变量为单个英文字母，不区分大小写。
"""

from __future__ import annotations

import itertools
from dataclasses import dataclass
from typing import Dict, List, Mapping, Sequence, Set, Tuple

MAX_VARIABLES = 8
MAX_EXPRESSION_LENGTH = 500

NOT = "NOT"
AND = "AND"
OR = "OR"
XOR = "XOR"
IMPLIES = "IMPLIES"
IFF = "IFF"
VAR = "VAR"
LPAREN = "LPAREN"
RPAREN = "RPAREN"
EOF = "EOF"


class TruthTableError(ValueError):
    """表达式非法或求值参数缺失。"""


@dataclass(frozen=True)
class Token:
    kind: str
    text: str
    position: int

    def describe(self) -> str:
        return "%s(%s)@%d" % (self.kind, self.text, self.position)


SYMBOLS: Tuple[Tuple[str, str], ...] = (
    ("<->", IFF),
    ("<=>", IFF),
    ("->", IMPLIES),
    ("=>", IMPLIES),
    ("&&", AND),
    ("||", OR),
    ("!", NOT),
    ("~", NOT),
    ("¬", NOT),
    ("∧", AND),
    ("∨", OR),
    ("&", AND),
    ("|", OR),
    ("^", XOR),
    ("⊕", XOR),
    ("+", OR),
    ("*", AND),
    ("→", IMPLIES),
    ("↔", IFF),
    ("(", LPAREN),
    (")", RPAREN),
)

WORDS: Dict[str, str] = {
    "not": NOT,
    "and": AND,
    "or": OR,
    "xor": XOR,
    "implies": IMPLIES,
    "iff": IFF,
}


def tokenize(text: str) -> List[Token]:
    if not isinstance(text, str):
        raise TruthTableError("表达式必须是字符串")
    if not text.strip():
        raise TruthTableError("表达式不能为空")
    if len(text) > MAX_EXPRESSION_LENGTH:
        raise TruthTableError("表达式过长")
    tokens: List[Token] = []
    index = 0
    while index < len(text):
        char = text[index]
        if char.isspace():
            index += 1
            continue
        matched = False
        for symbol, kind in SYMBOLS:
            if text.startswith(symbol, index):
                tokens.append(Token(kind, symbol, index))
                index += len(symbol)
                matched = True
                break
        if matched:
            continue
        if char.isalpha():
            end = index
            while end < len(text) and text[end].isalpha():
                end += 1
            word = text[index:end]
            lowered = word.lower()
            if lowered in WORDS:
                tokens.append(Token(WORDS[lowered], word, index))
            elif len(word) == 1:
                tokens.append(Token(VAR, word.upper(), index))
            else:
                raise TruthTableError(
                    "位置 %d 的 %s 不是有效运算符或单个字母变量" % (index, word)
                )
            index = end
            continue
        raise TruthTableError("位置 %d 出现无法识别的字符 %r" % (index, char))
    tokens.append(Token(EOF, "", len(text)))
    return tokens


class Node:
    """布尔表达式节点。"""

    def evaluate(self, env: Mapping[str, bool]) -> bool:
        raise NotImplementedError

    def variables(self) -> Set[str]:
        raise NotImplementedError


@dataclass(frozen=True)
class Variable(Node):
    name: str

    def evaluate(self, env: Mapping[str, bool]) -> bool:
        try:
            return env[self.name]
        except KeyError:
            raise TruthTableError("缺少变量 %s 的取值" % self.name)

    def variables(self) -> Set[str]:
        return {self.name}


@dataclass(frozen=True)
class Negation(Node):
    operand: Node

    def evaluate(self, env: Mapping[str, bool]) -> bool:
        return not self.operand.evaluate(env)

    def variables(self) -> Set[str]:
        return self.operand.variables()


@dataclass(frozen=True)
class Binary(Node):
    left: Node
    right: Node

    def variables(self) -> Set[str]:
        return self.left.variables() | self.right.variables()


@dataclass(frozen=True)
class Conjunction(Binary):
    def evaluate(self, env: Mapping[str, bool]) -> bool:
        return self.left.evaluate(env) and self.right.evaluate(env)


@dataclass(frozen=True)
class Disjunction(Binary):
    def evaluate(self, env: Mapping[str, bool]) -> bool:
        return self.left.evaluate(env) or self.right.evaluate(env)


@dataclass(frozen=True)
class ExclusiveOr(Binary):
    def evaluate(self, env: Mapping[str, bool]) -> bool:
        return self.left.evaluate(env) != self.right.evaluate(env)


@dataclass(frozen=True)
class Implication(Binary):
    def evaluate(self, env: Mapping[str, bool]) -> bool:
        return (not self.left.evaluate(env)) or self.right.evaluate(env)


@dataclass(frozen=True)
class Biconditional(Binary):
    def evaluate(self, env: Mapping[str, bool]) -> bool:
        return self.left.evaluate(env) == self.right.evaluate(env)


class Parser:
    def __init__(self, tokens: Sequence[Token]) -> None:
        self._tokens = list(tokens)
        self._index = 0

    def peek(self) -> Token:
        return self._tokens[self._index]

    def advance(self) -> Token:
        token = self._tokens[self._index]
        self._index += 1
        return token

    def expect(self, kind: str, message: str) -> Token:
        token = self.peek()
        if token.kind != kind:
            raise TruthTableError("%s（位置 %d）" % (message, token.position))
        return self.advance()

    def parse(self) -> Node:
        node = self.parse_iff()
        token = self.peek()
        if token.kind != EOF:
            raise TruthTableError("位置 %d 还有多余的内容 %r" % (token.position, token.text))
        return node

    def parse_iff(self) -> Node:
        node = self.parse_implies()
        while self.peek().kind == IFF:
            self.advance()
            node = Biconditional(node, self.parse_implies())
        return node

    def parse_implies(self) -> Node:
        node = self.parse_or()
        if self.peek().kind == IMPLIES:
            self.advance()
            return Implication(node, self.parse_implies())
        return node

    def parse_or(self) -> Node:
        node = self.parse_xor()
        while self.peek().kind == OR:
            self.advance()
            node = Disjunction(node, self.parse_xor())
        return node

    def parse_xor(self) -> Node:
        node = self.parse_and()
        while self.peek().kind == XOR:
            self.advance()
            node = ExclusiveOr(node, self.parse_and())
        return node

    def parse_and(self) -> Node:
        node = self.parse_not()
        while self.peek().kind == AND:
            self.advance()
            node = Conjunction(node, self.parse_not())
        return node

    def parse_not(self) -> Node:
        if self.peek().kind == NOT:
            self.advance()
            return Negation(self.parse_not())
        return self.parse_atom()

    def parse_atom(self) -> Node:
        token = self.peek()
        if token.kind == VAR:
            self.advance()
            return Variable(token.text)
        if token.kind == LPAREN:
            self.advance()
            node = self.parse_iff()
            self.expect(RPAREN, "缺少右括号")
            return node
        raise TruthTableError("位置 %d 需要一个变量或左括号" % token.position)


def parse(expression: str) -> Node:
    """把表达式文本解析成语法树。"""

    return Parser(tokenize(expression)).parse()


def _normalize_env(assignment: Mapping[str, object]) -> Dict[str, bool]:
    if not isinstance(assignment, Mapping):
        raise TruthTableError("取值必须是映射")
    normalized: Dict[str, bool] = {}
    for key, value in assignment.items():
        if not isinstance(key, str) or len(key) != 1 or not key.isalpha():
            raise TruthTableError("变量名必须是单个字母")
        if not isinstance(value, bool):
            raise TruthTableError("变量 %s 的取值必须是布尔值" % key)
        normalized[key.upper()] = value
    return normalized


def evaluate(expression: str, assignment: Mapping[str, object]) -> bool:
    node = parse(expression)
    env = _normalize_env(assignment)
    required = node.variables()
    missing = sorted(required - set(env))
    if missing:
        raise TruthTableError("缺少变量取值：%s" % ", ".join(missing))
    return node.evaluate(env)


@dataclass(frozen=True)
class TruthTable:
    expression: str
    variables: Tuple[str, ...]
    rows: Tuple[Tuple[Tuple[bool, ...], bool], ...]

    @property
    def row_count(self) -> int:
        return len(self.rows)

    @property
    def results(self) -> Tuple[bool, ...]:
        return tuple(result for _, result in self.rows)

    @property
    def is_tautology(self) -> bool:
        return all(self.results)

    @property
    def is_contradiction(self) -> bool:
        return not any(self.results)

    @property
    def is_satisfiable(self) -> bool:
        return any(self.results)

    def to_dict(self) -> dict:
        return {
            "expression": self.expression,
            "variables": list(self.variables),
            "rows": [
                {
                    "assignment": dict(zip(self.variables, values)),
                    "result": result,
                }
                for values, result in self.rows
            ],
            "tautology": self.is_tautology,
            "contradiction": self.is_contradiction,
        }


def build_table(expression: str) -> TruthTable:
    """枚举所有取值组合，生成真值表。"""

    node = parse(expression)
    names = sorted(node.variables())
    if len(names) > MAX_VARIABLES:
        raise TruthTableError("变量过多，最多支持 %d 个" % MAX_VARIABLES)
    rows: List[Tuple[Tuple[bool, ...], bool]] = []
    for combination in itertools.product((False, True), repeat=len(names)):
        env = dict(zip(names, combination))
        rows.append((combination, node.evaluate(env)))
    return TruthTable(expression.strip(), tuple(names), tuple(rows))


def format_table(table: TruthTable, symbols: str = "10") -> str:
    """把真值表排成等宽文本。"""

    if not isinstance(table, TruthTable):
        raise TruthTableError("table 必须是 TruthTable")
    true_char, false_char = _symbol_pair(symbols)
    header = list(table.variables) + ["|", table.expression]
    lines = [" ".join(header)]
    widths = [max(1, len(item)) for item in header]
    lines[0] = " ".join(
        item.ljust(width) for item, width in zip(header, widths)
    ).rstrip()
    for values, result in table.rows:
        cells = [true_char if value else false_char for value in values]
        cells.append("|")
        cells.append(true_char if result else false_char)
        lines.append(
            " ".join(item.ljust(width) for item, width in zip(cells, widths)).rstrip()
        )
    return "\n".join(lines)


def _symbol_pair(symbols: str) -> Tuple[str, str]:
    if symbols == "10":
        return "1", "0"
    if symbols.lower() == "tf":
        return "T", "F"
    raise TruthTableError("符号只能是 10 或 TF")


def parse_expression_lines(text: str) -> List[str]:
    """逐行读取表达式，支持 # 注释与空行。"""

    if not isinstance(text, str):
        raise TruthTableError("表达式列表必须是文本")
    expressions: List[str] = []
    for raw in text.splitlines():
        line = raw.split("#", 1)[0].strip()
        if not line:
            continue
        parse(line)
        expressions.append(line)
    if not expressions:
        raise TruthTableError("没有找到任何表达式")
    return expressions
