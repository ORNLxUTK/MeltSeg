from WeldPathTime import VideoProcessing
from FrameAnnotation import ImageAnnotationTool
import tkinter as tk
from sam2helpers import SAM2Boot

if __name__ == "__main__":
    video_preprocessing = VideoProcessing()
    root = tk.Tk()
    frameannotation = ImageAnnotationTool(root,
                                          video_preprocessing.output_folder)
    root.mainloop()
    sam2 = SAM2Boot(video_preprocessing.output_folder,
                    frameannotation.file_path, video_preprocessing.fps)
