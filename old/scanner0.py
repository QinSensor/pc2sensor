import asyncio
import threading
import time
import tkinter as tk
from tkinter import ttk
from bleak import BleakScanner, BleakClient

from sensor_map import UUID_MAP, MAPPINGS


class BLEDeviceScanner:
    def __init__(self, root):
        self.root = root
        self.root.title("BluVib Devices")

        columns = ("UUID", "BLE Name", "Connected", "Mode", "Readings", "Seen", "Action")
        self.tree = ttk.Treeview(root, columns=columns, show="headings")
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=150)
        self.tree.pack(fill=tk.BOTH, expand=True)

        self.tree.bind("<ButtonRelease-1>", self.on_click)

        self.device_map = {}  # {address: {name, connected, seen, readings, mode}}

        threading.Thread(target=self.scan_loop, daemon=True).start()

    def scan_loop(self):
        asyncio.run(self.scan_devices())

    async def scan_devices(self):
        while True:
            found_devices = await BleakScanner.discover()

            now = time.time()
            for dev in found_devices:
                if dev.name and dev.name.startswith("BluVib"):
                    if dev.address not in self.device_map:
                        self.device_map[dev.address] = {
                            "name": dev.name,
                            "connected": False,
                            "mode": "Unknown",
                            "readings": 0,
                            "seen": now
                        }
                    else:
                        self.device_map[dev.address]["seen"] = now

                    # Try connecting
                    try:
                        async with BleakClient(dev.address) as client:
                            if client.is_connected:
                                self.device_map[dev.address]["connected"] = True
                    except:
                        self.device_map[dev.address]["connected"] = False

            # Update table without removing old devices
            self.refresh_table()
            await asyncio.sleep(5)

    def refresh_table(self):
        self.tree.delete(*self.tree.get_children())
        for addr, info in self.device_map.items():
            seen_diff = int(time.time() - info["seen"])
            seen_str = time.strftime("%H hour %M min %S sec ago", time.gmtime(seen_diff))
            self.tree.insert("", tk.END, values=(
                addr,
                info["name"],
                str(info["connected"]),
                # info["mode"],
                self.read_value("mode"),
                info["readings"],
                seen_str,
                "View"
            ))

    def read_value(self, param_key):
        try:
            uuid = UUID_MAP[param_key]
            mapping = MAPPINGS.get(param_key, None)
            value_bytes = asyncio.run(client.read_gatt_char(uuid))
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

    def on_click(self, event):
        selected_item = self.tree.selection()
        if not selected_item:
            return
        item = selected_item[0]
        values = self.tree.item(item, "values")
        if values and values[-1] == "View":
            device_address = values[0]
            if device_address in self.device_map:
                self.open_device_window(device_address)

    def open_device_window(self, address):
        info = self.device_map[address]
        win = tk.Toplevel(self.root)
        win.title(f"Device: {info['name']} ({address})")
        tk.Label(win, text=f"Address: {address}").pack(pady=5)
        tk.Label(win, text="(UUID read/write UI goes here)").pack(pady=10)


if __name__ == "__main__":
    root = tk.Tk()
    app = BLEDeviceScanner(root)
    root.mainloop()
