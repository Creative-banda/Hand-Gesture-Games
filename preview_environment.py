import os
import random
import time

import pygame

os.environ.setdefault("SDL_VIDEODRIVER", "")
pygame.init()

WIDTH, HEIGHT = 1280, 720
screen = pygame.display.set_mode((WIDTH, HEIGHT))

from settings import MAX_DELTA_TIME, DISPLAY_FPS_CAP, BIRD_HEIGHT_FRACTION, PIPE_WIDTH_FRACTION
from environment import get_background
from effects import ScoreDisplay, HudChips, StageBanner
from particles import ParticleSystem

OUT_DIR = "preview"
os.makedirs(OUT_DIR, exist_ok=True)
clock = pygame.time.Clock()
bg = get_background((WIDTH, HEIGHT))
particles = ParticleSystem()

bird_img = pygame.image.load("assets/images/bird_sprite.png").convert_alpha()
bh = int(HEIGHT * BIRD_HEIGHT_FRACTION)
bird_img = pygame.transform.scale(bird_img, (int(bird_img.get_width() * bh / bird_img.get_height()), bh))
pipe_img = pygame.image.load("assets/images/pipe_sprite_single.png").convert_alpha()
pw = int(WIDTH * PIPE_WIDTH_FRACTION)
ph = int(pipe_img.get_height() * pw / pipe_img.get_width())
pipe_img = pygame.transform.scale(pipe_img, (pw, ph))
pipe_shadow = pipe_img.copy()
pipe_shadow.fill((8, 14, 20, 255), special_flags=pygame.BLEND_RGBA_MULT)
pipe_shadow.set_alpha(78)

score_display = ScoreDisplay((WIDTH, HEIGHT))
score_display.set(7)
hud = HudChips((WIDTH, HEIGHT))


def settle(phase, frames=40):
    bg.set_phase(phase, instant=True)
    for _ in range(frames):
        bg.update(1 / 60, 140)


def draw_scene(pipes):
    bg.draw_back(screen)
    shadow_offset = (int(HEIGHT * 0.012), int(HEIGHT * 0.014))
    for top, bottom in pipes:
        screen.blit(pipe_shadow, bottom.move(shadow_offset))
        screen.blit(pipe_shadow, top.move(shadow_offset))
        screen.blit(pipe_img, bottom)
        screen.blit(pygame.transform.flip(pipe_img, 0, 1), top)
    if pipes:
        gap_center_x = pipes[0][0].centerx + 10
        gap_center_y = (pipes[0][0].bottom + pipes[0][1].top) // 2
        bird_rect = bird_img.get_rect(center=(gap_center_x - 120, gap_center_y))
    else:
        bird_rect = bird_img.get_rect(center=(WIDTH // 6, HEIGHT // 2))
    screen.blit(bird_img, bird_rect)
    bg.draw_front(screen)
    particles.draw(screen)
    bg.draw_atmosphere(screen)


def mock_pipes():
    rng = random.Random(4)
    pipes = []
    for i in range(2):
        x = int(WIDTH * (0.45 + i * 0.5))
        gap_pos = int(HEIGHT * (0.3 + 0.18 * i))
        gap = int(HEIGHT * 0.25)
        top = pipe_img.get_rect(midbottom=(x, gap_pos))
        bottom = pipe_img.get_rect(midtop=(x, gap_pos + gap))
        pipes.append((top, bottom))
    return pipes


def bench(frames=240):
    times = []
    pipes = mock_pipes()
    for _ in range(frames):
        t0 = time.perf_counter()
        bg.update(1 / 60, 140)
        draw_scene(pipes)
        pygame.display.flip()
        times.append(time.perf_counter() - t0)
    times.sort()
    avg = sum(times) / len(times) * 1000
    p95 = times[int(len(times) * 0.95)] * 1000
    print(f"frame ms: avg={avg:.2f} p95={p95:.2f} -> ~{1000/avg:.0f} fps headroom")


for phase, name in [(0, "day"), (2, "golden"), (4, "sunset"), (5.5, "dusk"), (7, "night")]:
    particles.particles.clear()
    settle(phase)
    pipes = mock_pipes()
    draw_scene(pipes)
    score_display.draw(screen, (WIDTH // 2, int(HEIGHT * 0.08)))
    hud.draw(screen, "player_one", max(1, int(phase) + 1), 12, phase >= 2)
    pygame.image.save(screen, f"{OUT_DIR}/{name}.png")
    print("saved", name)

settle(4)
pipes = mock_pipes()
draw_scene(pipes)
particles.emit_pipe_pass((pipes[0][0].centerx - 110, (pipes[0][0].bottom + pipes[0][1].top) // 2))
banner = StageBanner(5, (WIDTH, HEIGHT))
for _ in range(30):
    banner.update(1 / 30)
banner.draw(screen)
score_display.pulse()
score_display.draw(screen, (WIDTH // 2, int(HEIGHT * 0.08)))
hud.draw(screen, "player_one", 5, 9, True)
pygame.image.save(screen, f"{OUT_DIR}/gameplay_fx.png")
print("saved gameplay_fx")

bench()
pygame.quit()
