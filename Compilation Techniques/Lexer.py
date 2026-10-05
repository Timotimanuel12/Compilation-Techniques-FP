
#  Character sets
DIGIT   = '0123456789'
LETTERS = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ'
LETTERS_DIGITS = LETTERS + DIGIT

# Keywords
KEYWORDS = [
    'var',
    'and',
    'or',
    'not',
    'if',
    'elif',
    'else',
    'while',
    'for',
    'to',
    'step',
    'func',
    'return',
    'true',
    'false',
    'null',
]

# Token types
TT_INT       = 'INT'
TT_FLOAT     = 'FLOAT'
TT_STRING    = 'STRING'
TT_IDENTIFIER= 'IDENTIFIER'
TT_KEYWORD   = 'KEYWORD'

# Arithmetic
TT_PLUS   = 'PLUS'       # +
TT_MINUS  = 'MINUS'      # -
TT_MUL    = 'MUL'        # *
TT_DIV    = 'DIV'        # /
TT_POW    = 'POW'        # **
TT_MOD    = 'MOD'        # %

# Assignment
TT_EQ     = 'EQ'         # =

# Comparison
TT_EQEQ   = 'EQEQ'      # ==
TT_NEQ    = 'NEQ'        # !=
TT_LT     = 'LT'         # <
TT_GT     = 'GT'         # >
TT_LTE    = 'LTE'        # <=
TT_GTE    = 'GTE'        # >=

# Delimiters
TT_LPAREN  = 'LPAREN'    # (
TT_RPAREN  = 'RPAREN'    # )
TT_LBRACE  = 'LBRACE'    # {
TT_RBRACE  = 'RBRACE'    # }
TT_LBRACKET= 'LBRACKET'  # [
TT_RBRACKET= 'RBRACKET'  # ]
TT_COMMA   = 'COMMA'     # ,
TT_COLON   = 'COLON'     # :
TT_SEMI    = 'SEMI'      # ;
TT_DOT     = 'DOT'       # .
TT_NEWLINE = 'NEWLINE'
TT_EOF     = 'EOF'


#  Errors
class Error:
    def __init__(self, pos_start, pos_end, error_name, details):
        self.pos_start  = pos_start
        self.pos_end    = pos_end
        self.error_name = error_name
        self.details    = details

    def as_string(self):
        result  = f'{self.error_name}: {self.details}\n'
        result += f'File {self.pos_start.fn}, line {self.pos_start.ln + 1}'
        return result


class IllegalCharError(Error):
    def __init__(self, pos_start, pos_end, details):
        super().__init__(pos_start, pos_end, 'Illegal Character', details)


class UnterminatedStringError(Error):
    def __init__(self, pos_start, pos_end):
        super().__init__(pos_start, pos_end, 'Unterminated String',
                         'String literal was never closed with a matching quote')


#  Position
class Position:
    def __init__(self, idx, ln, col, fn, ftxt):
        self.idx  = idx
        self.ln   = ln
        self.col  = col
        self.fn   = fn
        self.ftxt = ftxt

    def advance(self, current_char=None):
        self.idx += 1
        self.col += 1

        if current_char == '\n':
            self.ln  += 1
            self.col  = 0

        return self

    def copy(self):
        return Position(self.idx, self.ln, self.col, self.fn, self.ftxt)

    def __repr__(self):
        return f'(ln={self.ln + 1}, col={self.col})'


#  Token
class Token:
    def __init__(self, type_, value=None, pos_start=None, pos_end=None):
        self.type  = type_
        self.value = value

        if pos_start:
            self.pos_start = pos_start.copy()
            self.pos_end   = pos_start.copy()
            self.pos_end.advance()
        if pos_end:
            self.pos_end = pos_end.copy()

    def matches(self, type_, value):
        """Check if token is a specific keyword or identifier."""
        return self.type == type_ and self.value == value

    def __repr__(self):
        if self.value is not None:
            return f'{self.type}:{self.value}'
        return f'{self.type}'


