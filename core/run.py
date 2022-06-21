from core.interpreterController import Interpreter
from core.parserController import Parser
from core.lexerController import Lexer
from core.contextController import Context
from core.symbolTable import SymbolTable
from core.numberController import Number

import pprint

global_symbol_table = SymbolTable()
# global_symbol_table.set("null", Number(0))

def run(fn, text):

    #Generate Tokens
    lexer = Lexer(fn, text)
    tokens, error = lexer.make_tokens()

    if error: return None, error

    # Generate Syntax Tree
    parser = Parser(tokens)
    ast = parser.parse()

    if ast.error: return None, ast.error
    
    pp = pprint.PrettyPrinter(indent=4)

    #Run interpreter
    interpreter = Interpreter()
    context = Context('<program>')
    context.symbol_table = global_symbol_table
    result = interpreter.visit(ast.node, context)

    return result.value, result.error