import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, filedialog
import os
import json
import uuid
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.patches import Rectangle, Circle
from matplotlib.lines import Line2D
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Use a class to manage global state more safely
class ZiggleState:
    def __init__(self):
        self.fig = None
        self.ax = None
        self.width = 0
        self.height = 0
        self.undo_stack = []
        self.redo_stack = []

# Create a singleton instance of the state
ziggle_state = ZiggleState()

class GraphPlot:
    def __init__(self, root, project_name, project_id, width_val, height_val):
        self.root = root
        self.project_name = project_name
        self.project_id = project_id
        self.width_val = width_val
        self.height_val = height_val

        # Enhanced drawing state
        self.drawing_mode = None
        self.current_color = 'black'
        self.current_tool = None
        
        # Temporary preview element
        self.preview_element = None
        
        # Text input variables
        self.text_input_dialog = None
        self.current_text = ""
        self.current_font_size = 10
        
        # Zoom and pan variables
        self.zoom_level = 1.0
        self.pan_start = None
        self.max_zoom_out = 1.0  # Default max zoom out level
        self.min_zoom_in = 10.0  # Default min zoom in level

        # Project elements tracking with undo/redo support
        self.project_elements = {
            'rectangles': [],
            'lines': [],
            'circles': [],
            'texts': []
        }
        self.undo_stack = []
        self.redo_stack = []

        # Create the main application layout
        self.create_layout()
        
        # Try to load existing project state
        self.load_project_state()

    def undo_last_action(self):
        if not self.project_elements:
            return

        # Determine which list to remove from based on the last added element
        if self.project_elements['rectangles']:
            removed_element = self.project_elements['rectangles'].pop()
            action_type = 'rectangles'
        elif self.project_elements['lines']:
            removed_element = self.project_elements['lines'].pop()
            action_type = 'lines'
        elif self.project_elements['circles']:
            removed_element = self.project_elements['circles'].pop()
            action_type = 'circles'
        elif self.project_elements['texts']:
            removed_element = self.project_elements['texts'].pop()
            action_type = 'texts'
        else:
            return

        # Add to undo stack for potential redo
        self.redo_stack.append({
            'type': action_type,
            'element': removed_element
        })

        # Redraw everything
        self.redraw_project_elements()

    def redo_last_action(self):
        if not self.redo_stack:
            return

        # Get the last undone action
        last_action = self.redo_stack.pop()
        
        # Restore the element to its original list
        action_type = last_action['type']
        element = last_action['element']
        
        # Add back to the corresponding list
        self.project_elements[action_type].append(element)

        # Redraw everything
        self.redraw_project_elements()

    def on_mouse_press(self, event):
        if event.inaxes != ziggle_state.ax:
            return

        # Store the starting coordinates
        self.start_x, self.start_y = event.xdata, event.ydata
        
        # Handle text tool specifically
        if self.current_tool == 'text':
            # Remove any existing preview
            if self.preview_element:
                self.preview_element.remove()
                self.preview_element = None

            # Only place text if we have input
            if self.current_text:
                # Create text element
                text_data = {
                    'x1': self.start_x,
                    'x2': self.start_x,  # For text, x1 and x2 are the same
                    'y1': self.start_y,
                    'y2': self.start_y,  # For text, y1 and y2 are the same
                    'text': self.current_text,
                    'color': self.current_color,
                    'font_size': self.current_font_size
                }
                self.project_elements['texts'].append(text_data)
                
                # Place the text
                create_text(
                    self.start_x, self.start_x, 
                    self.start_y, self.start_y, 
                    self.current_text, 
                    self.current_color, 
                    self.current_font_size
                )

                # Reset text-related variables
                self.current_text = ""
                self.current_tool = None
                self.drawing_mode = False

                # Clear redo stack
                self.redo_stack.clear()

                # Redraw canvas
                ziggle_state.fig.canvas.draw_idle()
        else:
            # Existing press handling for other tools
            self.drawing_mode = True

            # Clear any existing preview
            if self.preview_element:
                self.preview_element.remove()
                self.preview_element = None

    def on_mouse_move(self, event):
        if not self.drawing_mode or event.inaxes != ziggle_state.ax:
            return

        # Remove previous preview if exists
        if self.preview_element:
            self.preview_element.remove()
            self.preview_element = None

        # Get current mouse position
        curr_x, curr_y = event.xdata, event.ydata

        # Create preview based on current tool
        if self.current_tool == 'rectangle':
            # Preview rectangle
            self.preview_element = ziggle_state.ax.add_patch(
                plt.Rectangle(
                    (min(self.start_x, curr_x), min(self.start_y, curr_y)), 
                    abs(curr_x - self.start_x), 
                    abs(curr_y - self.start_y), 
                    fill=False, 
                    edgecolor=self.current_color, 
                    linestyle='--'
                )
            )
        
        elif self.current_tool == 'line':
            # Preview line
            self.preview_element, = ziggle_state.ax.plot(
                [self.start_x, curr_x], 
                [self.start_y, curr_y], 
                color=self.current_color, 
                linestyle='--'
            )
        
        elif self.current_tool == 'circle':
            # Preview circle
            radius = ((curr_x - self.start_x)**2 + (curr_y - self.start_y)**2)**0.5
            self.preview_element = ziggle_state.ax.add_patch(
                plt.Circle(
                    (self.start_x, self.start_y), 
                    radius, 
                    fill=False, 
                    edgecolor=self.current_color, 
                    linestyle='--'
                )
            )

        # Refresh the canvas to show preview
        ziggle_state.fig.canvas.draw_idle()

    def on_mouse_release(self, event):
        if event.inaxes != ziggle_state.ax:
            return

        if not self.drawing_mode:
            return

        # Remove preview element
        if self.preview_element:
            self.preview_element.remove()
            self.preview_element = None

        end_x, end_y = event.xdata, event.ydata
        
        if self.current_tool == 'rectangle':
            rect_data = {
                'x1': min(self.start_x, end_x), 
                'x2': max(self.start_x, end_x), 
                'y1': min(self.start_y, end_y), 
                'y2': max(self.start_y, end_y), 
                'color': self.current_color,
                'filled': False
            }
            self.project_elements['rectangles'].append(rect_data)
            create_rectangle(
                min(self.start_x, end_x), 
                max(self.start_x, end_x), 
                min(self.start_y, end_y), 
                max(self.start_y, end_y), 
                self.current_color
            )
            
            # Clear redo stack when a new action is performed
            self.redo_stack.clear()
        
        elif self.current_tool == 'line':
            line_data = {
                'x1': self.start_x, 
                'y1': self.start_y, 
                'x2': end_x, 
                'y2': end_y, 
                'color': self.current_color
            }
            self.project_elements['lines'].append(line_data)
            create_line(self.start_x, self.start_y, end_x, end_y, 
                        self.current_color)
            
            # Clear redo stack when a new action is performed
            self.redo_stack.clear()
        
        elif self.current_tool == 'circle':
            radius = ((end_x - self.start_x)**2 + (end_y - self.start_y)**2)**0.5
            circle_data = {
                'x': self.start_x, 
                'y': self.start_y, 
                'radius': radius, 
                'color': self.current_color,
                'filled': False
            }
            self.project_elements['circles'].append(circle_data)
            create_circle(self.start_x, self.start_y, radius, 
                          self.current_color)
            
            # Clear redo stack when a new action is performed
            self.redo_stack.clear()
        
        # Reset drawing mode
        self.drawing_mode = False
        
        ziggle_state.fig.canvas.draw_idle()

    def set_text_tool(self):
        self.current_tool = 'text'
        # Open text input dialog
        self.open_text_input_dialog()

    def open_text_input_dialog(self):
        # Create a top-level dialog for text input
        self.text_input_dialog = tk.Toplevel(self.root)
        self.text_input_dialog.title("Text Input")
        self.text_input_dialog.geometry("300x200")
        self.text_input_dialog.grab_set()  # Make dialog modal

        # Text input
        tk.Label(self.text_input_dialog, text="Enter Text:").pack(pady=5)
        text_entry = tk.Entry(self.text_input_dialog, width=40)
        text_entry.pack(pady=5)
        text_entry.focus_set()

        # Font size input
        tk.Label(self.text_input_dialog, text="Font Size:").pack(pady=5)
        font_size_var = tk.StringVar(value="10")
        font_size_entry = tk.Entry(self.text_input_dialog, textvariable=font_size_var, width=10)
        font_size_entry.pack(pady=5)

        # Confirm button
        def confirm_text():
            self.current_text = text_entry.get()
            try:
                self.current_font_size = int(font_size_var.get())
            except ValueError:
                self.current_font_size = 10
            
            # Close the dialog and enable text placement
            self.text_input_dialog.destroy()
            self.drawing_mode = True

        confirm_btn = tk.Button(self.text_input_dialog, text="Confirm", command=confirm_text)
        confirm_btn.pack(pady=10)

        # Cancel button
        def cancel_text():
            self.current_tool = None
            self.text_input_dialog.destroy()

        cancel_btn = tk.Button(self.text_input_dialog, text="Cancel", command=cancel_text)
        cancel_btn.pack(pady=5)

    def redraw_project_elements(self):
        # Clear existing plot
        ziggle_state.ax.clear()
        ziggle_state.ax.grid(True, linestyle='--', alpha=0.7)
        ziggle_state.ax.set_xlim(0, self.width_val)
        ziggle_state.ax.set_ylim(0, self.height_val)
        ziggle_state.ax.set_aspect('equal')
        ziggle_state.ax.set_title(f'Project: {self.project_name}', fontsize=10)

        # Redraw rectangles
        for rect in self.project_elements.get('rectangles', []):
            create_rectangle(
                rect['x1'], rect['x2'], 
                rect['y1'], rect['y2'], 
                rect['color'], 
                rect.get('filled', False)
            )

        # Redraw lines
        for line in self.project_elements.get('lines', []):
            create_line(
                line['x1'], line['y1'], 
                line['x2'], line['y2'], 
                line['color']
            )

        # Redraw circles
        for circle in self.project_elements.get('circles', []):
            create_circle(
                circle['x'], circle['y'], 
                circle['radius'], 
                circle['color'], 
                circle.get('filled', False)
            )

        # Redraw texts
        for text in self.project_elements.get('texts', []):
            create_text(
                text['x1'], text['x2'], 
                text['y1'], text['y2'], 
                text['text'], 
                text['color'], 
                text['font_size']
            )

        # Refresh the canvas
        ziggle_state.fig.canvas.draw_idle()

    def save_project(self, show_message=True):
        try:
            # Ensure project directory exists
            project_dir = os.path.join("project", self.project_name)
            os.makedirs(project_dir, exist_ok=True)

            # Save project metadata
            project_info_path = os.path.join(project_dir, "project_state.json")
            with open(project_info_path, 'w') as f:
                json.dump({
                    'name': self.project_name,
                    'id': self.project_id,
                    'width': self.width_val,
                    'height': self.height_val,
                    'elements': self.project_elements
                }, f, indent=4)

            # Save the current figure
            figure_path = os.path.join(project_dir, "project_figure.png")
            ziggle_state.fig.savefig(figure_path, dpi=300, bbox_inches='tight')

            if show_message:
                messagebox.showinfo("Save Project", f"Project '{self.project_name}' saved successfully!")
            logger.info(f"Project {self.project_name} saved")
        except Exception as e:
            messagebox.showerror("Save Error", f"Could not save project: {str(e)}")
            logger.error(f"Project save error: {e}")

    def load_project_state(self):
        try:
            project_dir = os.path.join("project", self.project_name)
            project_info_path = os.path.join(project_dir, "project_state.json")
            
            if os.path.exists(project_info_path):
                with open(project_info_path, 'r') as f:
                    project_data = json.load(f)
                
                # Restore project elements
                self.project_elements = project_data.get('elements', {
                    'rectangles': [],
                    'lines': [],
                    'circles': [],
                    'texts': []
                })

                # Redraw existing elements
                self.redraw_project_elements()

                logger.info(f"Loaded project state for {self.project_name}")
        except Exception as e:
            logger.warning(f"Could not load project state: {e}")

    def create_layout(self):
        # Clear existing widgets
        for widget in self.root.winfo_children():
            widget.destroy()

        # Main container with grid layout
        self.main_frame = tk.Frame(self.root, bg='#f0f4f8')
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        # Toolbar (Top)
        self.create_toolbar()

        # Middle section with graph and side panel
        middle_frame = tk.Frame(self.main_frame, bg='#f0f4f8')
        middle_frame.pack(fill=tk.BOTH, expand=True)

        # Left side panel for tools
        self.create_side_panel(middle_frame)

        # Graph area
        self.graph_frame = tk.Frame(middle_frame, bg='white')
        self.graph_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Create graph
        self.create_graph(self.width_val, self.height_val)

        # Command input area (Bottom)
        self.create_command_input()

        # Connect mouse events
        ziggle_state.fig.canvas.mpl_connect('button_press_event', self.on_mouse_press)
        ziggle_state.fig.canvas.mpl_connect('motion_notify_event', self.on_mouse_move)
        ziggle_state.fig.canvas.mpl_connect('button_release_event', self.on_mouse_release)
        ziggle_state.fig.canvas.mpl_connect('scroll_event', self.on_scroll)

    def create_toolbar(self):
        toolbar_frame = tk.Frame(self.main_frame, bg='#34495e', height=40)
        toolbar_frame.pack(fill=tk.X)
        toolbar_frame.pack_propagate(False)

        # Project name display
        project_label = tk.Label(toolbar_frame, text=f"Project: {self.project_name}", 
                                 bg='#34495e', fg='white', font=('Segoe UI', 10))
        project_label.pack(side=tk.LEFT, padx=10)

        # Toolbar buttons
        toolbar_buttons = [
            ("New", self.new_project),
            ("Save", self.save_project),
            ("Export", self.export_project)
        ]

        for label, command in toolbar_buttons:
            btn = tk.Button(toolbar_frame, text=label, command=command, 
                            bg='#2c3e50', fg='white', relief=tk.FLAT)
            btn.pack(side=tk.RIGHT, padx=5, pady=2)

        # Text tool button
        text_btn = tk.Button(
            toolbar_frame, 
            text="Text", 
            command=self.set_text_tool,
            bg='#2980b9', 
            fg='white'
        )
        text_btn.pack(side=tk.LEFT, padx=5, pady=5)

    def create_side_panel(self, parent):
        side_panel = tk.Frame(parent, width=60, bg='#2c3e50')
        side_panel.pack(side=tk.LEFT, fill=tk.Y)
        side_panel.pack_propagate(False)

        # Drawing tools
        tools = [
            ("Rectangle", self.set_rectangle_tool),
            ("Line", self.set_line_tool),
            ("Circle", self.set_circle_tool),
            ("Text", self.set_text_tool),
            ("Pan", self.set_pan_tool),
            ("Zoom", self.set_zoom_tool)
        ]

        for label, command in tools:
            btn = tk.Button(side_panel, text=label, command=command, 
                            bg='#34495e', fg='white', width=8, relief=tk.FLAT)
            btn.pack(pady=5)

        # Color palette
        colors = ['black', 'red', 'blue', 'green', 'yellow']
        for color in colors:
            btn = tk.Button(side_panel, bg=color, width=2, 
                            command=lambda c=color: self.set_color(c))
            btn.pack(pady=2)

    def create_graph(self, width_val, height_val):
        # Clear any existing figure
        plt.close('all')
        
        # Create new figure with specified dimensions
        ziggle_state.fig, ziggle_state.ax = plt.subplots(figsize=(8, 6))
        
        # Set fixed limits based on input dimensions
        ziggle_state.ax.set_xlim(0, width_val)
        ziggle_state.ax.set_ylim(0, height_val)
        
        # Store original limits for zoom restrictions
        self.original_xlim = (0, width_val)
        self.original_ylim = (0, height_val)
        
        # Set aspect ratio to be equal
        ziggle_state.ax.set_aspect('equal')
        
        # Add grid
        ziggle_state.ax.grid(True, linestyle='--', alpha=0.7)
        
        # Set title
        ziggle_state.ax.set_title(f'Project: {self.project_name}', fontsize=10)
        
        # Create canvas
        canvas = FigureCanvasTkAgg(ziggle_state.fig, master=self.graph_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        
        # Connect mouse events
        canvas.mpl_connect('button_press_event', self.on_mouse_press)
        canvas.mpl_connect('motion_notify_event', self.on_mouse_move)
        canvas.mpl_connect('button_release_event', self.on_mouse_release)
        canvas.mpl_connect('scroll_event', self.on_scroll)
        
        return canvas

    def on_scroll(self, event):
        # Only zoom if inside the axes
        if event.inaxes != ziggle_state.ax:
            return

        # Determine zoom direction
        zoom_factor = 1.1 if event.button == 'up' else 0.9

        # Get current view limits
        cur_xlim = ziggle_state.ax.get_xlim()
        cur_ylim = ziggle_state.ax.get_ylim()

        # Calculate new view limits
        new_width = (cur_xlim[1] - cur_xlim[0]) * zoom_factor
        new_height = (cur_ylim[1] - cur_ylim[0]) * zoom_factor

        # Calculate zoom center
        xdata = event.xdata
        ydata = event.ydata

        # Compute new limits
        new_xlim = (
            xdata - (xdata - cur_xlim[0]) * zoom_factor,
            xdata + (cur_xlim[1] - xdata) * zoom_factor
        )
        new_ylim = (
            ydata - (ydata - cur_ylim[0]) * zoom_factor,
            ydata + (cur_ylim[1] - ydata) * zoom_factor
        )

        # Enforce zoom limits
        # Prevent zooming out beyond original dimensions
        if (new_xlim[0] < self.original_xlim[0] or 
            new_xlim[1] > self.original_xlim[1] or 
            new_ylim[0] < self.original_ylim[0] or 
            new_ylim[1] > self.original_ylim[1]):
            return

        # Prevent zooming in too much (minimum view size)
        min_width = (self.original_xlim[1] - self.original_xlim[0]) / 10
        min_height = (self.original_ylim[1] - self.original_ylim[0]) / 10
        if new_width < min_width or new_height < min_height:
            return

        # Set new limits
        ziggle_state.ax.set_xlim(new_xlim)
        ziggle_state.ax.set_ylim(new_ylim)

        # Redraw
        ziggle_state.fig.canvas.draw_idle()

    def ask_for_project_details(self):
        # Create a dialog for project details
        details_window = tk.Toplevel(self.root)
        details_window.title("New Project")
        details_window.geometry("300x250")
        details_window.grab_set()  # Make modal

        # Project name input
        tk.Label(details_window, text="Project Name:").pack(pady=5)
        name_entry = tk.Entry(details_window, width=30)
        name_entry.pack(pady=5)
        name_entry.focus_set()

        # Dimensions input
        tk.Label(details_window, text="Canvas Dimensions (WxH):").pack(pady=5)
        dimensions_entry = tk.Entry(details_window, width=30)
        dimensions_entry.pack(pady=5)
        dimensions_entry.insert(0, "300x300")  # Default suggestion

        # Error message label
        error_label = tk.Label(details_window, text="", fg="red")
        error_label.pack(pady=5)

        def validate_and_create():
            # Get project name
            project_name = name_entry.get().strip()
            if not project_name:
                error_label.config(text="Project name cannot be empty")
                return

            # Parse dimensions
            try:
                width, height = map(int, dimensions_entry.get().split('x'))
                if width <= 0 or height <= 0:
                    raise ValueError("Dimensions must be positive")
            except (ValueError, TypeError):
                error_label.config(text="Invalid dimensions. Use format WxH (e.g., 300x300)")
                return

            # Generate unique project ID
            project_id = str(uuid.uuid4())

            # Close the dialog
            details_window.destroy()

            # Create the project
            graph_plot = GraphPlot(self.root, project_name, project_id, width, height)
            graph_plot.create_graph(width, height)

        # Create button
        create_btn = tk.Button(details_window, text="Create Project", command=validate_and_create)
        create_btn.pack(pady=10)

        # Cancel button
        def cancel_creation():
            details_window.destroy()

        cancel_btn = tk.Button(details_window, text="Cancel", command=cancel_creation)
        cancel_btn.pack(pady=5)

    def create_command_input(self):
        command_frame = tk.Frame(self.main_frame, bg='#ecf0f1', height=50)
        command_frame.pack(fill=tk.X)
        command_frame.pack_propagate(False)

        # Undo Button
        undo_btn = tk.Button(command_frame, text="Undo", 
                             command=self.undo_last_action, 
                             bg='#e74c3c', 
                             fg='white')
        undo_btn.pack(side=tk.LEFT, padx=5, pady=5)

        # Redo Button
        redo_btn = tk.Button(command_frame, text="Redo", 
                             command=self.redo_last_action, 
                             bg='#3498db', 
                             fg='white')
        redo_btn.pack(side=tk.LEFT, padx=5, pady=5)

        # Command input with improved styling
        self.command_input = tk.Entry(command_frame, 
                                      font=('Consolas', 10), 
                                      bg='white', 
                                      fg='#2c3e50',
                                      insertbackground='#3498db')
        self.command_input.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=10, pady=5)
        
        # Bind Enter key to command execution
        self.command_input.bind('<Return>', self.execute_command)

        # Execute button
        execute_btn = tk.Button(command_frame, text="Execute", 
                                command=self.execute_command, 
                                bg='#3498db', 
                                fg='white')
        execute_btn.pack(side=tk.RIGHT, padx=10, pady=5)

        # Save button
        save_btn = tk.Button(command_frame, text="Save", 
                             command=lambda: self.save_project(show_message=True), 
                             bg='#2ecc71', 
                             fg='white')
        save_btn.pack(side=tk.RIGHT, padx=5, pady=5)

    # Tool selection methods
    def set_rectangle_tool(self):
        self.current_tool = 'rectangle'
        self.drawing_mode = True

    def set_line_tool(self):
        self.current_tool = 'line'
        self.drawing_mode = True

    def set_circle_tool(self):
        self.current_tool = 'circle'
        self.drawing_mode = True

    def set_text_tool(self):
        self.current_tool = 'text'
        # Open text input dialog
        self.open_text_input_dialog()

    def set_pan_tool(self):
        self.current_tool = 'pan'
        self.drawing_mode = False

    def set_zoom_tool(self):
        self.current_tool = 'zoom'
        self.drawing_mode = False

    def set_color(self, color):
        self.current_color = color

    # Mouse event handlers
    def on_mouse_move(self, event):
        if event.inaxes != ziggle_state.ax:
            return

        if self.current_tool == 'pan' and self.pan_start:
            dx = event.xdata - self.pan_start[0]
            dy = event.ydata - self.pan_start[1]
            
            ziggle_state.ax.set_xlim(ziggle_state.ax.get_xlim() - dx)
            ziggle_state.ax.set_ylim(ziggle_state.ax.get_ylim() - dy)
            
            ziggle_state.fig.canvas.draw_idle()

    # Project management methods
    def new_project(self):
        self.ask_for_project_details()

    def export_project(self):
        try:
            # Open file dialog to choose export location
            export_path = filedialog.asksaveasfilename(
                defaultextension=".png",
                filetypes=[("PNG files", "*.png"), ("All files", "*.*")]
            )
            
            if export_path:
                # Save high-resolution figure
                ziggle_state.fig.savefig(export_path, dpi=300, bbox_inches='tight')
                messagebox.showinfo("Export Successful", f"Project exported to {export_path}")
        except Exception as e:
            messagebox.showerror("Export Error", f"Could not export project: {str(e)}")
            logger.error(f"Project export error: {e}")

    def execute_command(self, event=None):
        command = self.command_input.get().strip()
        if command.endswith('<>'):
            try:
                commands = command.replace('<>', '\n').splitlines()
                for cmd in commands:
                    cmd = cmd.strip()
                    if cmd:
                        process_zigglescript_command(cmd)
                self.command_input.delete(0, tk.END)
                ziggle_state.fig.canvas.draw_idle()
            except Exception as e:
                messagebox.showerror("Command Error", str(e))
        else:
            messagebox.showerror("Invalid Command", "ZiggleScript commands must end with '<>'")

