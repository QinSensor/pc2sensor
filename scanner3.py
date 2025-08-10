import asyncio
import threading
import time
import tkinter as tk
from tkinter import ttk, messagebox
from bleak import BleakScanner, BleakClient
import subprocess


from a_sensor import ASensorParameterApp
from sensor_map import UUID_MAP, MAPPINGS  # Ensure you have these mappings

class BLEDeviceScanner:
    def __init__(self, root):
        self.root = root
        self.root.title("BluVib Devices")

        columns = ("Mac Address", "BLE Name", "Connected", "Mode", "Readings", "Seen", "Action")
        self.tree = ttk.Treeview(root, columns=columns, show="headings")
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=150)
        self.tree.pack(fill=tk.BOTH, expand=True)

        self.tree.bind("<ButtonRelease-1>", self.on_click)

        self.device_map = {}  # {address: {...}}
        self.device_clients = {}    # Address → connected BleakClient
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
                        "address": dev.address,  # Add this line here

                        "connected": False,
                        "mode": "Manual",  # Qin: in this mode, mode is not read
                        "readings": 0,  # starts at 0
                        "seen": now
                    })
                    info["seen"] = now

                    # Ensure we have a persistent BleakClient
                    if dev.address not in self.device_clients:
                        client = BleakClient(dev.address)
                        try:
                            await client.connect()
                            print(f"Connected to {dev.address}")
                            self.device_clients[dev.address] = client
                        except Exception as e:
                            print(f"Failed to connect {dev.address}:", e)
                            continue
                    else:
                        client = self.device_clients[dev.address]

                    if client.is_connected:
                        info["connected"] = True
                        info["mode"] = await self.read_mode_async(client)
                        info["readings"] += 1
                    else:
                        info["connected"] = False

            self.refresh_table()
            await asyncio.sleep(10)

    def connect_device(self, address):
        client = self.device_clients.get(address)
        if client and not client.is_connected:
            import asyncio
            asyncio.run(client.connect())
            print(f"Connected to {address}")

    def disconnect_device(self, address):
        client = self.device_clients.get(address)
        if client and client.is_connected:
            import asyncio
            asyncio.run(client.disconnect())
            print(f"Disconnected from {address}")

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
        address = device['address']
        name = device['name']
        client = self.device_clients.get(address)
        if not client:
            tk.messagebox.showerror("Error", f"No connected client found for {address}")
            return
        ASensorParameterApp(win, self, address, name, client.is_connected)  # pass


def restart_bluetooth_windows():
    try:
        subprocess.run(["powershell", "-Command", "Stop-Service bthserv -Force"], check=True)
        time.sleep(3)  # give Bluetooth time to come back online
        subprocess.run(["powershell", "-Command", "Start-Service bthserv"], check=True)
        print("Bluetooth service restarted")
    except Exception as e:
        print(f"Failed to restart Bluetooth service: {e}")

if __name__ == "__main__":
    print("Restarting bluetooth in PC...")
    restart_bluetooth_windows()
    time.sleep(3)  # give Bluetooth time to come back online

    root = tk.Tk()
    app = BLEDeviceScanner(root)
    root.mainloop()
