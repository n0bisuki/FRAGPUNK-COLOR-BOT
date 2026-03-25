"""
FRAGPUNK - Core Application Logic
==================================
DISCLAIMER: This project is for EDUCATIONAL PURPOSES ONLY.
This software is NOT intended to cause any damage to games, systems, or software.
Misuse of this software may violate game Terms of Service and result in account bans.
The author assumes NO responsibility for any misuse of this code.

For support and questions, join our Discord community:
Discord: https://discord.gg/tPHXyMZmKh
"""

import os
import cv2
import sys
import time
import math
import json
import psutil
import random 
import string
import win32api
import winsound
import threading
import numpy as np
from capture import Capture
from termcolor import colored
from mouse import ArduinoMouse
import serial.tools.list_ports
from ImGuI.overlay import ImGuiOverlay 
from util.display import display_serial_port_not_found
from fov_window import show_detection_window, toggle_window




class NeoRant:
    def __init__(self, settings):
        self.settings = settings
        #  finally get all settings
        self.XFOV = settings["XFOV"]
        self.YFOV = settings["YFOV"] 
        self.UI_TOGGLE = settings["UI_TOGGLE"] 
        self.SMOOTHNESS = settings["SMOOTHNESS"] 
        self.FOV_TOGGLE = settings["FOV_TOGGLE"]
        self.AIM_ASSIST_KEY = settings["AIM_ASSIST_KEY"] 
        self.CHEAT_ONOFF = settings["CHEAT_ONOFF"]
        self.INGAME_SENSITIVITY = settings["INGAME_SENSITIVITY"]  
        self.HEAD_OFFSET = settings.get("HEAD_OFFSET", 0)
        
        # Read MOVESPEED from settings; fallback to computed default
        self.MOVESPEED = float(settings.get("MOVESPEED", 0.35 * (self.INGAME_SENSITIVITY / 3.0)))
        self.FLICKSPEED = 1.07437623 * (self.INGAME_SENSITIVITY ** -0.9936827126)
         
        self.LOWER_COLOR, self.UPPER_COLOR = self.get_color_bounds("purple")

        self.monitor_width = win32api.GetSystemMetrics(0)
        self.monitor_height = win32api.GetSystemMetrics(1)
        self.CENTER_X, self.CENTER_Y = self.monitor_width // 2, self.monitor_height // 2
        self.x = self.CENTER_X - self.XFOV // 2
        self.y = self.CENTER_Y - self.YFOV // 2
        self.grabber = Capture(self.x, self.y, self.XFOV, self.YFOV)

        self.arduinomouse = ArduinoMouse(
            hk_self=self
        )
        self.launcher_pid  = 0
        self.window_toggled = False
        self.TOGGLED_CHEATE = False 
        self.WINDOW_TOGGLE = 0x71
          
        
        # Track previous key states for edge detection (press once)
        self._key_prev = {}
        self.overlay = ImGuiOverlay(hk_self=self)
        self.overlay.init_window()
        self.overlay.Hide_from_taskbar()
        threading.Thread(target=self.listener_keybind, daemon=True).start()
        threading.Thread(target=self.random_app_name, daemon=True).start() 
        threading.Thread(target=self.listener, daemon=True).start() 
        self.overlay.render_loop() 


    def random_app_name(self):
        while True:
            app_names = [
                "Discord","Visual Studio Code","Chrome","PyCharm","Firefox","Sublime Text","Notepad++","Atom",
                "Microsoft Word","Excel","PowerPoint","Photoshop","Illustrator","Premiere Pro","Audacity","Blender",
                "Unity","Maya","Eclipse","Android Studio","Spotify","Zoom","Slack","WhatsApp",
                "Telegram","Microsoft Teams","Trello","GitHub","GitLab","Jupyter Notebook","Google Docs","Google Sheets",
                "Google Slides","Adobe Acrobat","Adobe InDesign","Adobe After Effects","Adobe Lightroom","Audacity","GIMP","Krita",
                "VLC Media Player","iTunes","Microsoft Edge","Safari","Opera","Notion","Figma","Microsoft Outlook",
            ]
            random_app = random.choice(app_names)
            random_text = ''.join(random.choices(string.ascii_letters + string.digits, k=10))  # 10 random characters 
            os.system("title " + f"{random_app} {random_text}") 
            time.sleep(2)

    def play(self, s):
        winsound.Beep(1000 if s == "cheatOn" else 500, 200)
  
    def listener(self):
        while True: 
            left_down = (win32api.GetAsyncKeyState(int(self.AIM_ASSIST_KEY, 16)) & 0x8000) != 0
            if self.TOGGLED_CHEATE and left_down:
                self.process("move") 
            time.sleep(0.003)
            
    def listener_keybind(self):
        while True:
            # Prepare key bindings once
            bindings = [
                (int(self.CHEAT_ONOFF, 16),self.Cheat_Toggled),  
                # (self.WINDOW_TOGGLE, lambda: toggle_window(self)),
                # (int(self.FLICK_KEY, 16), lambda: self.process("flick") if self.TOGGLED_CHEATE else None),
            ]
            for vk, action in bindings:
                pressed = (win32api.GetAsyncKeyState(vk) & 0x8000) != 0
                prev = self._key_prev.get(vk, False)
                # Edge-trigger on key down
                if pressed and not prev and action is not None:
                    threading.Thread(target=action, daemon=True).start()
                self._key_prev[vk] = pressed
            time.sleep(0.005)
 

    def Cheat_Toggled(self):
        self.TOGGLED_CHEATE = not self.TOGGLED_CHEATE
        self.play("cheatOn" if self.TOGGLED_CHEATE else "cheatOff") 


    def get_color_bounds(self,color):
        if color == "yellow":
            return [30, 125, 150], [30, 255, 255]
        elif color == "purple":
            return [140, 110, 140], [160, 255, 255]
        elif color == "red":
            return [0, 0, 0], [4, 255, 255] 
        else:
            return [140, 110, 140], [160, 255, 255]

 
    def process(self, action):
        screen = self.grabber.get_screen()
        hsv = cv2.cvtColor(np.array(screen), cv2.COLOR_BGR2HSV)
        mask = cv2.inRange(hsv, np.array(self.LOWER_COLOR), np.array(self.UPPER_COLOR))
        # Reduced dilation iterations for faster processing
        dilated = cv2.dilate(mask, None, iterations=2)
        contours, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        if not contours:
            return
         
        screen_cx = self.grabber.xfov // 2
        screen_cy = self.grabber.yfov // 2 
        closest_part_distance = 100000  
        closest_contour = None

        for contour in contours: 
            area = cv2.contourArea(contour)
            if area < 25:
                continue
                
            x, y, w, h = cv2.boundingRect(contour) 
            if w < 8 or h < 8 or w > 250 or h > 250:
                continue
                
            cx = x + w // 2
            cy = y + int(h * 0.3) + self.HEAD_OFFSET
            x_diff = cx - screen_cx
            y_diff = cy - screen_cy 
            distance = (x_diff**2 + y_diff**2) ** 0.5

            if distance < closest_part_distance:
                closest_part_distance = distance
                closest_contour = (cx, cy, x_diff, y_diff, distance, w, h)

        if closest_contour is None:
            return

        cX, cY, x_diff, y_diff, distance, w, h = closest_contour

        if action == "move":
            flickx = x_diff * self.MOVESPEED
            flicky = y_diff * self.MOVESPEED
            # print(f"Closest target at distance: {distance:.2f}px")
            self.arduinomouse.move(flickx, flicky)

        elif action == "flick":
            pass
            # Use flick speed multiplier to cover distance quickly and ensure at least 1px step when non-zero
            # fs = float(getattr(self, "FLICKSPEED", 1.0))
            # print(fs)
            # mx = abs(x_diff) * fs
            # my = abs(y_diff) * fs
            # dx = int(math.copysign(max(1, round(mx)), x_diff)) if x_diff != 0 else 0
            # dy = int(math.copysign(max(1, round(my)), y_diff)) if y_diff != 0 else 0
            # self.arduinomouse.flick(dx, dy) 
            # self.arduinomouse.click()