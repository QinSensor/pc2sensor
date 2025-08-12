import asyncio
import numpy as np

from .sensor_map import UUID_DATA
import struct

# Replace with your actual UUIDs
DATA_UUID, data_size = UUID_DATA["data"]
calb_uuid, calb_size = UUID_DATA["calibration"]


def update_plot_display(app):
    """
    Called repeatedly by Tkinter root.after.
    Updates time, acceleration, velocity data arrays and redraws plots.
    """

    # Limit data size to avoid memory bloat
    max_points = 200
    if len(app.time_data) > max_points:
        app.time_data = app.time_data[-max_points:]
        app.acc_data = app.acc_data[-max_points:]
        app.vel_data = app.vel_data[-max_points:]

    # If no data yet, initialize with zeroes
    if not app.time_data:
        app.time_data.append(0)
        app.acc_data.append(0)
        app.vel_data.append(0)

    # Update plots using your plotting function
    update_plots(
        app.ax_acc_time,
        app.ax_acc_freq,
        app.ax_vel_time,
        app.ax_vel_freq,
        app.time_data,
        app.acc_data,
        app.vel_data,
        app.canvas,
    )

    # Schedule next update call in 200ms
    app.root.after(200, lambda: update_plot_display(app))


def update_plots(ax_acc_time, ax_acc_freq, ax_vel_time, ax_vel_freq, time_data, acc_data, vel_data, canvas):
    # Example placeholder implementation: replace with your own plot drawing logic

    ax_acc_time.clear()
    ax_acc_time.plot(time_data, acc_data)
    ax_acc_time.set_title("Acceleration vs Time")

    # Similarly update freq domain and velocity plots here...
    canvas.draw_idle()

def make_notification_handler(app):
    def handler(sender, data):
        acceleration = parse_acceleration_packet(data)
        acc_sample = acceleration[0] if len(acceleration) > 0 else 0

        app.acc_data.append(acc_sample)
        app.time_data.append(len(app.time_data))
        app.vel_data.append(0)

        max_points = 200
        if len(app.acc_data) > max_points:
            app.acc_data = app.acc_data[-max_points:]
            app.time_data = app.time_data[-max_points:]
            app.vel_data = app.vel_data[-max_points:]
    return handler

def start_acceleration_stream(app2):
    """
    Starts BLE notifications on the data characteristic and appends incoming data
    to app2.data_buffer.
    """
    async def notification_handler(sender, data):
        """
        Callback for BLE notifications.
        `data` is bytes received from the characteristic.
        """
        # Append incoming data bytes to buffer for processing
        app2.data_buffer.extend(data)

    async def start_notify():
        if app2.client and app2.client.is_connected:
            await app2.client.start_notify(DATA_UUID, notification_handler)
        else:
            print("Client not connected, cannot start notifications")

    # Schedule the coroutine safely from synchronous context
    asyncio.run_coroutine_threadsafe(start_notify(), app2.loop)

def start_acceleration_stream(app, client):
    handler = make_notification_handler(app)
    asyncio.run_coroutine_threadsafe(
        client.start_notify(DATA_UUID, handler),
        asyncio.get_event_loop()  # or app.loop if you keep it
    )


def parse_acceleration_packet(raw_data):
    """
    Parse raw data from sensor characteristic.
    raw_data: bytes object with length 16 or 128.
    Returns:
        np.array of floats: acceleration in g units (signed, centered around 0)
    """
    # Number of samples = len(raw_data) / 2
    num_samples = len(raw_data) // 2
    # Unpack as unsigned shorts, little-endian
    samples = struct.unpack('<' + 'H' * num_samples, raw_data)

    # Convert to signed centered values: raw - 0x8000
    centered = np.array(samples) - 0x8000

    # Convert to g units (assuming full scale ±2g, raw value range is 0 to 65535)
    # scale_factor depends on sensor spec; if ±2g over 65536 steps:
    scale_factor = 2.0 / 32768  # since 0x8000 is center

    acceleration_g = centered * scale_factor
    return acceleration_g

