import pygame
import cv2
import numpy as np
import torch
from PIL import Image
from transformers import AutoImageProcessor, AutoModelForDepthEstimation
from pygame import mixer
import sys
import os

 # ---------------- INIT ----------------
pygame.init()
mixer.init()

info = pygame.display.Info()
SCREEN_WIDTH, SCREEN_HEIGHT = info.current_w, info.current_h
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))

 # الألوان بتاعتك
BLACK = (0, 0, 0)
LIGHT_BLUE = (173, 216, 230)
WHITE = (255, 255, 255)
NAVY_BLUE = (20, 20, 40)

  #---------------- AI MODEL ----------------
checkpoint = "vinvino02/glpn-nyu"
print("Loading Neurix AI Model...")
image_processor = AutoImageProcessor.from_pretrained(checkpoint)
model = AutoModelForDepthEstimation.from_pretrained(checkpoint)

 # ---------------- SOUND ----------------
def play_sound(file_path):
     try:
         mixer.Sound(file_path).play()
     except:
         pass

 # ---------------- DEPTH TO 3D LOGIC ----------------
def process_depth_ai(frame):
     # تحويل الفريم لـ Image ليفهمها الموديل
     image = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
     pixel_values = image_processor(image, return_tensors="pt").pixel_values

     with torch.no_grad():
         outputs = model(pixel_values)
         predicted_depth = outputs.predicted_depth

     # ضبط المقاس
     prediction = torch.nn.functional.interpolate(
         predicted_depth.unsqueeze(1),
         size=image.size[::-1],
         mode="bicubic",
         align_corners=False,
     ).squeeze()

     output = prediction.numpy()
     # تنظيف البيانات للعرض
     norm = cv2.normalize(output, None, 0, 255, cv2.NORM_MINMAX, cv2.CV_8U)
     depth_colored = cv2.applyColorMap(norm, cv2.COLORMAP_JET)
     return depth_colored

  #---------------- MAIN APP ----------------
def run():
     cap = cv2.VideoCapture(0)
     clock = pygame.time.Clock()
     font = pygame.font.Font(None, 36)

     running = True
     depth_surface = None
    
     # أبعاد الزراير بتاعتك
     scan_button = pygame.Rect(SCREEN_WIDTH // 2 - 150, SCREEN_HEIGHT - 120, 300, 70)
     home_button_pos = (100, SCREEN_HEIGHT - 80)
     home_radius = 50

     while running:
         screen.fill(BLACK)
         m_pos = pygame.mouse.get_pos()
        
         for event in pygame.event.get():
             if event.type == pygame.QUIT:
                 running = False
            
             if event.type == pygame.MOUSEBUTTONDOWN:
                  #1.# زرار الـ Scan (بالأنيميشن والصوت بتوعك)
                 if scan_button.collidepoint(m_pos):
                     play_sound("audio/drawing.wav")
                    
                     # أنيميشن خط المسح (زي ما طلبت)
                     for y in range(0, SCREEN_HEIGHT, 30):
                         # عرض الكاميرا الحقيقية خلف الخط
                         ret, frame = cap.read()
                         if ret:
                             frame_surf = pygame.surfarray.make_surface(cv2.transpose(frame))
                             screen.blit(pygame.transform.scale(frame_surf, (SCREEN_WIDTH, SCREEN_HEIGHT)), (0,0))
                        
                         pygame.draw.line(screen, LIGHT_BLUE, (0, y), (SCREEN_WIDTH, y), 3)
                         pygame.display.flip()
                         pygame.time.delay(5)

                     play_sound("audio/quick_click.wav")
                    
                     # تنفيذ المسح بالذكاء الاصطناعي فعلياً
                     ret, frame = cap.read()
                     if ret:
                         depth_img = process_depth_ai(frame)
                         # تحويل النتيجة لسطح بيايم (Pygame Surface)
                         depth_img = cv2.cvtColor(depth_img, cv2.COLOR_BGR2RGB)
                         depth_surface = pygame.surfarray.make_surface(depth_img.transpose((1, 0, 2)))
                         depth_surface = pygame.transform.scale(depth_surface, (SCREEN_WIDTH, SCREEN_HEIGHT))

                 # 2. زرار الهوم
                 if math.sqrt((m_pos[0]-home_button_pos[0])**2 + (m_pos[1]-home_button_pos[1])**2) < home_radius:
                     play_sound("audio/back.wav")
                     running = False

          #--- العرض ---
         if depth_surface:
             screen.blit(depth_surface, (0, 0))
         else:
             # عرض الكاميرا العادية لو مفيش سكان
             ret, frame = cap.read()
             if ret:
                 frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                 raw_surf = pygame.surfarray.make_surface(frame.transpose((1, 0, 2)))
                 screen.blit(pygame.transform.scale(raw_surf, (SCREEN_WIDTH, SCREEN_HEIGHT)), (0, 0))

         # --- واجهة المستخدم (UI) بتاعتك ---
         # زرار الـ Scan
         pygame.draw.rect(screen, NAVY_BLUE, scan_button, border_radius=15)
         pygame.draw.rect(screen, LIGHT_BLUE, scan_button, 3, border_radius=15)
         text_img = font.render("START 3D SCAN", True, WHITE)
         screen.blit(text_img, (scan_button.centerx - 90, scan_button.centery - 15))

         # زرار الـ Home
         pygame.draw.circle(screen, NAVY_BLUE, home_button_pos, home_radius)
         pygame.draw.circle(screen, LIGHT_BLUE, home_button_pos, home_radius, 3)
         home_txt = font.render("HOME", True, WHITE)
         screen.blit(home_txt, (home_button_pos[0] - 35, home_button_pos[1] - 15))

         pygame.display.flip()
         clock.tick(30)

     cap.release()
     pygame.quit()

import math
if __name__ == "__main__":
     run()
    
    
    
