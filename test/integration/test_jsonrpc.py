import pytest
import sys
import os
import re
os.environ['SENTINEL_ENV'] = 'test'
os.environ['SENTINEL_CONFIG'] = os.path.normpath(os.path.join(os.path.dirname(__file__), '../test_sentinel.conf'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'lib'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
import config

from dynamicd import DynamicDaemon
from dynamic_config import DynamicConfig


def test_dynamicd():
    config_text = DynamicConfig.slurp_config_file(config.dynamic_conf)
    network = 'mainnet'
    is_testnet = False
    genesis_hash = u'0000fde3907194a0a6224ae29e069161e23cdff41a58f57c106a1e9e89ca1204'
    for line in config_text.split("\n"):
        if line.startswith('testnet=1'):
            network = 'testnet'
            is_testnet = True
            genesis_hash = u'000f5f5be1e3cbd87bfc3a7a154c29f6a74b1086ac74695c59e188df6b369fc0'

    creds = DynamicConfig.get_rpc_creds(config_text, network)
    dynamicd = DynamicDaemon(**creds)
    assert dynamicd.rpc_command is not None

    assert hasattr(dynamicd, 'rpc_connection')

    # Dynamic testnet block 0 hash == 0006dc5ab20561a3e49e112402beb5f451d7e82ce67f394c54480099dc241d88
    # test commands without arguments
    info = dynamicd.rpc_command('getinfo')
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
