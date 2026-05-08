<img width="1080" height="656" alt="image3" src="https://github.com/user-attachments/assets/ecd482bb-6160-460d-92a0-21b602a1c1ac" />
# Real-Time Traffic Sign Recognition on FPGA Using CNN (PYNQ-Z2)

![PYNQ-Z2 Setup](report_images/pynq_z2_board.jpg) <!-- Assuming an image exists, placeholder -->

## Overview
This repository contains the hardware and software implementation for a Real-Time Traffic Sign Recognition (TSR) system deployed on the **Xilinx PYNQ-Z2** FPGA. Using a hardware-software co-design approach, a quantized Convolutional Neural Network (CNN) is accelerated at the edge to recognize 43 distinct traffic sign classes from the GTSRB dataset.

The system utilizes the Zynq-7000 Processing System (PS) coupled with AXI Video Direct Memory Access (VDMA) to achieve real-time video processing with low latency.

## System Architecture
*   **Hardware (Programmable Logic):** The PL contains the AXI VDMA and video processing IP blocks, alongside a USB controller interfacing block to allow direct camera connection without external adapters.
*   **Software (Processing System):** The PS runs the PYNQ Linux OS and executes Python scripts. It utilizes the TensorFlow Lite Interpreter to run the quantized `INT8` model (`gtsrb_quantized.tflite`) directly, alongside OpenCV for image preprocessing.

## Results & Performance
The implementation was rigorously tested on the PYNQ-Z2 hardware. Moving from a standard software environment to the optimized PYNQ-Z2 edge device yielded excellent real-time performance. 

*   **Model Footprint:** ~900 KB (Reduced from several MBs via INT8 Quantization)
*   **Average Inference Latency:** `< 30 ms` per frame (Hardware measurements show an average of `11.0 ms to 11.5 ms` per frame on the TFLite interpreter).
*   **Frame Rate:** Achieves a steady throughput of **30 to 40 Frames Per Second (FPS)**, easily exceeding the standard requirement for real-time video processing (24–30 FPS).
*   **Classification Confidence:** The system demonstrates robust accuracy across various conditions. Example inference logs:
    *   *Speed limit (50km/h):* 94.21% Confidence
    *   *Stop:* 98.76% Confidence
    *   *No entry:* 91.33% Confidence

## Hardware Specifications
| Feature | Details |
|---|---|
| **FPGA Fabric** | XC7Z020 (Zynq-7000 SoC) |
| **LUTs / DSP** | ~53,200 LUTs / 220 DSP Slices |
| **RAM** | 512 MB DDR3 |
| **Camera Interface**| Standard USB Webcam |
| **Model** | MobileNet-based, quantized INT8 TFLite |

## Repository Structure
- `pynq_app.py` - Core live inference script running on the PYNQ-Z2.
- `tsr_demo.ipynb` / `tsr_no_camera.ipynb` - Jupyter Notebook versions of the inference pipeline.
- `build_hardware.tcl` / `build_hardware.py` - Scripts to regenerate the Vivado block design.
- `gtsrb_quantized.tflite` - The optimized INT8 TensorFlow Lite model.
- `*.xdc` - Constraints files for the PYNQ-Z2 board.
- Documentation - Setup guides and PDF reports.

## How to Run
1. Transfer the `.bit`, `.hwh`, and `.tflite` model files to the PYNQ board's `/home/xilinx/` directory.
2. Transfer `pynq_app.py` to the board.
3. SSH into the board or open a Jupyter Terminal.
4. Run the inference script:
   ```bash
   sudo python3 pynq_app.py
   ```
