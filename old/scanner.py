import asyncio
import threading
import tkinter as tk
from tkinter import ttk
from bleak import BleakScanner


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

    def start_scan(self):
        threading.Thread(target=self.scan_devices).start()

    def scan_devices(self):
        devices = asyncio.run(BleakScanner.discover(timeout=5))
        # Clear previous results
        for row in self.tree.get_children():
            self.tree.delete(row)
        # Populate table
        for d in devices:
            self.tree.insert("", tk.END, values=(d.address, d.rssi))


if __name__ == "__main__":
    root = tk.Tk()
    app = BLEScannerApp(root)
    root.mainloop()
