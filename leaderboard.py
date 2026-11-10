import json
import sys
from pathlib import Path


LEADERBOARD_PATH = Path(__file__).with_name("leaderboard.json")
WIDTH = 56
DIFFICULTY_ORDER = ("Easy", "Normal", "Hard", "Extreme", "Extreme (warning)")

COLORS = {
    "cyan": "96",
    "green": "92",
    "yellow": "93",
    "red": "91",
    "magenta": "95",
    "white": "97",
    "dim": "2",
}


def arcade_text(text, color="cyan", bold=False):
    if not sys.stdout.isatty():
        return str(text)

    style = COLORS.get(color, COLORS["cyan"])
    if bold:
        style = f"1;{style}"
    return f"\033[{style}m{text}\033[0m"


def load_leaderboards():
    try:
        contents = LEADERBOARD_PATH.read_text(encoding="utf-8")
    except FileNotFoundError:
        return {}
    except OSError as error:
        return error

    try:
        data = json.loads(contents)
    except json.JSONDecodeError as error:
        return error

    if isinstance(data, list):
        data = {"Normal": data}
    if not isinstance(data, dict):
        return ValueError("The leaderboard file must contain a list or object.")

    leaderboards = {}
    for level, entries in data.items():
        if not isinstance(level, str):
            continue
        if not isinstance(entries, list):
            entries = []

        valid_entries = [
            entry
            for entry in entries
            if isinstance(entry, dict)
            and isinstance(entry.get("name"), str)
            and isinstance(entry.get("waves"), int)
        ]
        leaderboards[level] = sorted(
            valid_entries,
            key=lambda entry: entry["waves"],
            reverse=True,
        )[:10]

    return leaderboards


def border(left, fill, right):
    return f"{left}{fill * WIDTH}{right}"


def framed_line(text="", color="cyan", bold=False):
    content = f" {text}"[:WIDTH].ljust(WIDTH)
    print(arcade_text(f"║{content}║", color, bold))


def show_leaderboard():
    leaderboards = load_leaderboards()

    print(arcade_text(border("╔", "═", "╗"), "cyan", True))
    framed_line("★  CYBER DEFENDER  ★", "magenta", True)
    framed_line("ARCADE HIGH SCORES", "yellow", True)
    print(arcade_text(border("╠", "═", "╣"), "cyan", True))

    if isinstance(leaderboards, Exception):
        framed_line("Could not load leaderboard.", "red", True)
        framed_line(str(leaderboards), "red")
        print(arcade_text(border("╚", "═", "╝"), "cyan", True))
        return

    if not leaderboards:
        framed_line("No saved scores yet. Play a game to set a record!", "white")
        print(arcade_text(border("╚", "═", "╝"), "cyan", True))
        return

    ordered_levels = [level for level in DIFFICULTY_ORDER if level in leaderboards]
    ordered_levels.extend(sorted(level for level in leaderboards if level not in ordered_levels))

    for level in ordered_levels:
        print(arcade_text(border("╟", "─", "╢"), "cyan"))
        framed_line(level.upper(), "yellow", True)

        entries = leaderboards[level]
        if not entries:
            framed_line("No scores yet", "dim")
            continue

        for position, entry in enumerate(entries, start=1):
            name = entry["name"][:30]
            waves = entry["waves"]
            row = f"{position:02}. {name:<30} {waves:>6} WAVES"
            color = ("yellow", "white", "magenta")[position - 1] if position <= 3 else "cyan"
            framed_line(row, color, position <= 3)

    print(arcade_text(border("╚", "═", "╝"), "cyan", True))


if __name__ == "__main__":
    show_leaderboard()
