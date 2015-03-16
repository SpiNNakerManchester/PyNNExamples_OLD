# imports of both spynnaker and external device plugin.
import spynnaker.pyNN as Frontend
import spynnaker_external_devices_plugin.pyNN as ExternalDevices

#######################
# import to allow prefix type for the prefix eieio protocol
######################
from spinnman.messages.eieio.eieio_prefix_type import EIEIOPrefixType
from spynnaker_external_devices_plugin.pyNN.connections\
    .spynnaker_live_spikes_connection import SpynnakerLiveSpikesConnection

# plotter in python
import pylab
import time
import random

# initial call to set up the front end (pynn requirement)
Frontend.setup(timestep=1.0, min_delay=1.0, max_delay=144.0)

# neurons per population and the length of runtime in ms for the simulation,
# as well as the expected weight each spike will contain
n_neurons = 100
run_time = 8000
weight_to_spike = 2.0

# neural parameters of the ifcur model used to respond to injected spikes.
# (cell params for a synfire chain)
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

##################################
# parameters for the injector population.  These parameters will work when
# sending 32-bit keys.
# NOTE: these parameters assume no prefix requirement - see below for a
#       set of parameters with a default prefix
##################################
cell_params_spike_injector = {

    # The port on which the spiNNaker machine should listen for packets.
    # Packets to be injected should be sent to this port on the spiNNaker
    # machine
    'port': 12345
}


##################################
# parameters for the injector population.  The parameters will work best when
# sending 16-bit keys.
##################################
cell_params_spike_injector_with_prefix = {

    # The port on which the spiNNaker machine should listen for packets.
    # Packets to be injected should be sent to this port on the spiNNaker
    # machine
    'port': 12346,

    # The prefix and prefix type allow the injector to convert received 16-bit
    # keys (or neuron ids) in to 32-bit spiNNaker keys.  With the settings
    # below, the prefix of 7 is put in the upper 16-bits of the key, with the
    # neuron id being the lower 16-bits.  Therefore, if 16-bit neuron id 4 is
    # received, the key sent will be:
    # (0x7 << 16) | 0x4 = 0x70000 | 0x4 = 0x70004
    'prefix': 7,
    'prefix_type': EIEIOPrefixType.UPPER_HALF_WORD,

    # This is the base key to be used for the injection, which is used to
    # allow the keys to be routed around the spiNNaker machine.  All keys, once
    # joined with the prefix, should have keys that look like this.  Since the
    # prefix is specified as 7 in the upper half word, the key 0x70000 works,
    # as long as 16-bit keys are received
    'virtual_key': 0x70000,
}

# create synfire populations (if cur exp)
pop_forward = Frontend.Population(n_neurons, Frontend.IF_curr_exp,
                                  cell_params_lif, label='pop_forward')
pop_backward = Frontend.Population(n_neurons, Frontend.IF_curr_exp,
                                   cell_params_lif, label='pop_backward')

# Create injection populations
injector_forward = Frontend.Population(
    n_neurons, ExternalDevices.ReverseIpTagMultiCastSource,
    cell_params_spike_injector_with_prefix, label='spike_injector_forward')
injector_backward = Frontend.Population(
    n_neurons, ExternalDevices.ReverseIpTagMultiCastSource,
    cell_params_spike_injector, label='spike_injector_backward')

# Create a connection from the injector into the populations
Frontend.Projection(injector_forward, pop_forward,
                    Frontend.OneToOneConnector(weights=weight_to_spike))
Frontend.Projection(injector_backward, pop_backward,
                    Frontend.OneToOneConnector(weights=weight_to_spike))

# Synfire chain connections where each neuron is connected to its next neuron
# NOTE: there is no recurrent connection so that each chain stops once it
# reaches the end
loop_forward = list()
loop_backward = list()
for i in range(0, n_neurons - 1):
    loop_forward.append((i, (i + 1) % n_neurons, weight_to_spike, 3))
    loop_backward.append(((i + 1) % n_neurons, i, weight_to_spike, 3))
Frontend.Projection(pop_forward, pop_forward,
                    Frontend.FromListConnector(loop_forward))
Frontend.Projection(pop_backward, pop_backward,
                    Frontend.FromListConnector(loop_backward))

# record spikes from the synfire chains so that we can read off valid results
# in a safe way afterwards, and verify the behavior
pop_forward.record()
pop_backward.record()

# Activate the sending of live spikes
ExternalDevices.activate_live_output_for(pop_forward)
ExternalDevices.activate_live_output_for(pop_backward)


# Create a sender of packets for the forward population
def send_input_forward(label, sender):
    for neuron_id in range(0, 100, 20):
        time.sleep(random.random() + 0.5)
        print "Sending forward spike", neuron_id
        sender.send_spike(label, neuron_id, send_full_keys=True)


# Create a sender of packets for the backward population
def send_input_backward(label, sender):
    for neuron_id in range(0, 100, 20):
        real_id = 100 - neuron_id - 1
        time.sleep(random.random() + 0.5)
        print "Sending backward spike", real_id
        sender.send_spike(label, real_id)


# Create a receiver of live spikes
def receive_spikes(label, time, neuron_ids):
    for neuron_id in neuron_ids:
        print "Received spike at time", time, "from", label, "-", neuron_id

# Set up the live connection for sending and receiving spikes
live_spikes_connection = SpynnakerLiveSpikesConnection(
    receive_labels=["pop_forward", "pop_backward"],
    send_labels=["spike_injector_forward", "spike_injector_backward"])

# Set up callbacks to occur at the start of simulation
live_spikes_connection.add_start_callback("spike_injector_forward",
                                          send_input_forward)
live_spikes_connection.add_start_callback("spike_injector_backward",
                                          send_input_backward)

# Set up callbacks to occur when spikes are received
live_spikes_connection.add_receive_callback("pop_forward", receive_spikes)
live_spikes_connection.add_receive_callback("pop_backward", receive_spikes)


# Run the simulation on spiNNaker
Frontend.run(run_time)

# Retrieve spikes from the synfire chain population
spikes_forward = pop_forward.getSpikes()
spikes_backward = pop_backward.getSpikes()

# If there are spikes, plot using matplotlib
if len(spikes_forward) != 0 or len(spikes_backward) != 0:
    pylab.figure()
    if len(spikes_forward) != 0:
        pylab.plot([i[1] for i in spikes_forward],
                   [i[0] for i in spikes_forward], "b.")
    if len(spikes_backward) != 0:
        pylab.plot([i[1] for i in spikes_backward],
                   [i[0] for i in spikes_backward], "r.")
    pylab.xlabel('neuron id')
    pylab.ylabel('Time/ms')
    pylab.title('spikes')
    pylab.show()
else:
    print "No spikes received"

# Clear data structures on spiNNaker to leave the machine in a clean state for
# future executions
Frontend.end()
