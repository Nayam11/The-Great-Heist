# enemy.py

import pygame
from settings import *

class Enemy:
    def __init__(self):
        self.path = [(200, 200), (400, 200), (400, 400), (200, 400)]
        self.current_point = 0

        self.x, self.y = self.path[self.current_point]
        self.speed = 2
        self.size = 30

    def move(self):
        target_x, target_y = self.path[self.current_point]

        # Move towards target
        if self.x < target_x:
            self.x += self.speed
        elif self.x > target_x:
            self.x -= self.speed

        if self.y < target_y:
            self.y += self.speed
        elif self.y > target_y:
            self.y -= self.speed

        # Check if reached point
        if abs(self.x - target_x) < self.speed and abs(self.y - target_y) < self.speed:
            self.current_point = (self.current_point + 1) % len(self.path)

    def draw(self, screen):
        pygame.draw.rect(screen, (0, 0, 255), (self.x, self.y, self.size, self.size))