import threading
import time
import os
import sys
import shutil
import signal
import subprocess
import pickle
from pathlib import Path

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

        self.halt()
        self.grid_runner = None

        self.making = True

        project_root = (
            Path(__file__).parent.parent
        )  # first parent: robot, second parent: CSPI, which is where entry point is
        module_name = "robot.grid.grid_maker"
        subprocess.run([sys.executable, "-m", module_name], cwd=project_root)

        path = Path("grid_output.pkl")
        with path.open("rb") as f:
            output = pickle.load(f)
        RTresult.register(output)
        if RTresult.error:
            return RTresult

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
            self.thread = threading.Thread(target=self.start_subprocess_for_runner)
            self.thread.start()

    def start_subprocess_for_runner(self):
        project_root = (
            Path(__file__).parent.parent
        )  # first parent: robot, second parent: CSPI, which is where entry point is
        module_name = "robot.grid.grid_runner"
        self.grid_proc = subprocess.Popen(
            [sys.executable, "-m", module_name],
            cwd=project_root,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        stdout, stderr = self.grid_proc.communicate()

        self.running = True

    def halt(self):
        try:
            self.grid_proc.send_signal(sig=signal.SIGBREAK)
            self._stop_event.set()
            if self.thread is not None and self.thread.is_alive():
                self.thread.join(timeout=2)
            self.running = False
        except:
            pass

    def move_forward(self):
        RTresult = RunTimeResult()

        if self.running:
            result = RTresult.register(self.commands.move_forward())
            if RTresult.error:
                return RTresult

            if result is None:
                return RTresult.success(Number.null)
            elif result == "GOAL":
                print("Robot has reached the goal!")

            return RTresult.success(Number.null)

        elif not self.grid_created:
            return RTresult.failure(
                GridError(
                    details="Grid has not yet been created. To create the grid, try calling the function 'CREATE_GRID()' at beginning of the file. "
                )
            )
        else:
            return RTresult.failure(GridError(details="User closed grid runner"))

    def rotate_left(self):
        if self.running:
            self.commands.rotate_left()
            return RunTimeResult().success(Number.null)
        elif not self.grid_created:
            return RunTimeResult().failure(
                GridError(
                    details="Grid has not yet been created. To create the grid, try calling the function 'CREATE_GRID()' at beginning of the file. "
                )
            )
        else:
            return RunTimeResult().failure(GridError(details="User closed grid runner"))

    def rotate_right(self):
        if self.running:
            self.commands.rotate_right()
            return RunTimeResult().success(Number.null)
        elif not self.grid_created:
            return RunTimeResult().failure(
                GridError(
                    details="Grid has not yet been created. To create the grid, try calling the function 'CREATE_GRID()' at beginning of the file. "
                )
            )
        else:
            return RunTimeResult().failure(GridError(details="User closed grid runner"))

    def can_move(self, direction) -> bool:
        if self.running:
            return RunTimeResult().success(Boolean(self.commands.can_move(direction)))
        elif not self.grid_created:
            return RunTimeResult().failure(
                GridError(
                    details="Grid has not yet been created. To create the grid, try calling the function 'CREATE_GRID()' at beginning of the file. "
                )
            )
        else:
            return RunTimeResult().failure(GridError(details="User closed grid runner"))


if __name__ == "__main__":
    robot = Robot()
    robot.create_grid()

    control = None

    while True:
        control = int(input("Enter a command: "))

        time.sleep(2)

        if control == 1:
            robot.move_forward()
        elif control == 2:
            robot.rotate_left()
        elif control == 3:
            robot.rotate_right()
        elif control == 4:
            dir = input("Direction: ").upper()
        elif control == 0:
            robot.halt()
            break
