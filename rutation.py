import cv2
import mediapipe as mp
import numpy as np
import math   # ضروري لحسابات الدوران
import time   # ضروري لحسابات الوقت والنبض
import random

# ── 1. إعدادات النظام ──────────────────────────────────────────────
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(model_complexity=0, min_detection_confidence=0.8, min_tracking_confidence=0.7)

cap = cv2.VideoCapture(0)
WIDTH, HEIGHT = 1280, 720
cap.set(3, WIDTH)
cap.set(4, HEIGHT)

# ── 2. بناء نجوم الكرة (السديم) ───────────────────────────────
STARS_COUNT = 250
nebula_points = []
for _ in range(STARS_COUNT):
    phi = random.uniform(0, 2 * math.pi)
    costheta = random.uniform(-1, 1)
    r = 180 * (random.uniform(0, 1)**(1/3))
    theta = math.acos(costheta)
    x = r * math.sin(theta) * math.cos(phi)
    y = r * math.sin(theta) * math.sin(phi)
    z = r * math.cos(theta)
    nebula_points.append({
        'pos': [x, y, z], 
        'speed': random.uniform(0.02, 0.05),
        'phase': random.uniform(0, 2 * math.pi)
    })

def rotate_3d(pt, rx, ry):
    ax, ay = math.radians(rx), math.radians(ry)
    x, y, z = pt
    # تدوير حول X
    y1 = y * math.cos(ax) - z * math.sin(ax)
    z1 = y * math.sin(ax) + z * math.cos(ax)
    # تدوير حول Y
    x2 = x * math.cos(ay) + z1 * math.sin(ay)
    z2 = -x * math.sin(ay) + z1 * math.cos(ay)
    return [x2, y1, z2]

def project(pt, cx, cy):
    z = pt[2] + 500
    return int(pt[0] * 650 / z + cx), int(pt[1] * 650 / z + cy), z

# ── 3. متغيرات التحكم ──────────────────────────────────────────
angle_x, angle_y = 0, 0
FIXED_CX, FIXED_CY = WIDTH // 2, HEIGHT // 2
GOLD = (40, 190, 240) # اللون الذهبي (BGR)

while True:
    ret, frame = cap.read()
    if not ret: break
    frame = cv2.flip(frame, 1)
    display = np.zeros((HEIGHT, WIDTH, 3), dtype=np.uint8)
    
    # رسم الشبكة الخلفية (Grid)
    for i in range(0, WIDTH, 60): cv2.line(display, (i, 0), (i, HEIGHT), (30, 30, 30), 1)
    for i in range(0, HEIGHT, 60): cv2.line(display, (0, i), (WIDTH, i), (30, 30, 30), 1)

    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = hands.process(rgb)
    
    control_active = False
    hand_color = (120, 120, 120) # قيمة افتراضية للون اليد (رمادي)

    if results.multi_hand_landmarks:
        lms = results.multi_hand_landmarks[0].landmark
        
        # شرط التحكم: السبابة مفرودة وباقي الأصابع مقبوضة
        # 8 = طرف السبابة، 6 = مفصل السبابة، 12,16,20 = باقي الأصابع
        index_is_up = lms[8].y < lms[6].y
        others_are_down = all(lms[t].y > lms[p].y for t, p in [(12,10), (16,14), (20,18)])
        
        if index_is_up and others_are_down:
            control_active = True
            hand_color = GOLD # لو التحكم شغال، لون اليد ذهبي
            # تحديث الزوايا بناءً على مكان السبابة
            angle_y = (lms[8].x - 0.5) * 360
            angle_x = (lms[8].y - 0.5) * -360
        
        # رسم الـ 21 نقطة
        for conn in mp_hands.HAND_CONNECTIONS:
            p1 = (int(lms[conn[0]].x * WIDTH), int(lms[conn[0]].y * HEIGHT))
            p2 = (int(lms[conn[1]].x * WIDTH), int(lms[conn[1]].y * HEIGHT))
            cv2.line(display, p1, p2, hand_color, 2)
        for lm in lms:
            cv2.circle(display, (int(lm.x*WIDTH), int(lm.y*HEIGHT)), 3, (255, 255, 255), -1)

    # ── 4. رسم نجوم الكرة ────────────────────────────────────────
    t_pulse = time.time()
    stars_draw = []
    for s in nebula_points:
        p_rot = rotate_3d(s['pos'], angle_x, angle_y)
        px, py, pz = project(p_rot, FIXED_CX, FIXED_CY)
        stars_draw.append((px, py, pz, s['phase']))

    # ترتيب العمق
    stars_draw.sort(key=lambda x: x[2], reverse=True)

    for x, y, z, phase in stars_draw:
        if 0 <= x < WIDTH and 0 <= y < HEIGHT:
            size = max(1, int(5 * (400/z)))
            # نبض ضوئي بسيط
            twinkle = abs(math.sin(t_pulse * 3 + phase))
            
            if control_active:
                # لون ذهبي نابض
                current_star_col = tuple(int(c * twinkle) for c in GOLD)
            else:
                # لون رمادي خافت
                current_star_col = (50, 50, 50)
                
            cv2.circle(display, (x, y), size, current_star_col, -1)

    # واجهة المستخدم (HUD)
    status_text = "JOYSTICK ACTIVE" if control_active else "LOCKED: FIST + INDEX"
    cv2.putText(display, status_text, (40, 50), 1, 1.5, hand_color, 2)

    cv2.imshow("Golden Star Sphere Control", display)
    if cv2.waitKey(1) & 0xFF == ord('q'): break

cap.release()
cv2.destroyAllWindows()