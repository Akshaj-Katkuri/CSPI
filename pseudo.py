
class Error: 
    def __init__(self, pos_start, pos_end, error_name, details):
        self.pos_start = pos_start
        self.pos_end = pos_end
        self.error_name = error_name
        self.details = details

    def as_string(self): 
        result = f'{self.error_name}: {self.details}'
        result += f'\nFile {self.pos_start.fn}, line {self.pos_start.ln + 1}'
        return result
    
class IllegalCharError(Error): 
    def __init__(self, pos_start, pos_end, details):
        super().__init__(pos_start, pos_end, 'Illegal Character', details)

class Position: 
    def __init__(self, idx, ln, col, fn, ftxt):
        self.idx = idx
        self.ln = ln
        self.col = col
        self.fn = fn
        self.ftxt = ftxt

    def advance(self, current_char):
        self.idx += 1
        self.col += 1

        if current_char == '\n':
            self.ln += 1
            self.col = 0
        
        return self
    
    def copy(self): 
        return Position(self.idx, self.ln, self.col, self.fn, self.ftxt)


TYPE_INT = 'TYPE_INT'
TYPE_FLOAT = 'TYPE_FLOAT'
TYPE_PLUS = 'TYPE_PLUS'
TYPE_MINUS = 'TYPE_MINUS'
TYPE_MUL = 'TYPE_MUL'
TYPE_DIV = 'TYPE_DIV'
TYPE_LPAREN = 'TYPE_LPAREN'
TYPE_RPAREN = 'TYPE_RPAREN'

class Token(): 
    def __init__(self, type_, value=None): 
        self.type = type_
        self.value = value

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
                tokens.append(Token(TYPE_PLUS))
                self.advance()
            elif self.current_char == '-': 
                tokens.append(Token(TYPE_MINUS))
                self.advance()
            elif self.current_char == '*':
                tokens.append(Token(TYPE_MUL))
                self.advance()
            elif self.current_char == '/':
                tokens.append(Token(TYPE_DIV))
                self.advance()
            elif self.current_char == '(':
                tokens.append(Token(TYPE_LPAREN))
                self.advance()
            elif self.current_char == ')':
                tokens.append(Token(TYPE_RPAREN))
                self.advance()
            elif self.current_char.isdigit(): 
                tokens.append(self.make_number())
            else: 
                pos_start = self.pos.copy()
                char = self.current_char
                self.advance()
                return [], IllegalCharError(pos_start, self.pos.idx, f"'{char}'")

        return tokens, None

    def make_number(self): 
        num_str = ''
        dot_count = 0 # to check if float or integer

        while self.current_char != None and (self.current_char.isdigit() or self.current_char == '.'):
            if self.current_char == '.':
                if dot_count == 1: break #TODO: implement raise error here
                dot_count += 1
                num_str += '.'
            else: 
                num_str += self.current_char
            self.advance()
            
        if dot_count == 0: 
            return Token(TYPE_INT, int(num_str))
        else: 
            return Token(TYPE_FLOAT, float(num_str))
        
def run(fn, text):
    lexer = Lexer(fn, text)
    tokens, error = lexer.make_tokens()

    return tokens, error