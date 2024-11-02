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
import textwrap
from tkinter import messagebox
import sys

# File paths
PACKAGE_FOLDER = 'package'
SAVE_FILE = 'package/clips.json'
KEY_FILE = 'package/key.key'
SETTINGS_FILE = 'package/settings.json'

# Global variables
clipsObj = []
cryptKey = None
autosave = False
darkmode = False
lastClip = None
selected_type_filter = "All"

if not os.path.exists(PACKAGE_FOLDER):
    response = messagebox.askyesno('No package folder found', 'Could not find folder named "package". Should clipboardy create the folder in this directory? It is necessary for it to work.')
    if response:
        os.makedirs(PACKAGE_FOLDER)
    else:
        messagebox.showinfo('Did not create folder "package"', 'Make sure to have a folder named "package" in the same directory as clipboardy for it to work.')
        sys.exit()
def load_settings():
    """Load autosave setting from settings file."""
    global autosave, darkmode
    if os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, 'r') as settings_file:
            try:
                settings = json.load(settings_file)
                autosave = settings.get("autosave", False)
                darkmode = settings.get("darkmode", False)
            except json.JSONDecodeError:
                print("Settings file is corrupted. Using default settings.")
    return False

def save_settings():
    """Save current settings to settings file."""
    with open(SETTINGS_FILE, 'w') as settings_file:
        json.dump({
            "autosave": autosave,
            "darkmode": darkmode,
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

        short_clip = textwrap.shorten(decrypted_clip, width=55, placeholder="...")
        
        # Display clip data in the table
        ctk.CTkLabel(frame, text=clip['date']).grid(row=index, column=0, padx=5, pady=5, sticky='w')
        ctk.CTkLabel(frame, text=short_clip).grid(row=index, column=1, padx=5, pady=5, sticky='w')
        ctk.CTkLabel(frame, text=clip['type']).grid(row=index, column=2, padx=5, pady=5, sticky='w')
        
        ctk.CTkButton(frame, text="📝", command=lambda c=decrypted_clip: pyperclip.copy(c), width=30).grid(row=index, column=3, padx=5, pady=5, sticky='e')
        ctk.CTkButton(frame, text="❌", command=lambda i=index: delete_clip_from_ui(i), width=30).grid(row=index, column=4, padx=5, pady=5, sticky='e')

def delete_clip_from_ui(index):
    """Delete a clip from the list and update UI."""
    if 0 <= index < len(clipsObj):
        clipsObj.pop(index)
        save_clips()
        populate_clips_table(clips_frame)

def UI():
    # Initialize and display the main UI
    global autosave_loading, inputbar, darkmode, filter_select, app, icon
    if darkmode:
        ctk.set_appearance_mode("dark")
    else:
        ctk.set_appearance_mode("light")
    ctk.set_default_color_theme("green")

    app = ctk.CTk()
    app.geometry("700x525")
    app.title("Clipboardy")

    autosave_loading = True

    ctk.CTkLabel(app, text="Clipboardy", font=('Calibri', 20)).pack()

    mainframe = ctk.CTkFrame(master=app, width=670, height=400)
    mainframe.pack(pady="10")
    mainframe.pack_propagate(False)

    # Define a frame for the input bar and filter, then pack them in one row
    input_frame = ctk.CTkFrame(mainframe)
    input_frame.pack(pady=10)

    inputbar = ctk.CTkEntry(input_frame, placeholder_text="Search your clips", width=520, height=30)
    filter_select = ctk.CTkComboBox(input_frame, values=["All", "Text", "URL", "Email", "IPv4", "IPv6", "Credit Card"], command=apply_filter ,width=110)
    filter_select.set("All")
    
    inputbar.pack(side="left", padx=(10, 5))
    filter_select.pack(side="left", padx=(5, 10))

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
    ctk.CTkButton(button_frame, text="Settings", command=settings_UI).pack(padx=5, side="left")

    ctk.CTkLabel(app, text="🟢 Status: Running").pack(side="left", padx="10")

    app.mainloop()

def settings_UI():
    settingsUI = ctk.CTk()
    settingsUI.geometry("400x400")
    settingsUI.title("Settings")

    ctk.CTkLabel(settingsUI, text="Settings", font=('Calibri', 20)).pack(pady=(10, 5))

    appearance_frame = ctk.CTkFrame(settingsUI)
    appearance_frame.pack(pady=10, padx=10, fill='x')

    ctk.CTkLabel(appearance_frame, text="Appearance", font=('Calibri', 18)).pack(pady=0)

    switch = ctk.CTkSwitch(appearance_frame, text="Dark Mode", command=toggle_darkmode)
    switch.pack(pady=5)
    switch.select() if darkmode else switch.deselect()

    danger_frame = ctk.CTkFrame(settingsUI)
    danger_frame.pack(pady=10, padx=10, fill='x')

    ctk.CTkLabel(danger_frame, text="Danger Zone", font=('Calibri', 18)).pack(pady=0)

    delete_btn = ctk.CTkButton(danger_frame, text="Reset encryption key", command=delete_key)
    delete_btn.pack(pady=5)

    settingsUI.mainloop()

def delete_key():
    response = messagebox.askyesno('Resetting encryption key', 'THIS WILL RESET THE ENCRYPTION KEY, and with this all your clips. Are you sure?')

    if response:
        os.remove(KEY_FILE)
        os.remove(SAVE_FILE)
        messagebox.showinfo('Resetting encryption key', 'Resetted encryption key, please restart the program.')
        sys.exit()

def apply_filter(choice):
    """Update type filter based on user selection"""
    global selected_type_filter
    selected_type_filter = choice
    filtered_clips = [
        clip for clip in clipsObj
        if (selected_type_filter == "All" or clip["type"] == selected_type_filter)
    ]

    populate_clips_table(clips_frame, filtered_clips)

def toggle_darkmode():
    """Toggle darkmode"""
    global darkmode
    darkmode = not darkmode
    save_settings()
    refresh_ui()

def toggle_autosave():
    """Enable or disable autosave and save the setting."""
    global autosave, autosave_loading
    if not autosave_loading:
        autosave = not autosave
        save_settings()

def save_clip():
    """Save current clipboard content if available."""
    global filter_select
    filter_select.set("All")

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

def refresh_ui():
    """Refresh UI appearance mode."""
    if darkmode:
        ctk.set_appearance_mode("dark")
    else:
        ctk.set_appearance_mode("light")

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
        time.sleep(2)

if __name__ == "__main__":
    main()
