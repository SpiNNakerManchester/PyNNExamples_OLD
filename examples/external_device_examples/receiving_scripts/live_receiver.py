from spinnman.connections.udp_packet_connections.stripped_iptag_connection \
    import StrippedIPTagConnection
from spinnman import constants
from spynnaker.pyNN.utilities.conf import config
import time


def packet_callback(packet):
    print(packet)

packet_grabber = \
    StrippedIPTagConnection(local_port=config.get("Recording",
                                                  "live_spike_port"))
packet_grabber.register_callback(packet_callback,
                                 constants.TRAFFIC_TYPE.EIEIO_DATA)

#sleep for the length of the simulation

time.sleep(10000)
