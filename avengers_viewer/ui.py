# ui.py
import pygame
import os
import subprocess

pygame.init()

W, H = 1280, 720
screen = pygame.display.set_mode((W, H))
pygame.display.set_caption("3D UI System")

BLACK = (0,0,0)
GRAY = (40,40,40)
WHITE = (255,255,255)

def draw_ui():
    screen.fill(BLACK)

    # panels
    pygame.draw.rect(screen, GRAY, (50, 50, 300, 600), border_radius=20)

    # 3D viewport area (visual only)
    pygame.draw.rect(screen, (20,20,20), (400, 50, 800, 600), border_radius=20)
    pygame.draw.rect(screen, WHITE, (400, 50, 800, 600), 2, border_radius=20)

    font = pygame.font.Font(None, 36)
    text = font.render("3D VIEWPORT AREA", True, WHITE)
    screen.blit(text, (650, 60))

running = True

# start 3D viewer
subprocess.Popen(["python", "viewer.py"])

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    draw_ui()
    pygame.display.flip()

pygame.quit()