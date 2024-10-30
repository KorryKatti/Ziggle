import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
import os
import json
import uuid
import matplotlib
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

class ZoomableCanvas(tk.Canvas):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.bind("<MouseWheel>", self.zoom)

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
        
        create_graph(filename, project_id, width, height)

    ttk.Button(dialog, text="Submit", command=on_submit).grid(row=3, columnspan=2, pady=10)

def create_graph(project_name, project_id, width, height):
    for widget in root.winfo_children():
        widget.destroy()

    create_toolbar(root)

    graph_frame = ttk.Frame(root, style='Graph.TFrame')
    graph_frame.pack(fill=tk.BOTH, expand=True, pady=10)

    figure = plt.figure()
    axes = figure.add_subplot(1, 1, 1)

    # Set the graph dimensions and aspect ratio
    axes.set_xlim(0, width)
    axes.set_ylim(0, height)
    axes.set_aspect('equal')

    # Set the grid and labels
    axes.grid(True, linestyle='-', linewidth=1)
    axes.set_xticks(range(0, width + 1, 50))
    axes.set_yticks(range(0, height + 1, 50))

    # Create the matplotlib canvas
    canvas = FigureCanvasTkAgg(figure, master=graph_frame)
    canvas.draw()
    canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    # Update the graph when resized
    def on_resize(event):
        figure.tight_layout()
        canvas.draw()

    canvas.get_tk_widget().bind('<Configure>', on_resize)

    project_label = ttk.Label(graph_frame, text=f"Project: {project_name}", font=("Arial", 16), style='Canvas.TLabel')
    project_label.pack(pady=10)

    uuid_label = ttk.Label(graph_frame, text=f"UUID: {project_id}", font=("Arial", 8), style='Canvas.TLabel')
    uuid_label.pack(pady=(0, 20))

    
def draw_grid(canvas, width, height):
    # Draw vertical lines for major grid lines
    for i in range(0, width + 1, 50):
        canvas.create_line(i, height, i, 0, fill="gray")
    
    # Draw horizontal lines for major grid lines
    for i in range(0, height + 1, 50):
        canvas.create_line(0, i, width, i, fill="gray")
    
    # Draw axes
    canvas.create_line(0, height, width, height, fill="black")  # X-axis
    canvas.create_line(0, height, 0, 0, fill="black")  # Y-axis

    # Draw X-axis labels
    for i in range(0, width + 1, 50):
        canvas.create_text(i, height + 15, text=str(i), fill="black", anchor=tk.N)
    
    # Draw Y-axis labels
    for i in range(0, height + 1, 50):
        canvas.create_text(-15, height - i, text=str(i), fill="black", anchor=tk.E)

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
