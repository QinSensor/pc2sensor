import asyncio
from bleak import BleakClient, BleakScanner, BleakError

ADDRESS = "D5:D0:F9:30:83:D7"
NOTIFY_CHARACTERISTIC_UUID = "1c930020-d459-11e7-9296-b8e856369374"
WRITE_CHARACTERISTIC_UUID = "1c930030-d459-11e7-9296-b8e856369374"

def handle_notification(sender, data):
    print(f"Notification from {sender}: {data.hex()}")

async def connect_and_listen():
    first_connection = True

    while True:
        print("Scanning for device...")
        devices = await BleakScanner.discover()
        device = next((d for d in devices if d.address == ADDRESS), None)
        if not device:
            print(f"Device {ADDRESS} not found. Retrying in 20 seconds...")
            await asyncio.sleep(5)
            continue

        print(f"Connecting to {device.address}")
        try:
            async with BleakClient(device.address) as client:
                print("Connected.")

                # Optionally, list services
                if first_connection:
                    svcs = client.services
                    for service in svcs:
                        print(f"Service: {service.uuid}")
                        for char in service.characteristics:
                            props = ",".join(char.properties)
                            print(f"  Characteristic: {char.uuid} - Properties: {props}")
                    first_connection = False

                # Start notifications
                await client.start_notify(NOTIFY_CHARACTERISTIC_UUID, handle_notification)
                print("Notifications started.")

                # Write request to device (optional)
                await asyncio.sleep(1)
                await client.write_gatt_char(WRITE_CHARACTERISTIC_UUID, bytearray([0x01]))
                print("Write done. Listening for notifications...")

                # Keep running until disconnected
                while client.is_connected:
                    await asyncio.sleep(1)

                print("Device disconnected. Will try to reconnect.")

        except BleakError as e:
            print(f"BLE error: {e}. Retrying in 5 seconds...")

        except Exception as e:
            print(f"Unexpected error: {e}. Retrying in 5 seconds...")

        # Wait before retrying
        await asyncio.sleep(5)

async def main():
    await connect_and_listen()

asyncio.run(main())
