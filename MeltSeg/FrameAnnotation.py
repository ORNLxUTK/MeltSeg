import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from PIL import Image, ImageTk
import math
import json
import os


class ImageAnnotationTool:
    def __init__(self, master, input_frame_dir: str | None):
        self.master = master
        self.master.title("Image Annotation Tool")

        screen_width = self.master.winfo_screenwidth()
        screen_height = self.master.winfo_screenheight()

        window_width = int(screen_width * 0.8)
        window_height = int(screen_height * 0.8)

        position_top = int((screen_height - window_height) / 2)
        position_right = int((screen_width - window_width) / 2)

        self.master.geometry(
            f"{window_width}x{window_height}+{position_right}+{position_top}")
        self.image_path = os.path.join(input_frame_dir, os.listdir(input_frame_dir)[0])
        self.original_image = None
        self.displayed_image = None
        self.photo = None
        self.points = {"Object 1": []}
        self.current_label = 'pos'
        self.current_object = 'Object 1'
        self.scale_factor = 1.0
        self.shapes = ['circle', 'square', 'triangle', 'diamond']

        self.create_widgets()

        self.canvas = tk.Canvas(self.master, bg="white")
        self.canvas.pack(fill=tk.BOTH, expand=True)

        self.canvas.bind("<Button-1>", self.on_left_click)
        self.canvas.bind("<Button-3>", self.on_right_click)

        self.master.bind("<Configure>", self.on_resize)
        self.master.after(100, self.wait_for_canvas_size)
        self.file_path = None

    def create_widgets(self):
        button_frame = tk.Frame(self.master)
        button_frame.pack(fill=tk.X)

        self.toggle_button = tk.Button(button_frame, text="Toggle Pos/Neg",
                                       command=self.toggle_label)
        self.toggle_button.pack(side=tk.LEFT, padx=5, pady=5)

        self.print_button = tk.Button(button_frame, text="Print Points",
                                      command=self.print_points)
        self.print_button.pack(side=tk.LEFT, padx=5, pady=5)

        self.save_button = tk.Button(button_frame, text="Save to JSON",
                                     command=self.save_to_json)
        self.save_button.pack(side=tk.LEFT, padx=5, pady=5)

        self.object_name_entry = tk.Entry(button_frame, width=15)
        self.object_name_entry.pack(side=tk.LEFT, padx=5, pady=5)
        self.object_name_entry.insert(0, self.current_object)

        self.new_object_button = tk.Button(button_frame, text="New Object",
                                           command=self.add_new_object)
        self.new_object_button.pack(side=tk.LEFT, padx=5, pady=5)

        self.object_var = tk.StringVar(value=self.current_object)
        self.object_dropdown = ttk.Combobox(button_frame,
                                            textvariable=self.object_var,
                                            values=[self.current_object])
        self.object_dropdown.pack(side=tk.LEFT, padx=5, pady=5)
        self.object_dropdown.bind("<<ComboboxSelected>>",
                                  self.on_object_selected)

        self.rename_button = tk.Button(button_frame, text="Rename Object",
                                       command=self.rename_object)
        self.rename_button.pack(side=tk.LEFT, padx=5, pady=5)

    def wait_for_canvas_size(self):
        if self.canvas.winfo_width() <= 1 or self.canvas.winfo_height() <= 1:
            # Canvas size not available yet, wait and check again
            self.master.after(100, self.wait_for_canvas_size)
        else:
            # Canvas size is available, proceed with image loading
            self.load_image()

    def load_image(self):
        if self.image_path:
            self.original_image = Image.open(self.image_path)
            self.scale_and_display_image()
            self.points = {}  # Clear existing points
            self.update_object_dropdown()

    def scale_and_display_image(self):
        if self.original_image:
            canvas_width = self.canvas.winfo_width()
            canvas_height = self.canvas.winfo_height()

            width_ratio = canvas_width / self.original_image.width
            height_ratio = canvas_height / self.original_image.height
            self.scale_factor = min(width_ratio, height_ratio)
            new_width = int(self.original_image.width * self.scale_factor)
            new_height = int(self.original_image.height * self.scale_factor)
            self.displayed_image = self.original_image.resize(
                (new_width, new_height), Image.Resampling.LANCZOS)

            self.photo = ImageTk.PhotoImage(self.displayed_image)
            self.canvas.delete("all")
            self.canvas.create_image(0, 0, anchor=tk.NW, image=self.photo)
            self.draw_points()

    def toggle_label(self):
        self.current_label = 'neg' if self.current_label == 'pos' else 'pos'
        self.toggle_button.config(
            text=f"Current: {self.current_label.capitalize()}")

    def on_left_click(self, event):
        if self.displayed_image:
            x, y = event.x, event.y
            original_x = int(x / self.scale_factor)
            original_y = int(y / self.scale_factor)
            if self.current_object not in self.points:
                self.points[self.current_object] = []
            self.points[self.current_object].append(
                (original_x, original_y, self.current_label))
            self.draw_points()

    def on_right_click(self, event):
        if self.displayed_image:
            x, y = event.x, event.y
            original_x = int(x / self.scale_factor)
            original_y = int(y / self.scale_factor)
            self.remove_nearby_point(original_x, original_y)

    def remove_nearby_point(self, x, y):
        for obj, points in self.points.items():
            for point in points:
                # 10 pixel radius for deletion
                if math.sqrt((point[0] - x)**2 + (point[1] - y)**2) < 10:
                    self.points[obj].remove(point)
                    self.draw_points()
                    return

    def draw_points(self):
        self.canvas.delete("point")
        for i, (object_name, object_points) in enumerate(self.points.items()):
            shape = self.shapes[i % len(self.shapes)]
            for x, y, label in object_points:
                scaled_x = int(x * self.scale_factor)
                scaled_y = int(y * self.scale_factor)
                color = "green" if label == 'pos' else "red"
                self.draw_shape(scaled_x, scaled_y, shape, color)

    def draw_shape(self, x, y, shape, color):
        size = 5
        if shape == 'circle':
            self.canvas.create_oval(x-size, y-size, x+size, y+size, fill=color,
                                    outline='black', tags="point")
        elif shape == 'square':
            self.canvas.create_rectangle(x-size, y-size, x+size, y+size,
                                         fill=color, outline='black',
                                         tags="point")
        elif shape == 'triangle':
            self.canvas.create_polygon(x, y-size, x-size, y+size, x+size,
                                       y+size, fill=color, outline='black',
                                       tags="point")
        elif shape == 'diamond':
            self.canvas.create_polygon(x, y-size, x+size, y, x, y+size,
                                       x-size, y, fill=color, outline='black',
                                       tags="point")

    def print_points(self):
        if not self.points:
            messagebox.showinfo("Info", "No points annotated yet.")
            return
        print("Annotated Points:")
        for object_name, object_points in self.points.items():
            print(f"\n{object_name}:")
            for x, y, label in object_points:
                print(f"  Coordinates: ({x}, {y}), "
                      f"Label: {int(label == 'pos')}({label})")

    def save_to_json(self):
        if not self.points:
            messagebox.showinfo("Info", "No points to save.")
            return

        file_path = filedialog.asksaveasfilename(
            defaultextension=".json", filetypes=[("JSON files", "*.json")])
        if not file_path:
            return  # User cancelled the save operation
        self.file_path = file_path
        json_data = {}
        for object_name, object_points in self.points.items():
            coordinates = [[point[0], point[1]] for point in object_points]
            labels = [int(point[2] == "pos") for point in object_points]
            json_data[object_name] = {"coordinates": coordinates,
                                      "labels": labels}

        with open(file_path, 'w') as json_file:
            json.dump(json_data, json_file, indent=2)

        messagebox.showinfo("Success", f"Data saved to {file_path}")

    def on_resize(self, event):
        if self.original_image:
            self.scale_and_display_image()

    def rename_object(self):
        old_name = self.current_object
        new_name = self.object_name_entry.get().strip()
        if not new_name:
            messagebox.showwarning("Warning",
                                   "Please enter a new object name.")
            return
        if new_name in self.points and new_name != old_name:
            messagebox.showwarning("Warning", "Object name already exists.")
            return
        if old_name in self.points:
            self.points[new_name] = self.points.pop(old_name)
            self.current_object = new_name
            self.update_object_dropdown()
            self.object_var.set(new_name)
            messagebox.showinfo("Success",
                                f"Object renamed from '{old_name}'"
                                f"to '{new_name}'")

    def add_new_object(self):
        new_object_name = self.object_name_entry.get().strip()
        if not new_object_name:
            messagebox.showwarning("Warning", "Please enter an object name.")
            return
        if new_object_name in self.points:
            # If the object exists, treat this as a rename operation
            self.rename_object()
        else:
            self.points[new_object_name] = []
            self.current_object = new_object_name
            self.update_object_dropdown()
            self.object_var.set(new_object_name)

    def on_object_selected(self, event):
        self.current_object = self.object_var.get()
        self.object_name_entry.delete(0, tk.END)
        self.object_name_entry.insert(0, self.current_object)

    def update_object_dropdown(self):
        object_list = list(self.points.keys())
        self.object_dropdown['values'] = object_list
        if self.current_object not in object_list:
            self.object_dropdown.set(object_list[0] if object_list else "")

if __name__ == "__main__":
    def main():
        root = tk.Tk()
        ImageAnnotationTool(root, input_frame_dir=None)
        root.mainloop()

    main()
