"""
dynamicd JSONRPC interface
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'lib'))
import config
import base58
from bitcoinrpc.authproxy import AuthServiceProxy, JSONRPCException
from dynode import Dynode
from decimal import Decimal
import time


class DynamicDaemon():
    def __init__(self, **kwargs):
        host = kwargs.get('host', '127.0.0.1')
        user = kwargs.get('user')
        password = kwargs.get('password')
        port = kwargs.get('port')

        self.creds = (user, password, host, port)

        # memoize calls to some dynamicd methods
        self.governance_info = None
        self.gobject_votes = {}

    @property
    def rpc_connection(self):
        return AuthServiceProxy("http://{0}:{1}@{2}:{3}".format(*self.creds))

    @classmethod
    def from_dynamic_conf(self, dynamic_dot_conf):
        from dynamic_config import DynamicConfig
        config_text = DynamicConfig.slurp_config_file(dynamic_dot_conf)
        creds = DynamicConfig.get_rpc_creds(config_text, config.network)

        return self(**creds)

    def rpc_command(self, *params):
        return self.rpc_connection.__getattr__(params[0])(*params[1:])

    # common RPC convenience methods
    def is_testnet(self):
        return self.rpc_command('getinfo')['testnet']

    def get_dynodes(self):
        dnlist = self.rpc_command('dynodelist', 'full')
        return [Dynode(k, v) for (k, v) in dnlist.items()]

    def get_object_list(self):
        try:
            golist = self.rpc_command('gobject', 'list')
        except JSONRPCException as e:
            golist = self.rpc_command('dnbudget', 'show')
        return golist

    def get_current_dynode_vin(self):
        from dynamiclib import parse_dynode_status_vin

        my_vin = None

        try:
            status = self.rpc_command('dynode', 'status')
            my_vin = parse_dynode_status_vin(status['vin'])
        except JSONRPCException as e:
            pass

        return my_vin

    def governance_quorum(self):
        # TODO: expensive call, so memoize this
        total_dynodes = self.rpc_command('dynode', 'count', 'enabled')
        min_quorum = self.govinfo['governanceminquorum']

        # the minimum quorum is calculated based on the number of dynodes
        quorum = max(min_quorum, (total_dynodes // 10))
        return quorum

    @property
    def govinfo(self):
        if (not self.governance_info):
            self.governance_info = self.rpc_command('getgovernanceinfo')
        return self.governance_info

    # governance info convenience methods
    def superblockcycle(self):
        return self.govinfo['superblockcycle']

    def governanceminquorum(self):
        return self.govinfo['governanceminquorum']

    def proposalfee(self):
        return self.govinfo['proposalfee']

    def last_superblock_height(self):
        height = self.rpc_command('getblockcount')
        cycle = self.superblockcycle()
        return cycle * (height // cycle)

    def next_superblock_height(self):
        return self.last_superblock_height() + self.superblockcycle()

    def is_dynode(self):
        return not (self.get_current_dynode_vin() is None)

    def is_synced(self):
        dnsync_status = self.rpc_command('dnsync', 'status')
        synced = (dnsync_status['IsBlockchainSynced'] and
                  dnsync_status['IsDynodeListSynced'] and
                  dnsync_status['IsWinnersListSynced'] and
                  dnsync_status['IsSynced'] and
                  not dnsync_status['IsFailed'])
        return synced

    def current_block_hash(self):
        height = self.rpc_command('getblockcount')
        block_hash = self.rpc_command('getblockhash', height)
        return block_hash

    def get_superblock_budget_allocation(self, height=None):
        if height is None:
            height = self.rpc_command('getblockcount')
        return Decimal(self.rpc_command('getsuperblockbudget', height))

    def next_superblock_max_budget(self):
        cycle = self.superblockcycle()
        current_block_height = self.rpc_command('getblockcount')

        last_superblock_height = (current_block_height // cycle) * cycle
        next_superblock_height = last_superblock_height + cycle

        last_allocation = self.get_superblock_budget_allocation(last_superblock_height)
        next_allocation = self.get_superblock_budget_allocation(next_superblock_height)

        next_superblock_max_budget = next_allocation

        return next_superblock_max_budget

    # "my" votes refers to the current running dynode
    # memoized on a per-run, per-object_hash basis
    def get_my_gobject_votes(self, object_hash):
        import dynamiclib
        if not self.gobject_votes.get(object_hash):
            my_vin = self.get_current_dynode_vin()
            # if we can't get DN vin from output of `dynode status`,
            # return an empty list
            if not my_vin:
                return []

            (txid, vout_index) = my_vin.split('-')

            cmd = ['gobject', 'getcurrentvotes', object_hash, txid, vout_index]
            raw_votes = self.rpc_command(*cmd)
            self.gobject_votes[object_hash] = dynamiclib.parse_raw_votes(raw_votes)

        return self.gobject_votes[object_hash]

    def is_govobj_maturity_phase(self):
        # 3-day period for govobj maturity
        maturity_phase_delta = 1662      # ~(60*24*3)/2.6
        if config.network == 'testnet':
            maturity_phase_delta = 24    # testnet

        event_block_height = self.next_superblock_height()
        maturity_phase_start_block = event_block_height - maturity_phase_delta

        current_height = self.rpc_command('getblockcount')
        event_block_height = self.next_superblock_height()

        # print "current_height = %d" % current_height
        # print "event_block_height = %d" % event_block_height
        # print "maturity_phase_delta = %d" % maturity_phase_delta
        # print "maturity_phase_start_block = %d" % maturity_phase_start_block

        return (current_height >= maturity_phase_start_block)

    def we_are_the_winner(self):
        import dynamiclib
        # find the elected DN vin for superblock creation...
        current_block_hash = self.current_block_hash()
        dn_list = self.get_dynodes()
        winner = dynamiclib.elect_dn(block_hash=current_block_hash, dnlist=dn_list)
        my_vin = self.get_current_dynode_vin()

        # print "current_block_hash: [%s]" % current_block_hash
        # print "DN election winner: [%s]" % winner
        # print "current dynode VIN: [%s]" % my_vin

        return (winner == my_vin)

    @property
    def DYNODE_WATCHDOG_MAX_SECONDS(self):
        # note: self.govinfo is already memoized
        return self.govinfo['dynodewatchdogmaxseconds']

    @property
    def SENTINEL_WATCHDOG_MAX_SECONDS(self):
        return (self.DYNODE_WATCHDOG_MAX_SECONDS // 2)

    def estimate_block_time(self, height):
        """
        Called by block_height_to_epoch if block height is in the future.
        Call `block_height_to_epoch` instead of this method.

        DO NOT CALL DIRECTLY if you don't want a "Oh Noes." exception.
        """
        current_block_height = self.rpc_command('getblockcount')
        diff = height - current_block_height

        if (diff < 0):
            raise Exception("Oh Noes.")

        future_minutes = 2.62 * diff
        future_seconds = 60 * future_minutes
        estimated_epoch = int(time.time() + future_seconds)

        return estimated_epoch

    def block_height_to_epoch(self, height):
        """
        Get the epoch for a given block height, or estimate it if the block hasn't
        been mined yet. Call this method instead of `estimate_block_time`.
        """
        epoch = -1

        try:
            bhash = self.rpc_command('getblockhash', height)
            block = self.rpc_command('getblock', bhash)
            epoch = block['time']
        except JSONRPCException as e:
            if e.message == 'Block height out of range':
                epoch = self.estimate_block_time(height)
            else:
                print("error: %s" % e)
                raise e

        return epoch
