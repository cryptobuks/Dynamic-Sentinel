import pytest
import os
import sys
import re

os.environ['SENTINEL_ENV'] = 'test'
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'lib'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

import config
from darksilk_config import DarkSilkConfig

@pytest.fixture
def darksilk_conf(**kwargs):
    defaults = {
        'rpcuser': 'darksilkrpc',
        'rpcpassword': 'EwJeV3fZTyTVozdECF627BkBMnNDwQaVLakG3A4wXYyk',
        'rpcport': 29241,
    }

    # merge kwargs into defaults
    for (key, value) in kwargs.items():
        defaults[key] = value

    conf = """# basic settings
testnet=1 # TESTNET
server=1
rpcuser={rpcuser}
rpcpassword={rpcpassword}
rpcallowip=127.0.0.1
rpcport={rpcport}
""".format(**defaults)

    return conf

def test_get_rpc_creds():
    darksilk_config = darksilk_conf()
    creds = DarkSilkConfig.get_rpc_creds(darksilk_config, 'testnet')

    for key in ('user', 'password', 'port'):
        assert key in creds
    assert creds.get('user') == 'darksilkrpc'
    assert creds.get('password') == 'EwJeV3fZTyTVozdECF627BkBMnNDwQaVLakG3A4wXYyk'
    assert creds.get('port') == 29241

    darksilk_config = darksilk_conf(rpcpassword='s00pers33kr1t', rpcport=8000)
    creds = DarkSilkConfig.get_rpc_creds(darksilk_config, 'testnet')

    for key in ('user', 'password', 'port'):
        assert key in creds
    assert creds.get('user') == 'darksilkrpc'
    assert creds.get('password') == 's00pers33kr1t'
    assert creds.get('port') == 8000

    no_port_specified = re.sub('\nrpcport=.*?\n', '\n', darksilk_conf(), re.M)
    creds = DarkSilkConfig.get_rpc_creds(no_port_specified, 'testnet')

    for key in ('user', 'password', 'port'):
        assert key in creds
    assert creds.get('user') == 'darksilkrpc'
    assert creds.get('password') == 'EwJeV3fZTyTVozdECF627BkBMnNDwQaVLakG3A4wXYyk'
    assert creds.get('port') == 31750


# ensure darksilk network (mainnet, testnet) matches that specified in config
# requires running darksilkd on whatever port specified...
#
# This is more of a darksilkd/jsonrpc test than a config test...
