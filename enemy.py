# enemy.py

import os
import pygame
import math
import random
from bullets import Bullet
from settings import TILE_SIZE, resource_path
import map

class Enemy:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.size = 32
        self.health = 100
        self.speed = 3
        self.angle = 0
        
        # State machine
        self.state = "patrol" # patrol, attack, investigate
        self.target_x = self.x + random.randint(-150, 150)
        self.target_y = self.y + random.randint(-150, 150)
        self.sight_range = 300
        
        self.shoot_timer = 0
        self.shoot_delay = 60 # Frames between shots
        
        image_path = resource_path(os.path.join('assets', 'PNG', 'Soldier 1', 'soldier1_gun.png'))
        self.original_image = pygame.image.load(image_path).convert_alpha()
        self.original_image = pygame.transform.scale(self.original_image, (self.size, self.size))

    def update(self, player, enemies_list):
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

        # Behavior execution
        bullets_to_spawn = None
        if self.state == "attack":
            # face player
            self.angle = -math.degrees(math.atan2(dy, dx))
            
            # handle shooting
            if self.shoot_timer <= 0:
                bullets_to_spawn = Bullet(self.x + self.size//2, self.y + self.size//2, player.x, player.y, 'enemy', 15)
                self.shoot_timer = self.shoot_delay
            else:
                self.shoot_timer -= 1
        else:
            # face target
            tdx = self.target_x - self.x
            tdy = self.target_y - self.y
            self.angle = -math.degrees(math.atan2(tdy, tdx))
            
            # if arrived near target and not attacking
            if math.sqrt(tdx**2 + tdy**2) < 10:
                if self.state == "investigate":
                    self.state = "patrol"
                self.target_x = self.x + random.randint(-150, 150)
                self.target_y = self.y + random.randint(-150, 150)

        # Move towards target
        move_dx = self.target_x - self.x
        move_dy = self.target_y - self.y
        dist = math.sqrt(move_dx**2 + move_dy**2)
        
        if dist > 0:
            move_x = (move_dx / dist) * self.speed
            move_y = (move_dy / dist) * self.speed
            
            new_x = self.x + move_x
            e_rect_x = pygame.Rect(new_x, self.y, self.size, self.size)
            collided_x = False
            for other in enemies_list:
                if other != self:
                    if e_rect_x.colliderect(pygame.Rect(other.x, other.y, other.size, other.size)):
                        collided_x = True
                        break
            if not collided_x and self._can_move(new_x, self.y):
                self.x = new_x
            else:
                self.target_x = self.x + random.randint(-150, 150)
                
            new_y = self.y + move_y
            e_rect_y = pygame.Rect(self.x, new_y, self.size, self.size)
            collided_y = False
            for other in enemies_list:
                if other != self:
                    if e_rect_y.colliderect(pygame.Rect(other.x, other.y, other.size, other.size)):
                        collided_y = True
                        break
            if not collided_y and self._can_move(self.x, new_y):
                self.y = new_y
            else:
                self.target_y = self.y + random.randint(-150, 150)
                
        return bullets_to_spawn
        
    def investigate(self, x, y):
        self.state = "investigate"
        self.target_x = x
        self.target_y = y

    def take_damage(self, amount):
        self.health -= amount

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
            # Collide with wall (1) or box (4)
            if map.grid[int(ty)][int(tx)] in [1, 4]:
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
            if 0 <= grid_y < len(map.grid) and 0 <= grid_x < len(map.grid[0]):
                if map.grid[grid_y][grid_x] in [1, 4]: # Lines of sight blocked by boxes too
                    return False
        return True

    def draw(self, screen, camera_x, camera_y):
        rotated_image = pygame.transform.rotate(self.original_image, self.angle)
        rect = rotated_image.get_rect(center=(self.x - camera_x + self.size // 2, self.y - camera_y + self.size // 2))
        screen.blit(rotated_image, rect.topleft)
        
        if self.health < 100:
            pygame.draw.rect(screen, (255, 0, 0), (self.x - camera_x, self.y - camera_y - 10, self.size, 5))
            pygame.draw.rect(screen, (0, 255, 0), (self.x - camera_x, self.y - camera_y - 10, self.size * (self.health / 100), 5))