import matplotlib.pyplot as plt

def create_text(x1, x2, y1, y2, text, color, font_size):
    x_pos = (x1 + x2) / 2
    y_pos = (y1 + y2) / 2

    plt.text(x_pos, y_pos, text, ha='center', va='center', color=color, fontsize=font_size)

def create_rectangle(x1, x2, y1, y2, color, filled=False):
    rect = Rectangle((x1, y1), x2-x1, y2-y1, linewidth=1, edgecolor=color, facecolor=color if filled else 'none')
    ziggle_state.ax.add_patch(rect)

def create_line(x1, y1, x2, y2, color):
    line = Line2D([x1, x2], [y1, y2], color=color, linewidth=2)
    ziggle_state.ax.add_line(line)

def create_circle(x, y, radius, color, filled=False):
    circle = Circle((x, y), radius, edgecolor=color, facecolor=color if filled else 'none', linewidth=1)
    ziggle_state.ax.add_patch(circle)

def submit_command():
    command = command_input.get("1.0", tk.END).strip()
    if command.endswith('<>'):
        try:
            commands = command.replace('<>', '\n').splitlines()
            for cmd in commands:
                cmd = cmd.strip()
                if cmd:
                    process_zigglescript_command(cmd)
            command_input.delete("1.0", tk.END)
            ziggle_state.fig.canvas.draw_idle()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to process command: {str(e)}")
    else:
        messagebox.showerror("Invalid Command", "ZiggleScript commands must end with '<>'")

