import cv2
import mediapipe as mp
import pyautogui
import numpy as np
import time

mp_hands = mp.solutions.hands
mp_draw  = mp.solutions.drawing_utils
hands    = mp_hands.Hands(
    max_num_hands=1,
    min_detection_confidence=0.85,
    min_tracking_confidence=0.85
)

screen_w, screen_h = pyautogui.size()
pyautogui.FAILSAFE = False

cap   = cv2.VideoCapture(0)
cam_w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
cam_h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

SMOOTH          = 0.2
STABILITY_LIMIT = 8
COOLDOWN        = 0.5
CLICK_THRESHOLD = 35

last_click_time = 0
is_clicking     = False
smooth_x, smooth_y = screen_w // 2, screen_h // 2
prev_sx, prev_sy   = screen_w // 2, screen_h // 2

def landmarks_to_screen(lm, frame_w, frame_h):
    x  = int(lm.x * frame_w)
    y  = int(lm.y * frame_h)
    sx = int(np.interp(x, [50, frame_w - 50], [0, screen_w]))
    sy = int(np.interp(y, [50, frame_h - 50], [0, screen_h]))
    return x, y, sx, sy

while True:
    ret, frame = cap.read()
    if not ret: break

    frame  = cv2.flip(frame, 1)
    rgb    = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    result = hands.process(rgb)
    current_time = time.time()

    if result.multi_hand_landmarks:
        for hand_lm in result.multi_hand_landmarks:
            lm = hand_lm.landmark

            tip8_x, tip8_y, s8x, s8y = landmarks_to_screen(lm[8], cam_w, cam_h)
            tip4_x, tip4_y, _, _     = landmarks_to_screen(lm[4], cam_w, cam_h)

            movement_dist = np.hypot(s8x - prev_sx, s8y - prev_sy)

            if movement_dist > STABILITY_LIMIT:
                smooth_x = smooth_x + SMOOTH * (s8x - smooth_x)
                smooth_y = smooth_y + SMOOTH * (s8y - smooth_y)
                prev_sx, prev_sy = s8x, s8y

            pyautogui.moveTo(int(smooth_x), int(smooth_y), duration=0)

            dist = np.hypot(tip8_x - tip4_x, tip8_y - tip4_y)
            click_ready = current_time - last_click_time > COOLDOWN

            if dist < CLICK_THRESHOLD and click_ready and not is_clicking:
                pyautogui.click()
                last_click_time = current_time
                is_clicking = True
                color_hud = (0, 255, 0)
            elif dist >= CLICK_THRESHOLD:
                is_clicking = False
                color_hud = (255, 165, 0)
            else:
                color_hud = (0, 0, 255)

            mp_draw.draw_landmarks(frame, hand_lm, mp_hands.HAND_CONNECTIONS)
            cv2.line(frame, (tip8_x, tip8_y), (tip4_x, tip4_y), color_hud, 3)

    cv2.imshow("Air Click", frame)
    if cv2.waitKey(1) & 0xFF == ord('q'): break

cap.release()
cv2.destroyAllWindows()
