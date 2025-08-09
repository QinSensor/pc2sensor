# 📦 BLE Sensor Reader

A simple Python script to read data from your BluSensor (or other BLE device) using [Bleak](https://github.com/hbldh/bleak).

---

## ✅ Requirements

1. **Install Python**  
   Download and install Python from [python.org](https://www.python.org/downloads/).  
   Make sure to check **"Add Python to PATH"** during installation.

2. **Install Bleak**  
   Open a terminal (Command Prompt or PowerShell) and run:
   ```bash
   pip install bleak


# ✏️ Edit `read_addr.py`

In the script `read_addr.py`, replace "D5:D0:F9:30:83:D7" in this line:

ADDRESS = "D5:D0:F9:30:83:D7"  # Your BLE device MAC address

with your own BluSensor address.


## ▶️ How to Run

1. Open a terminal and navigate to the script's folder:

2. Run the Python script:
   ```bash
   python read_addr.py


## ❓ Troubleshooting

**Cannot find device?**  
- Verify the MAC address.
- Make sure your BLE device is turned on and in range.
- Ensure your PC's Bluetooth drivers are up to date.

**Cannot connect sensor?**
- Go to Windows Settings--> Bluetooth & Other Devices  ---> Turn off Bluetooth and Turn on again.
- Magnate sensor to ensure that it is blinking.


## Code Progress
**Run to Get GUI**
```bash
    python main.py
    ```
[//]: # (**1. Fetch data, calibrated**)

[//]: # (```bash)

[//]: # (    python connect.py)

[//]: # (   ```)

[//]: # ( )
[//]: # (**2. GUI for variants, such as sample rate**)

[//]: # (```bash)

[//]: # (    python sample_rate.py)

[//]: # (```)

[//]: # ()
[//]: # (**3. Show all variants**)

[//]: # (```bash)

[//]: # (    python all_option.py)

[//]: # (```)



---

## 📄 License

This project is licensed under the MIT License.  
Feel free to reuse, modify, and share.

---




