from utilities import string_with_arrows

class Position: 
    def __init__(self, idx, ln, col, fn, ftxt):
        self.idx = idx
        self.ln = ln
        self.col = col
        self.fn = fn
        self.ftxt = ftxt

    def advance(self, current_char=None):
        self.idx += 1
        self.col += 1

        if current_char == '\n':
            self.ln += 1
            self.col = 0
        
        return self
    
    def revert(self, idx, col, ln): 
        self.idx = idx
        self.col = col
        self.ln = ln

        return self
    
    def copy(self): 
        return Position(self.idx, self.ln, self.col, self.fn, self.ftxt)

class Error: 
    def __init__(self, pos_start: Position, pos_end, error_name, details):
        self.pos_start = pos_start
        self.pos_end = pos_end
        self.error_name = error_name
        self.details = details

    def as_string(self): 
        result = f'{self.error_name}: {self.details}\n'
        result += f'File {self.pos_start.fn}, line {self.pos_start.ln + 1}'
        result += '\n\n' + string_with_arrows(self.pos_start.ftxt, self.pos_start, self.pos_end)
        return result

class IllegalCharError(Error): 
    def __init__(self, pos_start, pos_end, details):
        super().__init__(pos_start, pos_end, 'Illegal Character', details)

class ExpectedCharacterError(Error): 
    def __init__(self, pos_start, pos_end, details): 
        super().__init__(pos_start, pos_end, 'Expected Character', details)

class InvalidSyntaxError(Error): 
    def __init__(self, pos_start, pos_end, details=''):
        super().__init__(pos_start, pos_end, 'Invalid Synstax', details)

class RunTimeError(Error): 
    def __init__(self, pos_start, pos_end, details, context):
        super().__init__(pos_start, pos_end, 'Runtime Error', details)
        self.context = context

    def as_string(self):
        result = self.generate_traceback()
        result += f'{self.error_name}: {self.details}\n'
        result += '\n\n' + string_with_arrows(self.pos_start.ftxt, self.pos_start, self.pos_end)
        return result
    
    def generate_traceback(self):
        result = ''
        pos = self.pos_start
        ctx: Context = self.context

        while ctx: 
            result = f'     File {pos.fn}, line {pos.ln + 1}, in {ctx.display_name}\n' + result
            pos = ctx.parent_entry_pos
            ctx = ctx.parent
        
        return 'Traceback (most recent call last):\n' + result

# Token types
TYPE_INT = 'INT'
TYPE_FLOAT = 'FLOAT'
TYPE_IDENTIFIER = 'IDENTIFIER' # The variable name
TYPE_KEYWORD = 'KEYWORD' # Keywords like 'function'
TYPE_PLUS = 'PLUS'
TYPE_MINUS = 'MINUS'
TYPE_MUL = 'MUL'
TYPE_DIV = 'DIV'
TYPE_POW = 'POW'
TYPE_EQ = 'EQ' # Assignment operator
TYPE_LPAREN = 'LPAREN'
TYPE_RPAREN = 'RPAREN'
TYPE_EE = 'EE' # ==
TYPE_NE = 'NE' # !=
TYPE_LT = 'LT' # <
TYPE_GT = 'GT' # >
TYPE_LTE = 'LTE' # <=  
TYPE_GTE = 'GTE' # >=
TYPE_EOF = 'EOF'

KEYWORDS = [
    'VAR', 
    'AND', 
    'OR', 
    'NOT', 
    'MOD'
]

class Token(): 
    def __init__(self, type_, value=None, pos_start:Position=None, pos_end:Position=None): 
        self.type = type_
        self.value = value
        
        if pos_start: 
            self.pos_start = pos_start.copy()
            self.pos_end = pos_start.copy()
            self.pos_end.advance()
        if pos_end: 
            self.pos_end = pos_end.copy()

    def matches(self, type_, value):
        return self.type == type_ and self.value == value

    def __repr__(self):
        if self.value: 
            return f"{self.type}:{self.value}"
        return f'{self.type}'
    
