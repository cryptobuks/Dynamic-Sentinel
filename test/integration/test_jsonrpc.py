import pytest
import sys
import os
import re
os.environ['SENTINEL_ENV'] = 'test'
os.environ['SENTINEL_CONFIG'] = os.path.normpath(os.path.join(os.path.dirname(__file__), '../test_sentinel.conf'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'lib'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
import config

from darksilkd import DarkSilkDaemon
from darksilk_config import DarkSilkConfig


def test_darksilkd():
    config_text = DarkSilkConfig.slurp_config_file(config.darksilk_conf)
    network = 'mainnet'
    is_testnet = False
    genesis_hash = u'00002bf2d43a0aaeb5bdffe37516fcdf37b16921e6a094a38d6aa7c6109ca9be'
    for line in config_text.split("\n"):
        if line.startswith('testnet=1'):
            network = 'testnet'
            is_testnet = True
            genesis_hash = u'000d3939a4eacb52b654cb2d3776c820c0694f3fa8294921417c8baf55360808'

    creds = DarkSilkConfig.get_rpc_creds(config_text, network)
    darksilkd = DarkSilkDaemon(**creds)
    assert darksilkd.rpc_command is not None

    assert hasattr(darksilkd, 'rpc_connection')

    # DarkSilk testnet block 0 hash == 0006dc5ab20561a3e49e112402beb5f451d7e82ce67f394c54480099dc241d88
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
    assert info['testnet'] is is_testnet

    # test commands with args
    assert dashd.rpc_command('getblockhash', 0) == genesis_hash
