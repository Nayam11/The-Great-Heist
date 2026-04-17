# bullets.py

import os
import pygame
import math

from settings import resource_path

BULLET_IMG = None

class Bullet:
    def __init__(self, x, y, target_x, target_y, owner, damage):
        global BULLET_IMG
        if BULLET_IMG is None:
            path = resource_path(os.path.join('assets', 'bullet.png'))
            BULLET_IMG = pygame.image.load(path).convert()
            BULLET_IMG.set_colorkey((0, 0, 0)) # Makes black background transparent
            BULLET_IMG = pygame.transform.scale(BULLET_IMG, (15, 15))

        self.x = x
        self.y = y
        self.owner = owner # 'player' or 'enemy'
        self.damage = damage
        self.speed = 15
        self.size = 8
        
        dx = target_x - x
        dy = target_y - y
        dist = math.sqrt(dx**2 + dy**2)
        if dist == 0:
            self.dx, self.dy = 1, 0
        else:
            self.dx = dx / dist
            self.dy = dy / dist
            
        self.angle = -math.degrees(math.atan2(dy, dx))
        
        # Enemy bullets get a subtle red hue if possible, but for now we just use the sprite
        self.image = pygame.transform.rotate(BULLET_IMG, self.angle)
            
        self.max_range = 600
        self.distance_travelled = 0

    def move(self):
        self.x += self.dx * self.speed
        self.y += self.dy * self.speed
        self.distance_travelled += self.speed

    def is_dead(self):
        return self.distance_travelled >= self.max_range

    def draw(self, screen, camera_x, camera_y):
        rect = self.image.get_rect(center=(int(self.x - camera_x), int(self.y - camera_y)))
        screen.blit(self.image, rect.topleft)