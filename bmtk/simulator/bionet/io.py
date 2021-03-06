# Allen Institute Software License - This software license is the 2-clause BSD license plus clause a third
# clause that prohibits redistribution for commercial purposes without further permission.
#
# Copyright 2017. Allen Institute. All rights reserved.
#
# Redistribution and use in source and binary forms, with or without modification, are permitted provided that the
# following conditions are met:
#
# 1. Redistributions of source code must retain the above copyright notice, this list of conditions and the following
# disclaimer.
#
# 2. Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the following
# disclaimer in the documentation and/or other materials provided with the distribution.
#
# 3. Redistributions for commercial purposes are not permitted without the Allen Institute's written permission. For
# purposes of this license, commercial purposes is the incorporation of the Allen Institute's software into anything for
# which you will charge fees or other compensation. Contact terms@alleninstitute.org for commercial licensing
# opportunities.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES,
# INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
# SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY,
# WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
import pandas as pd
import time
import datetime
import os
import shutil
import json
import numpy as np
import logging
import h5py

from neuron import h

import bmtk.simulator.bionet.config as config
from bmtk.simulator.bionet import nrn


pc = h.ParallelContext()    # object to access MPI methods
MPI_Rank = int(pc.id())


def load_json(fullpath):
    """Tries to load a json file

    :param fullpath: path to file name to be loaded
    :return: json dictionary object
    """
    try:    
        with open(fullpath, 'r') as f:
            data = json.load(f)
            return data
    except IOError:
        print2log0("ERROR: cannot open {}".format(fullpath))
        nrn.quit_execution()


def load_h5(file_name):
    """load hdf5 file into memory

    :param file_name: full path to h5 file
    :return: file handle to hdf5 object
    """
    assert(os.path.exists(file_name))
    try:    
        data_handle = h5py.File(file_name, 'r')
        return data_handle
    except IOError:
        print2log0("ERROR: cannot open {}".format(file_name))
        nrn.quit_execution()


def load_csv(fullpath):
    """Load a csv file

    :param fullpath: path to the file name to be loaded
    :return: pandas dataframe
    """
    try:
        data = pd.read_csv(fullpath, sep=' ')
        return data
    except IOError:
        print2log0("ERROR: cannot open {}".format(fullpath))
        nrn.quit_execution()


def create_log(conf):
    logging.basicConfig(filename=conf["output"]["log_file"], level=logging.DEBUG)
    print2log0now('Created a log file')


def print2log(message):
    """Print statements to the log file from all processors"""
    delta_t = time.clock()
    full_string = '{}, t_wall: {} s'.format(message, str(delta_t))
    logging.info(full_string) 


def print2log0(string): 
    """Print from rank=0 only"""
    # CAUTION: NEURON's warning will not be save in either RUN_LOG or the log file created by the PBS.
    # To catch possible NEURON warnings, you need to use shell redirection, e.g.: $ python foo.py > file
    if int(pc.id()) == 0:
        delta_t = time.clock()
        # delta_t = timeit.default_timer()
        full_string = string + ' -- t_wall: %s s' % (str(delta_t))
        print(full_string)   # echo on the screen
        logging.info(full_string) 


def print2log0now(string):
    """Print from rank=0 only and report date,time"""
    if int(pc.id()) == 0:
        now = datetime.datetime.now()

        full_string = string + ' -- on %02d/%02d/%02d at %02d:%02d:%02d' % (now.year, now.month, now.day, now.hour, now.minute, now.second)
        print(full_string)   # echo on the screen
        logging.info(full_string) 


def extend_output_files(gids):
    # TODO: resize the files when running from an existing state
    pass


def create_output_files(simulator, gids):
    '''
    if simulator.calculate_ecp:  # creat single file for ecp from all contributing cells
        print2log0('    Will save time series of the ECP!')
        create_ecp_file(simulator)
    '''

    if simulator.cell_variables: # conf["run"]["save_cell_vars"]:
        print2log0('    Will save time series of individual cells')
        create_cell_vars_files(simulator, gids)
                
    # create_spike_file(simulator, gids)  # a single file including all gids
    

def create_cell_vars_files(simulator, gids):
    """create 1 hfd5 files per gid"""

    dt = simulator.dt # conf["run"]["dt"]
    tstop = simulator.tstop # conf["run"]["tstop"]

    nsteps = int(round(tstop/dt))

    for gid in gids["save_cell_vars"]:
        ofname = os.path.join(simulator.cell_var_output, '{}.h5'.format(gid))
        with h5py.File(ofname, 'w') as h5:
            h5.attrs['dt'] = dt
            h5.attrs['tstart'] = 0.0
            h5.attrs['tstop'] = tstop

            for var in simulator.cell_variables:
                h5.create_dataset(var, (nsteps,), maxshape=(None,), chunks=True)


def get_spike_trains_handle(file_name, trial_name):
    f5 = load_h5(file_name)
    spike_trains_handle = f5['processing/%s/spike_train' % trial_name]
    return spike_trains_handle


def setup_output_dir(conf):
    start_from_state =False
    if start_from_state:  # starting from a previously saved state
        try:
            assert os.path.exists(conf["output"]["output_dir"])
            print2log0('Will run simulation from a previously saved state...')
        except:
            print('ERROR: directory with the initial state does not exist')
            nrn.quit_execution()

    elif not start_from_state:  # starting from a new (init) state
        if int(pc.id()) == 0:
            if os.path.exists(conf["output"]["output_dir"]):
                if conf["run"]['overwrite_output_dir']:
                    shutil.rmtree(conf["output"]["output_dir"])
                    print('Overwriting the output directory %s:' %conf["output"]["output_dir"]) # must print to stdout because the log file is not created yet
                else:
                    print('ERROR: Directory already exists')
                    print("To overwrite existing output_dir set 'overwrite_output_dir': True")
                    nrn.quit_execution()

            os.makedirs(conf["output"]["output_dir"])
            os.makedirs(conf["output"]["cell_vars_dir"])

            create_log(conf)
            config.copy(conf)

        pc.barrier()

    print2log0('Output directory: %s' % conf["output"]["output_dir"])
    print2log0('Config file: %s' % conf["config_path"])


def save_state(conf):
    state = h.SaveState()
    state.save()

    state_dir = conf["output"]["state_dir"]
    f = h.File('{}/state_rank-{}'.format(state_dir, int(pc.id())))
    # f = h.File(state_dir + '/state_rank-%d' % (int(pc.id())))
    state.fwrite(f, 0)
    rlist = h.List('Random')
    for r_tmp in rlist:
        f.printf('%g\n', r_tmp.seq())
    f.close()


def read_state(conf):
    state_dir = conf["output"]["state_dir"]

    state = h.SaveState()
    f = h.File('{}/state_rank-{}'.format(state_dir, int(pc.id())))
    # f = h.File(state_dir+'/state_rank-%d' % (int(pc.id())))
    state.fread(f, 0)
    state.restore()
    rlist = h.List('Random')
    for r_tmp in rlist:
        r_tmp.seq(f.scanvar())
    f.close()
