import pygame
from settings import WIDTH, HEIGHT, PALETTE
from engine.scene_manager import Scene
from engine.narrator import Narrator
from engine.ui import StatsDisplay

class HouseScene(Scene):
    def __init__(self, manager, state, audio):
        super().__init__(manager)
        self.state = state
        self.audio = audio
        self.font = pygame.font.SysFont("arial", 28)
        self.narrator = Narrator(self.font)
        self.stats_display = StatsDisplay(state)

        # Cargar imágenes
        self.bg = pygame.image.load("assets/images/habitacion_bg.jpeg").convert()
        self.bg = pygame.transform.smoothscale(self.bg, (WIDTH, HEIGHT))
        
        # Cama sin deformar
        self.cama_icon = pygame.image.load("assets/images/cama_icon.png").convert_alpha()
        self.cama_icon = pygame.transform.smoothscale(self.cama_icon, (250, 180))  # Tamaño ajustado

        # Estados de Daniela - volteamos las imágenes problemáticas al cargarlas
        self.daniela_states = {}
        sprites = {
            "en_cama": "dormida_pr.png",
            "parada_pijama": "parada_pijama_pr.png", 
            "corriendo_pijama": "corriendo_pijama_pr.png",
            "parada_frente": "parada_frente_pr.png",
            "parada_costado": "parada_costado_pr.png",  # Esta la volteamos
            "caminando": "caminando_pr.png",           # Esta la volteamos
            "corriendo": "corriendo_pr.png",
            "asustada": "asustada_pr.png"
        }
        
        for state, file in sprites.items():
            img = pygame.image.load(f"assets/images/{file}").convert_alpha()
            # Voltear las imágenes que miran al lado incorrecto
            if state in ["parada_costado", "caminando"]:
                img = pygame.transform.flip(img, True, False)
            self.daniela_states[state] = pygame.transform.smoothscale(img, (120, 240))

        # Posiciones
        self.daniela_pos = pygame.Vector2(WIDTH - 640, HEIGHT - 370)
        self.daniela_target = self.daniela_pos.copy()
        self.anciana_zone = pygame.Rect(WIDTH - 220, HEIGHT - 300, 200, 300)
        self.placard_zone = pygame.Rect(580, HEIGHT - 510, 130, 220)  # Más pequeño
        self.door_zone = pygame.Rect(WIDTH - 250, HEIGHT // 2 - 200, 200, 400)

        # Cargar otros elementos
        self.anciana = pygame.image.load("assets/images/anciana_fan_npc.png").convert_alpha()
        self.anciana = pygame.transform.smoothscale(self.anciana, (180, 280))
        
        # Placard más pequeño
        self.placard_img = pygame.image.load("assets/images/percha_con_uniforme.png").convert_alpha()
        self.placard_img = pygame.transform.smoothscale(self.placard_img, (130, 220))
        
        self.door_img = pygame.image.load("assets/images/puerta_icon.png").convert_alpha()
        self.door_img = pygame.transform.smoothscale(self.door_img, (200, 400))

        # Variables de control
        self.daniela_state = "en_cama"
        self.daniela_speed = 200
        self.is_running = False
        self.facing_right = True
        self.is_moving = False

        self.input_cooldown = 1.0
        self.vestida = False
        self.anciana_detected = False
        self.has_exited = False
        self.transition_timer = 0
        self.last_click_time = 0

    def on_enter(self):
        self.narrator.say("No está ahí. No está ahí. Solo vestite. No la mires.")

    def handle_event(self, event, game_state):
        if self.input_cooldown > 0:
            return

        if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            current_time = pygame.time.get_ticks() / 1000.0
            is_double_click = (current_time - self.last_click_time) < 0.3
            self.last_click_time = current_time

            if self.daniela_state == "en_cama":
                self.daniela_state = "parada_pijama"
                self.narrator.say("Me tengo que levantar...")
                return

            if self.daniela_state != "en_cama":
                x, y = event.pos
                self.daniela_target = pygame.Vector2(x, y)
                self.facing_right = x > self.daniela_pos.x
                self.is_moving = True
                
                if is_double_click:
                    self.is_running = True
                    self.daniela_speed = 400
                    game_state.add_duality("panic_selfcontrol", -5)
                else:
                    self.is_running = False
                    self.daniela_speed = 200

    def update(self, dt, game_state):
        if self.input_cooldown > 0:
            self.input_cooldown -= dt

        if self.transition_timer > 0:
            self.transition_timer -= dt
            if self.transition_timer <= 0:
                from scenes.kitchen import KitchenScene  # Cambia ForestScene por KitchenScene
                self.manager.replace(KitchenScene(self.manager, game_state, self.audio))

        if self.daniela_state != "en_cama":
            delta = self.daniela_target - self.daniela_pos
            distance = delta.length()
            
            if distance > 5:
                self.daniela_pos += delta.normalize() * min(self.daniela_speed * dt, distance)
                
                # Actualizar animación - CORREGIDO
                if self.is_running:
                    self.daniela_state = "corriendo" if self.vestida else "corriendo_pijama"
                else:
                    if self.vestida:
                        self.daniela_state = "caminando"  # Siempre caminando cuando se mueve
                    else:
                        self.daniela_state = "parada_pijama"
            else:
                # Cuando deja de moverse
                self.is_moving = False
                if self.vestida:
                    # Si está vestida, usar parada_costado si mira de costado, parada_frente si mira de frente
                    self.daniela_state = "parada_costado" if abs(delta.x) > abs(delta.y) else "parada_frente"
                else:
                    self.daniela_state = "parada_pijama"
                
                # Detecciones solo cuando se está moviendo
                if not self.anciana_detected and self.anciana_zone.collidepoint(self.daniela_pos):
                    self.anciana_detected = True
                    game_state.add_duality("panic_selfcontrol", -15)
                    self.daniela_state = "asustada"
                    self.narrator.say("¡La miré! No debía mirarla...")
                
                if self.placard_zone.collidepoint(self.daniela_pos) and not self.vestida:
                    self.vestida = True
                    game_state.set_flag("vestida", True)
                    game_state.add_duality("panic_selfcontrol", 8)
                    self.narrator.say("Ropa puesta. Ahora puedo salir...")
                    # Cambiar inmediatamente al sprite vestido
                    self.daniela_state = "parada_frente"
                    self.placard_img = pygame.image.load("assets/images/percha_sin_uniforme.png").convert_alpha()
                    self.placard_img = pygame.transform.smoothscale(self.placard_img, (130, 220))

                if self.door_zone.collidepoint(self.daniela_pos) and self.vestida and not self.has_exited:
                    self.has_exited = True
                    self.narrator.say("Saliendo de la habitación...")
                    self.transition_timer = 1.5

        self.narrator.update(dt)

    def draw(self, screen, game_state):
        surf = screen
        surf.blit(self.bg, (0, 0))

        # Dibujar cama vacía
        if self.daniela_state != "en_cama":
            surf.blit(self.cama_icon, self.cama_icon.get_rect(center=(WIDTH - 640, HEIGHT - 370)))

        # Dibujar elementos
        surf.blit(self.anciana, self.anciana_zone.topleft)
        surf.blit(self.placard_img, self.placard_zone.topleft)
        surf.blit(self.door_img, self.door_zone.topleft)

        # Dibujar Daniela con volteo
        current_sprite = self.daniela_states.get(self.daniela_state)
        if current_sprite:
            # Solo voltear si no está mirando a la derecha
            if not self.facing_right:
                current_sprite = pygame.transform.flip(current_sprite, True, False)
            surf.blit(current_sprite, current_sprite.get_rect(center=(int(self.daniela_pos.x), int(self.daniela_pos.y))))

    
        self.narrator.draw(surf)
        self.stats_display.draw(surf)