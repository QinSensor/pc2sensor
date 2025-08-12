import asyncio
from editor import commit_changes


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