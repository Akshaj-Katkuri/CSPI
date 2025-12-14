import pygame
import sys
import json
import os

from utils.errors import GridError
from utils.results import RunTimeResult


MAX_SIZE = 10
MIN_SIZE = 2
DEFAULT_GRID_ROWS = 6
DEFAULT_GRID_COLS = 6
TOOLBAR_HEIGHT = 100
WIDTH, HEIGHT = 600, 700


WHITE = (245, 245, 245)
BLACK = (40, 40, 40)
GRAY = (160, 160, 160)
BLUE = (70, 130, 180)
GREEN = (0, 200, 0)
TOOLBAR_BG = (230, 230, 230)
LIGHT_GRAY = (210, 210, 210)


EMPTY = 0
WALL = 1
TURTLE = 2
GOAL = 3


class GridMaker:
    """A simple grid editor using pygame.

    Use GridEditor(path).run() to start the editor. When run() returns it will
    have exported the grid to the provided path.
    """

    def __init__(self, path="initial_grid.json", rows=DEFAULT_GRID_ROWS, cols=DEFAULT_GRID_COLS):
        # Resolve path relative to robot folder
        if not os.path.isabs(path):
            path = os.path.join(os.path.dirname(__file__), path)
        self.path = path
        self.GRID_ROWS = rows
        self.GRID_COLS = cols
        self.grid = None
        self.turtle_pos = None
        self.goal_pos = None
        self.turtle_dir = 0

        # UI / state
        self.current_tool = TURTLE
        self.dragging = False
        self.drag_action = None
        self.editing_locked = False

        # layout
        self.button_size = 50
        self.padding = 15
        self.buttons = {}
        self.confirm_button = None
        self.rotate_left_button = None
        self.rotate_right_button = None
        self.row_minus = None
        self.row_plus = None
        self.col_minus = None
        self.col_plus = None
        self.rotate_left_icon = None
        self.rotate_right_icon = None

        # runtime pygame objects
        self.screen = None

        # init grid from file (or empty)
        self.load_grid_from_json()

    # --- persistence ---
    def load_grid_from_json(self, path=None):
        path = path or self.path
        if not os.path.exists(path):
            self.grid = [[EMPTY for _ in range(self.GRID_COLS)] for _ in range(self.GRID_ROWS)]
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
            self.grid = [[EMPTY for _ in range(self.GRID_COLS)] for _ in range(self.GRID_ROWS)]
            self.turtle_pos = None
            self.goal_pos = None
            self.turtle_dir = 0

            for r in range(min(len(data), self.GRID_ROWS)):
                row = data[r]
                for c in range(min(len(row), self.GRID_COLS)):
                    val = row[c]
                    if val is None:
                        self.grid[r][c] = EMPTY
                    elif val == "WALL":
                        self.grid[r][c] = WALL
                    elif val == "GOAL":
                        self.grid[r][c] = GOAL
                        self.goal_pos = (r, c)
                    elif isinstance(val, (int, float)):
                        self.grid[r][c] = TURTLE
                        self.turtle_pos = (r, c)
                        deg = int(val) % 360
                        self.turtle_dir = ((360 - deg) % 360) // 90
                    else:
                        self.grid[r][c] = EMPTY

        except Exception as e:
            print("Failed to load", path, ":", e)
            self.grid = [[EMPTY for _ in range(self.GRID_COLS)] for _ in range(self.GRID_ROWS)]
            self.turtle_pos = None
            self.goal_pos = None
            self.turtle_dir = 0

    def export_grid_to_json(self, path=None):
        path = path or self.path
        data = []
        for r in range(self.GRID_ROWS):
            row = []
            for c in range(self.GRID_COLS):
                if self.grid[r][c] == EMPTY:
                    row.append(None)
                elif self.grid[r][c] == WALL:
                    row.append("WALL")
                elif self.grid[r][c] == GOAL:
                    row.append("GOAL")
                elif self.grid[r][c] == TURTLE:
                    deg = (360 - (self.turtle_dir * 90)) % 360
                    row.append(deg)
                else:
                    row.append(None)
            data.append(row)

        with open(path, "w") as f:
            json.dump(data, f, indent=2)
        print("✅ Grid exported to", path)

    # --- grid manipulation ---
    def resize_grid(self, new_rows, new_cols):
        new_grid = [[EMPTY for _ in range(new_cols)] for _ in range(new_rows)]
        for r in range(min(self.GRID_ROWS, new_rows)):
            for c in range(min(self.GRID_COLS, new_cols)):
                new_grid[r][c] = self.grid[r][c]
        self.grid = new_grid
        self.GRID_ROWS, self.GRID_COLS = new_rows, new_cols

        if self.turtle_pos and (self.turtle_pos[0] >= new_rows or self.turtle_pos[1] >= new_cols):
            self.turtle_pos = None
        if self.goal_pos and (self.goal_pos[0] >= new_rows or self.goal_pos[1] >= new_cols):
            self.goal_pos = None

    # --- drawing helpers ---
    def draw_turtle_icon(self, surface, rect, color, direction):
        cx, cy = rect.center
        pad = int(min(rect.width, rect.height) * 0.3)
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

    def draw_grid(self):
        grid_area_height = HEIGHT - TOOLBAR_HEIGHT
        self.CELL_SIZE = min(WIDTH // self.GRID_COLS, grid_area_height // self.GRID_ROWS)

        grid_width = self.GRID_COLS * self.CELL_SIZE
        grid_height = self.GRID_ROWS * self.CELL_SIZE
        self.offset_x = (WIDTH - grid_width) // 2
        self.offset_y = TOOLBAR_HEIGHT + (grid_area_height - grid_height) // 2

        for r in range(self.GRID_ROWS):
            for c in range(self.GRID_COLS):
                rect = pygame.Rect(self.offset_x + c * self.CELL_SIZE,
                                   self.offset_y + r * self.CELL_SIZE,
                                   self.CELL_SIZE, self.CELL_SIZE)

                if self.grid[r][c] == EMPTY:
                    pygame.draw.rect(self.screen, WHITE, rect)
                elif self.grid[r][c] == WALL:
                    pygame.draw.rect(self.screen, BLACK, rect)
                elif self.grid[r][c] == TURTLE:
                    pygame.draw.rect(self.screen, WHITE, rect)
                    self.draw_turtle_icon(self.screen, rect, BLUE, self.turtle_dir)
                elif self.grid[r][c] == GOAL:
                    pygame.draw.rect(self.screen, GRAY, rect)

                pygame.draw.rect(self.screen, (100, 100, 100), rect, 2)

    def draw_toolbar(self):
        pygame.draw.rect(self.screen, TOOLBAR_BG, (0, 0, WIDTH, TOOLBAR_HEIGHT))

        if not self.editing_locked:
            for tool, rect in self.buttons.items():
                if tool == TURTLE:
                    pygame.draw.rect(self.screen, WHITE, rect, border_radius=8)
                    self.draw_turtle_icon(self.screen, rect, BLUE, self.turtle_dir)
                elif tool == WALL:
                    pygame.draw.rect(self.screen, BLACK, rect, border_radius=8)
                elif tool == GOAL:
                    pygame.draw.rect(self.screen, GRAY, rect, border_radius=8)

                if tool == self.current_tool:
                    pygame.draw.rect(self.screen, GREEN, rect, 4, border_radius=8)

            if self.current_tool == TURTLE:
                pygame.draw.rect(self.screen, LIGHT_GRAY, self.rotate_left_button, border_radius=8)
                pygame.draw.rect(self.screen, LIGHT_GRAY, self.rotate_right_button, border_radius=8)
                self.screen.blit(self.rotate_left_icon, self.rotate_left_button)
                self.screen.blit(self.rotate_right_icon, self.rotate_right_button)

            font = pygame.font.SysFont(None, 24)
            pygame.draw.rect(self.screen, LIGHT_GRAY, self.row_minus, border_radius=6)
            pygame.draw.rect(self.screen, LIGHT_GRAY, self.row_plus, border_radius=6)
            pygame.draw.rect(self.screen, LIGHT_GRAY, self.col_minus, border_radius=6)
            pygame.draw.rect(self.screen, LIGHT_GRAY, self.col_plus, border_radius=6)

            self.screen.blit(font.render("-", True, BLACK), self.row_minus.move(8, 3))
            self.screen.blit(font.render("+", True, BLACK), self.row_plus.move(8, 3))
            self.screen.blit(font.render("-", True, BLACK), self.col_minus.move(8, 3))
            self.screen.blit(font.render("+", True, BLACK), self.col_plus.move(8, 3))

            self.screen.blit(font.render(f"Rows: {self.GRID_ROWS}", True, BLACK), (WIDTH - 270, 25))
            self.screen.blit(font.render(f"Cols: {self.GRID_COLS}", True, BLACK), (WIDTH - 270, 65))

        pygame.draw.rect(self.screen, GREEN, self.confirm_button, border_radius=10)
        font = pygame.font.SysFont(None, 28, bold=True)
        self.screen.blit(font.render("Confirm", True, WHITE), self.confirm_button.move(5, 5))

    def place_item(self, row, col):
        if self.current_tool == WALL:
            self.grid[row][col] = EMPTY if self.grid[row][col] == WALL else WALL

        elif self.current_tool == TURTLE:
            if self.turtle_pos:
                tr, tc = self.turtle_pos
                self.grid[tr][tc] = EMPTY
            self.grid[row][col] = TURTLE
            self.turtle_pos = (row, col)

        elif self.current_tool == GOAL:
            if self.goal_pos:
                gr, gc = self.goal_pos
                self.grid[gr][gc] = EMPTY
            self.grid[row][col] = GOAL
            self.goal_pos = (row, col)

    def _load_ui(self):
        # initialize pygame and UI rects/icons
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Grid Editor")

        self.button_size = 50
        self.padding = 15
        self.buttons = {
            TURTLE: pygame.Rect(self.padding, self.padding, self.button_size, self.button_size),
            WALL: pygame.Rect(2 * self.padding + self.button_size, self.padding, self.button_size, self.button_size),
            GOAL: pygame.Rect(3 * self.padding + 2 * self.button_size, self.padding, self.button_size, self.button_size)
        }

        self.confirm_button = pygame.Rect(WIDTH - 110, TOOLBAR_HEIGHT//2 - 20, 80, 40)
        self.rotate_left_button = pygame.Rect(4 * self.padding + 3 * self.button_size, self.padding, self.button_size, self.button_size)
        self.rotate_right_button = pygame.Rect(5 * self.padding + 4 * self.button_size, self.padding, self.button_size, self.button_size)

        # image paths relative to this file
        base = os.path.dirname(__file__)
        left_path = os.path.join(base, "rotate_left.png")
        right_path = os.path.join(base, "rotate_right.png")
        try:
            self.rotate_left_icon = pygame.image.load(left_path).convert_alpha()
            self.rotate_right_icon = pygame.image.load(right_path).convert_alpha()
            self.rotate_left_icon = pygame.transform.smoothscale(self.rotate_left_icon, (self.button_size, self.button_size))
            self.rotate_right_icon = pygame.transform.smoothscale(self.rotate_right_icon, (self.button_size, self.button_size))
        except Exception:
            # fall back to None — draw buttons without icons
            self.rotate_left_icon = None
            self.rotate_right_icon = None

        # Row/Col adjust buttons
        self.row_minus = pygame.Rect(WIDTH - 200, 20, 30, 30)
        self.row_plus = pygame.Rect(WIDTH - 160, 20, 30, 30)
        self.col_minus = pygame.Rect(WIDTH - 200, 60, 30, 30)
        self.col_plus = pygame.Rect(WIDTH - 160, 60, 30, 30)

    def run(self):
        """Run the editor. Returns after the user confirms (grid is exported)."""
        self._load_ui()

        running = True
        clock = pygame.time.Clock()

        while running:
            clock.tick(60)
            self.screen.fill(WHITE)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                    pygame.quit()
                    return RunTimeResult().failure(GridError(details='User closed grid maker'))

                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    mx, my = pygame.mouse.get_pos()
                    if self.confirm_button.collidepoint(mx, my):
                        self.export_grid_to_json()
                        running = False
                        break
                    elif not self.editing_locked:
                        for tool, rect in self.buttons.items():
                            if rect.collidepoint(mx, my):
                                self.current_tool = tool
                                break
                        else:
                            if self.current_tool == TURTLE:
                                if self.rotate_left_button.collidepoint(mx, my):
                                    self.turtle_dir = (self.turtle_dir - 1) % 4
                                    continue
                                elif self.rotate_right_button.collidepoint(mx, my):
                                    self.turtle_dir = (self.turtle_dir + 1) % 4
                                    continue

                            if self.row_minus.collidepoint(mx, my) and self.GRID_ROWS > MIN_SIZE:
                                self.resize_grid(self.GRID_ROWS - 1, self.GRID_COLS)
                            elif self.row_plus.collidepoint(mx, my) and self.GRID_ROWS < MAX_SIZE:
                                self.resize_grid(self.GRID_ROWS + 1, self.GRID_COLS)
                            elif self.col_minus.collidepoint(mx, my) and self.GRID_COLS > MIN_SIZE:
                                self.resize_grid(self.GRID_ROWS, self.GRID_COLS - 1)
                            elif self.col_plus.collidepoint(mx, my) and self.GRID_COLS < MAX_SIZE:
                                self.resize_grid(self.GRID_ROWS, self.GRID_COLS + 1)

                            elif my > TOOLBAR_HEIGHT:
                                col = (mx - self.offset_x) // self.CELL_SIZE
                                row = (my - self.offset_y) // self.CELL_SIZE
                                if 0 <= row < self.GRID_ROWS and 0 <= col < self.GRID_COLS:
                                    if self.current_tool == WALL:
                                        if self.grid[row][col] == EMPTY:
                                            self.drag_action = "add"
                                            self.grid[row][col] = WALL
                                        else:
                                            self.drag_action = "remove"
                                            self.grid[row][col] = EMPTY
                                        self.dragging = True

                                    elif self.current_tool == TURTLE:
                                        self.place_item(row, col)
                                        self.dragging = False
                                        self.drag_action = None

                                    elif self.current_tool == GOAL:
                                        if self.grid[row][col] == GOAL:
                                            self.grid[row][col] = EMPTY
                                        else:
                                            self.place_item(row, col)

                                    else:
                                        self.place_item(row, col)

                elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                    self.dragging = False
                    self.drag_action = None

                elif event.type == pygame.MOUSEMOTION and self.dragging and self.current_tool == WALL:
                    mx, my = event.pos
                    if my > TOOLBAR_HEIGHT:
                        col = (mx - self.offset_x) // self.CELL_SIZE
                        row = (my - self.offset_y) // self.CELL_SIZE
                        if 0 <= row < self.GRID_ROWS and 0 <= col < self.GRID_COLS:
                            if self.drag_action == "add" and self.grid[row][col] == EMPTY:
                                self.grid[row][col] = WALL
                            elif self.drag_action == "remove" and self.grid[row][col] == WALL:
                                self.grid[row][col] = EMPTY

            self.draw_toolbar()
            self.draw_grid()
            pygame.display.flip()

        pygame.quit()
        # do not sys.exit() so caller can continue
        return self.path
