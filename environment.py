import math
import random

import pygame

from settings import (
    ATMOSPHERE_GROUND_STEP,
    ATMOSPHERE_PHASE_STEP,
    CLOUD_ALTITUDE_RANGE,
    CLOUD_COUNT_FAR,
    CLOUD_COUNT_NEAR,
    CLOUD_SCALE_RANGE_FAR,
    CLOUD_SCALE_RANGE_NEAR,
    CLOUD_WIND_SPEED,
    GROUND_HEIGHT_FRACTION,
    MAX_PHASE,
    MOON_X_FRACTION,
    MOON_Y_FRACTION,
    PALETTES,
    PARALLAX_SPEEDS,
    STAR_COUNT,
    SUN_X_FRACTION,
    TWINKLE_STAR_COUNT,
)


def clamp(value, low, high):
    return max(low, min(high, value))


def lerp(a, b, t):
    return a + (b - a) * t


def lerp_color(c1, c2, t):
    return tuple(int(round(lerp(a, b, t))) for a, b in zip(c1[:3], c2[:3])) + tuple(
        int(round(lerp(a, b, t))) for a, b in zip(c1[3:], c2[3:])
    )


def smoothstep(t):
    return t * t * (3.0 - 2.0 * t)


def shade(color, amount):
    if amount >= 0:
        return tuple(int(c + (255 - c) * amount) for c in color[:3]) + tuple(color[3:])
    return tuple(int(c * (1 + amount)) for c in color[:3]) + tuple(color[3:])


def sample_palette(phase):
    keys = PALETTES
    if phase <= keys[0]["phase"]:
        return dict(keys[0])
    if phase >= keys[-1]["phase"]:
        return dict(keys[-1])
    for i in range(len(keys) - 1):
        a, b = keys[i], keys[i + 1]
        if a["phase"] <= phase <= b["phase"]:
            span = b["phase"] - a["phase"]
            t = smoothstep((phase - a["phase"]) / span if span > 0 else 0)
            out = {}
            for k, va in a.items():
                if k == "phase":
                    continue
                vb = b[k]
                if isinstance(va, (int, float)):
                    out[k] = type(va)(lerp(va, vb, t))
                else:
                    out[k] = lerp_color(va, vb, t)
            return out
    return dict(keys[-1])


def _make_surface(size):
    return pygame.Surface(size, pygame.SRCALPHA).convert_alpha()


def tinted(mask, color):
    out = mask.copy()
    out.fill((color[0], color[1], color[2], color[3] if len(color) > 3 else 255),
             special_flags=pygame.BLEND_RGBA_MULT)
    return out


def build_sky_strip(height, palette):
    strip = _make_surface((8, height))
    top = palette["sky_top"]
    bottom = palette["sky_bottom"]
    glow = palette["horizon_glow"]
    for y in range(height):
        t = y / (height - 1)
        color = lerp_color(top, bottom, t)
        g = 1.0 - abs(t - 0.86) / 0.5
        if g > 0:
            g = min(1.0, g) * (glow[3] / 255.0)
            color = lerp_color(color, glow[:3], min(1.0, g))
        pygame.draw.line(strip, color, (0, y), (7, y))
    return strip


def build_starfield(width, height, rng):
    surf = _make_surface((width, height))
    zone = int(height * 0.75)
    for _ in range(STAR_COUNT):
        x = rng.randrange(width)
        y = rng.randrange(zone)
        r = rng.choice((1, 1, 1, 2))
        a = rng.randint(90, 230)
        tint = rng.random()
        color = (int(220 + 35 * tint), int(225 + 25 * tint), 255)
        pygame.draw.circle(surf, color + (a,), (x, y), r)
    for _ in range(12):
        x = rng.randrange(width)
        y = rng.randrange(zone)
        length = rng.randint(3, 6)
        pygame.draw.line(surf, (235, 240, 255, 130), (x - length, y), (x + length, y), 1)
        pygame.draw.line(surf, (235, 240, 255, 130), (x, y - length), (x, y + length), 1)
    return surf


