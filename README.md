# truthtable

[![CI](https://github.com/eastyou/truthtable/actions/workflows/ci.yml/badge.svg)](https://github.com/eastyou/truthtable/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python 3.9+](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://www.python.org/)

面向信息技术与数学课的真值表工具：解析布尔表达式、枚举所有取值、判断重言式/矛盾式，并生成可打印的 A4 练习纸。纯标准库、零依赖。

## 安装

```bash
pip install -e .
```

## 支持的运算符

| 运算 | 写法 | 优先级 |
| --- | --- | --- |
| 非 | `not A`、`!A`、`~A`、`¬A` | 最高 |
| 与 | `A and B`、`A & B`、`A && B`、`A ∧ B` | 高 |
| 异或 | `A xor B`、`A ^ B`、`A ⊕ B` | 中 |
| 或 | `A or B`、`A \| B`、`A \|\| B`、`A ∨ B` | 中低 |
| 蕴含 | `A -> B`、`A => B`、`A implies B`、`A → B` | 低 |
| 等价 | `A <-> B`、`A <=> B`、`A iff B`、`A ↔ B` | 最低 |

变量为单个英文字母，不区分大小写；可用括号改变结合顺序。蕴含是右结合。

## 用法

```bash
# 打印真值表
truthtable eval "A and (B or not C)"

# 用 T/F 显示
truthtable eval "A -> B" --symbols tf

# 判断表达式类型
truthtable info "A or not A"

# 生成练习纸（每行一个表达式，# 开头为注释）
truthtable sheet examples/expressions.txt --answers -o 练习.html
```

练习纸每题预留结果列，学生填写 T/F 并判断类型；`--answers` 会附加答案页，标注重言式、矛盾式或可满足式。

## 项目结构

```text
truthtable/
├── truthtable/
│   ├── __init__.py
│   ├── __main__.py
│   ├── model.py      # 词法、递归下降解析、求值与真值表
│   ├── render.py     # HTML 表格与 A4 练习纸
│   └── cli.py        # 命令行入口
├── examples/
│   ├── expressions.txt
│   └── sample.html
└── tests/
    ├── test_model.py
    ├── test_render.py
    └── test_cli.py
```

## 测试

```bash
python -m unittest discover -s tests -v
```

## License

MIT © 2026 eastyou
