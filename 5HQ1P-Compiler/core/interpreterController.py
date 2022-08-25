from core.numberController import Number
from core.RunTimeResultController import RTResult
from core.illegalCharController import RTError
from core.valueController import Value
from core.illegalCharController import RTError
from core.RunTimeResultController import RTResult
from core.contextController import Context
from core.symbolTable import SymbolTable
from core.stringController import String
from core.listController import List
from core.baseFunctionController import BaseFunction
from core.parserController import Parser
from core.lexerController import Lexer
from core.contextController import Context
from core.symbolTable import SymbolTable
from core.numberController import Number
import const.constants
import const.tokens
import pprint

class Interpreter:
	def visit(self, node, context):
		method_name = f'visit_{type(node).__name__}'
		method = getattr(self, method_name, self.no_visit_method)
		return method(node, context)

	def no_visit_method(self, node, context):
		raise Exception(f'No visit_{type(node).__name__} method defined')


	def visit_NumberNode(self, node, context):
		return RTResult().success(
			Number(node.tok.value).set_context(context).set_pos(node.pos_start, node.pos_end)
		)

	def visit_StringNode(self, node, context):
		return RTResult().success(
			String(node.tok.value).set_context(context).set_pos(node.pos_start, node.pos_end)
		)

	def visit_VarAccessNode(self, node, context):
		res = RTResult()
		var_name = node.var_name_tok.value
		value = context.symbol_table.get(var_name)

		if not value:
			return res.failure(RTError(
				node.pos_start, node.pos_end,
				f"'{var_name}' nuk ekziston",
				context
			))

		value = value.copy().set_pos(node.pos_start, node.pos_end).set_context(context)
		return res.success(value)

	def visit_VarAssignNode(self, node, context):
		res = RTResult()
		var_name = node.var_name_tok.value
		value = res.register(self.visit(node.value_node, context))
		if res.should_return(): return res

		context.symbol_table.set(var_name, value)
		return res.success(value)

	def visit_BinOpNode(self, node, context):
		res = RTResult()
		left = res.register(self.visit(node.left_node, context))
		if res.should_return(): return res
		right = res.register(self.visit(node.right_node, context))
		if res.should_return(): return res

		if node.op_tok.type == const.tokens.SS_PLUS:
			result, error = left.added_to(right)
		elif node.op_tok.type == const.tokens.SS_MINUS:
			result, error = left.subbed_by(right)
		elif node.op_tok.type == const.tokens.SS_MUL:
			result, error = left.multed_by(right)
		elif node.op_tok.type == const.tokens.SS_DIV:
			result, error = left.dived_by(right)
		elif node.op_tok.type == const.tokens.SS_POW:
			result, error = left.powed_by(right)
		elif node.op_tok.type == const.tokens.SS_EE:
			result, error = left.get_comparison_eq(right)
		elif node.op_tok.type == const.tokens.SS_NE:
			result, error = left.get_comparison_ne(right)
		elif node.op_tok.type == const.tokens.SS_LT:
			result, error = left.get_comparison_lt(right)
		elif node.op_tok.type == const.tokens.SS_GT:
			result, error = left.get_comparison_gt(right)
		elif node.op_tok.type == const.tokens.SS_LTE:
			result, error = left.get_comparison_lte(right)
		elif node.op_tok.type == const.tokens.SS_GTE:
			result, error = left.get_comparison_gte(right)
		elif node.op_tok.matches(const.tokens.SS_KEYWORD, const.tokens.SS_AND):
			result, error = left.anded_by(right)
		elif node.op_tok.matches(const.tokens.SS_KEYWORD, const.tokens.SS_OR):
			result, error = left.ored_by(right)

		if error:
			return res.failure(error)
		else:
			return res.success(result.set_pos(node.pos_start, node.pos_end))

	def visit_UnaryOpNode(self, node, context):
		res = RTResult()
		number = res.register(self.visit(node.node, context))
		if res.should_return(): return res

		error = None

		if node.op_tok.type == const.tokens.SS_MINUS:
			number, error = number.multed_by(Number(-1))
		elif node.op_tok.matches(const.tokens.SS_KEYWORD, const.tokens.SS_NOT):
			number, error = number.notted()

		if error:
			return res.failure(error)
		else:
			return res.success(number.set_pos(node.pos_start, node.pos_end))

	def visit_IfNode(self, node, context):
		res = RTResult()

		for condition, expr, should_return_null in node.cases:
			condition_value = res.register(self.visit(condition, context))
			if res.should_return(): return res

			if condition_value.is_true():
				expr_value = res.register(self.visit(expr, context))
				if res.should_return(): return res
				return res.success(Number.null if should_return_null else expr_value)

		if node.else_case:
			expr, should_return_null = node.else_case
			expr_value = res.register(self.visit(expr, context))
			if res.should_return(): return res
			return res.success(Number.null if should_return_null else expr_value)

		return res.success(Number.null)

	def visit_ForNode(self, node, context):
		res = RTResult()
		elements = []

		start_value = res.register(self.visit(node.start_value_node, context))
		if res.should_return(): return res

		end_value = res.register(self.visit(node.end_value_node, context))
		if res.should_return(): return res

		if node.step_value_node:
			step_value = res.register(self.visit(node.step_value_node, context))
			if res.should_return(): return res
		else:
			step_value = Number(1)

		i = start_value.value

		if step_value.value >= 0:
			condition = lambda: i < end_value.value
		else:
			condition = lambda: i > end_value.value
		
		while condition():
			context.symbol_table.set(node.var_name_tok.value, Number(i))
			i += step_value.value

			value = res.register(self.visit(node.body_node, context))
			if res.should_return() and res.loop_should_continue == False and res.loop_should_break == False: return res
			
			if res.loop_should_continue:
				continue
			
			if res.loop_should_break:
				break

			elements.append(value)

		return res.success(
			Number.null if node.should_return_null else
			List(elements).set_context(context).set_pos(node.pos_start, node.pos_end)
		)

	def visit_WhileNode(self, node, context):
		res = RTResult()
		elements = []

		while True:
			condition = res.register(self.visit(node.condition_node, context))
			if res.should_return(): return res

			if not condition.is_true():
				break

			value = res.register(self.visit(node.body_node, context))
			if res.should_return() and res.loop_should_continue == False and res.loop_should_break == False: return res

			if res.loop_should_continue:
				continue
			
			if res.loop_should_break:
				break

			elements.append(value)

		return res.success(
			Number.null if node.should_return_null else
			List(elements).set_context(context).set_pos(node.pos_start, node.pos_end)
		)

	def visit_FuncDefNode(self, node, context):
		res = RTResult()

		func_name = node.var_name_tok.value if node.var_name_tok else None
		body_node = node.body_node
		arg_names = [arg_name.value for arg_name in node.arg_name_toks]
		func_value = Function(func_name, body_node, arg_names, node.should_auto_return).set_context(context).set_pos(node.pos_start, node.pos_end)
		
		if node.var_name_tok:
			context.symbol_table.set(func_name, func_value)

		return res.success(func_value)

	def visit_CallNode(self, node, context):
		res = RTResult()
		args = []

		value_to_call = res.register(self.visit(node.node_to_call, context))
		if res.should_return(): return res
		value_to_call = value_to_call.copy().set_pos(node.pos_start, node.pos_end)

		for arg_node in node.arg_nodes:
			args.append(res.register(self.visit(arg_node, context)))
			if res.should_return(): return res

		return_value = res.register(value_to_call.execute(args))
		if res.should_return(): return res
		return_value = return_value.copy().set_pos(node.pos_start, node.pos_end).set_context(context)
		return res.success(return_value)

	def visit_ListNode(self, node, context):
		res = RTResult()
		elements = []

		for element_node in node.element_nodes:
			elements.append(res.register(self.visit(element_node, context)))
			if res.should_return(): return res

		return res.success(
			List(elements).set_context(context).set_pos(node.pos_start, node.pos_end)
		)
	
	def visit_ReturnNode(self, node, context):
		res = RTResult()

		if node.node_to_return:
			value = res.register(self.visit(node.node_to_return, context))
			if res.should_return(): return res
		else:
			value = Number.null
		
		return res.success_return(value)

	def visit_ContinueNode(self, node, context):
		return RTResult().success_continue()

	def visit_BreakNode(self, node, context):
		return RTResult().success_break()

