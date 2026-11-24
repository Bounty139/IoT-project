import pygame
import sys
import random
import json
import os
import textwrap
from lan_leaderboard import PORT as LEADERBOARD_PORT
from lan_leaderboard import get_local_ip, start_server
from cyber_sounds import CyberSounds
 
pygame.mixer.pre_init(22050, -16, 1, 512)
pygame.init()
 
WIDTH, HEIGHT = 1100, 700
screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
pygame.display.set_caption("Cyber Defender")
clock = pygame.time.Clock()
 
# Colours
BLACK = (7, 10, 12)
PANEL = (13, 20, 23)
WHITE = (235, 245, 245)
GREEN = (40, 255, 105)
PINK = (255, 55, 180)
CYAN = (50, 225, 255)
GREY = (145, 155, 160)
ORANGE = (255, 160, 55)
 
# Fonts
FONT = pygame.font.SysFont("consolas", 24)
SMALL = pygame.font.SysFont("consolas", 19)
TITLE = pygame.font.SysFont("consolas", 54, bold=True)
SUBTITLE = pygame.font.SysFont("consolas", 28, bold=True)
 
# Game / menu state
screen_name = "menu"
difficulty = "Normal"
leaderboard_difficulty = "Normal"
 
notice = ""
notice_timer = 0
 
hitboxes = []
SOUND_ENABLED = True
arcade_audio = CyberSounds(enabled=SOUND_ENABLED)
hovered_button = None
fullscreen = False
 
DIFFICULTIES = ["Easy", "Normal", "Hard", "Extreme"]

DIFFICULTY_SETTINGS = {
    "Easy": {"funding": 200, "device_growth": 5, "infection_chance": 15, "infrastructure_growth": 7},
    "Normal": {"funding": 150, "device_growth": 7, "infection_chance": 20, "infrastructure_growth": 10},
    "Hard": {"funding": 100, "device_growth": 10, "infection_chance": 30, "infrastructure_growth": 15},
    "Extreme": {"funding": 50, "device_growth": 15, "infection_chance": 45, "infrastructure_growth": 25}
}

EMAILS = [
    {
        "fake": True,
        "sender": "Parcel Tracking",
        "subject": "Delivery status update",
        "body": "Your recent delivery requires a status review. Check the tracking details to confirm the delivery information."
    },
    {
        "fake": True,
        "sender": "Game Account Support",
        "subject": "Account activity notification",
        "body": "We noticed an account setting has recently changed. Please review your account activity."
    },
    {
        "fake": True,
        "sender": "Finance Department",
        "subject": "Updated payment record",
        "body": "A payment record has been updated. Please review the information for your department."
    },
    {
        "fake": True,
        "sender": "Staff Services",
        "subject": "Staff information update",
        "body": "A staff information review is taking place. Please check the latest details."
    },
    {
        "fake": True,
        "sender": "Software Updates",
        "subject": "New security update",
        "body": "A new update is available. Please check the details before proceeding."
    },
    {
        "fake": True,
        "sender": "IT Service Desk",
        "subject": "Storage limit notification",
        "body": "Your department storage allocation is nearly full. A review is required before the next maintenance cycle."
    },
    {
        "fake": False,
        "sender": "Library Services",
        "subject": "Your book return reminder",
        "body": "A book borrowed under your account is due soon. You can check the return date in your usual library account."
    },
    {
        "fake": False,
        "sender": "IT Support",
        "subject": "Planned network maintenance",
        "body": "Network maintenance is scheduled for this evening. Some services may briefly become unavailable."
    },
    {
        "fake": False,
        "sender": "Gaming Club",
        "subject": "Friday's session",
        "body": "Friday's gaming session will start at 3:30 PM in the usual room. Bring your controller if you have one."
    },
    {
        "fake": False,
        "sender": "Sports Centre",
        "subject": "Booking confirmation",
        "body": "Your sports centre booking has been confirmed. The details are available in your booking information."
    }
]
EMAIL_EVENT_CHANCE = 0.3
TROJAN_EVENT_CHANCE = 0.2
NEXT_WAVE_TROJAN_PRESSES = 10
NEXT_WAVE_PRESS_WINDOW_MS = 2000
next_wave_press_count = 0
next_wave_press_started = 0

LEADERBOARD_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "leaderboard.json")
game = None
selected_device = "PC"
game_over = False
player_name = ""
final_score = 0
score_entry_message = ""
MAX_PLAYER_NAME_LENGTH = 16
 
SCORES = {
    "Easy": [],
    "Normal": [],
    "Hard": [],
    "Extreme": []
}
 
# Static circuit decoration
CIRCUITS = [
    (random.randint(0, WIDTH),
     random.randint(0, HEIGHT),
     random.randint(35, 140))
    for _ in range(24)
]


def create_game(selected_difficulty):
    settings = DIFFICULTY_SETTINGS[selected_difficulty]
    return {
        "difficulty": selected_difficulty,
        "funding": settings["funding"],
        "wave": 1,
        "recoveries": 4,
        "game_over": False,
        "tutorial_protection_bought": False,
        "tutorial_complete": False,
        "devices": {
            "PC": {"infection": 5, "protection": 0, "antivirus": False, "password": False},
            "Laptop": {"infection": 0, "protection": 0, "antivirus": False, "password": False},
            "Phone": {"infection": 0, "protection": 0, "antivirus": False, "password": False},
            "Printer": {"infection": 0, "protection": 0, "antivirus": False, "password": False}
        },
        "infrastructure": {
            "Router": {"infection": 0, "protection": 0},
            "Switch": {"infection": 0, "protection": 0},
            "Network": {"infection": 0, "protection": 0}
        },
        "database": {"infection": 0, "level": 1, "protection": 0},
        "backup_available": False,
        "backup_used": False,
        "emergency_restart_used": False,
        "restart_protection": 0,
        "pending_email": None
    }


