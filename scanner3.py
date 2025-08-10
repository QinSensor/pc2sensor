import asyncio
import threading
import time
import tkinter as tk
from tkinter import ttk
from bleak import BleakScanner, BleakClient

from sensor_map import UUID_MAP, MAPPINGS  # Ensure you have these mappings


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

        self.device_map = {}  # {address: {...}}
        threading.Thread(target=self.scan_loop, daemon=True).start()

    def scan_loop(self):
        asyncio.run(self.scan_devices())

    async def scan_devices(self):
        while True:
            found_devices = await BleakScanner.discover()
            now = time.time()

            for dev in found_devices:
                if dev.name and dev.name.startswith("BluVib"):
                    info = self.device_map.setdefault(dev.address, {
                        "name": dev.name,
                        "connected": False,
                        "mode": "Manual",  # Qin: in this mode, mode is not read
                        "readings": 0,  # starts at 0
                        "seen": now
                    })
                    info["seen"] = now

                    try:
                        async with BleakClient(dev.address) as client:
                            if client.is_connected:
                                info["connected"] = True
                                # Only update mode if connected!
                                info["mode"] = await self.read_mode_async(client)
                                info["readings"] += 1  # increment if connected/read successful
                            else:
                                info["connected"] = False
                                # Do NOT change mode here
                    except Exception as e:
                        print(f"Connection failed to {dev.address}:", e)
                        info["connected"] = False
                        # Do NOT change mode here

            self.refresh_table()
            await asyncio.sleep(10)

    async def read_mode_async(self, client):
        """Async version for reading mode characteristic."""
        try:
            uuid = UUID_MAP["mode"]
            value_bytes = await client.read_gatt_char(uuid)
            raw_val = int.from_bytes(value_bytes, byteorder="little")
            mapping = MAPPINGS.get("mode", None)
            if mapping:
                return dict(mapping).get(raw_val, f"Unknown ({raw_val})")
            return str(raw_val)
        except Exception as e:
            print("Failed to read mode:", e)
            return "Error"

    def refresh_table(self):
        self.tree.delete(*self.tree.get_children())
        for addr, info in self.device_map.items():
            seen_diff = int(time.time() - info["seen"])
            seen_str = time.strftime("%Hh %Mm %Ss ago", time.gmtime(seen_diff))
            self.tree.insert("", tk.END, values=(
                addr,
                info["name"],
                str(info["connected"]),
                info.get("mode", "Unknown"),       # Display last known mode
                info["readings"],
                seen_str,
                "View"
            ))


if __name__ == "__main__":
    root = tk.Tk()
    app = BLEDeviceScanner(root)
    root.mainloop()