class Function(BaseFunction):
  def __init__(self, name, body_node, arg_names, should_auto_return):
    super().__init__(name)
    self.body_node = body_node
    self.arg_names = arg_names
    self.should_auto_return = should_auto_return

  def execute(self, args):
    res = RTResult()
    interpreter = Interpreter()
    exec_ctx = self.generate_new_context()

    res.register(self.check_and_populate_args(self.arg_names, args, exec_ctx))
    if res.should_return(): return res

    value = res.register(interpreter.visit(self.body_node, exec_ctx))
    if res.should_return() and res.func_return_value == None: return res

    ret_value = (value if self.should_auto_return else None) or res.func_return_value or Number.null
    return res.success(ret_value)

  def copy(self):
    copy = Function(self.name, self.body_node, self.arg_names, self.should_auto_return)
    copy.set_context(self.context)
    copy.set_pos(self.pos_start, self.pos_end)
    return copy

  def __repr__(self):
    return f"<funksioni {self.name}>"



class BuiltInFunction(BaseFunction):
  def __init__(self, name):
    super().__init__(name)

  def execute(self, args):
    res = RTResult()
    exec_ctx = self.generate_new_context()

    method_name = f'execute_{self.name}'
    method = getattr(self, method_name, self.no_visit_method)

    res.register(self.check_and_populate_args(method.arg_names, args, exec_ctx))
    if res.should_return(): return res

    return_value = res.register(method(exec_ctx))
    if res.should_return(): return res
    return res.success(return_value)
  
  def no_visit_method(self, node, context):
    raise Exception(f'No execute_{self.name} method defined')

  def copy(self):
    copy = BuiltInFunction(self.name)
    copy.set_context(self.context)
    copy.set_pos(self.pos_start, self.pos_end)
    return copy

  def __repr__(self):
    return f"<funksioni i integruar {self.name}>"

  #####################################

  def execute_printo(self, exec_ctx):
    print(str(exec_ctx.symbol_table.get('value')))
    return RTResult().success(Number.null)
  execute_printo.arg_names = ['value']
  
  def execute_shtyp(self, exec_ctx):
    text = input()
    return RTResult().success(String(text))
  execute_shtyp.arg_names = []

  def execute_shtyp_num(self, exec_ctx):
    while True:
      text = input()
      try:
        number = int(text)
        break
      except ValueError:
        print(f"'{text}' duhet te jete nje numer.")
    return RTResult().success(Number(number))
  execute_shtyp_num.arg_names = []

