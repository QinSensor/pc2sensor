import tkinter as tk
from tkinter import ttk
from bleak import BleakScanner, BleakClient
import threading
import asyncio
from .sensor_map import MAPPINGS, UUID_MAP_BUTTON, UUID_MAP


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
            # print("Debug: final:", self.param_final_values)
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

    # async def on_value_selected(self, event=None):
    #
    #     self.client = await self.reconnect()
    #     # TODO
    #     print("21")
    #     try:
    #         future = asyncio.run_coroutine_threadsafe(self.write_value_with_timeout(), self.loop)
    #         future.add_done_callback(lambda fut: print("Write completed or failed"))
    #     except asyncio.TimeoutError:
    #         print(f"Write timed out — assuming disconnect.")
    #         self.client = await self.reconnect()
    #         try:
    #             future = asyncio.run_coroutine_threadsafe(self.write_value_with_timeout(), self.loop)
    #             future.add_done_callback(lambda fut: print("Write completed or failed"))
    #             print("Write to Variant successful after reconnect")
    #         except Exception as e:
    #             print("Write to Variant failed after reconnect:", e)
    #             raise e
    #     except Exception as e:
    #         print("Write to Variant failed:", e)
    #         raise e
    #     print("22")

    async def on_value_selected(self, event=None):
        self.client = await self.reconnect()
        try:
            await self.write_value_with_timeout()
            print("Write completed successfully")

        except asyncio.TimeoutError:
            print("Write timed out — assuming disconnect.")
            self.client = await self.reconnect()
            try:
                await self.write_value_with_timeout()
                print("Write to Variant successful after reconnect")
            except Exception as e:
                print("Write to Variant failed after reconnect:", e)
                raise e
        except Exception as e:
            print("Write to Variant failed:", e)
            raise e

    async def reconnect(self):
        # address = self.client.address if self.client else None
        if not self.client or not self.client.is_connected:
            print("Not Connected! Trying to reconnect...")
            self.frame.after(0, lambda: self.status.set(f"Reconnecting..."))

            print("Setting Label")
            devices = await BleakScanner.discover(timeout=5.0)
            found = any(d.address == self.address for d in devices)
            print("Looking for device matching Address")
            if not found:
                self.frame.after(0, lambda: self.status.set(f"Sensor Not Found..."))
                raise Exception(f"Device with address {self.address} was not found during scan.")
            print("Before disconnection")
            try:
                # If client exists, disconnect first to clean up
                if self.client:
                    try:
                        await self.client.disconnect()
                    except Exception:
                        pass
                # Create new client instance if needed
                print("After disconnection")
                self.client = BleakClient(self.address)
                print("Creating new Client")
                await self.client.connect()
                self.frame.after(0, lambda: self.status.set(f"Reconnected"))
                print(f"Value Selected: Reconnected successfully to {self.address}.")
            except Exception as e:
                self.frame.after(0, lambda: self.status.set(f"Reconnection Failed"))
                print("Value Selected: Reconnect Device {address} failed:", e)
                return
        return self.client


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

    async def write_value_with_timeout(self, timeout=5):
        try:
            await asyncio.wait_for(self._async_write_value(), timeout=timeout)
        except asyncio.TimeoutError:
            print(f"Write operation timed out after {timeout} seconds.")
            self.frame.after(0, lambda: self.status.set("Write timed out"))
        except Exception as e:
            print("Unexpected error during write:", e)
            self.frame.after(0, lambda: self.status.set("Write failed"))






