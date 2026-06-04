import os
import re
import sys
import ctypes
import tkinter as tk
from tkinter import messagebox

APP_NAME = "OwO Boss Command Generator"
CREDIT_TEXT = "Made by Hassaan"
DEFAULT_HP = "80000"
ICON_FILE = "owo-boss.ico"

try:
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("hassaan.owo.boss.generator")
except Exception:
    pass


def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)


WEAPON_MAP = {
    "great sword": "sword", "greatsword": "sword", "sword": "sword", "gsword": "sword",
    "healing staff": "hstaff", "heal staff": "hstaff", "healstaff": "hstaff", "hstaff": "hstaff",
    "bow": "bow",
    "rune of the forgotten": "rune", "forgotten rune": "rune", "rune": "rune",
    "defender s aegis": "shield", "defenders aegis": "shield", "defender aegis": "shield", "aegis": "shield", "shield": "shield",
    "orb of potency": "orb", "potency orb": "orb", "orb": "orb",
    "vampiric staff": "vstaff", "vampire staff": "vstaff", "vamp staff": "vstaff", "vampstaff": "vstaff", "vstaff": "vstaff",
    "poison dagger": "pd", "poisoned dagger": "pd", "dagger": "pd", "pdagger": "pd", "pdag": "pd", "pd": "pd",
    "wand of absorption": "wand", "absorption wand": "wand", "arcane wand": "wand", "wand": "wand", "awand": "wand",
    "flame staff": "fstaff", "fire staff": "fstaff", "staff of flames": "fstaff", "staff of flame": "fstaff", "fstaff": "fstaff",
    "energy staff": "estaff", "earth staff": "estaff", "estaff": "estaff",
    "spirit staff": "sstaff", "snow staff": "sstaff", "sstaff": "sstaff",
    "arcane scepter": "ascept", "arcane sceptre": "ascept", "scepter": "ascept", "sceptre": "ascept", "arcane": "ascept", "ascept": "ascept",
    "resurrection staff": "rstaff", "res staff": "rstaff", "revive staff": "rstaff", "rstaff": "rstaff",
    "glacial axe": "axe", "ice axe": "axe", "guardian axe": "axe", "axe": "axe", "gaxe": "axe",
    "vanguard s banner": "vban", "vanguards banner": "vban", "vanguard banner": "vban", "banner": "vban", "vban": "vban",
    "culling scythe": "sythe", "celestial scythe": "sythe", "scythe": "sythe", "sythe": "sythe", "csyth": "sythe", "csy": "sythe",
    "rune of celebration": "crune", "celebration rune": "crune", "celestial rune": "crune", "crune": "crune", "cel": "crune",
    "staff of purity": "pstaff", "purity staff": "pstaff", "poison staff": "pstaff", "pstaff": "pstaff",
    "leeching scythe": "lsy", "leech scythe": "lsy", "life scythe": "lsy", "lsyth": "lsy", "lsy": "lsy", "lscythe": "lsy",
    "foul fish": "ffish", "fishing rod": "ffish", "fish": "ffish", "ffish": "ffish",
    "rune of luck": "lrune", "luck rune": "lrune", "lunar rune": "lrune", "lrune": "lrune",
    "staff of corruption": "cstaff", "corruption staff": "cstaff", "curse staff": "cstaff", "cstaff": "cstaff",
    "soul tithe": "soul", "tithe": "soul", "soul": "soul", "stithe": "soul",
    "briar heart staff": "bhstaff", "briarheart staff": "bhstaff", "briar staff": "bhstaff", "blood heal staff": "bhstaff", "bhstaff": "bhstaff",
    "arbiter s edge": "aedge", "arbiters edge": "aedge", "arbiter edge": "aedge", "abyssal edge": "aedge", "edge": "aedge", "aedge": "aedge",
    "wounding crossbow": "woundb", "wound crossbow": "woundb", "wounding bow": "woundb", "wound bow": "woundb", "crossbow": "woundb", "wbow": "woundb", "wcbow": "woundb", "xbow": "woundb", "woundb": "woundb",
    "bleeding gaze": "bgaz", "blood gaze": "bgaz", "basilisk gaze": "bgaz", "gaze": "bgaz", "bgaze": "bgaz", "bgaz": "bgaz",
    "conduit claw": "cclaw", "celestial claw": "cclaw", "claw": "cclaw", "cclaw": "cclaw",
}

