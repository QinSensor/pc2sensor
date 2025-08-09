import struct
import asyncio
from bleak import BleakClient, BleakScanner, BleakError

# address = "D5:D0:F9:30:83:D7"     # 1 axis
address = "FA:E2:AD:E2:8D:99"   # 3 axis 40
# address = "FB:0C:16:50:98:DB"       # 3 axis 39

# UUIDs
DATA_UUID = "1c930020-d459-11e7-9296-b8e856369374"
GAIN_UUID = "1c930022-d459-11e7-9296-b8e856369374"
SAMPLE_RATE_UUID = "1c930023-d459-11e7-9296-b8e856369374"
CALIBRATION_UUID = "1c930029-d459-11e7-9296-b8e856369374"

conversion_factor = 1.0  # fallback default


def decode_g(data):
    """Decode raw 16-bit unsigned data into signed G values using conversion_factor."""
    try:
        samples = struct.unpack('<' + 'H' * (len(data) // 2), data)
        return [(sample - 32768) * conversion_factor for sample in samples]
    except Exception as e:
        print("Error decoding data:", e)
        return []


def handle_notification(sender, data):
    values_g = decode_g(data)
    formatted = ", ".join(f"{v:.2f}" for v in values_g)
    print(f"Notification from {sender} ({len(values_g)} values):")
    for i in range(0, len(values_g), 10):
        print("   " + ", ".join(f"{v:.2f}" for v in values_g[i:i+10]))


async def connect_and_listen(address):
    global conversion_factor
    client = None

    try:
        print(f"Connecting to {address}")
        client = BleakClient(address)
        await client.connect()
        print("Connected!")

        # Read gain
        try:
            gain_bytes = await client.read_gatt_char(GAIN_UUID)
            gain = int.from_bytes(gain_bytes, byteorder='little')
            print(f"Gain: {gain} (bytes: {gain_bytes.hex()})")
        except Exception as e:
            print(f"Error reading GAIN: {e}")

        # Read calibration
        try:
            cal_bytes = await client.read_gatt_char(CALIBRATION_UUID)
            calibration = int.from_bytes(cal_bytes, byteorder='little')
            conversion_factor = 3.81 / calibration
            print(f"Calibration: {calibration}, Conversion Factor: {conversion_factor:.6f}")
        except Exception as e:
            print(f"Error reading CALIBRATION: {e}")
            conversion_factor = 1.0  # fallback

        # Start notifications
        await client.start_notify(DATA_UUID, handle_notification)
        print("Started notifications.")

        # Write sample rate
        await client.write_gatt_char(SAMPLE_RATE_UUID, bytearray([0x01]))
        print("Sample rate written.")

        # Keep alive while connected
        while client.is_connected:
            await asyncio.sleep(1)

    except Exception as e:
        print("BLE error:", e)

    finally:
        if client and client.is_connected:
            await client.disconnect()
            print("Disconnected.")


async def main():
    await connect_and_listen(address)

if __name__ == "__main__":
    asyncio.run(main())
