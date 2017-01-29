import pytest
import sys
import os
import re

os.environ['SENTINEL_ENV'] = 'test'
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'lib'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
import config

from darksilkd import DarkSilkDaemon
from darksilk_config import DarkSilkConfig


def test_darksilkd():
    config_text = DarkSilkConfig.slurp_config_file(config.darksilk_conf)
    creds = DarkSilkConfig.get_rpc_creds(config_text, 'testnet')

    darksilkd = DarkSilkDaemon(**creds)
    assert darksilkd.rpc_command is not None

    assert hasattr(darksilkd, 'rpc_connection')

    # DarkSilk testnet block 0 hash == 00000bafbc94add76cb75e2ec92894837288a481e5c005f6563d91623bf8bc2c
    # test commands without arguments
    info = darksilkd.rpc_command('getinfo')

    info_keys = [
        'blocks',
        'connections',
        'difficulty',
        'errors',
        'protocolversion',
        'proxy',
        'testnet',
        'timeoffset',
        'version',
    ]
    for key in info_keys:
        assert key in info
    assert info['testnet'] is True

    # test commands with args
    assert darksilkd.rpc_command('getblockhash', 0) == u'00000bafbc94add76cb75e2ec92894837288a481e5c005f6563d91623bf8bc2c'