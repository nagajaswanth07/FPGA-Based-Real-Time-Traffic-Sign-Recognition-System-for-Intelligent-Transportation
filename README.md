# Real-Time Traffic Sign Recognition on FPGA Using CNN (PYNQ-Z2)


## Project Showcase

### Inference Results
<img width="800" height="656" alt="image15" src="https://github.com/user-attachments/assets/0b54bef1-c579-4490-a208-a363474b73d2" />

<img width="400" height="407" alt="image17" src="https://github.com/user-attachments/assets/749cc048-24b9-4893-aa73-c7e9e2ab8349" />
<img width="400" height="395" alt="image16" src="https://github.com/user-attachments/assets/d96498e9-e1fc-4718-8a63-e42d9ce7563a" />


### Hardware Setup
![PYNQ-Z2 Hardware](report_images/image13.jpg)



## Overview
This repository contains the hardware and software implementation for a Real-Time Traffic Sign Recognition (TSR) system deployed on the **Xilinx PYNQ-Z2** FPGA. Using a hardware-software co-design approach, a quantized Convolutional Neural Network (CNN) is accelerated at the edge to recognize 43 distinct traffic sign classes from the GTSRB dataset.

The system utilizes the Zynq-7000 Processing System (PS) coupled with AXI Video Direct Memory Access (VDMA) to achieve real-time video processing with low latency.

## System Architecture
*   **Hardware (Programmable Logic):** The PL contains the AXI VDMA and video processing IP blocks, alongside a USB controller interfacing block to allow direct camera connection without external adapters.
*   **Software (Processing System):** The PS runs the PYNQ Linux OS and executes Python scripts. It utilizes the TensorFlow Lite Interpreter to run the quantized `INT8` model (`gtsrb_quantized.tflite`) directly, alongside OpenCV for image preprocessing.
<img width="1536" height="1024" alt="image10" src="https://github.com/user-attachments/assets/1250e372-b751-4f96-ad89-52f6ebb11005" />
<img width="1693" height="929" alt="image8" src="https://github.com/user-attachments/assets/be7011cd-f296-4ade-8976-c522571faba5" />

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
