from core.valueController import Value
from core.contextController import Context
from core.symbolTable import SymbolTable
from core.illegalCharController import RTError
from core.RunTimeResultController import RTResult

class BaseFunction(Value):
  def __init__(self, name):
    super().__init__()
    self.name = name or "<panjohur>"

  def generate_new_context(self):
    new_context = Context(self.name, self.context, self.pos_start)
    new_context.symbol_table = SymbolTable(new_context.parent.symbol_table)
    return new_context

  def check_args(self, arg_names, args):
    res = RTResult()

    if len(args) > len(arg_names):
      return res.failure(RTError(
        self.pos_start, self.pos_end,
        f"shum parametra bre n'{self}",
        self.context
      ))
    
    if len(args) < len(arg_names):
      return res.failure(RTError(
        self.pos_start, self.pos_end,
        f"ku i ki {len(arg_names) - len(args)} parametra n'{self}'",
        self.context
      ))

    return res.success(None)

  def populate_args(self, arg_names, args, exec_ctx):
    for i in range(len(args)):
      arg_name = arg_names[i]
      arg_value = args[i]
      arg_value.set_context(exec_ctx)
      exec_ctx.symbol_table.set(arg_name, arg_value)

  def check_and_populate_args(self, arg_names, args, exec_ctx):
    res = RTResult()
    res.register(self.check_args(arg_names, args))
    if res.error: return res
    self.populate_args(arg_names, args, exec_ctx)
    return res.success(None)