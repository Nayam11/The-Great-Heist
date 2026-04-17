# player.py

import os
import pygame
import math
from bullets import Bullet
from settings import TILE_SIZE, resource_path
import map

class Player:
    def __init__(self):
        self.x = 400
        self.y = 300
        self.size = 32
        self.health = 100
        self.base_speed = 5
        self.speed = self.base_speed
        self.speed_boost_timer = 0
        self.ammo = 5
        self.angle = 0
        
        image_path = resource_path(os.path.join('assets', 'PNG', 'Hitman 1', 'hitman1_gun.png'))
        self.original_image = pygame.image.load(image_path).convert_alpha()
        self.original_image = pygame.transform.scale(self.original_image, (self.size, self.size))

    def move(self, keys, camera_x, camera_y, smx, smy, joy_dx=0.0, joy_dy=0.0, joy_angle=None):
        # Handle speed boost timer
        if self.speed_boost_timer > 0:
            self.speed_boost_timer -= 1
            self.speed = self.base_speed * 1.75
        else:
            self.speed = self.base_speed
            
        new_x = self.x
        new_y = self.y

        if joy_dx != 0.0 or joy_dy != 0.0:
            new_x += joy_dx * self.speed
            new_y += joy_dy * self.speed
        else:
            if keys[pygame.K_w]: new_y -= self.speed
            if keys[pygame.K_s]: new_y += self.speed
            if keys[pygame.K_a]: new_x -= self.speed
            if keys[pygame.K_d]: new_x += self.speed
            
        if joy_angle is not None:
            self.angle = joy_angle
        else:
            # Specific Mouse Aiming taking into account the surface ZOOM scale
            dx = (smx + camera_x) - (self.x + self.size // 2)
            dy = (smy + camera_y) - (self.y + self.size // 2)
            if dx != 0 or dy != 0:
                self.angle = -math.degrees(math.atan2(dy, dx))

        # Check map grid bounds (collides with 1 Walls and 4 Barrier Boxes)
        if self._can_move(new_x, self.y): self.x = new_x
        if self._can_move(self.x, new_y): self.y = new_y

    def _can_move(self, x, y):
        tiles = [
            (y // TILE_SIZE, x // TILE_SIZE),
            (y // TILE_SIZE, (x + self.size) // TILE_SIZE),
            ((y + self.size) // TILE_SIZE, x // TILE_SIZE),
            ((y + self.size) // TILE_SIZE, (x + self.size) // TILE_SIZE)
        ]
        for ty, tx in tiles:
            if not (0 <= ty < len(map.grid) and 0 <= tx < len(map.grid[0])):
                return False
            # 1 is wall, 4 is barrier box
            if map.grid[int(ty)][int(tx)] in [1, 4]:
                return False
        return True

    def shoot(self, target_x, target_y):
        if self.ammo > 0:
            self.ammo -= 1
            return Bullet(self.x + self.size // 2, self.y + self.size // 2, target_x, target_y, 'player', 25)
        return None

    def take_damage(self, amount):
        self.health -= amount

    def heal(self, amount):
        self.health += amount
        if self.health > 100:
            self.health = 100

    def draw(self, screen, camera_x, camera_y):
        rotated_image = pygame.transform.rotate(self.original_image, self.angle)
        rect = rotated_image.get_rect(center=(self.x - camera_x + self.size // 2, self.y - camera_y + self.size // 2))
        screen.blit(rotated_image, rect.topleft)