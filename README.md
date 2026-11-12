# CompTech: A Small Scripting Language

This is a project for the **Compilation Techniques** course.
It is a small programming language, written in Python, together with the tools that read and run it.

The project has three parts:

1. The **Lexer** reads the code and splits it into words (tokens).
2. The **Parser** understands the structure of the code and builds a tree from it.
3. The **Interpreter** walks through the tree and runs the program.


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

for i = 0 to 10 step 2 {
    print(i)            # 0 2 4 6 8
}

while x > 0 {
    x = x - 1
}

var items = [1, 2, 3]
append(items, 4)
print(items[0], len(items))
```

The language has:

- **Values:** whole numbers (`10`), decimal numbers (`3.14`), text (`"hello"`), `true`, `false`, `null` and lists (`[1, 2, 3]`)
- **Variables:** `var x = 10` creates a variable, `x = 20` changes it
- **Maths:** `+  -  *  /  %` and `**` (power)
- **Comparisons:** `==  !=  <  >  <=  >=`
- **Logic:** `and`, `or`, `not`
- **Control flow:** `if` / `elif` / `else`, `while`, `for ... to ... step`
- **Functions:** `func name(params) { ... }` and `return`. Functions can call themselves (recursion) and can be passed to other functions.
- **Lists:** `items[0]` gets the first item, `items[-1]` gets the last
- **Comments:** everything after `#` on a line is ignored


### Built-in functions

| Function | Example | Result |
|---|---|---|
| `print(...)` | `print("Age:", 20)` | shows `Age: 20` |
| `input(text)` | `input("Name? ")` | the text the user types |
| `len(x)` | `len([1, 2, 3])` | `3` |
| `str(x)` | `str(42)` | `"42"` |
| `int(x)` | `int("42")` | `42` |
| `float(x)` | `float("1.5")` | `1.5` |
| `append(list, x)` | `append(items, 4)` | adds `4` to the end of `items` |
| `random(a, b)` | `random(1, 6)` | a whole number from 1 to 6 |


### Rules to remember

- Each statement goes on **its own line**.
- Blocks `{ }` are written over **several lines**. This does not work:
  `if x { print(x) }`
- `elif` and `else` go on the **same line** as the `}` before them: `} else {`
- `for i = 0 to 5` counts **0, 1, 2, 3, 4**. The end number is not included (like Python's `range`).
- Use `var` the first time you create a variable. Writing `x = 5` without `var x` first gives an error. This catches typos in variable names.
- Variables made inside a function stay inside that function.
- In `if` and `while`, the values `false`, `null`, `0`, `""` and `[]` count as false.


## How it works

```
 source code  ──►  Lexer  ──►  tokens  ──►  Parser  ──►  tree  ──►  Interpreter  ──►  result
   (text)        Lexer.py                 Parser.py   (Nodes.py)   Interpreter.py
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

**3. Interpreter:** walks through the tree and runs it. There is one Python function for each kind of node.
For example, `visit_NumberNode` handles numbers and `visit_IfNode` handles `if` statements.
For the tree above, it first works out `2 * 3 = 6`, then `1 + 6 = 7`.

Values in the language are stored as normal Python values (`10` is a Python `int`, `[1, 2]` is a Python `list`).
Variables are kept in **scopes**: one global scope for the whole program, plus a new scope for every function call.


## Files

All the code is in the `Compilation Techniques` folder.

| File | What it does |
|---|---|
| `main.py` | Start here. Runs a program file, or opens the interactive shell. |
| `Lexer.py` | Turns text into tokens. Also has the `Error` and `Position` classes. |
| `Parser.py` | Turns tokens into a tree. |
| `Nodes.py` | The pieces of the tree (`NumberNode`, `IfNode`, `BlockNode`, ...). |
| `Interpreter.py` | Runs the tree. |
| `examples/` | Example programs: `basics.txt`, `functions.txt`, `guessing_game.txt`. |
| `LL1_Grammar.txt` | The grammar of the language, written as an LL(1) context-free grammar. The parser follows this file. |
| `EBNF_Grammar.txt` | An earlier version of the grammar in EBNF form. It does not yet match `LL1_Grammar.txt` exactly. |


## How to run it

You need **Python 3** (tested with Python 3.12). No extra packages are needed.

**Run a program file:**

```
cd "Compilation Techniques"
python main.py examples/basics.txt
```

This prints:

```
Hello, World!
a + b  = 9
a / b  = 3.5
...
```

**Test the interpreter** (runs a few calculations):

```
python Interpreter.py
```

**Open the interactive shell** and type code line by line:

```
python main.py
```

```
>>> var x = 5
5
>>> func square(n) {
...     return n * n
... }
>>> square(x)
25
>>> exit
```

**See the tree** the parser builds (without running it):

```
python Parser.py
```


## Errors

When something is wrong, you get a message with the line number. There are three kinds:

| Kind | When | Example |
|---|---|---|
| `Illegal Character` | The lexer finds a character it does not know | `print($)` |
| `Invalid Syntax` | The code does not follow the grammar | `print(1, 2` → `Expected ')'` |
| `Runtime Error` | Something goes wrong while running | `print(1 / 0)` → `Division by zero` |


## Progress

- [x] Grammar (EBNF and LL(1))
- [x] Lexer
- [x] Parser
- [x] Interactive shell (`main.py`)
- [ ] Interpreter, built in parts:
  - [x] Part 1: maths (`+ - * / % **`, negative numbers)
  - [x] Part 2: variables
  - [ ] Part 3: text, true/false/null, lists, comparisons, `and` / `or` / `not`
  - [ ] Part 4: `if`, `while`, `for`
  - [ ] Part 5: functions and built-in functions (`print`, `input`, ...)
- [ ] Example programs running
- [ ] Code editor window (`tkinter`) for the demo
