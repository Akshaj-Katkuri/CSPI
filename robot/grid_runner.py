import pygame
import sys
import json
import os
import subprocess

# --- Config ---
MAX_SIZE = 10
MIN_SIZE = 2
GRID_ROWS = 6
GRID_COLS = 6
# No toolbar for the runner — let the grid occupy the full window
TOOLBAR_HEIGHT = 0
WIDTH, HEIGHT = 600, 700  # fixed window size

# Colors
WHITE = (245, 245, 245)
BLACK = (40, 40, 40)
GRAY = (160, 160, 160)
BLUE = (70, 130, 180)
GREEN = (0, 200, 0)
TOOLBAR_BG = (230, 230, 230)
LIGHT_GRAY = (210, 210, 210)

pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Grid Runner")

# Grid states
EMPTY = 0
WALL = 1
TURTLE = 2
GOAL = 3


# No maker invocation here — runner is read-only and will reload grid.json when it changes.


def load_grid_from_json(path="grid.json"):
    """Load grid state from JSON file if present. Falls back to an empty grid on error."""
    global grid, GRID_ROWS, GRID_COLS, turtle_pos, goal_pos, turtle_dir

    if not os.path.exists(path):
        # No saved file, start with empty grid
        grid = [[EMPTY for _ in range(GRID_COLS)] for _ in range(GRID_ROWS)]
        turtle_pos = None
        goal_pos = None
        turtle_dir = 0
        return

    try:
        with open(path, "r") as f:
            data = json.load(f)

        # Determine new size from file (handle ragged rows)
        file_rows = len(data)
        file_cols = max((len(r) for r in data), default=0)

        # Clamp sizes to allowed min/max
        new_rows = max(MIN_SIZE, min(MAX_SIZE, file_rows))
        new_cols = max(MIN_SIZE, min(MAX_SIZE, file_cols))

        GRID_ROWS, GRID_COLS = new_rows, new_cols
        grid = [[EMPTY for _ in range(GRID_COLS)] for _ in range(GRID_ROWS)]
        turtle_pos = None
        goal_pos = None
        turtle_dir = 0

        for r in range(min(len(data), GRID_ROWS)):
            row = data[r]
            for c in range(min(len(row), GRID_COLS)):
                val = row[c]
                if val is None:
                    grid[r][c] = EMPTY
                elif val == "Wall":
                    grid[r][c] = WALL
                elif val == "Goal":
                    grid[r][c] = GOAL
                    goal_pos = (r, c)
                elif isinstance(val, (int, float)):
                    # numeric value indicates turtle rotation in degrees
                    grid[r][c] = TURTLE
                    turtle_pos = (r, c)
                    deg = int(val) % 360
                    turtle_dir = ((360 - deg) % 360) // 90
                else:
                    grid[r][c] = EMPTY

    except Exception as e:
        print("Failed to load grid.json:", e)
        grid = [[EMPTY for _ in range(GRID_COLS)] for _ in range(GRID_ROWS)]
        turtle_pos = None
        goal_pos = None
        turtle_dir = 0


def export_grid_to_json(path="grid.json"):
    data = []
    for r in range(GRID_ROWS):
        row = []
        for c in range(GRID_COLS):
            if grid[r][c] == EMPTY:
                row.append(None)
            elif grid[r][c] == WALL:
                row.append("Wall")
            elif grid[r][c] == GOAL:
                row.append("Goal")
            elif grid[r][c] == TURTLE:
                # Convert turtle_dir to degrees
                deg = (360 - (turtle_dir * 90)) % 360  # 0=right, 90=up, etc
                row.append(deg)
            else:
                row.append(None)
        data.append(row)

    with open(path, "w") as f:
        json.dump(data, f, indent=2)
    print("✅ Grid exported to", path)


def resize_grid(new_rows, new_cols):
    """Resize grid while preserving content."""
    global grid, GRID_ROWS, GRID_COLS, turtle_pos, goal_pos

    new_grid = [[EMPTY for _ in range(new_cols)] for _ in range(new_rows)]

    for r in range(min(GRID_ROWS, new_rows)):
        for c in range(min(GRID_COLS, new_cols)):
            new_grid[r][c] = grid[r][c]

    grid = new_grid
    GRID_ROWS, GRID_COLS = new_rows, new_cols

    # reset turtle/goal if clipped
    if turtle_pos and (turtle_pos[0] >= new_rows or turtle_pos[1] >= new_cols):
        turtle_pos = None
    if goal_pos and (goal_pos[0] >= new_rows or goal_pos[1] >= new_cols):
        goal_pos = None


