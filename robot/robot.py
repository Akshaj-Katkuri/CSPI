import threading
import time

from grid_runner import GridRunner
from grid_maker import GridMaker

class Robot: 
    def __init__(self):
        self.making = False
        self.running = False
        self.grid_runner: GridRunner = GridRunner()
    
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
        while True: 
            self.grid_runner.update_display()

'''Other code below this for example'''

robot = Robot()
robot.create_grid()

while True: 
    print('now that it is threading, it should still be active as this is going on')
    time.sleep(2)
