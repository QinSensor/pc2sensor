import asyncio
import tkinter as tk
from tkinter import ttk
from bleak import BleakClient
import threading
from sensor_map import UUID_MAP, MAPPINGS

ADDRESS = "FA:E2:AD:E2:8D:99"   # 3 axis 40

class BLEParameterEditor:
    def __init__(self, root, param_key):
        self.root = root
        self.param_key = param_key
        self.uuid = UUID_MAP[param_key]
        self.mapping = MAPPINGS[param_key]

        self.client = None
        self.status = tk.StringVar(value="Connecting...")
        self.selected_value = tk.StringVar()

        tk.Label(root, text=f"{param_key.replace('_', ' ').title()} Selector").pack(pady=5)
        tk.Label(root, textvariable=self.status, fg="blue").pack(pady=5)


        if self.mapping:
            # Dropdown mode
            self.selected_value = tk.StringVar()
            self.widget = ttk.Combobox(
                root,
                textvariable=self.selected_value,
                values=[label for _, label in self.mapping],
                state="readonly"
            )
            self.widget.bind("<<ComboboxSelected>>", self.on_value_selected)
        else:
            # Numeric entry mode
            self.selected_value = tk.StringVar()
            self.widget = ttk.Entry(root, textvariable=self.selected_value)
            tk.Button(root, text="Set", command=self.on_value_selected).pack(pady=5)

        self.widget.pack(pady=20)
        self.widget["state"] = "disabled"

        threading.Thread(target=self.connect_and_read).start()

    def connect_and_read(self):
        try:
            self.client = BleakClient(ADDRESS)
            asyncio.run(self.client.connect())
            if self.client.is_connected:
                self.status.set("Connected")
                self.read_value()
            else:
                self.status.set("Connection failed.")
        except Exception as e:
            self.status.set("Error")
            print("Connection failed:", e)

    def read_value(self):
        try:
            value_bytes = asyncio.run(self.client.read_gatt_char(self.uuid))
            raw_val = int.from_bytes(value_bytes, byteorder="little")
            value_dict = dict(self.mapping)
            label = value_dict.get(raw_val, "Unknown")
            self.selected_value.set(label)
            self.widget["state"] = "readonly"
        except Exception as e:
            print("Failed to read value:", e)
            self.status.set("Read failed")

    def on_value_selected(self, event):
        try:
            label = self.selected_value.get()
            raw_val = next(val for val, lbl in self.mapping if lbl == label)
            data = raw_val.to_bytes(1, byteorder="little")
            asyncio.run(self.client.write_gatt_char(self.uuid, data))
            self.status.set(f"Wrote {label}")
            print(f"Wrote {raw_val} ({label}) to {self.param_key}")
        except Exception as e:
            print("Failed to write value:", e)
            self.status.set("Write failed")

if __name__ == "__main__":
    root = tk.Tk()
    app = BLEParameterEditor(root, "sample_rate")  # Change this to "gain", "mode", etc.
    root.mainloop()