PASSIVE_MAP = {
    "strength": "str", "attack": "str", "str": "str", "att": "str",
    "magic": "mag", "mag": "mag",
    "health": "hp", "health point": "hp", "health points": "hp", "hp": "hp",
    "weapon point": "wp", "weapon points": "wp", "wp": "wp",
    "physical resistance": "pr", "pr": "pr",
    "magic resistance": "mr", "magical resistance": "mr", "mr": "mr",
    "lifesteal": "ls", "life steal": "ls", "ls": "ls",
    "thorns": "th", "thorn": "th", "th": "th",
    "mana tap": "mtap", "manatap": "mtap", "mtap": "mtap",
    "absolve": "absv", "absv": "absv",
    "safeguard": "sg", "sg": "sg",
    "critical": "crit", "crit": "crit",
    "discharge": "dc", "dc": "dc",
    "kamikaze": "kk", "kkaze": "kk", "kk": "kk",
    "regeneration": "hgen", "regen": "hgen", "hgen": "hgen",
    "energize": "wgen", "energy": "wgen", "wgen": "wgen",
    "sprout": "sprout", "sprt": "sprout",
    "enrage": "enrage", "enra": "enrage",
    "sacrifice": "sac", "sac": "sac",
    "snail": "snail",
    "knowledge": "kno", "kno": "kno",
    "giant slayer": "slay", "slayer": "slay", "slay": "slay", "gslay": "slay",
    "adaptation": "adapt", "adapt": "adapt",
    "resonance": "res", "reso": "res", "res": "res",
    "living hive": "swarm", "swarm": "swarm", "hive": "swarm", "lhive": "swarm",
    "lone wolf": "lwolf", "wolf": "lwolf", "lwolf": "lwolf",
    "double strike": "dstrike", "defensive strike": "dstrike", "dstrike": "dstrike", "strike": "dstrike", "ds": "dstrike",
    "frost armor": "frarm", "frost armour": "frarm", "armor": "frarm", "armour": "frarm", "frarm": "frarm",
}

RARITIES = {
    "common", "uncommon", "rare", "epic", "mythical", "legendary",
    "fabled", "hidden", "special", "patreon", "gem", "bot", "distorted",
}

REMOVE_WORDS = {
    "pristine", "fine", "decent", "worn", "unknown", "empowered", "unempowered",
    "used", "new", "old", "broken", "damaged", "poor", "good", "excellent", "perfect",
}

THEMES = {
    "dark": {
        "BG": "#10151f",
        "PANEL": "#161d2a",
        "PANEL_2": "#1d2636",
        "TEXT": "#eef3ff",
        "MUTED": "#aab6cc",
        "ACCENT": "#7c5cff",
        "ACCENT_HOVER": "#9278ff",
        "GREEN": "#5ee6a8",
        "DANGER": "#ff6b6b",
        "BORDER": "#2a3447",
        "INPUT_BG": "#0d111a",
    },
    "light": {
        "BG": "#f3f5fb",
        "PANEL": "#ffffff",
        "PANEL_2": "#e9edf7",
        "TEXT": "#151a26",
        "MUTED": "#566174",
        "ACCENT": "#6246ea",
        "ACCENT_HOVER": "#725cff",
        "GREEN": "#138a55",
        "DANGER": "#c0392b",
        "BORDER": "#d8deea",
        "INPUT_BG": "#f8faff",
    },
}

current_theme = "dark"


def C(key):
    return THEMES[current_theme][key]


def normalize_name(value):
    value = value.lower().strip()
    value = re.sub(r"<:[^>]+>", " ", value)
    value = value.replace("’", "'").replace("`", "")
    value = re.sub(r"['’]", " ", value)
    value = re.sub(r"[^a-z0-9\s-]", " ", value)
    value = value.replace("-", " ")
    value = re.sub(r"\s+", " ", value).strip()
    return value


def clean_weapon_name(raw):
    cleaned = normalize_name(raw)

    cleaned = re.sub(r"\bquality\b.*", "", cleaned).strip()
    cleaned = re.sub(r"\bwear\b.*", "", cleaned).strip()
    cleaned = re.sub(r"\btype\b.*", "", cleaned).strip()
    cleaned = re.sub(r"\bkills\b.*", "", cleaned).strip()
    cleaned = re.sub(r"\bweapon cost\b.*", "", cleaned).strip()

    words = cleaned.split()
    words = [word for word in words if word not in RARITIES and word not in REMOVE_WORDS]
    name = " ".join(words).strip()

    if name in WEAPON_MAP:
        return WEAPON_MAP[name], None

    fallback = name.replace(" ", "")
    warning = f"Unknown weapon: '{raw.strip()}' cleaned as '{name}', fallback used: '{fallback}'"
    return fallback, warning


