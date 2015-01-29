from spinnman.messages.eieio.eieio_header import EIEIOHeader
from spinnman.messages.eieio.eieio_message import EIEIOMessage
from spinnman.messages.eieio.eieio_type_param import EIEIOTypeParam
from spinnman.messages.eieio.eieio_prefix_type import EIEIOPrefixType
from spinnman.connections.udp_packet_connections.reverse_iptag_connection\
    import ReverseIPTagConnection

from spynnaker.pyNN.utilities.conf import config

udp_connection = \
    ReverseIPTagConnection(remote_host=config.get("Machine", "machineName"),
                           remote_port=12345)

key = 0x70800
#key = 0x800
payload = 1

header = EIEIOHeader(type_param=EIEIOTypeParam.KEY_32_BIT)
message = EIEIOMessage(eieio_header=header, data=bytearray())
message.write_data(key)
udp_connection.send_eieio_message(message)
key += 1

'''
header = EIEIOHeader(type_param=EIEIOTypeParam.KEY_PAYLOAD_16_BIT)
message = EIEIOMessage(eieio_header=header, data=bytearray())
message.write_data(key, payload)
injection_connection.send_eieio_message(message)
key += 1
payload += 1

header = EIEIOHeader(type_param=EIEIOTypeParam.KEY_16_BIT, prefix_param=0xfff0,
                     prefix_type=EIEIOPrefixType.UPPER_HALF_WORD)
message = EIEIOMessage(eieio_header=header, data=bytearray())
message.write_data(key)
injection_connection.send_eieio_message(message)
key += 1

header = EIEIOHeader(type_param=EIEIOTypeParam.KEY_PAYLOAD_16_BIT,
                     prefix_param=0xfff0,
                     prefix_type=EIEIOPrefixType.UPPER_HALF_WORD)
message = EIEIOMessage(eieio_header=header, data=bytearray())
message.write_data(key, payload)
injection_connection.send_eieio_message(message)
key += 1
payload += 1

header = EIEIOHeader(type_param=EIEIOTypeParam.KEY_16_BIT,
                     prefix_param=0xfff0,
                     prefix_type=EIEIOPrefixType.LOWER_HALF_WORD)
message = EIEIOMessage(eieio_header=header, data=bytearray())
message.write_data(key)
injection_connection.send_eieio_message(message)
key += 1

header = EIEIOHeader(type_param=EIEIOTypeParam.KEY_PAYLOAD_16_BIT,
                     prefix_param=0xfff0,
                     prefix_type=EIEIOPrefixType.LOWER_HALF_WORD)
message = EIEIOMessage(eieio_header=header, data=bytearray())
message.write_data(key, payload)
injection_connection.send_eieio_message(message)
key += 1
payload += 1

header = EIEIOHeader(type_param=EIEIOTypeParam.KEY_16_BIT, prefix_param=0xfff0,
                     payload_base=0xeee0,
                     prefix_type=EIEIOPrefixType.LOWER_HALF_WORD)
message = EIEIOMessage(eieio_header=header, data=bytearray())
message.write_data(key)
injection_connection.send_eieio_message(message)
key += 1

header = EIEIOHeader(type_param=EIEIOTypeParam.KEY_PAYLOAD_16_BIT,
                     prefix_param=0xfff0, payload_base=0xeee0,
                     prefix_type=EIEIOPrefixType.LOWER_HALF_WORD)
message = EIEIOMessage(eieio_header=header, data=bytearray())
message.write_data(key, payload)
injection_connection.send_eieio_message(message)
key += 1
payload += 1

header = EIEIOHeader(type_param=EIEIOTypeParam.KEY_32_BIT)
message = EIEIOMessage(eieio_header=header, data=bytearray())
message.write_data(key)
injection_connection.send_eieio_message(message)
key += 1

header = EIEIOHeader(type_param=EIEIOTypeParam.KEY_PAYLOAD_32_BIT)
message = EIEIOMessage(eieio_header=header, data=bytearray())
message.write_data(key, payload)
injection_connection.send_eieio_message(message)
key += 1
payload += 1

header = EIEIOHeader(type_param=EIEIOTypeParam.KEY_32_BIT, prefix_param=0xfff0,
                     prefix_type=EIEIOPrefixType.UPPER_HALF_WORD)
message = EIEIOMessage(eieio_header=header, data=bytearray())
message.write_data(key)
injection_connection.send_eieio_message(message)
key += 1

header = EIEIOHeader(type_param=EIEIOTypeParam.KEY_PAYLOAD_32_BIT,
                     prefix_param=0xfff0,
                     prefix_type=EIEIOPrefixType.UPPER_HALF_WORD)
message = EIEIOMessage(eieio_header=header, data=bytearray())
message.write_data(key, payload)
injection_connection.send_eieio_message(message)
key += 1
payload += 1

header = EIEIOHeader(type_param=EIEIOTypeParam.KEY_32_BIT, prefix_param=0xfff0,
                     prefix_type=EIEIOPrefixType.LOWER_HALF_WORD)
message = EIEIOMessage(eieio_header=header, data=bytearray())
message.write_data(key)
injection_connection.send_eieio_message(message)
key += 1

header = EIEIOHeader(type_param=EIEIOTypeParam.KEY_PAYLOAD_32_BIT,
                     prefix_param=0xfff0,
                     prefix_type=EIEIOPrefixType.LOWER_HALF_WORD)
message = EIEIOMessage(eieio_header=header, data=bytearray())
message.write_data(key, payload)
injection_connection.send_eieio_message(message)
key += 1
payload += 1

header = EIEIOHeader(type_param=EIEIOTypeParam.KEY_32_BIT, prefix_param=0xfff0,
                     payload_base=0xeeee0000,
                     prefix_type=EIEIOPrefixType.LOWER_HALF_WORD)
message = EIEIOMessage(eieio_header=header, data=bytearray())
message.write_data(key)
injection_connection.send_eieio_message(message)
key += 1

header = EIEIOHeader(type_param=EIEIOTypeParam.KEY_PAYLOAD_32_BIT,
                     prefix_param=0xfff0, payload_base=0xeeee0000,
                     prefix_type=EIEIOPrefixType.LOWER_HALF_WORD)
message = EIEIOMessage(eieio_header=header, data=bytearray())
message.write_data(key, payload)
injection_connection.send_eieio_message(message)
key += 1
'''