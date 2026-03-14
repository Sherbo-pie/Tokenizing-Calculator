import math
from dataclasses import dataclass
from enum import Enum, auto
from typing import Optional


# ─────────────────────────────────────────────
#  TOKEN TYPES
# ─────────────────────────────────────────────

class TokenType(Enum):
    NUMBER   = auto()
    IDENT    = auto()   # variable names or function names
    PLUS     = auto()
    MINUS    = auto()
    MULTIPLY = auto()
    DIVIDE   = auto()
    POWER    = auto()
    ASSIGN   = auto()
    LPAREN   = auto()
    RPAREN   = auto()
    COMMA    = auto()
    EOF      = auto()


@dataclass
class Token:
    type:  TokenType
    value: object      # float for NUMBER, str for everything else
    pos:   int         # character position in original string


# ─────────────────────────────────────────────
#  LEXER  (text → token list)
# ─────────────────────────────────────────────

class Lexer:
    def __init__(self, text: str):
        self.text = text
        self.pos  = 0

    def tokenize(self) -> list[Token]:
        tokens = []
        while self.pos < len(self.text):
            ch = self.text[self.pos]

            # skip whitespace
            if ch in (' ', '\t'):
                self.pos += 1
                continue

            # numbers  (int or float)
            if ch.isdigit() or ch == '.':
                tokens.append(self._read_number())
                continue

            # identifiers  (variable / function names)
            if ch.isalpha() or ch == '_':
                tokens.append(self._read_ident())
                continue

            # single-character operators
            single = {
                '+': TokenType.PLUS,
                '-': TokenType.MINUS,
                '*': TokenType.MULTIPLY,
                '/': TokenType.DIVIDE,
                '^': TokenType.POWER,
                '=': TokenType.ASSIGN,
                '(': TokenType.LPAREN,
                ')': TokenType.RPAREN,
                ',': TokenType.COMMA,
            }
            if ch in single:
                tokens.append(Token(single[ch], ch, self.pos))
                self.pos += 1
                continue

            raise LexError(f"Unknown character '{ch}' at position {self.pos}")

        tokens.append(Token(TokenType.EOF, '', self.pos))
        return tokens

    def _read_number(self) -> Token:
        start = self.pos
        has_dot = False
        while self.pos < len(self.text):
            c = self.text[self.pos]
            if c.isdigit():
                self.pos += 1
            elif c == '.' and not has_dot:
                has_dot = True
                self.pos += 1
            else:
                break
        raw = self.text[start:self.pos]
        return Token(TokenType.NUMBER, float(raw), start)

    def _read_ident(self) -> Token:
        start = self.pos
        while self.pos < len(self.text) and (self.text[self.pos].isalnum() or self.text[self.pos] == '_'):
            self.pos += 1
        name = self.text[start:self.pos]
        return Token(TokenType.IDENT, name, start)


# ─────────────────────────────────────────────
#  PARSER + EVALUATOR  (tokens → result)
# ─────────────────────────────────────────────

# Grammar (operator precedence, low → high):
#
#   statement  → IDENT '=' expr  |  expr
#   expr       → term  (('+' | '-') term)*
#   term       → power (('*' | '/') power)*
#   power      → unary ('^' unary)*
#   unary      → '-' unary  |  primary
#   primary    → NUMBER
#              | IDENT '(' args ')'   ← function call
#              | IDENT                ← variable lookup
#              | '(' expr ')'

