from core.interpreterController import Interpreter
from core.parserController import Parser
from core.lexerController import Lexer
from core.contextController import Context
from core.symbolTable import SymbolTable
from core.numberController import Number
from core.interpreterController import BuiltInFunction
import const.constants

import pprint

global_symbol_table = SymbolTable()
global_symbol_table.set(const.constants.NULL, Number.null)
global_symbol_table.set(const.constants.TRUE, Number.true)
global_symbol_table.set(const.constants.FALSE, Number.false)
global_symbol_table.set("MATH_PI", Number.math_PI)
global_symbol_table.set("printo", BuiltInFunction.printo)
global_symbol_table.set("shtyp", BuiltInFunction.shtyp)
global_symbol_table.set("shtyp_num", BuiltInFunction.shtyp_num)
# global_symbol_table.set("pastro", BuiltInFunction.clear)
global_symbol_table.set("eshte_num", BuiltInFunction.eshte_num)
global_symbol_table.set("eshte_tekst", BuiltInFunction.eshte_tekst)
global_symbol_table.set("eshte_list", BuiltInFunction.eshte_list)
global_symbol_table.set("eshte_fun", BuiltInFunction.eshte_fun)
global_symbol_table.set("shto", BuiltInFunction.shto)
global_symbol_table.set("fshij", BuiltInFunction.fshij)
global_symbol_table.set("zgjat", BuiltInFunction.zgjat)
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