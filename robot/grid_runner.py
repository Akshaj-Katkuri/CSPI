
import pygame
import sys
import json
import os

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
		CELL_SIZE = min(WIDTH // self.GRID_COLS, grid_area_height // self.GRID_ROWS)
		grid_width = self.GRID_COLS * CELL_SIZE
		grid_height = self.GRID_ROWS * CELL_SIZE
		offset_x = (WIDTH - grid_width) // 2
		offset_y = TOOLBAR_HEIGHT + (grid_area_height - grid_height) // 2
		for r in range(self.GRID_ROWS):
			for c in range(self.GRID_COLS):
				rect = pygame.Rect(offset_x + c * CELL_SIZE,
								   offset_y + r * CELL_SIZE,
								   CELL_SIZE, CELL_SIZE)
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

	def update_display(self):
		if not self.window_open:
			raise RuntimeError("Grid window is closed")
		self.load_grid_from_json()
		self.screen.fill(WHITE)
		self.draw_grid()
		pygame.display.flip()
		# Process events to keep window responsive
		for event in pygame.event.get():
			if event.type == pygame.QUIT:
				self.window_open = False
				pygame.quit()
				raise RuntimeError("Grid window closed by user")

if __name__ == "__main__":
	runner = GridRunner()
	try:
		while True:
			runner.update_display()
			pygame.time.wait(2000)  # update every 2 seconds
	except RuntimeError as e:
		print(e)
		sys.exit(0)
