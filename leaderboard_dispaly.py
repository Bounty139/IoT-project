"""Live remote leaderboard display for the second Raspberry Pi."""

import argparse
import json
import threading
import time
from http.client import HTTPException
from urllib.error import URLError
from urllib.request import Request, urlopen

import pygame


WIDTH, HEIGHT = 900, 650
BACKGROUND = (7, 10, 12)
PANEL = (13, 20, 23)
WHITE = (235, 245, 245)
GREEN = (40, 255, 105)
PINK = (255, 55, 180)
CYAN = (50, 225, 255)
GREY = (145, 155, 160)
ORANGE = (255, 160, 55)
DIFFICULTIES = ("Easy", "Normal", "Hard", "Extreme")


class LeaderboardPoller:
    def __init__(self, url):
        self.url = url
        self.lock = threading.Lock()
        self.scores = {difficulty: [] for difficulty in DIFFICULTIES}
        self.error = "Connecting to game..."
        self.last_updated = None
        self.thread = threading.Thread(target=self._poll, daemon=True)

    def start(self):
        self.thread.start()

    def snapshot(self):
        with self.lock:
            return self.scores, self.error, self.last_updated

    def _poll(self):
        while True:
            try:
                request = Request(self.url, headers={"Accept": "application/json"})
                with urlopen(request, timeout=3) as response:
                    payload = json.loads(response.read().decode("utf-8"))

                raw_scores = payload.get("scores")
                if not isinstance(raw_scores, dict):
                    raise ValueError("Host returned invalid leaderboard data")

                scores = {}
                for difficulty in DIFFICULTIES:
                    entries = raw_scores.get(difficulty, [])
                    if not isinstance(entries, list):
                        raise ValueError(f"Invalid scores for {difficulty}")
                    scores[difficulty] = [
                        {"name": entry["name"], "waves": entry["waves"]}
                        for entry in entries[:10]
                        if isinstance(entry, dict)
                        and isinstance(entry.get("name"), str)
                        and type(entry.get("waves")) is int
                        and entry["waves"] >= 0
                    ]

                with self.lock:
                    self.scores = scores
                    self.error = ""
                    self.last_updated = time.strftime("%H:%M:%S")
            except (OSError, URLError, ValueError, HTTPException) as error:
                with self.lock:
                    self.error = str(error) or "Could not read leaderboard"

            time.sleep(2)


def draw_text(surface, font, text, color, position, center=False):
    image = font.render(str(text), True, color)
    rect = image.get_rect()
    if center:
        rect.center = position
    else:
        rect.topleft = position
    surface.blit(image, rect)


def run_display(host, port):
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
    pygame.display.set_caption("Cyber Defender - Remote Leaderboard")
    clock = pygame.time.Clock()
    title_font = pygame.font.SysFont("consolas", 42, bold=True)
    font = pygame.font.SysFont("consolas", 24)
    small_font = pygame.font.SysFont("consolas", 17)
    selected = 0
    poller = LeaderboardPoller(
        f"http://{host}:{port}/api/leaderboard"
    )
    poller.start()

    running = True
    while running:
        screen.fill(BACKGROUND)
        width, height = screen.get_size()
        center_x = width // 2
        scores_by_difficulty, error, last_updated = poller.snapshot()

        draw_text(screen, title_font, "CYBER DEFENDER", PINK,
                  (center_x, 58), center=True)
        draw_text(screen, small_font, "REMOTE LEADERBOARD", GREEN,
                  (center_x, 105), center=True)

        tab_width = min(170, max(120, (width - 100) // 4))
        total_tabs_width = tab_width * len(DIFFICULTIES)
        tab_start = center_x - total_tabs_width // 2
        for index, difficulty in enumerate(DIFFICULTIES):
            rect = pygame.Rect(
                tab_start + index * tab_width,
                145,
                tab_width - 8,
                48
            )
            color = GREEN if index == selected else CYAN
            pygame.draw.rect(screen, PANEL, rect, border_radius=6)
            pygame.draw.rect(screen, color, rect, 2, border_radius=6)
            draw_text(screen, small_font, difficulty.upper(), color,
                      rect.center, center=True)

        panel_height = max(100, min(340, height - 290))
        panel = pygame.Rect(60, 220, max(100, width - 120), panel_height)
        pygame.draw.rect(screen, PANEL, panel, border_radius=8)
        pygame.draw.rect(screen, PINK, panel, 2, border_radius=8)

        scores = scores_by_difficulty[DIFFICULTIES[selected]]
        if not scores:
            draw_text(screen, font, "No scores recorded yet.", GREY,
                      (center_x, panel.y + 75), center=True)
        else:
            line_height = min(30, max(22, (panel.height - 70) // 10))
            for position, score in enumerate(scores, start=1):
                row_y = panel.y + 22 + (position - 1) * line_height
                draw_text(
                    screen,
                    small_font,
                    f'{position:>2}.  {score["name"]} - {score["waves"]} waves',
                    WHITE,
                    (panel.x + 35, row_y)
                )

        status_color = GREEN if not error else ORANGE
        status = f"Connected - updated {last_updated}" if not error else error
        draw_text(screen, small_font, status, status_color,
                  (center_x, height - 42), center=True)
        draw_text(screen, small_font, "Use left/right arrows to change difficulty. ESC to exit.",
                  GREY, (center_x, height - 18), center=True)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key in (pygame.K_LEFT, pygame.K_a):
                    selected = (selected - 1) % len(DIFFICULTIES)
                elif event.key in (pygame.K_RIGHT, pygame.K_d):
                    selected = (selected + 1) % len(DIFFICULTIES)
                elif pygame.K_1 <= event.key <= pygame.K_4:
                    selected = event.key - pygame.K_1
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                for index in range(len(DIFFICULTIES)):
                    rect = pygame.Rect(
                        tab_start + index * tab_width,
                        145,
                        tab_width - 8,
                        48
                    )
                    if rect.collidepoint(event.pos):
                        selected = index

        pygame.display.flip()
        clock.tick(30)

    pygame.quit()


def main():
    parser = argparse.ArgumentParser(
        description="Display the live leaderboard from the game Raspberry Pi."
    )
    parser.add_argument("host", help="LAN IPv4 address of the game Raspberry Pi")
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()
    run_display(args.host, args.port)


if __name__ == "__main__":
    main()
