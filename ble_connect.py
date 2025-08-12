
# def connect_sensor(self):
#     # Delegate to parent
#     self.parent.connect_device(self.address)
#     self.conn_status.set("Connected")
#     self.update_button_states()
#
#
# def disconnect_sensor(self):
#     # Delegate to parent
#
#     self.parent.disconnect_device(self.address)
#     self.conn_status.set("Disconnected")
#     self.update_button_states()

def connect_sensor(app):
    app.parent.connect_device(app.address)
    app.conn_status.set("Connected")
    app.update_button_states()

def disconnect_sensor(app):
    app.parent.disconnect_device(app.address)
    app.conn_status.set("Disconnected")
    app.update_button_states()