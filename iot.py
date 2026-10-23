import random

import time


import sys


import json


from pathlib import Path

# ============================================================


# CYBER DEFENCE — MAIN PROJECT v0.9
# This game tracks a fictional cyber defence scenario where the player
# manages funding, protects devices, and fights off malware attacks.

# ============================================================


# Starting player economy and current game state.
funding = 200


wave = 1


difficulty = "Normal"


# Difficulty settings change how quickly malware spreads and how often
# new infections appear. Higher difficulties make the game harder.
DIFFICULTY_SETTINGS = {

    "Easy": {

        "device_growth": 5,

        "infection_chance": 15,

        "infrastructure_growth": 7,

    },

    "Normal": {

        "device_growth": 7,

        "infection_chance": 20,

        "infrastructure_growth": 10,

    },

    "Hard": {

        "device_growth": 10,

        "infection_chance": 30,

        "infrastructure_growth": 15,

    },

}


# Recovery kits let the player restore compromised devices or infrastructure.
recoveries = 4


# Backup system unlocks later and can restore the database in an emergency.
backup_available = False


backup_used = False


# Emergency Network Restart gives a one-time way to clear a critical database
# infection, with reduced infrastructure growth for the next few waves.
restart_available = True

restart_waves_remaining = 0


# These flags control whether Liam or Will can provide advice in-game.
liam_assistance = True


will_assistance = True


liam_advice_turns = 0


will_advice_turns = 0


tutorial_complete = False


# These values track repeated player choices and anti-skip protections.
last_choice = None

repeated_choice_count = 0

trojan_event_state = "inactive"

trojan_used = False




# ============================================================


# DEVICES
# Each device stores its current infection level, protection level, and any
# security tools that have been installed on it.

# ============================================================


devices = {


    "PC": {


        "infection": 0,


        "protection": 0,



        "antivirus": False,


        "password": False


    },


    "Laptop": {


        "infection": 0,


        "protection": 0,


        "antivirus": False,


        "password": False


    },


    "Phone": {


        "infection": 0,


        "protection": 0,


        "antivirus": False,


        "password": False


    },


    "Printer": {


        "infection": 0,


        "protection": 0,


        "antivirus": False,


        "password": False


    }


}




# ============================================================


# INFRASTRUCTURE


# ============================================================


infrastructure = {


    "Router": {


        "infection": 0,


        "protection": 0


    },


    "Switch": {


        "infection": 0,


        "protection": 0


    },


    "Network": {


        "infection": 0,


        "protection": 0


    }


}




# ============================================================


# DATABASE


# ============================================================


database = {


    "infection": 0,


    "level": 1,


    "protection": 0


}




# ============================================================


# THREATS


# ============================================================


active_threats = []




# ============================================================


# BASIC FUNCTIONS


# ============================================================


def pause():
    # Stops the game briefly and waits for the player to press Enter.
    input("\nPress ENTER to continue...")


def read_menu_key():
    # Reads a single arrow key or Enter key so the menu can support keyboard
    # navigation on both Windows and Unix-like systems.


    if sys.platform == "win32":

        import msvcrt


        key = msvcrt.getwch()

        if key in ("\x00", "\xe0"):

            return {"H": "UP", "P": "DOWN"}.get(msvcrt.getwch(), "")

        return "ENTER" if key in ("\r", "\n") else key


    import termios

    import tty


    descriptor = sys.stdin.fileno()

    previous_settings = termios.tcgetattr(descriptor)

    try:

        tty.setcbreak(descriptor)

        key = sys.stdin.read(1)

        if key == "\x1b":

            key += sys.stdin.read(2)

    finally:

        termios.tcsetattr(descriptor, termios.TCSADRAIN, previous_settings)


    if key == "\x1b[A":

        return "UP"

    if key == "\x1b[B":

        return "DOWN"

    return "ENTER" if key in ("\r", "\n") else key


def select_option(prompt, options):
    # Displays a menu and lets the player select an option by number or arrow
    # keys. It supports both normal terminal input and interactive key presses.

    if not sys.stdin.isatty():

        print(prompt)

        for index, (label, _) in enumerate(options, start=1):

            print(f"{index}. {label}")

        selection = input("Choose: ").strip()

        if selection.isdigit() and 1 <= int(selection) <= len(options):

            return options[int(selection) - 1][1]

        return ""


    selected = 0

    print(f"{prompt} (use Up/Down + Enter, or press a number)")


    def render_options():

        for index, (label, _) in enumerate(options):

            if index == selected:

                print(arcade_text(f">> {index + 1}. {label}", "magenta", bold=True))

            else:

                print(f"   {index + 1}. {label}")


    render_options()

    while True:

        key = read_menu_key()

        if key.isdigit() and 1 <= int(key) <= len(options):

            return options[int(key) - 1][1]

        if key == "UP":

            selected = (selected - 1) % len(options)

        elif key == "DOWN":

            selected = (selected + 1) % len(options)

        elif key == "ENTER":

            return options[selected][1]

        else:

            continue


        sys.stdout.write(f"\x1b[{len(options)}A")

        render_options()

        sys.stdout.flush()


