import asyncio
import tkinter as tk
from tkinter import ttk
import threading

from ActionButtons import BLEActionButtons
from sensor_map import UUID_MAP, MAPPINGS


class BLEParameterEditor:
    def __init__(self, parent, client, param_key):
        self.client = client
        self.param_key = param_key
        self.uuid = UUID_MAP[param_key]
        self.mapping = MAPPINGS.get(param_key, None)

        self.frame = ttk.Frame(parent)
        self.frame.pack(fill='x', pady=5)

        ttk.Label(self.frame, text=f"{param_key.replace('_', ' ').title()}").pack(side='left', padx=5)

        self.status = tk.StringVar(value="Waiting")
        ttk.Label(self.frame, textvariable=self.status, foreground="blue").pack(side='right', padx=5)

        self.selected_value = tk.StringVar()

        if self.mapping:
            self.widget = ttk.Combobox(
                self.frame,
                textvariable=self.selected_value,
                values=[label for _, label in self.mapping],
                state="readonly"
            )
            self.widget.bind("<<ComboboxSelected>>", self.on_value_selected)
            self.widget.pack(side='left', padx=5)
        else:
            self.widget = ttk.Entry(self.frame, textvariable=self.selected_value)
            self.widget.pack(side='left', padx=5)
            ttk.Button(self.frame, text="Set", command=self.on_value_selected).pack(side='left', padx=5)

        self.widget["state"] = "disabled"

        # Start reading in a thread to avoid blocking Tkinter
        threading.Thread(target=self.read_value, daemon=True).start()

    def read_value(self):
        asyncio.run(self._async_read_value())

    async def _async_read_value(self):
        try:
            value_bytes = await self.client.read_gatt_char(self.uuid)
            raw_val = int.from_bytes(value_bytes, byteorder="little")

            if self.mapping:
                value_dict = dict(self.mapping)
                label = value_dict.get(raw_val, "Unknown")
            else:
                label = str(raw_val)

            # Update GUI in main thread
            self.frame.after(0, lambda: self.update_ui(label))
        except Exception as e:
            print(f"Failed to read {self.param_key}:", e)
            self.frame.after(0, lambda: self.status.set("Read failed"))

    def update_ui(self, label):
        self.selected_value.set(label)
        self.widget["state"] = "readonly" if self.mapping else "normal"
        self.status.set("Connected")

    def on_value_selected(self, event=None):
        asyncio.run(self._async_write_value())

    async def _async_write_value(self):
        try:
            label = self.selected_value.get()
            if self.mapping:
                raw_val = next(val for val, lbl in self.mapping if lbl == label)
            else:
                raw_val = int(label)

            data = raw_val.to_bytes(1, byteorder="little")  # Adjust byte size if needed
            await self.client.write_gatt_char(self.uuid, data)
            self.frame.after(0, lambda: self.status.set(f"Wrote {label}"))
            print(f"Wrote {raw_val} ({label}) to {self.param_key}")
        except Exception as e:
            print(f"Failed to write {self.param_key}:", e)
            self.frame.after(0, lambda: self.status.set("Write failed"))


class ASensorParameterApp:
    def __init__(self, root, client, address, name):
        self.root = root
        self.root.title(address+ '('+ name+ ')')
        self.client = client  # already connected BleakClient

        self.editors = {}

        self.main_frame = ttk.Frame(root)
        self.main_frame.pack(padx=10, pady=10)

        # ---- CONNECT/DISCONNECT BUTTONS ----
        conn_frame = ttk.Frame(self.main_frame)
        conn_frame.pack(fill="x", pady=5)

        self.connect_btn = ttk.Button(conn_frame, text="Connect", command=self.connect_sensor)
        self.connect_btn.pack(side="left", padx=5)

        self.disconnect_btn = ttk.Button(conn_frame, text="Disconnect", command=self.disconnect_sensor)
        self.disconnect_btn.pack(side="left", padx=5)

        self.conn_status = tk.StringVar(value="Connect Status")
        ttk.Label(conn_frame, textvariable=self.conn_status, foreground="blue").pack(side="left", padx=10)

        # Initial button states
        self.update_button_states()

        # Create editors but disable until connected
        for param_key in UUID_MAP.keys():
            editor = BLEParameterEditor(self.main_frame, self.client, param_key)
            self.editors[param_key] = editor

        # ---- DEVICE ACTION BUTTONS ----
        self.buttons_frame = ttk.LabelFrame(self.main_frame, text="Device Actions")
        self.buttons_frame.pack(fill="x", pady=10)

        BLEActionButtons(self.buttons_frame, self.client)


        self.enable_editors()

    # ------------------------------
    # Connection controls
    # ------------------------------
    def connect_sensor(self):
        def do_connect():
            import asyncio
            try:
                asyncio.run(self.client.connect())
                print(f"Connected to {self.address}")
                self.conn_status.set("Connected")
            except Exception as e:
                print(f"Failed to connect: {e}")
                self.conn_status.set("Connect failed")
            self.root.after(0, self.update_button_states)
        threading.Thread(target=do_connect, daemon=True).start()

    def disconnect_sensor(self):
        def do_disconnect():
            import asyncio
            try:
                asyncio.run(self.client.disconnect())
                print(f"Disconnected from {self.address}")
                self.conn_status.set("Disconnected")
            except Exception as e:
                print(f"Failed to disconnect: {e}")
                self.conn_status.set("Disconnect failed")
        self.root.after(0, self.update_button_states)
        threading.Thread(target=do_disconnect, daemon=True).start()

    def update_button_states(self):
        """Enable/disable connect/disconnect buttons based on current status."""
        status = self.conn_status.get().lower()
        if status == "connected":
            self.connect_btn["state"] = "disabled"
            self.disconnect_btn["state"] = "normal"
        else:
            self.connect_btn["state"] = "normal"
            self.disconnect_btn["state"] = "disabled"

    def enable_editors(self):
        for editor in self.editors.values():
            editor.widget["state"] = "normal"
            editor.status.set("Connected")
            # Trigger read again after enabling
            threading.Thread(target=editor.read_value, daemon=True).start()

