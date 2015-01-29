from spinnman.data.little_endian_byte_array_byte_reader import \
    LittleEndianByteArrayByteReader
from spinnman.messages.eieio.eieio_command_header import EIEIOCommandHeader
from spinnman.messages.eieio.eieio_command_message import EIEIOCommandMessage
from spinnman.messages.eieio.eieio_header import EIEIOHeader
from spinnman.messages.eieio.eieio_message import EIEIOMessage
from spinnman.messages.eieio.eieio_type_param import EIEIOTypeParam
from spinnman.connections.udp_packet_connections.reverse_iptag_connection \
    import ReverseIPTagConnection
from spinnman import constants

from spynnaker.pyNN.utilities.conf import config
from spinnman.connections.udp_packet_connections.eieio_command_connection \
    import EieioCommandConnection


import threading
import sqlite3 as sqlite
from time import sleep
import math


class HostBasedInjector(object):
    """ class that does handshaking with tool chain reads the database
    generated, and injects a number of spikes with given spike ids / keys

    """

    def _receive_hand_shake(self, packet):
        """ merthod to process the eieio command messgae

        :param packet: the eieio command message
        :type packet: spinnman.messages.eieio.eieio_command_message
        :return:
        """
        self._recieved_hand_shake_condition.acquire()
        if packet.eieio_command_header.command != 1:
            raise Exception("not recieved correct type of command message")

        #read in data as it contains the path to the database
        reader = LittleEndianByteArrayByteReader(packet.data)
        while not reader.is_at_end():
            self._database_path += str(unichr(reader.read_byte()))

        self._recieved_hand_shake = True
        #send handshake
        hand_shake_response = EIEIOCommandMessage(EIEIOCommandHeader(
            constants.EIEIO_COMMAND_IDS.DATABASE_CONFIRMATION.value))
        self._database_connection.\
            send_eieio_command_message(hand_shake_response)

        #notify myself so that i can read database and inject spikes
        self._recieved_hand_shake_condition.notify()
        self._recieved_hand_shake_condition.release()

    def __init__(self, max_spikes, pop_id):
        self._injection_connection = \
            ReverseIPTagConnection(remote_host=config.get("Machine",
                                                          "machineName"),
                                   remote_port=12345)
        self._database_connection = \
            EieioCommandConnection(port_to_notify=19998, listen_port=19999,
                                   host_to_notify="localhost")
        self._database_connection.register_callback(self._receive_hand_shake)

        self._recieved_hand_shake_condition = threading.Condition()
        self._recieved_hand_shake = False
        self._database_path = ""
        self._max_spikes = max_spikes
        self._pop_id = pop_id

    def run(self):
        print "started \n"
        #wait till ready to read database
        self._recieved_hand_shake_condition.acquire()
        while not self._recieved_hand_shake:
            self._recieved_hand_shake_condition.wait()

        #recieved database location so connect
        connection = sqlite.connect(self._database_path)
        cur = connection.cursor()

        print "reading database \n"
        #search though databse to find the key being used by my injector pop
        key_to_neuron_id_mapping = self._query_database_for_key_mapping(cur)
        max_neurons = self._query_for_max_neurons_for_pop(cur)
        connection.close()

        print "injecting spikes \n"
        for spike in range(0, self._max_spikes):
            self._inject_spike(spike, key_to_neuron_id_mapping, max_neurons)
            sleep(1)
        self._recieved_hand_shake_condition.release()

    def _inject_spike(self, spike, key_to_neuron_id_mapping, max_neurons):
        spike_id = spike * math.floor((max_neurons / self._max_spikes))
        key = key_to_neuron_id_mapping[spike_id]
        header = EIEIOHeader(type_param=EIEIOTypeParam.KEY_32_BIT)
        message = EIEIOMessage(eieio_header=header)
        message.write_data(key)
        print "injecting with key {}\n".format(key)
        self._injection_connection.send_eieio_message(message)
        print "spike injected \n"

    def _query_database_for_key_mapping(self, cur):
        neuron_id_to_key_mapper = dict()
        for row in cur.execute(
                "SELECT n.neuron_id, n.key FROM key_to_neuron_mapping as n"
                " JOIN Partitionable_vertices as p ON n.vertex_id = p.vertex_id"
                " WHERE p.vertex_label=\"{}\"".format(self._pop_id)):
            neuron_id_to_key_mapper[row[0]] = row[1]
        return neuron_id_to_key_mapper

    def _query_for_max_neurons_for_pop(self, cur):
        cur.execute("SELECT no_atoms FROM Partitionable_vertices "
                    "WHERE vertex_label = \"{}\"".format(self._pop_id))
        return cur.fetchone()[0]

if __name__ == "__main__":
    injector = HostBasedInjector(5, "spike_injector_1")
    injector.run()
