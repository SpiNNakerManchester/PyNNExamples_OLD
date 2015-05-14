import math
import numpy
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import socket
import spynnaker.pyNN as p
import spynnaker_external_devices_plugin.pyNN as q
from spynnaker_external_devices_plugin.pyNN.connections\
    .spynnaker_live_spikes_connection import SpynnakerLiveSpikesConnection

FRAME_TIME_MS = 33
RESOLUTION = 32
DECAY_TIME_CONSTANT_MS = 644

# Setup
p.setup(timestep=1.0)

# Pushbot Retina - Down Polarity
retina_pop = p.Population(None, q.PushBotRetinaDevice, {
    "connected_to_real_chip_x": 0,
    "connected_to_real_chip_y": 0,
    "connected_to_real_chip_link_id": 4,
    "virtual_chip_x": 5,
    "virtual_chip_y": 0,
    "polarity": q.PushBotRetinaPolarity.Merged,
    "resolution": q.PushBotRetinaResolution.Downsample32})


# Activate live retina output
q.activate_live_output_for(retina_pop, host="0.0.0.0", port=17893)

# Take a flat numpy array of image data and convert it into a square
def get_square_image_data_view(image_data):
    image_data_view = image_data.view()
    image_data_view.shape = (RESOLUTION, RESOLUTION)
    return image_data_view

# Create image plot of retina output
fig = plt.figure()
image_data = numpy.zeros(RESOLUTION * RESOLUTION)
image = plt.imshow(get_square_image_data_view(image_data), interpolation="nearest", cmap="jet", vmin=0.0, vmax=float(FRAME_TIME_MS))

# Open socket to receive datagrams
spike_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
spike_socket.bind(("0.0.0.0", 17893))
spike_socket.setblocking(False)

# Determine mask for coordinates
coordinate_bits = int(math.log(RESOLUTION, 2))
coordinate_mask = (1 << (2 * coordinate_bits)) - 1

# Calculate delay proportion each frame
decay_proportion = math.exp(-float(FRAME_TIME_MS) / float(DECAY_TIME_CONSTANT_MS))

def updatefig(frame):
    global image_data, image, spike_socket, decay_proportion, coordinate_mask
    
    # Read all datagrams received during last frame
    while True:
        try:
            raw_data = spike_socket.recv(512)
        except socket.error, e:
            # If error isn't just a non-blocking read fail, print it
            #if e != "[Errno 11] Resource temporarily unavailable":
            #    print "Error '%s'" % e
            
            # Stop reading datagrams
            break
        else:
            # Slice off eieio header and convert to numpy array of uint32
            payload = numpy.fromstring(raw_data[2:], dtype="uint32")
            
            # Mask out x, y coordinates
            payload &= coordinate_mask
            
            # Increment these pixels
            image_data[payload] += 1.0
            
    # Decay image data
    image_data *= decay_proportion
    
    # Set image data
    image.set_array(get_square_image_data_view(image_data))
    return [image]

# Play animation
ani = animation.FuncAnimation(fig, updatefig, interval=FRAME_TIME_MS, blit=True)

p.run(None)
plt.show()
p.end()