def process_zigglescript_command(command):
    try:
        command_parts = command.split()
        command_name = " ".join(command_parts[:2])

        json_path = get_json_path()
        with open(json_path, 'r') as json_file:
            command_data = json.load(json_file)
            command_definitions = command_data['commands']

        if command_name not in command_definitions:
            raise ValueError(f"Unknown command: {command_name}")

        cmd_def = command_definitions[command_name]
        parameters = command_parts[2:]

        if command_name == "CREATE TEXT":
            params = parameters
            x1, x2, y1, y2 = params[:4]
            text = ' '.join(params[4:-2]).strip('"')
            color = params[-2]
            font_size = params[-1]
            create_text(float(x1), float(x2), float(y1), float(y2), text, color, int(font_size))

        elif command_name == "CREATE RECTANGLE":
            x1, x2, y1, y2, color, *options = parameters
            filled = "FILLED" in options
            create_rectangle(float(x1), float(x2), float(y1), float(y2), color.strip('"'), filled)

        elif command_name == "CREATE LINE":
            parameters = [param.strip('"') for param in parameters]
            x1, y1, x2, y2, color = parameters
            create_line(float(x1), float(y1), float(x2), float(y2), color)

        elif command_name == "CREATE CIRCLE":
            x, y, radius, color, *options = parameters
            filled = "FILLED" in options
            create_circle(float(x), float(y), float(radius), color.strip('"'), filled)

        ziggle_state.undo_stack.append({
            'command': command_name,
            'parameters': parameters
        })

    except json.JSONDecodeError as e:
        messagebox.showerror("JSON Error", f"Failed to parse JSON: {str(e)}")
    except Exception as e:
        messagebox.showerror("Command Error", f"Failed to process command: {str(e)}")

