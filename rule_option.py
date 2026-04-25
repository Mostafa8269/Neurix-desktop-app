import pygame
from pygame import mixer
import sys
import math
from dotenv import load_dotenv
import os

load_dotenv()
pygame.init()
# ... بعد pygame.init() ...
os.environ['SDL_VIDEO_WINDOW_POS'] = "0,0" # يضمن ظهورها في بداية الشاشة
# أضف السطر ده قبل تعريف الـ screen
import ctypes
try:
    # السطر ده بيجبر الويندوز إنه يركز على النافذة دي فوراً
    ctypes.windll.user32.SetForegroundWindow(pygame.display.get_wm_info()['window'])
except:
    pass
mixer.init()

# إعدادات الشاشة
info = pygame.display.Info()
SCREEN_WIDTH = int(os.getenv('SCREEN_WIDTH') or info.current_w)
SCREEN_HEIGHT = int(os.getenv('SCREEN_HEIGHT') or info.current_h)
SCREEN_SIZE = (SCREEN_WIDTH, SCREEN_HEIGHT)

# الألوان
BLACK = (10, 10, 15)
LIGHT_BLUE = (0, 255, 255) # لون سيان (Cyberpunk)
WHITE = (255, 255, 255)
NAVY_BLUE = (20, 20, 40)

# معامل التحويل
PIXEL_TO_MM = 0.264 

def distance(p1, p2):
    return math.sqrt((p1[0] - p2[0])**2 + (p1[1] - p2[1])**2)

def play_sound(file_path):
    """دالة بسيطة لتشغيل الأصوات القصيرة"""
    try:
        if os.path.exists(file_path):
            sound = mixer.Sound(file_path)
            sound.play()
    except:
        pass

def draw_line_with_measurement(screen, start_point, end_point):
    if start_point and end_point:
        pygame.draw.line(screen, LIGHT_BLUE, start_point, end_point, 3)
        pygame.draw.circle(screen, WHITE, start_point, 5)
        pygame.draw.circle(screen, WHITE, end_point, 5)
        
        dist_px = distance(start_point, end_point)
        line_length_mm = dist_px * PIXEL_TO_MM
        
        mid_point = ((start_point[0] + end_point[0]) // 2, (start_point[1] + end_point[1]) // 2)
        font = pygame.font.SysFont("Arial", 25, bold=True)
        text_surface = font.render(f'{line_length_mm:.1f} mm', True, WHITE)
        
        text_rect = text_surface.get_rect(center=mid_point)
        pygame.draw.rect(screen, (0, 0, 0), text_rect.inflate(15, 10), border_radius=5)
        screen.blit(text_surface, text_rect)

def run(screen):
    running = True
    drawing = False
    start_point = None
    end_point = None
    permanent_lines = []

    # تحميل صوت السحب (تأكد من الاسم في الفولدر)
    drag_sound = None
    sound_file = 'dragging.wav' 
    if os.path.exists(sound_file):
        drag_sound = mixer.Sound(sound_file)
        drag_sound.set_volume(0.5)

    home_btn = {"center": (60, 60), "radius": 40}
    clear_btn = pygame.Rect(SCREEN_WIDTH - 160, 30, 130, 50)

    clock = pygame.time.Clock()

    while running:
        mouse_pos = pygame.mouse.get_pos()
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if distance(mouse_pos, home_btn["center"]) <= home_btn["radius"]:
                    running = False # هيقفل ويرجع للبرنامج الرئيسي
                elif clear_btn.collidepoint(mouse_pos):
                    permanent_lines = []
                else:
                    start_point = mouse_pos
                    drawing = True
                    # صوت بداية الرسم
                    play_sound('dragging.wav')
            
            elif event.type == pygame.MOUSEBUTTONUP:
                if drawing:
                    mixer.Channel(1).stop() # إيقاف صوت الـ Loop
                    if start_point and end_point and distance(start_point, end_point) > 5:
                        permanent_lines.append((start_point, end_point))
                drawing = False
                start_point = None
                end_point = None
            
            elif event.type == pygame.MOUSEMOTION:
                if drawing:
                    end_point = mouse_pos
                    if drag_sound and not mixer.Channel(1).get_busy():
                        mixer.Channel(1).play(drag_sound, loops=-1)

        # الرسم
        screen.fill(BLACK)

        # رسم الشبكة
        for x in range(0, SCREEN_WIDTH, 50):
            pygame.draw.line(screen, (30, 30, 40), (x, 0), (x, SCREEN_HEIGHT))
        for y in range(0, SCREEN_HEIGHT, 50):
            pygame.draw.line(screen, (30, 30, 40), (0, y), (SCREEN_WIDTH, y))

        for line in permanent_lines:
            draw_line_with_measurement(screen, line[0], line[1])

        if drawing and start_point and end_point:
            draw_line_with_measurement(screen, start_point, end_point)

        # واجهة المستخدم (HOME & CLEAR)
        pygame.draw.circle(screen, NAVY_BLUE, home_btn["center"], home_btn["radius"])
        pygame.draw.circle(screen, LIGHT_BLUE, home_btn["center"], home_btn["radius"], 2)
        font = pygame.font.SysFont("Arial", 20, bold=True)
        screen.blit(font.render("HOME", True, WHITE), (35, 50))

        pygame.draw.rect(screen, (150, 0, 0), clear_btn, border_radius=10)
        screen.blit(font.render("CLEAR", True, WHITE), (SCREEN_WIDTH - 130, 45))

        pygame.display.flip()
        clock.tick(60)

if __name__ == '__main__':
    # تشغيل الشاشة الكاملة لو أردت، أو مقاس الـ .env
    screen = pygame.display.set_mode(SCREEN_SIZE, pygame.NOFRAME) 
    pygame.display.set_caption('Neurix Ruler Pro')
    run(screen)
    pygame.quit()
    sys.exit()