import pygame
import random

class Button:
    def __init__(self, text, rect, color, font, text_color, font_path, block_type="dirt",hover_sound=None):
        self.text = text
        self.rect = pygame.Rect(rect)
        self.color = color
        self.font = font
        self.text_color = text_color
        self.font_path = font_path
        self.block_type = block_type
        self.visible = True  # Whether the button is logically visible
        self.texture = self.generate_block_texture(self.rect.size, self.block_type)  # Cache texture
        self.hovered = False  # Track whether the button is being hovered over
        self.hover_sound = hover_sound  # Sound to play on hover

        # Cache rendered text and its dimensions
        self.text_surface = self.font.render(self.text, True, self.text_color)
        self.text_rect = self.text_surface.get_rect(center=self.rect.center)

        # Initialize target_y for smooth animations
        self.target_y = self.rect.y

        # Initialize alpha for fade-in/out effects
        self.alpha = 255  # Fully opaque by default
        self.search_alpha = 255  # 255 if matches search, 0 if not
        self.is_match = True
        self.onscreen_alpha = 255  # 255 if onscreen, 0 if outside

    def render_text_to_fit(self):
        """
        Shrink text if it's too big to fit inside the button width.
        """
        max_width = self.rect.width - 20  # Leave some margin
        font_size = self.font.get_height()
        font_path = self.font_path

        # Start with existing font
        current_font = self.font
        temp_surface = current_font.render(self.text, True, self.text_color)

        while font_size >= 10 and temp_surface.get_width() > max_width:
            font_size -= 1
            current_font = pygame.font.Font(font_path, font_size)
            temp_surface = current_font.render(self.text, True, self.text_color)

        self.font = current_font
        self.text_surface = temp_surface
        self.text_rect = self.text_surface.get_rect(center=self.rect.center)

    def generate_block_texture(self, size, block_type):
            """
            Generate a procedural texture for the button based on the block type.

            Args:
                size (tuple): The size of the button (width, height).
                block_type (str): The type of block texture to generate ("dirt", "grass", "cobblestone").

            Returns:
                pygame.Surface: A surface with the generated texture.
            """
            surface = pygame.Surface(size)
            width, height = size

            # Define color palettes for different block types
            if block_type == "dirt":
                colors = [(134, 96, 67), (115, 76, 50), (155, 110, 75)]  # Dirt shades
            elif block_type == "grass":
                colors = [(95, 159, 53), (80, 140, 45), (110, 180, 65)]  # Grass shades
            elif block_type == "cobblestone":
                colors = [(120, 120, 120), (100, 100, 100), (140, 140, 140)]  # Cobblestone shades
            else:
                colors = [(200, 200, 200)]  # Default to light gray

            # Fill the surface with a pixelated pattern
            for x in range(0, width, 4):  # Small 4x4 pixel blocks
                for y in range(0, height, 4):
                    color = random.choice(colors)
                    pygame.draw.rect(surface, color, (x, y, 4, 4))

            return surface

    def is_clicked(self, mouse_pos, scroll_offset):
        """
        Check if the button is clicked based on the mouse position and scroll offset.

        Args:
            mouse_pos (tuple): The current mouse position (x, y).
            scroll_offset (int): The current scroll offset.

        Returns:
            bool: True if the button is clicked, False otherwise.
        """
        # Adjust the button's rect position based on the scroll offset
        adjusted_rect = self.rect.move(0, -scroll_offset)
        return adjusted_rect.collidepoint(mouse_pos)
    
    def draw(self, window, hovered=False, scroll_offset=0):
        if not self.visible:
            return

        # --- NEW --- Update alpha for this frame
        self.alpha = min(self.search_alpha, self.onscreen_alpha)
        
        # Adjust position based on scroll
        adjusted_rect = self.rect.move(0, -scroll_offset)

        visible_margin = 100
        if adjusted_rect.bottom < (70 - visible_margin) or adjusted_rect.top > (700 + visible_margin):
            return

        # Create a surface for the button
        button_surface = pygame.Surface(self.rect.size, pygame.SRCALPHA)

        # Draw the background texture first (no alpha yet)
        button_surface.blit(self.texture, (0, 0))

        # Create a rounded mask
        mask_surface = pygame.Surface(self.rect.size, pygame.SRCALPHA)
        pygame.draw.rect(mask_surface, (255, 255, 255, 255), mask_surface.get_rect(), border_radius=8)

        # Apply the rounded mask
        button_surface.blit(mask_surface, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)

        # NOW apply alpha fade to the entire button surface
        faded_surface = button_surface.copy()
        faded_surface.set_alpha(self.alpha)

        # Blit the faded button onto the window
        window.blit(faded_surface, adjusted_rect.topleft)

        # Draw hover effect if needed
        if hovered:
            hover_surface = pygame.Surface(adjusted_rect.size, pygame.SRCALPHA)
            pygame.draw.rect(hover_surface, (255, 255, 255, 50), hover_surface.get_rect(), border_radius=8)
            window.blit(hover_surface, adjusted_rect.topleft)

        # Draw text (also faded with the button)
        if self.alpha > 0:
            text_surface_with_alpha = self.text_surface.copy()
            text_surface_with_alpha.set_alpha(self.alpha)
            text_rect = text_surface_with_alpha.get_rect(center=adjusted_rect.center)
            window.blit(text_surface_with_alpha, text_rect)