def get_choice(prompt, aliases=None, options=None):
    # Collects player input, normalizes it, and detects repeated choices that
    # could trigger the anti-skip Trojan Horse event.

    global last_choice, repeated_choice_count, trojan_event_state, trojan_used


    if options is not None:

        choice = select_option(prompt, options)

    else:

        choice = input(prompt).strip()


    choice = choice.strip()

    if aliases:

        choice = aliases.get(choice.lower(), choice)


    choice_key = choice.lower()

    if choice_key == last_choice:

        repeated_choice_count += 1

    else:

        last_choice = choice_key

        repeated_choice_count = 1


    if trojan_used:

        repeated_choice_count = 0

        last_choice = None

        return choice


    if repeated_choice_count < 10:

        return choice


    repeated_choice_count = 0

    last_choice = None

    print("\n⚠️ Repeating the same choice 10 times triggered the Trojan Horse!")

    if trojan_event_state not in ("warning", "escalation"):

        trojan_event_state = "warning"
        trojan_used = True

    print("That repeated choice was blocked.")

    return ""




def clear_line():
    # Prints a decorative divider line to separate big sections in the UI.
    print("\n" + arcade_text("═" * 60, "cyan", bold=True))

def arcade_text(text, color="cyan", bold=False):
    # Applies terminal color codes so text can stand out in the game UI.

    colors = {
        "cyan": "96",
        "green": "92",
        "yellow": "93",
        "red": "91",
        "magenta": "95",
        "dim": "2",
        "white": "97",
    }

    if not sys.stdout.isatty():

        return str(text)

    style = colors.get(color, colors["cyan"])

    if bold:

        style = f"1;{style}"

    return f"\033[{style}m{text}\033[0m"

def infection_meter(value, width=10):
    # Builds a visual infection bar for each device or infrastructure section.
    filled = round(max(0, min(100, value)) / 100 * width)

    color = "red" if value >= 75 else "yellow" if value >= 40 else "green"

    bar = arcade_text("█" * filled, color, bold=True)

    bar += arcade_text("░" * (width - filled), "dim")

    return f"[{bar}] {value:3d}%"

def infection_label(value):
    # Converts a numeric infection value into a simple status label.

    if value >= 75:

        return arcade_text("URGENT", "red", bold=True)

    if value >= 40:

        return arcade_text("WATCH", "yellow", bold=True)

    return arcade_text("OK", "green", bold=True)

def show_wave_dashboard():
    # Prints a compact HUD for the current wave, including budget and core stats.
    clear_line()

    print(arcade_text(f"★ CYBER DEFENCE // WAVE {wave} ★", "magenta", bold=True))

    print(arcade_text(f"BUDGET £{funding}  |  RECOVERY KITS {recoveries}  |  LEVEL {difficulty}", "yellow", bold=True))

    print("NETWORK  " + infection_meter(infrastructure["Network"]["infection"]))

    print("DATABASE " + infection_meter(database["infection"]))

    clear_line()




# ============================================================


# STATUS


# ============================================================


def show_status():
    # Shows all device, network, and database conditions in a readable report.

    clear_line()


    print(arcade_text("[ NETWORK STATUS ]", "cyan", bold=True))


    clear_line()


    print(arcade_text(f"\nBUDGET: £{funding}", "yellow", bold=True))


    print("WAVE:", wave)


    print("LEVEL:", difficulty)


    print("RECOVERY KITS:", recoveries)


    print(arcade_text("\n[ DEVICES ]", "magenta", bold=True))


    for name, data in devices.items():


        print(


            f"💻 {name}: "


            f"{infection_meter(data['infection'])}  {infection_label(data['infection'])} | "


            f"{data['protection']}% protection"


        )


    print(arcade_text("\n[ NETWORK EQUIPMENT ]", "magenta", bold=True))


    for name, data in infrastructure.items():


        print(


            f"🔴 {name}: "


            f"{infection_meter(data['infection'])}  {infection_label(data['infection'])} | "


            f"{data['protection']}% protection"


        )


    print(arcade_text("\n[ DATABASE ]", "magenta", bold=True))


    print(


        f"☠️ Database: "


        f"{infection_meter(database['infection'])}  {infection_label(database['infection'])} | "


        f"Level {database['level']} | "


        f"{database['protection']}% protection"


    )


    clear_line()




# ============================================================


# CURRENT THREATS


# ============================================================


def show_threats():
    # Lists all infected systems so the player can prioritize actions.

    clear_line()


    print(arcade_text("[ CURRENT THREATS ]", "red", bold=True))


    clear_line()


    found = False


    for name, data in devices.items():


        if data["infection"] > 0:


            found = True


            print(f"\n🦠 {name}")


            print(f"   Infection: {data['infection']}%")


            if data["infection"] >= 75:


                print("   ⚠️ CRITICAL!")


            elif data["infection"] >= 40:


                print("   ⚠️ HIGH RISK")


            else:


                print("   Malware is spreading.")


    for name, data in infrastructure.items():


        if data["infection"] > 0:


            found = True


            print(f"\n🔴 {name}")


            print(f"   Infection: {data['infection']}%")


            if data["infection"] >= 75:


                print("   ⚠️ CRITICAL!")


            else:


                print("   ⚠️ UNDER ATTACK")


    if database["infection"] > 0:


        found = True


        print("\n☠️ DATABASE")


        print(f"   Infection: {database['infection']}%")


        if database["infection"] >= 75:


            print("   ⚠️ CRITICAL!")


        else:


            print("   ⚠️ FINAL TARGET UNDER ATTACK")


    if not found:


        print("\n✅ No active infections.")


    clear_line()




