# map.py

import os
import pygame
from settings import *

# Example map (0 = floor, 1 = wall)
# 50 cols x 30 rows covers 2000x1200 pixels easily
grid = [[0 for _ in range(50)] for _ in range(30)]

# Add boundary walls
for i in range(50):
    grid[0][i] = 1
    grid[-1][i] = 1
for i in range(30):
    grid[i][0] = 1
    grid[i][-1] = 1

# Add some simple inner walls
for i in range(5, 15):
    grid[10][i] = 1
    grid[20][i] = 1
for i in range(15, 25):
    grid[i][25] = 1
for i in range(35, 45):
    grid[5][i] = 1
    grid[25][i] = 1

# Add Gold (2)
grid[5][5] = 2
grid[5][45] = 2
grid[25][5] = 2
grid[25][45] = 2
grid[15][25] = 2

# Add Exit Door (3)
grid[15][48] = 3

# Cache for loaded images
FLOOR_IMG = None
WALL_IMG = None

def draw_map(screen, camera_x, camera_y):
    global FLOOR_IMG, WALL_IMG
    
    # Lazy load images on first frame so display is already initialized
    if FLOOR_IMG is None:
        floor_path = os.path.join('assets', 'PNG', 'Tiles', 'tile_01.png')
        wall_path = os.path.join('assets', 'PNG', 'Tiles', 'tile_11.png')
        
        FLOOR_IMG = pygame.image.load(floor_path).convert_alpha()
        FLOOR_IMG = pygame.transform.scale(FLOOR_IMG, (TILE_SIZE, TILE_SIZE))
        
        WALL_IMG = pygame.image.load(wall_path).convert_alpha()
        WALL_IMG = pygame.transform.scale(WALL_IMG, (TILE_SIZE, TILE_SIZE))

    for row in range(len(grid)):
        for col in range(len(grid[row])):
            tile = grid[row][col]

            x = col * TILE_SIZE
            y = row * TILE_SIZE

            if tile == 0 or tile == 2 or tile == 3:
                # Always draw floor underneath everything
                screen.blit(FLOOR_IMG, (x - camera_x, y - camera_y))
            if tile == 1:
                screen.blit(WALL_IMG, (x - camera_x, y - camera_y))