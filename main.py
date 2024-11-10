import tkinter as tk
from tkinter import ttk, messagebox
import os
import json
import uuid
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import plotly.graph_objects as go
import plotly.io as pio
from pathlib import Path
import tkinter.simpledialog as simpledialog

# Global Plotly figure instance
fig = go.Figure()

# Config for Plotly interactive grid
config = {
    'scrollZoom': True,
    'displayModeBar': True,
    'modeBarButtonsToAdd': ['zoom2d', 'pan2d', 'resetScale2d'],
    'responsive': True
}

def get_json_path():
    """Get the absolute path to the zigglescript_commands.json file"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(script_dir, 'zigglescript_commands.json')

undo_stack = []
redo_stack = []

def create_graph(root, project_name, project_id, width, height):
    """Create a grid-based interactive Plotly graph."""
    for widget in root.winfo_children():
        widget.destroy()

    create_command_buttons(root)  # Add command buttons

    input_frame = tk.Frame(root)
    input_frame.pack(side=tk.BOTTOM, fill=tk.X)

    global fig
    fig = go.Figure() 

    # Add grid lines to figure
    x_grid = list(range(0, width + 1, max(1, width // 50)))
    y_grid = list(range(0, height + 1, max(1, height // 50)))
    for x in x_grid:
        fig.add_shape(
            type="line", x0=x, x1=x, y0=0, y1=height, line=dict(color="lightgray", width=1, dash="dash")
        )
    for y in y_grid:
        fig.add_shape(
            type="line", x0=0, x1=width, y0=y, y1=y, line=dict(color="lightgray", width=1, dash="dash")
        )

    fig.update_layout(
        showlegend=False,
        plot_bgcolor='white',
        xaxis=dict(range=[0, width], showgrid=False, zeroline=True, zerolinewidth=2, zerolinecolor='black', tickformat=',.0f'),
        yaxis=dict(range=[0, height], showgrid=False, zeroline=True, zerolinewidth=2, zerolinecolor='black', tickformat=',.0f'),
        margin=dict(l=50, r=50, t=50, b=50),
        dragmode='pan'
    )

    # Temporary save of plot HTML
    temp_dir = Path.home() / "temp_plots"
    temp_dir.mkdir(exist_ok=True)
    plot_path = temp_dir / "grid_plot.html"
    pio.write_html(fig, file=str(plot_path), config=None, include_plotlyjs='cdn', full_html=True)

    input_frame = tk.Frame(root)
    input_frame.pack(side=tk.BOTTOM, fill=tk.X)

    global command_input
    command_input = tk.Text(input_frame, height=5, wrap="word")
    command_input.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5, pady=5)

    execute_button = tk.Button(input_frame, text="Execute", command=submit_command)
    execute_button.pack(side=tk.RIGHT, padx=5, pady=5)

    undo_button = tk.Button(input_frame, text="Undo", command=undo_last_command)
    undo_button.pack(side=tk.RIGHT, padx=5, pady=5)

    redo_button = tk.Button(input_frame, text="Redo", command=redo_last_command)
    redo_button.pack(side=tk.RIGHT, padx=5, pady=5)


def submit_command():
    """Execute the ZiggleScript command entered by the user."""
    command = command_input.get("1.0", tk.END).strip()
    if command:
        try:
            process_zigglescript(command)
            command_input.delete("1.0", tk.END)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to process command: {str(e)}")


def create_text(x1, x2, y1, y2, text, color, font_size):
    x_pos = (x1 + x2) / 2
    y_pos = (y1 + y2) / 2

    fig.add_annotation(
        x=x_pos,
        y=y_pos,
        text=text,
        showarrow=False,
        font=dict(
            size=font_size,
            color=color,
        ),
        xanchor='center',
        yanchor='middle',
    )
    fig.show()


def create_circle(x, y, radius, color, filled=False):
    fig.add_shape(
        type="circle",
        x0=x - radius,
        y0=y - radius,
        x1=x + radius,
        y1=y + radius,
        line=dict(color=color, width=2),
        fillcolor=color if filled else "rgba(255, 255, 255, 0)"
    )
    
    fig.update_layout(
        xaxis=dict(scaleanchor='y'),
        yaxis=dict(scaleratio=1)
    )
    fig.show()


def create_rectangle(x1, x2, y1, y2, color, filled=False):
    fillcolor = color if filled else "rgba(255, 255, 255, 0)"
    line_width = 2 if filled else 1
    fig.add_shape(
        type="rect",
        x0=float(x1),
        x1=float(x2),
        y0=float(y1),
        y1=float(y2),
        line=dict(color=color, width=line_width),
        fillcolor=fillcolor
    )
    fig.show()


def create_line(x1, y1, x2, y2, color):
    fig.add_shape(
        type="line",
        x0=float(x1),
        y0=float(y1),
        x1=float(x2),
        y1=float(y2),
        line=dict(color=color, width=2)
    )
    fig.show()


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


def process_zigglescript(command):
    """Process a single ZiggleScript command."""
    global redo_stack
    redo_stack = []
    
    try:
        command = command.strip("<>")  # Remove <> syntax
        
        command_parts = command.split()
        command_name = " ".join(command_parts[:2])

        # Load command definitions from JSON
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
            x1, x2, y1, y2 = params[:4]  # Coordinates
            text = ' '.join(params[4:-2]).strip('"')  # Text without quotes
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

        else:
            pass

        # Add the executed command to the undo stack
        undo_stack.append({
            'command': command_name,
            'parameters': parameters
        })

    except Exception as e:
        raise Exception(f"Failed to process command: {str(e)}")

def undo_last_command():
    global undo_stack, redo_stack, fig
    if undo_stack:
        last_command = undo_stack.pop()
        redo_stack.append(last_command)
        command_name = last_command['command']
        parameters = last_command['parameters']

        try:
            # Reverse the last command's effects
            if command_name == "CREATE TEXT":
                fig.update_layout(annotations=[a for a in fig['layout']['annotations'] if a['text'] != parameters[4]])
            elif command_name == "CREATE RECTANGLE":
                fig.update_layout(shapes=[s for s in fig['layout']['shapes'] if (s['x0'], s['x1'], s['y0'], s['y1']) != (float(parameters[0]), float(parameters[1]), float(parameters[2]), float(parameters[3]))])
            elif command_name == "CREATE LINE":
                fig.update_layout(shapes=[s for s in fig['layout']['shapes'] if (s['x0'], s['y0'], s['x1'], s['y1']) != (float(parameters[0]), float(parameters[1]), float(parameters[2]), float(parameters[3]))])
            elif command_name == "CREATE CIRCLE":
                fig.update_layout(shapes=[s for s in fig['layout']['shapes'] if (s['x0'], s['y0'], s['x1'], s['y1']) != (float(parameters[0]) - float(parameters[2]), float(parameters[1]) - float(parameters[2]), float(parameters[0]) + float(parameters[2]), float(parameters[1]) + float(parameters[2]))])

            # Update plot
            fig.show()

        except Exception as e:
            messagebox.showerror("Undo Error", f"Failed to undo command: {str(e)}")


def redo_last_command():
    global undo_stack, redo_stack, fig
    if redo_stack:
        last_command = redo_stack.pop()
        undo_stack.append(last_command)
        command_name = last_command['command']
        parameters = last_command['parameters']

        try:
            # Reapply the last undone command's effects
            if command_name == "CREATE TEXT":
                create_text(float(parameters[0]), float(parameters[1]), float(parameters[2]), float(parameters[3]), parameters[4], parameters[5], int(parameters[6]))
            elif command_name == "CREATE RECTANGLE":
                create_rectangle(parameters[0], parameters[1], parameters[2], parameters[3], parameters[4], "FILLED" in parameters)
            elif command_name == "CREATE LINE":
                create_line(float(parameters[0]), float(parameters[1]), float(parameters[2]), float(parameters[3]), parameters[4])
            elif command_name == "CREATE CIRCLE":
                create_circle(float(parameters[0]), float(parameters[1]), float(parameters[2]), parameters[3], "FILLED" in parameters)

            # Update plot
            fig.show()

        except Exception as e:
            messagebox.showerror("Redo Error", f"Failed to redo command: {str(e)}")


def create_command_buttons(root):
    command_frame = tk.Frame(root)
    command_frame.pack(side=tk.TOP, fill=tk.X)

    # Create Rectangle Button
    tk.Button(command_frame, text="CREATE RECTANGLE", 
              command=lambda: command_input.insert(tk.END, "CREATE RECTANGLE x1 x2 y1 y2 color<>")).pack(side=tk.LEFT)

    # Create Line Button
    tk.Button(command_frame, text="CREATE LINE", 
              command=lambda: command_input.insert(tk.END, "CREATE LINE x1 y1 x2 y2 color<>")).pack(side=tk.LEFT)

    # Create Circle Button
    tk.Button(command_frame, text="CREATE CIRCLE", 
              command=lambda: command_input.insert(tk.END, "CREATE CIRCLE x y radius color<>")).pack(side=tk.LEFT)

    tk.Button(command_frame, text="CREATE TEXT", 
            command=lambda: command_input.insert(tk.END, 'CREATE TEXT x1 x2 y1 y2 "text" color font_size')).pack(side=tk.LEFT)


if __name__ == "__main__":
    root = tk.Tk()
    root.title("Welcome to Ziggle")
    root.geometry("1280x720")

    ask_for_project_details(root)
    root.mainloop()