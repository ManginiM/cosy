import pygame
from settings import WIDTH, HEIGHT, PALETTE
from engine.scene_manager import Scene
from engine.narrator import Narrator
from engine.ui import StatsDisplay

class Cuarto2Scene(Scene):
    def __init__(self, manager, game_state, audio):
        super().__init__(manager)
        self.game_state = game_state
        self.audio = audio
        self.font = pygame.font.SysFont("arial", 28)
        self.speaker_font = pygame.font.SysFont("arial", 24, bold=True)
        self.narrator = Narrator(self.font)
        self.stats_display = StatsDisplay(game_state)

        # Cargar imágenes
        self.bg = pygame.image.load("assets/images/habitacion_bg.jpeg").convert()
        self.bg = pygame.transform.smoothscale(self.bg, (WIDTH, HEIGHT))
        
        # Cama sin deformar (solo se usa cuando Daniela NO está durmiendo)
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
        self.daniela_pos = pygame.Vector2(WIDTH // 2, HEIGHT - 200)  # Empieza más cerca del centro
        self.daniela_target = self.daniela_pos.copy()
        self.anciana_zone = pygame.Rect(WIDTH - 220, HEIGHT - 300, 200, 300)
        self.placard_zone = pygame.Rect(580, HEIGHT - 510, 130, 220)
        # Puerta para volver a la cocina (escena 2) - en el lado derecho
        self.door_zone = pygame.Rect(WIDTH - 250, HEIGHT // 2 - 200, 200, 400)
        # Zona de la cama para dormir
        self.bed_zone = pygame.Rect(WIDTH - 700, HEIGHT - 400, 250, 180)

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
        self.daniela_state = "parada_pijama"
        self.daniela_speed = 200
        self.is_running = False
        self.facing_right = True
        self.is_moving = False

        self.input_cooldown = 0.5
        self.vestida = game_state.flags.get("vestida", False)
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
        
        # Variables para el final de dormir
        self.show_final_screen = False
        self.final_text = []
        self.final_timer = 0
        self.transition_target = None
        self.is_sleeping = False  # Nueva variable para controlar si está durmiendo

    def on_enter(self):
        self.show_dialogue("Daniela", "De vuelta en mi habitación...")

    def show_dialogue(self, speaker, text):
        """Muestra un diálogo con el nombre del hablante"""
        self.current_dialogue = text
        self.current_speaker = speaker
        self.dialogue_timer = 0
        self.can_skip = False
        self.dialogue_cooldown = 0.5

    def handle_event(self, event, game_state):
        if self.input_cooldown > 0 or self.show_final_screen or self.is_sleeping:
            return

        # Manejar clic en diálogos
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
            
            # Movimiento normal
            self.daniela_target = pygame.Vector2(x, y)
            self.facing_right = x > self.daniela_pos.x
            self.is_moving = True
            
            if is_double_click:
                self.is_running = True
                self.daniela_speed = 400
                self.game_state.add_duality("panic_selfcontrol", -5)
            else:
                self.is_running = False
                self.daniela_speed = 200

    def update(self, dt, game_state):
        if self.input_cooldown > 0:
            self.input_cooldown -= dt

        if self.dialogue_cooldown > 0:
            self.dialogue_cooldown -= dt

        # Manejar la pantalla de final
        if self.show_final_screen:
            self.final_timer -= dt
            if self.final_timer <= 0:
                from scenes.title import TitleScene
                self.manager.replace(TitleScene(self.manager))
            return

        # Manejar transiciones
        if hasattr(self, 'transition_timer') and self.transition_timer > 0:
            self.transition_timer -= dt
            if self.transition_timer <= 0:
                if self.transition_target == "kitchen":
                    from scenes.kitchen import KitchenScene
                    self.manager.replace(KitchenScene(self.manager, game_state, self.audio))
                elif self.transition_target == "ending_dormir":
                    # Cuando termina la transición de dormir, mostrar la pantalla final
                    self.show_final_screen = True
                    self.final_text = [
                        "FINAL: DORMIR",
                        f"Daniela decidió que el mundo era demasiado para ella.",
                        "Volvió a la cama y se dejó vencer por el cansancio,",
                        "prefiriendo el sueño eterno antes enfrentar la realidad."
                    ]
                    self.final_timer = 5.0
            return

        # Actualizar temporizador de diálogo
        if self.current_dialogue:
            self.dialogue_timer += dt
            if self.dialogue_timer >= 1.0:
                self.can_skip = True
            
            # Ocultar diálogo automáticamente después del tiempo
            if self.dialogue_timer >= self.dialogue_duration:
                self.current_dialogue = None
                self.current_speaker = None

        # Si está durmiendo, no procesar movimiento
        if self.is_sleeping:
            return

        # Movimiento de Daniela
        delta = self.daniela_target - self.daniela_pos
        distance = delta.length()
        
        if distance > 5:
            self.daniela_pos += delta.normalize() * min(self.daniela_speed * dt, distance)
            
            # Actualizar animación
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
            # Detectar anciana
            if not self.anciana_detected and self.anciana_zone.collidepoint(self.daniela_pos):
                self.anciana_detected = True
                self.game_state.add_duality("panic_selfcontrol", -80)
                self.daniela_state = "asustada"
                self.show_dialogue("Daniela", "¡Ay! La anciana todavía está ahí...")
            
            # Detectar placard para vestirse
            if self.placard_zone.collidepoint(self.daniela_pos) and not self.vestida:
                self.vestida = True
                self.game_state.set_flag("vestida", True)
                self.game_state.add_duality("panic_selfcontrol", 40)
                self.show_dialogue("Daniela", "Me vestí. Ahora puedo volver a la cocina.")
                # Cambiar inmediatamente al sprite vestido
                self.daniela_state = "parada_frente"
                try:
                    self.placard_img = pygame.image.load("assets/images/percha_sin_uniforme.png").convert_alpha()
                    self.placard_img = pygame.transform.smoothscale(self.placard_img, (130, 220))
                except:
                    pass

            # Detectar puerta para volver a la cocina (solo si está vestida)
            if self.door_zone.collidepoint(self.daniela_pos) and self.vestida and not self.has_exited:
                self.has_exited = True
                self.show_dialogue("Daniela", "Volviendo a la cocina...")
                self.transition_target = "kitchen"
                self.transition_timer = 1.5
                
            # Detectar cama para dormir (final)
            if self.bed_zone.collidepoint(self.daniela_pos) and not self.has_exited and not self.is_sleeping:
                # Cambiar estado a dormida
                self.daniela_state = "en_cama"
                self.is_sleeping = True
                self.show_dialogue("Daniela", "No puedo más... voy a volver a dormir...")
                # Esperar a que termine el diálogo antes de mostrar el final
                self.transition_target = "ending_dormir"
                self.transition_timer = 3.0  # 3 segundos para ver la animación de dormida

    def draw(self, screen, game_state):
        surf = screen
        
        # Dibujar pantalla de final si está activa
        if self.show_final_screen:
            self.draw_final_screen(surf)
            return
        
        surf.blit(self.bg, (0, 0))

        # SI NO está durmiendo, dibujar cama vacía y otros elementos
        if not self.is_sleeping:
            # Dibujar cama vacía
            surf.blit(self.cama_icon, self.cama_icon.get_rect(center=(WIDTH - 640, HEIGHT - 370)))
            
            # Dibujar otros elementos
            if self.anciana:
                surf.blit(self.anciana, self.anciana_zone.topleft)
            
            if self.placard_img:
                surf.blit(self.placard_img, self.placard_zone.topleft)
            
            if self.door_img:
                surf.blit(self.door_img, self.door_zone.topleft)

            # Dibujar Daniela con volteo (solo si no está durmiendo)
            current_sprite = self.daniela_states.get(self.daniela_state)
            if current_sprite:
                # Solo voltear si no está mirando a la derecha
                if not self.facing_right:
                    current_sprite = pygame.transform.flip(current_sprite, True, False)
                surf.blit(current_sprite, current_sprite.get_rect(center=(int(self.daniela_pos.x), int(self.daniela_pos.y))))
        
        # SI está durmiendo, solo dibujar a Daniela dormida
        else:
            # Obtener sprite de Daniela dormida
            sleep_sprite = self.daniela_states.get("en_cama")
            if sleep_sprite:
                # Posición en la cama (misma posición donde estaba la cama vacía)
                sleep_pos = (WIDTH - 640, HEIGHT - 370)
                surf.blit(sleep_sprite, sleep_sprite.get_rect(center=sleep_pos))
            
            # NO dibujamos cama vacía, anciana, placard ni puerta cuando está durmiendo

        # Dibujar diálogo con nombre del hablante (si hay)
        self.draw_dialogue_with_speaker(surf)
        
        # Dibujar estadísticas
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

    def draw_final_screen(self, screen):
        """Dibuja la pantalla de final"""
        # Fondo semitransparente
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 220))
        screen.blit(overlay, (0, 0))
        
        # Fuente para el título
        title_font = pygame.font.SysFont("arial", 48, bold=True)
        text_font = pygame.font.SysFont("arial", 32)
        small_font = pygame.font.SysFont("arial", 24)
        
        # Título
        title = title_font.render(self.final_text[0], True, (255, 255, 255))
        screen.blit(title, (WIDTH // 2 - title.get_width() // 2, HEIGHT // 4))
        
        # Líneas de texto
        y_offset = HEIGHT // 3
        for i, line in enumerate(self.final_text[1:]):
            text = text_font.render(line, True, (255, 255, 255))
            screen.blit(text, (WIDTH // 2 - text.get_width() // 2, y_offset + i * 40))
        
        # Contador para volver al menú
        countdown = small_font.render(f"Volviendo al menú principal en {int(self.final_timer)}...", True, (200, 200, 200))
        screen.blit(countdown, (WIDTH // 2 - countdown.get_width() // 2, HEIGHT * 3 // 4))