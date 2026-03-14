# Tokenising Calculator

A text-based calculator built from scratch using **lexical analysis** and a **recursive descent parser** — the same foundational techniques used in real programming language compilers and NLP pipelines.

No `eval()`. No shortcuts. The entire pipeline is implemented manually.

---

## How it works

Raw input like `(3 + 4) * 2` passes through three stages:

```
"(3 + 4) * 2"
      ↓
   LEXER — scans characters, classifies tokens
      ↓
[LPAREN] [NUMBER:3] [PLUS] [NUMBER:4] [RPAREN] [MULTIPLY] [NUMBER:2] [EOF]
      ↓
   PARSER — applies precedence rules, builds evaluation tree
      ↓
   14
```

### Stage 1 — Lexer
Scans the input string character by character and emits a stream of typed tokens (`NUMBER`, `PLUS`, `MINUS`, `MULTIPLY`, `DIVIDE`, `LPAREN`, `RPAREN`, `EOF`). Handles floats, multi-digit numbers, whitespace, and unknown character errors with position info.

### Stage 2 — Recursive Descent Parser
Implements operator precedence directly in the grammar:

```
statement  →  IDENT '=' expr  |  expr
expr       →  term   (('+' | '-') term)*
term       →  power  (('*' | '/') power)*
power      →  unary  ('^' unary)*
unary      →  '-' unary  |  primary
primary    →  NUMBER | IDENT '(' args ')' | IDENT | '(' expr ')'
```

Each grammar rule is a function — precedence falls out naturally from the call hierarchy.

### Stage 3 — Evaluator
The parser evaluates the expression directly as it parses (no separate AST step), printing each operation so the pipeline is fully visible.

---

## Features

- **Arithmetic** — `+` `-` `*` `/` with correct precedence
- **Exponentiation** — `2 ^ 10` → `1024`
- **Parentheses** — `(3 + 4) * 2` → `14`
- **Unary minus** — `-5 + 3` → `-2`
- **Variables** — `x = 10` then use `x` in any expression
- **Built-in functions** — `sqrt`, `abs`, `floor`, `ceil`, `round`, `log`, `log2`, `log10`, `sin`, `cos`, `tan`, `pow`, `max`, `min`
- **Built-in constants** — `pi`, `e`
- **Session history** — view past expressions and results with `history`
- **Verbose pipeline** — every run prints the full token table and numbered parse steps

---

## Getting started

**Requirements:** Python 3.10+

```bash
git clone https://github.com/your-username/tokenising-calculator
cd tokenising-calculator
python tokenising_calculator.py
```

### Example session

```
> 3 + 4 * 2
  Tokens:
  [NUMBER    ]  value=3   pos=0
  [PLUS      ]  value='+'  pos=2
  [NUMBER    ]  value=4   pos=4
  [MULTIPLY  ]  value='*'  pos=6
  [NUMBER    ]  value=2   pos=8
  [EOF       ]  value=''  pos=9

  Parse / Eval steps:
   1.  4 * 2 = 8
   2.  3 + 8 = 11

  ✓  Result: 11

> x = 5
  ✓  x = 5

> sqrt(x * 20) + x ^ 2
  ✓  Result: 35

> history
  1.  3 + 4 * 2       →  11
  2.  x = 5           →  5
  3.  sqrt(x*20)+x^2  →  35
```

### REPL commands

| Command   | Description                        |
|-----------|------------------------------------|
| `help`    | Show all operators, functions, commands |
| `vars`    | List all defined variables         |
| `history` | Show past expressions and results  |
| `clear`   | Clear history                      |
| `exit`    | Quit                               |

---

## Browser UI

A visual version is also included (`tokenising_calculator.html`) — open it by double-clicking, no server or install needed.

It renders the token stream and parse steps live as you type.

---

## Project structure

```
tokenising-calculator/
├── tokenising_calculator.py    # Core lexer, parser, evaluator + REPL
├── tokenising_calculator.html  # Standalone browser UI
└── README.md
```

---

## Concepts covered

- Lexical analysis / tokenisation
- Recursive descent parsing
- Operator precedence via grammar hierarchy
- Symbol table (variable storage)
- Error handling with source position reporting# Tokenizing-Calculator
