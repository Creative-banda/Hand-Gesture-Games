import math

import pygame

from settings import (
    SCORE_FONT_FRACTION,
    SCORE_PULSE_DURATION,
    SHAKE_FREQUENCY,
    SHAKE_MAX_OFFSET,
    SHAKE_TRAUMA_DECAY,
    STAGE_BANNER_DURATION,
)

GOLD = (255, 215, 0)
WHITE = (255, 255, 255)

_font_cache = {}


def get_font(size_px):
    size_px = max(8, int(size_px))
    if size_px not in _font_cache:
        try:
            _font_cache[size_px] = pygame.font.Font("assets/fonts/Helvetica Bold.ttf", size_px)
        except (FileNotFoundError, OSError):
            _font_cache[size_px] = pygame.font.SysFont("arial", size_px, bold=True)
    return _font_cache[size_px]


def render_outlined(text, font, color, outline_px=2, outline_alpha=200):
    text_surf = font.render(text, True, color)
    pad = outline_px + 2
    surf = pygame.Surface(
        (text_surf.get_width() + pad * 2, text_surf.get_height() + pad * 2), pygame.SRCALPHA
    )
    if outline_px > 0:
        outline = font.render(text, True, (10, 12, 18, outline_alpha))
        for dx in (-outline_px, 0, outline_px):
            for dy in (-outline_px, 0, outline_px):
                if dx or dy:
                    surf.blit(outline, (pad + dx, pad + dy))
    shadow = font.render(text, True, (0, 0, 0, 110))
    surf.blit(shadow, (pad + outline_px + 1, pad + outline_px + 1))
    surf.blit(text_surf, (pad, pad))
    return surf


def draw_text_centered(surface, text, font, color, center, outline_px=2):
    surf = render_outlined(text, font, color, outline_px)
    surface.blit(surf, surf.get_rect(center=center))
    return surf


class ScreenShake:
    def __init__(self):
        self.trauma = 0.0
        self.time = 0.0
        self._seed = pygame.time.get_ticks() % 1000

    def add(self, amount):
        self.trauma = min(1.0, self.trauma + amount)

    @property
    def active(self):
        return self.trauma > 0.001

    def update(self, dt):
        self.time += dt
        self.trauma = max(0.0, self.trauma - SHAKE_TRAUMA_DECAY * dt)

    def offset(self):
        if not self.active:
            return (0, 0)
        amp = SHAKE_MAX_OFFSET * self.trauma * self.trauma
        t = self.time * SHAKE_FREQUENCY
        ox = amp * math.sin(t * 1.13 + self._seed)
        oy = amp * math.sin(t * 0.97 + self._seed * 2.7)
        return (int(ox), int(oy))


class FadeOverlay:
    def __init__(self, window_size):
        self.surface = pygame.Surface(window_size, pygame.SRCALPHA)
        self.mode = None
        self.color = (0, 0, 0)
        self.t = 0.0
        self.duration = 0.0
        self.flash_color = (255, 255, 255)
        self.flash_t = 0.0
        self.flash_duration = 0.0

    def fade_in(self, color, duration):
        self.color = color
        self.duration = max(0.001, duration)
        self.t = 0.0
        self.mode = "in"

    def fade_out(self, color, duration):
        self.color = color
        self.duration = max(0.001, duration)
        self.t = 0.0
        self.mode = "out"

    def flash(self, color, duration=0.22):
        self.flash_color = color
        self.flash_duration = max(0.001, duration)
        self.flash_t = self.flash_duration

    def update(self, dt):
        if self.mode:
            self.t += dt
            if self.t >= self.duration:
                self.mode = None
                self.t = 0.0
        if self.flash_t > 0:
            self.flash_t = max(0.0, self.flash_t - dt)

    @property
    def blocking(self):
        return bool(self.mode) or self.flash_t > 0

    def draw(self, surface):
        if self.mode == "out":
            a = int(255 * min(1.0, self.t / self.duration))
        elif self.mode == "in":
            a = int(255 * max(0.0, 1.0 - self.t / self.duration))
        else:
            a = 0
        if a > 0:
            self.surface.fill(self.color + (a,))
            surface.blit(self.surface, (0, 0))
        if self.flash_t > 0:
            fa = int(220 * (self.flash_t / self.flash_duration))
            self.surface.fill(self.flash_color + (fa,))
            surface.blit(self.surface, (0, 0))


