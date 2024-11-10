import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import os
import json
import uuid
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.patches import Rectangle, Circle
from matplotlib.lines import Line2D

# Global Plotly figure instance
fig = None
ax = None
width = 0
height = 0

undo_stack = []
redo_stack = []

class GraphPlot:
    def __init__(self, root, project_name, project_id, width_val, height_val):
        self.root = root
        self.project_name = project_name
        self.project_id = project_id
        self.width_val = width_val
        self.height_val = height_val

        self.create_graph()

    def create_graph(self):
        for widget in self.root.winfo_children():
            widget.destroy()

        create_command_buttons(self.root)

        input_frame = tk.Frame(self.root)
        input_frame.pack(side=tk.BOTTOM, fill=tk.X)

        global fig, ax
        fig, ax = plt.subplots(figsize=(8, 8), dpi=100)

        canvas = FigureCanvasTkAgg(fig, master=self.root)
        canvas.draw()
        canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)

        ax.grid(True)
        ax.set_xlim(0, self.width_val)
        ax.set_ylim(0, self.height_val)

        ax.set_aspect('equal')

        self.cidpress = canvas.mpl_connect('button_press_event', self.on_press)
        self.cidrelease = canvas.mpl_connect('button_release_event', self.on_release)
        self.cidmotion = canvas.mpl_connect('motion_notify_event', self.on_motion)

        input_frame = tk.Frame(self.root)
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

        center_button = tk.Button(input_frame, text="Center", command=self.center_view)
        center_button.pack(side=tk.RIGHT, padx=5, pady=5)

        self.x0 = None
        self.y0 = None
        self.xCenter = None
        self.yCenter = None
        self.xWidth = None
        self.yHeight = None

    def on_press(self, event):
        if event.button == 1:  # left mouse button
            self.x0 = event.xdata
            self.y0 = event.ydata
        elif event.button == 3:  # right mouse button
            self.xCenter = (ax.get_xlim()[0] + ax.get_xlim()[1]) / 2
            self.yCenter = (ax.get_ylim()[0] + ax.get_ylim()[1]) / 2
            self.xWidth = ax.get_xlim()[1] - ax.get_xlim()[0]
            self.yHeight = ax.get_ylim()[1] - ax.get_ylim()[0]

    def on_motion(self, event):
        if self.x0 is not None and self.y0 is not None:
            dx = event.xdata - self.x0
            dy = event.ydata - self.y0
            ax.set_xlim(ax.get_xlim()[0] - dx, ax.get_xlim()[1] - dx)
            ax.set_ylim(ax.get_ylim()[0] - dy, ax.get_ylim()[1] - dy)
            fig.canvas.draw_idle()
            self.x0 = event.xdata
            self.y0 = event.ydata

    def on_release(self, event):
        if event.button == 3:  # right mouse button
            xLim = ax.get_xlim()
            yLim = ax.get_ylim()
            ax.set_xlim(self.xCenter - self.xWidth / 2 * 0.9, self.xCenter + self.xWidth / 2 * 0.9)
            ax.set_ylim(self.yCenter - self.yHeight / 2 * 0.9, self.yCenter + self.yHeight / 2 * 0.9)
            fig.canvas.draw_idle()
        self.x0 = None
        self.y0 = None

    def center_view(self):
        ax.set_xlim(0, self.width_val)
        ax.set_ylim(0, self.height_val)
        fig.canvas.draw_idle()


import matplotlib.pyplot as plt

def create_text(x1, x2, y1, y2, text, color, font_size):
    x_pos = (x1 + x2) / 2
    y_pos = (y1 + y2) / 2

    plt.text(x_pos, y_pos, text, ha='center', va='center', color=color, fontsize=font_size)


def create_rectangle(x1, x2, y1, y2, color, filled=False):
    rect = Rectangle((x1, y1), x2-x1, y2-y1, linewidth=1, edgecolor=color, facecolor=color if filled else 'none')
    ax.add_patch(rect)


def create_line(x1, y1, x2, y2, color):
    line = Line2D([x1, x2], [y1, y2], color=color, linewidth=2)
    ax.add_line(line)


def create_circle(x, y, radius, color, filled=False):
    circle = Circle((x, y), radius, edgecolor=color, facecolor=color if filled else 'none', linewidth=1)
    ax.add_patch(circle)


def submit_command():
    command = command_input.get("1.0", tk.END).strip()
    if command.endswith("<>"):
        try:
            commands = command.replace("<>", "\n").splitlines()
            for cmd in commands:
                cmd = cmd.strip()
                if cmd:
                    process_zigglescript_command(cmd)
            command_input.delete("1.0", tk.END)
            fig.canvas.draw_idle()
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

        undo_stack.append({
            'command': command_name,
            'parameters': parameters
        })

    except json.JSONDecodeError as e:
        messagebox.showerror("JSON Error", f"Failed to parse JSON: {str(e)}")
    except Exception as e:
        messagebox.showerror("Command Error", f"Failed to process command: {str(e)}")


def undo_last_command():
    global undo_stack, redo_stack, ax
    if undo_stack:
        last_command = undo_stack.pop()
        redo_stack.append(last_command)
        command_name = last_command['command']
        parameters = last_command['parameters']

        ax.clear()
        ax.grid(True)
        ax.set_xlim(0, width)
        ax.set_ylim(0, height)
        ax.set_aspect('equal')

        for command in undo_stack:
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

        fig.canvas.draw_idle()


def redo_last_command():
    global undo_stack, redo_stack, ax
    if redo_stack:
        last_command = redo_stack.pop()
        undo_stack.append(last_command)
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

        fig.canvas.draw_idle()


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
        width_val = width_entry.get()
        height_val = height_entry.get()
        filename = filename_entry.get().strip()

        try:
            width_val = int(width_val)
            height_val = int(height_val)
            if width_val <= 0 or height_val <= 0:
                raise ValueError("Width and height must be positive integers.")
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
            ziggle_file.write(f'height = "{height_val}"\n')
            ziggle_file.write(f'width = "{width_val}"\n')

        messagebox.showinfo("Project Created", f"Project '{filename}' created successfully!")
        dialog.destroy()
        
        project = GraphPlot(root, filename, project_id, width_val, height_val)

    ttk.Button(dialog, text="Submit", command=on_submit).grid(row=3, columnspan=2, pady=10)


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