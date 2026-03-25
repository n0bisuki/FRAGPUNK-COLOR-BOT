# FRAGPUNK - Project Documentation

## ⚠️ DISCLAIMER

**This project is for educational purposes only.** This code is designed to demonstrate concepts in image processing, computer vision, mouse input automation, and GUI overlay systems. **This software is NOT intended to cause any damage to games, systems, or any software/hardware.** 

Use of this software to cheat in online games or to gain unfair advantages in multiplayer environments is strictly against the terms of service of most games and can result in account bans, legal consequences, or other penalties. **The author assumes no responsibility for any misuse of this code.**

---

## 📋 Project Overview

FRAGPUNK is a Python-based application that demonstrates advanced computer vision and input automation techniques. It serves as an educational tool for understanding screen capture, color detection, and automated mouse control.

**If you need any support or have questions, please join our Discord server:**  
🔗 **Discord:** https://discord.gg/tPHXyMZmKh

---

## 📁 File Documentation

### 1. **index.py** - Entry Point
**Location:** `FRAGPUNK/index.py` (Lines 1-63)

**Purpose:**  
This is the main entry point of the application. It handles initialization and configuration management.

**Key Functions:**
- **Settings Management:** Loads or creates a `settings.json` configuration file with default values
- **Default Settings:** Initializes parameters for field of view (FOV), sensitivity, keybindings, and movement speed
- **Dynamic Configuration:** Automatically fills in missing settings with defaults and computes `MOVESPEED` based on in-game sensitivity
- **Application Initialization:** Creates and starts the `NeoRant` application instance

**Default Settings Structure:**
```python
{
    "XFOV": 97,              # Horizontal field of view in pixels
    "YFOV": 50,              # Vertical field of view in pixels
    "SMOOTHNESS": 3,         # Movement smoothing factor
    "HEAD_OFFSET": 3,        # Pixel offset for head targeting
    "MOVESPEED": 0.55,       # Base movement speed multiplier
    "FOV_TOGGLE": False,     # Enable/disable FOV window visualization
    "UI_TOGGLE": "0x75",     # Hex keycode for toggling UI
    "CHEAT_ONOFF": "0x74",   # Hex keycode for enabling/disabling cheat
    "INGAME_SENSITIVITY": 3, # In-game mouse sensitivity setting
    "AIM_ASSIST_KEY": "0x01" # Hex keycode for aim assist activation
}
```

---

### 2. **NeoRant.py** - Core Application Logic
**Location:** `FRAGPUNK/NeoRant.py` (Lines 1-187)

**Purpose:**  
This is the main application class that implements the core functionality of screen monitoring, target detection, and mouse automation.

**Key Components:**

#### **Initialization (`__init__`)**
- Loads all configuration settings from `index.py`
- Sets up screen capture region based on monitor dimensions and FOV settings
- Initializes hardware components (Arduino mouse interface)
- Creates and configures the ImGui overlay for visualization
- Starts three background threads for continuous operation

#### **Threading System**
Three daemon threads run concurrently:
1. **`listener_keybind()`** - Monitors keyboard input for cheat toggle
2. **`listener()`** - Monitors the aim assist key and triggers target tracking
3. **ImGui Render Loop** - Handles the overlay UI rendering

#### **Color Detection**
- **`get_color_bounds(color)`** - Returns HSV color range bounds for different target colors
  - **Purple:** [140, 110, 140] to [160, 255, 255] (default for FRAGPUNK enemies)
  - **Yellow:** [30, 125, 150] to [30, 255, 255]
  - **Red:** [0, 0, 0] to [4, 255, 255]

#### **Screen Capture & Processing**
- **`process(action)`** - Main computer vision pipeline:
  1. Captures a rectangular region of the screen (FOV-based)
  2. Converts captured image from BGR to HSV color space
  3. Creates a binary mask for target colors using `cv2.inRange()`
  4. Applies morphological dilation to connect nearby pixels
  5. Finds contours (connected components) in the mask
  6. Filters contours by area and bounding box dimensions
  7. Calculates center points for valid contours
  8. Identifies the closest target to screen center
  9. Moves mouse towards the target using calculated offsets

#### **Key Methods**
- **`Cheat_Toggled()`** - Toggles the cheat on/off and plays audio feedback
- **`play(s)`** - Produces beep sounds (1000Hz for enable, 500Hz for disable)
- **`random_app_name()`** - Periodically changes the window title to random application names (for obfuscation)
- **`listener()`** - Continuous monitoring of aim assist key press
- **`listener_keybind()`** - Keyboard input handler with edge-detection (press-once triggering)

