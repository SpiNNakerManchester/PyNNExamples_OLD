"""
LOG:7th August 2015.

-------------------_________________********************____________________--------------------
-------------------_________________********************____________________--------------------
OLD LOG:
-------------------_________________********************____________________--------------------
(A single IZK neuron with exponential, conductance-based synapses, fed by two
spike sources.

Run as:

$ python IZK_cond_exp.py <simulator>

where <simulator> is 'neuron', 'nest', etc

Originally for LIF neuron (Andrew Davison, UNIC, CNRS), adapted for Izhikevich neuron on SpiNNaker
May 2006

Expected result can be found in:
  .. figure::  ./examples/results/IZK_cond_exp.png

$Id: IF_cond_exp.py 917 2011-01-31 15:23:34Z apdavison $)
"""

#!/usr/bin/python

from pyNN.random import NumpyRNG, RandomDistribution
import numpy, pylab

#simulator_name = 'spiNNaker'
#exec("import pyNN.%s as p" % simulator_name)
import spynnaker.pyNN as p

p.setup(timestep=1.0,min_delay=1.0,max_delay=100.0)
p.set_number_of_neurons_per_core('IZK_curr_exp',100)

#*****SOME CONSTANT INPUTS**************

scale_fact=10


#***********************THALAMIC CELLS***************************************
# TCR cells are in a tonic spiking mode, which is 'RS' mode, when the membrane potential is -60mV
TCR_cell_params = {   'a'      : 0.02, 'b'    : 0.2, 'c' : -65,   'd'    : 6,
                'v_init'   : -65,'u_init'   : -14,
                'tau_syn_E'   : 5, 'tau_syn_I'   : 6,
              'i_offset': 9
                }

## INHIBITION INDUCED BURSTING MODE OF THE TCR CELLS

#TCR_cell_params = {   'a'      : -0.026, 'b'    : -1, 'c' : -45,   'd'    : 0,
#                'v_init'   : -63.8,'u_init'   : 0,
#                'tau_syn_E'   : 5, 'tau_syn_I'   : 6,
#                'i_offset': 80
#                }


# IN cells are set as FS type
IN_cell_params = {   'a'      : 0.1, 'b'    : 0.2, 'c' : -75,   'd'    : 6,
                'v_init'   : -75,'u_init'   : -16,
                'tau_syn_E'   : 5, 'tau_syn_I'   : 6,
                'i_offset': 0
                }
# TRN cells are set as tonic bursting.
TRN_cell_params = {   'a'      : 0.02, 'b'    : 0.25, 'c' : -50,   'd'    : 2,
                'v_init'   : -70,'u_init'   : -16,
                'tau_syn_E'   : 5, 'tau_syn_I'   : 6,
                'i_offset': 10
                }

###***** THALAMIC MICRO COLUMN: APPROX 90 NEURONS*****

##******************************CELLS OF THE LATERAL GENICULATE NUCLEUS************************

TCR_pop = p.Population(4*scale_fact, p.IZK_curr_exp, TCR_cell_params, label='TCR_pop')
TRN_pop =   p.Population(4*scale_fact, p.IZK_curr_exp, TRN_cell_params, label='TRN_pop')
IN_pop = p.Population(1*scale_fact, p.IZK_curr_exp, IN_cell_params, label='IN_pop')

Rate_Inp=20
duration=500
start_time=250

#****EXTERNAL INPUT TO THE THALAMIC CELLS************************************
spike_sourceE_ret2tcr = p.Population(4*scale_fact, p.SpikeSourcePoisson, {'rate':Rate_Inp, 'duration':duration,'start':start_time}, label='spike_sourceE_ret2tcr')
spike_sourceE_ret2in = p.Population(1*scale_fact, p.SpikeSourcePoisson, {'rate': Rate_Inp, 'duration':duration,'start':start_time}, label='spike_sourceE_ret2in')

# random distributions
rng = NumpyRNG(seed=28374)
delay_distr = RandomDistribution('normal', [100,20], rng=rng)
thalamic_delay_distr= 1;##RandomDistribution('normal', [100,20], rng=rng)
#pconn=0.75
weights=1;


