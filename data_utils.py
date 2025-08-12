import asyncio
import numpy as np

from sensor_map import UUID_DATA

# Replace with your actual UUIDs
DATA_UUID, data_size = UUID_DATA["data"]
calb_uuid, calb_size = UUID_DATA["calibration"]
TEMP_UUID, _ = UUID_DATA["temp"]
BATTERY_UUID, _ = UUID_DATA["battery"]


async def read_ble_value(client, uuid):
    """Read a BLE characteristic and return integer value."""
    try:
        data = await client.read_gatt_char(uuid)
        return int.from_bytes(data, byteorder="little", signed=True)
    except Exception as e:
        print(f"Error reading {uuid}: {e}")
        return None


async def async_update_sensor_readings(client, temp_var, battery_var):
    """Read temperature and battery from BLE and update Tkinter StringVars."""
    temp_raw = await read_ble_value(client, TEMP_UUID)
    batt_raw = await read_ble_value(client, BATTERY_UUID)
    if temp_raw is not None:
        temp_var.set(f"Temp: {temp_raw / 100:.2f} °C")
    if batt_raw is not None:
        battery_var.set(f"Battery: {batt_raw}%")


def update_temp_time(app):
        asyncio.run_coroutine_threadsafe(
            async_update_sensor_readings(app.client, app.temp_var, app.battery_var),
            app.loop
        )
        app.root.after(200000, lambda: update_temp_time(app))

def update_plot_display(app):
    # --- Fake example data ---
    if len(app.time_data) > 200:
        app.time_data.pop(0)
        app.acc_data.pop(0)
        app.vel_data.pop(0)
    t = app.time_data[-1] + 0.02 if app.time_data else 0
    acc = np.sin(2 * np.pi * 1 * t)
    vel = (app.vel_data[-1] + acc * 0.02) if app.vel_data else 0
    app.time_data.append(t)
    app.acc_data.append(acc)
    app.vel_data.append(vel)

    update_plots(app.ax_acc_time, app.ax_acc_freq, app.ax_vel_time, app.ax_vel_freq,
                 app.time_data, app.acc_data, app.vel_data, app.canvas)

    app.root.after(200, lambda: update_plot_display(app))


def update_plots(ax_acc_time, ax_acc_freq, ax_vel_time, ax_vel_freq,
                 time_data, acc_data, vel_data, canvas, dt=0.02):
    """
    Update four plots: acceleration time, acceleration spectrum,
    velocity time, velocity spectrum.
    """
    # FFT
    if len(acc_data) > 10:
        acc_fft = np.abs(np.fft.rfft(acc_data))
        vel_fft = np.abs(np.fft.rfft(vel_data))
        freqs = np.fft.rfftfreq(len(acc_data), d=dt)
    else:
        acc_fft = vel_fft = freqs = []

    # Clear and redraw
    ax_acc_time.clear()
    ax_acc_time.plot(time_data, acc_data)
    ax_acc_time.set_title("Acceleration vs Time")

    ax_acc_freq.clear()
    ax_acc_freq.plot(freqs, acc_fft)
    ax_acc_freq.set_title("Acceleration Spectrum")

    ax_vel_time.clear()
    ax_vel_time.plot(time_data, vel_data)
    ax_vel_time.set_title("Velocity vs Time")

    ax_vel_freq.clear()
    ax_vel_freq.plot(freqs, vel_fft)
    ax_vel_freq.set_title("Velocity Spectrum")

    canvas.draw()
    
    
def start_acceleration_stream(app):
    """Subscribe to acceleration data from sensor."""
    asyncio.run_coroutine_threadsafe(
        app.client.start_notify(DATA_UUID, app.handle_acceleration),
        app.loop
    )


def handle_acceleration(app, sender, data: bytearray):
    """Callback when acceleration data arrives."""
    # Example: assume data is 3x int16 values (X, Y, Z) in little endian
    x = int.from_bytes(data[0:2], byteorder="little", signed=True)
    y = int.from_bytes(data[2:4], byteorder="little", signed=True)
    z = int.from_bytes(data[4:6], byteorder="little", signed=True)

    # Pick one axis (or magnitude)
    acc_value = (x**2 + y**2 + z**2)**0.5  # magnitude in raw units

    # Keep data buffers small
    if len(app.time_data) > 200:
        app.time_data.pop(0)
        app.acc_data.pop(0)
        app.vel_data.pop(0)

    t = app.time_data[-1] + 0.02 if app.time_data else 0
    vel_value = (app.vel_data[-1] + acc_value*0.02) if app.vel_data else 0

    app.time_data.append(t)
    app.acc_data.append(acc_value)
    app.vel_data.append(vel_value)
