from utilities import string_with_arrows

import os

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
TYPE_STRING = 'STRING'
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
TYPE_LSQUARE = 'LSQUARE'
TYPE_RSQUARE = 'RSQUARE'
TYPE_EE = 'EE' # ==
TYPE_NE = 'NE' # !=
TYPE_LT = 'LT' # <
TYPE_GT = 'GT' # >
TYPE_LTE = 'LTE' # <=  
TYPE_GTE = 'GTE' # >=
TYPE_COMMA = 'COMMA'
TYPE_ARROW = 'ARROW'
TYPE_NEWLINE = 'NEWLINE'
TYPE_EOF = 'EOF'

KEYWORDS = [
    'VAR', 
    'AND', 
    'OR', 
    'NOT', 
    'MOD', 
    'IF', 
    'THEN',
    'ELIF',
    'ELSE',
    'THEN', 
    'FOR', 
    'STEP',
    'WHILE',
    'TO',
    'FUN', #TODO: Change this to "PROCEDURE"
    'END',
    'RETURN',
    'CONTINUE',
    'BREAK'
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

# Lexer

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
            elif self.current_char in ';\n':
                tokens.append(Token(TYPE_NEWLINE, pos_start=self.pos))
                self.advance()
            elif self.current_char.isdigit(): 
                tokens.append(self.make_number())
            elif self.current_char.isalpha() or self.current_char == '_': 
                tokens.append(self.make_identifier())
            elif self.current_char == '"':
                tokens.append(self.make_string())
            elif self.current_char == '+': 
                tokens.append(Token(TYPE_PLUS, pos_start=self.pos))
                self.advance()
            elif self.current_char == '-': 
                if self.get_next_char == '>':
                    pos_start = self.pos.copy()
                    self.advance()
                    self.advance()
                    tokens.append(Token(TYPE_ARROW, '**', pos_start=pos_start, pos_end=self.pos)) #TODO: Verify this pos for end and start
                else: 
                    tokens.append(Token(TYPE_MINUS, pos_start=self.pos))
                    self.advance()
            elif self.current_char == '*':
                if self.get_next_char() == '*':
                    pos_start = self.pos.copy()
                    self.advance()
                    self.advance()
                    tokens.append(Token(TYPE_POW, '**', pos_start=pos_start, pos_end=self.pos)) #TODO: Verify this pos for end and start
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
            elif self.current_char == '[':
                tokens.append(Token(TYPE_LSQUARE, pos_start=self.pos))
                self.advance()
            elif self.current_char == ']':
                tokens.append(Token(TYPE_RSQUARE, pos_start=self.pos))
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
            elif self.current_char == ',': 
                tokens.append(Token(TYPE_COMMA, pos_start=self.pos))
                self.advance()
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

    def make_string(self): 
        string = ''
        pos_start = self.pos.copy()
        escape_character = False
        self.advance()

        escape_characters = {
            'n': '\n',
            't': '\t'
        }

        while (self.current_char != '"' or escape_character) and self.current_char != None: 
            if escape_character: 
                string += escape_characters.get(self.current_char, self.current_char)
                self.advance()
                escape_character = False
            else:
                if self.current_char == '\\':
                    escape_character = True
                    self.advance()
                else:
                    string += self.current_char
                    self.advance()
                    escape_character = False

        self.advance()
        return Token(TYPE_STRING, string, pos_start, self.pos)
    
    def make_identifier(self):
        id_str = ''
        pos_start = self.pos.copy()

        while self.current_char != None and (self.current_char.isalnum() or self.current_char == '_'):
            id_str += self.current_char
            self.advance()

        token_type = TYPE_KEYWORD if id_str in KEYWORDS else TYPE_IDENTIFIER
        return Token(token_type, id_str, pos_start=pos_start, pos_end=self.pos)
    
    def make_minus_or_arrow(self): 
        token_type = TYPE_MINUS
        pos_start = self.pos.copy()
        self.advance()

        if self.current_char == '>': 
            self.advance()
            token_type = TYPE_ARROW

        return Token(token_type, pos_start=pos_start, pos_end=self.pos)
    
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
    
class StringNode:
    def __init__(self, token: Token):
        self.token = token

        self.pos_start = token.pos_start
        self.pos_end = token.pos_end

    def __repr__(self):
        return f'{self.token}'
    
class ListNode: 
    def __init__(self, element_nodes, pos_start, pos_end):
        self.element_nodes = element_nodes

        self.pos_start = pos_start
        self.pos_end = pos_end
    
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
    
class IfNode: 
    def __init__(self, cases, else_case): 
        self.cases = cases
        self.else_case = else_case

        self.pos_start = self.cases[0][0].pos_start
        self.pos_end = (self.else_case or self.cases[-1])[0].pos_end

class ForNode: 
    def __init__(self, var_name_token, start_value_node, end_value_node, step_value_node, body_node, should_return_null): 
        self.var_name_token: Token = var_name_token
        self.start_value_node = start_value_node
        self.end_value_node = end_value_node
        self.step_value_node = step_value_node
        self.body_node = body_node
        self.should_return_null = should_return_null

        self.pos_start = var_name_token.pos_start
        self.pos_end = body_node.pos_end 

class WhileNode:
    def __init__(self, condition_node, body_node, should_return_null):
        self.condition_node = condition_node
        self.body_node = body_node
        self.should_return_null = should_return_null

        self.pos_start = condition_node.pos_start
        self.pos_end = body_node.pos_end

class FunctionDefinitionNode: 
    def __init__(self, var_name_token: Token, arg_name_tokens: list[Token], body_node, should_auto_return): #TODO: Double check these typings
        self.var_name_token = var_name_token
        self.arg_name_tokens = arg_name_tokens
        self.body_node = body_node
        self.should_auto_return = should_auto_return

        if self.var_name_token: 
            self.pos_start = self.var_name_token.pos_start
        elif len(self.arg_name_tokens) > 0: 
            self.pos_start = self.arg_name_tokens[0].pos_start
        else: 
            self.pos_start = self.body_node.pos_start

        self.pos_end = self.body_node.pos_end

class CallNode: 
    def __init__(self, node_to_call, arg_nodes):
        self.node_to_call = node_to_call
        self.arg_nodes = arg_nodes

        self.pos_start = self.node_to_call.pos_start

        if len(self.arg_nodes) > 0: 
            self.pos_end = self.arg_nodes[len(self.arg_nodes) - 1].pos_end #TODO: Change this to [-1] if same thing
        else: 
            self.pos_end = self.node_to_call.pos_end

class ReturnNode: 
    def __init__(self, node_to_return, pos_start, pos_end): 
        self.node_to_return = node_to_return
        
        self.pos_start = pos_start
        self.pos_end = pos_end

class ContinueNode:
    def __init__(self, pos_start, pos_end):
        self.pos_start = pos_start
        self.pos_end = pos_end

class BreakNode:
    def __init__(self, pos_start, pos_end):
        self.pos_start = pos_start
        self.pos_end = pos_end

class ParseResult: 
    def __init__(self):
        self.error = None
        self.node = None
        self.last_registered_advance_count = 0
        self.advance_count = 0
        self.to_reverse_count = 0

    def register_advancement(self): 
        self.advance_count += 1

    def register(self, result): 
        self.last_registered_advance_count = result.advance_count
        self.advance_count += result.advance_count
        if result.error: self.error = result.error
        return result.node
    
    def try_register(self, result): 
        if result.error: 
            self.to_reverse_count = result.advance_count
            return None
        return self.register(result)

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
        self.update_current_token()
        return self.current_token
    
    def reverse(self, amount=1) -> Token:
        self.token_idx -= amount
        self.update_current_token()
        return self.current_token

    def update_current_token(self): 
        if self.token_idx < len(self.tokens):
            self.current_token: Token = self.tokens[self.token_idx]
    
    def get_next_token(self) -> Token: 
        return self.tokens[self.token_idx + 1] if self.token_idx + 1 < len(self.tokens) else None
    
    def parse(self): 
        result = self.statements()
        if not result.error and self.current_token.type != TYPE_EOF:
            return result.failure(InvalidSyntaxError(
                self.current_token.pos_start, self.current_token.pos_end, "Expected '+', '-', '*', or '/'"
            ))
        return result
    
    def if_expr_cases(self, case_keyword): 
        result = ParseResult()
        cases = []
        else_case = None

        if not self.current_token.matches(TYPE_KEYWORD, case_keyword): 
            return result.failure(InvalidSyntaxError(
                self.current_token.pos_start, self.current_token.pos_end, 
                f"Expected {case_keyword}"
            ))
        
        result.register_advancement()
        self.advance()

        condition = result.register(self.expr())
        if result.error: return result

        if not self.current_token.matches(TYPE_KEYWORD, 'THEN'): 
            return result.failure(InvalidSyntaxError(
                self.current_token.pos_start, self.current_token.pos_end, 
                "Expected 'THEN'"
            ))
        
        result.register_advancement()
        self.advance()

        if self.current_token.type == TYPE_NEWLINE: 
            result.register_advancement()
            self.advance()

            statements = result.register(self.statements())
            if result.error: return result
            cases.append((condition, statements, True))

            if self.current_token.matches(TYPE_KEYWORD, 'END'): 
                result.register_advancement()
                self.advance()
            else: 
                all_cases = result.register(self.elif_or_else_expr())
                if result.error: return result
                new_cases, else_case = all_cases
                cases.extend(new_cases)
        else: 
            expr = result.register(self.statement())
            if result.error: return result
            cases.append((condition, expr, False))

            all_cases = result.register(self.elif_or_else_expr())
            if result.error: return result
            new_cases, else_case = all_cases
            cases.extend(new_cases)

        return result.success((cases, else_case))
    
    def if_expr(self): 
        result = ParseResult()
        all_cases = result.register(self.if_expr_cases('IF'))
        if result.error: return result
        cases, else_cases = all_cases
        return result.success(IfNode(cases, else_cases))
    
    def elif_expr(self): 
        return self.if_expr_cases('ELIF')
    
    def else_expr(self): 
        result = ParseResult()
        else_case = None

        if self.current_token.matches(TYPE_KEYWORD, 'ELSE'): 
            result.register_advancement()
            self.advance()

            if self.current_token.type == TYPE_NEWLINE:
                result.register_advancement()
                self.advance()

                statements = result.register(self.statements())
                if result.error: return result
                else_case = (statements, True)

                if self.current_token.matches(TYPE_KEYWORD, 'END'): 
                    result.register_advancement()
                    self.advance()
                else: 
                    return result.failure(InvalidSyntaxError(
                        self.current_token.pos_start, self.current_token.pos_end, 
                        "Expected 'END'"
                    ))
            else: 
                expr = result.register(self.statement())
                if result.error: return result
                else_case = (expr, False)

        return result.success(else_case)
    
    def elif_or_else_expr(self): 
        result = ParseResult()
        cases, else_case = [], None

        if self.current_token.matches(TYPE_KEYWORD, 'ELIF'):
            all_cases = result.register(self.elif_expr())
            if result.error: return result
            cases, else_case = all_cases
        else: 
            else_case = result.register(self.else_expr())
            if result.error: return result

        return result.success((cases, else_case))
    
    def for_expr(self): 
        result = ParseResult()

        if not self.current_token.matches(TYPE_KEYWORD, 'FOR'): 
            return result.failure(InvalidSyntaxError(
                self.current_token.pos_start, self.current_token.pos_end, 
                "Expected 'FOR'"
            ))
        
        result.register_advancement()
        self.advance()

        if self.current_token.type != TYPE_IDENTIFIER: 
            return result.failure(InvalidSyntaxError(
                self.current_token.pos_start, self.current_token.pos_end, 
                "Expected Identifier"
            ))
        
        var_name = self.current_token
        result.register_advancement()
        self.advance()

        if self.current_token.type != TYPE_EQ: 
            return result.failure(InvalidSyntaxError(
                self.current_token.pos_start, self.current_token.pos_end, 
                "Expected '='"
            ))
        
        result.register_advancement()
        self.advance()

        start_node = result.register(self.expr())
        if result.error: return result

        if not self.current_token.matches(TYPE_KEYWORD, 'TO'):
            return result.failure(InvalidSyntaxError(
                self.current_token.pos_start, self.current_token.pos_end, 
                "Expected 'TO'"
            ))
        
        result.register_advancement()
        self.advance()

        end_node = result.register(self.expr())
        if result.error: return result

        if self.current_token.matches(TYPE_KEYWORD, 'STEP'): 
            result.register_advancement()
            self.advance()

            step_node = result.register(self.expr())
            if result.error: return result
        else: 
            step_node = None

        if not self.current_token.matches(TYPE_KEYWORD, 'THEN'):
            return result.failure(InvalidSyntaxError(
                self.current_token.pos_start, self.current_token.pos_end, 
                "Expected 'THEN'"
            ))
        
        result.register_advancement()
        self.advance()

        if self.current_token.type == TYPE_NEWLINE: 
            result.register_advancement()
            self.advance()

            body_node = result.register(self.statements())
            if result.error: return result

            if not self.current_token.matches(TYPE_KEYWORD, 'END'):
                return result.failure(InvalidSyntaxError(
                    self.current_token.pos_start, self.current_token.pos_end, 
                    "Expected 'END'"
                ))
            
            result.register_advancement()
            self.advance()

            return result.success(ForNode(
                var_name, start_node, end_node, step_node, body_node, True
            ))

        body_node = result.register(self.statement())
        if result.error: return result

        return result.success(ForNode(
            var_name, start_node, end_node, step_node, body_node, False
        ))

    def while_expr(self): 
        result = ParseResult()

        if not self.current_token.matches(TYPE_KEYWORD, 'WHILE'): 
            return result.failure(InvalidSyntaxError(
                self.current_token.pos_start, self.current_token.pos_end, 
                "Expected 'WHILE'"
            ))
        
        result.register_advancement()
        self.advance()

        condition = result.register(self.expr())
        if result.error: return result

        if not self.current_token.matches(TYPE_KEYWORD, 'THEN'): 
            return result.failure(InvalidSyntaxError(
                self.current_token.pos_start, self.current_token.pos_end, 
                "Expected 'THEN'"
            ))
        
        result.register_advancement()
        self.advance()

        if self.current_token.type == TYPE_NEWLINE: 
            result.register_advancement()
            self.advance()

            body = result.register(self.statements())
            if result.error: return result

            if not self.current_token.matches(TYPE_KEYWORD, 'END'):
                return result.failure(InvalidSyntaxError(
                    self.current_token.pos_start, self.current_token.pos_end, 
                    "Expected 'END'"
                ))
            
            result.register_advancement()
            self.advance()

            return result.success(WhileNode(
                condition, body, True
            ))

        body = result.register(self.statement())
        if result.error: return result

        return result.success(WhileNode(
            condition, body, False
        ))
    
    def func_def(self): 
        result = ParseResult()

        if not self.current_token.matches(TYPE_KEYWORD, 'FUN'): 
            return result.failure(InvalidSyntaxError(
                self.current_token.pos_start, self.current_token.pos_end, 
                "Expected 'FUN'"
            ))

        result.register_advancement()
        self.advance()

        if self.current_token.type == TYPE_IDENTIFIER: 
            var_name_token: Token = self.current_token
            result.register_advancement()
            self.advance()
            if self.current_token.type != TYPE_LPAREN:
                return result.failure(InvalidSyntaxError(
                self.current_token.pos_start, self.current_token.pos_end, 
                "Expected '('"
            ))
        else: 
            var_name_token = None #TODO: Raise error and remove the error message part
            if self.current_token.type != TYPE_LPAREN: 
                return result.failure(InvalidSyntaxError(
                    self.current_token.pos_start, self.current_token.pos_end, 
                    "Expected identifier or '('"
                ))

        result.register_advancement()
        self.advance()
        arg_name_tokens = []

        if self.current_token.type == TYPE_IDENTIFIER: 
            arg_name_tokens.append(self.current_token)
            result.register_advancement()
            self.advance()

            while self.current_token.type == TYPE_COMMA: 
                result.register_advancement
                self.advance()

                if self.current_token.type != TYPE_IDENTIFIER: 
                    return result.failure(InvalidSyntaxError(
                        self.current_token.pos_start, self.current_token.pos_end, 
                        "Espected identifier"
                    ))
                
                arg_name_tokens.append(self.current_token)
                result.register_advancement()
                self.advance()
        
            if self.current_token.type != TYPE_RPAREN: 
                return result.failure(InvalidSyntaxError(
                    self.current_token.pos_start, self.current_token.pos_end,
                    "Expected ',' or ')"
                ))
        else: 
            if self.current_token.type != TYPE_RPAREN: 
                return result.failure(InvalidSyntaxError(
                    self.current_token.pos_start, self.current_token.pos_end,
                    "Expected identifier or ')"
                ))
            
        result.register_advancement()
        self.advance()

        if self.current_token.type == TYPE_ARROW: 
            result.register_advancement()
            self.advance()

            body_node = result.register(self.expr())
            if result.error: return result

            return result.success(FunctionDefinitionNode(
                var_name_token=var_name_token, arg_name_tokens=arg_name_tokens, body_node=body_node, should_auto_return=True
            ))
        
        if self.current_token.type != TYPE_NEWLINE:
            return result.failure(InvalidSyntaxError(
                self.current_token.pos_start, self.current_token.pos_end, 
                "Expected '->' or NEWLINE"
            ))

        result.register_advancement()
        self.advance()

        body_node = result.register(self.statements())
        if result.error: return result

        if not self.current_token.matches(TYPE_KEYWORD, 'END'):
            return result.failure(InvalidSyntaxError(
                self.current_token.pos_start, self.current_token.pos_end,
                "Expected 'END'"
            ))
        
        result.register_advancement()
        self.advance()

        return result.success(FunctionDefinitionNode(
            var_name_token=var_name_token,
            arg_name_tokens=arg_name_tokens,
            body_node=body_node,
            should_auto_return=False
        ))

    
    def list_expr(self): 
        result = ParseResult()
        start_pos = self.current_token.pos_start.copy()
        element_nodes = []

        if self.current_token.type != TYPE_LSQUARE: 
            return result.failure(InvalidSyntaxError(
                self.current_token.pos_start, self.current_token.pos_end, 
                "Expected '['"
            ))
        result.register_advancement()
        self.advance()

        if self.current_token.type == TYPE_RSQUARE:
            result.register_advancement()
            self.advance()
            return result.success(ListNode([], pos_start=start_pos, pos_end=self.current_token.pos_end))
        
        element_nodes.append(result.register(self.expr()))
        if result.error: 
            return result.failure(InvalidSyntaxError(
                self.current_token.pos_start, self.current_token.pos_end, 
                "Expected ']', 'VAR', int, float, identifier, '+', '-', '[', or '('" #TODO: Add keywords and double check error message if keywords needed
            ))

        while self.current_token.type == TYPE_COMMA: 
            result.register_advancement()
            self.advance()

            element_nodes.append(result.register(self.expr()))
            if result.error: return result

        if self.current_token.type != TYPE_RSQUARE: 
            result.failure(InvalidSyntaxError(
                self.current_token.pos_start, self.current_token.pos_end, 
                "Expected ',' or ']'"
            ))
        
        result.register_advancement()
        self.advance()

        return result.success(ListNode(
            element_nodes=element_nodes, pos_start=start_pos, pos_end=self.current_token.pos_end.copy()
        ))
    
    def atom(self): 
        result = ParseResult()
        token = self.current_token

        if token.type in (TYPE_INT, TYPE_FLOAT): 
            result.register_advancement()
            self.advance()
            return result.success(NumberNode(token))
        
        if token.type == TYPE_STRING: 
            result.register_advancement()
            self.advance()
            return result.success(StringNode(token))
        
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
        
        elif token.type == TYPE_LSQUARE: 
            list_expr = result.register(self.list_expr())
            if result.error: return result
            return result.success(list_expr)
            
        elif token.matches(TYPE_KEYWORD, 'IF'): 
            if_expr = result.register(self.if_expr())
            if result.error: return result
            return result.success(if_expr)
        
        elif token.matches(TYPE_KEYWORD, 'FOR'):
            for_expr = result.register(self.for_expr())
            if result.error: return result
            return result.success(for_expr)
        
        elif token.matches(TYPE_KEYWORD, 'WHILE'): 
            while_expr = result.register(self.while_expr())
            if result.error: return result
            return result.success(while_expr)
        
        elif token.matches(TYPE_KEYWORD, 'FUN'): 
            func_def = result.register(self.func_def())
            if result.error: return result
            return result.success(func_def)
            
        return result.failure(InvalidSyntaxError(token.pos_start, token.pos_end, "Expected int, float, identifier, '[', '(', 'IF', 'FOR', 'WHILE', 'FUN'"))
    
    def call(self): 
        result = ParseResult()
        atom = result.register(self.atom())
        if result.error: return result

        if self.current_token.type == TYPE_LPAREN: 
            result.register_advancement()
            self.advance()
            arg_nodes = []

            if self.current_token.type == TYPE_RPAREN: 
                result.register_advancement()
                self.advance()
            else: 
                arg_nodes.append(result.register(self.expr()))
                if result.error: 
                    return result.failure(InvalidSyntaxError(
                        "Expected ')', 'VAR', int, float, identifier, '+', '-', '[', or '('" #TODO: change this error to have keywords. don't copy paste cus this also has ')' in the beginning. 
                    ))
                
                while self.current_token.type == TYPE_COMMA: 
                    result.register_advancement()
                    self.advance()

                    arg_nodes.append(result.register(self.expr()))
                    if result.error: return result

                if self.current_token.type != TYPE_RPAREN: 
                    return result.failure(InvalidSyntaxError(
                        self.current_token.pos_start, self.current_token.pos_end, 
                        "Expected ',' or ')'"
                    ))
                
                result.register_advancement()
                self.advance()
            return result.success(CallNode(node_to_call=atom, arg_nodes=arg_nodes))
        return result.success(atom)
    
    def power(self): 
        return self.binary_operation(self.call, (TYPE_POW, ), self.factor)
    
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
                "Expected int, float, identifier, '+', '-', '(', '[', or 'NOT")
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
                "Expected 'VAR', 'IF', 'WHILE', FOR', 'FUN', int, float, identifier, '+', '-', '[', or '('" #TODO: change this error to have keywords
            ))
        
        return result.success(node)

    def statement(self): 
        result = ParseResult()
        pos_start = self.current_token.pos_start.copy()

        if self.current_token.matches(TYPE_KEYWORD, 'RETURN'): 
            result.register_advancement()
            self.advance()

            expr = result.try_register(self.expr())
            if not expr: 
                self.reverse(result.to_reverse_count)
            return result.success(ReturnNode(expr, pos_start, self.current_token.pos_end.copy()))

        if self.current_token.matches(TYPE_KEYWORD, 'CONTINUE'): 
            result.register_advancement()
            self.advance()
            return result.success(ContinueNode(pos_start, self.current_token.pos_end.copy()))

        if self.current_token.matches(TYPE_KEYWORD, 'BREAK'):
            result.register_advancement()
            self.advance()
            return result.success(BreakNode(pos_start, self.current_token.pos_end.copy()))

        expr = result.register(self.expr())
        if result.error: 
            return result.failure(InvalidSyntaxError(
                pos_start=pos_start, pos_end=self.current_token.pos_end.copy(),
                details="Expected 'RETURN', 'CONTINUE', 'BREAK', 'VAR', 'IF', 'WHILE', FOR', 'FUN', int, float, identifier, '+', '-', '[', or '('" #TODO: change this error to have keywords
            ))
        
        return result.success(expr)
    
    def statements(self): 
        result = ParseResult()
        statements = []
        pos_start = self.current_token.pos_start.copy()

        while self.current_token.type == TYPE_NEWLINE: 
            result.register_advancement()
            self.advance()

        statement = result.register(self.statement())
        if result.error: return result
        statements.append(statement)

        more_statements = True

        while True: 
            newline_count = 0
            while self.current_token.type == TYPE_NEWLINE: 
                result.register_advancement()
                self.advance()
                newline_count += 1
            if newline_count == 0:
                more_statements = False

            if not more_statements: break
            statement = result.try_register(self.statement())
            if not statement: 
                self.reverse(result.to_reverse_count)
                more_statements = False
                continue
            statements.append(statement)

        return result.success(ListNode(
            statements,
            pos_start,
            self.current_token.pos_end.copy()
        ))
    
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
        self.reset()

    def reset(self): 
        self.value = None
        self.error = None
        self.func_return_value = None
        self.loop_should_continue = False
        self.loop_should_break = False

    def register(self, result):
        if isinstance(result, RunTimeResult):
            self.error = result.error
            self.func_return_value = result.func_return_value
            self.loop_should_continue = result.loop_should_continue
            self.loop_should_break = result.loop_should_break
            return result.value
        return result

    def success(self, value):
        self.reset()
        self.value = value
        return self

    def success_return(self, value):
        self.reset()
        self.func_return_value = value
        return self
    
    def success_continue(self):
        self.reset()
        self.loop_should_continue = True
        return self
    
    def success_break(self):
        self.reset()
        self.loop_should_break = True
        return self

    def failure(self, error):
        self.reset()
        self.error = error
        return self
    
    def should_return(self): 
        return (
            self.error or
            self.func_return_value or 
            self.loop_should_continue or
            self.loop_should_break
        )