#  Lexer
class Lexer:
    def __init__(self, fn, text):
        self.fn           = fn
        self.text         = text
        self.pos          = Position(-1, 0, -1, fn, text)
        self.current_char = None
        self.advance()

    # Iteration
    def advance(self):
        self.pos.advance(self.current_char)
        self.current_char = (
            self.text[self.pos.idx]
            if self.pos.idx < len(self.text)
            else None
        )

    def peek(self): #looks at the next character without consuming
        peek_idx = self.pos.idx + 1
        return self.text[peek_idx] if peek_idx < len(self.text) else None

    # Main tokenise loop ─────────────────────
    def make_tokens(self):
        tokens = []

        while self.current_char is not None:
            ch = self.current_char

            # Skip whitespace (not newlines) 
            if ch in ' \t':
                self.advance()

            # Newline → statement boundary 
            elif ch == '\n':
                tokens.append(Token(TT_NEWLINE, pos_start=self.pos))
                self.advance()

            # Single-line comment (#) 
            elif ch == '#':
                self.skip_comment()

            # Numbers 
            elif ch in DIGIT:
                tokens.append(self.make_number())

            # Identifiers / keywords 
            elif ch in LETTERS or ch == '_':
                tokens.append(self.make_identifier())

            # Strings 
            elif ch in ('"', "'"):
                tok, err = self.make_string(ch)
                if err: return [], err
                tokens.append(tok)

            # Two char operators first 
            elif ch == '*' and self.peek() == '*':
                tokens.append(Token(TT_POW, pos_start=self.pos))
                self.advance(); self.advance()

            elif ch == '=' and self.peek() == '=':
                tokens.append(Token(TT_EQEQ, pos_start=self.pos))
                self.advance(); self.advance()

            elif ch == '!' and self.peek() == '=':
                tokens.append(Token(TT_NEQ, pos_start=self.pos))
                self.advance(); self.advance()

            elif ch == '<' and self.peek() == '=':
                tokens.append(Token(TT_LTE, pos_start=self.pos))
                self.advance(); self.advance()

            elif ch == '>' and self.peek() == '=':
                tokens.append(Token(TT_GTE, pos_start=self.pos))
                self.advance(); self.advance()

            # Single-char operators / delimiters 
            elif ch == '+':  tokens.append(Token(TT_PLUS,     pos_start=self.pos)); self.advance()
            elif ch == '-':  tokens.append(Token(TT_MINUS,    pos_start=self.pos)); self.advance()
            elif ch == '*':  tokens.append(Token(TT_MUL,      pos_start=self.pos)); self.advance()
            elif ch == '/':  tokens.append(Token(TT_DIV,      pos_start=self.pos)); self.advance()
            elif ch == '%':  tokens.append(Token(TT_MOD,      pos_start=self.pos)); self.advance()
            elif ch == '=':  tokens.append(Token(TT_EQ,       pos_start=self.pos)); self.advance()
            elif ch == '<':  tokens.append(Token(TT_LT,       pos_start=self.pos)); self.advance()
            elif ch == '>':  tokens.append(Token(TT_GT,       pos_start=self.pos)); self.advance()
            elif ch == '(':  tokens.append(Token(TT_LPAREN,   pos_start=self.pos)); self.advance()
            elif ch == ')':  tokens.append(Token(TT_RPAREN,   pos_start=self.pos)); self.advance()
            elif ch == '{':  tokens.append(Token(TT_LBRACE,   pos_start=self.pos)); self.advance()
            elif ch == '}':  tokens.append(Token(TT_RBRACE,   pos_start=self.pos)); self.advance()
            elif ch == '[':  tokens.append(Token(TT_LBRACKET, pos_start=self.pos)); self.advance()
            elif ch == ']':  tokens.append(Token(TT_RBRACKET, pos_start=self.pos)); self.advance()
            elif ch == ',':  tokens.append(Token(TT_COMMA,    pos_start=self.pos)); self.advance()
            elif ch == ':':  tokens.append(Token(TT_COLON,    pos_start=self.pos)); self.advance()
            elif ch == ';':  tokens.append(Token(TT_SEMI,     pos_start=self.pos)); self.advance()
            elif ch == '.':  tokens.append(Token(TT_DOT,      pos_start=self.pos)); self.advance()

            # Unknown character 
            else:
                pos_start = self.pos.copy()
                self.advance()
                return [], IllegalCharError(pos_start, self.pos, f"'{ch}'")

        tokens.append(Token(TT_EOF, pos_start=self.pos))
        return tokens, None

    # Helper: skip comment
    def skip_comment(self):
        """Advance past everything until end of line."""
        while self.current_char is not None and self.current_char != '\n':
            self.advance()

    # Helper: make number 
    def make_number(self):
        num_str   = ''
        dot_count = 0
        pos_start = self.pos.copy()

        while self.current_char is not None and self.current_char in DIGIT + '.':
            if self.current_char == '.':
                if dot_count == 1: break
                dot_count += 1
            num_str += self.current_char
            self.advance()

        if dot_count == 0:
            return Token(TT_INT,   int(num_str),   pos_start, self.pos)
        else:
            return Token(TT_FLOAT, float(num_str), pos_start, self.pos)

    # Helper: make identifier or keyword
    def make_identifier(self):
        id_str    = ''
        pos_start = self.pos.copy()

        while self.current_char is not None and self.current_char in LETTERS_DIGITS + '_':
            id_str += self.current_char
            self.advance()

        # Decide: is it a reserved keyword or a plain identifier?
        tok_type = TT_KEYWORD if id_str in KEYWORDS else TT_IDENTIFIER
        return Token(tok_type, id_str, pos_start, self.pos)
    
    # Helper: make string literal 
    def make_string(self, quote_char):
        string    = ''
        pos_start = self.pos.copy()
        self.advance()          # skip opening quote

        # Escape sequences supported inside strings
        escape_chars = {
            'n':  '\n',
            't':  '\t',
            '\\': '\\',
            '"':  '"',
            "'":  "'",
        }

        while self.current_char is not None and self.current_char != quote_char:
            if self.current_char == '\\':
                self.advance()
                ch = self.current_char
                string += escape_chars.get(ch, '\\' + (ch or ''))
            else:
                string += self.current_char
            self.advance()

        if self.current_char is None:
            return None, UnterminatedStringError(pos_start, self.pos)

        self.advance()          # skip closing quote
        return Token(TT_STRING, string, pos_start, self.pos), None


#  Entry point
def run(fn, text):
    lexer = Lexer(fn, text)
    tokens, error = lexer.make_tokens()
    return tokens, error