# ============================================================


# DEVICE PROTECTION


# ============================================================


def protect_device():
    # Increases protection on one device for a cost of £10.

    global funding


    print("\nWhich device would you like to protect?")


    names = list(devices.keys())


    choice = get_choice(

        "\nChoose a device:",

        options=[(name, str(index)) for index, name in enumerate(names, 1)],

    )


    if not choice.isdigit():


        print("❌ Invalid choice.")


        return


    choice = int(choice)


    if choice < 1 or choice > len(names):


        print("❌ Invalid choice.")


        return


    name = names[choice - 1]


    if funding < 10:


        print("❌ Not enough funding.")


        return


    funding -= 10


    devices[name]["protection"] += 10


    if devices[name]["protection"] > 100:


        devices[name]["protection"] = 100


    print(f"\n🛡️ {name} protection increased!")


    print("Protection:", devices[name]["protection"], "%")




# ============================================================


# ANTIVIRUS


# ============================================================


def buy_antivirus():
    # Adds antivirus to a device, slowing malware growth and reducing spread.

    global funding


    print("\nWhich device needs Antivirus?")


    names = list(devices.keys())


    choice = get_choice(

        "\nChoose a device:",

        options=[(name, str(index)) for index, name in enumerate(names, 1)],

    )


    if not choice.isdigit():


        return


    choice = int(choice)


    if choice < 1 or choice > len(names):


        return


    name = names[choice - 1]


    if devices[name]["antivirus"]:


        print("❌ Antivirus is already installed.")


        return


    if funding < 20:


        print("❌ Not enough funding.")


        return


    funding -= 20


    devices[name]["antivirus"] = True


    print(f"\n🛡️ Antivirus installed on {name}!")




# ============================================================


# PASSWORD SECURITY


# ============================================================


def buy_password_security():
    # Adds stronger password protection for a device to reduce infection risk.

    global funding


    print("\nWhich device needs stronger password security?")


    names = list(devices.keys())


    choice = get_choice(

        "\nChoose a device:",

        options=[(name, str(index)) for index, name in enumerate(names, 1)],

    )


    if not choice.isdigit():


        return


    choice = int(choice)


    if choice < 1 or choice > len(names):


        return


    name = names[choice - 1]


    if devices[name]["password"]:


        print("❌ Strong password security already active.")


        return


    if funding < 15:


        print("❌ Not enough funding.")


        return


    funding -= 15


    devices[name]["password"] = True


    print(f"\n🔐 Strong password security added to {name}!")




# ============================================================


# DATABASE UPGRADE


# ============================================================


def upgrade_database():
    # Raises the database level for extra defense and bonus income.

    global funding


    if database["level"] >= 5:


        print("\n❌ Database is already at maximum level.")


        return


    cost = database["level"] * 50


    print("\nDATABASE UPGRADE")


    print("Current Level:", database["level"])


    print("Upgrade Cost: £", cost)


    choice = get_choice("\nUpgrade database? (y/n): ")


    if choice.lower() != "y":


        return


    if funding < cost:


        print("❌ Not enough funding.")


        return


    funding -= cost


    database["level"] += 1


    database["protection"] += 15


    if database["protection"] > 75:


        database["protection"] = 75


    print("\n⬆️ Database upgraded!")


    print("New Level:", database["level"])


    print("Protection:", database["protection"], "%")




# ============================================================


# BACKUP DATABASE


# ============================================================


def backup_database():
    # Unlocks a one-time backup feature if the player reaches wave 5.

    global funding


    global backup_available


    global backup_used


    if wave < 5:


        print("\n🔒 Backup Database unlocks at Wave 5.")


        return


    if backup_used:


        print("\n❌ Backup Database has already been used.")


        return


    cost = 450


    print("\n💾 BACKUP DATABASE")


    print("Cost: £450")


    print("One use per game.")


    print("If the main database becomes critically infected,")


    print("the backup can restore it to 25% infection.")


    choice = get_choice("\nPurchase Backup Database? (y/n): ")


    if choice.lower() != "y":


        return


    if funding < cost:


        print("❌ Not enough funding.")


        return


    funding -= cost


    backup_available = True


    print("\n💾 Backup Database prepared!")




# ============================================================


# DEVICE RECOVERY


# ============================================================


def recover_device():
    # Recovers a fully compromised device and resets its security settings.

    global recoveries


    available = []


    for name, data in devices.items():


        if data["infection"] >= 100:


            available.append(name)


    if not available:


        print("\n❌ No fully compromised devices need recovery.")


        return


    if recoveries <= 0:


        print("\n❌ You have no recoveries remaining.")


        return


    print("\nCOMPROMISED DEVICES")


    choice = get_choice(

        "\nChoose device to recover:",

        options=[(name, str(index)) for index, name in enumerate(available, 1)],

    )


    if not choice.isdigit():


        return


    choice = int(choice)


    if choice < 1 or choice > len(available):


        return


    name = available[choice - 1]


    devices[name]["infection"] = 0


    devices[name]["protection"] = 0


    devices[name]["antivirus"] = False


    devices[name]["password"] = False


    recoveries -= 1


    print(f"\n🛠️ {name} has been recovered!")


    print("⚠️ All security upgrades on that device were lost.")


    print("Recoveries remaining:", recoveries)




