from cmath import isclose
import pygame
from pygame.locals import *
from typing import Tuple
from random import shuffle
import sys
import os

BLUE  = (0, 0, 255)
RED   = (255, 0, 0)
DARKRED = (150, 0, 0)
GREEN = (0, 255, 0)
DARKGREEN = (0, 150, 0)
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
TRANSPARENT = (0, 0, 0, 0)


number = float | int
def transform(num: number, old_bounds: Tuple[number], new_bounds: Tuple[number]) -> number:
    '''
    Scales number from old bounds to new bounds.  Bounds are assumed to be tuples of format (lower bound, upper bound).
    '''
    ratio = (num - old_bounds[0]) / (old_bounds[1] - old_bounds[0])
    return new_bounds[0] + ratio * (new_bounds[1] - new_bounds[0])


def create_help_menu(size: Tuple[int, int]) -> pygame.Surface:
    menu = pygame.Surface(size, SRCALPHA)
    menu.fill((150,150,150,200))
    x, y = menu.get_rect().center

    title = FONT.render('Help', True, WHITE)
    title_len = FONT.size('Help')
    menu.blit(title, (x - title_len[0]/2, title_len[1] + int(size[1]/2 * 0.05)))

    controls = (
        'Up Arrow --------------------- Thruster Up',
        'Down Arrow -------------- Thruster Down',
        'Space Bar -------------- Open Parachute'
    )
    control_txts = [(FONT.render(control, True, WHITE), FONT.size(control)) for control in controls]
    y *= 0.9
    for control_txt, control_len in control_txts:
        menu.blit(control_txt, (x - control_len[0]/2, y))
        y += control_len[1]

    return menu

# Ty StackOverflow
def resource_path(relative_path):
    # """ Get absolute path to resource, works for dev and for PyInstaller """
    # try:
    #     # PyInstaller creates a temp folder and stores path in _MEIPASS
    #     base_path = sys._MEIPASS
    # except Exception:
    #     base_path = os.path.abspath(".")

    # return os.path.join(base_path, relative_path)

    if getattr(sys, 'frozen', False):
        return os.path.join(sys._MEIPASS, relative_path)
    else:
        return relative_path


class Parachuter(pygame.sprite.Sprite):
    B = 0.1
    INCREMENT = 0.1

    def __init__(self):
        super(Parachuter, self).__init__()
        path = r"sprites\player"
        self.sprites = {filename[:-4]: pygame.image.load(f"{resource_path(path)}\\{filename}").convert() for filename in os.listdir(resource_path(path))}
        for key in self.sprites:
            self.sprites[key].set_colorkey(WHITE)
        
        self.surf = self.sprites['normal']
        self.hitbox = self.surf.get_rect()
        self.halfheight = self.hitbox.height/2
        self.hitbox.center = (SCREEN_WIDTH/4, SCREEN_HEIGHT/2)
        self.offset = 0
        self.drawbox = self.hitbox.copy()

        self.accelerations = {
            'weight': G,
            'thrusters': 0,
            'drag': 0
        }
        self.velocity = 0
        self.y = self.hitbox.centery
        self.parachute = False
        self.spacebar = False

    def update(self, pressed_buttons=None):
        # Can't hold multiple down at once
        if pressed_buttons:
            if pressed_buttons[K_SPACE]:
                self.parachute = not self.parachute if not self.spacebar else self.parachute
                self.spacebar = True
            elif not pressed_buttons[K_SPACE]:
                self.spacebar = False
                if pressed_buttons[K_UP]:
                    self.parachute = False
                    self.accelerations['thrusters'] += Parachuter.INCREMENT
                elif pressed_buttons[K_DOWN]:
                    self.parachute = False
                    self.accelerations['thrusters'] -= Parachuter.INCREMENT
        self.step()

    def step(self):
        if self.parachute:
            self.accelerations['drag'] = -Parachuter.B * self.velocity # * abs(self.velocity)
        self.velocity += sum(self.accelerations.values()) * DT
        self.y -= self.velocity * DT
        self.hitbox.centery = round(self.y)

        if self.y + self.halfheight >= SCREEN_HEIGHT:# and self.velocity < 0:
            self.hitbox.bottom = SCREEN_HEIGHT
            self.y = self.hitbox.centery
            self.velocity = 0
            self.parachute = False
        if self.y - self.halfheight <= 0 and self.velocity > 0:
            self.hitbox.top *= -1
            self.hitbox.y *= -1
            self.velocity *= -1
        
        self.update_sprite()
        self.drawbox.centery = self.hitbox.centery - self.offset
        # print(self.drawbox.center, self.hitbox.center)

    def update_sprite(self):
        # Method assumes cannot thruster and parachuter at the same time
        is_down = False
        if not isclose(self.accelerations['thrusters'], 0, abs_tol = Parachuter.INCREMENT/10):
            is_down = self.accelerations['thrusters'] < 0
            self.surf = self.sprites['thruster_down'] if is_down else self.sprites['thruster_up']

        elif self.parachute and self.velocity != 0:
            is_down = self.velocity < 0
            self.surf = self.sprites['parachute_down'] if is_down else self.sprites['parachute_up']
        
        else:
            self.surf = self.sprites['normal']
        
        self.offset = self.surf.get_height() - self.halfheight*2 if is_down else 0
        self.drawbox.centerx = self.hitbox.centerx - (self.surf.get_width() - self.drawbox.width)/2

    def __setattr__(self, name, value):
        if name == "parachute":
            if value:
                self.accelerations['thrusters'] = 0
            else:
                self.accelerations['drag'] = 0
        super(Parachuter, self).__setattr__(name, value)


