import cv2
import numpy as np
import time
import threading
import dxcam


class Capture:
    def __init__(self, x, y, xfov, yfov):
        self.x, self.y, self.xfov, self.yfov = x, y, xfov, yfov
        # Camera and control flags
        self.camera = None
        self._running = True
        self._reconnect_backoff = 0.1  # seconds, grows up to 1.0
        # Define capture region
        self.region = (self.x, self.y, self.x + self.xfov, self.y + self.yfov)
        # Buffers
        self.screen = np.zeros((self.yfov, self.xfov, 3), np.uint8)
        self.image = None
        # Thread + Lock
        self.lock = threading.Lock()
        self.capture_thread = threading.Thread(target=self.capture_loop, daemon=True)
        # Initialize camera before starting thread (safe even if it fails; loop will retry)
        self._init_camera()
        self.capture_thread.start()
        # FPS counter
        self.start_time = time.time()
        self.frame_count = 0
        self.fps = 0

    def _init_camera(self):
        try:
            self.camera = dxcam.create(output_idx=0)
        except Exception:
            self.camera = None

    def capture_loop(self):
        while self._running:
            try:
                with self.lock:
                    self.capture_screen()
            except Exception:
                # Swallow unexpected exceptions to avoid console spam; attempt to recover next loop
                pass
            self.update_fps()
            # Yield to scheduler without adding artificial delay (no FPS cap)
            time.sleep(0)

    def capture_screen(self):
        # Capture frame from dxcam
        if self.camera is None:
            # Try to (re)initialize camera with backoff
            self._init_camera()
            time.sleep(self._reconnect_backoff)
            self._reconnect_backoff = min(1.0, self._reconnect_backoff * 2)
            return
        try:
            frame = self.camera.grab(region=self.region)
        except Exception:
            frame = None
            # Drop camera to force re-init next loop
            try:
                self.camera = None
            except Exception:
                pass
        if frame is not None:
            # dxcam returns numpy BGR image (same as cv2)
            self.image = frame
            self.screen = frame
            # Reset reconnect backoff on success
            self._reconnect_backoff = 0.1

    def update_fps(self):
        self.frame_count += 1
        elapsed_time = time.time() - self.start_time
        if elapsed_time >= 1:
            self.fps = self.frame_count / elapsed_time
            # print(f" - FPS: {self.fps:.0f}", end="\r")
            self.frame_count = 0
            self.start_time = time.time()

    def get_screen(self):
        with self.lock:
            # Return a valid buffer even if no frame yet
            if self.screen is None:
                return np.zeros((self.yfov, self.xfov, 3), np.uint8)
            return self.screen

    def stop(self, join_timeout: float = 1.0):
        """Signal the capture loop to stop and optionally join the thread."""
        self._running = False
        try:
            if self.capture_thread.is_alive():
                self.capture_thread.join(timeout=join_timeout)
        except Exception:
            pass