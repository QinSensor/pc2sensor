# reconnect in every 20 seconds
import struct
import asyncio
from bleak import BleakClient, BleakScanner, BleakError
#
# ADDRESS = "D5:D0:F9:30:83:D7"     # 1 axis
ADDRESS = "FA:E2:AD:E2:8D:99"   # 3 axis 40
# ADDRESS = "FB:0C:16:50:98:DB"       # 3 axis 39
DATA_UUID = "1c930020-d459-11e7-9296-b8e856369374"
GAIN_UUID = "1c930022-d459-11e7-9296-b8e856369374"
SAMPLE_RATE_UUID = "1c930023-d459-11e7-9296-b8e856369374"

CALIBRATION_UUID = "1c930029-d459-11e7-9296-b8e856369374"

conversion_factor = 1.0

def decode_g(data):
    samples = struct.unpack('<' + 'H' * (len(data) // 2), data)
    # Convert to signed: 0g is 0x8000, scale using formula
    accel_g = [(sample - 32768) * conversion_factor for sample in samples]
    return accel_g

# Example 'handle_notification' function:
def handle_notification(sender, data):
    values_g = decode_g(data)
    print(f"Notification from {sender}: {values_g}")

async def connect_and_listen():
    global conversion_factor

    while True:
        print("Scanning for device...")
        devices = await BleakScanner.discover(timeout=30.0)
        device = next((d for d in devices if d.address == ADDRESS), None)
        if not device:
            print(f"Device {ADDRESS} not found. Retrying in 20 seconds...")
            await asyncio.sleep(20)
            continue

        print(f"Connecting to {device.address}")
        try:
            async with BleakClient(device.address) as client:
                print("Connected.")

                # Read gain value
                try:
                    gain_bytes = await client.read_gatt_char(GAIN_UUID)
                    gain = int.from_bytes(gain_bytes, byteorder='little')
                    print(f"Gain: {gain} (raw bytes: {gain_bytes.hex()})")
                except Exception as e:
                    print(f"Failed to read Gain characteristic: {e}")

                # Read calibration value
                try:
                    cal_bytes = await client.read_gatt_char(CALIBRATION_UUID)
                    calibration = int.from_bytes(cal_bytes, byteorder='little')
                    conversion_factor = 3.81 / calibration
                    print(f"Calibration: {calibration} (raw bytes: {cal_bytes.hex()})")
                except Exception as e:
                    print(f"Failed to read Calibration characteristic: {e}")

                # Start notifications
                await client.start_notify(DATA_UUID, handle_notification)
                print("Notifications started.")

                # Write request to device (optional)
                await asyncio.sleep(1)
                # await client.write_gatt_char(SAMPLE_RATE_UUID, bytearray([0x01]))
                # print("Write done. Listening for notifications...")

                try:
                    before_bytes = await client.read_gatt_char(SAMPLE_RATE_UUID)
                    before_rate = int.from_bytes(before_bytes, byteorder='little')
                    print(f"Sample rate before write: {before_rate} (raw bytes: {before_bytes.hex()})")

                    new_rate = 0x01
                    await client.write_gatt_char(SAMPLE_RATE_UUID, bytearray([new_rate]))
                    print(f"Sample rate write done (wrote {new_rate}).")

                    after_bytes = await client.read_gatt_char(SAMPLE_RATE_UUID)
                    after_rate = int.from_bytes(after_bytes, byteorder='little')
                    print(f"Sample rate after write: {after_rate} (raw bytes: {after_bytes.hex()})")
                except Exception as e:
                    print(f"Sample rate read/write error: {e}")

                # Keep running until disconnected
                while client.is_connected:
                    await asyncio.sleep(1)

                print("Device disconnected. Will try to reconnect.")

        except BleakError as e:
            print(f"BLE error: {e}. Retrying in 5 seconds...")

        except Exception as e:
            print(f"Unexpected error: {e}. Retrying in 5 seconds...")

        # Wait before retrying
        await asyncio.sleep(15)

async def main():
    await connect_and_listen()

asyncio.run(main())
