import pygame, json, sys
from settings import WIDTH, HEIGHT, PALETTE
from engine.scene_manager import Scene
from engine.ui import Button

class EndingScene(Scene):
    def __init__(self, manager, state, audio):
        super().__init__(manager)
        self.state = state
        self.audio = audio
        self.font_big = pygame.font.SysFont("arial", 36)
        self.font = pygame.font.SysFont("arial", 22)
        with open("narrative/script.json", "r", encoding="utf-8") as f:
            self.script = json.load(f)

        self.text = ""
        self.input_cooldown = 0.2
        self.buttons = []

        try:
            self.bg = pygame.image.load("assets/images/ending_bg.png").convert()
            self.bg = pygame.transform.smoothscale(self.bg, (WIDTH, HEIGHT))
        except Exception:
            self.bg = None

    def on_enter(self):
        # Texto según las NUEVAS estadísticas de dualidad
        panic_selfcontrol = self.state.get_duality("panic_selfcontrol")
        rejection_understanding = self.state.get_duality("rejection_understanding")
        intelligence = self.state.get_stat("intelligence")
        
        if panic_selfcontrol < -30:
            self.text = "El pánico te consume. Huyes de todo contacto espiritual."
        elif rejection_understanding > 30:
            self.text = "Aprendes a comprender a los espíritus. Encuentras paz en la aceptación."
        elif intelligence > 70:
            self.text = "Tu inteligencia te permite entender el equilibrio entre ambos mundos."
        else:
            self.text = "Mantienes un frágil equilibrio entre el miedo y la curiosidad."

        self.audio.stop_ambience()

        # Botones (código existente)
        btn_w, btn_h = 220, 48
        gap = 18
        y = HEIGHT - 80
        x_center = WIDTH // 2

        def go_title():
            from scenes.title import TitleScene
            self.manager.replace(TitleScene(self.manager))

        def quit_game():
            pygame.quit()
            sys.exit(0)

        self.buttons = [
            Button(
                rect=(x_center - btn_w - gap//2, y, btn_w, btn_h),
                text="Volver al título",
                font=self.font,
                on_click=go_title
            ),
            Button(
                rect=(x_center + gap//2, y, btn_w, btn_h),
                text="Salir",
                font=self.font,
                on_click=quit_game
            ),
        ]

    def handle_event(self, event, game_state):
        if self.input_cooldown > 0:
            return
        for b in self.buttons:
            b.handle_event(event)
        if event.type == pygame.KEYUP:
            from scenes.title import TitleScene
            self.manager.replace(TitleScene(self.manager))

    def update(self, dt, game_state):
        if self.input_cooldown > 0:
            self.input_cooldown -= dt

    def draw(self, screen, game_state):
        surf = screen
        if self.bg:
            surf.blit(self.bg, (0, 0))
        else:
            surf.fill(PALETTE["bg"])

        t1 = self.font_big.render("Fin del demo", True, PALETTE["ink"])
        t1r = t1.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 40))
        surf.blit(t1, t1r)

        y = HEIGHT // 2 + 10
        wrapped, line = [], ""
        for word in self.text.split():
            test = (line + " " + word).strip()
            if len(test) > 60:
                wrapped.append(line)
                line = word
            else:
                line = test
        if line:
            wrapped.append(line)
        for i, s in enumerate(wrapped):
            tx = self.font.render(s, True, PALETTE["ink"])
            surf.blit(tx, (WIDTH // 2 - 280, y + i * 28))

        for b in self.buttons:
            b.draw(surf)