class Lexer: 
    def __init__(self, fn, text):
        self.fn = fn
        self.text = text
        self.pos = Position(-1, 0, -1, fn, text)
        self.current_char: str = None
        self.advance()

    def advance(self): 
        self.pos.advance(self.current_char)
        self.current_char = self.text[self.pos.idx] if self.pos.idx < len(self.text) else None

    def get_next_char(self): 
        next_pos = self.pos.copy().advance()
        return self.text[next_pos.idx] if next_pos.idx < len(self.text) else None
    
    def make_tokens(self): 
        tokens = []

        while self.current_char != None: 
            if self.current_char in ' \t': 
                self.advance()
            elif self.current_char.isdigit(): 
                tokens.append(self.make_number())
            elif self.current_char.isalpha() or self.current_char == '_': 
                tokens.append(self.make_identifier())
            elif self.current_char == '+': 
                tokens.append(Token(TYPE_PLUS, pos_start=self.pos))
                self.advance()
            elif self.current_char == '-': 
                tokens.append(Token(TYPE_MINUS, pos_start=self.pos))
                self.advance()
            elif self.current_char == '*':
                if self.get_next_char() == '*':
                    tokens.append(Token(TYPE_POW, '**', pos_start=self.pos))
                    self.advance()
                    self.advance()
                else: 
                    tokens.append(Token(TYPE_MUL, pos_start=self.pos))
                    self.advance()
            elif self.current_char == '/':
                tokens.append(Token(TYPE_DIV, pos_start=self.pos))
                self.advance()
            elif self.current_char == '%': 
                tokens.append(Token(TYPE_KEYWORD, 'MOD', pos_start=self.pos))
                self.advance()
            elif self.current_char == '^':
                tokens.append(Token(TYPE_POW, pos_start=self.pos))
                self.advance()
            elif self.current_char == '(':
                tokens.append(Token(TYPE_LPAREN, pos_start=self.pos))
                self.advance()
            elif self.current_char == ')':
                tokens.append(Token(TYPE_RPAREN, pos_start=self.pos))
                self.advance()
            elif self.current_char == '!': 
                token, error = self.make_not_equals()
                if error: return [], error
                tokens.append(token)
            elif self.current_char == '=': #TODO: Change this to accept ← or <- for assignment operator
                token, error = self.make_equals()
                if error: return [], error
                tokens.append(token)
            elif self.current_char == '<': 
                token, error = self.make_less_than()
                if error: return [], error
                tokens.append(token)
            elif self.current_char == '>': 
                token, error = self.make_greater_than()
                if error: return [], error
                tokens.append(token)
            else: 
                pos_start = self.pos.copy()
                char = self.current_char
                self.advance()
                return [], IllegalCharError(pos_start, self.pos, f"'{char}'")

        tokens.append(Token(TYPE_EOF, pos_start=self.pos))
        return tokens, None

    def make_number(self): 
        num_str = ''
        dot_count = 0 # to check if float or integer
        pos_start = self.pos.copy()
        starting_char = self.current_char

        while self.current_char != None and (self.current_char.isdigit() or self.current_char == '.' or self.current_char.isalpha()):
            if self.current_char.isalpha(): 
                self.current_char = starting_char
                self.pos.revert(pos_start.idx, pos_start.col, pos_start.ln)
                return self.make_identifier()
            elif self.current_char == '.':
                if dot_count == 1: break #TODO: implement raise error here
                dot_count += 1
                num_str += '.'
            else: 
                num_str += self.current_char
            self.advance()
            
        if dot_count == 0: 
            return Token(TYPE_INT, int(num_str), pos_start=pos_start, pos_end=self.pos)
        else: 
            return Token(TYPE_FLOAT, float(num_str), pos_start=pos_start, pos_end=self.pos)
    
    def make_identifier(self):
        id_str = ''
        pos_start = self.pos.copy()

        while self.current_char != None and (self.current_char.isalnum() or self.current_char == '_'):
            id_str += self.current_char
            self.advance()

        token_type = TYPE_KEYWORD if id_str in KEYWORDS else TYPE_IDENTIFIER
        return Token(token_type, id_str, pos_start=pos_start, pos_end=self.pos)
    
    def make_not_equals(self): 
        pos_start = self.pos.copy()
        self.advance()

        if self.current_char == '=': 
            self.advance()
            return Token(TYPE_NE, pos_start=pos_start, pos_end=self.pos), None
        
        self.advance()
        return None, ExpectedCharacterError(pos_start, self.pos, "'=' (after '!')")
    
    def make_equals(self): 
        token_type = TYPE_EQ
        pos_start = self.pos.copy()
        self.advance()

        if self.current_char == '=': 
            self.advance()
            token_type = TYPE_EE

        return Token(token_type, pos_start=pos_start, pos_end=self.pos), None
    
    def make_less_than(self):
        token_type = TYPE_LT
        pos_start = self.pos.copy()
        self.advance()

        if self.current_char == '=': 
            self.advance()
            token_type = TYPE_LTE

        return Token(token_type, pos_start=pos_start, pos_end=self.pos), None
    
    def make_greater_than(self): 
        token_type = TYPE_GT
        pos_start = self.pos.copy()
        self.advance()

        if self.current_char == '=': 
            self.advance()
            token_type = TYPE_GTE

        return Token(token_type, pos_start=pos_start, pos_end=self.pos), None
        
