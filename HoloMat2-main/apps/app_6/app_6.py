import pygame
import sys
import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()
pygame.init()

# ---------------- SCREEN ----------------
SCREEN_WIDTH = int(os.getenv('SCREEN_WIDTH') or 1280)
SCREEN_HEIGHT = int(os.getenv('SCREEN_HEIGHT') or 720)
SCREEN_SIZE = (SCREEN_WIDTH, SCREEN_HEIGHT)

screen = pygame.display.set_mode(SCREEN_SIZE)
pygame.display.set_caption("PCB Designer Pro")

# ---------------- COLORS ----------------
BLACK = (10, 10, 10)
WHITE = (240, 240, 240)
GRAY = (180, 180, 180)
RED = (255, 70, 70)
BLUE = (80, 160, 255)
GREEN = (80, 255, 120)

FONT = pygame.font.Font(None, 32)

GRID = 60
TRACE_THICKNESS = 12
HOLE_RADIUS = 18

# ---------------- CLICK EFFECT ----------------
class ClickEffect:
    def __init__(self, pos):
        self.pos = pos
        self.r = 5
        self.alpha = 200

    def update(self):
        self.r += 4
        self.alpha -= 10

    def draw(self, surf):
        if self.alpha > 0:
            s = pygame.Surface((self.r*2, self.r*2), pygame.SRCALPHA)
            pygame.draw.circle(s, (255,255,255,self.alpha), (self.r,self.r), self.r, 2)
            surf.blit(s, (self.pos[0]-self.r, self.pos[1]-self.r))

# ---------------- UI BUTTON ----------------
class Button:
    def __init__(self, rect, text):
        self.rect = pygame.Rect(rect)
        self.text = text
        self.active = False

    def draw(self):
        color = WHITE if self.active else BLACK
        pygame.draw.rect(screen, color, self.rect, border_radius=10)
        pygame.draw.rect(screen, WHITE, self.rect, 2, border_radius=10)

        txt = FONT.render(self.text, True, BLACK if self.active else WHITE)
        screen.blit(txt, txt.get_rect(center=self.rect.center))

    def hit(self, pos):
        return self.rect.collidepoint(pos)

# ---------------- GRID ----------------
def draw_grid():
    for x in range(0, SCREEN_WIDTH, GRID):
        pygame.draw.line(screen, GRAY, (x,0), (x,SCREEN_HEIGHT))
    for y in range(0, SCREEN_HEIGHT, GRID):
        pygame.draw.line(screen, GRAY, (0,y), (SCREEN_WIDTH,y))

def snap(p):
    return (round(p[0]/GRID)*GRID, round(p[1]/GRID)*GRID)

def export(traces, holes):
    surf = pygame.Surface(SCREEN_SIZE)
    surf.fill(BLACK)

    for a,b,c in traces:
        pygame.draw.line(surf, c, a, b, TRACE_THICKNESS)

    for p,c in holes:
        pygame.draw.circle(surf, c, p, HOLE_RADIUS)

    name = f"pcb_{datetime.now().strftime('%H%M%S')}.png"
    pygame.image.save(surf, name)
    print("Saved:", name)

# ---------------- MAIN ----------------
def run():
    mode = "trace"

    traces = []
    holes = []
    history = []

    start = None
    preview = None

    clicks = []

    buttons = [
        Button((20, 20, 120, 50), "Trace"),
        Button((160, 20, 120, 50), "Hole"),
        Button((300, 20, 120, 50), "Undo"),
        Button((440, 20, 120, 50), "Clear"),
        Button((580, 20, 120, 50), "Export"),
        Button((720, 20, 120, 50), "Home"),
    ]
    buttons[0].active = True

    running = True
    while running:

        mouse = pygame.mouse.get_pos()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                sys.exit()

            if event.type == pygame.MOUSEBUTTONDOWN:
                clicks.append(ClickEffect(mouse))

                snapped = snap(mouse)

                # buttons
                for b in buttons:
                    if b.hit(mouse):
                        for bb in buttons:
                            bb.active = False
                        b.active = True

                        if b.text == "Trace":
                            mode = "trace"
                        elif b.text == "Hole":
                            mode = "hole"
                        elif b.text == "Undo":
                            if history:
                                t = history.pop()
                                if t[0] == "trace":
                                    traces.pop()
                                else:
                                    holes.pop()
                        elif b.text == "Clear":
                            traces.clear()
                            holes.clear()
                            history.clear()
                        elif b.text == "Export":
                            export(traces, holes)
                        elif b.text == "Home":
                            running = False

                        break
                else:
                    # drawing
                    if mode == "hole":
                        holes.append((snapped, RED))
                        history.append(("hole", snapped))

                    elif mode == "trace":
                        start = snapped

            if event.type == pygame.MOUSEBUTTONUP:
                if mode == "trace" and start:
                    end = snap(mouse)
                    traces.append((start, end, BLUE))
                    history.append(("trace", start, end, BLUE))
                    start = None

        # preview line
        if mode == "trace" and start:
            preview = (start, snap(mouse))
        else:
            preview = None

        # ---------------- DRAW ----------------
        screen.fill(BLACK)
        draw_grid()

        # traces
        for a,b,c in traces:
            pygame.draw.line(screen, c, a, b, TRACE_THICKNESS)

        # preview
        if preview:
            pygame.draw.line(screen, GREEN, preview[0], preview[1], TRACE_THICKNESS)

        # holes
        for p,c in holes:
            pygame.draw.circle(screen, c, p, HOLE_RADIUS)

        # buttons
        for b in buttons:
            b.draw()

        # click effects
        for c in clicks[:]:
            c.update()
            c.draw(screen)
            if c.alpha <= 0:
                clicks.remove(c)

        pygame.display.flip()
        pygame.time.delay(16)

run()