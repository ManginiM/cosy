import pygame
import math
from settings import WIDTH, HEIGHT, PALETTE
from engine.scene_manager import Scene
from engine.narrator import Narrator
from engine.ui import StatsDisplay

class EscuelaScene(Scene):
    def __init__(self, manager, game_state, audio):
        super().__init__(manager)
        self.game_state = game_state
        self.audio = audio
        self.font = pygame.font.SysFont("arial", 28)
        self.speaker_font = pygame.font.SysFont("arial", 24, bold=True)
        self.narrator = Narrator(self.font)
        self.stats_display = StatsDisplay(game_state)

        # Fondo
        try:
            self.bg = pygame.image.load("assets/images/aula2_bg.jpeg").convert()
            self.bg = pygame.transform.smoothscale(self.bg, (WIDTH, HEIGHT))
        except:
            self.bg = pygame.Surface((WIDTH, HEIGHT))
            self.bg.fill((150, 180, 200))

        # Silla interactiva MUCHO MÁS GRANDE
        try:
            self.silla_img = pygame.image.load("assets/images/silla_icon.png").convert_alpha()
            self.silla_img = pygame.transform.smoothscale(self.silla_img, (180, 240))  # AÚN MÁS GRANDE: 180x240
        except:
            self.silla_img = None

        # Daniela sentada en la silla
        try:
            self.daniela_sentada_img = pygame.image.load("assets/images/silla_escola_pr.png").convert_alpha()
            self.daniela_sentada_img = pygame.transform.smoothscale(self.daniela_sentada_img, (160, 300))  # Más grande
        except:
            self.daniela_sentada_img = None

        # Espíritu aterrador
        try:
            self.espiritu_img = pygame.image.load("assets/images/espiritu_escolar_npc.png").convert_alpha()
            self.espiritu_img = pygame.transform.smoothscale(self.espiritu_img, (200, 320))  # Más grande
        except:
            self.espiritu_img = None

        # Estados de Daniela de pie (para movimiento)
        self.daniela_states = {}
        sprites = {
            "parada_frente": "parada_frente_pr.png",
            "parada_costado": "parada_costado_pr.png",
            "caminando": "caminando_pr.png",
            "corriendo": "corriendo_pr.png",
            "asustada": "asustada_pr.png"
        }
        
        for state, file in sprites.items():
            try:
                img = pygame.image.load(f"assets/images/{file}").convert_alpha()
                if state in ["parada_costado", "caminando"]:
                    img = pygame.transform.flip(img, True, False)  # Voltear para que mire a la izquierda
                self.daniela_states[state] = pygame.transform.smoothscale(img, (140, 280))  # Más grande
            except:
                print(f"Error cargando: {file}")

        # Posiciones - SILLA MÁS ARRIBA
        self.silla_pos = (WIDTH // 2, HEIGHT - 250)  # Silla más arriba (HEIGHT - 250)
        # Zona de la silla MÁS GRANDE para facilitar clic
        self.silla_zone = pygame.Rect(self.silla_pos[0] - 90, self.silla_pos[1] - 120, 180, 240)
        
        # Variables para movimiento del espíritu
        self.espiritu_base_pos = (WIDTH // 2, HEIGHT - 280)  # Posición base cerca de Daniela
        self.espiritu_pos = self.espiritu_base_pos
        self.espiritu_offset = 0  # Para movimiento sinusoidal
        self.espiritu_speed = 2.0  # Velocidad de movimiento
        self.espiritu_radius = 150  # Radio del movimiento circular
        
        # Daniela empieza en el centro de la pantalla
        self.daniela_pos = pygame.Vector2(WIDTH // 2, HEIGHT - 150)
        self.daniela_target = self.daniela_pos.copy()
        
        # Zona de salida (esquina derecha)
        self.exit_zone = pygame.Rect(WIDTH - 100, HEIGHT // 2 - 50, 80, 100)
        
        # Variables de control
        self.sequence_step = 0  # 0: pantalla negra, 1: puede moverse, 2: sentado, 3: clase inicia, 4: espíritu aparece, 5: diálogos, 6: huir
        self.sequence_timer = 0
        self.show_black_screen = True
        self.black_screen_text = "Daniela se dirigió a la escuela"
        self.black_screen_timer = 2.0
        
        # Daniela
        self.daniela_state = "parada_frente"
        self.daniela_speed = 180
        self.facing_right = False  # Mira hacia la izquierda
        self.is_moving = False
        self.has_sentado = False
        self.can_move = True
        
        # Espíritu
        self.espiritu_visible = False
        self.espiritu_dialog_index = 0
        
        # Diálogos del espíritu (insistencia por atención)
        self.espiritu_dialogues = [
            "Te recuerdo a mí antes...",
            "Tienes la piel muy linda y pálida...",
            "Te ves asustada... ¿acaso me escuchas?",
            "Es posible, dios mío...",
            "Hola hola, sé que me escuchas...",
            "No tengas miedo, solo quiero hablar...",
            "Eres especial, como yo lo fui...",
            "¿Por qué todos nos abandonan?",
            "Quédate conmigo, no quiero estar solo...",
            "Puedo ver que tienes el mismo don que yo..."
        ]
        
        # Transición
        self.transition_timer = 0
        self.is_huyendo = False
        
        # Diálogos
        self.current_dialogue = None
        self.current_speaker = None
        self.dialogue_timer = 0
        self.dialogue_duration = 4.0
        self.can_skip = False
        self.dialogue_cooldown = 0.5
        
        # Control de clic
        self.input_cooldown = 0.5
        self.last_click_time = 0

    def on_enter(self):
        self.show_black_screen = True
        self.black_screen_timer = 2.0

    def show_dialogue(self, speaker, text):
        self.current_dialogue = text
        self.current_speaker = speaker
        self.dialogue_timer = 0
        self.can_skip = False
        self.dialogue_cooldown = 0.5

    def handle_event(self, event, game_state):
        if self.input_cooldown > 0 or self.show_black_screen or self.transition_timer > 0:
            return

        # Manejar clic en diálogos
        if event.type == pygame.MOUSEBUTTONUP and event.button == 1 and self.dialogue_cooldown <= 0:
            if self.can_skip and self.current_dialogue:
                self.current_dialogue = None
                self.current_speaker = None
                self.dialogue_cooldown = 0.5
                
                # Avanzar secuencia después de diálogo
                if self.sequence_step == 3:  # Después de "Inició la clase"
                    self.sequence_step = 4
                    self.sequence_timer = 1.5
                elif self.sequence_step == 5:  # Después de diálogo del espíritu
                    self.espiritu_dialog_index += 1
                    if self.espiritu_dialog_index < len(self.espiritu_dialogues):
                        self.sequence_step = 5
                        self.sequence_timer = 2.0
                    else:
                        self.sequence_step = 6  # Daniela huye
                        self.sequence_timer = 1.0
                
                return

        # MOVIMIENTO NORMAL - clic para moverse (solo si puede moverse)
        if event.type == pygame.MOUSEBUTTONUP and event.button == 1 and self.can_move and not self.has_sentado:
            current_time = pygame.time.get_ticks() / 1000.0
            is_double_click = (current_time - self.last_click_time) < 0.3
            self.last_click_time = current_time

            x, y = event.pos
            
            # Si hace clic en la silla y está cerca, sentarse
            if self.silla_zone.collidepoint(x, y):
                silla_center = pygame.Vector2(self.silla_pos)
                distancia = silla_center.distance_to(self.daniela_pos)
                if distancia < 150:  # Mayor tolerancia para silla más grande
                    self.has_sentado = True
                    self.can_move = False
                    self.daniela_state = "parada_frente"
                    self.sequence_step = 2  # Sentado
                    self.show_dialogue("Daniela", "Me senté en mi lugar...")
                    self.sequence_timer = 2.0
                    return
            
            # Movimiento normal a cualquier parte
            self.daniela_target = pygame.Vector2(x, y)
            self.facing_right = x > self.daniela_pos.x
            self.is_moving = True
            
            if is_double_click:
                self.daniela_speed = 300
                self.game_state.add_duality("panic_selfcontrol", -3)
            else:
                self.daniela_speed = 180

    def update(self, dt, game_state):
        if self.input_cooldown > 0:
            self.input_cooldown -= dt

        if self.dialogue_cooldown > 0:
            self.dialogue_cooldown -= dt

        # Pantalla negra inicial
        if self.show_black_screen:
            self.black_screen_timer -= dt
            if self.black_screen_timer <= 0:
                self.show_black_screen = False
                self.sequence_step = 1  # Puede moverse
                self.can_move = True
                self.show_dialogue("Daniela", "Aquí está mi escuela...")
            return

        # Manejar secuencia automática
        if self.sequence_timer > 0:
            self.sequence_timer -= dt
            if self.sequence_timer <= 0:
                self.advance_sequence(game_state)
                return

        # Actualizar diálogo
        if self.current_dialogue:
            self.dialogue_timer += dt
            if self.dialogue_timer >= 1.0:
                self.can_skip = True
            
            # Ocultar diálogo automáticamente después del tiempo
            if self.dialogue_timer >= self.dialogue_duration and self.can_skip:
                self.current_dialogue = None
                self.current_speaker = None
                # Si hay un diálogo activo y termina, avanzar secuencia automáticamente
                if self.sequence_step == 3:  # Después de "Inició la clase"
                    self.sequence_step = 4
                    self.sequence_timer = 1.5
                elif self.sequence_step == 5:  # Después de diálogo del espíritu
                    self.espiritu_dialog_index += 1
                    if self.espiritu_dialog_index < len(self.espiritu_dialogues):
                        self.sequence_step = 5
                        self.sequence_timer = 2.0
                    else:
                        self.sequence_step = 6  # Daniela huye
                        self.sequence_timer = 1.0

        # Transición a tarot.py (con manejo de error)
        if self.transition_timer > 0:
            self.transition_timer -= dt
            if self.transition_timer <= 0:
                try:
                    from scenes.tarot import TarotScene
                    self.manager.replace(TarotScene(self.manager, game_state, self.audio))
                except Exception as e:
                    print(f"Error al cargar tarot.py: {e}")
                    # Si hay error, volver al menú principal
                    from scenes.title import TitleScene
                    self.manager.replace(TitleScene(self.manager))
            return

        # MOVIMIENTO de Daniela (si puede moverse y no está sentada)
        if self.can_move and not self.has_sentado and self.is_moving:
            delta = self.daniela_target - self.daniela_pos
            distance = delta.length()
            
            if distance > 5:
                self.daniela_pos += delta.normalize() * min(self.daniela_speed * dt, distance)
                self.daniela_state = "caminando"
            else:
                self.is_moving = False
                self.daniela_state = "parada_costado" if self.facing_right else "parada_frente"

        # MOVIMIENTO DEL ESPÍRITU (si es visible) - se mueve alrededor de Daniela
        if self.espiritu_visible:
            self.espiritu_offset += dt * self.espiritu_speed
            
            # Movimiento circular alrededor de Daniela sentada
            angle = self.espiritu_offset
            x_offset = math.cos(angle) * self.espiritu_radius
            y_offset = math.sin(angle) * (self.espiritu_radius * 0.7)  # Elipse más ancha que alta
            
            # Posición base alrededor de Daniela (sentada en la silla)
            base_x, base_y = self.silla_pos
            self.espiritu_pos = (base_x + x_offset, base_y + y_offset - 50)

        # Si está huyendo (después de la secuencia del espíritu)
        if self.is_huyendo:
            self.can_move = False
            self.daniela_state = "corriendo"
            self.daniela_target = pygame.Vector2(WIDTH + 150, HEIGHT - 150)
            delta = self.daniela_target - self.daniela_pos
            distance = delta.length()
            
            if distance > 5:
                self.daniela_pos += delta.normalize() * min(350 * dt, distance)
            else:
                # Activar transición
                self.transition_timer = 1.5

    def advance_sequence(self, game_state):
        if self.sequence_step == 2:  # Después de sentarse
            self.sequence_step = 3
            self.show_dialogue("Narrador", "Inició la clase...")
            
        elif self.sequence_step == 4:  # Espíritu aparece (después de clase)
            self.espiritu_visible = True
            game_state.add_duality("panic_selfcontrol", -15)  # Aumenta pánico
            game_state.add_duality("rejection_understanding", -10)  # Aumenta rechazo
            self.sequence_step = 5
            self.sequence_timer = 2.0
            
        elif self.sequence_step == 5:  # Espíritu habla
            if self.espiritu_dialog_index < len(self.espiritu_dialogues):
                self.show_dialogue("Espíritu", self.espiritu_dialogues[self.espiritu_dialog_index])
                # Afectar estados del juego
                game_state.add_duality("panic_selfcontrol", -12)  # Aumenta pánico
                game_state.add_duality("rejection_understanding", -8)  # Aumenta rechazo
            else:
                self.sequence_step = 6  # Daniela huye
                self.sequence_timer = 1.0
                
        elif self.sequence_step == 6:  # Iniciar huida
            self.has_sentado = False
            self.is_huyendo = True
            self.espiritu_visible = False
            self.show_dialogue("Daniela", "¡No soporto más! ¡Tengo que salir de aquí!")

    def draw(self, screen, game_state):
        surf = screen
        
        # Pantalla negra inicial
        if self.show_black_screen:
            surf.fill((0, 0, 0))
            title_font = pygame.font.SysFont("arial", 48, bold=True)
            title = title_font.render(self.black_screen_text, True, (255, 255, 255))
            surf.blit(title, (WIDTH // 2 - title.get_width() // 2, HEIGHT // 2 - 50))
            return
        
        # Fondo del aula
        surf.blit(self.bg, (0, 0))

        # Dibujar silla (siempre visible, ENORME)
        if self.silla_img:
            silla_rect = self.silla_img.get_rect(center=self.silla_pos)
            surf.blit(self.silla_img, silla_rect)
            
            # Indicador de interacción si está cerca y puede sentarse
            if self.can_move and not self.has_sentado:
                silla_center = pygame.Vector2(self.silla_pos)
                distancia = silla_center.distance_to(self.daniela_pos)
                if distancia < 150:  # Mayor tolerancia para silla más grande
                    # Solo un efecto visual sutil (sin texto)
                    highlight = pygame.Surface((self.silla_zone.width, self.silla_zone.height), pygame.SRCALPHA)
                    highlight.fill((255, 255, 0, 50))  # Amarillo semi-transparente
                    surf.blit(highlight, self.silla_zone.topleft)

        # Dibujar espíritu (EN MOVIMIENTO)
        if self.espiritu_visible and self.espiritu_img:
            espiritu_rect = self.espiritu_img.get_rect(center=self.espiritu_pos)
            surf.blit(self.espiritu_img, espiritu_rect)
            
            # Dibujar línea fantasmal desde el espíritu hacia Daniela
            if self.has_sentado:
                start_pos = self.espiritu_pos
                end_pos = self.silla_pos
                # Línea discontinua para efecto fantasmal
                for i in range(0, 100, 10):
                    t = i / 100.0
                    x = start_pos[0] + (end_pos[0] - start_pos[0]) * t
                    y = start_pos[1] + (end_pos[1] - start_pos[1]) * t
                    if i % 20 < 10:  # Patrón de guiones
                        pygame.draw.circle(surf, (200, 100, 200, 150), (int(x), int(y)), 3)

        # Dibujar Daniela
        if self.has_sentado and self.daniela_sentada_img:
            # Daniela sentada en la silla
            sentada_rect = self.daniela_sentada_img.get_rect(center=self.silla_pos)
            surf.blit(self.daniela_sentada_img, sentada_rect)
        elif not self.has_sentado:
            # Daniela de pie y moviéndose
            current_sprite = self.daniela_states.get(self.daniela_state)
            if current_sprite:
                # Voltear sprite si mira hacia la derecha
                if self.facing_right:
                    current_sprite = pygame.transform.flip(current_sprite, True, False)
                surf.blit(current_sprite, current_sprite.get_rect(center=(int(self.daniela_pos.x), int(self.daniela_pos.y))))
            else:
                # Placeholder
                pygame.draw.circle(surf, (0, 0, 255), (int(self.daniela_pos.x), int(self.daniela_pos.y)), 40)

        # Dibujar zona de salida cuando esté huyendo
        if self.is_huyendo:
            exit_text = self.font.render("SALIR →", True, (255, 0, 0))
            surf.blit(exit_text, (WIDTH - 80, HEIGHT // 2 - 50))

        # Dibujar diálogo
        self.draw_dialogue_with_speaker(surf)
        
        # Dibujar estadísticas
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
            elif self.current_speaker == "Espíritu":
                speaker_color = (255, 100, 100)
            elif self.current_speaker == "Narrador":
                speaker_color = (200, 200, 100)
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