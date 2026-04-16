# player.py

import os
import math
import pygame
from settings import *
from map import grid   # IMPORTANT
from bullets import Bullet

class Player:
    def __init__(self):
        self.x = 100
        self.y = 100
        self.size = 30
        self.speed = 5
        self.angle = 0
        self.health = 100

        # Load and scale player image
        image_path = os.path.join('assets', 'PNG', 'Hitman 1', 'hitman1_gun.png')
        self.original_image = pygame.image.load(image_path).convert_alpha()
        self.original_image = pygame.transform.scale(self.original_image, (self.size, self.size))

    def move(self, keys, camera_x, camera_y):
        new_x = self.x
        new_y = self.y

        # Calculate new position
        if keys[pygame.K_d]:
            new_x += self.speed
        if keys[pygame.K_a]:
            new_x -= self.speed
        if keys[pygame.K_w]:
            new_y -= self.speed
        if keys[pygame.K_s]:
            new_y += self.speed
            
        # Mouse aiming
        mx, my = pygame.mouse.get_pos()
        dx = (mx + camera_x) - (self.x + self.size // 2)
        dy = (my + camera_y) - (self.y + self.size // 2)
        self.angle = -math.degrees(math.atan2(dy, dx))

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

    def shoot(self, target_x, target_y):
        return Bullet(self.x + self.size // 2, self.y + self.size // 2, target_x, target_y, 'player', 25)

    def take_damage(self, amount):
        self.health -= amount

    def draw(self, screen, camera_x, camera_y):
        # Rotate image based on the current angle
        rotated_image = pygame.transform.rotate(self.original_image, self.angle)
        # Center the rotated image properly on the player's position
        rect = rotated_image.get_rect(center=(self.x - camera_x + self.size // 2, self.y - camera_y + self.size // 2))
        
        screen.blit(rotated_image, rect.topleft)