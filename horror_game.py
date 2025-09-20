"""
Horror Story Fullscreen Game (Python + Pygame)

Scary edition with:
- Flickering flashlight
- Low ambient sound (ambient.ogg in same folder)
- Shadows sometimes converge on you
- Glitch/static flashes
- Personalised death message
- Hides hostname/IP if known recording/streaming apps running

Install:
    pip install pygame psutil
"""

import sys, os, random, time, getpass, platform, math, socket
import psutil, pygame
from pygame import gfxdraw

# ----------------------------- Configuration -----------------------------
WIDTH, HEIGHT = 0, 0  # will be overwritten by fullscreen
FPS = 60
FLASHLIGHT_RADIUS = 200
SHADOW_SPAWN_RATE = 1.2  # seconds
MAX_SHADOWS = 12

recording_apps = [
    "obs64.exe", "obs32.exe", "streamlabs obs.exe", "xsplit.exe", "zoom.exe", "teams.exe"
]

# ----------------------------- Utility functions -----------------------------
def gather_system_info(max_procs=10):
    username = getpass.getuser()
    hostname = platform.node()

    procs = []
    try:
        for p in psutil.process_iter(['name']):
            name = p.info.get('name') or '<unknown>'
            procs.append(name)
    except Exception:
        procs = ['(process list unavailable)']

    seen = []
    for name in procs:
        if name not in seen:
            seen.append(name)
        if len(seen) >= max_procs:
            break

    return {'username': username, 'hostname': hostname, 'processes': seen}

# ----------------------------- Game objects -----------------------------
class Shadow:
    def __init__(self, x, y, size, speed):
        self.x = x
        self.y = y
        self.size = size
        self.speed = speed
        self.dir = random.uniform(0, 2 * math.pi)

    def update(self, dt, target_x, target_y):
        # occasionally change direction toward player
        if random.random() < 0.01:
            self.dir = math.atan2(target_y - self.y, target_x - self.x)
        # sometimes freeze
        if random.random() < 0.005:
            return
        self.x += self.speed * dt * math.cos(self.dir)
        self.y += self.speed * dt * math.sin(self.dir)
        # wrap
        if self.x < -100: self.x = WIDTH + 100
        if self.x > WIDTH + 100: self.x = -100
        if self.y < -100: self.y = HEIGHT + 100
        if self.y > HEIGHT + 100: self.y = -100

    def draw(self, surf):
        s = int(self.size)
        for i in range(6, 0, -1):
            a = max(0, 40 - i * 6)
            gfxdraw.filled_circle(surf, int(self.x), int(self.y),
                                  int(s * i / 6), (0, 0, 0, a))

