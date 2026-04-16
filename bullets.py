# bullets.py

import pygame
import math

class Bullet:
    def __init__(self, x, y, target_x, target_y, owner, damage):
        self.x = x
        self.y = y
        self.owner = owner # 'player' or 'enemy'
        self.damage = damage
        self.speed = 15
        self.size = 4
        
        dx = target_x - x
        dy = target_y - y
        dist = math.sqrt(dx**2 + dy**2)
        if dist == 0:
            self.dx, self.dy = 1, 0
        else:
            self.dx = dx / dist
            self.dy = dy / dist
            
        self.max_range = 600
        self.distance_travelled = 0

    def move(self):
        self.x += self.dx * self.speed
        self.y += self.dy * self.speed
        self.distance_travelled += self.speed

    def is_dead(self):
        return self.distance_travelled >= self.max_range

    def draw(self, screen, camera_x, camera_y):
        color = (255, 255, 0) if self.owner == 'player' else (255, 50, 50)
        pygame.draw.rect(screen, color, (int(self.x - camera_x), int(self.y - camera_y), self.size, self.size))