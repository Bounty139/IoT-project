# IoT-project


import pygame
import sys
import random

# CYBER DEFENDER - RASPBERRY PI ARCADE GUI
# Version 0.1 - Graphical interface prototype

pygame.init()
pygame.display.set_caption("Cyber Defender")
screen = pygame.display.set_mode((1100, 700), pygame.RESIZABLE)
clock = pygame.time.Clock()

BLACK = (5, 8, 9)
PANEL = (8, 10, 12)
WHITE = (245, 250, 245)
GREEN = (90, 255, 65)
DARK_GREEN = (15, 75, 25)
PINK = (255, 70, 220)
CYAN = (70, 230, 255)
GREY = (150, 160, 160)
ORANGE = (255, 170, 55)

FONT = pygame.font.SysFont("dejavusans", 22, bold=True)
SMALL = pygame.font.SysFont("dejavusans", 16)
TITLE = pygame.font.SysFont("dejavusans", 48, bold=True)
SUBTITLE = pygame.font.SysFont("dejavusans", 28, bold=True)

screen_name = "menu"
difficulty = "Normal"
leaderboard_difficulty = 0
notice = ""
notice_timer = 0
hitboxes = {}

DIFFICULTIES = ["Easy", "Normal", "Hard", "Extreme"]

# Temporary leaderboard.
# Persistent storage will be connected later.
scores = {name: [] for name in DIFFICULTIES}


def draw_text(surface, text, font, colour, centre):
    image = font.render(str(text), True, colour)
    surface.blit(image, image.get_rect(center=centre))


def draw_circuit_background(surface):
    w, h = surface.get_size()
    surface.fill((2, 18, 7))

    random.seed(12)

    for _ in range(32):
        x = random.randint(0, max(1, w))
        y = random.randint(0, max(1, h))
        length = random.randint(55, 180)

        if random.choice([True, False]):
            pygame.draw.line(
                surface, DARK_GREEN,
                (x, y), (min(w, x + length), y), 5
            )

            for bx in range(x, min(w, x + length), 22):
                pygame.draw.line(
                    surface, GREEN,
                    (bx, y - 5), (bx + 12, y - 5), 2
                )
                pygame.draw.line(
                    surface, GREEN,
                    (bx, y + 5), (bx + 12, y + 5), 2
                )
        else:
            pygame.draw.line(
                surface, DARK_GREEN,
                (x, y), (x, min(h, y + length)), 5
            )

            for by in range(y, min(h, y + length), 22):
                pygame.draw.line(
                    surface, GREEN,
                    (x - 5, by), (x - 5, by + 12), 2
                )
                pygame.draw.line(
                    surface, GREEN,
                    (x + 5, by), (x + 5, by + 12), 2
                )

    random.seed()


def draw_panel(surface, rect, fill=PANEL,
               border=WHITE, width=3):
    pygame.draw.rect(
        surface, fill, rect, border_radius=8
    )
    pygame.draw.rect(
        surface, border, rect, width, border_radius=8
    )


def add_button(surface, key, label, rect,
               colour=GREEN, fill=(12, 24, 16)):

    rect = pygame.Rect(rect)
    mouse_over = rect.collidepoint(pygame.mouse.get_pos())

    border = PINK if mouse_over else colour

    pygame.draw.rect(
        surface, fill, rect, border_radius=8
    )
    pygame.draw.rect(
        surface, border, rect, 3, border_radius=8
    )

    draw_text(surface, label, FONT, WHITE, rect.center)
    hitboxes[key] = rect


def show_notice(message):
    global notice, notice_timer
    notice = message
    notice_timer = 180


def draw_header(surface, title):
    w, h = surface.get_size()

    rect = pygame.Rect(
        w * 0.12, 22, w * 0.76, 82
    )

    draw_panel(surface, rect, BLACK, WHITE, 4)
    draw_text(surface, title, TITLE, PINK, rect.center)

    draw_text(
        surface, "ESC  -  MAIN MENU",
        SMALL, WHITE, (105, 28)
    )


