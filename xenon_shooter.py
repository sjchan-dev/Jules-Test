"""Xenon 2-style scrolling shooter controlled by webcam gestures.

Controls:
  - Move ship: tilt/shift your face horizontally.
  - Rapid fire: open your mouth wider.
  - Fragment bomb: open a hand; bomb spawns at that hand location.

Dependencies:
  pip install pygame opencv-python mediapipe numpy
"""

from __future__ import annotations

import math
import random
import time
from dataclasses import dataclass
from typing import Optional, Tuple

import cv2
import mediapipe as mp
import numpy as np
import pygame


WIDTH, HEIGHT = 960, 540
FPS = 60
SCROLL_SPEED = 120

SHIP_SPEED = 520
SHIP_Y = HEIGHT - 80
SHIP_SIZE = (50, 30)

BULLET_SPEED = 560
BULLET_COOLDOWN = 0.18
RAPID_FIRE_COOLDOWN = 0.06

ENEMY_SPAWN_TIME = 0.7
ENEMY_SPEED_MIN = 90
ENEMY_SPEED_MAX = 200

BOMB_RADIUS = 140
BOMB_COOLDOWN = 2.5


@dataclass
class Bullet:
    x: float
    y: float

    def update(self, dt: float) -> None:
        self.y -= BULLET_SPEED * dt


@dataclass
class Enemy:
    x: float
    y: float
    speed: float
    size: int

    def update(self, dt: float) -> None:
        self.y += self.speed * dt


@dataclass
class Fragment:
    x: float
    y: float
    vx: float
    vy: float
    life: float

    def update(self, dt: float) -> None:
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.life -= dt


class GestureTracker:
    def __init__(self) -> None:
        self._face_mesh = mp.solutions.face_mesh.FaceMesh(
            static_image_mode=False,
            max_num_faces=1,
            refine_landmarks=True,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5,
        )
        self._hands = mp.solutions.hands.Hands(
            static_image_mode=False,
            max_num_hands=2,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5,
        )

    def process(self, frame: np.ndarray) -> Tuple[Optional[float], float, list[Tuple[float, float]]]:
        """Return (face_x, mouth_open_ratio, open_hand_positions)."""
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        face_results = self._face_mesh.process(rgb)
        hands_results = self._hands.process(rgb)

        face_x = None
        mouth_open_ratio = 0.0

        if face_results.multi_face_landmarks:
            landmarks = face_results.multi_face_landmarks[0].landmark
            nose = landmarks[1]
            face_x = nose.x

            upper_lip = landmarks[13]
            lower_lip = landmarks[14]
            mouth_open = abs(lower_lip.y - upper_lip.y)
            left_eye = landmarks[33]
            right_eye = landmarks[263]
            face_width = abs(right_eye.x - left_eye.x)
            if face_width > 0:
                mouth_open_ratio = mouth_open / face_width

        open_hands: list[Tuple[float, float]] = []
        if hands_results.multi_hand_landmarks:
            for hand_landmarks in hands_results.multi_hand_landmarks:
                if self._is_open_hand(hand_landmarks):
                    wrist = hand_landmarks.landmark[0]
                    open_hands.append((wrist.x, wrist.y))

        return face_x, mouth_open_ratio, open_hands

    @staticmethod
    def _is_open_hand(hand_landmarks: mp.solutions.hands.HandLandmark) -> bool:
        tips = [4, 8, 12, 16, 20]
        wrist = hand_landmarks.landmark[0]
        extended = 0
        for tip_index in tips:
            tip = hand_landmarks.landmark[tip_index]
            if tip.y < wrist.y - 0.05:
                extended += 1
        return extended >= 3


def draw_starfield(surface: pygame.Surface, stars: list[Tuple[float, float]], dt: float) -> None:
    surface.fill((5, 5, 20))
    for i, (x, y) in enumerate(stars):
        y += SCROLL_SPEED * dt
        if y > HEIGHT:
            y = 0
            x = random.random() * WIDTH
        stars[i] = (x, y)
        pygame.draw.circle(surface, (200, 200, 255), (int(x), int(y)), 1)