class ScoreDisplay:
    def __init__(self, window_size):
        h = window_size[1]
        self.font = get_font(h * SCORE_FONT_FRACTION)
        self.glow_font = get_font(h * SCORE_FONT_FRACTION * 1.06)
        self.value = -1
        self.cached = None
        self.glow_cached = None
        self.pulse_t = 0.0

    def set(self, value):
        if value != self.value:
            self.value = value
            self.cached = render_outlined(str(value), self.font, WHITE, outline_px=max(2, self.font.get_height() // 26))
            self.glow_cached = render_outlined(str(value), self.glow_font, GOLD, outline_px=3)

    def pulse(self):
        self.pulse_t = SCORE_PULSE_DURATION

    def update(self, dt):
        self.pulse_t = max(0.0, self.pulse_t - dt)

    def draw(self, surface, center):
        if self.cached is None:
            return
        img = self.cached
        if self.pulse_t > 0:
            t = self.pulse_t / SCORE_PULSE_DURATION
            scale = 1.0 + 0.24 * math.sin(t * math.pi)
            img = pygame.transform.rotozoom(img, 0, scale)
            glow = self.glow_cached
            glow.set_alpha(int(150 * t))
            surface.blit(glow, glow.get_rect(center=center))
        rect = img.get_rect(center=(center[0], int(center[1] - (img.get_height() - self.cached.get_height()) / 2)))
        surface.blit(img, rect)


class HudChips:
    def __init__(self, window_size):
        h = window_size[1]
        self.font = get_font(h / 46)
        self.margin = int(h * 0.016)
        self._text_cache = {}

    def _chip(self, label, value, value_color, border_color, border_alpha):
        key = (label, str(value), value_color, border_color, border_alpha // 16)
        if key in self._text_cache:
            return self._text_cache[key]
        label_surf = self.font.render(label.upper() + " ", True, (185, 200, 218, 210))
        value_surf = self.font.render(str(value), True, value_color + (255,))
        margin = self.margin
        text_w = label_surf.get_width() + value_surf.get_width()
        text_h = max(label_surf.get_height(), value_surf.get_height())
        chip_h = text_h + margin
        chip_w = text_w + margin * 2
        chip = pygame.Surface((chip_w, chip_h), pygame.SRCALPHA)
        pygame.draw.rect(chip, (10, 16, 28, 105), chip.get_rect(), border_radius=chip_h // 2)
        pygame.draw.rect(chip, border_color + (border_alpha,), chip.get_rect().inflate(-1, -1), 1,
                         border_radius=chip_h // 2 - 1)
        chip.blit(label_surf, (margin, (chip_h - label_surf.get_height()) // 2))
        chip.blit(value_surf, (margin + label_surf.get_width(), (chip_h - value_surf.get_height()) // 2))
        if len(self._text_cache) > 60:
            self._text_cache.clear()
        self._text_cache[key] = chip
        return chip

    def draw(self, surface, player, stage, best, new_best=False):
        margin = self.margin
        x, y = margin, margin
        pulse = 0
        if new_best:
            pulse = int(60 * (0.5 + 0.5 * math.sin(pygame.time.get_ticks() / 180.0)))
        chips = [
            ("Player", player, WHITE, (255, 255, 255), 42),
            ("Stage", stage, WHITE, (255, 255, 255), 42),
            ("Best", best, GOLD, (255, 215, 0) if new_best else (255, 255, 255), 42 + pulse if new_best else 42),
        ]
        for label, value, color, border, balpha in chips:
            chip = self._chip(label, value, color, border, balpha)
            surface.blit(chip, (x, y))
            y += chip.get_height() + int(margin * 0.5)


class StageBanner:
    def __init__(self, stage, window_size):
        self.stage = stage
        self.duration = STAGE_BANNER_DURATION
        self.t = 0.0
        h = window_size[1]
        self.main = render_outlined(f"STAGE {stage}", get_font(h / 14), GOLD, outline_px=3)
        self.sub = render_outlined("SPEED UP", get_font(h / 48), WHITE, outline_px=2)

    @property
    def done(self):
        return self.t >= self.duration

    def update(self, dt):
        self.t += dt

    def draw(self, surface, accent=GOLD):
        if self.done:
            return
        p = self.t / self.duration
        alpha = math.sin(p * math.pi)
        rise = int((1 - p) * 26)
        center = (surface.get_width() // 2, int(surface.get_height() * 0.17) + rise)
        main = self.main.copy()
        main.set_alpha(int(255 * alpha))
        surface.blit(main, main.get_rect(center=center))
        sub = self.sub.copy()
        sub.set_alpha(int(220 * alpha))
        surface.blit(sub, sub.get_rect(center=(center[0], center[1] + main.get_height())))
