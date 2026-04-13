import cv2
import mediapipe as mp
import numpy as np
import math
import random
import time

# ── 1. إعدادات Mediapipe والـ 21 نقطة الاحترافية ────────────────────
mp_hands = mp.solutions.hands
# model_complexity=1 لزيادة دقة تتبع الـ 21 نقطة أثناء الحركة
hands = mp_hands.Hands(model_complexity=1, min_detection_confidence=0.8, min_tracking_confidence=0.7)

cap = cv2.VideoCapture(0)
W, H = 1280, 720
cap.set(3, W)
cap.set(4, H)

# ── 2. بناء خاتم النجوم الاحترافي (Pro Star Ring) ───────────────────
# عدد النجوم في الخاتم
STARS_COUNT = 15
# حجم كل نجمة
STAR_SIZE = 10
# لون ذهبي ملكي للواجهة
HOLOG_COLOR = (40, 190, 240) 

def create_star_points(size):
    # وظيفة لإنشاء نقاط نجمة خماسية (X, Y)
    r1 = size
    r2 = size * 0.4
    pts = []
    for i in range(10):
        rad = math.radians(i * 36) # 360 / 10 = 36 درجة لكل نقطة
        r = r1 if i % 2 == 0 else r2
        pts.append([math.cos(rad) * r, math.sin(rad) * r])
    return np.array(pts)

# إنشاء نقاط النجمة الخماسية مرة واحدة
star_points = create_star_points(STAR_SIZE)

# وظيفة لإضافة تأثير توهج هولوغرافي
def apply_glow(image, color):
    # تأثير توهج احترافي (Bloom)
    blur_col = tuple(min(255, int(c * 0.5)) for c in color)
    blurred = cv2.GaussianBlur(image, (11, 11), 0)
    image = cv2.addWeighted(image, 1.0, blurred, 1.2, 0)
    return image

# متغيرات الموقع والحركة
# مكان الخاتم الحالي (في النص)
curr_x, curr_y = W // 2, H // 2
# سرعة المتابعة (Lerp Factor) - جرب تغيرها لزيادة أو تقليل النعومة
follow_speed = 0.2 
# دوران تلقائي بطيء لإعطاء حياة للهولوغرام
rotation_angle = 0 
t_start = time.time() # للتوقيت

