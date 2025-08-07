import asyncio
import tkinter as tk
from tkinter import ttk, messagebox
from bleak import BleakClient
import threading

# Sensor MAC address and UUIDs
address = "FA:E2:AD:E2:8D:99"
DATA_UUID = "1c930020-d459-11e7-9296-b8e856369374"
GAIN_UUID = "1c930022-d459-11e7-9296-b8e856369374"
SAMPLE_RATE_UUID = "1c930023-d459-11e7-9296-b8e856369374"
CALIBRATION_UUID = "1c930029-d459-11e7-9296-b8e856369374"

class BLEGUI:
    def __init__(self, root):
        self.root = root
        self.client = None

        self.root.title("Sensor Interface")
        self.status = tk.StringVar(value="Disconnected")

        tk.Label(root, text="Sensor Status:").pack()
        tk.Label(root, textvariable=self.status, fg="blue").pack()

        self.connect_btn = tk.Button(root, text="Connect", command=self.connect)
        self.connect_btn.pack(pady=5)

        self.read_btn = tk.Button(root, text="Read Sensor", command=self.read_sensor, state=tk.DISABLED)
        self.read_btn.pack(pady=5)

        self.calibrate_btn = tk.Button(root, text="Calibrate", command=self.calibrate, state=tk.DISABLED)
        self.calibrate_btn.pack(pady=5)

        self.output = tk.Text(root, height=10, width=50)
        self.output.pack(pady=10)

    def log(self, message):
        self.output.insert(tk.END, message + "\n")
        self.output.see(tk.END)

    def connect(self):
        self.status.set("Connecting...")
        threading.Thread(target=self._connect_async).start()

    def _connect_async(self):
        try:
            self.client = BleakClient(address)
            asyncio.run(self.client.connect())
            if self.client.is_connected:
                self.status.set("Connected")
                self.log("Connected to sensor.")
                self.read_btn["state"] = tk.NORMAL
                self.calibrate_btn["state"] = tk.NORMAL
            else:
                self.status.set("Failed to connect.")
        except Exception as e:
            self.status.set("Error")
            self.log(f"Connection failed: {e}")

    def read_sensor(self):
        threading.Thread(target=self._read_async).start()

    def _read_async(self):
        try:
            data = asyncio.run(self.client.read_gatt_char(DATA_UUID))
            # Assume raw 3-axis data (e.g. 6 bytes: 3 int16 values)
            if len(data) >= 6:
                x = int.from_bytes(data[0:2], byteorder='little', signed=True)
                y = int.from_bytes(data[2:4], byteorder='little', signed=True)
                z = int.from_bytes(data[4:6], byteorder='little', signed=True)
                self.log(f"Sensor Reading:\nX: {x}, Y: {y}, Z: {z}")
            else:
                self.log(f"Raw data: {data.hex()}")
        except Exception as e:
            self.log(f"Read failed: {e}")

    def calibrate(self):
        threading.Thread(target=self._calibrate_async).start()

    def _calibrate_async(self):
        try:
            asyncio.run(self.client.write_gatt_char(CALIBRATION_UUID, bytearray([0x01])))
            self.log("Calibration command sent.")
        except Exception as e:
            self.log(f"Calibration failed: {e}")

if __name__ == "__main__":
    root = tk.Tk()
    app = BLEGUI(root)
    root.mainloop()
