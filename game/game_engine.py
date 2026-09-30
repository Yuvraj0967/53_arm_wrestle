import math
import random
import pygame


class GameEngine:

    PRESS_COST = 4.0
    STAMINA_REGEN = 0.1
    EXHAUST_THRESHOLD = 10.0
    EXHAUST_RECOVER = 30.0

    AI_BUILD_TIME = (4.0, 6.0)
    AI_SURGE_TIME = (1.0, 2.0)
    AI_EXHAUST_TIME = (2.0, 3.0)
    AI_SURGE_MULT = 2.0
    AI_NORMAL_MULT = 1.0
    AI_TIRED_MULT = 0.3

    def __init__(self, width, height):
        self.width = width
        self.height = height

        self.arm_position = 0.0
        self.target_limit = 100.0
        self.last_key = None

        self.stamina = 100.0
        self.max_stamina = 100.0
        self.exhausted = False

        self.winner = None
        self.game_state = "PLAYING"
        self.ai_strength = 0.35

        self._reset_ai()

        self.font_big = pygame.font.SysFont(None, 44)
        self.font_med = pygame.font.SysFont(None, 26)
        self.font_small = pygame.font.SysFont(None, 22)

    def _reset_ai(self):
        self.ai_state = "BUILDING"
        self.ai_state_duration = random.uniform(*self.AI_BUILD_TIME)
        self.ai_state_elapsed = 0.0
        self.last_tick = pygame.time.get_ticks()

    def handle_event(self, event):
        if self.game_state != "PLAYING":
            if event.type == pygame.KEYDOWN and event.key == pygame.K_r:
                self.reset()
            return

        if event.type == pygame.KEYDOWN:
            if self.exhausted or self.stamina <= self.EXHAUST_THRESHOLD:
                return

            if event.key == pygame.K_LEFT:
                if self.last_key != pygame.K_LEFT:
                    self.arm_position -= 4.2
                    self.stamina = max(0.0, self.stamina - self.PRESS_COST)
                    self.last_key = pygame.K_LEFT
            elif event.key == pygame.K_RIGHT:
                if self.last_key != pygame.K_RIGHT:
                    self.arm_position -= 4.2
                    self.stamina = max(0.0, self.stamina - self.PRESS_COST)
                    self.last_key = pygame.K_RIGHT

    def _update_ai_state(self, dt):
        self.ai_state_elapsed += dt
        if self.ai_state_elapsed < self.ai_state_duration:
            return
        self.ai_state_elapsed = 0.0
        if self.ai_state == "BUILDING":
            self.ai_state = "SURGE"
            self.ai_state_duration = random.uniform(*self.AI_SURGE_TIME)
        elif self.ai_state == "SURGE":
            self.ai_state = "EXHAUSTED"
            self.ai_state_duration = random.uniform(*self.AI_EXHAUST_TIME)
        else:
            self.ai_state = "BUILDING"
            self.ai_state_duration = random.uniform(*self.AI_BUILD_TIME)

    def _ai_multiplier(self):
        if self.ai_state == "SURGE":
            return self.AI_SURGE_MULT
        if self.ai_state == "EXHAUSTED":
            return self.AI_TIRED_MULT
        return self.AI_NORMAL_MULT

    def update(self):
        now = pygame.time.get_ticks()
        dt = min((now - self.last_tick) / 1000.0, 0.05)
        self.last_tick = now

        if self.game_state != "PLAYING":
            return

        self._update_ai_state(dt)
        ai_variance = random.uniform(0.3, 1.0)
        self.arm_position += self.ai_strength * ai_variance * self._ai_multiplier() * (dt * 60)

        if self.stamina < self.max_stamina:
            self.stamina = min(self.max_stamina, self.stamina + self.STAMINA_REGEN)

        if not self.exhausted and self.stamina <= self.EXHAUST_THRESHOLD:
            self.exhausted = True
        elif self.exhausted and self.stamina >= self.EXHAUST_RECOVER:
            self.exhausted = False

        if self.arm_position <= -self.target_limit:
            self.winner = "PLAYER"
            self.game_state = "GAME_OVER"
        elif self.arm_position >= self.target_limit:
            self.winner = "COMPUTER"
            self.game_state = "GAME_OVER"

    def reset(self):
        self.arm_position = 0.0
        self.stamina = 100.0
        self.exhausted = False
        self.last_key = None
        self.winner = None
        self.game_state = "PLAYING"
        self._reset_ai()

    def render(self, screen):
        screen.fill((25, 28, 35))
        ticks = pygame.time.get_ticks()
        flash_on = (ticks // 150) % 2 == 0

        title_surf = self.font_big.render("ARM WRESTLE SHOWDOWN", True, (240, 240, 240))
        screen.blit(title_surf, (self.width // 2 - title_surf.get_width() // 2, 12))

        player_header = self.font_med.render("PLAYER", True, (80, 160, 255))
        computer_header = self.font_med.render("COMPUTER", True, (255, 100, 80))
        screen.blit(player_header, (60, 55))
        screen.blit(computer_header, (self.width - 150, 55))

        ai_labels = {
            "BUILDING": ("AI: building energy...", (230, 200, 90)),
            "SURGE": ("AI: POWER SURGE!", (255, 60, 60)),
            "EXHAUSTED": ("AI: exhausted", (120, 180, 255)),
        }
        ai_text, ai_color = ai_labels[self.ai_state]
        ai_surf = self.font_small.render(ai_text, True, ai_color)
        screen.blit(ai_surf, (self.width - 40 - ai_surf.get_width(), 78))

        table_rect = pygame.Rect(40, 100, self.width - 80, 310)
        pygame.draw.rect(screen, (110, 50, 15), table_rect, border_radius=14)
        pygame.draw.rect(screen, (70, 30, 8), table_rect, width=5, border_radius=14)

        pygame.draw.line(screen, (45, 18, 4), (self.width // 2, 100), (self.width // 2, 410), 4)

        offset_x = (self.arm_position / self.target_limit) * 95
        hand_x = (self.width // 2) + int(offset_x)
        hand_y = 235

        p_shoulder = (70, 330)
        p_elbow = (140, 215)
        c_shoulder = (self.width - 70, 330)
        c_elbow = (self.width - 140, 215)

        if self.exhausted and self.game_state == "PLAYING":
            p_shoulder = (p_shoulder[0] + random.randint(-3, 3), p_shoulder[1] + random.randint(-3, 3))
            p_elbow = (p_elbow[0] + random.randint(-4, 4), p_elbow[1] + random.randint(-4, 4))

        pygame.draw.line(screen, (200, 145, 110), p_shoulder, p_elbow, 32)
        pygame.draw.line(screen, (215, 160, 125), p_elbow, (hand_x, hand_y), 26)
        pygame.draw.circle(screen, (185, 130, 95), p_elbow, 18)

        pygame.draw.line(screen, (170, 110, 85), c_shoulder, c_elbow, 32)
        pygame.draw.line(screen, (185, 125, 95), c_elbow, (hand_x, hand_y), 26)
        pygame.draw.circle(screen, (150, 95, 70), c_elbow, 18)

        pygame.draw.circle(screen, (225, 175, 140), (hand_x, hand_y), 24)
        pygame.draw.circle(screen, (160, 115, 85), (hand_x, hand_y), 24, width=3)

        stamina_label = self.font_med.render("STAMINA", True, (220, 220, 220))
        screen.blit(stamina_label, (40, 445))

        stamina_bg = pygame.Rect(140, 448, 240, 22)
        stamina_fill = pygame.Rect(140, 448, int(240 * (self.stamina / self.max_stamina)), 22)
        pygame.draw.rect(screen, (45, 50, 60), stamina_bg, border_radius=6)

        if self.exhausted:
            bar_color = (255, 40, 40) if flash_on else (120, 20, 20)
            pygame.draw.rect(screen, bar_color, stamina_fill, border_radius=6)
            pygame.draw.rect(screen, (255, 60, 60), stamina_bg, width=2, border_radius=6)
            if flash_on:
                warn = self.font_med.render("EXHAUSTED!", True, (255, 70, 70))
                screen.blit(warn, (400, 447))
        else:
            bar_color = (60, 210, 100) if self.stamina > 25 else (220, 60, 60)
            pygame.draw.rect(screen, bar_color, stamina_fill, border_radius=6)

        if self.game_state == "GAME_OVER":
            overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 200))
            screen.blit(overlay, (0, 0))

            win_text = "PLAYER WINS THE MATCH!" if self.winner == "PLAYER" else "COMPUTER WINS!"
            color = (80, 240, 100) if self.winner == "PLAYER" else (240, 80, 80)
            text_surf = self.font_big.render(win_text, True, color)
            screen.blit(
                text_surf,
                (self.width // 2 - text_surf.get_width() // 2, self.height // 2 - 45)
            )

            restart_surf = self.font_med.render(
                "Press [R] to Rematch", True, (240, 240, 240)
            )
            screen.blit(
                restart_surf,
                (self.width // 2 - restart_surf.get_width() // 2, self.height // 2 + 10)
            )