class Parser:
    def __init__(self, tokens: list[Token], variables: dict, steps: list):
        self.tokens    = tokens
        self.pos       = 0
        self.variables = variables
        self.steps     = steps         

    # ── helpers ────────────────────────────────

    def cur(self) -> Token:
        return self.tokens[self.pos]

    def eat(self, ttype: TokenType) -> Token:
        tok = self.cur()
        if tok.type != ttype:
            raise ParseError(f"Expected {ttype.name} but got '{tok.value}' at position {tok.pos}")
        self.pos += 1
        return tok

    def match(self, *types) -> bool:
        return self.cur().type in types

    # ── grammar rules ──────────────────────────

    def statement(self):
        # assignment:  name = expr
        if (self.cur().type == TokenType.IDENT
                and self.pos + 1 < len(self.tokens)
                and self.tokens[self.pos + 1].type == TokenType.ASSIGN):
            name = self.eat(TokenType.IDENT).value
            self.eat(TokenType.ASSIGN)
            value = self.expr()
            self.variables[name] = value
            self.steps.append(f"Assigned  {name} = {_fmt(value)}")
            return value, name
        return self.expr(), None

    def expr(self) -> float:
        left = self.term()
        while self.match(TokenType.PLUS, TokenType.MINUS):
            op  = self.cur().value
            self.pos += 1
            right = self.term()
            prev  = left
            left  = left + right if op == '+' else left - right
            self.steps.append(f"{_fmt(prev)} {op} {_fmt(right)} = {_fmt(left)}")
        return left

    def term(self) -> float:
        left = self.power()
        while self.match(TokenType.MULTIPLY, TokenType.DIVIDE):
            op  = self.cur().value
            self.pos += 1
            right = self.power()
            if op == '/' and right == 0:
                raise EvalError("Division by zero")
            prev = left
            left = left * right if op == '*' else left / right
            self.steps.append(f"{_fmt(prev)} {op} {_fmt(right)} = {_fmt(left)}")
        return left

    def power(self) -> float:
        base = self.unary()
        if self.match(TokenType.POWER):
            self.pos += 1
            exp  = self.unary() 
            prev = base
            base = base ** exp
            self.steps.append(f"{_fmt(prev)} ^ {_fmt(exp)} = {_fmt(base)}")
        return base

    def unary(self) -> float:
        if self.match(TokenType.MINUS):
            self.pos += 1
            val = self.unary()
            self.steps.append(f"Unary minus → {_fmt(-val)}")
            return -val
        return self.primary()

    def primary(self) -> float:
        tok = self.cur()

        # number literal
        if tok.type == TokenType.NUMBER:
            self.pos += 1
            return tok.value

        # identifier → function call or variable
        if tok.type == TokenType.IDENT:
            name = tok.value
            self.pos += 1
            if self.match(TokenType.LPAREN):
                return self._call_function(name)
            # variable lookup
            if name in self.variables:
                val = self.variables[name]
                self.steps.append(f"Variable  {name} = {_fmt(val)}")
                return val
            raise EvalError(f"Undefined variable '{name}'")

        # parenthesised expression
        if tok.type == TokenType.LPAREN:
            self.eat(TokenType.LPAREN)
            self.steps.append("Opened parenthesis — evaluating inner expression")
            val = self.expr()
            self.eat(TokenType.RPAREN)
            self.steps.append(f"Closed parenthesis → {_fmt(val)}")
            return val

        raise ParseError(f"Unexpected token '{tok.value}' at position {tok.pos}")

    def _call_function(self, name: str) -> float:
        self.eat(TokenType.LPAREN)
        args = []
        if not self.match(TokenType.RPAREN):
            args.append(self.expr())
            while self.match(TokenType.COMMA):
                self.pos += 1
                args.append(self.expr())
        self.eat(TokenType.RPAREN)

        FUNCS = {
            'sqrt':  (1, lambda a: math.sqrt(a)),
            'abs':   (1, lambda a: abs(a)),
            'floor': (1, lambda a: float(math.floor(a))),
            'ceil':  (1, lambda a: float(math.ceil(a))),
            'round': (1, lambda a: float(round(a))),
            'log':   (1, lambda a: math.log(a)),
            'log2':  (1, lambda a: math.log2(a)),
            'log10': (1, lambda a: math.log10(a)),
            'sin':   (1, lambda a: math.sin(math.radians(a))),
            'cos':   (1, lambda a: math.cos(math.radians(a))),
            'tan':   (1, lambda a: math.tan(math.radians(a))),
            'pow':   (2, lambda a, b: a ** b),
            'max':   (2, lambda a, b: max(a, b)),
            'min':   (2, lambda a, b: min(a, b)),
        }

        if name not in FUNCS:
            raise EvalError(f"Unknown function '{name}()'")

        expected_argc, fn = FUNCS[name]
        if len(args) != expected_argc:
            raise EvalError(
                f"{name}() expects {expected_argc} argument(s), got {len(args)}"
            )

        result = fn(*args)
        arg_str = ', '.join(_fmt(a) for a in args)
        self.steps.append(f"Called  {name}({arg_str}) = {_fmt(result)}")
        return result


