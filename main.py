# main.py

import os
import sys
import math
import platform
import pygame
import firebase_db
from settings import *
import map
from player import Player
from enemy import Enemy

# Initialize pygame
pygame.init()
pygame.mixer.init()

# Android-Safe Display Logic: Try to get info, but use hard defaults if it returns 0
infoObject = pygame.display.Info()
WIDTH, HEIGHT = infoObject.current_w, infoObject.current_h
if WIDTH <= 0 or HEIGHT <= 0:
    WIDTH, HEIGHT = 1280, 720 # Safe landscape default

screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.FULLSCREEN)
pygame.display.set_caption("The Great Heist")

# Dynamic UI Scaling Helpers
# We use 1280x720 as the 'Base' for scaling font sizes and box widths
# CAP the scale to prevent oversized text on giant screens
UI_SCALE = min(min(WIDTH/1280, HEIGHT/720), 1.25)

def get_font(size):
    scaled_size = int(size * UI_SCALE)
    try:
        return pygame.font.Font(pygame.font.get_default_font(), scaled_size)
    except:
        return pygame.font.SysFont(None, scaled_size)

font = get_font(36) # Reduced from 48
title_font = get_font(64) # Reduced from 96
small_font = get_font(28) # Reduced from 32
tiny_font = get_font(20) # Reduced from 24

GAME_ZOOM = 1.35 # Pixel Art Zoom for World
UI_ZOOM = 1.0     # Sharp 1:1 Scale for Menus

# Shared scaling references
RENDER_W, RENDER_H = WIDTH, HEIGHT
render_surf = pygame.Surface((WIDTH, HEIGHT))

def update_viewport(zoom_level):
    global RENDER_W, RENDER_H, render_surf
    new_w = int(WIDTH / zoom_level)
    new_h = int(HEIGHT / zoom_level)
    if new_w != RENDER_W or new_h != RENDER_H:
        RENDER_W, RENDER_H = new_w, new_h
        render_surf = pygame.Surface((RENDER_W, RENDER_H))

update_viewport(UI_ZOOM) # Init for Login

clock = pygame.time.Clock()

GOLD_IMG = None
HP_IMG = None
SP_IMG = None
SHOOT_SND = None
HIT_SND = None
KACHING_SND = None

unlocked_levels = 1
current_level = 1

player = Player()
gold_items = []
hp_potions = []
sp_potions = []
exit_door = None
enemies = []
bullets = []

def load_assets():
    global GOLD_IMG, HP_IMG, SP_IMG, SHOOT_SND, HIT_SND, KACHING_SND
    if GOLD_IMG is None:
        try: GOLD_IMG = pygame.image.load(resource_path(os.path.join('assets', 'gold.png'))).convert_alpha()
        except: pass
    if HP_IMG is None:
        try: HP_IMG = pygame.image.load(resource_path(os.path.join('assets', 'health_potion.png'))).convert_alpha()
        except: pass
    if SP_IMG is None:
        try: SP_IMG = pygame.image.load(resource_path(os.path.join('assets', 'speed_potion.png'))).convert_alpha()
        except: pass
        
    if SHOOT_SND is None:
        try: SHOOT_SND = pygame.mixer.Sound(resource_path(os.path.join('assets', 'shoot.wav')))
        except: pass
    if HIT_SND is None:
        try: HIT_SND = pygame.mixer.Sound(resource_path(os.path.join('assets', 'hit.wav')))
        except: pass
    if KACHING_SND is None:
        try: KACHING_SND = pygame.mixer.Sound(resource_path(os.path.join('assets', 'kaching.wav')))
        except: pass

def play_sound(snd):
    if snd: snd.play()

