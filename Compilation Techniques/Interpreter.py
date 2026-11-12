# Interpreter.py
#
# ══════════════════════════════════════════════════════════════════════════════
#  STEP 3 — THE INTERPRETER
#
#  The interpreter walks through the tree built by the Parser and runs it.
#  There is ONE function for each kind of node, named visit_<NodeName>.
#  For example, a NumberNode is handled by visit_NumberNode.
#
#  Built so far:
#    - Part 1: numbers and maths ( + - * / % ** and negative numbers )
#    - Part 2: variables and scopes ( var x = 10, x = 20 )
# ══════════════════════════════════════════════════════════════════════════════

from Lexer import *
from Nodes import *
from Parser import Parser


class RTError(Error):
    """An error that happens while the program is running, e.g. 1 / 0."""
    def __init__(self, node, details):
        super().__init__(node.pos_start, node.pos_end, 'Runtime Error', details)


class Scope:
    """Stores variables in a dictionary. Inner scopes can look up outer ones."""
    def __init__(self, parent=None):
        self.values = {}
        self.parent = parent

    def define(self, name, value):
        """Create a new variable in this scope (var x = ...)."""
        self.values[name] = value

    def get(self, name):
        """Read a variable, checking outer scopes if needed."""
        if name in self.values:
            return True, self.values[name]
        if self.parent:
            return self.parent.get(name)
        return False, None

    def set(self, name, value):
        """Update an existing variable, checking outer scopes if needed."""
        if name in self.values:
            self.values[name] = value
            return True
        if self.parent:
            return self.parent.set(name, value)
        return False


class Interpreter:
    def __init__(self):
        self.scope = Scope()            # global scope for the whole program

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

    # ── Variables (Part 2) ────────────────────────────────────────────────────

    def visit_VarAccessNode(self, node):
        name = node.var_name_tok.value
        found, value = self.scope.get(name)
        if not found:
            raise RTError(node, f"'{name}' is not defined")
        return value

    def visit_VarAssignNode(self, node):
        name  = node.var_name_tok.value
        value = self.visit(node.value_node)

        if node.is_declaration:         # var x = 10
            self.scope.define(name, value)
        else:                           # x = 20
            if not self.scope.set(name, value):
                raise RTError(node, f"'{name}' is not defined (use 'var {name} = ...' first)")

        return value

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
    interpreter = Interpreter()
    tests = [
        # Part 1: maths
        '1 + 2',
        '1 + 2 * 3',
        '(1 + 2) * 3',
        '10 / 4',
        '10 % 3',
        '2 ** 10',
        '-5 + 2',
        '1 / 0',
        # Part 2: variables
        'var x = 10',
        'x = x + 5',
        'x * 2',
        'y = 1',
    ]
    for code in tests:
        result, error = interpreter.run('<test>', code + '\n')
        if error:
            print(f'{code:<16} =  {error.error_name}: {error.details}')
        else:
            print(f'{code:<16} =  {result}')
