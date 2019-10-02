import easyvvuq as uq
import chaospy as cp
import os
import sys
import pytest
from pprint import pformat, pprint
from gauss.encoder_gauss import GaussEncoder
from gauss.decoder_gauss import GaussDecoder
from dask.distributed import Client
from dask_jobqueue import SLURMCluster
import subprocess

__copyright__ = """

    Copyright 2018 Robin A. Richardson, David W. Wright

    This file is part of EasyVVUQ

    EasyVVUQ is free software: you can redistribute it and/or modify
    it under the terms of the Lesser GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    EasyVVUQ is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    Lesser GNU General Public License for more details.

    You should have received a copy of the Lesser GNU General Public License
    along with this program.  If not, see <https://www.gnu.org/licenses/>.

"""
__license__ = "LGPL"


def dask_execute():
    campaign = uq.CampaignDask(name='cannonsim', work_dir='.', db_type='sql')
    # Define parameter space for the cannonsim app
    params = {
        "angle": {
            "type": "float",
            "min": 0.0,
            "max": 6.28,
            "default": 0.79},
        "air_resistance": {
            "type": "float",
            "min": 0.0,
            "max": 1.0,
            "default": 0.2},
        "height": {
            "type": "float",
            "min": 0.0,
            "max": 1000.0,
            "default": 1.0},
        "time_step": {
            "type": "float",
            "min": 0.0001,
            "max": 1.0,
            "default": 0.01},
        "gravity": {
            "type": "float",
            "min": 0.0,
            "max": 1000.0,
            "default": 9.8},
        "mass": {
            "type": "float",
            "min": 0.0001,
            "max": 1000.0,
            "default": 1.0},
        "velocity": {
            "type": "float",
            "min": 0.0,
            "max": 1000.0,
            "default": 10.0}}

    # Create an encoder and decoder for the cannonsim app
    encoder = uq.encoders.GenericEncoder(
        template_fname='tests/cannonsim/test_input/cannonsim.template',
        delimiter='#',
        target_filename='in.cannon')
    decoder = uq.decoders.SimpleCSV(
        target_filename='output.csv', output_columns=[
            'Dist', 'lastvx', 'lastvy'], header=0)
    # Create a collation element for this campaign
    collater = uq.collate.AggregateSamples(average=False)
    actions = uq.actions.ExecuteLocal("/home/hpc/pn69ju/di73kuj2/cannonsim/bin/cannonsim in.cannon output.csv")
    campaign.add_app(name='cannonsim',
                     params=params,
                     encoder=encoder,
                     decoder=decoder,
                     collater=collater)
    stats = uq.analysis.BasicStats(qoi_cols=['Dist', 'lastvx', 'lastvy'])
    # Make a random sampler
    vary = {
        "angle": cp.Uniform(0.0, 1.0),
        "height": cp.Uniform(2.0, 10.0),
        "velocity": cp.Normal(10.0, 1.0),
        "mass": cp.Uniform(5.0, 1.0)
    }
    sampler = uq.sampling.RandomSampler(vary=vary)
    campaign.set_sampler(sampler)
    campaign.draw_samples(num_samples=56, replicas=1)
    cluster = SLURMCluster(job_extra=['--cluster=mpp2'], queue='mpp2_batch', cores=28, processes=28, memory='32 GB')
    print(cluster.job_script())
    cluster.scale(4)
    client = Client(cluster)
    campaign.populate_runs_dir()
    campaign.apply_for_each_run_dir(actions, client)
    campaign.collate()
    campaign.apply_analysis(stats)


if __name__ == '__main__':
    dask_execute()
