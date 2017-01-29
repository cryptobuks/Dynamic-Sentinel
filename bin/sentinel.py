#!/usr/bin/env python
import sys
import os
sys.path.append(os.path.normpath(os.path.join(os.path.dirname(__file__), '../lib')))
import init
import config
import misc
from darksilkd import DarkSilkDaemon
from models import Superblock, Proposal, GovernanceObject, Watchdog
from models import VoteSignals, VoteOutcomes, Transient
import socket
from misc import printdbg
import time
from bitcoinrpc.authproxy import JSONRPCException
import signal


# sync darksilkd gobject list with our local relational DB backend
def perform_darksilkd_object_sync(darksilkd):
    GovernanceObject.sync(darksilkd)


# delete old watchdog objects, create new when necessary
def watchdog_check(darksilkd):
    printdbg("in watchdog_check")
    # delete expired watchdogs
    for wd in Watchdog.expired(darksilkd):
        printdbg("\tFound expired watchdog [%s], voting to delete" % wd.object_hash)
        wd.vote(darksilkd, VoteSignals.delete, VoteOutcomes.yes)

    # now, get all the active ones...
    active_wd = Watchdog.active(darksilkd)
    active_count = active_wd.count()

    # none exist, submit a new one to the network
    if 0 == active_count:
        # create/submit one
        printdbg("\tNo watchdogs exist... submitting new one.")
        wd = Watchdog(created_at=int(time.time()))
        wd.submit(darksilkd)

    else:
        wd_list = sorted(active_wd, key=lambda wd: wd.object_hash)

        # highest hash wins
        winner = wd_list.pop()
        printdbg("\tFound winning watchdog [%s], voting VALID" % winner.object_hash)
        winner.vote(darksilkd, VoteSignals.valid, VoteOutcomes.yes)

        # if remaining Watchdogs exist in the list, vote delete
        for wd in wd_list:
            printdbg("\tFound losing watchdog [%s], voting DELETE" % wd.object_hash)
            wd.vote(darksilkd, VoteSignals.delete, VoteOutcomes.yes)

    printdbg("leaving watchdog_check")


def attempt_superblock_creation(darksilkd):
    import darksilklib

    if not darksilkd.is_stormnode():
        print("We are not a Stormnode... can't submit superblocks!")
        return

    # query votes for this specific ebh... if we have voted for this specific
    # ebh, then it's voted on. since we track votes this is all done using joins
    # against the votes table
    #
    # has this stormnode voted on *any* superblocks at the given event_block_height?
    # have we voted FUNDING=YES for a superblock for this specific event_block_height?

    event_block_height = darksilkd.next_superblock_height()

    if Superblock.is_voted_funding(event_block_height):
        # printdbg("ALREADY VOTED! 'til next time!")

        # vote down any new SBs because we've already chosen a winner
        for sb in Superblock.at_height(event_block_height):
            if not sb.voted_on(signal=VoteSignals.funding):
                sb.vote(darksilkd, VoteSignals.funding, VoteOutcomes.no)

        # now return, we're done
        return

    if not darksilkd.is_govobj_maturity_phase():
        printdbg("Not in maturity phase yet -- will not attempt Superblock")
        return

    proposals = Proposal.approved_and_ranked(proposal_quorum=darksilkd.governance_quorum(), next_superblock_max_budget=darksilkd.next_superblock_max_budget())
    budget_max = darksilkd.get_superblock_budget_allocation(event_block_height)
    sb_epoch_time = darksilkd.block_height_to_epoch(event_block_height)

    sb = darksilklib.create_superblock(proposals, event_block_height, budget_max, sb_epoch_time)
    if not sb:
        printdbg("No superblock created, sorry. Returning.")
        return

    # find the deterministic SB w/highest object_hash in the DB
    dbrec = Superblock.find_highest_deterministic(sb.hex_hash())
    if dbrec:
        dbrec.vote(darksilkd, VoteSignals.funding, VoteOutcomes.yes)

        # any other blocks which match the sb_hash are duplicates, delete them
        for sb in Superblock.select().where(Superblock.sb_hash == sb.hex_hash()):
            if not sb.voted_on(signal=VoteSignals.funding):
                sb.vote(darksilkd, VoteSignals.delete, VoteOutcomes.yes)

        printdbg("VOTED FUNDING FOR SB! We're done here 'til next superblock cycle.")
        return
    else:
        printdbg("The correct superblock wasn't found on the network...")

    # if we are the elected stormnode...
    if (darksilkd.we_are_the_winner()):
        printdbg("we are the winner! Submit SB to network")
        sb.submit(darksilkd)


def check_object_validity(darksilkd):
    # vote (in)valid objects
    for gov_class in [Proposal, Superblock]:
        for obj in gov_class.select():
            obj.vote_validity(darksilkd)


def is_darksilkd_port_open(darksilkd):
    # test socket open before beginning, display instructive message to MN
    # operators if it's not
    port_open = False
    try:
        info = darksilkd.rpc_command('getinfo')
        port_open = True
    except (socket.error, JSONRPCException) as e:
        print("%s" % e)

    return port_open


def main():
    darksilkd = DarkSilkDaemon.from_darksilk_conf(config.darksilk_conf)

    # check darksilkd connectivity
    if not is_darksilkd_port_open(darksilkd):
        print("Cannot connect to darksilkd. Please ensure darksilkd is running and the JSONRPC port is open to Sentinel.")
        return

    # check darksilkd sync
    if not darksilkd.is_synced():
        print("darksilkd not synced with network! Awaiting full sync before running Sentinel.")
        return

    # ensure valid stormnode
    if not darksilkd.is_stormnode():
        print("Invalid Stormnode Status, cannot continue.")
        return

    # register a handler if SENTINEL_DEBUG is set
    if os.environ.get('SENTINEL_DEBUG', None):
        import logging
        logger = logging.getLogger('peewee')
        logger.setLevel(logging.DEBUG)
        logger.addHandler(logging.StreamHandler())

    # ========================================================================
    # general flow:
    # ========================================================================
    #
    # load "gobject list" rpc command data & create new objects in local MySQL DB
    perform_darksilkd_object_sync(darksilkd)

    # delete old watchdog objects, create a new if necessary
    watchdog_check(darksilkd)

    # auto vote network objects as valid/invalid
    check_object_validity(darksilkd)

    # create a Superblock if necessary
    attempt_superblock_creation(darksilkd)


def signal_handler(signum, frame):
    print("Got a signal [%d], cleaning up..." % (signum))
    Transient.delete('SENTINEL_RUNNING')
    sys.exit(1)


if __name__ == '__main__':
    signal.signal(signal.SIGINT, signal_handler)

    # ensure another instance of Sentinel is not currently running
    mutex_key = 'SENTINEL_RUNNING'
    # assume that all processes expire after 'timeout_seconds' seconds
    timeout_seconds = 90

    is_running = Transient.get(mutex_key)
    if is_running:
        printdbg("An instance of Sentinel is already running -- aborting.")
        sys.exit(1)
    else:
        Transient.set(mutex_key, misc.now(), timeout_seconds)

    # locked to this instance -- perform main logic here
    main()

    Transient.delete(mutex_key)