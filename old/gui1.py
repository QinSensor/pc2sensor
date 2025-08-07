import asyncio
import tkinter as tk
from tkinter import ttk
from bleak import BleakClient
import threading

# BLE sensor address and UUID
ADDRESS = "FA:E2:AD:E2:8D:99"
SAMPLE_RATE_UUID = "1c930023-d459-11e7-9296-b8e856369374"

# Supported sample rates (Hz)
SAMPLE_RATES = [10, 20, 50, 100]

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
        self.dropdown = ttk.Combobox(root, textvariable=self.selected_rate, values=[f"{r} Hz" for r in SAMPLE_RATES], state="readonly")
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
            current_rate = int.from_bytes(rate_bytes, byteorder="little")
            if current_rate not in SAMPLE_RATES:
                print(f"Unexpected sample rate: {current_rate}")
                current_rate = SAMPLE_RATES[0]
            self.selected_rate.set(f"{current_rate} Hz")
            self.dropdown["state"] = "readonly"  # Enable after reading
        except Exception as e:
            print("Failed to read sample rate:", e)
            self.status.set("Read failed")

    def on_rate_selected(self, event):
        selected_text = self.selected_rate.get()  # e.g., "50 Hz"
        try:
            rate = int(selected_text.split()[0])  # Extract number
            data = rate.to_bytes(1, byteorder="little")  # Assume 1 byte
            asyncio.run(self.client.write_gatt_char(SAMPLE_RATE_UUID, data))
            print(f"Wrote sample rate: {rate} Hz")
        except Exception as e:
            print("Failed to write sample rate:", e)

if __name__ == "__main__":
    root = tk.Tk()
    app = SampleRateSelector(root)
    root.mainloop()
