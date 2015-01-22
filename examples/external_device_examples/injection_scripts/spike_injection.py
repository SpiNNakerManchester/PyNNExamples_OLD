import spynnaker.pyNN as Frontend
import spynnaker_external_devices_plugin.pyNN as ExternalDevices
from spinnman.messages.eieio.eieio_prefix_type import EIEIOPrefixType
import pylab

Frontend.setup(timestep=1.0, min_delay=1.0, max_delay=144.0)

nNeurons = 100
run_time = 10000
using_prefix = True

cell_params_lif = {'cm'        : 0.25,  # nF
                   'i_offset'  : 0.0,
                   'tau_m'     : 20.0,
                   'tau_refrac': 2.0,
                   'tau_syn_E' : 5.0,
                   'tau_syn_I' : 5.0,
                   'v_reset'   : -70.0,
                   'v_rest'    : -65.0,
                   'v_thresh'  : -50.0
                  }

cell_params_spike_injector = {'host_port_number' : 12345,
                              'host_ip_address'  : "localhost",
                              'virtual_key'      : 0x70000,
                              'prefix'           : None,
                              'tag'              : None}

cell_params_spike_injector_with_prefix = \
    {'host_port_number' : 12345,
     'host_ip_address'  : "localhost",
     'virtual_key'      : 0x70800,
     'prefix'           : 7,
     'prefix_type'      : EIEIOPrefixType.UPPER_HALF_WORD}

populations = list()
projections = list()

weight_to_spike = 2.0

populations.append(Frontend.Population(nNeurons, Frontend.IF_curr_exp,
                                       cell_params_lif, label='pop_1'))

if using_prefix:
    populations.append(
        Frontend.Population(nNeurons,
                            ExternalDevices.ReverseIpTagMultiCastSource,
                            cell_params_spike_injector_with_prefix,
                            label='spike_injector_1'))
else:
    populations.append(
        Frontend.Population(nNeurons,
                            ExternalDevices.ReverseIpTagMultiCastSource,
                            cell_params_spike_injector,
                            label='spike_injector_1'))

populations[0].record()

projections.append(
    Frontend.Projection(populations[1], populations[0],
                        Frontend.OneToOneConnector(weights=weight_to_spike)))

loopConnections = list()
for i in range(0, nNeurons - 1):
    singleConnection = (i, ((i + 1) % nNeurons), weight_to_spike, 3)
    loopConnections.append(singleConnection)

projections.append(Frontend.Projection(populations[0], populations[0],
                   Frontend.FromListConnector(loopConnections)))


Frontend.run(run_time)

spikes = populations[0].getSpikes(compatible_output=True)

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


Frontend.end()