# ─────────────────────────────────────────────
#  CUSTOM EXCEPTIONS
# ─────────────────────────────────────────────

class LexError(Exception):   pass
class ParseError(Exception): pass
class EvalError(Exception):  pass


# ─────────────────────────────────────────────
#  HELPERS
# ─────────────────────────────────────────────

def _fmt(n: float) -> str:
    """Display integers without decimal point, floats with up to 8 sig-figs."""
    if isinstance(n, float) and n.is_integer():
        return str(int(n))
    return f"{n:.8g}"


def _print_tokens(tokens: list[Token]) -> None:
    print("\n  Tokens:")
    print("  " + "─" * 50)
    for tok in tokens:
        val = _fmt(tok.value) if tok.type == TokenType.NUMBER else repr(tok.value)
        print(f"  [{tok.type.name:<10}]  value={val:<12}  pos={tok.pos}")
    print()


def _print_steps(steps: list[str]) -> None:
    if not steps:
        return
    print("  Parse / Eval steps:")
    print("  " + "─" * 50)
    for i, s in enumerate(steps, 1):
        print(f"  {i:>2}.  {s}")
    print()


def _print_help() -> None:
    print("""
  ┌─────────────────────────────────────────────────────┐
  │              Tokenising Calculator — Help            │
  ├─────────────────────────────────────────────────────┤
  │  Operators    + - * / ^ ( )                         │
  │  Variables    x = 5   then use x in any expression  │
  │  Functions    sqrt  abs  floor  ceil  round          │
  │               log  log2  log10                       │
  │               sin  cos  tan  (degrees)               │
  │               pow(a,b)  max(a,b)  min(a,b)          │
  │  Constants    pi   e                                 │
  │  Commands     help   vars   history   clear   exit  │
  └─────────────────────────────────────────────────────┘
  Examples:
    3 + 4 * 2
    (3 + 4) * 2
    sqrt(16) + abs(-5)
    x = 10
    x * 3 + sin(45)
    pow(2, 10)
""")


# ─────────────────────────────────────────────
#  MAIN REPL
# ─────────────────────────────────────────────

def calculate(text: str, variables: dict, verbose: bool = True) -> Optional[float]:
    """Tokenise, parse, and evaluate one expression string."""
    steps = []
    try:
        tokens = Lexer(text).tokenize()

        if verbose:
            _print_tokens(tokens)

        result, assigned_name = Parser(tokens, variables, steps).statement()

        if verbose:
            _print_steps(steps)

        return result, assigned_name

    except (LexError, ParseError, EvalError) as e:
        print(f"\n  ✗  Error: {e}\n")
        return None, None


def main():
    variables = {
        'pi': math.pi,
        'e':  math.e,
    }
    history = []

    print("=" * 56)
    print("  Tokenising Calculator  —  type 'help' for commands")
    print("=" * 56)

    while True:
        try:
            raw = input("\n  > ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n  Bye!\n")
            break

        if not raw:
            continue

        cmd = raw.lower()

        if cmd in ('exit', 'quit'):
            print("\n  Bye!\n")
            break

        if cmd == 'help':
            _print_help()
            continue

        if cmd == 'vars':
            if variables:
                print("\n  Variables:")
                for k, v in variables.items():
                    print(f"    {k} = {_fmt(v)}")
                print()
            else:
                print("\n  No variables defined yet.\n")
            continue

        if cmd == 'history':
            if history:
                print("\n  History:")
                for i, (expr, res) in enumerate(history, 1):
                    res_str = _fmt(res) if res is not None else "error"
                    print(f"  {i:>3}.  {expr}  →  {res_str}")
                print()
            else:
                print("\n  No history yet.\n")
            continue

        if cmd == 'clear':
            history.clear()
            print("\n  History cleared.\n")
            continue

        # evaluate
        result, assigned_name = calculate(raw, variables, verbose=True)

        if result is not None:
            history.append((raw, result))
            if assigned_name:
                print(f"  ✓  {assigned_name} = {_fmt(result)}\n")
            else:
                print(f"  ✓  Result: {_fmt(result)}\n")


if __name__ == '__main__':
    main()