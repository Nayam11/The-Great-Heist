# main.py

import pygame
from settings import *

# Initialize pygame
pygame.init()

# Create screen
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("The Great Heist")

# Clock (controls FPS)
clock = pygame.time.Clock()

running = True
while running:
    clock.tick(FPS)

    # Event handling
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # Draw
    screen.fill(BLACK)

    # Update display
    pygame.display.flip()

# Quit properly
pygame.quit()