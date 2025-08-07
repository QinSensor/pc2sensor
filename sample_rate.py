# read and write sample rate, and list in GUI successfully

import asyncio
import tkinter as tk
from tkinter import ttk
from bleak import BleakClient
import threading

# BLE sensor address and UUID
ADDRESS = "FA:E2:AD:E2:8D:99"
SAMPLE_RATE_UUID = "1c930023-d459-11e7-9296-b8e856369374"

# Supported value-to-rate mapping: (value, Hz)
SAMPLE_RATE_MAP = [
    (1, 25600),
    (2, 12800),
    (3, 5120),
    (4, 2560),
    (5, 1280),
    (6, 512),
    (7, 256)
]

class SampleRateSelector:
    def __init__(self, root):
        self.root = root
        self.client = None

        self.root.title("Sample Rate Selector")
        self.status = tk.StringVar(value="Connecting...")
        self.selected_rate = tk.StringVar()

        # Status label
        tk.Label(root, textvariable=self.status, fg="blue").pack(pady=5)

        # Dropdown menu for sample rates
        self.dropdown = ttk.Combobox(
            root,
            textvariable=self.selected_rate,
            values=[f"{hz} Hz" for _, hz in SAMPLE_RATE_MAP],
            state="readonly"
        )
        self.dropdown.bind("<<ComboboxSelected>>", self.on_rate_selected)
        self.dropdown.pack(pady=20)
        self.dropdown["state"] = "disabled"  # Initially disabled

        # Start BLE connection in a background thread
        threading.Thread(target=self.connect_and_read).start()

    def connect_and_read(self):
        try:
            self.client = BleakClient(ADDRESS)
            asyncio.run(self.client.connect())

            if self.client.is_connected:
                self.status.set("Connected")
                self.read_sample_rate()
            else:
                self.status.set("Connection failed.")
        except Exception as e:
            self.status.set("Error")
            print("Connection failed:", e)

    def read_sample_rate(self):
        try:
            rate_bytes = asyncio.run(self.client.read_gatt_char(SAMPLE_RATE_UUID))
            value = int.from_bytes(rate_bytes, byteorder="little")
            # Look up corresponding Hz
            rates = dict(SAMPLE_RATE_MAP)
            current_rate = rates.get(value, None)
            if current_rate is None:
                print(f"Unexpected value: {value}")
                current_rate = SAMPLE_RATE_MAP[0][1]
            self.selected_rate.set(f"{current_rate} Hz")
            self.dropdown["state"] = "readonly"  # Enable after reading
        except Exception as e:
            print("Failed to read sample rate:", e)
            self.status.set("Read failed")

    def on_rate_selected(self, event):
        selected_text = self.selected_rate.get()  # e.g., "5120 Hz"
        try:
            hz = int(selected_text.split()[0])
            # Find the corresponding value
            value = next(val for val, rate in SAMPLE_RATE_MAP if rate == hz)
            data = value.to_bytes(1, byteorder="little")
            asyncio.run(self.client.write_gatt_char(SAMPLE_RATE_UUID, data))
            print(f"Wrote sample rate value: {value} (for {hz} Hz)")
            self.status.set(f"Wrote {hz} Hz.")

            # NOTE: You must write to the 'release' characteristic to commit!
            # e.g., await self.client.write_gatt_char(RELEASE_UUID, ...)
            # This part is not implemented since RELEASE_UUID is not given.

        except Exception as e:
            print("Failed to write sample rate:", e)
            self.status.set("Write failed.")

if __name__ == "__main__":
    root = tk.Tk()
    app = SampleRateSelector(root)
    root.mainloop()
