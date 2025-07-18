import asyncio
from bleak import BleakClient, BleakScanner

ADDRESS = "D5:D0:F9:30:83:D7"  # Your BLE device MAC address

NOTIFY_CHARACTERISTIC_UUID = "1c930020-d459-11e7-9296-b8e856369374"
WRITE_CHARACTERISTIC_UUID = "1c930030-d459-11e7-9296-b8e856369374"


def handle_notification(sender, data):
    print(f"Notification from {sender}: {data.hex()}")

async def main():
    print("Scanning for devices...")
    devices = await BleakScanner.discover()
    device = next((d for d in devices if d.address == ADDRESS), None)
    if not device:
        print(f"Device {ADDRESS} not found.")
        return
    
    print(f"Connecting to {device.address}")

    async with BleakClient(device.address) as client:
        print("Connected.")   # means context manager successfully connected

        await client.connect()
    
        svcs = client.services  # no await here, it's a property
        for service in svcs:
            print(f"Service: {service.uuid}")
            for char in service.characteristics:
                props = ",".join(char.properties)
                print(f"  Characteristic: {char.uuid} - Properties: {props}")

        
        # Enable notifications
        await client.start_notify(NOTIFY_CHARACTERISTIC_UUID, handle_notification)
        print("Notifications started.")

        await asyncio.sleep(1)  # small delay to ensure CCCD is properly configured

        # Write to request data
        await client.write_gatt_char(WRITE_CHARACTERISTIC_UUID, bytearray([0x01]))
        print("Write done. Waiting for notifications...")

        # Wait to receive data
        await asyncio.sleep(10)

        await client.stop_notify(NOTIFY_CHARACTERISTIC_UUID)
        print("Notifications stopped.")

    print("Disconnected cleanly.")

asyncio.run(main())
