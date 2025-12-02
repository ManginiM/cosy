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
        self.speaker_font = pygame.font.SysFont("arial", 24, bold=True)
        self.narrator = Narrator(self.font)
        self.stats_display = StatsDisplay(state)

        # Cargar imágenes
        self.bg = pygame.image.load("assets/images/habitacion_bg.jpeg").convert()
        self.bg = pygame.transform.smoothscale(self.bg, (WIDTH, HEIGHT))
        
        # Cama sin deformar
        self.cama_icon = pygame.image.load("assets/images/cama_icon.png").convert_alpha()
        self.cama_icon = pygame.transform.smoothscale(self.cama_icon, (250, 180))

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
            try:
                img = pygame.image.load(f"assets/images/{file}").convert_alpha()
                # Voltear las imágenes que miran al lado incorrecto
                if state in ["parada_costado", "caminando"]:
                    img = pygame.transform.flip(img, True, False)
                self.daniela_states[state] = pygame.transform.smoothscale(img, (120, 240))
            except:
                print(f"Error cargando: {file}")

        # Posiciones
        self.daniela_pos = pygame.Vector2(WIDTH - 640, HEIGHT - 370)
        self.daniela_target = self.daniela_pos.copy()
        self.anciana_zone = pygame.Rect(WIDTH - 220, HEIGHT - 300, 200, 300)
        self.placard_zone = pygame.Rect(580, HEIGHT - 510, 130, 220)
        self.door_zone = pygame.Rect(WIDTH - 250, HEIGHT // 2 - 200, 200, 400)

        # Cargar otros elementos
        try:
            self.anciana = pygame.image.load("assets/images/anciana_fan_npc.png").convert_alpha()
            self.anciana = pygame.transform.smoothscale(self.anciana, (180, 280))
        except:
            self.anciana = None
        
        # Placard más pequeño
        try:
            self.placard_img = pygame.image.load("assets/images/percha_con_uniforme.png").convert_alpha()
            self.placard_img = pygame.transform.smoothscale(self.placard_img, (130, 220))
        except:
            self.placard_img = None
        
        try:
            self.door_img = pygame.image.load("assets/images/puerta_icon.png").convert_alpha()
            self.door_img = pygame.transform.smoothscale(self.door_img, (200, 400))
        except:
            self.door_img = None

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
        
        # Variables para el sistema de diálogos
        self.current_dialogue = None
        self.current_speaker = None
        self.dialogue_timer = 0
        self.dialogue_duration = 4.0
        self.can_skip = False
        self.dialogue_cooldown = 0.5
        
        # Cola de diálogos para evitar superposición
        self.dialogue_queue = []
        
        # Variables para la cama (primer clic)
        self.has_clicked_bed = False

    def on_enter(self):
        self.show_dialogue("Daniela", "Me tengo que levantar...")

    def show_dialogue(self, speaker, text):
        """Muestra un diálogo con el nombre del hablante"""
        # Si ya hay un diálogo en curso, lo ponemos en cola
        if self.current_dialogue:
            self.dialogue_queue.append({"speaker": speaker, "text": text})
            return
            
        self.current_dialogue = text
        self.current_speaker = speaker
        self.dialogue_timer = 0
        self.can_skip = False
        self.dialogue_cooldown = 0.5

    def next_dialogue(self):
        """Pasa al siguiente diálogo en la cola"""
        if self.dialogue_queue:
            next_dialogue = self.dialogue_queue.pop(0)
            self.current_dialogue = next_dialogue["text"]
            self.current_speaker = next_dialogue["speaker"]
            self.dialogue_timer = 0
            self.can_skip = False
            self.dialogue_cooldown = 0.5
        else:
            self.current_dialogue = None
            self.current_speaker = None

    def handle_event(self, event, game_state):
        if self.input_cooldown > 0:
            return

        # Manejar clic en diálogos
        if event.type == pygame.MOUSEBUTTONUP and event.button == 1 and self.dialogue_cooldown <= 0:
            if self.can_skip and self.current_dialogue:
                # Si hay diálogo activo y se puede saltar, pasamos al siguiente
                self.next_dialogue()
                return

        if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            current_time = pygame.time.get_ticks() / 1000.0
            is_double_click = (current_time - self.last_click_time) < 0.3
            self.last_click_time = current_time

            # Si Daniela está en la cama, primer clic para levantarse
            if self.daniela_state == "en_cama" and not self.has_clicked_bed:
                self.daniela_state = "parada_pijama"
                self.has_clicked_bed = True
                
                # Mostrar primer diálogo inmediatamente
                self.current_dialogue = "No está ahí. No ella está ahí."
                self.current_speaker = "Daniela"
                self.dialogue_timer = 0
                self.can_skip = False
                self.dialogue_cooldown = 0.5
                
                # Poner segundo diálogo en cola para después
                self.dialogue_queue.append({
                    "speaker": "Daniela", 
                    "text": "Solo vestite. No la mires."
                })
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

        if self.dialogue_cooldown > 0:
            self.dialogue_cooldown -= dt

        if self.transition_timer > 0:
            self.transition_timer -= dt
            if self.transition_timer <= 0:
                from scenes.kitchen import KitchenScene
                self.manager.replace(KitchenScene(self.manager, game_state, self.audio))

        # Actualizar temporizador de diálogo
        if self.current_dialogue:
            self.dialogue_timer += dt
            if self.dialogue_timer >= 1.0:
                self.can_skip = True
            
            # Ocultar diálogo automáticamente después del tiempo
            if self.dialogue_timer >= self.dialogue_duration:
                self.next_dialogue()

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
                        self.daniela_state = "caminando"
                    else:
                        self.daniela_state = "parada_pijama"
            else:
                # Cuando deja de moverse
                self.is_moving = False
                if self.vestida:
                    self.daniela_state = "parada_costado" if abs(delta.x) > abs(delta.y) else "parada_frente"
                else:
                    self.daniela_state = "parada_pijama"
                
                # Detecciones solo cuando se está moviendo
                if not self.anciana_detected and self.anciana_zone.collidepoint(self.daniela_pos):
                    self.anciana_detected = True
                    game_state.add_duality("panic_selfcontrol", -80)
                    self.daniela_state = "asustada"
                    self.show_dialogue("Daniela", "Miercoles ¡La miré!...")
                
                if self.placard_zone.collidepoint(self.daniela_pos) and not self.vestida:
                    self.vestida = True
                    game_state.set_flag("vestida", True)
                    game_state.add_duality("panic_selfcontrol", 40)
                    self.show_dialogue("Daniela", "Listo, ya me puedo ir")
                    # Cambiar inmediatamente al sprite vestido
                    self.daniela_state = "parada_frente"
                    try:
                        self.placard_img = pygame.image.load("assets/images/percha_sin_uniforme.png").convert_alpha()
                        self.placard_img = pygame.transform.smoothscale(self.placard_img, (130, 220))
                    except:
                        pass

                # CAMBIO IMPORTANTE: Se eliminó la condición "and self.vestida"
                if self.door_zone.collidepoint(self.daniela_pos) and not self.has_exited:
                    self.has_exited = True
                    # Ahora con nombre de hablante
                    self.show_dialogue("Daniela", "Saliendo de la habitación...")
                    self.transition_timer = 1.5

    def draw(self, screen, game_state):
        surf = screen
        surf.blit(self.bg, (0, 0))

        # Dibujar cama vacía
        if self.daniela_state != "en_cama":
            surf.blit(self.cama_icon, self.cama_icon.get_rect(center=(WIDTH - 640, HEIGHT - 370)))

        # Dibujar elementos
        if self.anciana:
            surf.blit(self.anciana, self.anciana_zone.topleft)
        
        if self.placard_img:
            surf.blit(self.placard_img, self.placard_zone.topleft)
        
        if self.door_img:
            surf.blit(self.door_img, self.door_zone.topleft)

        # Dibujar Daniela con volteo
        current_sprite = self.daniela_states.get(self.daniela_state)
        if current_sprite:
            # Solo voltear si no está mirando a la derecha
            if not self.facing_right:
                current_sprite = pygame.transform.flip(current_sprite, True, False)
            surf.blit(current_sprite, current_sprite.get_rect(center=(int(self.daniela_pos.x), int(self.daniela_pos.y))))

        # Dibujar diálogo con nombre del hablante
        self.draw_dialogue_with_speaker(surf)
        
        self.stats_display.draw(surf)
    
    def draw_dialogue_with_speaker(self, screen):
        """Dibuja el diálogo con el nombre del hablante arriba"""
        if not self.current_dialogue:
            return
            
        # Dimensiones del cuadro de diálogo
        box_width = WIDTH - 100
        box_height = 100
        box_x = 50
        box_y = HEIGHT - box_height - 20
        
        # Dibujar cuadro de diálogo
        pygame.draw.rect(screen, (0, 0, 0, 200), (box_x, box_y, box_width, box_height))
        pygame.draw.rect(screen, (255, 255, 255), (box_x, box_y, box_width, box_height), 2)
        
        # Dibujar nombre del hablante arriba del cuadro
        if self.current_speaker:
            # Color según el hablante (solo Daniela en esta escena)
            if self.current_speaker == "Daniela":
                speaker_color = (0, 200, 255)  # Cyan para Daniela
            else:
                speaker_color = (255, 255, 255)  # Blanco por defecto
            
            speaker_text = self.speaker_font.render(self.current_speaker, True, speaker_color)
            screen.blit(speaker_text, (box_x + 10, box_y - 30))
        
        # Dividir texto en líneas
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
        
        # Dibujar líneas de texto (máximo 3 líneas)
        for i, line in enumerate(lines):
            if i < 3:
                text_surf = self.font.render(line, True, (255, 255, 255))
                screen.blit(text_surf, (box_x + 20, box_y + 15 + i * 30))
        
        # Indicador de "clic para continuar" si se puede saltar
        if self.can_skip:
            skip_text = self.font.render("Clic para continuar", True, (200, 200, 200))
            screen.blit(skip_text, (box_x + box_width - skip_text.get_width() - 20, box_y + box_height - 30))