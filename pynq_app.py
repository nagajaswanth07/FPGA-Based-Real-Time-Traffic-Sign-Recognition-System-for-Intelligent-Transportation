import os
import cv2
import numpy as np
import time
from pynq import Overlay
import tflite_runtime.interpreter as tflite

# ---------------------------------------------------------
# 1. LOAD OVERLAY (PYNQ-Z2 Hardware Design)
# ---------------------------------------------------------
# The overlay is the .bit + .hwh pair generated from Vivado.
# Both files must be in the same directory as this script.
overlay = Overlay("design_1.bit")
print("Overlay loaded successfully on PYNQ-Z2!")

# Access the VDMA block from the overlay
# The path must match the hierarchy in your Vivado Block Design
vdma = overlay.axi_vdma_0

# ---------------------------------------------------------
# 2. LOAD TFLITE MODEL
# ---------------------------------------------------------
MODEL_PATH = "gtsrb_quantized.tflite"
interpreter = tflite.Interpreter(model_path=MODEL_PATH)
interpreter.allocate_tensors()

input_details  = interpreter.get_input_details()
output_details = interpreter.get_output_details()

print("Model Loaded. Input shape:", input_details[0]['shape'])

# ---------------------------------------------------------
# 3. CLASS LABEL MAPPING (GTSRB 43 Classes)
# ---------------------------------------------------------
gtsrb_labels = {
    0: "Speed limit (20km/h)",   1: "Speed limit (30km/h)",   2: "Speed limit (50km/h)",
    3: "Speed limit (60km/h)",   4: "Speed limit (70km/h)",   5: "Speed limit (80km/h)",
    6: "End of speed limit (80km/h)",                         7: "Speed limit (100km/h)",
    8: "Speed limit (120km/h)",  9: "No passing",
    10: "No passing for vehicles over 3.5 metric tons",
    11: "Right-of-way at the next intersection",              12: "Priority road",
    13: "Yield",                14: "Stop",                   15: "No vehicles",
    16: "Vehicles over 3.5 metric tons prohibited",           17: "No entry",
    18: "General caution",      19: "Dangerous curve to the left",
    20: "Dangerous curve to the right",                       21: "Double curve",
    22: "Bumpy road",           23: "Slippery road",          24: "Road narrows on the right",
    25: "Road work",            26: "Traffic signals",         27: "Pedestrians",
    28: "Children crossing",    29: "Bicycles crossing",       30: "Beware of ice/snow",
    31: "Wild animals crossing",
    32: "End of all speed and passing limits",                33: "Turn right ahead",
    34: "Turn left ahead",      35: "Ahead only",             36: "Go straight or right",
    37: "Go straight or left",  38: "Keep right",             39: "Keep left",
    40: "Roundabout mandatory", 41: "End of no passing",
    42: "End of no passing by vehicles over 3.5 metric tons"
}

# ---------------------------------------------------------
# 4. MAIN INFERENCE LOOP
# ---------------------------------------------------------
def run_inference():
    print("Starting Traffic Sign Recognition on PYNQ-Z2...")
    print("Press Ctrl+C to stop.\n")
    try:
        while True:
            # A. Capture Frame from VDMA
            # readchannel reads from the S2MM (write to DDR) channel
            frame = vdma.readchannel.readframe()

            # B. Pre-process: resize to model input (100x100)
            img_rgb    = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img_resized = cv2.resize(img_rgb, (100, 100))

            # C. Handle Input Type (Float32 or UInt8)
            if input_details[0]['dtype'] == np.float32:
                # Normalise for float32 model
                input_data = np.expand_dims(img_resized, axis=0).astype(np.float32) / 255.0
            else:
                # No normalisation for UInt8 model
                input_data = np.expand_dims(img_resized, axis=0).astype(np.uint8)

            # D. Run Inference
            start_time = time.time()
            interpreter.set_tensor(input_details[0]['index'], input_data)
            interpreter.invoke()
            end_time   = time.time()

            # E. Get Results
            output_data = interpreter.get_tensor(output_details[0]['index'])
            prediction  = np.argmax(output_data[0])

            # Confidence calculation based on output type
            if output_details[0]['dtype'] == np.float32:
                confidence = output_data[0][prediction] * 100
            else:
                confidence = output_data[0][prediction] / 255.0 * 100

            label = gtsrb_labels.get(prediction, f"Class {prediction}")

            # F. Print result to terminal
            print(
                f"\rDetected: {label:<45} | "
                f"Confidence: {confidence:>5.2f}% | "
                f"Latency: {(end_time - start_time) * 1000:>6.2f}ms",
                end=""
            )

            # G. (Optional) Output to HDMI Tx via OpenCV
            # PYNQ-Z2 has HDMI Out — uncomment below to display on a monitor
            # cv2.imshow("PYNQ-Z2 TSR", frame)
            # if cv2.waitKey(1) & 0xFF == ord('q'):
            #     break

    except KeyboardInterrupt:
        print("\n\nStopping application.")
        # cv2.destroyAllWindows()


if __name__ == "__main__":
    run_inference()
