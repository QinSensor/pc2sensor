import asyncio
import numpy as np

from .sensor_map import UUID_DATA
import time

# Replace with your actual UUIDs
DATA_UUID, data_size = UUID_DATA["data"]
calb_uuid, calb_size = UUID_DATA["calibration"]

def update_plot_display(info, canvas, ax_acc_time, ax_vel_time, ax_acc_freq, ax_vel_freq, max_points=200):
    print("Total Notification:", len(info["data"]))
    # Limit data size
    # plot_data = info["data"]
    plot_data = info["data"][-max_points:]

    # Extract data
    timestamps = [d["timestamp"] for d in plot_data]
    acc_means = [d["acc_mean"] for d in plot_data]
    velocity = [d.get("velocity", 0) for d in info["data"]]

    # --- Acceleration vs Time ---
    ax_acc_time.clear()
    ax_acc_time.plot(timestamps, acc_means, color="blue", label="Acceleration")
    ax_acc_time.set_title("Acceleration vs Time")
    ax_acc_time.set_xlabel("Time (s)")
    ax_acc_time.set_ylabel("Acceleration")
    ax_acc_time.legend()

    # --- Velocity vs Time ---
    ax_vel_time.clear()
    ax_vel_time.plot(timestamps, velocity, color="red", label="Velocity")
    ax_vel_time.set_title("Velocity vs Time")
    ax_vel_time.set_xlabel("Time (s)")
    ax_vel_time.set_ylabel("Velocity")
    ax_vel_time.legend()

    # Helper function for FFT plot
    def plot_fft(ax, data, time_data, title, color="green"):
        ax.clear()
        n = len(data)
        if n > 1:
            dt_arr = np.diff(time_data)
            dt = np.mean(dt_arr[dt_arr > 0]) if np.any(dt_arr > 0) else 1e-6
            freqs = np.fft.rfftfreq(n, d=dt)
            fft_vals = np.abs(np.fft.rfft(data))
            ax.plot(freqs, fft_vals, color=color)
            ax.set_title(title)
            ax.set_xlabel("Frequency (Hz)")
            ax.set_ylabel("Magnitude")
        else:
            ax.text(0.5, 0.5, "Not enough data for FFT", ha='center', va='center')
            ax.set_title(title)

    # --- Acceleration Frequency Spectrum ---
    plot_fft(ax_acc_freq, acc_means, timestamps, "Acceleration Frequency Spectrum", color="green")

    # --- Velocity Frequency Spectrum ---
    plot_fft(ax_vel_freq, velocity, timestamps, "Velocity Frequency Spectrum", color="orange")

    # Redraw canvas
    canvas.draw_idle()

    # Schedule next update in 200 ms
    canvas.get_tk_widget().after(200, lambda: update_plot_display(info, canvas, ax_acc_time, ax_vel_time, ax_acc_freq, ax_vel_freq, max_points))


def start_acceleration_stream_Scanner(sender, info, loop, calib):
    if "count_notify" not in info:
        info["count_notify"] = 0

    async def notification_handler(sender, data):
        now = time.time()  # current timestamp

        calib_value = int(calib)
        conversion_factor = 250000/(65536*calib_value)
        acc_values = [(reading - 32768) * conversion_factor for reading in list(data)]
        acc_mean = sum(acc_values) / len(acc_values)  # simple example

        if len(info["data"]) == 0:
            print("calibration is: ", calib_value)
            print("Data length of one notification:", len(acc_values))

        if len(info["data"]) == 0:
            # First measurement, assume velocity = 0
            velocity = 0
        else:
            # Previous velocity
            prev_velocity = info["data"][-1].get("velocity", 0)
            prev_time = info["data"][-1]["timestamp"]
            dt = now - prev_time  # time difference in seconds
            velocity = prev_velocity + acc_mean * dt

        info["data"].append({
            "timestamp": round(now, 2),
            "acc_mean": round(acc_mean, 2),
            "acc_values": [round(v, 2) for v in acc_values],
            "velocity": round(velocity, 2),
        })

        info["count_notify"] += 1
        print("Notification count:", info["count_notify"])

    async def start_notify():
        print("\nNotify:")
        if sender and sender.is_connected:
            await sender.start_notify(DATA_UUID, notification_handler)
            print("Get notified")
        else:
            print("Client not connected, cannot start notifications")

    # Schedule the coroutine safely from synchronous context
    asyncio.run_coroutine_threadsafe(start_notify(), loop)
    print("Finish.")