class Value:
    def __init__(self):
        self.set_pos()
        self.set_context()

    def set_pos(self, pos_start: Position = None, pos_end: Position = None):
        self.pos_start = pos_start
        self.pos_end = pos_end
        return self
    
    def set_context(self, context=None):
        self.context = context
        return self
    
    def added_to(self, other): 
        return None, self.illegal_operation(other)
        
    def subract_by(self, other): 
        return None, self.illegal_operation(other)
        
    def multiply_by(self, other):
        return None, self.illegal_operation(other)
        
    def divide_by(self, other):
       return None, self.illegal_operation(other)
        
    def mod_by(self, other): 
       return None, self.illegal_operation(other)
        
    def power_by(self, other): 
        return None, self.illegal_operation(other)
        
    def get_comparison_eq(self, other):
        return None, self.illegal_operation(other)
        
    def get_comparison_ne(self, other):
        return None, self.illegal_operation(other)
        
    def get_comparison_lt(self, other):
        return None, self.illegal_operation(other)
        
    def get_comparison_gt(self, other):
        return None, self.illegal_operation(other)
        
    def get_comparison_lte(self, other):
        return None, self.illegal_operation(other)
        
    def get_comparison_gte(self, other):
        return None, self.illegal_operation(other)
        
    def and_by(self, other):
        return None, self.illegal_operation(other)
        
    def or_by(self, other): 
        return None, self.illegal_operation(other)
        
    def notted(self): 
        return None, self.illegal_operation()
    
    def execute(self): 
        return RunTimeResult().failure(self.illegal_operation())
    
    def copy(self): 
        raise Exception('No copy method defined')
    
    def is_true(self): 
        return False
    
    def illegal_operation(self, other=None):
        if not other: other = self
        return RuntimeError(
            self.pos_start, self.pos_end,
            'Illegal operation',
            self.context
        )

