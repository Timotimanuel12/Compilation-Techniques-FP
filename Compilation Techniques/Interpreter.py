# Interpreter.py
#
# ══════════════════════════════════════════════════════════════════════════════
#  STEP 3 — THE INTERPRETER
#
#  The interpreter walks through the tree built by the Parser and runs it.
#  There is ONE function for each kind of node, named visit_<NodeName>.
#  For example, a NumberNode is handled by visit_NumberNode.
#
#  Built in 5 parts:
#    - Part 1: numbers and maths ( + - * / % ** and negative numbers )
#    - Part 2: variables and scopes ( var x = 10, x = 20 )
#    - Part 3: strings, booleans, null, lists, indexing, comparisons, and/or/not
#    - Part 4: control flow ( if / elif / else, while, for )
#    - Part 5: functions and built-in functions ( func, return, print, ... )
# ══════════════════════════════════════════════════════════════════════════════

import random

from Lexer import *
from Nodes import *
from Parser import Parser


class RTError(Error):
    """An error that happens while the program is running, e.g. 1 / 0."""
    def __init__(self, node, details):
        super().__init__(node.pos_start, node.pos_end, 'Runtime Error', details)


class ReturnSignal(Exception):
    """Used internally to jump out of a function when 'return' is reached."""
    def __init__(self, value, node):
        self.value = value
        self.node  = node


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


class Function:
    """A user-defined function created with 'func name(params) { ... }'."""
    def __init__(self, name, param_names, body_node, defining_scope):
        self.name           = name
        self.param_names    = param_names
        self.body_node      = body_node
        self.defining_scope = defining_scope

    def __repr__(self):
        return f'<function {self.name}>'


class BuiltInFunction:
    """A built-in function provided by the language, e.g. print() or len()."""
    def __init__(self, name, fn):
        self.name = name
        self.fn   = fn

    def __repr__(self):
        return f'<built-in function {self.name}>'


