import asyncio
from bleak import BleakClient, BleakScanner

SENSOR_ADDRESSES = [
    "FA:E2:AD:E2:8D:99",  # 3 axis, 40---get data
    "FB:0C:16:50:98:DB",  # 3 axis, 39
    "D5:D0:F9:30:83:D7",  # 1 axis
]
NOTIFY_CHARACTERISTIC_UUID = "1c930020-d459-11e7-9296-b8e856369374"
WRITE_CHARACTERISTIC_UUID  = "1c930023-d459-11e7-9296-b8e856369374"

async def sensor_session(address):
    received = []
    def handle_notification(sender, data):
        print(f"[{address}] Notification from {sender}: {data.hex()}")
        received.append(data)

    print(f"[{address}] Scanning for device...")
    devices = await BleakScanner.discover(timeout=50.0)     # default is 5 seconds
    device = next((d for d in devices if d.address == address), None)
    if not device:
        print(f"[{address}] Device not found.")
        return

    print(f"[{address}] Connecting...")
    async with BleakClient(device.address) as client:
        print(f"[{address}] Connected.")

        print(f"[{address}] Discovering services ...")
        for service in client.services:
            print(f"[{address}] Service: {service.uuid}")
            for char in service.characteristics:
                print(f"   Characteristic: {char.uuid}  Properties: {char.properties}")

        await client.start_notify(NOTIFY_CHARACTERISTIC_UUID, handle_notification)
        print(f"[{address}] Notifications started.")

        await asyncio.sleep(1)  # Wait for notification setup

        await client.write_gatt_char(WRITE_CHARACTERISTIC_UUID, bytearray([0x01]))
        print(f"[{address}] Write done. Listening for notifications...")

        await asyncio.sleep(10)  # Listen for notifications

        await client.stop_notify(NOTIFY_CHARACTERISTIC_UUID)
        print(f"[{address}] Notifications stopped.")

    print(f"[{address}] Disconnected cleanly.")

    # Print all received notifications
    print(f"\n[{address}] All notifications received:")
    for idx, data in enumerate(received):
        print(f"{idx + 1}: {data.hex()}")

async def main():
    for address in SENSOR_ADDRESSES:
        await sensor_session(address)  # process one sensor at a time

if __name__ == "__main__":
    asyncio.run(main())
