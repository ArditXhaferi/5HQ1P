from core.numberController import Number
from core.RunTimeResultController import RTResult
from core.illegalCharController import RTError
import const.tokens

class Interpreter:
	def visit(self, node, context):
		method_name = f'visit_{type(node).__name__}'
		method = getattr(self, method_name, self.no_visit_method)
		return method(node, context)

	def no_visit_method(self, node, context):
		raise Exception(f'No visit_{type(node).__name__} method defined')

	###################################

	def visit_NumberNode(self, node, context):
		return RTResult().success(
			Number(node.tok.value).set_context(context).set_pos(node.pos_start, node.pos_end)
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

		value = value.copy().set_pos(node.pos_start, node.pos_end)
		return res.success(value)

	def visit_VarAssignNode(self, node, context):
		res = RTResult()
		var_name = node.var_name_tok.value
		value = res.register(self.visit(node.value_node, context))
		if res.error: return res

		context.symbol_table.set(var_name, value)
		return res.success(value)

	def visit_BinOpNode(self, node, context):
		res = RTResult()
		left = res.register(self.visit(node.left_node, context))
		if res.error: return res
		right = res.register(self.visit(node.right_node, context))
		if res.error: return res

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
		if res.error: return res

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

		for condition, expr in node.cases:
			condition_value = res.register(self.visit(condition, context))
			if res.error: return res

			if condition_value.is_true():
				expr_value = res.register(self.visit(expr, context))
				if res.error: return res
				return res.success(expr_value)

		if node.else_case:
			else_value = res.register(self.visit(node.else_case, context))
			if res.error: return res
			return res.success(else_value)

		return res.success(None)

	def visit_ForNode(self, node, context):
		res = RTResult()

		start_value = res.register(self.visit(node.start_value_node, context))
		if res.error: return res

		end_value = res.register(self.visit(node.end_value_node, context))
		if res.error: return res

		if node.step_value_node:
			step_value = res.register(self.visit(node.step_value_node, context))
			if res.error: return res
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

			res.register(self.visit(node.body_node, context))
			if res.error: return res

		return res.success(None)

	def visit_WhileNode(self, node, context):
		res = RTResult()

		while True:
			condition = res.register(self.visit(node.condition_node, context))
			if res.error: return res

			if not condition.is_true(): break

			res.register(self.visit(node.body_node, context))
			if res.error: return res

		return res.success(None)