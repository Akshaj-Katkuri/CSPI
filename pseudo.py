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

class InvalidSyntaxError(Error): 
    def __init__(self, pos_start, pos_end, details=''):
        super().__init__(pos_start, pos_end, 'Invalid Synstax', details)

# Token types
TYPE_INT = 'INT'
TYPE_FLOAT = 'FLOAT'
TYPE_PLUS = 'PLUS'
TYPE_MINUS = 'MINUS'
TYPE_MUL = 'MUL'
TYPE_DIV = 'DIV'
TYPE_LPAREN = 'LPAREN'
TYPE_RPAREN = 'RPAREN'
TYPE_EOF = 'EOF'

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
    
    def make_tokens(self): 
        tokens = []

        while self.current_char != None: 
            if self.current_char in ' \t': 
                self.advance()
            elif self.current_char == '+': 
                tokens.append(Token(TYPE_PLUS, pos_start=self.pos))
                self.advance()
            elif self.current_char == '-': 
                tokens.append(Token(TYPE_MINUS, pos_start=self.pos))
                self.advance()
            elif self.current_char == '*':
                tokens.append(Token(TYPE_MUL, pos_start=self.pos))
                self.advance()
            elif self.current_char == '/':
                tokens.append(Token(TYPE_DIV, pos_start=self.pos))
                self.advance()
            elif self.current_char == '(':
                tokens.append(Token(TYPE_LPAREN, pos_start=self.pos))
                self.advance()
            elif self.current_char == ')':
                tokens.append(Token(TYPE_RPAREN, pos_start=self.pos))
                self.advance()
            elif self.current_char.isdigit(): 
                tokens.append(self.make_number())
            else: 
                pos_start = self.pos.copy()
                char = self.current_char
                self.advance()
                return [], IllegalCharError(pos_start, self.pos.idx, f"'{char}'")

        tokens.append(Token(TYPE_EOF, pos_start=self.pos))
        return tokens, None

    def make_number(self): 
        num_str = ''
        dot_count = 0 # to check if float or integer
        pos_start = self.pos.copy()

        while self.current_char != None and (self.current_char.isdigit() or self.current_char == '.'):
            if self.current_char == '.':
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
        
# Nodes for PEMDAS operations tree

class NumberNode:
    def __init__(self, token: Token):
        self.token = token

    def __repr__(self):
        return f'{self.token}'
    
class BinaryOperatorNode:
    def __init__(self, left_node, operator_token, right_node):
        self.left_node = left_node
        self.operator_token = operator_token
        self.right_node = right_node

    def __repr__(self):
        return f'({self.left_node}, {self.operator_token}, {self.right_node})'
    
class UnaryOperatorNode: 
    def __init__(self, operator_token, node):
        self.operator_token = operator_token
        self.node = node

    def __repr__(self):
        return f'({self.operator_token}, {self.node})'

class ParseResult: 
    def __init__(self):
        self.error = None
        self.node = None

    def register(self, response): 
        if isinstance(response, ParseResult): 
            if response.error: self.error = response.error
            return response.node
        
        return response

    def success(self, node): 
        self.node = node
        return self

    def failure(self, error): 
        self.error = error
        return self

# Parser

class Parser: 
    def __init__(self, tokens):
        self.tokens = tokens
        self.token_idx = -1
        self.advance()

    def advance(self): 
        self.token_idx += 1
        if self.token_idx < len(self.tokens):
            self.current_token: Token = self.tokens[self.token_idx]
        return self.current_token
    
    def parse(self): 
        result = self.expr()
        if not result.error and self.current_token.type != TYPE_EOF:
            return result.failure(InvalidSyntaxError(
                self.current_token.pos_start, self.current_token.pos_end, "Expected '+', '-', '*', or '/'"
            ))
        return result
    
    def factor(self): 
        response = ParseResult()
        token = self.current_token

        if token.type in (TYPE_PLUS, TYPE_MINUS): 
            response.register(self.advance())
            factor = response.register(self.factor())
            if response.error: return response
            return response.success(UnaryOperatorNode(token, factor))
        
        elif token.type in (TYPE_INT, TYPE_FLOAT): 
            response.register(self.advance())
            return response.success(NumberNode(token))
        
        elif token.type == TYPE_LPAREN: 
            response.register(self.advance())
            expr = response.register(self.expr())
            if response.error: return response
            if self.current_token.type == TYPE_RPAREN: 
                response.register(self.advance())
                return response.success(expr)
            else:
                return response.failure(InvalidSyntaxError(
                    self.current_token.pos_start, self.current_token.pos_end, "Expected ')'"
                ))
        
        return response.failure(InvalidSyntaxError(token.pos_start, token.pos_end, "Expected int or float"))

    def term(self): 
        return self.binary_operation(self.factor, (TYPE_DIV, TYPE_MUL))

    def expr(self): 
        return self.binary_operation(self.term, (TYPE_PLUS, TYPE_MINUS))
    
    def binary_operation(self, func, op_tokens): 
        result = ParseResult()
        left = result.register(func())
        if result.error: return result

        while self.current_token.type in op_tokens: 
            op_token = self.current_token
            result.register(self.advance())
            right = result.register(func())
            if result.error: return result
            left = BinaryOperatorNode(left, op_token, right)

        return result.success(left)

def run(fn, text):
    lexer = Lexer(fn, text)
    tokens, error = lexer.make_tokens()
    if error: return None, error

    # Generate Tree
    parser = Parser(tokens)
    tree = parser.parse()

    return tree.node, tree.error