def main() -> None:
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Xenon 2 Gesture Shooter")
    clock = pygame.time.Clock()

    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    tracker = GestureTracker()

    ship_x = WIDTH / 2
    bullets: list[Bullet] = []
    enemies: list[Enemy] = []
    fragments: list[Fragment] = []

    last_fire = 0.0
    last_spawn = 0.0
    last_bomb = 0.0
    stars = [(random.random() * WIDTH, random.random() * HEIGHT) for _ in range(140)]
    score = 0
    running = True

    while running:
        dt = clock.tick(FPS) / 1000
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        ret, frame = cap.read()
        if ret:
            frame = cv2.flip(frame, 1)
            face_x, mouth_open_ratio, open_hands = tracker.process(frame)
            if face_x is not None:
                target_x = face_x * WIDTH
                ship_x += (target_x - ship_x) * min(1.0, dt * 6)

            now = time.time()
            cooldown = RAPID_FIRE_COOLDOWN if mouth_open_ratio > 0.55 else BULLET_COOLDOWN
            if now - last_fire > cooldown:
                bullets.append(Bullet(ship_x, SHIP_Y))
                last_fire = now

            if open_hands and now - last_bomb > BOMB_COOLDOWN:
                hand_x, hand_y = open_hands[0]
                bomb_x = hand_x * WIDTH
                bomb_y = hand_y * HEIGHT
                for _ in range(28):
                    angle = random.random() * math.tau
                    speed = random.uniform(220, 420)
                    fragments.append(
                        Fragment(
                            bomb_x,
                            bomb_y,
                            math.cos(angle) * speed,
                            math.sin(angle) * speed,
                            0.8,
                        )
                    )
                last_bomb = now

        now = time.time()
        if now - last_spawn > ENEMY_SPAWN_TIME:
            enemies.append(
                Enemy(
                    random.randint(20, WIDTH - 20),
                    -30,
                    random.uniform(ENEMY_SPEED_MIN, ENEMY_SPEED_MAX),
                    random.randint(16, 28),
                )
            )
            last_spawn = now

        bullets = [b for b in bullets if b.y > -40]
        for bullet in bullets:
            bullet.update(dt)

        enemies = [e for e in enemies if e.y < HEIGHT + 60]
        for enemy in enemies:
            enemy.update(dt)

        fragments = [f for f in fragments if f.life > 0]
        for fragment in fragments:
            fragment.update(dt)

        for bullet in bullets[:]:
            for enemy in enemies[:]:
                if abs(bullet.x - enemy.x) < enemy.size and abs(bullet.y - enemy.y) < enemy.size:
                    bullets.remove(bullet)
                    enemies.remove(enemy)
                    score += 10
                    break

        for fragment in fragments[:]:
            for enemy in enemies[:]:
                if (fragment.x - enemy.x) ** 2 + (fragment.y - enemy.y) ** 2 < (enemy.size + 6) ** 2:
                    enemies.remove(enemy)
                    score += 8

        draw_starfield(screen, stars, dt)

        for bullet in bullets:
            pygame.draw.rect(screen, (255, 220, 120), (bullet.x - 2, bullet.y - 8, 4, 10))

        for enemy in enemies:
            pygame.draw.circle(screen, (200, 60, 70), (int(enemy.x), int(enemy.y)), enemy.size)
            pygame.draw.circle(screen, (255, 140, 150), (int(enemy.x) - 5, int(enemy.y) - 3), 4)

        for fragment in fragments:
            pygame.draw.circle(screen, (120, 200, 255), (int(fragment.x), int(fragment.y)), 3)

        pygame.draw.polygon(
            screen,
            (80, 200, 255),
            [
                (ship_x, SHIP_Y - SHIP_SIZE[1] / 2),
                (ship_x - SHIP_SIZE[0] / 2, SHIP_Y + SHIP_SIZE[1] / 2),
                (ship_x + SHIP_SIZE[0] / 2, SHIP_Y + SHIP_SIZE[1] / 2),
            ],
        )

        font = pygame.font.Font(None, 28)
        score_text = font.render(f"Score: {score}", True, (240, 240, 240))
        screen.blit(score_text, (16, 12))

        pygame.display.flip()

    cap.release()
    pygame.quit()


if __name__ == "__main__":
    main()
