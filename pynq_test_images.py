"""
pynq_test_images.py
====================
Run Traffic Sign Recognition on PYNQ-Z2 WITHOUT a camera.
Uses static GTSRB test images downloaded from the internet OR
placed in a local 'test_images/' folder.

NO overlay / NO VDMA / NO camera required.
Runs purely on the ARM Cortex-A9 (PS side).

Usage:
  python3 pynq_test_images.py                        # auto-downloads test images
  python3 pynq_test_images.py --images test_images/  # use local folder
"""

import os
import sys
import time
import argparse
import urllib.request
import numpy as np
import cv2
try:
    import tflite_runtime.interpreter as tflite
except ImportError:
    import tensorflow as tf
    tflite = tf.lite

# ---------------------------------------------------------
# GTSRB Class Labels (43 classes)
# ---------------------------------------------------------
GTSRB_LABELS = {
    0: "Speed limit (20km/h)",    1: "Speed limit (30km/h)",    2: "Speed limit (50km/h)",
    3: "Speed limit (60km/h)",    4: "Speed limit (70km/h)",    5: "Speed limit (80km/h)",
    6: "End of speed limit (80km/h)",                           7: "Speed limit (100km/h)",
    8: "Speed limit (120km/h)",   9: "No passing",
    10: "No passing for vehicles over 3.5 metric tons",
    11: "Right-of-way at the next intersection",                12: "Priority road",
    13: "Yield",                  14: "Stop",                   15: "No vehicles",
    16: "Vehicles over 3.5 metric tons prohibited",             17: "No entry",
    18: "General caution",        19: "Dangerous curve to the left",
    20: "Dangerous curve to the right",                         21: "Double curve",
    22: "Bumpy road",             23: "Slippery road",          24: "Road narrows on the right",
    25: "Road work",              26: "Traffic signals",         27: "Pedestrians",
    28: "Children crossing",      29: "Bicycles crossing",       30: "Beware of ice/snow",
    31: "Wild animals crossing",
    32: "End of all speed and passing limits",                  33: "Turn right ahead",
    34: "Turn left ahead",        35: "Ahead only",             36: "Go straight or right",
    37: "Go straight or left",    38: "Keep right",             39: "Keep left",
    40: "Roundabout mandatory",   41: "End of no passing",
    42: "End of no passing by vehicles over 3.5 metric tons"
}

# ---------------------------------------------------------
# Sample GTSRB test images (publicly available via GitHub)
# Format: (url, expected_class_id)
# ---------------------------------------------------------
SAMPLE_IMAGES = [
    # Stop sign (class 14)
    ("https://upload.wikimedia.org/wikipedia/commons/thumb/f/f9/STOP_sign.jpg/240px-STOP_sign.jpg", 14),
    # Speed limit 50 (class 2)
    ("https://upload.wikimedia.org/wikipedia/commons/thumb/4/47/Speed_limit_50_sign.svg/240px-Speed_limit_50_sign.svg.png", 2),
    # No entry (class 17)
    ("https://upload.wikimedia.org/wikipedia/commons/thumb/d/d5/No_entry_road_sign.jpg/240px-No_entry_road_sign.jpg", 17),
    # Yield (class 13)
    ("https://upload.wikimedia.org/wikipedia/commons/thumb/7/72/MUTCD_R1-2.svg/240px-MUTCD_R1-2.svg.png", 13),
    # General caution (class 18)
    ("https://upload.wikimedia.org/wikipedia/commons/thumb/0/07/Caution_Sign_Yellow.svg/240px-Caution_Sign_Yellow.svg.png", 18),
]


def download_test_images(save_dir="test_images"):
    """Download sample traffic sign images for testing."""
    os.makedirs(save_dir, exist_ok=True)
    downloaded = []

    print(f"\n📥 Downloading {len(SAMPLE_IMAGES)} test images to '{save_dir}/'...\n")
    for i, (url, class_id) in enumerate(SAMPLE_IMAGES):
        filename = os.path.join(save_dir, f"test_{i:02d}_class{class_id:02d}.jpg")
        if os.path.exists(filename):
            print(f"  ✅ Already exists: {filename}")
            downloaded.append((filename, class_id))
            continue
        try:
            urllib.request.urlretrieve(url, filename)
            print(f"  ✅ Downloaded: {filename}  (expected class {class_id}: {GTSRB_LABELS[class_id]})")
            downloaded.append((filename, class_id))
        except Exception as e:
            print(f"  ⚠️  Failed to download {url}: {e}")

    return downloaded


