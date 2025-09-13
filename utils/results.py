from utils.errors import EndOfFile


class ParseResult: 
    def __init__(self):
        self.error = None
        self.node = None
        self.last_registered_advance_count = 0
        self.advance_count = 0
        self.to_reverse_count = 0

    def register_advancement(self): 
        self.last_registered_advance_count = 1
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
    
    def try_eof_register(self, result): 
        if result.error and isinstance(result.error, EndOfFile): 
            self.to_reverse_count = result.advance_count
            return None
        return self.register(result)

    def success(self, node): 
        self.node = node
        return self

    def failure(self, error): 
        if not self.error or self.last_registered_advance_count == 0:
            self.error = error
        return self

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
