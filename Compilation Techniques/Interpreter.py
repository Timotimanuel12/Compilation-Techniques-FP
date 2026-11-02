# Interpreter.py
#
# ══════════════════════════════════════════════════════════════════════════════
#  STEP 3 — THE INTERPRETER
#
#  The interpreter walks through the tree built by the Parser and runs it.
#  There is ONE function for each kind of node, named visit_<NodeName>.
#  For example, a NumberNode is handled by visit_NumberNode.
#
#  Built so far:  numbers and maths  ( + - * / % **  and negative numbers )
# ══════════════════════════════════════════════════════════════════════════════

from Lexer import *
from Nodes import *
from Parser import Parser


class RTError(Error):
    """An error that happens while the program is running, e.g. 1 / 0."""
    def __init__(self, node, details):
        super().__init__(node.pos_start, node.pos_end, 'Runtime Error', details)


class Interpreter:
    def run(self, fn, text):
        """Source code → Lexer → Parser → Interpreter. Returns (result, error)."""
        # 1. Lexer: text → tokens
        tokens, error = Lexer(fn, text).make_tokens()
        if error:
            return None, error

        try:
            # 2. Parser: tokens → tree
            tree = Parser(tokens).parse()

            # 3. Interpreter: tree → result
            result = self.visit(tree)
            return result, None
        except Error as error:          # a syntax error or a runtime error
            return None, error

    def visit(self, node):
        """Run one node by calling the matching visit_... function."""
        method_name = f'visit_{type(node).__name__}'    # e.g. 'visit_NumberNode'
        method = getattr(self, method_name, None)       # find the function with that name

        if method is None:
            raise RTError(node, f'{type(node).__name__} is not supported yet')
        return method(node)

    # ── Statements in a row ───────────────────────────────────────────────────

    def visit_BlockNode(self, node):
        # Run each statement in order, top to bottom.
        # The value of the last statement is returned (the shell shows it).
        result = None
        for statement in node.statement_nodes:
            result = self.visit(statement)
        return result

    # ── Values ────────────────────────────────────────────────────────────────

    def visit_NumberNode(self, node):
        # The lexer already turned the text "42" into the Python number 42,
        # so we just hand it back.
        return node.tok.value

    # ── Operators ─────────────────────────────────────────────────────────────

    def visit_BinOpNode(self, node):
        # A BinOpNode has a left side, an operator and a right side, e.g. 2 * 3.
        # First work out both sides (they may be bigger trees themselves)...
        left  = self.visit(node.left_node)
        right = self.visit(node.right_node)

        # ...then do the operation that matches the operator token.
        op = node.op_tok.type

        # Dividing by zero is impossible, so stop with a clear error message
        if op in (TT_DIV, TT_MOD) and right == 0:
            raise RTError(node, 'Division by zero')

        if op == TT_PLUS:   return left + right
        if op == TT_MINUS:  return left - right
        if op == TT_MUL:    return left * right
        if op == TT_DIV:    return left / right
        if op == TT_MOD:    return left % right
        if op == TT_POW:    return left ** right

        raise RTError(node, f'The operator {op} is not supported yet')

    def visit_UnaryOpNode(self, node):
        # A UnaryOpNode is an operator with only ONE side, e.g. -5
        value = self.visit(node.node)

        op = node.op_tok.type
        if op == TT_MINUS:  return -value
        if op == TT_PLUS:   return value

        raise RTError(node, f'The operator {node.op_tok} is not supported yet')


# Run this file directly (python Interpreter.py) to test what is built so far
if __name__ == '__main__':
    tests = [
        '1 + 2',
        '1 + 2 * 3',
        '(1 + 2) * 3',
        '10 / 4',
        '10 % 3',
        '2 ** 10',
        '-5 + 2',
        '1 / 0',
        'x + 1',
    ]
    for code in tests:
        result, error = Interpreter().run('<test>', code + '\n')
        if error:
            print(f'{code:<12} =  {error.error_name}: {error.details}')
        else:
            print(f'{code:<12} =  {result}')
