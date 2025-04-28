import pygame
import random
import time
import webbrowser
from ui_elements import Button, SearchBar, Scrollbar
from state_manager import ButtonStateManager
import ctypes
import win32con
import math
import threading

DEBUG = False  # Set to False to disable debugging output

# === Initialization ===
pygame.init()
pygame.key.set_repeat(300, 50)  # Enable key repeat for the search bar

# Initialize the Pygame mixer
pygame.mixer.init()

# Load the background music
pygame.mixer.music.load("data/sounds/minecraft.mp3")
pygame.mixer.music.set_volume(0.5) # Set the volume (optional, range: 0.0 to 1.0)

# Play the music (loop indefinitely)
pygame.mixer.music.play(-1)

# Load the hover sound effect
hover_sound = pygame.mixer.Sound("data/sounds/select.wav")
hover_sound.set_volume(0.03)  # Set volume (optional)

# Load the search bar extend sound effect
search_extend_sound = pygame.mixer.Sound("data/sounds/searchextend.wav")
search_extend_sound.set_volume(0.5)  # Set volume (optional)

press_btn_sound = pygame.mixer.Sound("data/sounds/press.mp3")
press_btn_sound.set_volume(0.5)  # Set volume (optional)

# Set the window title
pygame.display.set_caption("Fable Mod List")

# Set the window icon
icon = pygame.image.load("data/images/icon.png")
pygame.display.set_icon(icon)

# Initialize the clock for controlling the frame rate
clock = pygame.time.Clock()

# Center of the window
window_width = 578.08
window_height = 867.12
center_x = window_width / 2
WINDOW = pygame.display.set_mode((window_width, window_height), pygame.HWSURFACE | pygame.DOUBLEBUF)
FONT = pygame.font.Font("data/font/minecraft_font.ttf", 24)
BG_COLOR = (30, 30, 30)
SCROLLBAR_BG_COLOR = (50, 50, 50)
scroll_offset = 0
scroll_velocity = 0
scroll_speed = 15
drag_sensitivity = 14
dt = clock.get_time() / 1000.0  # Delta time in seconds

# Load the background image
background_image = pygame.image.load("data/images/background.png").convert()
background_image = pygame.transform.scale(background_image, (WINDOW.get_width(), WINDOW.get_height()))

# Load mod names and mod jar names
def load_mod_data(names_filepath, jars_filepath):
    """
    Load mod names and their corresponding jar file names.

    Args:
        names_filepath (str): Path to the mod names file.
        jars_filepath (str): Path to the mod jar file names.

    Returns:
        list: A list of tuples where each tuple contains (mod_name, mod_jar).
    """
    with open(names_filepath, "r") as names_file, open(jars_filepath, "r") as jars_file:
        mod_names = [line.strip() for line in names_file.readlines()]
        mod_jars = [line.strip() for line in jars_file.readlines()]
        return list(zip(mod_names, mod_jars))  # Pair mod names with their corresponding jar files

# Load mod data
mod_data = load_mod_data("data/mod_names.txt", "data/mod_jar.txt")

# ==FADE CONFIGURATION==
onscreen_top = 196
onscreen_bottom = 867
fade_margin = 90
fade_range = 30

# ==BUTTON CONFIGURATION==
button_width = 350
button_height = 40
button_spacing = 20  # Spacing between buttons
start_y = 166  # Padding from the top of the window

# ==BUTTON CONFIGURATION==
buttons = []
for i, (mod_name, mod_jar) in enumerate(mod_data):
    # Calculate button position
    button_x = center_x - (button_width / 2)  # Center horizontally
    button_y = start_y + i * (button_height + button_spacing)  # Stack vertically

    # Create the button
    button = Button(
        mod_name,
        (button_x, button_y, button_width, button_height),  # Button position and size
        (70, 70, 70),  # Default color
        FONT,  # Font object
        (255, 255, 255),  # Text color
        "data/font/minecraft_font.ttf",  # Font path
        block_type=random.choice(["dirt", "grass", "cobblestone"]),  # Random block type
        hover_sound=hover_sound,  # Sound effect for hover
    )
    button.render_text_to_fit()
    buttons.append(button)


