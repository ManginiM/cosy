import pygame
from settings import PALETTE

class StatsDisplay:
    """Muestra las estadísticas del personaje como barras de dualidad"""
    def __init__(self, game_state, position=(20, 20)):
        self.game_state = game_state
        self.position = position
        self.visible = True
        self.font = pygame.font.Font(None, 20)
        self.small_font = pygame.font.Font(None, 16)
        
        # Colores para las dualidades
        self.negative_color = (220, 80, 80)    # Rojo para lado negativo (pánico, rechazo)
        self.positive_color = (80, 180, 80)    # Verde para lado positivo (autocontrol, comprensión)
        self.neutral_color = (200, 200, 200)   # Gris para fondo
        self.intelligence_color = (200, 180, 80) # Amarillo para inteligencia

    def draw(self, surf):
        if not self.visible:
            return

        x, y = self.position
        bar_width = 200
        bar_height = 8
        marker_size = 12
        
        # Título
        title = self.font.render("ESTADO MENTAL", True, PALETTE["text"])
        surf.blit(title, (x, y))
        y += 30

        # Dualidad 1: Pánico vs Autocontrol
        duality1 = self.game_state.get_duality("panic_selfcontrol")
        self._draw_duality_bar(surf, x, y, "Pánico", "Autocontrol", duality1, bar_width, bar_height, marker_size)
        y += 40

        # Dualidad 2: Rechazo vs Comprensión
        duality2 = self.game_state.get_duality("rejection_understanding")
        self._draw_duality_bar(surf, x, y, "Rechazo", "Comprensión", duality2, bar_width, bar_height, marker_size)
        y += 40

        # Inteligencia (barra normal)
        intelligence = self.game_state.get_stat("intelligence")
        self._draw_single_bar(surf, x, y, "Inteligencia", intelligence, bar_width, bar_height)
        y += 30

    def _draw_duality_bar(self, surf, x, y, label_neg, label_pos, value, width, height, marker_size):
        # Dibujar etiquetas
        label_neg_surf = self.small_font.render(label_neg, True, PALETTE["text"])
        label_pos_surf = self.small_font.render(label_pos, True, PALETTE["text"])
        
        surf.blit(label_neg_surf, (x, y))
        surf.blit(label_pos_surf, (x + width - label_pos_surf.get_width(), y))
        
        y += 20

        # Dibujar barra de fondo
        bar_rect = pygame.Rect(x, y, width, height)
        pygame.draw.rect(surf, self.neutral_color, bar_rect, border_radius=3)
        
        # Dibujar marcador
        marker_pos = x + (value + 100) / 200 * width
        marker_rect = pygame.Rect(marker_pos - marker_size//2, y - marker_size//4, marker_size, marker_size)
        
        # Color del marcador según la tendencia
        marker_color = self.negative_color if value < 0 else self.positive_color
        pygame.draw.circle(surf, marker_color, (int(marker_pos), y + height//2), marker_size//2)
        pygame.draw.circle(surf, (0, 0, 0), (int(marker_pos), y + height//2), marker_size//2, 1)

    def _draw_single_bar(self, surf, x, y, label, value, width, height):
        # Dibujar etiqueta
        label_surf = self.small_font.render(label, True, PALETTE["text"])
        surf.blit(label_surf, (x, y))
        
        # Barra de fondo
        bar_rect = pygame.Rect(x, y + 20, width, height)
        pygame.draw.rect(surf, self.neutral_color, bar_rect, border_radius=3)
        
        # Barra de valor
        fill_width = int((value / 100) * width)
        if fill_width > 0:
            fill_rect = pygame.Rect(x, y + 20, fill_width, height)
            pygame.draw.rect(surf, self.intelligence_color, fill_rect, border_radius=3)
        
        # Texto del valor
        value_text = self.small_font.render(f"{value}/100", True, PALETTE["text"])
        surf.blit(value_text, (x + width + 5, y + 18))

class Button:
    # ... (el código existente de Button se mantiene igual)
    def __init__(self, rect, text, font, on_click):
        self.rect = pygame.Rect(rect)
        self.text = text
        self.font = font
        self.on_click = on_click
        self.hover = False
        self.pressed = False
        self.skin = None
        try:
            img = pygame.image.load("assets/ui_button.png").convert_alpha()
            self.skin = pygame.transform.smoothscale(img, (self.rect.w, self.rect.h))
        except Exception:
            self.skin = None

    def handle_event(self, event, audio=None):
        if event.type == pygame.MOUSEMOTION:
            self.hover = self.rect.collidepoint(event.pos)

        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                self.pressed = True

        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            if self.pressed and self.rect.collidepoint(event.pos):
                if audio:
                    audio.play_click()
                if self.on_click:
                    self.on_click()
            self.pressed = False

    def draw(self, surf):
        if self.skin:
            surf.blit(self.skin, self.rect.topleft)
        else:
            color = PALETTE["accent2"] if self.hover else PALETTE["accent"]
            pygame.draw.rect(surf, color, self.rect, border_radius=14)
            pygame.draw.rect(surf, PALETTE["shadow"], self.rect, width=2, border_radius=14)
        txt = self.font.render(self.text, True, (255, 255, 255))
        txtr = txt.get_rect(center=self.rect.center)
        surf.blit(txt, txtr)