# ----------------------------- Main game -----------------------------
def main():
    pygame.init()
    pygame.display.set_caption('They Know')
    pygame.mixer.init()

    # Fullscreen setup
    info = pygame.display.Info()
    global WIDTH, HEIGHT
    WIDTH, HEIGHT = info.current_w, info.current_h
    screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.FULLSCREEN)

    clock = pygame.time.Clock()

    try:
        font = pygame.font.Font(None, 32)
        title_font = pygame.font.Font(None, 80)
    except Exception:
        font = pygame.font.SysFont('Arial', 32)
        title_font = pygame.font.SysFont('Arial', 80)

    # gather info
    sysinfo = gather_system_info(max_procs=12)
    username = sysinfo['username']
    hostname = sysinfo['hostname']
    proc_list = sysinfo['processes']

    # detect if any recording apps are open
    is_recording = any(
        any(app in p.lower() for app in recording_apps)
        for p in proc_list
    )

    # choose what to display
    if is_recording:
        shown_hostname = "[hidden]"
        shown_ip = "[hidden]"
    else:
        shown_hostname = hostname
        try:
            shown_ip = socket.gethostbyname(hostname)
        except Exception:
            shown_ip = "(ip unavailable)"

    # Narrative lines
    lines = []
    lines.append(f"Welcome, {username}.")
    lines.append(f"This is {shown_hostname}.")
    lines.append(f"IP: {shown_ip}")
    lines.append("I have been watching what you leave open:")
    for p in proc_list:
        lines.append(f" - {p}")
    lines.append(time.strftime("It's %H:%M:%S. You shouldn't be here."))
    lines.append("Move your mouse to keep the light. Survive the night.")

    # Sound
    try:
        pygame.mixer.Sound('ambient.ogg').play(-1)
    except Exception:
        pass  # no sound file provided

    # prepare shadow list
    shadows = []
    spawn_timer = 0
    start_time = time.time()
    alive = True
    reveal_text = ''
    reveal_time = None

    running = True
    while running:
        dt = clock.tick(FPS) / 1000.0
        spawn_timer += dt

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                if event.key == pygame.K_r and not alive:
                    main()  # restart
                    return

        mouse_x, mouse_y = pygame.mouse.get_pos()

        # spawn shadows
        if spawn_timer > SHADOW_SPAWN_RATE and len(shadows) < MAX_SHADOWS and alive:
            spawn_timer = 0
            sx = random.uniform(-100, WIDTH + 100)
            sy = random.uniform(-100, HEIGHT + 100)
            size = random.uniform(30, 120)
            speed = random.uniform(10, 60)
            shadows.append(Shadow(sx, sy, size, speed))

        # update shadows
        for s in shadows:
            s.update(dt, mouse_x, mouse_y)

        # collision check
        if alive:
            for s in shadows:
                dist = math.hypot(s.x - mouse_x, s.y - mouse_y)
                if dist < s.size * 0.6 and dist > FLASHLIGHT_RADIUS * 0.6:
                    alive = False
                    reveal_time = time.time()
                    reveal_text = (
                        f"I've been inside {shown_hostname} since {time.strftime('%Y')}. "
                        f"You left {len(proc_list)} doors open, {username}. "
                        "Now you are in the dark with me."
                    )
                    break

        # draw
        screen.fill((10, 10, 10))

        ambient = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        ambient.fill((0, 0, 0, 200))

        shadow_surf = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        for s in shadows:
            s.draw(shadow_surf)
        ambient.blit(shadow_surf, (0, 0))

        # flashlight mask with flicker
        mask = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        mask.fill((0, 0, 0, 220))
        flicker = random.uniform(0.8, 1.2)
        current_radius = int(FLASHLIGHT_RADIUS * flicker)
        for r in range(current_radius, 0, -8):
            alpha = max(0, int(220 * (r / current_radius)))
            gfxdraw.filled_circle(mask, mouse_x, mouse_y, r, (0, 0, 0, alpha))
        ambient.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_SUB)
        screen.blit(ambient, (0, 0))

        elapsed = time.time() - start_time
        if elapsed < 6:
            t = title_font.render('They Know', True, (200, 200, 200))
            tr = t.get_rect(center=(WIDTH//2, HEIGHT//6))
            screen.blit(t, tr)
            for i, line in enumerate(lines[:int(elapsed)+1]):
                txt = font.render(line, True, (180, 180, 180))
                screen.blit(txt, (WIDTH//10, HEIGHT//4 + i * 30))

        # death reveal
        if not alive:
            death_overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            death_overlay.fill((0, 0, 0, 180))
            screen.blit(death_overlay, (0, 0))
            if reveal_time is not None:
                delay = random.uniform(0.02, 0.08)
                t_elapsed = time.time() - reveal_time
                chars = int(t_elapsed / delay)
                toshow = reveal_text[:chars]
                y = HEIGHT//2 - 60
                for line in toshow.split('\n'):
                    txt = font.render(line, True, (255, 100, 100))
                    screen.blit(txt, (WIDTH//6, y))
                    y += 40
                hint = font.render('Press R to restart or ESC to quit', True, (200, 200, 200))
                screen.blit(hint, (WIDTH//6, y + 40))

        # HUD
        hud_surf = pygame.Surface((360, 160), pygame.SRCALPHA)
        hud_surf.fill((0, 0, 0, 120))
        hud_surf_rect = hud_surf.get_rect(bottomright=(WIDTH - 20, HEIGHT - 20))
        screen.blit(hud_surf, hud_surf_rect)
        hud_title = font.render('Open: (observed)', True, (200, 200, 200))
        screen.blit(hud_title, (hud_surf_rect.x + 12, hud_surf_rect.y + 8))
        for i, p in enumerate(proc_list[:5]):
            t = font.render(p, True, (170, 170, 170))
            screen.blit(t, (hud_surf_rect.x + 12, hud_surf_rect.y + 40 + i * 22))

        # glitch overlay occasionally
        if random.random() < 0.05:
            glitch = pygame.Surface((WIDTH, HEIGHT))
            glitch.fill((random.randint(0,255), 0, 0))
            glitch.set_alpha(15)
            screen.blit(glitch, (0, random.randint(-10,10)))

        # crosshair
        gfxdraw.filled_circle(screen, mouse_x, mouse_y, 3, (255, 255, 255, 200))

        pygame.display.flip()

    pygame.quit()

if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print('An error occurred:', e)
        print('Make sure pygame and psutil are installed: pip install pygame psutil')