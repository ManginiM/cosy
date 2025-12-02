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
        self.speaker_font = pygame.font.SysFont("arial", 24, bold=True)
        self.narrator = Narrator(self.font)
        self.stats_display = StatsDisplay(game_state)

        # Cargar imágenes
        try:
            self.bg = pygame.image.load("assets/images/cocina_bg.png").convert()
            scaled_width = int(WIDTH * 0.9)
            scaled_height = int(HEIGHT * 0.9)
            self.bg = pygame.transform.smoothscale(self.bg, (scaled_width, scaled_height))
            self.bg_x = (WIDTH - scaled_width) // 2
            self.bg_y = (HEIGHT - scaled_height) // 2
        except:
            self.bg = pygame.Surface((WIDTH, HEIGHT))
            self.bg.fill((200, 180, 150))
            self.bg_x = 0
            self.bg_y = 0

        # Mesa
        try:
            self.mesa_img = pygame.image.load("assets/images/mesa_icon.png").convert_alpha()
            self.mesa_img = pygame.transform.smoothscale(self.mesa_img, (320, 240))
        except:
            self.mesa_img = None

        # Niño fantasma
        try:
            self.nino_fantasma = pygame.image.load("assets/images/fantama_sentado_npc.png").convert_alpha()
            self.nino_fantasma = pygame.transform.smoothscale(self.nino_fantasma, (140, 210))
        except:
            self.nino_fantasma = None

        # Estados de Daniela
        self.daniela_sentada_states = {}
        try:
            img = pygame.image.load("assets/images/sentada_pijama_pr.png").convert_alpha()
            img = pygame.transform.flip(img, True, False)
            self.daniela_sentada_states["pijama"] = pygame.transform.smoothscale(img, (120, 240))
        except:
            pass

        try:
            img = pygame.image.load("assets/images/sentada_pr.png").convert_alpha()
            img = pygame.transform.flip(img, True, False)
            self.daniela_sentada_states["vestida"] = pygame.transform.smoothscale(img, (120, 240))
        except:
            pass

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
            img = pygame.transform.flip(img, True, False)
            self.daniela_estados_pie["parada_costado"] = pygame.transform.smoothscale(img, (120, 240))
        except:
            pass

        try:
            img = pygame.image.load("assets/images/caminando_pr.png").convert_alpha()
            img = pygame.transform.flip(img, True, False)
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

        try:
            self.daniela_asustada = pygame.image.load("assets/images/asustada_pr.png").convert_alpha()
            self.daniela_asustada = pygame.transform.smoothscale(self.daniela_asustada, (120, 240))
        except:
            self.daniela_asustada = None

        # Comida
        self.comida_zone = pygame.Rect(200, HEIGHT - 350, 100, 100)
        self.comida_img = None
        try:
            self.comida_img = pygame.image.load("assets/images/desayuno_icon.png").convert_alpha()
            self.comida_img = pygame.transform.smoothscale(self.comida_img, (80, 80))
        except:
            pass
        
        # Posiciones
        self.daniela_pos = pygame.Vector2(WIDTH // 2, HEIGHT - 150)
        self.daniela_target = self.daniela_pos.copy()
        self.mesa_pos = (WIDTH - 400, HEIGHT - 180)
        self.mesa_zone = pygame.Rect(WIDTH - 500, HEIGHT - 230, 300, 150)
        self.nino_pos = (WIDTH - 350, HEIGHT - 200)
        
        # Zona izquierda para volver a la habitación (visible)
        self.left_door_zone = pygame.Rect(0, 0, 150, HEIGHT)
        
        # Zona derecha para ir a la escuela (INVISIBLE)
        self.school_door_zone = pygame.Rect(WIDTH - 50, HEIGHT // 2 - 150, 50, 300)

        # Variables de control
        self.vestida = game_state.flags.get("vestida", False)
        self.daniela_state = "parada_frente" if self.vestida else "parada_pijama"
        self.daniela_speed = 150
        self.is_running = False
        self.facing_right = True
        self.is_moving = False
        self.is_sentada = False
        self.has_comida = False
        self.has_desayunado = False
        self.comida_timer = 0
        self.nino_sospechoso = False
        self.en_panico = False

        self.input_cooldown = 0.5
        self.transition_timer = 0
        self.last_click_time = 0
        
        self.transition_target = None
        self.comida_proximity_zone = pygame.Rect(150, HEIGHT - 400, 200, 200)
        
        # Secuencia de pánico
        self.panic_sequence_step = 0
        self.panic_sequence_timer = 0
        
        # Diálogos
        self.current_dialogue = None
        self.current_speaker = None
        self.dialogue_timer = 0
        self.dialogue_duration = 4.0
        self.can_skip = False
        self.dialogue_cooldown = 0.5

    def on_enter(self):
        self.show_dialogue("Daniela", "¿Por qué me mira así? Solo quiero desayunar. No soy nadie.")

    def show_dialogue(self, speaker, text):
        self.current_dialogue = text
        self.current_speaker = speaker
        self.dialogue_timer = 0
        self.can_skip = False
        self.dialogue_cooldown = 0.5

    def handle_event(self, event, game_state):
        if self.input_cooldown > 0 or self.en_panico or self.panic_sequence_step > 0:
            return

        if event.type == pygame.MOUSEBUTTONUP and event.button == 1 and self.dialogue_cooldown <= 0:
            if self.can_skip and self.current_dialogue:
                self.current_dialogue = None
                self.current_speaker = None
                self.dialogue_cooldown = 0.5
                return

        if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            current_time = pygame.time.get_ticks() / 1000.0
            is_double_click = (current_time - self.last_click_time) < 0.3
            self.last_click_time = current_time

            x, y = event.pos
            
            if self.is_sentada:
                self.is_sentada = False
                self.daniela_pos = pygame.Vector2(self.mesa_pos[0] - 80, self.mesa_pos[1] - 50)
                self.daniela_target = self.daniela_pos.copy()
                return

            if not self.is_sentada:
                if self.comida_zone.collidepoint(x, y) and not self.has_comida:
                    if self.comida_proximity_zone.collidepoint(self.daniela_pos):
                        self.has_comida = True
                        self.show_dialogue("Daniela", "Tengo mi comida. Ahora puedo sentarme a desayunar.")
                    return
                
                if self.mesa_zone.collidepoint(x, y):
                    if self.has_comida:
                        self.is_sentada = True
                        self.comida_timer = 5.0
                        self.show_dialogue("Daniela", "Voy a desayunar un poco...")
                    else:
                        self.is_sentada = True
                        self.comida_timer = 1.0
                    return
                
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

        if self.dialogue_cooldown > 0:
            self.dialogue_cooldown -= dt

        if self.transition_timer > 0:
            self.transition_timer -= dt
            if self.transition_timer <= 0:
                if self.transition_target == "cuarto2":
                    from scenes.cuarto2 import Cuarto2Scene
                    self.manager.replace(Cuarto2Scene(self.manager, game_state, self.audio))
                elif self.transition_target == "escuela":
                    from scenes.escuela import EscuelaScene
                    self.manager.replace(EscuelaScene(self.manager, game_state, self.audio))
                elif self.en_panico:
                    from scenes.tarot import TarotScene
                    self.manager.replace(TarotScene(self.manager, game_state, self.audio))
                else:
                    from scenes.title import TitleScene
                    self.manager.replace(TitleScene(self.manager))
                return

        if self.current_dialogue:
            self.dialogue_timer += dt
            if self.dialogue_timer >= 1.0:
                self.can_skip = True
            
            if self.dialogue_timer >= self.dialogue_duration:
                self.current_dialogue = None
                self.current_speaker = None

        if self.panic_sequence_step > 0:
            self.panic_sequence_timer -= dt
            if self.panic_sequence_timer <= 0:
                self.advance_panic_sequence(game_state)
            return

        # Si toca la zona derecha INVISIBLE para ir a la escuela
        if self.school_door_zone.collidepoint(self.daniela_pos) and not self.en_panico and self.transition_timer <= 0:
            if self.vestida and self.has_desayunado:
                self.show_dialogue("Daniela", "Es hora de ir a la escuela...")
                self.transition_target = "escuela"
                self.transition_timer = 1.5
            elif not self.vestida:
                self.show_dialogue("Daniela", "No puedo ir a la escuela en pijama...")
                game_state.add_duality("rejection_understanding", -5)  # Aumenta rechazo
            elif not self.has_desayunado:
                self.show_dialogue("Daniela", "Debería desayunar antes de ir a la escuela...")
                game_state.add_duality("panic_selfcontrol", -5)  # Aumenta pánico
                
        # Si toca la zona izquierda
        if self.left_door_zone.collidepoint(self.daniela_pos) and not self.en_panico and self.transition_timer <= 0:
            self.show_dialogue("Daniela", "Volviendo a la habitación...")
            self.transition_target = "cuarto2"
            self.transition_timer = 1.5

        if self.en_panico and self.school_door_zone.collidepoint(self.daniela_pos):
            if self.transition_timer <= 0:
                self.show_dialogue("Daniela", "¡Logré escapar! Saliendo de la cocina...")
                self.transition_timer = 1.5

        if self.is_sentada and not self.has_comida and self.comida_timer > 0:
            self.comida_timer -= dt
            if self.comida_timer <= 0:
                self.panic_sequence_step = 1
                self.panic_sequence_timer = 3.0
                self.show_dialogue("Daniela", "El espíritu me está mirando muy raro...")

        if self.is_sentada and self.has_comida and self.comida_timer > 0:
            self.comida_timer -= dt
            if self.comida_timer <= 0:
                self.is_sentada = False
                self.has_desayunado = True
                self.show_dialogue("Daniela", "Terminé de desayunar. Ahora puedo ir a la escuela.")
                game_state.add_duality("panic_selfcontrol", 10)  # Aumenta autocontrol
                self.daniela_pos = pygame.Vector2(self.mesa_pos[0] - 80, self.mesa_pos[1] - 50)
                self.daniela_target = self.daniela_pos.copy()

        if not self.is_sentada and self.panic_sequence_step == 0:
            delta = self.daniela_target - self.daniela_pos
            distance = delta.length()
            
            if distance > 5:
                self.daniela_pos += delta.normalize() * min(self.daniela_speed * dt, distance)
                
                if self.is_running:
                    self.daniela_state = "corriendo" if self.vestida else "corriendo_pijama"
                else:
                    if self.vestida:
                        self.daniela_state = "caminando" if distance > 10 else "parada_frente"
                    else:
                        self.daniela_state = "parada_pijama"
            else:
                self.is_moving = False
                if self.vestida:
                    self.daniela_state = "parada_costado" if self.facing_right else "parada_frente"
                else:
                    self.daniela_state = "parada_pijama"

    def advance_panic_sequence(self, game_state):
        self.panic_sequence_step += 1
        
        if self.panic_sequence_step == 2:
            self.is_sentada = False
            self.panic_sequence_timer = 3.0
            self.show_dialogue("Daniela", "¿Estará sospechando de mí?")
            if self.daniela_asustada:
                self.daniela_state = "asustada"
                
        elif self.panic_sequence_step == 3:
            self.panic_sequence_timer = 3.0
            self.show_dialogue("Daniela", "¿Me habrá descubierto?")
            
        elif self.panic_sequence_step == 4:
            self.panic_sequence_timer = 2.0
            self.show_dialogue("Daniela", "¡Tengo que salir de aquí!")
            
        elif self.panic_sequence_step == 5:
            self.en_panico = True
            self.nino_sospechoso = True
            game_state.add_duality("panic_selfcontrol", -20)
            self.daniela_target = pygame.Vector2(self.school_door_zone.centerx, self.school_door_zone.centery)
            self.is_running = True
            self.daniela_speed = 400
            self.panic_sequence_step = 0

    def draw(self, screen, game_state):
        surf = screen
        
        surf.fill((0, 0, 0))
        surf.blit(self.bg, (self.bg_x, self.bg_y))

        if not self.has_comida and self.comida_img:
            comida_rect = self.comida_img.get_rect(center=(self.comida_zone.x + 50, self.comida_zone.y + 50))
            surf.blit(self.comida_img, comida_rect)

        if self.mesa_img:
            mesa_rect = self.mesa_img.get_rect(center=self.mesa_pos)
            surf.blit(self.mesa_img, mesa_rect)

        if self.nino_fantasma:
            nino_rect = self.nino_fantasma.get_rect(center=self.nino_pos)
            surf.blit(self.nino_fantasma, nino_rect)

        # Zona izquierda (visible - amarilla)
        transition_surface = pygame.Surface((self.left_door_zone.width, self.left_door_zone.height), pygame.SRCALPHA)
        transition_surface.fill((255, 255, 0, 100))
        surf.blit(transition_surface, self.left_door_zone.topleft)
        transition_text = self.font.render("← Habitación", True, (255, 255, 255))
        surf.blit(transition_text, (10, HEIGHT // 2 - 50))

        # Zona derecha para la escuela (INVISIBLE - no se dibuja)
        # Solo se mostrará texto indicativo si Daniela está cerca
        if self.school_door_zone.collidepoint(self.daniela_pos):
            school_text = self.font.render("Escuela →", True, (255, 255, 255))
            surf.blit(school_text, (WIDTH - school_text.get_width() - 20, HEIGHT // 2 - 50))

        # Indicador de estado
        status_text = ""
        if not self.vestida:
            status_text = "Necesito vestirme"
        elif not self.has_desayunado:
            status_text = "Necesito desayunar"
        else:
            status_text = "Lista para la escuela"
        
        status = self.font.render(status_text, True, (255, 255, 255))
        surf.blit(status, (WIDTH - status.get_width() - 20, 30))

        if self.is_sentada:
            current_state = "vestida" if self.vestida else "pijama"
            current_sprite = self.daniela_sentada_states.get(current_state)
            if current_sprite:
                sentada_pos = (self.mesa_pos[0] - 80, self.mesa_pos[1] - 50)
                surf.blit(current_sprite, current_sprite.get_rect(center=sentada_pos))
            else:
                color = (0, 0, 255) if self.vestida else (255, 0, 0)
                pygame.draw.circle(surf, color, (self.mesa_pos[0] - 80, self.mesa_pos[1] - 50), 30)
        else:
            if self.daniela_state == "asustada" and self.daniela_asustada:
                current_sprite = self.daniela_asustada
                if not self.facing_right:
                    current_sprite = pygame.transform.flip(current_sprite, True, False)
                surf.blit(current_sprite, current_sprite.get_rect(center=(int(self.daniela_pos.x), int(self.daniela_pos.y))))
            else:
                current_sprite = self.daniela_estados_pie.get(self.daniela_state)
                if current_sprite:
                    if not self.facing_right:
                        current_sprite = pygame.transform.flip(current_sprite, True, False)
                    surf.blit(current_sprite, current_sprite.get_rect(center=(int(self.daniela_pos.x), int(self.daniela_pos.y))))
                else:
                    color = (0, 0, 255) if self.vestida else (255, 0, 0)
                    pygame.draw.circle(surf, color, (int(self.daniela_pos.x), int(self.daniela_pos.y)), 30)

        self.draw_dialogue_with_speaker(surf)
        self.stats_display.draw(surf)
    
    def draw_dialogue_with_speaker(self, screen):
        if not self.current_dialogue:
            return
            
        box_width = WIDTH - 100
        box_height = 100
        box_x = 50
        box_y = HEIGHT - box_height - 20
        
        pygame.draw.rect(screen, (0, 0, 0, 200), (box_x, box_y, box_width, box_height))
        pygame.draw.rect(screen, (255, 255, 255), (box_x, box_y, box_width, box_height), 2)
        
        if self.current_speaker:
            if self.current_speaker == "Daniela":
                speaker_color = (0, 200, 255)
            else:
                speaker_color = (255, 255, 255)
            
            speaker_text = self.speaker_font.render(self.current_speaker, True, speaker_color)
            screen.blit(speaker_text, (box_x + 10, box_y - 30))
        
        words = self.current_dialogue.split(' ')
        lines = []
        current_line = []
        
        for word in words:
            test_line = ' '.join(current_line + [word])
            test_width = self.font.size(test_line)[0]
            
            if test_width <= box_width - 40:
                current_line.append(word)
            else:
                lines.append(' '.join(current_line))
                current_line = [word]
        
        if current_line:
            lines.append(' '.join(current_line))
        
        for i, line in enumerate(lines):
            if i < 3:
                text_surf = self.font.render(line, True, (255, 255, 255))
                screen.blit(text_surf, (box_x + 20, box_y + 15 + i * 30))
        
        if self.can_skip:
            skip_text = self.font.render("Clic para continuar", True, (200, 200, 200))
            screen.blit(skip_text, (box_x + box_width - skip_text.get_width() - 20, box_y + box_height - 30))