def change_infection(target, amount):
    target["infection"] = max(0, min(100, target["infection"] + amount))


def load_scores():
    if os.path.exists(LEADERBOARD_FILE):
        try:
            with open(LEADERBOARD_FILE, "r", encoding="utf-8") as file:
                saved = json.load(file)
            if not isinstance(saved, dict):
                show_notice("Saved leaderboard has an invalid format")
                return
            for name in DIFFICULTIES:
                scores = []
                saved_scores = saved.get(name, [])
                if not isinstance(saved_scores, list):
                    show_notice(f"Saved scores for {name} have an invalid format")
                    continue
                for entry in saved_scores:
                    if isinstance(entry, dict):
                        if isinstance(entry.get("name"), str) and isinstance(entry.get("waves"), int):
                            scores.append({"name": entry["name"], "waves": entry["waves"]})
                    elif isinstance(entry, str) and entry != "---" and ": " in entry:
                        player_name, waves_text = entry.rsplit(": ", 1)
                        if waves_text.isdigit():
                            scores.append({"name": player_name, "waves": int(waves_text)})
                SCORES[name] = sorted(scores, key=lambda score: score["waves"], reverse=True)[:10]
        except (OSError, json.JSONDecodeError):
            show_notice("Could not read the saved leaderboard")


def add_score(name, selected_difficulty, waves):
    if selected_difficulty not in SCORES:
        return

    scores = SCORES[selected_difficulty]
    scores.append({"name": name, "waves": waves})
    scores.sort(key=lambda entry: entry["waves"], reverse=True)
    del scores[10:]

    try:
        with open(LEADERBOARD_FILE, "w", encoding="utf-8") as file:
            json.dump(SCORES, file, indent=2)
        play_sound("leaderboard_entry")
    except OSError as error:
        show_notice(f"Could not save score: {error}")


def get_scores(selected_difficulty):
    return SCORES.get(selected_difficulty, [])


def get_all_scores():
    return SCORES


def malware_attack():
    settings = DIFFICULTY_SETTINGS[game["difficulty"]]
    assets = list(game["devices"].items())
    assets.extend(game["infrastructure"].items())
    assets.append(("Database", game["database"]))
    infection_before = {
        name: item["infection"] for name, item in assets
    }

    for name, device in game["devices"].items():
        if device["infection"] >= 100:
            continue

        if device["infection"] > 0:
            growth = settings["device_growth"]
            if device["antivirus"]:
                growth -= 3
            growth -= device["protection"] // 25
            if device["password"]:
                growth -= 1
            change_infection(device, max(1, growth))
        else:
            chance = settings["infection_chance"]
            chance -= device["protection"] // 10
            if device["password"]:
                chance -= 3
            if random.randint(1, 100) <= max(3, chance):
                device["infection"] = 5

    if all(device["infection"] >= 100 for device in game["devices"].values()):
        infrastructure = game["infrastructure"]
        router_growth = settings["infrastructure_growth"]
        if game["restart_protection"] > 0:
            router_growth = 3

        if infrastructure["Router"]["infection"] < 100:
            growth = router_growth - infrastructure["Router"]["protection"] // 25
            change_infection(infrastructure["Router"], max(1, growth))
        elif infrastructure["Switch"]["infection"] < 100:
            growth = router_growth - infrastructure["Switch"]["protection"] // 25
            change_infection(infrastructure["Switch"], max(1, growth))
        elif infrastructure["Network"]["infection"] < 100:
            growth = router_growth - infrastructure["Network"]["protection"] // 25
            change_infection(infrastructure["Network"], max(1, growth))
        else:
            growth = settings["infrastructure_growth"]
            growth -= game["database"]["protection"] // 20
            change_infection(game["database"], max(1, growth))

    if game["restart_protection"] > 0:
        game["restart_protection"] -= 1

    infection_after = {
        name: item["infection"] for name, item in assets
    }
    if infection_after["Database"] > infection_before["Database"]:
        play_sound("database_alarm")
    elif any(
        infection_before[name] < 75 <= infection_after[name]
        for name in infection_before
    ):
        play_sound("critical_alert")
    elif any(
        infection_before[name] == 0 and infection_after[name] > 0
        for name in infection_before
    ):
        play_sound("malware_detected")
    elif any(
        infection_after[name] > infection_before[name]
        for name in infection_before
    ):
        play_sound("infection_tick")


def trigger_trojan():
    if game is None:
        return

    targets = [
        (name, device)
        for name, device in game["devices"].items()
        if device["infection"] > 0 and not device["antivirus"]
    ]
    if not targets:
        targets = [
            (name, device)
            for name, device in game["devices"].items()
            if not device["antivirus"]
        ]

    if targets:
        name, device = random.choice(targets)
        infection_before = device["infection"]
        if infection_before:
            change_infection(device, infection_before)
            show_notice(f"{name} infection doubled to {device['infection']}%")
        else:
            change_infection(device, 5)
            show_notice(f"{name} infection started at 5%")
    else:
        name = random.choice(list(game["devices"]))
        show_notice(f"Antivirus blocked the Trojan on {name}")

    play_sound("trojan_detected")


def funding_income():
    average_protection = sum(
        device["protection"] for device in game["devices"].values()
    ) / len(game["devices"])
    income = int(average_protection / 10) + game["database"]["level"] * 5
    game["funding"] += income
    if game["funding"] < 10:
        game["funding"] += 10
    return income


def protect_selected_device():
    if game is None:
        return
    device = game["devices"][selected_device]
    if game["funding"] < 10:
        show_notice("Not enough funding")
    elif device["protection"] >= 100:
        show_notice(f"{selected_device} is fully protected")
    else:
        game["funding"] -= 10
        device["protection"] = min(100, device["protection"] + 10)
        play_sound("upgrade")
        show_notice(f"{selected_device} protection increased")


