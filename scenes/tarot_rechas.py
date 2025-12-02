import pygame
from settings import WIDTH, HEIGHT, PALETTE
from engine.scene_manager import Scene
from engine.narrator import Narrator
from engine.ui import StatsDisplay

class TarotRechasScene(Scene):
    def __init__(self, manager, game_state, audio):
        super().__init__(manager)
        self.game_state = game_state
        self.audio = audio
        self.font = pygame.font.SysFont("arial", 28)
        self.speaker_font = pygame.font.SysFont("arial", 24, bold=True)
        self.narrator = Narrator(self.font)
        self.stats_display = StatsDisplay(game_state)

        # Estados de la escena
        self.state = "INTRO"
        self.waiting_for_click = True
        
        # Cargar imágenes - MISMO FONDO Y PERSONAJES QUE ESCENA 2
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

        # Obtener estadísticas del jardín
        self.spirits_listened = 0
        self.darknesses_cleaned = 0
        self.spirits_cleaned = 0
        
        # Intentar obtener flags
        if hasattr(game_state, 'flags'):
            self.spirits_listened = game_state.flags.get("espiritus_escuchados", 0)
            self.darknesses_cleaned = game_state.flags.get("oscuridades_limpiadas", 0)
            self.spirits_cleaned = game_state.flags.get("espiritus_limpiados", 0)

        # Diálogos con nombres - BASADO EN DECISIÓN DE RENUNCIAR AL PODER
        self.dialogues = [
            {"speaker": "Daniela", "text": "He vuelto... y he hecho lo que pediste."},
            {"speaker": "Elena", "text": "Lo veo. Las sombras del jardín están más tranquilas."},
        ]
        
        # Diálogo diferente dependiendo de si escuchó espíritus
        if self.spirits_listened > 0:
            self.dialogues.append({"speaker": "Daniela", "text": f"Escuché a {self.spirits_listened} de ellos... y fue demasiado."})
            self.dialogues.append({"speaker": "Elena", "text": "El entendimiento sin compasión es un peso demasiado grande para algunos."})
        else:
            self.dialogues.append({"speaker": "Daniela", "text": f"Limpié {self.darknesses_cleaned} oscuridades, termine mi tarea."})
            self.dialogues.append({"speaker": "Elena", "text": "Hay muchas formas de hacer una cosa, podrias a ver..."})
        
        # Continuación de diálogos
        self.dialogues.extend([
            {"speaker": "Daniela", "text": "No importa!"},
            {"speaker": "Daniela", "text": "Solo quiero que esto termine."},
            {"speaker": "Daniela", "text": "Cumple tu parte del trato."},
            {"speaker": "Elena", "text": "¿Estás segura? Una vez que cierres esta puerta, no podrás volver a abrirla."},
            {"speaker": "Daniela", "text": "Estoy segura."},
            {"speaker": "Elena", "text": "Como desees. Pero recuerda: lo que ignoras no deja de existir. Solo dejarás de verlo."}
        ])
        
        self.current_dialogue = 0
        self.dialogue_timer = 0
        self.dialogue_speed = 4.0
        self.can_skip = False
        self.current_speaker = None
        self.current_dialogue_text = ""

        # Opciones al final - diferentes para esta escena
        self.options = ["Confirmar la renuncia", "Pensarlo una vez más"]
        self.selected_option = 0
        self.show_options = False
        self.option_selected = False

        # Posiciones
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
                
                option_height = 60
                option_start_y = HEIGHT // 2 - 30
                
                for i, option in enumerate(self.options):
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
            # Confirmar renuncia - FINAL NEGATIVO
            game_state.add_duality("rejection_understanding", -50)
            game_state.add_duality("panic_selfcontrol", 50)  # Aumenta autocontrol (pierde miedo)
            self.transition_timer = 3.0
            self.transition_target = "ending_rechas"
        else:
            # Pensarlo más - FINAL NEUTRO-NEGATIVO
            self.current_speaker = "Daniela"
            self.current_dialogue_text = "Tal vez... tal vez necesite más tiempo para decidir."
            game_state.add_duality("rejection_understanding", -20)
            self.transition_timer = 3.0
            self.transition_target = "ending_doubt"

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

        if hasattr(self, 'transition_timer') and self.transition_timer > 0:
            self.transition_timer -= dt
            if self.transition_timer <= 0:
                if self.transition_target == "ending_rechas":
                    self.show_final_screen = True
                    self.final_text = [
                        "FINAL: LA NEGACIÓN",
                        f"Daniela renunció a su don para siempre."
                    ]
                    self.final_timer = 5.0
                elif self.transition_target == "ending_doubt":
                    self.show_final_screen = True
                    self.final_text = [
                        "FINAL: LA DUDA PERMANENTE",
                        f"Daniela no pudo decidirse, atrapada entre el miedo y la curiosidad."
                    ]
                    self.final_timer = 5.0

        if hasattr(self, 'show_final_screen') and self.show_final_screen:
            if hasattr(self, 'final_timer'):
                self.final_timer -= dt
                if self.final_timer <= 0:
                    from scenes.title import TitleScene
                    self.manager.replace(TitleScene(self.manager))

        self.narrator.update(dt)

    def draw(self, screen, game_state):
        if hasattr(self, 'show_final_screen') and self.show_final_screen:
            self.draw_final_screen(screen)
            return
            
        if self.state == "INTRO":
            screen.fill((0, 0, 0))
            font_large = pygame.font.SysFont("arial", 36)
            font_small = pygame.font.SysFont("arial", 24)
            
            text1 = font_large.render("Daniela regresa a la tienda, agotada pero determinada.", True, (255, 255, 255))
            hint = font_small.render("(Haz clic para continuar)", True, (150, 150, 150))
            
            text1_rect = text1.get_rect(center=(WIDTH//2, HEIGHT//2 - 30))
            text2_rect = text2.get_rect(center=(WIDTH//2, HEIGHT//2 + 10))
            hint_rect = hint.get_rect(center=(WIDTH//2, HEIGHT//2 + 60))
            
            screen.blit(text1, text1_rect)
            screen.blit(text2, text2_rect)
            screen.blit(hint, hint_rect)

        else:
            screen.blit(self.bg, (0, 0))

            if self.state == "ENTRANDO" and self.daniela_caminando:
                screen.blit(self.daniela_caminando, self.daniela_caminando.get_rect(center=(int(self.daniela_pos.x), int(self.daniela_pos.y))))
            elif self.daniela_asustada:
                screen.blit(self.daniela_asustada, self.daniela_asustada.get_rect(center=(int(self.daniela_pos.x), int(self.daniela_pos.y))))

            if self.state == "DIALOGO" and self.current_dialogue < len(self.dialogues):
                if self.dialogues[self.current_dialogue]["speaker"] == "Elena" and self.tarotista_habla:
                    screen.blit(self.tarotista_habla, self.tarotista_habla.get_rect(center=self.tarotista_pos))
                elif self.tarotista_frente:
                    screen.blit(self.tarotista_frente, self.tarotista_frente.get_rect(center=self.tarotista_pos))
            else:
                if self.tarotista_frente:
                    screen.blit(self.tarotista_frente, self.tarotista_frente.get_rect(center=self.tarotista_pos))

            if self.state == "EXPLORAR" and self.show_options and not self.option_selected:
                self.draw_options_ui(screen)

        self.draw_dialogue_with_speaker(screen)
        self.stats_display.draw(screen)
    
    def draw_dialogue_with_speaker(self, screen):
        if (self.state == "DIALOGO" or 
            (hasattr(self, 'transition_timer') and self.transition_timer > 0) or
            (self.state == "EXPLORAR" and self.option_selected)):
            
            if not self.current_dialogue_text:
                return
                
            box_width = WIDTH - 100
            box_height = 100
            box_x = 50
            box_y = HEIGHT - box_height - 20
            
            pygame.draw.rect(screen, (0, 0, 0, 200), (box_x, box_y, box_width, box_height))
            pygame.draw.rect(screen, (255, 255, 255), (box_x, box_y, box_width, box_height), 2)
            
            if self.current_speaker:
                if self.current_speaker == "Elena":
                    speaker_color = (255, 215, 0)
                elif self.current_speaker == "Daniela":
                    speaker_color = (0, 200, 255)
                else:
                    speaker_color = (255, 255, 255)
                
                speaker_text = self.speaker_font.render(self.current_speaker, True, speaker_color)
                screen.blit(speaker_text, (box_x + 10, box_y - 30))
            
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
            
            for i, line in enumerate(lines):
                if i < 3:
                    text_surf = self.font.render(line, True, (255, 255, 255))
                    screen.blit(text_surf, (box_x + 20, box_y + 15 + i * 30))
            
            if self.can_skip and self.state == "DIALOGO":
                skip_text = self.font.render("Clic para continuar", True, (200, 200, 200))
                screen.blit(skip_text, (box_x + box_width - skip_text.get_width() - 20, box_y + box_height - 30))
    
    def draw_options_ui(self, screen):
        option_height = 60
        option_start_y = HEIGHT // 2 - 30
        
        title_font = pygame.font.SysFont("arial", 32, bold=True)
        title = title_font.render("¿Confirmas tu decisión?", True, (255, 255, 255))
        screen.blit(title, (WIDTH // 2 - title.get_width() // 2, HEIGHT // 2 - 100))
        
        for i, option in enumerate(self.options):
            is_hovered = False
            mouse_pos = pygame.mouse.get_pos()
            option_rect = pygame.Rect(
                WIDTH // 2 - 200, 
                option_start_y + i * option_height, 
                400, 50
            )
            
            if option_rect.collidepoint(mouse_pos):
                is_hovered = True
            
            if i == self.selected_option and self.option_selected:
                text_color = (255, 150, 150)
                bg_color = (80, 40, 60, 180)
                border_color = (255, 150, 150)
            elif is_hovered:
                text_color = (255, 255, 255)
                bg_color = (100, 60, 80, 200)
                border_color = (255, 180, 180)
            else:
                text_color = (220, 220, 220)
                bg_color = (70, 30, 50, 150)
                border_color = (180, 120, 150)
            
            s = pygame.Surface((option_rect.width, option_rect.height), pygame.SRCALPHA)
            s.fill(bg_color)
            screen.blit(s, option_rect)
            
            pygame.draw.rect(screen, border_color, option_rect, 3, border_radius=8)
            
            option_surf = self.font.render(option, True, text_color)
            option_text_rect = option_surf.get_rect(center=option_rect.center)
            screen.blit(option_surf, option_text_rect)
            
            if i == self.selected_option and self.option_selected:
                check_surf = self.font.render("✓", True, (255, 150, 150))
                screen.blit(check_surf, (option_rect.right - 40, option_rect.centery - 15))
            elif is_hovered:
                arrow_surf = self.font.render("→", True, (255, 255, 255))
                screen.blit(arrow_surf, (option_rect.left + 20, option_rect.centery - 15))
    
    def draw_final_screen(self, screen):
        screen.fill((0, 0, 0))
        
        title_font = pygame.font.SysFont("arial", 36, bold=True)
        text_font = pygame.font.SysFont("arial", 24)
        stats_font = pygame.font.SysFont("arial", 20)
        
        title = title_font.render(self.final_text[0], True, (255, 150, 150))
        screen.blit(title, (WIDTH // 2 - title.get_width() // 2, HEIGHT // 4))
        
        for i, line in enumerate(self.final_text[1:], 1):
            text = text_font.render(line, True, (255, 200, 200))
            screen.blit(text, (WIDTH // 2 - text.get_width() // 2, HEIGHT // 3 + i * 40))
        
        stats_y = HEIGHT // 2 + 150
        stats = [
            f"Rechazo final: {self.game_state.dualities['rejection_understanding']}",
            f"Autocontrol final: {self.game_state.dualities['panic_selfcontrol']}"
        ]
        
        for i, stat in enumerate(stats):
            stat_text = stats_font.render(stat, True, (255, 200, 200))
            screen.blit(stat_text, (WIDTH // 2 - stat_text.get_width() // 2, stats_y + i * 35))
        
        continue_text = text_font.render("Clic para volver al menú principal", True, (255, 200, 200))
        screen.blit(continue_text, (WIDTH // 2 - continue_text.get_width() // 2, HEIGHT - 100))