def undo_last_command():
    global ziggle_state
    if ziggle_state.undo_stack:
        last_command = ziggle_state.undo_stack.pop()
        ziggle_state.redo_stack.append(last_command)
        command_name = last_command['command']
        parameters = last_command['parameters']

        ziggle_state.ax.clear()
        ziggle_state.ax.grid(True)
        ziggle_state.ax.set_xlim(0, ziggle_state.width)
        ziggle_state.ax.set_ylim(0, ziggle_state.height)
        ziggle_state.ax.set_aspect('equal')

        for command in ziggle_state.undo_stack:
            cmd_name = command['command']
            params = command['parameters']

            if cmd_name == "CREATE TEXT":
                create_text(float(params[0]), float(params[1]), float(params[2]), float(params[3]), params[4], params[5], int(params[6]))
            elif cmd_name == "CREATE RECTANGLE":
                create_rectangle(float(params[0]), float(params[1]), float(params[2]), float(params[3]), params[4], "FILLED" in params)
            elif cmd_name == "CREATE LINE":
                create_line(float(params[0]), float(params[1]), float(params[2]), float(params[3]), params[4])
            elif cmd_name == "CREATE CIRCLE":
                create_circle(float(params[0]), float(params[1]), float(params[2]), params[3], "FILLED" in params)

        ziggle_state.fig.canvas.draw_idle()