def buy_antivirus():
    device = game["devices"][selected_device]
    if game["funding"] < 20:
        show_notice("Not enough funding")
    elif device["antivirus"]:
        show_notice("Antivirus already installed")
    else:
        game["funding"] -= 20
        device["antivirus"] = True
        play_sound("upgrade")
        show_notice(f"Antivirus installed on {selected_device}")


def improve_password():
    device = game["devices"][selected_device]
    if game["funding"] < 15:
        show_notice("Not enough funding")
    elif device["password"]:
        show_notice("Password security already improved")
    else:
        game["funding"] -= 15
        device["password"] = True
        play_sound("upgrade")
        show_notice(f"Password security improved on {selected_device}")


def upgrade_database():
    database = game["database"]
    if database["level"] >= 5:
        show_notice("Database is at maximum level")
        return
    cost = database["level"] * 50
    if game["funding"] < cost:
        show_notice(f"Database upgrade costs £{cost}")
    else:
        game["funding"] -= cost
        database["level"] += 1
        database["protection"] = min(75, database["protection"] + 15)
        play_sound("upgrade")
        show_notice("Database upgraded")


def recover_infected_systems():
    available = [
        name for name, item in game["devices"].items()
        if item["infection"] >= 100
    ]
    available += [
        name for name, item in game["infrastructure"].items()
        if item["infection"] >= 100
    ]
    if game["database"]["infection"] >= 100:
        available.append("Database")
    if game["recoveries"] <= 0:
        show_notice("No recoveries available")
    elif not available:
        show_notice("Nothing currently needs recovering")
    else:
        name = available[0]
        if name == "Database":
            game["database"] = {"infection": 0, "level": 1, "protection": 0}
        elif name in game["devices"]:
            game["devices"][name] = {
                "infection": 0,
                "protection": 0,
                "antivirus": False,
                "password": False
            }
        else:
            game["infrastructure"][name] = {"infection": 0, "protection": 0}
        game["recoveries"] -= 1
        play_sound("recovery")
        show_notice(f"{name} recovered")
 
 
def play_sound(name):
    if SOUND_ENABLED:
        arcade_audio.play(name)
 
 
# ---------------------------------
# DRAWING FUNCTIONS
# ---------------------------------
 
def draw_text(text, font, color, x, y, center=False):
    image = font.render(str(text), True, color)
    rect = image.get_rect()
 
    if center:
        rect.center = (x, y)
    else:
        rect.topleft = (x, y)
 
    screen.blit(image, rect)
    return rect
 
 
def draw_circuit_background():
    screen.fill(BLACK)
 
    for x, y, length in CIRCUITS:
        pygame.draw.line(
            screen, (0, 42, 20),
            (x, y), (x + length, y), 2
        )
 
        pygame.draw.line(
            screen, (0, 42, 20),
            (x + length, y),
            (x + length, y + 24), 2
        )
 
        pygame.draw.circle(
            screen, (0, 65, 30),
            (x + length, y + 24), 3
        )
 
 
def draw_panel(rect, border=WHITE, fill=PANEL, width=2):
    pygame.draw.rect(
        screen, fill, rect, border_radius=8
    )
 
    pygame.draw.rect(
        screen, border, rect, width, border_radius=8
    )
 
 
def add_button(label, rect, action, accent=GREEN, font=FONT):
    hitboxes.append((pygame.Rect(rect), action, label))
 
    mouse = pygame.mouse.get_pos()
    is_hover = pygame.Rect(rect).collidepoint(mouse)
 
    color = accent if is_hover else WHITE
    fill = (20, 38, 28) if is_hover else PANEL
 
    pygame.draw.rect(
        screen, fill, rect, border_radius=7
    )
 
    pygame.draw.rect(
        screen, color, rect, 2, border_radius=7
    )
 
    draw_text(
        label, font, color,
        rect[0] + rect[2] // 2,
        rect[1] + rect[3] // 2,
        center=True
    )
 
 
def show_notice(message, seconds=2.0):
    global notice, notice_timer
 
    notice = message
    notice_timer = seconds


load_scores()

LEADERBOARD_SERVER = None
LEADERBOARD_SERVER_IP = get_local_ip()
try:
    LEADERBOARD_SERVER = start_server(LEADERBOARD_FILE)
except OSError as error:
    show_notice(f"Remote leaderboard unavailable: {error}")
 
 
def draw_header(title, subtitle=None):
    draw_text(
        title, TITLE, PINK,
        screen.get_width() // 2, 48, center=True
    )
 
    if subtitle:
        draw_text(
            subtitle, SMALL, GREEN,
            screen.get_width() // 2, 100, center=True
        )
 
 
def draw_sound_button():
    label = "SOUND: ON" if SOUND_ENABLED else "SOUND: OFF"
 
    add_button(
        label,
        (screen.get_width() - 155, 18, 135, 42),
        "toggle_sound",
        CYAN,
        SMALL
    )
 
 
# ---------------------------------
# MAIN MENU
# ---------------------------------
 
