import pyNN.spiNNaker as p

from spinnman.model.cpu_state import CPUState

from spynnaker.pyNN.exceptions import ExecutableFailedToStartException
from spynnaker.pyNN.exceptions import ExecutableFailedToStopException

import math
import sys
from spynnaker.pyNN.utilities.conf import config
from spinnman.transceiver import create_transceiver_from_hostname
from spinnman.model.core_subsets import CoreSubsets
from spinnman.model.core_subset import CoreSubset

hostname = config.get("Machine", "machineName")
down_chips = config.get("Machine", "down_chips")
down_cores = config.get("Machine", "down_cores")
version = config.getint("Machine", "version")
for i in range(1, len(sys.argv)):
    if sys.argv[i] == "-hostname":
        hostname = sys.argv[i + 1]
        i += 1
    elif sys.argv[i] == "-down_chips":
        downed_chips = sys.argv[i + 1]
        i += 1
    elif sys.argv[i] == "-down_cores":
        downed_cores = sys.argv[i + 1]
        i += 1
    elif sys.argv[i] == "-version":
        version = sys.argv[i + 1]
        i += 1

n_neurons_per_pop = 1
spike_gap = 10
weight = 10.0

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


def create_injector(i, x, y, proc):
    pop = p.Population(n_neurons_per_pop, p.SpikeSourceArray,
                       {"spike_times": [spike_times[i]]},
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

# Get the machine details from a transceiver
ignored_chips = None
ignored_cores = None
if down_chips is not None and down_chips != "None":
    ignored_chips = CoreSubsets()
    for down_chip in down_chips.split(":"):
        x, y = down_chip.split(",")
        ignored_chips.add_core_subset(CoreSubset(int(x), int(y), []))
if down_cores is not None and down_cores != "None":
    ignored_cores = CoreSubsets()
    for down_core in down_cores.split(":"):
        x, y, processor_id = down_core.split(",")
        ignored_cores.add_processor(int(x), int(y), int(processor_id))
transceiver = create_transceiver_from_hostname(
    hostname, ignore_chips=ignored_chips,
    ignore_cores=ignored_cores)
transceiver.ensure_board_is_ready(version)
machine = transceiver.get_machine_details()
cores = [(chip.x, chip.y, processor.processor_id)
         for chip in machine.chips
         for processor in filter(lambda proc: not proc.is_monitor,
                                 chip.processors)]
cores = sorted(cores)

# Get the number of cores and use this to make the simulation
n_cores = 0
for chip in machine.chips:
    for processor in chip.processors:
        if not processor.is_monitor:
            n_cores += 1
n_pops = int(math.floor(n_cores / 2.0))
print "n_cores =", n_cores, "n_pops =", n_pops
spike_times = range(0, n_pops * spike_gap, spike_gap)
run_time = (n_pops + 1) * spike_gap + 1

for do_injector_first in [True, False]:

    # Set up for execution
    p.setup(1.0, machine=hostname)

    injectors = list()
    populations = list()
    for i in range(n_pops):
        injector = None
        pop = None
        (x1, y1, p1) = cores[i * 2]
        (x2, y2, p2) = cores[(i * 2) + 1]
        if do_injector_first:
            injector = create_injector(i, x1, y1, p1)
            pop = create_pop(i, x2, y2, p2)
        else:
            pop = create_pop(i, x1, y1, p1)
            injector = create_injector(i, x2, y2, p2)
        pop.record()
        p.Projection(injector, pop, p.OneToOneConnector(weights=weight))
        injectors.append(injector)
        populations.append(pop)

    for i in range(n_pops - 1):
        p.Projection(populations[i], populations[i + 1],
                     p.AllToAllConnector(weights=weight / n_neurons_per_pop))

    try:
        p.run(run_time)
        last_failed_pop = None
        for i in range(n_pops):
            population = populations[i]
            spikes = population.getSpikes()
            if len(spikes) == 0:
                placement = get_placement(population)
                errors.append((placement.x, placement.y, placement.p,
                               "Failed to spike"))
                last_failed_pop = i
            else:
                start = i + 1
                if last_failed_pop is not None:
                    start = (spike_times[last_failed_pop + 1] +
                             (i - (last_failed_pop + 1)) + 1)
                expected_out_times = [float(t)
                                      for _ in range(n_neurons_per_pop)
                                      for t in range(
                                          start,
                                          (i + 1) * spike_gap, spike_gap - 1)]
                out_times = [spike[1] for spike in spikes]
                if out_times != expected_out_times:
                    placement = get_placement(population)
                    errors.append(
                        (placement.x, placement.y, placement.p,
                         "Spiked at {} instead of {} (injection = {})".format(
                             out_times, expected_out_times, spike_times[i])))
                else:
                    all_spikes.append((population.label, spikes))
    except ExecutableFailedToStartException, ExecutableFailedToStopException:
        core_infos = transceiver.get_cpu_information()
        core_info_dict = dict()
        for core_info in core_infos:
            core_info_dict[core_info.x, core_info.y, core_info.p] = core_info
        for i in range(n_pops):
            population = populations[i]
            vertex = population._vertex
            spinnaker = population._spinnaker
            subvertices = spinnaker._graph_mapper.get_subvertices_from_vertex(
                vertex)
            subvertex = iter(subvertices).next()
            placement = spinnaker._placements.get_placement_of_subvertex(
                subvertex)
            core_info = core_info_dict[placement.x, placement.y, placement.p]
            if core_info.state not in (CPUState.RUNNING, CPUState.SYNC0,
                                       CPUState.FINSHED):
                errors.append((core_info.x, core_info.y, core_info.p,
                               "CPU State is {}".format(core_info.state)))
    p.end()

if len(errors) == 0:
    for label, spikes in all_spikes:
        print label, spikes
    print "No errors"
else:
    for (x, y, p, error) in sorted(errors, key=lambda e: (e[0], e[1], e[2])):
        print "Error at core {}, {}, {}: {}".format(x, y, p, error)