def split_boss_blocks(text):
    text = text.strip()
    matches = list(re.finditer(r"##\s*Lvl\s*\d+", text, flags=re.I))

    if not matches:
        return []

    blocks = []

    for index, match in enumerate(matches):
        start = match.start()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        blocks.append(text[start:end].strip())

    return blocks


def parse_boss(block):
    compact = " ".join(block.split())
    warnings = []

    header = re.search(
        r"##\s*Lvl\s*(\d+)\s+\w+\s+(.+?)(?=<:|###|-#|\*\*|$)",
        compact,
        re.I
    )

    if not header:
        raise ValueError("Could not find boss level/name.")

    level = header.group(1)
    animal = header.group(2).strip().lower()

    weapon_match = re.search(
        r"###\s+(?!__Description__)(.+?)(?=\*\*Quality:\*\*|\*\*Wear:\*\*|\*\*Type:\*\*|\*\*Kills:\*\*|###\s+__Description__|$)",
        compact,
        re.I
    )

    if not weapon_match:
        raise ValueError(f"Could not find weapon for {level} {animal}.")

    weapon, weapon_warning = clean_weapon_name(weapon_match.group(1))

    if weapon_warning:
        warnings.append(weapon_warning)

    quality_match = re.search(r"\*\*Quality:\*\*.*?([\d.]+)%", compact, re.I)
    quality = float(quality_match.group(1)) if quality_match else 55.0

    passives = []
    found_titles = re.findall(r"\*\*__([^_]+)__\*\*", compact)

    for title in found_titles:
        key = normalize_name(title)

        if key in PASSIVE_MAP:
            short = PASSIVE_MAP[key]
            passives.append(short)

    passive_text = " " + " ".join(passives) if passives else ""

    return {
        "part": f"{level} {animal} {weapon}{passive_text}",
        "quality": quality,
        "warnings": warnings,
    }


def normalize_hp(value):
    value = value.strip().lower().replace(",", "")

    if not value:
        return DEFAULT_HP

    if value.endswith("k"):
        number = value[:-1].strip()

        if not number:
            return DEFAULT_HP

        return str(int(float(number) * 1000))

    return value


def get_state():
    state = {
        "boss1": "",
        "boss2": "",
        "boss3": "",
        "hp1": "",
        "hp2": "",
        "hp3": "",
        "output": "",
        "warnings": "",
        "status": "Ready.",
    }

    for name in state:
        widget_name = {
            "boss1": "boss1_text",
            "boss2": "boss2_text",
            "boss3": "boss3_text",
            "hp1": "hp1_entry",
            "hp2": "hp2_entry",
            "hp3": "hp3_entry",
            "output": "output_text",
            "warnings": "warnings_text",
        }.get(name)

        if widget_name and widget_name in globals():
            widget = globals()[widget_name]
            try:
                if isinstance(widget, tk.Text):
                    state[name] = widget.get("1.0", tk.END).strip()
                elif isinstance(widget, tk.Entry):
                    state[name] = widget.get().strip()
            except Exception:
                pass

    return state


def get_boss_inputs():
    texts = [
        boss1_text.get("1.0", tk.END).strip(),
        boss2_text.get("1.0", tk.END).strip(),
        boss3_text.get("1.0", tk.END).strip(),
    ]

    boss_blocks = []

    for text in texts:
        blocks = split_boss_blocks(text)
        boss_blocks.extend(blocks)

    if len(boss_blocks) != 3:
        raise ValueError(
            f"Expected exactly 3 bosses, but found {len(boss_blocks)}.\n\n"
            "Paste one boss into each box."
        )

    return boss_blocks


