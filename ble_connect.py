def connect_sensor(self):
    # Delegate to parent
    self.parent.connect_device(self.address)
    self.conn_status.set("Connected")
    self.update_button_states()


def disconnect_sensor(self):
    # Delegate to parent

    self.parent.disconnect_device(self.address)
    self.conn_status.set("Disconnected")
    self.update_button_states()