# Nodes for PEMDAS operations tree

class NumberNode:
    def __init__(self, token: Token):
        self.token = token

        self.pos_start = token.pos_start
        self.pos_end = token.pos_end

    def __repr__(self):
        return f'{self.token}'
    
class VariableAccessNode:
    def __init__(self, var_name_token: Token):
        self.var_name_token = var_name_token

        self.pos_start = var_name_token.pos_start
        self.pos_end = var_name_token.pos_end

class VariableAssignNode:
    def __init__(self, var_name_token: Token, value_node):
        self.var_name_token = var_name_token
        self.value_node = value_node

        self.pos_start = var_name_token.pos_start
        self.pos_end = value_node.pos_end
    
class BinaryOperatorNode:
    def __init__(self, left_node, operator_token: Token, right_node):
        self.left_node = left_node
        self.operator_token = operator_token
        self.right_node = right_node

        self.pos_start = left_node.pos_start
        self.pos_end = right_node.pos_end

    def __repr__(self):
        return f'({self.left_node}, {self.operator_token}, {self.right_node})'
    
class UnaryOperatorNode: 
    def __init__(self, operator_token: Token, node):
        self.operator_token = operator_token
        self.node = node

        self.pos_start = operator_token.pos_start
        self.pos_end = node.pos_end

    def __repr__(self):
        return f'({self.operator_token}, {self.node})'

class ParseResult: 
    def __init__(self):
        self.error = None
        self.node = None
        self.advance_count = 0

    def register_advancement(self): 
        self.advance_count += 1

    def register(self, result): 
        self.advance_count += result.advance_count
        if result.error: self.error = result.error
        return result.node

    def success(self, node): 
        self.node = node
        return self

    def failure(self, error): 
        if not self.error or self.advance_count == 0:
            self.error = error
        return self

# Parser

