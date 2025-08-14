import tkinter as tk
from tkinter import ttk
import threading
from bleak import BleakClient, BleakScanner
from utils.edit_variant import BLEParameterEditor
import matplotlib
matplotlib.use("TkAgg")
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from utils.ActionButtons import BLEActionButtons
from utils.sensor_map import UUID_MAP,  PARAM_LABELS
from utils.plot_utils import update_plot_display
from utils.ble_connect import connect_sensor, disconnect_sensor
from utils.commit_utils import on_commit_button_click
from utils.show_battery_temp import *


class ASensorParameterApp:
    def __init__(self, root, parent, address, name, sensor_connection, loop):
        self.sensor_connection = sensor_connection
        self.data_buffer = []
        self.root = root
        self.loop = loop
        self.root.title(address + '(' + name + ')')
        self.parent = parent  # Reference to BLEDeviceScanner
        self.client = sensor_connection.get_client()  # or passed explicitly
        self.address = address
        self.name = name
        self.param_raw_values = {}
        self.param_final_values = {}

        self.editors = {}

        self.main_frame = ttk.Frame(root)
        self.main_frame.pack(padx=0, pady=0)

        # Create editors but disable until connected
        for param_key in UUID_MAP.keys():
            label_text = PARAM_LABELS.get(param_key, param_key)
            editor = BLEParameterEditor(self.main_frame, self.client, param_key, self.param_raw_values,
                                        self.param_final_values, self.loop, label=label_text)
            self.editors[param_key] = editor

        # print("Debug: final values: ", self.param_final_values)

        button_frame = tk.Frame(self.main_frame)
        button_frame.pack(pady=5)
        self.commit_button = tk.Button(button_frame, text="SAVE",
                                       command=lambda: on_commit_button_click(self, address, parent))
        self.commit_button.pack(side="left", padx=5)
        self.commit_status_label = tk.Label(button_frame, text="", fg="green")
        self.commit_status_label.pack(side="left", padx=5)

        conn_frame = ttk.Frame(self.main_frame)
        conn_frame.pack(fill="x", pady=0)

        self.connect_btn = ttk.Button(conn_frame, text="Connect", command=lambda: connect_sensor(self))
        self.connect_btn.pack(side="left", padx=0)

        self.disconnect_btn = ttk.Button(conn_frame, text="Disconnect", command=lambda: disconnect_sensor(self))
        self.disconnect_btn.pack(side="left", padx=0)

        # Connection status
        initial_status = "Connected" if self.client.is_connected else "Disconnected"
        self.conn_status = tk.StringVar(value=initial_status)
        ttk.Label(conn_frame, textvariable=self.conn_status, foreground="blue").pack(side="left", padx=10)

        # Device actions in same line
        actions_frame = ttk.LabelFrame(conn_frame, text="Device Actions")
        actions_frame.pack(side="left", padx=0)
        BLEActionButtons(actions_frame, self.client)

        # ---- TEMPERATURE & BATTERY ----
        sensor_frame = tk.Frame(self.main_frame)
        sensor_frame.pack(fill="x", pady=0)

        self.temp_var = tk.StringVar(value="Temp: -- °C")
        self.battery_var = tk.StringVar(value="Battery: -- V")
        self.time_var = tk.StringVar(value="Time: --:--:--")

        ttk.Label(sensor_frame, textvariable=self.temp_var).grid(row=0, column=0, padx=5, sticky="w")
        ttk.Label(sensor_frame, textvariable=self.battery_var).grid(row=0, column=1, padx=5, sticky="w")
        ttk.Label(sensor_frame, textvariable=self.time_var).grid(row=0, column=2, padx=5, sticky="w")

        # ---- PLOTS ----
        fig = Figure(figsize=(12, 9))
        self.ax_acc_time = fig.add_subplot(221)
        self.ax_acc_freq = fig.add_subplot(222)
        self.ax_vel_time = fig.add_subplot(223)
        self.ax_vel_freq = fig.add_subplot(224)

        self.canvas = FigureCanvasTkAgg(fig, master=self.main_frame)
        fig.tight_layout(pad=7.0)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill="both", expand=True, pady=10, padx=10)

        # Start periodic updates
        self.root.after(1000, lambda: update_temp_time(self))
        self.root.after(200, lambda: update_plot_display(info=self.parent.device_map[address],
                                                         canvas=self.canvas,
                                                         ax_acc_time=self.ax_acc_time,
                                                         ax_vel_time=self.ax_vel_time,
                                                         ax_acc_freq=self.ax_acc_freq,
                                                         ax_vel_freq=self.ax_vel_freq
                                                         ))
        sensor_frame.pack(fill="x", pady=10)

        self.enable_editors()

    def enable_editors(self):
        for editor in self.editors.values():
            editor.widget["state"] = "normal"
            editor.status.set("Connected")
            threading.Thread(target=editor.read_value, daemon=True).start()


class SensorConnection:
    def __init__(self, address):
        self.address = address
        self.client: BleakClient | None = None

    async def connect(self):
        try:
            if self.client and getattr(self.client, "is_connected", False):
                await self.client.disconnect()
            self.client = BleakClient(self.address)
            await self.client.connect()
            print(f"Connected to {self.address}")
        except Exception as e:
            print(f"Failed to connect {self.address}: {e}")

    async def disconnect(self):
        if self.client and getattr(self.client, "is_connected", False):
            await self.client.disconnect()

    def get_client(self):
        return self.client

    @property
    def is_connected(self):
        return self.client.is_connected if self.client else False

    async def reconnect(self):
        try:
            if self.client and getattr(self.client, "is_connected", False):
                await self.client.disconnect()
            if self.client and self.client.is_connected:
                await self.client.disconnect()
            self.client = BleakClient(self.address)
            await self.client.connect()
            print(f"Reconnected to {self.address}")

        except Exception as e:
            print(f"Failed to reconnect {self.address}: {e}")


