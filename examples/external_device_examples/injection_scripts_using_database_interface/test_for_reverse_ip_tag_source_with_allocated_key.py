import spynnaker.pyNN as frontend
import spynnaker_external_devices_plugin.pyNN as externaldevices
from spinnman.messages.eieio.eieio_prefix_type import EIEIOPrefixType
import pylab

frontend.setup(timestep=1.0, min_delay=1.0, max_delay=144.0)

nNeurons = 100
run_time = 10000

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

cell_params_spike_injector = {'host_port_number': 12345}

populations = list()
projections = list()

weight_to_spike = 2.0

populations.append(frontend.Population(nNeurons, frontend.IF_curr_exp,
                                       cell_params_lif, label='pop_1'))
populations.append(
    frontend.Population(nNeurons, externaldevices.ReverseIpTagMultiCastSource,
                        cell_params_spike_injector,
                        label='spike_injector_1'))

populations[0].record()
externaldevices.activate_live_output_for(populations[0])

projections.append(frontend.Projection(
    populations[1], populations[0],
    frontend.OneToOneConnector(weights=weight_to_spike)))

loopConnections = list()
for i in range(0, nNeurons - 1):
    singleConnection = (i, ((i + 1) % nNeurons), weight_to_spike, 3)
    loopConnections.append(singleConnection)

projections.append(frontend.Projection(populations[0], populations[0],
                   frontend.FromListConnector(loopConnections)))


frontend.run(run_time)

spikes = populations[0].getSpikes(compatible_output=True)

if spikes is not None:
    print spikes
    pylab.figure()
    pylab.plot([i[1] for i in spikes], [i[0] for i in spikes], ".")
    pylab.xlabel('neuron id')
    pylab.ylabel('Time/ms')
    pylab.title('spikes')
    pylab.show()
else:
    print "No spikes received"

frontend.end()