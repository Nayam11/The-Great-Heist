# player.py

import pygame
from settings import *
from map import grid   # IMPORTANT

class Player:
    def __init__(self):
        self.x = 100
        self.y = 100
        self.size = 30
        self.speed = 5

    def move(self, keys):
        new_x = self.x
        new_y = self.y

        # Calculate new position first
        if keys[pygame.K_RIGHT]:
            new_x += self.speed
        if keys[pygame.K_LEFT]:
            new_x -= self.speed
        if keys[pygame.K_UP]:
            new_y -= self.speed
        if keys[pygame.K_DOWN]:
            new_y += self.speed

        # Check all 4 corners
        left = new_x
        right = new_x + self.size
        top = new_y
        bottom = new_y + self.size

        # Convert all corners to tiles
        tiles = [
            (top // TILE_SIZE, left // TILE_SIZE),
            (top // TILE_SIZE, right // TILE_SIZE),
            (bottom // TILE_SIZE, left // TILE_SIZE),
            (bottom // TILE_SIZE, right // TILE_SIZE),
        ]

        can_move = True

        for tile_y, tile_x in tiles:
            if not (0 <= tile_y < len(grid) and 0 <= tile_x < len(grid[0])):
                can_move = False
            elif grid[tile_y][tile_x] == 1:
                can_move = False

        if can_move:
            self.x = new_x
            self.y = new_y

    def draw(self, screen):
        pygame.draw.rect(screen, (255, 0, 0), (self.x, self.y, self.size, self.size))