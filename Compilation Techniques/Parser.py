# Parser.py
#
# ══════════════════════════════════════════════════════════════════════════════
#  LL(1) GRAMMAR  (see LL1_Grammar.txt for the full reference)
#
#   program     → stmts EOF
#   stmt        → var_decl | if_stmt | while_stmt | for_stmt
#               | func_def | return_stmt | expr_stmt
#   expr        → or → and → not → comparison
#               → arith → term → factor → power → call → atom
# ══════════════════════════════════════════════════════════════════════════════

from Lexer import *
from Nodes import *


# ──────────────────────────────────────────────────────────────────────────────
#  STEP 2 — THE PARSER
#
#  The parser reads the list of tokens from left to right and builds the tree.
#  There is ONE function for each rule in LL1_Grammar.txt, with the same name.
#  To choose between rules, it only ever looks at the current token (LL(1)).
#  Each "_tail" / "more_" rule from the grammar becomes a while loop.
# ──────────────────────────────────────────────────────────────────────────────

class InvalidSyntaxError(Error):
    def __init__(self, pos_start, pos_end, details):
        super().__init__(pos_start, pos_end, 'Invalid Syntax', details)


class Parser:
    def __init__(self, tokens):
        self.tokens      = tokens
        self.idx         = 0
        self.current_tok = tokens[0]

    # ── Helpers ───────────────────────────────────────────────────────────────

    def advance(self):
        """Move on to the next token."""
        self.idx += 1
        self.current_tok = self.tokens[self.idx]

    def is_keyword(self, word):
        """Is the current token this keyword? e.g. is_keyword('if')"""
        return self.current_tok.matches(TT_KEYWORD, word)

    def error(self, message):
        """Stop parsing and report a syntax error at the current token."""
        raise InvalidSyntaxError(self.current_tok.pos_start,
                                 self.current_tok.pos_end, message)

    def expect(self, type_, description):
        """The current token MUST be this type. Take it and move on."""
        if self.current_tok.type != type_:
            self.error(f'Expected {description}')
        tok = self.current_tok
        self.advance()
        return tok

    def expect_keyword(self, word):
        """The current token MUST be this keyword. Take it and move on."""
        if not self.is_keyword(word):
            self.error(f"Expected '{word}'")
        tok = self.current_tok
        self.advance()
        return tok

    # ── Program ───────────────────────────────────────────────────────────────

    def parse(self):
        # program → stmts EOF
        pos_start  = self.current_tok.pos_start
        statements = self.stmts()
        if self.current_tok.type != TT_EOF:
            self.error('Expected a statement')
        return BlockNode(statements, pos_start, self.current_tok.pos_end)

    def stmts(self):
        # stmts → stmt stmts | NEWLINE stmts | ε
        statements = []
        # Keep going until we reach the end of a block '}' or the end of the file
        while self.current_tok.type not in (TT_RBRACE, TT_EOF):
            if self.current_tok.type == TT_NEWLINE:
                self.advance()                      # skip blank lines
            else:
                statements.append(self.stmt())
        return statements

    # ── Statements ────────────────────────────────────────────────────────────

    def stmt(self):
        # stmt → var_decl | if_stmt | while_stmt | for_stmt
        #      | func_def | return_stmt | expr_stmt
        # The first token tells us which kind of statement it is.
        if self.is_keyword('var'):    return self.var_decl()
        if self.is_keyword('if'):     return self.if_stmt()
        if self.is_keyword('while'):  return self.while_stmt()
        if self.is_keyword('for'):    return self.for_stmt()
        if self.is_keyword('func'):   return self.func_def()
        if self.is_keyword('return'): return self.return_stmt()
        return self.expr_stmt()

    def var_decl(self):
        # var_decl → "var" IDENTIFIER "=" expr NEWLINE
        self.expect_keyword('var')
        name = self.expect(TT_IDENTIFIER, 'a variable name')
        self.expect(TT_EQ, "'='")
        value = self.expr()
        self.expect(TT_NEWLINE, 'a new line')
        return VarAssignNode(name, value, is_declaration=True)

    def if_stmt(self):
        # if_stmt   → "if" expr block elif_part else_part
        # elif_part → "elif" expr block elif_part | ε
        # else_part → "else" block | ε
        cases = []

        self.expect_keyword('if')
        condition = self.expr()
        body      = self.block()
        cases.append((condition, body))

        while self.is_keyword('elif'):
            self.advance()
            condition = self.expr()
            body      = self.block()
            cases.append((condition, body))

        else_case = None
        if self.is_keyword('else'):
            self.advance()
            else_case = self.block()

        return IfNode(cases, else_case)

    def while_stmt(self):
        # while_stmt → "while" expr block
        self.expect_keyword('while')
        condition = self.expr()
        body      = self.block()
        return WhileNode(condition, body)

    def for_stmt(self):
        # for_stmt  → "for" IDENTIFIER "=" expr "to" expr step_part block
        # step_part → "step" expr | ε
        self.expect_keyword('for')
        var_name = self.expect(TT_IDENTIFIER, 'a variable name')
        self.expect(TT_EQ, "'='")
        start = self.expr()
        self.expect_keyword('to')
        end = self.expr()

        step = None
        if self.is_keyword('step'):
            self.advance()
            step = self.expr()

        body = self.block()
        return ForNode(var_name, start, end, step, body)

    def func_def(self):
        # func_def    → "func" IDENTIFIER "(" params ")" block
        # params      → IDENTIFIER more_params | ε
        # more_params → "," IDENTIFIER more_params | ε
        self.expect_keyword('func')
        name = self.expect(TT_IDENTIFIER, 'a function name')
        self.expect(TT_LPAREN, "'('")

        params = []
        if self.current_tok.type == TT_IDENTIFIER:
            params.append(self.expect(TT_IDENTIFIER, 'a parameter name'))
            while self.current_tok.type == TT_COMMA:
                self.advance()
                params.append(self.expect(TT_IDENTIFIER, 'a parameter name'))

        self.expect(TT_RPAREN, "')'")
        body = self.block()
        return FuncDefNode(name, params, body)

    def return_stmt(self):
        # return_stmt  → "return" return_value
        # return_value → expr NEWLINE | NEWLINE
        return_tok = self.expect_keyword('return')

        value = None
        if self.current_tok.type != TT_NEWLINE:
            value = self.expr()

        end_tok = self.expect(TT_NEWLINE, 'a new line')
        return ReturnNode(value, return_tok.pos_start, end_tok.pos_start)

    def expr_stmt(self):
        # expr_stmt → expr NEWLINE
        node = self.expr()
        self.expect(TT_NEWLINE, 'a new line')
        return node

    def block(self):
        # block → "{" stmts "}"
        lbrace     = self.expect(TT_LBRACE, "'{'")
        statements = self.stmts()
        rbrace     = self.expect(TT_RBRACE, "'}'")
        return BlockNode(statements, lbrace.pos_start, rbrace.pos_end)

    # ── Expressions (lowest to highest precedence) ────────────────────────────

    def expr(self):
        # expr        → or_expr assign_tail
        # assign_tail → "=" expr | ε
        node = self.or_expr()

        if self.current_tok.type == TT_EQ:
            # Only a plain variable name can be on the left of '='
            if not isinstance(node, VarAccessNode):
                self.error("Left side of '=' must be a variable name")
            self.advance()
            value = self.expr()
            return VarAssignNode(node.var_name_tok, value)

        return node

    def or_expr(self):
        # or_expr → and_expr or_tail
        # or_tail → "or" and_expr or_tail | ε
        node = self.and_expr()
        while self.is_keyword('or'):
            op = self.current_tok
            self.advance()
            node = BinOpNode(node, op, self.and_expr())
        return node

    def and_expr(self):
        # and_expr → not_expr and_tail
        # and_tail → "and" not_expr and_tail | ε
        node = self.not_expr()
        while self.is_keyword('and'):
            op = self.current_tok
            self.advance()
            node = BinOpNode(node, op, self.not_expr())
        return node

    def not_expr(self):
        # not_expr → "not" not_expr | comparison
        if self.is_keyword('not'):
            op = self.current_tok
            self.advance()
            return UnaryOpNode(op, self.not_expr())
        return self.comparison()

    def comparison(self):
        # comparison → arith comp_tail
        # comp_tail  → comp_op arith comp_tail | ε
        node = self.arith()
        while self.current_tok.type in (TT_EQEQ, TT_NEQ, TT_LT, TT_GT, TT_LTE, TT_GTE):
            op = self.current_tok
            self.advance()
            node = BinOpNode(node, op, self.arith())
        return node

    def arith(self):
        # arith      → term arith_tail
        # arith_tail → add_op term arith_tail | ε
        node = self.term()
        while self.current_tok.type in (TT_PLUS, TT_MINUS):
            op = self.current_tok
            self.advance()
            node = BinOpNode(node, op, self.term())
        return node

    def term(self):
        # term      → factor term_tail
        # term_tail → mul_op factor term_tail | ε
        node = self.factor()
        while self.current_tok.type in (TT_MUL, TT_DIV, TT_MOD):
            op = self.current_tok
            self.advance()
            node = BinOpNode(node, op, self.factor())
        return node

    def factor(self):
        # factor → "+" factor | "-" factor | power
        if self.current_tok.type in (TT_PLUS, TT_MINUS):
            op = self.current_tok
            self.advance()
            return UnaryOpNode(op, self.factor())
        return self.power()

    def power(self):
        # power      → call power_tail
        # power_tail → "**" factor | ε
        node = self.call()
        if self.current_tok.type == TT_POW:
            op = self.current_tok
            self.advance()
            node = BinOpNode(node, op, self.factor())
        return node

    def call(self):
        # call      → atom call_tail
        # call_tail → "(" args ")" call_tail
        #           | "[" expr "]" call_tail
        #           | "." IDENTIFIER call_tail
        #           | ε
        node = self.atom()

        while self.current_tok.type in (TT_LPAREN, TT_LBRACKET, TT_DOT):
            if self.current_tok.type == TT_LPAREN:          # add(1, 2)
                self.advance()
                arguments = self.args(TT_RPAREN)
                self.expect(TT_RPAREN, "')'")
                node = CallNode(node, arguments)

            elif self.current_tok.type == TT_LBRACKET:      # items[0]
                self.advance()
                index = self.expr()
                self.expect(TT_RBRACKET, "']'")
                node = IndexNode(node, index)

            else:                                           # player.score
                self.advance()
                name = self.expect(TT_IDENTIFIER, "a name after '.'")
                node = MemberAccessNode(node, name)

        return node

    def args(self, closing_type):
        # args      → expr more_args | ε
        # more_args → "," expr more_args | ε
        # Used for function calls  f(1, 2)  and list literals  [1, 2].
        # closing_type is ')' or ']' — if we see it straight away, the list is empty.
        items = []
        if self.current_tok.type == closing_type:
            return items

        items.append(self.expr())
        while self.current_tok.type == TT_COMMA:
            self.advance()
            items.append(self.expr())
        return items

    def atom(self):
        # atom → INT | FLOAT | STRING | "true" | "false" | "null"
        #      | IDENTIFIER | "(" expr ")" | "[" args "]"
        tok = self.current_tok

        if tok.type in (TT_INT, TT_FLOAT):
            self.advance()
            return NumberNode(tok)

        if tok.type == TT_STRING:
            self.advance()
            return StringNode(tok)

        if self.is_keyword('true') or self.is_keyword('false'):
            self.advance()
            return BoolNode(tok)

        if self.is_keyword('null'):
            self.advance()
            return NullNode(tok)

        if tok.type == TT_IDENTIFIER:
            self.advance()
            return VarAccessNode(tok)

        if tok.type == TT_LPAREN:                           # ( expr )
            self.advance()
            node = self.expr()
            self.expect(TT_RPAREN, "')'")
            return node

        if tok.type == TT_LBRACKET:                         # [1, 2, 3]
            self.advance()
            elements = self.args(TT_RBRACKET)
            rbracket = self.expect(TT_RBRACKET, "']'")
            return ListNode(elements, tok.pos_start, rbracket.pos_end)

        self.error("Expected a value (number, string, name, '(' or '[')")


# ──────────────────────────────────────────────────────────────────────────────
#  Entry point: source code → tokens → tree
# ──────────────────────────────────────────────────────────────────────────────

def run(fn, text):
    # 1. Lexer: text → tokens
    tokens, error = Lexer(fn, text).make_tokens()
    if error:
        return None, error

    # 2. Parser: tokens → tree
    try:
        tree = Parser(tokens).parse()
        return tree, None
    except InvalidSyntaxError as error:
        return None, error


# Run this file directly (python Parser.py) to see the parser working
if __name__ == '__main__':
    code = '''
var x = 10

func add(a, b) {
    return a + b
}

if x > 5 and not false {
    print(add(x, 2) * 3)
} else {
    x = x - 1
}
'''
    tree, error = run('<demo>', code)
    if error:
        print(error.as_string())
    else:
        for statement in tree.statement_nodes:
            print(statement)
