"""
Synfirechain-like example
"""
import spynnaker8.pyNN as p
import pylab

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
    singleConnection = (i, ((i + 1) % nNeurons))
    loopConnections.append(singleConnection)

injectionConnection = [(0, 0)]
spikeArray = {'spike_times': [[0]]}
populations.append(
    p.Population(nNeurons, p.IF_curr_exp(**cell_params_lif), label='pop_1'))
populations.append(
    p.Population(1, p.SpikeSourceArray(**spikeArray), label='inputSpikes_1'))

projections.append(p.Projection(
    populations[0], populations[0], p.FromListConnector(loopConnections),
    p.StaticSynapse(weight=weight_to_spike, delay=delay)))
projections.append(p.Projection(
    populations[1], populations[0], p.FromListConnector(injectionConnection),
    p.StaticSynapse(weight=weight_to_spike, delay=1)))

populations[0].record(['v', 'gsyn_exc', 'gsyn_inh', 'spikes'])

p.run(5000)

v = None
gsyn = None
spikes = None

v = populations[0].get('v', compatible_output=True)
gsyn_exc = populations[0].get('gsyn_exc', compatible_output=True)
gsyn_inh = populations[0].get('gsyn_inh', compatible_output=True)
spikes = populations[0].get('spikes', compatible_output=True)

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

# Make some graphs

if v is not None:
    ticks = len(v) / nNeurons
    pylab.figure()
    pylab.xlabel('Time/ms')
    pylab.ylabel('v')
    pylab.title('v')
    for pos in range(0, nNeurons, 20):
        v_for_neuron = v[pos * ticks: (pos + 1) * ticks]
        pylab.plot([i[2] for i in v_for_neuron])
    pylab.show()

if gsyn_exc is not None:
    ticks = len(gsyn_exc) / nNeurons
    pylab.figure()
    pylab.xlabel('Time/ms')
    pylab.ylabel('gsyn exc')
    pylab.title('gsyn exc')
    for pos in range(0, nNeurons, 20):
        gsyn_for_neuron = gsyn_exc[pos * ticks: (pos + 1) * ticks]
        pylab.plot([i[2] for i in gsyn_for_neuron])
    pylab.show()

if gsyn_inh is not None:
    ticks = len(gsyn_inh) / nNeurons
    pylab.figure()
    pylab.xlabel('Time/ms')
    pylab.ylabel('gsyn inh')
    pylab.title('gsyn inh')
    for pos in range(0, nNeurons, 20):
        gsyn_for_neuron = gsyn_inh[pos * ticks: (pos + 1) * ticks]
        pylab.plot([i[2] for i in gsyn_for_neuron])
    pylab.show()

p.end()
