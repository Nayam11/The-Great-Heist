import pygame
import os
import wave
import struct
import math
import random

def create_images():
    os.makedirs('assets', exist_ok=True)
    
    # 1. Gold Stack
    surf = pygame.Surface((40, 40), pygame.SRCALPHA)
    # Draw bars
    pygame.draw.rect(surf, (200, 150, 0), (5, 20, 20, 10))
    pygame.draw.rect(surf, (255, 215, 0), (6, 21, 18, 8))
    
    pygame.draw.rect(surf, (200, 150, 0), (15, 20, 20, 10))
    pygame.draw.rect(surf, (255, 215, 0), (16, 21, 18, 8))
    
    pygame.draw.rect(surf, (200, 150, 0), (10, 12, 20, 10))
    pygame.draw.rect(surf, (255, 215, 0), (11, 13, 18, 8))
    
    # Add shiny pixel
    pygame.draw.rect(surf, (255, 255, 255), (14, 15, 3, 3))
    
    pygame.image.save(surf, os.path.join('assets', 'gold.png'))
    print("Created gold.png")

    # 2. Barrier Box
    surf_box = pygame.Surface((40, 40), pygame.SRCALPHA)
    pygame.draw.rect(surf_box, (100, 70, 40), (0, 0, 40, 40))
    pygame.draw.rect(surf_box, (139, 69, 19), (2, 2, 36, 36))
    pygame.draw.line(surf_box, (100, 70, 40), (2, 2), (38, 38), 3)
    pygame.draw.line(surf_box, (100, 70, 40), (38, 2), (2, 38), 3)
    
    pygame.image.save(surf_box, os.path.join('assets', 'box.png'))
    print("Created box.png")
    
    # 3. Potions
    # Health (+20)
    surf_hp = pygame.Surface((40, 40), pygame.SRCALPHA)
    pygame.draw.circle(surf_hp, (200, 0, 0), (20, 25), 10)
    pygame.draw.rect(surf_hp, (200, 0, 0), (16, 12, 8, 10))
    pygame.draw.rect(surf_hp, (150, 150, 150), (15, 10, 10, 4))
    # Red cross
    pygame.draw.line(surf_hp, (255, 255, 255), (20, 20), (20, 30), 2)
    pygame.draw.line(surf_hp, (255, 255, 255), (15, 25), (25, 25), 2)
    pygame.image.save(surf_hp, os.path.join('assets', 'health_potion.png'))
    
    # Speed (1.75x)
    surf_sp = pygame.Surface((40, 40), pygame.SRCALPHA)
    pygame.draw.circle(surf_sp, (0, 255, 0), (20, 25), 10)
    pygame.draw.rect(surf_sp, (0, 255, 0), (16, 12, 8, 10))
    pygame.draw.rect(surf_sp, (150, 150, 150), (15, 10, 10, 4))
    # Lightning bolt indicator
    pygame.draw.polygon(surf_sp, (255, 255, 255), [(23,17), (18,25), (21,25), (17,33), (27,22), (22,22)])
    pygame.image.save(surf_sp, os.path.join('assets', 'speed_potion.png'))

def create_sound(filename, frames, sample_rate=44100):
    with wave.open(os.path.join('assets', filename), 'w') as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        for frame in frames:
            # clamp and scale
            v = int(max(-1.0, min(1.0, frame)) * 32767.0)
            wav_file.writeframesraw(struct.pack('<h', v))
    print(f"Created {filename}")

def synthesize_audio():
    sample_rate = 44100
    
    # 1. Shoot (Descend sweep noise)
    length = int(sample_rate * 0.15)
    shoot_data = []
    freq = 800.0
    for i in range(length):
        freq *= 0.999
        t = i / sample_rate
        val = math.sin(2.0 * math.pi * freq * t) * random.uniform(0.5, 1.0)
        # linear fade out
        env = 1.0 - (i / length)
        shoot_data.append(val * env * 0.5)
    create_sound('shoot.wav', shoot_data)
    
    # 2. Hit (Short low frequency crunch)
    length = int(sample_rate * 0.1)
    hit_data = []
    for i in range(length):
        v = random.uniform(-1, 1) if (i//150)%2 == 0 else random.uniform(-0.5, 0.5)
        env = 1.0 - (i / length)
        hit_data.append(v * env * 0.6)
    create_sound('hit.wav', hit_data)
    
    # 3. Kaching (High pitched dual chime)
    length = int(sample_rate * 0.4)
    kaching_data = []
    for i in range(length):
        t = i / sample_rate
        f1 = 1200.0
        f2 = 1800.0 if t > 0.1 else 0  # second note hits at 0.1s
        v1 = math.sin(2.0 * math.pi * f1 * t) * math.exp(-15*t)
        v2 = math.sin(2.0 * math.pi * f2 * t) * math.exp(-10*(t-0.1)) if t > 0.1 else 0
        kaching_data.append((v1 + v2) * 0.5)
    create_sound('kaching.wav', kaching_data)

if __name__ == '__main__':
    pygame.init()
    # Dummy window so surfaces work cleanly
    pygame.display.set_mode((1, 1), pygame.HIDDEN)
    create_images()
    synthesize_audio()
    pygame.quit()
