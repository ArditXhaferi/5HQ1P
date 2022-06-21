import const.tokens
from nodes.binOpNode import BinOpNode
from nodes.numberNode import NumberNode
from nodes.unaryOpNode import UnaryOpNode
from core.illegalCharController import InvalidSyntaxError
from nodes.varAcessNode import VarAccessNode
from nodes.varAssignNode import VarAssignNode

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

	def atom(self):
		res = ParseResult()
		tok = self.current_tok

		if tok.type in (const.tokens.SS_INT, const.tokens.SS_FLOAT):
			res.register_advancement()
			self.advance()
			return res.success(NumberNode(tok))

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

		return res.failure(InvalidSyntaxError(
			tok.pos_start, tok.pos_end,
			"Pritet int, float, identifier, '+', '-' ose '('"
		))

	def power(self):
		return self.bin_op(self.atom, (const.tokens.SS_POW, ), self.factor)

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

		node = res.register(self.bin_op(self.term, (const.tokens.SS_PLUS, const.tokens.SS_MINUS)))

		if res.error:
			return res.failure(InvalidSyntaxError(
				self.current_tok.pos_start, self.current_tok.pos_end,
				"Pritet '"+const.tokens.SS_VAR+"', Num, Dec, Identifikuesi, '+', '-' ose '('"
			))

		return res.success(node)

	#Handle binary operation
	def bin_op(self, func_a, ops, func_b=None):
		if func_b == None:
			func_b = func_a
		
		res = ParseResult()
		left = res.register(func_a())
		if res.error: return res

		while self.current_tok.type in ops:
			op_tok = self.current_tok
			res.register_advancement()
			self.advance()
			right = res.register(func_b())
			if res.error: return res
			left = BinOpNode(left, op_tok, right)

		return res.success(left)