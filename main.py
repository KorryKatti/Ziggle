import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
import os
import json
import uuid
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import webview
import threading
from pathlib import Path
import plotly.graph_objects as go
import plotly.io as pio



def open_plot_in_webview(plot_path):
    """Open the Plotly graph in a pywebview window."""
    # Load the HTML file in the webview
    webview.create_window('Interactive Plot', str(plot_path), width=800, height=600)
    webview.start()


def open_plot():
    """Open the plot in a pywebview window."""
    # Ensure the temp directory exists
    temp_dir = Path.home() / "temp_plots"
    plot_path = temp_dir / "grid_plot.html"
    
    if plot_path.exists():
        # Open the webview directly without threading
        open_plot_in_webview(plot_path)
    else:
        messagebox.showerror("Error", "Plot not found. Please create a plot first.")

class ZoomPanCanvas(FigureCanvasTkAgg):
    def __init__(self, figure, master=None):
        super().__init__(figure, master=master)
        self.figure = figure
        self._scale_factor = 1.0
        self._drag_data = {"x": 0, "y": 0}

        # Bind events for zoom and pan
        self.get_tk_widget().bind("<MouseWheel>", self.zoom)
        self.get_tk_widget().bind("<ButtonPress-1>", self.start_pan)
        self.get_tk_widget().bind("<B1-Motion>", self.pan)

    def zoom(self, event):
        """Zoom in or out based on mouse wheel."""
        base_scale = 1.1
        if event.delta > 0:
            scale_factor = base_scale
        else:
            scale_factor = 1 / base_scale

        self._scale_factor *= scale_factor
        xdata, ydata = event.x, event.y
        self.figure.gca().set_xlim(self.figure.gca().get_xlim()[0] * scale_factor, 
                                   self.figure.gca().get_xlim()[1] * scale_factor)
        self.figure.gca().set_ylim(self.figure.gca().get_ylim()[0] * scale_factor, 
                                   self.figure.gca().get_ylim()[1] * scale_factor)
        self.draw()

    def start_pan(self, event):
        """Record the starting position of a pan."""
        self._drag_data["x"] = event.x
        self._drag_data["y"] = event.y

    def pan(self, event):
        """Move the plot view when dragging the mouse."""
        dx = event.x - self._drag_data["x"]
        dy = event.y - self._drag_data["y"]
        
        xlim = self.figure.gca().get_xlim()
        ylim = self.figure.gca().get_ylim()

        self.figure.gca().set_xlim(xlim[0] - dx / 100, xlim[1] - dx / 100)
        self.figure.gca().set_ylim(ylim[0] + dy / 100, ylim[1] + dy / 100)

        self._drag_data["x"] = event.x
        self._drag_data["y"] = event.y
        self.draw()