def draw_turtle_icon(surface, rect, color, direction):
    """Draw a triangle pointing in the given direction."""
    cx, cy = rect.center
    pad = int(min(rect.width, rect.height) * 0.35)
    if pad < 1:
        pad = 1

    if direction == 0:  # right
        points = [
            (cx - pad, cy - pad),
            (cx - pad, cy + pad),
            (cx + pad, cy)
        ]
    elif direction == 1:  # down
        points = [
            (cx - pad, cy - pad),
            (cx + pad, cy - pad),
            (cx, cy + pad)
        ]
    elif direction == 2:  # left
        points = [
            (cx + pad, cy - pad),
            (cx + pad, cy + pad),
            (cx - pad, cy)
        ]
    elif direction == 3:  # up
        points = [
            (cx - pad, cy + pad),
            (cx + pad, cy + pad),
            (cx, cy - pad)
        ]

    pygame.draw.polygon(surface, color, points)


def draw_grid():
    global CELL_SIZE, offset_x, offset_y
    grid_area_height = HEIGHT - TOOLBAR_HEIGHT
    CELL_SIZE = min(WIDTH // GRID_COLS, grid_area_height // GRID_ROWS)

    grid_width = GRID_COLS * CELL_SIZE
    grid_height = GRID_ROWS * CELL_SIZE
    offset_x = (WIDTH - grid_width) // 2
    offset_y = TOOLBAR_HEIGHT + (grid_area_height - grid_height) // 2

    for r in range(GRID_ROWS):
        for c in range(GRID_COLS):
            rect = pygame.Rect(offset_x + c * CELL_SIZE,
                               offset_y + r * CELL_SIZE,
                               CELL_SIZE, CELL_SIZE)

            if grid[r][c] == EMPTY:
                pygame.draw.rect(screen, WHITE, rect)
            elif grid[r][c] == WALL:
                pygame.draw.rect(screen, BLACK, rect)
            elif grid[r][c] == TURTLE:
                pygame.draw.rect(screen, WHITE, rect)
                draw_turtle_icon(screen, rect, BLUE, turtle_dir)
            elif grid[r][c] == GOAL:
                pygame.draw.rect(screen, GRAY, rect)

            pygame.draw.rect(screen, (100, 100, 100), rect, 2)  # bolder grid lines


def place_item(row, col):
    global turtle_pos, goal_pos

    if current_tool == WALL:
        grid[row][col] = EMPTY if grid[row][col] == WALL else WALL

    elif current_tool == TURTLE:
        if turtle_pos:
            tr, tc = turtle_pos
            grid[tr][tc] = EMPTY
        grid[row][col] = TURTLE
        turtle_pos = (row, col)

    elif current_tool == GOAL:
        if goal_pos:
            gr, gc = goal_pos
            grid[gr][gc] = EMPTY
        grid[row][col] = GOAL
        goal_pos = (row, col)


# --- Runner startup ---
print(f"grid_runner: started pid={os.getpid()}")

def ensure_grid_created(path="grid.json"):
    """Ensure grid.json exists and contains at least one non-empty cell (wall/goal/turtle).
    If not, run the grid maker (grid_maker.py) to create it, then reload.
    """
    # First try to load (will create an empty grid if file missing)
    load_grid_from_json(path)

    # Detect emptiness: grid has only EMPTY cells and no turtle/goal
    has_content = False
    for r in range(GRID_ROWS):
        for c in range(GRID_COLS):
            if grid[r][c] != EMPTY:
                has_content = True
                break
        if has_content:
            break

    if not has_content:
        # Try also to detect if file existed but contained only nulls
        file_path = os.path.join(os.path.dirname(__file__), path)
        need_maker = False
        if not os.path.exists(file_path) or os.path.getsize(file_path) < 5:
            need_maker = True
        else:
            try:
                with open(file_path, "r") as f:
                    data = json.load(f)
                # If data is empty list or all rows empty/None
                if not data:
                    need_maker = True
                else:
                    only_nulls = True
                    for row in data:
                        for cell in row:
                            if cell is not None:
                                only_nulls = False
                                break
                        if not only_nulls:
                            break
                    if only_nulls:
                        need_maker = True
            except Exception:
                need_maker = True

        if need_maker:
            # Do not launch the editor from the runner — that can create nested
            # Pygame event loops or block. The runner is read-only; if a grid
            # doesn't exist, continue with an empty grid and let the external
            # editor (creator) be responsible for creating the JSON file.
            print("No grid data found — continuing with empty grid. Use the editor to create grid.json")

        # Reload after maker (or even if maker wasn't run but file changed)
        load_grid_from_json(path)


# Ensure a grid exists (run maker if necessary) and load it
ensure_grid_created()

# Track file modification time to reload when changed
grid_path = os.path.join(os.path.dirname(__file__), "grid.json")
try:
    last_mtime = os.path.getmtime(grid_path)
except Exception:
    last_mtime = 0

# Default tool and state
current_tool = TURTLE
dragging = False
drag_action = None

running = True
clock = pygame.time.Clock()
while running:
    clock.tick(60)
    screen.fill(WHITE)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        # No input handling for editing; only allow quit
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                running = False

    # If grid.json changed on disk, reload
    try:
        mtime = os.path.getmtime(grid_path)
    except Exception:
        mtime = 0
    if mtime != last_mtime:
        last_mtime = mtime
        load_grid_from_json()

    draw_grid()

    pygame.display.flip()

pygame.quit()
sys.exit()