class Parser: 
    def __init__(self, tokens):
        self.tokens = tokens
        self.token_idx = -1
        self.advance()

    def advance(self) -> Token: 
        self.token_idx += 1
        if self.token_idx < len(self.tokens):
            self.current_token: Token = self.tokens[self.token_idx]
        return self.current_token
    
    def get_next_token(self) -> Token: 
        return self.tokens[self.token_idx + 1] if self.token_idx + 1 < len(self.tokens) else None
    
    def parse(self): 
        result = self.expr()
        if not result.error and self.current_token.type != TYPE_EOF:
            return result.failure(InvalidSyntaxError(
                self.current_token.pos_start, self.current_token.pos_end, "Expected '+', '-', '*', or '/'"
            ))
        return result
    
    def atom(self): 
        result = ParseResult()
        token = self.current_token

        if token.type in (TYPE_INT, TYPE_FLOAT): 
            result.register_advancement()
            self.advance()
            return result.success(NumberNode(token))
        
        elif token.type == TYPE_IDENTIFIER:
            result.register_advancement()
            self.advance()
            return result.success(VariableAccessNode(token))
        
        elif token.type == TYPE_LPAREN: 
            result.register_advancement()
            self.advance()
            expr = result.register(self.expr())
            if result.error: return result
            if self.current_token.type == TYPE_RPAREN: 
                result.register_advancement()
                self.advance()
                return result.success(expr)
            else:
                return result.failure(InvalidSyntaxError(
                    self.current_token.pos_start, self.current_token.pos_end, "Expected ')'"
                ))
            
        return result.failure(InvalidSyntaxError(token.pos_start, token.pos_end, "Expected int, float, identifier, '+', '-', or '('"))
    
    def power(self): 
        return self.binary_operation(self.atom, (TYPE_POW, ), self.factor)
    
    def factor(self): 
        result = ParseResult()
        token = self.current_token

        if token.type in (TYPE_PLUS, TYPE_MINUS): 
            result.register_advancement()
            self.advance()
            factor = result.register(self.factor())
            if result.error: return result
            return result.success(UnaryOperatorNode(token, factor))
        
        return self.power()

    def term(self): 
        return self.binary_operation(self.factor, (TYPE_DIV, TYPE_MUL, (TYPE_KEYWORD, 'MOD')))
    
    def arith_expr(self): 
        return self.binary_operation(self.term, (TYPE_PLUS, TYPE_MINUS))
    
    def comp_expr(self): 
        result = ParseResult()

        if self.current_token.matches(TYPE_KEYWORD, 'NOT'): 
            op_token = self.current_token
            result.register_advancement()
            self.advance()

            node = result.register(self.comp_expr())
            if result.error: return result
            return result.success(UnaryOperatorNode(op_token, node))

        node = result.register(self.binary_operation(self.arith_expr, (TYPE_EE, TYPE_NE, TYPE_LT, TYPE_GT, TYPE_LTE, TYPE_GTE)))

        if result.error: 
            return result.failure(InvalidSyntaxError(
                self.current_token.pos_start, self.current_token.pos_end, 
                "Expected int, float, identifier, '+', '-', '(', or 'NOT")
            )
        
        return result.success(node)

    def expr(self): 
        result = ParseResult()

        if self.current_token.matches(TYPE_KEYWORD, 'VAR'):
            result.register_advancement()
            self.advance()

            if self.current_token.type != TYPE_IDENTIFIER:
                return result.failure(InvalidSyntaxError(
                    self.current_token.pos_start, self.current_token.pos_end, "Expected identifier"
                ))
            
            var_name = self.current_token
            result.register_advancement()
            self.advance()

            if self.current_token.type != TYPE_EQ:
                return result.failure(InvalidSyntaxError(
                    self.current_token.pos_start, self.current_token.pos_end, "Expected '='" #TODO: Change this to left arrow later
                ))
            
            result.register_advancement()
            self.advance()

            expr = result.register(self.expr())
            if result.error: return result
            return result.success(VariableAssignNode(var_name, expr))
        
        if self.current_token.type == TYPE_IDENTIFIER and self.get_next_token().type == TYPE_EQ: 
            var_name = self.current_token
            
            result.register_advancement()
            self.advance() # now at TYPE_EQ

            result.register_advancement()
            self.advance() # now at value

            expr = result.register(self.expr())
            if result.error: return result
            return result.success(VariableAssignNode(var_name, expr))

        node = result.register(self.binary_operation(self.comp_expr, ((TYPE_KEYWORD, 'AND'), (TYPE_KEYWORD, 'OR'))))

        if result.error: 
            return result.failure(InvalidSyntaxError(
                self.current_token.pos_start, self.current_token.pos_end,
                "Expected 'VAR', int, float, identifier, '+', '-', or '('"
            ))
        
        return result.success(node)
    
    def binary_operation(self, func_a, op_tokens, func_b=None) -> ParseResult: 
        result = ParseResult()
        left = result.register(func_a())
        if result.error: return result

        while self.current_token.type in op_tokens or (self.current_token.type, self.current_token.value) in op_tokens: 
            op_token = self.current_token
            result.register_advancement()
            self.advance()
            right = result.register(func_b()) if func_b else result.register(func_a())
            if result.error: return result
            left = BinaryOperatorNode(left, op_token, right)

        return result.success(left)

class RunTimeResult:
    def __init__(self):
        self.value = None
        self.error = None

    def register(self, result):
        if isinstance(result, RunTimeResult):
            if result.error: self.error = result.error
            return result.value
        return result

    def success(self, value):
        self.value = value
        return self

    def failure(self, error):
        self.error = error
        return self

