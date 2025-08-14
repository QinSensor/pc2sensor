import asyncio
import threading
import time
import tkinter as tk
from tkinter import ttk, messagebox
from bleak import BleakScanner, BleakClient
import subprocess
from a_sensor import ASensorParameterApp, SensorConnection
from utils.plot_utils import start_acceleration_stream, start_acceleration_stream_Scanner
# from utils.plot_utils import start_acceleration_stream
from utils.sensor_map import UUID_MAP, MAPPINGS  # Ensure you have these mappings


# TODO button of clear_capture and

class BLEDeviceScanner:
    def __init__(self, root, loop):
        self.loop = loop
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

            found_addresses = set()

            for dev in found_devices:
                if dev.name and dev.name.startswith("BluVib"):
                    found_addresses.add(dev.address)
                    info = self.device_map.setdefault(dev.address, {
                        "name": dev.name,
                        "address": dev.address,  # Add this line here
                        "data": [],
                        "connected": False,
                        "mode": "Unknown",  # Qin: in this mode, mode is not read
                        "readings": 0,  # starts at 0
                        "seen": now
                    })
                    info["seen"] = now    # time

                    # Ensure we have a persistent BleakClient
                    if dev.address not in self.device_clients:
                        # Create a persistent wrapper
                        sensor_conn = SensorConnection(dev.address)
                        self.device_clients[dev.address] = sensor_conn
                        try:
                            await sensor_conn.connect()
                            print(f"Connected to {dev.address}")
                        except Exception as e:
                            print(f"Failed to connect {dev.address}:", e)
                            continue
                    else:
                        sensor_conn = self.device_clients[dev.address]
                        await sensor_conn.connect()  # reconnect if needed

                    # if sensor_conn.is_connected:
                    client = sensor_conn.get_client()
                    if client and client.is_connected:
                        info["connected"] = True
                        info["mode"] = await self.read_value_async(sensor_conn, "mode")
                        info["readings"] += 1
                        info["calibration"] = await self.read_value_async(sensor_conn, "calibration")
                        start_acceleration_stream_Scanner(client, info, self.loop, info["calibration"])
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

    async def read_value_async(self, client, para):
        """Async version for reading mode characteristic."""
        try:
            if hasattr(client, "get_client"):
                client = client.get_client()  # unwrap SensorConnection
            uuid, byte_size = UUID_MAP[para]
            value_bytes = await client.read_gatt_char(uuid)
            raw_val = int.from_bytes(value_bytes, byteorder="little")

            mapping = MAPPINGS.get(para, None)
            if mapping:
                return dict(mapping).get(raw_val, f"Unknown ({raw_val})")
            return str(raw_val)
        except Exception as e:
            print("Failed to read :", para, e)
            return f"Error: {e}"

    def refresh_table(self):
        print("Refreshing UI table")
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
            print("RawData for ", addr, "is ", info["data"])

    # Method called by App2 after commit to remove sensor immediately
    async def on_sensor_commit(self, sensor_address):
        # # Mark as disconnected, don't remove from device_map
        # if sensor_address in self.device_map:
        #     self.device_map[sensor_address]["connected"] = False
        #     print(f"App1: Marked sensor {sensor_address} as disconnected after commit")
        sensor_conn = self.device_clients.get(sensor_address)

        if sensor_conn:
            # Reconnect existing object (UI still holds reference)
            await sensor_conn.reconnect()
        else:
            # First time connecting for this sensor
            sensor_conn = SensorConnection(sensor_address)
            await sensor_conn.connect()
            self.device_clients[sensor_address] = sensor_conn

        now = time.time()
        info = self.device_map.setdefault(sensor_address, {
            "name": sensor_conn.get_client().name if sensor_conn.get_client() else "Unknown",
            "address": sensor_address,
            "connected": False,
            "mode": "Manual",
            "data": [],
            "readings": 0,
            "seen": now,
            "calibration": 0
        })
        info["seen"] = now  # time

        if sensor_conn.is_connected:
            info["connected"] = True
            info["mode"] = await self.read_value_async(sensor_conn.get_client(), "mode")
            info["readings"] += 1
            print("Get data***********")

        else:
            info["connected"] = False

        self.refresh_table()

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
        sensor_conn = self.device_clients.get(address)
        if not sensor_conn:
            tk.messagebox.showerror("Error", f"No connected client found for {address}")
            return
        ASensorParameterApp(win, self, address, name, sensor_conn, self.loop)


def start_loop(loop):
    asyncio.set_event_loop(loop)
    loop.run_forever()


if __name__ == "__main__":
    root = tk.Tk()

    loop = asyncio.new_event_loop()
    # Start the event loop in a new thread
    loop_thread = threading.Thread(target=start_loop, args=(loop,), daemon=True)
    loop_thread.start()

    app = BLEDeviceScanner(root, loop)
    root.mainloop()
