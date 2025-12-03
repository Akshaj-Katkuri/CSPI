import threading
import time

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

    def move_forward(self): 
        self.commands.move_forward()

'''Other code below this for example'''

robot = Robot()
robot.create_grid()

control = None

while True: 
    control = int(input("Enter a command: "))
    if control == 1: 
        robot.move_forward()
