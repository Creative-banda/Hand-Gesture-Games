import math
import random

import pygame

from settings import (
    PARTICLE_COLLISION_COUNT,
    PARTICLE_CONFETTI_COUNT,
    PARTICLE_MAX_COUNT,
    PARTICLE_PIPE_PASS_COUNT,
    PARTICLE_STAGE_MOTE_COUNT,
)

WHITE = (255, 255, 255)
GOLD = (255, 215, 0)

_circle_cache = {}


def _particle_surface(size, color, alpha):
    bucket = max(0, min(7, int(alpha / 32)))
    key = (size, color, bucket)
    if key in _circle_cache:
        return _circle_cache[key]
    a = min(255, (bucket + 1) * 32)
    surf = pygame.Surface((size * 2 + 2, size * 2 + 2), pygame.SRCALPHA)
    pygame.draw.circle(surf, color + (a,), (size + 1, size + 1), size)
    if len(_circle_cache) > 400:
        _circle_cache.clear()
    _circle_cache[key] = surf
    return surf


class Particle:
    __slots__ = ("x", "y", "vx", "vy", "life", "max_life", "size", "color", "gravity", "drag", "shape", "alpha_mul")

    def __init__(self, x, y, vx, vy, life, size, color, gravity=0.0, drag=0.0, shape="circle", alpha_mul=1.0):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.life = life
        self.max_life = life
        self.size = size
        self.color = color
        self.gravity = gravity
        self.drag = drag
        self.shape = shape
        self.alpha_mul = alpha_mul


class ParticleSystem:
    def __init__(self):
        self.particles = []
        self.rng = random.Random()

    def emit(self, pos, count, colors, speed=(40, 140), angle=(0, 360), size=(2, 4), life=(0.5, 0.9),
             gravity=0.0, drag=0.0, shape="circle", alpha_mul=1.0):
        for _ in range(count):
            ang = math.radians(self.rng.uniform(*angle))
            sp = self.rng.uniform(*speed)
            self.particles.append(
                Particle(
                    pos[0], pos[1],
                    math.cos(ang) * sp, math.sin(ang) * sp,
                    self.rng.uniform(*life),
                    self.rng.randint(int(size[0]), int(size[1])),
                    colors[self.rng.randrange(len(colors))],
                    gravity, drag, shape, alpha_mul,
                )
            )
        excess = len(self.particles) - PARTICLE_MAX_COUNT
        if excess > 0:
            del self.particles[:excess]

    def emit_pipe_pass(self, pos, accent=(255, 230, 140)):
        self.emit(
            pos, PARTICLE_PIPE_PASS_COUNT,
            [WHITE, GOLD, accent],
            speed=(50, 170), angle=(-160, -20), size=(2, 4), life=(0.4, 0.8), gravity=220,
        )

    def emit_collision(self, pos):
        self.emit(
            pos, PARTICLE_COLLISION_COUNT,
            [WHITE, (210, 210, 215), (255, 170, 90), (150, 150, 160)],
            speed=(60, 280), size=(2, 5), life=(0.5, 1.1), gravity=520, drag=1.6,
        )

    def emit_confetti(self, pos):
        self.emit(
            pos, PARTICLE_CONFETTI_COUNT,
            [GOLD, WHITE, (255, 240, 160)],
            speed=(80, 260), angle=(-150, -30), size=(2, 5), life=(0.8, 1.5), gravity=320,
        )
        self.emit(
            pos, PARTICLE_CONFETTI_COUNT // 3,
            [GOLD, (255, 250, 200)],
            speed=(60, 140), size=(3, 6), life=(0.9, 1.6), gravity=-40, shape="rect",
        )

    def emit_stage_motes(self, width, height, accent):
        for _ in range(PARTICLE_STAGE_MOTE_COUNT):
            x = self.rng.uniform(0, width)
            y = height * self.rng.uniform(0.55, 0.95)
            color = accent if self.rng.random() < 0.5 else WHITE
            self.particles.append(
                Particle(
                    x, y, self.rng.uniform(-12, 12), self.rng.uniform(-55, -25),
                    self.rng.uniform(1.4, 2.4), self.rng.randint(2, 3), color,
                    gravity=-8, drag=0.4, shape="circle", alpha_mul=0.65,
                )
            )

    def update(self, dt):
        alive = []
        for p in self.particles:
            p.vy += p.gravity * dt
            if p.drag:
                damp = max(0.0, 1.0 - p.drag * dt)
                p.vx *= damp
                p.vy *= damp
            p.x += p.vx * dt
            p.y += p.vy * dt
            p.life -= dt
            if p.life > 0:
                alive.append(p)
        self.particles = alive

    def draw(self, surface, offset=(0, 0)):
        ox, oy = offset
        for p in self.particles:
            t = p.life / p.max_life
            alpha = int(255 * min(1.0, t * 1.6) * p.alpha_mul)
            if p.shape == "rect":
                surf = _particle_surface(p.size, p.color, alpha)
                img = pygame.transform.rotate(surf, (p.life * 220) % 360)
                surface.blit(img, (int(p.x + ox - img.get_width() // 2), int(p.y + oy - img.get_height() // 2)))
            else:
                surf = _particle_surface(p.size, p.color, alpha)
                surface.blit(surf, (int(p.x + ox - p.size - 1), int(p.y + oy - p.size - 1)))
