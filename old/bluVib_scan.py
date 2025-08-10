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
        columns = ("UUID", "BLE Name", "Connected", "Transferring", "Mode", "Readings", "Seen")
        self.tree = ttk.Treeview(root, columns=columns, show="headings")
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=150)
        self.tree.pack(fill=tk.BOTH, expand=True)

        # Start scanning in a background thread
        threading.Thread(target=self.scan_loop, daemon=True).start()

    def scan_loop(self):
        asyncio.run(self.scan_devices())

    async def scan_devices(self):
        while True:
            devices = await BleakScanner.discover()
            self.tree.delete(*self.tree.get_children())

            for d in devices:
                name = d.name or ""
                if name.startswith("BluVib"):
                    # Placeholder values for Connected, Transferring, Mode, Readings, Seen
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
                        seen
                    ))
            await asyncio.sleep(5)  # Scan refresh interval

if __name__ == "__main__":
    root = tk.Tk()
    app = BLEDeviceScanner(root)
    root.mainloop()