class Plot(pygame.sprite.Sprite):
    def __init__(self):
        super(Plot, self).__init__()
        self.size = self.width, self.height = (SCREEN_WIDTH/2, SCREEN_HEIGHT/2)

        self.axes = pygame.Surface(self.size, SRCALPHA)
        self.axes.fill((100,100,100,175))
        pygame.draw.line(self.axes, BLACK, (0, 0), (0, self.height))
        pygame.draw.line(self.axes, BLACK, (0, (self.height-1)/2), (self.width-1, (self.height-1)/2))
        self.points = pygame.Surface((1, self.height))

        self.update_surface()
        self.rect = self.surf.get_rect()
        self.rect.center = (SCREEN_WIDTH*0.75, SCREEN_HEIGHT*0.375)
        self.colors = [RED, GREEN, BLUE]
        shuffle(self.colors)

    def update(self, parachuter):
        data = (SCREEN_HEIGHT - parachuter.y, parachuter.velocity, sum(parachuter.accelerations.values()))
        all_old_bounds = (
            (0, SCREEN_HEIGHT),
            (-50, 50),
            (-5, 5)
        )
        new_bounds = (SCREEN_HEIGHT*0.5, SCREEN_HEIGHT*0)
        
        new_data = pygame.Surface((1, self.height))
        for data_point, color, old_bounds in zip(data, self.colors, all_old_bounds):
            data_point = transform(data_point, old_bounds, new_bounds)
            pygame.draw.circle(new_data, color, (0, data_point), 1)

        width = self.points.get_width() 
        # print(width) 
        if width >= self.width:
            tmp = pygame.Surface(self.size)
            tmp.blit(self.points, (0,0), (1, 0, self.width, self.height))
            tmp.blit(new_data, (self.width-2, 0))
            self.points = tmp
            # self.points.blit(self.points, (-1,0), (0,0,self.width,self.height))
            # self.points.blit(new_data, (self.width-2, 0))
        else:
            new_points = pygame.Surface((width + 1, self.height))
            new_points.blit(self.points, (0, 0))
            new_points.blit(new_data, (width-1, 0))
            self.points = new_points
        self.update_surface()

    def update_surface(self):
        self.surf = pygame.Surface(self.size, SRCALPHA)
        self.surf.fill(TRANSPARENT)
        self.surf.blit(self.axes, (0,0))
        self.points.set_colorkey(BLACK, pygame.RLEACCEL)
        self.surf.blit(self.points, (0,0))


class Button(pygame.sprite.Sprite):
    PADDING_HORZ = 10
    PADDING_VERT = 5

    def __init__(self, text, pos, size=None, color=(170,170,170), text_pos=None):
        super(Button, self).__init__()
        self.text = text
        self.txt_surf = FONT.render(text, True, WHITE)
        font_size = FONT.size(text)
        self.size = self.width, self.height = size if size is not None else (font_size[0] + 2*Button.PADDING_HORZ, font_size[1] + 2*Button.PADDING_VERT)

        if text_pos == "LEFT":
            self.text_pos = ((Button.PADDING_HORZ, self.height/2 - font_size[1]/2))
        else:
            self.text_pos = (self.width/2 - font_size[0]/2, self.height/2 - font_size[1]/2)

        self.surf = pygame.Surface(self.size)
        self.color = color
        self.surf.fill(self.color)
        self.surf.blit(self.txt_surf, self.text_pos)
        self.rect = self.surf.get_rect()
        self.rect.x, self.rect.y = pos
    
    def update(self, text="", color=None):
        if color is not None:
            self.color = color
        if text:
            self.text = text
        self.txt_surf = FONT.render(self.text, True, WHITE)
        self.surf.fill(self.color)
        self.surf.blit(self.txt_surf, self.text_pos)


