# main.py

import pygame
from settings import *
from map import draw_map
from player import Player

# Initialize pygame
pygame.init()

# Create screen
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("The Great Heist")

# Clock (controls FPS)
clock = pygame.time.Clock()

# Create player
player = Player()

running = True
while running:
    clock.tick(FPS)

    # Event handling
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # --- INPUT ---
    keys = pygame.key.get_pressed()
    player.move(keys)

    # --- DRAW ---
    screen.fill(BLACK)

    draw_map(screen)
    player.draw(screen)

    # Update display
    pygame.display.flip()

# Quit properly
pygame.quit()