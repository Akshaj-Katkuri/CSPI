import threading
import time
import os
import shutil

from robot.grid.grid_runner import GridRunner
from robot.grid.grid_maker import GridMaker
from robot.robot_commands import RobotCommands

from utils.results import RunTimeResult
from utils.errors import GridError
from values import Number, Boolean

class Robot: 
    def __init__(self):
        self.making = False
        self.grid_created = False
        self.running = False
        self.grid_runner = None
        self.thread = None
        # Event used to request the loop thread to stop
        self._stop_event = threading.Event()
        # JSON files are stored in the `grid` subfolder; pass that relative path
        self.commands = RobotCommands(os.path.join("grid", "current_grid.json"))
    
    def create_grid(self): 
        RTresult = RunTimeResult()
        
        self.making = True

        RTresult.register(GridMaker().run())
        if RTresult.error: return RTresult
        
        self.making = False

        base = os.path.dirname(__file__)
        src = os.path.join(base, "grid", "initial_grid.json")
        dst = os.path.join(base, "grid", "current_grid.json")
        try:
            if os.path.exists(src):
                shutil.copyfile(src, dst)
        except Exception as e:
            print(f"Warning: failed to copy initial grid to current_grid.json: {e}")

        self.grid_created = True
        self.start_grid()

        return RTresult.success(Number.null)
    
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
        if self.running: 
            result: str = self.commands.move_forward()
            if result is None: 
                return RunTimeResult().success(Number.null)
            elif result.upper() == "OUT OF BOUNDS": 
                return RunTimeResult().failure(GridError(details="Robot is trying to move out of bounds."))
            elif result.upper() == "WALL":
                return RunTimeResult().failure(GridError(details="Robot ran into a wall."))
            elif result.upper() == "GOAL": 
                print("Robot has reached the goal!")
                return RunTimeResult().success(Number.null)
            else:
                return RunTimeResult().success(Number.null)
        elif not self.grid_created:
            return RunTimeResult().failure(GridError(details="Grid has not yet been created. To create the grid, try calling the function 'CREATE_GRID()' at beginning of the file. "))
        else: 
            return RunTimeResult().failure(GridError(details='User closed grid runner'))

    def turn_left(self): 
        if self.running: 
            self.commands.turn_left()
            return RunTimeResult().success(Number.null)
        elif not self.grid_created:
            return RunTimeResult().failure(GridError(details="Grid has not yet been created. To create the grid, try calling the function 'CREATE_GRID()' at beginning of the file. "))
        else: 
            return RunTimeResult().failure(GridError(details='User closed grid runner'))

    def turn_right(self): 
        if self.running: 
            self.commands.turn_right()
            return RunTimeResult().success(Number.null)
        elif not self.grid_created:
            return RunTimeResult().failure(GridError(details="Grid has not yet been created. To create the grid, try calling the function 'CREATE_GRID()' at beginning of the file. "))
        else: 
            return RunTimeResult().failure(GridError(details='User closed grid runner'))

    def can_move(self, direction) -> bool: 
        if self.running: 
            return RunTimeResult().success(Boolean(self.commands.can_move(direction)))
        elif not self.grid_created:
            return RunTimeResult().failure(GridError(details="Grid has not yet been created. To create the grid, try calling the function 'CREATE_GRID()' at beginning of the file. "))
        else: 
            return RunTimeResult().failure(GridError(details='User closed grid runner'))
        


if __name__ == '__main__': 
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
