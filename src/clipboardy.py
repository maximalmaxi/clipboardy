import os
import json
import pyperclip
import base64
import time
import threading
from datetime import datetime
from cryptography.fernet import Fernet
import validators
import customtkinter as ctk

# File paths
SAVE_FILE = 'package/clips.json'
KEY_FILE = 'package/key.key'
SETTINGS_FILE = 'package/settings.json'

# Global variables
clipsObj = []
cryptKey = None
autosave = False
# Just an example setting to showcase the new settings functionality thats now supporting multiple settings.
setting2 = False
lastClip = None

def load_settings():
    """Load autosave setting from settings file."""
    global autosave, setting2
    if os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, 'r') as settings_file:
            try:
                settings = json.load(settings_file)
                autosave = settings.get("autosave", False)
                setting2 = settings.get("setting2", False)
            except json.JSONDecodeError:
                print("Settings file is corrupted. Using default settings.")
    return False

def save_settings():
    """Save current settings to settings file."""
    with open(SETTINGS_FILE, 'w') as settings_file:
        json.dump({
            "autosave": autosave,
            "setting2": setting2,
        }, settings_file)

def generate_key():
    """Generate and save encryption key."""
    generatedKey = Fernet.generate_key()
    with open(KEY_FILE, 'wb') as keyfile:
        keyfile.write(generatedKey)
    return generatedKey

def load_key():
    """Load encryption key from file."""
    with open(KEY_FILE, 'rb') as securekey:
        return securekey.read()

def load_clips():
    """Load saved clipboard clips."""
    if not os.path.exists(SAVE_FILE):
        with open(SAVE_FILE, 'w') as fp:
            json.dump([], fp)
        return []

    if os.stat(SAVE_FILE).st_size != 0:
        with open(SAVE_FILE, 'r') as fp:
            try:
                return json.load(fp)
            except json.JSONDecodeError:
                return []
    return []

def save_clips():
    """Save clipboard clips to file."""
    with open(SAVE_FILE, 'w') as json_file:
        json.dump(clipsObj, json_file, indent=4, separators=(',', ': '))

def encrypt_clip(clip):
    """Encrypt clipboard content."""
    return base64.urlsafe_b64encode(Fernet(cryptKey).encrypt(clip.encode())).decode()

def decrypt_clip(encrypted_clip):
    """Decrypt encrypted clipboard content."""
    return Fernet(cryptKey).decrypt(base64.urlsafe_b64decode(encrypted_clip)).decode()

def populate_clips_table(frame, clips_to_display=None):
    """Update the UI table with clipboard clips."""
    for widget in frame.winfo_children():
        widget.destroy()

    frame.grid_columnconfigure(0, weight=1)
    frame.grid_columnconfigure(1, weight=3)
    frame.grid_columnconfigure(2, weight=1)
    frame.grid_columnconfigure(3, weight=1)
    frame.grid_columnconfigure(4, weight=1)

    clips_to_display = clips_to_display if clips_to_display is not None else clipsObj

    for index, clip in enumerate(clips_to_display):
        decrypted_clip = decrypt_clip(clip['clip'])
        
        # Display clip data in the table
        ctk.CTkLabel(frame, text=clip['date']).grid(row=index, column=0, padx=5, pady=5, sticky='w')
        ctk.CTkLabel(frame, text=decrypted_clip).grid(row=index, column=1, padx=5, pady=5, sticky='w')
        ctk.CTkLabel(frame, text=clip['type']).grid(row=index, column=2, padx=5, pady=5, sticky='w')
        
        ctk.CTkButton(frame, text="🗒️", command=lambda c=decrypted_clip: pyperclip.copy(c), width=20).grid(row=index, column=3, padx=5, pady=5, sticky='e')
        ctk.CTkButton(frame, text="❌", command=lambda i=index: delete_clip_from_ui(i), width=20).grid(row=index, column=4, padx=5, pady=5, sticky='e')

def delete_clip_from_ui(index):
    """Delete a clip from the list and update UI."""
    if 0 <= index < len(clipsObj):
        clipsObj.pop(index)
        save_clips()
        populate_clips_table(clips_frame)

