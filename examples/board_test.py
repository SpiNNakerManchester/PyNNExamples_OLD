import pyNN.spiNNaker as p
import math

n_neurons_per_pop = 1
spike_gap = 10
weight = 10.0

cell_params_lif = {
    'cm': 0.25,
    'i_offset': 0.0,
    'tau_m': 20.0,
    'tau_refrac': 2.0,
    'tau_syn_E': 1.0,
    'tau_syn_I': 1.0,
    'v_reset': -70.0,
    'v_rest': -65.0,
    'v_thresh': -50.0
}


def create_injector(i, x, y, proc):
    pop = p.Population(n_neurons_per_pop, p.SpikeSourceArray,
                       {"spike_times": spike_times},
                       label="injector_{}".format(i))
    pop.add_placement_constraint(x, y, proc)
    return pop


def create_pop(i, x, y, proc):
    pop = p.Population(n_neurons_per_pop, p.IF_curr_exp, cell_params_lif,
                       label=("pop_{}".format(i)))
    pop.add_placement_constraint(x, y, proc)
    return pop


def get_placement(population):
    vertex = population._vertex
    spinnaker = population._spinnaker
    subvertices = spinnaker._graph_mapper.get_subvertices_from_vertex(
        vertex)
    subvertex = iter(subvertices).next()
    return spinnaker._placements.get_placement_of_subvertex(subvertex)

errors = list()
all_spikes = list()

for do_injector_first in [True, False]:

    # Set up for execution
    p.setup(1.0)

    machine = p.get_machine()
    cores = sorted([
        (chip.x, chip.y, processor.processor_id) for chip in machine.chips
        for processor in chip.processors if not processor.is_monitor
    ])
    n_cores = len(cores)
    n_pops = int(math.floor(n_cores / 2.0))
    print "n_cores =", n_cores, "n_pops =", n_pops

    spike_times = range(0, n_pops * spike_gap, spike_gap)
    run_time = (n_pops + 1) * spike_gap + 1

    injectors = list()
    for i in range(n_pops):
        injector = None
        (x1, y1, p1) = cores[i * 2]
        (x2, y2, p2) = cores[(i * 2) + 1]
        if do_injector_first:
            injector = create_injector(i, x1, y1, p1)
        else:
            injector = create_injector(i, x2, y2, p2)
        injectors.append(injector)

    populations = list()
    for i in range(n_pops):
        pop = None
        (x1, y1, p1) = cores[i * 2]
        (x2, y2, p2) = cores[(i * 2) + 1]
        if do_injector_first:
            pop = create_pop(i, x2, y2, p2)
        else:
            pop = create_pop(i, x1, y1, p1)
        pop.record()
        populations.append(pop)

    for i in range(n_pops):
        p.Projection(
            injectors[i], populations[i],
            p.AllToAllConnector(weights=(weight / n_neurons_per_pop)))

    p.run(run_time)
    for i in range(n_pops):
        population = populations[i]
        spikes = population.getSpikes()
        if len(spikes) == 0:
            placement = get_placement(population)
            errors.append((placement.x, placement.y, placement.p,
                           "Failed to spike"))
        else:

            expected_out_times = [spike_time + 1
                                  for spike_time in spike_times]
            out_times = [spike[1] for spike in spikes]
            if len(out_times) != len(expected_out_times):
                placement = get_placement(population)
                errors.append(
                    (placement.x, placement.y, placement.p,
                     "Spiked at {} instead of {}".format(
                         out_times, expected_out_times)))
            else:
                all_spikes.append((population.label, spikes))
    p.end()

if len(errors) == 0:
    print "No errors"
else:
    for (x, y, p, error) in sorted(errors, key=lambda e: (e[0], e[1], e[2])):
        print "Error at core {}, {}, {}: {}".format(x, y, p, error)
