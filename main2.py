import asyncio
import threading
import tkinter as tk
from tkinter import ttk
from bleak import BleakScanner, BleakClient
from sensor_map import UUID_MAP, MAPPINGS  # You already have these


# ---------- Parameter Editor for One Device ----------
class MultiParamEditor:
    def __init__(self, root, address):
        self.root = root
        self.address = address
        self.root.title(f"Edit Parameters - {address}")
        self.client = None

        self.status = tk.StringVar(value="Connecting...")
        tk.Label(root, textvariable=self.status, fg="blue").pack(pady=5)

        self.param_widgets = {}  # param_key -> widget, mapping
        self.values = {}  # param_key -> tk.StringVar

        frame = tk.Frame(root)
        frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Create one row per parameter
        for row, param_key in enumerate(UUID_MAP.keys()):
            tk.Label(frame, text=param_key.replace("_", " ").title()).grid(row=row, column=0, sticky="w", pady=3)

            mapping = MAPPINGS.get(param_key, None)
            var = tk.StringVar()
            self.values[param_key] = var

            if mapping:
                widget = ttk.Combobox(frame, textvariable=var,
                                      values=[label for _, label in mapping],
                                      state="readonly", width=15)
                widget.bind("<<ComboboxSelected>>", lambda e, pk=param_key: self.write_value(pk))
            else:
                widget = ttk.Entry(frame, textvariable=var, width=10)
                tk.Button(frame, text="Set", command=lambda pk=param_key: self.write_value(pk)).grid(row=row, column=2, padx=5)

            widget.grid(row=row, column=1, padx=5)
            self.param_widgets[param_key] = (widget, mapping)

        # Start BLE connection in a thread
        threading.Thread(target=self.connect_and_read_all, daemon=True).start()

    def connect_and_read_all(self):
        try:
            self.client = BleakClient(self.address)
            asyncio.run(self.client.connect())
            if self.client.is_connected:
                self.status.set("Connected")
                for param_key in UUID_MAP.keys():
                    self.read_value(param_key)
            else:
                self.status.set("Connection failed.")
        except Exception as e:
            self.status.set(f"Error: {e}")
            print("Connection failed:", e)

    def read_value(self, param_key):
        try:
            uuid = UUID_MAP[param_key]
            mapping = MAPPINGS.get(param_key, None)
            value_bytes = asyncio.run(self.client.read_gatt_char(uuid))
            raw_val = int.from_bytes(value_bytes, byteorder="little")

            if mapping:
                value_dict = dict(mapping)
                label = value_dict.get(raw_val, f"Unknown ({raw_val})")
                self.values[param_key].set(label)
                self.param_widgets[param_key][0]["state"] = "readonly"
            else:
                self.values[param_key].set(str(raw_val))
                self.param_widgets[param_key][0]["state"] = "normal"

        except Exception as e:
            print(f"Failed to read {param_key}:", e)

    def write_value(self, param_key):
        try:
            uuid = UUID_MAP[param_key]
            mapping = MAPPINGS.get(param_key, None)
            val_str = self.values[param_key].get()

            if mapping:
                raw_val = next(val for val, lbl in mapping if lbl == val_str)
                data = raw_val.to_bytes(1, byteorder="little")
            else:
                raw_val = int(val_str)
                # For integers, choose correct byte size
                if raw_val <= 0xFF:
                    data = raw_val.to_bytes(1, byteorder="little")
                elif raw_val <= 0xFFFF:
                    data = raw_val.to_bytes(2, byteorder="little")
                else:
                    raise ValueError("Value too large")

            asyncio.run(self.client.write_gatt_char(uuid, data))
            self.status.set(f"Wrote {val_str} to {param_key}")
            print(f"Wrote {raw_val} ({val_str}) to {param_key}")

        except Exception as e:
            print(f"Failed to write {param_key}:", e)
            self.status.set("Write failed")


# ---------- Scanner Window ----------
class BLEScannerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("BLE Device Scanner")

        self.tree = ttk.Treeview(root, columns=("Address", "RSSI"), show="headings")
        self.tree.heading("Address", text="Address")
        self.tree.heading("RSSI", text="RSSI")
        self.tree.pack(fill=tk.BOTH, expand=True)

        self.scan_button = tk.Button(root, text="Scan BLE Devices", command=self.start_scan)
        self.scan_button.pack(pady=10)

        self.tree.bind("<Double-1>", self.open_editor)

    def start_scan(self):
        threading.Thread(target=self.scan_devices, daemon=True).start()

    def scan_devices(self):
        devices = asyncio.run(BleakScanner.discover(timeout=5))
        # Clear previous results
        for row in self.tree.get_children():
            self.tree.delete(row)
        # Populate table
        for d in devices:
            rssi = getattr(d, "rssi", "N/A")

            self.tree.insert("", tk.END, values=(d.address, rssi))

    def open_editor(self, event):
        selected_item = self.tree.selection()
        if not selected_item:
            return
        address = self.tree.item(selected_item)["values"][0]
        param_window = tk.Toplevel(self.root)
        MultiParamEditor(param_window, address)


# ---------- Main ----------
if __name__ == "__main__":
    root = tk.Tk()
    app = BLEScannerApp(root)
    root.mainloop()
