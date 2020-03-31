from easyvvuq.decoders.simple_csv import SimpleCSV
import os
import numpy as np
import pytest


@pytest.fixture
def decoder():
    return SimpleCSV('test.csv', output_columns=['Step', 'Value'])


def test_simple_csv(decoder):
    df = decoder.parse_sim_output({'run_dir': os.path.join('tests', 'simple_csv')})
    assert(df['Step'][1] == 1)
    assert(df['Value'][5] == 25.950662)


def test_get_restart_dict(decoder):
    restart_dict = decoder.get_restart_dict()
    assert(restart_dict['target_filename'] == 'test.csv')
    assert(restart_dict['output_columns'] == ['Step', 'Value'])
    assert(restart_dict['header'] == 0)


def test_sim_complete(decoder):
    assert(decoder.sim_complete({'run_dir': os.path.join('tests', 'simple_csv')}))