def draw_menu():
    draw_header("CYBER DEFENDER", "ARCADE CYBER DEFENCE")
 
    draw_panel(
        (screen.get_width() // 2 - 245,
         145, 490, 440),
        GREEN
    )
 
    add_button(
        "START GAME",
        (screen.get_width() // 2 - 175, 205, 350, 62),
        "difficulty", GREEN
    )
 
    add_button(
        "LEADERBOARD",
        (screen.get_width() // 2 - 175, 295, 350, 62),
        "leaderboard", PINK
    )
 
    add_button(
        "HOW TO PLAY",
        (screen.get_width() // 2 - 175, 385, 350, 62),
        "how", CYAN
    )
 
    add_button(
        "QUIT",
        (screen.get_width() // 2 - 175, 475, 350, 62),
        "quit", WHITE
    )
 
    draw_text(
        "DEFEND YOUR NETWORK. SURVIVE THE WAVES.",
        SMALL, GREEN,
        screen.get_width() // 2, 630, center=True
    )

    draw_text(
        f"REMOTE LEADERBOARD: {LEADERBOARD_SERVER_IP}:{LEADERBOARD_PORT}",
        SMALL, CYAN,
        screen.get_width() // 2, 660, center=True
    )
 
    draw_sound_button()
 
 
# ---------------------------------
# DIFFICULTY SELECT
# ---------------------------------
 
def draw_difficulty():
    draw_header("SELECT DIFFICULTY", "Pick a challenge, then follow the tutorial.")
 
    for i, name in enumerate(DIFFICULTIES):
        add_button(
            name.upper(),
            (screen.get_width() // 2 - 190,
             165 + i * 92, 380, 62),
            "diff_" + name,
            GREEN if name == "Normal" else PINK
        )
 
    add_button(
        "BACK",
        (35, screen.get_height() - 75, 150, 48),
        "menu", WHITE
    )
 
    draw_sound_button()
 
 
# ---------------------------------
# LEADERBOARD
# ---------------------------------
 
def draw_leaderboard():
    draw_header("LEADERBOARD", "TOP SCORES BY DIFFICULTY")
 
    draw_panel(
        (screen.get_width() // 2 - 300,
         150, 600, 400),
        PINK
    )
 
    add_button(
        "<",
        (screen.get_width() // 2 - 245, 170, 65, 50),
        "lb_prev", CYAN
    )
 
    add_button(
        leaderboard_difficulty.upper(),
        (screen.get_width() // 2 - 140, 170, 280, 50),
        "lb_none", GREEN
    )
 
    add_button(
        ">",
        (screen.get_width() // 2 + 180, 170, 65, 50),
        "lb_next", CYAN
    )
 
    scores = get_scores(leaderboard_difficulty)
    if not scores:
        draw_text(
            "No scores recorded yet.",
            SMALL, GREY,
            screen.get_width() // 2, 300, center=True
        )

    for i, score in enumerate(scores):
        draw_text(
            f'{i + 1}. {score["name"]} - {score["waves"]} waves',
            SMALL, WHITE,
            screen.get_width() // 2 - 210,
            235 + i * 28
        )
 
    draw_text(
        "Top 10 scores for this difficulty.",
        SMALL, GREY,
        screen.get_width() // 2, 500, center=True
    )
 
    add_button(
        "BACK",
        (35, screen.get_height() - 75, 150, 48),
        "menu", WHITE
    )
 
    draw_sound_button()
 
 
# ---------------------------------
# GAME OVER / NAME ENTRY
# ---------------------------------

def draw_score_entry():
    compact = screen.get_height() < 560
    wave_label = "WAVE" if final_score == 1 else "WAVES"
    draw_header("GAME OVER", f"YOU SURVIVED {final_score} {wave_label}")

    panel_width = min(700, screen.get_width() - 40)
    panel_x = (screen.get_width() - panel_width) // 2
    panel_y = 125 if compact else 155
    panel_height = 330 if compact else 370
    draw_panel((panel_x, panel_y, panel_width, panel_height), PINK)

    draw_text(
        "ENTER YOUR NAME FOR THE LEADERBOARD",
        SMALL if compact else FONT, WHITE,
        screen.get_width() // 2, panel_y + (58 if compact else 65),
        center=True
    )

    field_width = min(520, screen.get_width() - 80)
    field_x = (screen.get_width() - field_width) // 2
    field_y = panel_y + (100 if compact else 110)
    draw_panel((field_x, field_y, field_width, 64), CYAN)
    draw_text(
        player_name or "Type your name...",
        SUBTITLE, WHITE if player_name else GREY,
        field_x + 14, field_y + 17
    )
    draw_text(
        f"{len(player_name)}/{MAX_PLAYER_NAME_LENGTH}",
        SMALL, GREY, screen.get_width() // 2,
        panel_y + (210 if compact else 200), center=True
    )
    draw_text(
        score_entry_message or "Type on the keyboard. Backspace edits your name.",
        SMALL, ORANGE if score_entry_message else WHITE,
        screen.get_width() // 2,
        panel_y + (240 if compact else 230), center=True
    )

    add_button(
        "SAVE SCORE",
        (
            screen.get_width() // 2 - 140,
            panel_y + (270 if compact else 275),
            280, 58
        ),
        "submit_score", GREEN
    )
    draw_sound_button()


# ---------------------------------
# HOW TO PLAY
# ---------------------------------
 
def draw_fullscreen_modal_background():
    screen.fill(BLACK)
    panel = pygame.Rect(8, 8, screen.get_width() - 16, screen.get_height() - 16)
    draw_panel(panel, CYAN, PANEL, 3)


def draw_email():
    email = game["pending_email"] if game else None
    if not email:
        draw_header("NO NEW EMAIL", "Start another wave to receive an email.")
        add_button(
            "BACK TO DASHBOARD",
            (screen.get_width() // 2 - 180, 400, 360, 58),
            "game", GREEN
        )
        draw_sound_button()
        return

    compact = screen.get_height() < 560
    draw_fullscreen_modal_background()
    draw_header("INCOMING EMAIL", "Check the message, then choose what to do.")

    text_x = 32
    text_width = screen.get_width() - 64
    label_font = SMALL if compact else FONT
    draw_text(
        f"FROM: {email['sender']}",
        label_font, WHITE, text_x, 145
    )
    draw_text(
        f"SUBJECT: {email['subject']}",
        label_font, GREEN, text_x, 185
    )

    character_width = max(1, SMALL.size("M")[0])
    wrap_width = max(20, text_width // character_width)
    for index, line in enumerate(textwrap.wrap(email["body"], width=wrap_width)):
        draw_text(
            line, SMALL, WHITE, text_x,
            225 + index * 26
        )

    button_width = min(220, (screen.get_width() - 96) // 3)
    button_gap = 12
    button_x = (
        screen.get_width() - (button_width * 3 + button_gap * 2)
    ) // 2
    button_height = 52 if compact else 58
    button_y = screen.get_height() - button_height - 40
    draw_text(
        "Open, ignore, or report the email to continue.",
        SMALL, GREY, screen.get_width() // 2, button_y - 30, center=True
    )
    buttons = [
        ("OPEN EMAIL", "email_open", ORANGE),
        ("IGNORE", "email_ignore", WHITE),
        ("REPORT EMAIL", "email_report", GREEN)
    ]
    for index, (label, action, accent) in enumerate(buttons):
        add_button(
            label,
            (
                button_x + index * (button_width + button_gap),
                button_y,
                button_width,
                button_height
            ),
            action, accent, SMALL
        )
    draw_sound_button()


def draw_how():
    draw_header("HOW TO PLAY", "PROTECT YOUR NETWORK")
 
    draw_panel(
        (screen.get_width() // 2 - 410,
         145, 820, 425),
        CYAN
    )
 
    lines = [
        "1. Your devices are the PC, laptop, phone and printer.",
        "2. Risk rises when unwanted software spreads.",
        "3. Use your funding to buy protection and upgrades.",
        "4. At 100% risk, use a recovery to reset that item.",
        "5. Protect the network and database through each wave.",
        "6. Green is low, orange means watch it, pink is high.",
        "7. Check emails between waves: report fake ones, open real ones.",
        "8. Antivirus can stop a Trojan doubling infection.",
        "9. Press NEXT WAVE 10 times quickly to double infection."
    ]
 
    line_spacing = 42 if len(lines) > 6 else 55
    start_y = 185 if len(lines) > 6 else 205
    for i, line in enumerate(lines):
        draw_text(
            line, SMALL, WHITE,
            screen.get_width() // 2 - 350,
            start_y + i * line_spacing
        )
 
    add_button(
        "BACK",
        (35, screen.get_height() - 75, 150, 48),
        "menu", WHITE
    )
 
    draw_sound_button()
 
 
def draw_tutorial():
    draw_header("TUTORIAL - WAVE 1", "A quick first mission: protect a device")
    draw_panel(
        (screen.get_width() // 2 - 390, 145, 780, 430),
        CYAN
    )

    pc = game["devices"]["PC"]
    draw_text(
        "Unwanted software has reached your PC.",
        FONT, WHITE,
        screen.get_width() // 2, 205, center=True
    )
    draw_text(
        f"PC risk: {pc['infection']}%     Protection: {pc['protection']}%",
        SUBTITLE, PINK,
        screen.get_width() // 2, 265, center=True
    )
    draw_text(
        f"Available funding: £{game['funding']}",
        FONT, GREEN,
        screen.get_width() // 2, 320, center=True
    )

    if game["tutorial_protection_bought"]:
        draw_text(
            "PC protection is ready. Your first wave is next.",
            SMALL, GREEN,
            screen.get_width() // 2, 375, center=True
        )
        draw_text(
            "Protection helps slow down unwanted software.",
            SMALL, WHITE,
            screen.get_width() // 2, 405, center=True
        )
        add_button(
            "START GAME",
            (screen.get_width() // 2 - 170, 455, 340, 58),
            "tutorial_continue", GREEN
        )
    else:
        draw_text(
            "Buy protection now to help stop the risk growing.",
            SMALL, WHITE,
            screen.get_width() // 2, 375, center=True
        )
        add_button(
            "BUY PC PROTECTION - £10",
            (screen.get_width() // 2 - 190, 430, 380, 58),
            "tutorial_protect", GREEN
        )

    add_button(
        "MAIN MENU",
        (35, screen.get_height() - 75, 150, 48),
        "menu", WHITE
    )
    draw_sound_button()


# ---------------------------------
# GAME DASHBOARD
# ---------------------------------
 
def get_risk_color(value):
    if value >= 75:
        return PINK
    if value >= 40:
        return ORANGE
    return GREEN


def draw_bar(label, value, rect):
    x, y, w, h = rect
    color = get_risk_color(value)
 
    pygame.draw.rect(
        screen, (45, 45, 45),
        rect, border_radius=5
    )
 
    fill_w = int(w * max(0, min(value, 100)) / 100)
 
    if fill_w > 0:
        pygame.draw.rect(
            screen, color,
            (x, y, fill_w, h),
            border_radius=5
        )
 
    pygame.draw.rect(
        screen, WHITE, rect, 1, border_radius=5
    )
 
    draw_text(
        f"{label}: {value}%",
        SMALL, WHITE, x, y - 26
    )
 
 
def draw_compact_bar(label, value, rect):
    x, y, width, _ = rect
    draw_text(f"{label}: {value}% risk", SMALL, WHITE, x, y)

    track = pygame.Rect(x, y + 22, width, 8)
    pygame.draw.rect(screen, (45, 45, 45), track, border_radius=4)
    fill_width = int(track.width * max(0, min(value, 100)) / 100)
    if fill_width:
        color = get_risk_color(value)
        pygame.draw.rect(
            screen, color,
            (track.x, track.y, fill_width, track.height),
            border_radius=4
        )
    pygame.draw.rect(screen, WHITE, track, 1, border_radius=4)


def draw_game():
    current = game
    compact = screen.get_height() < 600
    draw_header(
        "NETWORK STATUS",
        f"DIFFICULTY: {difficulty.upper()}   |   WAVE: {current['wave'] if current else 1}"
    )

    summary_y = 120 if compact else 135
    summary_height = 75 if compact else 110
    summary_text_y = summary_y + 22 if compact else 165
    draw_panel(
        (30, summary_y, screen.get_width() - 60, summary_height),
        GREEN
    )
    draw_text(
        f"FUNDING: £{current['funding'] if current else 0}",
        SUBTITLE, GREEN, 55, summary_text_y
    )
    draw_text(
        f"RECOVERIES: {current['recoveries'] if current else 0}",
        SUBTITLE, CYAN, screen.get_width() - 300, summary_text_y
    )

    panel_y = 205 if compact else 255
    panel_height = 170 if compact else 245
    margin = 30
    gap = 18
    column_width = max(1, (screen.get_width() - 2 * margin - gap) // 2)
    left_panel = (margin, panel_y, column_width, panel_height)
    right_x = margin + column_width + gap
    right_panel = (right_x, panel_y, column_width, panel_height)
    draw_panel(left_panel, GREEN)
    draw_panel(right_panel, CYAN)

    draw_text(
        "DEVICES - RISK", SMALL, GREEN,
        margin + column_width // 2, panel_y + 20, center=True
    )
    draw_text(
        "NETWORK - RISK", SMALL, CYAN,
        right_x + column_width // 2, panel_y + 20, center=True
    )

    device_names = ("PC", "Laptop", "Phone", "Printer")
    network_names = ("Router", "Switch", "Network")
    if current:
        device_items = [
            (name, current["devices"][name]["infection"])
            for name in device_names
        ]
        network_items = [
            (name, current["infrastructure"][name]["infection"])
            for name in network_names
        ]
        network_items.append(("Database", current["database"]["infection"]))
    else:
        device_items = [(name, 0) for name in device_names]
        network_items = [(name, 0) for name in network_names]
        network_items.append(("Database", 0))

    bar_x = margin + 12
    right_bar_x = right_x + 12
    bar_width = max(1, column_width - 24)
    if compact:
        for index, (name, value) in enumerate(device_items):
            draw_compact_bar(
                name, value,
                (bar_x, panel_y + 34 + index * 30, bar_width, 30)
            )
        for index, (name, value) in enumerate(network_items):
            draw_compact_bar(
                name, value,
                (right_bar_x, panel_y + 34 + index * 30, bar_width, 30)
            )
    else:
        for index, (name, value) in enumerate(device_items):
            draw_bar(
                name, value,
                (bar_x, panel_y + 60 + index * 50, bar_width, 22)
            )
        for index, (name, value) in enumerate(network_items):
            draw_bar(
                name, value,
                (right_bar_x, panel_y + 60 + index * 50, bar_width, 22)
            )

    button_y = panel_y + panel_height + (12 if compact else 15)
    button_height = 38 if compact else 52
    button_gap = 8
    button_margin = 30
    button_width = max(
        1,
        (screen.get_width() - 2 * button_margin - 3 * button_gap) // 4
    )
    buttons = [
        ("UPGRADES", "upgrades", GREEN),
        ("RECOVERY", "recovery", CYAN),
        ("THREATS", "threats", ORANGE),
        ("NEXT WAVE", "attack", PINK)
    ]
    for index, (label, action, accent) in enumerate(buttons):
        add_button(
            label,
            (
                button_margin + index * (button_width + button_gap),
                button_y,
                button_width,
                button_height
            ),
            action, accent
        )

    if not compact:
        draw_text(
            "Check each risk level, then choose your next action.",
            SMALL, GREY,
            screen.get_width() // 2, button_y + button_height + 14,
            center=True
        )

    menu_height = 34 if compact else 48
    menu_y = screen.get_height() - menu_height - (10 if compact else 27)
    add_button(
        "MAIN MENU",
        (35, menu_y, 150, menu_height),
        "menu", WHITE, SMALL
    )
    draw_sound_button()
 
 
# ---------------------------------
# PLACEHOLDER SCREENS
# ---------------------------------
 
def draw_placeholder(title, description, return_to="game"):
    draw_header(title, description)
 
    draw_panel(
        (screen.get_width() // 2 - 350,
         180, 700, 300),
        CYAN
    )
 
    draw_text(
        "This section is a GUI placeholder.",
        FONT, WHITE,
        screen.get_width() // 2, 300, center=True
    )
 
    draw_text(
        "It will be connected to the actual game logic later.",
        SMALL, GREY,
        screen.get_width() // 2, 355, center=True
    )
 
    add_button(
        "BACK TO DASHBOARD",
        (screen.get_width() // 2 - 180, 420, 360, 58),
        return_to, GREEN
    )
 
    draw_sound_button()


def draw_upgrades():
    draw_header("UPGRADES", f"FUNDING: £{game['funding'] if game else 0}")
    draw_panel((30, 145, screen.get_width() - 60, 420), GREEN)

    names = list(game["devices"].keys()) if game else ["PC"]
    for i, name in enumerate(names):
        y = 175 + i * 55
        add_button(
            name,
            (55, y, 180, 44),
            "device_" + name,
            GREEN if name == selected_device else WHITE,
            SMALL
        )

    add_button("PROTECT £10", (260, 175, 250, 44), "protect_device", GREEN, SMALL)
    add_button("ANTIVIRUS £20", (260, 230, 250, 44), "buy_antivirus", CYAN, SMALL)
    add_button("PASSWORD £15", (260, 285, 250, 44), "improve_password", PINK, SMALL)
    add_button("UPGRADE DATABASE", (260, 340, 250, 44), "upgrade_database", ORANGE, SMALL)

    add_button("BACK TO DASHBOARD", (260, 470, 250, 58), "game", GREEN)
    draw_sound_button()


def draw_recovery():
    draw_header("RECOVERY", f"RECOVERIES AVAILABLE: {game['recoveries'] if game else 0}")
    draw_panel((screen.get_width() // 2 - 350, 150, 700, 390), CYAN)
    draw_text("Use one recovery to reset the first item at 100% risk.", FONT, WHITE,
              screen.get_width() // 2, 220, center=True)
    add_button("USE RECOVERY", (screen.get_width() // 2 - 180, 300, 360, 58),
               "recover_system", CYAN)
    add_button("BACK TO DASHBOARD", (screen.get_width() // 2 - 180, 410, 360, 58),
               "game", GREEN)
    draw_sound_button()


def draw_threats():
    draw_header("DEVICE STATUS", "RISK LEVELS")
    draw_panel((screen.get_width() // 2 - 350, 145, 700, 420), ORANGE)

    y = 175
    if game:
        assets = list(game["devices"].items())
        assets.extend(game["infrastructure"].items())
        assets.append(("Database", game["database"]))
        for name, item in assets:
            risk = item["infection"]
            status = "NEEDS HELP" if risk >= 100 else "HIGH RISK" if risk >= 75 else "WATCH" if risk > 0 else "SAFE"
            draw_text(
                f"{name}: {risk}%  {status}",
                SMALL, WHITE,
                screen.get_width() // 2 - 280, y
            )
            y += 35

    add_button("BACK TO DASHBOARD", (screen.get_width() // 2 - 180, 500, 360, 58),
               "game", GREEN)
    draw_sound_button()
 
 
# ---------------------------------
# NAVIGATION / ACTIONS
# ---------------------------------
 
def change_lb(direction):
    global leaderboard_difficulty
 
    index = DIFFICULTIES.index(leaderboard_difficulty)
 
    leaderboard_difficulty = DIFFICULTIES[
        (index + direction) % len(DIFFICULTIES)
    ]
 
 
def handle_action(action):
    global screen_name, difficulty, game, selected_device, game_over
    global leaderboard_difficulty, SOUND_ENABLED, player_name, final_score
    global score_entry_message, notice_timer
    global next_wave_press_count, next_wave_press_started
    global fullscreen, screen, running

    modal_actions = (
        "email_open", "email_ignore", "email_report"
    )
    if action != "attack" and action not in modal_actions:
        next_wave_press_count = 0
        next_wave_press_started = 0
 
    if action == "toggle_sound":
        SOUND_ENABLED = not SOUND_ENABLED
        arcade_audio.set_muted(not SOUND_ENABLED)
 
        show_notice(
            "Sound enabled" if SOUND_ENABLED else "Sound muted"
        )
 
        if SOUND_ENABLED:
            play_sound("menu_select")
 
        return
 
    if action == "quit":
        running = False
        return

    if action == "submit_score":
        name = player_name.strip()
        if not name:
            score_entry_message = "Type your name before saving your score."
            return
        add_score(name, difficulty, final_score)
        leaderboard_difficulty = difficulty
        screen_name = "leaderboard"
        return
 
    if action == "menu":
        screen_name = "menu"
        play_sound("back")
 
    elif action == "difficulty":
        screen_name = "difficulty"
        play_sound("new_game")
 
    elif action == "leaderboard":
        screen_name = "leaderboard"
        play_sound("leaderboard_open")
 
    elif action == "how":
        screen_name = "how"
        play_sound("how_to_play")
 
    elif action.startswith("diff_"):
        difficulty = action.split("_", 1)[1]
        game = create_game(difficulty)
        game_over = False
        player_name = ""
        final_score = 0
        score_entry_message = ""
        screen_name = "tutorial"
        play_sound(f"difficulty_{difficulty.lower()}")
        show_notice(f"{difficulty} tutorial")

    elif action == "tutorial_protect":
        if game and not game["tutorial_protection_bought"]:
            pc = game["devices"]["PC"]
            if game["funding"] < 10:
                show_notice("Not enough funding for PC protection")
            else:
                game["funding"] -= 10
                pc["protection"] = min(100, pc["protection"] + 10)
                pc["infection"] = 9
                game["tutorial_protection_bought"] = True
                play_sound("protection_up")
                show_notice("PC protection installed")

    elif action == "tutorial_continue":
        if game and game["tutorial_protection_bought"]:
            game["tutorial_complete"] = True
            screen_name = "game"
            play_sound("game_start")
            show_notice("Defend the network and watch for email alerts")
 
    elif action == "lb_prev":
        change_lb(-1)
        play_sound("click")
 
    elif action == "lb_next":
        change_lb(1)
        play_sound("click")
 
    elif action == "upgrades":
        screen_name = "upgrades"
        play_sound("menu_select")
 
    elif action == "recovery":
        screen_name = "recovery"
        play_sound("menu_select")
 
    elif action == "threats":
        screen_name = "threats"
        play_sound("critical_alert")
 
    elif action in ("email_open", "email_ignore", "email_report"):
        if game and game["pending_email"]:
            email = game["pending_email"]
            if action == "email_report":
                if email["fake"]:
                    game["recoveries"] += 1
                    play_sound("phishing_success")
                    show_notice("Correct! Suspicious email reported. +1 recovery")
                else:
                    play_sound("phishing_failure")
                    show_notice("This email was legitimate. No recovery earned.")
            elif action == "email_open":
                if email["fake"]:
                    name = random.choice(list(game["devices"]))
                    device = game["devices"][name]
                    infection_before = device["infection"]
                    infection_amount = random.randint(5, 10)
                    change_infection(device, infection_amount)
                    actual_increase = device["infection"] - infection_before
                    play_sound("phishing_failure")
                    show_notice(
                        f"Phishing email! {name} infection +{actual_increase}%"
                    )
                else:
                    game["funding"] += 10
                    play_sound("phishing_success")
                    show_notice("Legitimate email opened. +£10 funding")
            else:
                show_notice("Email ignored. No change.")

            game["pending_email"] = None
            screen_name = "game"
            if next_wave_press_count:
                next_wave_press_started = pygame.time.get_ticks()
        else:
            screen_name = "game"

    elif action.startswith("device_"):
        selected_device = action.split("_", 1)[1]
        show_notice(f"{selected_device} selected")

    elif action == "protect_device":
        protect_selected_device()

    elif action == "buy_antivirus":
        buy_antivirus()

    elif action == "improve_password":
        improve_password()

    elif action == "upgrade_database":
        upgrade_database()

    elif action == "recover_system":
        recover_infected_systems()

    elif action == "game":
        screen_name = "game"

    elif action == "attack":
        if game and not game["game_over"]:
            now = pygame.time.get_ticks()
            elapsed = now - next_wave_press_started
            if (
                next_wave_press_count == 0
                or elapsed < 0
                or elapsed > NEXT_WAVE_PRESS_WINDOW_MS
            ):
                next_wave_press_count = 1
                next_wave_press_started = now
            else:
                next_wave_press_count += 1

            if next_wave_press_count >= NEXT_WAVE_TROJAN_PRESSES:
                next_wave_press_count = 0
                next_wave_press_started = 0
                trigger_trojan()
                return

            play_sound("wave_start")
            malware_attack()
            income = funding_income()
            play_sound("funding")
            show_notice(f"Wave {game['wave']} complete - income £{income}")

            if game["database"]["infection"] >= 100:
                if game["backup_available"] and not game["backup_used"]:
                    game["database"]["infection"] = 25
                    game["backup_used"] = True
                    play_sound("backup_activated")
                    show_notice("Backup database restored")
                elif not game["emergency_restart_used"]:
                    for item in game["infrastructure"].values():
                        item["infection"] = 0
                    game["database"]["infection"] = 0
                    game["emergency_restart_used"] = True
                    game["restart_protection"] = 2
                    play_sound("emergency_restart")
                    show_notice("Emergency restart saved the network")
                else:
                    game["game_over"] = True
                    game_over = True
                    final_score = max(0, game["wave"] - 1)
                    player_name = ""
                    score_entry_message = ""
                    screen_name = "score_entry"
                    play_sound("game_over")

            if not game["game_over"]:
                game["wave"] += 1
                event_roll = random.random()
                if event_roll < TROJAN_EVENT_CHANCE:
                    trigger_trojan()
                elif event_roll < TROJAN_EVENT_CHANCE + EMAIL_EVENT_CHANCE:
                    game["pending_email"] = random.choice(EMAILS)
                    screen_name = "email"
                    notice_timer = 0
 
    elif action == "fullscreen":
        fullscreen = not fullscreen
 
        if fullscreen:
            screen = pygame.display.set_mode(
                (0, 0), pygame.FULLSCREEN
            )
        else:
            screen = pygame.display.set_mode(
                (WIDTH, HEIGHT), pygame.RESIZABLE
            )
 
 
# ---------------------------------
# MAIN LOOP
# ---------------------------------

def handle_name_input(event):
    global player_name, score_entry_message

    if event.key == pygame.K_BACKSPACE:
        player_name = player_name[:-1]
        score_entry_message = ""
    elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
        handle_action("submit_score")
    elif (
        event.unicode
        and event.unicode.isprintable()
        and len(player_name) < MAX_PLAYER_NAME_LENGTH
    ):
        player_name += event.unicode
        score_entry_message = ""


running = True
play_sound("boot")
 
while running:
    hitboxes = []
    draw_circuit_background()
 
    if screen_name == "menu":
        draw_menu()
 
    elif screen_name == "difficulty":
        draw_difficulty()
 
    elif screen_name == "leaderboard":
        draw_leaderboard()

    elif screen_name == "score_entry":
        draw_score_entry()
 
    elif screen_name == "how":
        draw_how()
 
    elif screen_name == "tutorial":
        draw_tutorial()

    elif screen_name == "game":
        draw_game()
 
    elif screen_name == "upgrades":
        draw_upgrades()
 
    elif screen_name == "recovery":
        draw_recovery()
 
    elif screen_name == "threats":
        draw_threats()

    elif screen_name == "email":
        draw_email()

    # Temporary notification
    if notice_timer > 0:
        notice_timer -= clock.get_time() / 1000
 
        draw_panel(
            (screen.get_width() // 2 - 210,
             screen.get_height() - 135, 420, 55),
            PINK
        )
 
        draw_text(
            notice, SMALL, WHITE,
            screen.get_width() // 2,
            screen.get_height() - 108,
            center=True
        )
 
    # Hover sound plays only when entering a button
    mouse_pos = pygame.mouse.get_pos()
 
    current_hover = next(
        (label for rect, action, label in hitboxes
         if rect.collidepoint(mouse_pos)),
        None
    )
 
    if current_hover != hovered_button and current_hover is not None:
        play_sound("hover")
 
    hovered_button = current_hover
 
    # Events
    for event in pygame.event.get():
 
        if event.type == pygame.QUIT:
            running = False
 
        elif event.type == pygame.KEYDOWN:
            if screen_name == "score_entry":
                handle_name_input(event)
            elif screen_name == "email":
                if event.key in (pygame.K_ESCAPE, pygame.K_BACKSPACE):
                    handle_action("email_ignore")
                elif event.key == pygame.K_F11:
                    handle_action("fullscreen")
            elif event.key == pygame.K_ESCAPE:
                screen_name = "menu"
                play_sound("select")
 
            elif event.key == pygame.K_F11:
                handle_action("fullscreen")
 
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            play_sound("click")
 
            for rect, action, label in hitboxes:
                if rect.collidepoint(event.pos):
                    handle_action(action)
                    break
 
        elif event.type == pygame.VIDEORESIZE and not fullscreen:
            screen = pygame.display.set_mode(
                event.size, pygame.RESIZABLE
            )
 
    pygame.display.flip()
    clock.tick(60)
 
 
pygame.quit()
if LEADERBOARD_SERVER is not None:
    LEADERBOARD_SERVER.shutdown()
    LEADERBOARD_SERVER.server_close()
sys.exit()
