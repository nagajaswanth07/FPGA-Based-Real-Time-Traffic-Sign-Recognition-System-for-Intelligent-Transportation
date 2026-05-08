# 🚦 PYNQ-Z2 Traffic Sign Recognition — Step-by-Step Guide

Follow these steps to run the Traffic Sign Recognition (TSR) project on your PYNQ-Z2 board.

---

## Part 1: Prepare the Files
You need to move these files from your laptop to the PYNQ-Z2 board:
1. `gtsrb_quantized.tflite` (The AI Model)
2. `tsr_no_camera.ipynb` (Jupyter Notebook for verification)
3. `pynq_test_images.py` (Python script version)
4. (Optional) Any `.jpg` images you want to test in a folder named `test_images/`



## Part 2: Upload to PYNQ-Z2
1. **Connect** your PYNQ-Z2 board to your network/laptop and power it on.
2. **Open Browser**: Go to `http://192.168.2.99` (or the IP address of your board).
3. **Log in**: The default password is `xilinx`.
4. **Upload**: Use the "Upload" button in the Jupyter Home interface to upload the 3 files mentioned above.
5. **Create Folder**: Click **New** -> **Folder**, rename it to `test_images`, and upload your traffic sign images into it.

---

## Part 3: Run the Verification (No Camera Needed)

### Option A: Using Jupyter (Visual Results)
1. In the Jupyter interface, click on **`tsr_no_camera.ipynb`**.
2. Go to the menu: **Cell** -> **Run All**.
3. **Result**: It will display the images, the predicted sign name, the confidence percentage, and a bar chart of the performance.

### Option B: Using Terminal (Fastest)
1. Open a terminal in Jupyter (**New** -> **Terminal**) or use SSH.
2. Run the command:
   ```bash
   python3 pynq_test_images.py
   ```
3. **Result**: It will print a formatted table showing each image and what the AI detected.

---

## Part 4: Running with USB Webcam (NEW)
1. **Connect**: Plug any standard USB webcam into the PYNQ-Z2 USB port.
2. **Hardware**: Ensure you have uploaded the USB-optimized `design_1.bit` and `design_1.hwh`.
3. **Run Live**:
   ```bash
   sudo python3 pynq_tsr_usb_live.py
   ```
4. **Result**: The terminal will show live detections and processing speed (FPS/ms).

---

## Part 4: (Optional) Running with Hardware Overlay
If you have generated the bitstream in Vivado and want to use the FPGA fabric:
1. Rename `design_1_wrapper.bit` to `design_1.bit`.
2. Upload `design_1.bit` and `design_1.hwh` to the board.
3. Open a notebook and load the overlay:
   ```python
   from pynq import Overlay
   overlay = Overlay("design_1.bit")
   ```

---

## Troubleshooting
* **Library Error**: If it says `tflite_runtime` is missing, run this in a PYNQ terminal:
  ```bash
  pip3 install tflite-runtime
  ```
* **No Images**: If the script says "No images found," ensure your images are in the `test_images/` folder relative to the script.
