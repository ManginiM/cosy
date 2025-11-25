import pygame
from settings import WIDTH, HEIGHT, PALETTE
from engine.scene_manager import Scene
from engine.narrator import Narrator
from engine.ui import StatsDisplay

class KitchenScene(Scene):
    def __init__(self, manager, game_state, audio):
        super().__init__(manager)
        self.game_state = game_state
        self.audio = audio
        self.font = pygame.font.SysFont("arial", 28)
        self.narrator = Narrator(self.font)
        self.stats_display = StatsDisplay(game_state)

        # Cargar imágenes
        try:
            self.bg = pygame.image.load("assets/images/cocina_bg.png").convert()
            self.bg = pygame.transform.smoothscale(self.bg, (WIDTH, HEIGHT))
        except:
            self.bg = pygame.Surface((WIDTH, HEIGHT))
            self.bg.fill((200, 180, 150))

        # Mesa más compacta y hacia el costado
        try:
            self.mesa_img = pygame.image.load("assets/images/mesa_icon.png").convert_alpha()
            self.mesa_img = pygame.transform.smoothscale(self.mesa_img, (250, 180))  # Más compacta
        except:
            self.mesa_img = None

        try:
            self.nino_fantasma = pygame.image.load("assets/images/fantama_sentado_npc.png").convert_alpha()
            self.nino_fantasma = pygame.transform.smoothscale(self.nino_fantasma, (100, 150))
        except:
            self.nino_fantasma = None

        # Estados de Daniela sentada
        self.daniela_sentada_states = {}
        try:
            self.daniela_sentada_states["pijama"] = pygame.image.load("assets/images/sentada_pijama_pr.png").convert_alpha()
            self.daniela_sentada_states["pijama"] = pygame.transform.smoothscale(self.daniela_sentada_states["pijama"], (100, 200))
        except:
            pass

        try:
            self.daniela_sentada_states["vestida"] = pygame.image.load("assets/images/sentada_pr.png").convert_alpha()
            self.daniela_sentada_states["vestida"] = pygame.transform.smoothscale(self.daniela_sentada_states["vestida"], (100, 200))
        except:
            pass

        # Estados de Daniela de pie (mismos que en house)
        self.daniela_estados_pie = {}
        try:
            img = pygame.image.load("assets/images/parada_pijama_pr.png").convert_alpha()
            self.daniela_estados_pie["parada_pijama"] = pygame.transform.smoothscale(img, (120, 240))
        except:
            pass

        try:
            img = pygame.image.load("assets/images/parada_frente_pr.png").convert_alpha()
            self.daniela_estados_pie["parada_frente"] = pygame.transform.smoothscale(img, (120, 240))
        except:
            pass

        try:
            img = pygame.image.load("assets/images/parada_costado_pr.png").convert_alpha()
            self.daniela_estados_pie["parada_costado"] = pygame.transform.smoothscale(img, (120, 240))
        except:
            pass

        try:
            img = pygame.image.load("assets/images/caminando_pr.png").convert_alpha()
            self.daniela_estados_pie["caminando"] = pygame.transform.smoothscale(img, (120, 240))
        except:
            pass

        try:
            img = pygame.image.load("assets/images/corriendo_pr.png").convert_alpha()
            self.daniela_estados_pie["corriendo"] = pygame.transform.smoothscale(img, (120, 240))
        except:
            pass

        try:
            img = pygame.image.load("assets/images/corriendo_pijama_pr.png").convert_alpha()
            self.daniela_estados_pie["corriendo_pijama"] = pygame.transform.smoothscale(img, (120, 240))
        except:
            pass

        # Posiciones - mesa al costado
        self.mesa_pos = (WIDTH - 400, HEIGHT - 300)  # Mesa a la derecha
        self.mesa_zone = pygame.Rect(WIDTH - 500, HEIGHT - 100, 100, 150)
        self.nino_pos = (WIDTH - 350, HEIGHT - 320)
        
        # Daniela empieza fuera de la mesa
        self.daniela_pos = pygame.Vector2(WIDTH // 2, HEIGHT - 150)
        self.daniela_target = self.daniela_pos.copy()
        self.exit_zone = pygame.Rect(WIDTH - 200, 100, 150, 80)

        # Variables de control
        self.vestida = game_state.flags.get("vestida", False)
        self.daniela_state = "parada_frente" if self.vestida else "parada_pijama"
        self.daniela_speed = 150
        self.is_running = False
        self.facing_right = True
        self.is_moving = False
        self.is_sentada = False  # Empieza de pie

        self.input_cooldown = 0.5
        self.transition_timer = 0
        self.last_click_time = 0

    def on_enter(self):
        self.narrator.say("¿Por qué me mira así? Solo quiero desayunar. No soy nadie.")

    def handle_event(self, event, game_state):
        if self.input_cooldown > 0:
            return

        if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            current_time = pygame.time.get_ticks() / 1000.0
            is_double_click = (current_time - self.last_click_time) < 0.3
            self.last_click_time = current_time

            x, y = event.pos
            
            # Si está sentada, puede levantarse
            if self.is_sentada:
                self.is_sentada = False
                self.daniela_pos = pygame.Vector2(self.mesa_pos[0] - 80, self.mesa_pos[1] - 50)
                self.daniela_target = self.daniela_pos.copy()
                return

            # Si no está sentada, puede moverse o sentarse
            if not self.is_sentada:
                # Si hace clic en la mesa, sentarse
                if self.mesa_zone.collidepoint(x, y):
                    self.is_sentada = True
                    self.narrator.say("Voy a desayunar un poco...")
                    return
                
                # Movimiento normal
                self.daniela_target = pygame.Vector2(x, y)
                self.facing_right = x > self.daniela_pos.x
                self.is_moving = True
                
                if is_double_click:
                    self.is_running = True
                    self.daniela_speed = 300
                    game_state.add_duality("panic_selfcontrol", -3)
                else:
                    self.is_running = False
                    self.daniela_speed = 150
                    game_state.add_duality("panic_selfcontrol", 2)

    def update(self, dt, game_state):
        if self.input_cooldown > 0:
            self.input_cooldown -= dt

        if self.transition_timer > 0:
            self.transition_timer -= dt
            if self.transition_timer <= 0:
                from scenes.title import TitleScene
                self.manager.replace(TitleScene(self.manager))

        # Movimiento solo si no está sentada
        if not self.is_sentada:
            delta = self.daniela_target - self.daniela_pos
            distance = delta.length()
            
            if distance > 5:
                self.daniela_pos += delta.normalize() * min(self.daniela_speed * dt, distance)
                
                # Actualizar animación como en house
                if self.is_running:
                    self.daniela_state = "corriendo" if self.vestida else "corriendo_pijama"
                else:
                    if self.vestida:
                        self.daniela_state = "caminando" if distance > 10 else "parada_frente"
                    else:
                        self.daniela_state = "parada_pijama"
            else:
                # Cuando deja de moverse
                self.is_moving = False
                if self.vestida:
                    self.daniela_state = "parada_costado" if self.facing_right else "parada_frente"
                else:
                    self.daniela_state = "parada_pijama"
            
            # Salir por la puerta
            if self.exit_zone.collidepoint(self.daniela_pos):
                self.narrator.say("Saliendo de la cocina...")
                self.transition_timer = 1.5

        self.narrator.update(dt)

    def draw(self, screen, game_state):
        surf = screen
        surf.blit(self.bg, (0, 0))

        # Dibujar mesa si existe
        if self.mesa_img:
            mesa_rect = self.mesa_img.get_rect(center=self.mesa_pos)
            surf.blit(self.mesa_img, mesa_rect)

        # Dibujar niño fantasma si existe
        if self.nino_fantasma:
            nino_rect = self.nino_fantasma.get_rect(center=self.nino_pos)
            surf.blit(self.nino_fantasma, nino_rect)

        # Dibujar Daniela
        if self.is_sentada:
            # Sentada en la mesa
            current_state = "vestida" if self.vestida else "pijama"
            current_sprite = self.daniela_sentada_states.get(current_state)
            if current_sprite:
                sentada_pos = (self.mesa_pos[0] - 80, self.mesa_pos[1] - 50)
                surf.blit(current_sprite, current_sprite.get_rect(center=sentada_pos))
            else:
                # Placeholder si no hay sprite
                color = (0, 0, 255) if self.vestida else (255, 0, 0)
                pygame.draw.circle(surf, color, (self.mesa_pos[0] - 80, self.mesa_pos[1] - 50), 30)
        else:
            # De pie y moviéndose - misma lógica que house
            current_sprite = self.daniela_estados_pie.get(self.daniela_state)
            if current_sprite:
                if not self.facing_right:
                    current_sprite = pygame.transform.flip(current_sprite, True, False)
                surf.blit(current_sprite, current_sprite.get_rect(center=(int(self.daniela_pos.x), int(self.daniela_pos.y))))
            else:
                # Placeholder si no hay sprites
                color = (0, 0, 255) if self.vestida else (255, 0, 0)
                pygame.draw.circle(surf, color, (int(self.daniela_pos.x), int(self.daniela_pos.y)), 30)

      
        self.narrator.draw(surf)
        self.stats_display.draw(surf)