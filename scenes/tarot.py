import pygame
from settings import WIDTH, HEIGHT, PALETTE
from engine.scene_manager import Scene
from engine.narrator import Narrator
from engine.ui import StatsDisplay

class TarotScene(Scene):
    def __init__(self, manager, game_state, audio):
        super().__init__(manager)
        self.game_state = game_state
        self.audio = audio
        self.font = pygame.font.SysFont("arial", 28)
        self.speaker_font = pygame.font.SysFont("arial", 24)
        self.narrator = Narrator(self.font)
        self.stats_display = StatsDisplay(game_state)

        # Estados de la escena
        self.state = "INTRO"  # INTRO, ENTRANDO, DIALOGO, ELECCION
        self.intro_timer = 0
        self.waiting_for_click = True
        
        # Cargar imágenes
        try:
            self.bg = pygame.image.load("assets/images/casa_tarot_bg.png").convert()
            self.bg = pygame.transform.smoothscale(self.bg, (WIDTH, HEIGHT))
        except:
            self.bg = pygame.Surface((WIDTH, HEIGHT))
            self.bg.fill((80, 60, 100))

        # Daniela asustada - CORREGIDA: sin voltear para que mire a la izquierda
        try:
            self.daniela_asustada = pygame.image.load("assets/images/asustada_pr.png").convert_alpha()
            self.daniela_asustada = pygame.transform.smoothscale(self.daniela_asustada, (120, 240))
            # NO voltear - dejar que mire a la izquierda naturalmente
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

        # Diálogos con información del hablante
        self.dialogues = [
            {"speaker": "Elena", "text": "Has atraído demasiados ojos, pequeña. Vienes acompañada."},
            {"speaker": "Daniela", "text": "¿Qué? ¿De qué está hablando?"},
            {"speaker": "Elena", "text": "A mi no me intentes engañar, se que también los ves"},
            {"speaker": "Daniela", "text": "..."},
            {"speaker": "Daniela", "text": "Pero no quiero."},
            {"speaker": "Daniela", "text": "No quiero ver nada."},
            {"speaker": "Daniela", "text": "Solo quiero ser normal."},
            {"speaker": "Elena", "text": "El Jardín de los Susurros está en peligro. Para ayudarte a ti misma, debes ayudar a los espíritus. Ve allí y restaura el equilibrio."},
        ]
        self.current_dialogue = 0
        self.dialogue_timer = 0
        self.dialogue_speed = 4.0
        self.can_skip = False
        self.current_speaker = None
        self.dialogue_text = ""

        # Opciones al final
        self.options = ["Aceptar la misión", "Postergar la salida"]
        self.selected_option = 0
        self.show_options = False

        # Posiciones - MÁS ARRIBA
        self.daniela_start_pos = pygame.Vector2(-100, HEIGHT - 200)  # Más arriba
        self.daniela_target_pos = pygame.Vector2(WIDTH // 3, HEIGHT - 200)  # Más arriba
        self.daniela_pos = self.daniela_start_pos.copy()
        self.daniela_speed = 150
        self.daniela_moving = True

        self.tarotista_pos = (2 * WIDTH // 3, HEIGHT - 220)  # Tarotista más arriba

        # Control de tiempo entre diálogos
        self.dialogue_cooldown = 0.5

    def on_enter(self):
        # Configurar el narrador para que los diálogos duren más tiempo
        self.narrator.display_time = 4.0
        # Iniciar con la pantalla negra esperando clic
        self.state = "INTRO"
        self.waiting_for_click = True
        self.current_dialogue = 0
        self.show_options = False
        self.daniela_pos = self.daniela_start_pos.copy()
        self.daniela_moving = True

    def show_dialogue(self, speaker, text):
        """Muestra diálogo con el nombre del hablante"""
        self.current_speaker = speaker
        self.dialogue_text = text
        self.narrator.say(text)

    def handle_event(self, event, game_state):
        if self.state == "INTRO" and self.waiting_for_click:
            if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                self.waiting_for_click = False
                self.state = "ENTRANDO"
        
        elif self.state == "DIALOGO":
            if event.type == pygame.MOUSEBUTTONUP and event.button == 1 and self.dialogue_cooldown <= 0:
                if self.can_skip:
                    self.current_dialogue += 1
                    self.dialogue_timer = 0
                    self.can_skip = False
                    self.dialogue_cooldown = 0.5
                    
                    # Si llegamos al final de los diálogos, mostrar opciones
                    if self.current_dialogue >= len(self.dialogues):
                        self.show_options = True
                        self.state = "EXPLORAR"
                    else:
                        # Mostrar siguiente diálogo
                        dialogue = self.dialogues[self.current_dialogue]
                        self.show_dialogue(dialogue["speaker"], dialogue["text"])
        
        elif self.state == "EXPLORAR" and self.show_options:
            if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                x, y = event.pos
                
                # Verificar clic en opciones
                option_height = 50
                option_start_y = HEIGHT // 2
                
                for i, option in enumerate(self.options):
                    option_rect = pygame.Rect(WIDTH // 2 - 150, option_start_y + i * option_height, 300, 40)
                    if option_rect.collidepoint(x, y):
                        self.selected_option = i
                        self.select_option(game_state)
                        return

    def select_option(self, game_state):
        if self.selected_option == 0:
            # Aceptar la misión - ir al jardín
            self.show_dialogue("Daniela", "Voy al Jardín de los Susurros...")
            # Transición a la siguiente escena (Jardín)
            from scenes.garden import GardenScene
            self.manager.push(GardenScene(self.manager, self.game_state, self.audio))
        else:
            # Postergar - volver al título
            game_state.add_duality("rejection_understanding", -8)
            self.show_dialogue("Daniela", "Necesito más tiempo para pensarlo...")
            from scenes.title import TitleScene
            self.manager.replace(TitleScene(self.manager))

    def update(self, dt, game_state):
        if self.dialogue_cooldown > 0:
            self.dialogue_cooldown -= dt

        if self.state == "ENTRANDO":
            # Mover a Daniela desde la izquierda hasta su posición
            if self.daniela_moving:
                direction = self.daniela_target_pos - self.daniela_pos
                distance = direction.length()
                
                if distance > 5:
                    self.daniela_pos += direction.normalize() * min(self.daniela_speed * dt, distance)
                else:
                    # Llegó a su posición
                    self.daniela_moving = False
                    self.state = "DIALOGO"
                    # Mostrar el primer diálogo
                    dialogue = self.dialogues[self.current_dialogue]
                    self.show_dialogue(dialogue["speaker"], dialogue["text"])

        elif self.state == "DIALOGO":
            self.dialogue_timer += dt
            if self.dialogue_timer >= 1.0:
                self.can_skip = True
            
            # Avance automático si no se salta
            if self.dialogue_timer >= self.dialogue_speed:
                self.dialogue_timer = 0
                self.current_dialogue += 1
                self.can_skip = False
                
                if self.current_dialogue >= len(self.dialogues):
                    self.show_options = True
                    self.state = "EXPLORAR"
                else:
                    dialogue = self.dialogues[self.current_dialogue]
                    self.show_dialogue(dialogue["speaker"], dialogue["text"])

        self.narrator.update(dt)

    def draw(self, screen, game_state):
        if self.state == "INTRO":
            # Pantalla negra con texto - SOLO SE PASA CON CLIC
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
            # Dibujar fondo de la tienda
            screen.blit(self.bg, (0, 0))

            # Dibujar personajes
            # Daniela - durante la entrada usa sprite caminando, después asustada
            if self.state == "ENTRANDO" and self.daniela_caminando:
                screen.blit(self.daniela_caminando, self.daniela_caminando.get_rect(center=(int(self.daniela_pos.x), int(self.daniela_pos.y))))
            elif self.daniela_asustada:
                screen.blit(self.daniela_asustada, self.daniela_asustada.get_rect(center=(int(self.daniela_pos.x), int(self.daniela_pos.y))))

            # Tarotista: si está hablando Elena, usar tarotista_habla, sino tarotista_frente
            if self.state == "DIALOGO" and self.current_dialogue < len(self.dialogues):
                current_speaker = self.dialogues[self.current_dialogue]["speaker"]
                if current_speaker == "Elena" and self.tarotista_habla:
                    screen.blit(self.tarotista_habla, self.tarotista_habla.get_rect(center=self.tarotista_pos))
                elif self.tarotista_frente:
                    screen.blit(self.tarotista_frente, self.tarotista_frente.get_rect(center=self.tarotista_pos))
            else:
                # Por defecto, tarotista de frente
                if self.tarotista_frente:
                    screen.blit(self.tarotista_frente, self.tarotista_frente.get_rect(center=self.tarotista_pos))

            # Si estamos en exploración y mostrar opciones
            if self.state == "EXPLORAR" and self.show_options:
                # Instrucciones
                inst_surf = self.font.render("Elige una opción:", True, (255, 255, 255))
                screen.blit(inst_surf, (WIDTH // 2 - inst_surf.get_width() // 2, 50))
                
                # Dibujar opciones
                option_height = 50
                option_start_y = HEIGHT // 2
                
                for i, option in enumerate(self.options):
                    color = (255, 255, 0) if i == self.selected_option else (255, 255, 255)
                    option_surf = self.font.render(option, True, color)
                    option_rect = option_surf.get_rect(center=(WIDTH//2, option_start_y + i * option_height))
                    
                    # Fondo para la opción
                    pygame.draw.rect(screen, (0, 0, 0, 180), 
                                   (option_rect.x - 10, option_rect.y - 10, 
                                    option_rect.width + 20, option_rect.height + 10))
                    pygame.draw.rect(screen, color, 
                                   (option_rect.x - 10, option_rect.y - 10, 
                                    option_rect.width + 20, option_rect.height + 10), 2)
                    
                    screen.blit(option_surf, option_rect)

        # Dibujar diálogo personalizado con nombre del hablante
        self.draw_custom_dialogue(screen)
        self.stats_display.draw(screen)
    
    def draw_custom_dialogue(self, surf):
        """Dibuja el diálogo con el nombre del hablante arriba en otro color"""
        if not self.narrator.active:
            return
            
        # Dibujar el cuadro de diálogo
        dialogue_rect = pygame.Rect(50, HEIGHT - 120, WIDTH - 100, 80)
        pygame.draw.rect(surf, (0, 0, 0, 180), dialogue_rect)
        pygame.draw.rect(surf, (255, 255, 255), dialogue_rect, 2)
        
        # Dibujar el nombre del hablante si existe
        if self.current_speaker:
            speaker_color = (255, 255, 0) if self.current_speaker == "Elena" else (0, 255, 255)  # Amarillo para Elena, Cyan para Daniela
            speaker_text = self.speaker_font.render(self.current_speaker, True, speaker_color)
            surf.blit(speaker_text, (dialogue_rect.x + 10, dialogue_rect.y - 25))
        
        # Dibujar el texto del diálogo
        dialogue_lines = self.wrap_text(self.dialogue_text, self.font, WIDTH - 140)
        for i, line in enumerate(dialogue_lines):
            text_surf = self.font.render(line, True, (255, 255, 255))
            surf.blit(text_surf, (dialogue_rect.x + 20, dialogue_rect.y + 15 + i * 30))
    
    def wrap_text(self, text, font, max_width):
        """Envuelve el texto en múltiples líneas si es demasiado ancho"""
        words = text.split(' ')
        lines = []
        current_line = []
        
        for word in words:
            test_line = ' '.join(current_line + [word])
            test_width = font.size(test_line)[0]
            
            if test_width <= max_width:
                current_line.append(word)
            else:
                lines.append(' '.join(current_line))
                current_line = [word]
        
        if current_line:
            lines.append(' '.join(current_line))
            
        return lines