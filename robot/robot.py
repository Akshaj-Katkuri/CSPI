import threading
import time
import os
import shutil

from grid_runner import GridRunner
from grid_maker import GridMaker
from robot_commands import RobotCommands

class Robot: 
    def __init__(self):
        self.making = False
        self.running = False
        self.grid_runner = None
        self.commands = RobotCommands("current_grid.json")
    
    def create_grid(self): 
        self.making = True
        GridMaker().run()
        self.making = False

        base = os.path.dirname(__file__)
        src = os.path.join(base, "initial_grid.json")
        dst = os.path.join(base, "current_grid.json")
        try:
            if os.path.exists(src):
                shutil.copyfile(src, dst)
        except Exception as e:
            print(f"Warning: failed to copy initial grid to current_grid.json: {e}")

        self.start_grid()
    
    def start_grid(self): 
        if not self.running and not self.making:
            self.running = True
            threading.Thread(target=self.loop).start()

    def loop(self): 
        if self.grid_runner is None: 
            self.grid_runner = GridRunner()
        try:
            while True:
                self.grid_runner.update_display()
                # time.sleep(2)
        except RuntimeError as e:
            print(f"Grid Runner Error: {e}")
            self.grid_runner.close()
            self.running = False

    def halt(self): 
        self.grid_runner.close()
        self.running = False

    def move_forward(self): 
        self.commands.move_forward()

    def turn_left(self): 
        self.commands.turn_left()

    def turn_right(self): 
        self.commands.turn_right()

    def can_move(self, direction) -> bool: 
        return self.commands.can_move(direction)


robot = Robot()
robot.create_grid()

control = None

while True: 
    control = int(input("Enter a command: "))

    time.sleep(2)

    if control == 1: 
        robot.move_forward()
    elif control == 2: 
        robot.turn_left()
    elif control == 3: 
        robot.turn_right()
    elif control == 4: 
        dir = input("Direction: ").upper()
        print(robot.can_move(dir))
    elif control == 0: 
        robot.halt()
        break
