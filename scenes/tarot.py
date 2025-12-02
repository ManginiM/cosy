import pygame
from settings import WIDTH, HEIGHT, PALETTE
from engine.scene_manager import Scene
from engine.narrator import Narrator
from engine.ui import StatsDisplay

class TarotScene(Scene):
    def __init__(self, manager, game_state, audio=None):
        super().__init__(manager)
        self.game_state = game_state
        self.audio = audio
        self.font = pygame.font.SysFont("arial", 28)
        self.speaker_font = pygame.font.SysFont("arial", 24, bold=True)  # Fuente para nombres
        self.narrator = Narrator(self.font)
        self.stats_display = StatsDisplay(game_state)

        # Estados de la escena
        self.state = "INTRO"
        self.waiting_for_click = True
        
        # Cargar imágenes
        try:
            self.bg = pygame.image.load("assets/images/casa_tarot_bg.png").convert()
            self.bg = pygame.transform.smoothscale(self.bg, (WIDTH, HEIGHT))
        except:
            self.bg = pygame.Surface((WIDTH, HEIGHT))
            self.bg.fill((80, 60, 100))

        # Daniela asustada - SIN VOLTEAR (mira a la izquierda)
        try:
            self.daniela_asustada = pygame.image.load("assets/images/asustada_pr.png").convert_alpha()
            self.daniela_asustada = pygame.transform.smoothscale(self.daniela_asustada, (120, 240))
        except:
            self.daniela_asustada = None

        # Daniela caminando - para la entrada
        try:
            self.daniela_caminando = pygame.image.load("assets/images/caminando_pr.png").convert_alpha()
            self.daniela_caminando = pygame.transform.smoothscale(self.daniela_caminando, (120, 240))
            # Voltear para que mire a la derecha mientras camina
            self.daniela_caminando = pygame.transform.flip(self.daniela_caminando, True, False)
        except:
            self.daniela_caminando = None

        # Tarotista de frente
        try:
            self.tarotista_frente = pygame.image.load("assets/images/tarota_npc.png").convert_alpha()
            self.tarotista_frente = pygame.transform.smoothscale(self.tarotista_frente, (150, 260))
        except:
            self.tarotista_frente = None

        # Tarotista hablando (mirando a la izquierda)
        try:
            self.tarotista_habla = pygame.image.load("assets/images/tarota_habla_npc.png").convert_alpha()
            self.tarotista_habla = pygame.transform.smoothscale(self.tarotista_habla, (150, 260))
        except:
            self.tarotista_habla = None

        # Diálogos con nombres - MISMO ESTILO QUE ESCENA 2 PERO CON NOMBRES
        self.dialogues = [
            {"speaker": "Elena", "text": "Has atraído demasiados ojos, pequeña."},
            {"speaker": "Daniela", "text": "¿Qué? ¿De qué está hablando?"},
            {"speaker": "Elena", "text": "A mi no me intentes engañar. Los veo a tu alrededor. "},
            {"speaker": "Elena", "text": "Lo sé porque también los veo. Como tú. Pero yo aprendí a escucharlos."},
            {"speaker": "Daniela", "text": "Pero no quiero."},
            {"speaker": "Elena", "text": "El Jardín de los Susurros te espera."},
            {"speaker": "Daniela", "text": "¿El Jardín de los Susurros?"},
            {"speaker": "Elena", "text": "El jardín está en peligro..."},
            {"speaker": "Daniela", "text": "¿Y qué tengo que ver yo con eso?"},
            {"speaker": "Elena", "text": "Te siguen porque necesitan algo que puedes dar."},
            {"speaker": "Daniela", "text": "¿Y si no quiero?"},
            {"speaker": "Elena", "text": "No te dejaran en paz"},
            {"speaker": "Elena", "text": "Igual es tu elección"}
        ]
        
        self.current_dialogue = 0
        self.dialogue_timer = 0
        self.dialogue_speed = 4.0
        self.can_skip = False
        self.current_speaker = None
        self.current_dialogue_text = ""

        # Opciones al final - botones simples sin fondo negro
        self.options = ["Aceptar la misión", "Postergar la salida"]
        self.selected_option = 0
        self.show_options = False
        self.option_selected = False  # Para evitar selección múltiple

        # Posiciones - más arriba
        self.daniela_start_pos = pygame.Vector2(-100, HEIGHT - 180)
        self.daniela_target_pos = pygame.Vector2(WIDTH // 3, HEIGHT - 180)
        self.daniela_pos = self.daniela_start_pos.copy()
        self.daniela_speed = 150
        self.daniela_moving = True

        self.tarotista_pos = (2 * WIDTH // 3, HEIGHT - 200)

        self.dialogue_cooldown = 0.5
        self.transition_timer = 0
        self.transition_target = None

    def on_enter(self):
        self.narrator.display_time = 4.0
        self.state = "INTRO"
        self.waiting_for_click = True
        self.current_dialogue = 0
        self.show_options = False
        self.option_selected = False
        self.daniela_pos = self.daniela_start_pos.copy()
        self.daniela_moving = True
        
        # Inicializar diálogo actual
        if self.dialogues:
            dialogue = self.dialogues[self.current_dialogue]
            self.current_speaker = dialogue["speaker"]
            self.current_dialogue_text = dialogue["text"]

    def show_dialogue(self):
        """Actualiza el diálogo actual para mostrar"""
        if self.current_dialogue < len(self.dialogues):
            dialogue = self.dialogues[self.current_dialogue]
            self.current_speaker = dialogue["speaker"]
            self.current_dialogue_text = dialogue["text"]
            self.dialogue_timer = 0
            self.can_skip = False

    def handle_event(self, event, game_state):
        if self.state == "INTRO" and self.waiting_for_click:
            if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                self.waiting_for_click = False
                self.state = "ENTRANDO"
        
        elif self.state == "DIALOGO":
            if event.type == pygame.MOUSEBUTTONUP and event.button == 1 and self.dialogue_cooldown <= 0:
                if self.can_skip:
                    self.current_dialogue += 1
                    self.dialogue_cooldown = 0.5
                    
                    if self.current_dialogue >= len(self.dialogues):
                        self.show_options = True
                        self.state = "EXPLORAR"
                    else:
                        self.show_dialogue()
        
        elif self.state == "EXPLORAR" and self.show_options and not self.option_selected:
            if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                x, y = event.pos
                
                # Verificar clic en opciones (botones simples, sin fondo)
                option_height = 60
                option_start_y = HEIGHT // 2 - 30
                
                for i, option in enumerate(self.options):
                    # Crear rectángulo invisible para el clic (más grande para mejor usabilidad)
                    option_rect = pygame.Rect(
                        WIDTH // 2 - 200, 
                        option_start_y + i * option_height, 
                        400, 50
                    )
                    
                    if option_rect.collidepoint(x, y):
                        self.selected_option = i
                        self.option_selected = True
                        self.select_option(game_state)
                        return

    def select_option(self, game_state):
        if self.selected_option == 0:
            self.current_speaker = "Daniela"
            self.current_dialogue_text = "Está bien... iré al Jardín de los Susurros."
            self.transition_timer = 3.0  # Dar tiempo para leer el diálogo
            self.transition_target = "garden"
        else:
            game_state.add_duality("rejection_understanding", -8)
            self.current_speaker = "Daniela"
            self.current_dialogue_text = "Necesito más tiempo para pensarlo..."
            self.transition_timer = 3.0
            self.transition_target = "title"

    def update(self, dt, game_state):
        if self.dialogue_cooldown > 0:
            self.dialogue_cooldown -= dt

        if self.state == "ENTRANDO":
            if self.daniela_moving:
                direction = self.daniela_target_pos - self.daniela_pos
                distance = direction.length()
                
                if distance > 5:
                    self.daniela_pos += direction.normalize() * min(self.daniela_speed * dt, distance)
                else:
                    self.daniela_moving = False
                    self.state = "DIALOGO"
                    self.show_dialogue()

        elif self.state == "DIALOGO":
            self.dialogue_timer += dt
            if self.dialogue_timer >= 1.0:
                self.can_skip = True
            
            if self.dialogue_timer >= self.dialogue_speed:
                self.dialogue_timer = 0
                self.current_dialogue += 1
                self.can_skip = False
                
                if self.current_dialogue >= len(self.dialogues):
                    self.show_options = True
                    self.state = "EXPLORAR"
                else:
                    self.show_dialogue()

        # Manejo de la transición - CORREGIDO
        if hasattr(self, 'transition_timer') and self.transition_timer > 0:
            self.transition_timer -= dt
            if self.transition_timer <= 0:
                if self.transition_target == "garden":
                    from scenes.garden import GardenScene
                    # Asegúrate de pasar los parámetros correctos
                    self.manager.replace(GardenScene(self.manager, self.game_state, self.audio))
                else:
                    from scenes.title import TitleScene
                    self.manager.replace(TitleScene(self.manager))

        self.narrator.update(dt)

    def draw(self, screen, game_state):
        if self.state == "INTRO":
            screen.fill((0, 0, 0))
            font_large = pygame.font.SysFont("arial", 36)
            font_small = pygame.font.SysFont("arial", 24)
            
            text1 = font_large.render("Daniela corrió por mucho rato hasta que se perdió,", True, (255, 255, 255))
            text2 = font_large.render("y encontró la tienda de una señora", True, (255, 255, 255))
            hint = font_small.render("(Haz clic para continuar)", True, (150, 150, 150))
            
            text1_rect = text1.get_rect(center=(WIDTH//2, HEIGHT//2 - 30))
            text2_rect = text2.get_rect(center=(WIDTH//2, HEIGHT//2 + 10))
            hint_rect = hint.get_rect(center=(WIDTH//2, HEIGHT//2 + 60))
            
            screen.blit(text1, text1_rect)
            screen.blit(text2, text2_rect)
            screen.blit(hint, hint_rect)

        else:
            screen.blit(self.bg, (0, 0))

            # Dibujar personajes
            # Daniela - durante la entrada usa sprite caminando, después asustada
            if self.state == "ENTRANDO" and self.daniela_caminando:
                screen.blit(self.daniela_caminando, self.daniela_caminando.get_rect(center=(int(self.daniela_pos.x), int(self.daniela_pos.y))))
            elif self.daniela_asustada:
                screen.blit(self.daniela_asustada, self.daniela_asustada.get_rect(center=(int(self.daniela_pos.x), int(self.daniela_pos.y))))

            # Tarotista: si está hablando Elena, usar tarotista_habla, sino tarotista_frente
            if self.state == "DIALOGO" and self.current_dialogue < len(self.dialogues):
                # Los diálogos pares son de Elena (0, 2, 4...)
                if self.dialogues[self.current_dialogue]["speaker"] == "Elena" and self.tarotista_habla:
                    screen.blit(self.tarotista_habla, self.tarotista_habla.get_rect(center=self.tarotista_pos))
                elif self.tarotista_frente:
                    screen.blit(self.tarotista_frente, self.tarotista_frente.get_rect(center=self.tarotista_pos))
            else:
                # Por defecto, tarotista de frente
                if self.tarotista_frente:
                    screen.blit(self.tarotista_frente, self.tarotista_frente.get_rect(center=self.tarotista_pos))

            # Si estamos en exploración y mostrar opciones
            if self.state == "EXPLORAR" and self.show_options and not self.option_selected:
                self.draw_options_ui(screen)

        # Dibujar diálogo con nombre del hablante
        self.draw_dialogue_with_speaker(screen)
        self.stats_display.draw(screen)
    
    def draw_dialogue_with_speaker(self, screen):
        """Dibuja el diálogo con el nombre del hablante arriba"""
        # Solo dibujar si hay diálogo activo o estamos en estado DIALOGO o transición
        if (self.state == "DIALOGO" or 
            (hasattr(self, 'transition_timer') and self.transition_timer > 0) or
            (self.state == "EXPLORAR" and self.option_selected)):
            
            if not self.current_dialogue_text:
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
                # Color según el hablante
                if self.current_speaker == "Elena":
                    speaker_color = (255, 215, 0)  # Dorado para Elena
                elif self.current_speaker == "Daniela":
                    speaker_color = (0, 200, 255)  # Cyan para Daniela
                else:
                    speaker_color = (255, 255, 255)  # Blanco por defecto
                
                speaker_text = self.speaker_font.render(self.current_speaker, True, speaker_color)
                screen.blit(speaker_text, (box_x + 10, box_y - 30))
            
            # Dibujar texto del diálogo (con salto de línea si es necesario)
            words = self.current_dialogue_text.split(' ')
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
            
            # Dibujar líneas de texto
            for i, line in enumerate(lines):
                if i < 3:  # Máximo 3 líneas
                    text_surf = self.font.render(line, True, (255, 255, 255))
                    screen.blit(text_surf, (box_x + 20, box_y + 15 + i * 30))
            
            # Indicador de "clic para continuar" si se puede saltar
            if self.can_skip and self.state == "DIALOGO":
                skip_text = self.font.render("Clic para continuar", True, (200, 200, 200))
                screen.blit(skip_text, (box_x + box_width - skip_text.get_width() - 20, box_y + box_height - 30))
    
    def draw_options_ui(self, screen):
        """Dibuja las opciones con estilo simple y claro"""
        option_height = 60
        option_start_y = HEIGHT // 2 - 30
        
        # Título de las opciones
        title_font = pygame.font.SysFont("arial", 32, bold=True)
        title = title_font.render("¿Qué decides hacer?", True, (255, 255, 255))
        screen.blit(title, (WIDTH // 2 - title.get_width() // 2, HEIGHT // 2 - 100))
        
        for i, option in enumerate(self.options):
            # Determinar colores según estado
            is_hovered = False
            mouse_pos = pygame.mouse.get_pos()
            option_rect = pygame.Rect(
                WIDTH // 2 - 200, 
                option_start_y + i * option_height, 
                400, 50
            )
            
            # Verificar hover
            if option_rect.collidepoint(mouse_pos):
                is_hovered = True
            
            # Colores según estado
            if i == self.selected_option and self.option_selected:
                # Ya fue seleccionada
                text_color = (255, 215, 0)  # Dorado
                bg_color = (60, 40, 80, 180)  # Morado oscuro semi-transparente
                border_color = (255, 215, 0)  # Dorado
            elif is_hovered:
                # Mouse encima
                text_color = (255, 255, 255)  # Blanco
                bg_color = (80, 60, 100, 200)  # Morado medio semi-transparente
                border_color = (200, 180, 255)  # Morado claro
            else:
                # Normal
                text_color = (220, 220, 220)  # Gris claro
                bg_color = (50, 30, 70, 150)  # Morado muy oscuro semi-transparente
                border_color = (150, 120, 180)  # Morado medio
            
            # Dibujar fondo semi-transparente
            s = pygame.Surface((option_rect.width, option_rect.height), pygame.SRCALPHA)
            s.fill(bg_color)
            screen.blit(s, option_rect)
            
            # Dibujar borde
            pygame.draw.rect(screen, border_color, option_rect, 3, border_radius=8)
            
            # Texto
            option_surf = self.font.render(option, True, text_color)
            option_text_rect = option_surf.get_rect(center=option_rect.center)
            screen.blit(option_surf, option_text_rect)
            
            # Indicador de selección (flecha o checkmark)
            if i == self.selected_option and self.option_selected:
                check_surf = self.font.render("✓", True, (255, 215, 0))
                screen.blit(check_surf, (option_rect.right - 40, option_rect.centery - 15))
            elif is_hovered:
                # Flecha para indicar hover
                arrow_surf = self.font.render("→", True, (255, 255, 255))
                screen.blit(arrow_surf, (option_rect.left + 20, option_rect.centery - 15))