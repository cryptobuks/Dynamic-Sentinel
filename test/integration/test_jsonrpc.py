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
    creds = DarkSilkConfig.get_rpc_creds(config_text, 'mainnet')

    darksilkd = DarkSilkDaemon(**creds)
    assert darksilkd.rpc_command is not None

    assert hasattr(darksilkd, 'rpc_connection')

    # DarkSilk testnet block 0 hash == 0000b0f60bd743b8b5ed3e62a1fbad5d2c073d2b9cb3baa108872dbe1315e48e
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
    assert info['mainnet'] is True

    # test commands with args
    assert darksilkd.rpc_command('getblockhash', 0) == u'0000b0f60bd743b8b5ed3e62a1fbad5d2c073d2b9cb3baa108872dbe1315e48e'
