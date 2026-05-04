import pygame
from pygame import mixer
import sys
import math
from dotenv import load_dotenv
import os

# حذفنا Mediapipe و OpenCV من هنا عشان نمنع تضارب الكاميرا
load_dotenv()
pygame.init()
os.environ['SDL_VIDEO_WINDOW_POS'] = "0,0"

import ctypes
try:
    ctypes.windll.user32.SetForegroundWindow(pygame.display.get_wm_info()['window'])
except:
    pass

mixer.init()

# إعدادات الشاشة
info = pygame.display.Info()
SCREEN_WIDTH = int(os.getenv('SCREEN_WIDTH') or info.current_w)
SCREEN_HEIGHT = int(os.getenv('SCREEN_HEIGHT') or info.current_h)
SCREEN_SIZE = (SCREEN_WIDTH, SCREEN_HEIGHT)

PIXEL_TO_MM = 0.264 

# الألوان
BLACK = (10, 10, 15)
LIGHT_BLUE = (0, 255, 255)
WHITE = (255, 255, 255)
NAVY_BLUE = (20, 20, 40)

def distance(p1, p2):
    return math.sqrt((p1[0] - p2[0])**2 + (p1[1] - p2[1])**2)

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

    # إعدادات الصوت
    drag_sound = None
    sound_file = 'dragging.wav' 
    if os.path.exists(sound_file):
        drag_sound = mixer.Sound(sound_file)
        drag_sound.set_volume(0.5)

    home_btn_center = (60, 60)
    home_btn_radius = 40
    clear_btn = pygame.Rect(SCREEN_WIDTH - 160, 30, 130, 50)
    
    clock = pygame.time.Clock()

    while running:
        # الميزة هنا: active_pos هيقرأ مكان الماوس اللي الـ Air Click بيحركه!
        active_pos = pygame.mouse.get_pos()
        active_click = pygame.mouse.get_pressed()[0] 

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            
            # التعامل مع الضغطات (سواء من ماوس حقيقي أو من حركة Pinch)
            if event.type == pygame.MOUSEBUTTONDOWN:
                if distance(event.pos, home_btn_center) <= home_btn_radius:
                    running = False
                elif clear_btn.collidepoint(event.pos):
                    permanent_lines = []
                else:
                    if not drawing:
                        start_point = event.pos
                        drawing = True
                        if drag_sound:
                            mixer.Channel(1).play(drag_sound, loops=-1)

            if event.type == pygame.MOUSEBUTTONUP:
                if drawing:
                    mixer.Channel(1).stop()
                    if start_point and end_point and distance(start_point, end_point) > 5:
                        permanent_lines.append((start_point, end_point))
                drawing = False
                start_point = None
                end_point = None

        if drawing:
            end_point = active_pos

        # الرسم
        screen.fill(BLACK)
        for x in range(0, SCREEN_WIDTH, 50): pygame.draw.line(screen, (30, 30, 40), (x, 0), (x, SCREEN_HEIGHT))
        for y in range(0, SCREEN_HEIGHT, 50): pygame.draw.line(screen, (30, 30, 40), (0, y), (SCREEN_WIDTH, y))
        
        for line in permanent_lines: draw_line_with_measurement(screen, line[0], line[1])
        if drawing and start_point and end_point: draw_line_with_measurement(screen, start_point, end_point)

        # رسم الأزرار
        pygame.draw.circle(screen, NAVY_BLUE, home_btn_center, home_btn_radius)
        pygame.draw.circle(screen, LIGHT_BLUE, home_btn_center, home_btn_radius, 2)
        font = pygame.font.SysFont("Arial", 20, bold=True)
        screen.blit(font.render("HOME", True, WHITE), (35, 50))
        pygame.draw.rect(screen, (150, 0, 0), clear_btn, border_radius=10)
        screen.blit(font.render("CLEAR", True, WHITE), (SCREEN_WIDTH - 130, 45))

        pygame.display.flip()
        clock.tick(60)

if __name__ == '__main__':
    # فتح المسطرة في نافذة كاملة بدون فريم
    screen = pygame.display.set_mode(SCREEN_SIZE, pygame.NOFRAME) 
    pygame.display.set_caption('Neurix Ruler Pro')
    run(screen)
    pygame.quit()
    sys.exit()