import json
import os


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
        try:
            # Load current grid state
            with open(self.path, "r") as f:
                data = json.load(f)
            
            # Find turtle position and direction
            turtle_pos = None
            turtle_dir_deg = 0
            
            for r in range(len(data)):
                for c in range(len(data[r])):
                    val = data[r][c]
                    if isinstance(val, (int, float)):
                        turtle_pos = (r, c)
                        turtle_dir_deg = int(val) % 360
                        break
                if turtle_pos:
                    break
            
            if turtle_pos is None:
                print("Error: Turtle not found in grid")
                return
            
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
                raise RuntimeError(f"Turtle would move out of bounds to ({row}, {col}). Grid bounds: rows [0, {max_rows-1}], cols [0, {max_cols-1}]")
            
            # Update grid: remove turtle from old position, add to new position
            for r in range(len(data)):
                for c in range(len(data[r])):
                    if isinstance(data[r][c], (int, float)):
                        data[r][c] = None  # Clear old turtle position
            
            # Place turtle at new position with same direction
            data[row][col] = turtle_dir_deg
            
            # Write back to JSON
            with open(self.path, "w") as f:
                json.dump(data, f, indent=2)
            
            print(f"Turtle moved to ({row}, {col})")
        
        except RuntimeError: 
            print("Robot reached the boundary, so it cannot move forward. ")
        
        except Exception as e:
            print(f"Error moving forward: {e}")