def redo_last_command():
    global ziggle_state
    if ziggle_state.redo_stack:
        last_command = ziggle_state.redo_stack.pop()
        ziggle_state.undo_stack.append(last_command)
        command_name = last_command['command']
        parameters = last_command['parameters']

        if command_name == "CREATE TEXT":
            create_text(float(parameters[0]), float(parameters[1]), float(parameters[2]), float(parameters[3]), parameters[4], parameters[5], int(parameters[6]))
        elif command_name == "CREATE RECTANGLE":
            create_rectangle(float(parameters[0]), float(parameters[1]), float(parameters[2]), float(parameters[3]), parameters[4], "FILLED" in parameters)
        elif command_name == "CREATE LINE":
            create_line(float(parameters[0]), float(parameters[1]), float(parameters[2]), float(parameters[3]), parameters[4])
        elif command_name == "CREATE CIRCLE":
            create_circle(float(parameters[0]), float(parameters[1]), float(parameters[2]), parameters[3], "FILLED" in parameters)

        ziggle_state.fig.canvas.draw_idle()

def create_command_buttons(root):
    command_frame = tk.Frame(root)
    command_frame.pack(side=tk.TOP, fill=tk.X)

    tk.Button(command_frame, text="CREATE RECTANGLE", 
              command=lambda: command_input.insert(tk.END, "CREATE RECTANGLE x1 x2 y1 y2 color<>")).pack(side=tk.LEFT)

    tk.Button(command_frame, text="CREATE LINE", 
              command=lambda: command_input.insert(tk.END, "CREATE LINE x1 y1 x2 y2 color<>")).pack(side=tk.LEFT)

    tk.Button(command_frame, text="CREATE CIRCLE", 
              command=lambda: command_input.insert(tk.END, "CREATE CIRCLE x y radius color<>")).pack(side=tk.LEFT)

    tk.Button(command_frame, text="CREATE TEXT", 
            command=lambda: command_input.insert(tk.END, 'CREATE TEXT x1 x2 y1 y2 "text" color font_size<>')).pack(side=tk.LEFT)