#==SEARCH BAR CONFIGURATION==
search_bar_width = 50  # Desired width of the search bar
search_bar_height = 40  # Desired height of the search bar
search_bar_y = 35       # Y position of the search bar (padding from the top)

# Calculate the X position to center the search bar
search_bar_x = 70

# Initialize the search bar
search_bar = SearchBar(
    (search_bar_x, search_bar_y, search_bar_width, search_bar_height),  # Position and size
    FONT,  # Font object
    "data/images/magnifyicon.png",  # Path to the magnifying glass icon
    extend_sound=search_extend_sound,  # Sound effect for search bar extension
)

#== SCROLLBAR CONFIGURATION ==
scrollbar = Scrollbar(
    (880, 70, 20, 630),
    total_content_height=len(buttons) * 60,  # 40px button height + 20px spacing
    visible_height=630
)

state_manager = ButtonStateManager(buttons)



# Initialize search bar state
search_query = ""
cursor_position = 0
selection_start = 0
selection_end = 0
undo_stack = []
search_active = False  # Search bar is not active by default
cursor_visible = False  # Cursor is hidden until search bar is focused
is_dragging = False  # Flag to check if the scrollbar is being dragged
search_active = False  # Search bar is expanded or not
search_animating = False  # Is animation running
search_width = 50  # Start small
search_target_width = 800  # Full expanded width
search_expand_speed = 10  # Base speed of expansion

# Load and resize the custom cursor image
cursor_image = pygame.image.load("data/images/custom_cursor.png").convert_alpha()
cursor_image = pygame.transform.scale(cursor_image, (24, 24))  # Resize to 24x24 pixels

# Hide the default cursor
pygame.mouse.set_visible(False)

# Generate particles for the twinkling effect
def generate_particles(num_particles, width, height):
    particles = []
    for _ in range(num_particles):
        direction = random.choice([-1, 1])  # -1 for right-to-left, 1 for left-to-right
        speed = random.uniform(0.1, 0.5) * direction  # Slow horizontal speed
        size = random.uniform(1, 3)  # Size variation for depth illusion
        particles.append({
            "x": random.uniform(0, width) if direction == 1 else random.uniform(-50, 0),  # Start slightly off-screen
            "y": random.uniform(0, height),  # Random vertical position
            "vx": speed,  # Horizontal speed
            "vy": 0,  # No vertical drift
            "size": size,
            "brightness": random.randint(150, 255),
            "direction": direction,
            "lifetime": random.uniform(5.0, 10.0),  # Lifetime in seconds
            "age": 0.0,
            "alpha": 255,
            "float_phase": random.uniform(0, math.pi * 2)  # For smoother up/down sinusoidal bobbing
        })
    return particles


def update_and_draw_particles(particles, surface, width, height, dt):
    for particle in particles:
        # Update age
        particle["age"] += dt

        # Respawn particle if its lifetime ends or it moves off-screen
        if particle["age"] >= particle["lifetime"] or particle["x"] < -50 or particle["x"] > width + 50:
            particle["x"] = random.uniform(-50, 0) if particle["direction"] == 1 else random.uniform(width, width + 50)
            particle["y"] = random.uniform(0, height)
            particle["vx"] = random.uniform(0.1, 0.5) * particle["direction"]  # Slow horizontal speed
            particle["size"] = random.uniform(1, 3)
            particle["brightness"] = random.randint(150, 255)
            particle["lifetime"] = random.uniform(5.0, 10.0)
            particle["age"] = 0.0
            particle["float_phase"] = random.uniform(0, math.pi * 2)

        # Bobbing up and down using a sine wave
        bobbing = math.sin(particle["float_phase"] + particle["age"] * 2.0) * 0.5
        particle["y"] += bobbing

        # Move particle horizontally
        particle["x"] += particle["vx"]

        # Calculate alpha based on lifetime
        life_ratio = 1.0 - (particle["age"] / particle["lifetime"])
        particle["alpha"] = int(255 * life_ratio)

        # Clamp alpha
        particle["alpha"] = max(0, min(255, particle["alpha"]))

        # Draw particle
        color = (particle["brightness"], particle["brightness"], particle["brightness"], particle["alpha"])
        particle_surface = pygame.Surface((particle["size"] * 2, particle["size"] * 2), pygame.SRCALPHA)
        pygame.draw.circle(particle_surface, color, (int(particle["size"]), int(particle["size"])), int(particle["size"]))
        surface.blit(particle_surface, (particle["x"], particle["y"]))