# ============================================================


# INFRASTRUCTURE RECOVERY


# ============================================================


def recover_infrastructure():
    # Restores a badly infected infrastructure component to healthy state.

    global recoveries


    available = []


    for name, data in infrastructure.items():


        if data["infection"] >= 100:


            available.append(name)


    if not available:


        print("\n❌ No compromised infrastructure requires recovery.")


        return


    if recoveries <= 0:


        print("\n❌ No recoveries remaining.")


        return


    print("\nCOMPROMISED INFRASTRUCTURE")


    choice = get_choice(

        "\nChoose infrastructure to recover:",

        options=[(name, str(index)) for index, name in enumerate(available, 1)],

    )


    if not choice.isdigit():


        return


    choice = int(choice)


    if choice < 1 or choice > len(available):


        return


    name = available[choice - 1]


    infrastructure[name]["infection"] = 0


    infrastructure[name]["protection"] = 0


    recoveries -= 1


    print(f"\n🛠️ {name} has been recovered!")




# ============================================================


# PHISHING EMAIL


# ============================================================


def phishing_email():
    # Simulates a malicious email that may infect a random device if clicked.

    global recoveries


    print("\n" + "=" * 60)


    print("📧 NEW EMAIL")


    print("=" * 60)


    print("\nFrom: System Developers")


    print("Subject: IMPORTANT SECURITY UPDATE")


    print("\nYour account requires immediate verification.")


    print("Click the link below to continue.")


    while True:


        choice = get_choice(


            "\nChoose:",


            options=[("Open the email", "1"), ("Ignore/report the email", "2")],


        )


        if choice in ("1", "2"):


            break


        print("❌ Please choose 1 or 2.")


    if choice == "1":


        print("\n⚠️ PHISHING ATTACK!")


        print("The email was malicious.")


        target = random.choice(list(devices.keys()))


        threat = random.choice(["Virus", "Trojan Horse"])


        devices[target]["infection"] += 5


        devices[target]["infection"] = min(

            100, devices[target]["infection"]

        )


        print(f"\n🦠 {threat} detected on {target}!")


        print("Infection +5%.")


    elif choice == "2":


        recoveries += 1


        print("\n✅ Correct!")


        print("The email was phishing.")


        print("🛠️ +1 Recovery")




# ============================================================


# LEGITIMATE DEVELOPER EMAIL


# ============================================================


def legitimate_email():
    # Displays a harmless message with advice from the development team.

    print("\n" + "=" * 60)


    print("📧 DEVELOPER MESSAGE")


    print("=" * 60)


    print("\nFrom: Cyber Defence Development Team")


    print("Subject: Network Security Update")


    print("\nWe've been monitoring the current build.")


    print("Keep an eye on devices with rising infection levels.")


    print("\n💡 Developer Tip:")


    print("Don't put all of your funding into one device.")


    pause()




# ============================================================


# LIAM EMAIL


# ============================================================


def liam_email():
    # Gives the player a bonus of funding and recovery kits from Liam.

    global funding


    global recoveries


    print("\n" + "=" * 60)


    print("📧 OPERATIONS MESSAGE")


    print("=" * 60)


    print("\nFrom: Liam — Head of Operations")


    print("Subject: 🛡️ Operations Support")


    print("\nHey Commander,")


    print("\nI've been keeping an eye on how things are going.")


    print("I've authorised some additional resources for you.")


    funding += 50


    recoveries += 3


    print("\n🎁 +3 Recoveries")


    print("💰 +£50 Funding")


    print("\n💡 Tip from Operations:")


    print("Don't put everything into protecting one device.")


    print("A strong network means keeping everything covered.")


    print("\n— Liam")


    print("Head of Operations")


    pause()




# ============================================================


# WILL EMAIL


# ============================================================


def will_email():
    # Gives a small reward and player-friendly advice from the testing team.

    global recoveries


    print("\n" + "=" * 60)


    print("📧 TESTING REPORT")


    print("=" * 60)


    print("\nFrom: Will — Testing & Feedback")


    print("Subject: 🧪 Quick Testing Report")


    print("\nHey Commander,")


    print("\nI've been testing the current build.")


    print("Your network is starting to show some weaknesses.")


    recoveries += 1


    print("\n🛠️ +1 Recovery")


    print("\n💡 Tester Tip:")


    print("Just because an infection is low doesn't mean")


    print("you should completely ignore it.")


    print("\n— Will")


    print("Testing & Feedback")


    pause()




# ============================================================


# EMAIL SYSTEM


# ============================================================


def receive_email():
    # Randomly selects the next email event to add gameplay variety.

    roll = random.randint(1, 100)


    if roll <= 8:


        liam_email()


    elif roll <= 30:


        will_email()


    elif roll <= 50:


        legitimate_email()


    else:


        phishing_email()




# ============================================================


# DEVELOPER ASSISTANCE


# ============================================================