def draw_menu(surface):
    w, h = surface.get_size()

    draw_header(surface, "CYBER DEFENDER")

    draw_text(
        surface, "ARCADE EDITION",
        SUBTITLE, CYAN, (w // 2, 145)
    )

    labels = [
        ("start", "START GAME"),
        ("leaderboard", "LEADERBOARD"),
        ("how", "HOW TO PLAY"),
        ("exit", "EXIT")
    ]

    bw = min(430, w * 0.55)
    bh = 62
    start_y = 220

    for i, (key, label) in enumerate(labels):
        add_button(
            surface, key, label,
            (w // 2 - bw // 2, start_y + i * 82, bw, bh)
        )


def draw_difficulty(surface):
    w, h = surface.get_size()

    draw_header(surface, "SELECT DIFFICULTY")

    draw_text(
        surface,
        "Choose how challenging the network attack will be.",
        FONT, WHITE, (w // 2, 160)
    )

    for i, name in enumerate(DIFFICULTIES):
        add_button(
            surface, "diff_" + name, name.upper(),
            (w // 2 - 190, 215 + i * 78, 380, 58),
            ORANGE if name == "Extreme" else GREEN
        )

    add_button(
        surface, "back", "BACK",
        (35, h - 82, 150, 48), GREY
    )


def draw_leaderboard(surface):
    w, h = surface.get_size()

    draw_header(surface, "LEADERBOARD")

    name = DIFFICULTIES[leaderboard_difficulty]

    draw_panel(
        surface,
        pygame.Rect(w * .18, 125, w * .64, 55),
        WHITE, WHITE, 2
    )

    draw_text(
        surface, name.upper() + "  HI-SCORES",
        SUBTITLE, BLACK, (w // 2, 152)
    )

    add_button(
        surface, "lb_prev", "<",
        (w * .12, 128, 55, 48)
    )

    add_button(
        surface, "lb_next", ">",
        (w * .82, 128, 55, 48)
    )

    board = pygame.Rect(
        w * .18, 195, w * .64, h - 250
    )

    draw_panel(surface, board, BLACK, WHITE, 3)

    entries = scores[name][:10]

    if not entries:
        draw_text(
            surface, "NO SCORES RECORDED YET",
            FONT, GREY, board.center
        )
    else:
        row_h = min(42, (board.height - 20) // 10)

        for i, entry in enumerate(entries):
            y = board.y + 10 + i * row_h

            draw_text(
                surface, str(i + 1),
                FONT, CYAN,
                (board.x + 35, y + row_h // 2)
            )

            draw_text(
                surface, entry["name"][:18],
                FONT, WHITE,
                (board.x + board.width * .38,
                 y + row_h // 2)
            )

            draw_text(
                surface, str(entry["waves"]) + " WAVES",
                FONT, GREEN,
                (board.x + board.width * .76,
                 y + row_h // 2)
            )

            pygame.draw.line(
                surface, GREY,
                (board.x + 12, y + row_h),
                (board.right - 12, y + row_h), 1
            )

    add_button(
        surface, "back", "BACK",
        (35, h - 65, 150, 45), GREY
    )


def draw_how(surface):
    w, h = surface.get_size()

    draw_header(surface, "HOW TO PLAY")

    lines = [
        "Protect your devices and stop malware reaching the database.",
        "Use upgrades to improve protection and reduce infection.",
        "Watch the network: Router, Switch and Network are important.",
        "Recover a device when its infection reaches 100%.",
        "If the database reaches 100%, you may lose the game.",
        "Survive as many waves as possible."
    ]

    panel = pygame.Rect(
        w * .13, 145, w * .74, h - 245
    )

    draw_panel(surface, panel)

    for i, line in enumerate(lines):
        draw_text(
            surface, line, SMALL, WHITE,
            (w // 2, panel.y + 45 + i * 48)
        )

    add_button(
        surface, "back", "BACK",
        (35, h - 75, 150, 48), GREY
    )


def draw_game(surface):
    w, h = surface.get_size()

    draw_header(surface, "NETWORK COMMAND CENTRE")

    stats = [
        ("DIFFICULTY", difficulty),
        ("WAVE", "1"),
        ("FUNDING", "£200"),
        ("RECOVERIES", "4")
    ]

    gap = 12
    box_w = (w * .76 - gap * 3) / 4

    for i, (label, value) in enumerate(stats):
        x = w * .12 + i * (box_w + gap)

        rect = pygame.Rect(x, 120, box_w, 70)
        draw_panel(surface, rect)

        draw_text(
            surface, label, SMALL, CYAN,
            (rect.centerx, rect.y + 20)
        )

        draw_text(
            surface, value, FONT, WHITE,
            (rect.centerx, rect.y + 49)
        )

    left = pygame.Rect(
        w * .08, 210, w * .52, h - 300
    )

    right = pygame.Rect(
        w * .63, 210, w * .29, h - 300
    )

    draw_panel(surface, left)
    draw_panel(surface, right)

    draw_text(
        surface, "DEVICE STATUS",
        SUBTITLE, GREEN,
        (left.centerx, left.y + 28)
    )

    devices = [
        "PC", "Laptop", "Phone", "Printer",
        "Router", "Switch", "Network", "Database"
    ]

    for i, device in enumerate(devices):
        col = 0 if i < 4 else 1
        row = i if i < 4 else i - 4

        x = left.x + 18 + col * (left.width / 2)
        y = left.y + 65 + row * 58

        draw_text(
            surface, device, SMALL, WHITE,
            (x + 55, y + 10)
        )

        bar = pygame.Rect(
            x + 10, y + 25,
            left.width / 2 - 30, 14
        )

        pygame.draw.rect(
            surface, (45, 55, 48),
            bar, border_radius=5
        )

        pygame.draw.rect(
            surface, GREEN,
            (bar.x, bar.y, bar.width * .05, bar.height),
            border_radius=5
        )

        draw_text(
            surface, "5%", SMALL, WHITE,
            (bar.right + 22, bar.centery)
        )

    draw_text(
        surface, "ACTIONS",
        SUBTITLE, PINK,
        (right.centerx, right.y + 28)
    )

    actions = [
        ("upgrades", "UPGRADES"),
        ("recovery", "RECOVERY"),
        ("threats", "CURRENT THREATS"),
        ("attack", "START NEXT WAVE"),
        ("back", "MAIN MENU")
    ]

    for i, (key, label) in enumerate(actions):
        add_button(
            surface, key, label,
            (right.x + 18, right.y + 62 + i * 55,
             right.width - 36, 43),
            ORANGE if key == "attack" else GREEN
        )


def draw_placeholder(surface, title, message):
    w, h = surface.get_size()

    draw_header(surface, title)

    panel = pygame.Rect(
        w * .18, 180, w * .64, h - 280
    )

    draw_panel(surface, panel)

    draw_text(
        surface, message, FONT, WHITE, panel.center
    )

    add_button(
        surface, "back", "BACK",
        (35, h - 75, 150, 48), GREY
    )


# MAIN PROGRAM LOOP

running = True

while running:
    w, h = screen.get_size()
    hitboxes = {}

    draw_circuit_background(screen)

    if screen_name == "menu":
        draw_menu(screen)

    elif screen_name == "difficulty":
        draw_difficulty(screen)

    elif screen_name == "leaderboard":
        draw_leaderboard(screen)

    elif screen_name == "how":
        draw_how(screen)

    elif screen_name == "game":
        draw_game(screen)

    elif screen_name == "upgrades":
        draw_placeholder(
            screen, "UPGRADE BAY",
            "Upgrade shop will be connected to the game mechanics."
        )

    elif screen_name == "recovery":
        draw_placeholder(
            screen, "RECOVERY SYSTEM",
            "Recovery options will be connected to the game mechanics."
        )

    elif screen_name == "threats":
        draw_placeholder(
            screen, "CURRENT THREATS",
            "Live threat information will be connected to the game mechanics."
        )

    if notice_timer > 0:
        draw_panel(
            screen,
            pygame.Rect(w * .2, h - 52, w * .6, 38),
            BLACK, PINK, 2
        )

        draw_text(
            screen, notice, SMALL, WHITE,
            (w // 2, h - 33)
        )

        notice_timer -= 1

    pygame.display.flip()

    for event in pygame.event.get():

        if event.type == pygame.QUIT:
            running = False

        elif event.type == pygame.VIDEORESIZE:
            screen = pygame.display.set_mode(
                event.size, pygame.RESIZABLE
            )

        elif event.type == pygame.KEYDOWN:

            if event.key == pygame.K_ESCAPE:
                screen_name = "menu"

            elif event.key == pygame.K_F11:
                if screen.get_flags() & pygame.FULLSCREEN:
                    screen = pygame.display.set_mode(
                        (1100, 700), pygame.RESIZABLE
                    )
                else:
                    screen = pygame.display.set_mode(
                        (0, 0), pygame.FULLSCREEN
                    )

        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:

            clicked = None

            for key, rect in hitboxes.items():
                if rect.collidepoint(event.pos):
                    clicked = key
                    break

            if clicked == "start":
                screen_name = "difficulty"

            elif clicked == "leaderboard":
                screen_name = "leaderboard"

            elif clicked == "how":
                screen_name = "how"

            elif clicked == "exit":
                running = False

            elif clicked == "back":
                screen_name = "menu"

            elif clicked and clicked.startswith("diff_"):
                difficulty = clicked[5:]
                screen_name = "game"

                show_notice(
                    difficulty +
                    " difficulty selected. Gameplay integration is next."
                )

            elif clicked == "lb_prev":
                leaderboard_difficulty = (
                    leaderboard_difficulty - 1
                ) % len(DIFFICULTIES)

            elif clicked == "lb_next":
                leaderboard_difficulty = (
                    leaderboard_difficulty + 1
                ) % len(DIFFICULTIES)

            elif clicked == "upgrades":
                screen_name = "upgrades"

            elif clicked == "recovery":
                screen_name = "recovery"

            elif clicked == "threats":
                screen_name = "threats"

            elif clicked == "attack":
                show_notice(
                    "Wave controls will be connected to the real game next."
                )

pygame.quit()
sys.exit()
