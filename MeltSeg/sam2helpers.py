import json
import torch
from sam2.sam2_video_predictor import SAM2VideoPredictor
import numpy as np
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from tkinter import ttk
import tkinter as tk
import os
from PIL import Image
import subprocess


class SAM2ModelSelector:
    def __init__(self, parent):
        self.parent = parent
        self.selected_model = tk.StringVar()
        self.result = None
        self.masked_output_dir = None

        # Create the top-level window
        self.top = tk.Toplevel(parent)
        self.top.title("Select SAM2 Model Version")
        screen_width = self.top.winfo_screenwidth()
        screen_height = self.top.winfo_screenheight()
        window_width = 300
        window_height = 200
        position_right = int((screen_width - window_width) / 2)
        position_top = int((screen_height - window_height) / 2)
        self.top.geometry(
            f"{window_width}x{window_height}+{position_right}+{position_top}")
        self.top.resizable(False, False)

        # Make the popup modal
        self.top.grab_set()

        self.create_widgets()
        
        self.video_segments = {}

    def create_widgets(self):
        # Label
        ttk.Label(self.top, text="Choose SAM2 Model Version:",
                  padding=(10, 10)).pack()

        # Radio buttons for model versions
        models = [
            ("SAM2 Tiny", "facebook/sam2.1-hiera-tiny"),
            ("SAM2 Small", "facebook/sam2.1-hiera-small"),
            ("SAM2 Base+", "facebook/sam2.1-hiera-base-plus"),
            ("SAM2 Large", "facebook/sam2.1-hiera-large"),
        ]

        for text, value in models:
            ttk.Radiobutton(self.top, text=text, value=value,
                            variable=self.selected_model).pack(padx=20, pady=5,
                                                               anchor='w')

        # Set default selection
        self.selected_model.set("SAM2 Base+")

        # OK and Cancel buttons
        button_frame = ttk.Frame(self.top, padding=(0, 10))
        button_frame.pack(fill='x')

        ttk.Button(button_frame, text="OK", command=self.on_ok).pack(
            side='right', padx=(0, 10))
        ttk.Button(button_frame, text="Cancel", command=self.on_cancel).pack(
            side='right', padx=(0, 10))

    def on_ok(self):
        self.result = self.selected_model.get()
        self.top.destroy()

    def on_cancel(self):
        self.top.destroy()


