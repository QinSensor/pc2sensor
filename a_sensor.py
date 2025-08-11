import asyncio
import tkinter as tk
from tkinter import ttk
import threading

from ActionButtons import BLEActionButtons
from sensor_map import UUID_MAP, MAPPINGS, UUID_MAP_BUTTON


async def compute_trigger_delay(client, raw_val):
    """
    Computes trigger_delay % from raw_val and trace_len.
    Returns string as 'percent' (integer) or raw_val as string if unavailable.
    """
    trace_len_entry = UUID_MAP.get("trace_len")
    if trace_len_entry:
        trace_len_uuid, _ = trace_len_entry
        try:
            trace_len_bytes = await client.read_gatt_char(trace_len_uuid)
            trace_len = int.from_bytes(trace_len_bytes, byteorder="little")
            if trace_len:
                percent = int(raw_val * 100 / trace_len)  # integer division
                return f"{percent}"
        except Exception as er:
            print(f"Failed to read trace_len for trigger_delay: {er}")
    return str(raw_val)



class BLEParameterEditor:
    def __init__(self, parent, client, param_key):
        self.client = client
        self.param_key = param_key
        self.uuid, self.byte_size = UUID_MAP[param_key]
        self.mapping = MAPPINGS.get(param_key, None)
        self.param_raw_values = {}

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
            uuid_str, _ = UUID_MAP[self.param_key]
            self.uuid = uuid_str

            value_bytes = await self.client.read_gatt_char(self.uuid)
            raw_val = int.from_bytes(value_bytes, byteorder="little")

            self.param_raw_values[self.param_key] = raw_val
            print("Debug: all read:", self.param_raw_values)

            if self.mapping:
                value_dict = dict(self.mapping)
                label = value_dict.get(raw_val, "Unknown")
            else:
                label = str(raw_val)
            if self.param_key == "trigger_delay":
                label = self.param_raw_values["trigger_delay"]/self.param_raw_values["trace_len"]*100
                # label = await compute_trigger_delay(self.client, raw_val)

            # Update GUI in main thread
            self.frame.after(0, lambda: self.update_ui(label))
        except Exception as e:
            print("all read:", self.param_raw_values)
            print(f"Failed to read {self.param_key}:", e)
            self.frame.after(0, lambda: self.status.set("Read failed"))

    def update_ui(self, label):
        self.selected_value.set(label)
        self.widget["state"] = "readonly" if self.mapping else "normal"
        self.status.set("Fetched")

    def on_value_selected(self, event=None):
        asyncio.run(self._async_write_value())



    async def _async_write_value(self):
        try:
            label = self.selected_value.get()
            self.uuid, byte_size = UUID_MAP[self.param_key]

            if self.mapping:
                raw_val = next(val for val, lbl in self.mapping if lbl == label)
            else:
                raw_val = int(label)

            data = raw_val.to_bytes(byte_size, byteorder="little")  # Adjust byte size if needed
            await self.client.write_gatt_char(self.uuid, data)

            # Show human decimal label (from UI) and raw bytes sent (in hex)
            self.frame.after(0, lambda: self.status.set(f"Wrote {label} (bytes: {data.hex()})"))
            print(f"Wrote {raw_val} ({label}) to {self.param_key} as bytes: {data.hex()}")
            # self.frame.after(0, lambda: self.status.set(f"Wrote {label}"))

            # Debug log
            print(f"Wrote {raw_val} ({label}) to {self.param_key} ({self.uuid}, {byte_size} bytes)")
        except Exception as e:
            print(f"Failed to write {self.param_key}:", e)
            self.frame.after(0, lambda: self.status.set("Write failed"))


class ASensorParameterApp:
    def __init__(self, root, parent, address, name, is_connected):
        self.root = root
        self.root.title(address+ '('+ name+ ')')
        self.parent = parent  # Reference to BLEDeviceScanner
        self.client = self.parent.device_clients[address]  # or passed explicitly
        self.address = address
        self.name = name

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

        # Initialize connection status using is_connected
        initial_status = "Connected" if is_connected else "Disconnected"
        self.conn_status = tk.StringVar(value=initial_status)
        ttk.Label(conn_frame, textvariable=self.conn_status, foreground="blue").pack(side="left", padx=10)

        # Initial button states
        self.update_button_states()

        # Create editors but disable until connected
        for param_key in UUID_MAP.keys():
            editor = BLEParameterEditor(self.main_frame, self.client, param_key)
            self.editors[param_key] = editor
            print("Debug :", self.editors)

        self.commit_button = tk.Button(self.main_frame, text="SAVE", command=self.on_commit_button_click)
        self.commit_button.pack(pady=20)

        # ---- DEVICE ACTION BUTTONS ----
        self.buttons_frame = ttk.LabelFrame(self.main_frame, text="Device Actions")
        self.buttons_frame.pack(fill="x", pady=10)

        BLEActionButtons(self.buttons_frame, self.client)


        self.enable_editors()

    def connect_sensor(self):
        # Delegate to parent
        self.parent.connect_device(self.address)
        self.conn_status.set("Connected")
        self.update_button_states()

    def disconnect_sensor(self):
        # Delegate to parent

        self.parent.disconnect_device(self.address)
        self.conn_status.set("Disconnected")
        self.update_button_states()

    def on_commit_button_click(self):

        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(commit_changes(self.client))
        finally:
            loop.close()
        # Run async task from sync button callback
        # asyncio.create_task(commit_changes(self.client))

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


# async def commit_changes(client):
#     COMMIT_UUID = "1c930030-d459-11e7-9296-b8e856369374"
#     data = bytes([0x01])
#     try:
#         await client.write_gatt_char(COMMIT_UUID, data)
#         print("Commit successful")
#     except Exception as e:
#         print("Commit failed:", e)
async def commit_changes(client):
    # Write any byte, e.g., 0x01
    data = bytes([0x01])  # 1 byte of data
    COMMIT_UUID = UUID_MAP_BUTTON.get("commit")
    try:
        await client.write_gatt_char(COMMIT_UUID, data)
        print("Commit command sent successfully.")
    except Exception as e:
        print(f"Failed to write commit command: {e}")