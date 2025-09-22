from lexer.tokens import *
from utils.errors import InvalidSyntaxError, EndOfFile
from utils.results import ParseResult
from parser.nodes import *

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
        result = self.statements(initial=True)
        if not result.error and self.current_token.type != TYPE_EOF:
            return result.failure(InvalidSyntaxError(
                self.current_token.pos_start, self.current_token.pos_end, 
                "Expected '+', '-', '*', or '/'"
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

        if self.current_token.type != TYPE_LPAREN: 
            return result.failure(InvalidSyntaxError(
                self.current_token.pos_start, self.current_token.pos_end, 
                "Expected '('"
            ))

        result.register_advancement()
        self.advance()

        condition = result.register(self.expr())
        if result.error: return result

        if self.current_token.type != TYPE_RPAREN: 
            return result.failure(InvalidSyntaxError(
                self.current_token.pos_start, self.current_token.pos_end, 
                "Expected ')'"
            ))

        result.register_advancement()
        self.advance()

        while self.current_token.type == TYPE_NEWLINE:
            result.register_advancement()
            self.advance()

        if self.current_token.type != TYPE_LCURL: 
            return result.failure(InvalidSyntaxError(
                self.current_token.pos_start, self.current_token.pos_end, 
                "Expected '{'"
            ))

        result.register_advancement()
        self.advance()

        statements = result.register(self.statements())
        if result.error: return result
        cases.append((condition, statements, True))

        if self.current_token.type != TYPE_RCURL: 
            return result.failure(InvalidSyntaxError(
                self.current_token.pos_start, self.current_token.pos_end, 
                "Expected '}'"
            ))

        result.register_advancement()
        self.advance()

        while self.current_token.type == TYPE_NEWLINE:
            result.register_advancement()
            self.advance()

        if self.current_token.matches(TYPE_KEYWORD, 'ELIF'):
            all_cases = result.register(self.elif_expr())
            if result.error: return result
            new_cases, else_case = all_cases
            cases.extend(new_cases)
        elif self.current_token.matches(TYPE_KEYWORD, 'ELSE'):
            else_case = result.register(self.else_expr())
            if result.error: return result

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

            while self.current_token.type == TYPE_NEWLINE:
                result.register_advancement()
                self.advance()

            if self.current_token.type != TYPE_LCURL: 
                return result.failure(InvalidSyntaxError(
                    self.current_token.pos_start, self.current_token.pos_end, 
                    "Expected '{'"
                ))

            result.register_advancement()
            self.advance()

            statements = result.register(self.statements())
            if result.error: return result
            else_case = (statements, True)

            if self.current_token.type != TYPE_RCURL: 
                return result.failure(InvalidSyntaxError(
                    self.current_token.pos_start, self.current_token.pos_end, 
                    "Expected '}'"
                ))
            
            result.register_advancement()
            self.advance()

        return result.success(else_case)
    
    def for_expr(self): 
        result = ParseResult()

        if not self.current_token.matches(TYPE_KEYWORD, 'FOR'): 
            return result.failure(InvalidSyntaxError(
                self.current_token.pos_start, self.current_token.pos_end, 
                "Expected 'FOR'"
            ))
        
        result.register_advancement()
        self.advance()

        if not self.current_token.matches(TYPE_KEYWORD, 'EACH'): 
            return result.failure(InvalidSyntaxError(
                self.current_token.pos_start, self.current_token.pos_end, 
                "Expected 'EACH'"
            ))
        
        result.register_advancement()
        self.advance()

        if self.current_token.type != TYPE_IDENTIFIER: 
            return result.failure(InvalidSyntaxError(
                self.current_token.pos_start, self.current_token.pos_end, 
                "Expected identifier"
            ))
        
        var_name = self.current_token
        result.register_advancement()
        self.advance()

        if not self.current_token.matches(TYPE_KEYWORD, 'IN'):
            return result.failure(InvalidSyntaxError(
                self.current_token.pos_start, self.current_token.pos_end,
                "Expected 'IN'"
            ))
        
        result.register_advancement()
        self.advance()

        if self.current_token.type != TYPE_IDENTIFIER: #TODO: Add list expr here too
            return result.failure(InvalidSyntaxError(
                self.current_token.pos_start, self.current_token.pos_end,
                "Expected identifier" #TODO: or list expr in error message
            ))
        
        list_node = VariableAccessNode(self.current_token)
        result.register_advancement()
        self.advance()
        
        while self.current_token.type == TYPE_NEWLINE:
            result.register_advancement()
            self.advance()

        if self.current_token.type != TYPE_LCURL:
            return result.failure(InvalidSyntaxError(
                self.current_token.pos_start, self.current_token.pos_end, 
                "Expected '{'"
            ))
        
        result.register_advancement()
        self.advance()

        body_node = result.register(self.statements())
        if result.error: return result

        if self.current_token.type != TYPE_RCURL: 
            return result.failure(InvalidSyntaxError(
                self.current_token.pos_start, self.current_token.pos_end, 
                "Expected '}'"
            ))
        
        result.register_advancement()
        self.advance()
        
        return result.success(ForNode(
                var_name_token=var_name, list_node=list_node, body_node=body_node, should_return_null=True
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

        if self.current_token.type != TYPE_LPAREN: 
            return result.failure(InvalidSyntaxError(
                self.current_token.pos_start, self.current_token.pos_end, 
                "Expected '('"
            ))
        
        result.register_advancement()
        self.advance()

        condition = result.register(self.expr())
        if result.error: return result

        if self.current_token.type != TYPE_RPAREN: 
            return result.failure(InvalidSyntaxError(
                self.current_token.pos_start, self.current_token.pos_end, 
                "Expected ')'"
            ))
        
        result.register_advancement()
        self.advance()

        while self.current_token.type == TYPE_NEWLINE: 
            result.register_advancement()
            self.advance()

        if self.current_token.type != TYPE_LCURL: 
            return result.failure(InvalidSyntaxError(
                self.current_token.pos_start, self.current_token.pos_end, 
                "Expected '{'"
            ))
        
        result.register_advancement()
        self.advance()

        body = result.register(self.statements())
        if result.error: return result

        if self.current_token.type != TYPE_RCURL: 
            return result.failure(InvalidSyntaxError(
                self.current_token.pos_start, self.current_token.pos_end, 
                "Expected '}'"
            ))
        
        result.register_advancement()
        self.advance()

        return result.success(WhileNode(
            condition, body, True
        ))
    
    def repeat_expr(self): 
        result = ParseResult()

        if not self.current_token.matches(TYPE_KEYWORD, 'REPEAT'):
            return result.failure(InvalidSyntaxError(
                self.current_token.pos_start, self.current_token.pos_end,
                "Expected 'REPEAT'"
            ))
        
        result.register_advancement()
        self.advance()
        
        if self.current_token.matches(TYPE_KEYWORD, 'UNTIL'):
            result.register_advancement()
            self.advance()

            if self.current_token.type != TYPE_LPAREN:
                return result.failure(InvalidSyntaxError(
                    self.current_token.pos_start, self.current_token.pos_end, 
                    "Expected '('"
                ))
            
            result.register_advancement()
            self.advance()

            condition = result.register(self.expr())
            if result.error: return result

            if self.current_token.type != TYPE_RPAREN:
                return result.failure(InvalidSyntaxError(
                    self.current_token.pos_start, self.current_token.pos_end, 
                    "Expected ')'"
                ))
            
            result.register_advancement()
            self.advance()

            while self.current_token.type == TYPE_NEWLINE: 
                result.register_advancement()
                self.advance()

            if self.current_token.type != TYPE_LCURL:
                return result.failure(InvalidSyntaxError(
                    self.current_token.pos_start, self.current_token.pos_end, 
                    "Expected '{'"
                ))
            
            result.register_advancement()
            self.advance()

            body = result.register(self.statements())
            if result.error: 
                return result

            if self.current_token.type != TYPE_RCURL: 
                return result.failure(InvalidSyntaxError(
                    self.current_token.pos_start, self.current_token.pos_end, 
                    "Expected '}'"
                ))
            
            result.register_advancement()
            self.advance()

            return result.success(RepeatUntilNode(
                condition, body, True
            ))
        else:
            if self.current_token.type != TYPE_INT:
                return result.failure(InvalidSyntaxError(
                    self.current_token.pos_start, self.current_token.pos_end, 
                    "Expected 'UNTIL' or int"
                ))
            
            count = self.current_token

            result.register_advancement()
            self.advance()

            if not self.current_token.matches(TYPE_KEYWORD, 'TIMES'):
                return result.failure(InvalidSyntaxError(
                    self.current_token.pos_start, self.current_token.pos_end, 
                    "Expected 'TIMES'"
                ))
            
            result.register_advancement()
            self.advance()

            while self.current_token.type == TYPE_NEWLINE: 
                result.register_advancement()
                self.advance()

            if self.current_token.type != TYPE_LCURL: 
                return result.failure(InvalidSyntaxError(
                    self.current_token.pos_start, self.current_token.pos_end, 
                    "Expected '{'"
                ))
            
            result.register_advancement()
            self.advance()

            body = result.register(self.statements())
            if result.error: return result

            if self.current_token.type != TYPE_RCURL:
                return result.failure(InvalidSyntaxError(
                    self.current_token.pos_start, self.current_token.pos_end, 
                    "Expected '}'"
                ))
            
            result.register_advancement()
            self.advance()

            return result.success(RepeatNode(
                count_token=count, body_node=body, should_return_null=True
            ))

    def func_def(self): 
        result = ParseResult()

        if not self.current_token.matches(TYPE_KEYWORD, 'PROCEDURE'): 
            return result.failure(InvalidSyntaxError(
                self.current_token.pos_start, self.current_token.pos_end, 
                "Expected 'PROCEDURE'"
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
                result.register_advancement()
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
        
        while self.current_token.type == TYPE_NEWLINE: 
            result.register_advancement()
            self.advance()
        
        if self.current_token.type != TYPE_LCURL:
            return result.failure(InvalidSyntaxError(
                self.current_token.pos_start, self.current_token.pos_end, 
                "Expected '{'"
            ))

        result.register_advancement()
        self.advance()

        body_node = result.register(self.statements())
        if result.error: return result

        if self.current_token.type != TYPE_RCURL:
            return result.failure(InvalidSyntaxError(
                self.current_token.pos_start, self.current_token.pos_end,
                "Expected '}'"
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
                "Expected ']', int, float, identifier, expression, '[', or '('"
            ))

        while self.current_token.type == TYPE_COMMA: 
            result.register_advancement()
            self.advance()

            element_nodes.append(result.register(self.expr()))
            if result.error: return result

        if self.current_token.type != TYPE_RSQUARE: 
            return result.failure(InvalidSyntaxError(
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
        
        elif token.matches(TYPE_KEYWORD, 'REPEAT'):
            repeat_expr = result.register(self.repeat_expr())
            if result.error: return result
            return result.success(repeat_expr)
        
        elif token.matches(TYPE_KEYWORD, 'PROCEDURE'): 
            func_def = result.register(self.func_def())
            if result.error: return result
            return result.success(func_def)
        
        elif token.type == TYPE_EOF:
            result.register_advancement() # Fake registering advancement, so this error isn't overwritten during propogation
            return result.failure(EndOfFile(token.pos_start, token.pos_end, "Reached end of file"))

        return result.failure(InvalidSyntaxError(
            token.pos_start, token.pos_end, "Expected int, float, identifier, '[', '(', or expression"
        ))

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
                        "Expected ')', int, float, identifier, or expression"
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
                "Expected int, float, identifier, '+', '-', '(', '[', or 'NOT')" #TODO: add keywords
            ))

        return result.success(node)

    def expr(self): 
        result = ParseResult()
        
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
                "Expected int, float, identifier, '+', '-', '[', '(', or 'NOT'"
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
                details="Expected 'RETURN', 'CONTINUE', 'BREAK', 'IF', 'WHILE', FOR', 'PROCEDURE', int, float, identifier, '+', '-', '[', '(', or 'NOT'"
            ))
        
        return result.success(expr)
    
    def statements(self, initial=False): 
        result = ParseResult()
        statements = []
        pos_start = self.current_token.pos_start.copy()

        while self.current_token.type == TYPE_NEWLINE: 
            result.register_advancement()
            self.advance()

        statement = result.register(self.statement())
        if result.error: 
            if isinstance(result.error, EndOfFile) and initial:
                result.last_registered_advance_count = 0
                return result.failure(InvalidSyntaxError(
                    result.error.pos_start, result.error.pos_end,
                    "Expected 'int, float, identifier, procedure call, or expression'"
                ))
            return result
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
            if initial: 
                statement = result.try_eof_register(self.statement())
                if result.error: 
                    while self.current_token.type == TYPE_NEWLINE:
                        result.register_advancement()
                        self.advance()
                    if self.current_token.type == TYPE_EOF:
                        statement = None
                    else: 
                        return result
            else: 
                statement = result.try_register(self.statement())
                # if result.error and not isinstance(result.error, EndOfFile): 
                #     if result.last_registered_advance_count != 0: 
                #         return result
                #     else: 
                #         statement = None
                # elif isinstance(result.error, EndOfFile):
                #     statement = None
                #     result.error = None

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
