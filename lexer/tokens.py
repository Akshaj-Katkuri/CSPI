from utils.position import Position

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
TYPE_LSQUARE = 'LSQUARE' # [
TYPE_RSQUARE = 'RSQUARE' # ]
TYPE_LCURL = 'LCURL' # {
TYPE_RCURL = 'RCURL' # }
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
    'TRUE',
    'FALSE',
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
    'EACH',
    'IN',
    'WHILE',
    'REPEAT',
    'UNTIL',
    'TIMES',
    'TO',
    'PROCEDURE',
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