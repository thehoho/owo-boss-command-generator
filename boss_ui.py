# ============================================================
# boss_ui.py  –  OwO Boss Command Generator  v0.6-portable
# Modes: Text Mode (paste wboss output) + Image Mode (screenshot scan)
# Made by Hassaan
# ============================================================

import os, re, sys, ctypes, threading, tempfile
import tkinter as tk
from tkinter import ttk, messagebox, filedialog

APP_NAME   = "OwO Boss Command Generator"
CREDIT_TEXT = "Made by Hassaan"
DEFAULT_HP  = "80000"
ICON_FILE   = "owo-boss.ico"

try:
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
        "hassaan.owo.boss.generator")
except Exception:
    pass

def resource_path(relative_path):
    try:
        base = sys._MEIPASS
    except Exception:
        base = os.path.abspath(".")
    return os.path.join(base, relative_path)

# ─── Image-mode optional libraries ───────────────────────────
try:
    import cv2
    import numpy as np
    from PIL import Image as PILImage, ImageTk, ImageGrab
    import pytesseract
    from rapidfuzz import process as fuzz_process, fuzz as _fuzz

    def _configure_tesseract():
        """
        Prefer the portable/bundled Tesseract first, then fall back to a normal
        Windows installation.

        Supported portable layouts:
        - vendor/tesseract/tesseract.exe
        - tesseract/tesseract.exe

        When packaged by PyInstaller, resource_path() points into the bundled
        app folder, so the same code works both locally and inside the EXE.
        """
        bundled_candidates = [
            resource_path(os.path.join("vendor", "tesseract", "tesseract.exe")),
            resource_path(os.path.join("tesseract", "tesseract.exe")),
        ]

        installed_candidates = [
            r"C:\Program Files\Tesseract-OCR\tesseract.exe",
            r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
            r"C:\Users\{}\AppData\Local\Programs\Tesseract-OCR\tesseract.exe".format(
                os.environ.get("USERNAME", "")),
        ]

        for _tp in bundled_candidates + installed_candidates:
            if not os.path.exists(_tp):
                continue

            pytesseract.pytesseract.tesseract_cmd = _tp

            tesseract_base = os.path.dirname(_tp)
            tessdata_candidates = [
                os.path.join(tesseract_base, "tessdata"),
                resource_path(os.path.join("vendor", "tesseract", "tessdata")),
                resource_path(os.path.join("tesseract", "tessdata")),
            ]

            for _td in tessdata_candidates:
                if os.path.isdir(_td):
                    os.environ["TESSDATA_PREFIX"] = _td
                    break

            return

    _configure_tesseract()

    IMAGE_LIBS_OK = True
except ImportError as _ie:
    IMAGE_LIBS_OK = False

# Drag-and-drop support
try:
    from tkinterdnd2 import DND_FILES, TkinterDnD
    HAS_DND = True
except ImportError:
    HAS_DND = False

# ─── Theme ───────────────────────────────────────────────────
THEME = {
    # Single modern dark theme.
    "BG": "#070b16",
    "PANEL": "#111827",
    "PANEL_2": "#1b2435",
    "TEXT": "#f8fafc",
    "MUTED": "#9aa7bd",
    "ACCENT": "#8b5cf6",
    "ACCENT_HOVER": "#9f7aea",
    "GREEN": "#2dd4bf",
    "DANGER": "#fb7185",
    "BORDER": "#263145",
    "INPUT_BG": "#0b1020",
}
current_theme = "dark"
def C(key): return THEME[key]

# ─── OWO vocab ────────────────────────────────────────────────
WEAPON_SHORTCUTS = sorted([
    "axe","bhstaff","bgaz","bow","cclaw","crune","cstaff","sythe","aedge",
    "estaff","ffish","fstaff","hstaff","lrune","lsy","orb","pd","pstaff",
    "rstaff","rune","ascept","shield","soul","sstaff","sword","vban","vstaff",
    "wand","xbow",
])
PASSIVE_SHORTCUTS = sorted([
    "absv","adapt","crit","dc","ds","enrage","fr","gslay","hgen","hp",
    "kk","kno","ls","lwolf","mag","mr","mtap","pr","res","sac","sg",
    "snail","sprout","str","swarm","th","wgen","wp",
])
ANIMALS = [
    "bee","bug","snail","beetle","butterfly","chick","mouse","chicken",
    "rabbit","chipmunk","sheep","pig","cow","dog","cat","crocodile",
    "tiger","penguin","elephant","whale","dragon","unicorn","snowman",
    "ghost","dove","pbird","pdolphin","pogre","pscorpion","ptiger",
    "camel","fish","panda","shrimp","spider","deer","fox","lion","owl",
    "squid","boar","eagle","frog","gorilla","wolf",
]
RARITIES = ["Common","Uncommon","Rare","Epic","Legendary","Mythical","Divine","Fabled"]
PASSIVE_CMD_OVERRIDES = {"sprt": "sprout"}
RUNE_WEAPONS = {"rune"}
ORB_WEAPONS  = {"orb"}

def passive_slots(weapon):
    if weapon in RUNE_WEAPONS: return 1
    if weapon in ORB_WEAPONS:  return 3
    return 2

def to_cmd_name(stem, is_passive):
    return PASSIVE_CMD_OVERRIDES.get(stem, stem) if is_passive else stem

# ─── Icon cache (loaded once at startup) ─────────────────────
_icon_cache: dict = {"weapons": {}, "passives": {}}  # stem -> PhotoImage

def load_icon_cache(assets_dir=None, size=22):
    """
    Pre-load 22×22 thumbnails for every weapon and passive icon.
    Also registers aliases so the command shortcut names (e.g. 'bgaz', 'sprout')
    resolve correctly even when the file uses a different stem (e.g. 'bleeding_gaze', 'sprt').
    """
    if not IMAGE_LIBS_OK:
        return

    if assets_dir is None:
        assets_dir = resource_path("assets")

    # If the app is running from source and a caller passes "assets", keep it.
    # If it is running from a PyInstaller bundle, resolve it inside _MEIPASS.
    if not os.path.isdir(assets_dir):
        bundled_assets = resource_path("assets")
        if os.path.isdir(bundled_assets):
            assets_dir = bundled_assets

    hex_col = C("PANEL_2").lstrip("#")
    bg_rgb  = tuple(int(hex_col[i:i+2], 16) for i in (0, 2, 4))

    for category in ("weapons", "passives"):
        folder = os.path.join(assets_dir, category)
        if not os.path.isdir(folder):
            continue
        for fname in os.listdir(folder):
            stem, ext = os.path.splitext(fname)
            if ext.lower() not in {".png", ".webp", ".jpg", ".jpeg"}:
                continue
            try:
                img = PILImage.open(os.path.join(folder, fname)).convert("RGBA")
                img = img.resize((size, size), PILImage.LANCZOS)
                bg  = PILImage.new("RGBA", (size, size), bg_rgb + (255,))
                bg.paste(img, mask=img.split()[3])
                _icon_cache[category][stem.lower()] = ImageTk.PhotoImage(bg.convert("RGB"))
            except Exception:
                pass

    # Weapon aliases: command shortcut → actual file stem
    _W = _icon_cache["weapons"]
    for alias, real in [
        ("bgaz",   "bleeding_gaze"),
        ("cclaw",  "claw"),
        ("aedge",  "edge"),
        ("ascept", "scepter"),
        ("sythe",  "culling_scythe"),
        ("sythe",  "culling_scythe"),
        ("xbow",   "xbow"),
    ]:
        if real in _W and alias not in _W:
            _W[alias] = _W[real]

    # Passive aliases: command shortcut → actual file stem
    _P = _icon_cache["passives"]
    for alias, real in [
        ("sprout", "sprt"),
        ("enrage", "enra"),
    ]:
        if real in _P and alias not in _P:
            _P[alias] = _P[real]


