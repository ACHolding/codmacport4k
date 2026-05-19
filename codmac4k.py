import sys
import os
import math
import random
import array
import struct
import pygame

# Initialize pygame and its systems
pygame.init()
pygame.font.init()

# Initial window dimensions (Xbox 720p HD Standard)
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.DOUBLEBUF | pygame.HWSURFACE)
pygame.display.set_caption("Call of Duty 26: Mac Port [Xbox Build v26.04]")

# Colors
COLOR_BG_DARK = (15, 16, 17)
COLOR_BG_PANEL = (26, 28, 30)
COLOR_TEXT_WHITE = (240, 240, 240)
COLOR_TEXT_GRAY = (140, 145, 150)
COLOR_XBOX_GREEN = (16, 124, 16)
COLOR_XBOX_GREEN_GLOW = (57, 255, 20)
COLOR_WARNING_RED = (220, 50, 50)
COLOR_ORANGE_XP = (255, 102, 0)
COLOR_ZOMBIE_GREEN = (40, 180, 70)
COLOR_BLOOD = (180, 20, 20)
COLOR_GRID = (30, 40, 32)

# Game States
STATE_INTRO = "INTRO"
STATE_MENU = "MENU"
STATE_CAMPAIGN = "CAMPAIGN"
STATE_MULTIPLAYER = "MULTIPLAYER"
STATE_ZOMBIES = "ZOMBIES"
STATE_SETTINGS = "SETTINGS"
STATE_EXIT = "EXIT"

# Initial state setup
current_state = STATE_INTRO
intro_timer = 0
intro_stage = 0
connecting_text = "CONNECTING TO ONLINE SERVICES..."

# Fonts setup
def get_font(name_list, size, bold=False):
    for name in name_list:
        try:
            return pygame.font.SysFont(name, size, bold=bold)
        except Exception:
            continue
    return pygame.font.Font(None, size)

FONT_TITLE = get_font(["Impact", "Arial Black", "Arial", "sans-serif"], 64, bold=True)
FONT_SUBTITLE = get_font(["Impact", "Arial", "sans-serif"], 32, bold=True)
FONT_MENU = get_font(["Arial Black", "Arial", "sans-serif"], 28, bold=True)
FONT_HUD = get_font(["Lucida Console", "Courier New", "Courier", "monospace"], 20, bold=True)
FONT_HUD_LG = get_font(["Lucida Console", "Courier New", "Courier", "monospace"], 36, bold=True)
FONT_TEXT = get_font(["Arial", "sans-serif"], 18, bold=False)
FONT_BANNER = get_font(["Impact", "Arial Black", "sans-serif"], 80, bold=True)

# Sound Synthesis Helper
pygame.mixer.init(frequency=22050, size=-16, channels=2)
sounds = {}

def create_sound_effects():
    global sounds
    try:
        if not pygame.mixer.get_init():
            return
        
        rate = 22050
        
        # 1. UI SELECT (High-pitched click-beep)
        duration = 0.05
        num_samples = int(rate * duration)
        data = array.array('h')
        for i in range(num_samples):
            t = i / rate
            freq = 1200
            val = int(12000 * math.sin(2 * math.pi * freq * t) * (1 - t/duration))
            # stereo
            data.append(val)
            data.append(val)
        sounds['select'] = pygame.mixer.Sound(buffer=data)

        # 2. UI CLICK (Confirmation sound)
        duration = 0.08
        num_samples = int(rate * duration)
        data = array.array('h')
        for i in range(num_samples):
            t = i / rate
            freq = 600 if t < 0.04 else 900
            val = int(15000 * math.sin(2 * math.pi * freq * t) * (1 - t/duration))
            data.append(val)
            data.append(val)
        sounds['click'] = pygame.mixer.Sound(buffer=data)

        # 3. GUNSHOT (Decaying white noise + low frequency explosion)
        duration = 0.22
        num_samples = int(rate * duration)
        data = array.array('h')
        for i in range(num_samples):
            t = i / rate
            noise = random.uniform(-1.0, 1.0)
            sine = math.sin(2 * math.pi * 90 * t)
            decay = math.exp(-15 * t)
            val = int(26000 * (noise * 0.75 + sine * 0.25) * decay)
            val = max(-32768, min(32767, val))
            data.append(val)
            data.append(val)
        sounds['shoot'] = pygame.mixer.Sound(buffer=data)

        # 4. HITMARKER (Short distinct tick)
        duration = 0.03
        num_samples = int(rate * duration)
        data = array.array('h')
        for i in range(num_samples):
            t = i / rate
            val = int(18000 * (random.uniform(-0.5, 0.5) + math.sin(2 * math.pi * 1800 * t)) * math.exp(-60 * t))
            data.append(val)
            data.append(val)
        sounds['hitmarker'] = pygame.mixer.Sound(buffer=data)

        # 5. RELOAD (Mechanical reload click-clack)
        duration = 0.5
        num_samples = int(rate * duration)
        data = array.array('h')
        for i in range(num_samples):
            t = i / rate
            val = 0
            if 0.05 <= t <= 0.09:
                tc = t - 0.05
                val = int(16000 * math.sin(2 * math.pi * 350 * tc) * math.exp(-35 * tc))
            elif 0.25 <= t <= 0.29:
                tc = t - 0.25
                val = int(18000 * math.sin(2 * math.pi * 500 * tc) * math.exp(-40 * tc))
            elif 0.38 <= t <= 0.42:
                tc = t - 0.38
                val = int(20000 * math.sin(2 * math.pi * 450 * tc) * math.exp(-30 * tc))
            data.append(val)
            data.append(val)
        sounds['reload'] = pygame.mixer.Sound(buffer=data)

        # 6. ZOMBIE GROWL (Guttural sound)
        duration = 0.6
        num_samples = int(rate * duration)
        data = array.array('h')
        for i in range(num_samples):
            t = i / rate
            freq = 65 + 30 * math.sin(2 * math.pi * 8 * t)
            noise = random.uniform(-0.6, 0.6)
            decay = math.sin(math.pi * t / duration)
            val = int(11000 * (math.sin(2 * math.pi * freq * t) + noise) * decay)
            val = max(-32768, min(32767, val))
            data.append(val)
            data.append(val)
        sounds['zombie'] = pygame.mixer.Sound(buffer=data)

        # 7. LEVEL UP (Arpeggio fanfare)
        duration = 0.7
        num_samples = int(rate * duration)
        data = array.array('h')
        for i in range(num_samples):
            t = i / rate
            if t < 0.2:
                freq = 440  # A4
                vol = t / 0.2
            elif t < 0.4:
                freq = 554  # C#5
                vol = 1.0
            elif t < 0.55:
                freq = 659  # E5
                vol = 1.0
            else:
                freq = 880  # A5
                vol = (0.7 - t) / 0.15
            val = int(12000 * math.sin(2 * math.pi * freq * t) * vol)
            data.append(val)
            data.append(val)
        sounds['levelup'] = pygame.mixer.Sound(buffer=data)

        # 8. HURT (Pain sound/grunt)
        duration = 0.15
        num_samples = int(rate * duration)
        data = array.array('h')
        for i in range(num_samples):
            t = i / rate
            freq = 80 - 20 * t
            noise = random.uniform(-0.8, 0.8)
            decay = math.exp(-12 * t)
            val = int(14000 * (math.sin(2 * math.pi * freq * t) + noise) * decay)
            val = max(-32768, min(32767, val))
            data.append(val)
            data.append(val)
        sounds['hurt'] = pygame.mixer.Sound(buffer=data)

        # 9. MUSIC SOUNDTRACK (Cyberpunk military loop)
        music_dur = 4.0
        num_samples_m = int(rate * music_dur)
        data_m = array.array('h')
        for i in range(num_samples_m):
            t = i / rate
            # Bassline: E (82Hz) -> G (98Hz) -> A (110Hz) -> D (73Hz)
            beat = int(t) % 4
            if beat == 0:
                freq = 82.4
            elif beat == 1:
                freq = 98.0
            elif beat == 2:
                freq = 110.0
            else:
                freq = 73.4
                
            # Bass pluck
            beat_t = t % 1.0
            bass_decay = math.exp(-5 * beat_t)
            synth = math.sin(2 * math.pi * freq * t) * 0.7 + math.sin(2 * math.pi * (freq*2) * t) * 0.3
            bass_val = synth * bass_decay
            
            # Kick drum on 1 and 3 (0.0s, 0.5s of every 1s)
            kick_t = t % 0.5
            kick_decay = math.exp(-16 * kick_t)
            kick = math.sin(2 * math.pi * 55 * kick_t) * kick_decay
            
            # Hi-hat on off-beats
            hat_t = (t + 0.25) % 0.5
            hat = 0
            if hat_t < 0.04:
                hat = random.uniform(-1.0, 1.0) * math.exp(-80 * hat_t) * 0.15
                
            val = int(6000 * (bass_val * 0.4 + kick * 0.55 + hat * 0.1))
            val = max(-32768, min(32767, val))
            data_m.append(val)
            data_m.append(val)
        sounds['music'] = pygame.mixer.Sound(buffer=data_m)
        
    except Exception as e:
        print(f"Failed to generate synth audio: {e}")

create_sound_effects()

# Play Background Music Loop if generated
music_channel = None
if 'music' in sounds:
    try:
        music_channel = pygame.mixer.Channel(0)
        music_channel.play(sounds['music'], loops=-1)
        music_channel.set_volume(0.2)
    except Exception:
        pass

def play_sfx(name):
    if name in sounds:
        try:
            # Find a free channel or mix on channel 1-7 (reserving 0 for music)
            chan = pygame.mixer.find_channel(True)
            if chan:
                # Keep music volume distinct
                if chan.get_busy() and chan.get_sound() == sounds.get('music'):
                    pass
                else:
                    chan.play(sounds[name])
        except Exception:
            pass

# Settings Configurations
config_crt_scanlines = True
config_screen_shake = True
config_music = True
config_sfx = True
avg_fps = 60.0

# ----------------- GAME OBJECTS / SYSTEMS -----------------

# Particle System
particles = []

def spawn_splatter(x, y, color, count=15):
    for _ in range(count):
        particles.append({
            'x': x,
            'y': y,
            'vx': random.uniform(-5.0, 5.0),
            'vy': random.uniform(-7.0, 2.0),
            'size': random.randint(2, 6),
            'color': color,
            'life': 1.0,
            'decay': random.uniform(0.02, 0.05),
            'gravity': 0.25
        })

