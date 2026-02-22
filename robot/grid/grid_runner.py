import pygame
import sys
import json
import os

from signal import signal, SIGINT, SIGBREAK

MAX_SIZE = 10
MIN_SIZE = 2
DEFAULT_GRID_ROWS = 6
DEFAULT_GRID_COLS = 6
WIDTH, HEIGHT = 600, 700
TOOLBAR_HEIGHT = 0  # No toolbar for runner

WHITE = (245, 245, 245)
BLACK = (40, 40, 40)
GRAY = (160, 160, 160)
BLUE = (70, 130, 180)

EMPTY = 0
WALL = 1
TURTLE = 2
GOAL = 3

running = True


class GridRunner:
    def __init__(self, path="current_grid.json"):
        # Always resolve path relative to robot folder
        if not os.path.isabs(path):
            path = os.path.join(os.path.dirname(__file__), path)
        self.path = path
        self.GRID_ROWS = DEFAULT_GRID_ROWS
        self.GRID_COLS = DEFAULT_GRID_COLS
        self.grid = None
        self.turtle_pos = None
        self.goal_pos = None
        self.turtle_dir = 0
        self.screen = None
        self.window_open = False

        # map of (r,c) -> underlying cell type (WALL or GOAL) when turtle overlaps
        self.under_map = {}

        self.invalid_json_error_count = 0

        self._init_pygame()
        self.load_grid_from_json()

    def _init_pygame(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Grid Runner")
        self.window_open = True

    def load_grid_from_json(self, path=None):
        path = path or self.path
        if not os.path.exists(path):
            self.grid = [
                [EMPTY for _ in range(self.GRID_COLS)] for _ in range(self.GRID_ROWS)
            ]
            self.turtle_pos = None
            self.goal_pos = None
            self.turtle_dir = 0
            return
        try:
            with open(path, "r") as f:
                data = json.load(f)
            file_rows = len(data)
            file_cols = max((len(r) for r in data), default=0)
            new_rows = max(MIN_SIZE, min(MAX_SIZE, file_rows))
            new_cols = max(MIN_SIZE, min(MAX_SIZE, file_cols))
            self.GRID_ROWS, self.GRID_COLS = new_rows, new_cols
            self.grid = [
                [EMPTY for _ in range(self.GRID_COLS)] for _ in range(self.GRID_ROWS)
            ]
            self.turtle_pos = None
            self.goal_pos = None
            # reset under_map when loading
            self.under_map = {}
            for r in range(min(len(data), self.GRID_ROWS)):
                row = data[r]
                for c in range(min(len(row), self.GRID_COLS)):
                    val = row[c]
                    if val is None:
                        self.grid[r][c] = EMPTY
                    # handle strings for wall/goal (both capitalizations)
                    elif val == "WALL" or val == "Wall":
                        self.grid[r][c] = WALL
                    elif val == "GOAL" or val == "Goal":
                        self.grid[r][c] = GOAL
                        self.goal_pos = (r, c)
                    # overlapping entry: ["Wall"/"Goal", deg]
                    elif (
                        isinstance(val, list)
                        and len(val) >= 2
                        and isinstance(val[1], (int, float))
                    ):
                        under = val[0]
                        deg = int(val[1]) % 360
                        # treat underlying as wall or goal (case-insensitive)
                        if under == "WALL" or under == "Wall":
                            self.grid[r][c] = TURTLE
                            self.under_map[(r, c)] = WALL
                        elif under == "GOAL" or under == "Goal":
                            self.grid[r][c] = TURTLE
                            self.under_map[(r, c)] = GOAL
                            self.goal_pos = (r, c)
                        else:
                            # unknown underlying, treat as turtle on empty
                            self.grid[r][c] = TURTLE
                        self.turtle_pos = (r, c)
                        self.turtle_dir = ((360 - deg) % 360) // 90
                    elif isinstance(val, (int, float)):
                        # plain turtle
                        self.grid[r][c] = TURTLE
                        self.turtle_pos = (r, c)
                        deg = int(val) % 360
                        self.turtle_dir = ((360 - deg) % 360) // 90
                    else:
                        self.grid[r][c] = EMPTY
        except Exception as e:
            if (
                self.invalid_json_error_count > 5
            ):  # Sometimes when .json is being updated, it throws error, so this to flush them out and get error only when supposed to
                print("Failed to load", path, ":", e)
                self.grid = [
                    [EMPTY for _ in range(self.GRID_COLS)]
                    for _ in range(self.GRID_ROWS)
                ]
                self.turtle_pos = None
                self.goal_pos = None
                self.turtle_dir = 0
                self.invalid_json_error_count = 0
            else:
                self.invalid_json_error_count += 1

    def draw_turtle_icon(self, surface, rect: pygame.Rect, color, direction):
        cx, cy = rect.center
        pad = int(min(rect.width, rect.height) * 0.3)
        if pad < 1:
            pad = 1
        if direction == 0:  # right
            points = [(cx - pad, cy - pad), (cx - pad, cy + pad), (cx + pad, cy)]
        elif direction == 1:  # down
            points = [(cx - pad, cy - pad), (cx + pad, cy - pad), (cx, cy + pad)]
        elif direction == 2:  # left
            points = [(cx + pad, cy - pad), (cx + pad, cy + pad), (cx - pad, cy)]
        elif direction == 3:  # up
            points = [(cx - pad, cy + pad), (cx + pad, cy + pad), (cx, cy - pad)]
        pygame.draw.polygon(surface, color, points)

    def draw_grid(self):
        grid_area_height = HEIGHT - TOOLBAR_HEIGHT
        CELL_SIZE = min(WIDTH // self.GRID_COLS, grid_area_height // self.GRID_ROWS)
        grid_width = self.GRID_COLS * CELL_SIZE
        grid_height = self.GRID_ROWS * CELL_SIZE
        offset_x = (WIDTH - grid_width) // 2
        offset_y = TOOLBAR_HEIGHT + (grid_area_height - grid_height) // 2
        for r in range(self.GRID_ROWS):
            for c in range(self.GRID_COLS):
                rect = pygame.Rect(
                    offset_x + c * CELL_SIZE,
                    offset_y + r * CELL_SIZE,
                    CELL_SIZE,
                    CELL_SIZE,
                )
                if self.grid[r][c] == EMPTY:
                    pygame.draw.rect(self.screen, WHITE, rect)
                elif self.grid[r][c] == WALL:
                    pygame.draw.rect(self.screen, BLACK, rect)
                elif self.grid[r][c] == TURTLE:
                    # if there's an underlying element, draw it first so turtle appears on top
                    if (r, c) in self.under_map:
                        under = self.under_map[(r, c)]
                        if under == WALL:
                            pygame.draw.rect(self.screen, BLACK, rect)
                        elif under == GOAL:
                            pygame.draw.rect(self.screen, GRAY, rect)
                    else:
                        pygame.draw.rect(self.screen, WHITE, rect)
                    self.draw_turtle_icon(self.screen, rect, BLUE, self.turtle_dir)
                elif self.grid[r][c] == GOAL:
                    pygame.draw.rect(self.screen, GRAY, rect)
                pygame.draw.rect(self.screen, (100, 100, 100), rect, 2)

    def update_display(self):
        if not self.window_open:
            raise RuntimeError("Grid window is closed")

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.window_open = False
                raise RuntimeError("Grid window closed by user")

        if self.window_open:
            self.load_grid_from_json()
            self.screen.fill(WHITE)
            self.draw_grid()
            pygame.display.flip()

    def close(self):
        if self.window_open:
            self.window_open = False
            pygame.quit()


def handle_exit_signal(*args):
    global running
    running = False


signal(SIGINT, handle_exit_signal)
if sys.platform == "win32":
    signal(SIGBREAK, handle_exit_signal)

if __name__ == "__main__":
    runner = GridRunner()
    try:
        while running:
            runner.update_display()
    except RuntimeError:
        pass  # print(e)
    finally:
        runner.close()
        sys.exit(0)