# def update_plots(ax_acc_time, ax_acc_freq, ax_vel_time, ax_vel_freq,
#                  time_data, acc_data, vel_data, canvas, dt=0.02):
#     """
#     Update four plots: acceleration time, acceleration spectrum,
#     velocity time, velocity spectrum.
#     """
#     # FFT
#     if len(acc_data) > 10:
#         acc_fft = np.abs(np.fft.rfft(acc_data))
#         vel_fft = np.abs(np.fft.rfft(vel_data))
#         freqs = np.fft.rfftfreq(len(acc_data), d=dt)
#     else:
#         acc_fft = vel_fft = freqs = []
#
#     # Clear and redraw
#     ax_acc_time.clear()
#     ax_acc_time.plot(time_data, acc_data)
#     ax_acc_time.set_title("Acceleration vs Time")
#
#     ax_acc_freq.clear()
#     ax_acc_freq.plot(freqs, acc_fft)
#     ax_acc_freq.set_title("Acceleration Spectrum")
#
#     ax_vel_time.clear()
#     ax_vel_time.plot(time_data, vel_data)
#     ax_vel_time.set_title("Velocity vs Time")
#
#     ax_vel_freq.clear()
#     ax_vel_freq.plot(freqs, vel_fft)
#     ax_vel_freq.set_title("Velocity Spectrum")
#
#     canvas.draw()
#
    


# def handle_acceleration(app, sender, data: bytearray):
#     """Callback when acceleration data arrives."""
#     # Example: assume data is 3x int16 values (X, Y, Z) in little endian
#     x = int.from_bytes(data[0:2], byteorder="little", signed=True)
#     y = int.from_bytes(data[2:4], byteorder="little", signed=True)
#     z = int.from_bytes(data[4:6], byteorder="little", signed=True)
#
#     # Pick one axis (or magnitude)
#     acc_value = (x**2 + y**2 + z**2)**0.5  # magnitude in raw units
#
#     # Keep data buffers small
#     if len(app.time_data) > 200:
#         app.time_data.pop(0)
#         app.acc_data.pop(0)
#         app.vel_data.pop(0)
#
#     t = app.time_data[-1] + 0.02 if app.time_data else 0
#     vel_value = (app.vel_data[-1] + acc_value*0.02) if app.vel_data else 0
#
#     app.time_data.append(t)
#     app.acc_data.append(acc_value)
#     app.vel_data.append(vel_value)
#
#
# def update_plot_display(app):
#     async def read_and_update():
#         try:
#             raw_data = await app.client.read_gatt_char(DATA_UUID)
#             acc_samples = parse_acceleration_packet(raw_data)
#
#             # Calculate instantaneous acceleration magnitude (RMS)
#             magnitude = np.sqrt(np.mean(acc_samples ** 2))
#
#             # Update data lists (keep max 200 points)
#             if len(app.time_data) > 200:
#                 app.time_data.pop(0)
#                 app.acc_data.pop(0)
#                 app.vel_data.pop(0)
#
#             t = app.time_data[-1] + 0.02 if app.time_data else 0
#             app.time_data.append(t)
#             app.acc_data.append(magnitude)
#
#             # Simple velocity integration (velocity += acceleration * dt)
#             dt = 0.02
#             vel = app.vel_data[-1] + magnitude * dt if app.vel_data else 0
#             app.vel_data.append(vel)
#
#             # Update the plots
#             update_plots(app.ax_acc_time, app.ax_acc_freq, app.ax_vel_time, app.ax_vel_freq,
#                          app.time_data, app.acc_data, app.vel_data, app.canvas)
#         except Exception as e:
#             print("Failed to read or update plot:", e)
#         finally:
#             # Schedule next update after 200 ms
#             app.root.after(200, lambda: update_plot_display(app))
#
#     # Run the async read_and_update safely in the event loop
#     asyncio.run_coroutine_threadsafe(read_and_update(), app.loop)
