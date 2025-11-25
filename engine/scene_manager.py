import pygame
from settings import PALETTE

class Scene:
    def __init__(self, manager):
        self.manager = manager
    def on_enter(self): pass
    def on_exit(self): pass
    def handle_event(self, event, game_state): pass  # Agregamos game_state
    def update(self, dt, game_state): pass           # Agregamos game_state
    def draw(self, screen, game_state): pass         # Agregamos game_state y screen

class SceneManager:
    def __init__(self, screen, game_state):          # Agregamos game_state
        self.screen = screen
        self.game_state = game_state                  # Almacenamos game_state
        self.stack = []

    def push(self, scene):
        if self.stack:
            self.stack[-1].on_exit()
        self.stack.append(scene)
        scene.on_enter()

    def pop(self):
        if self.stack:
            self.stack[-1].on_exit()
            self.stack.pop()
            if self.stack:
                self.stack[-1].on_enter()

    def replace(self, scene):
        self.pop()
        self.push(scene)

    def current(self):
        return self.stack[-1] if self.stack else None

    def handle_event(self, event):
        if self.current():
            self.current().handle_event(event, self.game_state)  # Pasamos game_state

    def update(self, dt):
        if self.current():
            self.current().update(dt, self.game_state)           # Pasamos game_state

    def draw(self):
        if self.current():
            self.current().draw(self.screen, self.game_state)    # Pasamos game_state y screen
        else:
            self.screen.fill(PALETTE["bg"])   