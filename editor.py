import tkinter as tk
from tkinter import ttk
from bleak import BleakScanner, BleakClient
import threading
import asyncio

from sensor_map import MAPPINGS, UUID_MAP_BUTTON, UUID_MAP


class BLEParameterEditor:
    def __init__(self, parent, client, param_key, param_raw_values, param_final_values, loop, label=None):
        self.loop = loop
        self.client = client
        self.address = client.address
        self.param_key = param_key
        self.param_raw_values = param_raw_values
        self.param_final_values = param_final_values
        self.uuid, self.byte_size = UUID_MAP[param_key]
        self.mapping = MAPPINGS.get(param_key, None)

        display_label = label if label else f"{param_key.replace('_', ' ').title()}"

        self.frame = ttk.Frame(parent)
        self.frame.pack(fill='x', pady=5)

        ttk.Label(self.frame, text=display_label).pack(side='left', padx=5)

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
            self.widget.bind("<<ComboboxSelected>>", self.on_value_selected_sync)
            self.widget.pack(side='left', padx=5)
        else:
            self.widget = ttk.Entry(self.frame, textvariable=self.selected_value)
            self.widget.pack(side='left', padx=5)
            self.widget.bind("<Return>", self.on_value_selected_sync)

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

            if self.mapping:
                value_dict = dict(self.mapping)
                label = value_dict.get(raw_val, "Unknown")
            else:
                label = str(raw_val)
            self.param_final_values[self.param_key] = label
            print("Debug: final:", self.param_final_values)
            if self.param_key == "trigger_delay":
                label = int(self.param_final_values["trigger_delay"])  # TODO ask Jim about its definiction

            # Update GUI in main thread
            self.frame.after(0, lambda: self.update_ui(label))
        except Exception as e:
            print(self.param_raw_values)
            print(f"Failed to read {self.param_key}:", e)
            self.frame.after(0, lambda: self.status.set("Read failed"))

    def update_ui(self, label):
        self.selected_value.set(label)
        self.widget["state"] = "readonly" if self.mapping else "normal"
        self.status.set("Fetched")

    def on_value_selected_sync(self, event=None):
        # schedule the async method on the running loop
        asyncio.run_coroutine_threadsafe(self.on_value_selected(event), self.loop)
        # asyncio.create_task(self.on_value_selected(event), self.loop)

    async def on_value_selected(self, event=None):
        address = self.client.address if self.client else None
        if not self.client or not self.client.is_connected:

            print("Not Connected! Trying to reconnect...")
            self.frame.after(0, lambda: self.status.set(f"Reconnecting..."))

            print("31")
            devices = await BleakScanner.discover(timeout=5.0)
            found = any(d.address == address for d in devices)
            print("32")
            if not found:

                self.frame.after(0, lambda: self.status.set(f"Sensor Not Found..."))
                raise Exception(f"Device with address {address} was not found during scan.")
            print("33")
            try:
                # If client exists, disconnect first to clean up
                if self.client:
                    try:
                        await self.client.disconnect()
                    except Exception:
                        pass
                # Create new client instance if needed
                print("34")
                self.client = BleakClient(self.address)
                print("35")
                await self.client.connect()
                self.frame.after(0, lambda: self.status.set(f"Reconnected"))
                print(f"Value Selected: Reconnected successfully to {address}.")
            except Exception as e:
                self.frame.after(0, lambda: self.status.set(f"Reconnection Failed"))
                print("Value Selected: Reconnect Device {address} failed:", e)
                return
        print("21")
        await self._async_write_value()
        print("22")

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

            # Debug log
            print(f"Wrote {raw_val} ({label}) to {self.param_key} ({self.uuid}, {byte_size} bytes)")
        except Exception as e:
            print(f"Failed to write {self.param_key}:", e)
            self.frame.after(0, lambda: self.status.set("Write failed"))


async def commit_changes(self, client):
    print('11')
    client =await ensure_fresh_connection(self, client)
    print('12')
    COMMIT_UUID = "1c930030-d459-11e7-9296-b8e856369374"
    data = bytes([0x01])

    self.commit_status_label.after(0, lambda:
        self.commit_status_label.config(text="Committing...", fg="green"))
    await asyncio.sleep(0)  # let UI refresh before we block
    # self.commit_status_label.after(0, lambda:
    # self.commit_status_label.config(text="Commit successful ✅", fg="green"))
    # self.commit_status_label.config(text=f"Committing...", fg="green")
    print('13')

    try:
        await asyncio.wait_for(client.write_gatt_char(COMMIT_UUID, data), timeout=5)
        # await client.write_gatt_char(COMMIT_UUID, data)
        # self.commit_status_label.config(text=f"Commit successful", fg="green")
        print("Commit successful")
    except asyncio.TimeoutError:
        print(f"Write to {COMMIT_UUID} timed out — assuming disconnect.")
        # self.commit_status_label.config(text=f"Reconnecting...", fg="red")
        client = await ensure_fresh_connection(self, client)
        try:
            await asyncio.wait_for(client.write_gatt_char(COMMIT_UUID, data), timeout=5)
            # self.commit_status_label.config(text="Commit successful ✅", fg="green")
            print("Commit successful after reconnect")
        except Exception as e:
            # self.commit_status_label.config(text="Commit failed ❌", fg="red")
            print("Commit failed after reconnect:", e)
            raise e
    except Exception as e:
        # self.commit_status_label.config(text=f"Commit failed", fg="red")
        print("Commit failed:", e)
        raise e

    return client


async def ensure_fresh_connection(self, client):
    if not client or not client.is_connected:
        address = client.address if client else None
        self.commit_status_label.config(text=f"Reconnecting...", fg="red")
        print(f"Not Connected to {address}! Trying to reconnect...")

        # Scan for device first
        devices = await BleakScanner.discover(timeout=5.0)
        found = any(d.address == address for d in devices)

        if not found:
            self.commit_status_label.config(text=f"Sensor Not Found", fg="red")
            raise Exception(f"Device with address {address} was not found during scan.")

        if client:
            try:
                await client.disconnect()
            except Exception:
                pass

        client = BleakClient(address)
        try:
            await client.connect()
            self.commit_status_label.config(text=f"Reconnected", fg="green")
            print(f"Reconnected successfully to {address}.")
        except Exception as e:
            self.commit_status_label.config(text=f"Sensor Not Found", fg="red")
            raise Exception(f"Device {address} not connected and reconnection failed.") from e

    return client
