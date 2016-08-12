try:
    import pyNN.spiNNaker as p
except Exception as e:
    import spynnaker.pyNN as p
import numpy
import matplotlib.pyplot as py_plot

p.setup(timestep=1.0, min_delay=1.0, max_delay=8.0)

n_pop = 6
nNeurons = 100
simulation_time = 3000

rng = p.NumpyRNG(seed=28374)
rng1 = p.NumpyRNG(seed=12345)

delay_distr = p.RandomDistribution('uniform', [5, 10], rng)
weight_distr = p. RandomDistribution('uniform', [0, 2], rng1)

v_distr = p.RandomDistribution('uniform', [-55, -95], rng)

cell_params_lif_in = {
    'tau_m': 32,
    'v_init': -80,
    'v_rest': -75,
    'v_reset': -95,
    'v_thresh': -55,
    'tau_syn_E': 5,
    'tau_syn_I': 10,
    'tau_refrac': 20,
    'i_offset': 1
}

cell_params_lif = {
    'tau_m': 32,
    'v_init': -80,
    'v_rest': -75,
    'v_reset': -95,
    'v_thresh': -55,
    'tau_syn_E': 5,
    'tau_syn_I': 10,
    'tau_refrac': 5,
    'i_offset': 0
}

cell_params_lif_dual = {'tau_syn_E2': 100}
cell_params_lif_dual.update(cell_params_lif)


populations = list()
projections = list()

weight_to_spike = 20

for i in range(n_pop):
    if i == 0:
        populations.append(p.Population(
            nNeurons, p.IF_curr_exp, cell_params_lif_in, label='pop_%d' % i))
        populations[i].randomInit(v_distr)
    elif i == 1:
        populations.append(p.Population(
            nNeurons, p.IF_curr_exp, cell_params_lif, label='pop_%d' % i))
        dual_stim_population = p.Population(
            nNeurons, p.IF_curr_dual_exp, cell_params_lif_dual,
            label='pop_dual_%d' % i)
    else:
        populations.append(p.Population(
            nNeurons, p.IF_curr_exp, cell_params_lif, label='pop_%d' % i))
    if i == 1:
        projections.append(p.Projection(
            populations[i - 1], dual_stim_population, p.OneToOneConnector(
                weights=weight_to_spike, delays=10), target='excitatory'))
        projections.append(p.Projection(
            populations[i], dual_stim_population, p.OneToOneConnector(
                weights=weight_to_spike, delays=10), target='excitatory2'))
    if i > 0:
        projections.append(p.Projection(
            populations[i - 1], populations[i], p.OneToOneConnector(
                weights=weight_to_spike, delays=10)))

    populations[i].record_v()
    populations[i].record()

p.run(simulation_time)

id_accumulator = 0
colour_divider = 0x600 / n_pop
for i in range(n_pop):
    colour = 0x000000
    colour_scale = (i / 6) * colour_divider
    if (i % 6) < 2 or (i % 6) == 5:
        colour += 0xFF0000 - (colour_scale * 0x10000)
    if (i % 6) > 0 and (i % 6) < 4:
        colour += 0x00FF00 - (colour_scale * 0x100)
    if (i % 6) > 2:
        colour += 0x0000FF - colour_scale
    data = numpy.asarray(populations[i].getSpikes())
    if len(data) > 0:
        py_plot.scatter(
            data[:, 0], data[:, 1] + id_accumulator,
            color=('#%06x' % colour), s=4)
    id_accumulator = id_accumulator + populations[i].size

p.end()
py_plot.show()
