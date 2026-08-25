import sys, random, pygame, json
from collections import deque
import cv2 as cv, mediapipe as mp
from pathlib import Path
import math

mp_drawing = mp.solutions.drawing_utils
mp_drawing_styles = mp.solutions.drawing_styles
mp_hands = mp.solutions.hands
drawing_spec = mp_drawing.DrawingSpec(thickness=1, circle_radius=1)
pygame.init()

VID_CAP = cv.VideoCapture(1)

if not VID_CAP.isOpened():
    print("Error: Could not open camera")
    sys.exit()

screen_info = pygame.display.Info()
window_size = (screen_info.current_w, screen_info.current_h)
screen = pygame.display.set_mode(window_size, pygame.FULLSCREEN)

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GOLD = (255, 215, 0)

pygame.mixer.init()
bg_music = pygame.mixer.Sound('assets/music/background_music3.mp3')
pipe_pass_sound = pygame.mixer.Sound('assets/music/pipe_pass.mp3')
game_over_sound = pygame.mixer.Sound('assets/music/game_over.mp3')

mp_pose = mp.solutions.pose

from settings import (
    BIRD_HEIGHT_FRACTION,
    DISPLAY_FPS_CAP,
    GRACE_PERIOD_SECONDS,
    MAX_DELTA_TIME,
    MAX_PHASE,
    PIPE_GAP_FRACTION,
    PIPE_MAX_BOTTOM_FRACTION,
    PIPE_MIN_TOP_FRACTION,
    PIPE_SPACING_FRACTION,
    PIPE_WIDTH_FRACTION,
    REFERENCE_FPS,
    SPAWN_INTERVAL_MIN_FRAMES,
    SPAWN_INTERVAL_STAGE_SCALE,
    SPAWN_INTERVAL_START_FRAMES,
    STAGE_DURATION_SECONDS,
    WORLD_SPEED_MULTIPLIER,
)

BIRD_MIN_ANGLE = -32
BIRD_MAX_ANGLE = 42
from environment import get_background
from effects import (
    FadeOverlay,
    GOLD,
    HudChips,
    ScoreDisplay,
    ScreenShake,
    StageBanner,
    draw_text_centered,
    get_font,
    render_outlined,
)
from particles import ParticleSystem


