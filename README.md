# MeltSeg - GUI Interface for SAM2

## [Overview](#overview) | [Installation Requirements](#installation-requirements) | [Usage](#usage)

### Overview

[SAM2](https://github.com/facebookresearch/sam2), released by META AI, is a deep learning framework for video segmentation. The model can segment objects in a video using a series of input point labels on an initial frame. Using the initial frame and input points, the model generates a segmentation mask for each labeled object and propagates the segmented masks throughout the frames of the video. For a more in-depth discussion of the mechanisms behind SAM2 and its architecture, see their [paper](https://ai.meta.com/research/publications/sam-2-segment-anything-in-images-and-videos/).

Since SAM2 is a powerful state-of-the-art tool for video segmentation, this repo streamlines video frame splitting, the generation of input labels, and creation of the output segmentation video.

Though designed specifically for welding videos, this package can be used for other video domains. (Preprocessing may be required depending on the input video).

### Installation Requirements

1. Create a [`conda`](https://docs.conda.io/projects/conda/en/latest/user-guide/tasks/manage-environments.html) environment
2. Install `python>=3.10` and [`torch>=2.3.1`](https://pytorch.org/get-started/locally/)
3. Clone the [SAM2 GitHub Repo](https://github.com/facebookresearch/sam2)
4. Follow installation instructions within SAM2's `README.md`
5. Ensure [ffmpeg](https://anaconda.org/conda-forge/ffmpeg) is installed
6. Reference `requirements.txt` for remaining package requirements

### Usage

- Run from repo root: `python3 MeltSeg/main.py`