def developer_assistance():
    # Lets the player request guidance from Liam or Will, with limited usage.

    global liam_assistance


    global will_assistance


    global liam_advice_turns


    global will_advice_turns


    print("\n" + "=" * 60)


    print("🆘 DEVELOPER ASSISTANCE")


    print("=" * 60)


    choices = [("Liam - Head of Operations", "1")]


    if not liam_assistance:


        choices[0] = ("Liam - Head of Operations (already used)", "1")


    choices.append(("Will - Testing & Feedback", "2"))


    if not will_assistance:


        choices[1] = ("Will - Testing & Feedback (already used)", "2")


    choice = get_choice("\nChoose assistance:", options=choices)


    if choice == "1" and liam_assistance:


        liam_assistance = False


        liam_advice_turns = 3


        print("\n🛡️ LIAM'S ADVICE")


        print("\nFocus on your weakest devices first.")


        print("Don't overspend on a single device.")


        print("Keep some funding available for emergencies.")


        print("Your database becomes especially important later.")


    elif choice == "2" and will_assistance:


        will_assistance = False


        will_advice_turns = 3


        weakest = min(


            devices,


            key=lambda x: devices[x]["infection"]


        )


        print("\n🧪 WILL'S ADVICE")


        print("\nI'd keep an eye on:", weakest)


        print("Check your Current Threats regularly.")


        print("Small problems are easier to handle than major ones.")


    else:


        print("\n❌ Assistance unavailable.")




# ============================================================


# MALWARE ATTACK


# ============================================================


def malware_attack():
    # Spreads infections across devices and network infrastructure using the
    # current difficulty settings, protection values, and security upgrades.

    global active_threats


    settings = DIFFICULTY_SETTINGS[difficulty]


    active_threats = []


    for name, data in devices.items():


        if data["infection"] > 0:


            increase = settings["device_growth"]


            if data["antivirus"]:


                increase -= 3


            increase -= data["protection"] // 25


            if data["password"]:


                increase -= 1


            increase = max(1, increase)

            data["infection"] = min(100, data["infection"] + increase)


        else:


            infection_chance = settings["infection_chance"]


            infection_chance -= data["protection"] // 10


            if data["password"]:


                infection_chance -= 3


            infection_chance = max(3, infection_chance)


            chance = random.randint(1, 100)


            if chance <= infection_chance:


                data["infection"] = 5


                print("\n" + "!" * 60)


                print("⚠️ NEW MALWARE DETECTED!")


                print(f"🦠 A threat has appeared on {name}!")


                print("Infection: 5%")


                print("!" * 60)


                active_threats.append(name)


    # --------------------------------------------------------

    # INFRASTRUCTURE CHAIN

    # --------------------------------------------------------


    global restart_waves_remaining


    if restart_waves_remaining > 0:

        router_switch_growth = 3

        network_database_growth = 2

    else:

        router_switch_growth = settings["infrastructure_growth"]

        network_database_growth = settings["infrastructure_growth"]


    all_devices_infected = all(

        data["infection"] >= 100

        for data in devices.values()

    )


    if all_devices_infected:

        router = infrastructure["Router"]

        router["infection"] = min(

            100, router["infection"] + router_switch_growth

        )


    if infrastructure["Router"]["infection"] >= 100:

        switch = infrastructure["Switch"]

        switch["infection"] = min(

            100, switch["infection"] + router_switch_growth

        )


    if infrastructure["Switch"]["infection"] >= 100:

        network = infrastructure["Network"]

        network["infection"] = min(

            100, network["infection"] + network_database_growth

        )


    if infrastructure["Network"]["infection"] >= 100:

        database_increase = max(

            1, network_database_growth - database["protection"] // 20

        )

        database["infection"] = min(

            100, database["infection"] + database_increase

        )


    if restart_waves_remaining > 0:

        restart_waves_remaining -= 1

        if restart_waves_remaining == 0:

            print("\n⚠️ Emergency Network Restart protection has expired.")

        else:

            print("\n🛡️ Emergency restart protection: 1 wave remaining.")




# ============================================================


# FUNDING


# ============================================================


def generate_funding():
    # Adds passive income based on average device protection and database level.

    global funding


    total_protection = sum(


        data["protection"]


        for data in devices.values()


    )


    average_protection = total_protection / len(devices)


    device_income = int(average_protection / 10)


    database_income = database["level"] * 5


    funding += device_income + database_income


    if funding < 10:


        print("\n⚠️ EMERGENCY FUNDING")


        print("Your organisation has exhausted its available funds.")


        print("Emergency support has been authorised.")


        print("💰 +£10 Funding")


        funding += 10




# ============================================================


# DATABASE GAME OVER / BACKUP


# ============================================================


def emergency_network_restart():
    # Gives a one-time emergency reset for the infrastructure and database.

    global restart_available

    global restart_waves_remaining


    if not restart_available:

        return False


    print("\n" + "🚨" * 20)

    print("        EMERGENCY NETWORK RESTART")

    print("🚨" * 20)

    print("\nThe Database has reached 100% infection.")

    print("The Emergency Network Restart can save the network once.")

    print("\nThis will reset:")

    print("• Router infection → 0%")

    print("• Switch infection → 0%")

    print("• Network infection → 0%")

    print("• Database infection → 0%")

    print("• Reduced infrastructure growth for the next 2 waves.")

    print("• Your current wave and device progress stay intact.")


    choice = get_choice("\nActivate Emergency Network Restart? (y/n): ")

    if choice.lower() != "y":

        print("\n❌ Emergency Network Restart declined.")

        return False


    infrastructure["Router"]["infection"] = 0

    infrastructure["Switch"]["infection"] = 0

    infrastructure["Network"]["infection"] = 0

    database["infection"] = 0

    restart_available = False

    restart_waves_remaining = 2


    print("\n🛡️ EMERGENCY NETWORK RESTART ACTIVATED!")

    print("Router: 0%")

    print("Switch: 0%")

    print("Network: 0%")

    print("Database: 0%")

    print(f"\n🌊 You remain on Wave {wave}.")

    print("⚡ Reduced infrastructure growth will last for the next 2 waves.")

    return True




