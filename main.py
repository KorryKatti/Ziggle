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

from tkinter import Text, Button

def create_graph(root, project_name, project_id, width, height):
    for widget in root.winfo_children():
        widget.destroy()
    
    create_toolbar(root)
    graph_frame = ttk.Frame(root, style='Graph.TFrame')
    graph_frame.pack(fill=tk.BOTH, expand=True, pady=10)

    # Create the Plotly figure (this remains the same)
    fig = go.Figure()

    # Add grid lines (same as before)
    x_grid = list(range(0, width + 1, max(1, width // 50)))  # Adaptive grid density
    y_grid = list(range(0, height + 1, max(1, height // 50)))

    for x in x_grid:
        fig.add_shape(
            type="line",
            x0=x, x1=x,
            y0=0, y1=height,
            line=dict(color="lightgray", width=1, dash="dash")
        )

    for y in y_grid:
        fig.add_shape(
            type="line",
            x0=0, x1=width,
            y0=y, y1=y,
            line=dict(color="lightgray", width=1, dash="dash")
        )

    fig.update_layout(
        showlegend=False,
        plot_bgcolor='white',
        xaxis=dict(
            range=[0, width],
            showgrid=False,
            zeroline=True,
            zerolinewidth=2,
            zerolinecolor='black',
            tickformat=',.0f'
        ),
        yaxis=dict(
            range=[0, height],
            showgrid=False,
            zeroline=True,
            zerolinewidth=2,
            zerolinecolor='black',
            tickformat=',.0f'
        ),
        margin=dict(l=50, r=50, t=50, b=50),
        dragmode='pan'
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

    # Project info labels
    info_frame = ttk.Frame(graph_frame)
    info_frame.pack(fill=tk.X, pady=5)
    
    project_label = ttk.Label(info_frame, text=f"Project: {project_name}", font=("Arial", 16))
    project_label.pack(side=tk.LEFT, padx=10)
    
    uuid_label = ttk.Label(info_frame, text=f"UUID: {project_id}", font=("Arial", 8))
    uuid_label.pack(side=tk.RIGHT, padx=10)

    # Open interactive grid button
    open_button = ttk.Button(graph_frame, text="Open Interactive Grid", command=open_plot)
    open_button.pack(pady=10)

    # Add preview label
    preview_label = ttk.Label(graph_frame, text="Click 'Open Interactive Grid' to view the full interactive grid\nFeatures: Zoom, Pan, Reset, Save as PNG", justify=tk.CENTER)
    preview_label.pack(pady=5)

    # Command Input Section
    input_frame = ttk.Frame(graph_frame)
    input_frame.pack(side=tk.BOTTOM, fill=tk.X)

    command_input = Text(input_frame, height=2, wrap="word")
    command_input.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5, pady=5)

    execute_button = Button(input_frame, text="Execute", command=lambda: process_command(command_input.get("1.0", "end-1c")))
    execute_button.pack(side=tk.RIGHT, padx=5, pady=5)

def process_command(command_text):
    # This function will parse and execute the ZiggleScript commands
    print(f"Executing command: {command_text}")
    # Add parsing and shape drawing logic here

def execute_command(command):
    """Execute the given ZiggleScript command."""
    # Check if the command ends with '<>'
    if not command.endswith('<>'):
        messagebox.showerror("Invalid Command", "Command must end with '<>'.")
        return

    command = command[:-2].strip()  # Remove '<>' and any trailing spaces

    # Split the command and check if it's for drawing a rectangle
    if command.startswith("DRAW RECTANGLE"):
        try:
            parts = command.split()  # Split the command into parts
            x0, y0, x1, y1, color = map(str.strip, parts[2:])  # Extract coordinates and color
            
            # Convert coordinates to integers
            x0, y0, x1, y1 = int(x0), int(y0), int(x1), int(y1)
            
            # Draw the rectangle on the Plotly figure
            fig.add_shape(
                type="rect",
                x0=x0, y0=y0,
                x1=x1, y1=y1,
                fillcolor=color,
                line=dict(color="black")
            )
            fig.show()  # Refresh the plot to show the new shape
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to draw rectangle: {e}")
    else:
        messagebox.showerror("Invalid Command", "Unknown command.")

def submit_command():
    """Get the command from the input box and execute it."""
    command = command_input.get()
    execute_command(command)
    command_input.delete(0, tk.END)  # Clear the input box

# Add command input box to your main window
command_frame = ttk.Frame(root)
command_frame.pack(pady=10)

ttk.Label(command_frame, text="Enter Command:").pack(side=tk.LEFT)
command_input = ttk.Entry(command_frame, width=50)
command_input.pack(side=tk.LEFT, padx=5)

submit_button = ttk.Button(command_frame, text="Submit", command=submit_command)
submit_button.pack(side=tk.LEFT)

# Ensure the Plotly figure is accessible globally
global fig
fig = go.Figure()  # Create an initial empty figure


import http.server
import socketserver
import webbrowser
import threading

PORT = 8000  # Choose a port for localhost

def start_http_server(directory):
    """Start a simple HTTP server in a specified directory."""
    handler = http.server.SimpleHTTPRequestHandler
    os.chdir(directory)  # Set directory to serve files from

    # Create and start the server
    with socketserver.TCPServer(("", PORT), handler) as httpd:
        print(f"Serving at http://localhost:{PORT}")
        httpd.serve_forever()

def open_plot():
    """Open the plot on localhost server and in the default web browser."""
    # Ensure the temp directory and plot exist
    temp_dir = Path.home() / "temp_plots"
    plot_path = temp_dir / "grid_plot.html"
    
    if plot_path.exists():
        # Start the server in a separate thread to keep the main app responsive
        threading.Thread(target=start_http_server, args=(temp_dir,), daemon=True).start()

        # Open the plot in the default web browser via localhost
        webbrowser.open(f"http://localhost:{PORT}")
        
        # Show the ZiggleScript command popup after opening the browser
        open_command_popup()
    else:
        messagebox.showerror("Error", "Plot not found. Please create a plot first.")



def open_command_popup():
    """Create the command input popup using a Tkinter Toplevel window."""
    command_popup = tk.Toplevel(root)
    command_popup.title("Ziggle Command Center")
    command_popup.geometry("400x200")
    
    ttk.Label(command_popup, text="Enter ZiggleScript Commands:", font=("Arial", 12)).pack(pady=10)
    
    # Command input field
    command_input = tk.Text(command_popup, height=6, wrap="word")
    command_input.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
    
    # Execute button to process commands
    execute_button = ttk.Button(command_popup, text="Execute", 
                                command=lambda: process_command(command_input.get("1.0", "end-1c")))
    execute_button.pack(pady=10)

    # Ensuring window behavior
    command_popup.transient(root)  # Keep on top of main window
    command_popup.grab_set()       # Block interactions with other windows until closed
    command_popup.protocol("WM_DELETE_WINDOW", lambda: close_popup(command_popup))  # Handle window close

def close_popup(popup):
    """Handle the close event of the popup window."""
    popup.grab_release()
    popup.destroy()


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

    open_button = ttk.Button(toolbar, text="Open", command=lambda: open_project(root), style='Toolbar.TButton')
    open_button.pack(side=tk.LEFT)


def create_landing_page(root):
    landing_frame = ttk.Frame(root, style='Landing.TFrame')
    landing_frame.pack(pady=20, fill=tk.BOTH, expand=True)

    welcome_label = ttk.Label(landing_frame, text="Welcome to Ziggle", font=("Arial", 24), style='Landing.TLabel')
    welcome_label.pack(pady=10)

    button_frame = ttk.Frame(landing_frame, style='Landing.TFrame')
    button_frame.pack(pady=10)

    new_button = ttk.Button(button_frame, text="New", command=lambda: on_new(root), style='Landing.TButton')
    new_button.pack(side=tk.LEFT, padx=10)

    open_button = ttk.Button(button_frame, text="Open", command=lambda: on_open(root), style='Landing.TButton')
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

def ask_for_project_details(root):
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
            json.dump({"name": filename, "id": project_id}, info_file, indent=4)

        ziggle_path = os.path.join(project_dir, "data.ziggle")
        with open(ziggle_path, 'w') as ziggle_file:
            ziggle_file.write(f'height = "{height}"\n')
            ziggle_file.write(f'width = "{width}"\n')

        messagebox.showinfo("Project Created", f"Project '{filename}' created successfully!")
        dialog.destroy()
        
        create_graph(root, filename, project_id, width, height)

    ttk.Button(dialog, text="Submit", command=on_submit).grid(row=3, columnspan=2, pady=10)


# Main application entry point
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
