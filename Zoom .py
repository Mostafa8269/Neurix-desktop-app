import cv2
import mediapipe as mp
import numpy as np
import math
 
mp_hands = mp.solutions.hands
mp_draw = mp.solutions.drawing_utils
hands = mp_hands.Hands(model_complexity=0, min_detection_confidence=0.7) # complexity=0 أسرع

cap = cv2.VideoCapture(0)
W, H = 1280, 720
cap.set(cv2.CAP_PROP_FPS, 60) 


curr_scale = 100.0
last_stable_dist = 0
error_margin = 0.02 

vertices = np.array([[-1,-1,1],[1,-1,1],[1,1,1],[-1,1,1],[-1,-1,-1],[1,-1,-1],[1,1,-1],[-1,1,-1]])
faces = [(0,1,2,3), (4,5,6,7), (0,1,5,4), (2,3,7,6), (1,2,6,5), (0,3,7,4)]

while True:
    ret, frame = cap.read()
    if not ret: break
    frame = cv2.flip(frame, 1)
    display = np.zeros((H, W, 3), dtype=np.uint8)
    
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = hands.process(rgb)

    if results.multi_hand_landmarks:
        for hand_lms in results.multi_hand_landmarks:
            mp_draw.draw_landmarks(display, hand_lms, mp_hands.HAND_CONNECTIONS)
            
            lms = hand_lms.landmark
            dist = math.hypot(lms[8].x - lms[4].x, lms[8].y - lms[4].y)

        
            if abs(dist - last_stable_dist) > error_margin:
                curr_scale = dist * 1800 
                last_stable_dist = dist

    
    render_scale = max(1, curr_scale)
    projected = []
    for v in vertices:
        x = int(v[0] * render_scale + W // 2)
        y = int(v[1] * render_scale + H // 2)
        projected.append((x, y))

    for face in faces:
        pts = np.array([projected[v] for v in face], np.int32)
        cv2.fillPoly(display, [pts], (255, 100, 0))
        cv2.polylines(display, [pts], True, (255, 255, 255), 2)

    cv2.putText(display, f"FAST MODE | Scale: {int(curr_scale)}", (50, 50), 1, 1.5, (0, 255, 0), 2)
    cv2.imshow("Super Fast Zoom", display)
    if cv2.waitKey(1) & 0xFF == ord('q'): break

cap.release()
cv2.destroyAllWindows()
