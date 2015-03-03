from spinnman.messages.eieio.eieio_header import EIEIOHeader
from spinnman.messages.eieio.eieio_message import EIEIOMessage
from spinnman.messages.eieio.eieio_type_param import EIEIOTypeParam
from spinnman.connections.udp_packet_connections.reverse_iptag_connection\
    import ReverseIPTagConnection

from spynnaker.pyNN.utilities.conf import config
import time

use_prefix = False

udp_connection = ReverseIPTagConnection(
    remote_host=config.get("Machine", "machineName"), remote_port=12345)

if not use_prefix:
    base_key = 0x70800
    for key in range(base_key, base_key + 100, 20):
        header = EIEIOHeader(type_param=EIEIOTypeParam.KEY_32_BIT)
        message = EIEIOMessage(eieio_header=header, data=bytearray())
        message.write_data(key)
        print "Sending key", hex(key)
        udp_connection.send_eieio_message(message)
        time.sleep(1.0)
else:
    for key in range(0, 100, 20):
        header = EIEIOHeader(type_param=EIEIOTypeParam.KEY_16_BIT)
        message = EIEIOMessage(eieio_header=header, data=bytearray())
        message.write_data(key)
        print "Sending key", hex(key)
        udp_connection.send_eieio_message(message)
        time.sleep(1.0)