for var in range(1,5):

    proj_retTOtcr = p.Projection(spike_sourceE_ret2tcr, TCR_pop, p.FixedProbabilityConnector(p_connect=0.5, weights=var, delays=1), target='excitatory')
    proj_retTOin = p.Projection(spike_sourceE_ret2in, IN_pop, p.FixedProbabilityConnector(p_connect=0.15, weights=weights, delays=1), target='excitatory')

    #********************** EFFERENTS AND AFFERENTS OF THE TCR CELLS FROM OTHER THALAMOCORTICAL CELLS*******************
    proj_tcrTOtrn = p.Projection(TCR_pop, TRN_pop, p.FixedProbabilityConnector(p_connect=0.2,weights=weights, delays=thalamic_delay_distr), target='excitatory')

    #********************** EFFERENTS AND AFFERENTS OF THE IN CELLS FROM OTHER THALAMOCORTICAL CELLS*******************
    proj_inTOtcr = p.Projection(IN_pop, TCR_pop, p.FixedProbabilityConnector(p_connect=0.47,weights=weights, delays=thalamic_delay_distr), target='inhibitory')
    proj_inTOin = p.Projection(IN_pop, IN_pop, p.FixedProbabilityConnector(p_connect=0.3,weights=weights, delays=thalamic_delay_distr), target='inhibitory')


    #********************** EFFERENTS AND AFFERENTS OF THE TRN CELLS FROM OTHER THALAMOCORTICAL CELLS*******************
    proj_trnTOtcr = p.Projection(TRN_pop, TCR_pop, p.FixedProbabilityConnector(p_connect=0.47,weights=weights, delays=thalamic_delay_distr), target='inhibitory')
    proj_trnTOtrn = p.Projection(TRN_pop, TRN_pop, p.FixedProbabilityConnector(p_connect=0.47,weights=weights, delays=thalamic_delay_distr), target='inhibitory')


    #Recording membrane potential
    TCR_pop.record_v()
    IN_pop.record_v()
    TRN_pop.record_v()


    #recording spike populations
    spike_sourceE_ret2tcr.record()
    spike_sourceE_ret2in.record()
    TCR_pop.record()
    IN_pop.record()
    TRN_pop.record()

    p.run(1000) #end of simulation
    print 'Current value :', var
    TCR_pop.print_v('./Results/TCR_pop.dat')
    IN_pop.print_v('./Results/IN_pop.dat')
    TRN_pop.print_v('./Results/TRN_pop.dat')
    p.end()
##***********VISUALISING AND STORING DATA************

##  RASTER PLOT FOR SPIKES
#### CAN WE PLOT ALL OF THESE AS SUBFIGURES ON A SINGLE WINDOW?

####data = numpy.asarray(spike_sourceE_ret2tcr.getSpikes())
####if len(data) > 0:
####    pylab.scatter(data[:,1], data[:,0], color='red', s=1)
####    spikes = spike_sourceE_ret2tcr.getSpikes()
####    spike_file = open('./spike_sourceE_ret2tcr.spikes', "w")
####    for (neuronId, time) in spikes:
####        spike_file.write("%f\t%d\n" % (time, neuronId))
####    spike_file.close()
####    pylab.show()
####
####data = numpy.asarray(spike_sourceE_ret2in.getSpikes())
####if len(data) > 0:
####    pylab.scatter(data[:,1], data[:,0], color='red', s=1)
####    spikes = spike_sourceE_ret2in.getSpikes()
####    spike_file = open('./spike_sourceE_ret2in.spikes', "w")
####    for (neuronId, time) in spikes:
####        spike_file.write("%f\t%d\n" % (time, neuronId))
####    spike_file.close()
####    pylab.show()
####
####data = numpy.asarray(TCR_pop.getSpikes())
####if len(data) > 0:
####    pylab.scatter(data[:,1], data[:,0], color='red', s=1)
####    spikes = TCR_pop.getSpikes()
####    spike_file = open('./TCR_pop.spikes', "w")
####    for (neuronId, time) in spikes:
####        spike_file.write("%f\t%d\n" % (time, neuronId))
####    spike_file.close()
####    pylab.show()
####
####data = numpy.asarray(IN_pop.getSpikes())
####if len(data) > 0:
####    pylab.scatter(data[:,1], data[:,0], color='red', s=1)
####    spikes = IN_pop.getSpikes()
####    spike_file = open('./IN_pop.spikes', "w")
####    for (neuronId, time) in spikes:
####        spike_file.write("%f\t%d\n" % (time, neuronId))
####    spike_file.close()
####    pylab.show()
####
####data = numpy.asarray(TRN_pop.getSpikes())
####if len(data) > 0:
####    pylab.scatter(data[:,1], data[:,0], color='red', s=1)
####    spikes = TRN_pop.getSpikes()
####    spike_file = open('./TRN_pop.spikes', "w")
####    for (neuronId, time) in spikes:
####        spike_file.write("%f\t%d\n" % (time, neuronId))
####    spike_file.close()
####    pylab.show()
####
####
######TCR_pop.print_v('./Results/TCR_pop.dat')
######IN_pop.print_v('./Results/IN_pop.dat')
######TRN_pop.print_v('./Results/TRN_pop.dat')
####
####
####p.end()