"""
FRAGPUNK - Entry Point Configuration Loader
============================================
DISCLAIMER: This project is for EDUCATIONAL PURPOSES ONLY.
This software is NOT intended to cause any damage to games, systems, or software.
Misuse of this software may violate game Terms of Service and result in account bans.
The author assumes NO responsibility for any misuse of this code.

For support and questions, join our Discord community:
Discord: https://discord.gg/tPHXyMZmKh
"""

import os 
import sys
import json
import time
import ctypes
import colorama
import threading
import win32api
from util.setting import *
from util.display import *
from NeoRant import NeoRant

 

if __name__ == '__main__':   
    colorama.init() 
    # Load or create settings.json
    settings_path = "ssettings.json"
    default_settings = {
        "XFOV": 97,
        "YFOV": 50,
        "SMOOTHNESS": 3,   
        "HEAD_OFFSET": 3,
        "MOVESPEED": 0.55,
        "FOV_TOGGLE": False, 
        "UI_TOGGLE": "0x75",
        "CHEAT_ONOFF": "0x74",
        "INGAME_SENSITIVITY": 3, 
        "AIM_ASSIST_KEY": "0x01", 
    }
    if os.path.exists(settings_path):
        with open(settings_path, "r") as f:
            settings = json.load(f)
        # Backfill any missing keys with defaults
        updated = False
        for k, v in default_settings.items():
            if k not in settings:
                settings[k] = v
                updated = True
        # Ensure MOVESPEED exists; default derives from INGAME_SENSITIVITY
        if "MOVESPEED" not in settings:
            try:
                ingame_sens = float(settings.get("INGAME_SENSITIVITY", 3))
            except Exception:
                ingame_sens = 3.0
            settings["MOVESPEED"] = round(0.55 * (ingame_sens / 3.0), 3)
            updated = True
        if updated:
            with open(settings_path, "w") as f:
                json.dump(settings, f, indent=4, ensure_ascii=False)
    else:
        settings = default_settings
        # Include computed MOVESPEED in first-time creation
        try:
            ingame_sens = float(settings.get("INGAME_SENSITIVITY", 3))
        except Exception:
            ingame_sens = 3.0
        settings["MOVESPEED"] = round(0.55 * (ingame_sens / 3.0), 3)
        with open(settings_path, "w") as f:
            json.dump(settings, f, indent=4, ensure_ascii=False) 
    app = NeoRant(settings) 

