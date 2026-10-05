# Parser.py
#
# ══════════════════════════════════════════════════════════════════════════════
#  EBNF GRAMMAR  (see EBNF_Grammar.txt for the full reference)
#
#   program     = { statement } EOF
#   statement   = var_decl | if_stmt | while_stmt | for_stmt
#               | func_def | return_stmt | expr_stmt
#   expr        = assign → or → and → not → comparison
#               → arithmetic → term → factor → power → call → atom
# ══════════════════════════════════════════════════════════════════════════════


# ──────────────────────────────────────────────────────────────────────────────
#  STEP 1 — AST NODE CLASSES
#
#  Each class represents one "shape" of node that can appear in the tree.
#  The parser will create instances of these as it reads tokens.
#  The interpreter (a future step) will walk the tree and evaluate them.
# ──────────────────────────────────────────────────────────────────────────────


# ── Literals ──────────────────────────────────────────────────────────────────

class NumberNode:
    """
    Represents an integer or float literal.
    Example source:  42   or   3.14
    """
    def __init__(self, tok):
        self.tok = tok                  # the INT or FLOAT token

    def __repr__(self):
        return f'{self.tok}'


class StringNode:
    """
    Represents a string literal.
    Example source:  "hello"
    """
    def __init__(self, tok):
        self.tok = tok                  # the STRING token

    def __repr__(self):
        return f'{self.tok}'


class BoolNode:
    """
    Represents a boolean literal.
    Example source:  true   or   false
    """
    def __init__(self, tok):
        self.tok = tok                  # KEYWORD token with value 'true'/'false'

    def __repr__(self):
        return f'{self.tok}'


class NullNode:
    """
    Represents the null literal.
    Example source:  null
    """
    def __init__(self, tok):
        self.tok = tok                  # KEYWORD token with value 'null'

    def __repr__(self):
        return 'null'


class ListNode:
    """
    Represents a list literal.
    Example source:  [1, 2, 3]
    """
    def __init__(self, element_nodes, pos_start, pos_end):
        self.element_nodes = element_nodes  # list of AST nodes (the items)
        self.pos_start     = pos_start
        self.pos_end       = pos_end

    def __repr__(self):
        return f'[{", ".join(str(e) for e in self.element_nodes)}]'


# ── Variables ─────────────────────────────────────────────────────────────────

class VarAccessNode:
    """
    Represents reading the value of a variable.
    Example source:  x
    """
    def __init__(self, var_name_tok):
        self.var_name_tok = var_name_tok    # IDENTIFIER token
        self.pos_start    = var_name_tok.pos_start
        self.pos_end      = var_name_tok.pos_end

    def __repr__(self):
        return f'{self.var_name_tok}'


class VarAssignNode:
    """
    Represents declaring or re-assigning a variable.
    Example source:  var x = 10   or   x = 99
    The 'is_declaration' flag distinguishes var x = ... from x = ...
    """
    def __init__(self, var_name_tok, value_node, is_declaration=False):
        self.var_name_tok  = var_name_tok   # IDENTIFIER token
        self.value_node    = value_node     # the right-hand-side expression node
        self.is_declaration = is_declaration
        self.pos_start     = var_name_tok.pos_start
        self.pos_end       = value_node.pos_end

    def __repr__(self):
        prefix = 'var ' if self.is_declaration else ''
        return f'({prefix}{self.var_name_tok} = {self.value_node})'


# ── Operations ────────────────────────────────────────────────────────────────

class BinOpNode:
    """
    Represents a binary operation between two expressions.
    Example source:  3 + 4   or   x == y   or   a and b
    """
    def __init__(self, left_node, op_tok, right_node):
        self.left_node  = left_node     # left-hand AST node
        self.op_tok     = op_tok        # the operator token (PLUS, MUL, EQEQ …)
        self.right_node = right_node    # right-hand AST node
        self.pos_start  = left_node.pos_start
        self.pos_end    = right_node.pos_end

    def __repr__(self):
        return f'({self.left_node} {self.op_tok} {self.right_node})'


class UnaryOpNode:
    """
    Represents a unary operation on a single expression.
    Example source:  -x   or   not active
    """
    def __init__(self, op_tok, node):
        self.op_tok    = op_tok     # the operator token (MINUS, keyword 'not')
        self.node      = node       # the operand AST node
        self.pos_start = op_tok.pos_start
        self.pos_end   = node.pos_end

    def __repr__(self):
        return f'({self.op_tok} {self.node})'


# ── Function call & access ────────────────────────────────────────────────────

