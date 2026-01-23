import os
import random
import time

from values import *
from utils.context import Context, SymbolTable
from utils.results import RunTimeResult
from utils.errors import RunTimeError
from lexer.tokens import *
from parser.nodes import *
from lexer.lexer import Lexer
from parser.parser import Parser

from robot.robot import Robot

class BaseFunction(Value): 
    def __init__(self, name):
        super().__init__()
        self.name = name or "<anonymous>" #TODO: prob change this to no anonymous

    def generate_new_context(self): 
        new_context = Context(self.name, self.context, self.pos_start)
        new_context.symbol_table = SymbolTable(new_context.parent.symbol_table)
        return new_context
    
    def check_args(self, arg_names, args):
        RTresult = RunTimeResult()

        if len(args) > len(arg_names): 
            return RTresult.failure(RunTimeError(
                self.pos_start, self.pos_end, 
                f"{len(args) - len(arg_names)} too many arguments passed into '{self.name}'",
                self.context
            ))
        elif len(args) < len(arg_names): 
            return RTresult.failure(RunTimeError(
                self.pos_start, self.pos_end, 
                f"{len(arg_names) - len(args)} too few arguments passed into '{self.name}'",
                self.context
            ))
        
        return RTresult.success(None)
    
    def populate_args(self, arg_names, args, exec_context): 
        """ Puts all the arguments into a symbol table """
        for i in range(len(args)): 
            arg_name = arg_names[i]
            arg_value: Value = args[i]
            arg_value.set_context(exec_context)
            exec_context.symbol_table.set(arg_name, arg_value)

    def check_and_populate_args(self, arg_names, args, exec_context):
        RTresult = RunTimeResult()
        RTresult.register(self.check_args(arg_names, args))
        if RTresult.should_return(): return RTresult
        self.populate_args(arg_names, args, exec_context)
        return RTresult.success(None)

class Function(BaseFunction):
    def __init__(self, name, body_node, arg_names, should_auto_return):
        super().__init__(name)
        self.arg_names = arg_names
        self.body_node = body_node
        self.should_auto_return = should_auto_return

    def execute(self, args): 
        RTresult = RunTimeResult()
        interpreter = Interpreter()
        exec_context = self.generate_new_context()

        RTresult.register(self.check_and_populate_args(self.arg_names, args, exec_context))
        if RTresult.should_return(): return RTresult

        value = RTresult.register(interpreter.visit(self.body_node, exec_context))
        if RTresult.should_return() and RTresult.func_return_value == None: return RTresult

        return_value = (value if self.should_auto_return else None) or RTresult.func_return_value or Number.null
        return RTresult.success(return_value)
    
    def copy(self): 
        copy = Function(self.name, self.body_node, self.arg_names, self.should_auto_return)
        copy.set_context(self.context)
        copy.set_pos(self.pos_start, self.pos_end)
        return copy
    
    def __repr__(self):
        return f'<function {self.name}>'

