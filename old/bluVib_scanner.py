import asyncio
import threading
import time
import tkinter as tk
from tkinter import ttk
from bleak import BleakScanner

class BLEDeviceScanner:
    def __init__(self, root):
        self.root = root
        self.root.title("BluVib Devices")

        # Table setup
        columns = ("UUID", "BLE Name", "Connected", "Transferring", "Mode", "Readings", "Seen", "Action")
        self.tree = ttk.Treeview(root, columns=columns, show="headings")
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=150)
        self.tree.pack(fill=tk.BOTH, expand=True)

        # Bind click event for "View" column
        self.tree.bind("<ButtonRelease-1>", self.on_click)

        # Device storage for quick access
        self.device_map = {}

        # Start scanning in a background thread
        threading.Thread(target=self.scan_loop, daemon=True).start()

    def scan_loop(self):
        asyncio.run(self.scan_devices())

    async def scan_devices(self):
        while True:
            devices = await BleakScanner.discover()
            self.tree.delete(*self.tree.get_children())
            self.device_map.clear()

            for d in devices:
                name = d.name or ""
                if name.startswith("BluVib"):
                    connected = "False"
                    transferring = "False"
                    mode = "Unknown"
                    readings = "0"
                    seen = time.strftime("%H hour %M min %S sec ago", time.gmtime(0))

                    self.tree.insert("", tk.END, values=(
                        d.address,
                        name,
                        connected,
                        transferring,
                        mode,
                        readings,
                        seen,
                        "View"
                    ))
                    self.device_map[d.address] = d
            await asyncio.sleep(5)

    def on_click(self, event):
        """Handle clicks on the 'View' action column."""
        selected_item = self.tree.selection()
        if not selected_item:
            return
        item = selected_item[0]
        values = self.tree.item(item, "values")
        if values and values[-1] == "View":
            device_address = values[0]
            if device_address in self.device_map:
                self.open_device_window(self.device_map[device_address])

    def open_device_window(self, device):
        """Open a new window for reading/writing the device UUIDs."""
        win = tk.Toplevel(self.root)
        win.title(f"Device: {device.name} ({device.address})")
        tk.Label(win, text=f"Address: {device.address}").pack(pady=5)
        tk.Label(win, text="(Here we add UUID reading/writing widgets from yesterday)").pack(pady=10)
        # TODO: integrate yesterday's UUID read/write code here


if __name__ == "__main__":
    root = tk.Tk()
    app = BLEDeviceScanner(root)
    root.mainloop()