def get_json_path():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(script_dir, 'zigglescript_commands.json')

def get_recent_projects(max_projects=5):
    """
    Retrieve recently opened projects from the project index
    """
    try:
        index_path = os.path.join(os.getcwd(), "project", "index.json")
        if not os.path.exists(index_path):
            return []
        
        with open(index_path, 'r') as index_file:
            projects = json.load(index_file)
        
        # Sort projects by most recently added (assuming last added is most recent)
        recent_projects = projects[-max_projects:]
        recent_projects.reverse()  # Most recent first
        return recent_projects
    except Exception as e:
        logger.error(f"Error retrieving recent projects: {e}")
        return []

def open_recent_project(root, project_data):
    """
    Open a recently created project
    """
    try:
        project_name = project_data['name']
        project_id = project_data['id']
        
        # Load project details
        project_dir = os.path.join("project", project_name)
        ziggle_path = os.path.join(project_dir, "data.ziggle")
        
        # Read project dimensions
        with open(ziggle_path, 'r') as ziggle_file:
            lines = ziggle_file.readlines()
            width_val = int(lines[1].split('"')[1])
            height_val = int(lines[0].split('"')[1])
        
        # Destroy current landing page and create project
        for widget in root.winfo_children():
            widget.destroy()
        
        project = GraphPlot(root, project_name, project_id, width_val, height_val)
    except Exception as e:
        logger.error(f"Error opening recent project {project_name}: {e}")
        messagebox.showerror("Open Project Error", f"Could not open project {project_name}")

