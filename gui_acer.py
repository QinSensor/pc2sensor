import asyncio
import threading
import tkinter as tk
from tkinter import ttk
from bleak import BleakClient

UUID_MAP = {
    'sample_rate': "1c930023-d459-11e7-9296-b8e856369374",
    'gain': "1c930022-d459-11e7-9296-b8e856369374",
    'mode': "1c930031-d459-11e7-9296-b8e856369374",
    'holdoff_interval': "1c93003a-d459-11e7-9296-b8e856369374",
    'wakeup_interval': "1c930036-d459-11e7-9296-b8e856369374",
    'trace_len': "1c930024-d459-11e7-9296-b8e856369374",
    'axes': "1c93002b-d459-11e7-9296-b8e856369374",
    'trigger_delay': "1c930025-d459-11e7-9296-b8e856369374",

    # 'window': "1c930027-d459-11e7-9296-b8e856369374",
    #
    # 'trigger_level': "1c93002D-d459-11e7-9296-b8e856369374",

    # ... Add as needed ...
}

ADDRESS = "FA:E2:AD:E2:8D:99"

# Example UUIDs for all parameters—replace with your specific ones.

SAMPLE_RATE_MAP = [
    (1, 25600),
    (2, 12800),
    (3, 5120),
    (4, 2560),
    (5, 1280),
    (6, 512),
    (7, 256)
]
GAIN_OPTIONS = [1, 2, 4, 8]
WINDOW_TYPES = ["Hann", "Rectangular", "Hamming"]
OPERATING_MODES = ["Wakeup", "Continuous"]
AXES = [1, 2, 3]

TRACE_LEN_TABLE = [
    (0, 64),
    (1, 128),
    (2, 256),
    (3, 512),
    (4, 1024),
    (5, 2048),
    (6, 4096),
    (7, 8192),
    (8, 16384),
    (9, 32768),
    (10, 65536),
    (11, 131072),
    (12, 262144),
    (13, 524288),
    (14, 1048576),
    (15, 2097152)
]





def find_key_by_val(d, val):
    for k, v in d.items():
        if v == val:
            return k
    return None