class BuiltInFunction(BaseFunction): 
    def __init__(self, name):
        super().__init__(name)

    def execute(self, args): 
        RTresult = RunTimeResult()
        exec_context = self.generate_new_context()

        method_name = f'execute_{self.name}'
        method = getattr(self, method_name, self.no_visit_method)

        RTresult.register(self.check_and_populate_args(method.arg_names, args, exec_context))
        if RTresult.should_return(): return RTresult

        return_value = RTresult.register(method(exec_context))
        if RTresult.should_return(): return RTresult
        return RTresult.success(return_value)

    def no_visit_method(self, node, context): 
        raise Exception(f'No execute_{self.name} method defined')
    
    def copy(self):
        copy = BuiltInFunction(self.name)
        copy.set_context(self.context)
        copy.set_pos(self.pos_start, self.pos_end)
        return copy
    
    def __repr__(self): 
        return f"<built-in function {self.name}>"
    
    ####### Execute method for all functions #######

    def execute_display(self, exec_context): 
        print(str(exec_context.symbol_table.get('value')))
        return RunTimeResult().success(Number.null)
    execute_display.arg_names = ["value"]

    def execute_input(self, exec_context): #TODO: Maybe make this fancier with string argument?
        text = input()
        txt = text.strip()
        if txt == "":
            return RunTimeResult().success(String(text))

        try:
            fval = float(txt)
            if fval.is_integer():
                return RunTimeResult().success(Number(int(fval)))
            return RunTimeResult().success(Number(fval))
        except Exception:
            return RunTimeResult().success(String(text))
    execute_input.arg_names = []

    def execute_random(self, exec_context):
        min_value = exec_context.symbol_table.get('min_value')
        max_value = exec_context.symbol_table.get('max_value')

        if not isinstance(min_value, Number): 
            return RunTimeResult().failure(RunTimeError(
                self.pos_start, self.pos_end, 
                "First argument must be an integer", 
                exec_context
            ))
        if not isinstance(max_value, Number): 
            return RunTimeResult().failure(RunTimeError(
                self.pos_start, self.pos_end, 
                "Second argument must be an integer", 
                exec_context
            ))

        random_value = random.randint(min_value.value, max_value.value)
        return RunTimeResult().success(Number(random_value))
    execute_random.arg_names = ['min_value', 'max_value']

    def execute_clear(self, exec_context): 
        os.system('cls' if os.name == 'nt' else 'clear')
        return RunTimeResult().success(Number.null)
    execute_clear.arg_names = []

    def execute_append(self, exec_context: Context): 
        list_ = exec_context.symbol_table.get('list')
        value_ = exec_context.symbol_table.get('value')

        if not isinstance(list_, List): 
            return RunTimeResult().failure(RunTimeError( #TODO: Change to syntax error maybe?
                self.pos_start, self.pos_end,
                "First argument must be a list", 
                exec_context
            ))
        
        list_.elements.append(value_) #TODO: Maybe add error check for value_ too?
        return RunTimeResult().success(Number.null)
    execute_append.arg_names = ['list', 'value']

    def execute_insert(self, exec_context):
        list_ = exec_context.symbol_table.get('list')
        index = exec_context.symbol_table.get('index')
        value = exec_context.symbol_table.get('value')

        if not isinstance(list_, List): 
            return RunTimeResult().failure(RunTimeError( #TODO: Change to syntax error maybe?
                self.pos_start, self.pos_end,
                "First argument must be a list", 
                exec_context
            ))
        
        if not isinstance(index, Number): 
            return RunTimeResult().failure(RunTimeError( #TODO: Change to syntax error maybe?
                self.pos_start, self.pos_end,
                "Second argument must be an integer", 
                exec_context
            ))
        
        list_.elements.insert(index.value, value)
        return RunTimeResult().success(Number.null)
    execute_insert.arg_names = ['list', 'index', 'value']

    def execute_remove(self, exec_context): 
        list_ = exec_context.symbol_table.get('list')
        index = exec_context.symbol_table.get('index')

        if not isinstance(list_, List): 
            return RunTimeResult().failure(RunTimeError( #TODO: Change to syntax error maybe?
                self.pos_start, self.pos_end,
                "First argument must be a list", 
                exec_context
            ))
        
        if not isinstance(index, Number): 
            return RunTimeResult().failure(RunTimeError( #TODO: Change to syntax error maybe?
                self.pos_start, self.pos_end,
                "Second argument must be an integer", 
                exec_context
            ))
        
        try: 
            element = list_.elements.pop(index.value)
        except: #TODO: Add type of error here
            return RunTimeResult().failure(RunTimeError(
                self.pos_start, self.pos_end, 
                "Element at this index couldn't be removed because index is out of bounds",
                exec_context
            ))
        return RunTimeResult().success(element)
    execute_remove.arg_names = ['list', 'index']

    def execute_length(self, exec_context: Context): 
        list_ = exec_context.symbol_table.get('list')

        if not isinstance(list_, List): 
            return RunTimeResult().failure(RunTimeError( #TODO: Change to syntax error maybe?
                self.pos_start, self.pos_end,
                "Argument must be a list", 
                exec_context
            ))
        
        return RunTimeResult().success(Number(len(list_.elements)))
    execute_length.arg_names = ['list']

    def execute_create_grid(self, exec_context: Context): #TODO: This sucks make it better
        RTresult = RunTimeResult()
        robot: Robot = global_symbol_table.get(100)

        RTresult.register(robot.create_grid())
        if RTresult.error: 
            RTresult.error.pos_start = self.pos_start
            RTresult.error.pos_end = self.pos_end
            return RTresult

        return RTresult.success(Number.null)
    execute_create_grid.arg_names = []

    def execute_move_forward(self, exec_context: Context): 
        RTresult = RunTimeResult()
        robot: Robot = global_symbol_table.get(100)

        time.sleep(2)
        RTresult.register(robot.move_forward())
        if RTresult.error: 
            RTresult.error.pos_start = self.pos_start
            RTresult.error.pos_end = self.pos_end
            return RTresult
        
        return RTresult.success(Number.null)
    execute_move_forward.arg_names = []

    def execute_rotate_left(self, exec_context: Context): 
        RTresult = RunTimeResult()
        robot: Robot = global_symbol_table.get(100)

        time.sleep(2)
        RTresult.register(robot.rotate_left())
        
        if RTresult.error: 
            RTresult.error.pos_start = self.pos_start
            RTresult.error.pos_end = self.pos_end
            return RTresult
        
        return RTresult.success(Number.null)
    execute_rotate_left.arg_names = []
    
    def execute_rotate_right(self, exec_context: Context): 
        RTresult = RunTimeResult()
        robot: Robot = global_symbol_table.get(100)

        time.sleep(2)
        RTresult.register(robot.rotate_right())
        
        if RTresult.error: 
            RTresult.error.pos_start = self.pos_start
            RTresult.error.pos_end = self.pos_end
            return RTresult
        
        return RTresult.success(Number.null)
    execute_rotate_right.arg_names = []

    def execute_can_move(self, exec_context: Context): 
        _direction = exec_context.symbol_table.get("direction")

        if isinstance(_direction, str): 
            _direction = String(_direction)
        
        RTresult = RunTimeResult()
        robot: Robot = global_symbol_table.get(100)

        if (not isinstance(_direction, String)
            or _direction.value not in ["FORWARD", "RIGHT", "LEFT", "BACKWARD"]): 
            return RunTimeResult().failure(RunTimeError(
                self.pos_start, self.pos_end,
                "Argument must be one of these valid directions: FORWARD, RIGHT, LEFT, BACKWARD", 
                exec_context
            ))
        
        value = RTresult.register(robot.can_move(_direction.value))
        if RTresult.error: return RTresult
        
        return RunTimeResult().success(value)
    execute_can_move.arg_names = ["direction"]

    def execute_run(self, exec_context): 
        fn = exec_context.symbol_table.get('fn')

        if not isinstance(fn, String): 
            return RunTimeResult().failure(RunTimeError(
                self.pos_start, self.pos_end, 
                "Argument must be a string", 
                exec_context
            ))
        
        fn = fn.value

        try: 
            with open(fn, 'r') as f:
                script = f.read()
        except Exception as e: 
            return RunTimeResult().failure(RunTimeError(
                self.pos_start, self.pos_end,
                f'Failed to load script {fn}\n' + str(e),
                exec_context
            ))
        
        _, error = run(fn, script)

        if error: 
            return RunTimeResult().failure(RunTimeError(
                self.pos_start, self.pos_end,
                f'Failed to finish executing script "{fn}"\n' + error.as_string(),
                exec_context
            ))
        
        return RunTimeResult().success(Number.null)
    execute_run.arg_names = ['fn']