#   def execute_clear(self, exec_ctx):
#     os.system('cls' if os.name == 'nt' else 'cls') 
#     return RTResult().success(Number.null)
#   execute_clear.arg_names = []

  def execute_eshte_num(self, exec_ctx):
    is_number = isinstance(exec_ctx.symbol_table.get("value"), Number)
    return RTResult().success(Number.true if is_number else Number.false)
  execute_eshte_num.arg_names = ["value"]

  def execute_eshte_tekst(self, exec_ctx):
    is_number = isinstance(exec_ctx.symbol_table.get("value"), String)
    return RTResult().success(Number.true if is_number else Number.false)
  execute_eshte_tekst.arg_names = ["value"]

  def execute_eshte_list(self, exec_ctx):
    is_number = isinstance(exec_ctx.symbol_table.get("value"), List)
    return RTResult().success(Number.true if is_number else Number.false)
  execute_eshte_list.arg_names = ["value"]

  def execute_eshte_fun(self, exec_ctx):
    is_number = isinstance(exec_ctx.symbol_table.get("value"), BaseFunction)
    return RTResult().success(Number.true if is_number else Number.false)
  execute_eshte_fun.arg_names = ["value"]

  def execute_shto(self, exec_ctx):
    list_ = exec_ctx.symbol_table.get("list")
    value = exec_ctx.symbol_table.get("value")

    if not isinstance(list_, List):
      return RTResult().failure(RTError(
        self.pos_start, self.pos_end,
        "Argumenti i pare duhet te jete lista",
        exec_ctx
      ))

    list_.elements.append(value)
    return RTResult().success(Number.null)
  execute_shto.arg_names = ["list", "value"]

  def execute_fshij(self, exec_ctx):
    list_ = exec_ctx.symbol_table.get("list")
    index = exec_ctx.symbol_table.get("index")

    if not isinstance(list_, List):
      return RTResult().failure(RTError(
        self.pos_start, self.pos_end,
        "Argumenti i pare duhet te jete lista",
        exec_ctx
      ))

    if not isinstance(index, Number):
      return RTResult().failure(RTError(
        self.pos_start, self.pos_end,
        "Argumenti i dyte duhet te jete numri",
        exec_ctx
      ))

    try:
      element = list_.elements.pop(index.value)
    except:
      return RTResult().failure(RTError(
        self.pos_start, self.pos_end,
        'Elementi në kete indeks nuk mund te hiqej nga lista sepse indeksi eshte jashte kufijve',
        exec_ctx
      ))
    return RTResult().success(element)
  execute_fshij.arg_names = ["list", "index"]

  def execute_zgjat(self, exec_ctx):
    listA = exec_ctx.symbol_table.get("listA")
    listB = exec_ctx.symbol_table.get("listB")

    if not isinstance(listA, List):
      return RTResult().failure(RTError(
        self.pos_start, self.pos_end,
        "Argumenti i pare duhet te jete list",
        exec_ctx
      ))

    if not isinstance(listB, List):
      return RTResult().failure(RTError(
        self.pos_start, self.pos_end,
        "Argumenti i dyte duhet te jete lista",
        exec_ctx
      ))

    listA.elements.extend(listB.elements)
    return RTResult().success(Number.null)
  execute_zgjat.arg_names = ["listA", "listB"]

  def execute_sa(self, exec_ctx):
    list_ = exec_ctx.symbol_table.get("list")

    if not isinstance(list_, List):
      return RTResult().failure(RTError(
        self.pos_start, self.pos_end,
        "Argumenti duhet te jete list",
        exec_ctx
      ))

    return RTResult().success(Number(len(list_.elements)))
  execute_sa.arg_names = ["list"]

  def execute_zbato(self, exec_ctx):
    fn = exec_ctx.symbol_table.get("fn")

    if not isinstance(fn, String):
      return RTResult().failure(RTError(
        self.pos_start, self.pos_end,
        "Argumenti duhet te jete tekst",
        exec_ctx
      ))

    fn = fn.value

    try:
      with open(fn, "r") as f:
        script = f.read()
    except Exception as e:
      return RTResult().failure(RTError(
        self.pos_start, self.pos_end,
        f"Ngarkimi i skriptit deshtoi \"{fn}\"\n" + str(e),
        exec_ctx
      ))

    _, error = run(fn, script)
    
    if error:
      return RTResult().failure(RTError(
        self.pos_start, self.pos_end,
        f"Deshtoi ne ekzekutimin e skriptit \"{fn}\"\n" +
        error.as_string(),
        exec_ctx
      ))

    return RTResult().success(Number.null)
  execute_zbato.arg_names = ["fn"]

BuiltInFunction.printo      = BuiltInFunction("printo")
BuiltInFunction.shtyp       = BuiltInFunction("shtyp")
BuiltInFunction.shtyp_num   = BuiltInFunction("shtyp_num")
# BuiltInFunction.clear       = BuiltInFunction("clear")
BuiltInFunction.eshte_num   = BuiltInFunction("eshte_num")
BuiltInFunction.eshte_tekst   = BuiltInFunction("eshte_tekst")
BuiltInFunction.eshte_list     = BuiltInFunction("eshte_list")
BuiltInFunction.eshte_fun = BuiltInFunction("eshte_fun")
BuiltInFunction.shto      = BuiltInFunction("shto")
#TODO add function to remove and first and last items of array
BuiltInFunction.fshij  = BuiltInFunction("fshij")
BuiltInFunction.zgjat  = BuiltInFunction("zgjat")
BuiltInFunction.sa     = BuiltInFunction("sa")
BuiltInFunction.zbato					= BuiltInFunction("zbato")

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
global_symbol_table.set("sa", BuiltInFunction.sa)
global_symbol_table.set("zbato", BuiltInFunction.zbato)

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