import asyncio
import threading
import time
import tkinter as tk
from tkinter import ttk
from bleak import BleakScanner, BleakClient

from sensor_map import UUID_MAP, MAPPINGS  # Make sure this file exists with your mappings


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

        self.device_map = {}  # {address: {..., client}}

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
                            "seen": now,
                            "client": None
                        }
                    else:
                        self.device_map[dev.address]["seen"] = now

                    # Try connecting (just once per scan)
                    try:
                        client = BleakClient(dev.address)
                        await client.connect()
                        if client.is_connected:
                            self.device_map[dev.address]["connected"] = True
                            self.device_map[dev.address]["client"] = client
                        else:
                            self.device_map[dev.address]["connected"] = False
                            self.device_map[dev.address]["client"] = None
                    except Exception as e:
                        print(f"Connection failed to {dev.address}:", e)
                        self.device_map[dev.address]["connected"] = False
                        self.device_map[dev.address]["client"] = None

            self.refresh_table()
            await asyncio.sleep(5)

    def refresh_table(self):
        self.tree.delete(*self.tree.get_children())
        for addr, info in self.device_map.items():
            seen_diff = int(time.time() - info["seen"])
            seen_str = time.strftime("%Hh %Mm %Ss ago", time.gmtime(seen_diff))

            self.tree.insert("", tk.END, values=(
                addr,
                info["name"],
                str(info["connected"]),
                "Click View",  # We don't read mode here
                info["readings"],
                seen_str,
                "View"
            ))

    def read_mode(self, client):
        """Reads the 'mode' characteristic from the given connected client."""
        try:
            uuid = UUID_MAP["mode"]
            value_bytes = asyncio.run(client.read_gatt_char(uuid))
            raw_val = int.from_bytes(value_bytes, byteorder="little")
            mapping = MAPPINGS.get("mode", None)
            if mapping:
                return dict(mapping).get(raw_val, f"Unknown ({raw_val})")
            return str(raw_val)
        except Exception as e:
            print("Failed to read mode:", e)
            return "Error"

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

        # Read mode only when opening
        mode_str = "Unknown"
        client = info.get("client")
        if client and client.is_connected:
            mode_str = self.read_mode(client)
        tk.Label(win, text=f"Mode: {mode_str}").pack(pady=5)

        tk.Label(win, text="(UUID read/write UI goes here)").pack(pady=10)


if __name__ == "__main__":
    root = tk.Tk()
    app = BLEDeviceScanner(root)
    root.mainloop()