BuiltInFunction.display     = BuiltInFunction("display")
BuiltInFunction.input       = BuiltInFunction("input")
BuiltInFunction.random      = BuiltInFunction("random")
BuiltInFunction.clear       = BuiltInFunction("clear")
BuiltInFunction.append      = BuiltInFunction("append")
BuiltInFunction.insert      = BuiltInFunction("insert")
BuiltInFunction.remove      = BuiltInFunction("remove")
BuiltInFunction.length      = BuiltInFunction("length")
BuiltInFunction.create_grid = BuiltInFunction("create_grid")
BuiltInFunction.move_forward= BuiltInFunction("move_forward")
BuiltInFunction.rotate_left   = BuiltInFunction("rotate_left")
BuiltInFunction.rotate_right  = BuiltInFunction("rotate_right")
BuiltInFunction.can_move    = BuiltInFunction("can_move")
BuiltInFunction.run         = BuiltInFunction("run")


# Interpreter
#TODO: Make static class, hard challenge
class Interpreter: 
    def visit(self, node, context: Context) -> RunTimeResult: 
        """ Process the node and visit all the child nodes """
        method_name = f'visit_{type(node).__name__}'
        method = getattr(self, method_name, self.no_visit_method)
        return method(node, context)
    
    def no_visit_method(self, node, context: Context): 
        raise Exception(f'No visit_{type(node).__name__}')
    
    def visit_NumberNode(self, node: NumberNode, context: Context):
        return RunTimeResult().success(
            Number(node.token.value).set_context(context).set_pos(node.token.pos_start, node.token.pos_end)
            )
    
    def visit_BooleanNode(self, node: BooleanNode, context: Context): 
        return RunTimeResult().success(
            Boolean(node.token.value).set_context(context).set_pos(node.token.pos_start, node.token.pos_end)
        )

    def visit_StringNode(self, node: StringNode, context: Context): 
        return RunTimeResult().success(
            String(node.token.value).set_context(context).set_pos(node.token.pos_start, node.token.pos_end)
        )
    
    def visit_VariableAccessNode(self, node: VariableAccessNode, context: Context): 
        RTresult = RunTimeResult()
        var_name = node.var_name_token.value
        value = context.symbol_table.get(var_name)

        if not value: 
            return RTresult.failure(RunTimeError(
                node.pos_start, node.pos_end, 
                f"'{var_name}' is not defined", 
                context
            ))
        
        value = value.copy().set_pos(node.pos_start, node.pos_end).set_context(context)
        return RTresult.success(value)
    
    def visit_VariableAssignNode(self, node: VariableAssignNode, context: Context):
        RTresult = RunTimeResult()
        var_name = node.var_name_token.value
        value = RTresult.register(self.visit(node.value_node, context))
        if RTresult.should_return(): return RTresult

        context.symbol_table.set(var_name, value)
        return RTresult.success(value)
    
    def visit_ListNode(self, node: ListNode, context: Context): 
        RTresult = RunTimeResult()
        elements = []

        for element_node in node.element_nodes: 
            elements.append(RTresult.register(self.visit(element_node, context)))
            if RTresult.should_return(): return RTresult

        return RTresult.success(
            List(elements).set_context(context).set_pos(node.pos_start, node.pos_end)
        )

    def visit_BinaryOperatorNode(self, node: BinaryOperatorNode, context: Context): 
        RTresult = RunTimeResult()
        left: Number = RTresult.register(self.visit(node.left_node, context))
        if RTresult.should_return(): return RTresult
        right: Number = RTresult.register(self.visit(node.right_node, context))
        if RTresult.should_return(): return RTresult
        
        if node.operator_token.type == TYPE_PLUS:
            result, error = left.added_to(right)
        elif node.operator_token.type == TYPE_MINUS:
            result, error = left.subract_by(right)
        elif node.operator_token.type == TYPE_MUL:
            result, error = left.multiply_by(right)
        elif node.operator_token.type == TYPE_DIV:
            result, error = left.divide_by(right)
        elif node.operator_token.matches(TYPE_KEYWORD, 'MOD'): 
            result, error = left.mod_by(right)
        elif node.operator_token.type == TYPE_POW:
            result, error = left.power_by(right)
        elif node.operator_token.type == TYPE_EE: 
            result, error = left.get_comparison_eq(right)
        elif node.operator_token.type == TYPE_NE:
            result, error = left.get_comparison_ne(right)
        elif node.operator_token.type == TYPE_LT:
            result, error = left.get_comparison_lt(right)
        elif node.operator_token.type == TYPE_GT:
            result, error = left.get_comparison_gt(right)
        elif node.operator_token.type == TYPE_LTE:
            result, error = left.get_comparison_lte(right)
        elif node.operator_token.type == TYPE_GTE:
            result, error = left.get_comparison_gte(right)
        elif node.operator_token.matches(TYPE_KEYWORD, 'AND'): 
            result, error = left.and_by(right)
        elif node.operator_token.matches(TYPE_KEYWORD, 'OR'): 
            result, error = left.or_by(right)

        if error: 
            return RTresult.failure(error)
        else: 
            return RTresult.success(result.set_pos(node.pos_start, node.pos_end))

    def visit_UnaryOperatorNode(self, node: UnaryOperatorNode, context: Context):
        RTresult = RunTimeResult()
        number = RTresult.register(self.visit(node.node, context))
        if RTresult.should_return(): return RTresult

        error = None

        if node.operator_token.type == TYPE_MINUS:
            number, error = number.multiply_by(Number(-1))
        elif node.operator_token.matches(TYPE_KEYWORD, 'NOT'): 
            number, error = number.notted()

        if error:
            return RTresult.failure(error)
        else: 
            return RTresult.success(number.set_pos(node.pos_start, node.pos_end))
        
    def visit_IfNode(self, node: IfNode, context: Context): 
        RTresult = RunTimeResult()

        for condition, expr, should_return_null in node.cases: 
            condition_value = RTresult.register(self.visit(condition, context))
            if RTresult.should_return(): return RTresult

            if condition_value.is_true(): 
                expr_value = RTresult.register(self.visit(expr, context))
                if RTresult.should_return(): return RTresult
                return RTresult.success(Number.null if should_return_null else expr_value)
        
        if node.else_case: 
            expr, should_return_null = node.else_case
            expr_value = RTresult.register(self.visit(expr, context))
            if RTresult.should_return(): return RTresult
            return RTresult.success(Number.null if should_return_null else expr_value)
        
        return RTresult.success(Number.null)
    
    def visit_ForNode(self, node: ForNode, context: Context): 
        RTresult = RunTimeResult()
        elements = []

        #TODO: Change this to accept list node also once made
        iterable = RTresult.register(self.visit(node.list_node, context))
        if RTresult.should_return(): return RTresult

        if not isinstance(iterable, List):
            return RTresult.failure(RunTimeError(
                node.list_node.pos_start, node.list_node.pos_end,
                "For loop can only iterate over a list",
                context
            ))

        for item in iterable.elements:
            context.symbol_table.set(node.var_name_token.value, item)

            value = RTresult.register(self.visit(node.body_node, context))
            if RTresult.should_return() and not RTresult.loop_should_continue and not RTresult.loop_should_break:
                return RTresult

            if RTresult.loop_should_continue:
                continue

            if RTresult.loop_should_break:
                break

            elements.append(value)

        return RTresult.success(
            Number.null if node.should_return_null else
            List(elements).set_context(context).set_pos(node.pos_start, node.pos_end)
        )
    
    def visit_WhileNode(self, node: WhileNode, context: Context): 
        RTresult = RunTimeResult()
        elements = []

        while True: 
            condition_value: Number = RTresult.register(self.visit(node.condition_node, context)) #TODO: Change this to boolean node once made
            if RTresult.should_return(): return RTresult

            if not condition_value.is_true(): 
                break

            value = RTresult.register(self.visit(node.body_node, context))
            if RTresult.should_return() and RTresult.loop_should_continue == False and RTresult.loop_should_break == False: return RTresult

            if RTresult.loop_should_continue: 
                continue

            if RTresult.loop_should_break: 
                break

            elements.append(value)

        return RTresult.success(
            Number.null if node.should_return_null else
            List(elements).set_context(context).set_pos(node.pos_start, node.pos_end)
        )
    
    def visit_RepeatUntilNode(self, node: RepeatUntilNode, context: Context):
        RTresult = RunTimeResult()
        elements = []

        while True: 
            condition_value: Number = RTresult.register(self.visit(node.condition_node, context)) #TODO: Change this to boolean node once made
            if RTresult.should_return(): return RTresult

            if condition_value.is_true():
                break

            value = RTresult.register(self.visit(node.body_node, context))
            if RTresult.should_return() and RTresult.loop_should_continue == False and RTresult.loop_should_break == False: return RTresult

            if RTresult.loop_should_continue: 
                continue

            if RTresult.loop_should_break: 
                break

            elements.append(value)

        return RTresult.success(
            Number.null if node.should_return_null else
            List(elements).set_context(context).set_pos(node.pos_start, node.pos_end)
        )
    
    def visit_RepeatNode(self, node: RepeatNode, context: Context):
        RTresult = RunTimeResult()
        elements = []

        if node.count_token:
            count: Token = node.count_token
            if RTresult.should_return(): return RTresult
        else: 
            count = RTresult.register(self.visit(node.count_node, context))
            if RTresult.should_return(): return RTresult

        for i in range(count.value): 
            value = RTresult.register(self.visit(node.body_node, context))
            if RTresult.should_return() and RTresult.loop_should_continue == False and RTresult.loop_should_break == False: return RTresult

            if RTresult.loop_should_continue: 
                continue

            if RTresult.loop_should_break: 
                break

            elements.append(value)

        return RTresult.success(
            Number.null if node.should_return_null else
            List(elements).set_context(context).set_pos(node.pos_start, node.pos_end)
        )

    def visit_FunctionDefinitionNode(self, node: FunctionDefinitionNode, context: Context):
        RTresult = RunTimeResult()

        func_name = node.var_name_token.value if node.var_name_token else None #TODO: Shouldn't need this if condition later
        body_node = node.body_node
        arg_names = [arg_name.value for arg_name in node.arg_name_tokens]
        func_value = Function(func_name, body_node, arg_names, node.should_auto_return).set_context(context).set_pos(node.pos_start, node.pos_end)
        
        if node.var_name_token: #TODO: could prob remove this later after requiring function name
            context.symbol_table.set(func_name, func_value)

        return RTresult.success(func_value)
    
    def visit_CallNode(self, node: CallNode, context: Context): 
        RTresult = RunTimeResult()
        args = []

        value_to_call: Value = RTresult.register(self.visit(node.node_to_call, context))
        if RTresult.should_return(): return RTresult
        value_to_call: Value = value_to_call.copy().set_pos(node.pos_start, node.pos_end)

        for arg_node in node.arg_nodes:
            args.append(RTresult.register(self.visit(arg_node, context)))
            if RTresult.should_return(): return RTresult

        return_value = RTresult.register(value_to_call.execute(args))
        if RTresult.should_return(): return RTresult
        return_value = return_value.copy().set_pos(node.pos_start, node.pos_end).set_context(context)
        return RTresult.success(return_value)
    
    def visit_ReturnNode(self, node: ReturnNode, context: Context): 
        RTresult = RunTimeResult()

        if node.node_to_return: 
            value = RTresult.register(self.visit(node.node_to_return, context))
            if RTresult.should_return(): return RTresult
        else: 
            value = Number.null

        return RTresult.success_return(value)
    
    def visit_ContinueNode(self, node: ContinueNode, context: Context): 
        return RunTimeResult().success_continue()
    
    def visit_BreakNode(self, node: BreakNode, context: Context): 
        return RunTimeResult().success_break()
    
