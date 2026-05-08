import tensorflow as tf
import numpy as np
import os

# 1. LOAD THE MODEL
# Assuming best_gtsrb_model.keras is in the current directory
MODEL_PATH = 'best_gtsrb_model.keras'
if not os.path.exists(MODEL_PATH):
    print(f"Error: {MODEL_PATH} not found.")
    print("Ensure your trained .keras model is in the same folder as this script.")
    exit()

model = tf.keras.models.load_model(MODEL_PATH)
print(f"Model loaded: {MODEL_PATH}")
print(f"Input shape : {model.input_shape}")

# 2. REPRESENTATIVE DATASET FOR INT8 QUANTIZATION
# Used to calibrate the 8-bit scale/zero-point values.
# Replace random data with ~100 real images from your dataset for best accuracy.
def representative_data_gen():
    for _ in range(100):
        # Same input shape as the model: (1, 100, 100, 3) float32
        data = np.random.rand(1, 100, 100, 3).astype(np.float32)
        yield [data]

# 3. CONVERT TO TFLITE (Full Integer Quantization)
converter = tf.lite.TFLiteConverter.from_keras_model(model)
converter.optimizations = [tf.lite.Optimize.DEFAULT]
converter.representative_dataset = representative_data_gen

# Force all ops to INT8 (compatible with embedded ARM cores on PYNQ-Z2)
converter.target_spec.supported_ops = [tf.lite.OpsSet.TFLITE_BUILTINS_INT8]

# UInt8 I/O: matches raw camera sensor pixel data (0–255)
converter.inference_input_type  = tf.uint8
converter.inference_output_type = tf.uint8

print("\nQuantizing model to INT8 for PYNQ-Z2 deployment...")
tflite_model_quant = converter.convert()

# 4. SAVE THE QUANTIZED MODEL
OUTPUT_PATH = 'gtsrb_quantized.tflite'
with open(OUTPUT_PATH, 'wb') as f:
    f.write(tflite_model_quant)

original_size  = os.path.getsize(MODEL_PATH)
quantized_size = os.path.getsize(OUTPUT_PATH)

print(f"\n✅ Quantization Successful!")
print(f"   Output saved : {OUTPUT_PATH}")
print(f"   Original size : {original_size  / 1024 / 1024:.2f} MB")
print(f"   Quantized size: {quantized_size / 1024 / 1024:.2f} MB")
print(f"   Size reduction: {(1 - quantized_size/original_size)*100:.1f}%")
print(f"\n📌 Next step: copy '{OUTPUT_PATH}' to the PYNQ-Z2 board")
print(f"   via: scp {OUTPUT_PATH} xilinx@<PYNQ_IP>:/home/xilinx/")