class Number(Value): 
    def __init__(self, value):
        super().__init__()
        self.value = value
    
    def added_to(self, other): 
        if isinstance(other, Number):
            return Number(self.value + other.value).set_context(self.context), None
        else: 
            return None, Value.illegal_operation(self.pos_start, other.pos_end)
        
    def subract_by(self, other): 
        if isinstance(other, Number):
            return Number(self.value - other.value).set_context(self.context), None
        else: 
            return None, Value.illegal_operation(self.pos_start, other.pos_end)
        
    def multiply_by(self, other):
        if isinstance(other, Number):
            return Number(self.value * other.value).set_context(self.context), None
        else: 
            return None, Value.illegal_operation(self.pos_start, other.pos_end)
        
    def divide_by(self, other):
        if isinstance(other, Number):
            if other.value == 0:
                return None, RunTimeError(other.pos_start, other.pos_end, "Division by zero", self.context)
            return Number(self.value / other.value).set_context(self.context), None
        else: 
            return None, Value.illegal_operation(self.pos_start, other.pos_end)
        
    def mod_by(self, other): 
        if isinstance(other, Number): 
            if other.value == 0: 
                return None, RunTimeError(other.pos_start, other.pos_end, "Division by zero", self.context)
            return Number(self.value % other.value).set_context(self.context), None
        else: 
            return None, Value.illegal_operation(self.pos_start, other.pos_end)
        
    def power_by(self, other): 
        if isinstance(other, Number):
            return Number(self.value ** other.value).set_context(self.context), None
        else: 
            return None, Value.illegal_operation(self.pos_start, other.pos_end)

    def get_comparison_eq(self, other):
        if isinstance(other, Number):
            return Number(int(self.value == other.value)).set_context(self.context), None
        else: 
            return None, Value.illegal_operation(self.pos_start, other.pos_end)
        
    def get_comparison_ne(self, other):
        if isinstance(other, Number):
            return Number(int(self.value != other.value)).set_context(self.context), None
        else: 
            return None, Value.illegal_operation(self.pos_start, other.pos_end)
        
    def get_comparison_lt(self, other):
        if isinstance(other, Number):
            return Number(int(self.value < other.value)).set_context(self.context), None
        else: 
            return None, Value.illegal_operation(self.pos_start, other.pos_end)
        
    def get_comparison_gt(self, other):
        if isinstance(other, Number):
            return Number(int(self.value > other.value)).set_context(self.context), None
        else: 
            return None, Value.illegal_operation(self.pos_start, other.pos_end)
        
    def get_comparison_lte(self, other):
        if isinstance(other, Number):
            return Number(int(self.value <= other.value)).set_context(self.context), None
        else: 
            return None, Value.illegal_operation(self.pos_start, other.pos_end)
        
    def get_comparison_gte(self, other):
        if isinstance(other, Number):
            return Number(int(self.value >= other.value)).set_context(self.context), None
        else: 
            return None, Value.illegal_operation(self.pos_start, other.pos_end)
        
    def and_by(self, other):
        if isinstance(other, Number):
            return Number(int(self.value and other.value)).set_context(self.context), None
        else: 
            return None, Value.illegal_operation(self.pos_start, other.pos_end)
        
    def or_by(self, other): 
        if isinstance(other, Number): 
            return Number(int(self.value or other.value)).set_context(self.context), None
        else: 
            return None, Value.illegal_operation(self.pos_start, other.pos_end)
        
    def notted(self): 
        return Number(1 if self.value == 0 else 0).set_context(self.context), None
        
    def copy(self): 
        copy = Number(self.value)
        copy.set_pos(self.pos_start, self.pos_end)
        copy.set_context(self.context)
        return copy
    
    def is_true(self): 
        return self.value != 0
        
    def __repr__(self):
        return str(self.value)

