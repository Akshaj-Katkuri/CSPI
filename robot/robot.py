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
        self.thread = None
        # Event used to request the loop thread to stop
        self._stop_event = threading.Event()
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
            # Clear any previous stop request and start a background thread
            self._stop_event.clear()
            self.thread = threading.Thread(target=self.loop)
            self.thread.start()

    def loop(self): 
        if self.grid_runner is None: 
            self.grid_runner = GridRunner()
        try:
            # Run until a stop is requested or GridRunner signals shutdown
            while not self._stop_event.is_set():
                try:
                    self.grid_runner.update_display()
                except RuntimeError:
                    # Propagate to outer handler so we can clean up
                    raise
        except RuntimeError as e:
            print(f"Grid Runner Error: {e}")
            self.grid_runner.close()
            self.running = False
        finally:
            # Ensure running flag is cleared when loop exits
            self.running = False

    def halt(self): 
        # Signal the loop thread to stop
        try:
            self._stop_event.set()
            # Close the grid runner (safe to call even if None)
            if self.grid_runner is not None:
                self.grid_runner.close()
            # Join the thread to ensure it has exited
            if self.thread is not None and self.thread.is_alive():
                self.thread.join(timeout=2)
        finally:
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
