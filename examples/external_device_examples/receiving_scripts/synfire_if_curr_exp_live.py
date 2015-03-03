# Standard PyNN imports
import pyNN.spiNNaker as p
import pylab

# Extra imports for external communication
from spynnaker_external_devices_plugin.pyNN import activate_live_output_for
from spynnaker.pyNN.utilities.conf import config
from spinnman.connections.udp_packet_connections.stripped_iptag_connection \
    import StrippedIPTagConnection
from spinnman.constants import TRAFFIC_TYPE


# Define a function to handle the received packet
def packet_callback(packet):
    count = packet.eieio_header.count_param + 1
    time = packet.eieio_header.payload_base
    print "Received", count, "spikes at time", time

    data = packet.data
    for i in range(0, count, 4):
        key = (data[i + 3] << 24 | data[i + 2] << 16
               | data[i + 1] << 8 | data[i])
        print "   ", key

# Define a synfire chain as usual
p.setup(timestep=1.0, min_delay=1.0, max_delay=144.0)
nNeurons = 200  # number of neurons in each population
p.set_number_of_neurons_per_core("IF_curr_exp", nNeurons / 2)

cell_params_lif = {'cm': 0.25,
                   'i_offset': 0.0,
                   'tau_m': 20.0,
                   'tau_refrac': 2.0,
                   'tau_syn_E': 5.0,
                   'tau_syn_I': 5.0,
                   'v_reset': -70.0,
                   'v_rest': -65.0,
                   'v_thresh': -50.0
                   }

populations = list()
projections = list()

weight_to_spike = 2.0
delay = 17

loopConnections = list()
for i in range(0, nNeurons):
    singleConnection = (i, ((i + 1) % nNeurons), weight_to_spike, delay)
    loopConnections.append(singleConnection)

injectionConnection = [(0, 0, weight_to_spike, 1)]
spikeArray = {'spike_times': [[0]]}
populations.append(p.Population(nNeurons, p.IF_curr_exp, cell_params_lif,
                   label='pop_1'))
populations.append(p.Population(1, p.SpikeSourceArray, spikeArray,
                   label='inputSpikes_1'))

projections.append(p.Projection(populations[0], populations[0],
                   p.FromListConnector(loopConnections)))
projections.append(p.Projection(populations[1], populations[0],
                   p.FromListConnector(injectionConnection)))

populations[0].record()

# Activate live output for the population
activate_live_output_for(populations[0])

# Create a connection and register the callback function
packet_grabber = StrippedIPTagConnection(
    local_port=config.get("Recording", "live_spike_port"))
packet_grabber.register_callback(packet_callback, TRAFFIC_TYPE.EIEIO_DATA)

# Start the simulation
p.run(5000)

spikes = populations[0].getSpikes(compatible_output=True)

if spikes is not None:
    print spikes
    pylab.figure()
    pylab.plot([i[1] for i in spikes], [i[0] for i in spikes], ".")
    pylab.xlabel('Time/ms')
    pylab.ylabel('spikes')
    pylab.title('spikes')
    pylab.show()
else:
    print "No spikes received"
