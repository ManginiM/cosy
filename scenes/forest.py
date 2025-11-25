import pygame
from settings import WIDTH, HEIGHT, PALETTE
from engine.scene_manager import Scene
from engine.narrator import Narrator
from engine.ui import StatsDisplay

class ForestScene(Scene):
    def __init__(self, manager, state, audio):
        super().__init__(manager)
        self.state = state
        self.audio = audio
        self.font = pygame.font.SysFont("arial", 28)
        self.narrator = Narrator(self.font)
        self.stats_display = StatsDisplay(state)
        
        # Cargar fondo del parque
        try:
            self.bg = pygame.image.load("assets/images/forest_bg.png").convert()
            self.bg = pygame.transform.smoothscale(self.bg, (WIDTH, HEIGHT))
        except:
            self.bg = pygame.Surface((WIDTH, HEIGHT))
            self.bg.fill((100, 150, 100))

    def on_enter(self):
        self.narrator.say("Has llegado al parque. Esta es la Escena 2: El Parque.")
        self.narrator.say("Próximamente: La persecución de espíritus...")

    def handle_event(self, event, game_state):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            from scenes.title import TitleScene
            self.manager.replace(TitleScene(self.manager))

    def update(self, dt, game_state):
        self.narrator.update(dt)

    def draw(self, screen, game_state):
        surf = screen
        surf.blit(self.bg, (0, 0))
        
        title = self.font.render("ESCENA 2: EL PARQUE", True, PALETTE["ink"])
        title_rect = title.get_rect(center=(WIDTH//2, HEIGHT//2))
        surf.blit(title, title_rect)
        
        instruction = self.font.render("Presiona ESC para volver al menú", True, PALETTE["ink"])
        instruction_rect = instruction.get_rect(center=(WIDTH//2, HEIGHT//2 + 50))
        surf.blit(instruction, instruction_rect)
        
        self.narrator.draw(surf)
        self.stats_display.draw(surf)