import math
import numpy
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import socket
import spynnaker.pyNN as p
import spynnaker_external_devices_plugin.pyNN as q

# How regularily to display frames
FRAME_TIME_MS = 33

# Resolution to start retina with
RESOLUTION = q.PushBotRetinaResolution.Downsample32

# Time constant of pixel decay
DECAY_TIME_CONSTANT_MS = 100

# Value of brightest pixel to show
DISPLAY_MAX = 33.0

# Setup
p.setup(timestep=1.0)

# Pushbot Retina - Down Polarity
retina_pop = p.Population(None, q.PushBotRetinaDevice, {
    "spinnaker_link_id": 0,
    "virtual_chip_x": 5,
    "virtual_chip_y": 0,
    "polarity": q.PushBotRetinaPolarity.Merged,
    "resolution": RESOLUTION})


# Activate live retina output
q.activate_live_output_for(retina_pop, host="0.0.0.0", port=17893)


# Take a flat numpy array of image data and convert it into a square
def get_square_image_data_view(image_data):
    image_data_view = image_data.view()
    image_data_view.shape = (RESOLUTION.value.pixels, RESOLUTION.value.pixels)
    return image_data_view

# Create image plot of retina output
fig = plt.figure()
image_data = numpy.zeros(RESOLUTION.value.pixels ** 2)
image = plt.imshow(get_square_image_data_view(image_data),
                   interpolation="nearest", cmap="jet",
                   vmin=0.0, vmax=DISPLAY_MAX)

# Open socket to receive datagrams
spike_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
spike_socket.bind(("0.0.0.0", 17893))
spike_socket.setblocking(False)

# Determine mask for coordinates
coordinate_mask = (1 << (2 * RESOLUTION.value.coordinate_bits)) - 1

# Calculate delay proportion each frame
decay_proportion = math.exp(-float(FRAME_TIME_MS) /
                            float(DECAY_TIME_CONSTANT_MS))


def updatefig(frame):
    global image_data, image, spike_socket, decay_proportion, coordinate_mask

    # Read all datagrams received during last frame
    while True:
        try:
            raw_data = spike_socket.recv(512)
        except socket.error:
            # If error isn't just a non-blocking read fail, print it
            # if e != "[Errno 11] Resource temporarily unavailable":
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
ani = animation.FuncAnimation(fig, updatefig, interval=FRAME_TIME_MS,
                              blit=True)

# Run infinite simulation (non-blocking)
p.run(None)

# Show animated plot (blocking)
plt.show()

# End simulation
p.end()