def ask_for_project_details(root):
    # Create a styled landing page with sidebar
    root.configure(bg='#f0f4f8')  # Soft blue-gray background
    
    # Main container (split into sidebar and main content)
    main_container = tk.Frame(root, bg='#f0f4f8')
    main_container.pack(expand=True, fill=tk.BOTH, padx=0, pady=0)

    # Sidebar for recent projects
    sidebar = tk.Frame(main_container, width=250, bg='#2c3e50')
    sidebar.pack(side=tk.LEFT, fill=tk.Y)
    sidebar.pack_propagate(False)

    # Sidebar Title
    sidebar_title = tk.Label(sidebar, text="Recent Projects", 
                              font=('Segoe UI', 16, 'bold'), 
                              fg='white', 
                              bg='#2c3e50',
                              pady=15)
    sidebar_title.pack()

    # Recent Projects List
    recent_projects_frame = tk.Frame(sidebar, bg='#2c3e50')
    recent_projects_frame.pack(fill=tk.BOTH, expand=True, padx=10)

    # Scrollbar for recent projects
    scrollbar = tk.Scrollbar(recent_projects_frame)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    recent_projects_listbox = tk.Listbox(
        recent_projects_frame, 
        yscrollcommand=scrollbar.set,
        bg='#2c3e50', 
        fg='white',
        font=('Segoe UI', 10),
        borderwidth=0,
        highlightthickness=0,
        selectbackground='#3498db'
    )
    recent_projects_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    scrollbar.config(command=recent_projects_listbox.yview)

    # Populate recent projects
    recent_projects = get_recent_projects()
    for project in recent_projects:
        recent_projects_listbox.insert(tk.END, project['name'])

    # Open Recent Project functionality
    def on_project_select(event):
        selection = recent_projects_listbox.curselection()
        if selection:
            index = selection[0]
            project_data = recent_projects[index]
            open_recent_project(root, project_data)

    recent_projects_listbox.bind('<Double-1>', on_project_select)

    # Main content frame (right side)
    main_content = tk.Frame(main_container, bg='#f0f4f8')
    main_content.pack(side=tk.RIGHT, expand=True, fill=tk.BOTH, padx=40, pady=40)

    # Title and Subtitle
    title_frame = tk.Frame(main_content, bg='#f0f4f8')
    title_frame.pack(pady=(0, 30))

    title_label = tk.Label(title_frame, text="Welcome to Ziggle", 
                           font=('Segoe UI', 24, 'bold'), 
                           fg='#2c3e50', 
                           bg='#f0f4f8')
    title_label.pack()

    subtitle_label = tk.Label(title_frame, 
                              text="Create Your 2D Drawing Project", 
                              font=('Segoe UI', 12), 
                              fg='#7f8c8d', 
                              bg='#f0f4f8')
    subtitle_label.pack()

    # Form Frame
    form_frame = tk.Frame(main_content, bg='#f0f4f8')
    form_frame.pack(expand=True)

    # Style for labels and entries
    label_style = {
        'font': ('Segoe UI', 10),
        'fg': '#2c3e50',
        'bg': '#f0f4f8',
        'anchor': 'w'
    }

    entry_style = {
        'font': ('Segoe UI', 10),
        'relief': tk.FLAT,
        'bg': 'white',
        'highlightthickness': 1,
        'highlightcolor': '#3498db',
        'highlightbackground': '#bdc3c7'
    }

    # Width Input
    width_label = tk.Label(form_frame, text="Project Width (mm)", **label_style)
    width_label.pack(fill=tk.X, padx=20)
    width_entry = tk.Entry(form_frame, **entry_style)
    width_entry.pack(fill=tk.X, padx=20, pady=(0, 10), ipady=5)

    # Height Input
    height_label = tk.Label(form_frame, text="Project Height (mm)", **label_style)
    height_label.pack(fill=tk.X, padx=20)
    height_entry = tk.Entry(form_frame, **entry_style)
    height_entry.pack(fill=tk.X, padx=20, pady=(0, 10), ipady=5)

    # Filename Input
    filename_label = tk.Label(form_frame, text="Project Name", **label_style)
    filename_label.pack(fill=tk.X, padx=20)
    filename_entry = tk.Entry(form_frame, **entry_style)
    filename_entry.pack(fill=tk.X, padx=20, pady=(0, 20), ipady=5)

    # Error Label
    error_label = tk.Label(form_frame, text="", fg='#e74c3c', bg='#f0f4f8', font=('Segoe UI', 10))
    error_label.pack(pady=(0, 10))

    def validate_and_submit():
        # Clear previous error
        error_label.config(text="")
        
        width_val = width_entry.get().strip()
        height_val = height_entry.get().strip()
        filename = filename_entry.get().strip()

        try:
            width_val = int(width_val)
            height_val = int(height_val)
            
            if width_val <= 0 or height_val <= 0:
                raise ValueError("Width and height must be positive integers.")
            if not filename:
                raise ValueError("Project name cannot be empty")
            
            # Validate filename (no special characters)
            import re
            if not re.match(r'^[a-zA-Z0-9_-]+$', filename):
                raise ValueError("Project name can only contain letters, numbers, underscores, and hyphens")

        except ValueError as e:
            error_label.config(text=str(e))
            return

        # If all validations pass
        project_id = str(uuid.uuid4())
        project_dir = os.path.join("project", filename)
        os.makedirs(project_dir, exist_ok=True)

        index_path = ensure_project_directory()
        with open(index_path, 'r+') as index_file:
            projects = json.load(index_file)
            # Remove duplicate project names to avoid clutter
            projects = [p for p in projects if p['name'] != filename]
            projects.append({"name": filename, "id": project_id})
            index_file.seek(0)
            json.dump(projects, index_file, indent=4)
            index_file.truncate()

        info_path = os.path.join(project_dir, "info.json")
        with open(info_path, 'w') as info_file:
            json.dump({"name": filename, "id": project_id}, info_file, indent=4)

        ziggle_path = os.path.join(project_dir, "data.ziggle")
        with open(ziggle_path, 'w') as ziggle_file:
            ziggle_file.write(f'height = "{height_val}"\n')
            ziggle_file.write(f'width = "{width_val}"\n')

        # Destroy landing page and create project
        main_container.destroy()
        project = GraphPlot(root, filename, project_id, width_val, height_val)

    # Submit Button with modern styling
    submit_button = tk.Button(
        form_frame, 
        text="Create Project", 
        command=validate_and_submit,
        bg='#3498db',  # Bright blue
        fg='white', 
        font=('Segoe UI', 12, 'bold'),
        relief=tk.FLAT,
        padx=20,
        pady=10
    )
    submit_button.pack(pady=20)

    # Set focus and bind Enter key
    width_entry.focus_set()
    root.bind('<Return>', lambda event: validate_and_submit())

def ensure_project_directory():
    project_dir = os.path.join(os.getcwd(), "project")
    os.makedirs(project_dir, exist_ok=True)

    index_path = os.path.join(project_dir, "index.json")
    if not os.path.exists(index_path):
        with open(index_path, 'w') as index_file:
            json.dump([], index_file)

    return index_path

if __name__ == "__main__":
    root = tk.Tk()
    root.title("Welcome to Ziggle")
    root.geometry("1280x720")

    ask_for_project_details(root)
    root.mainloop()