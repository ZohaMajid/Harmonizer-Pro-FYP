# 🎨 Harmonizer Pro - Final Year Project

Harmonizer Pro is an AI-powered image processing studio built with Python and Flask. It allows users to upload source images and a target theme, blending the color palettes dynamically while offering a 4x High-Definition upscaling feature using Deep Learning.

## Features:
* Smart Harmonization: Context-aware color grading based on a target theme.
* HD AI Upscaling: Utilizes OpenCV DNN to upscale images 4x without losing quality.
* Batch Processing: Group uploads are processed together and organized into distinct project batches.
* Interactive UI: Real-time progress tracking, and a custom before/after image slider.

## Installation & Setup

1. Clone the repository:
   git clone [https://github.com/ZohaMajid/Harmonizer-Pro-FYP.git](https://github.com/ZohaMajid/Harmonizer-Pro-FYP.git)
   cd Harmonizer-Pro-FYP

2. Create a virtual environment and install dependencies:

  python -m venv venv
  venv\Scripts\activate
  pip install flask flask-sqlalchemy opencv-python opencv-contrib-python

CRITICAL: Download the AI Model:
Because the AI model is too large for GitHub, you must download it manually:

  i. Download the EDSR_x4.pb model (approx. 38MB).
 ii. Create a folder named models in the root directory.
iii. Place the EDSR_x4.pb file inside the models folder.

3. Run the Application:
python app.py
The application will be available at http://127.0.0.1:5000
