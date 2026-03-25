"""
FRAGPUNK - Configuration Utilities
===================================
DISCLAIMER: This project is for EDUCATIONAL PURPOSES ONLY.
This software is NOT intended to cause any damage to games, systems, or software.
Misuse of this software may violate game Terms of Service and result in account bans.
The author assumes NO responsibility for any misuse of this code.

For support and questions, join our Discord community:
Discord: https://discord.gg/tPHXyMZmKh
"""

import ctypes
import os   
import json 
import time  

DISCORD = "https://discord.gg/tPHXyMZmKh"

def read_json_file(path):
    with open(path+"/settings.json", "r") as f:
        return json.load(f)
def update_json_config(path, config):
    with open(path+"/settings.json", "w") as f:
        json.dump(config, f, indent=4, ensure_ascii=False)