def start_new_level(level_idx):
    global gold_items, hp_potions, sp_potions, exit_door, enemies, bullets, player
    
    map.generate_map(level_idx)
    
    player = Player()
    player.ammo = 5 + (level_idx * 2) 
    
    for r in range(2, len(map.grid)):
        for c in range(2, len(map.grid[0])):
            if map.grid[r][c] == 0:
                player.x = c * TILE_SIZE
                player.y = r * TILE_SIZE
                break
        else: continue
        break
        
    gold_items.clear()
    hp_potions.clear()
    sp_potions.clear()
    enemies.clear()
    bullets.clear()
    
    for r in range(len(map.grid)):
        for c in range(len(map.grid[r])):
            if map.grid[r][c] == 2:
                gold_items.append(pygame.Rect(c * TILE_SIZE, r * TILE_SIZE, TILE_SIZE, TILE_SIZE))
                map.grid[r][c] = 0
            elif map.grid[r][c] == 3:
                exit_door = pygame.Rect(c * TILE_SIZE, r * TILE_SIZE, TILE_SIZE, TILE_SIZE)
                map.grid[r][c] = 0
            elif map.grid[r][c] == 5:
                hp_potions.append(pygame.Rect(c * TILE_SIZE, r * TILE_SIZE, TILE_SIZE, TILE_SIZE))
                map.grid[r][c] = 0
            elif map.grid[r][c] == 6:
                sp_potions.append(pygame.Rect(c * TILE_SIZE, r * TILE_SIZE, TILE_SIZE, TILE_SIZE))
                map.grid[r][c] = 0

    all_empty_tiles = [(r, c) for r in range(len(map.grid)) for c in range(len(map.grid[0])) if map.grid[r][c] == 0]
    safe_spawns = [(r, c) for (r, c) in all_empty_tiles if math.sqrt((c * TILE_SIZE - player.x)**2 + (r * TILE_SIZE - player.y)**2) > 350]
    import random
    random.shuffle(safe_spawns)

    num_enemies = min(15, 2 + int(level_idx * 1.5))
    num_to_spawn = min(num_enemies, len(safe_spawns))
    
    for i in range(num_to_spawn):
        r, c = safe_spawns[i]
        new_e = Enemy(c * TILE_SIZE, r * TILE_SIZE)
        new_e.speed += (level_idx * 0.1)
        enemies.append(new_e)

