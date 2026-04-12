import pygame
from pygame import mixer
import time
import os
import sys
import math
from dotenv import load_dotenv

load_dotenv()

# Initialize Pygame
pygame.init()
# Initialize the mixer
mixer.init()
SCREEN_WIDTH = int(os.getenv('SCREEN_WIDTH') or 1920 )
SCREEN_HEIGHT = int(os.getenv('SCREEN_HEIGHT') or 1080 )
SCREEN_SIZE = (SCREEN_WIDTH, SCREEN_HEIGHT)
NAVY_BLUE = (20, 20, 40)
LIGHT_BLUE = (173, 216, 230)
HOME_TOGGLE_DELAY = 1.0  # Delay in seconds for home button toggle
APP_SELECT_DELAY = 1.0  # Delay to prevent immediate app launch
LOGO_DELAY = 1  # Delay in seconds before showing the logo

def play_sound(file_path):
    mixer.music.load(file_path)
    mixer.music.play()

class AppCircle:
    def __init__(self, center, radius, app_index, final_pos, is_main=False):
        self.center = center
        self.radius = radius
        self.app_index = app_index
        self.is_main = is_main
        self.visible = is_main
        self.final_pos = final_pos
        self.hover_time = 0
        self.is_hovered_flag = False
        self.animation_start_time = None
        self.is_animating = False
        self.image = self.load_image()

    def load_image(self):
        # Load the home logo if this is the main circle, otherwise load the app image
        if self.is_main:
            image_path = './logo.jpg'
            if os.path.exists(image_path):
                image = pygame.image.load(image_path)
                return pygame.transform.scale(image, (2 * self.radius, 2 * self.radius))
        else:
            image_path = f'./apps/app_{self.app_index}/app_{self.app_index}.jpg'
            if os.path.exists(image_path):
                image = pygame.image.load(image_path)
                return pygame.transform.scale(image, (2 * self.radius, 2 * self.radius))
        return None

    def draw(self, screen):
        # Adjust radius when hovered
        if self.is_hovered_flag:
            current_radius = self.radius + min((time.time() - self.hover_time) * 10, self.radius * 0.5)
        else:
            current_radius = self.radius

        # Animate position
        if self.animation_start_time is not None:
            elapsed_time = time.time() - self.animation_start_time
            if elapsed_time < 0.5:
                t = elapsed_time / 0.5
                if self.visible:
                    self.center = (
                        int((1 - t) * SCREEN_SIZE[0] // 2 + t * self.final_pos[0]),
                        int((1 - t) * SCREEN_SIZE[1] // 2 + t * self.final_pos[1])
                    )
                else:
                    self.center = (
                        int(t * SCREEN_SIZE[0] // 2 + (1 - t) * self.final_pos[0]),
                        int(t * SCREEN_SIZE[1] // 2 + (1 - t) * self.final_pos[1])
                    )
            else:
                self.center = self.final_pos if self.visible else (SCREEN_SIZE[0] // 2, SCREEN_SIZE[1] // 2)
                self.animation_start_time = None
                self.is_animating = False

        # Draw the circle
        if self.visible or self.is_animating:
            if self.image:
                top_left = (self.center[0] - self.radius, self.center[1] - self.radius)
                screen.blit(self.image, top_left)
            else:
                pygame.draw.circle(screen, NAVY_BLUE, self.center, int(current_radius))
            pygame.draw.circle(screen, LIGHT_BLUE, self.center, int(current_radius), 5)

    def is_hovered(self, pos):
        return math.hypot(pos[0] - self.center[0], pos[1] - self.center[1]) <= self.radius

def map_coords(x, y):
    mapped_x = (y / 1080) * 1920
    mapped_y = 1080 - ((x / 1920) * 1080)
    return mapped_x, mapped_y

def create_circles():
    circles = []
    num_circles = 8
    center_x, center_y = SCREEN_SIZE[0] // 2, SCREEN_SIZE[1] // 2
    main_circle_radius = 100
    app_circle_radius = 50
    distance = 250

    main_circle = AppCircle((center_x, center_y), main_circle_radius, 0, (center_x, center_y), is_main=True)
    circles.append(main_circle)

    angle_step = 360 / num_circles
    for i in range(num_circles):
        angle = math.radians(angle_step * i)
        x = center_x + int(distance * math.cos(angle))
        y = center_y + int(distance * math.sin(angle))
        circles.append(AppCircle((center_x, center_y), app_circle_radius, i + 1, (x, y)))
    return circles

def run_home_screen(screen):
    circles = create_circles()
    main_circle = circles[0]
    running = True
    apps_visible = False
    last_toggle_time = 0
    last_app_select_time = 0

    # Wait for 10 seconds of black screen before showing the logo and circles
    start_time = time.time()
    while time.time() - start_time < LOGO_DELAY:
        screen.fill((0, 0, 0))
        pygame.display.flip()
        pygame.time.delay(100)  # Small delay to avoid high CPU usage

    play_sound("./audio/startup.wav")
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                x, y = event.pos
                mapped_x, mapped_y = map_coords(x, y)

                for circle in circles:
                    if circle.is_hovered((mapped_x, mapped_y)):
                        circle.is_hovered_flag = True
                        if circle.is_main:
                            play_sound("./audio/home.wav")
                            if time.time() - last_toggle_time > HOME_TOGGLE_DELAY:
                                apps_visible = not apps_visible
                                last_toggle_time = time.time()
                                for app_circle in circles[1:]:
                                    app_circle.visible = apps_visible
                                    app_circle.animation_start_time = time.time()
                                    app_circle.is_animating = True
                                    last_app_select_time = time.time() + APP_SELECT_DELAY
                        elif circle.visible and apps_visible:
                            if time.time() > last_app_select_time:
                                try:
                                    app = f'app_{circle.app_index}.app_{circle.app_index}'
                                    mod = __import__(f'apps.{app}', fromlist=[''])
                                    play_sound("./audio/confirmation.wav")
                                    mod.run(screen)  # Run the app
                                    last_app_select_time = time.time()
                                except ModuleNotFoundError:
                                    play_sound("./audio/reject.wav")
                    else:
                        circle.hover_time = time.time() if circle.visible else 0

        screen.fill((0, 0, 0))

        # Draw the border around the screen
        pygame.draw.rect(screen, (255, 255, 255), (0, 0, SCREEN_WIDTH, SCREEN_HEIGHT), 10)

        for circle in circles:
            circle.draw(screen)

        pygame.display.flip()
        pygame.time.delay(50)

if __name__ == '__main__':
    os.environ['SDL_VIDEO_WINDOW_POS'] = '-3440,0'
    screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
    pygame.display.set_caption('Home Screen')
    run_home_screen(screen)