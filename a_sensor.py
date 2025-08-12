import asyncio
import tkinter as tk
from tkinter import ttk
import threading

import numpy as np
import matplotlib
matplotlib.use("TkAgg")
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from bleak import BleakClient, BleakScanner

from ActionButtons import BLEActionButtons
from sensor_map import UUID_MAP, MAPPINGS, UUID_MAP_BUTTON, PARAM_LABELS
from data_utils import async_update_sensor_readings, update_plots


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


class ASensorParameterApp:
    def __init__(self, root, parent, address, name, client, loop):
        self.root = root
        self.loop = loop
        self.root.title(address + '(' + name + ')')
        self.parent = parent  # Reference to BLEDeviceScanner
        # self.client = self.parent.device_clients[address]  # or passed explicitly
        self.client = client  # or passed explicitly
        self.address = address
        self.name = name
        self.param_raw_values = {}
        self.param_final_values = {}

        self.editors = {}

        self.main_frame = ttk.Frame(root)
        self.main_frame.pack(padx=10, pady=10)



        # Create editors but disable until connected
        for param_key in UUID_MAP.keys():
            label_text = PARAM_LABELS.get(param_key, param_key)
            editor = BLEParameterEditor(self.main_frame, self.client, param_key, self.param_raw_values,
                                        self.param_final_values, self.loop, label=label_text)
            self.editors[param_key] = editor

        # print(self.param_raw_values)
        print("Debug: final values: ", self.param_final_values)

        self.commit_button = tk.Button(self.main_frame, text="SAVE", command=self.on_commit_button_click)
        self.commit_button.pack(pady=0)
        # Status label (initially empty)
        self.commit_status_label = tk.Label(self.main_frame, text="", fg="green")
        self.commit_status_label.pack()


        conn_frame = ttk.Frame(self.main_frame)
        conn_frame.pack(fill="x", pady=5)

        self.connect_btn = ttk.Button(conn_frame, text="Connect", command=self.connect_sensor)
        self.connect_btn.pack(side="left", padx=5)

        self.disconnect_btn = ttk.Button(conn_frame, text="Disconnect", command=self.disconnect_sensor)
        self.disconnect_btn.pack(side="left", padx=5)

        # Connection status
        initial_status = "Connected" if client.is_connected else "Disconnected"
        self.conn_status = tk.StringVar(value=initial_status)
        ttk.Label(conn_frame, textvariable=self.conn_status, foreground="blue").pack(side="left", padx=10)

        # Device actions in same line
        actions_frame = ttk.LabelFrame(conn_frame, text="Device Actions")
        actions_frame.pack(side="left", padx=10)
        BLEActionButtons(actions_frame, self.client)

        # ---- TEMPERATURE & BATTERY ----
        sensor_frame = ttk.LabelFrame(self.main_frame, text="Sensor Readings")
        sensor_frame.pack(fill="x", pady=0)

        self.temp_var = tk.StringVar(value="Temp: -- °C")
        self.battery_var = tk.StringVar(value="Battery: -- %")
        ttk.Label(sensor_frame, textvariable=self.temp_var).pack(anchor="w")
        ttk.Label(sensor_frame, textvariable=self.battery_var).pack(anchor="w")

        # ---- PLOTS ----
        fig = Figure(figsize=(8, 6))
        self.ax_acc_time = fig.add_subplot(221)
        self.ax_acc_freq = fig.add_subplot(222)
        self.ax_vel_time = fig.add_subplot(223)
        self.ax_vel_freq = fig.add_subplot(224)

        self.canvas = FigureCanvasTkAgg(fig, master=self.main_frame)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill="both", expand=True)

        # Data buffers
        self.time_data = []
        self.acc_data = []
        self.vel_data = []

        # Start periodic updates
        self.root.after(1000, self.update_sensor_readings)
        self.root.after(200, self.update_plots)

        self.enable_editors()

    def update_sensor_readings(self):
        asyncio.run_coroutine_threadsafe(
            async_update_sensor_readings(self.client, self.temp_var, self.battery_var),
            self.loop
        )
        self.root.after(2000, self.update_sensor_readings)

    def update_plot_display(self):
        # --- Fake example data ---
        if len(self.time_data) > 200:
            self.time_data.pop(0)
            self.acc_data.pop(0)
            self.vel_data.pop(0)
        t = self.time_data[-1] + 0.02 if self.time_data else 0
        acc = np.sin(2 * np.pi * 1 * t)
        vel = (self.vel_data[-1] + acc * 0.02) if self.vel_data else 0
        self.time_data.append(t)
        self.acc_data.append(acc)
        self.vel_data.append(vel)

        update_plots(self.ax_acc_time, self.ax_acc_freq, self.ax_vel_time, self.ax_vel_freq,
                     self.time_data, self.acc_data, self.vel_data, self.canvas)

        self.root.after(200, self.update_plot_display)

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

    def _on_commit_done(self, future):
        try:
            new_client = future.result()
            self.client = new_client
            self.commit_status_label.after(0, lambda:
            self.commit_status_label.config(text="Commit successful ✅", fg="green"))
        except Exception as ee:
            self.commit_status_label.after(0, lambda:
            self.commit_status_label.config(text=f"Commit failed ❌: {ee}", fg="red"))
        finally:
            self.commit_status_label.after(3000, lambda: self.commit_status_label.config(text=""))

    def on_commit_button_click(self):
        # try:
        print('1')
        self.commit_status_label.after(0, lambda:
        self.commit_status_label.config(text="Commiting...", fg="green"))
        # self.commit_status_label.update_idletasks()  # forces immediate redraw

        future = asyncio.run_coroutine_threadsafe(commit_changes(self, self.client), self.loop)
        future.add_done_callback(lambda fut: self._on_commit_done(fut))

            # new_client = future.result()  # wait for coroutine to finish
            # self.client = new_client  # update client reference if reconnect created new one
            #
            # self.commit_status_label.after(0, lambda:
            # self.commit_status_label.config(text="Commit successful ✅", fg="green"))
        # except Exception as ee:
        #     print("Exception caught:", ee)  # debug line
        #     self.commit_status_label.after(0, lambda exe=ee:
        #     self.commit_status_label.config(text=f"Commit failed ❌: {exe}", fg="red"))
        # finally:
        #     self.commit_status_label.after(3000, lambda: self.commit_status_label.config(text=""))

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
