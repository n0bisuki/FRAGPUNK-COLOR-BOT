# imgui/overlay.py
import os
import time
import glfw
import imgui
import ctypes
import win32gui
import win32con
import win32api
import webbrowser
import numpy as np
from PIL import Image
from OpenGL.GL import *
from ctypes import wintypes
from util.setting import DISCORD 
from util.setting import FRAGPUNK 
from util.virtual_key_codes import virtual_keys
from imgui.integrations.glfw import GlfwRenderer
from util.setting import read_json_file, update_json_config

user32 = ctypes.windll.user32
GetAsyncKeyState = user32.GetAsyncKeyState

class ImGuiOverlay:
    def __init__(self, hk_self, title="Overlay"):
        ctypes.windll.user32.SetProcessDPIAware()
        self.screen_width = hk_self.monitor_width - 1
        self.screen_height = hk_self.monitor_height - 1
        self.title = title
        self.window = None
        self.hwnd = None
        self.impl = None
        self.loop = True
        self.show_window = False
        self.show_fov_window = hk_self.settings.get("FOV_TOGGLE",False) 
        self.last_toggle_time = 0
        self._last_style_check = 0.0  # throttle expensive Win32 style checks

        self.streamDllLoaded=False
        self.waiting_for_key = None  # Which keybind we're assigning (e.g. "LEFT_MB")
        self.key_input_ready = False  # Set to True externally when a key is captured
        self.last_pressed_key = None  # Captured key value
        self.hk_self = hk_self
        
        try:
            self._ui_toggle_vk = int(self.hk_self.UI_TOGGLE, 16)
        except Exception:
            self._ui_toggle_vk = win32con.VK_INSERT  # sensible default

    def init_window(self):
        if not glfw.init():
            raise Exception("Could not initialize GLFW")

        glfw.window_hint(glfw.FLOATING, glfw.TRUE)
        glfw.window_hint(glfw.DECORATED, glfw.FALSE)
        glfw.window_hint(glfw.TRANSPARENT_FRAMEBUFFER, glfw.TRUE)
        # Create hidden first to avoid taskbar entry creation; we'll show after styles are applied
        glfw.window_hint(glfw.VISIBLE, glfw.FALSE)
        # Do not focus when shown
        try:
            glfw.window_hint(glfw.FOCUS_ON_SHOW, glfw.FALSE)
        except Exception:
            pass

        # Create with empty title so nothing leaks into taskbar/alt-tab labels
        self.window = glfw.create_window(
            self.screen_width, self.screen_height, "", None, None
        )
        if not self.window:
            glfw.terminate()
            raise Exception("Failed to create GLFW window")

        glfw.make_context_current(self.window)
        self.hwnd = self.get_hwnd_from_glfw(self.window)
        # Cap to monitor refresh to reduce CPU usage (vsync)
        try:
            glfw.swap_interval(1)
        except Exception:
            pass
        self.make_window_clickthrough(self.hwnd)  
        # Ensure the window doesn't appear on the taskbar right away
        self.Hide_from_taskbar()
        # Make a hidden owner window to ensure this window never shows in taskbar
        try:
            self._owner_hwnd = self._create_hidden_owner_window()
            # Set as owner; owned windows are excluded from the taskbar
            win32gui.SetWindowLong(self.hwnd, win32con.GWL_HWNDPARENT, self._owner_hwnd) 
            win32gui.SetWindowText(self.hwnd, "") 
            win32gui.ShowWindow(self.hwnd, win32con.SW_SHOWNOACTIVATE)
        except Exception:
            self._owner_hwnd = None
            pass

        # Re-apply taskbar hiding when window focus changes (Windows sometimes resets styles)
        def _on_focus(window, focused):
            try:
                self.Hide_from_taskbar()
            except Exception:
                pass
        glfw.set_window_focus_callback(self.window, _on_focus)


        imgui.create_context()

        io = imgui.get_io()
        io.config_flags |= imgui.CONFIG_NAV_ENABLE_KEYBOARD
        imgui.style_colors_dark()
        self.impl = GlfwRenderer(self.window) 
 

        style = imgui.get_style()
        colors = style.colors
        self.purple = (132/255.0, 58/255.0, 255/255.0, 1.0)      # RGBA (0-1)
        self.purple_hovered = (160/255.0, 80/255.0, 255/255.0, 1.0)
        self.purple_active = (100/255.0, 40/255.0, 200/255.0, 1.0)
        # Slightly darkened purple for backgrounds
        self.window_bg = (self.purple[0] * 0.15, self.purple[1] * 0.15, self.purple[2] * 0.15, 0.95)

        # Apply to buttons
        colors[imgui.COLOR_BUTTON] = self.purple
        colors[imgui.COLOR_BUTTON_HOVERED] = self.purple_hovered
        colors[imgui.COLOR_BUTTON_ACTIVE] = self.purple_active

        
        # Slider
        colors[imgui.COLOR_SLIDER_GRAB] = self.purple
        colors[imgui.COLOR_SLIDER_GRAB_ACTIVE] = self.purple_active

        # Tab (left tab selection)
        colors[imgui.COLOR_TAB] = self.purple_hovered
        colors[imgui.COLOR_TAB_ACTIVE] = self.purple
        colors[imgui.COLOR_TAB_HOVERED] = self.purple_hovered
        colors[imgui.COLOR_TAB_UNFOCUSED] = (0.2, 0.2, 0.2, 1.0)   # optional background
        colors[imgui.COLOR_TAB_UNFOCUSED_ACTIVE] = self.purple_active

        # Headers and check marks
        colors[imgui.COLOR_HEADER] = self.purple
        colors[imgui.COLOR_HEADER_HOVERED] = self.purple_hovered
        colors[imgui.COLOR_HEADER_ACTIVE] = self.purple_active
        colors[imgui.COLOR_CHECK_MARK] = self.purple

        # Frame backgrounds (affects slider background)
        colors[imgui.COLOR_FRAME_BACKGROUND] = (self.purple[0], self.purple[1], self.purple[2], 0.25)
        colors[imgui.COLOR_FRAME_BACKGROUND_HOVERED] = (self.purple_hovered[0], self.purple_hovered[1], self.purple_hovered[2], 0.35)
        colors[imgui.COLOR_FRAME_BACKGROUND_ACTIVE] = (self.purple_active[0], self.purple_active[1], self.purple_active[2], 0.50)

        # Window background globally
        colors[imgui.COLOR_WINDOW_BACKGROUND] = self.window_bg

        # Title bar background to match theme
        colors[imgui.COLOR_TITLE_BACKGROUND] = (self.purple[0] * 0.25, self.purple[1] * 0.25, self.purple[2] * 0.25, 1.0)
        colors[imgui.COLOR_TITLE_BACKGROUND_ACTIVE] = (self.purple[0] * 0.35, self.purple[1] * 0.35, self.purple[2] * 0.35, 1.0)
        colors[imgui.COLOR_TITLE_BACKGROUND_COLLAPSED] = (self.purple[0] * 0.18, self.purple[1] * 0.18, self.purple[2] * 0.18, 0.80)

    def make_window_clickthrough(self, hwnd):
        styles = win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)
        styles |= win32con.WS_EX_LAYERED
        win32gui.SetWindowLong(hwnd, win32con.GWL_EXSTYLE, styles)
        win32gui.SetLayeredWindowAttributes(hwnd, 0, 255, win32con.LWA_ALPHA)

    def set_click_through(self, enable=True):
        styles = win32gui.GetWindowLong(self.hwnd, win32con.GWL_EXSTYLE)
        if enable:
            styles |= win32con.WS_EX_TRANSPARENT
        else:
            styles &= ~win32con.WS_EX_TRANSPARENT
        win32gui.SetWindowLong(self.hwnd, win32con.GWL_EXSTYLE, styles)

    def get_hwnd_from_glfw(self, window):
        glfw._glfw.glfwGetWin32Window.restype = ctypes.c_void_p
        glfw._glfw.glfwGetWin32Window.argtypes = [ctypes.c_void_p]
        return glfw._glfw.glfwGetWin32Window(window)
 
    def Hide_from_taskbar(self):   
        ex_style = win32gui.GetWindowLong(self.hwnd, win32con.GWL_EXSTYLE)
        ex_style &= ~win32con.WS_EX_APPWINDOW  # Remove app window style
        ex_style |= win32con.WS_EX_TOOLWINDOW  # Add tool window style
        ex_style |= win32con.WS_EX_NOACTIVATE  # Do not activate -> avoid taskbar/alt-tab
        win32gui.SetWindowLong(self.hwnd, win32con.GWL_EXSTYLE, ex_style)

        # Force Windows to refresh the non-client area to update styles
        win32gui.SetWindowPos(
            self.hwnd, 0, 0, 0, 0, 0,
            win32con.SWP_NOACTIVATE |
            win32con.SWP_NOMOVE |
            win32con.SWP_NOSIZE |
            win32con.SWP_NOZORDER |
            win32con.SWP_FRAMECHANGED
        )

    def enforce_taskbar_hidden(self):
        """Continuously ensure the overlay stays hidden from the taskbar.
        Some window events can flip WS_EX_APPWINDOW back on; if that happens,
        remove it again and force a non-client refresh.
        """
        try:
            now = time.time()
            # Only check a couple times per second
            if now - self._last_style_check < 0.5:
                return
            self._last_style_check = now
            ex_style = win32gui.GetWindowLong(self.hwnd, win32con.GWL_EXSTYLE)
            needs_fix = (ex_style & win32con.WS_EX_APPWINDOW) or not (ex_style & win32con.WS_EX_TOOLWINDOW) or not (ex_style & win32con.WS_EX_NOACTIVATE)
            if needs_fix:
                self.Hide_from_taskbar()
            # Re-assert owner and empty title (infrequently)
            if getattr(self, "_owner_hwnd", None):
                try:
                    win32gui.SetWindowLong(self.hwnd, win32con.GWL_HWNDPARENT, self._owner_hwnd)
                except Exception:
                    pass
            try:
                if win32gui.GetWindowText(self.hwnd):
                    win32gui.SetWindowText(self.hwnd, "")
            except Exception:
                pass
        except Exception:
            pass

    def _create_hidden_owner_window(self):
        """Create an invisible owner window to prevent taskbar button for the overlay.
        Uses the built-in STATIC window class to avoid custom registration.
        """
        hInstance = win32api.GetModuleHandle(None)
        hwnd_owner = win32gui.CreateWindowEx(
            win32con.WS_EX_TOOLWINDOW,  # tool window, no taskbar
            "Static",                   # built-in class
            None,                        # no title
            win32con.WS_POPUP,           # popup style, no border
            0, 0, 0, 0,                  # zero-size and off-screen
            0,                           # no parent
            0,                           # no menu
            hInstance,
            None
        )
        # Keep it hidden just in case
        win32gui.ShowWindow(hwnd_owner, win32con.SW_HIDE)
        return hwnd_owner

    def color_from_name(self, name):
        mapping = {
            "red": (1.0, 0.0, 0.0, 1.0),
            "green": (0.0, 1.0, 0.0, 1.0),
            "white": (1.0, 1.0, 1.0, 1.0),
            "purple":(132/255.0, 58/255.0, 255/255.0, 1.0)  
        }
        return mapping.get(name.lower(), (1.0, 1.0, 1.0, 1.0))  # default white

    def render_loop(self):
        self.set_click_through(not self.show_window)
        self._ui_toggle_vk = int(self.hk_self.UI_TOGGLE, 16)
        while not glfw.window_should_close(self.window) and self.loop:
            glfw.poll_events()
            self.impl.process_inputs()
            # Re-enforce hidden state in case Windows toggled styles
            self.enforce_taskbar_hidden()

            # Use cached virtual key to avoid per-frame parsing cost
            if win32api.GetAsyncKeyState(self._ui_toggle_vk) & 0x8000:
                current_time = time.time()
                if current_time - self.last_toggle_time > 0.3:
                    self.show_window = not self.show_window
                    self.set_click_through(not self.show_window)
                    self.last_toggle_time = current_time

            imgui.new_frame()

            # Draw FOV box in background every frame
            if self.show_fov_window:  
                self.draw_valorant_side_brackets_alt(thickness=0.5)

            self.render_watermarks()
            if self.show_window:
                self.render_window()

            imgui.render()
            glClearColor(0, 0, 0, 0)
            glClear(GL_COLOR_BUFFER_BIT)
            self.impl.render(imgui.get_draw_data())
            glfw.swap_buffers(self.window) 

            if win32api.GetAsyncKeyState(win32con.VK_END) & 0x8000:
                break

        self.impl.shutdown()
        glfw.terminate()

    def render_watermarks(self):  
        # // bottom right
        imgui.set_next_window_position(
            self.screen_width - 150, self.screen_height - 150
        )
        imgui.push_style_color(imgui.COLOR_WINDOW_BACKGROUND, *[0.1, 0.1, 0.1, 0.1])
        imgui.begin(
            "Watermark Layout",
            True,
            imgui.WINDOW_NO_TITLE_BAR
            | imgui.WINDOW_NO_RESIZE
            | imgui.WINDOW_NO_MOVE
            | imgui.WINDOW_NO_SAVED_SETTINGS
            | imgui.WINDOW_NO_SCROLL_WITH_MOUSE
            | imgui.WINDOW_NO_INPUTS,
        )
        # FPS badge (label left, value right)
        fps = getattr(self.hk_self.grabber, "fps", None)
        if fps is not None:
            color = (
                "green" if fps >= 100 else ("yellow" if fps >= 60 else "red")
            )
            # 2-column layout
            imgui.columns(2, "wm_fps_cols", border=False)
            # Left: label
            imgui.text("FPS:")
            imgui.next_column()
            # Right: value right-aligned within the column
            value = f"{fps:.0f}"
            val_w = imgui.calc_text_size(value).x
            col_w = imgui.get_column_width()
            # Move cursor so that text ends at the right edge (with small padding)
            right_pad = 8
            imgui.set_cursor_pos_x(imgui.get_cursor_pos_x() + max(0, col_w - val_w - right_pad))
            imgui.text_colored(value, *self.color_from_name(color))
            imgui.columns(1)

        text = "Singularity"
        text_width = imgui.calc_text_size(text).x
        window_width = imgui.get_window_width()
        center_x = (window_width - text_width) / 2

        imgui.set_cursor_pos_x(center_x)
        if self.hk_self.TOGGLED_CHEATE:
            imgui.text_colored(text, *self.color_from_name("purple"))
        else:
            imgui.text_colored(text, *self.color_from_name("red"))

        imgui.text("Assist: ")
        imgui.same_line()
        if self.hk_self.TOGGLED_CHEATE:
            imgui.text_colored("Active", *self.color_from_name("green"))
        else:
            imgui.text_colored("Inactive", *self.color_from_name("red")) 

        # imgui.text("Flick: ")
        # imgui.same_line()
        # if self.hk_self.TOGGLED_CHEATE:
        #     imgui.text_colored("Active", *self.color_from_name("green"))
        # else:
        #     imgui.text_colored("Inactive", *self.color_from_name("red"))

        imgui.text("")
        imgui.same_line()
        imgui.text_colored(f"XFOV: {self.hk_self.XFOV}", *self.color_from_name("white"))
        imgui.same_line()
        imgui.text_colored(f"YFOV: {self.hk_self.YFOV}", *self.color_from_name("white"))
        imgui.end()
        imgui.pop_style_color() 
    def draw_valorant_side_brackets_alt(self, thickness=1.0):
        """Alternate function that draws the same side brackets as the primary one.
        Kept identical geometry and palette so it renders the same when called ("same to same").
        """
        try:
            xfov = int(getattr(self.hk_self, "XFOV", 0) or 0)
            yfov = int(getattr(self.hk_self, "YFOV", 0) or 0)
            if xfov <= 0 or yfov <= 0:
                return

            cx = int(self.screen_width // 2)
            cy = int(self.screen_height // 2)
            x1 = int(cx - xfov // 2)
            y1 = int(cy - yfov // 2)
            x2 = int(cx + xfov // 2)
            y2 = int(cy + yfov // 2)

            # Choose a draw list
            draw_list = None
            for getter in (getattr(imgui, "get_foreground_draw_list", None),
                           getattr(imgui, "get_background_draw_list", None),
                           getattr(imgui, "get_window_draw_list", None)):
                if getter:
                    try:
                        draw_list = getter()
                    except Exception:
                        draw_list = None
                if draw_list is not None:
                    break
            if draw_list is None:
                return

            def rgba(r, g, b, a):
                return imgui.get_color_u32_rgba(r, g, b, a)

            # Same color palette as primary
            base = rgba(1.0, 1.0, 1.0, 1.0)
            base_soft = rgba(1.0, 1.0, 1.0, 0.35)
            glow_soft = rgba(1.0, 1.0, 1.0, 0.08)
            glow_soft2 = rgba(1.0, 1.0, 1.0, 0.04)

            # Same geometry as primary
            inset = max(10, int(xfov * 0.12))
            bevel = max(12, int(yfov * 0.15))

            L = [
                (x1 + inset, y1),
                (x1,         y1 + bevel),
                (x1,         y2 - bevel),
                (x1 + inset, y2),
            ]
            R = [
                (x2 - inset, y1),
                (x2,         y1 + bevel),
                (x2,         y2 - bevel),
                (x2 - inset, y2),
            ]

            # Keep joins clean: draw as polylines with unified thickness
            inner_gap = max(2, int(min(xfov, yfov) * 0.025))

            # Base layer
            draw_list.add_polyline(L, base, False, thickness)
            draw_list.add_polyline(R, base, False, thickness)
            # Soft overlays, same thickness
            draw_list.add_polyline(L, base_soft, False, thickness)
            draw_list.add_polyline(R, base_soft, False, thickness)
            draw_list.add_polyline(L, glow_soft, False, thickness)
            draw_list.add_polyline(R, glow_soft, False, thickness)
            draw_list.add_polyline(L, glow_soft2, False, thickness)
            draw_list.add_polyline(R, glow_soft2, False, thickness)

            # Inner inset polylines for the fill-toward-center vibe
            L_in = [(x + inner_gap, y) for (x, y) in L]
            R_in = [(x - inner_gap, y) for (x, y) in R]
            draw_list.add_polyline(L_in, base_soft, False, thickness)
            draw_list.add_polyline(R_in, base_soft, False, thickness)
            draw_list.add_polyline(L_in, glow_soft, False, thickness)
            draw_list.add_polyline(R_in, glow_soft, False, thickness) 
        except Exception:
            pass

    def render_window(self):
        w, h = 700, 420
        imgui.set_next_window_size(w, h, condition=imgui.ONCE)

        # Window style
        imgui.push_style_var(imgui.STYLE_WINDOW_ROUNDING, 10.0)
        imgui.push_style_var(imgui.STYLE_WINDOW_BORDERSIZE, 1.0)
        imgui.push_style_var(imgui.STYLE_FRAME_PADDING, (14, 12))
        # imgui.push_style_color(imgui.COLOR_WINDOW_BACKGROUND, *self.window_bg)
        imgui.push_style_color(imgui.COLOR_WINDOW_BACKGROUND, 0.12, 0.12, 0.15, 0.95)

        imgui.begin(
            "Singularity",
            False,
            # imgui.WINDOW_NO_TITLE_BAR
            # | imgui.WINDOW_NO_RESIZE
            # | imgui.WINDOW_NO_MOVE
            # | imgui.WINDOW_NO_COLLAPSE,
        )

        # --- Sidebar Tabs ---
        imgui.columns(2, "main", border=False)
        imgui.set_column_width(0, 160)

        if not hasattr(self, "active_tab"):
            self.active_tab = "KeyBinds"

        imgui.push_style_color(imgui.COLOR_BUTTON, *self.purple)
        imgui.push_style_color(imgui.COLOR_BUTTON_HOVERED, *self.purple_hovered)
        imgui.push_style_color(imgui.COLOR_BUTTON_ACTIVE, *self.purple_active)

        for tab in ["KeyBinds", "About"]:
            clicked, _ = imgui.selectable(tab, self.active_tab == tab)
            if clicked:
                self.active_tab = tab

        imgui.pop_style_color(3)
        imgui.next_column()

        # --- Right-side content ---
        imgui.push_style_color(imgui.COLOR_TEXT, 1, 1, 1, 0.9)

        if self.active_tab == "KeyBinds":
            imgui.text("KeyBinds Settings")

            # --- Keybind buttons (2 per row) ---
            vk_desc_map = {item["Value"].upper(): (item["Constant"].replace("VK_", "") if item["Constant"] else item["Description"]) for item in virtual_keys}

            def desc(v):
                return vk_desc_map.get(str(v).upper(), "None")  

            key_rows = [
                ("Aim Assist", "AIM_ASSIST_KEY"), 
                ("Cheat ON/OFF", "CHEAT_ONOFF"),
                ("IMGUI TOGGLE", "UI_TOGGLE"),
                # ("Flick", "FLICK_KEY"),
            ] 
  
            btn_width = (w - 160 - 10) / 2  # 10 = spacing between buttons
            btn_height = 35

            for i in range(0, len(key_rows), 2):
                label1, attr1 = key_rows[i]
                current1 = getattr(self.hk_self, attr1)
                # If we're waiting on this attr, show capture hint in label
                cap_hint1 = "  [press any key]" if self.waiting_for_key == attr1 else ""
                if imgui.button(f"{label1}: {desc(current1)}{cap_hint1}", btn_width, btn_height):
                    self.waiting_for_key = attr1

                if i + 1 < len(key_rows):
                    imgui.same_line(spacing=10)
                    label2, attr2 = key_rows[i + 1]
                    current2 = getattr(self.hk_self, attr2)
                    cap_hint2 = "  [press any key]" if self.waiting_for_key == attr2 else ""
                    if imgui.button(f"{label2}: {desc(current2)}{cap_hint2}", btn_width, btn_height):
                        self.waiting_for_key = attr2 

            # If capturing a key, detect the next pressed key and save
            if self.waiting_for_key:
                vk_code = self.detect_winapi_key()
                if vk_code is not None:
                    try:
                        hex_code = f"0x{vk_code:02X}"
                        # Update runtime
                        setattr(self.hk_self, self.waiting_for_key, hex_code)
                        # Persist to settings.json
                        config = read_json_file(os.getcwd())
                        config[self.waiting_for_key] = hex_code
                        update_json_config(os.getcwd(), config)
                    except Exception:
                        pass
                    finally:
                        self.waiting_for_key = None

            # Visual hint when capturing any keybind
            if self.waiting_for_key:
                imgui.spacing()
                imgui.text_colored("Listening... press any key to bind", 1.0, 1.0, 0.4, 1.0)
            # --- Sliders (2 per row, top-aligned) ---
            slider_width = (w - 160 - 10) / 2

            # Corrected draw_slider_row function
            def draw_slider_row(left_label, left_attr, left_min, left_max, is_float_left=False,
                                right_label=None, right_attr=None, right_min=None, right_max=None, is_float_right=False):
                imgui.begin_group()  # row group

                # Left slider
                imgui.begin_group()
                # imgui.align_text_to_frame_padding()
                imgui.dummy(0, 7)
                imgui.text(left_label)
                imgui.push_item_width(slider_width)
                if is_float_left:
                    changed, value = imgui.slider_float(f"##{left_attr}", getattr(self.hk_self, left_attr), left_min, left_max, "%.2f")
                else:
                    changed, value = imgui.slider_int(f"##{left_attr}", getattr(self.hk_self, left_attr), left_min, left_max)
                if changed:
                    if is_float_left:
                        value = round(float(value), 2)
                    setattr(self.hk_self, left_attr, value)
                    config = read_json_file(os.getcwd())
                    config[left_attr] = value
                    update_json_config(os.getcwd(), config)
                imgui.pop_item_width()
                imgui.end_group()

                # Right slider
                if right_label and right_attr:
                    imgui.same_line(spacing=10)
                    imgui.begin_group()
                    imgui.text(right_label)
                    imgui.push_item_width(slider_width)
                    if is_float_right:
                        changed, value = imgui.slider_float(f"##{right_attr}", getattr(self.hk_self, right_attr), right_min, right_max, "%.2f")
                    else:
                        changed, value = imgui.slider_int(f"##{right_attr}", getattr(self.hk_self, right_attr), right_min, right_max)
                    if changed:
                        if is_float_right:
                            value = round(float(value), 2)
                        setattr(self.hk_self, right_attr, value)
                        config = read_json_file(os.getcwd())
                        config[right_attr] = value
                        update_json_config(os.getcwd(), config)
                    imgui.pop_item_width()
                    imgui.end_group()

                imgui.end_group()  # end row


            # Row 1: SMOOTHNESS (int) & Ingame Sensitivity (float)
            draw_slider_row("SMOOTHNESS (Restart Req)", 
                            "SMOOTHNESS", 1, 20, 
                            is_float_left=False,
                            right_label="Ingame Sensitivity", 
                            right_attr="INGAME_SENSITIVITY", 
                            right_min=0.0, 
                            right_max=5.0, 
                            is_float_right=True
                        )

            # Row 2: XFOV & YFOV (both int)
            draw_slider_row("XFOV", "XFOV", 30, 200, 
                            is_float_left=False,
                            right_label="YFOV", 
                            right_attr="YFOV", 
                            right_min=30, 
                            right_max=200, 
                            is_float_right=False
                            )

            # Row 3: MOVESPEED (float) & HEAD_OFFSET (int) side-by-side
            draw_slider_row("Move Speed", "MOVESPEED", 0.10, 1, 
                            is_float_left=True,
                            right_label="Head Offset",
                            right_attr="HEAD_OFFSET",
                            right_min=0,
                            right_max=30,
                            is_float_right=False)


           # --- Left side ---
            if imgui.button("Fov Toggle", 120.0, 35.0):
                self.show_fov_window = not self.show_fov_window
                
                config = read_json_file(os.getcwd())
                config["FOV_TOGGLE"] = self.show_fov_window
                update_json_config(os.getcwd(), config)
                time.sleep(1)



        elif self.active_tab == "About":
            imgui.text("About Section") 
            imgui.text(f"Version: {FRAGPUNK}")
            imgui.text("Developer: Nobita") 
            imgui.text("Discord: ")
            imgui.same_line()
            if imgui.small_button(DISCORD):
                webbrowser.open(DISCORD)

        imgui.pop_style_color()  # pop COLOR_TEXT
        imgui.columns(1)
        imgui.end()
        imgui.pop_style_color()  # pop COLOR_WINDOW_BACKGROUND
        imgui.pop_style_var(3)

    def detect_winapi_key(self):
        for vk_code in range(0x01, 0xFE):  # Valid virtual key codes
            # If high-order bit is set, key was pressed
            if GetAsyncKeyState(vk_code) & 0x8000:
                return vk_code
        return None

    def get_virtual_key_info_by_code(self, key_code: int):
        hex_code = f"0x{key_code:02X}"  # Convert int to hex string like '0xFB'
        for item in virtual_keys:
            if item["Value"].upper() == hex_code.upper():
                return item  # or return (item["Constant"], item["Description"])
        return None


# Example usage (in your project):
# from ImGuI.overlay import ImGuiOverlay
# overlay = ImGuiOverlay()
# overlay.init_window()
# overlay.Hide_from_taskbar()
# overlay.render_loop()
