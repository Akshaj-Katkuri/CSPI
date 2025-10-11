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


def CREATE_GRID(path: str = "grid.json", rows: int = 6, cols: int = 6, *, use_subprocess_editor: bool = True) -> Optional[subprocess.Popen]:
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

    # 1) Launch editor. Start it non-blocking and spawn a watcher thread that
    # waits for the editor process to exit (user pressed Confirm) and then
    # starts the runner. This allows the interpreter to continue running.
    editor_proc = None
    if use_subprocess_editor:
        try:
            editor_proc = subprocess.Popen([sys.executable, os.path.join(base, "grid_maker.py")], cwd=base)
        except Exception as e:
            print("Failed to launch grid_maker.py as subprocess:", e)
    else:
        # run in-process (blocking) on a background thread so CREATE_GRID
        # itself can return immediately while still waiting for the editor
        # to finish before starting the runner.
        GridEditor = None
        try:
            from robot.grid_maker import GridEditor  # preferred when package-importing
        except Exception:
            try:
                from grid_maker import GridEditor
            except Exception:
                GridEditor = None

        if GridEditor:
            def _run_editor_in_thread():
                try:
                    editor = GridEditor(path=json_path, rows=rows, cols=cols)
                    editor.run()
                finally:
                    # after in-process editor finishes, ensure runner
                    print("in-process editor thread: editor.run() returned")
                    ensure_runner_running(path=path)

            t = threading.Thread(target=_run_editor_in_thread, daemon=True)
            t.start()
        else:
            try:
                editor_proc = subprocess.Popen([sys.executable, os.path.join(base, "grid_maker.py")], cwd=base)
            except Exception as e:
                print("Failed to launch grid_maker.py:", e)

    # Spawn watcher thread which waits for editor_proc to exit, then starts runner.
    def _watch_editor_and_start_runner(proc):
        try:
            if proc is not None:
                print(f"watcher: waiting for editor pid={getattr(proc, 'pid', None)}")
                proc.wait()
                print(f"watcher: editor pid={getattr(proc, 'pid', None)} exited with code={proc.returncode}")
        except Exception:
            pass
        # Now the editor has exited (or we couldn't wait). Ensure runner is running.
        print("watcher: ensuring runner is running")
        ensure_runner_running(path=path)

    if editor_proc is not None:
        threading.Thread(target=_watch_editor_and_start_runner, args=(editor_proc,), daemon=True).start()

    # Do not start the runner synchronously here. The watcher thread will
    # start the runner after the editor exits (user pressed Confirm). Return
    # immediately so the interpreter can continue. Return the editor_proc so
    # caller can inspect it if desired; if a runner is already running, return it.
    with _proc_lock:
        if _runner_proc is not None and _runner_proc.poll() is None:
            print(f"CREATE_GRID: runner already running pid={_runner_proc.pid}")
            return _runner_proc

    if editor_proc is not None:
        print(f"CREATE_GRID: started editor subprocess pid={editor_proc.pid}")
        return editor_proc

    print("CREATE_GRID: no editor process started; returning None")
    return None


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
                    print(f"run_grid_runner: reusing runner pid={_runner_proc.pid}")
                    return _runner_proc
            except Exception:
                # If poll fails for some reason, continue and try to start a fresh process
                pass

        try:
            creationflags = 0
            kwargs = {}
            # On Windows, create a new console and detach the child so it doesn't
            # hold or interfere with the caller's terminal. Redirect stdio so the
            # parent's console remains usable.
            if os.name == 'nt':
                # Use cmd "start" so the process opens in a new console window and
                # the command returns immediately. We supply an empty title argument
                # (""") to avoid the first quoted argument being treated as the
                # window title.
                cmd = ["cmd", "/c", "start", "", sys.executable, runner_script]
                print(f"run_grid_runner: launching (Windows start) {cmd} (cwd={base})")
                proc = subprocess.Popen(cmd, cwd=base, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                # Note: proc.pid will be the PID of the cmd.exe starter, not the final python.
            else:
                # On POSIX, start a new session to detach from parent terminal.
                kwargs['start_new_session'] = True
                print(f"run_grid_runner: launching runner script {runner_script} (cwd={base})")
                proc = subprocess.Popen([sys.executable, runner_script], cwd=base, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, **kwargs)
            running = True
            _runner_proc = proc
            print(f"run_grid_runner: started runner pid={proc.pid}")
            return proc
        except Exception as e:
            print("Failed to start grid_runner.py:", repr(e))
            return None


def ensure_runner_running(path: str = "grid.json") -> Optional[subprocess.Popen]:
    """Ensure a single runner process is running and return it.

    This will not start a new process if one we started earlier is still alive.
    """
    global running, _runner_proc
    # Check whether runner is already running while holding the lock, but do
    # not call run_grid_runner while holding the lock to avoid deadlock (it
    # also tries to acquire the same lock). If a runner is needed, call
    # run_grid_runner outside the lock.
    need_start = False
    with _proc_lock:
        if _runner_proc is not None:
            try:
                if _runner_proc.poll() is None:
                    running = True
                    return _runner_proc
            except Exception:
                _runner_proc = None
        need_start = True

    if need_start:
        return run_grid_runner(path=path)
    return None


def stop_runner():
    """Stop the runner subprocess if it was started by this module."""
    global running, _runner_proc
    with _proc_lock:
        if _runner_proc:
            try:
                print(f"stop_runner: terminating runner pid={_runner_proc.pid}")
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
    return CREATE_GRID()