class ButtonStateManager:
    def __init__(self, buttons, debug_mode=False):
        self.buttons = buttons
        self.debug_mode = debug_mode  # Store the debug mode state
        self.hovered_button = None
        self.mouse_down_on = None
        self.last_hovered_button = None
        self.last_clicked_button = None

    def debug_scroll(self, scroll_offset):
        """
        Debug scrolling behavior by logging changes in the scroll offset.

        Args:
            scroll_offset (int): The current scroll offset.
        """
        if self.debug_mode:  # Use the instance's debug_mode attribute
            print(f"Scroll offset: {scroll_offset}")

    def update_hover_state(self, mouse_pos, scroll_offset):
        """
        Update the hover state of buttons based on the mouse position.

        Args:
            mouse_pos (tuple): The current mouse position.
            scroll_offset (int): The current scroll offset.
        """
        self.hovered_button = None
        for button in self.buttons:
            if button.is_clicked(mouse_pos, scroll_offset):
                self.hovered_button = button
                break

        # Detect hover state changes
        if self.hovered_button != self.last_hovered_button:
            if self.hovered_button:
                # Play hover sound when a new button is hovered
                if hasattr(self.hovered_button, "hover_sound") and self.hovered_button.hover_sound:
                    self.hovered_button.hover_sound.play()

            if self.debug_mode and self.hovered_button:
                print(f"Hovered over: {self.hovered_button.text}")
            self.last_hovered_button = self.hovered_button

    def handle_mouse_down(self):
        """
        Handle mouse down events and track the button being clicked.
        """
        if self.hovered_button:
            self.mouse_down_on = self.hovered_button

    def handle_mouse_up(self):
        """
        Handle mouse up events and trigger actions if a button is clicked.
        """
        if self.mouse_down_on and self.mouse_down_on == self.hovered_button:
            if self.debug_mode and self.mouse_down_on != self.last_clicked_button:
                print(f"Clicked on: {self.mouse_down_on.text}")
                self.last_clicked_button = self.mouse_down_on
        self.mouse_down_on = None