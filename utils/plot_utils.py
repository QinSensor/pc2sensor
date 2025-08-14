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
    app.time_data = app.time_data[-max_points:] if app.time_data else [0]
    app.acc_data = app.acc_data[-max_points:] if app.acc_data else [0]
    app.vel_data = app.vel_data[-max_points:] if app.vel_data else [0]

    print(len(app.time_data), len(app.acc_data), len(app.vel_data))

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

    # Force redraw
    try:
        app.canvas.draw_idle()
    except Exception as e:
        print(f"Failed to redraw canvas: {e}")

    # Schedule next update call in 200ms
    app.root.after(200, lambda: update_plot_display(app))


def update_plots(ax_acc_time, ax_acc_freq, ax_vel_time, ax_vel_freq, time_data, acc_data, vel_data, canvas):
    print("Updating acc_time:", len(time_data))
    print("Updating acc_freq:", len(acc_data))
    # --- Acceleration vs Time ---
    ax_acc_time.clear()
    ax_acc_time.plot(time_data, acc_data)
    ax_acc_time.set_title("Acceleration vs Time")

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

import time
def start_acceleration_stream_Scanner(sender, info, loop, calib):
    async def notification_handler(sender, data):
        now = time.time()  # current timestamp

        calib_value = int(calib)
        conversion_factor = 250000/(65536*calib_value)
        acc_values = [(reading - 32768) * conversion_factor for reading in list(data)]
        acc_mean = sum(acc_values) / len(acc_values)  # simple example

        if info["data"] is []:
            print("calibration is: ", calib_value)
            print("Data length of one notification:", len(acc_values))

        # # Append every reading
        # info["data"].append({
        #     "timestamp": now,
        #     "acc_mean": acc_mean,
        #     "raw": acc_values
        # })
        info["data"].append({
            "timestamp": round(now, 2),
            "acc_mean": round(acc_mean, 2),
            "raw": [round(v, 2) for v in acc_values]
        })

    async def start_notify():
        print("\n notify:")
        if sender and sender.is_connected:
            await sender.start_notify(DATA_UUID, notification_handler)
            print("get notified")
        else:
            print("Client not connected, cannot start notifications")

    # Schedule the coroutine safely from synchronous context
    asyncio.run_coroutine_threadsafe(start_notify(), loop)
    print("Finish")


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

