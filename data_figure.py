import struct

from utils.sensor_map import UUID_DATA

data_uuid, data_size = UUID_DATA["data"]
calb_uuid, calb_size = UUID_DATA["calibration"]


def update_plot(self, g_values):
    # g_values is a list of 8 points
    for val in g_values:
        self.x_data.append(len(self.x_data))
        self.y_data[0].append(val)  # if plotting 1 axis
    self.ax.clear()
    self.ax.plot(self.x_data, self.y_data[0])
    self.canvas.draw()


def parse_data_packet(raw_bytes, scale_factor=1.0):
    # Expecting exactly 16 bytes → 8 samples
    samples = struct.unpack("<8H", raw_bytes)  # unsigned short, little endian
    # Convert to signed range and scale to g
    g_values = [ (s - 0x8000) * scale_factor for s in samples ]
    return g_values


async def read_scale_factor(self):
    raw_bytes = await self.client.read_gatt_char(calb_uuid)
    # Example: single float, little endian
    scale_factor, = struct.unpack("<f", raw_bytes)
    return scale_factor


async def start_stream(self):
    self.scale_factor = await self.read_scale_factor()
    await self.client.start_notify(data_uuid, self.notification_handler)

def notification_handler(self, sender, data):
    g_values = parse_data_packet(data, self.scale_factor)
    # Update your plot with the new g_values
    self.update_plot(g_values)
