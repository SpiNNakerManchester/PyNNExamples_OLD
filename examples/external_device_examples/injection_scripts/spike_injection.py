# imports of both spynnaker and external device plugin.
import spynnaker.pyNN as Frontend
import spynnaker_external_devices_plugin.pyNN as ExternalDevices

#######################
# import to allow prefix type for the prefix eieio protocol
######################
from spinnman.messages.eieio.eieio_prefix_type import EIEIOPrefixType

# plotter in python
import pylab

# initial call to set up the front end (pynn requirement)
Frontend.setup(timestep=1.0, min_delay=1.0, max_delay=144.0)

# neurons per population and the length of runtime in ms for the simulation,
# as well as the expected weight each spike will contain
nNeurons = 100
run_time = 10000
weight_to_spike = 2.0

#######################
# if the spike being injected uses a prefix or not (dial for using different
# EIEIO protocol.
######################
using_prefix = False

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
    'port': 12345,

    # This is the base key to be used for the injection, which is used to
    # allow the keys to be routed around the spiNNaker machine.  All 32-bit
    # keys to be sent should have use this prefix e.g. to send a spike from
    # neuron id 8 to this population, the 32-bit spike should be:
    # 0x70800 | 0x8 = 0x70808
    'virtual_key': 0x70800
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

# bog standard pop and projection lists.
populations = list()
projections = list()

# create synfire population (if cur exp pop)
pop = Frontend.Population(nNeurons, Frontend.IF_curr_exp, cell_params_lif,
                          label='pop')

###############################
# Pick which set of parameters to use for the multicast source, depending on
# whether a prefix is to be used
##############################
injector = None
if using_prefix:
    injector = Frontend.Population(
        nNeurons, ExternalDevices.ReverseIpTagMultiCastSource,
        cell_params_spike_injector_with_prefix, label='spike_injector')
else:
    injector = Frontend.Population(
        nNeurons, ExternalDevices.ReverseIpTagMultiCastSource,
        cell_params_spike_injector, label='spike_injector')

# record spikes from the synfire chain so that we can read off valid results
# in a safe way afterwards, and verify the behavior
pop.record()

# Create a connection from the injector into the population
Frontend.Projection(injector, pop,
                    Frontend.OneToOneConnector(weights=weight_to_spike))

# Synfire chain connection where each neuron is connected to its next neuron
# NOTE: there is no recurrent connection from max atom to 0 atom, so that
# each chain stops once it reaches the top neuron
loopConnections = list()
for i in range(0, nNeurons - 1):
    singleConnection = (i, ((i + 1) % nNeurons), weight_to_spike, 3)
    loopConnections.append(singleConnection)
Frontend.Projection(pop, pop, Frontend.FromListConnector(loopConnections))

# Run the simulation on spiNNaker
Frontend.run(run_time)

# Retrieve spikes from the synfire chain population
spikes = pop.getSpikes(compatible_output=True)

# If there are spikes, plot using matplotlib.
###########################
# When this is executed with the "host_based_injector_tester.py" script in the
# same folder to this one it should generate a plot which shows a staggered
# synfire chain which fires 4 times, from neuron 0 initially, then from each of
# neuron 20, 40, 60, 80 in turn.  The basic plot looks like the following
#
#
#
#
#          #                #                #          #        #
#          #               #                #          #        #
#          #              #                #          #        #
#          #             #                #          #        #
#          #            #                #          #
#          #           #                #          #
#          #          #                #          #
#          #         #                #
#          #        #                #
#          #       #                #
#          #      #
#          #     #
#          #    #
#          #   #
#          #  #
#          ######################################################
#                                     Time(ms)
#
###########################
if len(spikes) != 0:
    print spikes
    pylab.figure()
    pylab.plot([i[1] for i in spikes], [i[0] for i in spikes], ".")
    pylab.xlabel('neuron id')
    pylab.ylabel('Time/ms')
    pylab.title('spikes')
    pylab.show()
else:
    print "No spikes received"

# Clear data structures on spiNNaker to leave the machine in a clean state for
# future executions
Frontend.end()