class SearchBar:
    def __init__(self, rect, font, icon_path, extend_sound=None):
        self.rect = pygame.Rect(rect)
        self.font = font

        # Animation properties
        self.target_width = self.rect.width  # Target width for animation
        self.animation_speed = 10  # Base speed of expansion/contraction
        self.easing_factor = 0.2  # Easing factor for smooth animation

        # Icon properties
        self.icon = pygame.image.load(icon_path)
        self.icon = pygame.transform.scale(self.icon, (30, 30))  # Scale the icon
        self.icon_rect = pygame.Rect(self.rect.x + 10, self.rect.centery - 16, 32, 32)

        # State properties
        self.expanded = False  # Whether the search bar is expanded
        self.cursor_visible = False  # Cursor visibility for blinking
        self.cursor_timer = 0

        # Text properties
        self.text_offset = 0  # Horizontal offset for scrolling text
        self.padding = 10  # Padding between text and edges

        # Sound assignment
        self.extend_sound = extend_sound  # Sound to play when extending

    def toggle(self):
        """
        Toggle the search bar between expanded and collapsed states.
        """
        self.expanded = not self.expanded
        if self.expanded:
            self.target_width = 438
            self.extend_sound.play()
        else:
            self.target_width = 50  # Expand to 600px or collapse to 50px


    def update(self):
        """
        Update the search bar's width for smooth animation.
        """
        # Smoothly animate the width toward the target width
        width_difference = self.target_width - self.rect.width
        if abs(width_difference) > 1:  # Only animate if there's a significant difference
            self.rect.width += width_difference * self.easing_factor
        else:
            self.rect.width = self.target_width  # Snap to target width when close enough

        # Update the icon position to stay aligned
        self.icon_rect.x = self.rect.x + self.padding

    def draw(self, window, search_query, cursor_position):
        """
        Draw the search bar and its contents.

        Args:
            window (pygame.Surface): The surface to draw on.
            search_query (str): The current search query.
            cursor_position (int): The position of the cursor in the query.
        """
        # Draw the search bar background
        if self.rect.width >= 50:
            search_bg = pygame.Surface((self.rect.width, self.rect.height), pygame.SRCALPHA)
            pygame.draw.rect(search_bg, (50, 50, 50, 72), search_bg.get_rect(), border_radius=8)
            window.blit(search_bg, (self.rect.x, self.rect.y))

            # Blit the semi-transparent background onto the main window
            window.blit(search_bg, (self.rect.x, self.rect.y))
        # Always draw the magnifying glass icon
        icon_x = self.rect.x + self.padding
        icon_y = self.rect.y + (self.rect.height - self.icon.get_height()) // 2
        window.blit(self.icon, (icon_x, icon_y))

        # Only draw the text if the search bar is expanded enough
        if self.rect.width > 80:
            # Calculate text start position
            text_x = self.icon_rect.right + self.padding
            text_y = self.rect.y + (self.rect.height - self.font.get_height()) // 2

            # Calculate the visible text area
            visible_width = self.rect.width - (self.icon_rect.width + self.padding * 3)
            text_surface = self.font.render(search_query, True, (255, 255, 255))

            # Handle text scrolling if it's too long
            text_width = text_surface.get_width()
            if text_width > visible_width:
                # Scroll the text to keep the cursor visible
                cursor_offset = self.font.size(search_query[:cursor_position])[0]
                if cursor_offset - self.text_offset > visible_width:
                    self.text_offset = cursor_offset - visible_width
                elif cursor_offset < self.text_offset:
                    self.text_offset = cursor_offset

                # Clip the text to the visible area
                text_surface = text_surface.subsurface((self.text_offset, 0, visible_width, text_surface.get_height()))
            else:
                self.text_offset = 0  # Reset scrolling if text fits

            # Draw the text
            window.blit(text_surface, (text_x, text_y))

            # Draw blinking cursor
            if self.cursor_visible:
                pre_cursor_width = self.font.size(search_query[:cursor_position])[0] - self.text_offset
                cursor_x = text_x + pre_cursor_width
                pygame.draw.line(
                    window, (255, 255, 255),
                    (cursor_x, text_y),
                    (cursor_x, text_y + text_surface.get_height()), 2
                )

class Scrollbar:
    def __init__(self, rect, total_content_height, visible_height):
        """
        Initialize the scrollbar.

        Args:
            rect (tuple): The rectangle defining the position and size of the scrollbar.
            total_content_height (int): The total height of the scrollable content.
            visible_height (int): The height of the visible area.
        """
        self.rect = pygame.Rect(rect)
        self.total_content_height = total_content_height
        self.visible_height = visible_height
        self.thumb_rect = pygame.Rect(self.rect.x, self.rect.y, self.rect.width, self.rect.height)

    def draw(self, window, scroll_offset):
        pygame.draw.rect(window, (100, 100, 100), self.rect)  # Background bar

        # Calculate thumb height
        thumb_height = max(40, self.visible_height / self.total_content_height * self.rect.height)
        self.thumb_rect.height = thumb_height

        max_scroll = self.total_content_height - self.visible_height

        if max_scroll > 0:
            scroll_percentage = scroll_offset / max_scroll
            self.thumb_rect.y = self.rect.y + scroll_percentage * (self.rect.height - thumb_height)
        else:
            self.thumb_rect.y = self.rect.y

        # Draw the thumb
        pygame.draw.rect(window, (200, 200, 200), self.thumb_rect)