class SAM2Boot(SAM2ModelSelector):
    def __init__(self, input_frames_dir_path: None | str = None, 
                 prompts_file_path: None | str = None,
                 output_video_fps: None | int = None):
        self.input_frames_dir_path = input_frames_dir_path
        self.output_video_fps = output_video_fps
        if not self.input_frames_dir_path:
            messagebox.showerror("Error", "No input frames directory selected")
            exit()
        self.root = tk.Tk()
        self.root.withdraw()
        super().__init__(self.root)
        self.root.quit()
        self.device = self.selectdevice()
        self.model_version = self.selectmodelversion()
        self.print_setup()
        self.run(prompts_file_path)
        self.save_video_segments(self.input_frames_dir_path, 0.25)
        self.convert_frames_to_video()

    def selectdevice(self):
        if torch.cuda.is_available():
            device = torch.device("cuda")
        else:
            device = torch.device("cpu")
        return device

    def selectmodelversion(self):
        self.root.wait_window(self.top)
        return self.result

    def print_setup(self):
        print("Selected Input Frames:", self.input_frames_dir_path)
        print("Selected Device:", self.device)
        print("Selected Model Version:", self.model_version)

    def run(self, prompts_file_path: str | None):
        if not prompts_file_path:
            messagebox.showerror("Error", "No prompts file selected")
            exit()
        with open(prompts_file_path, "r") as f:
            prompts = json.load(f)
        predictor = SAM2VideoPredictor.from_pretrained(self.model_version)

        with torch.inference_mode(), torch.autocast(self.device.type,
                                                    dtype=torch.bfloat16):
            state = predictor.init_state(self.input_frames_dir_path)
            for obj_id, (coordinates, labels) in prompts.items():
                points_array = np.array(prompts[obj_id][coordinates],
                                        dtype=np.float32)
                labels_array = np.array(prompts[obj_id][labels],
                                        dtype=np.int64)
                print(f"Processing object {obj_id}: {points_array, labels_array}")
                
                _, _, _ = predictor.add_new_points_or_box(
                    inference_state=state,
                    frame_idx=0,
                    obj_id=obj_id,
                    points=points_array,
                    labels=labels_array
                )
            for out_frame_idx, object_ids, output_masks in predictor.propagate_in_video(state):
                self.video_segments[out_frame_idx] = {
                    out_obj_id: (output_masks[i] > 0.0).cpu().numpy()
                    for i, out_obj_id in enumerate(object_ids)
                }
    
    def save_video_segments(self, frame_video_path: str, alpha: float):
        output_dir = filedialog.askdirectory(
            title="Select Ouput Directory for Masked Video Segments")
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        frame_names = [
            p for p in os.listdir(frame_video_path)
            if os.path.splitext(p)[-1] in [".jpg", ".jpeg", ".JPG", ".JPEG"]
        ]
        frame_names.sort(key=lambda p: int(os.path.splitext(p)[0]))
        
        for frame_idx, masks in self.video_segments.items():
            img = Image.open(os.path.join(frame_video_path, frame_names[frame_idx]))
            img_array = np.array(img).astype(np.float32)
            if img_array.ndim == 2:
                img_array = np.stack([img_array] * 3, axis=-1)
            elif img_array.ndim == 4:
                img_array = img_array.squeeze()
            colors = [
                (255, 0, 0),    # Red
                (0, 255, 0),    # Green
                (0, 0, 255),    # Blue
                (255, 255, 0),  # Yellow
                (255, 0, 255),  # Magenta
                (0, 255, 255),  # Cyan
                (255, 128, 0),  # Orange
                (128, 0, 255),  # Purple
                (0, 255, 128),  # Spring Green
                (255, 128, 128) # Light Pink
            ]
            colored_mask = np.zeros_like(img_array)
            for num_id, (_, mask) in enumerate(masks.items()):
                color = colors[num_id % len(colors)]
                mask_rgb = np.stack([mask.squeeze()] * 3, axis=-1)
                colored_mask += mask_rgb * np.array(color).reshape(1, 1, 3)
            
            colored_mask = colored_mask.astype(np.uint8) # 0-255
            binary_mask = np.any(colored_mask != 0, axis=-1, keepdims=True)
            blended_img = np.where(
                binary_mask,
                (1 - alpha) * img_array + alpha * colored_mask,
                img_array
            )
            final_img = Image.fromarray(blended_img.astype(np.uint8))
            final_img.save(os.path.join(output_dir, f'masked_frame_{frame_idx}.jpg'))
        print(f"Segmented video frames saved to {output_dir}")
        self.masked_output_dir = output_dir
    
    def convert_frames_to_video(self):
        if not self.masked_output_dir:
            messagebox.showerror("Error", "No masked frames directory selected")
            exit()
        video_name = filedialog.asksaveasfilename(
            title="Save Video As",
            filetypes=[("MP4 Files", "*.mp4")]
        )
        if not video_name:
            messagebox.showerror("Error", "No video name selected")
            exit()
        input_pattern = os.path.join(self.masked_output_dir, "masked_frame_%d.jpg")
        command = [
            'ffmpeg',
            '-framerate', str(self.output_video_fps),
            '-i', input_pattern,
            '-c:v', 'h264',
            '-pix_fmt', 'yuv420p',
            '-crf', '23',
            video_name
        ]
        print(command)
        try:
            subprocess.run(command, capture_output=True, text=True, check=True) 
            messagebox.showinfo("Success", "Video created successfully.")
        except subprocess.CalledProcessError as e:
            messagebox.showerror("Error", f"Error creating video: {e}")


if "__main__" == __name__:
    sam2_setup = SAM2Boot(input_frames_dir_path="/home/jwetzel2/ORNL/WeldPoolSeg/Data/Good_Video_Frames",
                          prompts_file_path="/home/jwetzel2/ORNL/WeldPoolSeg/Data/prompts.json",
                          output_video_fps=1)