def check_database():
    # Checks whether the database infection has reached 100% and triggers the
    # backup or game-over flow if necessary.

    global backup_used


    if database["infection"] < 100:

        return False


    print("\n" + "☠️" * 20)

    print("             DATABASE COMPROMISED")

    print("☠️" * 20)


    if backup_available and not backup_used:

        print("\n💾 BACKUP DATABASE AVAILABLE")

        choice = get_choice("\nActivate Backup Database? (y/n): ")

        if choice.lower() == "y":

            database["infection"] = 25

            backup_used = True

            print("\n💾 BACKUP ACTIVATED!")

            print("Database restored to 25% infection.")

            return False


    if restart_available and emergency_network_restart():

        return False


    print("\n❌ GAME OVER")

    print("Your database has been completely compromised.")

    return True


LEADERBOARD_PATH = Path(__file__).with_name("leaderboard.json")


def record_leaderboard_score():
    # Saves the player's score at the end of the run in a JSON leaderboard.

    score = max(0, wave - 1)

    name = input("\nEnter your name for the leaderboard: ").strip()

    if not name:

        name = "Commander"


    try:

        contents = LEADERBOARD_PATH.read_text(encoding="utf-8")

    except FileNotFoundError:

        leaderboards = {level: [] for level in DIFFICULTY_SETTINGS}

    except OSError:

        print("\n⚠️ The leaderboard could not be read or saved.")

        return

    else:

        try:

            leaderboard = json.loads(contents)

        except json.JSONDecodeError:

            print("\n⚠️ The leaderboard file is invalid; your score was not saved.")

            return


        if isinstance(leaderboard, list):

            legacy_scores = leaderboard

            leaderboards = {level: [] for level in DIFFICULTY_SETTINGS}

            leaderboards["Normal"] = [

                entry

                for entry in legacy_scores

                if isinstance(entry, dict)

                and isinstance(entry.get("name"), str)

                and isinstance(entry.get("waves"), int)

            ]

        elif isinstance(leaderboard, dict):

            leaderboards = {}

            for level in DIFFICULTY_SETTINGS:

                entries = leaderboard.get(level, [])

                if not isinstance(entries, list):

                    entries = []

                leaderboards[level] = [

                    entry

                    for entry in entries

                    if isinstance(entry, dict)

                    and isinstance(entry.get("name"), str)

                    and isinstance(entry.get("waves"), int)

                ]

        else:

            print("\n⚠️ The leaderboard file is invalid; your score was not saved.")

            return


    leaderboard = leaderboards[difficulty]

    leaderboard.append({"name": name, "waves": score})

    leaderboard.sort(key=lambda entry: entry["waves"], reverse=True)

    leaderboard = leaderboard[:10]

    leaderboards[difficulty] = leaderboard


    try:

        LEADERBOARD_PATH.write_text(

            json.dumps(leaderboards, indent=2) + "\n",

            encoding="utf-8",

        )

    except OSError:

        print("\n⚠️ Your score could not be saved to the leaderboard.")


    clear_line()

    print(f"             {difficulty.upper()} LEADERBOARD")

    clear_line()

    for position, entry in enumerate(leaderboard, start=1):

        print(f"{position}. {entry['name']} - {entry['waves']} waves")




# ============================================================


# WAVE 1 TUTORIAL


# ============================================================


