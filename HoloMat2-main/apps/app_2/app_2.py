import pygame
import cv2
import numpy as np
import torch
from PIL import Image
from datetime import datetime
from transformers import AutoImageProcessor, AutoModelForDepthEstimation
from pygame import mixer
import sys
import os
from dotenv import load_dotenv

load_dotenv()

# ---------------- INIT ----------------
pygame.init()
mixer.init()

info = pygame.display.Info()
SCREEN_WIDTH = info.current_w
SCREEN_HEIGHT = info.current_h
SCREEN_SIZE = (SCREEN_WIDTH, SCREEN_HEIGHT)

BLACK = (0, 0, 0)
LIGHT_BLUE = (173, 216, 230)
WHITE = (255, 255, 255)
NAVY_BLUE = (20, 20, 40)

# ---------------- AI MODEL (lazy load) ----------------
checkpoint = "vinvino02/glpn-nyu"
image_processor = None
model = None

def load_model():
    global image_processor, model
    if image_processor is None or model is None:
        print("Loading AI model...")
        image_processor = AutoImageProcessor.from_pretrained(checkpoint)
        model = AutoModelForDepthEstimation.from_pretrained(checkpoint)

# ---------------- SOUND ----------------
def play_sound(file_path):
    try:
        mixer.music.load(file_path)
        mixer.music.play()
    except:
        pass

# ---------------- DEPTH ----------------
def perform_depth_estimation(image):
    load_model()

    pixel_values = image_processor(image, return_tensors="pt").pixel_values

    with torch.no_grad():
        outputs = model(pixel_values)
        predicted_depth = outputs.predicted_depth

    prediction = torch.nn.functional.interpolate(
        predicted_depth.unsqueeze(1),
        size=image.size[::-1],
        mode="bicubic",
        align_corners=False,
    ).squeeze()

    output = prediction.numpy()

    min_d = np.min(output)
    max_d = np.max(output)
    if max_d - min_d == 0:
        max_d = min_d + 1

    norm = (output - min_d) / (max_d - min_d)
    norm = (norm * 255).astype("uint8")

    depth_resized = cv2.resize(norm, (image.width, image.height))
    depth_colored = cv2.applyColorMap(depth_resized, cv2.COLORMAP_JET)

    return depth_colored, norm

# ---------------- SAVE ----------------
def save_images(depth_map):
    try:
        os.makedirs("scans", exist_ok=True)
        name = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = f"scans/depth_{name}.png"
        cv2.imwrite(path, depth_map)
        print("Saved:", path)
    except:
        pass

# ---------------- MAIN APP ----------------
def run(screen, camera_manager=None):
    clock = pygame.time.Clock()

    running = True
    scanning = False
    depth_image = None

    circle_radius = int(min(SCREEN_WIDTH, SCREEN_HEIGHT) * 0.06)

    home_button = (
        circle_radius + 20,
        SCREEN_HEIGHT - circle_radius - 20
    )

    scan_button = pygame.Rect(
        SCREEN_WIDTH // 2 - 150,
        SCREEN_HEIGHT - 150,
        300,
        70
    )

    font = pygame.font.Font(None, 36)

    print("APP 2 RUNNING")

    while running:
        index_pos = None

        # ---------------- CAMERA (optional safe) ----------------
        if camera_manager:
            try:
                if camera_manager.update():
                    hands = camera_manager.get_transformed_landmarks()
                    if hands:
                        for h in hands:
                            index_pos = (int(h[8][0]), int(h[8][1]))
            except:
                pass

        # ---------------- EVENTS ----------------
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                pygame.quit()
                sys.exit()

        screen.fill(BLACK)

        # mouse fallback
        if pygame.mouse.get_pressed()[0]:
            index_pos = pygame.mouse.get_pos()

        # ---------------- INTERACTION ----------------
        if index_pos:

            # HOME BUTTON
            if (index_pos[0] - home_button[0])**2 + (index_pos[1] - home_button[1])**2 <= circle_radius**2:
                running = False

            # SCAN BUTTON
            if scan_button.collidepoint(index_pos) and not scanning:
                scanning = True
                depth_image = None

                play_sound("audio/drawing.wav")

                # animation
                for y in range(0, SCREEN_HEIGHT, 40):
                    screen.fill(BLACK)
                    pygame.draw.line(screen, WHITE, (0, y), (SCREEN_WIDTH, y), 2)
                    pygame.display.flip()
                    pygame.time.delay(5)

                play_sound("audio/quick_click.wav")

                try:
                    if camera_manager:
                        ret, frame = camera_manager.cap.read()
                    else:
                        cap = cv2.VideoCapture(0)
                        ret, frame = cap.read()
                        cap.release()

                    if ret:
                        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                        image = Image.fromarray(frame)

                        depth, raw = perform_depth_estimation(image)
                        save_images(raw)

                        depth_image = depth

                except Exception as e:
                    print("Scan error:", e)

                scanning = False

        # ---------------- DRAW DEPTH ----------------
        if depth_image is not None:
            try:
                surf = pygame.surfarray.make_surface(depth_image.transpose((1, 0, 2)))
                surf = pygame.transform.scale(surf, SCREEN_SIZE)
                screen.blit(surf, (0, 0))
            except:
                pass

        # ---------------- UI ----------------
        pygame.draw.rect(screen, BLACK, (0, SCREEN_HEIGHT - 200, SCREEN_WIDTH, 200))

        pygame.draw.rect(screen, NAVY_BLUE, scan_button, border_radius=15)
        pygame.draw.rect(screen, LIGHT_BLUE, scan_button, 3, border_radius=15)

        text = "Scanning..." if scanning else "Start Scan"
        screen.blit(font.render(text, True, WHITE), (scan_button.x + 80, scan_button.y + 20))

        pygame.draw.circle(screen, NAVY_BLUE, home_button, circle_radius)
        pygame.draw.circle(screen, LIGHT_BLUE, home_button, circle_radius, 3)
        screen.blit(font.render("Home", True, WHITE), (home_button[0] - 30, home_button[1] - 10))

        pygame.display.flip()
        clock.tick(60)

# ---------------- RUN DIRECT ----------------
if __name__ == "__main__":
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("App 2 Fixed")
    run(screen)

