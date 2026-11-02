# main.py
#
# How to use:
#   python main.py examples/basics.txt    → run a program from a file
#   python main.py                        → open the shell and type code

import sys

from Interpreter import Interpreter


def run_file(path):
    try:
        with open(path, encoding='utf-8') as f:
            code = f.read()
    except FileNotFoundError:
        print(f"Can't find the file: {path}")
        return

    # The extra '\n' makes sure the last line always ends with a NEWLINE
    _, error = Interpreter().run(path, code + '\n')
    if error:
        print(error.as_string())


def run_shell():
    print('Type code and press Enter. Type "exit" to quit.')
    interpreter = Interpreter()     # one interpreter, so variables are remembered

    while True:
        try:
            code = input('>>> ')
            if code.strip() == 'exit':
                break

            # If a line opens a block with '{', keep reading until it is closed
            while code.count('{') > code.count('}'):
                code += '\n' + input('... ')
        except (KeyboardInterrupt, EOFError):   # Ctrl+C or Ctrl+Z
            break

        result, error = interpreter.run('<shell>', code + '\n')
        if error:
            print(error.as_string())
        elif result is not None:
            print(result)


if __name__ == '__main__':
    if len(sys.argv) > 1:
        run_file(sys.argv[1])
    else:
        run_shell()
