import asyncio

from utils.sensor_map import UUID_DATA

TEMP_UUID, _ = UUID_DATA["temp"]
BATTERY_UUID, _ = UUID_DATA["battery"]
TIME_UUID, _ = UUID_DATA["time"]


def update_temp_time(app):
    asyncio.run_coroutine_threadsafe(
        async_update_sensor_readings(app.client, app.temp_var, app.battery_var, app.time_var),
        app.loop
    )
    app.root.after(200000, lambda: update_temp_time(app))


async def async_update_sensor_readings(client, temp_var, battery_var, time_var):
    """Read temperature and battery from BLE and update Tkinter StringVars."""
    temp_raw = await read_int_value(client, TEMP_UUID)
    batt_raw = await read_int_value(client, BATTERY_UUID)
    time_raw = await read_byte_value(client, TIME_UUID)
    print(time_raw)
    if temp_raw is not None:
        temp_var.set(f"Temp: {temp_raw / 256.0:.2f} °C")
    if batt_raw is not None:
        battery_var.set(f"Battery: {batt_raw/1000.0}V")
    if time_raw is not None:
        hour = time_raw[0]
        minute = time_raw[1]
        second = time_raw[2]
        time_var.set(f"BluVib Time Series Date at : {hour:02d}:{minute:02d}:{second:02d}")


async def read_int_value(client, uuid):
    """Read a BLE characteristic and return integer value."""
    try:
        data = await client.read_gatt_char(uuid)
        return int.from_bytes(data, byteorder="little", signed=True)
    except Exception as e:
        print(f"Error reading {uuid}: {e}")
        return None


async def read_byte_value(client, uuid):
    """Read a BLE characteristic and return raw bytes."""
    try:
        data = await client.read_gatt_char(uuid)
        return data  # Return raw bytes as-is
    except Exception as e:
        print(f"Error reading {uuid}: {e}")
        return None