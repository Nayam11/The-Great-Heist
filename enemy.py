# enemy.py

import os
import math
import pygame
import random
from settings import *
from map import grid
from bullets import Bullet

class Enemy:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.size = 30
        self.speed = 2.5
        self.health = 100
        self.angle = 0
        
        # AI states
        self.state = "patrol" # patrol, attack, investigate
        self.target_x = x + random.randint(-150, 150)
        self.target_y = y + random.randint(-150, 150)
        self.sight_range = 300
        self.shoot_cooldown = 0
        
        image_path = os.path.join('assets', 'PNG', 'Soldier 1', 'soldier1_gun.png')
        self.original_image = pygame.image.load(image_path).convert_alpha()
        self.original_image = pygame.transform.scale(self.original_image, (self.size, self.size))

    def take_damage(self, amount):
        self.health -= amount
        
    def investigate(self, x, y):
        self.state = "investigate"
        self.target_x = x
        self.target_y = y

    def update(self, player):
        # Determine distance to player
        dx = player.x - self.x
        dy = player.y - self.y
        dist_to_player = math.sqrt(dx**2 + dy**2)
        
        if dist_to_player <= self.sight_range and self.has_line_of_sight(player):
            self.state = "attack"
            self.target_x = player.x
            self.target_y = player.y
        elif self.state == "attack": # lost sight
            self.state = "investigate" # go to last known loc
            
        move_x, move_y = 0, 0
        tx = self.target_x - self.x
        ty = self.target_y - self.y
        dist_to_target = math.sqrt(tx**2 + ty**2)
        
        if dist_to_target > 5:
            move_x = (tx / dist_to_target) * self.speed
            move_y = (ty / dist_to_target) * self.speed
            self.angle = -math.degrees(math.atan2(ty, tx))
        else:
            if self.state in ["patrol", "investigate"]:
                self.state = "patrol"
                self.target_x = self.x + random.randint(-150, 150)
                self.target_y = self.y + random.randint(-150, 150)
                
        # Basic collision check (using map grid)
        new_x = self.x + move_x
        if self._can_move(new_x, self.y):
            self.x = new_x
        else:
            self.target_x = self.x + random.randint(-150, 150)
            
        new_y = self.y + move_y
        if self._can_move(self.x, new_y):
            self.y = new_y
        else:
            self.target_y = self.y + random.randint(-150, 150)

        # Shooting mechanics
        if self.shoot_cooldown > 0:
            self.shoot_cooldown -= 1
            
        if self.state == "attack" and self.shoot_cooldown == 0:
            self.shoot_cooldown = 60 # wait 60 frames (1 sec approx) to shoot
            return self.shoot(player.x + player.size//2, player.y + player.size//2)
            
        return None

    def shoot(self, target_x, target_y):
        return Bullet(self.x + self.size // 2, self.y + self.size // 2, target_x, target_y, 'enemy', 15)

    def _can_move(self, x, y):
        # Check all 4 corners
        left, right = x, x + self.size
        top, bottom = y, y + self.size
        
        tiles = [
            (top // TILE_SIZE, left // TILE_SIZE),
            (top // TILE_SIZE, right // TILE_SIZE),
            (bottom // TILE_SIZE, left // TILE_SIZE),
            (bottom // TILE_SIZE, right // TILE_SIZE),
        ]
        
        for ty, tx in tiles:
            if not (0 <= ty < len(grid) and 0 <= tx < len(grid[0])):
                return False
            if grid[int(ty)][int(tx)] == 1:
                return False
        return True

    def has_line_of_sight(self, player):
        x1, y1 = self.x + self.size // 2, self.y + self.size // 2
        x2, y2 = player.x + player.size // 2, player.y + player.size // 2

        dist = math.sqrt((x2 - x1)**2 + (y2 - y1)**2)
        if dist == 0: return True
        
        steps = int(dist / (TILE_SIZE / 2))
        if steps == 0: return True
        
        dx = (x2 - x1) / steps
        dy = (y2 - y1) / steps
        
        cx, cy = x1, y1
        for _ in range(steps):
            cx += dx
            cy += dy
            grid_y = int(cy // TILE_SIZE)
            grid_x = int(cx // TILE_SIZE)
            if 0 <= grid_y < len(grid) and 0 <= grid_x < len(grid[0]):
                if grid[grid_y][grid_x] == 1:
                    return False
        return True

    def draw(self, screen, camera_x, camera_y):
        rotated_image = pygame.transform.rotate(self.original_image, self.angle)
        rect = rotated_image.get_rect(center=(self.x - camera_x + self.size // 2, self.y - camera_y + self.size // 2))
        screen.blit(rotated_image, rect.topleft)
        
        if self.health < 100:
            pygame.draw.rect(screen, (255, 0, 0), (self.x - camera_x, self.y - camera_y - 10, self.size, 5))
            pygame.draw.rect(screen, (0, 255, 0), (self.x - camera_x, self.y - camera_y - 10, self.size * (self.health / 100), 5))