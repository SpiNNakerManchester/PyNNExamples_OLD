"""
Synfirechain-like example
"""
try:
    import pyNN.spiNNaker as p
except Exception as e:
    import spynnaker.pyNN as p
import pylab

p.setup(timestep=1.0, min_delay=1.0, max_delay=144.0)
nNeurons = 10  # number of neurons in each population
run_time = 6000


cell_params_lif = {'cm': 0.25,
                   'i_offset': 0.0,
                   'tau_m': 20.0,
                   'tau_refrac': 2.0,
                   'tau_syn_E': 1.0,
                   'tau_syn_I': 1.0,
                   'v_reset': -70.0,
                   'v_rest': -65.0,
                   'v_thresh': -50.0
                   }

populations = list()
projections = list()

weight_to_spike = 10.0
delay = 2
second_spike_start = delay * nNeurons
space_between_inputs = delay * nNeurons * 2

connections = list()
reverseConnections = list()
for i in range(0, nNeurons - 1):
    connections.append((i, (i + 1) % nNeurons, weight_to_spike, delay))
    reverseConnections.append(((i + 1) % nNeurons, i, weight_to_spike, delay))

injectionConnection_1 = [(0, 0, weight_to_spike, 1)]
injectionConnection_2 = [(1, nNeurons - 1, weight_to_spike, 1)]
input_1 = [i for i in xrange(0, run_time, space_between_inputs)]
input_2 = [i for i in xrange(second_spike_start, run_time,
                             space_between_inputs)]
spikeArray = {'spike_times': [input_1, input_2],
              'max_on_chip_memory_usage_for_spikes_in_bytes': 640,
              'space_before_notification': 320}
pop_1 = p.Population(nNeurons, p.IF_curr_exp, cell_params_lif, label='pop_1')
pop_2 = p.Population(nNeurons, p.IF_curr_exp, cell_params_lif, label='pop_2')
input_spikes = p.Population(2, p.SpikeSourceArray, spikeArray,
                            label='input_spikes')

p.Projection(pop_1, pop_1, p.FromListConnector(connections))
p.Projection(pop_2, pop_2, p.FromListConnector(reverseConnections))
p.Projection(input_spikes, pop_1, p.FromListConnector(injectionConnection_1))
p.Projection(input_spikes, pop_2, p.FromListConnector(injectionConnection_2))

pop_1.record()
pop_2.record()
input_spikes.record()

p.run(run_time)

spikes_1 = pop_1.getSpikes()
spikes_2 = pop_2.getSpikes()
input_spikes_data = input_spikes.getSpikes()

pylab.figure()
pylab.plot([i[1] for i in spikes_1], [i[0] for i in spikes_1], "b.")
pylab.plot([i[1] for i in spikes_2], [i[0] for i in spikes_2], "r.")
pylab.xlabel('Time/ms')
pylab.ylabel('spikes')
pylab.title('spikes')
pylab.show()

p.end()
