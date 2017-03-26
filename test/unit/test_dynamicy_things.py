import pytest
import sys
import os
os.environ['SENTINEL_CONFIG'] = os.path.normpath(os.path.join(os.path.dirname(__file__), '../test_sentinel.conf'))
sys.path.append(os.path.normpath(os.path.join(os.path.dirname(__file__), '../../lib')))


@pytest.fixture
def valid_dynamic_address(network='mainnet'):
    return 'yYe8KwyaUu5YswSYmB3q3ryx8XTUu9y7Ui' if (network == 'testnet') else 'XpjStRH8SgA6PjgebtPZqCa9y7hLXP767n'


@pytest.fixture
def invalid_dynamic_address(network='mainnet'):
    return 'yYe8KwyaUu5YswSYmB3q3ryx8XTUu9y7Uj' if (network == 'testnet') else 'XpjStRH8SgA6PjgebtPZqCa9y7hLXP767m'


@pytest.fixture
def current_block_hash():
    return '000001c9ba1df5a1c58a4e458fb6febfe9329b1947802cd60a4ae90dd754b534'


@pytest.fixture
def dn_list():
    from dynode import Dynode

    dynodelist_full = {
        u'701854b26809343704ab31d1c45abc08f9f83c5c2bd503a9d5716ef3c0cda857-1': u'  ENABLED 70201 yjaFS6dudxUTxYPTDB9BYd1Nv4vMJXm3vK 1474157572    82842 1474152618  71111 52.90.74.124:19999',
        u'f68a2e5d64f4a9be7ff8d0fbd9059dcd3ce98ad7a19a9260d1d6709127ffac56-1': u'  ENABLED 70201 yUuAsYCnG5XrjgsGvRwcDqPhgLUnzNfe8L 1474157732  1590425 1474155175  71122 [2604:a880:800:a1::9b:0]:19999',
        u'656695ed867e193490261bea74783f0a39329ff634a10a9fb6f131807eeca744-1': u'  ENABLED 70201 yepN97UoBLoP2hzWnwWGRVTcWtw1niKwcB 1474157704   824622 1474152571  71110 178.62.203.249:19999',
    }

    dnlist = [Dynode(vin, dnstring) for (vin, dnstring) in dynodelist_full.items()]

    return dnlist


@pytest.fixture
def dn_status_good():
    # valid dynode status enabled & running
    status = {
        "vin": "CTxIn(COutPoint(f68a2e5d64f4a9be7ff8d0fbd9059dcd3ce98ad7a19a9260d1d6709127ffac56, 1), scriptSig=)",
        "service": "[2604:a880:800:a1::9b:0]:19999",
        "pubkey": "yUuAsYCnG5XrjgsGvRwcDqPhgLUnzNfe8L",
        "status": "Dynode successfully started"
    }
    return status


@pytest.fixture
def dn_status_bad():
    # valid dynode but not running/waiting
    status = {
        "vin": "CTxIn(COutPoint(0000000000000000000000000000000000000000000000000000000000000000, 4294967295), coinbase )",
        "service": "[::]:0",
        "status": "Node just started, not yet activated"
    }
    return status


# ========================================================================


def test_valid_dynamic_address():
    from dynamiclib import is_valid_dynamic_address

    main = valid_dynamic_address()
    test = valid_dynamic_address('testnet')

    assert is_valid_dynamic_address(main) is True
    assert is_valid_dynamic_address(main, 'mainnet') is True
    assert is_valid_dynamic_address(main, 'testnet') is False

    assert is_valid_dynamic_address(test) is False
    assert is_valid_dynamic_address(test, 'mainnet') is False
    assert is_valid_dynamic_address(test, 'testnet') is True


def test_invalid_dynamic_address():
    from dynamiclib import is_valid_dynamic_address

    main = invalid_dynamic_address()
    test = invalid_dynamic_address('testnet')

    assert is_valid_dynamic_address(main) is False
    assert is_valid_dynamic_address(main, 'mainnet') is False
    assert is_valid_dynamic_address(main, 'testnet') is False

    assert is_valid_dynamic_address(test) is False
    assert is_valid_dynamic_address(test, 'mainnet') is False
    assert is_valid_dynamic_address(test, 'testnet') is False


def test_deterministic_dynode_elections(current_block_hash, dn_list):
    winner = elect_dn(block_hash=current_block_hash, dnlist=dn_list)
    assert winner == 'f68a2e5d64f4a9be7ff8d0fbd9059dcd3ce98ad7a19a9260d1d6709127ffac56-1'

    winner = elect_dn(block_hash='00000056bcd579fa3dc9a1ee41e8124a4891dcf2661aa3c07cc582bfb63b52b9', dnlist=dn_list)
    assert winner == '656695ed867e193490261bea74783f0a39329ff634a10a9fb6f131807eeca744-1'


def test_deterministic_dynode_elections(current_block_hash, dn_list):
    from dynamiclib import elect_dn

    winner = elect_dn(block_hash=current_block_hash, dnlist=dn_list)
    assert winner == 'f68a2e5d64f4a9be7ff8d0fbd9059dcd3ce98ad7a19a9260d1d6709127ffac56-1'

    winner = elect_dn(block_hash='00000056bcd579fa3dc9a1ee41e8124a4891dcf2661aa3c07cc582bfb63b52b9', dnlist=dn_list)
    assert winner == '656695ed867e193490261bea74783f0a39329ff634a10a9fb6f131807eeca744-1'


def test_parse_dynode_status_vin():
    from dynamiclib import parse_dynode_status_vin
    status = dn_status_good()
    vin = parse_dynode_status_vin(status['vin'])
    assert vin == 'f68a2e5d64f4a9be7ff8d0fbd9059dcd3ce98ad7a19a9260d1d6709127ffac56-1'

    status = dn_status_bad()
    vin = parse_dynode_status_vin(status['vin'])
    assert vin is None


def test_hash_function():
    import dynamiclib
    sb_data_hex = '5b227375706572626c6f636b222c207b226576656e745f626c6f636b5f686569676874223a2037323639362c20227061796d656e745f616464726573736573223a2022795965384b77796155753559737753596d42337133727978385854557539793755697c795965384b77796155753559737753596d4233713372797838585455753979375569222c20227061796d656e745f616d6f756e7473223a202232352e37353030303030307c32352e3735303030303030227d5d'
    sb_hash = '5c7c28ddec8c1ad54b49f6f1e79369e7ccaf76f5ddc30e502569d674e458ccf3'

    hex_hash = "%x" % dynamiclib.hashit(sb_data_hex)
    assert hex_hash == sb_hash
