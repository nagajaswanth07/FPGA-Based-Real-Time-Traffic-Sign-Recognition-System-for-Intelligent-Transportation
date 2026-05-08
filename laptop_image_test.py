import cv2
import numpy as np
import time
import sys
import os
import argparse

# Try to import TFLite, use regular TensorFlow as fallback if tflite_runtime is not installed
try:
    import tflite_runtime.interpreter as tflite
    print("[OK] Using tflite_runtime")
except ImportError:
    try:
        import tensorflow as tf
        tflite = tf.lite
        print("[OK] Using TensorFlow Lite Interpreter")
    except ImportError:
        print("[ERROR] Neither tflite_runtime nor tensorflow is installed.")
        print("Please run: pip install tensorflow opencv-python numpy")
        sys.exit(1)

# GTSRB Class Labels
GTSRB_LABELS = {
    0: "Speed limit (20km/h)",    1: "Speed limit (30km/h)",    2: "Speed limit (50km/h)",
    3: "Speed limit (60km/h)",    4: "Speed limit (70km/h)",    5: "Speed limit (80km/h)",
    6: "End of speed limit (80km/h)",                           7: "Speed limit (100km/h)",
    8: "Speed limit (120km/h)",   9: "No passing",
    10: "No passing for vehicles over 3.5 tons",
    11: "Right-of-way ahead",                                   12: "Priority road",
    13: "Yield",                  14: "Stop",                   15: "No vehicles",
    16: "Vehicles over 3.5 tons prohibited",                    17: "No entry",
    18: "General caution",        19: "Dangerous curve left",
    20: "Dangerous curve right",                                21: "Double curve",
    22: "Bumpy road",             23: "Slippery road",          24: "Road narrows right",
    25: "Road work",              26: "Traffic signals",        27: "Pedestrians",
    28: "Children crossing",      29: "Bicycles crossing",      30: "Beware of ice/snow",
    31: "Wild animals crossing",
    32: "End speed + passing limits",                           33: "Turn right ahead",
    34: "Turn left ahead",        35: "Ahead only",             36: "Go straight or right",
    37: "Go straight or left",    38: "Keep right",             39: "Keep left",
    40: "Roundabout mandatory",   41: "End of no passing",
    42: "End no passing (vehicles over 3.5 tons)"
}