def generate_command():
    try:
        boss_blocks = get_boss_inputs()
        bosses = [parse_boss(block) for block in boss_blocks]

        hp_values = [
            normalize_hp(hp1_entry.get()),
            normalize_hp(hp2_entry.get()),
            normalize_hp(hp3_entry.get()),
        ]

        qe = round(sum(boss["quality"] for boss in bosses) / 3)

        command = "neon b myself vs "
        command += ", ".join(boss["part"] for boss in bosses)
        command += " -hp " + " ".join(hp_values)
        command += f" -m -qe{qe}"

        output_text.delete("1.0", tk.END)
        output_text.insert(tk.END, command)

        all_warnings = []
        for boss in bosses:
            all_warnings.extend(boss["warnings"])

        warnings_text.delete("1.0", tk.END)

        if all_warnings:
            warnings_text.insert(tk.END, "\n".join(all_warnings))
            status_label.config(text="Generated with warnings.", fg=C("DANGER"))
        else:
            warnings_text.insert(tk.END, "No warnings. Everything matched cleanly.")
            status_label.config(text="Command generated and copied.", fg=C("GREEN"))

        root.clipboard_clear()
        root.clipboard_append(command)

    except Exception as error:
        status_label.config(text="Could not generate command.", fg=C("DANGER"))
        messagebox.showerror("Error", str(error))


def copy_output():
    command = output_text.get("1.0", tk.END).strip()

    if not command:
        messagebox.showinfo("Nothing to copy", "Generate a command first.")
        return

    root.clipboard_clear()
    root.clipboard_append(command)
    status_label.config(text="Command copied.", fg=C("GREEN"))


def clear_all():
    for box in [boss1_text, boss2_text, boss3_text, output_text, warnings_text]:
        box.delete("1.0", tk.END)

    for entry in [hp1_entry, hp2_entry, hp3_entry]:
        entry.delete(0, tk.END)

    warnings_text.insert(tk.END, "No command generated yet.")
    status_label.config(text="Cleared. Ready.", fg=C("MUTED"))


def toggle_theme():
    global current_theme

    state = get_state()
    current_theme = "light" if current_theme == "dark" else "dark"
    build_ui(state)


def style_textbox(textbox, height=5):
    textbox.configure(
        height=height,
        bg=C("INPUT_BG"),
        fg=C("TEXT"),
        insertbackground=C("TEXT"),
        selectbackground=C("ACCENT"),
        selectforeground="#ffffff",
        relief="flat",
        borderwidth=0,
        padx=8,
        pady=6,
        font=("Consolas", 9),
        wrap="word"
    )


def make_button(parent, text, command, bg_key="ACCENT", padx=12, pady=6):
    return tk.Button(
        parent,
        text=text,
        command=command,
        bg=C(bg_key),
        fg="#ffffff" if bg_key == "ACCENT" else C("TEXT"),
        activebackground=C("ACCENT_HOVER"),
        activeforeground="#ffffff",
        relief="flat",
        borderwidth=0,
        padx=padx,
        pady=pady,
        cursor="hand2",
        font=("Arial", 9, "bold")
    )


def create_boss_section(parent, title, helper_text, next_label, next_action):
    frame = tk.Frame(parent, bg=C("PANEL"), highlightbackground=C("BORDER"), highlightthickness=1)
    frame.pack(fill="x", pady=6)

    header = tk.Frame(frame, bg=C("PANEL"))
    header.pack(fill="x", padx=10, pady=(8, 2))

    title_label = tk.Label(header, text=title, bg=C("PANEL"), fg=C("TEXT"), font=("Arial", 11, "bold"))
    title_label.pack(side="left")

    helper_label = tk.Label(
        frame,
        text=helper_text,
        bg=C("PANEL"),
        fg=C("MUTED"),
        font=("Arial", 8),
        anchor="w"
    )
    helper_label.pack(fill="x", padx=10, pady=(0, 5))

    text_frame = tk.Frame(frame, bg=C("INPUT_BG"))
    text_frame.pack(fill="x", padx=10, pady=(0, 8))

    text_box = tk.Text(text_frame)
    style_textbox(text_box, height=5)
    text_box.pack(side="left", fill="both", expand=True)

    scrollbar = tk.Scrollbar(text_frame, command=text_box.yview)
    scrollbar.pack(side="right", fill="y")
    text_box.configure(yscrollcommand=scrollbar.set)

    actions = tk.Frame(frame, bg=C("PANEL"))
    actions.pack(fill="x", padx=10, pady=(0, 8))

    clear_btn = make_button(actions, "Clear Box", lambda: text_box.delete("1.0", tk.END), bg_key="PANEL_2")
    clear_btn.pack(side="left")

    next_btn = make_button(actions, next_label, next_action, bg_key="ACCENT")
    next_btn.pack(side="right")

    return text_box


