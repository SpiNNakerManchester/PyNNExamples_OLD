"""
retina example that just feeds data from a retina to live output via an
intermediate population
"""
import spynnaker.pyNN as p
import spynnaker_external_devices_plugin.pyNN as q
import retina_lib as retina_lib

connected_chip_details = {
    "connected_to_real_chip_x": 0,
    "connected_to_real_chip_y": 0,
    "connected_to_real_chip_link_id": 4
}


def get_updated_params(params):
    params.update(connected_chip_details)
    return params

# Setup
p.setup(timestep=1.0)

# # Munich Right Retina - Down Polarity
# retina_pop = p.Population(
#     None, q.MunichRetinaDevice, get_updated_params({
#         'virtual_chip_x': 5,
#         'virtual_chip_y': 0,
#         'polarity': q.MunichRetinaDevice.DOWN_POLARITY,
#         'position': q.MunichRetinaDevice.RIGHT_RETINA}),
#     label='External retina')

# # Munich Right Retina - Up Polarity
# retina_pop = p.Population(
#     None, q.MunichRetinaDevice, get_updated_params({
#         'virtual_chip_x': 6,
#         'virtual_chip_y': 0,
#         'polarity': q.MunichRetinaDevice.UP_POLARITY,
#         'position': q.MunichRetinaDevice.RIGHT_RETINA}),
#     label='External retina')

# # Munich Left Retina - Merged Polarity
# retina_pop = p.Population(
#     None, q.MunichRetinaDevice, get_updated_params({
#         'virtual_chip_x': 7,
#         'virtual_chip_y': 0,
#         'polarity': q.MunichRetinaDevice.MERGED_POLARITY,
#         'position': q.MunichRetinaDevice.LEFT_RETINA}),
#     label='External retina')

# # FPGA Retina - Merged Polarity
# retina_pop = p.Population(
#     None, q.ExternalFPGARetinaDevice, get_updated_params({
#         'mode': q.ExternalFPGARetinaDevice.MODE_128,
#         'polarity': q.ExternalFPGARetinaDevice.MERGED_POLARITY}),
#     label='External retina')

# # FPGA Retina - Up Polarity
# retina_pop = p.Population(
#     None, q.ExternalFPGARetinaDevice, get_updated_params({
#         'mode': q.ExternalFPGARetinaDevice.MODE_128,
#         'polarity': q.ExternalFPGARetinaDevice.UP_POLARITY}),
#     label='External retina')

# FPGA Retina - Down Polarity
retina_pop = p.Population(
    None, q.ExternalFPGARetinaDevice, get_updated_params({
        'mode': q.ExternalFPGARetinaDevice.MODE_128,
        'polarity': q.ExternalFPGARetinaDevice.DOWN_POLARITY}),
    label='External retina')

population = p.Population(1024, p.IF_curr_exp, {}, label='pop_1')
p.Projection(retina_pop, population,
             p.FromListConnector(retina_lib.subSamplerConnector2D(
                 128, 32, 2.0, 1)))

q.activate_live_output_for(population)
p.run(1000)
