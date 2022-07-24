import const.tokens
from nodes.binOpNode import BinOpNode
from nodes.numberNode import NumberNode
from nodes.unaryOpNode import UnaryOpNode
from core.illegalCharController import InvalidSyntaxError
from nodes.varAcessNode import VarAccessNode
from nodes.varAssignNode import VarAssignNode
from nodes.ifNode import IfNode
from nodes.forNode import ForNode
from nodes.whileNode import WhileNode
from nodes.funcDefNode import FuncDefNode
from nodes.callNode import CallNode
from nodes.stringNode import StringNode
from nodes.listNode import ListNode

class ParseResult:
	def __init__(self):
		self.error = None
		self.node = None
		self.advance_count = 0

	def register_advancement(self):
		self.advance_count += 1

	def register(self, res):
		self.advance_count += res.advance_count
		if res.error: self.error = res.error
		return res.node

	def success(self, node):
		self.node = node
		return self

	def failure(self, error):
		if not self.error or self.advance_count == 0:
			self.error = error
		return self


class Parser:
	def __init__(self, tokens):
		self.tokens = tokens
		self.tok_idx = -1
		self.advance()

	def advance(self, ):
		self.tok_idx += 1
		if self.tok_idx < len(self.tokens):
			self.current_tok = self.tokens[self.tok_idx]
		return self.current_tok

	def parse(self):
		res = self.expr()
		if not res.error and self.current_tok.type != const.tokens.SS_EOF:
			return res.failure(InvalidSyntaxError(
				self.current_tok.pos_start, self.current_tok.pos_end,
				"Pritet '+', '-', '*', '/' ose '^'"
			))
		return res

	def list_expr(self):
		res = ParseResult()
		element_nodes = []
		pos_start = self.current_tok.pos_start.copy()

		if self.current_tok.type != const.tokens.SS_LSQUARE:
			return res.failure(InvalidSyntaxError(
				self.current_tok.pos_start, self.current_tok.pos_end,
				f"Pritet '['"
			))

		res.register_advancement()
		self.advance()

		if self.current_tok.type == const.tokens.SS_RSQUARE:
			res.register_advancement()
			self.advance()
		else:
			element_nodes.append(res.register(self.expr()))
			if res.error:
				return res.failure(InvalidSyntaxError(
					self.current_tok.pos_start, self.current_tok.pos_end,
					f"Pritet ']', '{const.tokens.SS_VAR}', '{const.tokens.SS_IF}', '{const.tokens.SS_FOR}', '{const.tokens.SS_WHILE}', '{const.tokens.SS_FUN}', {const.tokens.SSS_INT}, {const.tokens.SSS_FLOAT}, identifier, '+', '-', '(', '[' ose '{const.tokens.SS_NOT}'"
				))

			while self.current_tok.type == const.tokens.SS_COMMA:
				res.register_advancement()
				self.advance()

				element_nodes.append(res.register(self.expr()))
				if res.error: return res
			
			if self.current_tok.type != const.tokens.SS_RSQUARE:
				return res.failure(InvalidSyntaxError(
					self.current_tok.pos_start, self.current_tok.pos_end,
					f"Pritet ',' or ']'"
				))

			res.register_advancement()
			self.advance()

		return res.success(ListNode(
			element_nodes,
			pos_start,
			self.current_tok.pos_end.copy()
		))

	#Expressions
	def if_expr(self):
		res = ParseResult()
		cases = []
		else_case = None

		if not self.current_tok.matches(const.tokens.SS_KEYWORD, const.tokens.SS_IF):
			return res.failure(InvalidSyntaxError(
				self.current_tok.pos_start, self.current_tok.pos_end,
				f"Pritet '{const.tokens.SS_IF}'"
			))

		res.register_advancement()
		self.advance()

		condition = res.register(self.expr())
		if res.error: return res

		if not self.current_tok.matches(const.tokens.SS_KEYWORD, const.tokens.SS_THEN):
			return res.failure(InvalidSyntaxError(
				self.current_tok.pos_start, self.current_tok.pos_end,
				f"Pritet '{const.tokens.SS_THEN}'"
			))

		res.register_advancement()
		self.advance()

		expr = res.register(self.expr())
		if res.error: return res
		cases.append((condition, expr))

		while self.current_tok.matches(const.tokens.SS_KEYWORD, const.tokens.SS_ELIF):
			res.register_advancement()
			self.advance()

			condition = res.register(self.expr())
			if res.error: return res

			if not self.current_tok.matches(const.tokens.SS_KEYWORD, const.tokens.SS_THEN):
				return res.failure(InvalidSyntaxError(
					self.current_tok.pos_start, self.current_tok.pos_end,
					f"Pritet '{const.tokens.SS_THEN}'"
				))

			res.register_advancement()
			self.advance()

			expr = res.register(self.expr())
			if res.error: return res
			cases.append((condition, expr))

		if self.current_tok.matches(const.tokens.SS_KEYWORD, const.tokens.SS_ELSE):
			res.register_advancement()
			self.advance()

			else_case = res.register(self.expr())
			if res.error: return res

		return res.success(IfNode(cases, else_case))
		
	def for_expr(self):
		res = ParseResult()

		if not self.current_tok.matches(const.tokens.SS_KEYWORD, const.tokens.SS_FOR):
			return res.failure(InvalidSyntaxError(
				self.current_tok.pos_start, self.current_tok.pos_end,
				f"Pritet '{const.tokens.SS_FOR}'"
			))

		res.register_advancement()
		self.advance()

		if self.current_tok.type != const.tokens.SS_IDENTIFIER:
			return res.failure(InvalidSyntaxError(
				self.current_tok.pos_start, self.current_tok.pos_end,
				f"Pritet identifier"
			))

		var_name = self.current_tok
		res.register_advancement()
		self.advance()

		if self.current_tok.type != const.tokens.SS_ASSIGNOR:
			return res.failure(InvalidSyntaxError(
				self.current_tok.pos_start, self.current_tok.pos_end,
				f"Pritet '='"
			))
		
		res.register_advancement()
		self.advance()

		start_value = res.register(self.expr())
		if res.error: return res

		if not self.current_tok.matches(const.tokens.SS_KEYWORD, const.tokens.SS_TO):
			return res.failure(InvalidSyntaxError(
				self.current_tok.pos_start, self.current_tok.pos_end,
				f"Pritet '{const.tokens.SS_TO}'"
			))
		
		res.register_advancement()
		self.advance()

		end_value = res.register(self.expr())
		if res.error: return res

		if self.current_tok.matches(const.tokens.SS_KEYWORD, const.tokens.SS_STEP):
			res.register_advancement()
			self.advance()

			step_value = res.register(self.expr())
			if res.error: return res
		else:
			step_value = None

		if not self.current_tok.matches(const.tokens.SS_KEYWORD, const.tokens.SS_THEN):
			return res.failure(InvalidSyntaxError(
				self.current_tok.pos_start, self.current_tok.pos_end,
				f"Pritet '{const.tokens.SS_THEN}'"
			))

		res.register_advancement()
		self.advance()

		body = res.register(self.expr())
		if res.error: return res

		return res.success(ForNode(var_name, start_value, end_value, step_value, body))

	def while_expr(self):
		res = ParseResult()

		if not self.current_tok.matches(const.tokens.SS_KEYWORD, const.tokens.SS_WHILE):
			return res.failure(InvalidSyntaxError(
				self.current_tok.pos_start, self.current_tok.pos_end,
				f"Pritet '{const.tokens.SS_WHILE}'"
			))

		res.register_advancement()
		self.advance()

		condition = res.register(self.expr())
		if res.error: return res

		if not self.current_tok.matches(const.tokens.SS_KEYWORD, const.tokens.SS_THEN):
			return res.failure(InvalidSyntaxError(
				self.current_tok.pos_start, self.current_tok.pos_end,
				f"Pritet '{const.tokens.SS_THEN}'"
			))

		res.register_advancement()
		self.advance()

		body = res.register(self.expr())
		if res.error: return res

		return res.success(WhileNode(condition, body))

	def func_def(self):
		res = ParseResult()

		if not self.current_tok.matches(const.tokens.SS_KEYWORD, const.tokens.SS_FUN):
			return res.failure(InvalidSyntaxError(
				self.current_tok.pos_start, self.current_tok.pos_end,
				f"Pritet '{const.tokens.SS_FUN}'"
			))

		res.register_advancement()
		self.advance()

		if self.current_tok.type == const.tokens.SS_IDENTIFIER:
			var_name_tok = self.current_tok
			res.register_advancement()
			self.advance()
			if self.current_tok.type != const.tokens.SS_LPAREN:
				return res.failure(InvalidSyntaxError(
					self.current_tok.pos_start, self.current_tok.pos_end,
					f"Pritet '('"
				))
		else:
			var_name_tok = None
			if self.current_tok.type != const.tokens.SS_LPAREN:
				return res.failure(InvalidSyntaxError(
					self.current_tok.pos_start, self.current_tok.pos_end,
					f"Pritet identifier ose '('"
				))
		
		res.register_advancement()
		self.advance()
		arg_name_toks = []

		if self.current_tok.type == const.tokens.SS_IDENTIFIER:
			arg_name_toks.append(self.current_tok)
			res.register_advancement()
			self.advance()
			
			while self.current_tok.type == const.tokens.SS_COMMA:
				res.register_advancement()
				self.advance()

				if self.current_tok.type != const.tokens.SS_IDENTIFIER:
					return res.failure(InvalidSyntaxError(
						self.current_tok.pos_start, self.current_tok.pos_end,
						f"Pritet identifier"
					))

				arg_name_toks.append(self.current_tok)
				res.register_advancement()
				self.advance()
			
			if self.current_tok.type != const.tokens.SS_RPAREN:
				return res.failure(InvalidSyntaxError(
					self.current_tok.pos_start, self.current_tok.pos_end,
					f"Pritet ',' ose ')'"
				))
		else:
			if self.current_tok.type != const.tokens.SS_RPAREN:
				return res.failure(InvalidSyntaxError(
					self.current_tok.pos_start, self.current_tok.pos_end,
					f"Pritet identifier ose ')'"
				))

		res.register_advancement()
		self.advance()

		if self.current_tok.type != const.tokens.SS_ARROW:
			return res.failure(InvalidSyntaxError(
				self.current_tok.pos_start, self.current_tok.pos_end,
				f"Pritet '->'"
			))

		res.register_advancement()
		self.advance()
		node_to_return = res.register(self.expr())
		if res.error: return res

		return res.success(FuncDefNode(
			var_name_tok,
			arg_name_toks,
			node_to_return
		))

	def call(self):
		res = ParseResult()
		atom = res.register(self.atom())
		if res.error: return res

		if self.current_tok.type == const.tokens.SS_LPAREN:
			res.register_advancement()
			self.advance()
			arg_nodes = []

			if self.current_tok.type == const.tokens.SS_RPAREN:
				res.register_advancement()
				self.advance()
			else:
				arg_nodes.append(res.register(self.expr()))
				if res.error:
					return res.failure(InvalidSyntaxError(
						self.current_tok.pos_start, self.current_tok.pos_end,
						f"Pritet ')', '{const.tokens.SS_VAR}', '{const.tokens.SS_IF}', '{const.tokens.SS_FOR}', '{const.tokens.SS_WHILE}', '{const.tokens.SS_FUN}', {const.tokens.SSS_INT}, {const.tokens.SSS_FLOAT}, identifier, '+', '-', '(' ose '{const.tokens.SS_NOT}'"
					))

				while self.current_tok.type == const.tokens.SS_COMMA:
					res.register_advancement()
					self.advance()

					arg_nodes.append(res.register(self.expr()))
					if res.error: return res

				if self.current_tok.type != const.tokens.SS_RPAREN:
					return res.failure(InvalidSyntaxError(
						self.current_tok.pos_start, self.current_tok.pos_end,
						f"Pritet ',' ose ')'"
					))

				res.register_advancement()
				self.advance()
			return res.success(CallNode(atom, arg_nodes))
		return res.success(atom)

	def atom(self):
		res = ParseResult()
		tok = self.current_tok

		if tok.type in (const.tokens.SS_INT, const.tokens.SS_FLOAT):
			res.register_advancement()
			self.advance()
			return res.success(NumberNode(tok))

		elif tok.type == const.tokens.SS_STRING:
			res.register_advancement()
			self.advance()
			return res.success(StringNode(tok))

		elif tok.type == const.tokens.SS_IDENTIFIER:
			res.register_advancement()
			self.advance()
			return res.success(VarAccessNode(tok))

		elif tok.type == const.tokens.SS_LPAREN:
			res.register_advancement()
			self.advance()
			expr = res.register(self.expr())
			if res.error: return res
			if self.current_tok.type == const.tokens.SS_RPAREN:
				res.register_advancement()
				self.advance()
				return res.success(expr)
			else:
				return res.failure(InvalidSyntaxError(
					self.current_tok.pos_start, self.current_tok.pos_end,
					"Pritet ')'"
				))

		elif tok.type == const.tokens.SS_LSQUARE:
			list_expr = res.register(self.list_expr())
			if res.error: return res
			return res.success(list_expr)

		elif tok.matches(const.tokens.SS_KEYWORD, const.tokens.SS_IF):
			if_expr = res.register(self.if_expr())
			if res.error: return res
			return res.success(if_expr)
		
		elif tok.matches(const.tokens.SS_KEYWORD, const.tokens.SS_FOR):
			for_expr = res.register(self.for_expr())
			if res.error: return res
			return res.success(for_expr)

		elif tok.matches(const.tokens.SS_KEYWORD, const.tokens.SS_WHILE):
			while_expr = res.register(self.while_expr())
			if res.error: return res
			return res.success(while_expr)

		elif tok.matches(const.tokens.SS_KEYWORD, const.tokens.SS_FUN):
			func_def = res.register(self.func_def())
			if res.error: return res
			return res.success(func_def)

		return res.failure(InvalidSyntaxError(
			tok.pos_start, tok.pos_end,
			f"Pritet int, float, identifier, '+', '-' ose '(', '{const.tokens.SS_IF}', '{const.tokens.SS_FOR}', '{const.tokens.SS_WHILE}', '{const.tokens.SS_FUN}'"
		))

	def power(self):
		return self.bin_op(self.call, (const.tokens.SS_POW, ), self.factor)

	def factor(self):
		res = ParseResult()
		tok = self.current_tok

		if tok.type in (const.tokens.SS_PLUS, const.tokens.SS_MINUS):
			res.register_advancement()
			self.advance()
			factor = res.register(self.factor())
			if res.error: return res
			return res.success(UnaryOpNode(tok, factor))

		return self.power()

	def term(self):
		return self.bin_op(self.factor, (const.tokens.SS_MUL, const.tokens.SS_DIV))

	def arith_expr(self):
		return self.bin_op(self.term, (const.tokens.SS_PLUS, const.tokens.SS_MINUS))

	def comp_expr(self):
		res = ParseResult()

		if self.current_tok.matches(const.tokens.SS_KEYWORD, const.tokens.SS_NOT):
			op_tok = self.current_tok
			res.register_advancement()
			self.advance()

			node = res.register(self.comp_expr())
			if res.error: return res
			return res.success(UnaryOpNode(op_tok, node))
		
		node = res.register(self.bin_op(self.arith_expr, (const.tokens.SS_EE, const.tokens.SS_NE, const.tokens.SS_LT, const.tokens.SS_GT, const.tokens.SS_LTE, const.tokens.SS_GTE)))
		
		if res.error:
			return res.failure(InvalidSyntaxError(
				self.current_tok.pos_start, self.current_tok.pos_end,
				"Pritet int, float, identifier, '+', '-', '(' or 'NOT'"
			))

		return res.success(node)

	def expr(self):
		res = ParseResult()

		if self.current_tok.matches(const.tokens.SS_KEYWORD, const.tokens.SS_VAR):
			res.register_advancement()
			self.advance()

			if self.current_tok.type != const.tokens.SS_IDENTIFIER:
				return res.failure(InvalidSyntaxError(
					self.current_tok.pos_start, self.current_tok.pos_end,
					"Pritet identifikuesi"
				))

			var_name = self.current_tok
			res.register_advancement()
			self.advance()

			if self.current_tok.type != const.tokens.SS_ASSIGNOR:
				return res.failure(InvalidSyntaxError(
					self.current_tok.pos_start, self.current_tok.pos_end,
					"Pritet përcaktuesi: '='"
				))

			res.register_advancement()
			self.advance()
			expr = res.register(self.expr())
			if res.error: return res
			return res.success(VarAssignNode(var_name, expr))

		node = res.register(self.bin_op(self.comp_expr, ((const.tokens.SS_KEYWORD, const.tokens.SS_AND), (const.tokens.SS_KEYWORD, const.tokens.SS_OR))))

		if res.error:
			return res.failure(InvalidSyntaxError(
				self.current_tok.pos_start, self.current_tok.pos_end,
				f"Pritet '{const.tokens.SS_VAR}', Num, Dec, Identifikuesi, '+', '-' ose '('"
			))

		return res.success(node)

	#Handle binary operation
	def bin_op(self, func_a, ops, func_b=None):
		if func_b == None:
			func_b = func_a
		
		res = ParseResult()
		left = res.register(func_a())
		if res.error: return res

		while self.current_tok.type in ops or (self.current_tok.type, self.current_tok.value) in ops:
			op_tok = self.current_tok
			res.register_advancement()
			self.advance()
			right = res.register(func_b())
			if res.error: return res
			left = BinOpNode(left, op_tok, right)

		return res.success(left)