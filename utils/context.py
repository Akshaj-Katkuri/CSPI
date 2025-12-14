from utils.position import Position


class Context: 
    def __init__(self, display_name, parent=None, parent_entry_pos: Position = None):
        self.display_name = display_name
        self.parent = parent
        self.parent_entry_pos: Position = parent_entry_pos
        self.symbol_table: 'SymbolTable' = None
        # Delay importing/creating Robot to avoid circular imports. Create on first access.
        self._robot = None

    @property
    def robot(self):
        if self._robot is None:
            # Local import to avoid circular import at module import time
            from robot.robot import Robot
            self._robot = Robot()
        return self._robot

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
