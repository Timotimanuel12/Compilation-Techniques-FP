# CompTech: A Small Scripting Language

This is a project for the **Compilation Techniques** course.
It is a small programming language, written in Python, together with the tools that read it.

Right now the project can:

1. **Read** code written in the language and split it into words (the **Lexer**).
2. **Understand** the structure of the code and build a tree from it (the **Parser**).

Running the code (the **Interpreter**) is not built yet.


## What the language looks like

```
# This is a comment
var x = 10

func add(a, b) {
    return a + b
}

if x > 5 and not false {
    print(add(x, 2) * 3)
} elif x == 5 {
    print("five")
} else {
    x = x - 1
}

for i = 1 to 10 step 2 {
    print(i)
}

while x > 0 {
    x = x - 1
}

var items = [1, 2, 3]
print(items[0])
```

The language has:

- **Values:** whole numbers (`10`), decimal numbers (`3.14`), text (`"hello"`), `true`, `false`, `null` and lists (`[1, 2, 3]`)
- **Variables:** `var x = 10` creates a variable, `x = 20` changes it
- **Maths:** `+  -  *  /  %` and `**` (power)
- **Comparisons:** `==  !=  <  >  <=  >=`
- **Logic:** `and`, `or`, `not`
- **Control flow:** `if` / `elif` / `else`, `while`, `for ... to ... step`
- **Functions:** `func name(params) { ... }` and `return`
- **Comments:** everything after `#` on a line is ignored


### Rules to remember

- Each statement goes on **its own line**.
- Blocks `{ }` are written over **several lines**. This does not work:
  `if x { print(x) }`
- `elif` and `else` go on the **same line** as the `}` before them: `} else {`
- The file must **end with an empty line**.


## How it works

```
 source code  ──►  Lexer  ──►  tokens  ──►  Parser  ──►  tree
   (text)        Lexer.py                 Parser.py    (Nodes.py)
```

**1. Lexer:** reads the code one character at a time and groups the characters into **tokens**.

```
var x = 10    ──►    KEYWORD:var  IDENTIFIER:x  EQ  INT:10  NEWLINE
```

**2. Parser:** reads the tokens from left to right and builds a **tree** that shows how the code fits together.
For example, `1 + 2 * 3` becomes:

```
      +
     / \
    1   *
       / \
      2   3
```

The `*` is lower in the tree, so it is worked out first.

The parser follows the grammar in `LL1_Grammar.txt`. There is one Python function for each grammar rule, with the same name.
The grammar is **LL(1)**: the parser can always decide what to do by looking at just the next token.


## Files

All the code is in the `Compilation Techniques` folder.

| File | What it does |
|---|---|
| `Lexer.py` | Turns text into tokens. Also has the `Error` and `Position` classes. |
| `Parser.py` | Turns tokens into a tree. |
| `Nodes.py` | The pieces of the tree (`NumberNode`, `IfNode`, `BlockNode`, ...). |
| `LL1_Grammar.txt` | The grammar of the language, written as an LL(1) context-free grammar. The parser follows this file. |
| `EBNF_Grammar.txt` | An earlier version of the grammar in EBNF form. It does not yet match `LL1_Grammar.txt` exactly. |


## How to run it

You need **Python 3** (tested with Python 3.12). No extra packages are needed.

```
cd "Compilation Techniques"
python Parser.py
```

This parses a small example program and prints its tree:

```
(var IDENTIFIER:x = INT:10)
(func IDENTIFIER:add(IDENTIFIER:a, IDENTIFIER:b) { (return (IDENTIFIER:a PLUS IDENTIFIER:b)) })
(if ((IDENTIFIER:x GT INT:5) KEYWORD:and (KEYWORD:not KEYWORD:false)) then { ... } else { ... })
```

To parse your own code from Python:

```python
from Parser import run

tree, error = run('<my code>', 'var x = 1 + 2\n')
if error:
    print(error.as_string())
else:
    print(tree)
```

If the code has a mistake, you get an error with the line number, for example:

```
Invalid Syntax: Expected ')'
File <my code>, line 1
```


## Progress

- [x] Grammar (EBNF and LL(1))
- [x] Lexer
- [x] Parser
- [ ] Interpreter (to actually run the code)
