import asyncio
import tkinter as tk
from tkinter import ttk
import threading

from editor import BLEParameterEditor

import matplotlib
matplotlib.use("TkAgg")
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from ActionButtons import BLEActionButtons
from sensor_map import UUID_MAP,  PARAM_LABELS
from data_utils import async_update_sensor_readings, update_plots, start_acceleration_stream, update_temp_time, \
    update_plot_display
from ble_connect import connect_sensor, disconnect_sensor
from commit_utils import on_commit_button_click


class ASensorParameterApp:
    def __init__(self, root, parent, address, name, client, loop):
        self.root = root
        self.loop = loop
        self.root.title(address + '(' + name + ')')
        self.parent = parent  # Reference to BLEDeviceScanner
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

        self.commit_button = tk.Button(self.main_frame, text="SAVE", command=lambda: on_commit_button_click(self))
        self.commit_button.pack(pady=0)
        # Status label (initially empty)
        self.commit_status_label = tk.Label(self.main_frame, text="", fg="green")
        self.commit_status_label.pack()


        conn_frame = ttk.Frame(self.main_frame)
        conn_frame.pack(fill="x", pady=5)

        self.connect_btn = ttk.Button(conn_frame, text="Connect", command=lambda: connect_sensor(self))
        self.connect_btn.pack(side="left", padx=5)

        self.disconnect_btn = ttk.Button(conn_frame, text="Disconnect", command=lambda: disconnect_sensor(self))
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
        self.root.after(1000, lambda: update_temp_time(self))
        self.root.after(200, lambda: update_plot_display(self))

        self.enable_editors()

    def enable_editors(self):
        for editor in self.editors.values():
            editor.widget["state"] = "normal"
            editor.status.set("Connected")
            # Trigger read again after enabling
            threading.Thread(target=editor.read_value, daemon=True).start()