def update_particles():
    for p in particles[:]:
        p['x'] += p['vx']
        p['y'] += p['vy']
        p['vy'] += p['gravity']
        p['life'] -= p['decay']
        if p['life'] <= 0:
            particles.remove(p)

def draw_particles(surf):
    for p in particles:
        alpha = int(p['life'] * 255)
        # Create a tiny surface for transparency if needed, or simple draw
        s = pygame.Surface((p['size']*2, p['size']*2), pygame.SRCALPHA)
        pygame.draw.circle(s, p['color'] + (alpha,), (p['size'], p['size']), p['size'])
        surf.blit(s, (p['x'] - p['size'], p['y'] - p['size']))

# Text indicators (XP alerts, rank ups, notifications)
floating_texts = []

def spawn_floating_text(text, x, y, color=COLOR_ORANGE_XP, scale_up=False, size=24):
    font_to_use = FONT_SUBTITLE if scale_up else FONT_HUD
    floating_texts.append({
        'text': text,
        'x': x,
        'y': y,
        'vy': -2.5,
        'life': 1.0,
        'decay': 0.015,
        'color': color,
        'font': font_to_use
    })

def update_floating_texts():
    for t in floating_texts[:]:
        t['x'] += random.uniform(-0.5, 0.5)
        t['y'] += t['vy']
        t['life'] -= t['decay']
        if t['life'] <= 0:
            floating_texts.remove(t)

