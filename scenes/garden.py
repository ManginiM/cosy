import pygame
import random
from settings import WIDTH, HEIGHT, PALETTE
from engine.scene_manager import Scene
from engine.narrator import Narrator
from engine.ui import StatsDisplay

class GardenScene(Scene):
    def __init__(self, manager, game_state, audio):
        super().__init__(manager)
        self.game_state = game_state
        self.audio = audio
        self.font = pygame.font.SysFont("arial", 28)
        self.speaker_font = pygame.font.SysFont("arial", 24, bold=True)
        self.narrator = Narrator(self.font)
        self.stats_display = StatsDisplay(game_state)

        # Cargar fondo
        try:
            self.bg = pygame.image.load("assets/images/forest_glitter.png").convert()
            self.bg = pygame.transform.smoothscale(self.bg, (WIDTH, HEIGHT))
        except:
            self.bg = pygame.Surface((WIDTH, HEIGHT))
            self.bg.fill((30, 60, 40))

        # Cargar imágenes de Daniela
        self.daniela_sprites = {}
        sprite_files = {
            "quieta": "parada_frente_pr.png",
            "caminando": "caminando_pr.png",
            "asustada": "asustada_pr.png",
            "escuchando": "agachada_pr.png"
        }
        
        for name, file in sprite_files.items():
            try:
                img = pygame.image.load(f"assets/images/{file}").convert_alpha()
                self.daniela_sprites[name] = pygame.transform.smoothscale(img, (120, 240))
            except:
                pass

        # Cargar imágenes de espíritus y oscuridades
        self.load_images()
        
        # Estados de juego
        self.state = "ENTRADA"
        self.decision_made = None
        
        # Daniela
        self.daniela_pos = pygame.Vector2(WIDTH // 2, HEIGHT - 150)
        self.daniela_target = self.daniela_pos.copy()
        self.daniela_speed = 300
        self.daniela_state = "quieta"
        self.facing_right = True
        
        # Inicializar juego
        self.init_game()
        
        # Diálogos
        self.current_dialogue = None
        self.current_speaker = None
        self.dialogue_timer = 0
        self.dialogue_duration = 4.0
        self.can_skip = False
        self.dialogue_cooldown = 0.5
        
        # Temporizador de transición
        self.transition_timer = 0

    def load_images(self):
        """Carga todas las imágenes necesarias"""
        # Espíritus afectados
        self.spirit_affected_images = []
        try:
            esp1 = pygame.image.load("assets/images/espiritu1_npc.png").convert_alpha()
            esp1 = pygame.transform.smoothscale(esp1, (100, 150))
            self.spirit_affected_images.append(esp1)
            
            esp2 = pygame.image.load("assets/images/espiritu2_npc.png").convert_alpha()
            esp2 = pygame.transform.smoothscale(esp2, (100, 150))
            self.spirit_affected_images.append(esp2)
        except:
            pass
        
        # Espíritus limpios
        self.spirit_cleaned_images = []
        for i in range(1, 4):
            try:
                img = pygame.image.load(f"assets/images/fantasma_limpio{i}_npc.png").convert_alpha()
                img = pygame.transform.smoothscale(img, (100, 150))
                self.spirit_cleaned_images.append(img)
            except:
                pass
        
        # Oscuridad
        try:
            self.darkness_image = pygame.image.load("assets/images/oscuridad_icon.png").convert_alpha()
            self.darkness_image = pygame.transform.smoothscale(self.darkness_image, (80, 80))
        except:
            self.darkness_image = None

    def init_game(self):
        """Inicializa todos los elementos del juego"""
        # Número de elementos
        self.num_spirits = 8
        self.spirits = []
        self.darknesses = []
        
        # Contadores
        self.spirits_listened = 0
        self.darknesses_cleaned = 0
        self.spirits_cleaned = 0
        self.game_completed = False
        
        # Diálogos
        self.spirit_dialogues = [
            "Soy María... la oscuridad me hace ver monstruosa. Antes era maestra...",
            "Me llamo Carlos. Estas sombras distorsionan mi verdadera forma. Era médico...",
            "Soy Juan, un artista. La oscuridad me ha robado los colores...",
            "Me dicen la Dama Blanca... pero ahora soy una sombra de lo que fui.",
            "Soy un niño perdido... tengo miedo de esta oscuridad.",
            "Fui guardián de este jardín... ahora las sombras me atormentan.",
            "Busco a mi esposa... la oscuridad nos separó.",
            "Mi nombre se perdió... solo queda este tormento."
        ]
        
        self.darkness_dialogues = [
            "Una presencia oscura... mejor no mirar...",
            "Algo se retuerce en la sombra... tengo miedo...",
            "No quiero ver lo que hay dentro...",
            "Es fría y pegajosa... me da náuseas.",
            "Parece que me observa desde dentro.",
            "Retrocede... no te acerques...",
            "Siento un vacío helado...",
            "Algo susurra desde la oscuridad..."
        ]
        
        # Crear espíritus y oscuridades
        self.create_spirits_and_darknesses()

    def create_spirits_and_darknesses(self):
        """Crea los espíritus y oscuridades en posiciones aleatorias"""
        used_positions = []
        
        for i in range(self.num_spirits):
            # Encontrar posición para espíritu
            attempts = 0
            while attempts < 50:
                x = random.randint(100, WIDTH - 100)
                y = random.randint(100, HEIGHT - 200)
                pos = pygame.Vector2(x, y)
                
                # Verificar que no esté demasiado cerca de otras posiciones
                too_close = False
                for other_pos in used_positions:
                    if pos.distance_to(other_pos) < 150:
                        too_close = True
                        break
                
                if not too_close:
                    used_positions.append(pos)
                    
                    # Crear espíritu
                    spirit = {
                        "pos": pos,
                        "radius": 50,
                        "active": True,
                        "hovered": False,
                        "listened": False,
                        "cleaned": False,
                        "affected_image_index": i % 2 if self.spirit_affected_images else 0,
                        "cleaned_image_index": random.randint(0, len(self.spirit_cleaned_images)-1) if self.spirit_cleaned_images else 0,
                        "dialogue": self.spirit_dialogues[i % len(self.spirit_dialogues)],
                        "can_be_cleaned": True
                    }
                    self.spirits.append(spirit)
                    
                    # Crear oscuridad cerca del espíritu
                    offset_x = random.choice([-80, -60, 60, 80])
                    offset_y = random.choice([-80, -60, 60, 80])
                    darkness_pos = pygame.Vector2(
                        max(50, min(WIDTH - 50, x + offset_x)),
                        max(50, min(HEIGHT - 50, y + offset_y))
                    )
                    
                    darkness = {
                        "pos": darkness_pos,
                        "radius": 40,
                        "active": True,
                        "hovered": False,
                        "spirit_index": i,
                        "dialogue": self.darkness_dialogues[i % len(self.darkness_dialogues)]
                    }
                    self.darknesses.append(darkness)
                    
                    used_positions.append(darkness_pos)
                    break
                
                attempts += 1

    def on_enter(self):
        self.show_dialogue("Daniela", "El Jardín de los Susurros... veo espíritus atrapados en la oscuridad. ¿Debería escucharlos o limpiar las sombras?")
        self.state = "JUGANDO"

    def show_dialogue(self, speaker, text):
        self.current_dialogue = text
        self.current_speaker = speaker
        self.dialogue_timer = 0
        self.can_skip = False
        self.dialogue_cooldown = 0.5

    def handle_event(self, event, game_state):
        if self.state != "JUGANDO":
            # Permitir clic para saltar diálogo inicial
            if self.state == "ENTRADA" and event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self.current_dialogue and self.can_skip:
                    self.current_dialogue = None
                    self.current_speaker = None
                    self.state = "JUGANDO"
                return
            
            # Permitir clic para saltar diálogo final
            if self.state == "FINAL" and event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self.current_dialogue and self.can_skip:
                    self.current_dialogue = None
                    self.current_speaker = None
                    # Comenzar transición inmediatamente
                    self.transition_timer = 2.0
                return
            
            return
        
        # Manejar clic en diálogo
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.can_skip and self.current_dialogue:
                self.current_dialogue = None
                self.current_speaker = None
                self.dialogue_cooldown = 0.5
                return
        
        # Movimiento con clic
        if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            if self.current_dialogue and self.can_skip:
                # Si hay diálogo, el clic es para cerrarlo
                self.current_dialogue = None
                self.current_speaker = None
                self.dialogue_cooldown = 0.5
                return
            
            mouse_pos = pygame.Vector2(event.pos[0], event.pos[1])
            
            # Verificar clic en espíritu
            spirit_clicked = self.handle_spirit_click(mouse_pos, game_state)
            if spirit_clicked:
                return
            
            # Verificar clic en oscuridad
            darkness_clicked = self.handle_darkness_click(mouse_pos, game_state)
            if darkness_clicked:
                return
            
            # Si no clicó en nada interactivo, moverse
            self.daniela_target = mouse_pos
            self.facing_right = mouse_pos.x > self.daniela_pos.x
            self.daniela_state = "caminando"

    def handle_spirit_click(self, mouse_pos, game_state):
        """Maneja clic en espíritus"""
        for i, spirit in enumerate(self.spirits):
            if spirit["active"] and not spirit["listened"]:
                distance_to_spirit = spirit["pos"].distance_to(mouse_pos)
                distance_to_daniela = spirit["pos"].distance_to(self.daniela_pos)
                
                if distance_to_spirit < spirit["radius"] and distance_to_daniela < 200:
                    # Escuchar al espíritu
                    spirit["listened"] = True
                    self.spirits_listened += 1
                    
                    game_state.add_duality("rejection_understanding", 20)
                    self.show_dialogue("Espíritu", spirit["dialogue"])
                    
                    return True
        return False

    def handle_darkness_click(self, mouse_pos, game_state):
        """Maneja clic en oscuridades"""
        for darkness in self.darknesses:
            if darkness["active"]:
                distance_to_darkness = darkness["pos"].distance_to(mouse_pos)
                distance_to_daniela = darkness["pos"].distance_to(self.daniela_pos)
                
                if distance_to_darkness < darkness["radius"] and distance_to_daniela < 200:
                    # Limpiar oscuridad
                    darkness["active"] = False
                    self.darknesses_cleaned += 1
                    
                    # Obtener espíritu asociado
                    spirit_index = darkness["spirit_index"]
                    spirit = self.spirits[spirit_index]
                    
                    if spirit["listened"] and not spirit["cleaned"]:
                        # Limpiar espíritu
                        spirit["cleaned"] = True
                        self.spirits_cleaned += 1
                        game_state.add_duality("rejection_understanding", 15)
                        self.show_dialogue("Daniela", "La oscuridad se disipa... el espíritu recupera su forma.")
                    else:
                        # No escuchó al espíritu - SOLO afecta rechazo/comprensión
                        game_state.add_duality("rejection_understanding", -15)
                        self.show_dialogue("Daniela", darkness["dialogue"])
                    
                    # Verificar si se limpiaron todas las oscuridades
                    if self.darknesses_cleaned >= self.num_spirits:
                        self.end_game(game_state)
                    
                    return True
        return False

    def update(self, dt, game_state):
        if self.dialogue_cooldown > 0:
            self.dialogue_cooldown -= dt
        
        if self.current_dialogue:
            self.dialogue_timer += dt
            if self.dialogue_timer >= 1.0:
                self.can_skip = True
        
        # Actualizar movimiento
        if self.state == "JUGANDO":
            self.update_daniela_movement(dt)
            
            # Actualizar estado basado en cercanía (SOLO CUANDO NO SE MUEVE)
            if self.daniela_state != "caminando":
                self.update_daniela_state()
        
        # Manejar temporizador de transición FINAL
        elif self.state == "FINAL":
            if self.transition_timer > 0:
                self.transition_timer -= dt
                
                if self.transition_timer <= 0:
                    self.go_to_next_scene()
                    return

    def update_daniela_movement(self, dt):
        """Actualiza el movimiento de Daniela"""
        if self.daniela_state == "caminando":
            direction = self.daniela_target - self.daniela_pos
            distance = direction.length()
            
            if distance > 5:
                move_distance = self.daniela_speed * dt
                if move_distance < distance:
                    self.daniela_pos += direction.normalize() * move_distance
                else:
                    self.daniela_pos = self.daniela_target
                    self.daniela_state = "quieta"
            else:
                self.daniela_state = "quieta"
        
        # Si llega al destino, actualizar estado según lo que tenga cerca
        if self.daniela_pos.distance_to(self.daniela_target) <= 5 and self.daniela_state == "caminando":
            self.daniela_state = "quieta"

    def update_daniela_state(self):
        """Actualiza el estado de Daniela basado en lo que tenga cerca SOLO CUANDO ESTÁ QUIETA"""
        # Solo actualizar si está quieta (no caminando)
        if self.daniela_state == "caminando":
            return
        
        # Estado por defecto: quieta
        new_state = "quieta"
        
        # Verificar cercanía a espíritus no escuchados (distancia más pequeña para que sea más preciso)
        for spirit in self.spirits:
            if spirit["active"] and not spirit["listened"]:
                distance = spirit["pos"].distance_to(self.daniela_pos)
                if distance < 100:
                    new_state = "escuchando"
                    break
        
        # Si no encontró espíritu cerca, verificar oscuridades
        if new_state == "quieta":
            for darkness in self.darknesses:
                if darkness["active"]:
                    distance = darkness["pos"].distance_to(self.daniela_pos)
                    if distance < 100:
                        new_state = "asustada"
                        break
        
        # Actualizar estado
        self.daniela_state = new_state

    def end_game(self, game_state):
        """Termina el juego y determina el resultado"""
        self.game_completed = True
        
        # Calcular puntuación de comprensión
        understanding_score = self.game_state.dualities["rejection_understanding"]
        
        # Determinar decisión final basada en comprensión
        if understanding_score >= 50:  # Alta comprensión
            self.decision_made = "CONSERVAR_PODER"
            if self.spirits_listened > 0:
                final_text = f"He escuchado {self.spirits_listened} historias. Mi don puede ayudar a otros."
            else:
                final_text = f"He limpiado las oscuridades. Aunque no conozca sus historias, siento que debo conservar esta habilidad."
            game_state.add_duality("rejection_understanding", 30)
        else:  # Baja comprensión (alta rechazo)
            self.decision_made = "RENUNCIAR_PODER"
            if self.spirits_listened > 0:
                final_text = f"He escuchado sus historias, pero el peso es demasiado. Necesito que esto termine."
            else:
                final_text = f"Las oscuridades están limpias, pero no quiero saber más. Que la tarotista cumpla su trato."
            game_state.add_duality("rejection_understanding", -30)
        
        # Guardar decisión para la siguiente escena
        # Asegurarnos de que game_state tenga un diccionario de flags
        if not hasattr(game_state, 'flags'):
            game_state.flags = {}
        
        game_state.flags["jardin_decision"] = self.decision_made
        game_state.flags["espiritus_escuchados"] = self.spirits_listened
        game_state.flags["oscuridades_limpiadas"] = self.darknesses_cleaned
        game_state.flags["espiritus_limpiados"] = self.spirits_cleaned
        
        # DEBUG: Mostrar lo que se guardó
        print(f"DEBUG: Guardando decisión: {self.decision_made}")
        print(f"DEBUG: Flags guardados: {game_state.flags}")
        
        self.show_dialogue("Daniela", final_text)
        self.state = "FINAL"
        self.transition_timer = 0  # Inicialmente 0, se activa después del diálogo

    def go_to_next_scene(self):
        """Va a la escena correspondiente según la decisión"""
        print("DEBUG: Intentando cambiar a siguiente escena...")
        
        # Obtener la decisión del jugador
        decision = None
        
        # Intentar obtener la decisión guardada
        if hasattr(self.game_state, 'flags') and self.game_state.flags:
            decision = self.game_state.flags.get("jardin_decision")
            print(f"DEBUG: Decisión obtenida de flags: {decision}")
        
        # Si no hay decisión guardada, usar la de esta escena
        if not decision and hasattr(self, 'decision_made'):
            decision = self.decision_made
            print(f"DEBUG: Usando decisión local: {decision}")
        
        # Si aún no hay decisión, usar comprensión como fallback
        if not decision:
            understanding_score = self.game_state.dualities["rejection_understanding"]
            decision = "CONSERVAR_PODER" if understanding_score >= 50 else "RENUNCIAR_PODER"
            print(f"DEBUG: Usando fallback por comprensión: {decision}")
        
        print(f"DEBUG: Decisión final: {decision}")
        
        # Intentar cargar la escena correspondiente
        try:
            if "CONSERVAR" in decision:
                from scenes.tarot_acep import TarotAcepScene
                print("DEBUG: Intentando cargar TarotAcepScene...")
                self.manager.replace(TarotAcepScene(self.manager, self.game_state, self.audio))
            else:
                from scenes.tarot_rechas import TarotRechasScene
                print("DEBUG: Intentando cargar TarotRechasScene...")
                self.manager.replace(TarotRechasScene(self.manager, self.game_state, self.audio))
        except ImportError as e:
            print(f"ERROR: No se pudo cargar la escena siguiente: {e}")
            print(f"ERROR: Asegúrate de que tarot_acep.py y tarot_rechas.py existen en la carpeta scenes/")
            # Fallback al título
            from scenes.title import TitleScene
            self.manager.replace(TitleScene(self.manager))

    def draw(self, screen, game_state):
        # Dibujar fondo
        screen.blit(self.bg, (0, 0))
        
        # Dibujar oscuridades
        for darkness in self.darknesses:
            if darkness["active"] and self.darkness_image:
                darkness_rect = self.darkness_image.get_rect(center=(int(darkness["pos"].x), int(darkness["pos"].y)))
                screen.blit(self.darkness_image, darkness_rect)
        
        # Dibujar espíritus
        for spirit in self.spirits:
            if spirit["active"]:
                # Determinar qué imagen usar
                if spirit["cleaned"] and self.spirit_cleaned_images:
                    img = self.spirit_cleaned_images[spirit["cleaned_image_index"]]
                elif self.spirit_affected_images:
                    img = self.spirit_affected_images[spirit["affected_image_index"]]
                else:
                    continue
                
                if img:
                    img_rect = img.get_rect(center=(int(spirit["pos"].x), int(spirit["pos"].y)))
                    screen.blit(img, img_rect)
        
        # Dibujar Daniela - CORRECCIÓN DE DIRECCIÓN
        current_sprite = self.daniela_sprites.get(self.daniela_state, self.daniela_sprites.get("quieta"))
        if current_sprite:
            # CORRECCIÓN: Voltear sprite cuando mira hacia la izquierda (dirección contraria)
            # Si se mueve hacia la derecha (facing_right=True), la imagen original mira hacia la izquierda
            # Entonces volteamos la imagen cuando facing_right=True para que mire hacia la derecha
            if self.daniela_state == "caminando":
                # Si está caminando, voltear según la dirección
                if self.facing_right:
                    # Si mira hacia la derecha, voltear horizontalmente para que mire a la derecha
                    current_sprite = pygame.transform.flip(current_sprite, True, False)
            elif self.daniela_state in ["asustada", "escuchando"]:
                # Estados especiales no se voltean
                pass
            else:
                # Estados normales, voltear según facing_right
                if self.facing_right:
                    current_sprite = pygame.transform.flip(current_sprite, True, False)
            
            sprite_rect = current_sprite.get_rect(center=(int(self.daniela_pos.x), int(self.daniela_pos.y)))
            screen.blit(current_sprite, sprite_rect)
        else:
            # Fallback si no hay sprites
            pygame.draw.circle(screen, (0, 0, 255), (int(self.daniela_pos.x), int(self.daniela_pos.y)), 30)
        
        # Dibujar estadísticas
        self.stats_display.draw(screen)
        
        # Dibujar diálogo (si hay)
        if self.current_dialogue:
            self.draw_dialogue(screen)
        
        # Dibujar transición final
        if self.state == "FINAL":
            self.draw_final_transition(screen)

    def draw_dialogue(self, screen):
        """Dibuja el cuadro de diálogo"""
        box_width = WIDTH - 100
        box_height = 100
        box_x = 50
        box_y = HEIGHT - box_height - 20
        
        # Fondo del diálogo
        dialogue_bg = pygame.Surface((box_width, box_height), pygame.SRCALPHA)
        dialogue_bg.fill((0, 0, 0, 200))
        screen.blit(dialogue_bg, (box_x, box_y))
        pygame.draw.rect(screen, (255, 255, 255), (box_x, box_y, box_width, box_height), 2)
        
        # Nombre del hablante
        if self.current_speaker:
            color = (0, 200, 255) if self.current_speaker == "Daniela" else (200, 150, 255)
            speaker_text = self.speaker_font.render(self.current_speaker, True, color)
            screen.blit(speaker_text, (box_x + 10, box_y - 30))
        
        # Texto del diálogo
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
        
        # Dibujar máximo 3 líneas
        for i, line in enumerate(lines[:3]):
            text_surf = self.font.render(line, True, (255, 255, 255))
            screen.blit(text_surf, (box_x + 20, box_y + 15 + i * 30))
        
        # Indicador para continuar
        if self.can_skip:
            skip_text = self.font.render("Clic para continuar", True, (200, 200, 200))
            skip_x = box_x + box_width - skip_text.get_width() - 20
            skip_y = box_y + box_height - 30
            screen.blit(skip_text, (skip_x, skip_y))

    def draw_final_transition(self, screen):
        """Dibuja la transición final"""
        if self.transition_timer > 0:
            # Fade out gradual
            alpha = int(255 * (1 - self.transition_timer / 2.0))
            if alpha > 0:
                overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
                overlay.fill((0, 0, 0, alpha))
                screen.blit(overlay, (0, 0))