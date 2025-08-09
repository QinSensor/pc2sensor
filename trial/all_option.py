import asyncio
import threading
import tkinter as tk
from tkinter import ttk
from bleak import BleakClient

ADDRESS = "FA:E2:AD:E2:8D:99"
SAMPLE_RATE_UUID = "1c930023-d459-11e7-9296-b8e856369374"

SAMPLE_RATE_MAP = [
    (1, 25600),
    (2, 12800),
    (3, 5120),
    (4, 2560),
    (5, 1280),
    (6, 512),
    (7, 256)
]

WINDOW_TYPES = ["Hann", "Hamming", "Blackman", "Nuttall", "Blackman-Nuttall",
                "Blackman-Harris", "Flattop",  "Rectangular"]
OPERATING_MODES = ["Manual", "Wakeup", "Wakeup+", "Ready",
                   "Event", "MotionDetect"]
TRACE_LENGTHS = [64, 128, 256, 512, 1024, 2048, 4096, 8192, 16384, 32768, 65536, 131072, 262144, 524288, 1048576, 2097152]
GAINS = [1, 2, 4, 10]
AXES = [1, 3]


class BluVibGUI:
    def __init__(self, root):
        self.root = root
        self.client = None
        self.status = tk.StringVar(value="Not connected")
        self.selected_window = tk.StringVar(value=WINDOW_TYPES[0])
        self.selected_mode = tk.StringVar(value=OPERATING_MODES[0])
        self.selected_sample_rate = tk.StringVar()
        self.selected_trace_length = tk.StringVar(value=str(TRACE_LENGTHS[1]))
        self.selected_gain = tk.StringVar(value=str(GAINS[0]))
        self.selected_axes = tk.StringVar(value=str(AXES[2]))
        self.wakeup_interval = tk.StringVar(value="10")
        self.holdoff_interval = tk.StringVar(value="0")
        self.trigger_level = tk.StringVar(value="2")
        self.trigger_delay = tk.StringVar(value="90")

        # GUI Layout
        self.build_form()
        # BLE connect in background
        threading.Thread(target=self.connect_and_read, daemon=True).start()

    def build_form(self):
        row = 0
        tk.Label(self.root, text="BluVib290039", font=("Arial", 16)).grid(row=row, column=0, columnspan=2, pady=6)

        row += 1
        tk.Label(self.root, text="Window:").grid(row=row, column=0, sticky=tk.W)
        ttk.Combobox(self.root, textvariable=self.selected_window, values=WINDOW_TYPES, state="readonly").grid(row=row, column=1)

        row += 1
        tk.Label(self.root, text="Operating Mode:").grid(row=row, column=0, sticky=tk.W)
        ttk.Combobox(self.root, textvariable=self.selected_mode, values=OPERATING_MODES, state="readonly").grid(row=row, column=1)

        row += 1
        tk.Label(self.root, text="Sample Rate (Hz):").grid(row=row, column=0, sticky=tk.W)
        ttk.Combobox(self.root, textvariable=self.selected_sample_rate,
                     values=[str(hz) for _, hz in SAMPLE_RATE_MAP], state="readonly",
                     postcommand=self.sync_sample_rate_field
                     ).grid(row=row, column=1)

        row += 1
        tk.Label(self.root, text="Trace Length (Samples):").grid(row=row, column=0, sticky=tk.W)
        ttk.Combobox(self.root, textvariable=self.selected_trace_length, values=[str(x) for x in TRACE_LENGTHS], state="readonly").grid(row=row, column=1)

        row += 1
        tk.Label(self.root, text="Gain:").grid(row=row, column=0, sticky=tk.W)
        ttk.Combobox(self.root, textvariable=self.selected_gain, values=[str(x) for x in GAINS], state="readonly").grid(row=row, column=1)

        row += 1
        tk.Label(self.root, text="Axes:").grid(row=row, column=0, sticky=tk.W)
        ttk.Combobox(self.root, textvariable=self.selected_axes, values=[str(x) for x in AXES], state="readonly").grid(row=row, column=1)

        row += 1
        tk.Label(self.root, text="Wakeup Interval (s):").grid(row=row, column=0, sticky=tk.W)
        tk.Entry(self.root, textvariable=self.wakeup_interval).grid(row=row, column=1)

        row += 1
        tk.Label(self.root, text="Holdoff Interval (s):").grid(row=row, column=0, sticky=tk.W)
        tk.Entry(self.root, textvariable=self.holdoff_interval).grid(row=row, column=1)

        row += 1
        tk.Label(self.root, text="Trigger Level (g):").grid(row=row, column=0, sticky=tk.W)
        tk.Entry(self.root, textvariable=self.trigger_level).grid(row=row, column=1)

        row += 1
        tk.Label(self.root, text="Trigger Delay (%):").grid(row=row, column=0, sticky=tk.W)
        tk.Entry(self.root, textvariable=self.trigger_delay).grid(row=row, column=1)

        row += 1
        btn_frame = tk.Frame(self.root)
        btn_frame.grid(row=row, column=0, columnspan=2, pady=8)
        tk.Button(btn_frame, text="Save", command=self.on_save).pack(side=tk.LEFT, padx=2)
        tk.Button(btn_frame, text="Restart", command=self.on_restart).pack(side=tk.LEFT, padx=2)
        tk.Button(btn_frame, text="Factory Reset", command=self.on_factory_reset).pack(side=tk.LEFT, padx=2)

        row += 1
        tk.Label(self.root, textvariable=self.status, fg="blue").grid(row=row, column=0, columnspan=2, pady=6)

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
            self.status.set("BLE Error")
            print("BLE Connection failed:", e)

    def read_sample_rate(self):
        try:
            rate_bytes = asyncio.run(self.client.read_gatt_char(SAMPLE_RATE_UUID))
            value = int.from_bytes(rate_bytes, byteorder="little")
            rates = dict(SAMPLE_RATE_MAP)
            current_rate = rates.get(value, None)
            if current_rate is None:
                current_rate = SAMPLE_RATE_MAP[0][1]
            self.selected_sample_rate.set(str(current_rate))
        except Exception as e:
            print("Failed to read sample rate:", e)

    def sync_sample_rate_field(self):
        # When dropdown expands, update to current device value if needed
        pass

    def on_save(self):
        selected_rate = int(self.selected_sample_rate.get())
        value = next(val for val, hz in SAMPLE_RATE_MAP if hz == selected_rate)
        data = value.to_bytes(1, byteorder="little")
        try:
            asyncio.run(self.client.write_gatt_char(SAMPLE_RATE_UUID, data))
            self.status.set(f"Sample rate {selected_rate} Hz set (remember to commit!)")
        except Exception as e:
            print("Failed to write sample rate:", e)
            self.status.set("Failed to write sample rate")
        # Add BLE write code for other parameters as needed

    def on_restart(self):
        self.status.set("Restart pressed (not implemented)")

    def on_factory_reset(self):
        self.status.set("Factory reset pressed (not implemented)")


if __name__ == "__main__":
    root = tk.Tk()
    gui = BluVibGUI(root)
    root.mainloop()