particles = generate_particles(100, 900, 700)

def bring_window_to_foreground():
    hwnd = pygame.display.get_wm_info()['window']

    # Get the thread ID of the current foreground window
    fg_window = ctypes.windll.user32.GetForegroundWindow()
    fg_thread_id = ctypes.windll.user32.GetWindowThreadProcessId(fg_window, None)

    # Get the thread ID of the Pygame window
    current_thread_id = ctypes.windll.kernel32.GetCurrentThreadId()

    # Attach the input threads
    ctypes.windll.user32.AttachThreadInput(fg_thread_id, current_thread_id, True)

    # Bring the Pygame window to the foreground
    ctypes.windll.user32.SetForegroundWindow(hwnd)

    # Detach the input threads
    ctypes.windll.user32.AttachThreadInput(fg_thread_id, current_thread_id, False)

    # Restore the window if it is minimized
    ctypes.windll.user32.ShowWindow(hwnd, win32con.SW_RESTORE)

# Update button positions and fade them in/out
def update_button_positions_and_fade(buttons, scroll_offset):
    for button in buttons:
        # Always calculate based on true position
        button_top = button.target_y - scroll_offset
        button_bottom = button_top + button.rect.height

        # --- Calculate onscreen alpha (fade at edges) ---
        if button_bottom < onscreen_top - fade_margin or button_top > onscreen_bottom + fade_margin:
            button.onscreen_alpha = 0
        elif button_bottom < onscreen_top:
            distance = onscreen_top - button_bottom
            button.onscreen_alpha = max(0, 255 - int(255 * (distance / fade_range)))
        elif button_top > onscreen_bottom:
            distance = button_top - onscreen_bottom
            button.onscreen_alpha = max(0, 255 - int(255 * (distance / fade_range)))
        else:
            button.onscreen_alpha = 255

        # --- Smoothly update search_alpha based on match ---
        if button.is_match:
            if button.search_alpha < 255:
                button.search_alpha += 15
                button.search_alpha = min(255, button.search_alpha)
        else:
            if button.search_alpha > 0:
                button.search_alpha -= 15
                button.search_alpha = max(0, button.search_alpha)


        # --- Calculate final alpha ---
        button.alpha = min(button.search_alpha, button.onscreen_alpha)

        # --- Move smoothly toward target_y ---
        dy = button.target_y - button.rect.y
        if abs(dy) > 1:
            button.rect.y += dy * 0.2
        else:
            button.rect.y = button.target_y

        # --- Set visibility based on final alpha ---
        button.visible = button.alpha > 0
   
def update_target_positions(buttons, search_query, button_spacing):
    y_position = start_y  # Starting y-position for buttons
    for button in buttons:
        previous_visible = button.visible  # Track the previous visibility state
        button.is_match = matches_query(button.text, search_query)
        if button.is_match:
            button.target_y = y_position
            y_position += button.rect.height + button_spacing


        # Print only if the visibility state changes
        if DEBUG and button.visible != previous_visible:
            print(f"Button '{button.text}': visible={button.visible}, target_y={button.target_y}, rect.y={button.rect.y}")

def matches_query(button_text, search_query):
    if not search_query.strip():
        return True  # Show all buttons if the query is empty

    button_text = button_text.lower()
    search_query = search_query.lower()
    i = 0
    for char in button_text:
        if i < len(search_query) and char == search_query[i]:
            i += 1

    # Debugging output
    if DEBUG: print(f"Matching '{search_query}' with '{button_text}': {'Matched' if i == len(search_query) else 'Not Matched'}")
    return i == len(search_query)

def open_url(url):
    webbrowser.open(url)
    time.sleep(0.3)  # Delay to ensure the thread is ready
    bring_window_to_foreground()