def UI():
    """Initialize and display the main UI."""
    global autosave_loading, inputbar
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("green")

    app = ctk.CTk()
    app.geometry("700x525")
    app.title("Clipboardy")

    autosave_loading = True

    ctk.CTkLabel(app, text="Clipboardy", font=('Calibri', 20)).pack()

    mainframe = ctk.CTkFrame(master=app, width=670, height=400)
    mainframe.pack(pady="10")
    mainframe.pack_propagate(False)

    inputbar = ctk.CTkEntry(mainframe, placeholder_text="Search your clips", width=650, height=30)
    inputbar.pack(pady="10")
    inputbar.bind("<KeyRelease>", search_clips)

    global clips_frame
    clips_frame = ctk.CTkScrollableFrame(mainframe)
    clips_frame.pack(pady="10", fill="both", expand=True)

    headers = ["Date", "Clip", "Type", "Copy", "Delete"]
    for i, header in enumerate(headers):
        ctk.CTkLabel(clips_frame, text=header).grid(row=0, column=i, padx=5, pady=5)

    populate_clips_table(clips_frame)

    status_frame = ctk.CTkFrame(master=app, width=670, height=40)
    status_frame.pack(pady="5")
    status_frame.pack_propagate(False)

    switch = ctk.CTkSwitch(app, text="Auto Save", command=toggle_autosave)
    switch.pack(side="right", padx="10")
    switch.select() if autosave else switch.deselect()

    autosave_loading = False

    button_frame = ctk.CTkFrame(status_frame)
    button_frame.pack(side="left", expand=True)

    ctk.CTkButton(button_frame, text="Save clip", command=save_clip).pack(padx=5, side="left")
    ctk.CTkButton(button_frame, text="Delete all", command=delete_all_clips).pack(padx=5, side="left")
    ctk.CTkButton(button_frame, text="Settings", command=toggle_setting2).pack(padx=5, side="left")

    ctk.CTkLabel(app, text="🟢 Status: Running").pack(side="left", padx="10")

    app.mainloop()

def toggle_setting2():
    """Toggle setting2"""
    global setting2
    setting2 = not setting2
    save_settings()

def toggle_autosave():
    """Enable or disable autosave and save the setting."""
    global autosave, autosave_loading
    if not autosave_loading:
        autosave = not autosave
        save_settings()

def save_clip():
    """Save current clipboard content if available."""
    current_clip = pyperclip.paste()
    content_type = determine_content_type(current_clip)

    if current_clip:
        encrypted_clip = encrypt_clip(current_clip)
        current_date = datetime.now().strftime("%Y-%m-%d")
        clipsObj.append({"clip": encrypted_clip, "date": current_date, "type": content_type})
        save_clips()
        populate_clips_table(clips_frame)
    else:
        print("No new clip to save.")

def determine_content_type(current_clip):
    """Detect content type (URL, Email, etc.) in clipboard content."""
    validators_map = {
        "URL": validators.url,
        "Email": validators.email,
        "IPv4": validators.ipv4,
        "IPv6": validators.ipv6,
        "Credit Card": validators.card_number,
    }
    
    for content_type, validator in validators_map.items():
        if validator(current_clip):
            return content_type
    
    return "Text"

def delete_all_clips():
    """Clear all clips and refresh UI."""
    global clipsObj
    clipsObj = []
    save_clips()
    populate_clips_table(clips_frame)

def search_clips(event=None):
    """Filter displayed clips based on search input."""
    search_term = inputbar.get().lower()
    filtered_clips = [
        clip for clip in clipsObj if search_term in decrypt_clip(clip['clip']).lower()
    ]
    populate_clips_table(clips_frame, filtered_clips)

def main():
    """Initialize and run the application."""
    global cryptKey, clipsObj, lastClip, autosave

    load_settings()

    if not os.path.exists(KEY_FILE):
        cryptKey = generate_key()
        print("Generated a new encryption key.")
    else:
        cryptKey = load_key()

    clipsObj = load_clips()

    monitor_thread = threading.Thread(target=monitor_clipboard, daemon=True)
    monitor_thread.start()

    UI()

def monitor_clipboard():
    """Monitor clipboard changes and save new clips if autosave is enabled."""
    global lastClip
    lastClip = pyperclip.paste()
    
    while True:
        if autosave:
            current_clip = pyperclip.paste()
            if current_clip != lastClip and current_clip not in [decrypt_clip(clip['clip']) for clip in clipsObj] and lastClip is not None:
                save_clip()
                lastClip = current_clip
        time.sleep(1)

if __name__ == "__main__":
    main()