class CallNode:
    """
    Represents a function call.
    Example source:  add(3, 7)   or   print("hi")
    """
    def __init__(self, callee_node, arg_nodes):
        self.callee_node = callee_node  # the expression being called (e.g. VarAccessNode)
        self.arg_nodes   = arg_nodes    # list of argument AST nodes
        self.pos_start   = callee_node.pos_start
        self.pos_end     = arg_nodes[-1].pos_end if arg_nodes else callee_node.pos_end

    def __repr__(self):
        args = ', '.join(str(a) for a in self.arg_nodes)
        return f'({self.callee_node}({args}))'


class IndexNode:
    """
    Represents index access into a list or string.
    Example source:  items[0]
    """
    def __init__(self, collection_node, index_node):
        self.collection_node = collection_node  # the list/string being indexed
        self.index_node      = index_node       # the index expression
        self.pos_start       = collection_node.pos_start
        self.pos_end         = index_node.pos_end

    def __repr__(self):
        return f'({self.collection_node}[{self.index_node}])'


# ── Control flow ──────────────────────────────────────────────────────────────

class IfNode:
    """
    Represents an if / elif / else statement.
    Example source:
        if x > 5 { ... } elif x == 5 { ... } else { ... }

    'cases' is a list of (condition_node, body_node) pairs — one per if/elif.
    'else_case' is an optional body_node for the else branch.
    """
    def __init__(self, cases, else_case):
        self.cases     = cases          # list of (condition, block) tuples
        self.else_case = else_case      # block node or None
        self.pos_start = cases[0][0].pos_start
        self.pos_end   = (else_case or cases[-1][1]).pos_end

    def __repr__(self):
        parts = ' '.join(f'if {c} then {b}' for c, b in self.cases)
        if self.else_case:
            parts += f' else {self.else_case}'
        return f'({parts})'


class WhileNode:
    """
    Represents a while loop.
    Example source:  while x > 0 { x = x - 1 }
    """
    def __init__(self, condition_node, body_node):
        self.condition_node = condition_node
        self.body_node      = body_node
        self.pos_start      = condition_node.pos_start
        self.pos_end        = body_node.pos_end

    def __repr__(self):
        return f'(while {self.condition_node} do {self.body_node})'


class ForNode:
    """
    Represents a for loop.
    Example source:  for i = 1 to 10 step 2 { ... }

    'step_node' is optional (None if not specified).
    """
    def __init__(self, var_name_tok, start_node, end_node, step_node, body_node):
        self.var_name_tok = var_name_tok    # loop variable IDENTIFIER token
        self.start_node   = start_node      # starting value expression
        self.end_node     = end_node        # ending value expression
        self.step_node    = step_node       # step expression or None
        self.body_node    = body_node
        self.pos_start    = var_name_tok.pos_start
        self.pos_end      = body_node.pos_end

    def __repr__(self):
        step = f' step {self.step_node}' if self.step_node else ''
        return f'(for {self.var_name_tok} = {self.start_node} to {self.end_node}{step} do {self.body_node})'


# ── Functions ─────────────────────────────────────────────────────────────────

class FuncDefNode:
    """
    Represents a function definition.
    Example source:  func add(a, b) { return a + b }

    'func_name_tok' is None for anonymous / lambda functions.
    'param_toks' is a list of IDENTIFIER tokens.
    """
    def __init__(self, func_name_tok, param_toks, body_node):
        self.func_name_tok = func_name_tok  # IDENTIFIER token or None
        self.param_toks    = param_toks     # list of IDENTIFIER tokens
        self.body_node     = body_node
        self.pos_start     = func_name_tok.pos_start if func_name_tok else body_node.pos_start
        self.pos_end       = body_node.pos_end

    def __repr__(self):
        name   = self.func_name_tok or '<anonymous>'
        params = ', '.join(str(p) for p in self.param_toks)
        return f'(func {name}({params}) {self.body_node})'


class ReturnNode:
    """
    Represents a return statement.
    Example source:  return a + b   or just   return
    'return_node' is None when returning without a value.
    """
    def __init__(self, return_node, pos_start, pos_end):
        self.return_node = return_node  # expression node or None
        self.pos_start   = pos_start
        self.pos_end     = pos_end

    def __repr__(self):
        if self.return_node:
            return f'(return {self.return_node})'
        return '(return)'


# ── Program body ──────────────────────────────────────────────────────────────

class BlockNode:
    """
    Represents a sequence of statements inside { }.
    Used as the body of if / while / for / func.
    """
    def __init__(self, statement_nodes, pos_start, pos_end):
        self.statement_nodes = statement_nodes  # ordered list of statement nodes
        self.pos_start       = pos_start
        self.pos_end         = pos_end

    def __repr__(self):
        stmts = '; '.join(str(s) for s in self.statement_nodes)
        return f'{{ {stmts} }}'
