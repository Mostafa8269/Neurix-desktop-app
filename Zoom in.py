import cv2
import mediapipe as mp
import numpy as np
import math
import random

# ── 1. إعدادات Mediapipe والـ 21 نقطة ──────────────────────────
mp_hands = mp.solutions.hands
# رسم الـ 21 نقطة والروابط
mp_draw = mp.solutions.drawing_utils
hands = mp_hands.Hands(model_complexity=0, min_detection_confidence=0.8)

cap = cv2.VideoCapture(0)
W, H = 1280, 720

# ── 2. بناء المكعب 3D (ثابت) ──────────────────────────────────
vertices = np.array([
    [-1, -1,  1], [1, -1,  1], [1,  1,  1], [-1,  1,  1],
    [-1, -1, -1], [1, -1, -1], [1,  1, -1], [-1,  1, -1]
])
faces = [(0, 1, 2, 3), (4, 5, 6, 7), (0, 1, 5, 4), (2, 3, 7, 6), (1, 2, 6, 5), (0, 3, 7, 4)]
face_colors = [(255, 100, 0), (0, 100, 255), (100, 100, 100), (200, 200, 200), (0, 255, 0), (255, 0, 255)]

current_zoom = 100

while True:
    ret, frame = cap.read()
    if not ret: break
    frame = cv2.flip(frame, 1)
    display = np.zeros((H, W, 3), dtype=np.uint8)

    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = hands.process(rgb)

    if results.multi_hand_landmarks:
        for hand_lms in results.multi_hand_landmarks:
            # ── 3. رسم الـ 21 نقطة والروابط فوراً ──────────────────────
            mp_draw.draw_landmarks(display, hand_lms, mp_hands.HAND_CONNECTIONS,
                                 mp_draw.DrawingSpec(color=(0, 255, 0), thickness=2, circle_radius=4),
                                 mp_draw.DrawingSpec(color=(0, 200, 0), thickness=2))
            
            lms = hand_lms.landmark
            # حساب الزوم (بين السبابة 8 والإبهام 4)
            dist = math.hypot(lms[4].x - lms[8].x, lms[4].y - lms[8].y)
            current_zoom = np.interp(dist, [0.05, 0.4], [50, 600])

    # ── 4. رسم المكعب الثابت مع الـ Zoom In ───────────────────────
    projected_pts = []
    for v in vertices:
        # تكبير فقط (ثابت بدون دوران)
        scaled = v * current_zoom
        px = int(scaled[0] + W // 2)
        py = int(scaled[1] + H // 2)
        projected_pts.append((px, py))

    # رسم أوجه المكعب
    for i, face in enumerate(faces):
        pts = np.array([projected_pts[v] for v in face], np.int32).reshape((-1, 1, 2))
        cv2.fillPoly(display, [pts], face_colors[i], cv2.LINE_AA)
        cv2.polylines(display, [pts], True, (255, 255, 255), 2)

    #HUD
    cv2.putText(display, f"ZOOM: {int(current_zoom)}", (40, 50), 1, 1.5, (0, 255, 0), 2)
    cv2.putText(display, "21 POINTS ACTIVE", (40, 90), 1, 1, (200, 200, 200), 1)

    cv2.imshow("Hand 21 Points & Cube Zoom", display)
    if cv2.waitKey(1) & 0xFF == ord('q'): break

cap.release()
cv2.destroyAllWindows()