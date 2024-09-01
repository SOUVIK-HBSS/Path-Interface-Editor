import tkinter as tk
from tkinter import ttk

# Define the initial grid size and zoom factor
GRID_SIZE = 20
ZOOM_FACTOR = 1.2

# Define colors using RGB values
COLORS = {
    "grid": "#D3D3D3",  # light grey
    "path": "#A9A9A9",  # dark grey
    "point": "#000000",  # black
    "hover": "#FF0000",  # red
    "dotted_line": "#FF0000",  # red
    "highlight": "#ADD8E6",  # light blue
    "lane": "#808080",  # grey
    "footpath": "#A52A2A",  # brown
    "median": "#FFD700",  # gold
    "shoulder": "#8B4513"  # saddle brown
}

class EditablePathInterface(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Editable Path Interface")
        
        # Create a frame for the buttons and canvas
        self.button_frame = tk.Frame(self)
        self.button_frame.pack(side=tk.TOP, fill=tk.X)
        
        # Create the canvas with a label
        self.canvas_frame = tk.Frame(self)
        self.canvas_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.canvas_label = tk.Label(self.canvas_frame, text="Viewport")
        self.canvas_label.pack()
        self.canvas = tk.Canvas(self.canvas_frame, bg="white")
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
        # Create the outliner and properties window frame
        self.side_frame = tk.Frame(self)
        self.side_frame.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Create the outliner with a label
        self.outliner_label = tk.Label(self.side_frame, text="Outliner")
        self.outliner_label.pack()
        self.outliner = tk.Listbox(self.side_frame, width=30, height=20)
        self.outliner.pack(fill=tk.Y)
        self.outliner.bind("<<ListboxSelect>>", self.on_outliner_select)
        
        # Create the properties window
        self.properties_label = tk.Label(self.side_frame, text="Properties")
        self.properties_label.pack()
        self.properties_frame = tk.Frame(self.side_frame)
        self.properties_frame.pack(fill=tk.X)
        self.properties = {}
        self.create_properties_widgets()
        
        self.paths = []
        self.path_properties = []
        self.last_point = None
        self.hover_point = None
        self.current_zoom = 1
        self.adding_path = False
        self.dotted_line = None
        self.pan_start = None
        self.pan_offset = [0, 0]
        self.selected_path_index = None
        
        self.canvas.bind("<Button-1>", self.on_click)
        self.canvas.bind("<Motion>", self.on_motion)
        self.bind("<Escape>", self.finish_path)
        
        self.draw_grid()
        
        # Add buttons to the button frame
        tk.Button(self.button_frame, text="Add Path", command=self.add_path).pack(side=tk.LEFT)
        tk.Button(self.button_frame, text="Clear Points", command=self.clear_points).pack(side=tk.LEFT)
        tk.Button(self.button_frame, text="Zoom In", command=self.zoom_in).pack(side=tk.LEFT)
        tk.Button(self.button_frame, text="Zoom Out", command=self.zoom_out).pack(side=tk.LEFT)
        tk.Button(self.button_frame, text="Pan Canvas", command=self.enable_pan).pack(side=tk.LEFT)

    def create_properties_widgets(self):
        properties = [
            "Number of Lanes (Per Direction)",
            "Lane Width",
            "Footpath Size",
            "Median Width",
            "Shoulder Width",
            "Road Markings",
            "Traffic Signs and Signals",
            "Parking Lanes",
            "Greenery"
        ]
        for prop in properties:
            frame = tk.Frame(self.properties_frame)
            frame.pack(fill=tk.X)
            label = tk.Label(frame, text=prop, width=25, anchor='w')
            label.pack(side=tk.LEFT)
            entry = tk.Entry(frame)
            entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
            self.properties[prop] = entry
        
        apply_button = tk.Button(self.properties_frame, text="Apply", command=self.apply_properties)
        apply_button.pack()

    def snap_to_grid(self, x, y):
        return (round(x / GRID_SIZE) * GRID_SIZE, round(y / GRID_SIZE) * GRID_SIZE)

    def draw_grid(self):
        self.canvas.delete("grid")
        width = self.canvas.winfo_width()
        height = self.canvas.winfo_height()
        for x in range(-width * 2, width * 3, GRID_SIZE):
            self.canvas.create_line(x * self.current_zoom, -height * 2, x * self.current_zoom, height * 3, fill=COLORS["grid"], tags="grid")
        for y in range(-height * 2, height * 3, GRID_SIZE):
            self.canvas.create_line(-width * 2, y * self.current_zoom, width * 3, y * self.current_zoom, fill=COLORS["grid"], tags="grid")

    def draw_paths(self):
        self.canvas.delete("path")
        for i, path in enumerate(self.paths):
            color = COLORS["highlight"] if i == self.selected_path_index else COLORS["path"]
            for j in range(len(path) - 1):
                self.canvas.create_line(path[j][0] * self.current_zoom, path[j][1] * self.current_zoom,
                                        path[j+1][0] * self.current_zoom, path[j+1][1] * self.current_zoom,
                                        fill=color, width=3, tags="path")
            for point in path:
                point_color = COLORS["highlight"] if i == self.selected_path_index else COLORS["point"]
                self.canvas.create_oval(point[0] * self.current_zoom - 5, point[1] * self.current_zoom - 5,
                                        point[0] * self.current_zoom + 5, point[1] * self.current_zoom + 5,
                                        fill=point_color, tags="path")
            if i == self.selected_path_index:
                self.draw_road_properties(path, self.path_properties[i])

    def draw_road_properties(self, path, properties):
        if not path or not properties:
            return
        lane_width = float(properties.get("Lane Width", 3.5))
        footpath_size = float(properties.get("Footpath Size", 1.5))
        median_width = float(properties.get("Median Width", 2.0))
        shoulder_width = float(properties.get("Shoulder Width", 1.0))
        lanes_per_direction = int(properties.get("Number of Lanes (Per Direction)", 2))

        total_road_width = (lanes_per_direction * 2 * lane_width) + (2 * footpath_size) + median_width + (2 * shoulder_width)
        half_road_width = total_road_width / 2

        for i in range(len(path) - 1):
            x1, y1 = path[i]
            x2, y2 = path[i + 1]
            dx = x2 - x1
            dy = y2 - y1
            length = (dx**2 + dy**2)**0.5
            ux = dx / length
            uy = dy / length

            # Draw footpaths
            self.canvas.create_line((x1 - uy * half_road_width) * self.current_zoom, (y1 + ux * half_road_width) * self.current_zoom,
                                    (x2 - uy * half_road_width) * self.current_zoom, (y2 + ux * half_road_width) * self.current_zoom,
                                    fill=COLORS["footpath"], width=footpath_size * self.current_zoom, tags="path")
            self.canvas.create_line((x1 + uy * half_road_width) * self.current_zoom, (y1 - ux * half_road_width) * self.current_zoom,
                                    (x2 + uy * half_road_width) * self.current_zoom, (y2 - ux * half_road_width) * self.current_zoom,
                                    fill=COLORS["footpath"], width=footpath_size * self.current_zoom, tags="path")

            # Draw shoulders
            self.canvas.create_line((x1 - uy * (half_road_width - footpath_size)) * self.current_zoom, (y1 + ux * (half_road_width - footpath_size)) * self.current_zoom,
                                    (x2 - uy * (half_road_width - footpath_size)) * self.current_zoom, (y2 + ux * (half_road_width - footpath_size)) * self.current_zoom,
                                    fill=COLORS["shoulder"], width=shoulder_width * self.current_zoom, tags="path")
            self.canvas.create_line((x1 + uy * (half_road_width - footpath_size)) * self.current_zoom, (y1 - ux * (half_road_width - footpath_size)) * self.current_zoom,
                                    (x2 + uy * (half_road_width - footpath_size)) * self.current_zoom, (y2 - ux * (half_road_width - footpath_size)) * self.current_zoom,
                                    fill=COLORS["shoulder"], width=shoulder_width * self.current_zoom, tags="path")

            # Draw lanes
            for lane in range(lanes_per_direction):
                offset = footpath_size + shoulder_width + (lane + 0.5) * lane_width
                self.canvas.create_line((x1 - uy * (half_road_width - offset)) * self.current_zoom, (y1 + ux * (half_road_width - offset)) * self.current_zoom,
                                        (x2 - uy * (half_road_width - offset)) * self.current_zoom, (y2 + ux * (half_road_width - offset)) * self.current_zoom,
                                        fill=COLORS["lane"], width=lane_width * self.current_zoom, tags="path")
                self.canvas.create_line((x1 + uy * (half_road_width - offset)) * self.current_zoom, (y1 - ux * (half_road_width - offset)) * self.current_zoom,
                                        (x2 + uy * (half_road_width - offset)) * self.current_zoom, (y2 - ux * (half_road_width - offset)) * self.current_zoom,
                                        fill=COLORS["lane"], width=lane_width * self.current_zoom, tags="path")

            # Draw median
            self.canvas.create_line((x1 - uy * median_width / 2) * self.current_zoom, (y1 + ux * median_width / 2) * self.current_zoom,
                                    (x2 - uy * median_width / 2) * self.current_zoom, (y2 + ux * median_width / 2) * self.current_zoom,
                                    fill=COLORS["median"], width=median_width * self.current_zoom, tags="path")
            self.canvas.create_line((x1 + uy * median_width / 2) * self.current_zoom, (y1 - ux * median_width / 2) * self.current_zoom,
                                    (x2 + uy * median_width / 2) * self.current_zoom, (y2 - ux * median_width / 2) * self.current_zoom,
                                    fill=COLORS["median"], width=median_width * self.current_zoom, tags="path")

    def on_click(self, event):
        if not self.adding_path:
            return
        x, y = self.snap_to_grid(self.canvas.canvasx(event.x) / self.current_zoom, self.canvas.canvasy(event.y) / self.current_zoom)
        if self.hover_point:
            self.canvas.delete(self.hover_point)
        self.hover_point = self.canvas.create_oval(x * self.current_zoom - 5, y * self.current_zoom - 5,
                                                   x * self.current_zoom + 5, y * self.current_zoom + 5,
                                                   outline=COLORS["hover"], width=2)
        if self.paths:
            if len(self.paths[-1]) > 0 and (x, y) == self.paths[-1][0]:
                self.paths[-1].append((x, y))
                self.canvas.create_line(self.paths[-1][-2][0] * self.current_zoom, self.paths[-1][-2][1] * self.current_zoom,
                                        self.paths[-1][-1][0] * self.current_zoom, self.paths[-1][-1][1] * self.current_zoom,
                                        fill=COLORS["path"], width=3, tags="path")
                self.canvas.create_oval(x * self.current_zoom - 5, y * self.current_zoom - 5,
                                        x * self.current_zoom + 5, y * self.current_zoom + 5,
                                        fill=COLORS["point"], tags="path")
                self.last_point = None
                self.add_path()  # Automatically start a new path
            else:
                if (x, y) not in self.paths[-1]:
                    self.paths[-1].append((x, y))
                    if len(self.paths[-1]) > 1:
                        self.canvas.create_line(self.paths[-1][-2][0] * self.current_zoom, self.paths[-1][-2][1] * self.current_zoom,
                                                self.paths[-1][-1][0] * self.current_zoom, self.paths[-1][-1][1] * self.current_zoom,
                                                fill=COLORS["path"], width=3, tags="path")
                    self.canvas.create_oval(x * self.current_zoom - 5, y * self.current_zoom - 5,
                                            x * self.current_zoom + 5, y * self.current_zoom + 5,
                                            fill=COLORS["point"], tags="path")
                    self.last_point = (x, y)
        self.update_outliner()

    def on_motion(self, event):
        if not self.adding_path:
            return
        x, y = self.snap_to_grid(self.canvas.canvasx(event.x) / self.current_zoom, self.canvas.canvasy(event.y) / self.current_zoom)
        if self.hover_point:
            self.canvas.delete(self.hover_point)
        self.hover_point = self.canvas.create_oval(x * self.current_zoom - 5, y * self.current_zoom - 5,
                                                   x * self.current_zoom + 5, y * self.current_zoom + 5,
                                                   outline=COLORS["hover"], width=2)
        if self.dotted_line:
            self.canvas.delete(self.dotted_line)
        if self.last_point:
            self.dotted_line = self.canvas.create_line(self.last_point[0] * self.current_zoom, self.last_point[1] * self.current_zoom,
                                                       x * self.current_zoom, y * self.current_zoom,
                                                       fill=COLORS["dotted_line"], dash=(4, 2), width=3)

    def on_pan(self, event):
        if self.pan_start:
            dx = event.x - self.pan_start[0]
            dy = event.y - self.pan_start[1]
            self.canvas.scan_dragto(self.pan_offset[0] + dx, self.pan_offset[1] + dy, gain=1)
        else:
            self.pan_start = (event.x, event.y)

    def finish_path(self, event):
        if self.adding_path:
            self.adding_path = False
            self.last_point = None
            if self.hover_point:
                self.canvas.delete(self.hover_point)
                self.hover_point = None
            if self.dotted_line:
                self.canvas.delete(self.dotted_line)
                self.dotted_line = None
            if len(self.paths[-1]) > 1 and self.paths[-1][0] == self.paths[-1][-1]:
                self.paths[-1].pop()  # Remove the last point if it is the same as the first point
            if len(self.paths[-1]) == 0:
                self.paths.pop()
            self.update_outliner()

    def update_outliner(self):
        self.outliner.delete(0, tk.END)
        for i, path in enumerate(self.paths):
            if len(path) > 0:
                self.outliner.insert(tk.END, f"Path {i+1}: {len(path) - 1} points")

    def add_path(self):
        self.paths.append([])
        self.path_properties.append({})
        self.last_point = None
        self.adding_path = True
        self.canvas.unbind("<B1-Motion>")

    def clear_points(self):
        self.paths.clear()
        self.path_properties.clear()
        self.canvas.delete("all")
        self.draw_grid()
        self.last_point = None
        self.hover_point = None
        self.dotted_line = None
        self.update_outliner()
        self.adding_path = False
        self.canvas.unbind("<B1-Motion>")

    def zoom_in(self):
        self.current_zoom *= ZOOM_FACTOR
        self.canvas.delete("all")
        self.draw_grid()
        self.draw_paths()
        self.canvas.unbind("<B1-Motion>")

    def zoom_out(self):
        self.current_zoom /= ZOOM_FACTOR
        self.canvas.delete("all")
        self.draw_grid()
        self.draw_paths()
        self.canvas.unbind("<B1-Motion>")

    def enable_pan(self):
        self.canvas.bind("<B1-Motion>", self.on_pan)
        self.canvas.bind("<ButtonRelease-1>", self.reset_pan)

    def reset_pan(self, event):
        if self.pan_start:
            dx = event.x - self.pan_start[0]
            dy = event.y - self.pan_start[1]
            self.pan_offset[0] += dx
            self.pan_offset[1] += dy
        self.pan_start = None

    def on_outliner_select(self, event):
        selection = event.widget.curselection()
        if selection:
            self.selected_path_index = selection[0]
            self.draw_paths()
            self.update_properties()

    def update_properties(self):
        if self.selected_path_index is not None:
            properties = self.path_properties[self.selected_path_index]
            for key, entry in self.properties.items():
                entry.delete(0, tk.END)
                entry.insert(0, properties.get(key, ""))

    def apply_properties(self):
        if self.selected_path_index is not None:
            properties = self.path_properties[self.selected_path_index]
            for key, entry in self.properties.items():
                properties[key] = entry.get()
            self.draw_paths()

if __name__ == "__main__":
    app = EditablePathInterface()
    app.mainloop()
