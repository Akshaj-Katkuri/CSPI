from lexer.tokens import Token

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

class RepeatUntilNode:
    def __init__(self, condition_node, body_node, should_return_null):
        self.condition_node = condition_node
        self.body_node = body_node
        self.should_return_null = should_return_null

        self.pos_start = condition_node.pos_start
        self.pos_end = body_node.pos_end

class RepeatNode:
    def __init__(self, count_token, body_node, should_return_null):
        self.count_token = count_token
        self.body_node = body_node
        self.should_return_null = should_return_null

        self.pos_start = count_token.pos_start
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