# === Main Game Loop ===
running = True
search_query = ""
previous_search_query = ""
cursor_position = 0
while running:
    # Draw the background image
    WINDOW.blit(background_image, (0, 0))
    mouse_pos = pygame.mouse.get_pos()

    # Update hover state
    state_manager.update_hover_state(mouse_pos, scroll_offset)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        elif event.type == pygame.WINDOWFOCUSLOST:
            # print("Window lost focus")
            bring_window_to_foreground()

        # Handle mouse button down events
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # Left mouse button
                state_manager.handle_mouse_down()
                if search_bar.icon_rect.collidepoint(event.pos):  # Check if clicked on magnifying glass
                    search_bar.toggle()  # Toggle the search bar state

                if scrollbar.thumb_rect.collidepoint(mouse_pos):
                    is_dragging = True
                    drag_offset = mouse_pos[1] - scrollbar.thumb_rect.y
                elif search_bar.rect.collidepoint(mouse_pos):
                    search_active = True
                    cursor_visible = True
                    pygame.mouse.set_visible(False)  # Ensure system cursor is hidden
                else:
                    search_active = False
                    cursor_visible = False
                    pygame.mouse.set_visible(False)  # Ensure system cursor is hidden elsewhere

                # Check if a button is clicked
                for button in buttons:
                    if not button.visible:
                        continue  # Ignore non-matching buttons

                    adjusted_rect = button.rect.move(0, -scroll_offset)
                    if adjusted_rect.collidepoint(mouse_pos):
                        # Find correct mod_jar based on button.text
                        for mod_name, mod_jar in mod_data:
                            if mod_name == button.text:
                                press_btn_sound.play()
                                google_search_url = f"https://www.google.com/search?q={mod_jar.replace(' ', '+')}"
                                threading.Thread(target=open_url, args=(google_search_url,), daemon=True).start()
                                # time.sleep(0.5)
                                break
                        break

        # Handle mouse button up events
        elif event.type == pygame.MOUSEBUTTONUP:
            is_dragging = False
            if event.button == 1:
                state_manager.handle_mouse_up()

        # Handle mouse wheel scrolling
        elif event.type == pygame.MOUSEWHEEL:
            if event.y > 0:  # Scroll up
                scroll_velocity -= scroll_speed
            elif event.y < 0:  # Scroll down
                scroll_velocity += scroll_speed
        
            # Clamp scroll offset
            max_scroll = scrollbar.total_content_height - scrollbar.visible_height
            scroll_offset = max(0, min(scroll_offset, max_scroll))

        # Handle mouse motion (dragging the scrollbar)
        elif event.type == pygame.MOUSEMOTION and is_dragging:
            # Move the thumb based on mouse movement
            new_thumb_y = mouse_pos[1] - drag_offset

            # Clamp thumb inside scrollbar area
            thumb_height = scrollbar.thumb_rect.height
            new_thumb_y = max(scrollbar.rect.y, min(scrollbar.rect.y + scrollbar.rect.height - thumb_height, new_thumb_y))

            # Calculate the scroll offset based on thumb position
            scroll_percentage = (new_thumb_y - scrollbar.rect.y) / (scrollbar.rect.height - thumb_height)
            max_scroll = scrollbar.total_content_height - scrollbar.visible_height
            scroll_offset = scroll_percentage * max_scroll
            
        # Handle key presses for the search bar
        elif event.type == pygame.KEYDOWN and search_active:
            ctrl = pygame.key.get_mods() & pygame.KMOD_CTRL
            shift = pygame.key.get_mods() & pygame.KMOD_SHIFT

            if ctrl and event.key == pygame.K_a:
                # Ctrl+A select all
                selection_start = 0
                selection_end = len(search_query)
                cursor_position = len(search_query)
            elif ctrl and event.key == pygame.K_z:
                # Ctrl+Z undo
                if undo_stack:
                    search_query, cursor_position = undo_stack.pop()
                    selection_start = selection_end = cursor_position
            elif shift and event.key == pygame.K_LEFT:
                # Shift + Left Arrow: Extend selection to the left
                if cursor_position > 0:
                    cursor_position -= 1
                    selection_end = cursor_position
            elif shift and event.key == pygame.K_RIGHT:
                # Shift + Right Arrow: Extend selection to the right
                if cursor_position < len(search_query):
                    cursor_position += 1
                    selection_end = cursor_position
            else:
                if event.key == pygame.K_BACKSPACE:
                    if selection_start != selection_end:
                        # Delete selection
                        start, end = sorted([selection_start, selection_end])
                        undo_stack.append((search_query, cursor_position))
                        search_query = search_query[:start] + search_query[end:]
                        cursor_position = start
                        selection_start = selection_end = cursor_position
                    elif cursor_position > 0:
                        # Delete character before cursor
                        undo_stack.append((search_query, cursor_position))
                        search_query = search_query[:cursor_position - 1] + search_query[cursor_position:]
                        cursor_position -= 1
                        selection_start = selection_end = cursor_position
                elif event.key == pygame.K_LEFT:
                    if cursor_position > 0:
                        cursor_position -= 1
                        selection_start = selection_end = cursor_position
                elif event.key == pygame.K_RIGHT:
                    if cursor_position < len(search_query):
                        cursor_position += 1
                        selection_start = selection_end = cursor_position
                else:
                    if selection_start != selection_end:
                        # Replace selected text
                        start, end = sorted([selection_start, selection_end])
                        undo_stack.append((search_query, cursor_position))
                        search_query = search_query[:start] + event.unicode + search_query[end:]
                        cursor_position = start + 1
                        selection_start = selection_end = cursor_position
                    else:
                        # Insert character at cursor position
                        undo_stack.append((search_query, cursor_position))
                        search_query = search_query[:cursor_position] + event.unicode + search_query[cursor_position:]
                        cursor_position += 1
                        selection_start = selection_end = cursor_position

            # Reset scroll position to the top when the search query changes
            scroll_offset = 0

            # Update target positions and fade logic
            update_target_positions(buttons, search_query, button_spacing)
            update_button_positions_and_fade(buttons, scroll_offset)

    # Track if the search query changed
    if search_query != previous_search_query:
        previous_search_query = search_query
        if DEBUG: print(f"Search query changed to: '{search_query}'")
        update_target_positions(buttons, search_query, button_spacing)


    # Update search bar animation
    search_bar.update()

    # Set a clipping rectangle to restrict rendering to below the search bar
    update_button_positions_and_fade(buttons, scroll_offset)

    # Apply inertia/friction to scrolling
    if abs(scroll_velocity) > 0.1:
        scroll_offset += scroll_velocity
        scroll_velocity *= 0.9  # Gradual deceleration for smooth scrolling
        max_scroll = scrollbar.total_content_height - scrollbar.visible_height
        scroll_offset = max(0, min(scroll_offset, max_scroll))
    else:
        scroll_velocity = 0

    max_scroll = scrollbar.total_content_height - scrollbar.visible_height
    scroll_offset = max(0, min(scroll_offset, max_scroll))

    # Debug scroll offset
    state_manager.debug_scroll(scroll_offset)

    # Measure FPS
    fps = clock.get_fps()
    pygame.display.set_caption(f"Fable Mod List - FPS: {int(fps)}")

    # Draw the background image
    WINDOW.blit(background_image, (0, 0))

    # Rendering logic
    update_and_draw_particles(particles, WINDOW, 900, 700, dt)
    search_bar.draw(WINDOW, search_query, cursor_position)
    scrollbar.draw(WINDOW, scroll_offset)

    
    # Render the buttons
    for button in buttons:
        is_hovered = (state_manager.hovered_button == button)
        button.draw(WINDOW, hovered=is_hovered, scroll_offset=scroll_offset)

    # Reset the clipping rectangle
    WINDOW.set_clip(None)
    
    # Render the custom cursor on top of everything
    cursor_offset = (cursor_image.get_width() // 2, cursor_image.get_height() // 2)
    WINDOW.blit(cursor_image, (mouse_pos[0] - cursor_offset[0], mouse_pos[1] - cursor_offset[1]))
    
    pygame.display.flip()
    clock.tick(230)

pygame.quit()
