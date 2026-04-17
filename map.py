# map.py

import os
import pygame
import random
from settings import TILE_SIZE, resource_path

map_width = 50
map_height = 30
grid = []

FLOOR_IMG = None
WALL_IMG = None
BOX_IMG = None

def generate_map(level):
    global grid
    grid = [[0 for _ in range(map_width)] for _ in range(map_height)]
    
    # Border walls
    for i in range(map_width):
        grid[0][i] = 1
        grid[map_height-1][i] = 1
    for i in range(map_height):
        grid[i][0] = 1
        grid[i][map_width-1] = 1
        
    # Generate Rooms with Gates dynamically
    num_rooms = min(15, 3 + int(level * 1.5))
    for _ in range(num_rooms):
        room_w = random.randint(5, 12)
        room_h = random.randint(5, 12)
        start_x = random.randint(2, map_width - room_w - 2)
        start_y = random.randint(2, map_height - room_h - 2)
        
        # Build square structures
        for rx in range(room_w):
            grid[start_y][start_x + rx] = 1
            grid[start_y + room_h - 1][start_x + rx] = 1
        for ry in range(room_h):
            grid[start_y + ry][start_x] = 1
            grid[start_y + ry][start_x + room_w - 1] = 1
            
        # Punch holes (gates) into the room
        for _ in range(random.randint(1, 3)):
            gate_side = random.randint(0, 3)
            # 0: top, 1: bot, 2: left, 3: right
            if gate_side == 0: grid[start_y][start_x + random.randint(1, room_w-2)] = 0
            elif gate_side == 1: grid[start_y + room_h - 1][start_x + random.randint(1, room_w-2)] = 0
            elif gate_side == 2: grid[start_y + random.randint(1, room_h-2)][start_x] = 0
            elif gate_side == 3: grid[start_y + random.randint(1, room_h-2)][start_x + room_w - 1] = 0

    # Place defensive Barrier Boxes randomly
    for _ in range(10 + level * 2):
        rx, ry = random.randint(2, map_width-3), random.randint(2, map_height-3)
        if grid[ry][rx] == 0: grid[ry][rx] = 4

    # Highly restricted Powerups
    if random.random() < 0.4: # Only 40% chance to spawn a Health Potion per level
        while True:
            rx, ry = random.randint(2, map_width-3), random.randint(2, map_height-3)
            if grid[ry][rx] == 0: 
                grid[ry][rx] = 5
                break
                
    if random.random() < 0.25: # Only 25% chance to spawn a Speed Potion
        while True:
            rx, ry = random.randint(2, map_width-3), random.randint(2, map_height-3)
            if grid[ry][rx] == 0: 
                grid[ry][rx] = 6
                break

    # Spawn Exit Door
    door_placed = False
    while not door_placed:
        dx = random.randint(2, map_width - 3)
        dy = random.randint(2, map_height - 3)
        if grid[dy][dx] == 0:
            grid[dy][dx] = 3
            door_placed = True

    # Run flood fill to guarantee connectivity
    ensure_connected()

    # Spawn scaling Gold clusters
    num_gold = min(15, 2 + level)
    for _ in range(num_gold):
        gx = random.randint(2, map_width - 3)
        gy = random.randint(2, map_height - 3)
        if grid[gy][gx] == 0:
            grid[gy][gx] = 2

def ensure_connected():
    global grid
    # Find first empty floor tile to seed fill
    sr, sc = -1, -1
    for r in range(2, map_height-2):
        for c in range(2, map_width-2):
            if grid[r][c] == 0:
                sr, sc = r, c
                break
        if sr != -1: break
        
    if sr == -1: return

    visited = set()
    queue = [(sr, sc)]
    visited.add((sr, sc))
    
    while queue:
        r, c = queue.pop(0)
        for dr, dc in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
            nr, nc = r + dr, c + dc
            if 0 < nr < map_height-1 and 0 < nc < map_width-1:
                if grid[nr][nc] != 1 and (nr, nc) not in visited: # Treat everything not wall (1) as navigable floor
                    visited.add((nr, nc))
                    queue.append((nr, nc))
                    
    # Now check all empty floor tiles; if any are unvisited, forcibly carve a path
    for r in range(1, map_height-1):
        for c in range(1, map_width-1):
            if grid[r][c] != 1 and (r, c) not in visited:
                dist_best = float('inf')
                br, bc = -1, -1
                for (vr, vc) in visited:
                    if abs(vr-r) + abs(vc-c) < dist_best:
                        dist_best = abs(vr-r) + abs(vc-c)
                        br, bc = vr, vc
                
                # Carve straight line to best visited node
                if br != -1 and bc != -1:
                    cx, cy = c, r
                    while cx != bc or cy != br:
                        if cx != bc: cx += 1 if bc > cx else -1
                        elif cy != br: cy += 1 if br > cy else -1
                        grid[cy][cx] = 0
                        visited.add((cy, cx))

def load_map_assets():
    global FLOOR_IMG, WALL_IMG, BOX_IMG
    if FLOOR_IMG is None:
        try:
            FLOOR_IMG = pygame.transform.scale(pygame.image.load(resource_path(os.path.join('assets', 'PNG', 'Tiles', 'tile_01.png'))).convert_alpha(), (TILE_SIZE, TILE_SIZE))
            WALL_IMG = pygame.transform.scale(pygame.image.load(resource_path(os.path.join('assets', 'PNG', 'Tiles', 'tile_11.png'))).convert_alpha(), (TILE_SIZE, TILE_SIZE))
        except:
            FLOOR_IMG = pygame.Surface((TILE_SIZE, TILE_SIZE))
            FLOOR_IMG.fill((50, 150, 50))
            WALL_IMG = pygame.Surface((TILE_SIZE, TILE_SIZE))
            WALL_IMG.fill((100, 100, 100))
            
    if BOX_IMG is None:
        try:
            BOX_IMG = pygame.image.load(resource_path(os.path.join('assets', 'box.png'))).convert_alpha()
            BOX_IMG = pygame.transform.scale(BOX_IMG, (TILE_SIZE, TILE_SIZE))
        except:
            pass

def draw_map(screen, camera_x, camera_y):
    load_map_assets()

    for row in range(len(grid)):
        for col in range(len(grid[row])):
            tile = grid[row][col]

            x = col * TILE_SIZE
            y = row * TILE_SIZE

            if tile != 1 and tile != 4:
                # Floor underneath
                screen.blit(FLOOR_IMG, (x - camera_x, y - camera_y))
                
            if tile == 1:
                screen.blit(WALL_IMG, (x - camera_x, y - camera_y))
            elif tile == 4:
                # Barrier box logic - draws floor AND block
                screen.blit(FLOOR_IMG, (x - camera_x, y - camera_y))
                if BOX_IMG:
                    screen.blit(BOX_IMG, (x - camera_x, y - camera_y))
                else:
                    pygame.draw.rect(screen, (139, 69, 19), (x - camera_x, y - camera_y, TILE_SIZE, TILE_SIZE))