import asyncio
import tkinter as tk
from bleak import BleakClient
import threading

# Sensor info
ADDRESS = "FA:E2:AD:E2:8D:99"
SAMPLE_RATE_UUID = "1c930023-d459-11e7-9296-b8e856369374"

# Sample rates to toggle through (in Hz)
SAMPLE_RATES = [10, 20, 50, 100]

class SampleRateGUI:
    def __init__(self, root):
        self.root = root
        self.client = None
        self.current_rate = None
        self.rate_index = 0

        self.root.title("Sensor Sample Rate")
        self.status = tk.StringVar(value="Connecting...")

        # Status label
        tk.Label(root, textvariable=self.status, fg="blue").pack(pady=5)

        # Sample rate button
        self.sample_btn = tk.Button(root, text="Sample Rate: ?", command=self.change_sample_rate, state=tk.DISABLED)
        self.sample_btn.pack(pady=20)

        # Start BLE connection in background
        threading.Thread(target=self.connect_and_read_rate).start()

    def connect_and_read_rate(self):
        try:
            self.client = BleakClient(ADDRESS)
            asyncio.run(self.client.connect())

            if self.client.is_connected:
                self.status.set("Connected")
                self.read_sample_rate()
            else:
                self.status.set("Failed to connect.")
        except Exception as e:
            self.status.set("Error")
            print("Connection failed:", e)

    def read_sample_rate(self):
        try:
            rate_bytes = asyncio.run(self.client.read_gatt_char(SAMPLE_RATE_UUID))
            self.current_rate = int.from_bytes(rate_bytes, byteorder="little")
            self.rate_index = SAMPLE_RATES.index(self.current_rate) if self.current_rate in SAMPLE_RATES else 0
            self.update_sample_rate_text()
            self.sample_btn["state"] = tk.NORMAL
        except Exception as e:
            print("Failed to read sample rate:", e)
            self.sample_btn["text"] = "Sample Rate: ?"

    def update_sample_rate_text(self):
        self.sample_btn["text"] = f"Sample Rate: {self.current_rate} Hz"

    def change_sample_rate(self):
        self.rate_index = (self.rate_index + 1) % len(SAMPLE_RATES)
        self.current_rate = SAMPLE_RATES[self.rate_index]
        try:
            data = self.current_rate.to_bytes(1, byteorder="little")  # Assuming it's 1 byte
            asyncio.run(self.client.write_gatt_char(SAMPLE_RATE_UUID, data))
            self.update_sample_rate_text()
        except Exception as e:
            print("Failed to write sample rate:", e)

if __name__ == "__main__":
    root = tk.Tk()
    app = SampleRateGUI(root)
    root.mainloop()