def load_local_images(folder):
    """Load all jpg/png images from a local folder."""
    exts = ('.jpg', '.jpeg', '.png', '.bmp')
    images = []
    for fn in sorted(os.listdir(folder)):
        if fn.lower().endswith(exts):
            images.append((os.path.join(folder, fn), -1))  # -1 = unknown class
    return images


def preprocess(img_bgr, input_dtype):
    """Resize to 100x100 and format for TFLite."""
    img_rgb     = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
    img_resized = cv2.resize(img_rgb, (100, 100))
    if input_dtype == np.float32:
        return np.expand_dims(img_resized, axis=0).astype(np.float32) / 255.0
    else:
        return np.expand_dims(img_resized, axis=0).astype(np.uint8)


def run_inference_on_images(image_list, model_path="gtsrb_quantized.tflite"):
    """Load TFLite model and run inference on each image."""

    # Load model
    print(f"\n🔧 Loading model: {model_path}")
    interpreter = tflite.Interpreter(model_path=model_path)
    interpreter.allocate_tensors()
    in_det  = interpreter.get_input_details()
    out_det = interpreter.get_output_details()
    print(f"   Input shape : {in_det[0]['shape']}")
    print(f"   Input dtype : {in_det[0]['dtype']}")

    results = []
    print(f"\n{'='*75}")
    print(f"  {'#':<4}  {'Image':<28}  {'Predicted Sign':<38}  {'Conf':>6}  {'ms':>6}")
    print(f"{'='*75}")

    for idx, (img_path, expected_class) in enumerate(image_list):
        img = cv2.imread(img_path)
        if img is None:
            print(f"  {idx+1:<4}  {os.path.basename(img_path):<28}  [ERROR: cannot read image]")
            continue

        input_data = preprocess(img, in_det[0]['dtype'])

        t0 = time.time()
        interpreter.set_tensor(in_det[0]['index'], input_data)
        interpreter.invoke()
        latency_ms = (time.time() - t0) * 1000

        output = interpreter.get_tensor(out_det[0]['index'])[0]
        pred   = int(np.argmax(output))

        if out_det[0]['dtype'] == np.float32:
            confidence = float(output[pred]) * 100
        else:
            confidence = float(output[pred]) / 255.0 * 100

        label  = GTSRB_LABELS.get(pred, f"Class {pred}")
        match  = "✅" if expected_class == pred else ("❓" if expected_class == -1 else "❌")

        print(f"  {idx+1:<4}  {os.path.basename(img_path):<28}  {match} {label:<36}  {confidence:>5.1f}%  {latency_ms:>5.1f}")

        results.append({
            "image":      os.path.basename(img_path),
            "predicted":  label,
            "class_id":   pred,
            "confidence": confidence,
            "latency_ms": latency_ms,
            "correct":    (expected_class == pred)
        })

    print(f"{'='*75}")

    if results:
        avg_lat  = np.mean([r["latency_ms"] for r in results])
        avg_conf = np.mean([r["confidence"] for r in results])
        correct  = sum(1 for r in results if r["correct"])
        known    = sum(1 for r in results if r["class_id"] != -1)
        accuracy = (correct / known * 100) if known > 0 else 0.0

        print(f"\n📊 Summary")
        print(f"   Board          : PYNQ-Z2 (ARM Cortex-A9, no camera needed)")
        print(f"   Model          : {model_path}")
        print(f"   Images tested  : {len(results)}")
        print(f"   Avg latency    : {avg_lat:.2f} ms  ({1000/avg_lat:.1f} FPS equivalent)")
        print(f"   Avg confidence : {avg_conf:.2f}%")
        if known > 0:
            print(f"   Accuracy       : {correct}/{known} = {accuracy:.1f}%")

    return results


# ---------------------------------------------------------
# Main
# ---------------------------------------------------------
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="PYNQ-Z2 TSR - No Camera Demo")
    parser.add_argument("--images",  type=str, default=None,
                        help="Path to local folder with test images (jpg/png). "
                             "If not set, downloads sample images automatically.")
    parser.add_argument("--model",   type=str, default="gtsrb_quantized.tflite",
                        help="Path to TFLite model file")
    args = parser.parse_args()

    print("=" * 60)
    print("  PYNQ-Z2 Traffic Sign Recognition — Test Image Mode")
    print("  (No camera / No overlay / No VDMA required)")
    print("=" * 60)

    if args.images and os.path.isdir(args.images):
        image_list = load_local_images(args.images)
        print(f"\n📁 Found {len(image_list)} images in '{args.images}'")
    else:
        image_list = download_test_images("test_images")

    if not image_list:
        print("\n❌ No images found. Add images to 'test_images/' folder and retry.")
        sys.exit(1)

    run_inference_on_images(image_list, model_path=args.model)
