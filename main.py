# main.py

import sys
import math
import pygame
from settings import *
from map import grid, draw_map
from player import Player
from enemy import Enemy

# Initialize pygame
pygame.init()

# Grab the native display size and setup FULLSCREEN
infoObject = pygame.display.Info()
WIDTH, HEIGHT = infoObject.current_w, infoObject.current_h
screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.FULLSCREEN)
pygame.display.set_caption("The Great Heist")

# Clock (controls FPS)
clock = pygame.time.Clock()

# Create player
player = Player()

# Spawn items from the grid layout
gold_items = []
exit_door = None

for r in range(len(grid)):
    for c in range(len(grid[r])):
        if grid[r][c] == 2:
            gold_items.append(pygame.Rect(c * TILE_SIZE, r * TILE_SIZE, TILE_SIZE, TILE_SIZE))
        elif grid[r][c] == 3:
            exit_door = pygame.Rect(c * TILE_SIZE, r * TILE_SIZE, TILE_SIZE, TILE_SIZE)

# Create enemies manually
enemies = []
enemies.append(Enemy(600, 200))
enemies.append(Enemy(800, 300))
enemies.append(Enemy(600, 800))
enemies.append(Enemy(1100, 800))

bullets = []

game_state = "playing" # playing, won, lost
font = pygame.font.SysFont(None, 48)

camera_x = 0
camera_y = 0

running = True
while running:
    clock.tick(FPS)

    # Event handling
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                running = False
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if game_state == "playing":
                mx, my = pygame.mouse.get_pos()
                bullets.append(player.shoot(mx + camera_x, my + camera_y))

    if game_state == "playing":
        # --- INPUT ---
        keys = pygame.key.get_pressed()
        player.move(keys, camera_x, camera_y)
        
        # --- CAMERA UPDATES ---
        camera_x = player.x - WIDTH // 2 + player.size // 2
        camera_y = player.y - HEIGHT // 2 + player.size // 2
        
        max_x = len(grid[0]) * TILE_SIZE - WIDTH
        max_y = len(grid) * TILE_SIZE - HEIGHT
        
        camera_x = max(0, min(camera_x, max(0, max_x)))
        camera_y = max(0, min(camera_y, max(0, max_y)))
        
        p_rect = pygame.Rect(player.x, player.y, player.size, player.size)

        # Collect gold
        for g_rect in gold_items[:]:
            if p_rect.colliderect(g_rect):
                gold_items.remove(g_rect)

        # Win condition (Exit Door)
        if exit_door and p_rect.colliderect(exit_door):
            if len(gold_items) == 0 and len(enemies) == 0:
                game_state = "won"

        # Enemies update
        for enemy in enemies:
            new_b = enemy.update(player)
            if new_b: # enemy decides to shoot
                bullets.append(new_b)

        # Bullets logic
        for b in bullets[:]:
            b.move()
            if b.is_dead():
                bullets.remove(b)
                continue
                
            b_rect = pygame.Rect(b.x, b.y, b.size, b.size)
            
            # Check bullet wall collision
            hit_wall = False
            for ty in range(len(grid)):
                for tx in range(len(grid[ty])):
                    if grid[ty][tx] == 1:
                        w_rect = pygame.Rect(tx * TILE_SIZE, ty * TILE_SIZE, TILE_SIZE, TILE_SIZE)
                        if b_rect.colliderect(w_rect):
                            hit_wall = True
                            break
                if hit_wall: break
            if hit_wall:
                bullets.remove(b)
                continue

            # Check bullet entity collision
            if b.owner == 'player':
                for enemy in enemies[:]:
                    e_rect = pygame.Rect(enemy.x, enemy.y, enemy.size, enemy.size)
                    if b_rect.colliderect(e_rect):
                        enemy.take_damage(b.damage)
                        bullets.remove(b)
                        if enemy.health <= 0:
                            enemies.remove(enemy)
                            # Alert nearest enemy!
                            if enemies:
                                nearest = min(enemies, key=lambda e: math.sqrt((e.x - enemy.x)**2 + (e.y - enemy.y)**2))
                                nearest.investigate(enemy.x, enemy.y)
                        break # stop calculating for this bullet
            elif b.owner == 'enemy':
                if b_rect.colliderect(p_rect):
                    player.take_damage(b.damage)
                    bullets.remove(b)
                    if player.health <= 0:
                        game_state = "lost"

    # --- DRAW ---
    screen.fill(BLACK)
    draw_map(screen, int(camera_x), int(camera_y))
    
    # Draw logic for interactive tiles
    for g in gold_items:
        pygame.draw.circle(screen, YELLOW, (int(g.centerx - camera_x), int(g.centery - camera_y)), TILE_SIZE // 3)
    
    if exit_door:
        # It glows Green if everything is clear, Red if blocked
        door_color = GREEN if (len(gold_items) == 0 and len(enemies) == 0) else (150, 0, 0)
        draw_door = pygame.Rect(exit_door.left - camera_x, exit_door.top - camera_y, exit_door.width, exit_door.height)
        pygame.draw.rect(screen, door_color, draw_door)

    # Draw entities
    if game_state == "playing":
        player.draw(screen, int(camera_x), int(camera_y))
        for enemy in enemies:
            enemy.draw(screen, int(camera_x), int(camera_y))
        for b in bullets:
            b.draw(screen, int(camera_x), int(camera_y))
            
        # Draw UI (Static, NO CAMERA OFFSET)
        pygame.draw.rect(screen, (255, 0, 0), (10, 10, 200, 20))
        pygame.draw.rect(screen, GREEN, (10, 10, max(0, player.health) * 2, 20))
        h_text = font.render(f"Health: {player.health} | Gold Remaining: {len(gold_items)} | Enemies Remaining: {len(enemies)}", True, WHITE)
        screen.blit(h_text, (220, 5))
        
    elif game_state == "won":
        text = font.render("HEIST SUCCESSFUL! YOU ESCAPED! (Press ESC)", True, GREEN)
        screen.blit(text, (WIDTH // 2 - text.get_width() // 2, HEIGHT // 2))
    elif game_state == "lost":
        text = font.render("WASTED. PRESS ESC TO QUIT.", True, (255, 0, 0))
        screen.blit(text, (WIDTH // 2 - text.get_width() // 2, HEIGHT // 2))

    # Update display
    pygame.display.flip()

# Quit properly
pygame.quit()
sys.exit()