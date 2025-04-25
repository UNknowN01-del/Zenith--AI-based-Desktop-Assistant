import tkinter as tk
from tkinter import ttk
import keyboard
import threading
from datetime import datetime
import sys
import os
from PIL import Image, ImageTk, ImageDraw
import math
import colorsys

class ModernFloatingAssistant:
    def __init__(self, root):
        self.root = root
        self.root.title("AI Assistant")
        
        # Make window floating and always on top
        self.root.attributes('-topmost', True, '-alpha', 0.95)  # Slight transparency
        self.root.overrideredirect(True)
        
        # Configure the window
        self.width = 300
        self.height = 80
        self.corner_radius = 20
        
        # Colors
        self.bg_color = '#1E1E2E'
        self.accent_color = '#89B4FA'
        self.text_color = '#CDD6F4'
        self.highlight_color = '#F5C2E7'
        
        # Position window in bottom right corner
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()
        x = screen_width - self.width - 20
        y = screen_height - self.height - 40
        self.root.geometry(f'{self.width}x{self.height}+{x}+{y}')
        
        # Create rounded background
        self.create_rounded_background()
        
        # Create main container with transparency
        self.container = tk.Frame(root, bg=self.bg_color)
        self.container.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)
        
        # Create status display with gradient
        self.status_frame = tk.Frame(self.container, bg=self.bg_color)
        self.status_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Microphone icon with pulse animation
        self.mic_canvas = tk.Canvas(
            self.status_frame,
            width=30,
            height=30,
            bg=self.bg_color,
            highlightthickness=0
        )
        self.mic_canvas.pack(side=tk.LEFT, padx=(5, 10))
        self.create_mic_icon()
        
        # Status text with gradient effect
        self.status_var = tk.StringVar(value="Hold 'P' to speak")
        self.status_label = tk.Label(
            self.status_frame,
            textvariable=self.status_var,
            font=('Segoe UI', 10),
            bg=self.bg_color,
            fg=self.text_color
        )
        self.status_label.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Control buttons
        self.button_frame = tk.Frame(self.status_frame, bg=self.bg_color)
        self.button_frame.pack(side=tk.RIGHT)
        
        # Minimize button
        self.min_button = self.create_button("—", self.minimize)
        self.min_button.pack(side=tk.LEFT, padx=2)
        
        # Close button
        self.close_button = self.create_button("×", self.close)
        self.close_button.pack(side=tk.LEFT, padx=2)
        
        # Add drag functionality
        self.status_frame.bind('<Button-1>', self.start_drag)
        self.status_frame.bind('<B1-Motion>', self.on_drag)
        
        # Initialize variables
        self.speak_command = None
        self.stop_command = None
        self.is_listening = False
        self.minimized = False
        self.minimized_label = None
        self.pulse_animation_id = None
        self.current_pulse = 0
        
        # Set up keyboard listener
        self.keyboard_thread = threading.Thread(target=self.keyboard_listener, daemon=True)
        self.keyboard_thread.start()
        
        # Start animations
        self.animate_pulse()

    def create_rounded_background(self):
        """Create rounded rectangle background"""
        # Create base image with transparency
        self.bg_image = Image.new('RGBA', (self.width, self.height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(self.bg_image)
        
        # Draw rounded rectangle with semi-transparent background
        draw.rounded_rectangle(
            [0, 0, self.width, self.height],
            radius=self.corner_radius,
            fill=self.bg_color
        )
        
        # Convert to PhotoImage
        self.bg_photo = ImageTk.PhotoImage(self.bg_image)
        
        # Create background label
        bg_label = tk.Label(self.root, image=self.bg_photo, bg=self.bg_color)
        bg_label.place(x=0, y=0, relwidth=1, relheight=1)

    def create_button(self, text, command):
        """Create a custom rounded button"""
        btn = tk.Label(
            self.button_frame,
            text=text,
            font=('Segoe UI', 11),
            bg=self.bg_color,
            fg=self.text_color,
            padx=8,
            pady=2
        )
        btn.bind('<Button-1>', command)
        btn.bind('<Enter>', lambda e: self.on_button_hover(e, True))
        btn.bind('<Leave>', lambda e: self.on_button_hover(e, False))
        return btn

    def on_button_hover(self, event, entering):
        """Handle button hover effects"""
        if entering:
            event.widget.configure(fg=self.highlight_color)
        else:
            event.widget.configure(fg=self.text_color)

    def create_mic_icon(self):
        """Create animated microphone icon"""
        self.mic_size = 20
        center_x = 15
        center_y = 15
        
        # Create base microphone shape
        self.mic_canvas.create_oval(
            center_x - 8, center_y - 8,
            center_x + 8, center_y + 8,
            outline=self.accent_color,
            width=2,
            tags='mic'
        )
        
        # Create pulse circles
        self.pulse_circles = []
        for i in range(3):
            circle = self.mic_canvas.create_oval(
                center_x - 8, center_y - 8,
                center_x + 8, center_y + 8,
                outline=self.accent_color,
                width=1,
                state='hidden',
                tags=f'pulse{i}'
            )
            self.pulse_circles.append(circle)

    def animate_pulse(self):
        """Animate the microphone pulse effect"""
        if self.is_listening:
            self.current_pulse = (self.current_pulse + 1) % 30
            
            for i, circle in enumerate(self.pulse_circles):
                phase = (self.current_pulse + i * 10) % 30
                if phase < 15:
                    scale = 1 + (phase / 15)
                    alpha = 1 - (phase / 15)
                    
                    # Update circle size and opacity
                    x = 15 - (8 * scale)
                    y = 15 - (8 * scale)
                    x2 = 15 + (8 * scale)
                    y2 = 15 + (8 * scale)
                    
                    self.mic_canvas.coords(circle, x, y, x2, y2)
                    self.mic_canvas.itemconfig(
                        circle,
                        state='normal',
                        outline=self.highlight_color if i % 2 == 0 else self.accent_color
                    )
                else:
                    self.mic_canvas.itemconfig(circle, state='hidden')
        else:
            for circle in self.pulse_circles:
                self.mic_canvas.itemconfig(circle, state='hidden')
        
        self.pulse_animation_id = self.root.after(50, self.animate_pulse)

    def keyboard_listener(self):
        """Listen for keyboard events"""
        keyboard.on_press_key('p', self.on_p_press)
        keyboard.on_release_key('p', self.on_p_release)
        keyboard.wait()

    def on_p_press(self, e):
        """Handle P key press"""
        if not self.is_listening and self.speak_command:
            self.is_listening = True
            self.status_var.set("🎤 Listening...")
            self.status_label.configure(fg=self.highlight_color)
            
            # Run the speak command in a separate thread
            thread = threading.Thread(target=self._run_speak_command)
            thread.daemon = True
            thread.start()

    def on_p_release(self, e):
        """Handle P key release"""
        if self.is_listening:
            self.is_listening = False
            if self.stop_command:
                self.stop_command(silent=True)
            self._reset_status()

    def _run_speak_command(self):
        """Run the speak command in a separate thread"""
        try:
            self.speak_command()
        finally:
            self.root.after(0, self._reset_status)

    def _reset_status(self):
        """Reset the status display"""
        self.is_listening = False
        self.status_var.set("Hold 'P' to speak")
        self.status_label.configure(fg=self.text_color)

    def minimize(self, event=None):
        """Minimize to floating icon"""
        if not self.minimized:
            self.minimized = True
            self.root.withdraw()
            
            # Create minimal floating icon
            self.minimized_label = tk.Toplevel(self.root)
            self.minimized_label.overrideredirect(True)
            self.minimized_label.attributes('-topmost', True, '-alpha', 0.95)
            
            # Create rounded background for minimized state
            mini_size = 40
            mini_bg = Image.new('RGBA', (mini_size, mini_size), (0, 0, 0, 0))
            draw = ImageDraw.Draw(mini_bg)
            draw.rounded_rectangle(
                [0, 0, mini_size, mini_size],
                radius=10,
                fill=self.bg_color
            )
            self.mini_photo = ImageTk.PhotoImage(mini_bg)
            
            mini_frame = tk.Frame(self.minimized_label, bg=self.bg_color)
            mini_frame.pack(fill=tk.BOTH, expand=True)
            
            bg_label = tk.Label(mini_frame, image=self.mini_photo, bg=self.bg_color)
            bg_label.place(x=0, y=0, relwidth=1, relheight=1)
            
            label = tk.Label(
                mini_frame,
                text="🎤",
                font=('Segoe UI', 14),
                bg=self.bg_color,
                fg=self.accent_color,
                width=2,
                height=1
            )
            label.pack(padx=5, pady=5)
            
            # Position the minimized label
            x = self.root.winfo_x()
            y = self.root.winfo_y()
            self.minimized_label.geometry(f'{mini_size}x{mini_size}+{x}+{y}')
            
            # Add bindings
            label.bind('<Button-1>', self.restore)
            label.bind('<Button-3>', self.show_menu)
            label.bind('<B1-Motion>', self.drag_minimized)
            
            self._mini_drag_data = {'x': 0, 'y': 0}

    def restore(self, event=None):
        """Restore from minimized state"""
        if self.minimized:
            self.minimized = False
            x = self.minimized_label.winfo_x()
            y = self.minimized_label.winfo_y()
            self.minimized_label.destroy()
            self.minimized_label = None
            
            self.root.geometry(f'{self.width}x{self.height}+{x}+{y}')
            self.root.deiconify()

    def start_drag(self, event):
        """Start window drag"""
        self._drag_data = {'x': event.x, 'y': event.y}

    def on_drag(self, event):
        """Handle window drag"""
        if hasattr(self, '_drag_data'):
            x = self.root.winfo_x() + (event.x - self._drag_data['x'])
            y = self.root.winfo_y() + (event.y - self._drag_data['y'])
            self.root.geometry(f'+{x}+{y}')

    def drag_minimized(self, event):
        """Handle dragging of minimized icon"""
        if self.minimized:
            x = self.minimized_label.winfo_x() + (event.x - self._mini_drag_data['x'])
            y = self.minimized_label.winfo_y() + (event.y - self._mini_drag_data['y'])
            self.minimized_label.geometry(f'+{x}+{y}')

    def show_menu(self, event):
        """Show right-click menu"""
        menu = tk.Menu(self.root, tearoff=0)
        menu.configure(bg=self.bg_color, fg=self.text_color)
        menu.add_command(label="Restore", command=self.restore)
        menu.add_separator()
        menu.add_command(label="Exit", command=self.close)
        menu.tk_popup(event.x_root, event.y_root)

    def close(self, event=None):
        """Close the application"""
        if self.pulse_animation_id:
            self.root.after_cancel(self.pulse_animation_id)
        self.root.quit()

    def set_speak_command(self, command):
        """Set the callback for the speak action"""
        self.speak_command = command

    def set_stop_command(self, command):
        """Set the callback for the stop action"""
        self.stop_command = command

    def speak(self, text, is_user=False):
        """Display message in the UI"""
        prefix = "You:" if is_user else "Assistant:"
        self.status_var.set(f"{prefix} {text}")
        if is_user:
            self.status_label.configure(fg=self.highlight_color)
        else:
            self.status_label.configure(fg=self.accent_color)

def create_gui():
    """Create and return the GUI instance"""
    root = tk.Tk()
    return ModernFloatingAssistant(root)

# For testing
if __name__ == "__main__":
    gui = create_gui()
    gui.root.mainloop() 