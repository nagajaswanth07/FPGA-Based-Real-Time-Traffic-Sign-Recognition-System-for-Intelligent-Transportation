# Real-Time Traffic Sign Recognition Using Quantized CNN on PYNQ-Z2 FPGA Architecture

**Abstract**— Real-time Traffic Sign Recognition (TSR) is a critical component of modern Advanced Driver Assistance Systems (ADAS) and autonomous vehicles. This report presents the design and implementation of a TSR system leveraging a quantized Convolutional Neural Network (CNN) deployed on the Xilinx PYNQ-Z2 Field Programmable Gate Array (FPGA). By utilizing hardware-software co-design principles, the system achieves low-latency inference at the edge. The model is trained on the German Traffic Sign Recognition Benchmark (GTSRB) dataset and quantized to INT8 precision via TensorFlow Lite, reducing the memory footprint to approximately 900 KB. The hardware architecture utilizes the Zynq-7000 Processing System (PS) coupled with AXI Video Direct Memory Access (VDMA) IP to handle video streaming. The resulting implementation demonstrates high-accuracy classification across 43 traffic sign categories with an inference latency of less than 30 ms per frame, enabling a processing throughput of 30–40 frames per second (FPS).

---

## I. INTRODUCTION

The rapid advancement of autonomous driving technologies demands highly efficient, real-time image processing capabilities at the edge. Traffic Sign Recognition (TSR) systems must rapidly classify a wide variety of signs under diverse environmental conditions. While deep learning models, particularly Convolutional Neural Networks (CNNs), provide state-of-the-art accuracy for this task, they are traditionally computationally expensive and memory-intensive, making them challenging to deploy on resource-constrained edge devices.

FPGAs offer a compelling solution by providing customizable hardware acceleration, low latency, and deterministic power consumption. The Xilinx PYNQ-Z2 board, built around the Zynq-7000 SoC (XC7Z020), bridges the gap between software engineers and FPGA hardware by offering a Python-based ecosystem (Jupyter Notebooks) running on top of a Linux OS. This project demonstrates an end-to-end TSR system on the PYNQ-Z2, showcasing a balance between high classification accuracy and strict edge-computing performance constraints.

## II. SYSTEM ARCHITECTURE

The system is designed using a hardware-software co-design approach, dividing the workload between the Zynq Processing System (PS) and the Programmable Logic (PL).

### A. Hardware Design (Programmable Logic)
The hardware overlay is designed using Xilinx Vivado. It acts as the backbone for high-speed image acquisition and preprocessing. Key components include:
*   **Zynq-7000 PS:** Orchestrates the system, runs the PYNQ Linux OS, and executes the Python application. In the updated configuration, the PS handles direct USB camera interfacing.
*   **USB Controller (PS-Side):** Facilitates direct connection to standard USB Webcams, eliminating the need for complex PL-to-parallel-camera adapters.
*   **AXI Interconnect (Optional):** Provides a high-speed communication backbone for future hardware accelerators.

### B. Software Application (Processing System)
The software stack is built using the PYNQ API and Python. 
*   **PYNQ Overlay:** The `design_1.bit` and hardware handoff file `design_1.hwh` are loaded dynamically using the `pynq.Overlay` library.
*   **TensorFlow Lite Interpreter:** A lightweight inference engine is used to execute the quantized model directly on the ARM Cortex-A9 processor.
*   **OpenCV:** Used for resizing the captured video frames to the required input tensor shape (100x100x3) and converting color spaces (BGR to RGB).

## III. METHODOLOGY

### A. Dataset and Preprocessing
The model was trained on the **German Traffic Sign Recognition Benchmark (GTSRB)**, which consists of over 50,000 images categorized into 43 distinct classes (e.g., Speed limits, Stop, No Entry, Yield). 
For inference, incoming frames from the hardware pipeline are captured, resized to 100x100 pixels, and converted into an 8-bit unsigned integer array to match the quantized model's input requirements.

### B. Model Architecture and Quantization
To meet edge constraints, a lightweight MobileNet-based architecture was selected. Post-training quantization was applied using TensorFlow Lite, converting the 32-bit floating-point weights and activations into 8-bit integers (INT8). 
*   **Original Size:** Several Megabytes
*   **Quantized Size:** ~900 KB (`gtsrb_quantized.tflite`)
This significant reduction in size allows the entire model to fit comfortably within the system's memory and reduces memory bandwidth requirements during inference, with only a negligible loss in classification accuracy.

### C. Deployment Workflow
1.  **Bitstream Generation:** The hardware block design was synthesized and routed in Vivado targeting the `xc7z020clg400-1` part, with the USB controller explicitly enabled.
2.  **File Transfer:** The generated `.bit`, `.hwh`, `.tflite` model, and the new live Python inference script (`pynq_tsr_usb_live.py`) were transferred to the PYNQ-Z2 `/home/xilinx/` directory.
3.  **Execution:** The inference script initializes the USB camera via OpenCV, captures frames in a continuous loop, formats the data, and invokes the TFLite interpreter for real-time classification.

## IV. EXPERIMENTAL RESULTS

The proposed architecture was validated locally on the PYNQ-Z2 hardware. The evaluation focused on two primary metrics: accuracy/confidence and inference latency.

### A. Performance Latency
The transition from a standard software environment to the optimized PYNQ-Z2 edge device yielded excellent real-time performance. 
*   **Average Inference Latency:** < 30 ms per frame (Hardware measurements show an average of ~11.0 ms to 11.5 ms per frame execution on the TFLite interpreter).
*   **Frame Rate:** The overall system achieves a steady throughput of 30 to 40 Frames Per Second (FPS), comfortably exceeding the standard requirement for real-time video processing (24–30 FPS).

### B. Classification Confidence
The INT8 quantized model demonstrated robust accuracy across various test conditions. Typical output logs during live inference demonstrate high confidence levels:
*   *Speed limit (50km/h):* 94.21% Confidence
*   *Stop:* 98.76% Confidence
*   *No entry:* 91.33% Confidence

### C. Hardware Comparison
Compared to the smaller EDGE Z7-10 board (XC7Z010 fabric), the PYNQ-Z2 (XC7Z020) provides significantly more resources (~53,200 LUTs vs ~17,600 LUTs and 220 DSP slices vs 80), preventing routing congestion and allowing for potential future integration of custom IP accelerators (like a DPU) to push inference speeds even further.

## V. CONCLUSION

This project successfully implemented a real-time Traffic Sign Recognition system on the PYNQ-Z2 FPGA platform. By coupling a carefully quantized INT8 CNN with the AXI VDMA hardware overlay, the system handles 100x100 pixel image classification efficiently at the edge. The resulting architecture requires less than 30 ms per inference while maintaining classification confidences consistently above 90% for clear signs. This implementation serves as a robust foundation for deploying lightweight autonomous driving perception models on programmable SoC architectures.

## VI. FUTURE WORK
Future iterations of this project will explore offloading the convolutional operations entirely to the Programmable Logic (PL) using Xilinx Vitis AI and a Deep Learning Processor Unit (DPU). This would further decouple the inference engine from the Zynq CPU, theoretically reducing latency to the sub-millisecond range and significantly improving energy efficiency per frame.