Number.null = Number(0)
Number.false = Number(0)
Number.true = Number(1)

class String(Value):
    def __init__(self, value): 
        super().__init__()
        self.value = value

    def added_to(self, other):
        if isinstance(other, String): 
            return String(self.value + other.value).set_context(self.context), None
        else: 
            return None, Value.illegal_operation(self, other)
        
    def multiply_by(self, other):
        if isinstance(other, Number): 
            return String(self.value * other.value).set_context(self.context), None
        else: 
            return None, Value.illegal_operation(self, other)
        
    def is_true(self): 
        return len(self.value) > 0
    
    def copy(self):
        copy = String(self.value)
        copy.set_pos(self.pos_start, self.pos_end)
        copy.set_context(self.context)
        return copy
    
    def __str__(self): 
        return self.value

    def __repr__(self):
        return f'"{self.value}"'

class List(Value):
    def __init__(self, elements: list):
        super().__init__()
        self.elements: list = elements

    def added_to(self, other):
        """ Appends a value to the list. """
        new_list = self.copy()
        new_list.elements.append(other)
        return new_list, None
    
    def subract_by(self, other):
        if isinstance(other, Number): 
            new_list = self.copy()
            try:
                new_list.elements.pop(other.value)
                return new_list, None
            except: 
               return None, RunTimeError(
                   other.pos_start, other.pos_end, 
                   "Element could not be removed from list because index is out of bounds.",
                   self.context
               ) 
        else: 
            return None, Value.illegal_operation(self, other)
    
    def multiply_by(self, other):
        """ Concatenates another list to this. """
        if isinstance(other, List): 
            new_list = self.copy()
            new_list.elements.extend(other.elements)
            return new_list, None
        else: 
            return None, Value.illegal_operation(self, other)
        
    def divide_by(self, other):
        if isinstance(other, Number): 
            try:
                return self.elements[other.value], None
            except: 
               return None, RunTimeError(
                   other.pos_start, other.pos_end, 
                   "Element could not be removed from list because index is out of bounds.",
                   self.context
               ) 
        else: 
            return None, Value.illegal_operation(self, other)
    
    def copy(self): 
        copy = List(self.elements)
        copy.set_pos(self.pos_start, self.pos_end)
        copy.set_context(self.context)
        return copy
    
    def __str__(self): 
        return ", ".join([str(x) for x in self.elements]) #TODO: Remove this maybe

    def __repr__(self):
        return f'[{", ".join([str(x) for x in self.elements])}]' #TODO: Change to print quotes only if string

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
            return RunTimeResult().failue(RuntimeError( #TODO: Change to syntax error maybe?
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
            return RunTimeResult().failue(RuntimeError( #TODO: Change to syntax error maybe?
                self.pos_start, self.pos_end,
                "First argument must be a list", 
                exec_context
            ))
        
        if not isinstance(index, Number): 
            return RunTimeResult().failue(RuntimeError( #TODO: Change to syntax error maybe?
                self.pos_start, self.pos_end,
                "Second argument must be a number", 
                exec_context
            ))
        
        try: 
            element = list_.elements.pop(index.value)
        except: #TODO: Add type of error here
            return RunTimeResult().failure(RuntimeError(
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
            return RunTimeResult().failue(RuntimeError( #TODO: Change to syntax error maybe?
                self.pos_start, self.pos_end,
                "First argument must be a list", 
                exec_context
            ))
        
        if not isinstance(listB, List): 
            return RunTimeResult().failue(RuntimeError( #TODO: Change to syntax error maybe?
                self.pos_start, self.pos_end,
                "Second argument must be a list", 
                exec_context
            ))
        
        listA.elements.extend(listB.elements)
        return RunTimeResult().success(Number.null)
    execute_extend.arg_names = ['listA', 'listB']

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

class Context: 
    def __init__(self, display_name, parent=None, parent_entry_pos: Position = None):
        self.display_name = display_name
        self.parent = parent
        self.parent_entry_pos: Position = parent_entry_pos
        self.symbol_table: SymbolTable = None

class SymbolTable:
    def __init__(self, parent=None):
        self.symbols = {}
        self.parent: SymbolTable = parent

    def get(self, name) -> Number: #for now only return's number 
        value = self.symbols.get(name, None)
        if value == None and self.parent:
            return self.parent.get(name)
        return value
    
    def set(self, name, value): 
        self.symbols[name] = value

    def remove(self, name): 
        del self.symbols[name]

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

        condition_value: Number = RTresult.register(self.visit(node.condition_node, context)) #TODO: Change this to boolean node once made
        if RTresult.should_return(): return RTresult

        while condition_value.is_true(): 
            RTresult.register(self.visit(node.body_node, context))
            if RTresult.should_return(): return RTresult

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