class BluVibGUI:
    def __init__(self, root):
        self.root = root
        self.client = None
        self.status = tk.StringVar(value="Not connected")
        self.selected_window = tk.StringVar()
        self.selected_mode = tk.StringVar()
        self.selected_sample_rate = tk.StringVar()
        # In your GUI __init__ or build_form:
        self.selected_trace_length = tk.StringVar()


        # self.selected_trace_length = tk.StringVar()
        self.selected_gain = tk.StringVar()
        self.selected_axes = tk.StringVar()
        self.wakeup_interval = tk.StringVar()
        self.holdoff_interval = tk.StringVar()
        self.trigger_level = tk.StringVar()
        self.trigger_delay = tk.StringVar()
        self.build_form()
        threading.Thread(target=self.connect_and_read_all, daemon=True).start()

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
                     values=[str(hz) for _, hz in SAMPLE_RATE_MAP], state="readonly").grid(row=row, column=1)
        # row += 1
        # tk.Label(self.root, text="Trace Length (Samples):").grid(row=row, column=0, sticky=tk.W)
        # ttk.Combobox(self.root, textvariable=self.selected_trace_length, values=[str(x) for x in TRACE_LENGTHS], state="readonly").grid(row=row, column=1)
        row += 1
        tk.Label(self.root, text="Gain:").grid(row=row, column=0, sticky=tk.W)
        ttk.Combobox(self.root, textvariable=self.selected_gain, values=[str(x) for x in GAIN_OPTIONS], state="readonly").grid(row=row, column=1)
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

        ttk.Combobox(
            self.root,
            textvariable=self.selected_trace_length,
            values=[str(x[1]) for x in TRACE_LEN_TABLE],  # Show sample counts
            state="readonly"
        ).grid(row=row, column=1)

        # Reading from BLE:
        value = int.from_bytes(await self.client.read_gatt_char(TRACE_LEN_UUID), byteorder="little")
        length_map = dict(TRACE_LEN_TABLE)
        current_length = length_map.get(value, 512)
        self.selected_trace_length.set(str(current_length))

        # Writing to BLE:
        desired_length = int(self.selected_trace_length.get())
        value = next(idx for idx, cnt in TRACE_LEN_TABLE if cnt == desired_length)
        await self.client.write_gatt_char(TRACE_LEN_UUID, value.to_bytes(1, byteorder="little"))

    def connect_and_read_all(self):
        try:
            self.client = BleakClient(ADDRESS)
            asyncio.run(self.client.connect())
            if self.client.is_connected:
                self.status.set("Connected, reading parameters...")
                asyncio.run(self.read_all_parameters())
                self.status.set("Parameters loaded")
            else:
                self.status.set("Connection failed.")
        except Exception as e:
            self.status.set("BLE Error")
            print("BLE Connection failed:", e)

    async def read_all_parameters(self):
        # Read Sample Rate
        sr_val = await self.read_value(UUID_MAP['sample_rate'])
        if sr_val is not None:
            rates = dict(SAMPLE_RATE_MAP)
            self.selected_sample_rate.set(str(rates.get(sr_val, 25600)))
        # Gain
        gain_val = await self.read_value(UUID_MAP['gain'])
        if gain_val is not None:
            self.selected_gain.set(str(gain_val))
        # Window
        window_val = await self.read_value(UUID_MAP['window'])
        if window_val is not None:
            if window_val < len(WINDOW_TYPES):
                self.selected_window.set(WINDOW_TYPES[window_val])
            else:
                self.selected_window.set(WINDOW_TYPES[0])
        # Mode
        mode_val = await self.read_value(UUID_MAP['mode'])
        if mode_val is not None:
            if mode_val < len(OPERATING_MODES):
                self.selected_mode.set(OPERATING_MODES[mode_val])
            else:
                self.selected_mode.set(OPERATING_MODES[0])
        # # Trace Length
        # trace_val = await self.read_value(UUID_MAP['trace'])
        # if trace_val is not None:
        #     self.selected_trace_length.set(str(TRACE_LENGTHS[trace_val]) if trace_val < len(TRACE_LENGTHS) else str(TRACE_LENGTHS[0]))
        # Axes
        axes_val = await self.read_value(UUID_MAP['axes'])
        if axes_val is not None:
            self.selected_axes.set(str(AXES[axes_val]) if axes_val < len(AXES) else str(AXES[0]))
        # Scalars/entries (assuming 1 byte)
        wakeup_val = await self.read_value(UUID_MAP['wakeup_interval'])
        if wakeup_val is not None:
            self.wakeup_interval.set(str(wakeup_val))
        holdoff_val = await self.read_value(UUID_MAP['holdoff_interval'])
        if holdoff_val is not None:
            self.holdoff_interval.set(str(holdoff_val))
        trig_lvl_val = await self.read_value(UUID_MAP['trigger_level'])
        if trig_lvl_val is not None:
            self.trigger_level.set(str(trig_lvl_val))
        trig_dly_val = await self.read_value(UUID_MAP['trigger_delay'])
        if trig_dly_val is not None:
            self.trigger_delay.set(str(trig_dly_val))

    async def read_value(self, uuid):
        try:
            data = await self.client.read_gatt_char(uuid)
            return int.from_bytes(data, byteorder="little")
        except Exception as e:
            print(f"Failed to read {uuid}:", e)
            return None

    def on_save(self):
        # Write each parameter!
        threading.Thread(target=self.save_all_parameters, daemon=True).start()

    def save_all_parameters(self):
        try:
            asyncio.run(self._save_parameters())
            self.status.set("Parameters written (remember to commit if needed!)")
        except Exception as e:
            self.status.set("Write failed")
            print("Write error:", e)

    async def _save_parameters(self):
        # Write sample rate (map Hz to value)
        rate_hz = int(self.selected_sample_rate.get())
        value = next(val for val, hz in SAMPLE_RATE_MAP if hz == rate_hz)
        await self.write_value(UUID_MAP['sample_rate'], value)
        # Gain
        await self.write_value(UUID_MAP['gain'], int(self.selected_gain.get()))
        # Window
        if self.selected_window.get() in WINDOW_TYPES:
            await self.write_value(UUID_MAP['window'], WINDOW_TYPES.index(self.selected_window.get()))
        # Mode
        if self.selected_mode.get() in OPERATING_MODES:
            await self.write_value(UUID_MAP['mode'], OPERATING_MODES.index(self.selected_mode.get()))
        # Trace
        if self.selected_trace_length.get().isdigit():
            idx = TRACE_LENGTHS.index(int(self.selected_trace_length.get()))
            await self.write_value(UUID_MAP['trace'], idx)
        # Axes
        if self.selected_axes.get().isdigit():
            idx = AXES.index(int(self.selected_axes.get()))
            await self.write_value(UUID_MAP['axes'], idx)
        # Scalars
        await self.write_value(UUID_MAP['wakeup_interval'], int(self.wakeup_interval.get()))
        await self.write_value(UUID_MAP['holdoff_interval'], int(self.holdoff_interval.get()))
        await self.write_value(UUID_MAP['trigger_level'], int(self.trigger_level.get()))
        await self.write_value(UUID_MAP['trigger_delay'], int(self.trigger_delay.get()))

    async def write_value(self, uuid, value):
        try:
            await self.client.write_gatt_char(uuid, value.to_bytes(1, byteorder='little'))
        except Exception as e:
            print(f"Failed to write {uuid}:", e)

    def on_restart(self):
        self.status.set("Restart pressed (not implemented)")

    def on_factory_reset(self):
        self.status.set("Factory reset pressed (not implemented)")


if __name__ == "__main__":
    root = tk.Tk()
    gui = BluVibGUI(root)
    root.mainloop()
