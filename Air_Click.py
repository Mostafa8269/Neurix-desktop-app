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

SMOOTH          = 0.7
DEAD_ZONE       = 15
COOLDOWN        = 0.6
CLICK_THRESHOLD = 35

last_click_time = 0
is_clicking     = False
smooth_x        = screen_w // 2
smooth_y        = screen_h // 2
prev_sx         = screen_w // 2
prev_sy         = screen_h // 2


def landmarks_to_screen(lm, frame_w, frame_h):
    x  = int(lm.x * frame_w)
    y  = int(lm.y * frame_h)
    sx = int(np.interp(x, [0, frame_w], [0, screen_w]))
    sy = int(np.interp(y, [0, frame_h], [0, screen_h]))
    return x, y, sx, sy


def apply_dead_zone(cx, cy, px, py, threshold):
    nx = cx if abs(cx - px) > threshold else px
    ny = cy if abs(cy - py) > threshold else py
    return nx, ny


print("Air Click شغال — اضغط Q للإيقاف")

while True:
    ret, frame = cap.read()
    if not ret:
        break

    frame  = cv2.flip(frame, 1)
    rgb    = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    result = hands.process(rgb)

    current_time = time.time()

    if result.multi_hand_landmarks:
        for hand_lm in result.multi_hand_landmarks:
            lm = hand_lm.landmark

            tip8_x, tip8_y, s8x, s8y = landmarks_to_screen(lm[8], cam_w, cam_h)
            tip4_x, tip4_y, _, _     = landmarks_to_screen(lm[4], cam_w, cam_h)

            s8x, s8y = apply_dead_zone(s8x, s8y, prev_sx, prev_sy, DEAD_ZONE)
            smooth_x  = smooth_x + SMOOTH * (s8x - smooth_x)
            smooth_y  = smooth_y + SMOOTH * (s8y - smooth_y)
            prev_sx, prev_sy = int(smooth_x), int(smooth_y)

            pyautogui.moveTo(int(smooth_x), int(smooth_y), duration=0)

            dist        = np.hypot(tip8_x - tip4_x, tip8_y - tip4_y)
            click_ready = current_time - last_click_time > COOLDOWN

            if dist < CLICK_THRESHOLD and click_ready and not is_clicking:
                pyautogui.click()
                last_click_time = current_time
                is_clicking     = True
                color_hud       = (0, 255, 0)
            elif dist >= CLICK_THRESHOLD:
                is_clicking = False
                color_hud   = (255, 165, 0)
            else:
                color_hud = (0, 0, 255) if is_clicking else (255, 165, 0)

            mp_draw.draw_landmarks(frame, hand_lm, mp_hands.HAND_CONNECTIONS)

            cv2.line(frame, (tip8_x, tip8_y), (tip4_x, tip4_y), color_hud, 2)

            if is_clicking:
                cv2.putText(frame, "CLICK!",
                            (cam_w // 2 - 50, 70),
                            cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 255, 0), 3)

    cv2.putText(frame,
                f"THRESHOLD:{CLICK_THRESHOLD} | SMOOTH:{SMOOTH} | DZ:{DEAD_ZONE} | Q quit",
                (10, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (200, 200, 200), 1)

    cv2.imshow("Air Click", frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
