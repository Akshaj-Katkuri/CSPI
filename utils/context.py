from utils.position import Position
from robot.robot import Robot

class Context: 
    def __init__(self, display_name, parent=None, parent_entry_pos: Position = None):
        self.display_name = display_name
        self.parent = parent
        self.parent_entry_pos: Position = parent_entry_pos
        self.symbol_table: SymbolTable = None
        self.robot: Robot = Robot()

class SymbolTable:
    def __init__(self, parent=None):
        self.symbols = {}
        self.parent: SymbolTable = parent

    def get(self, name):
        value = self.symbols.get(name, None)
        if value == None and self.parent:
            return self.parent.get(name)
        return value
    
    def set(self, name, value): 
        self.symbols[name] = value

    def remove(self, name): 
        del self.symbols[name]
