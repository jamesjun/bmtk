# -*- coding: utf-8 -*-

"""Simulates an example network of 14 cell receiving two kinds of exernal input as defined in configuration file"""


import sys, os
import h5py
import numpy as np
from numpy.random import randint

import bmtk.simulator.bionet.config as config
from bmtk.simulator.bionet import io, nrn
from bmtk.simulator.bionet.simulation import Simulation
from bmtk.analyzer.spikes_analyzer import spike_files_equal
from bmtk.simulator.bionet.biograph import BioGraph
from bmtk.simulator.bionet.bionetwork import BioNetwork

from bmtk.utils.io import TabularNetwork_AI
from bmtk.simulator.bionet.property_schemas import AIPropertySchema


import set_weights
import set_cell_params
import set_syn_params


def run(config_file):
    conf = config.from_json(config_file)        # build configuration
    io.setup_output_dir(conf)                   # set up output directories
    nrn.load_neuron_modules(conf)               # load NEURON modules and mechanisms
    nrn.load_py_modules(cell_models=set_cell_params,  # load custom Python modules
                        syn_models=set_syn_params,
                        syn_weights=set_weights)

    graph = BioGraph.from_config(conf,  # create network graph containing parameters of the model
                                 network_format=TabularNetwork_AI,
                                 property_schema=AIPropertySchema)

    net = BioNetwork.from_config(conf, graph)   # create netwosim = Simulation.from_config(conf, network=net)  rk of in NEURON
    sim = Simulation.from_config(conf, network=net)         # initialize a simulation
    # sim.set_recordings()                        # set recordings of relevant variables to be saved as an ouput
    sim.run()                                   # run simulation

    assert (os.path.exists(conf['output']['spikes_ascii_file']))
    assert (spike_files_equal(conf['output']['spikes_ascii_file'], 'expected/spikes.txt'))

    # Test the results of the ecp
    SAMPLE_SIZE = 100
    expected_h5 = h5py.File('expected/ecp.h5', 'r')
    nrows, ncols = expected_h5['ecp'].shape
    expected_mat = np.matrix(expected_h5['ecp'])
    results_h5 = h5py.File('output/ecp.h5', 'r')
    assert ('ecp' in results_h5.keys())
    results_mat = np.matrix(results_h5['ecp'][:])

    assert (results_h5['ecp'].shape == (nrows, ncols))
    for i, j in zip(randint(0, nrows, size=SAMPLE_SIZE), randint(0, ncols, size=SAMPLE_SIZE)):
        assert (results_mat[i, j] == expected_mat[i, j])

    nrn.quit_execution()                        # exit


if __name__ == '__main__':
    if __file__ != sys.argv[-1]:
        run(sys.argv[-1])
    else:
        run('config.json')
