from utils.position import Position
from lexer.tokens import *
from utils.errors import IllegalCharError, ExpectedCharacterError

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
            elif self.current_char == '#':
                self.skip_comment()
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

    def skip_comment(self): 
        self.advance() # Advance past the '#'

        while self.current_char != '\n': 
            self.advance()

        self.advance() # Advance past the new line
    
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