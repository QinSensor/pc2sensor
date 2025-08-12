import asyncio
from editor import ensure_fresh_connection


def on_commit_button_click(self):
    # try:
    print('1')
    self.commit_status_label.after(0, lambda:
    self.commit_status_label.config(text="Commiting...", fg="green"))
    # self.commit_status_label.update_idletasks()  # forces immediate redraw

    future = asyncio.run_coroutine_threadsafe(commit_changes(self, self.client), self.loop)
    future.add_done_callback(lambda fut: self._on_commit_done(fut))


def update_button_states(self):
    """Enable/disable connect/disconnect buttons based on current status."""
    status = self.conn_status.get().lower()
    if status == "connected":
        self.connect_btn["state"] = "disabled"
        self.disconnect_btn["state"] = "normal"
    else:
        self.connect_btn["state"] = "normal"
        self.disconnect_btn["state"] = "disabled"


def _on_commit_done(self, future):
    try:
        new_client = future.result()
        self.client = new_client
        self.commit_status_label.after(0, lambda:
        self.commit_status_label.config(text="Commit successful ✅", fg="green"))
    except Exception as ee:
        self.commit_status_label.after(0, lambda:
        self.commit_status_label.config(text=f"Commit failed ❌: {ee}", fg="red"))
    finally:
        self.commit_status_label.after(3000, lambda: self.commit_status_label.config(text=""))


async def commit_changes(self, client):
    print('11')
    client =await ensure_fresh_connection(self, client)
    print('12')
    COMMIT_UUID = "1c930030-d459-11e7-9296-b8e856369374"
    data = bytes([0x01])

    self.commit_status_label.after(0, lambda:
        self.commit_status_label.config(text="Committing...", fg="green"))
    await asyncio.sleep(0)  # let UI refresh before we block
    # self.commit_status_label.after(0, lambda:
    # self.commit_status_label.config(text="Commit successful ✅", fg="green"))
    # self.commit_status_label.config(text=f"Committing...", fg="green")
    print('13')

    try:
        await asyncio.wait_for(client.write_gatt_char(COMMIT_UUID, data), timeout=5)
        # await client.write_gatt_char(COMMIT_UUID, data)
        # self.commit_status_label.config(text=f"Commit successful", fg="green")
        print("Commit successful")
    except asyncio.TimeoutError:
        print(f"Write to {COMMIT_UUID} timed out — assuming disconnect.")
        # self.commit_status_label.config(text=f"Reconnecting...", fg="red")
        client = await ensure_fresh_connection(self, client)
        try:
            await asyncio.wait_for(client.write_gatt_char(COMMIT_UUID, data), timeout=5)
            # self.commit_status_label.config(text="Commit successful ✅", fg="green")
            print("Commit successful after reconnect")
        except Exception as e:
            # self.commit_status_label.config(text="Commit failed ❌", fg="red")
            print("Commit failed after reconnect:", e)
            raise e
    except Exception as e:
        # self.commit_status_label.config(text=f"Commit failed", fg="red")
        print("Commit failed:", e)
        raise e

    return client


