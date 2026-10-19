import os
import time
import random
import pygame
import keyboard
import mouse

# ---------------- Settings ----------------
SPECIAL_KEYS_FOLDER_NAME = "Special Keys"  # Folder that holds Alt, Back, CTRL, Enter, ESC, Number, Shift, StopHolding
STOP_HOLDING_MIN_SECONDS = 0.35            # A key must be held at least this long for StopHolding to play on release
# ------------------------------------------

# Initialize the mixer with a small buffer for low latency and many channels for spamming
pygame.mixer.pre_init(44100, -16, 2, 512)
pygame.mixer.init()
pygame.mixer.set_num_channels(32)

AUDIO_EXTENSIONS = (".mp3", ".wav", ".ogg")

# Get the directory where this script is located
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))

KEYBOARD_SOUNDS_DIR = os.path.join(CURRENT_DIR, "Keyboard Sounds")
SPECIAL_KEYS_DIR = os.path.join(CURRENT_DIR, SPECIAL_KEYS_FOLDER_NAME)
SPACEBAR_SOUND_PATH = os.path.join(CURRENT_DIR, "Spacebar Click.mp3")
MOUSE_LEFT_SOUND_PATH = os.path.join(CURRENT_DIR, "Mouse Sounds", "Mouse Click Left.mp3")
MOUSE_RIGHT_SOUND_PATH = os.path.join(CURRENT_DIR, "Mouse Sounds", "Mouse Click Right.mp3")


def load_sound(path):
    try:
        return pygame.mixer.Sound(path)
    except Exception as e:
        print(f"Could not load {os.path.basename(path)}: {e}")
        return None


# Preload all regular keyboard sounds
keyboard_sounds = []
if os.path.exists(KEYBOARD_SOUNDS_DIR):
    for f in os.listdir(KEYBOARD_SOUNDS_DIR):
        if f.lower().endswith(AUDIO_EXTENSIONS):
            sound = load_sound(os.path.join(KEYBOARD_SOUNDS_DIR, f))
            if sound:
                keyboard_sounds.append(sound)

# Preload special key sounds, matched by file name (extension is ignored)
SPECIAL_SOUND_NAMES = ["alt", "back", "ctrl", "enter", "esc", "number", "shift", "stopholding"]
special_sounds = {}

if os.path.exists(SPECIAL_KEYS_DIR):
    for f in os.listdir(SPECIAL_KEYS_DIR):
        stem, ext = os.path.splitext(f)
        if ext.lower() in AUDIO_EXTENSIONS and stem.lower() in SPECIAL_SOUND_NAMES:
            sound = load_sound(os.path.join(SPECIAL_KEYS_DIR, f))
            if sound:
                special_sounds[stem.lower()] = sound
else:
    print(f"WARNING: Special keys folder not found: {SPECIAL_KEYS_DIR}")

spacebar_sound = load_sound(SPACEBAR_SOUND_PATH) if os.path.exists(SPACEBAR_SOUND_PATH) else None
mouse_left_sound = load_sound(MOUSE_LEFT_SOUND_PATH) if os.path.exists(MOUSE_LEFT_SOUND_PATH) else None
mouse_right_sound = load_sound(MOUSE_RIGHT_SOUND_PATH) if os.path.exists(MOUSE_RIGHT_SOUND_PATH) else None

print(f"Loaded {len(keyboard_sounds)} regular keyboard sounds.")
print(f"Loaded special sounds: {', '.join(sorted(special_sounds)) or 'none'}")
print(f"Mouse sounds: left={'yes' if mouse_left_sound else 'NO'}, right={'yes' if mouse_right_sound else 'NO'}")

# Maps the key names reported by the keyboard library to the special sound names
KEY_TO_SPECIAL = {
    "alt": "alt",
    "alt gr": "alt",
    "backspace": "back",
    "ctrl": "ctrl",
    "enter": "enter",
    "esc": "esc",
    "shift": "shift",
}
NUMBER_KEYS = set("0123456789")

# Tracks held keys (scan code -> time pressed) to block auto-repeat spam
held_keys = {}


def normalize_key_name(name):
    if not name:
        return ""
    name = name.lower()
    for prefix in ("left ", "right "):
        if name.startswith(prefix):
            name = name[len(prefix):]
    return name


def get_key_sound(key_name):
    """Returns the sound for a key press: special sound first, then spacebar, then random regular."""
    if key_name in NUMBER_KEYS and "number" in special_sounds:
        return special_sounds["number"]

    special_name = KEY_TO_SPECIAL.get(key_name)
    if special_name and special_name in special_sounds:
        return special_sounds[special_name]

    if key_name == "space" and spacebar_sound:
        return spacebar_sound

    if keyboard_sounds:
        return random.choice(keyboard_sounds)
    return None


def handle_keyboard_event(event):
    key_id = event.scan_code
    key_name = normalize_key_name(event.name)

    try:
        if event.event_type == keyboard.KEY_DOWN:
            # Ignore Windows auto-repeat while a key is held down
            if key_id in held_keys:
                return
            held_keys[key_id] = time.time()

            sound = get_key_sound(key_name)
            if sound:
                sound.play()

        elif event.event_type == keyboard.KEY_UP:
            pressed_at = held_keys.pop(key_id, None)

            # Only play StopHolding if we saw the key go down AND it was held long enough
            if pressed_at is None:
                return

            held_for = time.time() - pressed_at
            stop_sound = special_sounds.get("stopholding")
            if stop_sound and held_for >= STOP_HOLDING_MIN_SECONDS:
                stop_sound.play()
    except Exception as e:
        print(f"Error playing key sound: {e}")


def play_mouse_left_sound(*args):
    try:
        if mouse_left_sound:
            mouse_left_sound.play()
    except Exception as e:
        print(f"Error playing left mouse sound: {e}")


def play_mouse_right_sound(*args):
    try:
        if mouse_right_sound:
            mouse_right_sound.play()
    except Exception as e:
        print(f"Error playing right mouse sound: {e}")


# Register hooks (remember to run the terminal as Administrator on Windows)
keyboard.hook(handle_keyboard_event)

# 'double' is required because Windows reports fast repeated clicks as double-click events
mouse.on_button(play_mouse_left_sound, buttons=["left"], types=("down", "double"))
mouse.on_button(play_mouse_right_sound, buttons=["right"], types=("down", "double"))

print("Keyboard & Mouse Sound FX Running! Press TAB to stop.")
keyboard.wait("tab")