def tutorial_wave():
    # Shows a beginner walkthrough explaining infection, protection, and funding.

    global funding


    global wave


    global tutorial_complete


    clear_line()


    print("        🛡️ CYBER DEFENCE")


    print("             WAVE 1")


    clear_line()


    print("\nWelcome, Commander!")


    print("\nYou are responsible for protecting your")


    print("organisation from cyber attacks.")


    pause()


    # --------------------------------------------------------


    # OBJECTIVE


    # --------------------------------------------------------


    clear_line()


    print("                  OBJECTIVE")


    clear_line()


    print("\nYour job is simple:")


    print("Keep your network running for as long as possible.")


    print("\nCyber threats will try to infect your devices.")


    print("You must spend your funding wisely to protect them.")


    pause()


    # --------------------------------------------------------


    # NETWORK


    # --------------------------------------------------------


    clear_line()


    print("               YOUR NETWORK")


    clear_line()


    print("\nYour network contains several devices.")


    print("\nFor now, we're only going to worry about one:")


    print("\n💻 PC")


    print("\nDon't worry about the rest yet.")


    print("You'll learn about more parts of the network later.")


    pause()


    # --------------------------------------------------------


    # FIRST ATTACK


    # --------------------------------------------------------


    clear_line()


    print("                 ⚠️ WARNING")


    clear_line()


    print("\n🚨 MALWARE DETECTED!")


    print("\nA Virus has appeared on your PC.")


    devices["PC"]["infection"] = 5


    print("\n💻 PC Infection: 5%")


    print("\nThis means malware has started spreading.")


    print("If infection reaches 100%, the device is compromised.")


    pause()


    # --------------------------------------------------------


    # PROTECTION


    # --------------------------------------------------------


    clear_line()


    print("             🛡️ PROTECT YOUR PC")


    clear_line()


    print("\nYou can spend funding to protect your devices.")


    print("\n💰 Protect PC: £10")


    print("🛡️ Protection gained: +10%")


    while True:


        print("\nWhat would you like to do?")


        choice = get_choice(

            "\nChoose an option:",

            options=[("Protect the PC", "1"), ("Leave it alone", "2")],

        )


        if choice == "1":


            if funding >= 10:


                funding -= 10


                devices["PC"]["protection"] += 10


                print("\n🛡️ PC protected!")


                print(


                    "Protection:",


                    devices["PC"]["protection"],


                    "%"


                )


                print("Funding remaining: £", funding)


                break


            else:


                print("\n❌ You don't have enough funding.")


        elif choice == "2":


            print("\n⚠️ Leaving the PC unprotected is risky.")


            print("For this tutorial, let's protect it first.")


        else:


            print("\n❌ Please choose 1 or 2.")


    pause()


    # --------------------------------------------------------


    # FUNDING


    # --------------------------------------------------------


    clear_line()


    print("                  💰 FUNDING")


    clear_line()


    print("\nFunding is your main resource.")


    print("\nYou use it to:")


    print("• Protect devices")


    print("• Buy security upgrades")


    print("• Recover from attacks")


    print("• Strengthen your network")


    print("\nSpend carefully.")


    print("You won't have unlimited money.")


    pause()


    # --------------------------------------------------------


    # COMPLETE WAVE


    # --------------------------------------------------------


    clear_line()


    print("             WAVE 1 COMPLETE")


    clear_line()


    print("\nThe Virus is still spreading...")


    devices["PC"]["infection"] = 9


    print("\n💻 PC Infection: 9%")


    print(


        "🛡️ PC Protection:",


        devices["PC"]["protection"],


        "%"


    )


    print("\nYour protection has slowed the infection.")


    pause()


    # --------------------------------------------------------


    # COMPLETE


    # --------------------------------------------------------


    clear_line()


    print("          🎉 TUTORIAL COMPLETE")


    clear_line()


    print("\nYou've learned the basics:")


    print("✅ What infection means")


    print("✅ How to protect a device")


    print("✅ How funding works")


    print("✅ Why you need to react to threats")


    print("\nFrom Wave 2 onwards, things become")


    print("less predictable.")


    print("\nYou'll start encountering more threats")


    print("and more decisions.")


    tutorial_complete = True


    pause()




# ============================================================


# HOW TO PLAY


# ============================================================


def how_to_play():
    # Explains the basic loop of the game before the player starts playing.

    clear_line()


    print("                  HOW TO PLAY")


    clear_line()


    print("""


Your objective is to keep the network running.


Each wave:


1. Check your network.


2. Check Current Threats.


3. Decide where to spend funding.


4. Protect devices.


5. Respond to malware.


6. Recover compromised devices.


7. Keep the Database alive.


If the Database reaches 100% infection,


you may be able to use the Backup Database


or the one-time Emergency Network Restart.


If neither is available, the game ends.


The further you survive, the better your result.


""")


    pause()




# ============================================================


# UPGRADES MENU


# ============================================================


def upgrades_menu():
    # Main shop menu where the player can spend funding on device upgrades,
    # recovery tools, and database improvements.

    while True:


        clear_line()


        print(arcade_text("[ POWER-UPS & UPGRADES ]", "yellow", bold=True))


        clear_line()


        choice = get_choice(

            "\nChoose an upgrade:",

            options=[

                ("Protect | £10 | +10% device protection", "1"),

                ("Antivirus | £20 | up to -3% growth/wave", "2"),

                (

                    "Password | £15 | -3% infection chance, up to -1% growth",

                    "3",

                ),

                (

                    "Database | level x £50 | +15% defense, +£5 income/wave",

                    "4",

                ),

                (

                    "Backup | £450 at Wave 5 | one-time restore to 25%",

                    "5",

                ),

                ("Recover Device", "6"),

                ("Recover Infrastructure", "7"),

                ("Return", "8"),

            ],

        )


        if choice == "1":


            protect_device()


        elif choice == "2":


            buy_antivirus()


        elif choice == "3":


            buy_password_security()


        elif choice == "4":


            upgrade_database()


        elif choice == "5":


            backup_database()


        elif choice == "6":


            recover_device()


        elif choice == "7":


            recover_infrastructure()


        elif choice == "8":


            break


        else:


            print("❌ Invalid choice.")




# ============================================================


# MAIN GAME TURN


# ============================================================


