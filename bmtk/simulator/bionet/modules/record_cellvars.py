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
import numpy as np
import h5py

from bmtk.simulator.bionet.modules.sim_module import SimulatorMod


class CellVarsMod(SimulatorMod):
    def __init__(self, outputdir, variables):
        """Module used for saving NEURON cell properities at each given step of the simulation.

        :param outputdir: directory where variables will be saved to.
        :param variables: list of NEURON variables (strings) to collect and save each step
        """
        self._cell_vars = variables
        self._outputdir = outputdir

        self._gid_list = []  # list of all gids that will have their variables saved
        self._data_block = {}  # table of variable data indexed by [gid][variable]
        self._block_step = 0  # time step within a given block

    def _get_filename(self, gid):
        return os.path.join(self._outputdir, '{}.h5'.format(gid))

    def initialize(self, sim):
        # get list of gids to save. Will only work for biophysical cells saved on the current MPI rank
        self._gid_list = list(set(sim.gids['biophysical']) & set(sim.gids['save_cell_vars']))

        # preallocate block data for saving variables
        self._data_block = {gid: {v: np.zeros(sim.nsteps_block) for v in self._cell_vars} for gid in self._gid_list}

        # Create files for saving variables
        for gid in self._gid_list:
            with h5py.File(self._get_filename(gid), 'w') as h5:
                h5.attrs['dt'] = sim.dt
                h5.attrs['tstart'] = 0.0
                h5.attrs['tstop'] = sim.tstop

                for v in self._cell_vars:
                    h5.create_dataset(v, (sim.n_steps,), chunks=True)

    def step(self, sim, tstep, rel_time=0.0):
        # save all necessary cells/variables at the current time-step into memory
        for gid in self._gid_list:
            cell = sim.net.cells[gid]
            for variable, data_block in self._data_block[gid].items():
                data_block[self._block_step] = getattr(cell.hobj.soma[0](0.5), variable)

        self._block_step += 1

    def block(self, sim, block_interval):
        # write variables in memory to file
        itstart, itend = block_interval
        # TODO: keep a reference to the hdf5 file instead of opening it on every block
        for gid, var_table in self._data_block.items():
            with h5py.File(self._get_filename(gid), 'a') as h5:
                for var_name, var_data in var_table.items():
                    h5[var_name][itstart:itend] = var_data[0:(itend-itstart)]
                    self._data_block[gid][var_name][:] = 0.0  # np.zeros(sim.nsteps_block)

        self._block_step = 0

    def finalize(self, sim):
        if self._block_step > 0:
            # just in case the simulation doesn't end on a block step
            self.block(sim, (sim.n_steps - self._block_step, sim.n_steps))