def build_sun_mask(diameter):
    surf = _make_surface((diameter, diameter))
    center = diameter // 2
    steps = 30
    for i in range(steps, 0, -1):
        r = int(center * i / steps)
        t = i / steps
        a = int(255 * (t ** 3.0))
        pygame.draw.circle(surf, (255, 255, 255, a), (center, center), max(1, r))
    return surf


def build_sun_core(diameter):
    surf = _make_surface((diameter, diameter))
    pygame.draw.circle(surf, (255, 255, 255, 245), (diameter // 2, diameter // 2), max(2, diameter // 2))
    return surf


def build_moon(diameter):
    surf = _make_surface((diameter, diameter))
    c = diameter // 2
    r = diameter // 2 - 1
    pygame.draw.circle(surf, (226, 232, 246, 255), (c, c), r)
    pygame.draw.circle(surf, (208, 216, 236, 255), (int(c - r * 0.28), int(c - r * 0.18)), int(r * 0.22))
    pygame.draw.circle(surf, (206, 214, 234, 255), (int(c + r * 0.30), int(c + r * 0.26)), int(r * 0.16))
    pygame.draw.circle(surf, (212, 220, 240, 255), (int(c + r * 0.10), int(c - r * 0.42)), int(r * 0.11))
    return surf


def build_cloud_mask(rng, width, height):
    surf = _make_surface((width, height))
    base_y = int(height * 0.70)
    lobes = rng.randint(4, 6)
    for i in range(lobes):
        cx = int(width * (0.12 + 0.76 * (i / max(1, lobes - 1))))
        r = int(height * rng.uniform(0.22, 0.34))
        cy = base_y - rng.randint(int(height * 0.06), int(height * 0.30))
        pygame.draw.circle(surf, (255, 255, 255, 255), (cx, cy), r)
    body_h = int(height * 0.34)
    pygame.draw.ellipse(
        surf, (255, 255, 255, 255),
        pygame.Rect(int(width * 0.06), base_y - body_h, int(width * 0.88), body_h * 2),
    )
    shade_surf = _make_surface((width, height))
    for y in range(height):
        t = y / height
        a = int(120 * max(0.0, (t - 0.42) / 0.58))
        if a:
            pygame.draw.line(shade_surf, (160, 170, 200, a), (0, y), (width, y))
    surf.blit(shade_surf, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
    surf.fill((255, 255, 255, 208), special_flags=pygame.BLEND_RGBA_MULT)
    return surf


def build_ridge_mask(width, height, cycles, rng, snow=False):
    half_w = max(64, width // 2)
    half_h = max(24, height // 2)
    surf = _make_surface((half_w, half_h))
    snow_surf = _make_surface((half_w, half_h)) if snow else None
    phases = [rng.uniform(0, math.tau) for _ in cycles]
    points = []
    for x in range(0, half_w + 3, 3):
        y = 0.0
        for (freq, amp), ph in zip(cycles, phases):
            y += math.sin((x / half_w) * math.tau * freq + ph) * amp * half_h
        base = half_h * (0.62 - sum(a for _, a in cycles) * 0.35)
        points.append((x, base + y))
    points.append((half_w, half_h + 4))
    points.append((0, half_h + 4))
    pygame.draw.polygon(surf, (255, 255, 255, 255), points)
    if snow:
        n = len(points) - 2
        for i in range(2, n - 2):
            x, y = points[i]
            depth = min(points[i - 2][1], points[i + 2][1]) - y
            if depth > half_h * 0.05 and y < half_h * 0.55:
                s = max(3, int(depth * 0.9))
                pygame.draw.polygon(
                    snow_surf,
                    (255, 255, 255, 255),
                    [(x - s, y + int(s * 1.15)), (x + s, y + int(s * 1.15)), (x, y - 1)],
                )
    body = pygame.transform.smoothscale(surf, (width, height))
    caps = pygame.transform.smoothscale(snow_surf, (width, height)) if snow else None
    return body, caps


def build_hills_mask(width, height, rng):
    half_w = max(64, width // 2)
    half_h = max(24, height // 2)
    surf = _make_surface((half_w, half_h))
    cycles = [(2, 0.16), (3, 0.11), (7, 0.05)]
    phases = [rng.uniform(0, math.tau) for _ in cycles]
    points = []
    for x in range(0, half_w + 3, 3):
        y = 0.0
        for (freq, amp), ph in zip(cycles, phases):
            y += math.sin((x / half_w) * math.tau * freq + ph) * amp * half_h
        points.append((x, half_h * 0.45 + y))
    points.append((half_w, half_h + 4))
    points.append((0, half_h + 4))
    pygame.draw.polygon(surf, (255, 255, 255, 255), points)
    return pygame.transform.smoothscale(surf, (width, height))


def build_trees_mask(width, height, rng):
    surf = _make_surface((width, height))
    pad = int(height * 0.8)
    count = max(8, width // 95)

    def draw_tree(x, by, s):
        trunk_w = max(2, int(s * 0.09))
        pygame.draw.rect(surf, (185, 185, 185, 255), (x - trunk_w // 2, by - int(s * 0.30), trunk_w, int(s * 0.30)))
        if rng.random() < 0.55:
            for i in range(3):
                wide = s * (0.62 - 0.14 * i)
                ty = by - int(s * (0.38 + 0.27 * i))
                th = int(s * 0.40)
                pygame.draw.polygon(
                    surf,
                    (255, 255, 255, 255),
                    [(x - wide / 2, ty + th), (x + wide / 2, ty + th), (x, ty)],
                )
        else:
            crown_r = s * 0.30
            cy = by - int(s * 0.58)
            for ox, oy, rr in (
                (-crown_r * 0.7, 0.05, 0.85),
                (crown_r * 0.7, 0.02, 0.9),
                (0, -crown_r * 0.55, 1.0),
            ):
                pygame.draw.circle(
                    surf,
                    (255, 255, 255, 255),
                    (int(x + ox * crown_r), int(cy + oy * crown_r)),
                    max(2, int(crown_r * rr)),
                )

    for _ in range(count):
        lo, hi = min(pad, width // 4), max(min(pad, width // 4) + 1, width - min(pad, width // 4))
        x = rng.randrange(lo, hi)
        s = height * rng.uniform(0.7, 1.05)
        xs = {x}
        if x < pad:
            xs.add(x + width)
        if x > width - pad:
            xs.add(x - width)
        for xx in xs:
            draw_tree(xx, height - 2, s)
    surf.fill((255, 255, 255, 245), special_flags=pygame.BLEND_RGBA_MULT)
    return surf


def build_bushes_mask(width, height, rng):
    surf = _make_surface((width, height))
    count = max(6, width // 120)
    pad = height * 2
    for _ in range(count):
        x = rng.randrange(0, width)
        s = height * rng.uniform(0.7, 1.15)
        xs = {x}
        if x < pad:
            xs.add(x + width)
        if x > width - pad:
            xs.add(x - width)
        for xx in xs:
            for ox, rr in ((-s * 0.55, 0.55), (s * 0.5, 0.6), (0, 0.78)):
                pygame.draw.circle(
                    surf,
                    (255, 255, 255, 255),
                    (int(xx + ox), int(height - s * rr * 0.5)),
                    max(2, int(s * rr)),
                )
            for _ in range(4):
                bx = int(xx + rng.uniform(-s, s))
                bl = rng.randint(3, max(4, int(height * 0.4)))
                lean = rng.randint(-3, 3)
                pygame.draw.line(surf, (230, 230, 230, 255), (bx, height - 1), (bx + lean, height - 1 - bl), 1)
    return surf


def build_ground_tile(width, height, palette):
    surf = _make_surface((width, height))
    rng = random.Random(20240817)
    grass_h = int(height * 0.36)
    pygame.draw.rect(surf, palette["soil_color"], (0, grass_h, width, height - grass_h))
    pygame.draw.rect(surf, palette["grass_body"], (0, 0, width, grass_h))
    for y in range(grass_h):
        t = y / max(1, grass_h - 1)
        row_color = lerp_color(palette["grass_top"], palette["grass_body"], t)
        pygame.draw.line(surf, row_color, (0, y), (width, y))
    rim = shade(palette["grass_top"], 0.30)
    for x in range(0, width, 6):
        r = rng.randint(2, 4)
        pygame.draw.circle(surf, rim, (x, 1), r)
    for _ in range(width // 4):
        x = rng.randrange(width)
        bl = rng.randint(4, 11)
        lean = rng.randint(-3, 4)
        pygame.draw.line(
            surf,
            lerp_color(palette["grass_top"], palette["grass_body"], rng.random()),
            (x, 2),
            (x + lean, 2 + bl),
            1,
        )
    speck = palette["soil_speckle"]
    for _ in range(width // 6):
        x = rng.randrange(width)
        y = rng.randrange(grass_h + 2, height)
        pygame.draw.rect(surf, speck, (x, y, rng.randint(1, 3), rng.randint(1, 2)))
    light_soil = shade(palette["soil_color"], 0.18)
    dark_soil = shade(palette["soil_color"], -0.22)
    for _ in range(width // 40):
        x = rng.randrange(width)
        y = rng.randrange(grass_h + 4, height - 2)
        rw = rng.randint(4, 10)
        rh = max(2, rw // 2)
        pygame.draw.ellipse(surf, light_soil, (x, y, rw, rh))
        pygame.draw.ellipse(surf, dark_soil, (x + 1, y + 1, rw - 2, rh - 2))
    pygame.draw.line(surf, shade(palette["grass_top"], 0.45), (0, 0), (width, 0), 2)
    return surf


def build_vignette(width, height):
    w, h = max(80, width // 4), max(60, height // 4)
    small = _make_surface((w, h))
    max_a = 150
    for x in range(w):
        t = abs(x - w / 2) / (w / 2)
        a = int(max_a * max(0.0, (t - 0.55) / 0.45) ** 2.0)
        if a:
            pygame.draw.line(small, (6, 10, 20, a), (x, 0), (x, h))
    for y in range(h):
        t = abs(y - h / 2) / (h / 2)
        a = int(max_a * max(0.0, (t - 0.62) / 0.38) ** 2.0)
        if a:
            pygame.draw.line(small, (6, 10, 20, a), (0, y), (w, y))
    return pygame.transform.smoothscale(small, (width, height))


def build_haze_strip(haze_height, palette):
    strip = _make_surface((16, 128))
    hc = palette["haze_color"]
    ha = palette["haze_alpha"]
    for y in range(128):
        t = (y / 127) ** 1.6
        pygame.draw.line(strip, hc + (int(ha * t),), (0, y), (15, y))
    return pygame.transform.smoothscale(strip, (16, max(8, haze_height // 4)))


class ParallaxBackground:
    def __init__(self, window_size):
        self.size = (int(window_size[0]), int(window_size[1]))
        self.width, self.height = self.size
        self.rng = random.Random()
        self.ground_top = int(self.height * (1 - GROUND_HEIGHT_FRACTION))
        self.phase_value = 0.0
        self.step_index = -1
        self.flash_strength = 0.0
        self.scroll = {k: 0.0 for k in PARALLAX_SPEEDS}
        self.pending_jobs = []
        self.pal = dict(PALETTES[0])

        self.palette_steps = [
            sample_palette(i * ATMOSPHERE_PHASE_STEP)
            for i in range(int(MAX_PHASE / ATMOSPHERE_PHASE_STEP) + 1)
        ]
        self.ground_stride = max(1, int(round(ATMOSPHERE_GROUND_STEP / ATMOSPHERE_PHASE_STEP)))
        self.ground_tiles = [
            build_ground_tile(self.width, self.height - self.ground_top, self.palette_steps[i])
            for i in range(0, len(self.palette_steps), self.ground_stride)
        ]
        self.sky_strips = [build_sky_strip(self.height, p) for p in self.palette_steps]
        self.haze_height = int(self.height * 0.22)
        self.haze_strips = [build_haze_strip(self.haze_height, p) for p in self.palette_steps]

        self.stars = build_starfield(self.width, self.height, self.rng)
        self.twinkles = [
            (
                self.rng.randrange(self.width),
                self.rng.randrange(int(self.height * 0.6)),
                self.rng.choice((1, 1, 2)),
                self.rng.uniform(0, math.tau),
                self.rng.uniform(1.2, 3.0),
            )
            for _ in range(TWINKLE_STAR_COUNT)
        ]
        moon_d = int(self.height * 0.055)
        self.moon = build_moon(moon_d)
        self.moon_halo = tinted(build_sun_mask(moon_d * 4), (190, 205, 240))
        self.sun_mask = build_sun_mask(int(self.height * 0.42))
        self.sun_core = build_sun_core(int(self.height * 0.055))

        layer_heights = {
            "mountains_far": int(self.height * 0.34),
            "mountains_near": int(self.height * 0.27),
            "hills": int(self.height * 0.16),
            "trees": int(self.height * 0.14),
            "bushes": int(self.height * 0.06),
        }
        self.baselines = {
            "mountains_far": self.ground_top,
            "mountains_near": self.ground_top + 2,
            "snow": self.ground_top + 2,
            "hills": self.ground_top + 6,
            "trees": self.ground_top + 12,
            "bushes": self.ground_top + 20,
        }
        mask_mfar, _ = build_ridge_mask(
            self.width, layer_heights["mountains_far"],
            [(1, 0.20), (2, 0.14), (5, 0.07)], self.rng,
        )
        mask_mnear, mask_snow = build_ridge_mask(
            self.width, layer_heights["mountains_near"],
            [(1, 0.22), (3, 0.13), (6, 0.06)], self.rng, snow=True,
        )
        self.masks = {
            "mountains_far": mask_mfar,
            "mountains_near": mask_mnear,
            "snow": mask_snow,
            "hills": build_hills_mask(self.width, layer_heights["hills"], self.rng),
            "trees": build_trees_mask(self.width, layer_heights["trees"], self.rng),
            "bushes": build_bushes_mask(self.width, layer_heights["bushes"], self.rng),
        }
        self.layers = {}

        self.clouds = []
        for kind, count, scale_range, factor_key in (
            ("far", CLOUD_COUNT_FAR, CLOUD_SCALE_RANGE_FAR, "clouds_far"),
            ("near", CLOUD_COUNT_NEAR, CLOUD_SCALE_RANGE_NEAR, "clouds_near"),
        ):
            for i in range(count):
                self.clouds.append(
                    {
                        "kind": kind,
                        "factor": PARALLAX_SPEEDS[factor_key],
                        "variant": i % 3,
                        "speed_mul": self.rng.uniform(0.5, 1.6),
                        "alpha_mul": self.rng.uniform(0.7, 1.0),
                        "scale": self.rng.uniform(*scale_range),
                        "x": self.rng.uniform(0, self.width),
                        "y_frac": self.rng.uniform(*CLOUD_ALTITUDE_RANGE),
                        "sprite": None,
                    }
                )
        self.cloud_masks = [
            build_cloud_mask(random.Random(1000 + v), 300, 110) for v in range(3)
        ]

        self.vignette = build_vignette(self.width, self.height)
        self.surf_atmo = _make_surface(self.size)
        self.surf_sky = _make_surface(self.size)
        self.surf_haze = _make_surface((self.width, self.haze_height))
        self.surf_sun = _make_surface(self.sun_mask.get_size())
        self.warm_band = _make_surface((self.width, self.haze_height))
        self.layers = {}

        self.set_phase(0.0, instant=True)

    def _jobs_for(self, idx):
        pal = self.palette_steps[idx]
        return [
            ("sky", idx),
            ("atmo", idx),
            ("sun", idx),
            ("haze", idx),
            ("clouds", idx),
            ("layer", "mountains_far", pal["mountains_far"]),
            ("layer", "mountains_near", pal["mountains_near"]),
            ("layer", "snow", pal["snow_color"]),
            ("layer", "hills", pal["hills"]),
            ("layer", "trees", pal["trees"]),
            ("layer", "bushes", pal["bushes"]),
        ]

    def _run_job(self, job):
        kind = job[0]
        if kind == "sky":
            idx = job[1]
            pal = self.palette_steps[idx]
            pygame.transform.smoothscale(self.sky_strips[idx], self.size, self.surf_sky)
            star_a = int(pal["star_alpha"])
            if star_a > 3:
                self.stars.set_alpha(star_a)
                self.surf_sky.blit(self.stars, (0, 0))
        elif kind == "atmo":
            pal = self.palette_steps[job[1]]
            self.surf_atmo.fill((0, 0, 0, 0))
            grade = pal["grade_color"]
            if grade[3] > 0:
                self.surf_atmo.fill(grade)
            factor = clamp(pal["vignette_alpha"] / 150.0, 0.0, 1.0)
            self.vignette.set_alpha(int(255 * factor))
            self.surf_atmo.blit(self.vignette, (0, 0))
        elif kind == "sun":
            self.surf_sun = tinted(self.sun_mask, self.palette_steps[job[1]]["sun_color"])
        elif kind == "haze":
            pygame.transform.smoothscale(
                self.haze_strips[job[1]], (self.width, self.haze_height), self.surf_haze
            )
        elif kind == "clouds":
            cc = self.palette_steps[job[1]]["cloud_color"]
            sprites = [tinted(m, cc) for m in self.cloud_masks]
            for cloud in self.clouds:
                w = max(8, int(300 * cloud["scale"]))
                h = max(4, int(110 * cloud["scale"]))
                cloud["sprite"] = pygame.transform.smoothscale(
                    sprites[cloud["variant"]], (w, h)
                )
        elif kind == "layer":
            _, key, color = job
            self.layers[key] = tinted(self.masks[key], color)

    def set_phase(self, phase, instant=False):
        self.phase_value = clamp(phase, 0.0, MAX_PHASE)
        idx = min(len(self.palette_steps) - 1, int(self.phase_value / ATMOSPHERE_PHASE_STEP + 0.5))
        if idx == self.step_index:
            return
        self.step_index = idx
        self.pal = self.palette_steps[idx]
        jobs = self._jobs_for(idx)
        if instant:
            for j in jobs:
                self._run_job(j)
            self.pending_jobs = []
        else:
            self.pending_jobs = jobs

    def horizon_flash(self, strength):
        self.flash_strength = max(self.flash_strength, strength)

    @property
    def accent_color(self):
        return self.pal["sun_color"]

    def update(self, dt, world_speed):
        if self.pending_jobs:
            self._run_job(self.pending_jobs.pop(0))
        self.flash_strength = max(0.0, self.flash_strength - dt * 1.1)
        for key, factor in PARALLAX_SPEEDS.items():
            self.scroll[key] = (self.scroll[key] + world_speed * factor * dt) % self.width
        for cloud in self.clouds:
            drift = (CLOUD_WIND_SPEED * cloud["speed_mul"] + world_speed * cloud["factor"]) * dt
            cloud["x"] -= drift
            if cloud["x"] < -300 * cloud["scale"] - 40:
                cloud["x"] = self.width + self.rng.uniform(10, 200)
                cloud["y_frac"] = self.rng.uniform(*CLOUD_ALTITUDE_RANGE)

    def _blit_layer(self, surface, key, sx, sy):
        img = self.layers[key]
        scroll_key = "mountains_near" if key == "snow" else key
        factor = PARALLAX_SPEEDS[scroll_key]
        off = self.scroll[scroll_key]
        x = -(off % self.width)
        y = self.baselines[key] - img.get_height()
        surface.blit(img, (int(x + sx * factor), int(y + sy * factor)))
        surface.blit(img, (int(x + self.width + sx * factor), int(y + sy * factor)))

    def _draw_celestial(self, surface, pal, sx, sy):
        f = PARALLAX_SPEEDS["celestial"]
        sun_a = int(pal["sun_glow_alpha"])
        if sun_a > 4:
            sun_x = int(self.width * SUN_X_FRACTION + sx * f)
            sun_y = int(self.height * pal["sun_y_fraction"] + sy * f)
            self.surf_sun.set_alpha(sun_a)
            surface.blit(self.surf_sun, self.surf_sun.get_rect(center=(sun_x, sun_y)))
            self.sun_core.set_alpha(sun_a)
            surface.blit(self.sun_core, self.sun_core.get_rect(center=(sun_x, sun_y)))
        moon_a = int(pal["moon_alpha"])
        if moon_a > 4:
            mx = int(self.width * MOON_X_FRACTION + sx * f)
            my = int(self.height * MOON_Y_FRACTION + sy * f)
            self.moon_halo.set_alpha(min(255, moon_a // 2))
            surface.blit(self.moon_halo, self.moon_halo.get_rect(center=(mx, my)))
            self.moon.set_alpha(moon_a)
            surface.blit(self.moon, self.moon.get_rect(center=(mx, my)))

    def draw_back(self, surface, shake=(0, 0)):
        sx, sy = shake
        pal = self.pal
        surface.blit(self.surf_sky, (0, 0))

        star_a = int(pal["star_alpha"])
        if star_a > 3:
            t = pygame.time.get_ticks() / 1000.0
            for (tx, ty, tr, phase, speed) in self.twinkles:
                tw = star_a * (0.45 + 0.55 * (0.5 + 0.5 * math.sin(t * speed + phase)))
                pygame.draw.circle(surface, (235, 240, 255, int(tw)), (int(tx + sx * 0.2), int(ty + sy * 0.2)), tr)

        self._draw_celestial(surface, pal, sx, sy)

        for cloud in self.clouds:
            alpha = int(clamp(pal["cloud_color"][3] * cloud["alpha_mul"], 0, 255))
            cloud["sprite"].set_alpha(alpha)
            surface.blit(
                cloud["sprite"],
                (int(cloud["x"] + sx * cloud["factor"]), int(self.height * cloud["y_frac"] + sy * cloud["factor"])),
            )

        self._blit_layer(surface, "mountains_far", sx, sy)
        self._blit_layer(surface, "mountains_near", sx, sy)
        if "snow" in self.layers:
            self._blit_layer(surface, "snow", sx, sy)

        boost = self.flash_strength
        if boost > 0.01:
            haze = self.surf_haze.copy()
            self.warm_band.fill(self.accent_color)
            haze.blit(self.warm_band, (0, 0), special_flags=pygame.BLEND_RGB_ADD)
        else:
            haze = self.surf_haze
        surface.blit(haze, (int(sx * 0.3), int(self.ground_top - self.haze_height + 8 + sy * 0.3)))

        self._blit_layer(surface, "hills", sx, sy)
        self._blit_layer(surface, "trees", sx, sy)
        self._blit_layer(surface, "bushes", sx, sy)

    def draw_front(self, surface, shake=(0, 0)):
        gidx = min(len(self.ground_tiles) - 1, int(self.phase_value / ATMOSPHERE_GROUND_STEP))
        ground = self.ground_tiles[gidx]
        off = self.scroll["foreground"]
        x = -(off % self.width)
        y = self.ground_top
        surface.blit(ground, (int(x + shake[0]), int(y + shake[1])))
        surface.blit(ground, (int(x + self.width + shake[0]), int(y + shake[1])))

    def draw_atmosphere(self, surface):
        surface.blit(self.surf_atmo, (0, 0))


_BACKGROUND = None


def get_background(window_size):
    global _BACKGROUND
    size = (int(window_size[0]), int(window_size[1]))
    if _BACKGROUND is None or _BACKGROUND.size != size:
        _BACKGROUND = ParallaxBackground(size)
    return _BACKGROUND
