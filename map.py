# map.py

import pygame
from settings import *

# Example map (0 = floor, 1 = wall)
grid = [
    [0,0,0,0,0,0,0,0],
    [0,1,1,0,0,1,1,0],
    [0,0,0,0,0,0,0,0],
    [0,1,0,0,0,0,1,0],
    [0,0,0,1,1,0,0,0]
]

def draw_map(screen):
    for row in range(len(grid)):
        for col in range(len(grid[row])):
            tile = grid[row][col]

            x = col * TILE_SIZE
            y = row * TILE_SIZE

            if tile == 0:
                color = GRAY
            elif tile == 1:
                color = WHITE

            pygame.draw.rect(screen, color, (x, y, TILE_SIZE, TILE_SIZE))