# player.py

import pygame
from settings import *

class Player:
    def __init__(self):
        self.x = 100
        self.y = 100
        self.size = 30
        self.speed = 5

    def move(self, keys):
        if keys[pygame.K_RIGHT]:
            self.x += self.speed
        if keys[pygame.K_LEFT]:
            self.x -= self.speed
        if keys[pygame.K_UP]:
            self.y -= self.speed
        if keys[pygame.K_DOWN]:
            self.y += self.speed

    def draw(self, screen):
        pygame.draw.rect(screen, (255, 0, 0), (self.x, self.y, self.size, self.size))