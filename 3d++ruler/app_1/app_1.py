import pygame
from pygame import mixer
import sys
import math
from dotenv import load_dotenv
import os

load_dotenv()
pygame.init()
mixer.init()

# إعدادات الشاشة
info = pygame.display.Info()
SCREEN_WIDTH = int(os.getenv('SCREEN_WIDTH') or info.current_w)
SCREEN_HEIGHT = int(os.getenv('SCREEN_HEIGHT') or info.current_h)
SCREEN_SIZE = (SCREEN_WIDTH, SCREEN_HEIGHT)

# الألوان
BLACK = (10, 10, 15)
LIGHT_BLUE = (173, 216, 230)
WHITE = (255, 255, 255)
NAVY_BLUE = (20, 20, 40)

# معامل التحويل (بكسل إلى مليمتر)
PIXEL_TO_MM = 0.264 

def distance(p1, p2):
    return math.sqrt((p1[0] - p2[0])**2 + (p1[1] - p2[1])**2)

def play_sound(file_path):
    try:
        if os.path.exists(file_path):
            mixer.Sound(file_path).play()
    except Exception as e:
        print(f"Error playing sound: {e}")

def draw_line_with_measurement(screen, start_point, end_point):
    if start_point and end_point:
        # رسم الخط والدوائر عند الأطراف
        pygame.draw.line(screen, LIGHT_BLUE, start_point, end_point, 3)
        pygame.draw.circle(screen, WHITE, start_point, 5)
        pygame.draw.circle(screen, WHITE, end_point, 5)
        
        # حساب المسافة
        dist_px = distance(start_point, end_point)
        line_length_mm = dist_px * PIXEL_TO_MM
        
        # عرض النص في منتصف الخط
        mid_point = ((start_point[0] + end_point[0]) // 2, (start_point[1] + end_point[1]) // 2)
        font = pygame.font.Font(None, 30)
        text_surface = font.render(f'{line_length_mm:.1f} mm', True, WHITE)
        
        # خلفية للنص لتحسين الرؤية
        text_rect = text_surface.get_rect(center=mid_point)
        pygame.draw.rect(screen, (0, 0, 0), text_rect.inflate(10, 6))
        screen.blit(text_surface, text_rect)

def run(screen):
    running = True
    drawing = False
    start_point = None
    end_point = None
    permanent_lines = []

    # إحداثيات الأزرار
    home_btn = {"center": (60, 60), "radius": 40}
    clear_btn = pygame.Rect(SCREEN_WIDTH - 160, 30, 130, 50)

    while running:
        mouse_pos = pygame.mouse.get_pos()
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
                
            elif event.type == pygame.MOUSEBUTTONDOWN:
                # 1. فحص زر الهوم
                if distance(mouse_pos, home_btn["center"]) <= home_btn["radius"]:
                    play_sound('audio/back.wav')
                    running = False
                
                # 2. فحص زر المسح
                elif clear_btn.collidepoint(mouse_pos):
                    play_sound('audio/back.wav')
                    permanent_lines = []
                
                # 3. بدء الرسم
                else:
                    start_point = mouse_pos
                    drawing = True
                    play_sound('audio/quick_click.wav')
            
            elif event.type == pygame.MOUSEBUTTONUP:
                if drawing and start_point and end_point:
                    # التأكد أن الخط له طول قبل إضافته
                    if distance(start_point, end_point) > 5:
                        permanent_lines.append((start_point, end_point))
                        play_sound('audio/quick_click.wav')
                drawing = False
                start_point = None
                end_point = None
                
            elif event.type == pygame.MOUSEMOTION:
                if drawing:
                    end_point = mouse_pos

        # الررررسم
        screen.fill(BLACK)

        # رسم شبكة خفيفة (اختياري للجمال)
        for x in range(0, SCREEN_WIDTH, 50):
            pygame.draw.line(screen, (20, 20, 25), (x, 0), (x, SCREEN_HEIGHT))
        for y in range(0, SCREEN_HEIGHT, 50):
            pygame.draw.line(screen, (20, 20, 25), (0, y), (SCREEN_WIDTH, y))

        # رسم الخطوط المحفوظة
        for line in permanent_lines:
            draw_line_with_measurement(screen, line[0], line[1])

        # رسم الخط الحالي أثناء السحب
        if drawing and start_point and end_point:
            draw_line_with_measurement(screen, start_point, end_point)

        # رسم واجهة المستخدم
        # Home
        pygame.draw.circle(screen, NAVY_BLUE, home_btn["center"], home_btn["radius"])
        pygame.draw.circle(screen, LIGHT_BLUE, home_btn["center"], home_btn["radius"], 2)
        font = pygame.font.Font(None, 24)
        home_txt = font.render("HOME", True, WHITE)
        screen.blit(home_txt, home_txt.get_rect(center=home_btn["center"]))

        # Clear
        pygame.draw.rect(screen, (80, 20, 20), clear_btn, border_radius=8)
        pygame.draw.rect(screen, (255, 50, 50), clear_btn, 2, border_radius=8)
        clear_txt = font.render("CLEAR", True, WHITE)
        screen.blit(clear_txt, clear_txt.get_rect(center=clear_btn.center))

        pygame.display.flip()
        pygame.time.Clock().tick(60) # تحديد الفريمات لراحة المعالج

if __name__ == '__main__':
    #ملفات الصوت
    if not os.path.exists('audio'):
        print("تحذير: مجلد audio غير موجود، لن يعمل الصوت")
    
    screen = pygame.display.set_mode(SCREEN_SIZE)
    pygame.display.set_caption('Neurix Ruler Pro')
    run(screen)