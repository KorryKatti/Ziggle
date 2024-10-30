import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
import os
import json
import uuid

class ZoomableCanvas(tk.Canvas):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.bind("<MouseWheel>", self.zoom)
        self.bind("<ButtonPress-1>", self.start_drag)
        self.bind("<B1-Motion>", self.drag)

        self.scale_factor = 1.0
        self.offset_x = 0
        self.offset_y = 0

    def zoom(self, event):
        """Zoom in or out based on mouse wheel movement."""
        if event.delta > 0:  # Zoom in
            self.scale_factor *= 1.1
        else:  # Zoom out
            self.scale_factor /= 1.1
        
        self.config(scrollregion=self.bbox("all"))  # Update scroll region
        self.scale("all", 0, 0, self.scale_factor, self.scale_factor)

    def start_drag(self, event):
        """Start dragging the canvas."""
        self.prev_x = event.x
        self.prev_y = event.y

    def drag(self, event):
        """Move the canvas with mouse drag."""
        dx = event.x - self.prev_x
        dy = event.y - self.prev_y
        self.xview_scroll(-dx, "units")
        self.yview_scroll(-dy, "units")
        self.prev_x = event.x
        self.prev_y = event.y

def ensure_project_directory():
    project_dir = os.path.join(os.getcwd(), "project")
    os.makedirs(project_dir, exist_ok=True)

    index_path = os.path.join(project_dir, "index.json")
    if not os.path.exists(index_path):
        with open(index_path, 'w') as index_file:
            json.dump([], index_file)

    return index_path

def ask_for_project_details():
    dialog = tk.Toplevel(root)
    dialog.title("New Project")
    
    ttk.Label(dialog, text="Enter Width (mm):").grid(row=0, column=0, padx=10, pady=10)
    width_entry = ttk.Entry(dialog)
    width_entry.grid(row=0, column=1, padx=10, pady=10)

    ttk.Label(dialog, text="Enter Height (mm):").grid(row=1, column=0, padx=10, pady=10)
    height_entry = ttk.Entry(dialog)
    height_entry.grid(row=1, column=1, padx=10, pady=10)

    ttk.Label(dialog, text="Enter Filename:").grid(row=2, column=0, padx=10, pady=10)
    filename_entry = ttk.Entry(dialog)
    filename_entry.grid(row=2, column=1, padx=10, pady=10)

    def on_submit():
        width = width_entry.get()
        height = height_entry.get()
        filename = filename_entry.get().strip()

        try:
            width = int(width)
            height = int(height)

            if not filename:
                raise ValueError("Filename cannot be empty")
        except ValueError as e:
            messagebox.showerror("Input Error", str(e))
            return

        project_id = str(uuid.uuid4())

        project_dir = os.path.join("project", filename)
        os.makedirs(project_dir, exist_ok=True)

        index_path = ensure_project_directory()
        with open(index_path, 'r+') as index_file:
            projects = json.load(index_file)
            projects.append({"name": filename, "id": project_id})
            index_file.seek(0)
            json.dump(projects, index_file, indent=4)

        info_path = os.path.join(project_dir, "info.json")
        with open(info_path, 'w') as info_file:
            json.dump({filename: project_id}, info_file, indent=4)

        ziggle_path = os.path.join(project_dir, "data.ziggle")
        with open(ziggle_path, 'w') as ziggle_file:
            ziggle_file.write(f'height = "{height}"\n')
            ziggle_file.write(f'width = "{width}"\n')

        messagebox.showinfo("Project Created", f"Project '{filename}' created successfully!")
        dialog.destroy()
        
        create_canvas(filename, project_id, width, height)

    ttk.Button(dialog, text="Submit", command=on_submit).grid(row=3, columnspan=2, pady=10)

def create_canvas(project_name, project_id, width, height):
    for widget in root.winfo_children():
        widget.destroy()

    create_toolbar(root)

    canvas_frame = ttk.Frame(root, style='Canvas.TFrame')
    canvas_frame.pack(fill=tk.BOTH, expand=True)

    # Create scrollbars
    h_scrollbar = ttk.Scrollbar(canvas_frame, orient=tk.HORIZONTAL)
    h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)

    v_scrollbar = ttk.Scrollbar(canvas_frame, orient=tk.VERTICAL)
    v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    # Create a zoomable canvas
    canvas = ZoomableCanvas(canvas_frame, background="lightgreen", scrollregion=(0, 0, width, height))
    canvas.pack(fill=tk.BOTH, expand=True)

    # Configure scrollbars
    h_scrollbar.config(command=canvas.xview)
    v_scrollbar.config(command=canvas.yview)
    canvas.config(xscrollcommand=h_scrollbar.set, yscrollcommand=v_scrollbar.set)

    # Draw the grid
    draw_grid(canvas, width, height)

    # Add a label to indicate the project name
    project_label = ttk.Label(canvas_frame, text=f"Project: {project_name}", font=("Arial", 16), style='Canvas.TLabel')
    project_label.pack(pady=10)

    # Add a label to display the UUID in small text
    uuid_label = ttk.Label(canvas_frame, text=f"UUID: {project_id}", font=("Arial", 8), style='Canvas.TLabel')
    uuid_label.pack(pady=(0, 20))

    # Add zoom buttons
    zoom_in_button = ttk.Button(canvas_frame, text="Zoom In", command=lambda: canvas.scale("all", 0, 0, 1.1, 1.1))
    zoom_in_button.pack(side=tk.LEFT, padx=10)

    zoom_out_button = ttk.Button(canvas_frame, text="Zoom Out", command=lambda: canvas.scale("all", 0, 0, 0.9, 0.9))
    zoom_out_button.pack(side=tk.LEFT, padx=10)