class Selection(pygame.sprite.Sprite):
    SELECTED = (90,90,90)
    UNSELECTED = (190,190,190)

    def __init__(self, text, pos):
        super(Selection, self).__init__()
        Button.PADDING_VERT = 7
        self.body = Button(text, pos, size=(SCREEN_WIDTH*0.46, SCREEN_HEIGHT*0.1), color=(135,135,135), text_pos="LEFT")
        Button.PADDING_VERT = 5
        x = 550
        self.choices = []
        for col in ["Red", "Green", "Blue"]:
            button = Button(col, (x, pos[1]+12), color=Selection.UNSELECTED)
            self.choices.append(button)
            x += button.rect.width + 10
        self.selected = None

        self.surf = self.body.surf.copy()
        self.rect = self.body.rect.copy()

    def clicked(self, pos):
        for choice in self.choices:
            if choice.rect.collidepoint(pos):
                if self.selected is not None:
                    self.selected.update(color=Selection.UNSELECTED)
                if self.selected == choice:
                    self.selected = None
                else:
                    self.selected = choice
                    choice.update(color=Selection.SELECTED)

    def answer(self, plot):
        mapping = {name: i for i, name in enumerate(["Displacement:", "Velocity:", "Acceleration:"])}
        mapping2 = {RED: 0, GREEN: 1, BLUE: 2}
        correct = mapping2[plot.colors[mapping[self.body.text]]]
        if self.choices[correct] != self.selected:
            self.selected.update(color=DARKRED)
        self.choices[correct].update(color=DARKGREEN)



SCREEN_HEIGHT = 600
SCREEN_WIDTH = 800
FRAME_RATE = 60
DT = 0.2
G = -1

pygame.init()

SCREEN = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
FONT = pygame.font.SysFont("arial", 24)
pygame.display.set_caption("Parachuter")
clock = pygame.time.Clock()

help_menu = create_help_menu((SCREEN_WIDTH/2+100, SCREEN_HEIGHT/2+100))
W = SCREEN_WIDTH * 0.51
H = SCREEN_HEIGHT * 0.025
btn_names = ["Help", "Guess", "Restart", "Quit"]
buttons = pygame.sprite.Group()
for btn_name in btn_names:
    btn = Button(btn_name, (W, H))
    buttons.add(btn)
    W += btn.width + 30

W = SCREEN_WIDTH * 0.51
H = SCREEN_HEIGHT * 0.65
motion_names = ["Displacement:", "Velocity:", "Acceleration:"]
selections = pygame.sprite.Group()
for motion_name in motion_names:
    selection = Selection(motion_name, (W, H))
    selections.add(selection)
    H += selection.rect.height + 10

bg_surf = pygame.image.load(r"sprites\background.png").convert()
bg_rect = bg_surf.get_rect()

def init():
    global parachuter; global plot; global guess_open; global guess_done; global help_open; global buttons; global selections
    parachuter, plot, help_open, guess_open, guess_done = Parachuter(), Plot(), False, False, False
    buttons.sprites()[1].update(text="Guess")
    for selection in selections:
        selection.selected = None
        for choice in selection.choices:
            choice.update(color=Selection.UNSELECTED)
init()

running = True
while running:

    for event in pygame.event.get():
        if event.type == QUIT:
            running = False

        elif event.type == MOUSEBUTTONUP:
            pos = pygame.mouse.get_pos()

            for button in buttons:
                if button.rect.collidepoint(pos):
                    match button.text:
                        case "Help":
                            help_open = not help_open
                        case "Guess":
                            if not guess_open and not guess_done:
                                help_open = guess_done = False
                                guess_open = True
                                button.update(text="Check")
                        case "Check":
                            if guess_open and not guess_done:
                                for selection in selections:
                                    if selection.selected is None:
                                        break
                                else:
                                    help_open = guess_open = False
                                    guess_done = True
                                    button.update(text="Again")
                                    for selection in selections:
                                        selection.answer(plot)
                        case "Again":
                            if guess_done:
                                button.update(text="Guess")
                                init()
                        case "Restart":
                            init()
                        case "Quit":
                            running = False
            if guess_open:
                for selection in selections:
                    if selection.rect.collidepoint(pos):
                        selection.clicked(pos)

            if guess_open:
                pass

    SCREEN.blit(bg_surf, bg_rect)

    if not (help_open or guess_open or guess_done):
        pressed_keys = pygame.key.get_pressed()
        parachuter.update(pressed_keys)
        plot.update(parachuter)

    SCREEN.blit(parachuter.surf, parachuter.drawbox)
    SCREEN.blit(plot.surf, plot.rect)
    for button in buttons:
        SCREEN.blit(button.surf, button.rect)

    if guess_open or guess_done:
        for selection in selections:
            SCREEN.blit(selection.surf, selection.rect)
            for choice in selection.choices:
                SCREEN.blit(choice.surf, choice.rect)
    if help_open:
        size = help_menu.get_rect().size
        SCREEN.blit(help_menu, (SCREEN_WIDTH/2-size[0]/2, SCREEN_HEIGHT/2-size[1]/2))

    pygame.display.flip()

    clock.tick(FRAME_RATE/2)

pygame.quit()
sys.exit(0)