def main():
    # Get the directory where the script is located
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    parser = argparse.ArgumentParser(description="Test TFLite model on local images")
    parser.add_argument("--image", type=str, help="Path to a single image file (e.g. test.jpg)")
    parser.add_argument("--folder", type=str, default=os.path.join(script_dir, "test_images"), 
                        help="Path to a folder of images. Defaults to 'test_images' in the script's folder.")
    args = parser.parse_args()

    # Use script_dir to find the model file regardless of where the command is run from
    model_path = os.path.join(script_dir, "gtsrb_quantized.tflite")
    
    print(f"Loading model: {model_path}...")
    try:
        interpreter = tflite.Interpreter(model_path=model_path)
        interpreter.allocate_tensors()
    except Exception as e:
        print(f"❌ Error loading model: {e}")
        print(f"Make sure 'gtsrb_quantized.tflite' is in: {script_dir}")
        sys.exit(1)

    in_det = interpreter.get_input_details()
    out_det = interpreter.get_output_details()

    # Collect images to test
    images_to_test = []
    
    # Priority 1: Specific image argument
    if args.image and os.path.exists(args.image):
        images_to_test.append(args.image)
    
    # Priority 2: Images in the folder (either specified or default)
    if not images_to_test and os.path.isdir(args.folder):
        for f in os.listdir(args.folder):
            if f.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp')):
                images_to_test.append(os.path.join(args.folder, f))

    if not images_to_test:
        if args.image:
            print(f"[ERROR] Image not found: {args.image}")
        else:
            print(f"[ERROR] No valid images found in: {args.folder}")
            print("Please put some .jpg or .png images in that folder.")
        sys.exit(1)

    print(f"\nFound {len(images_to_test)} image(s) to test. A window will pop up.")
    print("Press ANY KEY to advance to the next image. Press 'q' or 'ESC' to quit.")

    for img_path in images_to_test:
        img = cv2.imread(img_path)
        if img is None:
            print(f"[WARN] Could not read {img_path}")
            continue

        # Resize for display nicely if it's too huge or too small
        h, w = img.shape[:2]
        if w > 800 or h > 800:
            scale = 800 / max(h, w)
            disp_img = cv2.resize(img, (int(w*scale), int(h*scale)))
        elif w < 300 or h < 300:
            scale = 300 / max(h, w)
            disp_img = cv2.resize(img, (int(w*scale), int(h*scale)))
        else:
            disp_img = img.copy()

        # Preprocess for model (always 100x100)
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        img_resized = cv2.resize(img_rgb, (100, 100))

        if in_det[0]['dtype'] == np.float32:
            input_data = np.expand_dims(img_resized, axis=0).astype(np.float32) / 255.0
        else:
            input_data = np.expand_dims(img_resized, axis=0).astype(np.uint8)

        # Infer
        t0 = time.time()
        interpreter.set_tensor(in_det[0]['index'], input_data)
        interpreter.invoke()
        latency_ms = (time.time() - t0) * 1000

        output = interpreter.get_tensor(out_det[0]['index'])[0]
        
        # Calculate Top 5
        top_k = 5
        if out_det[0]['dtype'] == np.float32:
            conf_scores = output
        else:
            conf_scores = output.astype(float) / 255.0
            
        top_indices = np.argsort(conf_scores)[::-1][:top_k]
        pred_class = int(top_indices[0])
        conf = float(conf_scores[pred_class]) * 100

        # Construct Canvas (Matching the requested style)
        # We'll use a white background
        padding_top = 40
        padding_bottom = 150
        dh, dw = disp_img.shape[:2]
        canvas_h = dh + padding_top + padding_bottom
        canvas_w = max(dw, 400) # Ensure enough width for text
        canvas = np.ones((canvas_h, canvas_w, 3), dtype=np.uint8) * 255 # White background
        
        # Center the image horizontally
        x_offset = (canvas_w - dw) // 2
        canvas[padding_top:padding_top+dh, x_offset:x_offset+dw] = disp_img

        # 1. Top Title: "Predicted Class: 00003 (99.06%)"
        class_str = f"{pred_class:05d}"
        title_text = f"Predicted Class: {class_str}  ({conf:.2f}%)"
        font = cv2.FONT_HERSHEY_SIMPLEX
        text_size = cv2.getTextSize(title_text, font, 0.7, 1)[0]
        text_x = (canvas_w - text_size[0]) // 2
        cv2.putText(canvas, title_text, (text_x, 30), font, 0.7, (0, 0, 0), 2, cv2.LINE_AA)

        # 2. Bottom List: "Top-5 predictions:"
        list_y = padding_top + dh + 30
        cv2.putText(canvas, "Top-5 predictions:", (10, list_y), font, 0.6, (0, 0, 0), 1, cv2.LINE_AA)
        
        for i, idx in enumerate(top_indices):
            c_score = float(conf_scores[idx]) * 100
            line_text = f"{int(idx):05d} -> {c_score:.2f}%"
            cv2.putText(canvas, line_text, (10, list_y + 25 + (i * 20)), font, 0.5, (0, 0, 0), 1, cv2.LINE_AA)

        # Print to console as well
        label = GTSRB_LABELS.get(pred_class, "Unknown")
        print(f"[{os.path.basename(img_path)}] -> {label} ({conf:.1f}%) in {latency_ms:.1f}ms")

        # Save result image to test_images/results subfolder
        result_dir = os.path.join(script_dir, "test_images", "results")
        os.makedirs(result_dir, exist_ok=True)
        base_name = os.path.splitext(os.path.basename(img_path))[0]
        save_path = os.path.join(result_dir, f"result_{base_name}.png")
        cv2.imwrite(save_path, canvas)
        print(f"  -> Saved result to: {save_path}")

        cv2.imshow("PYNQ Laptop Offline Image Test", canvas)
        
        # Wait for key press
        key = cv2.waitKey(0) & 0xFF
        if key == 27 or key == ord('q'):  # ESC or q
            print("Quitting early...")
            break

    cv2.destroyAllWindows()
    print("Done!")

if __name__ == "__main__":
    main()
