import json
import os

from utils.errors import GridError
from utils.results import RunTimeResult

# TODO: Prob should make this a static class, passing path in as another parameter. 
class RobotCommands: 
    def __init__(self, current_grid_path):
        # Resolve path relative to robot folder (where this file is)
        if not os.path.isabs(current_grid_path):
            current_grid_path = os.path.join(os.path.dirname(__file__), current_grid_path)
        self.path = current_grid_path

    def move_forward(self, steps=1):
        """Move the turtle forward based on its current direction.
        
        Direction encoding in JSON: 0=right, 90=up, 180=left, 270=down (counterclockwise positive)
        """
        RTresult = RunTimeResult()

        try:
            # Load current grid state
            with open(self.path, "r") as f:
                data = json.load(f)
            
            # Find turtle position and direction. Turtle may be stored as a number
            # (deg) or as an overlapping list [under, deg].
            turtle_pos = None
            turtle_dir_deg = 0

            for r in range(len(data)):
                for c in range(len(data[r])):
                    val = data[r][c]
                    if isinstance(val, (int, float)):
                        turtle_pos = (r, c)
                        turtle_dir_deg = int(val) % 360
                        break
                    if isinstance(val, list) and len(val) >= 2 and isinstance(val[1], (int, float)):
                        turtle_pos = (r, c)
                        turtle_dir_deg = int(val[1]) % 360
                        break
                if turtle_pos:
                    break
            
            if turtle_pos is None:
                return GridError(details="No turtle found on grid.")
            
            # Calculate new position based on direction and steps
            row, col = turtle_pos
            
            for _ in range(steps):
                if turtle_dir_deg == 0:  # right
                    col += 1
                elif turtle_dir_deg == 90:  # up
                    row -= 1
                elif turtle_dir_deg == 180:  # left
                    col -= 1
                elif turtle_dir_deg == 270:  # down
                    row += 1
            
            # Clamp to grid bounds
            max_rows = len(data)
            max_cols = max((len(r) for r in data), default=0)
            
            # Check if out of bounds
            if row < 0 or row >= max_rows or col < 0 or col >= max_cols:
                return RTresult.failure(GridError(details="Robot is trying to move out of bounds."))
                # raise RuntimeError(f"Turtle would move out of bounds to ({row}, {col}). Grid bounds: rows [0, {max_rows-1}], cols [0, {max_cols-1}]")
            
            # Update grid: remove turtle from old position, but preserve underlying
            # wall/goal if present. Also check target cell for overlapping.
            old_pos = None
            for r in range(len(data)):
                for c in range(len(data[r])):
                    val = data[r][c]
                    if isinstance(val, (int, float)):
                        old_pos = (r, c)
                        data[r][c] = None
                    elif isinstance(val, list) and len(val) >= 2 and isinstance(val[1], (int, float)):
                        old_pos = (r, c)
                        # restore underlying value
                        data[r][c] = val[0] if val[0] is not None else None

            # Place turtle at new position with same direction. If there is an
            # underlying wall/goal, store as [under, deg] so the UI can render
            # the turtle overlapping the element.
            target_val = data[row][col]
            if isinstance(target_val, (int, float)) or (isinstance(target_val, list) and len(target_val) >= 2 and isinstance(target_val[1], (int, float))):
                return RTresult.failure(GridError(details="Target occupied by another turtle."))

            if target_val == "Wall" or target_val == "WALL" or target_val == 1:
                data[row][col] = ["Wall", turtle_dir_deg]
            elif target_val == "Goal" or target_val == "GOAL":
                data[row][col] = ["Goal", turtle_dir_deg]
            else:
                data[row][col] = turtle_dir_deg
            
            # Write back to JSON
            with open(self.path, "w") as f:
                json.dump(data, f, indent=2)

            # If we wrote an overlapping representation, return which underlying
            # element the turtle is on. Otherwise return None.
            cur = data[row][col]
            if isinstance(cur, list) and len(cur) >= 1:
                under = cur[0]
                if isinstance(under, str) and under.lower().startswith("wall"):
                    return RTresult.failure(GridError(details="Robot ran into a wall."))
                if isinstance(under, str) and under.lower().startswith("goal"):
                    return "GOAL"
            return None

        except Exception as e:
            print(f"Error moving forward: {e}")
            return None

    def turn_left(self, times=1):
        """Rotate the turtle left (counterclockwise) by 90 degrees per time.

        times: number of 90-degree steps to turn left.
        """
        try:
            with open(self.path, "r") as f:
                data = json.load(f)

            # find turtle
            turtle_pos = None
            turtle_dir_deg = 0
            for r in range(len(data)):
                for c in range(len(data[r])):
                    val = data[r][c]
                    if isinstance(val, (int, float)):
                        turtle_pos = (r, c)
                        turtle_dir_deg = int(val) % 360
                        break
                    if isinstance(val, list) and len(val) >= 2 and isinstance(val[1], (int, float)):
                        turtle_pos = (r, c)
                        turtle_dir_deg = int(val[1]) % 360
                        break
                if turtle_pos:
                    break

            if turtle_pos is None:
                print("Error: Turtle not found in grid")
                return

            row, col = turtle_pos
            # normalize times
            times = int(times) if times and times > 0 else 1
            new_deg = (turtle_dir_deg + 90 * times) % 360

            # write back, preserving underlying if present
            cur = data[row][col]
            if isinstance(cur, list) and len(cur) >= 2:
                data[row][col] = [cur[0], new_deg]
            else:
                data[row][col] = new_deg
            with open(self.path, "w") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Error turning left: {e}")

    def turn_right(self, times=1):
        """Rotate the turtle right (clockwise) by 90 degrees per time.

        times: number of 90-degree steps to turn right.
        """
        try:
            with open(self.path, "r") as f:
                data = json.load(f)

            # find turtle
            turtle_pos = None
            turtle_dir_deg = 0
            for r in range(len(data)):
                for c in range(len(data[r])):
                    val = data[r][c]
                    if isinstance(val, (int, float)):
                        turtle_pos = (r, c)
                        turtle_dir_deg = int(val) % 360
                        break
                    if isinstance(val, list) and len(val) >= 2 and isinstance(val[1], (int, float)):
                        turtle_pos = (r, c)
                        turtle_dir_deg = int(val[1]) % 360
                        break
                if turtle_pos:
                    break

            if turtle_pos is None:
                print("Error: Turtle not found in grid")
                return

            row, col = turtle_pos
            times = int(times) if times and times > 0 else 1
            new_deg = (turtle_dir_deg - 90 * times) % 360

            # write back, preserving underlying if present
            cur = data[row][col]
            if isinstance(cur, list) and len(cur) >= 2:
                data[row][col] = [cur[0], new_deg]
            else:
                data[row][col] = new_deg
            with open(self.path, "w") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Error turning right: {e}")

    def can_move(self, direction):
        """Return True if the robot can move one cell in the given relative direction.

        direction is a string: "FORWARD", "BACKWARD", "LEFT" or "RIGHT" (case-insensitive).
        Movement is blocked by grid bounds or walls. "Goal"/"GOAL" cells are treated as passable.
        """
        with open(self.path, "r") as f: 
            data = json.load(f)

        turtle_pos = None
        turtle_angle = 0

        for r in range(len(data)): 
            for c in range(len(data[r])): 
                value = data[r][c]

                if isinstance(value, (int)): 
                    # This means it is a turtle
                    turtle_pos = (r, c)
                    turtle_angle = value
                    break
                if isinstance(value, list) and len(value) >= 2 and isinstance(value[1], (int, float)):
                    # This means turtle is overlapping with a goal/wall
                    turtle_pos = (r, c)
                    turtle_angle = int(value[1]) % 360
                    break

        if turtle_pos == None:
            return False #TODO: Raise error here ex: "No turtle found on grid"
        
        d = (direction or "").strip().upper()
        if d == "FORWARD":
            offset = 0
        elif d == "BACKWARD":
            offset = 180
        elif d == "LEFT":
            offset = 90
        elif d == "RIGHT":
            offset = 270
        else:
            raise ValueError(f"Unknown direction: {direction}")

        abs_angle = (turtle_angle + offset) % 360

        if abs_angle == 0:  # right
            dr, dc = 0, 1
        elif abs_angle == 90:  # up
            dr, dc = -1, 0
        elif abs_angle == 180:  # left
            dr, dc = 0, -1
        elif abs_angle == 270:  # down
            dr, dc = 1, 0
        else:
            # Backup if angle isn't a multiple of 90 for some reason
            normalized = (round(abs_angle / 90) * 90) % 360
            if normalized == 0:
                dr, dc = 0, 1
            elif normalized == 90:
                dr, dc = -1, 0
            elif normalized == 180:
                dr, dc = 0, -1
            else:
                dr, dc = 1, 0

        row, col = turtle_pos
        target_r, target_c = row + dr, col + dc

        # Check if out of bounds
        max_rows = len(data)
        max_cols = len(data[0])
        if (target_r < 0
            or target_r >= max_rows
            or target_c < 0
            or target_c >= max_cols):
            return False

        target_value = data[target_r][target_c]

        if isinstance(target_value, str): 
            if target_value.upper() == "WALL": 
                return False

        if isinstance(target_value, int):
            # occupied by another turtle
            return False
        
        if isinstance(target_value, list) and len(target_value) >= 2 and isinstance(target_value[1], (int, float)):
            # occupied by a turtle on a wall/goal, which shouldn't happen since only one turtle can exist
            return False

        # Goal is valid
        return True
