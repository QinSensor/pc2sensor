import asyncio

from bleak import BleakClient, BleakScanner


async def commit_changes(app, client, address, scan_instance):
    COMMIT_UUID = "1c930030-d459-11e7-9296-b8e856369374"
    data = bytes([0x01])

    print("Starting commit...")
    client = await ensure_fresh_connection(app, client, address)
    print("Connected to sensor")

    app.commit_status_label.after(0, lambda:
        app.commit_status_label.config(text="Committing...", fg="green"))
    await asyncio.sleep(0)  # let UI refresh before blocking
    print('label for Committing...')

    try:
        await asyncio.wait_for(client.write_gatt_char(COMMIT_UUID, data), timeout=5)
        print("Commit successful")
        await scan_instance.on_sensor_commit(address)
    except asyncio.TimeoutError:
        print(f"Write to {COMMIT_UUID} timed out — assuming disconnect.")
        client = await ensure_fresh_connection(app, client, address)
        try:
            await asyncio.wait_for(client.write_gatt_char(COMMIT_UUID, data), timeout=5)
            print("Commit successful after reconnect")
            await scan_instance.on_sensor_commit(address)
        except Exception as e:
            print("Commit failed after reconnect:", e)
            raise e
    except Exception as e:
        print("Commit failed:", e)
        raise e

    print("After commit changes, the client: ", client, "Connected: ", client.is_connected)

    return client


def on_commit_button_click(app, address, scan_instance):
    print('Begin commit')
    app.commit_status_label.after(0, lambda:
        app.commit_status_label.config(text="Committing...", fg="green"))

    future = asyncio.run_coroutine_threadsafe(commit_changes(app, app.client, address, scan_instance), app.loop)
    future.add_done_callback(lambda fut: _on_commit_done(app, fut))


def _on_commit_done(app, future):
    try:
        new_client = future.result()
        app.client = new_client
        app.commit_status_label.after(0, lambda:
            app.commit_status_label.config(text="Commit successful ✅, to Disconnect", fg="green"))
    except Exception as ee:
        app.commit_status_label.after(0, lambda ee=ee:
        app.commit_status_label.config(text=f"Commit failed ❌: {ee}", fg="red"))

    finally:
        app.commit_status_label.after(3000, lambda: app.commit_status_label.config(text=""))


async def ensure_fresh_connection(app, client, address):
    if not client or not client.is_connected:
        app.commit_status_label.config(text=f"Reconnecting...", fg="red")  # OK
        print(f"Not Connected to {address}! Trying to reconnect...")

        # Scan for device first
        devices = await BleakScanner.discover(timeout=20.0)
        found = any(d.address == address for d in devices)
        print("Finding devices matching Address...")
        if not found:
            app.commit_status_label.config(text=f"Sensor Not Found", fg="red")
            raise Exception(f"Device with address {address} was not found during scan.")
        else:
            print("Found Device with address {address}.")

        if client:
            try:
                await client.disconnect()
            except Exception:
                pass
            print("old client disconnected")
        client = BleakClient(address)
        try:
            print("Created New client")
            await client.connect()
            app.commit_status_label.config(text=f"Reconnected", fg="green")
            print(f"Reconnected successfully to {address}.")
        except Exception as e:
            print("Fail in Reconnection")
            app.commit_status_label.config(text=f"Sensor Not Found", fg="red")
            raise Exception(f"Device {address} not connected and reconnection failed.") from e

    return client

