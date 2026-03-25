import sys
import time
import math
import serial
import ctypes
import random
import win32api
import win32con
import pyautogui
from termcolor import colored 
import serial.tools.list_ports

class ArduinoMouse:
    def __init__(self,hk_self, filter_length=4):
        self.hk_self = hk_self
        self.filter_length = self.hk_self.SMOOTHNESS 
        
        # Initialize smoothing variables
        self.prev_time = time.time()
        self.smooth_x = 0.0
        self.smooth_y = 0.0
        self.prev_raw_x = 0.0
        self.prev_raw_y = 0.0
        self.dx_hat = 0.0
        self.dy_hat = 0.0
        s = max(1, int(self.filter_length))
        self.min_cutoff = 6.0 - (s - 1) * (3.5 / 7.0) if s <= 8 else 2.5
        self.min_cutoff = max(2.5, min(6.0, self.min_cutoff))
        self.beta = 1.0
        self.d_cutoff = 3.5
        
        # Only initialize Arduino if ISARDUINO is True 
        self.serial_port = serial.Serial()
        self.serial_port.baudrate = 115200
        self.serial_port.timeout = 1
        self.serial_port.port = self.find_serial_port()
        if self.serial_port.port:
            self.serial_port.open()
        else:
            ctypes.windll.user32.MessageBoxA(
                    0,
                    b"Unable to find serial port or the Arduino device is with different name. Please check its connection and try again.",
                    b"[Error]",
                    0
            )
            sys.exit()

            

    def find_serial_port(self):
        port = next(
            (
                port
                for port in serial.tools.list_ports.comports()
                if "USB Serial Device" in port.description or "Arduino" in port.description
            ),
            None,
        )
        if port is not None:
            return port.device
        else: 
            return None

    def move(self, x, y): 
        now = time.time()
        dt = now - self.prev_time
        if dt <= 0:
            dt = 1.0 / 240.0
        self.prev_time = now

        rx = float(x)
        ry = float(y)
 
        def alpha_from_cutoff(cutoff_hz: float, dt_sec: float) -> float:
            tau = 1.0 / (2.0 * math.pi * max(1e-4, cutoff_hz))
            a = 1.0 / (1.0 + tau / max(1e-4, dt_sec))
            return max(0.02, min(0.98, a))
 
        dx = (rx - self.prev_raw_x) / dt
        dy = (ry - self.prev_raw_y) / dt
        a_d = alpha_from_cutoff(self.d_cutoff, dt)
        self.dx_hat = (1.0 - a_d) * self.dx_hat + a_d * dx
        self.dy_hat = (1.0 - a_d) * self.dy_hat + a_d * dy
        speed = max(abs(self.dx_hat), abs(self.dy_hat))
 
        cutoff_x = self.min_cutoff + self.beta * speed
        cutoff_y = cutoff_x 
        a_x = alpha_from_cutoff(cutoff_x, dt)
        a_y = alpha_from_cutoff(cutoff_y, dt)
 
        self.smooth_x = (1.0 - a_x) * self.smooth_x + a_x * rx
        self.smooth_y = (1.0 - a_y) * self.smooth_y + a_y * ry

        self.prev_raw_x = rx
        self.prev_raw_y = ry

        sx = int(self.smooth_x)
        sy = int(self.smooth_y)

        finalx = sx + 256 if sx < 0 else sx
        finaly = sy + 256 if sy < 0 else sy   
        data = f"{int(finalx)}:{int(finaly)}"
        self.serial_port.write(data.encode()) 

    def flick(self, x, y):  
        sx = int(x)
        sy = int(y) 
        while sx != 0 or sy != 0:
            step_x = max(-127, min(127, sx))
            step_y = max(-127, min(127, sy))
            finalx = step_x + 256 if step_x < 0 else step_x
            finaly = step_y + 256 if step_y < 0 else step_y
            data = f"{int(finalx)}:{int(finaly)}"
            self.serial_port.write(data.encode())
            sx -= step_x
            sy -= step_y
            time.sleep(0.001) 
        
    def click(self): 
        self.serial_port.write("shoot".encode()) 
        
    def close(self): 
        self.serial_port.close()

    def __del__(self):
        self.close()