def draw_centered_text(surface, text, font, color, y_pos):
    img = font.render(text, True, color)
    rect = img.get_rect(center=(surface.get_width() // 2, y_pos))
    surface.blit(img, rect)
    return rect

game_state = "landing" # 'landing', 'login', 'menu', 'guide', 'options', 'levels', 'playing', 'won', 'lost'
camera_x, camera_y = 0, 0
landing_camera_x = 0
global_volume = 1.0

# Mobile OS Detection System
is_mobile_os = ('ANDROID_ARGUMENT' in os.environ) or (platform.system().lower() in ['android', 'ios'])
control_mode = "MOBILE" if is_mobile_os else "PC"

# Twin-Stick Virtual Joypad Native Data Arrays
left_joy_center = (120, HEIGHT - 150)
right_joy_center = (WIDTH - 120, HEIGHT - 150)
joy_radius = 80
knob_radius = 35

left_touch_id = None
right_touch_id = None
left_knob_pos = list(left_joy_center)
right_knob_pos = list(right_joy_center)

joy_dx, joy_dy = 0.0, 0.0
joy_angle = None
auto_shoot_timer = 0


# Security Login Variables
username_text = ""
password_text = ""
active_field = "username" # 'username' or 'password'
show_password = False
user_box_rect = pygame.Rect(0, 0, 0, 0)
pass_box_rect = pygame.Rect(0, 0, 0, 0)
view_pass_btn = pygame.Rect(0, 0, 0, 0)

level_rects = {}

running = True
while running:
    clock.tick(FPS)
    load_assets()

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                if game_state == "playing": game_state = "menu"
                else: running = False
            
            # Keyboard tracker handling Multi-Field Login inputs
            if game_state == "login":
                if event.key == pygame.K_TAB or event.key == pygame.K_DOWN or event.key == pygame.K_UP:
                    active_field = "password" if active_field == "username" else "username"
                elif event.key == pygame.K_BACKSPACE:
                    if active_field == "username": username_text = username_text[:-1]
                    else: password_text = password_text[:-1]
                elif event.key == pygame.K_RETURN:
                    if len(username_text) > 0 and len(password_text) > 0 and firebase_db.login_status not in ["loading", "success"]:
                        firebase_db.login_async(username_text, password_text)
                else:
                    if active_field == "username" and len(username_text) < 15 and event.unicode.isalnum():
                        username_text += event.unicode
                    elif active_field == "password" and len(password_text) < 15 and event.unicode.isprintable():
                        password_text += event.unicode
                        
        # Multi-Touch FINGER routines for Android natively executing Joystick manipulations
        if event.type == pygame.FINGERDOWN or event.type == pygame.FINGERMOTION:
            if control_mode == "MOBILE" and game_state == "playing":
                fx, fy = event.x * WIDTH, event.y * HEIGHT
                if fx < WIDTH / 2: # Left Half of Phone glass
                    left_touch_id = event.finger_id
                    dist = math.hypot(fx - left_joy_center[0], fy - left_joy_center[1])
                    if dist < joy_radius:
                        left_knob_pos = [fx, fy]
                        joy_dx = (fx - left_joy_center[0]) / joy_radius
                        joy_dy = (fy - left_joy_center[1]) / joy_radius
                    else:
                        angle = math.atan2(fy - left_joy_center[1], fx - left_joy_center[0])
                        left_knob_pos = [left_joy_center[0] + math.cos(angle) * joy_radius, left_joy_center[1] + math.sin(angle) * joy_radius]
                        joy_dx = math.cos(angle)
                        joy_dy = math.sin(angle)
                else: # Right Half of Phone glass
                    right_touch_id = event.finger_id
                    dist = math.hypot(fx - right_joy_center[0], fy - right_joy_center[1])
                    if dist < joy_radius: 
                        right_knob_pos = [fx, fy]
                    else:
                        angle = math.atan2(fy - right_joy_center[1], fx - right_joy_center[0])
                        right_knob_pos = [right_joy_center[0] + math.cos(angle) * joy_radius, right_joy_center[1] + math.sin(angle) * joy_radius]
                    # Right stick absolutely maps directly to Character Angulation
                    joy_angle = -math.degrees(math.atan2(right_knob_pos[1] - right_joy_center[1], right_knob_pos[0] - right_joy_center[0]))
                    
        if event.type == pygame.FINGERUP:
            if control_mode == "MOBILE" and game_state == "playing":
                if event.finger_id == left_touch_id:
                    left_touch_id = None
                    left_knob_pos = list(left_joy_center)
                    joy_dx, joy_dy = 0.0, 0.0
                elif event.finger_id == right_touch_id:
                    right_touch_id = None
                    right_knob_pos = list(right_joy_center)
                    joy_angle = None
                
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            curr_zoom = GAME_ZOOM if game_state == "playing" else UI_ZOOM
            mx, my = pygame.mouse.get_pos()
            smx, smy = mx / curr_zoom, my / curr_zoom
            
            if game_state == "landing":
                game_state = "login"
                
            elif game_state == "login":
                # Handle field target clicks
                if user_box_rect.collidepoint((smx, smy)): active_field = "username"
                if pass_box_rect.collidepoint((smx, smy)): active_field = "password"
                if view_pass_btn.collidepoint((smx, smy)): show_password = not show_password
                
                # Evaluation processing
                if firebase_db.login_status in ["idle", "wrong_password", "error"] and len(username_text) > 0 and len(password_text) > 0:
                    if 'login_btn' in locals() and login_btn.collidepoint((smx, smy)):
                        firebase_db.login_async(username_text, password_text)
                if firebase_db.login_status == "error":
                    if 'cont_btn' in locals() and cont_btn.collidepoint((smx, smy)):
                        firebase_db.cached_unlocked_levels = 1
                        unlocked_levels = 1
                        game_state = "menu"
                
            elif game_state == "menu":
                if start_btn.collidepoint((smx, smy)):
                    game_state = "levels"
                elif guide_btn.collidepoint((smx, smy)):
                    game_state = "guide"
                elif options_btn.collidepoint((smx, smy)):
                    game_state = "options"
                elif quit_btn.collidepoint((smx, smy)):
                    running = False
                    
            elif game_state == "guide":
                if back_btn.collidepoint((smx, smy)):
                    game_state = "menu"
                    
            elif game_state == "levels":
                if back_btn.collidepoint((smx, smy)):
                    game_state = "menu"
                else:
                    for lv_idx, rect in level_rects.items():
                        if rect.collidepoint((smx, smy)) and lv_idx <= unlocked_levels:
                            current_level = lv_idx
                            start_new_level(current_level)
                            game_state = "playing"
                            
            elif game_state == "options":
                if back_btn.collidepoint((smx, smy)):
                    game_state = "menu"
                elif vol_up_btn.collidepoint((smx, smy)):
                    global_volume = min(1.0, global_volume + 0.1)
                elif vol_down_btn.collidepoint((smx, smy)):
                    global_volume = max(0.0, global_volume - 0.1)
                elif 'ctrl_mode_btn' in locals() and ctrl_mode_btn.collidepoint((smx, smy)):
                    control_mode = "MOBILE" if control_mode == "PC" else "PC"
                    
                pygame.mixer.music.set_volume(global_volume)
                if SHOOT_SND: SHOOT_SND.set_volume(global_volume)
                if HIT_SND: HIT_SND.set_volume(global_volume)
                if KACHING_SND: KACHING_SND.set_volume(global_volume)
                    
            elif game_state == "playing" and control_mode == "PC":
                b = player.shoot(smx + camera_x, smy + camera_y)
                if b:
                    bullets.append(b)
                    play_sound(SHOOT_SND)
                
            elif game_state in ["won", "lost"]:
                if game_state == "won" and unlocked_levels == current_level and unlocked_levels < 20:
                    unlocked_levels += 1 # Unlock next map!
                    # Sync to Firebase automatically!
                    if username_text:
                        firebase_db.save_progress_async(username_text, unlocked_levels)
                game_state = "levels"

    curr_zoom = GAME_ZOOM if game_state == "playing" else UI_ZOOM
    update_viewport(curr_zoom)

    if game_state == "playing":
        keys = pygame.key.get_pressed()
        
        mx, my = pygame.mouse.get_pos()
        smx, smy = mx / curr_zoom, my / curr_zoom
        
        if control_mode == "MOBILE":
            # Fire Float Vectors natively
            player.move(keys, camera_x, camera_y, smx, smy, joy_dx, joy_dy, joy_angle)
            
            # Auto-Shoot Mechanics dynamically triggering on Thumb-Pull deadzones
            if right_touch_id is not None and joy_angle is not None:
                auto_shoot_timer -= 1
                if auto_shoot_timer <= 0:
                    rad = math.radians(-joy_angle)
                    tx = player.x + player.size//2 + math.cos(rad) * 100
                    ty = player.y + player.size//2 + math.sin(rad) * 100
                    b = player.shoot(tx, ty)
                    if b:
                        bullets.append(b)
                        play_sound(SHOOT_SND)
                        auto_shoot_timer = int(FPS * 0.15) # Blistering 6.6 rounds per second
        else:
            player.move(keys, camera_x, camera_y, smx, smy) 
            
        camera_x = player.x - RENDER_W // 2 + player.size // 2
        camera_y = player.y - RENDER_H // 2 + player.size // 2
        
        max_x = len(map.grid[0]) * TILE_SIZE - RENDER_W
        max_y = len(map.grid) * TILE_SIZE - RENDER_H
        
        camera_x = max(0, min(camera_x, max(0, max_x)))
        camera_y = max(0, min(camera_y, max(0, max_y)))
        
        p_rect = pygame.Rect(player.x, player.y, player.size, player.size)

        for g_rect in gold_items[:]:
            if p_rect.colliderect(g_rect):
                gold_items.remove(g_rect)
                play_sound(KACHING_SND)
                
        for hp in hp_potions[:]:
            if p_rect.colliderect(hp):
                player.heal(20)
                hp_potions.remove(hp)
                play_sound(KACHING_SND)
                
        for sp in sp_potions[:]:
            if p_rect.colliderect(sp):
                player.speed_boost_timer = FPS * 5
                sp_potions.remove(sp)
                play_sound(KACHING_SND)

        if exit_door and p_rect.colliderect(exit_door):
            if len(gold_items) == 0 and len(enemies) == 0:
                game_state = "won"

        for enemy in enemies:
            new_b = enemy.update(player, enemies)
            if new_b: 
                bullets.append(new_b)
                play_sound(SHOOT_SND)

        for b in bullets[:]:
            b.move()
            if b.is_dead():
                bullets.remove(b)
                continue
                
            b_rect = pygame.Rect(b.x, b.y, b.size, b.size)
            
            bx = int(b.x // TILE_SIZE)
            by = int(b.y // TILE_SIZE)
            
            if 0 <= by < len(map.grid) and 0 <= bx < len(map.grid[0]):
                if map.grid[by][bx] in [1, 4]:
                    bullets.remove(b)
                    continue
            else:
                bullets.remove(b)
                continue

            if b.owner == 'player':
                for enemy in enemies[:]:
                    e_rect = pygame.Rect(enemy.x, enemy.y, enemy.size, enemy.size)
                    if b_rect.colliderect(e_rect):
                        enemy.take_damage(b.damage)
                        bullets.remove(b)
                        play_sound(HIT_SND)
                        if enemy.health <= 0:
                            enemies.remove(enemy)
                            player.ammo += 5
                            if enemies:
                                nearest = min(enemies, key=lambda e: math.sqrt((e.x - enemy.x)**2 + (e.y - enemy.y)**2))
                                nearest.investigate(enemy.x, enemy.y)
                        break
            elif b.owner == 'enemy':
                if b_rect.colliderect(p_rect):
                    player.take_damage(b.damage)
                    bullets.remove(b)
                    play_sound(HIT_SND)
                    if player.health <= 0:
                        game_state = "lost"

    render_surf.fill(BLACK)
    
    if game_state == "landing":
        if not map.grid: map.generate_map(1) 
        
        landing_camera_x += 2
        map.draw_map(render_surf, int(landing_camera_x), 0)
        
        scale = 1.0 + 0.05 * math.sin(pygame.time.get_ticks() / 200.0)
        t_img = title_font.render("THE GREAT HEIST", True, YELLOW)
        scaled_title = pygame.transform.scale(t_img, (int(t_img.get_width() * scale), int(t_img.get_height() * scale)))
        rect = scaled_title.get_rect(center=(RENDER_W // 2, RENDER_H // 2 - 50))
        render_surf.blit(scaled_title, rect.topleft)
        
        if (pygame.time.get_ticks() // 500) % 2 == 0:
            draw_centered_text(render_surf, "PRESS ANYWHERE TO COMMENCE", font, WHITE, RENDER_H // 2 + 50)
            
    elif game_state == "login":
        is_portrait = RENDER_H > RENDER_W
        y_step = 0.08 if not is_portrait else 0.12
        
        # Draw dynamic title (safely scaled down if too wide)
        t_img = title_font.render("SECURITY CLEARANCE REQUIRED", True, YELLOW)
        if t_img.get_width() > RENDER_W * 0.9:
            t_img = pygame.transform.scale(t_img, (int(RENDER_W * 0.9), int(t_img.get_height() * (RENDER_W * 0.9 / t_img.get_width()))))
        render_surf.blit(t_img, t_img.get_rect(center=(RENDER_W // 2, int(RENDER_H * 0.15))))

        draw_centered_text(render_surf, "Lost passwords are non-recoverable.", tiny_font, (150, 150, 150), int(RENDER_H * 0.22))
        
        # Username Input
        draw_centered_text(render_surf, "Username:", font, WHITE, int(RENDER_H * 0.30))
        txt_u = font.render(username_text, True, WHITE)
        u_color = YELLOW if active_field == "username" else GRAY
        box_w = min(400, int(RENDER_W * 0.8))
        user_box_rect = pygame.Rect(RENDER_W // 2 - box_w // 2, int(RENDER_H * 0.35), box_w, int(45 * UI_SCALE))
        pygame.draw.rect(render_surf, u_color, user_box_rect, 2)
        render_surf.blit(txt_u, (user_box_rect.centerx - txt_u.get_width()//2, user_box_rect.y + (user_box_rect.height - txt_u.get_height())//2))
        
        # Password Input
        draw_centered_text(render_surf, "Password:", font, WHITE, int(RENDER_H * 0.45))
        display_pass = password_text if show_password else "*" * len(password_text)
        txt_p = font.render(display_pass, True, WHITE)
        p_color = YELLOW if active_field == "password" else GRAY
        pass_box_rect = pygame.Rect(RENDER_W // 2 - box_w // 2, int(RENDER_H * 0.50), box_w, int(45 * UI_SCALE))
        pygame.draw.rect(render_surf, p_color, pass_box_rect, 2)
        render_surf.blit(txt_p, (pass_box_rect.centerx - txt_p.get_width()//2, pass_box_rect.y + (pass_box_rect.height - txt_p.get_height())//2))
        
        # Toggle Pass Button
        v_text_str = "VIEW" if not show_password else "HIDE"
        v_text = tiny_font.render(v_text_str, True, WHITE)
        view_pass_btn = pygame.Rect(pass_box_rect.right + 10, pass_box_rect.y, int(80 * UI_SCALE), pass_box_rect.height)
        if is_portrait: # Move VIEW button below in portrait to avoid overlap
            view_pass_btn = pygame.Rect(pass_box_rect.centerx - 40, pass_box_rect.bottom + 10, 80, 40)
            
        v_color = GREEN if show_password else GRAY
        pygame.draw.rect(render_surf, v_color, view_pass_btn, border_radius=5)
        render_surf.blit(v_text, (view_pass_btn.centerx - v_text.get_width()//2, view_pass_btn.centery - v_text.get_height()//2))
        
        submit_y = int(RENDER_H * 0.65) if not is_portrait else int(RENDER_H * 0.75)

        # Submissions
        if firebase_db.login_status in ["idle", "wrong_password", "error"]:
            login_btn = draw_centered_text(render_surf, "AUTHENTICATE [ENTER]", font, GREEN, submit_y)
            
        if firebase_db.login_status == "loading":
            draw_centered_text(render_surf, "VERIFYING ENCRYPTION...", font, YELLOW, submit_y)
            
        elif firebase_db.login_status == "wrong_password":
            draw_centered_text(render_surf, "CRITICAL: INVALID PASSWORD!", font, (255, 50, 50), submit_y + 60)
            
        elif firebase_db.login_status == "error":
            draw_centered_text(render_surf, "API TIMEOUT. OFFLINE MODE.", font, (255, 100, 100), submit_y + 50)
            cont_btn = draw_centered_text(render_surf, "BOOT OFFLINE (GUEST)", font, GREEN, submit_y + 100)
            
        elif firebase_db.login_status == "success":
            draw_centered_text(render_surf, "ACCESS GRANTED. INITIALIZING.", font, GREEN, submit_y)
            unlocked_levels = firebase_db.cached_unlocked_levels
            game_state = "menu" 
            
    elif game_state == "menu":
        draw_centered_text(render_surf, "THE GREAT HEIST", title_font, YELLOW, int(RENDER_H * 0.15))
        draw_centered_text(render_surf, f"PRO OPERATIVE: {username_text.upper()}", tiny_font, GRAY, int(RENDER_H * 0.22))
        
        start_btn = draw_centered_text(render_surf, "START MISSION", font, GREEN, int(RENDER_H * 0.40))
        guide_btn = draw_centered_text(render_surf, "FIELD MANUAL", font, WHITE, int(RENDER_H * 0.52))
        options_btn = draw_centered_text(render_surf, "SYS CONFIG", font, WHITE, int(RENDER_H * 0.64))
        quit_btn = draw_centered_text(render_surf, "TERMINATE", font, (255, 100, 100), int(RENDER_H * 0.76))
        
    elif game_state == "guide":
        draw_centered_text(render_surf, "OPERATIVE FIELD MANUAL", title_font, YELLOW, int(RENDER_H * 0.12))
        
        y_start = 0.22
        y_gap = 0.08
        draw_centered_text(render_surf, "- Player Base HP: 100  |  Enemy Guards HP: 50", font, WHITE, int(RENDER_H * y_start))
        draw_centered_text(render_surf, "- Player Hit DMG: 25   |  Enemy Hit DMG: 10", font, WHITE, int(RENDER_H * (y_start + y_gap)))
        draw_centered_text(render_surf, "- Red Potion (Health): Restores 20 HP instantly.", font, (255, 100, 100), int(RENDER_H * (y_start + y_gap*2)))
        draw_centered_text(render_surf, "- Blue Potion (Speed): Grants +1.75x Speed Buff.", font, (100, 150, 255), int(RENDER_H * (y_start + y_gap*3)))
        draw_centered_text(render_surf, "- Combat Ammo: Eliminating guards drops +5 Ammo.", font, GREEN, int(RENDER_H * (y_start + y_gap*4)))
        
        mission_y = 0.72 if not is_portrait else 0.82
        draw_centered_text(render_surf, "MISSION: Secure ALL Gold and Neutralize ALL Guards to escape!", tiny_font, YELLOW, int(RENDER_H * mission_y))
        
        back_btn = draw_centered_text(render_surf, "BACK TO MENU", font, GREEN, int(RENDER_H * 0.90))
        
    elif game_state == "options":
        draw_centered_text(render_surf, "CONFIGURATION", title_font, YELLOW, int(RENDER_H * 0.15))
        draw_centered_text(render_surf, "Move: W, A, S, D", font, WHITE, int(RENDER_H * 0.30))
        draw_centered_text(render_surf, "Aim: Mouse | Shoot: Left Click", font, WHITE, int(RENDER_H * 0.38))
        
        vol_y = int(RENDER_H * 0.55)
        # Simplified volume display as requested
        draw_centered_text(render_surf, f"MASTER VOLUME: {int(global_volume * 100)}%", font, WHITE, vol_y)
        
        ctrl_mode_btn = draw_centered_text(render_surf, f"INPUT METHOD: [ {control_mode} ]", font, YELLOW, int(RENDER_H * 0.70))
        
        back_btn = draw_centered_text(render_surf, "BACK TO MENU", font, GREEN, int(RENDER_H * 0.88))
        
    elif game_state == "levels":
        draw_centered_text(render_surf, "SELECT LEVEL", title_font, YELLOW, int(RENDER_H * 0.10))
        level_rects.clear()
        
        grid_w, grid_h = int(80 * UI_SCALE), int(50 * UI_SCALE)
        padding = int(20 * UI_SCALE)
        cols = 5 if not is_portrait else 4
        
        total_w = cols * grid_w + (cols - 1) * padding
        start_x = RENDER_W // 2 - total_w // 2 + grid_w // 2
        start_y = int(RENDER_H * 0.25)
        
        for i in range(20):
            lv_idx = i + 1
            col = i % cols
            row = i // cols
            x = start_x + col * (grid_w + padding)
            y = start_y + row * (grid_h + padding)
            
            rect = pygame.Rect(0, 0, grid_w, grid_h)
            rect.center = (x, y)
            level_rects[lv_idx] = rect
            
            color = GREEN if lv_idx <= unlocked_levels else GRAY
            pygame.draw.rect(render_surf, color, rect, border_radius=5)
            
            lvl_text = font.render(str(lv_idx), True, BLACK)
            t_rect = lvl_text.get_rect(center=(x, y))
            render_surf.blit(lvl_text, t_rect)
            
        back_btn = draw_centered_text(render_surf, "BACK", font, (255, 100, 100), int(RENDER_H * 0.90))
        
    elif game_state == "playing":
        map.draw_map(render_surf, int(camera_x), int(camera_y))
        
        for g in gold_items:
            if GOLD_IMG: render_surf.blit(GOLD_IMG, (int(g.x - camera_x), int(g.y - camera_y)))
            else: pygame.draw.circle(render_surf, YELLOW, (int(g.centerx - camera_x), int(g.centery - camera_y)), TILE_SIZE // 3)
                
        for hp in hp_potions:
            if HP_IMG: render_surf.blit(HP_IMG, (int(hp.x - camera_x), int(hp.y - camera_y)))
            
        for sp in sp_potions:
            if SP_IMG: render_surf.blit(SP_IMG, (int(sp.x - camera_x), int(sp.y - camera_y)))
        
        if exit_door:
            door_color = GREEN if (len(gold_items) == 0 and len(enemies) == 0) else (150, 0, 0)
            draw_door = pygame.Rect(exit_door.left - camera_x, exit_door.top - camera_y, exit_door.width, exit_door.height)
            pygame.draw.rect(render_surf, door_color, draw_door)

        player.draw(render_surf, int(camera_x), int(camera_y))
        for enemy in enemies:
            enemy.draw(render_surf, int(camera_x), int(camera_y))
        for b in bullets:
            b.draw(render_surf, int(camera_x), int(camera_y))
            
        # Dynamic HUD: Stays in corners properly
        pygame.draw.rect(render_surf, (255, 0, 0), (10, 10, int(150 * UI_SCALE), int(15 * UI_SCALE)))
        pygame.draw.rect(render_surf, GREEN, (10, 10, int(max(0, player.health) * 1.5 * UI_SCALE), int(15 * UI_SCALE)))
        h_text = small_font.render(f"Ammo: {player.ammo} | Gold: {len(gold_items)} | Foes: {len(enemies)}", True, WHITE)
        render_surf.blit(h_text, (int(170 * UI_SCALE), 8))
        
    elif game_state == "won":
        draw_centered_text(render_surf, "SUCCESS! ESCAPED!", title_font, GREEN, RENDER_H // 2 - int(50 * UI_SCALE))
        draw_centered_text(render_surf, "CLICK ANYWHERE TO CONTINUE", font, WHITE, RENDER_H // 2 + int(50 * UI_SCALE))
    elif game_state == "lost":
        draw_centered_text(render_surf, "WASTED.", title_font, (255, 0, 0), RENDER_H // 2 - int(50 * UI_SCALE))
        draw_centered_text(render_surf, "CLICK ANYWHERE TO RESTART", font, WHITE, RENDER_H // 2 + int(50 * UI_SCALE))

    scaled_up = pygame.transform.scale(render_surf, (WIDTH, HEIGHT))
    screen.blit(scaled_up, (0, 0))
    
    # Render translucent Touch-pads strictly OVER the final scaled-up resolution to prevent Zoom pixelation
    if game_state == "playing" and control_mode == "MOBILE":
        joy_surface = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        pygame.draw.circle(joy_surface, (255, 255, 255, 75), left_joy_center, joy_radius)
        pygame.draw.circle(joy_surface, (255, 255, 255, 200), left_knob_pos, knob_radius)
        
        pygame.draw.circle(joy_surface, (255, 50, 50, 75), right_joy_center, joy_radius)
        pygame.draw.circle(joy_surface, (255, 50, 50, 200), right_knob_pos, knob_radius)
        screen.blit(joy_surface, (0, 0))
        
    pygame.display.flip()

pygame.quit()
sys.exit()