while True:
    ret, frame = cap.read()
    if not ret: break
    frame = cv2.flip(frame, 1) # مرآة
    # واجهة خلفية داكنة تماماً لتركيز النظر على النجوم
    display = np.zeros((H, W, 3), dtype=np.uint8)
    # شبكة (Grid) خافتة جداً لزيادة الطابع التقني
    for x in range(0, W, 120): cv2.line(display, (x, 0), (x, H), (15, 15, 15), 1)
    for y in range(0, H, 120): cv2.line(display, (0, y), (W, y), (15, 15, 15), 1)

    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = hands.process(rgb)
    
    is_grabbing = False 
    status = "IDLE (نظام جاهز)"
    color = (200, 200, 200) # لون باهت في وضع السكون

    if results.multi_hand_landmarks:
        for hand_lms in results.multi_hand_landmarks:
            # ── 3. رسم الـ 21 نقطة الذهبية بشكل أنيق (نيون أخضر خفيف) ────────
            for idx, lm in enumerate(hand_lms.landmark):
                hx, hy = int(lm.x * W), int(lm.y * H)
                # رسم مفاصل اليد الذهبية
                cv2.circle(display, (hx, hy), 3, (100, 215, 255), -1, cv2.LINE_AA)
            
            # رسم الروابط بخطوط رفيعة
            mp.solutions.drawing_utils.draw_landmarks(display, hand_lms, mp_hands.HAND_CONNECTIONS,
                                                     mp.solutions.drawing_utils.DrawingSpec(color=(0, 200, 0), thickness=1),
                                                     mp.solutions.drawing_utils.DrawingSpec(color=(0, 150, 0), thickness=1))

            lms = hand_lms.landmark
            # ── 4. منطق "المسك" الاحترافي بالسبابة والإبهام (Pinch) ─────────────
            t_tip = lms[4] # طرف الإبهام
            i_tip = lms[8] # طرف السبابة
            
            # حساب المسافة بين الصباعين
            dist = math.hypot(t_tip.x - i_tip.x, t_tip.y - i_tip.y)
            
            # لو قربت صوابعك جداً (أقل من 0.06)، كأنك ماسك الخاتم
            if dist < 0.06:
                is_grabbing = True
                status = "GRABBED (ممسوك)"
                color = HOLOG_COLOR # ذهبي عند التفاعل

                # الهدف (Target) هو نقطة منتصف المسافة بين الصباعين
                grab_x = int((t_tip.x + i_tip.x) / 2 * W)
                grab_y = int((t_tip.y + i_tip.y) / 2 * H)
                
                # تطبيق النعومة (Lerp) أثناء المسك فقط
                curr_x += int((grab_x - curr_x) * follow_speed)
                curr_y += int((grab_y - curr_y) * follow_speed)

    # ── 5. دوران ورسم خاتم النجوم الاحترافي الـ 3D (Pro Star Ring) ────────────
    # دوران تلقائي بطيء لإعطاء حياة للهولوغرام
    t = time.time() - t_start
    rotation_angle = t * 0.5 # دوران تلقائي بطيء

    # لو ممسوك، النجوم بتنور أكتر وتكبر شوية
    final_star_size = STAR_SIZE + (2 if is_grabbing else 0)
    final_color = HOLOG_COLOR if is_grabbing else tuple(int(c * 0.7) for c in color)

    # رندرة النجوم في الخاتم بناءً على مكان الخاتم (curr_x, curr_y)
    for i in range(STARS_COUNT):
        # دوران مختلف قليلاً لإعطاء شعور بالتعقيد
        angle = math.radians(i * (360 / STARS_COUNT) + rotation_angle * 100) # دوران الخاتم
        dist_from_center = STAR_SIZE * 3 + (10 if is_grabbing else 0)
        
        # دوران X
        px = int(math.cos(angle) * dist_from_center + curr_x)
        # دوران Y
        py = int(math.sin(angle) * dist_from_center + curr_y)
        
        # رسم تأثير التوهج (Halo) الخارجي
        cv2.circle(display, (px, py), final_star_size + 10, tuple(int(c * 0.3) for c in final_color), 5, cv2.LINE_AA)
        # رسم الدائرة الأساسية (الكرة)
        # cv2.circle(display, (px, py), final_radius, final_color, -1, cv2.LINE_AA)
        
        # رسم الشكل النجمي
        poly = np.array(star_points, np.int32)
        # cv2.fillPoly(display, [poly], final_color) # لون ممتلئ
        
        # رسم الأضلاع بخط ذهبي ناعم
        # cv2.line(display, (px, py), hologram_points, color, 2, cv2.LINE_AA)

    # تأثير التوهج الهولوغرافي
    display = apply_glow(display, HOLOG_COLOR)

    #HUD واجهة المستخدم الاحترافية المعربة
    cv2.putText(display, "SYSTEM: NEURIX HOLOGRAPHIC PRO v1.0", (30, 40), 1, 1.5, HOLOG_COLOR, 2)
    cv2.putText(display, f"STATUS: {status}", (30, 75), 1, 1, (100, 215, 255), 1)
    cv2.putText(display, "GRAB & MOVE SYSTEM (نظام تحريك ممسوك)", (30, H - 30), 1, 1, (150, 150, 150), 1)

    cv2.imshow("Holographic Pro Star Ring v1.0", display)
    if cv2.waitKey(1) & 0xFF == ord('q'): break

cap.release()
cv2.destroyAllWindows()