def create_graph(project_name, project_id, width, height):
    # Clear any previous widgets
    for widget in root.winfo_children():
        widget.destroy()

    # Create toolbar and frame
    create_toolbar(root)
    graph_frame = ttk.Frame(root, style='Graph.TFrame')
    graph_frame.pack(fill=tk.BOTH, expand=True, pady=10)

    # Create the Plotly figure
    fig = go.Figure()

    # Add the main grid as a scatter plot with no markers
    x_grid = list(range(0, width + 1, max(1, width // 50)))  # Adaptive grid density
    y_grid = list(range(0, height + 1, max(1, height // 50)))

    # Add vertical grid lines
    for x in x_grid:
        fig.add_shape(
            type="line",
            x0=x, x1=x,
            y0=0, y1=height,
            line=dict(color="lightgray", width=1, dash="dash")
        )

    # Add horizontal grid lines
    for y in y_grid:
        fig.add_shape(
            type="line",
            x0=0, x1=width,
            y0=y, y1=y,
            line=dict(color="lightgray", width=1, dash="dash")
        )

    # Configure the layout
    fig.update_layout(
        showlegend=False,
        plot_bgcolor='white',
        xaxis=dict(
            range=[0, width],
            showgrid=False,
            zeroline=True,
            zerolinewidth=2,
            zerolinecolor='black',
            tickformat=',.0f'  # No scientific notation
        ),
        yaxis=dict(
            range=[0, height],
            showgrid=False,
            zeroline=True,
            zerolinewidth=2,
            zerolinecolor='black',
            tickformat=',.0f'  # No scientific notation
        ),
        margin=dict(l=50, r=50, t=50, b=50),
        dragmode='pan'  # Enable panning
    )

    # Save the plot as HTML
    temp_dir = Path.home() / "temp_plots"
    temp_dir.mkdir(exist_ok=True)
    plot_path = temp_dir / "grid_plot.html"
    
    config = {
        'scrollZoom': True,
        'displayModeBar': True,
        'modeBarButtonsToAdd': ['zoom2d', 'pan2d', 'resetScale2d'],
        'responsive': True
    }
    
    pio.write_html(
        fig, 
        file=str(plot_path),
        config=config,
        include_plotlyjs='cdn',
        full_html=True,
        auto_open=False
    )

    # Create a label frame for project info
    info_frame = ttk.Frame(graph_frame)
    info_frame.pack(fill=tk.X, pady=5)
    
    project_label = ttk.Label(info_frame, text=f"Project: {project_name}", 
                             font=("Arial", 16))
    project_label.pack(side=tk.LEFT, padx=10)
    
    uuid_label = ttk.Label(info_frame, text=f"UUID: {project_id}", 
                          font=("Arial", 8))
    uuid_label.pack(side=tk.RIGHT, padx=10)

    # Create button to open the plot in pywebview
    open_button = ttk.Button(graph_frame, text="Open Interactive Grid", 
                            command=open_plot)
    open_button.pack(pady=10)

    # Optional: Add preview label
    preview_label = ttk.Label(graph_frame, 
                             text="Click 'Open Interactive Grid' to view the full interactive grid\n" +
                                  "Features: Zoom, Pan, Reset, Save as PNG",
                             justify=tk.CENTER)
    preview_label.pack(pady=5)

def update_grid(width, height):
    """Update the grid dimensions"""
    create_graph(width, height)


def on_new():
    ask_for_project_details()

def on_open():
    print("Open button clicked")

import tkinter.simpledialog as simpledialog

def open_project():
    """Open a project by selecting from a list of saved projects in index.json."""
    # Ensure the main project directory and index.json exist
    index_path = ensure_project_directory()
    
    # Read the projects from index.json
    with open(index_path, 'r') as index_file:
        projects = json.load(index_file)
        
    if not projects:
        messagebox.showinfo("No Projects", "No projects found to open.")
        return
    
    # Prompt the user to select a project
    project_names = [project['name'] for project in projects]
    selected_project = simpledialog.askstring("Open Project", "Select a project to open:", initialvalue=project_names[0])

    if selected_project:
        # Find the selected project details
        project_info = next((p for p in projects if p['name'] == selected_project), None)
        if project_info:
            project_dir = os.path.join("project", project_info['name'])
            info_path = os.path.join(project_dir, "info.json")
            ziggle_path = os.path.join(project_dir, "data.ziggle")

            try:
                # Load width and height from the .ziggle file
                with open(ziggle_path, 'r') as ziggle_file:
                    dimensions = {}
                    for line in ziggle_file:
                        key, value = line.strip().split(" = ")
                        dimensions[key.strip()] = int(value.strip().strip('"'))

                width = dimensions.get("width")
                height = dimensions.get("height")

                # Open the graph with the saved dimensions
                create_graph(project_info['name'], project_info['id'], width, height)

            except (FileNotFoundError, ValueError) as e:
                messagebox.showerror("Error", f"Failed to open project: {e}")

# Update the "Open" button command in create_toolbar
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

    # Connect the Open button to open_project
    open_button = ttk.Button(toolbar, text="Open", command=open_project, style='Toolbar.TButton')
    open_button.pack(side=tk.LEFT)


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



def ensure_project_directory():
    """Ensure the main project directory exists and an index file is initialized."""
    project_dir = os.path.join(os.getcwd(), "project")
    os.makedirs(project_dir, exist_ok=True)

    index_path = os.path.join(project_dir, "index.json")
    if not os.path.exists(index_path):
        with open(index_path, 'w') as index_file:
            json.dump([], index_file)

    return index_path

def ask_for_project_details():
    """Prompt user for project dimensions and filename, then save project details."""
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

        # Create a directory for the new project
        project_dir = os.path.join("project", filename)
        os.makedirs(project_dir, exist_ok=True)

        # Update the main project index
        index_path = ensure_project_directory()
        with open(index_path, 'r+') as index_file:
            projects = json.load(index_file)
            projects.append({"name": filename, "id": project_id})
            index_file.seek(0)
            json.dump(projects, index_file, indent=4)

        # Save project info and dimensions in the project directory
        info_path = os.path.join(project_dir, "info.json")
        with open(info_path, 'w') as info_file:
            json.dump({"name": filename, "id": project_id}, info_file, indent=4)

        ziggle_path = os.path.join(project_dir, "data.ziggle")
        with open(ziggle_path, 'w') as ziggle_file:
            ziggle_file.write(f'height = "{height}"\n')
            ziggle_file.write(f'width = "{width}"\n')

        messagebox.showinfo("Project Created", f"Project '{filename}' created successfully!")
        dialog.destroy()
        
        # Call create_graph to open the canvas and display the project
        create_graph(filename, project_id, width, height)

    ttk.Button(dialog, text="Submit", command=on_submit).grid(row=3, columnspan=2, pady=10)


if __name__ == "__main__":
    root = tk.Tk()
    root.title("Welcome to Ziggle")
    root.geometry("1280x720")

    style = ttk.Style()
    style.theme_use('clam')
    style.configure('TFrame', background="#1F1D2D")
    style.configure('Toolbar.TFrame', background="#1F1D2D")
    style.configure('Landing.TFrame', background="#1F1D2D")
    style.configure('Canvas.TFrame', background="lightgreen")
    style.configure('TButton', background="#5C4F7C", foreground="#E0DEF4", padding=5)
    style.configure('Toolbar.TButton', background="#5C4F7C", foreground="#E0DEF4", padding=5)
    style.configure('Landing.TButton', background="#5C4F7C", foreground="#E0DEF4", padding=5)
    style.configure('Landing.TLabel', background="#1F1D2D", foreground="#E0DEF4")
    style.configure('Canvas.TLabel', background="#E0DEF4", foreground="#1F1D2D")

    root.tk_setPalette(background="#1F1D2D", foreground="#E0DEF4")

    create_toolbar(root)
    create_landing_page(root)

    root.mainloop()
