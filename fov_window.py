import cv2
import numpy as np
import threading

def show_detection_window(colorant, grabber, window_toggled):
    while window_toggled():
        screen = grabber.get_screen()
        hsv = cv2.cvtColor(screen, cv2.COLOR_BGR2HSV)

        LOWER_COLOR, UPPER_COLOR = colorant.get_color_bounds("purple")
 
        mask = cv2.inRange(hsv, np.array(LOWER_COLOR), np.array(UPPER_COLOR))
        highlighted = cv2.bitwise_and(screen, screen, mask=mask)

        # --- Find contours of detected areas ---
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        for cnt in contours:
            area = cv2.contourArea(cnt)
            if area > 200:  # filter out small noise areas
                x, y, w, h = cv2.boundingRect(cnt)
                # Draw a rectangle with color (BGR: green here)
                cv2.rectangle(screen, (x, y), (x + w, y + h), (0, 255, 0), 2)
                # Or draw contour itself (for outline effect)
                cv2.drawContours(screen, [cnt], -1, (0, 0, 255), 2)

        # Blending effect (your original style)
        blurred = cv2.GaussianBlur(highlighted, (0, 0), sigmaX=1, sigmaY=1)
        dimmed = cv2.addWeighted(screen, 0.1, np.zeros(screen.shape, dtype=screen.dtype), 0, 0)
        result = cv2.add(blurred, dimmed)

        # Resize for small windows
        if screen.shape[0] < 500 or screen.shape[1] < 500:
            result_resized = cv2.resize(result, (500, 500))
        else:
            result_resized = result

        cv2.imshow('FOV Window | (Resized For Better View)', result_resized)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cv2.destroyAllWindows()


def toggle_window(colorant):
    colorant.window_toggled = not colorant.window_toggled
    if colorant.window_toggled:
        threading.Thread(target=show_detection_window, args=(colorant,colorant.grabber, lambda: colorant.window_toggled), daemon=True).start()
