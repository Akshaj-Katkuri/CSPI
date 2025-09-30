import os
import sys
import subprocess
import json
import threading
from typing import Optional

running = False
_runner_proc: Optional[subprocess.Popen] = None
# Lock to serialize runner start/stop calls from multiple threads
_proc_lock = threading.Lock()


def CREATE_GRID(path: str = "grid.json", rows: int = 6, cols: int = 6) -> Optional[subprocess.Popen]:
    """Create or edit a grid using the grid editor, then start the grid runner.

    Steps:
    - Try to import and run GridEditor from `robot.grid_maker` in-process (so the caller
      stays in the same Python process). If that import fails, fall back to launching
      the `grid_maker.py` script as a subprocess.
    - After the editor finishes (user pressed Confirm), start `grid_runner.py` as a
      subprocess which will monitor the JSON file and display the read-only runner.

    Returns the subprocess.Popen for the runner (or None if runner failed to start).
    """
    base = os.path.dirname(__file__)
    json_path = os.path.join(base, path)

    # 1) Launch editor (prefer in-process for nicer integration)
    GridEditor = None
    try:
        from robot.grid_maker import GridEditor  # preferred when package-importing
    except Exception:
        try:
            # fallback to local script import
            from grid_maker import GridEditor
        except Exception:
            GridEditor = None

    if GridEditor:
        editor = GridEditor(path=json_path, rows=rows, cols=cols)
        editor.run()
    else:
        # fallback to running the script externally
        try:
            subprocess.run([sys.executable, os.path.join(base, "grid_maker.py")], check=False)
        except Exception as e:
            print("Failed to launch grid_maker.py:", e)

    # 2) After confirm, ensure the runner is running to watch the JSON file
    return ensure_runner_running(path=path)


def run_grid_runner(path: str = "grid.json") -> Optional[subprocess.Popen]:
    """Start the `grid_runner.py` script as a subprocess and return the Popen object.
    The runner reloads when the JSON file changes, so we run it as a separate process.
    """
    global running, _runner_proc
    base = os.path.dirname(__file__)
    runner_script = os.path.join(base, "grid_runner.py")
    # Guard start with a lock to avoid races
    with _proc_lock:
        # If we started a runner previously and it's still running, reuse it.
        if _runner_proc is not None:
            try:
                if _runner_proc.poll() is None:  # still running
                    return _runner_proc
            except Exception:
                # If poll fails for some reason, continue and try to start a fresh process
                pass

        try:
            proc = subprocess.Popen([sys.executable, runner_script], cwd=base)
            running = True
            _runner_proc = proc
            return proc
        except Exception as e:
            print("Failed to start grid_runner.py:", e)
            return None


def ensure_runner_running(path: str = "grid.json") -> Optional[subprocess.Popen]:
    """Ensure a single runner process is running and return it.

    This will not start a new process if one we started earlier is still alive.
    """
    global running, _runner_proc
    with _proc_lock:
        if _runner_proc is not None:
            try:
                if _runner_proc.poll() is None:
                    running = True
                    return _runner_proc
            except Exception:
                _runner_proc = None

        return run_grid_runner(path=path)


def stop_runner():
    """Stop the runner subprocess if it was started by this module."""
    global running, _runner_proc
    with _proc_lock:
        if _runner_proc:
            try:
                _runner_proc.terminate()
            except Exception:
                pass
            _runner_proc = None
        running = False


def TURN_LEFT(path: str = "grid.json") -> str:
    """Rotate the turtle left by adding 90 degrees to the numeric value in the grid JSON.

    The grid JSON represents the turtle rotation as a numeric degree value in the
    corresponding cell (other non-empty cells use 'Wall' or 'Goal'). This function
    finds the first numeric cell (the turtle) and adds 90 degrees modulo 360.

    Returns the path to the JSON file written.
    """
    base = os.path.dirname(__file__)
    file_path = os.path.join(base, path)

    try:
        with open(file_path, "r") as f:
            data = json.load(f)
    except Exception as e:
        raise RuntimeError(f"Failed to read {file_path}: {e}")

    found = False
    for r, row in enumerate(data):
        for c, cell in enumerate(row):
            if isinstance(cell, (int, float)):
                new_deg = (int(cell) + 90) % 360
                data[r][c] = new_deg
                found = True
                break
        if found:
            break

    if not found:
        raise RuntimeError("No turtle rotation value found in grid JSON")

    with open(file_path, "w") as f:
        json.dump(data, f, indent=2)

    return file_path


def start():
    """Compatibility helper that starts the editor then runner with default names."""
    return create_grid()