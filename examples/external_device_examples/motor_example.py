"""
motor example that just feeds data to the motor pop which starts the motor
going forward
"""

import spynnaker.pyNN as p
import spynnaker_external_devices_plugin.pyNN as q

# set up the tools
p.setup(timestep=1.0, min_delay=1.0, max_delay=32.0)

# set up the virtual chip coordinates for the motor
connected_chip_coords = {'x': 0, 'y': 0}
virtual_chip_coords = {'x': 0, 'y': 5}
link = 4

populations = list()
projections = list()


input_population = p.Population(1, p.SpikeSourcePoisson, {'rate': 1})
motor_population = q.MunichMotorPopulation(
    virtual_chip_x=0, virtual_chip_y=5, connected_to_real_chip_x=0,
    connected_to_real_chip_y=0, connected_to_real_chip_link_id=4)

p.Projection(input_population, motor_population,
             p.FromListConnector([(0, 0, 2.0, 1.0)]))

p.run(10000)