def make_hp_entry(parent, label, col):
    tk.Label(parent, text=label, bg=C("PANEL"), fg=C("TEXT"), font=("Arial", 9, "bold")).grid(
        row=2, column=col, padx=(10, 5), pady=(0, 10), sticky="w"
    )

    entry = tk.Entry(
        parent,
        width=14,
        bg=C("INPUT_BG"),
        fg=C("TEXT"),
        insertbackground=C("TEXT"),
        relief="flat",
        font=("Consolas", 10)
    )
    entry.grid(row=2, column=col + 1, padx=(0, 10), pady=(0, 10), ipady=5)

    return entry


def build_ui(state=None):
    global canvas, scrollable_frame
    global boss1_text, boss2_text, boss3_text
    global hp1_entry, hp2_entry, hp3_entry
    global output_text, warnings_text, status_label

    if state is None:
        state = {
            "boss1": "",
            "boss2": "",
            "boss3": "",
            "hp1": "",
            "hp2": "",
            "hp3": "",
            "output": "",
            "warnings": "No command generated yet.",
        }

    for child in root.winfo_children():
        child.destroy()

    root.configure(bg=C("BG"))

    container = tk.Frame(root, bg=C("BG"))
    container.pack(fill="both", expand=True)

    canvas = tk.Canvas(container, bg=C("BG"), highlightthickness=0)
    scrollbar = tk.Scrollbar(container, orient="vertical", command=canvas.yview)
    canvas.configure(yscrollcommand=scrollbar.set)

    scrollbar.pack(side="right", fill="y")
    canvas.pack(side="left", fill="both", expand=True)

    scrollable_frame = tk.Frame(canvas, bg=C("BG"))
    canvas_window = canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")

    def on_frame_configure(event):
        canvas.configure(scrollregion=canvas.bbox("all"))

    def on_canvas_configure(event):
        canvas.itemconfig(canvas_window, width=event.width)

    scrollable_frame.bind("<Configure>", on_frame_configure)
    canvas.bind("<Configure>", on_canvas_configure)

    def on_mousewheel(event):
        canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    canvas.bind_all("<MouseWheel>", on_mousewheel)

    top = tk.Frame(scrollable_frame, bg=C("BG"))
    top.pack(fill="x", padx=16, pady=(12, 6))

    title_label = tk.Label(top, text=APP_NAME, bg=C("BG"), fg=C("TEXT"), font=("Arial", 18, "bold"))
    title_label.pack(anchor="w")

    credit_label = tk.Label(top, text=CREDIT_TEXT, bg=C("BG"), fg=C("MUTED"), font=("Arial", 9))
    credit_label.pack(anchor="w", pady=(1, 0))

    theme_btn = make_button(top, "Switch to Light Mode" if current_theme == "dark" else "Switch to Dark Mode", toggle_theme, bg_key="PANEL_2")
    theme_btn.pack(anchor="e", pady=(0, 2))

    instructions = tk.Frame(scrollable_frame, bg=C("PANEL"), highlightbackground=C("BORDER"), highlightthickness=1)
    instructions.pack(fill="x", padx=16, pady=(4, 8))

    instructions_text = (
        "How to use:\n"
        "1. In Discord, run wboss i, copy the first boss message, then paste it into Boss 1.\n"
        "2. Click the right arrow, copy the second boss message, then paste it into Boss 2.\n"
        "3. Click the right arrow again, copy the third boss message, then paste it into Boss 3.\n"
        "4. HP values are optional. Leave empty for 80k, or write 90k / 100k / 90000.\n"
        "5. Click Generate & Copy Command, then paste the command into Discord."
    )

    instructions_label = tk.Label(
        instructions,
        text=instructions_text,
        bg=C("PANEL"),
        fg=C("MUTED"),
        justify="left",
        anchor="w",
        font=("Arial", 9)
    )
    instructions_label.pack(fill="x", padx=12, pady=10)

    main_frame = tk.Frame(scrollable_frame, bg=C("BG"))
    main_frame.pack(fill="x", padx=16)

    boss1_text = create_boss_section(
        main_frame,
        "Boss 1 Info",
        "Paste the first boss message here.",
        "Next → Boss 2",
        lambda: boss2_text.focus_set()
    )

    boss2_text = create_boss_section(
        main_frame,
        "Boss 2 Info",
        "Paste the second boss message here.",
        "Next → Boss 3",
        lambda: boss3_text.focus_set()
    )

    boss3_text = create_boss_section(
        main_frame,
        "Boss 3 Info",
        "Paste the third boss message here.",
        "Next → HP",
        lambda: hp1_entry.focus_set()
    )

    hp_frame = tk.Frame(scrollable_frame, bg=C("PANEL"), highlightbackground=C("BORDER"), highlightthickness=1)
    hp_frame.pack(fill="x", padx=16, pady=(6, 8))

    hp_title = tk.Label(hp_frame, text="Boss HP Values", bg=C("PANEL"), fg=C("TEXT"), font=("Arial", 11, "bold"))
    hp_title.grid(row=0, column=0, columnspan=6, sticky="w", padx=10, pady=(9, 2))

    hp_hint = tk.Label(
        hp_frame,
        text="Leave empty for 80000. You can write 90k, 100k, or 90000.",
        bg=C("PANEL"),
        fg=C("MUTED"),
        font=("Arial", 8)
    )
    hp_hint.grid(row=1, column=0, columnspan=6, sticky="w", padx=10, pady=(0, 8))

    hp1_entry = make_hp_entry(hp_frame, "Boss 1 HP:", 0)
    hp2_entry = make_hp_entry(hp_frame, "Boss 2 HP:", 2)
    hp3_entry = make_hp_entry(hp_frame, "Boss 3 HP:", 4)

    button_frame = tk.Frame(scrollable_frame, bg=C("BG"))
    button_frame.pack(fill="x", padx=16, pady=(0, 8))

    generate_btn = make_button(button_frame, "Generate & Copy Command", generate_command, bg_key="ACCENT", padx=20, pady=8)
    generate_btn.pack(side="left", padx=(0, 8))

    copy_btn = make_button(button_frame, "Copy Output", copy_output, bg_key="PANEL_2", padx=14, pady=8)
    copy_btn.pack(side="left", padx=(0, 8))

    clear_btn = make_button(button_frame, "Clear All", clear_all, bg_key="PANEL_2", padx=14, pady=8)
    clear_btn.pack(side="left")

    status_label = tk.Label(button_frame, text="Ready.", bg=C("BG"), fg=C("MUTED"), font=("Arial", 9))
    status_label.pack(side="right")

    output_frame = tk.Frame(scrollable_frame, bg=C("PANEL"), highlightbackground=C("BORDER"), highlightthickness=1)
    output_frame.pack(fill="x", padx=16, pady=(0, 8))

    output_label = tk.Label(output_frame, text="Generated Command", bg=C("PANEL"), fg=C("TEXT"), font=("Arial", 11, "bold"))
    output_label.pack(anchor="w", padx=10, pady=(8, 3))

    output_text = tk.Text(output_frame)
    style_textbox(output_text, height=3)
    output_text.pack(fill="x", padx=10, pady=(0, 10))

    warnings_frame = tk.Frame(scrollable_frame, bg=C("PANEL"), highlightbackground=C("BORDER"), highlightthickness=1)
    warnings_frame.pack(fill="x", padx=16, pady=(0, 14))

    warnings_label = tk.Label(warnings_frame, text="Warnings / Mapping Status", bg=C("PANEL"), fg=C("TEXT"), font=("Arial", 11, "bold"))
    warnings_label.pack(anchor="w", padx=10, pady=(8, 3))

    warnings_text = tk.Text(warnings_frame)
    style_textbox(warnings_text, height=2)
    warnings_text.pack(fill="x", padx=10, pady=(0, 10))

    boss1_text.insert("1.0", state.get("boss1", ""))
    boss2_text.insert("1.0", state.get("boss2", ""))
    boss3_text.insert("1.0", state.get("boss3", ""))
    hp1_entry.insert(0, state.get("hp1", ""))
    hp2_entry.insert(0, state.get("hp2", ""))
    hp3_entry.insert(0, state.get("hp3", ""))
    output_text.insert("1.0", state.get("output", ""))
    warnings_text.insert("1.0", state.get("warnings", "No command generated yet."))


root = tk.Tk()
root.title(APP_NAME)
root.geometry("1040x760")
root.minsize(850, 620)

try:
    icon_path = resource_path(ICON_FILE)
    if os.path.exists(icon_path):
        root.iconbitmap(icon_path)
        root.wm_iconbitmap(icon_path)
except Exception:
    pass

build_ui()
root.mainloop()
