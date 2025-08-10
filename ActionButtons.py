import asyncio
import threading
from tkinter import ttk
from sensor_map import UUID_MAP, UUID_MAP_BUTTON  # Make sure your UUID_MAP contains the needed keys

class BLEActionButtons:
    def __init__(self, parent, client):
        """
        parent: parent Tkinter frame/window where buttons will be placed
        client: already-connected BleakClient
        """
        self.parent = parent
        self.client = client

        # Button definitions: key in UUID_MAP, label, and send byte
        self.actions = [
            ("shutdown", "Power Off Sensor", b"\x01"),
            ("factory_reset", "Factory Reset", b"\x01"),
            ("restart", "Restart Sensor", b"\x01")
        ]

        self._create_buttons_in_row()

    def _create_buttons_in_row(self):
        """Create action buttons in a single horizontal row using grid."""
        for col_index, (uuid_key, label, data_bytes) in enumerate(self.actions):
            btn = ttk.Button(
                self.parent,
                text=label,
                command=lambda k=uuid_key, d=data_bytes: self._send_command(k, d)
            )
            btn.grid(row=0, column=col_index, padx=5, pady=5, sticky="ew")

        # Make all columns expand evenly (if parent uses grid weight)
        for col_index in range(len(self.actions)):
            self.parent.grid_columnconfigure(col_index, weight=1)

    def _send_command(self, uuid_key, data_bytes):
        uuid = UUID_MAP_BUTTON.get(uuid_key)
        if not uuid:
            print(f"[ERROR] UUID for {uuid_key} not found in UUID_MAP")
            return

        def write_bytes():
            try:
                asyncio.run(self.client.write_gatt_char(uuid, data_bytes))
                print(f"[OK] Wrote {data_bytes} to {uuid_key}")
            except Exception as e:
                print(f"[ERROR] Failed to send {uuid_key} command:", e)

        threading.Thread(target=write_bytes, daemon=True).start()