class Number: 
    def __init__(self, value):
        self.value = value
        self.set_position()
        self.set_context()

    def set_position(self, pos_start: Position = None, pos_end: Position = None):
        self.pos_start = pos_start
        self.pos_end = pos_end
        return self
    
    def set_context(self, context=None):
        self.context = context
        return self
    
    def added_to(self, other): 
        if isinstance(other, Number):
            return Number(self.value + other.value).set_context(self.context), None
        
    def subract_by(self, other): 
        if isinstance(other, Number):
            return Number(self.value - other.value).set_context(self.context), None
        
    def multiply_by(self, other):
        if isinstance(other, Number):
            return Number(self.value * other.value).set_context(self.context), None
        
    def divide_by(self, other):
        if isinstance(other, Number):
            if other.value == 0:
                return None, RunTimeError(other.pos_start, other.pos_end, "Division by zero", self.context)
            return Number(self.value / other.value).set_context(self.context), None
        
    def mod_by(self, other): 
        if isinstance(other, Number): 
            if other.value == 0: 
                return None, RunTimeError(other.pos_start, other.pos_end, "Division by zero", self.context)
            return Number(self.value % other.value).set_context(self.context), None
        
    def power_by(self, other): 
        if isinstance(other, Number):
            return Number(self.value ** other.value).set_context(self.context), None
        
    def get_comparison_eq(self, other):
        if isinstance(other, Number):
            return Number(int(self.value == other.value)).set_context(self.context), None
        
    def get_comparison_ne(self, other):
        if isinstance(other, Number):
            return Number(int(self.value != other.value)).set_context(self.context), None
        
    def get_comparison_lt(self, other):
        if isinstance(other, Number):
            return Number(int(self.value < other.value)).set_context(self.context), None
        
    def get_comparison_gt(self, other):
        if isinstance(other, Number):
            return Number(int(self.value > other.value)).set_context(self.context), None
        
    def get_comparison_lte(self, other):
        if isinstance(other, Number):
            return Number(int(self.value <= other.value)).set_context(self.context), None
        
    def get_comparison_gte(self, other):
        if isinstance(other, Number):
            return Number(int(self.value >= other.value)).set_context(self.context), None
        
    def and_by(self, other):
        if isinstance(other, Number):
            return Number(int(self.value and other.value)).set_context(self.context), None
        
    def or_by(self, other): 
        if isinstance(other, Number): 
            return Number(int(self.value or other.value)).set_context(self.context), None
        
    def notted(self): 
        return Number(1 if self.value == 0 else 0).set_context(self.context), None
        
    def copy(self): 
        copy = Number(self.value)
        copy.set_position(self.pos_start, self.pos_end)
        copy.set_context(self.context)
        return copy
        
    def __repr__(self):
        return str(self.value)

class Context: 
    def __init__(self, display_name, parent=None, parent_entry_pos=None):
        self.display_name = display_name
        self.parent = parent
        self.parent_entry_pos = parent_entry_pos
        self.symbol_table: SymbolTable = None

class SymbolTable:
    def __init__(self):
        self.symbols = {}
        self.parent: SymbolTable = None

    def get(self, name) -> Number: #for now only return's number 
        value = self.symbols.get(name, None)
        if value == None and self.parent:
            return self.parent.get(name)
        return value
    
    def set(self, name, value): 
        self.symbols[name] = value

    def remove(self, name): 
        del self.symbols[name]

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
            Number(node.token.value).set_context(context).set_position(node.token.pos_start, node.token.pos_end)
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
        
        value = value.copy().set_position(node.pos_start, node.pos_end)
        return RTresult.success(value)
    
    def visit_VariableAssignNode(self, node: VariableAssignNode, context: Context):
        RTresult = RunTimeResult()
        var_name = node.var_name_token.value
        value = RTresult.register(self.visit(node.value_node, context))
        if RTresult.error: return RTresult

        context.symbol_table.set(var_name, value)
        return RTresult.success(value)

    def visit_BinaryOperatorNode(self, node: BinaryOperatorNode, context: Context): 
        RTresult = RunTimeResult()
        left: Number = RTresult.register(self.visit(node.left_node, context))
        if RTresult.error: return RTresult
        right: Number = RTresult.register(self.visit(node.right_node, context))
        if RTresult.error: return RTresult
        
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
            return RTresult.success(result.set_position(node.pos_start, node.pos_end))

    def visit_UnaryOperatorNode(self, node: UnaryOperatorNode, context: Context):
        RTresult = RunTimeResult()
        number: Number = RTresult.register(self.visit(node.node, context))
        if RTresult.error: return RTresult

        error = None

        if node.operator_token.type == TYPE_MINUS:
            number, error = number.multiply_by(Number(-1))
        elif node.operator_token.matches(TYPE_KEYWORD, 'NOT'): 
            number, error = number.notted()

        if error:
            return RTresult.failure(error)
        else: 
            return RTresult.success(number.set_position(node.pos_start, node.pos_end))

global_symbol_table = SymbolTable()
global_symbol_table.set("NULL", Number(0))
global_symbol_table.set("TRUE", Number(1))
global_symbol_table.set("FALSE", Number(0))

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