global_symbol_table = SymbolTable()
global_symbol_table.set("NULL", Number.null)
global_symbol_table.set(100, Robot()) # 100 is just arbitrary. Not using a string so that way this isn't accessible to the user. 
global_symbol_table.set("DISPLAY", BuiltInFunction.display)
global_symbol_table.set("INPUT", BuiltInFunction.input)
global_symbol_table.set("RANDOM", BuiltInFunction.random)
global_symbol_table.set("CLEAR", BuiltInFunction.clear)
global_symbol_table.set("APPEND", BuiltInFunction.append)
global_symbol_table.set("INSERT", BuiltInFunction.insert)
global_symbol_table.set("REMOVE", BuiltInFunction.remove)
global_symbol_table.set("LENGTH", BuiltInFunction.length)
global_symbol_table.set("CREATE_GRID", BuiltInFunction.create_grid)
global_symbol_table.set("MOVE_FORWARD", BuiltInFunction.move_forward)
global_symbol_table.set("ROTATE_LEFT", BuiltInFunction.rotate_left)
global_symbol_table.set("ROATE_RIGHT", BuiltInFunction.rotate_right)
global_symbol_table.set("CAN_MOVE", BuiltInFunction.can_move)
global_symbol_table.set("FORWARD", String("FORWARD"))
global_symbol_table.set("RUN", BuiltInFunction.run)

def run(fn, text):
    lexer = Lexer(fn, text)
    tokens, error = lexer.make_tokens()
    if error: return None, error

    # Generate Tree
    parser = Parser(tokens)
    tree = parser.parse()
    if tree.error: return None, tree.error

    # Run program
    interpreter = Interpreter()
    context = Context("<program>")
    context.symbol_table = global_symbol_table
    result = interpreter.visit(tree.node, context)

    return result.value, result.error