#### **Hardware Integration**
- Uses `ArduinoMouse` class for mouse movement control
- Integrates with Arduino-based mouse input device for precise movement

#### **GUI Overlay**
- Creates an invisible ImGui window overlay
- Hides from taskbar to minimize visibility
- Renders real-time information and controls

---

### 3. **util/setting.py** - Configuration Utilities
**Location:** `FRAGPUNK/util/setting.py` (Line 6)

**Purpose:**  
Provides utility functions for configuration management and contact information.

**Contents:**
```python
DISCORD = "https://discord.gg/tPHXyMZmKh"

def read_json_file(path):
    # Reads settings.json from specified directory

def update_json_config(path, config):
    # Writes updated configuration back to settings.json
```

**Key Features:**
- Centralized Discord server link for community support
- JSON file I/O functions for persisting configuration
- Ensures configuration consistency across sessions

---

## 🔧 Technology Stack

**Core Libraries:**
- **OpenCV** (`cv2`) - Computer vision and image processing
- **NumPy** (`np`) - Numerical computing and array operations
- **PySerial** - Serial communication with Arduino devices
- **PyWin32** (`win32api`) - Windows API integration
- **ImGui** - Overlay GUI rendering
- **Colorama** - Terminal color output
- **TermColor** - Colored terminal text
- **PSUtil** - Process and system utilities

**Key Features:**
- Multi-threaded architecture for concurrent operations
- Real-time screen capture and processing
- HSV color space analysis for robust target detection
- Windows-specific system integration
- Arduino hardware communication

---

## 🎮 How It Works (Technical Flow)

1. **Startup** → `index.py` loads/creates `settings.json`
2. **Initialization** → `NeoRant` class initializes with settings
3. **Threading** → Three daemon threads start monitoring
4. **Main Loop** → ImGui renders overlay while threads execute
5. **Key Detection** → When cheat key is pressed, `Cheat_Toggled()` is called
6. **Aim Detection** → When aim assist key is held:
   - Screen region is captured
   - Color detection finds purple targets
   - Closest target is identified
   - Mouse is moved toward target using `MOVESPEED` calculations
7. **Obfuscation** → Window title changes randomly every 2 seconds

---

## 📝 Configuration

All settings are stored in `settings.json` and can be modified:
- **FOV Settings:** Adjust `XFOV` and `YFOV` to change capture region size
- **Movement:** Modify `MOVESPEED` and `SMOOTHNESS` for different tracking speeds
- **Sensitivity:** Adjust `INGAME_SENSITIVITY` and `HEAD_OFFSET` for game compatibility
- **Keybindings:** Change hex keycodes in `CHEAT_ONOFF` and `AIM_ASSIST_KEY`

---

## 🚀 Requirements

See `requirements.txt` for all Python dependencies. Key requirements:
- Python 3.7+
- Windows OS (uses Win32 API)
- Arduino device (for mouse control)
- OpenCV
- NumPy

---

## ⚖️ Legal & Ethical Considerations

**This code is provided for educational and research purposes only.**

- ❌ **Do NOT use** this code to cheat in online multiplayer games
- ❌ **Do NOT use** this code to gain unfair advantages in competitive environments
- ❌ **Do NOT use** this code to violate any game's Terms of Service
- ✅ **DO use** this code to learn about computer vision concepts
- ✅ **DO use** this code to understand input automation and threading
- ✅ **DO study** this code to improve your programming skills

**Potential consequences of misuse:**
- Game account permanent bans
- Legal action from game developers
- Hardware damage (if improperly interfacing with Arduino)
- System instability

---

## 💬 Support & Community

Need help? Have questions? Join our community Discord server:

🔗 **Discord Server:** https://discord.gg/tPHXyMZmKh

Feel free to ask questions about:
- Computer vision techniques
- Python programming
- Threading and concurrency
- Windows API integration
- Image processing algorithms

---

## 📜 License & Attribution

This project is provided as-is for educational purposes. Users are responsible for ensuring they comply with all applicable laws and terms of service agreements.

---

## 🔬 Learning Resources

This project demonstrates several advanced concepts:

1. **Computer Vision:** HSV color space, contour detection, morphological operations
2. **Multithreading:** Daemon threads, edge-triggered input detection
3. **System Integration:** Windows API, serial communication, hardware control
4. **GUI Frameworks:** ImGui overlay rendering
5. **Configuration Management:** JSON-based dynamic settings

Study this code to deepen your understanding of these topics!

---

**Last Updated:** 2026-03-25  
**Version:** Educational Release
