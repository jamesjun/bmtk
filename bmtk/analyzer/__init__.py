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

import os
import h5py
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

import bmtk.simulator.utils.config as cfg


def _get_config(config):
    if isinstance(config, basestring):
        return cfg.from_json(config)
    elif isinstance(config, dict):
        return config
    else:
        raise Exception('Could not convert {} (type "{}") to json.'.format(config, type(config)))

def plot_potential(cell_vars_h5=None, config_file=None, gids=None, show_plot=True, save=False):
    if (cell_vars_h5 or config_file) is None:
        raise Exception('Please specify a cell_vars hdf5 file or a simulation config.')

    if cell_vars_h5 is not None:
        plot_potential_hdf5(cell_vars_h5, show_plot, save_as='sim_potential.jpg' if save else None)

    else:
        # load the json file or object
        if isinstance(config_file, basestring):
            config = cfg.from_json(config_file)
        elif isinstance(config_file, dict):
            config = config_file
        else:
            raise Exception('Could not convert {} (type "{}") to json.'.format(config_file, type(config_file)))

        gid_list = gids or config['node_id_selections']['save_cell_vars']
        for gid in gid_list:
            save_as = '{}_v.jpg'.format(gid) if save else None
            title = 'cell gid {}'.format(gid)
            var_h5 = os.path.join(config['output']['cell_vars_dir'], '{}.h5'.format(gid))
            plot_potential_hdf5(var_h5, title, show_plot, save_as)


def plot_potential_hdf5(cell_vars_h5, title='membrane potential', show_plot=True, save_as=None):
    data_h5 = h5py.File(cell_vars_h5, 'r')
    membrane_trace = data_h5['v']

    tstart = data_h5.attrs['tstart']
    tstop = data_h5.attrs['tstop']
    x_axis = np.linspace(tstart, tstop, len(membrane_trace), endpoint=True)

    plt.plot(x_axis, membrane_trace)
    plt.xlabel('time (ms)')
    plt.ylabel('membrane (mV)')
    plt.title(title)

    if save_as is not None:
        plt.savefig(save_as)

    if show_plot:
        plt.show()


def plot_calcium(cell_vars_h5=None, config_file=None, gids=None, show_plot=True, save=False):
    if (cell_vars_h5 or config_file) is None:
        raise Exception('Please specify a cell_vars hdf5 file or a simulation config.')

    if cell_vars_h5 is not None:
        plot_calcium_hdf5(cell_vars_h5, show_plot, save_as='sim_ca.jpg' if save else None)

    else:
        # load the json file or object
        if isinstance(config_file, basestring):
            config = cfg.from_json(config_file)
        elif isinstance(config_file, dict):
            config = config_file
        else:
            raise Exception('Could not convert {} (type "{}") to json.'.format(config_file, type(config_file)))

        gid_list = gids or config['node_id_selections']['save_cell_vars']
        for gid in gid_list:
            save_as = '{}_v.jpg'.format(gid) if save else None
            title = 'cell gid {}'.format(gid)
            var_h5 = os.path.join(config['output']['cell_vars_dir'], '{}.h5'.format(gid))
            plot_calcium_hdf5(var_h5, title, show_plot, save_as)


def plot_calcium_hdf5(cell_vars_h5, title='Ca2+ influx', show_plot=True, save_as=None):
    data_h5 = h5py.File(cell_vars_h5, 'r')
    cai_trace = data_h5['cai']

    tstart = data_h5.attrs['tstart']
    tstop = data_h5.attrs['tstop']
    x_axis = np.linspace(tstart, tstop, len(cai_trace), endpoint=True)

    plt.plot(x_axis, cai_trace)
    plt.xlabel('time (ms)')
    plt.ylabel('calcium [Ca2+]')
    plt.title(title)

    if save_as is not None:
        plt.savefig(save_as)

    if show_plot:
        plt.show()


def spikes_table(config_file):
    config = _get_config(config_file)
    spikes_ascii = config['output']['spikes_ascii_file']
    return pd.read_csv(spikes_ascii, names=['time (ms)', 'cell gid'], sep=' ')