def draw_grid(canvas, width, height):
    """Draw a grid on the canvas like graph paper."""
    # Draw vertical lines for major and minor grid lines
    for i in range(0, width + 1, 10):  # Minor grid lines every 10 units
        canvas.create_line(i, 0, i, height, fill="lightgray", dash=(2, 2))  # Minor lines
    for i in range(0, width + 1, 50):  # Major grid lines every 50 units
        canvas.create_line(i, 0, i, height, fill="gray")  # Major lines
    
    # Draw horizontal lines for major and minor grid lines
    for i in range(0, height + 1, 10):  # Minor grid lines every 10 units
        canvas.create_line(0, i, width, i, fill="lightgray", dash=(2, 2))  # Minor lines
    for i in range(0, height + 1, 50):  # Major grid lines every 50 units
        canvas.create_line(0, i, width, i, fill="gray")  # Major lines
    
    # Draw axes
    canvas.create_line(0, height // 2, width, height // 2, fill="black")  # X-axis
    canvas.create_line(width // 2, 0, width // 2, height, fill="black")  # Y-axis

    # Draw axis labels
    for i in range(0, width + 1, 50):  # Labels for every 50 units
        canvas.create_text(i, height // 2 + 15, text=str(i), fill="black", anchor=tk.N)  # X labels
    for i in range(0, height + 1, 50):  # Labels for every 50 units
        canvas.create_text(width // 2 - 15, i, text=str(i), fill="black", anchor=tk.E)  # Y labels

def on_new():
    ask_for_project_details()

def on_open():
    print("Open button clicked")

def create_toolbar(root):
    toolbar = ttk.Frame(root, padding=5, style='Toolbar.TFrame')
    toolbar.pack(side=tk.TOP, fill=tk.X)

    file_button = ttk.Button(toolbar, text="File", command=lambda: print("File button clicked"), style='Toolbar.TButton')
    file_button.pack(side=tk.LEFT)

    export_button = ttk.Button(toolbar, text="Export", command=lambda: print("Export button clicked"), style='Toolbar.TButton')
    export_button.pack(side=tk.LEFT)

    command_button = ttk.Button(toolbar, text="Command", command=lambda: print("Command button clicked"), style='Toolbar.TButton')
    command_button.pack(side=tk.LEFT)

    contribute_button = ttk.Button(toolbar, text="Contribute", command=lambda: print("Contribute button clicked"), style='Toolbar.TButton')
    contribute_button.pack(side=tk.LEFT)

def create_landing_page(root):
    landing_frame = ttk.Frame(root, style='Landing.TFrame')
    landing_frame.pack(pady=20, fill=tk.BOTH, expand=True)

    welcome_label = ttk.Label(landing_frame, text="Welcome to Ziggle", font=("Arial", 24), style='Landing.TLabel')
    welcome_label.pack(pady=10)

    button_frame = ttk.Frame(landing_frame, style='Landing.TFrame')
    button_frame.pack(pady=10)

    new_button = ttk.Button(button_frame, text="New", command=on_new, style='Landing.TButton')
    new_button.pack(side=tk.LEFT, padx=10)

    open_button = ttk.Button(button_frame, text="Open", command=on_open, style='Landing.TButton')
    open_button.pack(side=tk.LEFT, padx=10)

if __name__ == "__main__":
    root = tk.Tk()
    root.title("Welcome to Ziggle")
    root.geometry("800x600")

    # Configure styles
    style = ttk.Style()
    style.theme_use('clam')
    style.configure('TFrame', background="#1F1D2D")
    style.configure('Toolbar.TFrame', background="#1F1D2D")
    style.configure('Landing.TFrame', background="#1F1D2D")
    style.configure('Canvas.TFrame', background="lightgreen")  # Canvas background color
    style.configure('TButton', background="#5C4F7C", foreground="#E0DEF4", padding=5)
    style.configure('Toolbar.TButton', background="#5C4F7C", foreground="#E0DEF4", padding=5)
    style.configure('Landing.TButton', background="#5C4F7C", foreground="#E0DEF4", padding=5)
    style.configure('Landing.TLabel', background="#1F1D2D", foreground="#E0DEF4")
    style.configure('Canvas.TLabel', background="#E0DEF4", foreground="#1F1D2D")

    # Set the Rose Pine colors
    root.tk_setPalette(background="#1F1D2D", foreground="#E0DEF4")

    create_toolbar(root)
    create_landing_page(root)

    root.mainloop()
