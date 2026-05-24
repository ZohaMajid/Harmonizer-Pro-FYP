import os
import uuid
from skimage import io, exposure
from skimage.exposure import match_histograms
import numpy as np
from rembg import remove, new_session
import cv2

session = new_session()

def upscale_to_hd(input_path, output_path):
    # Load a pre-trained Super Resolution model
    sr = cv2.dnn_superres.DnnSuperResImpl_create()
    
    # Path to a pre-trained model file (e.g., EDSR_x4.pb)
    basedir = os.path.abspath(os.path.dirname(__file__))
    model_path = os.path.join(basedir, "models","ESPCN_x4.pb")
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"CRITICAL: Could not find the AI model at {model_path}. Please check your folder structure.")
    # You can download these from OpenCV's official GitHub
    sr.readModel(model_path)
    sr.setModel("espcn", 4) # Upscale by 4x

    img = cv2.imread(input_path)
    result = sr.upsample(img)
    cv2.imwrite(output_path, result)

def process_harmonization(source_paths, target_path, output_folder, smart_mode=True):
    """
    source_path: Path to the single source image
    target_paths: A LIST of paths to multiple target images
    output_folder: Where to save the results
    smart_mode : Boolean (true = protect humans, False = harmonize everything)
    """
    # 1. Load the theme image once
    # We use io.imread which converts the image into a NumPy Array
    target_img = io.imread(target_path)
    if target_img.shape[-1] == 4:
        target_img = cv2.cvtColor(target_img, cv2.COLOR_RGBA2RGB)
    
    results = []

    for s_path in source_paths:
        # Load Source
        source_img = io.imread(s_path)
        h, w = source_img.shape[:2]

        if source_img.shape[-1] == 4:
            source_img = cv2.cvtColor(source_img, cv2.COLOR_RGBA2RGB)
        
        # 1. GLOBAL HARMONIZATION
        # Create the 'Themed' version of the image
        matched = match_histograms(source_img, target_img, channel_axis=-1)
        matched = matched.astype(np.uint8)

        if smart_mode:
            # 2. AI SALIENT OBJECT DETECTION (REMBG)
            with open(s_path, 'rb') as f:
                input_data = f.read()
                # only_mask=True extracts the alpha channel (0-255)
                mask_data = remove(input_data, only_mask=True, session=session)
            
            # Convert bytes to a grayscale mask array
            mask_decoded = np.frombuffer(mask_data, dtype=np.uint8)
            mask_decoded = cv2.imdecode(mask_decoded, cv2.IMREAD_GRAYSCALE)

            # Normalize to 0.0 - 1.0 range
            full_canvas_mask = cv2.resize(mask_decoded, (w, h), interpolation=cv2.INTER_LANCZOS4)
            mask_norm = full_canvas_mask.astype(float) / 255.0
            
            # Soften edges with Gaussian Blur to prevent 'harsh' AI cuts
            mask_blur = cv2.GaussianBlur(mask_norm, (21, 21), 0)
            
            # Expand mask to 3D (RGB)
            mask_3d = np.stack((mask_blur,) * 3, axis=-1)

            # 3. SMART BLENDING LOGIC
            # Background (mask=0) -> 100% Harmonized
            # Foreground Subject (mask=1) -> 20% Harmonized (protects original colors)
            blend_map = mask_3d * 0.2 + (1 - mask_3d) * 1.0
            
            src_float = source_img.astype(float)
            matched_float = matched.astype(float)
            
            # Result = Original * (1 - blend) + Harmonized * blend
            final_calc = (src_float * (1 - blend_map)) + (matched_float * blend_map)
            final_image = np.clip(final_calc, 0, 255).astype(np.uint8)
        else:
            final_image = matched

        # 4. SAVE RESULT
        result_filename = f"full_res_{uuid.uuid4().hex}.jpg"
        result_path = os.path.join(output_folder, result_filename)
        io.imsave(result_path, final_image)
        results.append(result_path)

    return results

   