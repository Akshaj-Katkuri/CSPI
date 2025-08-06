import os

from values import *
from utils.context import Context, SymbolTable
from utils.results import RunTimeResult
from utils.errors import RunTimeError
from lexer.tokens import *
from parser.nodes import *
from lexer.lexer import Lexer
from parser.parser import Parser

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

    def execute_print(self, exec_context): 
        print(str(exec_context.symbol_table.get('value')))
        return RunTimeResult().success(Number.null)
    execute_print.arg_names = ["value"]

    def execute_print_return(self, exec_context): 
        return RunTimeResult().success(String(str(exec_context.symbol_table.get('value'))))
    execute_print_return.arg_names = ["value"]

    def execute_input(self, exec_context): #TODO: Maybe make this fancier with string argument?
        text = input()
        return RunTimeResult().success(String(text))
    execute_input.arg_names = []

    def execute_input_int(self, exec_context): #TODO: Maybe make this fancier with string argument too?
        while True:
            text = input()
            try: 
                number = int(text)
                break
            except ValueError: 
                print(f"'{text}' mus be an integer. Try again!") #TODO: get rid of this and replace with error too?
        return RunTimeResult().success(Number(text))
    execute_input_int.arg_names = []

    def execute_clear(self, exec_context): 
        os.system('cls' if os.name == 'nt' else 'clear')
        return RunTimeResult().success(Number.null)
    execute_clear.arg_names = []

    def execute_is_number(self, exec_context): 
        is_number = isinstance(exec_context.symbol_table.get('value'), Number)
        return RunTimeResult().success(Number.true if is_number else Number.false)
    execute_is_number.arg_names = ['value']

    def execute_is_string(self, exec_context): 
        is_string = isinstance(exec_context.symbol_table.get('value'), String)
        return RunTimeResult().success(Number.true if is_string else Number.false)
    execute_is_string.arg_names = ['value']

    def execute_is_list(self, exec_context): 
        is_list = isinstance(exec_context.symbol_table.get('value'), List)
        return RunTimeResult().success(Number.true if is_list else Number.false)
    execute_is_list.arg_names = ['value']

    def execute_is_function(self, exec_context): 
        is_function = isinstance(exec_context.symbol_table.get('value'), BaseFunction)
        return RunTimeResult().success(Number.true if is_function else Number.false)
    execute_is_function.arg_names = ['value']

    def execute_append(self, exec_context): 
        list_ = exec_context.symbol_table.get('list')
        value_ = exec_context.symbol_table.get('value')

        if not isinstance(list_, List): 
            return RunTimeResult().failue(RunTimeError( #TODO: Change to syntax error maybe?
                self.pos_start, self.pos_end,
                "First argument must be a list", 
                exec_context
            ))
        
        list_.elements.append(value_) #TODO: Maybe add error check for value_ too?
        return RunTimeResult().success(Number.null)
    execute_append.arg_names = ['list', 'value']

    def execute_pop(self, exec_context): 
        list_ = exec_context.symbol_table.get('list')
        index = exec_context.symbol_table.get('index')

        if not isinstance(list_, List): 
            return RunTimeResult().failue(RunTimeError( #TODO: Change to syntax error maybe?
                self.pos_start, self.pos_end,
                "First argument must be a list", 
                exec_context
            ))
        
        if not isinstance(index, Number): 
            return RunTimeResult().failue(RunTimeError( #TODO: Change to syntax error maybe?
                self.pos_start, self.pos_end,
                "Second argument must be a number", 
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
    execute_pop.arg_names = ['list', 'index']

    def execute_extend(self, exec_context):
        listA = exec_context.symbol_table.get('listA')
        listB = exec_context.symbol_table.get('listB')

        if not isinstance(listA, List): 
            return RunTimeResult().failue(RunTimeError( #TODO: Change to syntax error maybe?
                self.pos_start, self.pos_end,
                "First argument must be a list", 
                exec_context
            ))
        
        if not isinstance(listB, List): 
            return RunTimeResult().failue(RunTimeError( #TODO: Change to syntax error maybe?
                self.pos_start, self.pos_end,
                "Second argument must be a list", 
                exec_context
            ))
        
        listA.elements.extend(listB.elements)
        return RunTimeResult().success(Number.null)
    execute_extend.arg_names = ['listA', 'listB']

    def execute_len(self, exec_context): 
        list_ = exec_context.symbol_table.get('list')

        if not isinstance(list_, List): 
            return RunTimeResult().failue(RunTimeError( #TODO: Change to syntax error maybe?
                self.pos_start, self.pos_end,
                "Argument must be a list", 
                exec_context
            ))
        
        return RunTimeResult().success(Number(len(list_.elements)))
    execute_len.arg_names = ['list']

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

BuiltInFunction.print       = BuiltInFunction("print")
BuiltInFunction.print_ret   = BuiltInFunction("print_ret")
BuiltInFunction.input       = BuiltInFunction("input")
BuiltInFunction.input_int   = BuiltInFunction("input_int")
BuiltInFunction.clear       = BuiltInFunction("clear")
BuiltInFunction.is_number   = BuiltInFunction("is_number")
BuiltInFunction.is_string   = BuiltInFunction("is_string")
BuiltInFunction.is_list     = BuiltInFunction("is_list")
BuiltInFunction.is_function = BuiltInFunction("is_function")
BuiltInFunction.append      = BuiltInFunction("append")
BuiltInFunction.pop         = BuiltInFunction("pop")
BuiltInFunction.extend      = BuiltInFunction("extend")
BuiltInFunction.len         = BuiltInFunction("len")
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
        number: Number = RTresult.register(self.visit(node.node, context))
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
            condition_value: Number = RTresult.register(self.visit(condition, context))
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

        start_value: Number = RTresult.register(self.visit(node.start_value_node, context))
        if RTresult.should_return(): return RTresult

        end_value: Number = RTresult.register(self.visit(node.end_value_node, context))
        if RTresult.should_return(): return RTresult

        if node.step_value_node: 
            step_value: Number = RTresult.register(self.visit(node.step_value_node, context))
            if RTresult.should_return(): return RTresult
        else: 
            step_value = Number(1)
        
        i = start_value.value

        if step_value.value >= 0: 
            condition = lambda: i < end_value.value
        else: 
            condition = lambda: i > end_value.value

        while condition(): 
            context.symbol_table.set(node.var_name_token.value, Number(i))
            i += step_value.value

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

        count: Token = node.count_token
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
global_symbol_table.set("TRUE", Number.true)
global_symbol_table.set("FALSE", Number.false) #TODO: Maybe add pi
global_symbol_table.set("PRINT", BuiltInFunction.print)
global_symbol_table.set("PRINT_RET", BuiltInFunction.print_ret)
global_symbol_table.set("INPUT", BuiltInFunction.input)
global_symbol_table.set("INPUT_INT", BuiltInFunction.input_int)
global_symbol_table.set("CLEAR", BuiltInFunction.clear)
global_symbol_table.set("CLS", BuiltInFunction.clear)
global_symbol_table.set("IS_NUM", BuiltInFunction.is_number)
global_symbol_table.set("IS_STR", BuiltInFunction.is_string)
global_symbol_table.set("IS_LIST", BuiltInFunction.is_list)
global_symbol_table.set("IS_FUN", BuiltInFunction.is_function)
global_symbol_table.set("APPEND", BuiltInFunction.append)
global_symbol_table.set("POP", BuiltInFunction.pop)
global_symbol_table.set("EXTEND", BuiltInFunction.extend)
global_symbol_table.set("LEN", BuiltInFunction.len)
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
