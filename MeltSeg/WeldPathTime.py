import os
import subprocess
import cv2
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

class VideoProcessing:
    def __init__(self):
        self.video_path = None
        self.output_folder = None
        self.fps = None
        self.process()

    def select_file(self):
        while True:
            file_path = filedialog.askopenfilename(title="Select Video File to Process")
            if not file_path:
                break
            try:
                if os.path.isfile(file_path):
                    self.video_path = file_path
                    return file_path
            except (OSError, IOError) as e:
                messagebox.showinfo("Error", f"Please select a valid video file.")
        messagebox.showinfo("Error", "No file selected.")

    def select_output_folder(self):
        while True:
            folder_path = filedialog.askdirectory(title="Select Output Frames Folder")
            if not folder_path:
                break
            if os.path.isdir(folder_path):
                self.output_folder = folder_path
                return folder_path
            else:
                create = messagebox.askyesno("Create Folder", 
                                             f"The folder '{folder_path}' doesn't exist. Do you want to create it?")
                if create:
                    try:
                        os.makedirs(folder_path)
                        self.output_folder = folder_path
                        return folder_path
                    except OSError:
                        messagebox.showerror("Error", "Failed to create folder. Please try again.")
                else:
                    messagebox.showinfo("Info", "Please select an existing folder or create a new one.")

    def get_fps(self):
        if self.video_path is None:
            messagebox.showinfo("Error", "No video file selected.")
            return None

        video = cv2.VideoCapture(self.video_path)
        fps = video.get(cv2.CAP_PROP_FPS)
        video.release()

        temp_root = tk.Tk()
        temp_root.withdraw()

        dialog = tk.Toplevel(temp_root)
        dialog.title("Select Output FPS")
        screen_width = dialog.winfo_screenwidth()
        screen_height = dialog.winfo_screenheight()
        position_right = int((screen_width - 300) / 2)
        position_top = int((screen_height - 150) / 2)
        dialog.geometry(f"300x150+{position_right}+{position_top}")
        
        tk.Label(dialog, text=f"Input Video FPS: {fps:.1f}").pack(pady=10)
        tk.Label(dialog, text="Output FPS:").pack()
        
        fps_options = list(reversed(range(1, int(fps) + 1)))
        selected_fps = tk.StringVar(dialog)
        selected_fps.set(str(fps_options[0]))
        fps_options = [str(f) for f in fps_options[1:]]
        fps_dropdown = ttk.Combobox(dialog, textvariable=selected_fps, values=fps_options)
        fps_dropdown.pack(pady=10)
        
        def set_fps():
            self.fps = int(selected_fps.get())
            dialog.quit()

        tk.Button(dialog, text="OK", command=set_fps).pack(pady=10)
        
        dialog.protocol("WM_DELETE_WINDOW", dialog.quit)
        dialog.transient(temp_root)
        dialog.grab_set()
        
        # Ensure the dialog is shown and brought to the front
        dialog.update()
        dialog.deiconify()
        dialog.lift()
        dialog.focus_force()

        temp_root.mainloop()

        dialog.destroy()
        temp_root.destroy()

        return self.fps
        
    def extract_frames(self):
        if not all([self.video_path, self.output_folder, self.fps]):
            messagebox.showinfo("Error", "Video path, output folder, or FPS not set.")
            return

        output_pattern = os.path.join(self.output_folder, '%05d.jpg')
        command = [
            'ffmpeg',
            '-i', self.video_path,
            '-vf', f'fps={self.fps}',
            '-q:v', '2',
            '-start_number', '0',
            output_pattern
        ]

        try:
            subprocess.run(command, capture_output=True, text=True, check=True)
            messagebox.showinfo("Success", "Frames extracted successfully.")
        except subprocess.CalledProcessError as e:
            messagebox.showerror("Error", f"Error extracting frames: {e}")

    def process(self):
        self.select_file()
        self.select_output_folder()
        self.get_fps()
        self.extract_frames()


def main():
    VideoProcessing()


if __name__ == '__main__':
    main()
