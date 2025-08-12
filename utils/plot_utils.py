import asyncio
import numpy as np

from .sensor_map import UUID_DATA
import struct

# Replace with your actual UUIDs
DATA_UUID, data_size = UUID_DATA["data"]
calb_uuid, calb_size = UUID_DATA["calibration"]


def update_plot_display(app):
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
    # --- Acceleration vs Time ---
    ax_acc_time.clear()
    ax_acc_time.plot(time_data, acc_data)
    ax_acc_time.set_title("Acceleration vs Time")

    # # --- Acceleration Frequency Domain ---
    # ax_acc_freq.clear()
    # if len(acc_data) > 1:
    #     dt = np.mean(np.diff(time_data))   # TODO ask Jim
    #     # dt = time_data[1] - time_data[0]
    #     if dt == 0:
    #         dt = 1e-6  # tiny value to avoid zero division
    #     freqs = np.fft.rfftfreq(len(acc_data), d=dt)
    #     fft_vals = np.abs(np.fft.rfft(acc_data))
    #     ax_acc_freq.plot(freqs, fft_vals)
    # ax_acc_freq.set_title("Acceleration Frequency Spectrum")

    # --- Velocity vs Time ---
    ax_vel_time.clear()
    ax_vel_time.plot(time_data, vel_data)
    ax_vel_time.set_title("Velocity vs Time")

    # Frequency domain plotting helper
    def plot_fft(ax, data, time_data, title):
        n = len(data)
        if n < 2:
            # Not enough data for FFT
            ax.text(0.5, 0.5, "Not enough data for FFT", ha='center', va='center')
            ax.set_title(title)
            return

        # Calculate sampling interval dt safely
        dt_arr = np.diff(time_data)
        dt = np.mean(dt_arr[dt_arr > 0]) if np.any(dt_arr > 0) else 1e-6

        freqs = np.fft.rfftfreq(n, d=dt)
        fft_vals = np.abs(np.fft.rfft(data))

        # Defensive check: truncate fft_vals if length mismatch happens
        if len(freqs) != len(fft_vals):
            min_len = min(len(freqs), len(fft_vals))
            freqs = freqs[:min_len]
            fft_vals = fft_vals[:min_len]

        ax.plot(freqs, fft_vals)
        ax.set_title(title)
        ax.set_xlabel("Frequency (Hz)")
        ax.set_ylabel("Magnitude")

    # Plot acceleration frequency
    plot_fft(ax_acc_freq, acc_data, time_data, "Acceleration Frequency Spectrum")

    # Plot velocity frequency
    plot_fft(ax_vel_freq, vel_data, time_data, "Velocity Frequency Spectrum")



    canvas.draw_idle()


def start_acceleration_stream(app2):
    import time
    import struct

    async def notification_handler(sender, data):
        now = time.time()  # current timestamp

        # Example: interpret bytes as signed integers
        acc_values = list(data)  # replace with correct decoding
        acc_mean = sum(acc_values) / len(acc_values)  # simple example

        app2.time_data.append(now)
        app2.acc_data.append(acc_mean)

        # Optional: integrate to get velocity
        if len(app2.time_data) > 1:
            dt = app2.time_data[-1] - app2.time_data[-2]
            new_vel = app2.vel_data[-1] + acc_mean * dt
            app2.vel_data.append(new_vel)
        else:
            app2.vel_data.append(0)

    async def start_notify():
        print("notify:")
        if app2.client and app2.client.is_connected:
            await app2.client.start_notify(DATA_UUID, notification_handler)
            print("get notified")
        else:
            print("Client not connected, cannot start notifications")

    # Schedule the coroutine safely from synchronous context
    asyncio.run_coroutine_threadsafe(start_notify(), app2.loop)
    print("Finish")


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