def play_wave():
    # Runs one full game turn: player chooses actions, malware triggers, email
    # events may happen, and funding is generated for the next wave.

    global wave


    global liam_advice_turns


    global will_advice_turns


    clear_line()


    show_wave_dashboard()


    clear_line()


    print("\nWhat would you like to do?")


    while True:


        choice = get_choice(

            "\nSelect action:",

            options=[

                ("Check network health", "1"),

                ("See current threats", "2"),

                ("Choose an upgrade", "3"),

                ("Get a helpful hint", "4"),

                ("Start the next attack", "5"),

            ],

        )


        if choice == "1":


            show_status()


        elif choice == "2":


            show_threats()


        elif choice == "3":


            upgrades_menu()


        elif choice == "4":


            developer_assistance()


        elif choice == "5":


            break


        else:


            print("❌ Invalid choice.")


    # --------------------------------------------------------


    # ATTACK


    # --------------------------------------------------------


    print("\n⚠️ The network is being attacked...")


    if not trigger_trojan_attack():

        malware_attack()


    # --------------------------------------------------------


    # EMAIL


    # --------------------------------------------------------


    email_chance = random.randint(1, 100)


    if email_chance <= 25:


        receive_email()


    # --------------------------------------------------------


    # ADVICE TIMERS


    # --------------------------------------------------------


    if liam_advice_turns > 0:


        liam_advice_turns -= 1


    if will_advice_turns > 0:


        will_advice_turns -= 1


    # --------------------------------------------------------


    # FUNDING


    # --------------------------------------------------------


    generate_funding()


    print("\n💰 Funding after wave:", funding)


    # --------------------------------------------------------


    # DATABASE


    # --------------------------------------------------------


    if check_database():


        return False


    wave += 1


    return True


# ============================================================


# TROJAN HORSE ANTI-SKIP EVENT


# ============================================================


def trojan_defence_snapshot():
    # Captures the important game values so the anti-skip Trojan event can
    # detect whether the player took a defensive action.

    """Return game values used to detect a successful defensive action."""

    return (

        funding,

        recoveries,

        repr(devices),

        repr(infrastructure),

        repr(database),

        restart_available,

        backup_used,

    )




def handle_trojan_defence():
    # Resets or cancels the Trojan event when the player performs a valid
    # defensive action such as upgrading or recovering systems.

    """A successful upgrade/recovery resets skips or cancels the event."""

    global trojan_event_state, consecutive_skips


    if trojan_event_state == "ready":

        consecutive_skips = 0

    elif trojan_event_state in ("warning", "escalation"):

        print("\nDefensive action detected.")

        if trojan_event_state == "warning":

            print("The Trojan Horse attack has been prevented.")

        else:

            print("The Trojan Horse's follow-up attack has been stopped.")

        trojan_event_state = "finished"

        consecutive_skips = 0




def trigger_trojan_attack():
    # Applies the next anti-skip strike from the Trojan event if the player has
    # been repeating the same choice too often.

    """Apply the next anti-skip strike and return whether growth is paused."""

    global trojan_event_state, trojan_used


    if trojan_event_state == "warning":

        database["infection"] = min(100, database["infection"] + 50)

        trojan_event_state = "escalation"


        print("\n" + "!" * 60)

        print("TROJAN HORSE ATTACK — FIRST STRIKE")

        print("!" * 60)

        print("The Trojan Horse has infiltrated the database.")

        print(f"Database infection: {database['infection']}%")

        print("Defend your network before the next wave to stop escalation.")

        print("Normal malware growth is suppressed during this strike.")

        return True


    if trojan_event_state == "escalation":

        database["infection"] = min(100, database["infection"] + 25)

        infrastructure["Router"]["infection"] = min(

            100, infrastructure["Router"]["infection"] + 25

        )

        infrastructure["Switch"]["infection"] = min(

            100, infrastructure["Switch"]["infection"] + 25

        )

        trojan_event_state = "finished"


        print("\n" + "!" * 60)

        print("TROJAN HORSE ATTACK — FINAL STRIKE")

        print("!" * 60)

        print("The Trojan Horse has spread through the infrastructure.")

        print(f"Database infection: {database['infection']}%")

        print(f"Router infection: {infrastructure['Router']['infection']}%")

        print(f"Switch infection: {infrastructure['Switch']['infection']}%")

        print("Normal malware growth is suppressed during this strike.")

        return True


    return False




# ============================================================


# MAIN GAME


# ============================================================


def main_game():
    # Runs the main loop after the tutorial, continuing each wave until defeat.

    global wave


    # Wave 1 has already been completed by the tutorial.


    wave = 2


    while True:


        if not play_wave():


            break


        clear_line()


        print("             WAVE COMPLETE")


        clear_line()


        print("\nYou survived the wave!")


        print("\nPrepare for the next attack...")


        pause()


    record_leaderboard_score()




# ============================================================


# START MENU


# ============================================================


def start_game():
    # Starts the title menu and lets the player choose to play, read the guide,
    # exit, or change the difficulty.

    global difficulty


    while True:


        clear_line()


        print(arcade_text("★ CYBER DEFENDER ★", "magenta", bold=True))


        clear_line()


        choice = get_choice(

            "\nChoose:",

            options=[

                ("Play", "1"),

                ("How to Play", "2"),

                ("Exit", "3"),

                (f"Difficulty: {difficulty}", "4"),

            ],

        )


        if choice == "1":


            tutorial_wave()


            main_game()


            break


        elif choice == "2":


            how_to_play()


        elif choice == "3":


            print("\nGoodbye, Commander!")


            break


        elif choice == "4":


            difficulty = get_choice(

                "\nChoose difficulty:",

                options=[(level, level) for level in DIFFICULTY_SETTINGS],

            )


        else:


            print("\n❌ Invalid choice.")




# ============================================================


# START


# ============================================================


start_game()

