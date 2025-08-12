import asyncio

from bleak import BleakClient, BleakScanner


async def commit_changes(app, client):
    print('11')
    client = await ensure_fresh_connection(app, client)
    print('12')
    COMMIT_UUID = "1c930030-d459-11e7-9296-b8e856369374"
    data = bytes([0x01])

    app.commit_status_label.after(0, lambda:
        app.commit_status_label.config(text="Committing...", fg="green"))
    await asyncio.sleep(0)  # let UI refresh before blocking
    print('13')

    try:
        await asyncio.wait_for(client.write_gatt_char(COMMIT_UUID, data), timeout=5)
        print("Commit successful")
    except asyncio.TimeoutError:
        print(f"Write to {COMMIT_UUID} timed out — assuming disconnect.")
        client = await ensure_fresh_connection(app, client)
        try:
            await asyncio.wait_for(client.write_gatt_char(COMMIT_UUID, data), timeout=5)
            print("Commit successful after reconnect")
        except Exception as e:
            print("Commit failed after reconnect:", e)
            raise e
    except Exception as e:
        print("Commit failed:", e)
        raise e

    return client


def on_commit_button_click(app):
    print('1')
    app.commit_status_label.after(0, lambda:
        app.commit_status_label.config(text="Committing...", fg="green"))

    future = asyncio.run_coroutine_threadsafe(commit_changes(app, app.client), app.loop)
    future.add_done_callback(lambda fut: _on_commit_done(app, fut))


def _on_commit_done(app, future):
    try:
        new_client = future.result()
        app.client = new_client
        app.commit_status_label.after(0, lambda:
            app.commit_status_label.config(text="Commit successful ✅", fg="green"))
    except Exception as ee:
        app.commit_status_label.after(0, lambda:
            app.commit_status_label.config(text=f"Commit failed ❌: {ee}", fg="red"))
    finally:
        app.commit_status_label.after(3000, lambda: app.commit_status_label.config(text=""))


async def ensure_fresh_connection(app, client):
    if not client or not client.is_connected:
        address = client.address if client else None
        app.commit_status_label.config(text=f"Reconnecting...", fg="red")
        print(f"Not Connected to {address}! Trying to reconnect...")

        # Scan for device first
        devices = await BleakScanner.discover(timeout=5.0)
        found = any(d.address == address for d in devices)

        if not found:
            app.commit_status_label.config(text=f"Sensor Not Found", fg="red")
            raise Exception(f"Device with address {address} was not found during scan.")

        if client:
            try:
                await client.disconnect()
            except Exception:
                pass

        client = BleakClient(address)
        try:
            await client.connect()
            app.commit_status_label.config(text=f"Reconnected", fg="green")
            print(f"Reconnected successfully to {address}.")
        except Exception as e:
            app.commit_status_label.config(text=f"Sensor Not Found", fg="red")
            raise Exception(f"Device {address} not connected and reconnection failed.") from e

    return client

# async def ensure_fresh_connection(self, client):
#     if not client or not client.is_connected:
#         address = client.address if client else None
#         self.commit_status_label.config(text=f"Reconnecting...", fg="red")
#         print(f"Not Connected to {address}! Trying to reconnect...")
#
#         # Scan for device first
#         devices = await BleakScanner.discover(timeout=5.0)
#         found = any(d.address == address for d in devices)
#
#         if not found:
#             self.commit_status_label.config(text=f"Sensor Not Found", fg="red")
#             raise Exception(f"Device with address {address} was not found during scan.")
#
#         if client:
#             try:
#                 await client.disconnect()
#             except Exception:
#                 pass
#
#         client = BleakClient(address)
#         try:
#             await client.connect()
#             self.commit_status_label.config(text=f"Reconnected", fg="green")
#             print(f"Reconnected successfully to {address}.")
#         except Exception as e:
#             self.commit_status_label.config(text=f"Sensor Not Found", fg="red")
#             raise Exception(f"Device {address} not connected and reconnection failed.") from e
#
#     return client

#
# def on_commit_button_click(self):
#     # try:
#     print('1')
#     self.commit_status_label.after(0, lambda:
#     self.commit_status_label.config(text="Commiting...", fg="green"))
#     # self.commit_status_label.update_idletasks()  # forces immediate redraw
#
#     future = asyncio.run_coroutine_threadsafe(commit_changes(self, self.client), self.loop)
#     future.add_done_callback(lambda fut: self._on_commit_done(fut))
#
#
# def _on_commit_done(self, future):
#     try:
#         new_client = future.result()
#         self.client = new_client
#         self.commit_status_label.after(0, lambda:
#         self.commit_status_label.config(text="Commit successful ✅", fg="green"))
#     except Exception as ee:
#         self.commit_status_label.after(0, lambda:
#         self.commit_status_label.config(text=f"Commit failed ❌: {ee}", fg="red"))
#     finally:
#         self.commit_status_label.after(3000, lambda: self.commit_status_label.config(text=""))
#
#
# async def commit_changes(self, client):
#     print('11')
#     client =await ensure_fresh_connection(self, client)
#     print('12')
#     COMMIT_UUID = "1c930030-d459-11e7-9296-b8e856369374"
#     data = bytes([0x01])
#
#     self.commit_status_label.after(0, lambda:
#         self.commit_status_label.config(text="Committing...", fg="green"))
#     await asyncio.sleep(0)  # let UI refresh before we block
#     # self.commit_status_label.after(0, lambda:
#     # self.commit_status_label.config(text="Commit successful ✅", fg="green"))
#     # self.commit_status_label.config(text=f"Committing...", fg="green")
#     print('13')
#
#     try:
#         await asyncio.wait_for(client.write_gatt_char(COMMIT_UUID, data), timeout=5)
#         # await client.write_gatt_char(COMMIT_UUID, data)
#         # self.commit_status_label.config(text=f"Commit successful", fg="green")
#         print("Commit successful")
#     except asyncio.TimeoutError:
#         print(f"Write to {COMMIT_UUID} timed out — assuming disconnect.")
#         # self.commit_status_label.config(text=f"Reconnecting...", fg="red")
#         client = await ensure_fresh_connection(self, client)
#         try:
#             await asyncio.wait_for(client.write_gatt_char(COMMIT_UUID, data), timeout=5)
#             # self.commit_status_label.config(text="Commit successful ✅", fg="green")
#             print("Commit successful after reconnect")
#         except Exception as e:
#             # self.commit_status_label.config(text="Commit failed ❌", fg="red")
#             print("Commit failed after reconnect:", e)
#             raise e
#     except Exception as e:
#         # self.commit_status_label.config(text=f"Commit failed", fg="red")
#         print("Commit failed:", e)
#         raise e
#
#     return client
#
#