class IconComboBox(tk.Frame):
    """
    Styled dropdown that shows a 22×22 icon beside the item name.
    Supports free-form typing, a filtered popup list, and keyboard Return.
    Gracefully falls back to text-only when icons are not available.
    """
    _active_popup = None   # module-level: at most one popup open at a time

    def __init__(self, parent, var, items, icons_dict, **kw):
        bg = C("INPUT_BG")
        super().__init__(parent, bg=bg,
                         highlightbackground=C("BORDER"),
                         highlightthickness=1, **kw)
        self._var    = var
        self._items  = list(items)
        self._icons  = icons_dict          # name -> PhotoImage (may be empty {})
        self._pref   = None                # reference to open popup

        # Icon preview (packed/unpacked dynamically in _refresh)
        self._icon_lbl = tk.Label(self, bg=bg, width=0, height=24)
        # Don't pack yet – _refresh() will pack it if there's an icon

        # Editable text field
        self._entry = tk.Entry(
            self, textvariable=var, bg=bg, fg=C("TEXT"),
            insertbackground=C("TEXT"), relief="flat",
            font=("Consolas", 9), bd=0, highlightthickness=0
        )
        self._entry.pack(side="left", fill="x", expand=True, padx=(2, 0))

        # Drop arrow
        self._arrow = tk.Button(
            self, text="▾", bg=bg, fg=C("MUTED"), relief="flat", bd=0,
            padx=5, pady=0, cursor="hand2", font=("Segoe UI", 9),
            activebackground=bg, activeforeground=C("ACCENT"),
            command=self._toggle
        )
        self._arrow.pack(side="right", padx=(0, 3))

        # Store trace name so we can remove it when the widget is destroyed
        self._trace_id = var.trace_add("write", lambda *a: self._refresh())
        self.bind("<Destroy>", self._on_destroy)
        self._refresh()

    def _on_destroy(self, event=None):
        """Remove the StringVar trace when this widget is destroyed.
        Without this, the trace fires on the dead widget and raises TclError."""
        try:
            self._var.trace_remove("write", self._trace_id)
        except Exception:
            pass

    # ── icon sync ────────────────────────────────────────────────
    def _refresh(self):
        # Guard: widget may have been destroyed (trace fires asynchronously)
        try:
            if not self.winfo_exists():
                return
        except Exception:
            return
        img = self._icons.get(self._var.get())
        if img:
            self._icon_lbl.config(image=img, width=26)
            self._icon_lbl._img = img   # prevent GC
            if not self._icon_lbl.winfo_ismapped():
                self._icon_lbl.pack(side="left", padx=(2, 0))
        else:
            self._icon_lbl.pack_forget()

    # ── popup toggle ──────────────────────────────────────────────
    def _toggle(self):
        if IconComboBox._active_popup:
            try:
                IconComboBox._active_popup.destroy()
            except Exception:
                pass
            IconComboBox._active_popup = None
            self._pref = None
            return
        self._open()

    def _open(self):
        popup = tk.Toplevel(self)
        popup.overrideredirect(True)
        popup.attributes("-topmost", True)
        popup.configure(bg=C("PANEL"))

        # Size & position
        popup.update_idletasks()
        pw = max(self.winfo_width(), 220)
        ph = 300
        px = self.winfo_rootx()
        py = self.winfo_rooty() + self.winfo_height() + 2
        sw = popup.winfo_screenwidth()
        sh = popup.winfo_screenheight()
        if px + pw > sw: px = sw - pw
        if py + ph > sh: py = self.winfo_rooty() - ph - 2
        popup.geometry(f"{pw}x{ph}+{px}+{py}")

        IconComboBox._active_popup = popup
        self._pref = popup

        # Search bar
        sv = tk.StringVar()
        search = tk.Entry(
            popup, textvariable=sv, bg=C("INPUT_BG"), fg=C("TEXT"),
            insertbackground=C("TEXT"), relief="flat", font=("Segoe UI", 9),
            highlightthickness=1, highlightbackground=C("BORDER")
        )
        search.pack(fill="x", padx=4, pady=(4, 2), ipady=4)
        search.focus_set()
        tk.Frame(popup, bg=C("BORDER"), height=1).pack(fill="x", padx=4)

        # Scrollable canvas list
        cf = tk.Canvas(popup, bg=C("PANEL"), highlightthickness=0)
        sb = ttk.Scrollbar(popup, orient="vertical", command=cf.yview)
        cf.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        cf.pack(side="left", fill="both", expand=True)

        inner = tk.Frame(cf, bg=C("PANEL"))
        wid   = cf.create_window((0, 0), window=inner, anchor="nw")
        inner.bind("<Configure>", lambda e: cf.configure(scrollregion=cf.bbox("all")))
        cf.bind("<Configure>",    lambda e: cf.itemconfig(wid, width=e.width))
        cf.bind("<MouseWheel>",   lambda e: cf.yview_scroll(-1*(e.delta//120), "units"))

        popup._imgs = []   # keep PhotoImages alive

        def _select(name):
            self._var.set(name)
            try: popup.destroy()
            except Exception: pass
            IconComboBox._active_popup = None
            self._pref = None

        def _render(filt=""):
            for w in inner.winfo_children():
                w.destroy()
            popup._imgs.clear()
            shown = [n for n in self._items if filt.lower() in n.lower()] if filt else self._items
            if not shown:
                tk.Label(inner, text="No matches", bg=C("PANEL"), fg=C("MUTED"),
                         font=("Segoe UI", 9)).pack(padx=8, pady=10)
                return
            for name in shown:
                img = self._icons.get(name)
                if img: popup._imgs.append(img)

                row = tk.Frame(inner, bg=C("PANEL"), cursor="hand2")
                row.pack(fill="x", padx=3, pady=1)

                if img:
                    tk.Label(row, image=img, bg=C("PANEL"), padx=2, pady=2).pack(side="left")
                else:
                    tk.Label(row, text="  ", bg=C("PANEL"), width=3).pack(side="left")

                tk.Label(row, text=name, bg=C("PANEL"), fg=C("TEXT"),
                         font=("Consolas", 9), anchor="w"
                         ).pack(side="left", fill="x", expand=True, padx=(2, 8), pady=3)

                def _hl(e, r=row):
                    for w in [r] + list(r.winfo_children()):
                        try: w.config(bg=C("ACCENT"))
                        except Exception: pass
                def _unhl(e, r=row):
                    for w in [r] + list(r.winfo_children()):
                        try: w.config(bg=C("PANEL"))
                        except Exception: pass

                for w in [row] + list(row.winfo_children()):
                    w.bind("<Button-1>", lambda e, n=name: _select(n))
                    w.bind("<Enter>", _hl)
                    w.bind("<Leave>", _unhl)

            # Scroll so current value is visible
            cur = self._var.get()
            if cur in shown:
                cf.after(30, lambda: cf.yview_moveto(shown.index(cur) / max(len(shown), 1)))

        _render()
        sv.trace_add("write", lambda *a: _render(sv.get()))

        # Return key selects first match
        def _on_return(e):
            filt    = sv.get()
            matches = [n for n in self._items if filt.lower() in n.lower()]
            if matches:
                _select(matches[0])
        search.bind("<Return>", _on_return)
        search.bind("<Escape>", lambda e: _select(self._var.get()))

        # Close on outside click
        def _maybe_close(e):
            try:
                if not popup.winfo_exists(): return
                w = popup.winfo_containing(e.x_root, e.y_root)
                if w is None or not str(w).startswith(str(popup)):
                    popup.destroy()
                    IconComboBox._active_popup = None
                    self._pref = None
            except Exception:
                pass
        popup.bind_all("<Button-1>", _maybe_close, add="+")

# ─── Image detection functions ────────────────────────────────
# (Only used when IMAGE_LIBS_OK is True)

def _open_rgba(path):
    return np.array(PILImage.open(path).convert("RGBA"))

def _alpha_premultiply(rgba):
    rgb   = rgba[:,:,:3].astype(float)
    alpha = rgba[:,:,3:4].astype(float) / 255.0
    return cv2.cvtColor((rgb * alpha).clip(0,255).astype(np.uint8), cv2.COLOR_RGB2BGR)

def _composite_white(rgba):
    rgb   = rgba[:,:,:3].astype(float)
    alpha = rgba[:,:,3:4].astype(float) / 255.0
    return (rgb * alpha + 255*(1-alpha)).clip(0,255).astype(np.uint8)

def _is_white_card(rgba_card):
    h, w  = rgba_card.shape[:2]
    y1,y2 = int(17*h/300), int(31*h/300)
    x1,x2 = int(10*w/200), int(190*w/200)
    band  = rgba_card[y1:y2, x1:x2, :3].astype(float)
    alpha = rgba_card[y1:y2, x1:x2, 3:4].astype(float) / 255.0
    return float((band * alpha + 255*(1-alpha)).mean()) > 150

ICON_X1, ICON_X2 = 128, 177

def _card_rois(ch, white, n_passives=2):
    s = ch / 300.0
    if white:
        w_roi = (ICON_X1, int(208*s), ICON_X2, int(258*s))
        px1   = 108 if n_passives == 3 else ICON_X1
        p_roi = (px1, int(259*s), ICON_X2, int(281*s))
    else:
        w_roi = (ICON_X1, int(200*s), ICON_X2, int(250*s))
        px1   = 110 if n_passives == 3 else ICON_X1
        p_roi = (px1, int(262*s), 192, int(290*s))
    return w_roi, p_roi

def _glyph_looks_like_7(mask, x1, x2):
    """
    Safe 1→7 check for the OwO pixel font.

    We only use this as a post-correction after OCR. It never changes 8/6/9/etc.
    A real 7 in the card font is wider and has a strong top bar; a real 1 is thin.
    """
    if x2 <= x1:
        return False

    glyph = mask[:, x1:x2]
    ys, xs = np.where(glyph > 0)
    if len(xs) == 0:
        return False

    gx1, gx2 = int(xs.min()), int(xs.max()) + 1
    gy1, gy2 = int(ys.min()), int(ys.max()) + 1
    glyph = glyph[gy1:gy2, gx1:gx2]

    h, w = glyph.shape[:2]
    if h < 5:
        return False

    # A real 1 is normally very narrow. A 7 is wider.
    if w < 5:
        return False

    total = float(glyph.sum())
    if total <= 0:
        return False

    top = glyph[:max(1, h // 3), :]
    top_ratio = float(top.sum()) / total

    # 7 = clear top bar. 1 = mostly vertical stroke.
    return top_ratio >= 0.32


def _split_hp_character_groups(mask):
    """
    Split HP text into visible character groups. This is intentionally simple and
    conservative; it is only used to fix OCR reading a visible 7 as 1.
    """
    # Ignore the outer border lines of the red HP box.
    if mask.shape[1] > 70:
        work = mask[:, 20:mask.shape[1]-20]
        offset = 20
    else:
        work = mask
        offset = 0

    cols = np.where(work.sum(axis=0) > 0)[0]
    if len(cols) == 0:
        return []

    groups = []
    group = [int(cols[0])]
    for col in cols[1:]:
        col = int(col)
        if col - group[-1] > 1:
            groups.append(group)
            group = [col]
        else:
            group.append(col)
    groups.append(group)

    return [(g[0] + offset, g[-1] + offset + 1) for g in groups]


def _fix_leading_7_in_hp_text(text, mask):
    """
    Fix the common OCR error where HP like 78,043 becomes 18,043.
    This only changes a leading 1 into 7 if the first visible glyph actually
    has the shape of a 7. It does not touch 8/6/etc.
    """
    groups = _split_hp_character_groups(mask)
    if not groups:
        return text

    # Remove tiny comma groups and the slash group from detection by using
    # only groups with real digit height/width. Keep order.
    digit_like = []
    for x1, x2 in groups:
        glyph = mask[:, x1:x2]
        ys, xs = np.where(glyph > 0)
        if len(xs) == 0:
            continue
        h = int(ys.max() - ys.min() + 1)
        w = int(xs.max() - xs.min() + 1)
        if h >= 6 and w >= 2:
            digit_like.append((x1, x2))

    if not digit_like:
        return text

    # Correct only the first digit of each side of the slash when OCR says 1.
    parts = text.split('/')
    if len(parts) != 2:
        return text

    left, right = parts[0], parts[1]

    # Find slash-ish group: narrow, diagonal-ish, near center. Use x position of '/'
    # from the raw groups when possible. Fallback to half split.
    slash_x = mask.shape[1] // 2
    for x1, x2 in groups:
        glyph = mask[:, x1:x2]
        ys, xs = np.where(glyph > 0)
        if len(xs) == 0:
            continue
        h = int(ys.max() - ys.min() + 1)
        w = int(xs.max() - xs.min() + 1)
        if 3 <= w <= 6 and h >= 8 and abs((x1 + x2) / 2 - mask.shape[1] / 2) < mask.shape[1] * 0.20:
            slash_x = (x1 + x2) // 2
            break

    left_digits = [(x1, x2) for x1, x2 in digit_like if x2 < slash_x]
    right_digits = [(x1, x2) for x1, x2 in digit_like if x1 > slash_x]

    if left.startswith('1') and left_digits and _glyph_looks_like_7(mask, *left_digits[0]):
        left = '7' + left[1:]

    if right.startswith('1') and right_digits and _glyph_looks_like_7(mask, *right_digits[0]):
        right = '7' + right[1:]

    return left + '/' + right


def _extract_hp(rgba_card, white):
    h, w = rgba_card.shape[:2]
    s    = h / 300.0
    y1, y2 = (int(175*s), int(200*s)) if white else (int(178*s), int(197*s))
    region = rgba_card[y1:y2, 8:w-8]
    comp   = _composite_white(region)
    big    = cv2.resize(comp, (comp.shape[1]*8, comp.shape[0]*8), interpolation=cv2.INTER_LANCZOS4)
    gray   = cv2.cvtColor(big, cv2.COLOR_RGB2GRAY)
    order  = [140,160,180,100,50,30,25,20,15,10] if white else [10,15,20,25,30,50,100,140,160,180]
    for thresh in order:
        _, t = cv2.threshold(gray, thresh, 255, cv2.THRESH_BINARY)
        text = pytesseract.image_to_string(
            PILImage.fromarray(t),
            config="--psm 7 -c tessedit_char_whitelist=0123456789/,. "
        ).strip().replace(" ","").replace(",","").replace(".","")
        text = _fix_leading_7_in_hp_text(text, t)
        m = re.search(r"(\d+)/(\d+)", text)
        if m:
            cur, mx = int(m.group(1)), int(m.group(2))
            if cur <= mx:
                return cur, mx
    return None, None

def _alpha_ocr(alpha_band, scale=10, config="--psm 7"):
    big = cv2.resize(alpha_band,
                     (alpha_band.shape[1]*scale, alpha_band.shape[0]*scale),
                     interpolation=cv2.INTER_LANCZOS4)
    return pytesseract.image_to_string(PILImage.fromarray(255-big), config=config).strip()

def _parse_level(text):
    m = re.search(r"[Ll][Vv][lLiI1]?\s*([0-9lLiI]{1,3})", text)
    if m:
        raw = m.group(1).replace('l','1').replace('L','1').replace('i','1').replace('I','1')
        try: return int(raw)
        except ValueError: pass
    for n in re.findall(r"\b(\d{1,3})\b", text):
        if 1 <= int(n) <= 200: return int(n)
    return None

def _parse_level_px(text, rgba_card, ch, cw):
    """
    White-card level fix: corrects 1→7 only (never 7→1).

    OCR sometimes reads the pixel-font 7 as 1 on white cards.
    We inspect the alpha channel glyphs with connected components —
    the same proven approach as _correct_level_1_7_dark for dark cards.

    We deliberately never convert a 7 back to 1 here: when OCR says 7,
    it is almost always correct. Doing so caused more harm than good.
    """
    level = _parse_level(text)
    if level is None:
        return None

    level_str = str(level)
    if '1' not in level_str:
        return level   # nothing ambiguous, trust OCR

    # Work on the alpha channel of the level band (white card: high alpha = text pixels).
    alpha_band = rgba_card[int(14*ch/300):int(34*ch/300), 30:cw-25, 3]
    if alpha_band.size == 0:
        return level

    _, mask = cv2.threshold(alpha_band, 80, 255, cv2.THRESH_BINARY)
    mask    = mask.astype(np.uint8)

    num_labels, _labels, stats, _ = cv2.connectedComponentsWithStats(mask, 8)

    comps = []
    for i in range(1, num_labels):
        x, y, w, h_c, area = stats[i]
        if area < 3 or h_c < 4:
            continue
        comps.append({"x": int(x), "y": int(y), "w": int(w),
                      "h": int(h_c), "area": int(area)})
    comps.sort(key=lambda c: c["x"])

    if len(comps) < len(level_str):
        return level

    # The last N components (sorted left→right) correspond to the digit glyphs.
    digit_comps = comps[-len(level_str):]
    corrected   = list(level_str)

    for idx, (digit, comp) in enumerate(zip(level_str, digit_comps)):
        if digit != '1':
            continue
        x, y, w, h_c = comp["x"], comp["y"], comp["w"], comp["h"]
        glyph = mask[y:y+h_c, x:x+w]
        if glyph.size == 0:
            continue
        top        = glyph[:max(1, h_c // 3), :]
        top_ratio  = float(top.sum()) / float(glyph.sum()) if glyph.sum() else 0.0
        # Real 1 in this font is narrow (≤3 px); real 7 is wider (≥5 px) with a top bar.
        if w >= 5 and (top_ratio >= 0.22 or comp["area"] <= 16):
            corrected[idx] = '7'

    try:
        return int(''.join(corrected))
    except Exception:
        return level


def _correct_level_1_7_dark(level, rgba_card):
    """
    Dark-card helper: Tesseract sometimes reads the pixel-font 7 as 1.

    Instead of trusting OCR, this inspects the real white glyph components in
    the title line. In the OwO boss card font, a real `1` is narrow, while a
    real `7` is wider and has a stronger top bar.
    """
    if level is None:
        return None

    level_str = str(level)
    if "1" not in level_str:
        return level

    h, w = rgba_card.shape[:2]

    # Crop the top-center `Lvl NN` line. Scales with the card size.
    y1, y2 = int(8 * h / 300), int(36 * h / 300)
    x1, x2 = int(50 * w / 200), int(150 * w / 200)
    region = rgba_card[y1:y2, x1:x2, :3]

    if region.size == 0:
        return level

    gray = cv2.cvtColor(region, cv2.COLOR_RGB2GRAY)
    _, mask = cv2.threshold(gray, 115, 255, cv2.THRESH_BINARY)

    # Connected components gives us each visible letter/digit in the title.
    num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(mask, 8)

    comps = []
    for label_idx in range(1, num_labels):
        x, y, cw, ch, area = stats[label_idx]

        # Ignore the card border/top decorations and tiny noise.
        if area < 3:
            continue
        if y < 5 and cw > 20:
            continue
        if ch < 4:
            continue

        comps.append({"x": int(x), "y": int(y), "w": int(cw), "h": int(ch), "area": int(area)})

    comps.sort(key=lambda c: c["x"])

    # Components should roughly be: L, v, l, digit, digit.
    # We only need the last N components, where N is the number of OCR digits.
    if len(comps) < len(level_str):
        return level

    digit_comps = comps[-len(level_str):]
    corrected = list(level_str)

    for idx, (digit, comp) in enumerate(zip(level_str, digit_comps)):
        if digit != "1":
            continue

        x, y, cw, ch = comp["x"], comp["y"], comp["w"], comp["h"]
        glyph = mask[y:y+ch, x:x+cw]
        if glyph.size == 0:
            continue

        top = glyph[:max(1, ch // 3), :]
        top_weight = float(top.sum())
        total_weight = float(glyph.sum())
        top_ratio = top_weight / total_weight if total_weight else 0.0

        # Real 1 in this font is usually 2-3 px wide.
        # Real 7 is usually 5+ px wide and has a visible top bar.
        if cw >= 5 and (top_ratio >= 0.22 or comp["area"] <= 16):
            corrected[idx] = "7"

    try:
        return int("".join(corrected))
    except Exception:
        return level

def _fuzzy_match(text, choices, threshold=65):
    best_s, best = 0, None
    for w in re.findall(r"[A-Za-z]+", text):
        r = fuzz_process.extractOne(w, choices, scorer=_fuzz.ratio, score_cutoff=threshold)
        if r and r[1] > best_s: best_s, best = r[1], r[0]
    return best

def _fuzzy_animal(text):
    best_s, best = 0, None
    for w in re.findall(r"[A-Za-z]+", text.lower()):
        if len(w) < 3: continue
        r = fuzz_process.extractOne(w, ANIMALS, scorer=_fuzz.ratio, score_cutoff=60)
        if r and r[1] > best_s: best_s, best = r[1], r[0]
    return best

def _extract_title(rgba_card, white):
    h, w  = rgba_card.shape[:2]
    alpha = rgba_card[:,:,3]
    rgb   = rgba_card[:,:,:3]
    if white:
        lvl_a  = alpha[int(14*h/300):int(34*h/300), 30:w-25]
        name_a = alpha[int(40*h/300):int(57*h/300), 10:w-10]
        lvl_text  = _alpha_ocr(lvl_a)
        name_text = _alpha_ocr(name_a)
        raw   = lvl_text + " " + name_text
        level = _parse_level_px(raw, rgba_card, h, w)
    else:
        region = rgb[3:int(h*0.175), 5:w-5]
        big    = cv2.resize(region, (region.shape[1]*3, region.shape[0]*3),
                            interpolation=cv2.INTER_LANCZOS4)

        # Main OCR pass.
        raw = pytesseract.image_to_string(
            PILImage.fromarray(big),
            config="--psm 6"
        ).strip()

        # Extra OCR pass focused on the level line only.
        lvl_region = rgb[int(8*h/300):int(36*h/300), int(50*w/200):int(150*w/200)]
        lvl_big = cv2.resize(
            lvl_region,
            (lvl_region.shape[1]*6, lvl_region.shape[0]*6),
            interpolation=cv2.INTER_LANCZOS4
        )
        lvl_gray = cv2.cvtColor(lvl_big, cv2.COLOR_RGB2GRAY)
        _, lvl_bin = cv2.threshold(lvl_gray, 110, 255, cv2.THRESH_BINARY)
        lvl_raw = pytesseract.image_to_string(
            PILImage.fromarray(lvl_bin),
            config="--psm 7 -c tessedit_char_whitelist=Lvlvl0123456789 "
        ).strip()

        raw = (lvl_raw + " " + raw).strip()
        level = _parse_level(raw)
        level = _correct_level_1_7_dark(level, rgba_card)

    return level, _fuzzy_match(raw, RARITIES, 65), _fuzzy_animal(raw)

def _load_templates(folder):
    out = {}
    if not os.path.isdir(folder): return out
    for f in os.listdir(folder):
        ext = os.path.splitext(f)[1].lower()
        if ext not in {".png",".webp",".jpg",".jpeg"}: continue
        out[os.path.splitext(f)[0].lower()] = np.array(
            PILImage.open(os.path.join(folder, f)).convert("RGBA"))
    return out

def _prep_template(rgba, size):
    pil   = PILImage.fromarray(rgba).resize((size, size), PILImage.LANCZOS)
    arr   = np.array(pil)
    bgr   = cv2.cvtColor(arr, cv2.COLOR_RGBA2BGR)
    alpha = arr[:,:,3]
    mask  = (alpha > 20).astype(np.uint8) * 255
    if mask.sum() == 0: mask = np.ones((size,size), dtype=np.uint8)*255
    return bgr, mask

def _suppress(smap, x, y, w, h):
    px=max(6,int(w*0.6)); py=max(6,int(h*0.6))
    smap[max(0,y-py):min(smap.shape[0],y+h+py),
         max(0,x-px):min(smap.shape[1],x+w+px)] = -1

def _iou(a, b):
    ix1=max(a["x"],b["x"]); iy1=max(a["y"],b["y"])
    ix2=min(a["x"]+a["w"],b["x"]+b["w"]); iy2=min(a["y"]+a["h"],b["y"]+b["h"])
    if ix2<=ix1 or iy2<=iy1: return 0.
    inter=(ix2-ix1)*(iy2-iy1)
    return inter/float(a["w"]*a["h"]+b["w"]*b["h"]-inter)

def _nms(cands, iou_thresh=0.3, max_items=None):
    cands=sorted(cands, key=lambda c: c["score"], reverse=True)
    kept=[]
    for c in cands:
        if not any(_iou(c,k)>iou_thresh for k in kept): kept.append(c)
        if max_items and len(kept)>=max_items: break
    return kept

SIZES_WEAPON  = list(range(34, 48, 2))
SIZES_PASSIVE = list(range(14, 28, 2))

def _find_matches(bgr_region, templates, threshold, sizes, max_hits=2):
    cands = []
    for name, tmpl_rgba in templates.items():
        for size in sizes:
            if bgr_region.shape[0]<size or bgr_region.shape[1]<size: continue
            bgr, mask = _prep_template(tmpl_rgba, size)
            try:
                res = cv2.matchTemplate(bgr_region, bgr, cv2.TM_CCORR_NORMED, mask=mask)
            except cv2.error: continue
            res = np.nan_to_num(res, nan=-1., posinf=-1., neginf=-1.)
            search = res.copy()
            for _ in range(max_hits):
                _, val, _, loc = cv2.minMaxLoc(search)
                if val < threshold: break
                x, y = loc
                cands.append({"name":name,"score":float(val),"x":x,"y":y,"w":size,"h":size})
                _suppress(search, x, y, size, size)
    return _nms(cands)

def _get_bgr(rgba_card, roi, brighten=False):
    x1,y1,x2,y2 = roi
    region = rgba_card[y1:y2, x1:x2]
    bgr = _alpha_premultiply(region)
    if brighten:
        bgr = np.clip(bgr.astype(float)*5.0, 0, 255).astype(np.uint8)
    return bgr

W_THRESH      = 0.82;  P_THRESH      = 0.80
W_THRESH_DEAD = 0.70;  P_THRESH_DEAD = 0.68

def process_image(path, assets_dir=None):
    """Run detection on a screenshot. Returns list of 3 boss dicts."""
    if assets_dir is None:
        assets_dir = resource_path("assets")

    if not os.path.isdir(assets_dir):
        bundled_assets = resource_path("assets")
        if os.path.isdir(bundled_assets):
            assets_dir = bundled_assets

    rgba_full = _open_rgba(path)
    H, W = rgba_full.shape[:2]
    card_w = W // 3
    weapons_dir  = os.path.join(assets_dir, "weapons")
    passives_dir = os.path.join(assets_dir, "passives")
    weapons  = _load_templates(weapons_dir)
    passives = _load_templates(passives_dir)

    results = []
    for idx in range(3):
        x1 = idx * card_w
        x2 = (idx+1)*card_w if idx < 2 else W
        rgba_card = rgba_full[:, x1:x2]
        ch, cw = rgba_card.shape[:2]
        white = _is_white_card(rgba_card)

        level, rarity, animal = _extract_title(rgba_card, white)
        cur_hp, max_hp = _extract_hp(rgba_card, white)
        dead = (cur_hp is None or cur_hp == 0)
        if cur_hp is None: cur_hp, max_hp = 0, 0

        wt = W_THRESH_DEAD if dead else W_THRESH
        pt = P_THRESH_DEAD if dead else P_THRESH

        w_roi, _ = _card_rois(ch, white, n_passives=2)
        w_bgr    = _get_bgr(rgba_card, w_roi, brighten=dead)
        w_hits   = _nms(_find_matches(w_bgr, weapons, wt, SIZES_WEAPON, max_hits=1), max_items=1)
        weapon_name = w_hits[0]["name"] if w_hits else ""

        n_pass   = passive_slots(weapon_name)
        _, p_roi = _card_rois(ch, white, n_passives=n_pass)
        p_bgr    = _get_bgr(rgba_card, p_roi, brighten=dead)
        p_hits   = _nms(_find_matches(p_bgr, passives, pt, SIZES_PASSIVE, max_hits=n_pass),
                        iou_thresh=0.3, max_items=n_pass)
        p_hits   = sorted(p_hits, key=lambda c: (c["y"], c["x"]))
        passive_names = [to_cmd_name(ph["name"], True) for ph in p_hits]

        results.append({
            "level":   str(level) if level else "",
            "rarity":  rarity or "",
            "animal":  animal or "",
            "weapon":  weapon_name,
            "passives": passive_names,
            "hp":      str(cur_hp),
            "dead":    dead,
        })
    return results

# ─── Existing Text Mode maps ──────────────────────────────────
WEAPON_MAP = {
    "great sword": "sword","greatsword": "sword","sword": "sword",
    "healing staff": "hstaff","heal staff": "hstaff","hstaff": "hstaff",
    "bow": "bow",
    "rune of the forgotten": "rune","forgotten rune": "rune","rune": "rune",
    "defender s aegis": "shield","defenders aegis": "shield","aegis": "shield","shield": "shield",
    "orb of potency": "orb","potency orb": "orb","orb": "orb",
    "vampiric staff": "vstaff","vamp staff": "vstaff","vstaff": "vstaff",
    "poison dagger": "pd","dagger": "pd","pd": "pd",
    "wand of absorption": "wand","absorption wand": "wand","wand": "wand",
    "flame staff": "fstaff","fire staff": "fstaff","fstaff": "fstaff",
    "energy staff": "estaff","estaff": "estaff",
    "spirit staff": "sstaff","sstaff": "sstaff",
    "arcane scepter": "ascept","scepter": "ascept","ascept": "ascept",
    "resurrection staff": "rstaff","res staff": "rstaff","rstaff": "rstaff",
    "glacial axe": "axe","axe": "axe",
    "vanguard s banner": "vban","banner": "vban","vban": "vban",
    "culling scythe": "sythe","scythe": "sythe","sythe": "sythe",
    "rune of celebration": "crune","celebration rune": "crune","crune": "crune",
    "staff of purity": "pstaff","purity staff": "pstaff","pstaff": "pstaff",
    "leeching scythe": "lsy","leech scythe": "lsy","lsy": "lsy",
    "foul fish": "ffish","fishing rod": "ffish","fish": "ffish","ffish": "ffish",
    "rune of luck": "lrune","luck rune": "lrune","lrune": "lrune",
    "staff of corruption": "cstaff","corruption staff": "cstaff","cstaff": "cstaff",
    "soul tithe": "soul","soul": "soul",
    "briar heart staff": "bhstaff","bhstaff": "bhstaff",
    "arbiter s edge": "aedge","edge": "aedge","aedge": "aedge",
    "wounding crossbow": "xbow","crossbow": "xbow","xbow": "xbow",
    "bleeding gaze": "bgaz","gaze": "bgaz","bgaz": "bgaz",
    "conduit claw": "cclaw","claw": "cclaw","cclaw": "cclaw",
}

PASSIVE_MAP = {
    "strength": "str","str": "str",
    "magic": "mag","mag": "mag",
    "health": "hp","hp": "hp",
    "weapon point": "wp","wp": "wp",
    "physical resistance": "pr","pr": "pr",
    "magic resistance": "mr","mr": "mr",
    "lifesteal": "ls","ls": "ls",
    "thorns": "th","th": "th",
    "mana tap": "mtap","mtap": "mtap",
    "absolve": "absv","absv": "absv",
    "safeguard": "sg","sg": "sg",
    "critical": "crit","crit": "crit",
    "discharge": "dc","dc": "dc",
    "kamikaze": "kk","kk": "kk",
    "regeneration": "hgen","regen": "hgen","hgen": "hgen",
    "energize": "wgen","wgen": "wgen",
    "sprout": "sprout","sprt": "sprout",
    "enrage": "enrage","enra": "enrage",
    "sacrifice": "sac","sac": "sac",
    "snail": "snail",
    "knowledge": "kno","kno": "kno",
    "giant slayer": "gslay","gslay": "gslay",
    "adaptation": "adapt","adapt": "adapt",
    "resonance": "res","res": "res",
    "living hive": "swarm","swarm": "swarm",
    "lone wolf": "lwolf","lwolf": "lwolf",
    "double strike": "ds","ds": "ds",
    "frost armor": "fr","fr": "fr",
}

RARITIES_SET = {
    "common","uncommon","rare","epic","mythical","legendary",
    "fabled","hidden","special","patreon","gem","bot","distorted",
}
REMOVE_WORDS = {
    "pristine","fine","decent","worn","unknown","empowered","unempowered",
    "used","new","old","broken","damaged","poor","good","excellent","perfect",
}

def normalize_name(value):
    value = value.lower().strip()
    value = re.sub(r"<:[^>]+>", " ", value)
    value = value.replace("'","'").replace("`","")
    value = re.sub(r"['']", " ", value)
    value = re.sub(r"[^a-z0-9\s-]", " ", value)
    value = value.replace("-"," ")
    return re.sub(r"\s+", " ", value).strip()

def clean_weapon_name(raw):
    cleaned = normalize_name(raw)
    for pat in [r"\bquality\b.*",r"\bwear\b.*",r"\btype\b.*",r"\bkills\b.*",r"\bweapon cost\b.*"]:
        cleaned = re.sub(pat, "", cleaned).strip()
    words = [w for w in cleaned.split() if w not in RARITIES_SET and w not in REMOVE_WORDS]
    name = " ".join(words).strip()
    if name in WEAPON_MAP:
        return WEAPON_MAP[name], None
    fallback = name.replace(" ","")
    return fallback, f"Unknown weapon: '{raw.strip()}' → fallback: '{fallback}'"

def split_boss_blocks(text):
    text = text.strip()
    matches = list(re.finditer(r"##\s*Lvl\s*\d+", text, flags=re.I))
    if not matches: return []
    blocks = []
    for i, m in enumerate(matches):
        end = matches[i+1].start() if i+1 < len(matches) else len(text)
        blocks.append(text[m.start():end].strip())
    return blocks

def parse_boss(block):
    compact  = " ".join(block.split())
    warnings = []
    header   = re.search(r"##\s*Lvl\s*(\d+)\s+\w+\s+(.+?)(?=<:|###|-#|\*\*|$)", compact, re.I)
    if not header: raise ValueError("Could not find boss level/name.")
    level  = header.group(1)
    animal = header.group(2).strip().lower()
    wm     = re.search(
        r"###\s+(?!__Description__)(.+?)(?=\*\*Quality:\*\*|\*\*Wear:\*\*|\*\*Type:\*\*|\*\*Kills:\*\*|###\s+__Description__|$)",
        compact, re.I)
    if not wm: raise ValueError(f"Could not find weapon for {level} {animal}.")
    weapon, warn = clean_weapon_name(wm.group(1))
    if warn: warnings.append(warn)
    qm      = re.search(r"\*\*Quality:\*\*.*?([\d.]+)%", compact, re.I)
    quality = float(qm.group(1)) if qm else 55.0
    passives = []
    for title in re.findall(r"\*\*__([^_]+)__\*\*", compact):
        key = normalize_name(title)
        if key in PASSIVE_MAP:
            passives.append(PASSIVE_MAP[key])
    passive_text = " " + " ".join(passives) if passives else ""
    return {"part": f"{level} {animal} {weapon}{passive_text}", "quality": quality, "warnings": warnings}

def normalize_hp(value):
    value = value.strip().lower().replace(",","")
    if not value: return DEFAULT_HP
    if value.endswith("k"):
        n = value[:-1].strip()
        return str(int(float(n)*1000)) if n else DEFAULT_HP
    return value

# ─── UI helpers ───────────────────────────────────────────────
def style_text(w, height=5):
    w.configure(
        height=height,
        bg=C("INPUT_BG"),
        fg=C("TEXT"),
        insertbackground=C("TEXT"),
        selectbackground=C("ACCENT"),
        selectforeground="#ffffff",
        relief="flat",
        borderwidth=0,
        highlightthickness=1,
        highlightbackground=C("BORDER"),
        highlightcolor=C("ACCENT"),
        padx=10,
        pady=8,
        font=("Consolas", 9),
        wrap="word",
    )

def make_btn(parent, text, cmd, bg="ACCENT", padx=12, pady=6):
    btn = tk.Button(
        parent,
        text=text,
        command=cmd,
        bg=C(bg),
        fg="#ffffff" if bg == "ACCENT" else C("TEXT"),
        activebackground=C("ACCENT_HOVER") if bg == "ACCENT" else C("PANEL_2"),
        activeforeground="#ffffff",
        disabledforeground="#ffffff",
        relief="flat",
        borderwidth=0,
        padx=padx,
        pady=pady,
        cursor="hand2",
        font=("Segoe UI", 9, "bold"),
    )
    return btn

def styled_label(parent, text, font=("Segoe UI",9), anchor="w", **kw):
    return tk.Label(parent, text=text, bg=kw.get("bg", C("PANEL")),
                    fg=kw.get("fg", C("TEXT")), font=font, anchor=anchor)

def make_combo(parent, values, var, width=14):
    # Modern-looking editable field. We intentionally avoid ttk.Combobox here
    # because the native Windows dropdown arrow makes the UI look dated.
    return tk.Entry(
        parent,
        textvariable=var,
        width=width,
        bg=C("INPUT_BG"),
        fg=C("TEXT"),
        insertbackground=C("TEXT"),
        relief="flat",
        font=("Segoe UI", 9),
        highlightthickness=1,
        highlightbackground=C("BORDER"),
        highlightcolor=C("ACCENT"),
    )

def apply_combo_style():
    style = ttk.Style()
    style.theme_use("clam")
    style.configure("TCombobox",
                    fieldbackground=C("INPUT_BG"), background=C("INPUT_BG"),
                    foreground=C("TEXT"), selectbackground=C("ACCENT"),
                    selectforeground="#ffffff", arrowcolor=C("MUTED"),
                    bordercolor=C("BORDER"), relief="flat")
    style.map("TCombobox",
              fieldbackground=[("readonly", C("INPUT_BG")),("active", C("INPUT_BG"))],
              foreground=[("readonly", C("TEXT"))])

# ─── Text Mode ────────────────────────────────────────────────
def create_text_boss_section(parent, title, helper, next_label, next_action):
    frame = tk.Frame(parent, bg=C("PANEL"),
                     highlightbackground=C("BORDER"), highlightthickness=1)
    frame.pack(fill="x", pady=6)
    tk.Frame(frame, bg=C("PANEL")).pack(fill="x", padx=10, pady=(8,2))
    tk.Label(frame, text=title, bg=C("PANEL"), fg=C("TEXT"),
             font=("Segoe UI",11,"bold"), anchor="w").pack(fill="x", padx=10)
    tk.Label(frame, text=helper, bg=C("PANEL"), fg=C("MUTED"),
             font=("Segoe UI",8), anchor="w").pack(fill="x", padx=10, pady=(0,5))
    tf = tk.Frame(frame, bg=C("INPUT_BG"))
    tf.pack(fill="x", padx=10, pady=(0,8))
    tb = tk.Text(tf)
    style_text(tb, height=5); tb.pack(side="left", fill="both", expand=True)
    sb = tk.Scrollbar(tf, command=tb.yview); sb.pack(side="right", fill="y")
    tb.configure(yscrollcommand=sb.set)
    af = tk.Frame(frame, bg=C("PANEL")); af.pack(fill="x", padx=10, pady=(0,8))
    make_btn(af, "Clear Box", lambda: tb.delete("1.0", tk.END), "PANEL_2").pack(side="left")
    make_btn(af, next_label, next_action).pack(side="right")
    return tb

def make_hp_entry_text(parent, label, col):
    tk.Label(parent, text=label, bg=C("PANEL"), fg=C("TEXT"),
             font=("Arial",9,"bold")).grid(row=2, column=col, padx=(10,5), pady=(0,10), sticky="w")
    e = tk.Entry(parent, width=14, bg=C("INPUT_BG"), fg=C("TEXT"),
                 insertbackground=C("TEXT"), relief="flat", font=("Consolas",10))
    e.grid(row=2, column=col+1, padx=(0,10), pady=(0,10), ipady=5)
    return e

# ─── Image Mode UI state ─────────────────────────────────────
# Per-boss StringVars for Image Mode
_im_vars = []  # list of 3 dicts of StringVar

def _make_im_vars():
    global _im_vars
    _im_vars = []
    for _ in range(3):
        _im_vars.append({
            "level":   tk.StringVar(value=""),
            "animal":  tk.StringVar(value=""),
            "weapon":  tk.StringVar(value=""),
            "p1":      tk.StringVar(value=""),
            "p2":      tk.StringVar(value=""),
            "p3":      tk.StringVar(value=""),
            "hp":      tk.StringVar(value=""),
            "qe":      tk.StringVar(value="55"),
        })

def _populate_im_vars(results):
    for i, boss in enumerate(results):
        v = _im_vars[i]
        v["level"].set(boss.get("level",""))
        v["animal"].set(boss.get("animal",""))
        v["weapon"].set(boss.get("weapon",""))
        passives = boss.get("passives", [])
        v["p1"].set(passives[0] if len(passives)>0 else "")
        v["p2"].set(passives[1] if len(passives)>1 else "")
        v["p3"].set(passives[2] if len(passives)>2 else "")
        v["hp"].set(boss.get("hp","0"))
        v["qe"].set("55")  # default, user can change

def _build_command_from_im():
    parts = []
    hp_vals = []
    qe_vals = []
    for i in range(3):
        v = _im_vars[i]
        lvl    = v["level"].get().strip()
        animal = v["animal"].get().strip()
        weapon = v["weapon"].get().strip()
        p1     = v["p1"].get().strip()
        p2     = v["p2"].get().strip()
        p3     = v["p3"].get().strip()
        hp     = normalize_hp(v["hp"].get())
        qe     = v["qe"].get().strip() or "55"
        try: qe_vals.append(float(qe))
        except: qe_vals.append(55.0)

        tokens = []
        if lvl: tokens.append(lvl)
        if animal: tokens.append(animal)
        if weapon: tokens.append(weapon)
        for p in [p1, p2, p3]:
            if p: tokens.append(p)
        parts.append(" ".join(tokens))
        hp_vals.append(hp)

    qe_avg = round(sum(qe_vals)/len(qe_vals)) if qe_vals else 55
    return (f"neon b myself vs {', '.join(parts)}"
            f" -hp {' '.join(hp_vals)} -m -qe{qe_avg}")

# ─── Build UI ────────────────────────────────────────────────
# References needed across functions
_text_widgets  = {}   # text mode widgets
_im_widgets    = {}   # image mode widgets
_status_im     = None
_output_im     = None
_im_boss_frames = []
_im_fields_built = False

def build_ui(state=None):
    global _text_widgets, _im_widgets, _status_im, _output_im
    global _im_boss_frames, _im_fields_built

    if state is None:
        state = {"boss1":"","boss2":"","boss3":"",
                 "hp1":"","hp2":"","hp3":"",
                 "output":"","warnings":"No command generated yet."}

    for child in root.winfo_children():
        child.destroy()

    apply_combo_style()
    _make_im_vars()
    _im_boss_frames = []
    _im_fields_built = False

    root.configure(bg=C("BG"))

    # ── Top bar
    top = tk.Frame(root, bg=C("BG"))
    top.pack(fill="x", padx=16, pady=(12,6))
    tk.Label(top, text=APP_NAME, bg=C("BG"), fg=C("TEXT"),
             font=("Segoe UI",20,"bold")).pack(side="left")
    tk.Label(top, text=CREDIT_TEXT, bg=C("BG"), fg=C("MUTED"),
             font=("Segoe UI",9)).pack(side="left", padx=(10,0), pady=(6,0))
    tk.Label(top, text="v0.6-portable", bg=C("PANEL_2"), fg=C("MUTED"),
             font=("Arial",9,"bold"), padx=10, pady=5).pack(side="right")

    # ── Notebook
    nb = ttk.Notebook(root)
    nb.pack(fill="both", expand=True, padx=16, pady=(0,12))
    style = ttk.Style()
    style.configure("TNotebook", background=C("BG"), borderwidth=0)
    style.configure("TNotebook.Tab", background=C("PANEL_2"), foreground=C("TEXT"),
                    padding=[16,6], font=("Arial",10,"bold"))
    style.map("TNotebook.Tab",
              background=[("selected", C("ACCENT"))],
              foreground=[("selected","#ffffff")])

    # ─── TAB 1: Text Mode ─────────────────────────────────────
    tab_text = tk.Frame(nb, bg=C("BG"))
    nb.add(tab_text, text="  📝 Text Mode  ")

    # Scrollable wrapper
    tc = tk.Canvas(tab_text, bg=C("BG"), highlightthickness=0)
    ts = tk.Scrollbar(tab_text, orient="vertical", command=tc.yview)
    tc.configure(yscrollcommand=ts.set)
    ts.pack(side="right", fill="y")
    tc.pack(side="left", fill="both", expand=True)
    tsf = tk.Frame(tc, bg=C("BG"))
    tcw = tc.create_window((0,0), window=tsf, anchor="nw")
    tsf.bind("<Configure>", lambda e: tc.configure(scrollregion=tc.bbox("all")))
    tc.bind("<Configure>", lambda e: tc.itemconfig(tcw, width=e.width))
    tc.bind_all("<MouseWheel>", lambda e: tc.yview_scroll(int(-1*(e.delta/120)),"units"))

    # Instructions
    inst = tk.Frame(tsf, bg=C("PANEL"), highlightbackground=C("BORDER"), highlightthickness=1)
    inst.pack(fill="x", padx=4, pady=(8,8))
    tk.Label(inst,
        text=("How to use Text Mode:\n"
              "1. In Discord run wboss i, copy Boss 1 message → paste into Boss 1\n"
              "2. Click Next, copy Boss 2 → Boss 2, repeat for Boss 3\n"
              "3. Enter HP values (optional, leave blank for 80000)\n"
              "4. Click Generate & Copy"),
        bg=C("PANEL"), fg=C("MUTED"), justify="left", anchor="w", font=("Segoe UI",9)
    ).pack(fill="x", padx=12, pady=10)

    mf = tk.Frame(tsf, bg=C("BG")); mf.pack(fill="x", padx=4)

    boss1_text = create_text_boss_section(mf, "Boss 1 Info",
        "Paste the first boss message here.", "Next → Boss 2",
        lambda: _text_widgets["boss2"].focus_set())
    boss2_text = create_text_boss_section(mf, "Boss 2 Info",
        "Paste the second boss message here.", "Next → Boss 3",
        lambda: _text_widgets["boss3"].focus_set())
    boss3_text = create_text_boss_section(mf, "Boss 3 Info",
        "Paste the third boss message here.", "Next → HP",
        lambda: _text_widgets["hp1"].focus_set())

    hp_frame = tk.Frame(tsf, bg=C("PANEL"),
                        highlightbackground=C("BORDER"), highlightthickness=1)
    hp_frame.pack(fill="x", padx=4, pady=(6,8))
    tk.Label(hp_frame, text="Boss HP Values", bg=C("PANEL"), fg=C("TEXT"),
             font=("Segoe UI",11,"bold")).grid(row=0, column=0, columnspan=6,
                                            sticky="w", padx=10, pady=(9,2))
    tk.Label(hp_frame, text="Optional – leave blank for 80 000. Accepts 90k / 90000.",
             bg=C("PANEL"), fg=C("MUTED"), font=("Segoe UI",8)
             ).grid(row=1, column=0, columnspan=6, sticky="w", padx=10, pady=(0,8))
    hp1 = make_hp_entry_text(hp_frame, "Boss 1 HP:", 0)
    hp2 = make_hp_entry_text(hp_frame, "Boss 2 HP:", 2)
    hp3 = make_hp_entry_text(hp_frame, "Boss 3 HP:", 4)

    bf = tk.Frame(tsf, bg=C("BG")); bf.pack(fill="x", padx=4, pady=(0,8))

    def text_generate():
        try:
            texts = [
                boss1_text.get("1.0", tk.END).strip(),
                boss2_text.get("1.0", tk.END).strip(),
                boss3_text.get("1.0", tk.END).strip(),
            ]
            blocks = []
            for t in texts:
                blocks.extend(split_boss_blocks(t))
            if len(blocks) != 3:
                raise ValueError(f"Expected 3 bosses, found {len(blocks)}.\nPaste one boss per box.")
            bosses    = [parse_boss(b) for b in blocks]
            hp_values = [normalize_hp(e.get()) for e in [hp1, hp2, hp3]]
            qe        = round(sum(b["quality"] for b in bosses)/3)
            command   = ("neon b myself vs " + ", ".join(b["part"] for b in bosses)
                         + " -hp " + " ".join(hp_values)
                         + f" -m -qe{qe}")
            _text_widgets["output"].delete("1.0", tk.END)
            _text_widgets["output"].insert(tk.END, command)
            warns = [w for b in bosses for w in b["warnings"]]
            _text_widgets["warnings"].delete("1.0", tk.END)
            if warns:
                _text_widgets["warnings"].insert(tk.END, "\n".join(warns))
                _text_widgets["status"].config(text="Generated with warnings.", fg=C("DANGER"))
            else:
                _text_widgets["warnings"].insert(tk.END, "No warnings.")
                _text_widgets["status"].config(text="Command generated and copied.", fg=C("GREEN"))
            root.clipboard_clear(); root.clipboard_append(command)
        except Exception as e:
            _text_widgets["status"].config(text="Error.", fg=C("DANGER"))
            messagebox.showerror("Error", str(e))

    def text_copy():
        cmd = _text_widgets["output"].get("1.0", tk.END).strip()
        if not cmd: messagebox.showinfo("Nothing", "Generate first."); return
        root.clipboard_clear(); root.clipboard_append(cmd)
        _text_widgets["status"].config(text="Copied.", fg=C("GREEN"))

    def text_clear():
        for b in [boss1_text, boss2_text, boss3_text,
                  _text_widgets["output"], _text_widgets["warnings"]]:
            b.delete("1.0", tk.END)
        for e in [hp1, hp2, hp3]: e.delete(0, tk.END)
        _text_widgets["warnings"].insert(tk.END, "No command generated yet.")
        _text_widgets["status"].config(text="Cleared.", fg=C("MUTED"))

    make_btn(bf, "⚡ Generate & Copy", text_generate, padx=20, pady=8).pack(side="left", padx=(0,8))
    make_btn(bf, "Copy", text_copy, "PANEL_2", 14, 8).pack(side="left", padx=(0,8))
    make_btn(bf, "Clear All", text_clear, "PANEL_2", 14, 8).pack(side="left")
    sl = tk.Label(bf, text="Ready.", bg=C("BG"), fg=C("MUTED"), font=("Segoe UI",9))
    sl.pack(side="right")

    # Output / Warnings
    for title, key, h in [("Generated Command","output",3),("Warnings","warnings",2)]:
        of = tk.Frame(tsf, bg=C("PANEL"),
                      highlightbackground=C("BORDER"), highlightthickness=1)
        of.pack(fill="x", padx=4, pady=(0,8))
        tk.Label(of, text=title, bg=C("PANEL"), fg=C("TEXT"),
                 font=("Segoe UI",11,"bold")).pack(anchor="w", padx=10, pady=(8,3))
        tb = tk.Text(of); style_text(tb, h); tb.pack(fill="x", padx=10, pady=(0,10))
        _text_widgets[key] = tb

    # Restore state
    boss1_text.insert("1.0", state.get("boss1",""))
    boss2_text.insert("1.0", state.get("boss2",""))
    boss3_text.insert("1.0", state.get("boss3",""))
    hp1.insert(0, state.get("hp1","")); hp2.insert(0, state.get("hp2","")); hp3.insert(0, state.get("hp3",""))
    _text_widgets["output"].insert("1.0", state.get("output",""))
    _text_widgets["warnings"].insert("1.0", state.get("warnings","No command generated yet."))
    _text_widgets["boss2"] = boss2_text
    _text_widgets["boss3"] = boss3_text
    _text_widgets["hp1"]   = hp1
    _text_widgets["status"] = sl

    # ─── TAB 2: Image Mode ────────────────────────────────────
    # Load asset icons now (Tk root exists, PhotoImages are safe to create).
    load_icon_cache()

    tab_img = tk.Frame(nb, bg=C("BG"))
    nb.add(tab_img, text="  📸 Image Mode  ")

    # Scrollable wrapper for image tab
    ic = tk.Canvas(tab_img, bg=C("BG"), highlightthickness=0)
    isc = tk.Scrollbar(tab_img, orient="vertical", command=ic.yview)
    ic.configure(yscrollcommand=isc.set)
    isc.pack(side="right", fill="y")
    ic.pack(side="left", fill="both", expand=True)
    isf = tk.Frame(ic, bg=C("BG"))
    icw = ic.create_window((0,0), window=isf, anchor="nw")
    isf.bind("<Configure>", lambda e: ic.configure(scrollregion=ic.bbox("all")))
    ic.bind("<Configure>", lambda e: ic.itemconfig(icw, width=e.width))

    if not IMAGE_LIBS_OK:
        tk.Label(isf,
            text="⚠  Image mode requires: opencv-python, pytesseract, pillow, rapidfuzz\n"
                 "pip install opencv-python pytesseract pillow rapidfuzz",
            bg=C("BG"), fg=C("DANGER"), font=("Arial",11), justify="center"
        ).pack(pady=60)
    else:
        # ── Drop Zone
        dz_outer = tk.Frame(isf, bg=C("PANEL"),
                             highlightbackground=C("ACCENT"), highlightthickness=2)
        dz_outer.pack(fill="x", padx=8, pady=(12,0))

        dz = tk.Label(dz_outer,
            text="📷  Drop a local screenshot here\nClick to browse, or press Ctrl+V after copying an image from Discord",
            bg=C("PANEL"), fg=C("MUTED"),
            font=("Segoe UI",13), pady=24, cursor="hand2")
        dz.pack(fill="x")

        im_status = tk.Label(isf, text="No image loaded.",
                             bg=C("BG"), fg=C("MUTED"), font=("Segoe UI",9))
        im_status.pack(anchor="w", padx=12, pady=(6,0))
        _im_widgets["status"] = im_status

        # ── Boss fields container (built after image processing)
        fields_frame = tk.Frame(isf, bg=C("BG"))
        fields_frame.pack(fill="x", padx=8, pady=(10,0))

        # ── Bottom action row
        ab = tk.Frame(isf, bg=C("BG"))
        ab.pack(fill="x", padx=8, pady=(10,8))

        browse_btn = make_btn(ab, "Browse Image", lambda: _browse(), "PANEL_2", padx=16, pady=8)
        browse_btn.pack(side="left", padx=(0,8))

        paste_btn = make_btn(ab, "Paste Image (Ctrl+V)", lambda: _load_image_from_clipboard(), "PANEL_2", padx=16, pady=8)
        paste_btn.pack(side="left", padx=(0,8))

        gen_btn = make_btn(ab, "⚡ Generate & Copy", lambda: _im_generate_copy(im_status),
                           padx=20, pady=8)
        gen_btn.pack(side="left", padx=(0,8))
        _im_widgets["gen_btn"] = gen_btn

        # ── Output
        out_frame = tk.Frame(isf, bg=C("PANEL"),
                             highlightbackground=C("BORDER"), highlightthickness=1)
        out_frame.pack(fill="x", padx=8, pady=(0,12))
        tk.Label(out_frame, text="Generated Command", bg=C("PANEL"), fg=C("TEXT"),
                 font=("Segoe UI",11,"bold")).pack(anchor="w", padx=10, pady=(8,3))
        out_tb = tk.Text(out_frame); style_text(out_tb, 3)
        out_tb.pack(fill="x", padx=10, pady=(0,10))
        _im_widgets["output"] = out_tb

        def _build_boss_fields(results):
            """Build/rebuild the 3-column editable boss fields after detection."""
            global _im_fields_built
            for child in fields_frame.winfo_children():
                child.destroy()
            _populate_im_vars(results)
            _im_fields_built = True

            # Header row
            for i in range(3):
                hdr = tk.Frame(fields_frame, bg=C("PANEL"),
                               highlightbackground=C("BORDER"), highlightthickness=1)
                hdr.grid(row=0, column=i, padx=4, pady=4, sticky="nsew")
                fields_frame.columnconfigure(i, weight=1)

                animal_val = results[i].get("animal","?")
                lvl_val    = results[i].get("level","?")
                rarity_val = results[i].get("rarity","")
                dead_val   = results[i].get("dead", False)
                dead_tag   = "  💀 DEAD" if dead_val else ""

                tk.Label(hdr,
                    text=f"Boss {i+1}{dead_tag}",
                    bg=C("PANEL"), fg=C("DANGER") if dead_val else C("ACCENT"),
                    font=("Segoe UI",11,"bold")).pack(anchor="w", padx=10, pady=(8,2))
                tk.Label(hdr,
                    text=f"Lvl {lvl_val}  {rarity_val} {animal_val}".strip(),
                    bg=C("PANEL"), fg=C("MUTED"),
                    font=("Segoe UI",8)).pack(anchor="w", padx=10, pady=(0,8))

                v = _im_vars[i]
                rows = [
                    ("Level",    "level", None),
                    ("Animal",   "animal", ANIMALS),
                    ("Weapon",   "weapon", WEAPON_SHORTCUTS),
                    ("Passive 1","p1",     PASSIVE_SHORTCUTS),
                    ("Passive 2","p2",     PASSIVE_SHORTCUTS),
                    ("Passive 3","p3",     PASSIVE_SHORTCUTS),  # collapsed if empty
                    ("HP",       "hp",     None),
                    ("QE",       "qe",     None),
                ]
                for label, key, choices in rows:
                    row = tk.Frame(hdr, bg=C("PANEL"))
                    row.pack(fill="x", padx=10, pady=2)
                    tk.Label(row, text=label+":", bg=C("PANEL"), fg=C("MUTED"),
                             width=10, anchor="w", font=("Segoe UI",9)).pack(side="left")
                    if choices is not None:
                        # Pick icon dict: weapons or passives
                        if key == "weapon":
                            icons_d = _icon_cache.get("weapons", {})
                        elif key in ("p1", "p2", "p3"):
                            icons_d = _icon_cache.get("passives", {})
                        else:
                            icons_d = {}
                        if icons_d:
                            items = [""] + [c for c in choices if c]
                            cb = IconComboBox(row, v[key], items, icons_d)
                            cb.pack(side="left", fill="x", expand=True, ipady=3)
                        else:
                            cb = make_combo(row, [""] + choices, v[key], width=16)
                            cb.pack(side="left", fill="x", expand=True, ipady=3)
                    else:
                        e = tk.Entry(row, textvariable=v[key], width=18,
                                     bg=C("INPUT_BG"), fg=C("TEXT"),
                                     insertbackground=C("TEXT"),
                                     relief="flat", font=("Consolas",9))
                        e.pack(side="left", fill="x", expand=True, ipady=3)

                tk.Frame(hdr, bg=C("PANEL"), height=8).pack()

            # Enable generate button
            _im_widgets["gen_btn"].config(state="normal")

        def _run_detection(path):
            try:
                im_status.config(text="⏳  Processing image...", fg=C("MUTED"))
                results = process_image(path)
                root.after(0, lambda: _build_boss_fields(results))
                root.after(0, lambda: im_status.config(
                    text=f"✓  Processed: {os.path.basename(path)}  "
                         f"(card styles: {', '.join('white' if r.get('dead') is not None else 'dark' for r in results)})",
                    fg=C("GREEN")))
                # Auto-generate and copy
                root.after(50, lambda: _im_generate_copy(im_status, auto=True))
            except Exception as ex:
                root.after(0, lambda: im_status.config(
                    text=f"✗  Error: {ex}", fg=C("DANGER")))

        def _clean_dropped_path(raw):
            """
            tkinterdnd2 returns paths differently depending on source:
            C:/file.png
            {C:/file with spaces.png}
            {C:/one.png} {C:/two.png}
            We only need the first file.
            """
            raw = str(raw).strip()

            if raw.startswith("{"):
                m = re.match(r"^\{(.+?)\}", raw)
                if m:
                    return m.group(1)

            # Fallback for normal file paths.
            return raw.strip("{}").strip().strip('"')

        def _load_image(path):
            path = _clean_dropped_path(path)

            if not os.path.isfile(path):
                im_status.config(
                    text="✗  Could not load that image. If dragging from Discord does not work, right-click the image, Copy Image, then press Ctrl+V here.",
                    fg=C("DANGER")
                )
                return

            # Update drop zone preview.
            try:
                img = PILImage.open(path)
                img.thumbnail((620, 130), PILImage.LANCZOS)
                photo = ImageTk.PhotoImage(img)
                dz.config(image=photo, text="", pady=5)
                dz.image = photo
            except Exception:
                dz.config(image="", text=f"📷 {os.path.basename(path)}", pady=20)

            t = threading.Thread(target=_run_detection, args=(path,), daemon=True)
            t.start()

        def _load_image_from_clipboard(event=None):
            """
            Reliable Discord workflow:
            Right-click image in Discord → Copy Image
            Then click Image Mode and press Ctrl+V.
            """
            try:
                clip = ImageGrab.grabclipboard()
            except Exception:
                clip = None

            if isinstance(clip, PILImage.Image):
                temp_path = os.path.join(
                    tempfile.gettempdir(),
                    "owo_boss_clipboard_image.png"
                )
                clip.convert("RGBA").save(temp_path)
                _load_image(temp_path)
                return "break"

            if isinstance(clip, list) and clip:
                for item in clip:
                    if os.path.isfile(item):
                        _load_image(item)
                        return "break"

            im_status.config(
                text="✗  No image found in clipboard. Try right-click image in Discord → Copy Image, then Ctrl+V.",
                fg=C("DANGER")
            )
            return "break"

        # Drag-and-drop
        if HAS_DND:
            dz.drop_target_register(DND_FILES)
            dz.dnd_bind("<<Drop>>", lambda e: _load_image(e.data))
            dz_outer.drop_target_register(DND_FILES)
            dz_outer.dnd_bind("<<Drop>>", lambda e: _load_image(e.data))

        # Click to browse
        def _browse():
            path = filedialog.askopenfilename(
                title="Select Boss Screenshot",
                filetypes=[("Images","*.png *.jpg *.jpeg *.webp *.bmp"),("All files","*.*")])
            if path: _load_image(path)

        dz.bind("<Button-1>", lambda e: _browse())
        dz_outer.bind("<Button-1>", lambda e: _browse())
        root.bind_all("<Control-v>", _load_image_from_clipboard)
        root.bind_all("<Control-V>", _load_image_from_clipboard)

        if not HAS_DND:
            tk.Label(isf,
                text="ℹ  Local file drag-and-drop needs tkinterdnd2. Discord images usually work best with Copy Image → Ctrl+V.",
                bg=C("BG"), fg=C("MUTED"), font=("Segoe UI",8)).pack(anchor="w", padx=12)

def _im_generate_copy(status_label, auto=False):
    if not _im_fields_built and not auto: return
    try:
        cmd = _build_command_from_im()
        _im_widgets["output"].delete("1.0", tk.END)
        _im_widgets["output"].insert(tk.END, cmd)
        root.clipboard_clear(); root.clipboard_append(cmd)
        _im_widgets["status"].config(
            text="✓  Command generated and copied to clipboard!", fg=C("GREEN"))
    except Exception as e:
        messagebox.showerror("Error", str(e))

def toggle_theme():
    # Dark-only UI for now.
    build_ui()

# ─── Root window ─────────────────────────────────────────────
if HAS_DND:
    root = TkinterDnD.Tk()
else:
    root = tk.Tk()

root.title(APP_NAME)
root.geometry("1120x820")
root.minsize(900, 640)

try:
    ip = resource_path(ICON_FILE)
    if os.path.exists(ip):
        root.iconbitmap(ip)
        root.wm_iconbitmap(ip)
        # Force Windows taskbar + title-bar icon via ctypes (works in .exe too)
        try:
            from ctypes import windll
            import ctypes
            hwnd = ctypes.windll.user32.GetParent(root.winfo_id())
            ico  = ctypes.windll.user32.LoadImageW(
                0, ip, 1, 0, 0, 0x00000010 | 0x00000040  # LR_LOADFROMFILE | LR_DEFAULTSIZE
            )
            if ico:
                ctypes.windll.user32.SendMessageW(hwnd, 0x0080, 1, ico)  # WM_SETICON ICON_BIG
                ctypes.windll.user32.SendMessageW(hwnd, 0x0080, 0, ico)  # WM_SETICON ICON_SMALL
        except Exception:
            pass
except Exception:
    pass

build_ui()
root.mainloop()