class Interpreter:
    def __init__(self):
        self.scope = Scope()            # global scope for the whole program
        self._register_builtins()

    def _register_builtins(self):
        """Add the built-in functions to the global scope."""
        builtins = {
            'print':  self._builtin_print,
            'input':  self._builtin_input,
            'len':    self._builtin_len,
            'str':    self._builtin_str,
            'int':    self._builtin_int,
            'float':  self._builtin_float,
            'append': self._builtin_append,
            'random': self._builtin_random,
        }
        for name, fn in builtins.items():
            self.scope.define(name, BuiltInFunction(name, fn))

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
        except ReturnSignal as ret:
            return None, RTError(ret.node, "'return' cannot be used outside a function")
        except Error as error:          # a syntax error or a runtime error
            return None, error

    def visit(self, node):
        """Run one node by calling the matching visit_... function."""
        method_name = f'visit_{type(node).__name__}'    # e.g. 'visit_NumberNode'
        method = getattr(self, method_name, None)       # find the function with that name

        if method is None:
            raise RTError(node, f'{type(node).__name__} is not supported yet')
        return method(node)

    def is_truthy(self, value):
        """false, null, 0, "" and [] count as false; everything else is true."""
        return bool(value)

    # ── Statements in a row ───────────────────────────────────────────────────

    def visit_BlockNode(self, node):
        # Run each statement in order, top to bottom.
        # The value of the last statement is returned (the shell shows it).
        result = None
        for statement in node.statement_nodes:
            result = self.visit(statement)
        return result

    # ── Values (Part 1 & Part 3) ──────────────────────────────────────────────

    def visit_NumberNode(self, node):
        # The lexer already turned the text "42" into the Python number 42,
        # so we just hand it back.
        return node.tok.value

    def visit_StringNode(self, node):
        return node.tok.value

    def visit_BoolNode(self, node):
        return node.tok.value == 'true'

    def visit_NullNode(self, node):
        return None

    def visit_ListNode(self, node):
        return [self.visit(element) for element in node.element_nodes]

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

    # ── Indexing (Part 3) ─────────────────────────────────────────────────────

    def visit_IndexNode(self, node):
        collection = self.visit(node.collection_node)
        index      = self.visit(node.index_node)

        if not isinstance(collection, (list, str)):
            raise RTError(node, 'Only lists and strings can be indexed with [...]')
        if type(index) is not int:
            raise RTError(node.index_node, 'Index must be a whole number')

        try:
            return collection[index]
        except IndexError:
            raise RTError(node.index_node, f'Index {index} is out of range')

    # ── Operators (Part 1 & Part 3) ───────────────────────────────────────────

    def visit_BinOpNode(self, node):
        # Logical operators ('and' / 'or') are checked first so they can short-circuit
        if node.op_tok.matches(TT_KEYWORD, 'and'):
            return self.is_truthy(self.visit(node.left_node)) and self.is_truthy(self.visit(node.right_node))
        if node.op_tok.matches(TT_KEYWORD, 'or'):
            return self.is_truthy(self.visit(node.left_node)) or self.is_truthy(self.visit(node.right_node))

        # A BinOpNode has a left side, an operator and a right side, e.g. 2 * 3.
        # First work out both sides (they may be bigger trees themselves)...
        left  = self.visit(node.left_node)
        right = self.visit(node.right_node)

        # ...then do the operation that matches the operator token.
        op = node.op_tok.type

        # Dividing by zero is impossible, so stop with a clear error message
        if op in (TT_DIV, TT_MOD) and right == 0:
            raise RTError(node, 'Division by zero')

        try:
            # Maths
            if op == TT_PLUS:   return left + right
            if op == TT_MINUS:  return left - right
            if op == TT_MUL:    return left * right
            if op == TT_DIV:    return left / right
            if op == TT_MOD:    return left % right
            if op == TT_POW:    return left ** right

            # Comparisons
            if op == TT_EQEQ:   return left == right
            if op == TT_NEQ:    return left != right
            if op == TT_LT:     return left < right
            if op == TT_GT:     return left > right
            if op == TT_LTE:    return left <= right
            if op == TT_GTE:    return left >= right
        except TypeError:
            raise RTError(node, f'Cannot use {node.op_tok} on {type(left).__name__} and {type(right).__name__}')

        raise RTError(node, f'The operator {op} is not supported yet')

    def visit_UnaryOpNode(self, node):
        # A UnaryOpNode is an operator with only ONE side, e.g. -5 or not true
        value = self.visit(node.node)

        if node.op_tok.matches(TT_KEYWORD, 'not'):
            return not self.is_truthy(value)

        op = node.op_tok.type
        try:
            if op == TT_MINUS:  return -value
            if op == TT_PLUS:   return +value
        except TypeError:
            raise RTError(node, f'Cannot use {node.op_tok} on {type(value).__name__}')

        raise RTError(node, f'The operator {node.op_tok} is not supported yet')

    # ── Control flow (Part 4) ─────────────────────────────────────────────────

    def visit_IfNode(self, node):
        # Check each if / elif condition in order; run the first block that is true
        for condition_node, body_node in node.cases:
            if self.is_truthy(self.visit(condition_node)):
                self.visit(body_node)
                return None

        if node.else_case is not None:
            self.visit(node.else_case)
        return None

    def visit_WhileNode(self, node):
        while self.is_truthy(self.visit(node.condition_node)):
            self.visit(node.body_node)
        return None

    def visit_ForNode(self, node):
        # for i = start to end step s { ... }  (end is not included, like range())
        start = self.visit(node.start_node)
        end   = self.visit(node.end_node)
        step  = self.visit(node.step_node) if node.step_node else 1

        if not isinstance(start, (int, float)) or not isinstance(end, (int, float)) or not isinstance(step, (int, float)):
            raise RTError(node, 'For loop start, end and step must be numbers')
        if step == 0:
            raise RTError(node.step_node, 'For loop step cannot be zero')

        var_name = node.var_name_tok.value
        i = start
        while (i < end) if step > 0 else (i > end):
            self.scope.define(var_name, i)
            self.visit(node.body_node)
            i += step
        return None

    # ── Functions (Part 5) ────────────────────────────────────────────────────

    def visit_FuncDefNode(self, node):
        name        = node.func_name_tok.value
        param_names = [param.value for param in node.param_toks]
        func        = Function(name, param_names, node.body_node, self.scope)
        self.scope.define(name, func)
        return None

    def visit_ReturnNode(self, node):
        value = self.visit(node.return_node) if node.return_node is not None else None
        raise ReturnSignal(value, node)

    def visit_CallNode(self, node):
        callee = self.visit(node.callee_node)
        args   = [self.visit(arg) for arg in node.arg_nodes]

        # 1. Built-in function (print, len, append, ...)
        if isinstance(callee, BuiltInFunction):
            return callee.fn(node, args)

        # 2. User-defined function (func name(...) { ... })
        if isinstance(callee, Function):
            if len(args) != len(callee.param_names):
                raise RTError(
                    node,
                    f"'{callee.name}' expects {len(callee.param_names)} argument(s), but got {len(args)}"
                )

            # Create a fresh local scope for this call, linked to where the function was defined
            call_scope = Scope(parent=callee.defining_scope)
            for param_name, arg_value in zip(callee.param_names, args):
                call_scope.define(param_name, arg_value)

            previous_scope = self.scope
            self.scope = call_scope
            try:
                self.visit(callee.body_node)
                return None
            except ReturnSignal as ret:
                return ret.value
            finally:
                self.scope = previous_scope

        raise RTError(node, f"'{callee}' is not a function")

    # ── Built-in functions (Part 5) ───────────────────────────────────────────

    def _expect_arg_count(self, node, name, args, expected):
        if len(args) != expected:
            raise RTError(node, f"'{name}' expects {expected} argument(s), but got {len(args)}")

    def _builtin_print(self, node, args):
        print(*args)
        return None

    def _builtin_input(self, node, args):
        if len(args) > 1:
            raise RTError(node, f"'input' expects at most 1 argument, but got {len(args)}")
        prompt = str(args[0]) if args else ''
        return input(prompt)

    def _builtin_len(self, node, args):
        self._expect_arg_count(node, 'len', args, 1)
        if not isinstance(args[0], (list, str)):
            raise RTError(node, "'len' only works on lists and strings")
        return len(args[0])

    def _builtin_str(self, node, args):
        self._expect_arg_count(node, 'str', args, 1)
        return str(args[0])

    def _builtin_int(self, node, args):
        self._expect_arg_count(node, 'int', args, 1)
        try:
            return int(args[0])
        except (ValueError, TypeError):
            raise RTError(node, f"Cannot convert '{args[0]}' to an integer")

    def _builtin_float(self, node, args):
        self._expect_arg_count(node, 'float', args, 1)
        try:
            return float(args[0])
        except (ValueError, TypeError):
            raise RTError(node, f"Cannot convert '{args[0]}' to a float")

    def _builtin_append(self, node, args):
        self._expect_arg_count(node, 'append', args, 2)
        if not isinstance(args[0], list):
            raise RTError(node, "First argument to 'append' must be a list")
        args[0].append(args[1])
        return None

    def _builtin_random(self, node, args):
        self._expect_arg_count(node, 'random', args, 2)
        a, b = args
        if type(a) is not int or type(b) is not int:
            raise RTError(node, "'random' expects two whole numbers")
        if a > b:
            raise RTError(node, "'random(a, b)' requires a <= b")
        return random.randint(a, b)


# Run this file directly (python Interpreter.py) to test what is built so far
if __name__ == '__main__':
    interpreter = Interpreter()
    tests = [
        # Part 1: maths
        '1 + 2 * 3',
        '(1 + 2) * 3',
        '10 / 4',
        '2 ** 10',
        '-5 + 2',
        '1 / 0',
        # Part 2: variables
        'var x = 10',
        'x = x + 5',
        'x * 2',
        'y = 1',
        # Part 3: strings, booleans, null, lists, comparisons, logic
        '"Hello, " + "World!"',
        'var items = [10, 20, 30]',
        'items[0] + items[-1]',
        'x == 15 and not false',
        'x < 5 or x >= 15',
        'not null',
        # Part 4 & 5: control flow, functions & built-ins
        'append(items, 40)',
        'len(items)',
        'func square(n) {\n    return n * n\n}',
        'square(6)',
    ]
    for code in tests:
        label = code.replace('\n', ' ')
        result, error = interpreter.run('<test>', code + '\n')
        if error:
            print(f'{label:<34} =  {error.error_name}: {error.details}')
        else:
            print(f'{label:<34} =  {result}')