def draw_floating_texts(surf):
    for t in floating_texts:
        alpha = int(t['life'] * 255)
        # Render text with drop shadow
        text_shadow = t['font'].render(t['text'], True, (0, 0, 0))
        text_shadow.set_alpha(alpha)
        text_surf = t['font'].render(t['text'], True, t['color'])
        text_surf.set_alpha(alpha)
        
        surf.blit(text_shadow, (t['x'] - text_surf.get_width()//2 + 2, t['y'] + 2))
        surf.blit(text_surf, (t['x'] - text_surf.get_width()//2, t['y']))

# Global Player Progression
player_xp = 350
player_level = 4
player_streak = 0
player_health = 100
hurt_overlay_alpha = 0
screen_shake_amt = 0

def add_xp(amount):
    global player_xp, player_level
    player_xp += amount
    spawn_floating_text(f"+{amount} XP", SCREEN_WIDTH//2, SCREEN_HEIGHT//2 - 80, COLOR_ORANGE_XP, scale_up=True)
    if player_xp >= 1000:
        player_xp -= 1000
        player_level += 1
        play_sfx('levelup')
        spawn_floating_text(f"RANK UP! LEVEL {player_level}", SCREEN_WIDTH//2, SCREEN_HEIGHT//2 - 150, COLOR_XBOX_GREEN_GLOW, scale_up=True)

# Gun System (M4A1 Carbine)
gun_recoil = 0
gun_y_offset = 0
gun_angle = 0
gun_ammo = 30
gun_max_ammo = 30
gun_reserve = 120
gun_muzzle_flash = 0
gun_reloading = False
gun_reload_timer = 0

def update_gun():
    global gun_recoil, gun_y_offset, gun_angle, gun_reloading, gun_reload_timer, gun_ammo
    # Return gun to neutral position using linear interpolation
    gun_recoil = max(0.0, gun_recoil * 0.8)
    gun_y_offset = gun_y_offset * 0.85
    gun_angle = gun_angle * 0.85
    
    if gun_reloading:
        gun_reload_timer -= 1
        # Animation stages based on timer
        if gun_reload_timer > 20:
            # lower gun
            gun_y_offset = (30 - gun_reload_timer) * 12
            gun_angle = (30 - gun_reload_timer) * 1.5
        elif gun_reload_timer > 10:
            # lowest point (clipping in ammo)
            gun_y_offset = 120
            gun_angle = 15
        else:
            # raise gun back
            gun_y_offset = gun_reload_timer * 12
            gun_angle = gun_reload_timer * 1.5
            
        if gun_reload_timer <= 0:
            gun_reloading = False
            needed = gun_max_ammo - gun_ammo
            transfer = min(needed, gun_reserve)
            gun_ammo += transfer
            gun_reserve -= transfer

def trigger_reload():
    global gun_reloading, gun_reload_timer
    if not gun_reloading and gun_ammo < gun_max_ammo and gun_reserve > 0:
        gun_reloading = True
        gun_reload_timer = 30 # 30 frames at 60fps = 0.5s
        play_sfx('reload')

def fire_gun():
    global gun_ammo, gun_recoil, gun_y_offset, gun_angle, gun_muzzle_flash, screen_shake_amt
    if gun_reloading:
        return False
    if gun_ammo <= 0:
        play_sfx('select') # empty click sound
        spawn_floating_text("RELOAD REDUX [R]", SCREEN_WIDTH//2, SCREEN_HEIGHT - 180, COLOR_WARNING_RED)
        return False
        
    gun_ammo -= 1
    gun_recoil = 25.0
    gun_y_offset = 35.0
    gun_angle = -5.0
    gun_muzzle_flash = 3 # flash visible for 3 frames
    if config_screen_shake:
        screen_shake_amt = 8
    play_sfx('shoot')
    return True

def draw_gun(surf):
    global gun_muzzle_flash
    # Position gun in bottom right
    gun_x = SCREEN_WIDTH - 250
    gun_y = SCREEN_HEIGHT - 220 + gun_y_offset + gun_recoil
    
    # Gun surface to allow rotation
    gun_surf = pygame.Surface((400, 300), pygame.SRCALPHA)
    
    # Draw procedural gun (M4A1)
    # Stock
    pygame.draw.polygon(gun_surf, (35, 37, 39), [(10, 200), (90, 180), (90, 230), (10, 240)])
    pygame.draw.rect(gun_surf, (20, 21, 22), (90, 195, 80, 25)) # stock buffer tube
    # Receiver / Body
    pygame.draw.polygon(gun_surf, (45, 47, 50), [(170, 185), (270, 185), (270, 225), (170, 230)])
    # Handguard
    pygame.draw.rect(gun_surf, (30, 31, 33), (270, 190, 90, 30))
    # Barrel
    pygame.draw.rect(gun_surf, (70, 72, 75), (360, 200, 40, 10))
    # Scope (Holographic/Red Dot Sight)
    pygame.draw.polygon(gun_surf, (20, 20, 21), [(210, 185), (250, 185), (245, 160), (215, 160)])
    pygame.draw.circle(gun_surf, (15, 15, 16), (230, 172), 8)
    pygame.draw.circle(gun_surf, (255, 0, 0), (230, 172), 2) # glass glow
    # Magazine
    pygame.draw.polygon(gun_surf, (25, 27, 28), [(225, 225), (245, 225), (235, 285), (215, 280)])
    # Grip
    pygame.draw.polygon(gun_surf, (20, 20, 21), [(185, 228), (205, 228), (195, 265), (180, 265)])
    
    # Muzzle flash
    if gun_muzzle_flash > 0:
        flash_points = [
            (400, 205),
            (420, 195),
            (410, 203),
            (435, 205),
            (410, 207),
            (420, 215),
        ]
        pygame.draw.polygon(gun_surf, (255, 200, 50), flash_points)
        pygame.draw.circle(gun_surf, (255, 255, 255), (405, 205), 8)
        gun_muzzle_flash -= 1
        
    # Rotate gun surf
    rotated_gun = pygame.transform.rotate(gun_surf, gun_angle)
    surf.blit(rotated_gun, (gun_x, gun_y))


# ----------------- GAME STATE: INTRO -----------------
def update_intro():
    global intro_timer, intro_stage, current_state, connecting_text
    intro_timer += 1
    
    if intro_stage == 0:
        if intro_timer > 60:
            connecting_text = "CONNECTING TO ONLINE SERVICES..."
            intro_stage = 1
    elif intro_stage == 1:
        if intro_timer > 120:
            connecting_text = "DOWNLOADING MAC PORT SHADERS [100%]..."
            intro_stage = 2
    elif intro_stage == 2:
        if intro_timer > 180:
            connecting_text = "XBOX PROFILE SYNCED SUCCESSFULLY."
            intro_stage = 3
    elif intro_stage == 3:
        if intro_timer > 240:
            connecting_text = "PRESS START TO INITIATE"
            
def draw_intro(surf):
    surf.fill(COLOR_BG_DARK)
    
    # Draw scanning background grids
    for i in range(0, SCREEN_HEIGHT, 40):
        intensity = int(15 + 10 * math.sin(intro_timer * 0.05 + i))
        pygame.draw.line(surf, (0, intensity, 0), (0, i), (SCREEN_WIDTH, i), 1)
        
    # Title
    title_shadow = FONT_TITLE.render("CALL OF DUTY 26", True, (0, 0, 0))
    title_main = FONT_TITLE.render("CALL OF DUTY 26", True, COLOR_XBOX_GREEN)
    
    # Subtle title glitch effect
    offset_x = random.randint(-2, 2) if intro_timer % 15 == 0 else 0
    surf.blit(title_shadow, (SCREEN_WIDTH//2 - title_main.get_width()//2 + 3 + offset_x, 200 + 3))
    surf.blit(title_main, (SCREEN_WIDTH//2 - title_main.get_width()//2 + offset_x, 200))
    
    # Subtitle
    sub_text = FONT_SUBTITLE.render("MAC PORT [XBOX BUILT EDITION]", True, COLOR_TEXT_WHITE)
    surf.blit(sub_text, (SCREEN_WIDTH//2 - sub_text.get_width()//2, 275))
    
    # Status/prompt text
    if intro_stage < 3:
        dots = "." * (int(intro_timer / 15) % 4)
        status_surf = FONT_HUD.render(connecting_text + dots, True, COLOR_TEXT_GRAY)
    else:
        # blinking effect
        if (intro_timer // 20) % 2 == 0:
            status_surf = FONT_HUD.render(connecting_text, True, COLOR_XBOX_GREEN_GLOW)
        else:
            status_surf = FONT_HUD.render(connecting_text, True, COLOR_TEXT_WHITE)
            
    surf.blit(status_surf, (SCREEN_WIDTH//2 - status_surf.get_width()//2, SCREEN_HEIGHT - 200))
    
    # Footer
    foot_text = FONT_TEXT.render("© 2026 ACTIVISION | XBOX PORTING LABS", True, COLOR_TEXT_GRAY)
    surf.blit(foot_text, (SCREEN_WIDTH//2 - foot_text.get_width()//2, SCREEN_HEIGHT - 60))


# ----------------- GAME STATE: MAIN MENU -----------------
menu_options = ["CAMPAIGN", "MULTIPLAYER", "ZOMBIES", "SETTINGS", "EXIT"]
menu_selected = 0
menu_animations = [0.0] * len(menu_options)
particle_dust = []

# Generate menu dust particles
for _ in range(40):
    particle_dust.append({
        'x': random.randint(0, SCREEN_WIDTH),
        'y': random.randint(0, SCREEN_HEIGHT),
        'speed': random.uniform(0.2, 0.8),
        'size': random.uniform(1.0, 3.0),
        'alpha': random.randint(30, 150)
    })

def update_menu():
    global menu_selected
    # Update animations
    for i in range(len(menu_options)):
        if i == menu_selected:
            menu_animations[i] = min(1.0, menu_animations[i] + 0.1)
        else:
            menu_animations[i] = max(0.0, menu_animations[i] - 0.1)
            
    # Update floating dust
    for p in particle_dust:
        p['y'] -= p['speed']
        if p['y'] < -10:
            p['y'] = SCREEN_HEIGHT + 10
            p['x'] = random.randint(0, SCREEN_WIDTH)

def draw_menu(surf):
    surf.fill(COLOR_BG_DARK)
    
    # Draw background parallax grid
    grid_offset = int((pygame.time.get_ticks() / 20) % 80)
    for x in range(-80 + grid_offset, SCREEN_WIDTH + 80, 80):
        pygame.draw.line(surf, COLOR_GRID, (x, 0), (x - 100, SCREEN_HEIGHT), 1)
    for y in range(0, SCREEN_HEIGHT, 60):
        pygame.draw.line(surf, COLOR_GRID, (0, y), (SCREEN_WIDTH, y), 1)
        
    # Draw dust particles
    for p in particle_dust:
        s = pygame.Surface((p['size']*2, p['size']*2), pygame.SRCALPHA)
        pygame.draw.circle(s, (100, 200, 120, p['alpha']), (p['size'], p['size']), p['size'])
        surf.blit(s, (p['x'], p['y']))
        
    # Top Header
    title_main = FONT_TITLE.render("CALL OF DUTY 26", True, COLOR_TEXT_WHITE)
    surf.blit(title_main, (80, 60))
    sub_main = FONT_SUBTITLE.render("MAC PORT / XBOX LIVE ACTIVE", True, COLOR_XBOX_GREEN_GLOW)
    surf.blit(sub_main, (80, 130))
    
    # Menu Items container
    menu_y_start = 240
    for i, option in enumerate(menu_options):
        anim = menu_animations[i]
        x_offset = 80 + anim * 25
        
        # Selection highlight box
        if anim > 0.01:
            box_width = 320 + anim * 30
            box_surf = pygame.Surface((box_width, 50), pygame.SRCALPHA)
            # fade in glow
            pygame.draw.rect(box_surf, (16, 124, 16, int(anim * 80)), (0, 0, box_width, 50), border_radius=4)
            pygame.draw.rect(box_surf, COLOR_XBOX_GREEN_GLOW + (int(anim*255),), (0, 0, box_width, 50), 2, border_radius=4)
            surf.blit(box_surf, (x_offset - 15, menu_y_start + i * 70 - 7))
            
        # Draw Text
        color = COLOR_XBOX_GREEN_GLOW if i == menu_selected else COLOR_TEXT_GRAY
        text_surf = FONT_MENU.render(option, True, color)
        surf.blit(text_surf, (x_offset, menu_y_start + i * 70))
        
    # Right-side Player Combat Record Card
    card_x = SCREEN_WIDTH - 480
    card_y = 220
    card_width = 400
    card_height = 360
    
    # Background panel
    pygame.draw.rect(surf, COLOR_BG_PANEL, (card_x, card_y, card_width, card_height), border_radius=8)
    pygame.draw.rect(surf, COLOR_XBOX_GREEN, (card_x, card_y, card_width, card_height), 2, border_radius=8)
    
    # Header card banner
    pygame.draw.rect(surf, COLOR_XBOX_GREEN, (card_x, card_y, card_width, 50), border_radius=8)
    card_title = FONT_HUD.render("PLAYER COMBAT CARD", True, COLOR_TEXT_WHITE)
    surf.blit(card_title, (card_x + 20, card_y + 15))
    
    # Stats content
    level_txt = FONT_HUD_LG.render(f"LVL {player_level}", True, COLOR_ORANGE_XP)
    surf.blit(level_txt, (card_x + 25, card_y + 70))
    
    rank_txt = FONT_TEXT.render("RANK: COMMANDER GRADE V", True, COLOR_TEXT_WHITE)
    surf.blit(rank_txt, (card_x + 25, card_y + 115))
    
    # XP Bar
    xp_bar_w = 350
    pygame.draw.rect(surf, (40, 42, 45), (card_x + 25, card_y + 145, xp_bar_w, 15), border_radius=3)
    pygame.draw.rect(surf, COLOR_ORANGE_XP, (card_x + 25, card_y + 145, int(xp_bar_w * (player_xp/1000.0)), 15), border_radius=3)
    xp_text = FONT_HUD.render(f"XP: {player_xp}/1000", True, COLOR_TEXT_GRAY)
    surf.blit(xp_text, (card_x + 25, card_y + 168))
    
    # Detailed statistics
    kills_label = FONT_TEXT.render("TOTAL CASUALTIES:", True, COLOR_TEXT_GRAY)
    kills_val = FONT_HUD.render("1,492", True, COLOR_TEXT_WHITE)
    surf.blit(kills_label, (card_x + 25, card_y + 210))
    surf.blit(kills_val, (card_x + 250, card_y + 210))
    
    kd_label = FONT_TEXT.render("K/D RATIO:", True, COLOR_TEXT_GRAY)
    kd_val = FONT_HUD.render("2.48", True, COLOR_XBOX_GREEN_GLOW)
    surf.blit(kd_label, (card_x + 25, card_y + 240))
    surf.blit(kd_val, (card_x + 250, card_y + 240))
    
    streak_label = FONT_TEXT.render("MAX KILLSTREAK:", True, COLOR_TEXT_GRAY)
    streak_val = FONT_HUD.render("25 (NUKED)", True, COLOR_ORANGE_XP)
    surf.blit(streak_label, (card_x + 25, card_y + 270))
    surf.blit(streak_val, (card_x + 250, card_y + 270))
    
    win_label = FONT_TEXT.render("W/L RATIO:", True, COLOR_TEXT_GRAY)
    win_val = FONT_HUD.render("1.85", True, COLOR_TEXT_WHITE)
    surf.blit(win_label, (card_x + 25, card_y + 300))
    surf.blit(win_val, (card_x + 250, card_y + 300))
    
    # Bottom Console Hints
    hint_surf = FONT_HUD.render("[W/S/Arrow Keys] Navigate  [ENTER/Space] Confirm", True, COLOR_TEXT_GRAY)
    surf.blit(hint_surf, (80, SCREEN_HEIGHT - 65))


# ----------------- GAME STATE: CAMPAIGN (TARGET RANGE) -----------------
campaign_targets = []
campaign_score = 0
campaign_time_left = 60 # 60 seconds TDM target shooter
campaign_timer_ticks = 0
crosshair_color = COLOR_TEXT_WHITE

def spawn_campaign_target():
    # Spawn a pop-up combat targets
    # z: depth scale from 0.4 (far) to 1.0 (close)
    depth = random.uniform(0.4, 1.0)
    w = int(90 * depth)
    h = int(140 * depth)
    x = random.randint(150, SCREEN_WIDTH - 150 - w)
    # y lines determined by depth to simulate perspective ground
    y = int(220 + (1 - depth) * 200)
    
    campaign_targets.append({
        'rect': pygame.Rect(x, y, w, h),
        'depth': depth,
        'head_rect': pygame.Rect(x + int(w * 0.3), y, int(w * 0.4), int(h * 0.25)),
        'color': (random.randint(60, 100), random.randint(80, 120), random.randint(60, 90)), # military camo green
        'active': True,
        'pop_dir': 1, # 1 popping up, -1 sliding down
        'pop_offset': h, # start fully hidden
        'speed': random.randint(6, 12),
        'life': 180 # stays for 3 seconds max
    })

def update_campaign():
    global campaign_time_left, campaign_timer_ticks, current_state, player_xp
    
    campaign_timer_ticks += 1
    if campaign_timer_ticks >= 60: # 1 second at 60 fps
        campaign_timer_ticks = 0
        campaign_time_left -= 1
        if campaign_time_left <= 0:
            # End game, return to menu
            spawn_floating_text("CAMPAIGN STAGE COMPLETE!", SCREEN_WIDTH//2, SCREEN_HEIGHT//2, COLOR_XBOX_GREEN_GLOW, scale_up=True)
            current_state = STATE_MENU
            
    # Spawn target randomly
    if len(campaign_targets) < 5 and random.random() < 0.04:
        spawn_campaign_target()
        
    # Update targets
    for t in campaign_targets[:]:
        t['life'] -= 1
        if t['pop_dir'] == 1:
            t['pop_offset'] = max(0, t['pop_offset'] - t['speed'])
            if t['life'] <= 30:
                t['pop_dir'] = -1
        else:
            t['pop_offset'] += t['speed']
            if t['pop_offset'] >= t['rect'].height or t['life'] <= 0:
                campaign_targets.remove(t)
                
    update_gun()
    update_particles()
    update_floating_texts()

def draw_campaign(surf):
    global crosshair_color
    surf.fill((20, 24, 28))
    
    # Draw perspective firing range ground
    pygame.draw.polygon(surf, (40, 42, 45), [(0, SCREEN_HEIGHT), (250, 220), (SCREEN_WIDTH - 250, 220), (SCREEN_WIDTH, SCREEN_HEIGHT)])
    # horizon sky
    pygame.draw.rect(surf, (15, 17, 19), (0, 0, SCREEN_WIDTH, 220))
    # Horizon line green glow
    pygame.draw.line(surf, COLOR_XBOX_GREEN, (0, 220), (SCREEN_WIDTH, 220), 2)
    
    # Grid lines on perspective ground
    for ratio in [0.1, 0.25, 0.45, 0.7, 0.95]:
        px = int(SCREEN_WIDTH * ratio)
        pygame.draw.line(surf, (35, 45, 38), (px, SCREEN_HEIGHT), (250 + int((SCREEN_WIDTH - 500) * ratio), 220), 1)
        
    # Obstacles/barriers
    # Sandbox far
    pygame.draw.rect(surf, (50, 48, 44), (200, 205, 300, 20), border_radius=3)
    pygame.draw.rect(surf, (40, 38, 34), (SCREEN_WIDTH - 500, 205, 300, 20), border_radius=3)
    
    # Draw targets
    # Sort targets by depth so further ones are drawn behind closer ones
    sorted_targets = sorted(campaign_targets, key=lambda tg: tg['depth'])
    for t in sorted_targets:
        # Draw target offset by pop_offset to simulate sliding up
        cur_y = t['rect'].y + t['pop_offset']
        if cur_y < SCREEN_HEIGHT:
            h_visible = t['rect'].height - t['pop_offset']
            if h_visible > 0:
                # Body silhouette
                body_surf = pygame.Surface((t['rect'].width, t['rect'].height), pygame.SRCALPHA)
                
                # Draw dummy shape
                # Body
                pygame.draw.ellipse(body_surf, t['color'], (0, int(t['rect'].height * 0.2), t['rect'].width, int(t['rect'].height * 0.8)))
                pygame.draw.rect(body_surf, (20, 20, 20), (0, int(t['rect'].height * 0.2), t['rect'].width, int(t['rect'].height * 0.8)), 2)
                # Head
                head_w = t['head_rect'].width
                head_h = t['head_rect'].height
                pygame.draw.ellipse(body_surf, (150, 110, 80), (int(t['rect'].width*0.3), 0, head_w, head_h))
                pygame.draw.ellipse(body_surf, (20, 20, 20), (int(t['rect'].width*0.3), 0, head_w, head_h), 2)
                
                # Target ring on chest
                cx, cy = t['rect'].width // 2, int(t['rect'].height * 0.5)
                pygame.draw.circle(body_surf, (200, 200, 200), (cx, cy), int(t['rect'].width * 0.25))
                pygame.draw.circle(body_surf, COLOR_WARNING_RED, (cx, cy), int(t['rect'].width * 0.15))
                pygame.draw.circle(body_surf, (255, 255, 255), (cx, cy), int(t['rect'].width * 0.05))
                
                # Clip drawing for pop transition
                surf.blit(body_surf, (t['rect'].x, cur_y), (0, t['pop_offset'], t['rect'].width, h_visible))

    # Particles and overlays
    draw_particles(surf)
    draw_floating_texts(surf)
    
    # Crosshair rendering based on target collision
    mx, my = pygame.mouse.get_pos()
    crosshair_color = COLOR_TEXT_WHITE
    for t in campaign_targets:
        cur_y = t['rect'].y + t['pop_offset']
        # adjust actual collision box based on popoffset
        active_rect = pygame.Rect(t['rect'].x, cur_y, t['rect'].width, t['rect'].height - t['pop_offset'])
        if active_rect.collidepoint(mx, my):
            crosshair_color = COLOR_XBOX_GREEN_GLOW
            
    # Draw Reticle
    pygame.draw.circle(surf, crosshair_color, (mx, my), 15, 2)
    pygame.draw.line(surf, crosshair_color, (mx - 22, my), (mx - 6, my), 2)
    pygame.draw.line(surf, crosshair_color, (mx + 6, my), (mx + 22, my), 2)
    pygame.draw.line(surf, crosshair_color, (mx, my - 22), (mx, my - 6), 2)
    pygame.draw.line(surf, crosshair_color, (mx, my + 6), (mx, my + 22), 2)
    pygame.draw.circle(surf, COLOR_WARNING_RED, (mx, my), 2)
    
    # Hitmarker rendering (draw short click reticle lines if shooter recently hit)
    global hitmarker_timer, hitmarker_headshot
    if hitmarker_timer > 0:
        h_color = COLOR_ORANGE_XP if hitmarker_headshot else COLOR_TEXT_WHITE
        # Draw X lines
        pygame.draw.line(surf, h_color, (mx - 10, my - 10), (mx - 4, my - 4), 2)
        pygame.draw.line(surf, h_color, (mx + 4, my - 4), (mx + 10, my - 10), 2)
        pygame.draw.line(surf, h_color, (mx - 10, my + 10), (mx - 4, my + 4), 2)
        pygame.draw.line(surf, h_color, (mx + 4, my + 4), (mx + 10, my + 10), 2)
        hitmarker_timer -= 1
        
    # Draw gun
    draw_gun(surf)
    
    # Top HUD
    # Score banner
    score_surf = FONT_HUD.render(f"SCORE: {campaign_score}", True, COLOR_TEXT_WHITE)
    surf.blit(score_surf, (40, 30))
    # Timer
    timer_color = COLOR_TEXT_WHITE if campaign_time_left > 10 else COLOR_WARNING_RED
    timer_surf = FONT_HUD_LG.render(f"00:{campaign_time_left:02d}", True, timer_color)
    surf.blit(timer_surf, (SCREEN_WIDTH//2 - timer_surf.get_width()//2, 30))
    # Mode Label
    mode_surf = FONT_HUD.render("MODE: CAMPAIGN TARGET TRAINING", True, COLOR_XBOX_GREEN_GLOW)
    surf.blit(mode_surf, (SCREEN_WIDTH - mode_surf.get_width() - 40, 30))
    
    # Bottom HUD Ammo / Gun Card
    hud_bg = pygame.Surface((300, 90), pygame.SRCALPHA)
    pygame.draw.rect(hud_bg, (20, 22, 24, 200), (0, 0, 300, 90), border_radius=6)
    pygame.draw.rect(hud_bg, COLOR_XBOX_GREEN, (0, 0, 300, 90), 2, border_radius=6)
    surf.blit(hud_bg, (SCREEN_WIDTH - 340, SCREEN_HEIGHT - 120))
    
    weapon_surf = FONT_HUD.render("M4A1 CARBINE [AUTO]", True, COLOR_TEXT_WHITE)
    surf.blit(weapon_surf, (SCREEN_WIDTH - 320, SCREEN_HEIGHT - 105))
    
    ammo_surf = FONT_HUD_LG.render(f"{gun_ammo:02d}", True, COLOR_XBOX_GREEN_GLOW if gun_ammo > 5 else COLOR_WARNING_RED)
    surf.blit(ammo_surf, (SCREEN_WIDTH - 320, SCREEN_HEIGHT - 75))
    
    reserve_surf = FONT_HUD.render(f"/ {gun_reserve}", True, COLOR_TEXT_GRAY)
    surf.blit(reserve_surf, (SCREEN_WIDTH - 260, SCREEN_HEIGHT - 65))
    
    # Escape Hint
    esc_surf = FONT_HUD.render("[ESC] RETREAT TO COMMAND DECK", True, COLOR_TEXT_GRAY)
    surf.blit(esc_surf, (40, SCREEN_HEIGHT - 50))


hitmarker_timer = 0
hitmarker_headshot = False

def process_campaign_shoot():
    global campaign_score, hitmarker_timer, hitmarker_headshot
    if not fire_gun():
        return
        
    mx, my = pygame.mouse.get_pos()
    hit_target = False
    
    # Check hits closest first (highest depth)
    sorted_targets = sorted(campaign_targets, key=lambda tg: tg['depth'], reverse=True)
    for t in sorted_targets:
        cur_y = t['rect'].y + t['pop_offset']
        active_rect = pygame.Rect(t['rect'].x, cur_y, t['rect'].width, t['rect'].height - t['pop_offset'])
        
        if active_rect.collidepoint(mx, my):
            # Check Headshot
            head_y = t['head_rect'].y + t['pop_offset']
            active_head = pygame.Rect(t['head_rect'].x, head_y, t['head_rect'].width, t['head_rect'].height)
            
            is_headshot = active_head.collidepoint(mx, my)
            hit_target = True
            
            # play hitmarker sound
            play_sfx('hitmarker')
            hitmarker_timer = 6
            hitmarker_headshot = is_headshot
            
            # Spawn blood splatter
            spawn_splatter(mx, my, COLOR_BLOOD, count=18)
            
            # Update Score and XP
            if is_headshot:
                campaign_score += 150
                add_xp(150)
                spawn_floating_text("+150 XP HEADSHOT!", t['rect'].x + t['rect'].width//2, cur_y - 20, COLOR_XBOX_GREEN_GLOW)
            else:
                campaign_score += 100
                add_xp(100)
                spawn_floating_text("+100 XP", t['rect'].x + t['rect'].width//2, cur_y - 20, COLOR_ORANGE_XP)
                
            campaign_targets.remove(t)
            break
            
    if not hit_target:
        # Spawn debris spark splatter
        spawn_splatter(mx, my, (150, 150, 150), count=5)


# ----------------- GAME STATE: MULTIPLAYER (TEAM DEATHMATCH BATTLE) -----------------
mp_allies_score = 6500
mp_axis_score = 6200
mp_killfeed = []
mp_timer = 180 # 3 minutes TDM matches
mp_timer_ticks = 0
mp_enemies = []
mp_announcement = ""
mp_announcement_timer = 0
mp_game_over = False
mp_victory = False

bot_names = ["Soap_MacTavish", "Ghost_Riley", "Price_Captain", "Shepherd_Gen", "Makarov_Val", "Yuri_Loyal", "Nikolai_Heli", "Roach_Sgt", "Sandman_Delta", "Frost_Delta", "Grinch_T1", "Truck_T1"]

def spawn_mp_enemy():
    depth = random.uniform(0.4, 0.9)
    w = int(80 * depth)
    h = int(120 * depth)
    x = random.randint(100, SCREEN_WIDTH - 100 - w)
    y = int(220 + (1 - depth) * 210)
    
    mp_enemies.append({
        'rect': pygame.Rect(x, y, w, h),
        'depth': depth,
        'head_rect': pygame.Rect(x + int(w * 0.3), y, int(w * 0.4), int(h * 0.25)),
        'color': (random.randint(140, 180), random.randint(40, 60), random.randint(40, 60)), # enemy orange/red highlights
        'active': True,
        'pop_offset': h,
        'pop_dir': 1,
        'speed': random.randint(8, 15),
        'name': random.choice(bot_names),
        'shoot_timer': random.randint(45, 90) # time to shoot player
    })

def add_killfeed(killer, weapon, victim, killer_is_player=False, victim_is_player=False):
    c1 = COLOR_XBOX_GREEN_GLOW if killer_is_player else COLOR_TEXT_WHITE
    c2 = COLOR_WARNING_RED if victim_is_player else COLOR_TEXT_GRAY
    
    mp_killfeed.append({
        'killer': killer,
        'weapon': weapon,
        'victim': victim,
        'c1': c1,
        'c2': c2,
        'timer': 240 # displays for 4 seconds
    })
    
    if len(mp_killfeed) > 5:
        mp_killfeed.pop(0)

def trigger_mp_announcement(text):
    global mp_announcement, mp_announcement_timer
    mp_announcement = text
    mp_announcement_timer = 120
    play_sfx('click')

def update_multiplayer():
    global mp_timer, mp_timer_ticks, mp_allies_score, mp_axis_score, mp_game_over, mp_victory, current_state, player_health, hurt_overlay_alpha
    
    if mp_game_over:
        return
        
    mp_timer_ticks += 1
    if mp_timer_ticks >= 60:
        mp_timer_ticks = 0
        mp_timer -= 1
        if mp_timer <= 0:
            mp_game_over = True
            mp_victory = mp_allies_score >= mp_axis_score
            
    # Random bot shootout simulation in background
    if random.random() < 0.03:
        b1 = random.choice(bot_names)
        b2 = random.choice(bot_names)
        while b1 == b2:
            b2 = random.choice(bot_names)
        wep = random.choice(["M4A1", "ACR", "Intervention", "Frag", "Claymore", "Desert Eagle"])
        
        # Determine who kills whom
        if random.random() > 0.5:
            mp_allies_score += 100
            add_killfeed(b1, wep, b2, False, False)
        else:
            mp_axis_score += 100
            add_killfeed(b2, wep, b1, False, False)
            
        # TDM Winning limits (7500 points)
        if mp_allies_score >= 7500 or mp_axis_score >= 7500:
            mp_game_over = True
            mp_victory = mp_allies_score >= mp_axis_score
            
    # Spawn interactive enemies
    if len(mp_enemies) < 4 and random.random() < 0.05:
        spawn_mp_enemy()
        
    # Update active enemies
    for e in mp_enemies[:]:
        if e['pop_dir'] == 1:
            e['pop_offset'] = max(0, e['pop_offset'] - e['speed'])
            
            # Enemy aims at player
            e['shoot_timer'] -= 1
            if e['shoot_timer'] <= 0:
                # Shoot player!
                e['pop_dir'] = -1 # retreats after shooting
                play_sfx('shoot')
                player_health = max(0, player_health - 25)
                hurt_overlay_alpha = 180
                play_sfx('hurt')
                spawn_floating_text("HIT!", SCREEN_WIDTH//2, SCREEN_HEIGHT//2, COLOR_WARNING_RED, scale_up=True)
                
                # Check player death
                if player_health <= 0:
                    add_killfeed(e['name'], "Rifle", "GamerMac (Player)", False, True)
                    player_health = 100 # respawn instantly
                    mp_axis_score += 100
                    trigger_mp_announcement("RESPAWNING...")
        else:
            e['pop_offset'] += e['speed']
            if e['pop_offset'] >= e['rect'].height:
                mp_enemies.remove(e)
                
    # Health regeneration
    if player_health < 100 and hurt_overlay_alpha == 0:
        player_health = min(100, player_health + 0.2)
        
    if hurt_overlay_alpha > 0:
        hurt_overlay_alpha = max(0, hurt_overlay_alpha - 4)
        
    # Update killfeed decay timers
    for k in mp_killfeed:
        k['timer'] -= 1
    mp_killfeed[:] = [k for k in mp_killfeed if k['timer'] > 0]
    
    update_gun()
    update_particles()
    update_floating_texts()

def draw_multiplayer(surf):
    surf.fill((18, 20, 22))
    
    # 2D Combat Arena Layout Background (Urban landscape vectors)
    pygame.draw.rect(surf, (30, 32, 35), (0, 220, SCREEN_WIDTH, SCREEN_HEIGHT - 220))
    pygame.draw.line(surf, COLOR_XBOX_GREEN, (0, 220), (SCREEN_WIDTH, 220), 2)
    
    # Draw simple background buildings silhouettes
    pygame.draw.rect(surf, (10, 11, 12), (100, 80, 200, 140))
    pygame.draw.rect(surf, (14, 15, 17), (400, 50, 250, 170))
    pygame.draw.rect(surf, (12, 13, 14), (800, 110, 180, 110))
    
    # Draw enemies
    sorted_enemies = sorted(mp_enemies, key=lambda tg: tg['depth'])
    for e in sorted_enemies:
        cur_y = e['rect'].y + e['pop_offset']
        h_visible = e['rect'].height - e['pop_offset']
        if h_visible > 0:
            enemy_surf = pygame.Surface((e['rect'].width, e['rect'].height), pygame.SRCALPHA)
            # Body outline Red
            pygame.draw.ellipse(enemy_surf, e['color'], (0, int(e['rect'].height * 0.2), e['rect'].width, int(e['rect'].height * 0.8)))
            pygame.draw.rect(enemy_surf, COLOR_WARNING_RED, (0, int(e['rect'].height * 0.2), e['rect'].width, int(e['rect'].height * 0.8)), 2)
            # Head
            head_w = e['head_rect'].width
            head_h = e['head_rect'].height
            pygame.draw.ellipse(enemy_surf, (170, 130, 100), (int(e['rect'].width*0.3), 0, head_w, head_h))
            pygame.draw.ellipse(enemy_surf, COLOR_WARNING_RED, (int(e['rect'].width*0.3), 0, head_w, head_h), 2)
            # Gun pointer (line towards center screen)
            pygame.draw.line(enemy_surf, (20, 20, 20), (int(e['rect'].width*0.5), int(e['rect'].height*0.5)), (0 if e['rect'].x > SCREEN_WIDTH//2 else e['rect'].width, int(e['rect'].height*0.6)), 4)
            
            surf.blit(enemy_surf, (e['rect'].x, cur_y), (0, e['pop_offset'], e['rect'].width, h_visible))
            
            # Enemy tag outline
            if e['pop_offset'] < 20:
                tag_surf = FONT_TEXT.render(e['name'], True, COLOR_WARNING_RED)
                surf.blit(tag_surf, (e['rect'].x + e['rect'].width//2 - tag_surf.get_width()//2, cur_y - 25))

    # Particles and HUD
    draw_particles(surf)
    draw_floating_texts(surf)
    
    # Blood screen overlay when player is hurt
    if hurt_overlay_alpha > 0:
        blood_surf = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        # Red border vignetting
        pygame.draw.rect(blood_surf, (150, 0, 0, int(hurt_overlay_alpha * 0.6)), (0, 0, SCREEN_WIDTH, SCREEN_HEIGHT), 30)
        pygame.draw.rect(blood_surf, (150, 0, 0, int(hurt_overlay_alpha * 0.3)), (25, 25, SCREEN_WIDTH - 50, SCREEN_HEIGHT - 50), 40)
        surf.blit(blood_surf, (0, 0))
        
    # Draw Gun
    draw_gun(surf)
    
    # Custom Crosshair
    mx, my = pygame.mouse.get_pos()
    pygame.draw.circle(surf, COLOR_XBOX_GREEN_GLOW, (mx, my), 10, 1)
    pygame.draw.circle(surf, COLOR_XBOX_GREEN_GLOW, (mx, my), 2)
    
    # Render Hitmarker
    global hitmarker_timer, hitmarker_headshot
    if hitmarker_timer > 0:
        h_color = COLOR_ORANGE_XP if hitmarker_headshot else COLOR_TEXT_WHITE
        pygame.draw.line(surf, h_color, (mx - 8, my - 8), (mx - 3, my - 3), 2)
        pygame.draw.line(surf, h_color, (mx + 3, my - 3), (mx + 8, my - 8), 2)
        pygame.draw.line(surf, h_color, (mx - 8, my + 8), (mx - 3, my + 3), 2)
        pygame.draw.line(surf, h_color, (mx + 3, my + 3), (mx + 8, my + 8), 2)
        hitmarker_timer -= 1
        
    # Score Header (TDM Panel)
    # Allies panel
    pygame.draw.rect(surf, COLOR_BG_PANEL, (SCREEN_WIDTH//2 - 200, 20, 180, 45), border_radius=4)
    pygame.draw.rect(surf, COLOR_XBOX_GREEN, (SCREEN_WIDTH//2 - 200, 20, 180, 45), 2, border_radius=4)
    team1 = FONT_HUD.render("ALLIES", True, COLOR_XBOX_GREEN_GLOW)
    score1 = FONT_HUD_LG.render(str(mp_allies_score), True, COLOR_TEXT_WHITE)
    surf.blit(team1, (SCREEN_WIDTH//2 - 190, 32))
    surf.blit(score1, (SCREEN_WIDTH//2 - 100, 25))
    
    # Axis panel
    pygame.draw.rect(surf, COLOR_BG_PANEL, (SCREEN_WIDTH//2 + 20, 20, 180, 45), border_radius=4)
    pygame.draw.rect(surf, COLOR_WARNING_RED, (SCREEN_WIDTH//2 + 20, 20, 180, 45), 2, border_radius=4)
    team2 = FONT_HUD.render("OPFOR", True, COLOR_WARNING_RED)
    score2 = FONT_HUD_LG.render(str(mp_axis_score), True, COLOR_TEXT_WHITE)
    surf.blit(team2, (SCREEN_WIDTH//2 + 30, 32))
    surf.blit(score2, (SCREEN_WIDTH//2 + 110, 25))
    
    # Match countdown timer
    min_left = mp_timer // 60
    sec_left = mp_timer % 60
    match_t = FONT_HUD_LG.render(f"{min_left:02d}:{sec_left:02d}", True, COLOR_TEXT_WHITE)
    surf.blit(match_t, (SCREEN_WIDTH//2 - match_t.get_width()//2, 75))
    
    # Draw Killfeed in bottom left
    k_y = SCREEN_HEIGHT - 260
    for feed in mp_killfeed:
        # Format text block
        k_txt = FONT_HUD.render(feed['killer'], True, feed['c1'])
        w_txt = FONT_HUD.render(f" [{feed['weapon']}] ", True, COLOR_ORANGE_XP)
        v_txt = FONT_HUD.render(feed['victim'], True, feed['c2'])
        
        # Blit inline
        x_pt = 40
        surf.blit(k_txt, (x_pt, k_y))
        x_pt += k_txt.get_width()
        surf.blit(w_txt, (x_pt, k_y))
        x_pt += w_txt.get_width()
        surf.blit(v_txt, (x_pt, k_y))
        
        k_y += 30
        
    # Announcements Banner
    global mp_announcement_timer
    if mp_announcement_timer > 0 and mp_announcement:
        ann_surf = FONT_HUD_LG.render(mp_announcement, True, COLOR_ORANGE_XP)
        pygame.draw.rect(surf, (0, 0, 0, 150), (0, 150, SCREEN_WIDTH, 60))
        surf.blit(ann_surf, (SCREEN_WIDTH//2 - ann_surf.get_width()//2, 160))
        mp_announcement_timer -= 1
        
    # Game Over Banner
    if mp_game_over:
        banner_bg = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        banner_bg.fill((0, 0, 0, 180))
        surf.blit(banner_bg, (0, 0))
        
        banner_text = "VICTORY!" if mp_victory else "DEFEAT"
        banner_color = COLOR_XBOX_GREEN_GLOW if mp_victory else COLOR_WARNING_RED
        
        b_surf = FONT_BANNER.render(banner_text, True, banner_color)
        surf.blit(b_surf, (SCREEN_WIDTH//2 - b_surf.get_width()//2, SCREEN_HEIGHT//2 - 100))
        
        p_surf = FONT_SUBTITLE.render("PRESS ANY KEY TO RETURN TO DECK", True, COLOR_TEXT_WHITE)
        surf.blit(p_surf, (SCREEN_WIDTH//2 - p_surf.get_width()//2, SCREEN_HEIGHT//2 + 20))
        
    # Left Bottom Health / HUD Bar
    pygame.draw.rect(surf, COLOR_BG_PANEL, (40, SCREEN_HEIGHT - 120, 240, 70), border_radius=5)
    pygame.draw.rect(surf, COLOR_XBOX_GREEN, (40, SCREEN_HEIGHT - 120, 240, 70), 2, border_radius=5)
    
    health_label = FONT_HUD.render("HP:", True, COLOR_TEXT_WHITE)
    surf.blit(health_label, (55, SCREEN_HEIGHT - 110))
    pygame.draw.rect(surf, (50, 50, 50), (95, SCREEN_HEIGHT - 108, 160, 14))
    h_col = COLOR_XBOX_GREEN_GLOW if player_health > 35 else COLOR_WARNING_RED
    pygame.draw.rect(surf, h_col, (95, SCREEN_HEIGHT - 108, int(160 * (player_health / 100.0)), 14))
    
    # Pulse graphic line representing heartbeat
    beat_pts = []
    pulse_t = pygame.time.get_ticks() / 150.0
    for idx in range(160):
        # speed of wave increases if health is low
        freq_factor = 2.0 if player_health < 35 else 1.0
        val = math.sin(pulse_t + idx * 0.15 * freq_factor)
        if (idx % 40) < 5: # heart spike
            val *= 3.5
        beat_pts.append((95 + idx, SCREEN_HEIGHT - 70 + int(val * 4)))
    if len(beat_pts) > 1:
        pygame.draw.lines(surf, COLOR_XBOX_GREEN_GLOW, False, beat_pts, 2)
        
    # Ammo box (Right Bottom)
    hud_bg = pygame.Surface((300, 90), pygame.SRCALPHA)
    pygame.draw.rect(hud_bg, (20, 22, 24, 200), (0, 0, 300, 90), border_radius=6)
    pygame.draw.rect(hud_bg, COLOR_XBOX_GREEN, (0, 0, 300, 90), 2, border_radius=6)
    surf.blit(hud_bg, (SCREEN_WIDTH - 340, SCREEN_HEIGHT - 120))
    weapon_surf = FONT_HUD.render("M4A1 CARBINE [AUTO]", True, COLOR_TEXT_WHITE)
    surf.blit(weapon_surf, (SCREEN_WIDTH - 320, SCREEN_HEIGHT - 105))
    ammo_surf = FONT_HUD_LG.render(f"{gun_ammo:02d}", True, COLOR_XBOX_GREEN_GLOW if gun_ammo > 5 else COLOR_WARNING_RED)
    surf.blit(ammo_surf, (SCREEN_WIDTH - 320, SCREEN_HEIGHT - 75))
    reserve_surf = FONT_HUD.render(f"/ {gun_reserve}", True, COLOR_TEXT_GRAY)
    surf.blit(reserve_surf, (SCREEN_WIDTH - 260, SCREEN_HEIGHT - 65))
    
    # Escape Hint
    esc_surf = FONT_HUD.render("[ESC] RETREAT TO COMMAND DECK", True, COLOR_TEXT_GRAY)
    surf.blit(esc_surf, (40, SCREEN_HEIGHT - 40))

def process_mp_shoot():
    global mp_allies_score, hitmarker_timer, hitmarker_headshot
    if not fire_gun():
        return
        
    mx, my = pygame.mouse.get_pos()
    hit_bot = False
    
    sorted_enemies = sorted(mp_enemies, key=lambda tg: tg['depth'], reverse=True)
    for e in sorted_enemies:
        cur_y = e['rect'].y + e['pop_offset']
        active_rect = pygame.Rect(e['rect'].x, cur_y, e['rect'].width, e['rect'].height - e['pop_offset'])
        
        if active_rect.collidepoint(mx, my):
            head_y = e['head_rect'].y + e['pop_offset']
            active_head = pygame.Rect(e['head_rect'].x, head_y, e['head_rect'].width, e['head_rect'].height)
            
            is_headshot = active_head.collidepoint(mx, my)
            hit_bot = True
            
            play_sfx('hitmarker')
            hitmarker_timer = 6
            hitmarker_headshot = is_headshot
            
            spawn_splatter(mx, my, COLOR_BLOOD, count=20)
            
            # Kill feed trigger
            wep = "M4A1"
            if is_headshot:
                wep = "Headshot"
                mp_allies_score += 150
                add_xp(150)
                spawn_floating_text("+150 HEADSHOT!", e['rect'].x + e['rect'].width//2, cur_y - 20, COLOR_XBOX_GREEN_GLOW)
            else:
                mp_allies_score += 100
                add_xp(100)
                spawn_floating_text("+100 XP", e['rect'].x + e['rect'].width//2, cur_y - 20, COLOR_ORANGE_XP)
                
            add_killfeed("GamerMac (Player)", wep, e['name'], True, False)
            
            # UAV / streak mock triggers
            global player_streak
            player_streak += 1
            if player_streak == 3:
                trigger_mp_announcement("UAV RECON ACQUIRED!")
            elif player_streak == 5:
                trigger_mp_announcement("PREDATOR MISSILE READY!")
                
            mp_enemies.remove(e)
            break
            
    if not hit_bot:
        spawn_splatter(mx, my, (130, 130, 130), count=4)


# ----------------- GAME STATE: ZOMBIES (SURVIVAL CO-OP MODE) -----------------
zombies_list = []
zombie_round = 1
zombie_score = 0
zombies_spawned_this_round = 0
zombies_max_round = 8
zombie_health_base = 100
zombie_round_timer = 120 # cooldown between rounds
zombie_wave_active = True

def spawn_zombie():
    global zombies_spawned_this_round
    # Spawn zombie at screen edges
    edge = random.randint(0, 3)
    speed = random.uniform(1.2, 2.5) + (zombie_round * 0.15)
    r_health = zombie_health_base + (zombie_round - 1) * 30
    
    if edge == 0: # top
        x = random.randint(0, SCREEN_WIDTH)
        y = -30
    elif edge == 1: # right
        x = SCREEN_WIDTH + 30
        y = random.randint(0, SCREEN_HEIGHT)
    elif edge == 2: # bottom
        x = random.randint(0, SCREEN_WIDTH)
        y = SCREEN_HEIGHT + 30
    else: # left
        x = -30
        y = random.randint(0, SCREEN_HEIGHT)
        
    zombies_list.append({
        'x': x,
        'y': y,
        'speed': speed,
        'health': r_health,
        'max_health': r_health,
        'color': COLOR_ZOMBIE_GREEN,
        'size': random.randint(16, 24),
        'growl_timer': random.randint(180, 400)
    })
    zombies_spawned_this_round += 1

def update_zombies():
    global zombie_wave_active, zombie_round, zombies_spawned_this_round, zombies_max_round, zombie_round_timer, player_health, hurt_overlay_alpha, current_state
    
    if player_health <= 0:
        # Zombie Game Over, return to menu
        spawn_floating_text("YOU DIED. SURVIVED ROUND: " + str(zombie_round), SCREEN_WIDTH//2, SCREEN_HEIGHT//2, COLOR_WARNING_RED, scale_up=True)
        current_state = STATE_MENU
        return
        
    # Check wave completion
    if zombie_wave_active:
        # Spawn new zombie periodically
        max_active = 4 + zombie_round * 2
        if len(zombies_list) < max_active and zombies_spawned_this_round < zombies_max_round:
            if random.random() < 0.03:
                spawn_zombie()
                
        if len(zombies_list) == 0 and zombies_spawned_this_round >= zombies_max_round:
            # Wave clear!
            zombie_wave_active = False
            zombie_round_timer = 240 # 4 seconds intermission
            trigger_mp_announcement(f"ROUND {zombie_round} COMPLETE")
            play_sfx('levelup')
    else:
        # Cooldown intermission
        zombie_round_timer -= 1
        if zombie_round_timer <= 0:
            zombie_round += 1
            zombies_spawned_this_round = 0
            zombies_max_round = 8 + zombie_round * 4
            zombie_wave_active = True
            trigger_mp_announcement(f"ROUND {zombie_round} BEGUN")
            play_sfx('zombie')
            
    # Update active zombies
    # Player is centered or is looking at screen center. Let's make player stand at the center: (640, 480)
    px, py = SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2
    
    for z in zombies_list[:]:
        # Move towards player
        dx = px - z['x']
        dy = py - z['y']
        dist = math.hypot(dx, dy)
        if dist > 0:
            z['x'] += (dx / dist) * z['speed']
            z['y'] += (dy / dist) * z['speed']
            
        # Growl sound
        z['growl_timer'] -= 1
        if z['growl_timer'] <= 0:
            play_sfx('zombie')
            z['growl_timer'] = random.randint(300, 600)
            
        # Hit player check
        if dist < (z['size'] + 15): # player radius simulated as 15
            # bite player
            player_health = max(0, player_health - 12)
            hurt_overlay_alpha = 150
            play_sfx('hurt')
            zombies_list.remove(z)
            spawn_floating_text("BITTEN!", px, py + 40, COLOR_BLOOD)
            
    # Regenerate health slowly if not hurt recently
    if player_health < 100 and hurt_overlay_alpha == 0:
        player_health = min(100, player_health + 0.15)
        
    if hurt_overlay_alpha > 0:
        hurt_overlay_alpha = max(0, hurt_overlay_alpha - 3)
        
    update_gun()
    update_particles()
    update_floating_texts()

def draw_zombies(surf):
    surf.fill((10, 12, 10))
    
    # Draw dark room with spotlight centered on mouse
    # We do a dark ambient lighting layer
    light_layer = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
    light_layer.fill((0, 0, 0, 245)) # high dark alpha
    
    # Cut out circular flashlight cone
    mx, my = pygame.mouse.get_pos()
    # Draw radial transparent gradient
    for r in range(160, 0, -20):
        # decreasing alpha towards center
        alpha = int((r / 160.0) * 230)
        pygame.draw.circle(light_layer, (0, 0, 0, alpha), (mx, my), r)
    # Complete transparency in center
    pygame.draw.circle(light_layer, (0, 0, 0, 0), (mx, my), 50)
    
    # Draw player base station (Center)
    px, py = SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2
    pygame.draw.circle(surf, COLOR_XBOX_GREEN, (px, py), 18)
    pygame.draw.circle(surf, COLOR_TEXT_WHITE, (px, py), 18, 2)
    # facing line
    ang = math.atan2(my - py, mx - px)
    pygame.draw.line(surf, COLOR_TEXT_WHITE, (px, py), (px + int(math.cos(ang)*24), py + int(math.sin(ang)*24)), 3)
    
    # Draw Zombies
    for z in zombies_list:
        zx, zy = int(z['x']), int(z['y'])
        # Body
        pygame.draw.circle(surf, z['color'], (zx, zy), z['size'])
        pygame.draw.circle(surf, (15, 40, 20), (zx, zy), z['size'], 2)
        # Red glowing eyes
        z_ang = math.atan2(py - zy, px - zx)
        eye_dist = z['size'] * 0.4
        ex1 = zx + int(math.cos(z_ang + 0.4) * eye_dist)
        ey1 = zy + int(math.sin(z_ang + 0.4) * eye_dist)
        ex2 = zx + int(math.cos(z_ang - 0.4) * eye_dist)
        ey2 = zy + int(math.sin(z_ang - 0.4) * eye_dist)
        pygame.draw.circle(surf, COLOR_WARNING_RED, (ex1, ey1), 3)
        pygame.draw.circle(surf, COLOR_WARNING_RED, (ex2, ey2), 3)
        
        # Zombie HP bar if damaged
        if z['health'] < z['max_health']:
            hp_w = z['size'] * 2
            pygame.draw.rect(surf, (50, 0, 0), (zx - hp_w//2, zy - z['size'] - 10, hp_w, 4))
            pygame.draw.rect(surf, COLOR_WARNING_RED, (zx - hp_w//2, zy - z['size'] - 10, int(hp_w * (z['health'] / z['max_health'])), 4))

    # Blit flashlight spotlight overlay
    surf.blit(light_layer, (0, 0))
    
    # Particles and text
    draw_particles(surf)
    draw_floating_texts(surf)
    
    # Draw Gun (Rotated towards flashlight mouse)
    # The gun will be positioned relative to the player center
    gun_x = px - 60
    gun_y = py - 30
    
    # Draw gun facing cursor
    gun_draw_angle = -math.degrees(ang)
    gun_surf = pygame.Surface((150, 80), pygame.SRCALPHA)
    pygame.draw.rect(gun_surf, (30, 32, 34), (20, 30, 60, 15), border_radius=2)
    pygame.draw.rect(gun_surf, (60, 62, 65), (80, 34, 30, 7))
    pygame.draw.rect(gun_surf, (10, 10, 11), (30, 45, 12, 18))
    
    # Reload indicator
    if gun_reloading:
        rot_gun = pygame.transform.rotate(gun_surf, gun_draw_angle - 40)
    else:
        rot_gun = pygame.transform.rotate(gun_surf, gun_draw_angle)
        
    surf.blit(rot_gun, (px - rot_gun.get_width()//2, py - rot_gun.get_height()//2))
    
    # Red blood overlay
    if hurt_overlay_alpha > 0:
        b_surf = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        pygame.draw.rect(b_surf, (180, 0, 0, int(hurt_overlay_alpha * 0.75)), (0, 0, SCREEN_WIDTH, SCREEN_HEIGHT), 25)
        surf.blit(b_surf, (0, 0))
        
    # Standard Reticle
    pygame.draw.circle(surf, COLOR_WARNING_RED, (mx, my), 8, 1)
    pygame.draw.circle(surf, COLOR_WARNING_RED, (mx, my), 2)
    
    # Hitmarker
    global hitmarker_timer
    if hitmarker_timer > 0:
        pygame.draw.line(surf, COLOR_TEXT_WHITE, (mx - 6, my - 6), (mx - 2, my - 2), 2)
        pygame.draw.line(surf, COLOR_TEXT_WHITE, (mx + 2, my - 2), (mx + 6, my - 6), 2)
        pygame.draw.line(surf, COLOR_TEXT_WHITE, (mx - 6, my + 6), (mx - 2, my + 2), 2)
        pygame.draw.line(surf, COLOR_TEXT_WHITE, (mx + 2, my + 2), (mx + 6, my + 6), 2)
        hitmarker_timer -= 1
        
    # Top Zombies HUD
    # Round count
    round_color = COLOR_WARNING_RED if zombie_wave_active else COLOR_TEXT_WHITE
    round_label = FONT_BANNER.render(f"ROUND {zombie_round}", True, round_color)
    surf.blit(round_label, (40, 30))
    
    # Score
    score_surf = FONT_HUD.render(f"POINTS: {zombie_score}", True, COLOR_XBOX_GREEN_GLOW)
    surf.blit(score_surf, (40, 130))
    
    # Health bar bottom left
    pygame.draw.rect(surf, COLOR_BG_PANEL, (40, SCREEN_HEIGHT - 90, 240, 50), border_radius=4)
    pygame.draw.rect(surf, COLOR_WARNING_RED, (40, SCREEN_HEIGHT - 90, 240, 50), 2, border_radius=4)
    hp_label = FONT_HUD.render("VITAL SIGNS", True, COLOR_TEXT_WHITE)
    surf.blit(hp_label, (55, SCREEN_HEIGHT - 80))
    pygame.draw.rect(surf, (40, 10, 10), (170, SCREEN_HEIGHT - 77, 95, 12))
    pygame.draw.rect(surf, COLOR_WARNING_RED, (170, SCREEN_HEIGHT - 77, int(95 * (player_health / 100.0)), 12))
    
    # Bottom HUD Ammo
    hud_bg = pygame.Surface((250, 75), pygame.SRCALPHA)
    pygame.draw.rect(hud_bg, (15, 17, 19, 210), (0, 0, 250, 75), border_radius=5)
    pygame.draw.rect(hud_bg, COLOR_WARNING_RED, (0, 0, 250, 75), 2, border_radius=5)
    surf.blit(hud_bg, (SCREEN_WIDTH - 290, SCREEN_HEIGHT - 110))
    
    w_label = FONT_HUD.render("COLT 1911 (.45)", True, COLOR_TEXT_WHITE)
    surf.blit(w_label, (SCREEN_WIDTH - 275, SCREEN_HEIGHT - 98))
    a_label = FONT_HUD_LG.render(f"{gun_ammo:02d}", True, COLOR_WARNING_RED if gun_ammo <= 2 else COLOR_TEXT_WHITE)
    surf.blit(a_label, (SCREEN_WIDTH - 275, SCREEN_HEIGHT - 74))
    r_label = FONT_HUD.render(f"/ {gun_reserve}", True, COLOR_TEXT_GRAY)
    surf.blit(r_label, (SCREEN_WIDTH - 220, SCREEN_HEIGHT - 65))
    
    # Exit Prompt
    esc_surf = FONT_HUD.render("[ESC] ESCAPE HORDE", True, COLOR_TEXT_GRAY)
    surf.blit(esc_surf, (40, SCREEN_HEIGHT - 35))

def process_zombies_shoot():
    global zombie_score, hitmarker_timer
    if not fire_gun():
        return
        
    mx, my = pygame.mouse.get_pos()
    hit_zombie = False
    
    # Test collisions
    for z in zombies_list[:]:
        zx, zy = int(z['x']), int(z['y'])
        dist = math.hypot(mx - zx, my - zy)
        if dist <= z['size']:
            # Hit!
            hit_zombie = True
            play_sfx('hitmarker')
            hitmarker_timer = 5
            
            # Gun damage
            damage = 40
            z['health'] -= damage
            zombie_score += 10
            add_xp(10)
            
            spawn_splatter(mx, my, COLOR_BLOOD, count=12)
            spawn_floating_text("+10 XP", zx, zy - z['size'] - 10, COLOR_XBOX_GREEN_GLOW)
            
            if z['health'] <= 0:
                zombie_score += 100
                add_xp(50)
                spawn_floating_text("ELIMINATED +50 XP", zx, zy - z['size'] - 15, COLOR_ORANGE_XP)
                zombies_list.remove(z)
                spawn_splatter(zx, zy, COLOR_BLOOD, count=25)
            break
            
    if not hit_zombie:
        # sparks/dust
        spawn_splatter(mx, my, (50, 70, 50), count=4)


# ----------------- GAME STATE: SETTINGS -----------------
settings_options = ["CRT SCANLINES", "SCREEN SHAKE", "MUSIC LOOP", "SOUND EFFECTS", "BACK TO DECK"]
settings_sel = 0

def draw_settings(surf):
    surf.fill(COLOR_BG_DARK)
    
    # Background Grid
    for x in range(0, SCREEN_WIDTH, 60):
        pygame.draw.line(surf, COLOR_GRID, (x, 0), (x, SCREEN_HEIGHT), 1)
    for y in range(0, SCREEN_HEIGHT, 60):
        pygame.draw.line(surf, COLOR_GRID, (0, y), (SCREEN_WIDTH, y), 1)
        
    # Title
    t_surf = FONT_TITLE.render("SYSTEM CONFIGURATION", True, COLOR_TEXT_WHITE)
    surf.blit(t_surf, (80, 80))
    
    # Draw Options
    s_y_start = 220
    for idx, opt in enumerate(settings_options):
        # selection indicator
        is_sel = idx == settings_sel
        color = COLOR_XBOX_GREEN_GLOW if is_sel else COLOR_TEXT_GRAY
        
        # Draw status for toggles
        status_str = ""
        if idx == 0:
            status_str = "[ ENABLED ]" if config_crt_scanlines else "[ DISABLED ]"
        elif idx == 1:
            status_str = "[ ENABLED ]" if config_screen_shake else "[ DISABLED ]"
        elif idx == 2:
            status_str = "[ PLAYING ]" if config_music else "[ MUTED ]"
        elif idx == 3:
            status_str = "[ AUDIBLE ]" if config_sfx else "[ SILENT ]"
            
        opt_text = f"{opt:<20} {status_str}" if status_str else opt
        o_surf = FONT_MENU.render(opt_text, True, color)
        
        if is_sel:
            pygame.draw.rect(surf, (16, 124, 16, 80), (60, s_y_start + idx * 70 - 6, 680, 48), border_radius=4)
            pygame.draw.rect(surf, COLOR_XBOX_GREEN_GLOW, (60, s_y_start + idx * 70 - 6, 680, 48), 2, border_radius=4)
            
        surf.blit(o_surf, (80, s_y_start + idx * 70))
        
    # Right panel: hardware info
    panel_x = 800
    panel_y = 214
    pygame.draw.rect(surf, COLOR_BG_PANEL, (panel_x, panel_y, 400, 380), border_radius=6)
    pygame.draw.rect(surf, COLOR_XBOX_GREEN, (panel_x, panel_y, 400, 380), 2, border_radius=6)
    
    h_surf = FONT_HUD.render("HARDWARE REPORT", True, COLOR_XBOX_GREEN_GLOW)
    surf.blit(h_surf, (panel_x + 20, panel_y + 20))
    
    info_lines = [
        "OS: macOS (Xbox Kernel Port v26)",
        "EMULATOR STACK: Windows 10 API Layer",
        "TARGET FRAME RATE: 60 FPS (LOCK)",
        f"MEASURED PERFORMANCE: {avg_fps:.1f} FPS",
        "AUDIO MIXER RATE: 22050 Hz (Stereo)",
        "ACTIVE ENGINE: PYGAME v2.6.1",
        "RENDER PIPELINE: DOUBLEBUFFER HW",
    ]
    
    for count, line in enumerate(info_lines):
        line_surf = FONT_TEXT.render(line, True, COLOR_TEXT_WHITE)
        surf.blit(line_surf, (panel_x + 20, panel_y + 70 + count * 35))
        
    hint_surf = FONT_HUD.render("[W/S] Navigate  [ENTER] Adjust / Select", True, COLOR_TEXT_GRAY)
    surf.blit(hint_surf, (80, SCREEN_HEIGHT - 65))

def process_settings_toggle():
    global config_crt_scanlines, config_screen_shake, config_music, config_sfx, current_state
    play_sfx('click')
    if settings_sel == 0:
        config_crt_scanlines = not config_crt_scanlines
    elif settings_sel == 1:
        config_screen_shake = not config_screen_shake
    elif settings_sel == 2:
        config_music = not config_music
        if music_channel:
            if config_music:
                music_channel.set_volume(0.2)
            else:
                music_channel.set_volume(0.0)
    elif settings_sel == 3:
        config_sfx = not config_sfx
        # mute/unmute SFX
        if not config_sfx:
            for sname in sounds:
                if sname != 'music':
                    sounds[sname].set_volume(0.0)
        else:
            for sname in sounds:
                if sname != 'music':
                    sounds[sname].set_volume(1.0)
    elif settings_sel == 4:
        current_state = STATE_MENU


# ----------------- MAIN GAME LOOP -----------------
clock = pygame.time.Clock()
running = True

# Screen shake variables
shake_offset_x = 0
shake_offset_y = 0

while running:
    # Maintain solid 60 FPS
    clock.tick(60)
    avg_fps = clock.get_fps() if clock.get_fps() > 0 else 60.0
    
    # Process screen shake decaying
    if screen_shake_amt > 0:
        shake_offset_x = random.randint(-screen_shake_amt, screen_shake_amt)
        shake_offset_y = random.randint(-screen_shake_amt, screen_shake_amt)
        screen_shake_amt -= 1
    else:
        shake_offset_x = 0
        shake_offset_y = 0

    # Event handling
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
            
        elif event.type == pygame.KEYDOWN:
            if current_state == STATE_INTRO:
                if intro_stage >= 3:
                    play_sfx('click')
                    current_state = STATE_MENU
                    
            elif current_state == STATE_MENU:
                if event.key == pygame.K_UP or event.key == pygame.K_w:
                    menu_selected = (menu_selected - 1) % len(menu_options)
                    play_sfx('select')
                elif event.key == pygame.K_DOWN or event.key == pygame.K_s:
                    menu_selected = (menu_selected + 1) % len(menu_options)
                    play_sfx('select')
                elif event.key == pygame.K_RETURN or event.key == pygame.K_SPACE:
                    play_sfx('click')
                    selected_opt = menu_options[menu_selected]
                    if selected_opt == "CAMPAIGN":
                        campaign_score = 0
                        campaign_time_left = 60
                        campaign_targets.clear()
                        gun_ammo = 30
                        gun_reserve = 120
                        current_state = STATE_CAMPAIGN
                    elif selected_opt == "MULTIPLAYER":
                        mp_allies_score = 6500
                        mp_axis_score = 6200
                        player_health = 100
                        mp_killfeed.clear()
                        mp_enemies.clear()
                        mp_timer = 180
                        mp_game_over = False
                        gun_ammo = 30
                        gun_reserve = 120
                        trigger_mp_announcement("MATCH INITIATED")
                        current_state = STATE_MULTIPLAYER
                    elif selected_opt == "ZOMBIES":
                        zombie_score = 0
                        zombie_round = 1
                        zombies_spawned_this_round = 0
                        zombies_max_round = 8
                        zombies_list.clear()
                        player_health = 100
                        z_ammo = 7
                        gun_ammo = 7
                        gun_max_ammo = 7
                        gun_reserve = 42
                        z_timer = 180
                        zombie_wave_active = True
                        trigger_mp_announcement("ROUND 1 INCOMING")
                        current_state = STATE_ZOMBIES
                    elif selected_opt == "SETTINGS":
                        current_state = STATE_SETTINGS
                    elif selected_opt == "EXIT":
                        running = False
                        
            elif current_state == STATE_CAMPAIGN:
                if event.key == pygame.K_ESCAPE:
                    current_state = STATE_MENU
                elif event.key == pygame.K_r:
                    trigger_reload()
                    
            elif current_state == STATE_MULTIPLAYER:
                if mp_game_over:
                    current_state = STATE_MENU
                else:
                    if event.key == pygame.K_ESCAPE:
                        current_state = STATE_MENU
                    elif event.key == pygame.K_r:
                        trigger_reload()
                        
            elif current_state == STATE_ZOMBIES:
                if event.key == pygame.K_ESCAPE:
                    current_state = STATE_MENU
                elif event.key == pygame.K_r:
                    trigger_reload()
                    
            elif current_state == STATE_SETTINGS:
                if event.key == pygame.K_UP or event.key == pygame.K_w:
                    settings_sel = (settings_sel - 1) % len(settings_options)
                    play_sfx('select')
                elif event.key == pygame.K_DOWN or event.key == pygame.K_s:
                    settings_sel = (settings_sel + 1) % len(settings_options)
                    play_sfx('select')
                elif event.key == pygame.K_RETURN:
                    process_settings_toggle()
                    
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1: # Left Click
                if current_state == STATE_CAMPAIGN:
                    process_campaign_shoot()
                elif current_state == STATE_MULTIPLAYER and not mp_game_over:
                    process_mp_shoot()
                elif current_state == STATE_ZOMBIES:
                    process_zombies_shoot()

    # Update logic based on state
    if current_state == STATE_INTRO:
        update_intro()
    elif current_state == STATE_MENU:
        update_menu()
    elif current_state == STATE_CAMPAIGN:
        update_campaign()
    elif current_state == STATE_MULTIPLAYER:
        update_multiplayer()
    elif current_state == STATE_ZOMBIES:
        update_zombies()

    # Render screen inside shake boundary offset
    draw_surf = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
    
    if current_state == STATE_INTRO:
        draw_intro(draw_surf)
    elif current_state == STATE_MENU:
        draw_menu(draw_surf)
    elif current_state == STATE_CAMPAIGN:
        draw_campaign(draw_surf)
    elif current_state == STATE_MULTIPLAYER:
        draw_multiplayer(draw_surf)
    elif current_state == STATE_ZOMBIES:
        draw_zombies(draw_surf)
    elif current_state == STATE_SETTINGS:
        draw_settings(draw_surf)
        
    # Draw CRT Scanline overlay filter if enabled
    if config_crt_scanlines:
        for y in range(0, SCREEN_HEIGHT, 3):
            pygame.draw.line(draw_surf, (0, 0, 0, 35), (0, y), (SCREEN_WIDTH, y), 1)

    # Blit drawing surface to screen with shake offsets
    screen.fill((0, 0, 0))
    screen.blit(draw_surf, (shake_offset_x, shake_offset_y))
    pygame.display.flip()

pygame.quit()
sys.exit()