def load_high_scores():
    try:
        with open('high_scores.json', 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []

def save_high_score(username, score):
    scores = load_high_scores()
    scores.append({"username": username, "score": score})
    scores.sort(key=lambda x: x["score"], reverse=True)
    scores = scores[:10]
    with open('high_scores.json', 'w') as f:
        json.dump(scores, f)

def draw_scores_panel(surface, font):
    scores = load_high_scores()
    panel_rect = pygame.Rect(window_size[0] // 3, int(window_size[1] / 1.5), window_size[0] // 3, 150)
    panel_surface = pygame.Surface((panel_rect.width, panel_rect.height), pygame.SRCALPHA)
    panel_surface.fill((18, 24, 44, 170))
    surface.blit(panel_surface, (panel_rect.x, panel_rect.y))
    pygame.draw.rect(surface, GOLD, panel_rect.inflate(-2, -2), 2, border_radius=15)
    title_text = "Top Scores"
    draw_text_centered(surface, title_text, font, WHITE, (panel_rect.centerx, panel_rect.y + 22))
    score_spacing = 35
    for i, score in enumerate(scores[:3]):
        score_text = f"#{i + 1} {score['username']}: {score['score']}"
        score_surf = font.render(score_text, True, GOLD if i == 0 else WHITE)
        score_x = panel_rect.x + 20
        score_y = panel_rect.y + 48 + i * score_spacing
        surface.blit(score_surf, (score_x, score_y))

def draw_gradient_button(surface, rect, text, font, color, enabled):
    colors = [(30, 130, 60), (70, 200, 110)] if enabled else [(50, 50, 50), (100, 100, 100)]
    body = pygame.Surface(rect.size, pygame.SRCALPHA)
    pygame.draw.rect(body, colors[0] + (235,), body.get_rect(), border_radius=12)
    inner = body.get_rect().inflate(-6, -6)
    h = inner.height
    for y in range(h):
        t = y / max(1, h - 1)
        c = (
            int(colors[1][0] * (0.75 + 0.25 * t)),
            int(colors[1][1] * (0.75 + 0.25 * t)),
            int(colors[1][2] * (0.75 + 0.25 * t)),
            235,
        )
        pygame.draw.line(body, c, (inner.x, y + 3), (inner.right, y + 3))
    mask = pygame.Surface(rect.size, pygame.SRCALPHA)
    pygame.draw.rect(mask, (255, 255, 255, 255), rect.inflate(-6, -6), border_radius=10)
    body.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
    surface.blit(body, rect.topleft)
    text_surf = font.render(text, True, color)
    surface.blit(text_surf, text_surf.get_rect(center=rect.center))

def _animated_backdrop(bg, clock):
    dt = min(MAX_DELTA_TIME, clock.tick(DISPLAY_FPS_CAP) / 1000.0)
    bg.update(dt, 26)
    bg.draw_back(screen)
    bg.draw_front(screen)
    bg.draw_atmosphere(screen)
    return dt

def show_start_screen():
    username = ""

    input_box = pygame.Rect(window_size[0] // 4, window_size[1] // 2, window_size[0] // 2, 60)
    start_button = pygame.Rect(window_size[0] // 3, window_size[1] // 2 + 100, window_size[0] // 3, 60)

    title_font = pygame.font.Font("assets/fonts/FlappyBirdy.ttf", 80)
    input_font = pygame.font.SysFont("Helvetica Bold.ttf", 36)
    score_font = pygame.font.SysFont("Helvetica Bold.ttf", 32)

    bird_icon = pygame.image.load("assets/images/bird_sprite.png").convert_alpha()
    bird_icon = pygame.transform.scale(bird_icon, (50, 50))

    bg = get_background(window_size)
    bg.set_phase(0.0)
    clock = pygame.time.Clock()

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                VID_CAP.release()
                cv.destroyAllWindows()
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if start_button.collidepoint(event.pos) and username:
                    return username
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN and username:
                    return username
                elif event.key == pygame.K_BACKSPACE:
                    username = username[:-1]
                elif len(username) < 15:
                    if event.unicode.isalnum() or event.unicode == '_':
                        username += event.unicode

        _animated_backdrop(bg, clock)

        bob = math.sin(pygame.time.get_ticks() / 500.0) * 6
        draw_text_centered(screen, "Flappy Bird", title_font, WHITE,
                           (window_size[0] // 2, int(window_size[1] / 5) + int(bob)), outline_px=3)

        box_glow = 150 + int(70 * (0.5 + 0.5 * math.sin(pygame.time.get_ticks() / 350.0)))
        box_surface = pygame.Surface(input_box.size, pygame.SRCALPHA)
        pygame.draw.rect(box_surface, (250, 250, 252, 225), box_surface.get_rect(), border_radius=10)
        screen.blit(box_surface, input_box.topleft)
        pygame.draw.rect(screen, GOLD + (box_glow,), input_box.inflate(2, 2), 3, border_radius=11)

        icon_bob = math.sin(pygame.time.get_ticks() / 400.0) * 3
        screen.blit(bird_icon, (input_box.x - 60, input_box.y + 5 + int(icon_bob)))

        if not username:
            placeholder = input_font.render("Enter your username", True, (150, 150, 150))
            screen.blit(placeholder, (input_box.x + 10, input_box.y + 10))
        else:
            txt_surface = input_font.render(username, True, BLACK)
            screen.blit(txt_surface, (input_box.x + 10, input_box.y + 10))

        mouse_pos = pygame.mouse.get_pos()
        hovered = username and start_button.collidepoint(mouse_pos)
        shadow_rect = start_button.move(0, 4)
        button_shadow = pygame.Surface(start_button.size, pygame.SRCALPHA)
        pygame.draw.rect(button_shadow, (0, 0, 0, 90), button_shadow.get_rect(), border_radius=12)
        screen.blit(button_shadow, shadow_rect.topleft)
        draw_gradient_button(screen, start_button, "Start Game", input_font, WHITE, bool(username))
        if hovered:
            pygame.draw.rect(screen, WHITE + (120,), start_button, 2, border_radius=12)

        draw_scores_panel(screen, score_font)

        pygame.display.flip()

def show_countdown():
    font = get_font(window_size[1] // 5)
    bg = get_background(window_size)
    bg.set_phase(0.0)
    clock = pygame.time.Clock()
    numbers = [3, 2, 1]
    per_number = 0.85
    total = len(numbers) * per_number
    elapsed = 0.0

    running = True
    while running:
        dt = min(MAX_DELTA_TIME, clock.tick(DISPLAY_FPS_CAP) / 1000.0)
        for event in pygame.event.get():
            if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                VID_CAP.release()
                cv.destroyAllWindows()
                pygame.quit()
                sys.exit()
        elapsed += dt
        if elapsed >= total:
            running = False
        _animated_backdrop(bg, clock)

        idx = min(int(elapsed / per_number), len(numbers) - 1)
        num = numbers[idx]
        local_t = (elapsed - idx * per_number) / per_number
        pop = 1.0 + 0.35 * math.sin(min(1.0, local_t * 2.4) * math.pi)
        alpha = 255 if local_t < 0.75 else int(255 * (1 - (local_t - 0.75) / 0.25))

        text = render_outlined(str(num), font, WHITE, outline_px=4)
        text = pygame.transform.rotozoom(text, 0, pop)
        text.set_alpha(alpha)
        center = (window_size[0] // 2, window_size[1] // 2)
        screen.blit(text, text.get_rect(center=center))

        ring_alpha = int(160 * max(0.0, 1.0 - local_t))
        if ring_alpha > 4:
            radius = int(window_size[1] * 0.16 * (0.6 + local_t * 0.8))
            pygame.draw.circle(screen, GOLD + (ring_alpha,), center, radius, 4)

        pygame.display.flip()

def _load_game_assets():
    bird_img = pygame.image.load("assets/images/bird_sprite.png").convert_alpha()
    bird_height = int(window_size[1] * BIRD_HEIGHT_FRACTION)
    bird_width = int(bird_img.get_width() * (bird_height / bird_img.get_height()))
    bird_img = pygame.transform.scale(bird_img, (bird_width, bird_height))

    pipe_img = pygame.image.load("assets/images/pipe_sprite_single.png").convert_alpha()
    pipe_width = int(window_size[0] * PIPE_WIDTH_FRACTION)
    pipe_height = int(pipe_img.get_height() * (pipe_width / pipe_img.get_width()))
    pipe_img = pygame.transform.scale(pipe_img, (pipe_width, pipe_height))

    pipe_shadow = pipe_img.copy()
    pipe_shadow.fill((8, 14, 20, 255), special_flags=pygame.BLEND_RGBA_MULT)
    pipe_shadow.set_alpha(78)
    pipe_img_top = pygame.transform.flip(pipe_img, 0, 1)

    highlight_w = max(4, pipe_width // 16)
    highlight = pygame.Surface((highlight_w, pipe_height), pygame.SRCALPHA)
    for y in range(pipe_height):
        t = y / pipe_height
        a = max(6, int(44 * (1 - abs(t - 0.45) * 1.5)))
        pygame.draw.line(highlight, (255, 255, 255, a), (0, y), (highlight_w, y))

    bird_frames = [
        pygame.transform.rotozoom(bird_img, -angle, 1.0) for angle in range(BIRD_MIN_ANGLE, BIRD_MAX_ANGLE + 1)
    ]

    return bird_img, bird_frames, pipe_img, pipe_img_top, pipe_shadow, highlight

def game_loop(username):
    bg_music.play(-1)

    bird_img, bird_frames, pipe_img, pipe_img_top, pipe_shadow, pipe_highlight = _load_game_assets()
    bird_frame = bird_img.get_rect()
    bird_frame.center = (window_size[0] // 6, window_size[1] // 2)
    rotated_bird = bird_frames[32]

    pipe_frames = deque()
    pipe_starting_template = pipe_img.get_rect()
    space_between_pipes = int(window_size[1] * PIPE_GAP_FRACTION)

    bg = get_background(window_size)
    bg.set_phase(0.0, instant=True)

    particles = ParticleSystem()
    shake = ScreenShake()
    fade = FadeOverlay(window_size)
    fade.fade_in((0, 0, 0), 0.5)
    score_display = ScoreDisplay(window_size)
    hud = HudChips(window_size)
    ready_font = get_font(window_size[1] // 16)
    ready_text = render_outlined("GET READY!", ready_font, WHITE, outline_px=3)

    stage = 1
    spawn_interval_frames = SPAWN_INTERVAL_START_FRAMES
    dist_between_pipes = int(window_size[0] * PIPE_SPACING_FRACTION)
    score = 0
    didUpdateScore = False
    game_is_running = True

    min_pipe_height = int(window_size[1] * PIPE_MIN_TOP_FRACTION)
    max_pipe_height = int(window_size[1] * PIPE_MAX_BOTTOM_FRACTION)

    high_scores = load_high_scores()
    current_high_score = high_scores[0]["score"] if high_scores else 0
    new_best_announced = current_high_score <= 0

    stage_timer = 0.0
    spawn_accumulator = spawn_interval_frames / REFERENCE_FPS - GRACE_PERIOD_SECONDS
    grace_timer = GRACE_PERIOD_SECONDS
    banner = None
    prev_bird_y = float(bird_frame.centery)
    vy_smooth = 0.0
    bird_angle = 0.0
    die_timer = -1.0

    def world_speed_now():
        interval_seconds = spawn_interval_frames / REFERENCE_FPS
        return dist_between_pipes / interval_seconds * WORLD_SPEED_MULTIPLIER

    game_clock = pygame.time.Clock()

    with mp_pose.Pose(
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5
    ) as pose:
        while True:
            dt = min(MAX_DELTA_TIME, game_clock.tick(DISPLAY_FPS_CAP) / 1000.0)

            for event in pygame.event.get():
                if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                    VID_CAP.release()
                    cv.destroyAllWindows()
                    pygame.quit()
                    sys.exit()

            ret, frame = VID_CAP.read()
            if not ret:
                print("Error reading frame from camera")
                continue

            frame = cv.rotate(frame, cv.ROTATE_90_COUNTERCLOCKWISE)
            frame.flags.writeable = False
            frame = cv.cvtColor(frame, cv.COLOR_BGR2RGB)
            results = pose.process(frame)
            frame.flags.writeable = True

            if not game_is_running:
                shake.update(dt)
                particles.update(dt)
                fade.update(dt)
                bg.update(dt, 0)
                if die_timer > 0:
                    die_timer -= dt
                    if die_timer <= 0:
                        return score
                shake_offset = shake.offset()
                bg.draw_back(screen, shake_offset)
                shadow_offset = (int(window_size[1] * 0.012), int(window_size[1] * 0.014))
                for pf in pipe_frames:
                    screen.blit(pipe_shadow, pf[1].move(shadow_offset))
                    screen.blit(pipe_shadow, pf[0].move(shadow_offset))
                    screen.blit(pipe_img, pf[1])
                    screen.blit(pipe_img_top, pf[0])
                screen.blit(rotated_bird, rotated_bird.get_rect(center=bird_frame.center))
                bg.draw_front(screen, shake_offset)
                particles.draw(screen, shake_offset)
                fade.draw(screen)
                pygame.display.flip()
                continue

            ret_pose = results.pose_landmarks is not None
            if ret_pose:
                landmarks = results.pose_landmarks.landmark
                left_shoulder = landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER]
                left_wrist = landmarks[mp_pose.PoseLandmark.LEFT_WRIST]
                left_mid_y = (left_shoulder.x + left_wrist.x) / 2
                sensitivity_factor = 1.5
                mid_y = left_mid_y * sensitivity_factor

                new_y = int(mid_y * window_size[1])
                if grace_timer > 0:
                    bird_frame.centery = window_size[1] // 2
                    vy_smooth *= max(0.0, 1.0 - dt * 6.0)
                else:
                    raw_vy = (new_y - prev_bird_y) / max(dt, 0.001)
                    vy_smooth += (raw_vy - vy_smooth) * min(1.0, dt * 9.0)
                    bird_frame.centery = new_y
                    if bird_frame.top < 0: bird_frame.y = 0
                    if bird_frame.bottom > window_size[1]: bird_frame.y = window_size[1] - bird_frame.height
                prev_bird_y = float(new_y)
            else:
                vy_smooth *= max(0.0, 1.0 - dt * 4.0)

            target_angle = max(BIRD_MIN_ANGLE, min(BIRD_MAX_ANGLE, vy_smooth * 0.05))
            bird_angle += (target_angle - bird_angle) * min(1.0, dt * 10.0)
            rotated_bird = bird_frames[int(round(bird_angle)) - BIRD_MIN_ANGLE]

            stage_timer += dt
            if stage_timer >= STAGE_DURATION_SECONDS:
                stage_timer -= STAGE_DURATION_SECONDS
                time_between_pipe_spawn_new = max(SPAWN_INTERVAL_MIN_FRAMES, int(spawn_interval_frames * SPAWN_INTERVAL_STAGE_SCALE))
                spawn_interval_frames = time_between_pipe_spawn_new
                stage += 1
                banner = StageBanner(stage, window_size)
                bg.horizon_flash(0.9)
                particles.emit_stage_motes(window_size[0], window_size[1], bg.accent_color)

            phase = min(MAX_PHASE, (stage - 1) + stage_timer / STAGE_DURATION_SECONDS)
            bg.set_phase(phase)

            speed = world_speed_now()
            bg.update(dt, speed)
            score_display.update(dt)
            shake.update(dt)
            fade.update(dt)
            particles.update(dt)
            if banner:
                banner.update(dt)
                if banner.done:
                    banner = None

            spawn_accumulator += dt
            if grace_timer > 0:
                grace_timer -= dt
            spawn_interval_seconds = spawn_interval_frames / REFERENCE_FPS
            while spawn_accumulator >= spawn_interval_seconds:
                spawn_accumulator -= spawn_interval_seconds
                gap_position = random.randint(min_pipe_height, max_pipe_height - space_between_pipes)
                top = pipe_starting_template.copy()
                top.x = window_size[0]
                top.bottom = gap_position
                bottom = pipe_starting_template.copy()
                bottom.x = window_size[0]
                bottom.top = gap_position + space_between_pipes
                pipe_frames.append([top, bottom])

            move_dx = speed * dt
            for pf in pipe_frames:
                pf[0].x -= move_dx
                pf[1].x -= move_dx
            if len(pipe_frames) > 0 and pipe_frames[0][0].right < 0:
                pipe_frames.popleft()

            checker = True
            for pf in pipe_frames:
                if pf[0].left <= bird_frame.x <= pf[0].right:
                    checker = False
                    if not didUpdateScore:
                        score += 1
                        didUpdateScore = True
                        pipe_pass_sound.play()
                        score_display.pulse()
                        gap_center_x = pf[0].centerx
                        gap_center_y = (pf[0].bottom + pf[1].top) // 2
                        particles.emit_pipe_pass((gap_center_x, gap_center_y), bg.accent_color)
            if checker: didUpdateScore = False

            score_display.set(score)
            if not new_best_announced and score > current_high_score:
                new_best_announced = True
                particles.emit_confetti((window_size[0] // 2, window_size[1] * 0.16))

            shake_offset = shake.offset()
            bg.draw_back(screen, shake_offset)

            shadow_offset = (int(window_size[1] * 0.012), int(window_size[1] * 0.014))
            for pf in pipe_frames:
                screen.blit(pipe_shadow, pf[1].move(shadow_offset))
                screen.blit(pipe_shadow, pf[0].move(shadow_offset))
                screen.blit(pipe_highlight, (pf[1].x + 4, pf[1].y))
                screen.blit(pipe_highlight, (pf[0].x + 4, pf[0].y))
                screen.blit(pipe_img, pf[1])
                screen.blit(pipe_img_top, pf[0])

            screen.blit(rotated_bird, rotated_bird.get_rect(center=bird_frame.center))

            bg.draw_front(screen, shake_offset)
            particles.draw(screen, shake_offset)
            bg.draw_atmosphere(screen)

            score_display.draw(screen, (window_size[0] // 2, int(window_size[1] * 0.08)))
            hud.draw(screen, username, stage, max(current_high_score, score), new_best_announced and score > 0)
            if banner:
                banner.draw(screen, bg.accent_color)
            if grace_timer > 0:
                bob = math.sin(pygame.time.get_ticks() / 300.0) * 5
                ready_text.set_alpha(int(255 * min(1.0, grace_timer / 0.6)))
                ready_pos = (window_size[0] // 2, int(window_size[1] * 0.3) + int(bob))
                screen.blit(ready_text, ready_text.get_rect(center=ready_pos))
            fade.draw(screen)

            pygame.display.flip()

            hit_ground = bird_frame.bottom >= bg.ground_top
            if hit_ground:
                bird_frame.bottom = int(bg.ground_top)
            if hit_ground or any([bird_frame.colliderect(pf[0]) or bird_frame.colliderect(pf[1]) for pf in pipe_frames]):
                game_is_running = False
                die_timer = 0.9
                shake.add(0.95)
                particles.emit_collision(bird_frame.center)
                fade.flash((255, 70, 50), 0.28)

def check_highscore_beaten(score):
    high_scores = load_high_scores()
    if not high_scores:
        return True
    return score > high_scores[0]["score"]

def show_new_highscore_animation(score):
    font = get_font(48)
    bg = get_background(window_size)
    particles = ParticleSystem()
    clock = pygame.time.Clock()
    duration = 1.4
    elapsed = 0.0
    base_pos = [window_size[0] // 2, window_size[1] // 3]
    burst_timer = 0.0

    while elapsed < duration:
        dt = min(MAX_DELTA_TIME, clock.tick(DISPLAY_FPS_CAP) / 1000.0)
        for event in pygame.event.get():
            if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                VID_CAP.release()
                cv.destroyAllWindows()
                pygame.quit()
                sys.exit()
        elapsed += dt
        burst_timer -= dt
        if burst_timer <= 0:
            burst_timer = 0.35
            particles.emit_confetti((random.uniform(window_size[0] * 0.25, window_size[0] * 0.75),
                                     random.uniform(window_size[1] * 0.15, window_size[1] * 0.45)))
        particles.update(dt)

        alpha_cycle = abs(255 - ((elapsed * 380) % 510))
        position = [base_pos[0], base_pos[1] + math.sin(elapsed * 2.2) * 10]

        text_surface = font.render("NEW HIGH SCORE!", True, (255, 255, 0))
        glow = font.render("NEW HIGH SCORE!", True, (120, 90, 0))
        glow.set_alpha(alpha_cycle // 2)
        screen.blit(glow, glow.get_rect(center=(int(position[0]) + 4, int(position[1]) + 4)))
        text_surface.set_alpha(alpha_cycle)
        screen.blit(text_surface, text_surface.get_rect(center=(int(position[0]), int(position[1]))))
        particles.draw(screen)
        pygame.display.flip()

def show_game_over(username, score):
    bg_music.stop()
    game_over_sound.play()

    dark = pygame.Surface(window_size, pygame.SRCALPHA)
    fade_t = 0.0
    clock = pygame.time.Clock()
    while fade_t < 0.6:
        dt = min(MAX_DELTA_TIME, clock.tick(DISPLAY_FPS_CAP) / 1000.0)
        for event in pygame.event.get():
            if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                VID_CAP.release()
                cv.destroyAllWindows()
                pygame.quit()
                sys.exit()
        fade_t += dt
        dark.fill((6, 8, 14, int(210 * min(1.0, fade_t / 0.6))))
        screen.blit(dark, (0, 0))
        pygame.display.flip()

    pygame.time.wait(1000)

    ret, frame = VID_CAP.read()
    if ret:
        Path("react").mkdir(parents=True, exist_ok=True)
        reaction_image_path = f"react/{username}_reaction.png"
        cv.imwrite(reaction_image_path, frame)
        print(f"Reaction image saved as {reaction_image_path}")
    else:
        print("Error capturing reaction image")
    save_high_score(username, score)
    font_large = pygame.font.Font("assets/fonts/Helvetica Bold.ttf", int(window_size[1]/8)) \
        if Path("assets/fonts/Helvetica Bold.ttf").exists() else pygame.font.SysFont("arial", int(window_size[1]/8), bold=True)
    font_medium = pygame.font.SysFont("Helvetica Bold.ttf", int(window_size[1]/12))

    photo = None
    if ret and Path(f"react/{username}_reaction.png").exists():
        photo = pygame.image.load(f"react/{username}_reaction.png").convert()
        photo = pygame.transform.scale(photo, window_size)

    panel_h = int(window_size[1] * 0.34)
    gradient_panel = pygame.Surface((window_size[0], panel_h), pygame.SRCALPHA)
    for y in range(panel_h):
        a = int(190 * (y / panel_h) ** 1.3)
        pygame.draw.line(gradient_panel, (10, 12, 22, a), (0, y), (window_size[0], y))

    reveal = 0.0
    while reveal < 1.0:
        dt = min(MAX_DELTA_TIME, clock.tick(DISPLAY_FPS_CAP) / 1000.0)
        for event in pygame.event.get():
            if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                VID_CAP.release()
                cv.destroyAllWindows()
                pygame.quit()
                sys.exit()
        reveal = min(1.0, reveal + dt / 0.7)
        eased = 1 - (1 - reveal) ** 3
        if photo:
            screen.blit(photo, (0, 0))
            dim = pygame.Surface(window_size, pygame.SRCALPHA)
            dim.fill((0, 0, 0, int(90 * (1 - eased))))
            screen.blit(dim, (0, 0))
        screen.blit(gradient_panel, (0, window_size[1] - panel_h))

        go_alpha = int(255 * eased)
        game_over_text = font_large.render('Game Over!', True, WHITE)
        game_over_text.set_alpha(go_alpha)
        tr = game_over_text.get_rect(center=(window_size[0]//2, window_size[1]//2 - int((1 - eased) * 40)))
        outline = font_large.render('Game Over!', True, (0, 0, 0))
        outline.set_alpha(go_alpha)
        for dx, dy in ((-3, 0), (3, 0), (0, -3), (0, 3)):
            screen.blit(outline, tr.move(dx, dy))
        screen.blit(game_over_text, tr)

        score_text = font_medium.render(f'Final Score: {score}', True, GOLD)
        score_text.set_alpha(int(255 * max(0.0, eased * 1.4 - 0.4)))
        sr = score_text.get_rect(center=(window_size[0]//2, window_size[1]//2 + int(window_size[1]*0.09)))
        screen.blit(score_text, sr)
        pygame.display.flip()

    pygame.time.wait(2000)

def main():
    while True:
        username = show_start_screen()
        show_countdown()
        final_score = game_loop(username)
        show_game_over(username, final_score)
        if check_highscore_beaten(final_score):
            show_new_highscore_animation(final_score)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        VID_CAP.release()
        cv.destroyAllWindows()
        pygame.quit()
        sys.exit()
